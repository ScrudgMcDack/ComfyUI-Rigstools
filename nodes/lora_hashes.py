import hashlib
import os
import re
from pathlib import PurePath

import folder_paths
import time

from ..core import CATEGORY, logger
from ..core.settings import debug

LORA_TAG = re.compile(r"<lora:([^>:]+)(?::([^>]+))?>", re.IGNORECASE)   # same pattern as Image Saver
EPOCH = re.compile(r"[-_](?:e|ep|epoch)?\d{1,6}$", re.IGNORECASE)          # "-000003", "_e10", "-ep05" at the end


def _lora_files():
    try:
        return list(folder_paths.get_filename_list("loras"))
    except Exception:
        return []


_index = {"key": None}


def _lora_index():
    """Lookup tables of models/loras, built once and again only when the file list changes."""
    files = _lora_files()
    key = hash(tuple(files))
    if _index["key"] != key:
        rel = {PurePath(f.replace("\\", "/")).with_suffix("").as_posix(): f for f in files}
        stems = {}
        for f in files:
            stems.setdefault(PurePath(f.replace("\\", "/")).stem, f)
        low_rel = {k.lower(): v for k, v in rel.items()}
        low_stem = {k.lower(): v for k, v in stems.items()}
        no_epoch = {}            # stem without the epoch -> the files with it
        for k, f in low_stem.items():
            base = EPOCH.sub("", k)
            if base != k:
                no_epoch.setdefault(base, []).append(f)
        _index.update(key=key, rel=rel, stems=stems, low_rel=low_rel, low_stem=low_stem, no_epoch=no_epoch)
    return _index


def find_lora(name: str):
    """Same matching as Image Saver (relative path without extension, then file stem), plus a case-insensitive
    fallback, plus the name without the epoch a trainer adds to the file (Style-000003, Style_e10, Style-ep05) —
    only when exactly one file fits, several epochs of one LoRA are not guessed. Returns the relative path or None."""
    ix = _lora_index()
    want = name.strip().replace("\\", "/")
    stem = PurePath(want).name
    for table, key in ((ix["rel"], want), (ix["stems"], stem)):
        if key in table:
            return table[key]
    found = ix["low_rel"].get(want.lower()) or ix["low_stem"].get(stem.lower())
    if found:
        return found
    fits = ix["no_epoch"].get(stem.lower(), [])
    return fits[0] if len(fits) == 1 else None


def peek_sha256(path: str):
    """The cached SHA-256 of a file, or None when there is no cache or it is older than the file
    (the file was replaced under the same name)."""
    cache = os.path.splitext(path)[0] + ".sha256"
    try:
        if os.path.getmtime(cache) + 1 < os.path.getmtime(path):
            return None
        with open(cache, "r", encoding="utf-8") as f:
            value = f.read().strip()
        return value.lower() if re.fullmatch(r"[0-9a-fA-F]{64}", value) else None
    except OSError:
        return None


def sha256_cached(path: str) -> str:
    """Full SHA-256 of a file, cached next to it in '<file>.sha256' — the same cache file Image Saver uses,
    so a file is hashed only once by either of them. A cache older than the file is recalculated."""
    cache = os.path.splitext(path)[0] + ".sha256"
    value = peek_sha256(path)
    if value:
        return value
    logger.info(f"Calculating sha256 for '{os.path.basename(path)}'")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    digest = h.hexdigest()
    try:
        with open(cache, "w", encoding="utf-8") as f:
            f.write(digest)
    except OSError as e:
        logger.warning(f"Could not write hash cache {cache}: {e}")
    return digest


class CLoraHashes:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "lora_stack": ("STRING", {"forceInput": True,
                                          "tooltip": "LoRA tags like '<lora:name:0.8> <lora:other:0.5>', "
                                                     "e.g. the LORA_STACK output of Parameters extractor"}),
            },
            "optional": {
                "with_weights": ("BOOLEAN", {"default": True,
                                             "tooltip": "Write 'Name:HASH:weight'. Image Saver accepts weights only when its "
                                                        "download_civitai_data is on — turn this off otherwise"}),
                "additional_hashes": ("STRING", {"forceInput": True,
                                                 "tooltip": "Optional hashes to keep: they are put before the LoRA hashes"}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    CATEGORY = CATEGORY.MAIN.value + CATEGORY.UTILS.value

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("ADDITIONAL_HASHES", "NOT_FOUND")

    DESCRIPTION = (
        "Turns a LoRA stack ('<lora:name:weight> …') into the additional_hashes string of Image Saver, so the "
        "LoRA are written to the image metadata and linked on Civitai without putting the LoRA tags into the "
        "prompt (the tags change what the text encoder sees).\n"
        "Each LoRA is found in models/loras and hashed with SHA-256 (first 10 characters, as Civitai expects). "
        "Hashes are cached in '<lora>.sha256' next to the file — the same cache Image Saver uses."
    )

    FUNCTION = "execute"

    def execute(self, lora_stack=None, with_weights=True, additional_hashes=None, unique_id=None):
        entries, not_found, seen = [], [], set()
        steps = []
        for name, rest in LORA_TAG.findall(lora_stack or ""):
            name = name.strip()
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            rel = find_lora(name)
            path = folder_paths.get_full_path("loras", rel) if rel else None
            if not path:
                not_found.append(name)
                continue
            try:
                cached = peek_sha256(path) is not None
                t0 = time.time()
                short = sha256_cached(path)[:10]
                steps.append(f"  {name}: {short}" + (" (from the cache)" if cached else
                             f" (calculated in {time.time() - t0:.1f} s, {os.path.getsize(path) / 2 ** 20:.0f} MB)"))
            except OSError as e:
                logger.warning(f"Could not hash LoRA '{name}': {e}")
                not_found.append(name)
                continue
            label = re.sub(r"[,:]", "_", PurePath(rel.replace("\\", "/")).stem)
            entry = f"{label}:{short}"
            if with_weights:
                try:
                    weight = float((rest or "1").split(":")[0])
                except ValueError:
                    weight = 1.0
                entry += f":{weight:g}"
            entries.append(entry)

        if not_found:
            logger.warning(f"LoRA not found in models/loras: {', '.join(not_found)}")
        debug("\n".join([f"LoRA hashes for Image Saver #{unique_id}: {len(seen)} LoRA in the stack"] + steps
                         + ([f"  not found in models/loras: {', '.join(not_found)}"] if not_found else [])
                         + (["  additional_hashes kept in front"] if (additional_hashes or "").strip(", ") else [])))
        prefix = (additional_hashes or "").strip().strip(",")
        result = ",".join(([prefix] if prefix else []) + entries)
        state = {"off": [] if result else ["ADDITIONAL_HASHES"], "warn": ["ADDITIONAL_HASHES"] if not_found else [],
                 "rebuilt": [], "reasons": {}}
        if not_found:
            state["reasons"]["ADDITIONAL_HASHES"] = {"code": "lorasMissing", "v": ", ".join(not_found)}
            if not result:
                state["off"] = ["ADDITIONAL_HASHES"]
        if entries:
            state["values"] = {"ADDITIONAL_HASHES": {"code": "count", "v": len(entries)}}
        return {"ui": {"rig_state": [state]}, "result": (result, ", ".join(not_found))}
