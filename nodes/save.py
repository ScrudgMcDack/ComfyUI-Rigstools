import json
import os
import re
import time
from datetime import datetime
from pathlib import PurePath

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import folder_paths
from ..core import CATEGORY, logger
from ..core.settings import debug_enabled
from ..core.runtime import Outputs   # imported on load: it hooks the executor ComfyUI creates later
from ..core.save_meta import collect, a1111_text, render_name, clean_part, model_stem
from .lora_hashes import find_lora, sha256_cached, peek_sha256
from .parameters import find_checkpoint

FORMATS = ["png", "jpeg", "webp"]
METADATA = ["all", "parameters only", "none"]
JPEG_EXIF_LIMIT = 65533          # the APP1 segment holds 64 KB minus its own header
IMAGE_EXT = re.compile(r"\.(png|jpe?g|webp)$", re.IGNORECASE)
TAG_MAKE, TAG_MODEL, EXIF_IFD, TAG_USER_COMMENT = 0x010F, 0x0110, 0x8769, 0x9286


# ---------------------------------------------------------------- model files and hashes

def model_path(name):
    """Full path of a checkpoint / diffusion model named in the graph, or None."""
    if not name:
        return None
    value, found = find_checkpoint(str(name))
    if found:
        return folder_paths.get_full_path("checkpoints", value)
    for folder in ("diffusion_models", "unet"):
        try:
            files = folder_paths.get_filename_list(folder)
        except Exception:
            continue
        want = str(name).replace("\\", "/").lower()
        for f in files:
            n = f.replace("\\", "/").lower()
            if n == want or PurePath(n).name == PurePath(want).name or PurePath(n).stem == PurePath(want).stem:
                return folder_paths.get_full_path(folder, f)
    return None


def embedding_path(name):
    try:
        files = folder_paths.get_filename_list("embeddings")
    except Exception:
        return None
    for f in files:
        if model_stem(f).lower() == name.lower():
            return folder_paths.get_full_path("embeddings", f)
    return None


def resolve_files(info):
    """Adds the files behind the model, LoRA and embeddings: [(kind, name, path or None)]."""
    items = []
    model = info["fields"]["model"]["v"]
    if model:
        items.append(("model", model_stem(model), model_path(model)))
    for lora in info["loras"]:
        rel = find_lora(lora["name"])
        items.append(("lora", lora["name"], folder_paths.get_full_path("loras", rel) if rel else None))
    for emb in info["embeddings"]:
        items.append(("embedding", emb, embedding_path(emb)))
    return items


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def sidecar_info(path):
    """What other tools keep next to a model file:
      <name>.metadata.json — LoRA Manager: sha256, size, and the Civitai API answer in "civitai";
      <name>.civitai.info  — Image Saver, Civitai Helper: the Civitai API answer itself.
    Returns {"modelVersionId", "type", "modelName", "modelVersionName", "air", "sha256", "source"}; the id is None
    when the model is not known on Civitai."""
    base = os.path.splitext(path)[0]
    out = {"modelVersionId": None, "sha256": None, "source": None}
    lm = _read_json(base + ".metadata.json")
    if lm:
        try:
            if isinstance(lm.get("sha256"), str) and int(lm.get("size") or -1) == os.path.getsize(path):
                out["sha256"] = lm["sha256"].lower()      # LoRA Manager already hashed it
        except (OSError, ValueError, TypeError):
            pass
    for data, source in ((lm and lm.get("civitai"), ".metadata.json"), (_read_json(base + ".civitai.info"), ".civitai.info")):
        if isinstance(data, dict) and isinstance(data.get("id"), int) and data["id"] > 0:
            model = data.get("model") if isinstance(data.get("model"), dict) else {}
            out.update({"modelVersionId": data["id"], "type": (model.get("type") or "").lower() or None,
                        "modelName": model.get("name"), "modelVersionName": data.get("name"),
                        "air": data.get("air") if isinstance(data.get("air"), str) else None, "source": source})
            break
    return out


EMBED_WEIGHT = re.compile(r"\(\s*embedding:([^,\s()\[\]:]+)\s*:\s*([-+]?\d*\.?\d+)\s*\)", re.IGNORECASE)


