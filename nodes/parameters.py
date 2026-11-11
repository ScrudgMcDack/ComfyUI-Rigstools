import re
from pathlib import PurePath

import folder_paths
from ..core import CATEGORY, logger
from ..core.settings import debug

try:  # real lists inside ComfyUI; static fallback keeps the module importable in tests
    import comfy.samplers as _cs
    SAMPLERS = list(_cs.KSampler.SAMPLERS)
    SCHEDULERS = list(_cs.KSampler.SCHEDULERS)
except Exception:  # pragma: no cover
    SAMPLERS = ["euler", "euler_ancestral", "heun", "dpm_2", "dpm_2_ancestral", "lms", "dpm_fast", "dpm_adaptive",
                "dpmpp_2s_ancestral", "dpmpp_sde", "dpmpp_2m", "dpmpp_2m_sde", "dpmpp_3m_sde", "ddim", "uni_pc",
                "uni_pc_bh2", "lcm"]
    SCHEDULERS = ["simple", "sgm_uniform", "karras", "exponential", "ddim_uniform", "beta", "normal",
                  "linear_quadratic", "kl_optimal"]

# A1111 / Civitai sampler names -> ComfyUI (inverse of the map used by Image Saver)
A1111_SAMPLERS = {
    "euler a": "euler_ancestral", "euler": "euler", "lms": "lms", "heun": "heun", "dpm2": "dpm_2",
    "dpm2 a": "dpm_2_ancestral", "dpm++ 2s a": "dpmpp_2s_ancestral", "dpm++ 2m": "dpmpp_2m", "dpm++ sde": "dpmpp_sde",
    "dpm++ 2m sde": "dpmpp_2m_sde", "dpm++ 3m sde": "dpmpp_3m_sde", "dpm++ 2m sde heun": "dpmpp_2m_sde_heun",
    "dpm fast": "dpm_fast", "dpm adaptive": "dpm_adaptive", "ddim": "ddim", "plms": "plms", "unipc": "uni_pc",
    "lcm": "lcm", "ddpm": "ddpm", "deis": "deis", "ipndm": "ipndm", "ipndm_v": "ipndm_v",
}
# A1111 "Schedule type" values and sampler suffixes -> ComfyUI schedulers
A1111_SCHEDULERS = {
    "karras": "karras", "exponential": "exponential", "sgm uniform": "sgm_uniform", "simple": "simple",
    "normal": "normal", "beta": "beta", "kl optimal": "kl_optimal", "ddim": "ddim_uniform", "uniform": "normal",
}

SETTINGS_LINE = re.compile(r"^(?:Steps:\s*\d|(?:Sampler|Schedule type|CFG scale|Seed|Size|Clip skip|Lora stack|Model|Version):)",
                           re.MULTILINE)
LORA_TAG = re.compile(r"<lora:[^>]+>", re.IGNORECASE)
NEGATIVE_MARK = "Negative prompt:"


def _split_settings(line: str) -> dict:
    """'Steps: 25, Sampler: X, Lora hashes: "a: 1, b: 2", Hashes: {...}' -> dict.
    Commas inside quotes and brackets do not split."""
    parts, buf, quote, depth = [], [], False, 0
    for ch in line:
        if ch == '"' and depth == 0:
            quote = not quote
        elif not quote and ch in "{[(":
            depth += 1
        elif not quote and ch in "}])":
            depth = max(0, depth - 1)
        if ch == "," and not quote and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    result = {}
    for part in parts:
        key, sep, value = part.partition(":")
        if sep and key.strip():
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':   # a quoted value (it has , : or " in it)
                try:
                    import json
                    value = json.loads(value)
                except ValueError:
                    value = value[1:-1]
            result[key.strip().lower()] = value
    return result


