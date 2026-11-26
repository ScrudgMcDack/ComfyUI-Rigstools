"""Posting pictures from PicoTeka to Civitai.

Civitai's public REST API only reads; posting goes through its MCP server (https://mcp.civitai.com/mcp, JSON-RPC over
HTTP with the user's API key): whoami → upload_image (base64) → create_post. Civitai reads the generation data and the
resources (checkpoint, LoRA…) from the picture's metadata itself, so the pictures go as they are — no model is attached
to the post by hand (that would mark the whole post as made with one model).

The key: the CIVITAI_API_KEY environment variable, else the key typed in Settings → Rigstools → Civitai → API key. That
field does not keep the key in the ComfyUI settings (they are sent to every page that opens ComfyUI): it hands the key
to this server, which keeps it in <ComfyUI user folder>/rigstools/civitai_key and never gives it back."""
import base64
import hashlib
import io
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from .logger import logger
from .settings import _user_dir, setting_value

MCP = "https://mcp.civitai.com/mcp"
# the server answers 403 to the default Python user agent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ComfyUI-Rigstools"
LIMIT = 10 * 1024 * 1024        # upload_image takes at most 10 MiB (after base64 decoding)
MAX_PICTURES = 20


def enabled():
    """Settings → Rigstools → Civitai → Allow posting (off by default). Off: nothing is sent to Civitai, not even the
    check of the key."""
    return setting_value("Rigstools.Civitai.Enabled", False) is True


def _key_file():
    return os.path.join(_user_dir(), "rigstools", "civitai_key")


def stored_key():
    try:
        with open(_key_file(), "r", encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def api_key():
    return (os.environ.get("CIVITAI_API_KEY") or "").strip() or stored_key()


def key_state():
    """What the settings field shows: is there a key and where from (env | file). Never the key itself."""
    source = "env" if (os.environ.get("CIVITAI_API_KEY") or "").strip() else "file" if stored_key() else None
    return {"set": source is not None, "source": source}


# what Civitai said about a key: {sha256 of the key: {"check": "ok" | "bad", "user", "error"}}; "unchecked" (no
# connection and the like) is not remembered, so the next look at the settings asks again
_checked = {}


def check_key(force=False):
    """-> {"check": none | ok | bad | unchecked, "user", "error"} for the key in use."""
    key = api_key()
    if not key:
        return {"check": "none"}
    if not enabled():
        return {"check": "unchecked", "error": "disabled"}
    h = hashlib.sha256(key.encode()).hexdigest()
    if not force and h in _checked:
        return _checked[h]
    try:
        mcp = _Mcp(key, timeout=20)
        mcp.open()
        m = re.search(r"You are (.+?) \(id", mcp.tool("whoami", {}))
        r = {"check": "ok", "user": m.group(1) if m else ""}
    except CivitaiError as e:
        r = {"check": "bad" if e.code in ("bad_key", "not_onboarded") else "unchecked", "error": e.code}
    if r["check"] != "unchecked":
        _checked[h] = r
    return r


def save_key(key):
    """Keeps the key typed in the settings ("" removes it) and checks it on Civitai; -> check_key()."""
    key = (key or "").strip()
    path = _key_file()
    if not key:
        try:
            os.remove(path)
        except OSError:
            pass
        return check_key()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(key)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return check_key(force=True)


class CivitaiError(Exception):
    """code: what the page shows (bad_key, not_onboarded, too_big, network, civitai); detail: the text for the log."""
    def __init__(self, code, detail=""):
        super().__init__(detail or code)
        self.code, self.detail = code, detail


class _Mcp:
    def __init__(self, key, timeout=180):
        self.key, self.sid, self.n, self.timeout = key, None, 0, timeout

    def _rpc(self, method, params=None, notify=False):
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if not notify:
            self.n += 1
            body["id"] = self.n
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                   "User-Agent": UA, "Authorization": "Bearer " + self.key}
        if self.sid:
            headers["Mcp-Session-Id"] = self.sid
        req = urllib.request.Request(MCP, json.dumps(body).encode(), headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                self.sid = r.headers.get("Mcp-Session-Id") or self.sid
                text = r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            raise CivitaiError("bad_key" if e.code in (401, 403) and "auth" in detail.lower() else "civitai",
                               f"HTTP {e.code}: {detail}")
        except Exception as e:      # offline, timeout, proxy…
            raise CivitaiError("network", str(e))
        for line in text.splitlines():       # an event stream answer: the JSON is on the "data:" line
            if line.startswith("data:"):
                text = line[5:]
        return json.loads(text) if text.strip() else None

    def open(self):
        self._rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                 "clientInfo": {"name": "rigstools-picoteka", "version": "1"}})
        self._rpc("notifications/initialized", notify=True)

    def tool(self, name, args):
        r = self._rpc("tools/call", {"name": name, "arguments": args})
        if not r or "error" in r:
            raise CivitaiError("civitai", f"{name}: {(r or {}).get('error')}")
        res = r["result"]
        text = "\n".join(c.get("text", "") for c in res.get("content", []) if isinstance(c, dict))
        if res.get("isError"):
            low = text.lower()
            code = ("not_onboarded" if "onboard" in low else "bad_key" if "unauthor" in low or "api key" in low
                    else "too_big" if "too large" in low else "civitai")
            raise CivitaiError(code, f"{name}: {text[:500]}")
        return text