def civitai_resources(info, items, shas, online=False, budget=8.0):
    """The "Civitai resources" block: every model, LoRA and embedding whose Civitai version id is known (our cache,
    the files next to it, or — with the setting on — the Civitai API), with the LoRA weights: that is where Civitai
    takes the weights from. shas: {(kind, name): full SHA-256}. budget: seconds for all API requests together.
    Plus status lines."""
    from ..core import civitai
    deadline = time.time() + budget
    weights = {l["name"]: l["weight"] for l in info["loras"]}
    texts = " ".join(v["v"] for k, v in info["fields"].items() if k in ("positive", "negative") and isinstance(v["v"], str))
    emb_w = {model_stem(m[0]).lower(): float(m[1]) for m in EMBED_WEIGHT.findall(texts)}
    res, without, sources = [], [], {}
    for kind, name, path in items:
        if not path:
            continue
        side = sidecar_info(path)
        sha = shas.get((kind, name)) or side.get("sha256")
        left = deadline - time.time()
        found = civitai.version_id(sha, side if side["modelVersionId"] else None, online=online and left > 0.5,
                                   timeout=max(0.5, min(6.0, left)))
        if not found and side["modelVersionId"]:
            found = side                               # no hash yet: the card next to the file is enough
        if not found:
            without.append(name)
            continue
        side = found
        sources[side.get("source") or "cache"] = sources.get(side.get("source") or "cache", 0) + 1
        r = {"_kind": kind, "_name": name}
        if side.get("modelName"):
            r["modelName"] = side["modelName"]
        if side.get("modelVersionName"):
            r["modelVersionName"] = side["modelVersionName"]
        r["modelVersionId"] = side["modelVersionId"]
        r["type"] = side.get("type") or {"model": "checkpoint", "lora": "lora", "embedding": "textualinversion"}[kind]
        if kind == "lora":
            r["weight"] = float(weights.get(name, 1.0))
        elif kind == "embedding":
            r["weight"] = emb_w.get(name.lower(), 1.0)
        if side.get("air"):
            r["air"] = side["air"]
        res.append(r)
    status = []
    if res:
        status.append({"kind": "ok", "code": "civitaiIds", "v": len(res), "n": len(res) + len(without),
                       "src": sources})
    if without:
        status.append({"kind": "muted", "code": "noCivitaiIdOnline" if online else "noCivitaiId", "v": ", ".join(without)})
    return res, status


def hash_files(items, compute):
    """{kind: …} of the 10-character hashes plus status lines. compute=False only looks into the caches."""
    hashes = {"model": None, "loras": {}, "embeddings": {}, "full": {}}
    status = []
    for kind, name, path in items:
        if not path:
            status.append({"kind": "warn", "code": f"{kind}Missing", "v": name})
            continue
        h = peek_sha256(path) or sidecar_info(path)["sha256"]
        if h is None:
            if not compute:
                status.append({"kind": "info", "code": "willHash", "v": name})
                continue
            t0 = time.time()
            h = sha256_cached(path)
            status.append({"kind": "info", "code": "hashed", "v": name,
                           "size": round(os.path.getsize(path) / 2 ** 20), "sec": round(time.time() - t0, 1)})
        hashes["full"][(kind, name)] = h
        if kind == "model":
            hashes["model"] = h[:10]
        else:
            hashes["loras" if kind == "lora" else "embeddings"][name] = h[:10]
    return hashes, status


# ---------------------------------------------------------------- values that our loaders read from a file

OUR_LOADERS = ("Load image with metadata [Rigstools]", "Load image with parameters [Rigstools]")
FILE_LOADERS = OUR_LOADERS + ("Load image with metadata [Crystools]",)
EXTRACTOR_KEYS = {"SEED": "seed", "STEPS": "steps", "CFG": "cfg", "CLIP": "clip_skip", "WIDTH": "width",
                  "HEIGHT": "height", "POSITIVE": "positive", "NEGATIVE": "negative", "MODEL_NAME": "model",
                  "LORA_STACK": "lora_stack", "SAMPLER": "sampler", "SCHEDULER": "scheduler"}
_file_cache = {}


def _file_parameters(image, rebuild=True):
    """Parameters text of an input / output picture (rebuilt from its ComfyUI prompt when it has none)."""
    from ..core.image_meta import read_metadata
    from ..core.prompt_graph import parameters_from_prompt
    try:
        path = folder_paths.get_annotated_filepath(image)
        key = (path, os.path.getmtime(path), rebuild)
    except Exception:
        return None
    if key not in _file_cache:
        try:
            img, meta = read_metadata(path)
            img.close()
            text = meta.get("parameters") or ""
            if not text and rebuild and isinstance(meta.get("prompt"), dict):
                text = parameters_from_prompt(meta["prompt"]) or ""
        except Exception:
            text = None
        if len(_file_cache) > 64:
            _file_cache.clear()
        _file_cache[key] = text
    return _file_cache[key]


