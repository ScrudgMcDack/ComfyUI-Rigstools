import fnmatch
import hashlib
import os
import re
import uuid
from pathlib import Path

import numpy as np
import torch
from PIL import ImageOps

import folder_paths

from ..core import CATEGORY, logger
from ..core.image_meta import read_metadata, summary, is_image_file
from ..core.prompt_graph import parameters_from_prompt as rebuild_parameters
from ..core.settings import debug

OUTPUT_SUFFIX = " [output]"
SKIP_DIRS = ("clipspace", ".*", "__pycache__")
SKIP_FILES = ("Thumbs.db", "*.DS_Store", "desktop.ini", "*.lock", "*.sha256")


# ---------------------------------------------------------------- files

def _walk(root, recursive=True):
    """(relative posix path, absolute path, mtime) of the image files under root."""
    found = []
    if not os.path.isdir(root):
        return found
    for base, dirs, files in os.walk(root, followlinks=True):
        dirs[:] = sorted(d for d in dirs if not any(fnmatch.fnmatch(d, p) for p in SKIP_DIRS))
        for name in files:
            if not is_image_file(name) or any(fnmatch.fnmatch(name, p) for p in SKIP_FILES):
                continue
            full = os.path.join(base, name)
            try:
                mtime = os.path.getmtime(full)
            except OSError:
                continue
            found.append((os.path.relpath(full, root).replace("\\", "/"), full, mtime))
        if not recursive:
            break
    return found


def _natural(text):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", text)]


def _roots():
    return {
        "input": folder_paths.get_input_directory(),
        "output": folder_paths.get_output_directory(),
        "temp": folder_paths.get_temp_directory(),
    }


def _ui_ref(path):
    """{"filename", "subfolder", "type"} when the file is inside input / output / temp, else None."""
    full = os.path.abspath(path)
    for kind, root in _roots().items():
        root = os.path.abspath(root)
        try:
            if os.path.commonpath([root, full]) == root:
                rel = os.path.relpath(full, root).replace("\\", "/")
                sub, _, name = rel.rpartition("/")
                return {"filename": name, "subfolder": sub, "type": kind}
        except ValueError:  # different drives on Windows
            continue
    return None


def resolve_folder(text):
    """'output', 'output/STEP_1', 'input/x', 'temp' or an absolute path. A plain relative path is under output."""
    t = (text or "").strip().strip('"').strip("'").replace("\\", "/") or "output"
    if os.path.isabs(t) or re.match(r"^[A-Za-z]:/", t):
        return os.path.normpath(t)
    head, _, rest = t.partition("/")
    roots = _roots()
    if head.lower() in roots:
        return os.path.normpath(os.path.join(roots[head.lower()], rest))
    return os.path.normpath(os.path.join(roots["output"], t))


def list_folder(folder, pattern="*", subfolders=False, sort="name"):
    root = resolve_folder(folder)
    patterns = [p.strip() for p in re.split(r"[;,]", pattern or "*") if p.strip()] or ["*"]
    files = [f for f in _walk(root, subfolders)
             if any(fnmatch.fnmatch(os.path.basename(f[0]).lower(), p.lower()) for p in patterns)]
    if sort == "date modified":
        files.sort(key=lambda f: (f[2], _natural(f[0])))
    else:
        files.sort(key=lambda f: _natural(f[0]))
    return root, files


# ---------------------------------------------------------------- loading

def _to_tensors(img):
    img = ImageOps.exif_transpose(img)
    if img.mode == "I":
        img = img.point(lambda v: v * (1 / 255))
    rgb = img.convert("RGB")
    image = torch.from_numpy(np.array(rgb).astype(np.float32) / 255.0)[None,]
    if "A" in img.getbands():
        mask = 1. - torch.from_numpy(np.array(img.getchannel("A")).astype(np.float32) / 255.0)
    elif img.mode == "P" and "transparency" in img.info:
        mask = 1. - torch.from_numpy(np.array(img.convert("RGBA").getchannel("A")).astype(np.float32) / 255.0)
    else:
        mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
    return image, mask.unsqueeze(0)


def load(path):
    img, metadata = read_metadata(path)
    try:
        image, mask = _to_tensors(img)
    finally:
        img.close()

    parameters = metadata.get("parameters") or ""
    rebuilt = False
    if not parameters and isinstance(metadata.get("prompt"), dict) and metadata["prompt"]:
        try:
            parameters = rebuild_parameters(metadata["prompt"]) or ""
            rebuilt = bool(parameters)
        except Exception as e:
            logger.warning(f"Could not rebuild parameters from the prompt: {e}")

    info = summary(metadata)
    info["rebuilt"] = rebuilt
    if rebuilt:
        info["preview"] = parameters[:600]
    p = Path(path)
    return image, mask, metadata, parameters, p.name, p.stem, info