PNG_SIG = b"\x89PNG\r\n\x1a\n"
TEXT_CHUNKS = (b"tEXt", b"iTXt", b"zTXt")


def _strip_text(data, keys):
    """A PNG without the text chunks named `keys` (e.g. workflow, prompt). Chunks are copied byte for byte, the
    picture (IDAT) is not touched: each chunk is length, type, data and its own CRC, so dropping a whole chunk keeps
    the file valid."""
    if not data.startswith(PNG_SIG):
        return data
    out, i = [PNG_SIG], 8
    while i + 8 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        kind, end = data[i + 4:i + 8], i + 12 + n
        if kind in TEXT_CHUNKS and data[i + 8:i + 8 + n].split(b"\0", 1)[0].decode("latin-1") in keys:
            i = end
            continue
        out.append(data[i:end])
        i = end
        if kind == b"IEND":
            break
    return b"".join(out)


def _png_smaller(data):
    """The same PNG compressed harder, without loss and with all its chunks: oxipng when it is installed (better and
    faster), else Pillow at zlib level 9."""
    try:
        import oxipng
        return oxipng.optimize_from_memory(data, level=2, strip=oxipng.StripChunks.none())
    except ImportError:
        pass
    from PIL import Image, PngImagePlugin
    im = Image.open(io.BytesIO(data))
    meta = PngImagePlugin.PngInfo()
    for k, v in (getattr(im, "text", {}) or {}).items():
        meta.add_text(k, v)
    out = io.BytesIO()
    im.save(out, "PNG", pnginfo=meta, optimize=True, compress_level=9)
    return out.getvalue()


def _exif(text, workflow=True):
    """EXIF for a WebP or JPEG copy: the A1111 parameters in UserComment (Civitai reads them there); for WebP also the
    ComfyUI workflow and prompt in Make / Model, where ComfyUI itself writes them."""
    from PIL import Image
    exif = Image.Exif()
    if text.get("parameters"):
        exif[0x8769] = {0x9286: b"UNICODE\0" + text["parameters"].encode("utf-16-be")}
    if workflow and text.get("workflow"):
        exif[0x010F] = "workflow:" + text["workflow"]
    if workflow and text.get("prompt"):
        exif[0x0110] = "prompt:" + text["prompt"]
    return exif


# ---- the prepared copies: compressed once, when the window checks the pictures, and sent from memory ------------
# key: (path, size, mtime, keep_workflow) — a changed file or the other checkbox gives another key; a copy is dropped
# when it is uploaded, when the window is closed without sending, or after 30 minutes untouched
_ready = {}
_ready_lock = threading.Lock()
READY_TTL = 30 * 60


def _ready_key(path, keep_workflow):
    st = os.stat(path)
    return (os.path.abspath(path), st.st_size, st.st_mtime_ns, bool(keep_workflow))