def _params_behind(r, link):
    """Parameters text that reaches a PARAMETERS input through our loaders / Metadata extractor, or None."""
    from ..core.prompt_graph import _is_link
    n = r.node(r.through_switch(link)) if _is_link(link) else None
    if not n:
        return None
    ct, ins = n.get("class_type", ""), n.get("inputs", {})
    if ct in OUR_LOADERS and isinstance(ins.get("image"), str):
        return _file_parameters(ins["image"])
    if ct == "Metadata extractor [Rigstools]":
        src = r.node(r.through_switch(ins.get("metadata_raw"))) if _is_link(ins.get("metadata_raw")) else None
        if src and src.get("class_type") in FILE_LOADERS and isinstance(src["inputs"].get("image"), str):
            return _file_parameters(src["inputs"]["image"], rebuild=ins.get("parameters_from_prompt", True) is not False)
    return None


def file_values(r, n, slot):
    """External values for the graph walk: outputs of Parameters extractor / Load image with parameters."""
    from ..core.prompt_graph import SKIP
    from .parameters import CParamExtractor, extract_values
    from .image_params import CLoadImageParams, _overrides_for, read_values
    ct, ins = n.get("class_type", ""), n.get("inputs", {})
    try:
        if ct == "Parameters extractor [Rigstools]":
            name = CParamExtractor.RETURN_NAMES[slot]
            text = _params_behind(r, ins.get("parameters"))
            if text is None or name not in EXTRACTOR_KEYS:
                return None
            fb = {k[9:]: v for k, v in ins.items() if k.startswith("fallback_") and not isinstance(v, list)}
            return extract_values(text, fb).get(EXTRACTOR_KEYS[name])
        if ct == "Load image with parameters [Rigstools]" and isinstance(ins.get("image"), str):
            name = CLoadImageParams.RETURN_NAMES[slot]
            if name not in EXTRACTOR_KEYS:
                return None
            values = read_values(ins["image"], _overrides_for(ins["image"], ins.get("values")), with_image=False)[6]
            return values.get(EXTRACTOR_KEYS[name])
    except Exception as e:
        logger.debug(f"file values of {ct}: {e}")
        return None
    return SKIP


IMAGE_KEYS = ("pixels", "image", "images", "IMAGE", "samples", "upscaled_image")
_size_cache = {}


def _file_size(image):
    try:
        path = folder_paths.get_annotated_filepath(image)
        key = (path, os.path.getmtime(path))
    except Exception:
        return None
    if key not in _size_cache:
        try:
            with Image.open(path) as im:
                _size_cache[key] = im.size
        except Exception:
            _size_cache[key] = None
    return _size_cache[key]


def image_source(r, link):
    """Where a picture comes from, walking up the image nodes to a file loader: {"size": (w, h) of the picture at
    that point (the file size, or the size a resize node with fixed numbers gives), "from_file": the size is the
    file's, "values": generation data of the file (extract_values) or None, "file": its name}."""
    from ..core.prompt_graph import _is_link
    from .parameters import extract_values
    size, resized = None, False
    for _ in range(40):
        if not _is_link(link):
            break
        link = r.through_switch(link)
        n = r.node(link)
        if not n:
            break
        ct, ins = n.get("class_type", ""), n.get("inputs", {})
        if isinstance(ins.get("image"), str) and (ct in FILE_LOADERS or "loadimage" in ct.lower().replace(" ", "")):
            text = _file_parameters(ins["image"])
            values = extract_values(text) if text else None
            fsize = _file_size(ins["image"])
            return {"size": size if resized else fsize, "from_file": not resized, "values": values,
                    "file": PurePath(ins["image"].replace("\\", "/")).name}
        if not resized:
            w, h = r.value(ins.get("width")), r.value(ins.get("height"))
            if isinstance(w, int) and isinstance(h, int) and w > 0 and h > 0:
                size, resized = (w, h), True
            elif any(k in ct.lower() for k in ("upscale", "scale", "resize", "crop")):
                resized = True                       # the size changes here and is not known
        link = next((ins[k] for k in IMAGE_KEYS if _is_link(ins.get(k))), None)
    return {"size": size, "from_file": False, "values": None, "file": None}


RESIZE_WORDS = ("upscale", "scale", "resize", "crop", "pad", "rescale")