def parse_a1111(text: str) -> dict:
    """Splits an A1111-style parameters text into positive, negative and the settings dict.
    Prompts are returned exactly as stored — they are part of what the text encoder saw."""
    text = text or ""
    settings_line = ""
    lines = list(SETTINGS_LINE.finditer(text))
    body = text
    # the settings line is the last line, starting with "Steps:" (A1111) or another known key (rebuilt text)
    if lines and "\n" not in text[lines[-1].start():].rstrip("\n"):
        m = lines[-1]
        body = text[:m.start()]
        settings_line = text[m.start():].split("\n", 1)[0]
        if body.endswith("\n"):
            body = body[:-1]

    positive, negative = body, None
    if body.startswith(NEGATIVE_MARK):
        positive, negative = "", body[len(NEGATIVE_MARK):]
    else:
        i = body.find("\n" + NEGATIVE_MARK)
        if i >= 0:
            positive, negative = body[:i], body[i + 1 + len(NEGATIVE_MARK):]
    if negative is not None and negative.startswith(" "):
        negative = negative[1:]              # "Negative prompt: " is written with one space

    return {"positive": positive, "negative": negative, "settings": _split_settings(settings_line)}


def _int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _float(value):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _sampler_and_scheduler(sampler_text, schedule_text):
    """('DPM++ 2M Karras', None) -> ('dpmpp_2m', 'karras'); unknown parts -> None."""
    sampler = scheduler = None
    if schedule_text:
        st = schedule_text.strip().lower()
        scheduler = st if st in SCHEDULERS else A1111_SCHEDULERS.get(st.replace("_", " "))
    if sampler_text:
        name = sampler_text.strip()
        low = name.lower()
        if low in SAMPLERS:                                  # already a ComfyUI name
            sampler = low
        else:
            for suffix, sched in (("karras", "karras"), ("exponential", "exponential")):
                if low.endswith(" " + suffix):
                    low = low[: -len(suffix) - 1]
                    scheduler = scheduler or sched
                    break
            if low in A1111_SAMPLERS:
                sampler = A1111_SAMPLERS[low]
            elif "_" in low:                                 # Image Saver: "<sampler>_<scheduler>"
                base, _, sched = low.rpartition("_")
                if base in SAMPLERS and sched in SCHEDULERS:
                    sampler, scheduler = base, scheduler or sched
    if sampler not in SAMPLERS:
        sampler = None
    if scheduler not in SCHEDULERS:
        scheduler = None
    return sampler, scheduler


def _norm(path: str) -> str:
    return path.replace("\\", "/").lower()


def find_checkpoint(model: str) -> tuple:
    """Matches a model name from the metadata to a file in models/checkpoints.
    Returns (value_for_ckpt_name, found_file)."""
    if not model:
        return "", False
    try:
        files = folder_paths.get_filename_list("checkpoints")
    except Exception:
        files = []
    want = _norm(model)
    want_name = PurePath(want).name
    want_stem = PurePath(want).stem if PurePath(want).suffix in (".safetensors", ".ckpt", ".pt", ".sft", ".gguf") else want_name
    by_path, by_name, by_stem = {}, {}, {}
    for f in files:
        n = _norm(f)
        by_path.setdefault(n, f)
        by_name.setdefault(PurePath(n).name, f)
        by_stem.setdefault(PurePath(n).stem, f)
    for table, key in ((by_path, want), (by_name, want_name), (by_stem, want_stem), (by_stem, want_name)):
        if key in table:
            return table[key], True
    return model, False


DEFAULTS = {"seed": 0, "steps": 20, "cfg": 7.0, "clip_skip": -2, "width": 1024, "height": 1024,
            "sampler": "euler", "scheduler": "normal"}


