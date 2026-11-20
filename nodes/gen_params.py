"""Generation parameters: the values of a picture (sent from the gallery, or typed) in fields, each also an output.

The node keeps the parameters text it got and the values typed over it in one widget (JSON), so the workflow
carries them. The outputs are those of Parameters extractor.
"""
import json

from ..core import CATEGORY
from ..core.settings import debug
from .parameters import extract_values, SAMPLERS, SCHEDULERS, steps_report
from .image import _json_safe
from .image_params import EDITABLE, _cast, lora_models


def _state(values):
    try:
        data = json.loads(values or "{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def read(values):
    """Values of the outputs: the parameters text with the typed values over it."""
    state = _state(values)
    v = extract_values(state.get("parameters") or "")
    for key, raw in (state.get("values") or {}).items():
        if key in EDITABLE:
            c = _cast(key, raw, v.get(key))
            if c is not None:
                v[key] = c
                if key in v["missing"]:
                    v["missing"].remove(key)
    return state, v


class CGenerationParams:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # drawn by web/rigstools.js as the parameters panel; the value is JSON {parameters, source, values}
                "values": ("RIGSTOOLS_GEN_PARAMS", {"default": "{}"}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    CATEGORY = CATEGORY.MAIN.value + CATEGORY.UTILS.value
    RETURN_TYPES = ("INT", "INT", "FLOAT", "INT", "INT", "INT", "STRING", "STRING", "*", "STRING", SAMPLERS, SCHEDULERS)
    RETURN_NAMES = ("SEED", "STEPS", "CFG", "CLIP", "WIDTH", "HEIGHT", "POSITIVE", "NEGATIVE", "MODEL_NAME",
                    "LORA_STACK", "SAMPLER", "SCHEDULER")
    DESCRIPTION = (
        "Generation parameters in fields — prompts, seed, steps, CFG, clip skip, size, sampler, scheduler, model and "
        "LoRA — each also an output, as in Parameters extractor.\n"
        "PicoTeka, the gallery of Rigstools, fills the node with the parameters of a picture (Parameters to workflow); the fields "
        "can be edited, a changed value is highlighted and goes to the output (↺ resets it). New parameters from the "
        "gallery replace everything, typed values included."
    )
    FUNCTION = "execute"

    def execute(self, values="{}", unique_id=None):
        state, v = read(values)
        debug(steps_report(f"Generation parameters #{unique_id}", state.get("parameters") or "", v))
        return (v["seed"], v["steps"], float(v["cfg"]), v["clip_skip"], v["width"], v["height"], v["positive"],
                v["negative"], v["model"], v["lora_stack"], v["sampler"], v["scheduler"])


def register_routes():
    try:
        from aiohttp import web
        from server import PromptServer
    except Exception:
        return

    @PromptServer.instance.routes.post("/rigstools/gen_params")
    async def gen_params(request):
        """Panel values of a parameters text: {parameters} -> the same shape as /rigstools/image_params."""
        text = (await request.json()).get("parameters") or ""
        v = extract_values(text)
        return web.json_response(_json_safe({
            "info": {}, "fields": {k: v[k] for k in EDITABLE}, "missing": v["missing"], "model_found": v["model_found"],
            "lora_from": v["lora_from"], "loras": lora_models(v["lora_stack"]), "samplers": SAMPLERS, "schedulers": SCHEDULERS,
        }))


register_routes()