def size_may_change(prompt, node_id, info):
    """True when the saved picture may get another size than the one known before the run: the base size is not
    known, or a node after the base pass changes the size (upscale, resize, crop…)."""
    from ..core.save_meta import _ancestors
    f = info["fields"]
    if not (isinstance(f["width"]["v"], int) and isinstance(f["height"]["v"], int)):
        return True
    save = prompt.get(str(node_id)) or {}
    after = set(_ancestors(prompt, save.get("inputs", {}).get("images")))
    if info.get("base_id"):
        after -= set(_ancestors(prompt, [info["base_id"], 0]))
    return any(any(w in prompt[n].get("class_type", "").lower() for w in RESIZE_WORDS) for n in after if n in prompt)


def has_values(info):
    return bool(info.get("base_id")) or any(v["src"] != "missing" for v in info["fields"].values())


def blocks(metadata, fmt, workflow_json, params):
    """What goes into the file: A1111 parameters, the ComfyUI workflow and the API prompt (as the stock Save Image
    writes them), plus the .json next to it."""
    embed = metadata == "all"
    return [{"key": "parameters", "on": metadata != "none" and bool(params.strip())},
            {"key": "workflow", "on": embed, "limit": fmt == "jpeg"},
            {"key": "prompt", "on": embed, "limit": fmt == "jpeg"},
            {"key": "workflow_json", "on": bool(workflow_json)}]


def sampler_status(info):
    """The status line when no sampler was found above the picture (None when the values come from inputs)."""
    if info.get("base_id"):
        return None
    if info.get("source_file"):
        return {"kind": "info", "code": "fromFile", "v": info["source_file"]}
    if any(v["src"] != "missing" for v in info["fields"].values()):
        return None
    return {"kind": "warn", "code": "noSampler"}


# ---------------------------------------------------------------- files

def output_folder(path_text, values, now):
    root = os.path.realpath(folder_paths.get_output_directory())
    sub = clean_part(render_name(path_text, values, now, counter=0).replace("\0", ""))
    folder = os.path.realpath(os.path.join(root, sub))
    if os.path.commonpath([root, folder]) != root:
        raise ValueError(f"The path '{path_text}' leads outside the output folder")
    return root, folder


PLACEHOLDER = re.compile("\x01([a-z]+)\x01")


def _rx(text):
    """Regex text for a name part; a value known only when saving matches anything."""
    return ".+?".join(re.escape(p) for p in PLACEHOLDER.split(text)[::2])


def shown_name(name):
    """The name for the panel: placeholders as [width], [time]…"""
    return PLACEHOLDER.sub(lambda m: f"[{m.group(1)}]", name)


def _counter_regex(pre, post):
    return re.compile("^" + _rx(pre) + r"(\d+)" + _rx(post) + r"\.(png|jpe?g|webp)$", re.IGNORECASE)


def _split_marker(name):
    """'a\\x004\\x00b' -> ('a', 4, 'b'); None when the name has no %counter."""
    if "\0" not in name:
        return None
    pre, arg, post = name.split("\0")[:3]
    post = post.replace("\0", "")
    return pre, int(arg) if arg.isdigit() else 0, post


