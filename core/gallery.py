"""Gallery index: the pictures of the gallery folders and their generation data in one SQLite file.

The metadata of a picture is read once and kept here; a scan reads only new and changed files (by mtime and size),
and drops the rows of files that are gone. Tags and rating live here too — the picture files are never changed.
Thumbnails are cached as WebP next to the database.
"""
import hashlib
import json
import os
import shutil
import sqlite3
import threading
import time
from pathlib import Path

from PIL import UnidentifiedImageError

import folder_paths

from . import logger
from .image_meta import read_metadata, is_image_file

SCHEMA_VERSION = 1
TRASH_DAYS = 30                   # how long the tags and rating of a picture deleted from the gallery are kept
THUMB_SIZES = (256, 512, 768)     # SHORT side of a cached thumbnail (the grid crops it to a square); the page asks for
                                  # its cell size in device pixels and gets the next size up
FORMATS = {"PNG": "PNG", "JPEG": "JPEG", "MPO": "JPEG", "WEBP": "WEBP"}


def data_dir():
    d = Path(folder_paths.get_user_directory()) / "rigstools" / "gallery"
    d.mkdir(parents=True, exist_ok=True)
    return d


def norm(path):
    return os.path.normcase(os.path.abspath(path))


SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS roots(path TEXT PRIMARY KEY, label TEXT, builtin INTEGER DEFAULT 0, added REAL);
CREATE TABLE IF NOT EXISTS images(
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE NOT NULL,          -- normalised absolute path (the key)
  real_path TEXT NOT NULL,            -- as found on disk
  root TEXT NOT NULL, folder TEXT NOT NULL, name TEXT NOT NULL,
  mtime REAL, size INTEGER, width INTEGER, height INTEGER, fmt TEXT,
  has_params INTEGER DEFAULT 0, rebuilt INTEGER DEFAULT 0, has_workflow INTEGER DEFAULT 0,
  positive TEXT, negative TEXT, seed INTEGER, steps INTEGER, cfg REAL, clip_skip INTEGER,
  sampler TEXT, scheduler TEXT, denoise REAL, gen_width INTEGER, gen_height INTEGER,
  model TEXT, loras TEXT,             -- loras: JSON [[name, weight], ...]
  rating INTEGER DEFAULT 0,
  indexed REAL
);
CREATE INDEX IF NOT EXISTS i_folder ON images(folder);
CREATE INDEX IF NOT EXISTS i_mtime ON images(mtime);
CREATE INDEX IF NOT EXISTS i_model ON images(model);
CREATE INDEX IF NOT EXISTS i_sampler ON images(sampler);
CREATE INDEX IF NOT EXISTS i_rating ON images(rating);
CREATE TABLE IF NOT EXISTS image_loras(image_id INTEGER, lora TEXT, weight REAL);
CREATE INDEX IF NOT EXISTS i_il_lora ON image_loras(lora);
CREATE INDEX IF NOT EXISTS i_il_image ON image_loras(image_id);
CREATE TABLE IF NOT EXISTS tags(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL COLLATE NOCASE);
CREATE TABLE IF NOT EXISTS image_tags(image_id INTEGER, tag_id INTEGER, PRIMARY KEY(image_id, tag_id));
CREATE INDEX IF NOT EXISTS i_it_tag ON image_tags(tag_id);
-- tags and rating of pictures deleted from the gallery: they come back with a file restored to the same place
CREATE TABLE IF NOT EXISTS trash(path TEXT PRIMARY KEY, rating INTEGER, tags TEXT, deleted REAL);
CREATE VIRTUAL TABLE IF NOT EXISTS images_fts USING fts5(positive, negative, name, content='images', content_rowid='id',
  tokenize='unicode61');
CREATE TRIGGER IF NOT EXISTS t_ai AFTER INSERT ON images BEGIN
  INSERT INTO images_fts(rowid, positive, negative, name) VALUES (new.id, new.positive, new.negative, new.name); END;
CREATE TRIGGER IF NOT EXISTS t_ad AFTER DELETE ON images BEGIN
  INSERT INTO images_fts(images_fts, rowid, positive, negative, name) VALUES ('delete', old.id, old.positive, old.negative, old.name);
  DELETE FROM image_loras WHERE image_id = old.id; DELETE FROM image_tags WHERE image_id = old.id; END;