def _ready_get(key):
    now = time.time()
    with _ready_lock:
        for k in [k for k, v in _ready.items() if now - v[3] > READY_TTL]:
            del _ready[k]
        v = _ready.get(key)
        if v:
            _ready[key] = (*v[:3], now)
            return v[:3]
    return None


def forget(paths):
    """Drops the prepared copies of these files (both checkbox states)."""
    paths = {os.path.abspath(p) for p in paths}
    with _ready_lock:
        for k in [k for k in _ready if k[0] in paths]:
            del _ready[k]


def _picture(path, keep_workflow):
    """The bytes to upload, their type and how they were made (see _make): the copy prepared before when there is one."""
    try:
        key = _ready_key(path, keep_workflow)
    except OSError:
        key = None
    got = key and _ready_get(key)
    if got:
        return got
    out = _make(path, keep_workflow)
    if key and out[2] != "as is":                 # the file itself is read again quickly; a compressed copy is kept
        with _ready_lock:
            _ready[key] = (*out, time.time())
    return out


def _make(path, keep_workflow):
    """The bytes to upload, their type and how they were made: as is | png (compressed harder) | webp | jpeg.
    Civitai's MCP takes at most 10 MiB, so a bigger PNG goes, the first that fits: the same PNG compressed harder
    without loss (oxipng); WebP without loss (stronger), with the parameters and the workflow in EXIF; JPEG 95 (the
    strongest, with loss; the parameters stay, the workflow does not). Without the workflow (the checkbox off) the
    ComfyUI workflow and prompt are taken out first; the parameters always stay."""
    with open(path, "rb") as fh:
        data = fh.read()
    ext = os.path.splitext(path)[1].lower()
    ctype = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(ext, "image/png")
    if ctype != "image/png" or not data.startswith(PNG_SIG):
        if len(data) > LIMIT:
            raise CivitaiError("too_big", f"{os.path.basename(path)}: {len(data)} bytes")
        return data, ctype, "as is"
    if not keep_workflow:
        data = _strip_text(data, ("workflow", "prompt"))
    if len(data) <= LIMIT:
        return data, "image/png", "as is"
    out = _png_smaller(data)
    if len(out) <= LIMIT:
        return out, "image/png", "png"
    from PIL import Image
    im = Image.open(io.BytesIO(data))
    text = dict(getattr(im, "text", {}) or {})
    buf = io.BytesIO()
    im.save(buf, "WEBP", lossless=True, quality=80, method=2, exif=_exif(text))
    if buf.tell() <= LIMIT:
        return buf.getvalue(), "image/webp", "webp"
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=95, exif=_exif(text, workflow=False))
    if buf.tell() > LIMIT:
        raise CivitaiError("too_big", f"{os.path.basename(path)}: {buf.tell()} bytes as JPEG")
    return buf.getvalue(), "image/jpeg", "jpeg"


# ---- jobs: a post runs in a thread, the page asks how far it got ------------------------------------------------
_jobs = {}
_lock = threading.Lock()


def job(job_id):
    with _lock:
        j = _jobs.get(job_id)
        return dict(j) if j else None


def precheck(path, keep_workflow=True):
    """For the thumbnails of the dialog: how the picture goes — "as is", "png" (compressed harder), "webp", "jpeg" —
    or "too_big"."""
    try:
        return _picture(path, keep_workflow)[2]
    except CivitaiError:
        return "too_big"


def post_status(post_id):
    """Is a post published? -> (True | False | None when unknown, the publishing date text). Reads get_post."""
    key = api_key()
    if not enabled() or not key:
        return None, None
    mcp = _Mcp(key, timeout=20)
    mcp.open()
    text = mcp.tool("get_post", {"id": int(post_id)})
    # "Post #N — title (draft)\nBy: …\nPublished: (draft)\nURL: …"; a published post has its date there
    m = re.search(r"(?im)^\s*published\s*:\s*(.+?)\s*$", text)
    if not m:
        return None, None
    value = m.group(1)
    if not value or "draft" in value.lower() or value.lower() in ("null", "none", "-", "—"):
        return False, None
    return True, value


UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_refreshed = {}         # post id -> when it was last asked about (see due())


def due(post_id, every):
    """True (and remembered) when the post was not asked about for `every` seconds: Civitai is not asked on every click."""
    now = time.time()
    if now - _refreshed.get(post_id, 0) < every:
        return False
    _refreshed[post_id] = now
    return True


def _get_json(url, key=None):
    h = {"User-Agent": UA, "Accept": "application/json"}
    if key:
        h["Authorization"] = "Bearer " + key
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=20) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raise CivitaiError("bad_key" if e.code in (401, 403) else "gone" if e.code == 404 else "civitai",
                           f"{url.split('?')[0]}: HTTP {e.code}")
    except Exception as e:
        raise CivitaiError("network", str(e))


def post_info(post_id):
    """-> {"published": bool, "published_at", "nsfw": the rating level of the whole post (0 — not rated yet)}.
    The site's own request post.get (tRPC, with the key): it knows the rating of a draft too. It is not a documented
    API — when it fails, whether the post is published is read from get_post of the MCP server, without the rating."""
    key = api_key()
    if not enabled() or not key:
        return None
    try:
        url = "https://civitai.com/api/trpc/post.get?input=" + urllib.parse.quote(json.dumps({"json": {"id": int(post_id)}}))
        d = _get_json(url, key)
        d = d.get("result", {}).get("data", {}).get("json", d)
        if "id" in d:
            return {"published": bool(d.get("publishedAt")), "published_at": d.get("publishedAt"),
                    "nsfw": int(d.get("nsfwLevel") or 0)}
    except CivitaiError as e:
        if e.code == "gone":                      # deleted on Civitai (on the site, or from PicoTeka elsewhere)
            return {"gone": True}
        logger.debug(f"Civitai post.get {post_id}: {e.detail}")
    published, at = post_status(post_id)
    return None if published is None else {"published": published, "published_at": at, "nsfw": None}


def image_info(cid):
    """A picture on Civitai by its id (the site's request image.get, a draft too): -> {"nsfw", "ingestion"} or
    {"gone": True} when it was deleted."""
    try:
        d = _trpc("image.get", {"id": int(cid)}) or {}
    except CivitaiError as e:
        if e.code == "gone":
            return {"gone": True}
        raise
    return {"nsfw": int(d.get("nsfwLevel") or 0), "ingestion": d.get("ingestion")}


def delete_image(cid):
    """Deletes one picture of a post on Civitai (the site's request image.delete). An empty post stays — the caller
    deletes the post instead when it is the last picture."""
    try:
        _trpc("image.delete", {"id": int(cid)}, post=True)
    except CivitaiError as e:
        if e.code != "gone":
            raise
    logger.info(f"PicoTeka → Civitai: image {cid} deleted")


def delete_post(post_id):
    """Deletes a post (with its pictures) on Civitai. A post already gone counts as deleted."""
    key = api_key()
    if not enabled() or not key:
        raise CivitaiError("disabled")
    mcp = _Mcp(key, timeout=30)
    mcp.open()
    try:
        mcp.tool("delete_post", {"id": int(post_id)})
    except CivitaiError as e:
        if "not found" not in e.detail.lower() and "not_found" not in e.detail.lower():
            raise
    logger.info(f"PicoTeka → Civitai: post {post_id} deleted")


def post_images(post_id):
    """The pictures of a published post (the public API; a draft gives none): [(uuid, Civitai image id, level)]."""
    d = _get_json(f"https://civitai.com/api/v1/images?postId={int(post_id)}&nsfw=X&limit=100")
    out = []
    for it in d.get("items", []):
        u = UUID.search(str(it.get("url") or ""))
        if u and it.get("id"):
            out.append((u.group(0), int(it["id"]), int(it.get("browsingLevel") or 0)))
    return out


# ---- Tools and Techniques of the pictures (the site's own requests, by the Civitai image id) ----------------------
IMAGE_TECHNIQUES = ("txt2img", "img2img", "inpainting", "controlnet", "workflow", "Paintover")
_lists = {"at": 0, "tools": [], "techniques": []}


