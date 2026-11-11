import json
from pathlib import PurePath

import folder_paths

from ..core import CATEGORY, logger
from .image import CLoadImageMeta, load, file_hash, _json_safe, metadata_lines, file_line
from ..core.image_meta import read_metadata, summary
from ..core.prompt_graph import parameters_from_prompt as rebuild_parameters
from .parameters import extract_values, find_checkpoint, SAMPLERS, SCHEDULERS
from ..core.settings import debug
from .lora_hashes import LORA_TAG, find_lora

# panel fields that can be changed by hand; the rest (LoRA) is shown read-only
EDITABLE = ("positive", "negative", "seed", "steps", "cfg", "clip_skip", "width", "height",
            "sampler", "scheduler", "model")


def lora_models(lora_stack):
    """[{name, weight, file}] for the LoRA tags of the stack; file is the path in models/loras or None."""
    out = []
    for name, weight in LORA_TAG.findall(lora_stack or ""):
        out.append({"name": name.strip(), "weight": (weight or "1").split(":")[0].strip(), "file": find_lora(name)})
    return out


def _cast(key, value, current):
    """Value typed in the panel -> output type; None when it cannot be used (then the image value stays)."""
    try:
        if key in ("seed", "steps", "width", "height"):
            v = int(float(str(value).strip()))
            return v if v >= (0 if key == "seed" else 1) else None
        if key == "clip_skip":
            v = int(float(str(value).strip()))
            return -abs(v) if v else None
        if key == "cfg":
            return float(str(value).strip().replace(",", "."))
        if key == "sampler":
            return value if value in SAMPLERS else None
        if key == "scheduler":
            return value if value in SCHEDULERS else None
        if key in ("positive", "negative"):
            return str(value)
        if key == "model":
            text = str(value).strip()
            return find_checkpoint(text)[0] if text else None
    except (TypeError, ValueError):
        return None
    return current


def _metadata_only(path):
    """Like load() but without decoding the pixels — for the panel."""
    img, metadata = read_metadata(path)
    img.close()
    parameters = metadata.get("parameters") or ""
    info = summary(metadata)
    info["rebuilt"] = False
    if not parameters and info["prompt"]:
        try:
            parameters = rebuild_parameters(metadata["prompt"]) or ""
            info["rebuilt"] = bool(parameters)
        except Exception as e:
            logger.warning(f"Could not rebuild parameters from the prompt: {e}")
    return None, None, metadata, parameters, PurePath(path).name, PurePath(path).stem, info


def read_values(image, overrides=None, with_image=True):
    """Everything the node outputs and the panel shows, with the panel overrides applied."""
    path = folder_paths.get_annotated_filepath(image)
    image_t, mask, metadata, parameters, name, stem, info = (load if with_image else _metadata_only)(path)
    values = extract_values(parameters)
    missing = list(values["missing"])
    applied = {}
    for key, raw in (overrides or {}).items():
        if key not in EDITABLE:
            continue
        v = _cast(key, raw, values.get(key))
        if v is None:
            logger.warning(f"Ignoring the value typed for {key}: {raw!r}")
            continue
        values[key] = v
        applied[key] = v
        if key in missing:
            missing.remove(key)
    values["missing"] = missing
    return image_t, mask, metadata, parameters, stem, info, values, applied


NAMES = {"clip_skip": "clip skip"}


def steps_report(where, image, info, parameters, v, applied):
    """The steps of reading a picture, for the console (Settings → Rigstools → Debug)."""
    lines = [file_line(f"Load image with parameters {where}", image, info)] + metadata_lines(info)
    if parameters:
        lost = [NAMES.get(k, k) for k in v["missing"]]
        done = "rebuilt" if info.get("rebuilt") else "found"
        lines.append(f"  all parameters {done}" if not lost else
                     f"  not {done}, the defaults are used: {', '.join(lost)}")
    if v["model"] and "model" not in v["missing"]:
        lines.append(f"  model found: {v['model']}" if v["model_found"] else
                     f"  model not found in models/checkpoints, the name is passed as is: {v['model']}")
    loras = lora_models(v["lora_stack"])
    if loras:
        lost = [l["name"] for l in loras if not l["file"]]
        lines.append(f"  LoRA: {len(loras)}, all found in models/loras" if not lost else
                     f"  LoRA: {len(loras)}, not found in models/loras: {', '.join(lost)}")
    if applied:     # prompts by name only, they are long
        typed = [k if k in ("positive", "negative") else f"{NAMES.get(k, k)} = {val}" for k, val in applied.items()]
        lines.append("  typed in the panel: " + ", ".join(typed))
    return "\n".join(lines)