CREATE TRIGGER IF NOT EXISTS t_au AFTER UPDATE OF positive, negative, name ON images BEGIN
  INSERT INTO images_fts(images_fts, rowid, positive, negative, name) VALUES ('delete', old.id, old.positive, old.negative, old.name);
  INSERT INTO images_fts(rowid, positive, negative, name) VALUES (new.id, new.positive, new.negative, new.name); END;
"""


class Index:
    """One connection per thread (sqlite3 objects are not shared between threads)."""

    def __init__(self, path=None):
        self.path = str(path or data_dir() / "gallery.db")
        self._local = threading.local()
        self.lock = threading.Lock()          # writers take it; readers do not need it (WAL)
        with self.lock:
            c = self.db()
            c.executescript(SCHEMA)
            c.execute("INSERT OR REPLACE INTO meta VALUES ('schema', ?)", (str(SCHEMA_VERSION),))
            out = norm(folder_paths.get_output_directory())
            c.execute("INSERT OR IGNORE INTO roots(path, label, builtin, added) VALUES (?, 'output', 1, ?)",
                      (out, time.time()))
            c.commit()

    def db(self):
        c = getattr(self._local, "conn", None)
        if c is None:
            c = sqlite3.connect(self.path, timeout=30)
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("PRAGMA synchronous=NORMAL")
            self._local.conn = c
        return c

    # ---- roots ------------------------------------------------------------------------------------------------
    def roots(self):
        return [dict(r) for r in self.db().execute("SELECT * FROM roots ORDER BY builtin DESC, label")]

    def add_root(self, path, label=None):
        p = Path(path).expanduser()
        if not p.is_dir():
            raise ValueError("not_folder")
        # a folder inside a gallery folder (or one holding a gallery folder) would index the same pictures twice
        new = norm(p.resolve())
        for r in self.roots():
            old = r["path"]
            if new == old or new.startswith(old.rstrip(os.sep) + os.sep):
                raise ValueError("inside_root")
            if old.startswith(new.rstrip(os.sep) + os.sep):
                raise ValueError("holds_root")
        with self.lock:
            c = self.db()
            c.execute("INSERT OR IGNORE INTO roots(path, label, builtin, added) VALUES (?, ?, 0, ?)",
                      (norm(p), label or p.name, time.time()))
            c.commit()

    def remove_root(self, path):
        with self.lock:
            c = self.db()
            c.execute("DELETE FROM images WHERE root = ?", (norm(path),))
            c.execute("DELETE FROM roots WHERE path = ? AND builtin = 0", (norm(path),))
            c.commit()


# ---- reading one picture -----------------------------------------------------------------------------------------
def _num(v, kind=float):
    try:
        return kind(str(v).strip())
    except (TypeError, ValueError):
        return None


def read_picture(path):
    """Row values of one picture: size, format and the generation data (A1111 parameters, or rebuilt from the
    ComfyUI prompt). Model and LoRA are kept as stored in the file — no lookup in the model folders here."""
    from ..nodes.parameters import parse_a1111, _sampler_and_scheduler
    from ..nodes.lora_hashes import LORA_TAG
    img, metadata = read_metadata(path)
    try:
        width, height = img.size
        fmt = FORMATS.get((img.format or "").upper(), (img.format or Path(path).suffix[1:]).upper())
    finally:
        img.close()
    parameters = metadata.get("parameters") or ""
    rebuilt = False
    if not parameters and metadata.get("prompt"):
        try:
            from .prompt_graph import parameters_from_prompt
            parameters = parameters_from_prompt(metadata["prompt"]) or ""
            rebuilt = bool(parameters)
        except Exception as e:
            logger.debug(f"gallery: could not rebuild parameters of {path}: {e}")
    row = {"width": width, "height": height, "fmt": fmt, "has_params": int(bool(parameters)), "rebuilt": int(rebuilt),
           "has_workflow": int(bool(metadata.get("workflow")))}
    if parameters:
        p = parse_a1111(parameters)
        s = p["settings"]
        size = (s.get("size") or "").lower().replace(" ", "").split("x")
        sampler, scheduler = _sampler_and_scheduler(s.get("sampler"), s.get("schedule type"))
        clip = _num(s.get("clip skip"), int)
        found = LORA_TAG.findall(s.get("lora stack") or "") or LORA_TAG.findall(p["positive"] or "")
        lora_list = []
        for name, weight in dict.fromkeys(found):        # (name, weight) pairs, the same tag once
            lora_list.append([name.strip(), _num((weight or "1").split(":")[0]) or 1.0])
        model = (s.get("model") or "").replace("\\", "/").split("/")[-1]
        for ext in (".safetensors", ".ckpt", ".pt", ".pth", ".sft", ".gguf"):
            if model.lower().endswith(ext):
                model = model[: -len(ext)]
        row.update({
            "positive": p["positive"] or "", "negative": p["negative"] or "",
            "seed": _num(s.get("seed"), int), "steps": _num(s.get("steps"), int), "cfg": _num(s.get("cfg scale")),
            "clip_skip": -abs(clip) if clip else None, "sampler": sampler or s.get("sampler"), "scheduler": scheduler,
            "denoise": _num(s.get("denoising strength")),
            "gen_width": _num(size[0], int) if len(size) == 2 else None,
            "gen_height": _num(size[1], int) if len(size) == 2 else None,
            "model": model or None, "loras": json.dumps(lora_list, ensure_ascii=False),
        })
    return row


COLUMNS = ("width", "height", "fmt", "has_params", "rebuilt", "has_workflow", "positive", "negative", "seed", "steps",
           "cfg", "clip_skip", "sampler", "scheduler", "denoise", "gen_width", "gen_height", "model", "loras")


# ---- scanning ----------------------------------------------------------------------------------------------------
class Scanner:
    """Walks the roots in a background thread; one scan at a time. status() is what the page shows."""

    def __init__(self, index):
        self.index = index
        self._thread = None
        self._again = False
        self.added_total = 0
        self.changes = 0
        self.state = {"running": False, "root": "", "done": 0, "total": 0, "added": 0, "updated": 0, "removed": 0, "failed": 0,
                      "failed_files": [], "missing": [], "finished": None, "error": None}

    def status(self):
        return dict(self.state)

    def start(self):
        from .settings import gallery_enabled
        if not gallery_enabled():             # the gallery is turned off in the settings: nothing is indexed
            return
        if self._thread and self._thread.is_alive():
            self._again = True            # a change came in during the scan: scan once more afterwards
            return
        self._thread = threading.Thread(target=self._run, name="rigstools-gallery-scan", daemon=True)
        self._thread.start()

    def _run(self):
        while True:
            self._again = False
            try:
                self.scan()
            except Exception as e:
                logger.warning(f"gallery scan failed: {e}", exc_info=True)
                self.state["error"] = str(e)
            if not self._again:
                break
        self.state["running"] = False

    def scan(self):
        st = self.state
        st.update(running=True, done=0, total=0, added=0, updated=0, removed=0, failed=0, failed_files=[], missing=[], error=None)
        t0 = time.time()
        c = self.index.db()
        with self.index.lock:
            c.execute("DELETE FROM trash WHERE deleted < ?", (time.time() - TRASH_DAYS * 86400,))
            c.commit()
        for root in self.index.roots():
            rpath = root["path"]
            st["root"] = root["label"]
            if not os.path.isdir(rpath):          # unplugged drive, renamed folder: shown on the page, its pictures are kept
                st["missing"].append({"label": root["label"], "path": rpath})
                continue
            files = []
            for dirpath, dirnames, filenames in os.walk(rpath):
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                files += [os.path.join(dirpath, f) for f in filenames if is_image_file(f)]
            st["total"] += len(files)
            known = {r["path"]: (r["mtime"], r["size"]) for r in
                     c.execute("SELECT path, mtime, size FROM images WHERE root = ?", (rpath,))}
            seen = set()
            batch = []
            for f in files:
                st["done"] += 1
                key = norm(f)
                seen.add(key)
                try:
                    stt = os.stat(f)
                except OSError:
                    continue
                old = known.get(key)
                if old and abs((old[0] or 0) - stt.st_mtime) < 1e-6 and old[1] == stt.st_size:
                    continue
                try:
                    row = read_picture(f)
                except Exception as e:
                    logger.debug(f"gallery: skipping {f}: {e}")
                    st["failed"] += 1
                    if len(st["failed_files"]) < 5:
                        # PIL tries its plugins one by one, the last message ("No module named ...") says nothing useful
                        bad = isinstance(e, (ImportError, UnidentifiedImageError))   # the page shows a localised text for it
                        st["failed_files"].append({"file": f, "error": "" if bad else str(e)[:200], "code": "bad_file" if bad else ""})
                    continue
                folder = os.path.relpath(os.path.dirname(f), rpath).replace("\\", "/")
                batch.append((key, f, rpath, "" if folder == "." else folder, os.path.basename(f), stt.st_mtime,
                              stt.st_size, row, bool(old)))
                if len(batch) >= 200:
                    self._write(batch)
                    batch = []
            self._write(batch)
            gone = [k for k in known if k not in seen]
            if gone:
                with self.index.lock:
                    c.executemany("DELETE FROM images WHERE path = ?", [(k,) for k in gone])
                    c.commit()
                st["removed"] += len(gone)
        st["finished"] = time.time()
        # running totals of what the finished scans found. The counters above are of one scan and the next scan resets
        # them when it starts; the page asks the status every few seconds and may come between two scans or during
        # the next one (a run finished during a scan, or the page's own auto refresh) — the totals lose nothing
        self.added_total += st["added"]
        self.changes += st["added"] + st["updated"] + st["removed"]
        st["last"] = {"finished": st["finished"], "changes": self.changes, "added_total": self.added_total}
        logger.info(f"Gallery index: {st['done']} pictures checked, {st['added']} added, {st['updated']} updated, "
                    f"{st['removed']} removed, {st['failed']} unreadable ({time.time() - t0:.1f} s)")

    def _write(self, batch):
        if not batch:
            return
        c = self.index.db()
        with self.index.lock:
            for key, real, root, folder, name, mtime, size, row, existed in batch:
                vals = [row.get(k) for k in COLUMNS]
                if existed:
                    c.execute(f"UPDATE images SET real_path=?, folder=?, name=?, mtime=?, size=?, "
                              f"{', '.join(k + '=?' for k in COLUMNS)}, indexed=? WHERE path=?",
                              [real, folder, name, mtime, size, *vals, time.time(), key])
                    iid = c.execute("SELECT id FROM images WHERE path=?", (key,)).fetchone()[0]
                    c.execute("DELETE FROM image_loras WHERE image_id=?", (iid,))
                    self.state["updated"] += 1
                else:
                    cur = c.execute(f"INSERT INTO images(path, real_path, root, folder, name, mtime, size, "
                                    f"{', '.join(COLUMNS)}, indexed) VALUES ({', '.join('?' * (8 + len(COLUMNS)))})",
                                    [key, real, root, folder, name, mtime, size, *vals, time.time()])
                    iid = cur.lastrowid
                    self.state["added"] += 1
                    kept = c.execute("SELECT rating, tags FROM trash WHERE path = ?", (key,)).fetchone()
                    if kept:                      # restored from the recycle bin: its tags and rating come back
                        c.execute("UPDATE images SET rating = ? WHERE id = ?", (kept["rating"], iid))
                        for name in json.loads(kept["tags"] or "[]"):
                            _tag_ids(c, [name])
                            c.execute("INSERT OR IGNORE INTO image_tags SELECT ?, id FROM tags WHERE name = ?", (iid, name))
                        c.execute("DELETE FROM trash WHERE path = ?", (key,))
                for lname, w in json.loads(row.get("loras") or "[]"):
                    c.execute("INSERT INTO image_loras VALUES (?, ?, ?)", (iid, lname, w))
            c.commit()


# ---- queries -----------------------------------------------------------------------------------------------------
SORTS = {"date": "mtime DESC", "date_asc": "mtime ASC", "name": "name COLLATE NOCASE ASC",
         "rating": "rating DESC, mtime DESC"}


def _fts_query(text):
    """User words -> an FTS5 query: every word must be there, each as a prefix ("meadow sun" -> meadow* sun*)."""
    words = [w.replace('"', "") for w in text.replace(",", " ").split() if w.strip('"')]
    return " ".join(f'"{w}"*' for w in words)


def where(q):
    """SQL WHERE + args for the filters of a request (dict of lists)."""
    w, a = ["1=1"], []
    one = lambda k: (q.get(k) or [""])[0]
    # the folders shown: "loc" = "root<TAB>folder", several allowed (any of them); "root" + "folder" is the old form
    locs = [v.split("\t", 1) for v in q.get("loc", []) if v]
    if one("root"):
        locs.append([one("root"), one("folder")])
    parts = []
    for loc in locs:
        root, folder = loc[0], (loc[1] if len(loc) > 1 else "")
        if folder:
            parts.append("(root = ? AND (folder = ? OR folder LIKE ?))"); a += [norm(root), folder, folder + "/%"]
        else:
            parts.append("root = ?"); a.append(norm(root))
    if parts:
        w.append("(" + " OR ".join(parts) + ")")
    text = _fts_query(one("q"))
    if text:
        w.append("id IN (SELECT rowid FROM images_fts WHERE images_fts MATCH ?)"); a.append(text)
    for key, col in (("model", "model"), ("sampler", "sampler")):
        vals = [v for v in q.get(key, []) if v]
        if vals:
            w.append(f"{col} IN ({','.join('?' * len(vals))})"); a += vals
    loras = [v for v in q.get("lora", []) if v]
    if loras:
        w.append(f"id IN (SELECT image_id FROM image_loras WHERE lora IN ({','.join('?' * len(loras))}))"); a += loras
    tags = [v for v in q.get("tag", []) if v]
    if tags:
        sub = "SELECT image_id FROM image_tags JOIN tags ON tags.id = tag_id WHERE tags.name IN ({})".format(
            ",".join("?" * len(tags)))
        if one("tag_mode") == "all":
            sub += f" GROUP BY image_id HAVING COUNT(DISTINCT tag_id) = {len(tags)}"
        w.append(f"id IN ({sub})"); a += tags
    if one("rating"):
        w.append("rating >= ?"); a.append(int(one("rating")))
    if one("from"):
        w.append("mtime >= ?"); a.append(float(one("from")))
    if one("to"):
        w.append("mtime < ?"); a.append(float(one("to")))
    return " AND ".join(w), a


def image_row(r, tags=None):
    d = dict(r)
    d["loras"] = json.loads(d.get("loras") or "[]")
    for k in ("path", "real_path", "root", "indexed"):    # paths on disk stay on the server
        d.pop(k, None)
    d["tags"] = tags if tags is not None else []
    return d


def list_images(index, q, offset=0, limit=100):
    c = index.db()
    w, a = where(q)
    sort = SORTS.get((q.get("sort") or ["date"])[0], SORTS["date"])
    total = c.execute(f"SELECT COUNT(*) FROM images WHERE {w}", a).fetchone()[0]
    rows = c.execute(f"SELECT * FROM images WHERE {w} ORDER BY {sort} LIMIT ? OFFSET ?", [*a, limit, offset]).fetchall()
    ids = [r["id"] for r in rows]
    tags = {}
    if ids:
        for t in c.execute(f"SELECT image_id, name FROM image_tags JOIN tags ON tags.id = tag_id "
                           f"WHERE image_id IN ({','.join('?' * len(ids))}) ORDER BY name", ids):
            tags.setdefault(t["image_id"], []).append(t["name"])
    return {"total": total, "offset": offset, "items": [image_row(r, tags.get(r["id"], [])) for r in rows]}


def facets(index, q):
    """Values to filter by with their counts, within the folder and search of the request (not the other filters,
    so a picked value does not hide the rest of its list)."""
    c = index.db()
    base = {k: v for k, v in q.items() if k in ("root", "folder", "q")}
    w, a = where(base)
    out = {}
    for key, col in (("model", "model"), ("sampler", "sampler")):
        out[key] = [[r[0], r[1]] for r in c.execute(
            f"SELECT {col}, COUNT(*) n FROM images WHERE {w} AND {col} IS NOT NULL AND {col} != '' "
            f"GROUP BY {col} ORDER BY n DESC LIMIT 50", a)]
    out["lora"] = [[r[0], r[1]] for r in c.execute(
        f"SELECT lora, COUNT(DISTINCT image_id) n FROM image_loras WHERE image_id IN (SELECT id FROM images WHERE {w}) "
        f"GROUP BY lora ORDER BY n DESC LIMIT 50", a)]
    out["tag"] = [[r[0], r[1]] for r in c.execute(
        f"SELECT tags.name, COUNT(*) n FROM image_tags JOIN tags ON tags.id = tag_id "
        f"WHERE image_id IN (SELECT id FROM images WHERE {w}) GROUP BY tags.name ORDER BY n DESC", a)]
    return out


def folders(index):
    """[{root, label, builtin, count, children: {folder: count}}] — counts include subfolders."""
    c = index.db()
    out = []
    for root in index.roots():
        counts = {}
        total = 0
        for r in c.execute("SELECT folder, COUNT(*) n FROM images WHERE root = ? GROUP BY folder", (root["path"],)):
            total += r["n"]
            parts = r["folder"].split("/") if r["folder"] else []
            for i in range(1, len(parts) + 1):
                key = "/".join(parts[:i])
                counts[key] = counts.get(key, 0) + r["n"]
        out.append({**root, "count": total, "folders": sorted(counts.items())})
    return out


# ---- editing: rating, tags, deleting, moving ----------------------------------------------------------------------
def _tag_ids(c, names):
    for n in names:
        c.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (n,))
    return [r[0] for r in c.execute(f"SELECT id FROM tags WHERE name IN ({','.join('?' * len(names))})", names)] if names else []


def _clean_tags(names):
    return list(dict.fromkeys(n.strip()[:64] for n in names or [] if n and n.strip()))


def set_rating(index, ids, rating):
    rating = max(0, min(5, int(rating)))
    with index.lock:
        c = index.db()
        c.executemany("UPDATE images SET rating = ? WHERE id = ?", [(rating, i) for i in ids])
        c.commit()


def edit_tags(index, ids, add=(), remove=()):
    add, remove = _clean_tags(add), _clean_tags(remove)
    with index.lock:
        c = index.db()
        for tid in _tag_ids(c, add):
            c.executemany("INSERT OR IGNORE INTO image_tags VALUES (?, ?)", [(i, tid) for i in ids])
        if remove:
            c.execute(f"DELETE FROM image_tags WHERE image_id IN ({','.join('?' * len(ids))}) AND tag_id IN "
                      f"(SELECT id FROM tags WHERE name IN ({','.join('?' * len(remove))}))", [*ids, *remove])
        c.execute("DELETE FROM tags WHERE id NOT IN (SELECT tag_id FROM image_tags)")
        c.commit()


def all_tags(index):
    return [[r[0], r[1]] for r in index.db().execute(
        "SELECT name, COUNT(image_id) n FROM tags LEFT JOIN image_tags ON tag_id = tags.id GROUP BY tags.id ORDER BY name")]


def rename_tag(index, old, new):
    """Renames a tag everywhere; to a name that already exists = the two tags become one."""
    new = (_clean_tags([new]) or [None])[0]
    if not new:
        raise ValueError("empty")
    with index.lock:
        c = index.db()
        r = c.execute("SELECT id FROM tags WHERE name = ?", (old,)).fetchone()
        if not r:
            return
        other = c.execute("SELECT id FROM tags WHERE name = ? AND id != ?", (new, r[0])).fetchone()
        if other:
            c.execute("INSERT OR IGNORE INTO image_tags SELECT image_id, ? FROM image_tags WHERE tag_id = ?", (other[0], r[0]))
            c.execute("DELETE FROM image_tags WHERE tag_id = ?", (r[0],))
            c.execute("DELETE FROM tags WHERE id = ?", (r[0],))
        else:
            c.execute("UPDATE tags SET name = ? WHERE id = ?", (new, r[0]))
        c.commit()


def delete_tag(index, name):
    with index.lock:
        c = index.db()
        c.execute("DELETE FROM image_tags WHERE tag_id IN (SELECT id FROM tags WHERE name = ?)", (name,))
        c.execute("DELETE FROM tags WHERE name = ?", (name,))
        c.commit()


def delete_files(index, ids, permanent=False):
    """Moves the files to the recycle bin; their tags and rating are kept for TRASH_DAYS. -> (deleted, errors).
    permanent (Shift + Delete in the gallery): the files are deleted from the disk, past the bin, and their tags and
    rating go with them."""
    if not permanent:
        from send2trash import send2trash
    c = index.db()
    done, errors = [], []
    for i in ids:
        r = c.execute("SELECT * FROM images WHERE id = ?", (i,)).fetchone()
        if not r:
            continue
        try:
            if os.path.exists(r["real_path"]):
                if permanent:
                    os.remove(r["real_path"])
                else:
                    send2trash(r["real_path"])
        except Exception as e:
            errors.append([r["name"], str(e)])
            continue
        tags = [t[0] for t in c.execute("SELECT name FROM tags JOIN image_tags ON tag_id = id WHERE image_id = ?", (i,))]
        with index.lock:
            if (tags or r["rating"]) and not permanent:
                c.execute("INSERT OR REPLACE INTO trash VALUES (?, ?, ?, ?)",
                          (r["path"], r["rating"], json.dumps(tags, ensure_ascii=False), time.time()))
            c.execute("DELETE FROM images WHERE id = ?", (i,))
            c.commit()
        done.append(i)
    return done, errors


def _free_name(folder, name):
    """name, or name_1, name_2… when a file with that name is already in the folder (it is never overwritten)."""
    stem, ext = os.path.splitext(name)
    candidate, n = name, 0
    while os.path.exists(os.path.join(folder, candidate)):
        n += 1
        candidate = f"{stem}_{n}{ext}"
    return candidate


def move_files(index, ids, root, folder):
    """Moves pictures to a folder of a gallery root (made when missing); rows keep their id, tags and rating."""
    rpath = norm(root)
    if rpath not in {r["path"] for r in index.roots()}:
        raise ValueError("not_root")
    folder = (folder or "").replace("\\", "/").strip("/")
    dest = os.path.abspath(os.path.join(rpath, folder))
    if norm(dest) != rpath and not norm(dest).startswith(rpath + os.sep):
        raise ValueError("not_root")
    os.makedirs(dest, exist_ok=True)
    c = index.db()
    done, errors = [], []
    for i in ids:
        r = c.execute("SELECT * FROM images WHERE id = ?", (i,)).fetchone()
        if not r:
            continue
        if os.path.dirname(norm(r["real_path"])) == norm(dest):
            continue
        name = _free_name(dest, r["name"])
        target = os.path.join(dest, name)
        try:
            shutil.move(r["real_path"], target)
        except OSError as e:
            errors.append([r["name"], str(e)])
            continue
        rel = os.path.relpath(dest, rpath).replace("\\", "/")
        with index.lock:
            c.execute("UPDATE images SET path = ?, real_path = ?, root = ?, folder = ?, name = ?, mtime = ? WHERE id = ?",
                      (norm(target), target, rpath, "" if rel == "." else rel, name, os.stat(target).st_mtime, i))
            c.commit()
        done.append(i)
    return done, errors


def for_loader(index, image_id):
    """The picture as an image name the ComfyUI loaders take: a file of input or output is used where it is
    ("sub/name.png", "sub/name.png [output]"); a file elsewhere is copied to input/rigstools_gallery first."""
    r = index.db().execute("SELECT real_path, name FROM images WHERE id = ?", (image_id,)).fetchone()
    if not r or not os.path.exists(r["real_path"]):
        return None
    real = r["real_path"]
    for base, suffix in ((folder_paths.get_input_directory(), ""), (folder_paths.get_output_directory(), " [output]")):
        try:
            rel = os.path.relpath(real, base)
        except ValueError:                # another drive (Windows)
            continue
        if not rel.startswith(".."):
            return rel.replace("\\", "/") + suffix
    dest = os.path.join(folder_paths.get_input_directory(), "rigstools_gallery")
    os.makedirs(dest, exist_ok=True)
    target = os.path.join(dest, r["name"])
    if os.path.exists(target) and os.path.getsize(target) != os.path.getsize(real):
        target = os.path.join(dest, _free_name(dest, r["name"]))
    if not os.path.exists(target):
        shutil.copy2(real, target)
    return "rigstools_gallery/" + os.path.basename(target)


# ---- thumbnails --------------------------------------------------------------------------------------------------
def thumb(index, image_id, size):
    """Path of the cached WebP thumbnail (made on first request); None when the picture is gone."""
    r = index.db().execute("SELECT real_path, mtime FROM images WHERE id = ?", (image_id,)).fetchone()
    if not r or not os.path.exists(r["real_path"]):
        return None
    size = next((s for s in THUMB_SIZES if s >= size), THUMB_SIZES[-1])
    key = hashlib.sha1(f"{r['real_path']}|{r['mtime']}|{size}|cover".encode()).hexdigest()
    d = data_dir() / "thumbs" / key[:2]
    p = d / f"{key}.webp"
    if not p.exists():
        from PIL import Image, ImageOps
        d.mkdir(parents=True, exist_ok=True)
        with Image.open(r["real_path"]) as im:
            im = ImageOps.exif_transpose(im)
            # the short side gets `size` pixels, so the square the grid crops out stays sharp (never enlarged)
            k = size / min(im.size)
            if k < 1:
                im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
            tmp = p.with_suffix(".tmp")
            im.save(tmp, "WEBP", quality=90, method=4)
            os.replace(tmp, p)
    return p


_index = None
_scanner = None


def get():
    """The index and scanner of this ComfyUI (made on first use)."""
    global _index, _scanner
    if _index is None:
        _index = Index()
        _scanner = Scanner(_index)
    return _index, _scanner