def extract_values(parameters, fallbacks=None) -> dict:
    """All values of an A1111-style parameters text; missing ones are taken from fallbacks (DEFAULTS by default).
    'missing' lists the substituted keys, 'model_text' is the checkpoint name as stored in the image."""
    fb = {**DEFAULTS, **(fallbacks or {})}
    fallback_seed, fallback_steps, fallback_cfg = fb["seed"], fb["steps"], fb["cfg"]
    fallback_clip_skip, fallback_width, fallback_height = fb["clip_skip"], fb["width"], fb["height"]
    fallback_sampler, fallback_scheduler = fb["sampler"], fb["scheduler"]
    parsed = parse_a1111(parameters if isinstance(parameters, str) else "")
    s = parsed["settings"]
    missing = []

    def pick(name, value, fallback):
        if value is None:
            missing.append(name)
            return fallback
        return value

    seed = pick("seed", _int(s.get("seed")), fallback_seed)
    steps = pick("steps", _int(s.get("steps")), fallback_steps)
    cfg = pick("cfg", _float(s.get("cfg scale")), fallback_cfg)

    clip = _int(s.get("clip skip"))
    clip = pick("clip_skip", -abs(clip) if clip else None, fallback_clip_skip)

    w = h = None
    size = re.match(r"\s*(\d+)\s*x\s*(\d+)", s.get("size", ""))
    if size:
        w, h = int(size.group(1)), int(size.group(2))
    width = pick("width", w, fallback_width)
    height = pick("height", h, fallback_height)

    positive = parsed["positive"]
    if not (parameters and positive):
        missing.append("positive")
    negative = parsed["negative"]
    if negative is None:
        missing.append("negative")
        negative = ""

    model_text = s.get("model", "")
    model, found = find_checkpoint(model_text)
    if not model_text:
        missing.append("model")
    elif not found:
        logger.warning(f"Checkpoint '{model_text}' not found in models/checkpoints; passing the name as is")

    lora_stack = s.get("lora stack") or None
    lora_from = "stack" if lora_stack else None
    if not lora_stack:
        tags = list(dict.fromkeys(LORA_TAG.findall(positive or "")))
        lora_stack = " ".join(tags) if tags else None
        lora_from = "prompt" if tags else None

    sampler, scheduler = _sampler_and_scheduler(s.get("sampler"), s.get("schedule type"))
    sampler = pick("sampler", sampler, fallback_sampler)
    scheduler = pick("scheduler", scheduler, fallback_scheduler)

    if missing:
        logger.debug(f"Not found in parameters, fallback used: {', '.join(missing)}")

    return {"seed": seed, "steps": steps, "cfg": float(cfg), "clip_skip": clip, "width": width, "height": height,
            "positive": positive, "negative": negative, "model": model, "model_found": found,
            "model_text": model_text, "lora_stack": lora_stack, "lora_from": lora_from, "sampler": sampler, "scheduler": scheduler,
            "missing": missing}


# value key -> output name
OUT_NAMES = {"seed": "SEED", "steps": "STEPS", "cfg": "CFG", "clip_skip": "CLIP", "width": "WIDTH", "height": "HEIGHT",
             "sampler": "SAMPLER", "scheduler": "SCHEDULER", "positive": "POSITIVE", "negative": "NEGATIVE",
             "model": "MODEL_NAME"}


def steps_report(title, parameters, v):
    """The steps of parsing, for the console (Settings → Rigstools → Debug)."""
    names = {"clip_skip": "clip skip"}
    lines = [title + (f": parsing {len(parameters)} chars of parameters" if parameters else ": no parameters text")]
    lost = [names.get(k, k) for k in v["missing"]]
    lines.append("  all parameters found" if not lost else f"  not found, the fallbacks are used: {', '.join(lost)}")
    if v["model"] and "model" not in v["missing"]:
        lines.append(f"  model found: {v['model']}" if v["model_found"] else
                     f"  model not found in models/checkpoints, the name is passed as is: {v['model']}")
    if v["lora_stack"]:
        lines.append(f"  LoRA: {len(LORA_TAG.findall(v['lora_stack']))}")
    return "\n".join(lines)


def output_state(v, fallback_prefix=""):
    """Which outputs got a substitute value (for the ✕ marks and their tooltips in web/rigstools.js)."""
    state = {"off": [], "rebuilt": [], "warn": [], "reasons": {}}
    for key in v["missing"]:
        out = OUT_NAMES.get(key)
        if not out:
            continue
        state["off"].append(out)
        if key in ("positive", "negative", "model"):
            state["reasons"][out] = {"code": "empty", "k": key}
        else:
            state["reasons"][out] = {"code": "fallback", "k": key, "v": v[key], "input": f"{fallback_prefix}{key}"}
    if not v["lora_stack"]:
        state["off"].append("LORA_STACK")
    # what comes out, for the styled tooltips (Draftsman)
    state["values"] = {out: {"code": "value", "v": " ".join(str(v[key]).split())[:90]}
                       for key, out in OUT_NAMES.items() if key not in v["missing"]}
    if v["lora_stack"]:
        state["values"]["LORA_STACK"] = {"code": "loras", "v": len(LORA_TAG.findall(v["lora_stack"]))}
    return state