def _trpc(proc, inp=None, post=False):
    key = api_key()
    if not enabled() or not key:
        raise CivitaiError("disabled")
    url = "https://civitai.com/api/trpc/" + proc
    h = {"User-Agent": UA, "Accept": "application/json", "Authorization": "Bearer " + key}
    data = None
    if post:
        data = json.dumps({"json": inp}).encode()
        h["Content-Type"] = "application/json"
    elif inp is not None:
        url += "?input=" + urllib.parse.quote(json.dumps({"json": inp}))
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data, h), timeout=30) as r:
            d = json.loads(r.read().decode("utf-8", "replace") or "null")
    except urllib.error.HTTPError as e:
        raise CivitaiError("bad_key" if e.code in (401, 403) else "gone" if e.code == 404 else "civitai",
                           f"{proc}: HTTP {e.code}")
    except Exception as e:
        raise CivitaiError("network", str(e))
    if isinstance(d, dict) and "result" in d:
        return (d["result"].get("data") or {}).get("json")
    return d


def tool_lists():
    """-> {"tools": [{id, name}] (pictures and editors first), "techniques": [{id, name}] (pictures only)}; kept a day."""
    if time.time() - _lists["at"] < 86400 and _lists["tools"]:
        return {"tools": _lists["tools"], "techniques": _lists["techniques"]}
    def items(d):
        return d if isinstance(d, list) else (d or {}).get("items", []) if isinstance(d, dict) else []
    tools = [{"id": x["id"], "name": x["name"], "type": x.get("type")} for x in items(_trpc("tool.getAll", {}))
             if isinstance(x, dict) and x.get("id") and x.get("name")]
    tools.sort(key=lambda x: (x.get("type") not in ("Image", "Editor", "Upscalers"), x["name"].lower()))
    techniques = [{"id": x["id"], "name": x["name"]} for x in items(_trpc("technique.getAll", {}))
                  if isinstance(x, dict) and x.get("name") in IMAGE_TECHNIQUES]
    _lists.update(at=time.time(), tools=tools, techniques=techniques)
    return {"tools": tools, "techniques": techniques}


def tag_image(image_id, tools, techniques):
    """Adds to a picture on Civitai the tools and techniques (ids) it does not have yet; what it has stays."""
    have = _trpc("image.getGenerationData", {"id": int(image_id)}) or {}
    has_tools = {x.get("id") for x in have.get("tools") or [] if isinstance(x, dict)}
    has_tech = {x.get("id") for x in have.get("techniques") or [] if isinstance(x, dict)}
    add_tools = [t for t in tools if t not in has_tools]
    add_tech = [t for t in techniques if t not in has_tech]
    if add_tools:
        _trpc("image.addTools", {"data": [{"imageId": int(image_id), "toolId": int(t)} for t in add_tools]}, post=True)
    if add_tech:
        _trpc("image.addTechniques", {"data": [{"imageId": int(image_id), "techniqueId": int(t)} for t in add_tech]},
              post=True)


