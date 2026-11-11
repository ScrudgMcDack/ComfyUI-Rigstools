"""
Civitai version ids of the models a picture was made with — for the "Civitai resources" block of Save image
(that block is where Civitai takes the LoRA weights from).

Where an id comes from, in this order:
  1. our own cache  <ComfyUI user folder>/rigstools/civitai.json  (key: the full SHA-256 of the file, so renaming or
     moving a model does not lose it);
  2. the files other tools keep next to the model: <name>.metadata.json of LoRA Manager (only when it stores its
     cards next to the models, its default), <name>.civitai.info of Image Saver / Civitai Helper;
  3. only with the "Rigstools → Civitai → look models up by hash" setting on: the public Civitai API
     GET https://civitai.com/api/v1/model-versions/by-hash/<SHA-256> (no API key). This tells Civitai which models
     you use, so it is off by default.
What 2 and 3 find goes into the cache. "Not on Civitai" is cached too and asked again after a week; a network error is
not cached (asked again after 10 minutes). Nothing is written into the model folders.
"""

import json
import os
import threading
import time
import urllib.error
import urllib.request

from . import logger
from .settings import setting_on, _user_dir

API = "https://civitai.com/api/v1/model-versions/by-hash/"
SETTING = "Rigstools.Civitai.Lookup"
NOT_FOUND_TTL = 7 * 24 * 3600
ERROR_PAUSE = 600
_lock = threading.Lock()
_cache = None
_cache_path = None
_errors = {}          # sha256 -> time of the last network error


def cache_path():
    return os.path.join(_user_dir(), "rigstools", "civitai.json")


def _load():
    global _cache, _cache_path
    path = cache_path()
    if _cache is None or _cache_path != path:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            _cache = data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            _cache = {}
        _cache_path = path
    return _cache


def _save():
    path = cache_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(_cache, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
    except OSError as e:
        logger.warning(f"Could not write the Civitai cache {path}: {e}")


def lookup_enabled():
    """Settings → Rigstools → Civitai → Lookup."""
    return setting_on(SETTING)


def from_api_answer(data, source):
    """The fields we keep from a Civitai model-version answer (also the content of .civitai.info / LoRA Manager)."""
    if not isinstance(data, dict) or not isinstance(data.get("id"), int) or data["id"] <= 0:
        return None
    model = data.get("model") if isinstance(data.get("model"), dict) else {}
    return {"modelVersionId": data["id"], "type": (model.get("type") or "").lower() or None,
            "modelName": model.get("name"), "modelVersionName": data.get("name"),
            "air": data.get("air") if isinstance(data.get("air"), str) else None, "source": source}


def cached(sha256):
    """The cached entry: {"modelVersionId", …, "source"} | {"missing": True, …} | None (never asked)."""
    if not sha256:
        return None
    with _lock:
        e = _load().get(sha256.lower())
    if e and e.get("missing") and time.time() - e.get("checked", 0) > NOT_FOUND_TTL:
        return None           # "not on Civitai" was a week ago: ask again
    return e


def remember(sha256, entry):
    if not sha256 or not entry:
        return
    with _lock:
        cache = _load()
        new = dict(entry, checked=int(time.time()))
        old = cache.get(sha256.lower())
        if old and {k: v for k, v in old.items() if k != "checked"} == {k: v for k, v in new.items() if k != "checked"}:
            return
        cache[sha256.lower()] = new
        _save()


def ask_civitai(sha256, timeout=6.0):
    """One API request. Returns the entry, {"missing": True} when Civitai does not know the file, None on an error."""
    if time.time() - _errors.get(sha256, 0) < ERROR_PAUSE:
        return None
    req = urllib.request.Request(API + sha256.upper(), headers={"User-Agent": "ComfyUI-Rigstools",
                                                                "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            entry = from_api_answer(json.loads(r.read().decode("utf-8")), "civitai")
            return entry or {"missing": True, "source": "civitai"}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"missing": True, "source": "civitai"}
        logger.debug(f"Civitai lookup {sha256[:10]}: HTTP {e.code}")
    except Exception as e:     # offline, timeout, proxy…
        logger.debug(f"Civitai lookup {sha256[:10]}: {e}")
    _errors[sha256] = time.time()
    return None


def version_id(sha256, sidecar=None, online=False, timeout=6.0):
    """The Civitai entry of a file. sidecar: what the files next to it say (from_api_answer format) or None."""
    e = cached(sha256)
    if e and not e.get("missing"):
        return e
    if sidecar and sidecar.get("modelVersionId"):
        remember(sha256, sidecar)
        return sidecar
    if e:                     # known as "not on Civitai"
        return None
    if online and sha256:
        e = ask_civitai(sha256, timeout)
        if e is not None:
            remember(sha256, e)
            return None if e.get("missing") else e
    return None