def metadata_lines(info, rebuild=True):
    """What the metadata of a picture holds, as log lines (Settings → Rigstools → Debug)."""
    found = [k for k in ("parameters", "prompt", "workflow") if info.get(k)]
    lines = ["  found: " + ", ".join(found) if found else "  no metadata in the file"]
    if info.get("parameters"):
        lines.append("  the parameters block is found")
    elif info.get("prompt") and rebuild:
        lines.append("  no parameters block, rebuilding the generation parameters from the prompt block")
        lines.append("  rebuilt from the prompt block" if info.get("rebuilt") else
                     "  could not rebuild them from the prompt block")
    elif info.get("prompt"):
        lines.append("  no parameters block; rebuilding from the prompt block is off")
    else:
        lines.append("  no parameters and no prompt block: the generation parameters cannot be determined")
    return lines


def file_line(title, name, info):
    size = ", ".join(x for x in (info.get("resolution"), info.get("format"), info.get("size")) if x)
    return f"{title}: loading {name}" + (f" ({size})" if size else "")


def file_hash(path):
    m = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            m.update(chunk)
    return m.hexdigest()




# ---------------------------------------------------------------- nodes

class CLoadImageMeta:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        inputs = sorted((f[0] for f in _walk(input_dir)), key=_natural)
        outputs = [f[0] + OUTPUT_SUFFIX for f in
                   sorted(_walk(folder_paths.get_output_directory()), key=lambda f: -f[2])]
        return {
            "required": {
                "image": (inputs + outputs, {
                    "image_upload": True,
                    "tooltip": "Files of the input folder",
                }),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    CATEGORY = CATEGORY.MAIN.value + CATEGORY.IMAGE.value
    RETURN_TYPES = ("IMAGE", "MASK", "METADATA_RAW", "STRING", "STRING")
    RETURN_NAMES = ("IMAGE", "MASK", "METADATA_RAW", "PARAMETERS", "FILENAME")
    DESCRIPTION = (
        "Loads an image together with its generation data. Reads PNG text chunks and the EXIF of JPEG / WebP "
        "(Image Saver, A1111 / Forge, stock Save Animated WEBP), so parameters, prompt and workflow come out "
        "of every format Image Saver writes.\n"
        "METADATA_RAW has the same format as in \"Load image with metadata\" (Crystools) — a drop-in replacement.\n"
        "Files can be taken from the input folder or straight from the output folder. The caption under the image "
        "says which data the file has, dimmed outputs carry nothing, ↻ — parameters rebuilt from the prompt; "
        "the ⓘ button in the title shows the full parameters and copies them."
    )
    FUNCTION = "execute"

    def execute(self, image, unique_id=None):
        path = folder_paths.get_annotated_filepath(image)
        image_t, mask, metadata, parameters, name, stem, info = load(path)
        info["name"] = image
        info["file"] = name
        debug("\n".join([file_line(f"Load image with metadata #{unique_id}", image, info)] + metadata_lines(info)))
        return {"ui": {"rig_meta": [info]}, "result": (image_t, mask, metadata, parameters, name)}

    @classmethod
    def IS_CHANGED(cls, image, **_):
        return file_hash(folder_paths.get_annotated_filepath(image))

    @classmethod
    def VALIDATE_INPUTS(cls, image, **_):
        if not folder_paths.exists_annotated_filepath(image):
            return f"Invalid image file: {image}"
        return True


class CLoadImageFolder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder": ("STRING", {
                    "default": "output",
                    "tooltip": "output, output/STEP_1, input/…, temp, or an absolute path. "
                               "A plain relative path is taken inside the output folder",
                }),
                "mode": (["by index", "latest"], {
                    "tooltip": "by index — the file number <index> in the sorted list (wraps around, so "
                               "'increment' walks through the folder in a loop); latest — the newest file",
                }),
                "index": ("INT", {
                    "default": 0, "min": 0, "max": 0xffffffff, "step": 1,
                    "control_after_generate": "increment",
                    "tooltip": "Number of the file in the sorted list, from 0. Use 'increment' to process "
                               "a folder one file per run",
                }),
                "pattern": ("STRING", {
                    "default": "*",
                    "tooltip": "File name filter, several separated by ; — e.g. STEP_1_*.png; *.webp",
                }),
                "sort": (["name", "date modified"], {
                    "tooltip": "Order for 'by index'. Names are compared naturally (2 before 10)",
                }),
                "subfolders": ("BOOLEAN", {"default": False, "tooltip": "Include files of the subfolders"}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    CATEGORY = CATEGORY.MAIN.value + CATEGORY.IMAGE.value
    RETURN_TYPES = ("IMAGE", "MASK", "METADATA_RAW", "STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("IMAGE", "MASK", "METADATA_RAW", "PARAMETERS", "FILENAME", "INDEX", "COUNT")
    DESCRIPTION = (
        "Loads one image with its generation data from a folder: by index (with 'increment' — one file per "
        "run, to process a whole folder) or the newest file. Outputs are the same as in "
        "\"Load image with metadata\" plus INDEX and COUNT.\n"
        "Tip: in 'latest' mode, don't save into the same folder from the same workflow, or the next run "
        "picks up its own result."
    )
    FUNCTION = "execute"

    @staticmethod
    def _pick(folder, mode, index, pattern, sort, subfolders):
        root, files = list_folder(folder, pattern, subfolders, sort)
        if not files:
            raise FileNotFoundError(f"No images in {root} matching '{pattern}'")
        if mode == "latest":
            pos = max(range(len(files)), key=lambda i: files[i][2])
        else:
            pos = index % len(files)
        return files[pos], pos, len(files)

    def execute(self, folder, mode, index, pattern, sort, subfolders, unique_id=None):
        (rel, path, _), pos, count = self._pick(folder, mode, index, pattern, sort, subfolders)
        image_t, mask, metadata, parameters, name, stem, info = load(path)
        debug("\n".join([f"Load image from folder #{unique_id}: {count} file(s) in {folder} matching '{pattern}'"
                          + (", subfolders included" if subfolders else "")
                          + (", taking the newest" if mode == "latest" else f", taking #{pos + 1} (index {index})"),
                          file_line("  ", rel, info).replace("  : ", "  ")] + metadata_lines(info)))
        info["file"] = Path(path).name
        info["position"] = f"{pos + 1} / {count}"

        ref = _ui_ref(path)
        if ref:
            sub = f"{ref['subfolder']}/" if ref["subfolder"] else ""
            info["name"] = f"{sub}{ref['filename']} [{ref['type']}]"
        if ref is None:  # outside ComfyUI folders: write a small preview into temp
            try:
                from PIL import Image
                with Image.open(path) as im:
                    im = ImageOps.exif_transpose(im)
                    im.thumbnail((1024, 1024))
                    temp = folder_paths.get_temp_directory()
                    os.makedirs(temp, exist_ok=True)
                    fname = f"rigstools_{uuid.uuid4().hex[:10]}.png"
                    im.save(os.path.join(temp, fname), compress_level=1)
                    ref = {"filename": fname, "subfolder": "", "type": "temp"}
            except Exception as e:
                logger.debug(f"preview: {e}")
        ui = {"rig_meta": [info]}
        if ref:
            ui["images"] = [ref]
        return {"ui": ui, "result": (image_t, mask, metadata, parameters, name, pos, count)}

    @classmethod
    def IS_CHANGED(cls, folder, mode, index, pattern, sort, subfolders, **_):
        try:
            (rel, path, mtime), pos, count = cls._pick(folder, mode, index, pattern, sort, subfolders)
            return f"{path}|{mtime}|{pos}|{count}"
        except Exception as e:
            return str(e)


# ---------------------------------------------------------------- badge data for the loader

def _json_safe(value):
    """NaN / Infinity (they occur in saved workflows) are not valid JSON for the browser — send them as null."""
    if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
        return None
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def register_routes():
    try:
        from aiohttp import web
        from server import PromptServer
    except Exception:
        return

    def work(name, full):
        """(body, status) for the node — runs in a worker thread, so reading the file does not hold up the server."""
        try:
            if not name or not folder_paths.exists_annotated_filepath(name):
                return {"error": "not found"}, 404
            path = folder_paths.get_annotated_filepath(name)
            if _ui_ref(path) is None:
                return {"error": "outside of ComfyUI folders"}, 403
            img, metadata = read_metadata(path)
            img.close()
            info = summary(metadata)
            info["name"] = name
            info["file"] = Path(path).name
            info["rebuilt"] = False
            text = metadata.get("parameters") or ""
            if not text and info["prompt"]:
                try:
                    text = rebuild_parameters(metadata["prompt"]) or ""
                    if text:
                        info["rebuilt"] = True
                        info["preview"] = text[:600]
                except Exception:
                    text = ""
            if full:
                info["text"] = text
                info["prompt_json"] = metadata.get("prompt") if info["prompt"] else None
                info["workflow_json"] = metadata.get("workflow") if info["workflow"] else None
            return _json_safe(info), 200
        except Exception as e:
            logger.warning(f"image_meta failed for {name!r}: {e}", exc_info=True)
            return {"error": str(e)}, 500

    @PromptServer.instance.routes.get("/rigstools/image_meta")
    async def image_meta(request):
        """Summary for the node (?filename=<annotated name>); with &full=1 also the full texts for the info dialog."""
        import asyncio
        body, status = await asyncio.get_running_loop().run_in_executor(
            None, work, request.query.get("filename", ""), request.query.get("full") == "1")
        return web.json_response(body, status=status)

register_routes()
