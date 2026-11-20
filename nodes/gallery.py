"""Gallery page and its API: /rigstools/gallery (the page), /rigstools/gallery/api/* (JSON, thumbnails, files).

Only pictures of the gallery folders are served. Changing the folder list is allowed from this computer only.
"""
import asyncio
import ipaddress
import json
import os
import threading
from pathlib import Path

from ..core import logger
from ..core import gallery as G
from ..core.image_meta import read_metadata
from ..core.prompt_graph import parameters_from_prompt
from ..core.settings import setting_on, setting_value, gallery_enabled

UI = Path(__file__).resolve().parent.parent / "gallery_ui"
TYPES = {".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".svg": "image/svg+xml"}


def _local(request):
    try:
        return ipaddress.ip_address((request.remote or "").split("%")[0]).is_loopback
    except ValueError:
        return False


def _files_allowed(request):
    """Deleting and moving files: from this computer, or from the network when Settings → Rigstools allows it."""
    return _local(request) or setting_on("Rigstools.Gallery.NetworkFileOps")


def _file_data(path):
    """Parameters text (rebuilt from the prompt when the file has none) and the workflow of a picture."""
    img, metadata = read_metadata(path)
    img.close()
    parameters = metadata.get("parameters") or ""
    if not parameters and metadata.get("prompt"):
        parameters = parameters_from_prompt(metadata["prompt"]) or ""
    workflow = metadata.get("workflow")
    if isinstance(workflow, str):
        try:
            workflow = json.loads(workflow)
        except ValueError:
            workflow = None
    return parameters, workflow


def _clean(o):
    """NaN and Infinity (they happen in workflows) are not JSON: the browser would refuse the whole answer."""
    if isinstance(o, float) and (o != o or o in (float("inf"), float("-inf"))):
        return None
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    return o


def _dumps(o):
    return json.dumps(_clean(o), ensure_ascii=False, default=str)


def _browse(path):
    """{path, parent, dirs: [{name, path}], places: [{name, path}]}; path "" = the drives (Windows) or "/"."""
    import string
    places = [{"name": "home", "path": str(Path.home())}]
    try:
        import folder_paths
        places.append({"name": "output", "path": folder_paths.get_output_directory()})
    except Exception:
        pass
    drives = [f"{d}:\\" for d in string.ascii_uppercase if os.name == "nt" and os.path.isdir(f"{d}:\\")]
    places += [{"name": d, "path": d, "drive": True} for d in drives]
    if not path:
        if os.name == "nt":
            return {"path": "", "parent": None, "dirs": [{"name": d, "path": d} for d in drives], "places": places}
        path = "/"
    p = Path(os.path.expanduser(path))
    if not p.is_dir():
        raise ValueError("not_folder")
    p = p.resolve()
    dirs = []
    try:
        with os.scandir(p) as it:
            for e in it:
                if e.name.startswith((".", "$")) or e.name in ("System Volume Information", "__pycache__"):
                    continue
                try:
                    if not e.is_dir():
                        continue
                    if getattr(e.stat(follow_symlinks=False), "st_file_attributes", 0) & 2:     # hidden on Windows
                        continue
                except OSError:
                    continue
                dirs.append({"name": e.name, "path": os.path.join(str(p), e.name)})
    except PermissionError:
        raise ValueError("no_access")
    dirs.sort(key=lambda d: d["name"].lower())
    parent = str(p.parent) if p.parent != p else ("" if os.name == "nt" else None)
    return {"path": str(p), "parent": parent, "dirs": dirs[:3000], "places": places}


def register_routes():
    try:
        from aiohttp import web
        from server import PromptServer
    except Exception:
        return
    routes = PromptServer.instance.routes

    async def run(fn, *args):
        return await asyncio.get_running_loop().run_in_executor(None, fn, *args)

    def query(request):
        q = {}
        for k, v in request.query.items():
            q.setdefault(k, []).append(v)
        return q

    @routes.get("/rigstools/gallery")
    async def page(request):
        if not gallery_enabled():
            ru = str(setting_value("Comfy.Locale", "en")).lower().startswith("ru")
            text = ("PicoTeka выключена: Настройки → Rigstools → PicoTeka." if ru else
                    "PicoTeka is turned off: Settings → Rigstools → PicoTeka.")
            return web.Response(text=f"<!doctype html><meta charset=utf-8><title>PicoTeka</title><body style='margin:0;"
                                     f"height:100vh;display:flex;align-items:center;justify-content:center;background:#0d0f14;"
                                     f"color:#8a8f9c;font:15px system-ui,sans-serif'>{text}</body>", content_type="text/html")
        return web.FileResponse(UI / "index.html", headers={"Cache-Control": "no-cache"})

    @routes.get("/rigstools/gallery/assets/{name}")
    async def asset(request):
        name = request.match_info["name"]
        p = (UI / name).resolve()
        if p.parent != UI or not p.is_file():
            return web.Response(status=404)
        return web.FileResponse(p, headers={"Cache-Control": "no-cache", "Content-Type": TYPES.get(p.suffix, "text/plain")})

    @routes.get("/rigstools/gallery/api/status")
    async def status(request):
        index, scanner = G.get()
        total = await run(lambda: index.db().execute("SELECT COUNT(*) FROM images").fetchone()[0])
        from ..core.settings import gallery_auto_scan
        return web.json_response({**scanner.status(), "indexed": total, "auto_scan": gallery_auto_scan()})

    @routes.post("/rigstools/gallery/api/scan")
    async def scan(request):
        G.get()[1].start()
        return web.json_response({"ok": True})

    @routes.get("/rigstools/gallery/api/folders")
    async def folders(request):
        index, _ = G.get()
        return web.json_response(await run(G.folders, index))

    @routes.post("/rigstools/gallery/api/roots")
    async def roots(request):
        if not _local(request):
            return web.json_response({"error": "local_only"}, status=403)
        index, scanner = G.get()
        body = await request.json()
        try:
            if body.get("remove"):
                await run(index.remove_root, body["remove"])
            else:
                await run(index.add_root, body.get("path", ""), body.get("label"))
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        scanner.start()
        return web.json_response(await run(G.folders, index))

    @routes.get("/rigstools/gallery/api/browse")
    async def browse(request):
        """The folders of this computer, for choosing a gallery folder (from this computer only, as adding one)."""
        if not _local(request):
            return web.json_response({"error": "local_only"}, status=403)
        try:
            return web.json_response(await run(_browse, request.query.get("path", "")))
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)

    @routes.get("/rigstools/gallery/api/images")
    async def images(request):
        index, _ = G.get()
        q = query(request)
        try:
            offset = max(0, int(request.query.get("offset", 0)))
            limit = min(500, max(1, int(request.query.get("limit", 120))))
            return web.json_response(await run(G.list_images, index, q, offset, limit))
        except Exception as e:
            logger.warning(f"gallery list failed: {e}")
            return web.json_response({"error": str(e)}, status=400)

    @routes.get("/rigstools/gallery/api/facets")
    async def facets(request):
        index, _ = G.get()
        return web.json_response(await run(G.facets, index, query(request)))

    @routes.get("/rigstools/gallery/api/thumb/{id}")
    async def thumb(request):
        index, _ = G.get()
        try:
            p = await run(G.thumb, index, int(request.match_info["id"]), int(request.query.get("s", 384)))
        except Exception as e:
            logger.debug(f"gallery thumb failed: {e}")
            p = None
        if not p:
            return web.Response(status=404)
        return web.FileResponse(p, headers={"Cache-Control": "max-age=86400", "Content-Type": "image/webp"})

    @routes.get("/rigstools/gallery/api/file/{id}")
    async def file(request):
        index, _ = G.get()
        r = await run(lambda: index.db().execute("SELECT real_path FROM images WHERE id = ?",
                                                 (int(request.match_info["id"]),)).fetchone())
        if not r or not os.path.exists(r[0]):
            return web.Response(status=404)
        return web.FileResponse(r[0], headers={"Cache-Control": "no-cache"})

    @routes.get("/rigstools/gallery/api/meta/{id}")
    async def meta(request):
        """What is written in the file: the parameters text, the ComfyUI prompt and workflow (for the ⓘ dialog)."""
        index, _ = G.get()
        r = await run(lambda: index.db().execute("SELECT real_path FROM images WHERE id = ?",
                                                 (int(request.match_info["id"]),)).fetchone())
        if not r or not os.path.exists(r[0]):
            return web.Response(status=404)

        def work():
            img, metadata = read_metadata(r[0])
            img.close()
            return {"parameters": metadata.get("parameters") or "", "prompt": metadata.get("prompt"),
                    "workflow": metadata.get("workflow")}
        return web.json_response(await run(work), dumps=_dumps)

    async def body_ids(request):
        body = await request.json()
        return body, [int(i) for i in body.get("ids") or []]

    @routes.post("/rigstools/gallery/api/rate")
    async def rate(request):
        body, ids = await body_ids(request)
        if ids:
            await run(G.set_rating, G.get()[0], ids, body.get("rating", 0))
        return web.json_response({"ok": True})

    @routes.post("/rigstools/gallery/api/tags")
    async def tags(request):
        body, ids = await body_ids(request)
        if ids:
            await run(G.edit_tags, G.get()[0], ids, body.get("add") or [], body.get("remove") or [])
        return web.json_response(await run(G.all_tags, G.get()[0]))

    @routes.get("/rigstools/gallery/api/tags")
    async def tag_list(request):
        return web.json_response(await run(G.all_tags, G.get()[0]))

    @routes.post("/rigstools/gallery/api/tag")
    async def tag_edit(request):
        """{rename: old, to: new} or {delete: name}."""
        body = await request.json()
        index = G.get()[0]
        try:
            if body.get("delete"):
                await run(G.delete_tag, index, body["delete"])
            else:
                await run(G.rename_tag, index, body.get("rename", ""), body.get("to", ""))
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        return web.json_response(await run(G.all_tags, index))

    @routes.post("/rigstools/gallery/api/delete")
    async def delete(request):
        if not _files_allowed(request):
            return web.json_response({"error": "network_files"}, status=403)
        _, ids = await body_ids(request)
        try:
            done, errors = await run(G.delete_files, G.get()[0], ids)
        except ImportError:
            return web.json_response({"error": "no_send2trash"}, status=500)
        return web.json_response({"done": done, "errors": errors})

    @routes.post("/rigstools/gallery/api/move")
    async def move(request):
        if not _files_allowed(request):
            return web.json_response({"error": "network_files"}, status=403)
        body, ids = await body_ids(request)
        try:
            done, errors = await run(G.move_files, G.get()[0], ids, body.get("root", ""), body.get("folder", ""))
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        return web.json_response({"done": done, "errors": errors})

    # ---- to the open workflow: the gallery page -> this server -> the last active ComfyUI tab (as LoRA Manager)
    active = {"sid": None}

    @routes.post("/rigstools/gallery/api/active")
    async def set_active(request):
        active["sid"] = (await request.json()).get("client_id")
        return web.json_response({"ok": True})

    @routes.post("/rigstools/gallery/api/send")
    async def send(request):
        """{id, kind: image | params | workflow} -> the event "rigstools.gallery" in the ComfyUI tab."""
        server = PromptServer.instance
        if not server.sockets:
            return web.json_response({"error": "no_comfy"}, status=409)
        body = await request.json()
        index = G.get()[0]
        r = await run(lambda: index.db().execute("SELECT real_path, name FROM images WHERE id = ?",
                                                 (int(body.get("id", 0)),)).fetchone())
        if not r or not os.path.exists(r["real_path"]):
            return web.json_response({"error": "gone"}, status=404)
        kind = body.get("kind")
        msg = {"kind": kind, "name": r["name"]}
        if kind == "image":
            msg["image"] = await run(G.for_loader, index, int(body["id"]))
        else:
            parameters, workflow = await run(_file_data, r["real_path"])
            if kind == "params":
                msg["parameters"] = parameters
            elif kind == "workflow" and workflow:
                msg["workflow"] = _clean(workflow)      # NaN in the workflow would break the message in the ComfyUI tab
            else:
                return web.json_response({"error": "no_workflow"}, status=404)
        sid = active["sid"] if active["sid"] in server.sockets else list(server.sockets)[-1]
        await server.send_json("rigstools.gallery", msg, sid)
        return web.json_response({"ok": True})

    # every finished run: scan, so new pictures show in the gallery. Not only the runs that report a picture in the
    # output folder: a save node may write to another connected folder or report nothing. The scan reads only new
    # and changed files, so a run that saved nothing costs a walk of the folders.
    queue = PromptServer.instance.prompt_queue
    task_done = queue.task_done

    def task_done_and_scan(item_id, history_result, *args, **kwargs):
        task_done(item_id, history_result, *args, **kwargs)
        G.get()[1].start()
    queue.task_done = task_done_and_scan

    # the first scan starts a few seconds after ComfyUI is up, so it does not slow the start
    threading.Timer(5.0, lambda: G.get()[1].start()).start()


register_routes()