def next_name(folder, name, ext, reserve=False):
    """Next free file name (without the folder). With reserve=True the file is created empty (exclusive), so two
    saves never get the same name; it is overwritten with the picture right after."""
    marker = _split_marker(name)
    existing = os.listdir(folder) if os.path.isdir(folder) else []
    if marker:
        pre, width, post = marker
        rx = _counter_regex(pre, post)
        n = max((int(m.group(1)) for f in existing if (m := rx.match(f))), default=0) + 1
        candidate = lambda k: f"{pre}{str(k).zfill(width)}{post}.{ext}"
    else:
        n = 1
        candidate = lambda k: f"{name}.{ext}" if k == 1 else f"{name}_{k}.{ext}"
    if PLACEHOLDER.search(name) and not reserve:      # preview: the exact name is not known yet
        return candidate(n)
    taken = {f.lower() for f in existing}
    while True:
        file = candidate(n)
        if file.lower() not in taken:
            if not reserve:
                return file
            try:
                os.close(os.open(os.path.join(folder, file), os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return file
            except FileExistsError:
                pass
        n += 1


def _exif(params, prompt, extra):
    exif = Image.Exif()
    if extra:
        for i, (k, v) in enumerate(extra.items()):
            exif[TAG_MAKE - i] = f"{k}:{json.dumps(v, separators=(',', ':'))}"
    if prompt is not None:
        exif[TAG_MODEL] = f"prompt:{json.dumps(prompt, separators=(',', ':'))}"
    if params:
        exif.get_ifd(EXIF_IFD)[TAG_USER_COMMENT] = b"UNICODE\0" + params.encode("utf-16-be")
    return exif


def write_image(img, path, fmt, quality, params, prompt, extra, status):
    """Writes the picture with its metadata. prompt / extra are None when they must not be embedded."""
    if fmt == "png":
        info = PngInfo()
        if params:
            info.add_text("parameters", params)
        for k, v in (extra or {}).items():
            info.add_text(k, json.dumps(v, separators=(",", ":")))
        if prompt is not None:
            info.add_text("prompt", json.dumps(prompt, separators=(",", ":")))
        img.save(path, pnginfo=info, compress_level=4)
        return
    exif = _exif(params, prompt, extra)
    if fmt == "jpeg":
        size = len(json.dumps(extra or {}, separators=(",", ":")).encode("utf-8"))
        if len(exif.tobytes()) > JPEG_EXIF_LIMIT and prompt is not None:   # the API prompt goes first: the workflow is enough to load
            prompt, exif = None, _exif(params, None, extra)
            status.append({"kind": "info", "code": "promptBig"})
        if len(exif.tobytes()) > JPEG_EXIF_LIMIT and extra:
            status.append({"kind": "warn", "code": "workflowBig", "v": round(size / 1024)})
            extra, exif = None, _exif(params, None, None)
        if len(exif.tobytes()) > JPEG_EXIF_LIMIT:
            status.append({"kind": "warn", "code": "paramsBig"})
            exif = Image.Exif()
        img.convert("RGB").save(path, quality=quality, optimize=True, exif=exif.tobytes())
    else:
        img.save(path, quality=quality, lossless=quality >= 100, method=4, exif=exif.tobytes())


def to_pil(t):
    arr = np.clip(255.0 * t.cpu().numpy(), 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA" if arr.shape[-1] == 4 else "RGB")


def _values(info, size=None):
    f = {k: v["v"] for k, v in info["fields"].items()}
    w, h = size if size else (f["width"], f["height"])
    return {"model": f["model"], "seed": f["seed"], "steps": f["steps"], "cfg": f["cfg"], "sampler": f["sampler"],
            "scheduler": f["scheduler"], "width": w, "height": h}


def slot_state(info, status, params):
    st = {"off": [], "rebuilt": [], "warn": [], "reasons": {}, "values": {}}
    lost = [s["v"] for s in status if s["code"] in ("modelMissing", "loraMissing", "embeddingMissing")]
    if lost:
        st["warn"].append("HASHES")
        st["reasons"]["HASHES"] = {"code": "hashesMissing", "v": ", ".join(lost)}
    if not params.strip():
        st["off"].append("PARAMETERS")
        st["reasons"]["PARAMETERS"] = {"code": "noSampler"}
    return st


# ---------------------------------------------------------------- the node

OVERRIDES = {"positive": "STRING", "negative": "STRING", "seed": "INT", "steps": "INT", "cfg": "FLOAT",
             "sampler_name": "*", "scheduler": "*", "model_name": "*", "clip_skip": "INT", "denoise": "FLOAT",
             "lora_stack": "STRING"}


TIPS = {"lora_stack": "Connect to use this LoRA list instead of the one found in the graph. Format: <lora:name:weight> "
                      "tags separated by spaces. Not the LORA_STACK type of stacker nodes"}


class CSaveImage:
    @classmethod
    def INPUT_TYPES(cls):
        tip = "Connect to use this value instead of the one found in the graph"
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "Picture(s) to save"}),
                "filename": ("STRING", {"default": "%date_%model_%seed_%counter<4>",
                                        "tooltip": "File name pattern. Variables: %date, %time, %model, %seed, %steps, "
                                                   "%cfg and more. See the context menu → Node Help for details"}),
                "path": ("STRING", {"default": "", "tooltip": "Subfolder of the ComfyUI output folder, the same "
                                                              "variables work here (e.g. txt2img/%date)"}),
                "format": (FORMATS, {"default": "png", "tooltip": "png — lossless, any metadata size; jpeg — metadata "
                                                                  "up to 64 KB (a big workflow does not fit); webp — "
                                                                  "lossless at quality 100"}),
                "quality": ("INT", {"default": 100, "min": 1, "max": 100,
                                    "tooltip": "Quality of jpeg / webp (webp at 100 is lossless)"}),
                "metadata": (METADATA, {"default": "all", "tooltip": "all — parameters + workflow (the picture opens "
                                                                     "the workflow in ComfyUI); parameters only — for "
                                                                     "publishing without your workflow; none — nothing"}),
                "workflow_json": ("BOOLEAN", {"default": False, "tooltip": "Also save the workflow next to the "
                                                                           "picture as <name>.json"}),
                "show_preview": ("BOOLEAN", {"default": True, "tooltip": "Show the saved pictures on the node"}),
                # set by the Preference switch on the panel (the widget itself is hidden); kept last so the widget
                # values of workflows saved before it stay in place
                "preference": (["input", "graph", "file"], {"default": "input",
                               "tooltip": "Which source wins: input — a connected input, graph — the values found in "
                                          "the graph, file — the generation data of the source picture. The others "
                                          "are the fallback"}),
            },
            "optional": {k: (t, {"forceInput": True, "tooltip": TIPS.get(k, tip)}) for k, t in OVERRIDES.items()},
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO", "unique_id": "UNIQUE_ID"},
        }

    CATEGORY = CATEGORY.MAIN.value + CATEGORY.IMAGE.value
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("FILEPATH", "PARAMETERS", "HASHES")
    OUTPUT_NODE = True
    FUNCTION = "execute"
    DESCRIPTION = (
        "Saves pictures with their generation data. The parameters (prompts, seed, steps, CFG, sampler, scheduler, "
        "model, LoRA from the loader nodes, clip skip, upscale / detailer passes) are collected from the graph by "
        "walking back from the picture — nothing has to be wired by hand. A connected input wins over the value "
        "from the graph.\n"
        "Writes A1111-style parameters (with model, LoRA and embedding hashes for Civitai) and, if chosen, the "
        "workflow. Never overwrites a file. The panel on the node shows what will be written before the run."
    )

    def execute(self, images, filename, path, format, quality, metadata, workflow_json, show_preview,
                preference="input", prompt=None, extra_pnginfo=None, unique_id=None, **overrides):
        t0 = time.time()
        given = {}
        for key, value in overrides.items():
            if key == "lora_stack":
                given["lora_stack"] = value
            elif key in ("positive", "negative", "seed", "steps", "cfg", "clip_skip", "denoise"):
                given[key] = value
            elif key == "sampler_name":
                given["sampler"] = value
            elif key == "scheduler":
                given["scheduler"] = value
            elif key == "model_name":
                given["model"] = value
        info = collect(prompt or {}, unique_id, overrides=given, external=file_values, source=image_source,
                       runtime=Outputs(), prefer=preference)
        h, w = int(images.shape[1]), int(images.shape[2])
        f = info["fields"]
        # size not given by the graph (img2img: the picture comes from a file through upscales…): the saved picture
        # is what the main pass made. With Hires fields the size before the upscale stays unknown.
        if f["width"]["v"] is None and f["height"]["v"] is None and f["width"]["src"] != "input" \
                and f["height"]["src"] != "input" and not info.get("hires"):
            f["width"], f["height"] = {"v": w, "src": "picture"}, {"v": h, "src": "picture"}  # the saved picture
        status = []
        if sampler_status(info):
            status.append(sampler_status(info))

        items = resolve_files(info)
        hashes, hstatus = hash_files(items, compute=metadata != "none")
        from ..core.civitai import lookup_enabled
        hashes["resources"], cstatus = civitai_resources(info, items, hashes["full"], online=lookup_enabled(), budget=5.0)
        hstatus += cstatus
        params, _ = a1111_text(info, final_size=(w, h), hashes=hashes)
        if not has_values(info):
            params = ""

        now = datetime.now()
        values = _values(info, (w, h))
        root, folder = output_folder(path, values, now)
        os.makedirs(folder, exist_ok=True)
        stem_pattern = clean_part(render_name(filename, values, now).replace("/", "_")) or now.strftime("%Y-%m-%d_%H%M%S")

        embed_params = params if metadata != "none" else ""
        embed_prompt = prompt if metadata == "all" else None
        embed_extra = extra_pnginfo if metadata == "all" and extra_pnginfo else None
        files, results = [], []
        for t in images:
            name = next_name(folder, stem_pattern, format, reserve=True)
            full = os.path.join(folder, name)
            fstatus = []
            write_image(to_pil(t), full, format, quality, embed_params, embed_prompt, embed_extra, fstatus)
            if workflow_json and extra_pnginfo and extra_pnginfo.get("workflow"):
                side = os.path.splitext(full)[0] + ".json"
                with open(side, "w", encoding="utf-8") as fh:
                    json.dump(extra_pnginfo["workflow"], fh, ensure_ascii=False)
                fstatus.append({"kind": "ok", "code": "workflowFile", "v": os.path.basename(side)})
            for s in fstatus:
                if s not in status:
                    status.append(s)
            files.append(full)
            sub = os.path.relpath(folder, root)
            results.append({"filename": name, "subfolder": "" if sub == "." else sub.replace("\\", "/"), "type": "output"})

        # what ended up in the file
        if metadata == "none":
            status.insert(0, {"kind": "muted", "code": "metaNone"})
        else:
            if params:
                status.insert(0, {"kind": "ok", "code": "paramsOk", "v": sum(bool(st.get("used")) for st in info["stages"]), "loras": len(info["loras"])})
            if metadata == "all" and not any(s["code"] == "workflowBig" for s in status):
                status.insert(1 if params else 0, {"kind": "ok", "code": "workflowIn"})
            elif metadata == "parameters only":
                status.append({"kind": "muted", "code": "workflowOff"})
            if hashes["model"]:
                status.append({"kind": "ok", "code": "modelHash", "v": model_stem(info["fields"]["model"]["v"]),
                               "h": hashes["model"]})
            status.extend(hstatus)
        if any(s["code"] == "workflowBig" for s in status) and not workflow_json:
            status.append({"kind": "info", "code": "workflowHint"})

        hash_text = ",".join([f"model:{hashes['model']}"] * bool(hashes["model"])
                             + [f"{n}:{v}" for n, v in hashes["loras"].items()]
                             + [f"{n}:{v}" for n, v in hashes["embeddings"].items()])
        sec = round(time.time() - t0, 1)
        if debug_enabled():
            logger.info(debug_report(unique_id, info, status, files, sec))
        saved_blocks = blocks(metadata, format, workflow_json, params)
        codes = {x["code"] for x in status}
        for blk in saved_blocks:
            if (blk["key"] == "workflow" and "workflowBig" in codes) or (blk["key"] == "prompt" and codes & {"promptBig", "workflowBig"}) \
                    or (blk["key"] in ("workflow", "prompt", "parameters") and "paramsBig" in codes):
                blk["on"], blk["dropped"] = False, True
        ui = {"rig_save": [{"files": [r["filename"] for r in results], "subfolder": results[0]["subfolder"] if results else "",
                            "fields": info["fields"], "loras": info["loras"], "stages": info["stages"],
                            "status": status, "text": params, "sec": sec, "format": format, "paths": files,
                            "blocks": saved_blocks}],
              "rig_state": [slot_state(info, status, params)]}
        if show_preview:
            ui["images"] = results
        return {"ui": ui, "result": ("\n".join(files), params, hash_text)}