class CParamExtractor:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "parameters": ("STRING", {"forceInput": True, "tooltip": "A1111 parameters: the PARAMETERS output of "
                                                                         "a loader or Metadata extractor"}),
            },
            "optional": {
                "fallback_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff,
                                          "tooltip": "Used when the image has no Seed"}),
                "fallback_steps": ("INT", {"default": 20, "min": 1, "max": 10000,
                                           "tooltip": "Used when the image has no Steps"}),
                "fallback_cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 100.0, "step": 0.1, "round": 0.01,
                                           "tooltip": "Used when the image has no CFG scale"}),
                "fallback_clip_skip": ("INT", {"default": -2, "min": -24, "max": -1,
                                               "tooltip": "Used when the image has no Clip skip (negative, as in CLIP Set Last Layer)"}),
                "fallback_width": ("INT", {"default": 1024, "min": 16, "max": 16384, "step": 8,
                                           "tooltip": "Used when the image has no Size"}),
                "fallback_height": ("INT", {"default": 1024, "min": 16, "max": 16384, "step": 8,
                                            "tooltip": "Used when the image has no Size"}),
                "fallback_sampler": (SAMPLERS, {"default": "euler",
                                                "tooltip": "Used when the sampler is missing or unknown"}),
                "fallback_scheduler": (SCHEDULERS, {"default": "normal",
                                                    "tooltip": "Used when the scheduler is missing or unknown"}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    CATEGORY = CATEGORY.MAIN.value + CATEGORY.UTILS.value

    # MODEL_NAME is "*": it plugs into a checkpoint list (ckpt_name of a loader) as well as into a text input
    RETURN_TYPES = ("INT", "INT", "FLOAT", "INT", "INT", "INT", "STRING", "STRING", "*", "STRING",
                    SAMPLERS, SCHEDULERS)
    RETURN_NAMES = ("SEED", "STEPS", "CFG", "CLIP", "WIDTH", "HEIGHT", "POSITIVE", "NEGATIVE", "MODEL_NAME",
                    "LORA_STACK", "SAMPLER", "SCHEDULER")

    DESCRIPTION = (
        "Parses the A1111-style parameters text of a generated image into separate values: seed, steps, CFG, "
        "clip skip, size, positive and negative prompts, checkpoint, LoRA stack, sampler and scheduler.\n"
        "Values missing from the image are taken from the fallback_* inputs (set them on the node or connect your "
        "own values; their outputs are dimmed). Prompts are returned exactly as stored.\n"
        "Input: the PARAMETERS output of Metadata extractor."
    )

    FUNCTION = "execute"

    def execute(self, parameters=None, fallback_seed=0, fallback_steps=20, fallback_cfg=7.0, fallback_clip_skip=-2,
                fallback_width=1024, fallback_height=1024, fallback_sampler="euler", fallback_scheduler="normal",
                unique_id=None):
        v = extract_values(parameters, {
            "seed": fallback_seed, "steps": fallback_steps, "cfg": fallback_cfg, "clip_skip": fallback_clip_skip,
            "width": fallback_width, "height": fallback_height, "sampler": fallback_sampler,
            "scheduler": fallback_scheduler,
        })
        debug(steps_report(f"Parameters extractor #{unique_id}", parameters, v))
        return {"ui": {"rig_state": [output_state(v, "fallback_")]},
                "result": (v["seed"], v["steps"], float(v["cfg"]), v["clip_skip"], v["width"], v["height"],
                           v["positive"], v["negative"], v["model"], v["lora_stack"], v["sampler"], v["scheduler"])}