def _overrides_for(image, values_json):
    try:
        data = json.loads(values_json or "{}")
    except Exception:
        return {}
    if not isinstance(data, dict) or data.get("image") != image:
        return {}  # typed for another picture: the panel clears them when the picture changes
    return data.get("values") or {}


class CLoadImageParams:
    @classmethod
    def INPUT_TYPES(cls):
        req = CLoadImageMeta.INPUT_TYPES()["required"]
        return {
            "required": {
                "image": req["image"],
                # drawn by web/rigstools.js as the parameters panel; the value is JSON of the hand-typed values
                "values": ("RIGSTOOLS_PARAMS", {"default": "{}"}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    CATEGORY = CATEGORY.MAIN.value + CATEGORY.IMAGE.value
    # MODEL_NAME is "*": it plugs into a checkpoint list (ckpt_name of a loader) as well as into a text input
    RETURN_TYPES = ("IMAGE", "MASK", "METADATA_RAW", "STRING", "STRING", "STRING", "INT", "INT", "FLOAT", "INT",
                    "INT", "INT", SAMPLERS, SCHEDULERS, "*", "STRING")
    RETURN_NAMES = ("IMAGE", "MASK", "METADATA_RAW", "PARAMETERS", "POSITIVE", "NEGATIVE", "SEED", "STEPS", "CFG",
                    "CLIP", "WIDTH", "HEIGHT", "SAMPLER", "SCHEDULER", "MODEL_NAME", "LORA_STACK")
    DESCRIPTION = (
        "Loads an image and shows its generation parameters right on the node: prompts, seed, steps, CFG, clip skip, "
        "size, sampler, scheduler, model and LoRA.\n"
        "Fields can be edited: a changed value is highlighted and goes to the output instead of the one from the "
        "image (↺ resets what was typed).\n"
        "Values missing from the image use the defaults."
    )
    FUNCTION = "execute"

    def execute(self, image, values="{}", unique_id=None):
        image_t, mask, metadata, parameters, stem, info, v, applied = read_values(image, _overrides_for(image, values))
        info["name"] = image
        debug(steps_report(f"#{unique_id} (run)", image, info, parameters, v, applied))
        return {
            "ui": {"rig_meta": [info]},
            "result": (image_t, mask, metadata, parameters, v["positive"], v["negative"], v["seed"], v["steps"],
                       float(v["cfg"]), v["clip_skip"], v["width"], v["height"], v["sampler"], v["scheduler"],
                       v["model"], v["lora_stack"]),
        }

    @classmethod
    def IS_CHANGED(cls, image, values="{}", **_):
        return file_hash(folder_paths.get_annotated_filepath(image)) + "|" + str(values)

    @classmethod
    def VALIDATE_INPUTS(cls, image, values="{}", **_):
        if not folder_paths.exists_annotated_filepath(image):
            return f"Invalid image file: {image}"
        return True


def register_routes():
    try:
        from aiohttp import web
        from server import PromptServer
    except Exception:
        return

    def work(name, node=""):
        """(body, status) of the panel values — runs in a worker thread, so reading the file does not hold up
        the server (and the /view request of the same picture)."""
        try:
            if not name or not folder_paths.exists_annotated_filepath(name):
                return {"error": "not found"}, 404
            _, _, _, parameters, stem, info, v, _ = read_values(name, with_image=False)
            info["name"] = name
            info["file"] = PurePath(folder_paths.get_annotated_filepath(name)).name
            debug(steps_report(f"#{node} (panel)", name, info, parameters, v, {}))
            fields = {k: v[k] for k in EDITABLE}
            return _json_safe({
                "info": info, "fields": fields, "missing": v["missing"], "model_found": v["model_found"],
                "lora_from": v["lora_from"],
                "loras": lora_models(v["lora_stack"]), "samplers": SAMPLERS, "schedulers": SCHEDULERS,
            }), 200
        except Exception as e:
            logger.warning(f"image_params failed for {name!r}: {e}", exc_info=True)
            return {"error": str(e)}, 500

    @PromptServer.instance.routes.get("/rigstools/image_params")
    async def image_params(request):
        """Values for the panel: ?filename=<annotated name>."""
        import asyncio
        body, status = await asyncio.get_running_loop().run_in_executor(
            None, work, request.query.get("filename", ""), request.query.get("node", ""))
        return web.json_response(body, status=status)

    @PromptServer.instance.routes.post("/rigstools/log")
    async def browser_log(request):
        """A failure the panel met in the browser, so it shows in the ComfyUI console too."""
        try:
            body = await request.json()
            logger.warning(str(body.get("message", ""))[:500])
        except Exception:
            pass
        return web.json_response({})

register_routes()