def debug_report(node_id, info, status, files, sec=None):
    """What Save image found, for the console (Settings → Rigstools → Debug). sec=None: the preview before the run,
    files then holds the predicted name."""
    if sec is None:
        lines = [f"Save image #{node_id} (preview before the run, values may change when it runs)"]
        lines += [f"  will be saved as: {f}" for f in files]
    else:
        lines = [f"Save image #{node_id}: {len(files)} file(s) in {sec} s"]
        lines += [f"  file: {f}" for f in files]
    lines.append(f"  preference: {info.get('prefer', 'input')}")
    if info.get("source_file"):
        lines.append(f"  source file: {info['source_file']}")
    lines.append("  passes:" if info["stages"] else "  passes: no sampler found")
    for i, st in enumerate(info["stages"], 1):
        extra = ", ".join(x for x in (f"steps {st['steps']}" if st.get("steps") is not None else "",
                                      f"cfg {st['cfg']}" if st.get("cfg") is not None else "",
                                      f"denoise {st['denoise']}" if st.get("denoise") is not None else "",
                                      f"x{st['upscale_by']}" if st.get("upscale_by") else "") if x)
        use = {"main": "the main values", "hires": "the Hires fields"}.get(st.get("used")) or \
            ("not used: repaints a part of the picture" if st["kind"] in ("detailer", "inpaint") else "not used")
        lines.append(f"    {i}. {st['type']} #{st['id']} - {st['kind']} ({extra}) -> {use}")
    if info.get("hires"):
        h = info["hires"]
        lines.append(f"  hires fields from: {h['type']} (steps {h['steps']}, denoise {h['denoise']}, "
                     f"upscale {h['upscale_by']}, upscaler {h['upscaler']})")
    for k, f in info["fields"].items():
        v = f["v"]
        v = (v[:80] + "…") if isinstance(v, str) and len(v) > 80 else v
        lines.append(f"  {k}: {v!r} [{f['src']}]")
    lines.append(f"  lora [{info['lora_src']}]:" + ("" if info["loras"] else " none"))
    for l in info["loras"]:
        lines.append(f"    {l['name']} {l['weight']}" + (f" (earlier pass: {l['from']})" if l.get("from") else ""))
    for s in status:
        lines.append(f"  {s['kind']}: {s['code']}" + (f" {s['v']}" if "v" in s else ""))
    return "\n".join(lines)