def start(items, title="", detail="", publish=False, keep_workflow=True, on_done=None, tools=(), techniques=(),
          on_published=None, on_ids=None):
    """Starts a post of items [(gallery id, path)]; -> job id. The job: stage (check, upload, post, done, error),
    done / total, the state of each picture (wait, upload, ok, error), url, error, detail. on_done(post_id, url,
    [(gallery id, uuid)], published) is called when the post is made (to mark the pictures in the gallery).
    There is no cancel: Civitai has no way to delete an uploaded picture that is not in a post yet."""
    job_id = uuid.uuid4().hex
    with _lock:
        for k in [k for k, v in _jobs.items() if time.time() - v["started"] > 3600]:
            del _jobs[k]
        _jobs[job_id] = {"stage": "check", "done": 0, "total": len(items), "items": ["wait"] * len(items),
                         "ids": [i for i, _ in items], "url": None, "post": None, "published": bool(publish),
                         "error": None, "detail": "", "user": None, "started": time.time()}

    def set_(**kw):
        with _lock:
            _jobs[job_id].update(kw)

    def mark(n, state):
        with _lock:
            _jobs[job_id]["items"] = [state if k == n else v for k, v in enumerate(_jobs[job_id]["items"])]

    def run():
        n = -1
        try:
            if not enabled():
                raise CivitaiError("disabled")
            key = api_key()
            if not key:
                raise CivitaiError("no_key")
            mcp = _Mcp(key)
            mcp.open()
            who = mcp.tool("whoami", {})
            m = re.search(r"You are (.+?) \(id", who)
            set_(user=m.group(1) if m else None, stage="upload")
            images = []
            for n, (_, path) in enumerate(items):
                mark(n, "upload")
                data, ctype, _ = _picture(path, keep_workflow)
                text = mcp.tool("upload_image", {"data": base64.b64encode(data).decode(), "contentType": ctype})
                u = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", text)
                if not u:
                    raise CivitaiError("civitai", f"upload_image: no UUID in {text[:200]}")
                img = {"uuid": u.group(0)}
                s = re.search(r"\((\d+)x(\d+)\)", text)
                if s:
                    img.update(width=int(s.group(1)), height=int(s.group(2)))
                images.append(img)
                forget([path])
                mark(n, "ok")
                set_(done=n + 1)
            n = -1
            set_(stage="post")
            args = {"images": images, "publish": bool(publish)}
            if title.strip():
                args["title"] = title.strip()
            if detail.strip():
                args["detail"] = detail.strip()
            text = mcp.tool("create_post", args)
            u = re.search(r"https://civitai\.com/posts/(\d+)", text)
            post_id = int(u.group(1)) if u else None
            # "Images processing: 149897312, …" — the Civitai ids of the pictures, in the order they were attached
            found = re.search(r"(?i)images processing:\s*([\d,\s]+)", text)
            cids = [int(x) for x in re.findall(r"\d+", found.group(1))] if found else []
            if len(cids) != len(images):
                cids = [None] * len(images)
            if on_done and post_id:
                try:
                    on_done(post_id, u.group(0), [(i, img["uuid"], cid) for (i, _), img, cid in zip(items, images, cids)],
                            bool(publish))
                except Exception as e:
                    logger.warning(f"PicoTeka → Civitai: could not mark the pictures: {e}", exc_info=True)
            # the ids came with the post: Tools and Techniques at once (a draft too); the window tells when they failed
            tag_ok = True
            if post_id and on_ids and all(cids) and (tools or techniques):
                set_(stage="tools")
                tag_ok = on_ids(post_id) is not False
            set_(stage="done", url=u.group(0) if u else None, post=post_id, tag_error=not tag_ok)
            logger.info(f"PicoTeka → Civitai: {len(images)} picture(s) {'published' if publish else 'as a draft'}: "
                        f"{u.group(0) if u else text[:200]}")
            # no ids in the answer: a published post gives them through the public API (it may need a moment);
            # a draft gets them when PicoTeka finds it published
            if not all(cids) and publish and post_id and on_published:
                for _ in range(8):
                    time.sleep(8)
                    try:
                        found = post_images(post_id)
                    except CivitaiError:
                        continue
                    if found:
                        on_published(post_id, found)
                        break
        except CivitaiError as e:
            if n >= 0:
                mark(n, "error")
            if e.code in ("bad_key", "not_onboarded") and api_key():     # the settings show it as rejected
                _checked[hashlib.sha256(api_key().encode()).hexdigest()] = {"check": "bad", "error": e.code}
            logger.warning(f"PicoTeka → Civitai failed ({e.code}): {e.detail}")
            set_(stage="error", error=e.code, detail=e.detail[:300])
        except Exception as e:
            if n >= 0:
                mark(n, "error")
            logger.warning(f"PicoTeka → Civitai failed: {e}", exc_info=True)
            set_(stage="error", error="civitai", detail=str(e)[:300])

    threading.Thread(target=run, name="rigstools-civitai-post", daemon=True).start()
    return job_id


def running():
    """The job still going, if any (the page that lost it — reloaded — finds it again)."""
    with _lock:
        for k, v in _jobs.items():
            if v["stage"] in ("check", "upload", "post"):
                return k
    return None