# ---------------------------------------------------------------- preview before the run

_last_preview = {}          # node id -> the last preview written to the log


def preview(prompt, node_id):
    """What the node will write, for the panel: values with their sources, passes, next file name, status."""
    node = prompt.get(str(node_id)) or {}
    ins = node.get("inputs", {})
    info = collect(prompt, node_id, external=file_values, source=image_source,
                   prefer=ins.get("preference") if isinstance(ins.get("preference"), str) else "input")
    items = resolve_files(info)
    metadata = ins.get("metadata", "all")
    from ..core.civitai import lookup_enabled
    pv_hashes, status = hash_files(items, compute=False)
    resources, cstatus = civitai_resources(info, items, pv_hashes["full"], online=lookup_enabled(), budget=12.0)
    status += cstatus
    if sampler_status(info):
        status.insert(0, sampler_status(info))
    # hashes already in the caches go in as they are; "…" stands for the ones calculated only when saving
    PENDING = "@@rigstools-pending-hash@@"   # plain ASCII: it also goes through the Hashes JSON unescaped
    pv = {"model": None, "loras": {}, "embeddings": {}, "resources": resources}
    for kind, name, path in items:
        if not path:
            continue
        h = pv_hashes["full"].get((kind, name))
        h = h[:10] if h else PENDING
        if kind == "model":
            pv["model"] = h
        else:
            pv["loras" if kind == "lora" else "embeddings"][name] = h
    params, _ = a1111_text(info, hashes=pv)
    # a hash that the resource list (Civitai IDs) replaced is not in the text, nor is its mark
    pending = PENDING in params
    params = params.replace(PENDING, "…")
    fmt = ins.get("format", "png") if isinstance(ins.get("format"), str) else "png"
    now = datetime.now()
    values = _values(info)
    # values that are known only when saving are shown as [time], [width], [height], [seed]…
    unknown = {"time"} | ({"width", "height"} if size_may_change(prompt, node_id, info) else set())
    # a connected input whose value the graph does not hold (a node that computes it) gets its value when it runs
    unknown |= {k for k, f in info["fields"].items() if f.get("src") == "input" and f.get("v") in (None, "")} \
        & {"model", "seed", "steps", "cfg", "sampler", "scheduler"}
    path_text = ins.get("path", "") if isinstance(ins.get("path"), str) else ""
    try:
        root, folder = output_folder(path_text, values, now)
        stem = clean_part(render_name(ins.get("filename", "") if isinstance(ins.get("filename"), str) else "",
                                      values, now, unknown=unknown).replace("/", "_")) or "[time]"
        name = shown_name(next_name(folder, stem, fmt))
        sub = shown_name(clean_part(render_name(path_text, values, now, counter=0, unknown=unknown).replace("\0", "")))
        next_file = (sub + "/" if sub else "") + name
        full_path = os.path.join(root, *([sub] if sub else []), name)
    except Exception as e:
        next_file, full_path, status = "", "", status + [{"kind": "warn", "code": "badPath", "v": str(e)}]
    if fmt == "jpeg" and metadata == "all":
        status.append({"kind": "info", "code": "jpegLimit"})
    # the panel asks again on every change of the graph: the log gets the preview only when it is different
    if debug_enabled():
        text = debug_report(node_id, info, status, [full_path or next_file])
        if _last_preview.get(str(node_id)) != text:
            _last_preview[str(node_id)] = text
            logger.info(text)
    return {"fields": info["fields"], "loras": info["loras"], "lora_src": info["lora_src"], "stages": info["stages"],
            "hires": info["hires"], "next": next_file, "path": full_path, "placeholders": "[" in next_file, "status": status, "text": params, "pending_hashes": pending,
            "blocks": blocks(metadata, fmt, bool(ins.get("workflow_json")), params), "folder": folder_paths.get_output_directory(),
            "state": slot_state(info, status, params if has_values(info) else "")}


def register_routes():
    try:
        from aiohttp import web
        from server import PromptServer
    except Exception:
        return

    @PromptServer.instance.routes.post("/rigstools/save_preview")
    async def save_preview(request):
        try:
            import asyncio
            body = await request.json()
            prompt = body.get("prompt") or {}
            result = await asyncio.get_running_loop().run_in_executor(None, preview, prompt, str(body.get("node")))
            return web.json_response(result)
        except Exception as e:
            logger.debug(f"save_preview: {e}")
            return web.json_response({"error": str(e)}, status=500)


register_routes()
