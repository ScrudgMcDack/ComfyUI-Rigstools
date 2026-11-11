"""Rebuilds A1111-style parameters text from a ComfyUI API prompt (the "prompt" metadata of an image).

Used when an image has no "parameters" (e.g. saved by the stock Save Image node). The main sampler is
found in the graph and its settings, prompts, checkpoint, LoRA and clip skip are traced back through the
links. Values that cannot be determined reliably (random seeds, wildcards resolved at run time, unknown
nodes) are left out, so the fallbacks of Parameters extractor are used for them instead of a wrong value.
"""
import json
import re
from pathlib import PurePath

MAX_DEPTH = 24

# keys that usually carry the value of simple "value" nodes
VALUE_KEYS = ("value", "text_0", "text", "string", "populated_text", "seed", "noise_seed", "int", "float",
              "number", "size", "positive", "negative", "prompt", "ckpt_name")
# outputs of "Input Parameters (Image Saver)" by slot
IMAGE_SAVER_INPUT_PARAMETERS = ("seed", "steps", "cfg", "sampler", "scheduler", "denoise")
CONDITIONING_KEYS = ("conditioning", "conditioning_to", "conditioning_1", "conditioning_from", "cond")
_NOT_A_SWITCH = object()
SKIP = object()
BASIC_PIPE = ("model", "clip", "vae", "positive", "negative")   # FromBasicPipe outputs


def _stem(name):
    """'a\\b/LoRA v1.5.safetensors' -> 'LoRA v1.5' (only a model extension is cut, a dot in the name stays)."""
    base = str(name).replace("\\", "/").rsplit("/", 1)[-1]
    for ext in (".safetensors", ".ckpt", ".pt", ".pth", ".bin", ".sft", ".gguf"):
        if base.lower().endswith(ext):
            return base[: -len(ext)]
    return base


def _is_link(v):
    return isinstance(v, list) and len(v) == 2 and isinstance(v[1], int)


class _Resolver:
    def __init__(self, prompt: dict, external=None, runtime=None):
        self.p = prompt
        # external(node, slot) -> value, or SKIP: values that come from a file (our image loaders) at run time
        self.external = external
        # runtime.output(node_id, slot) -> what the node output in the current run (core.runtime.Outputs), or None
        self.runtime = runtime if runtime else None
        self.hit = False                                # a run-time value was used (reset by the caller)
        self.file_hit = False                           # a value read from a file was used (reset by the caller)
        # a join (Concatenate…) with a part known only at run time: True — the known parts are joined (the graph
        # walk), False — the whole value is unknown (a connected input: its real value comes when it runs)
        self.partial = True

    def node(self, link):
        return self.p.get(str(link[0])) if _is_link(link) else None

    # ── scalar / string values ──
    def value(self, v, depth=0):
        """Literal as is; a link is followed to the value its source node outputs (None if unknown)."""
        if not _is_link(v):
            return v
        if depth > MAX_DEPTH:
            return None
        n = self.node(v)
        if not n:
            return None
        ct, ins, slot = n.get("class_type", ""), n.get("inputs", {}), v[1]
        if self.runtime:                                # at run time: what the node really output
            out = self.runtime.output(v[0], slot)
            if isinstance(out, (str, int, float)):
                self.hit = True
                return out

        if ct == "Input Parameters (Image Saver)" and slot < len(IMAGE_SAVER_INPUT_PARAMETERS):
            return self.value(ins.get(IMAGE_SAVER_INPUT_PARAMETERS[slot]), depth + 1)
        if ct.startswith("ShowText"):
            shown = ins.get("text_0")
            return shown if isinstance(shown, str) else self.value(ins.get("text"), depth + 1)
        if ct == "StringConcatenate":
            return self._join([ins.get("string_a"), ins.get("string_b")], ins.get("delimiter", ""), depth)
        if ct == "CR Text Concatenate":
            return self._join([ins.get("text1"), ins.get("text2")], ins.get("separator", ""), depth)
        if ct.startswith("JoinStringMulti"):
            count = ins.get("inputcount") or len([k for k in ins if k.startswith("string_")])
            return self._join([ins.get(f"string_{i}") for i in range(1, int(count) + 1)], ins.get("delimiter", ""), depth)
        if "wildcard" in ct.lower() and not isinstance(ins.get("populated_text"), str):
            return None  # resolved at run time, not stored
        if ct.startswith("Checkpoint Loader with Name"):  # slot 3 = name
            return self.value(ins.get("ckpt_name"), depth + 1) if slot == 3 else None
        chosen = self.switch_input(n, depth)
        if chosen is not _NOT_A_SWITCH:
            return self.value(chosen, depth + 1) if chosen is not None else None
        if self.external:
            ext = self.external(self, n, slot)
            if ext is not SKIP:
                if ext is not None:
                    self.file_hit = True
                return ext
        if "load image" in ct.lower() or ct.startswith("LoadImage"):
            return None                                   # values from a file are not in the prompt

        literals = {k: x for k, x in ins.items() if not _is_link(x) and isinstance(x, (str, int, float))}
        links = {k: x for k, x in ins.items() if _is_link(x)}
        for key in VALUE_KEYS:
            if key in literals and (key != "text" or "text_0" not in literals):
                return literals[key]
        if len(literals) == 1:
            return next(iter(literals.values()))
        for key in VALUE_KEYS:                         # e.g. "Lora Prompt Concatenation": the text is its positive
            if key in links:
                return self.value(links[key], depth + 1)
        if len(links) == 1 and not literals:          # pass-through nodes (Any to String, reroute-like)
            return self.value(next(iter(links.values())), depth + 1)
        return None

    def switch_input(self, n, depth=0):
        """For switch nodes returns the selected input (literal or link), None if the choice is unknown,
        _NOT_A_SWITCH for other nodes."""
        ct, ins = n.get("class_type", ""), n.get("inputs", {})
        if "on_true" in ins or "on_false" in ins:                 # Switch any [Crystools] and similar
            flag = self.value(ins.get("boolean"), depth + 1)
            return None if not isinstance(flag, bool) else ins.get("on_true" if flag else "on_false")
        if ct == "ImpactConditionalBranch" or ("tt_value" in ins and "ff_value" in ins):
            flag = self.value(ins.get("cond"), depth + 1)
            return None if not isinstance(flag, bool) else ins.get("tt_value" if flag else "ff_value")
        if ct == "ImpactSwitch" or ("select" in ins and "input1" in ins):
            sel = self.value(ins.get("select"), depth + 1)
            return None if not isinstance(sel, int) else ins.get(f"input{sel}")
        if "Input Switch" in ct and "Input" in ins:               # CR * Input Switch
            sel = self.value(ins.get("Input"), depth + 1)
            if not isinstance(sel, int):
                return None
            for key in (f"text{sel}", f"image{sel}", f"latent{sel}", f"model{sel}", f"clip{sel}",
                        f"conditioning{sel}", f"pipe{sel}", f"vae{sel}", f"input{sel}"):
                if key in ins:
                    return ins[key]
            return None
        return _NOT_A_SWITCH

    def from_pipe(self, link, depth=0):
        """For an output of FromBasicPipe (Impact Pack) returns the link that went into the pipe; _NOT_A_SWITCH for
        other nodes, None when it is not known."""
        n = self.node(link)
        ct = n.get("class_type", "") if n else ""
        if ct not in ("FromBasicPipe", "FromBasicPipe_v2"):
            return _NOT_A_SWITCH
        slot = link[1] - (1 if ct.endswith("_v2") else 0)
        if not 0 <= slot < len(BASIC_PIPE):
            return None
        key, pipe = BASIC_PIPE[slot], n.get("inputs", {}).get("basic_pipe")
        while _is_link(pipe) and depth <= MAX_DEPTH:      # ToBasicPipe, or Edit Basic Pipe with that input set
            pn = self.node(pipe)
            if not pn:
                return None
            ins = pn.get("inputs", {})
            if key in ins:
                return ins[key]
            pipe, depth = ins.get("basic_pipe"), depth + 1
        return None

    def through_switch(self, link, depth=0):
        """Resolves a link that points at a switch node (or a pipe unpacker) to the link of the selected input."""
        while _is_link(link) and depth <= MAX_DEPTH:
            n = self.node(link)
            if not n:
                return link
            chosen = self.switch_input(n, depth)
            if chosen is _NOT_A_SWITCH:
                chosen = self.from_pipe(link, depth)
                if chosen is _NOT_A_SWITCH:
                    return link
            link, depth = chosen, depth + 1
        return link

    def _join(self, parts, delimiter, depth):
        values = []
        for part in parts:
            if part is None:
                continue
            val = self.value(part, depth + 1)
            if val is None:                             # unknown part (known only at run time)
                if not self.partial:
                    return None
                continue                                # the graph walk leaves it out
            values.append(str(val))
        if len(values) > 1:                             # parts joined in the graph: a new value, not the file's
            self.file_hit = False
        return (delimiter or "").join(values) if values else None

    # ── graph walks ──
    def follow(self, link, keys, depth=0):
        """Follows the first existing link among `keys` until a node without them; yields every node passed."""
        while _is_link(link) and depth <= MAX_DEPTH:
            link = self.through_switch(link)
            n = self.node(link)
            if not n:
                return
            yield n, link
            ins = n.get("inputs", {})
            nxt = next((ins[k] for k in keys if _is_link(ins.get(k))), None)
            link, depth = nxt, depth + 1

    def prompt_text(self, link, which):
        """Text behind a positive/negative conditioning link."""
        for n, via in self.follow(link, ()):
            ins = n.get("inputs", {})
            if "text" in ins or "text_g" in ins:          # a text encoder
                text = self.value(ins.get("text"))
                if (text is None or text == "") and "text_g" in ins:
                    text = self.value(ins.get("text_g"))
                return text if isinstance(text, str) else None
            # conditioning pass-through (ControlNet apply, set area…)
            if which in ins and _is_link(ins[which]) and ("positive" in ins and "negative" in ins):
                return self.prompt_text(ins[which], which)
            # two encodings joined (ConditioningConcat / Combine): closest A1111 form is "a BREAK b"
            pair = [ins.get(k) for k in (("conditioning_to", "conditioning_from") if "conditioning_to" in ins
                                         else ("conditioning_1", "conditioning_2")) if _is_link(ins.get(k))]
            if len(pair) == 2:
                texts = [self.prompt_text(x, which) for x in pair]
                return None if any(t is None for t in texts) else " BREAK ".join(texts)
            nxt = next((ins[k] for k in CONDITIONING_KEYS if _is_link(ins.get(k))), None)
            return self.prompt_text(nxt, which) if nxt else None
        return None

    def model_and_loras(self, link):
        loras = []
        for n, _ in self.follow(link, ("model", "unet", "MODEL")):
            ct, ins = n.get("class_type", ""), n.get("inputs", {})
            for key in ("ckpt_name", "unet_name"):
                if key in ins:
                    name = self.value(ins[key])
                    return (name if isinstance(name, str) else None), list(reversed(loras))
            if "lora_name" in ins:                        # LoraLoader / LoraLoaderModelOnly
                name = self.value(ins["lora_name"])
                weight = self.value(ins.get("strength_model", 1.0))
                if isinstance(name, str) and name != "None":
                    loras.append((_stem(name), weight))
            elif isinstance(ins.get("loras"), (dict, list)):  # LoRA Manager loaders: {"__value__": [...]} or [...]
                items = ins["loras"].get("__value__", []) if isinstance(ins["loras"], dict) else ins["loras"]
                for item in reversed(items or []):
                    if isinstance(item, dict) and item.get("active", True) and item.get("name"):
                        loras.append((item["name"], item.get("strength", 1.0)))
            else:                                         # Power Lora Loader (rgthree): lora_1 = {on, lora, strength}
                rows = sorted(((k, v) for k, v in ins.items() if k.startswith("lora_") and isinstance(v, dict)
                               and "lora" in v), key=lambda kv: int(kv[0][5:]) if kv[0][5:].isdigit() else 0)
                for _, item in reversed(rows):
                    name = item.get("lora")
                    if item.get("on", True) and isinstance(name, str) and name not in ("", "None"):
                        loras.append((_stem(name), item.get("strength", 1.0)))
        return None, list(reversed(loras))

    def clip_skip(self, encoder_link):
        n = self.node(encoder_link)
        clip = n.get("inputs", {}).get("clip") if n else None
        for node, _ in self.follow(clip, ("clip",)):
            if node.get("class_type") == "CLIPSetLastLayer":
                v = self.value(node["inputs"].get("stop_at_clip_layer"))
                return v if isinstance(v, int) else None
        return None

    def empty_latent(self, link):
        """The node of the empty latent a sampler starts from (txt2img), None when it starts from a picture
        (img2img). Only the kind of the node counts — its size may be known only at run time."""
        for n, _ in self.follow(link, ("samples", "latent", "latent_image", "LATENT")):
            ins, ct = n.get("inputs", {}), n.get("class_type", "")
            if "width" in ins and "height" in ins and (ct.startswith("Empty") or "Aspect Ratio" in ct or "Empty Latent" in ct):
                return n
        return None

    def latent_size(self, link):
        """Size of the empty latent a sampler starts from (txt2img); None for img2img / a size not known yet."""
        n = self.empty_latent(link)
        if not n:
            return None
        ins = n.get("inputs", {})
        ratio = self.value(ins.get("aspect_ratio")) if "aspect_ratio" in ins else None
        m = re.search(r"(\d{3,5})\s*x\s*(\d{3,5})", ratio) if isinstance(ratio, str) else None
        if m and "custom" not in ratio.lower():   # CR SDXL Aspect Ratio and similar: the preset wins
            w, h = int(m.group(1)), int(m.group(2))
            if str(self.value(ins.get("swap_dimensions", "Off"))).lower() == "on":
                w, h = h, w
            return w, h
        w, h = self.value(ins["width"]), self.value(ins["height"])
        return (w, h) if isinstance(w, int) and isinstance(h, int) else None


def _sampler_nodes(prompt):
    for nid, n in prompt.items():
        ins = n.get("inputs", {}) if isinstance(n, dict) else {}
        if "positive" in ins and "negative" in ins and "steps" in ins and "cfg" in ins and "sampler_name" in ins \
                and ("seed" in ins or "noise_seed" in ins):
            yield nid, n


def _main_sampler(prompt, r):
    """Returns (sampler node, is_refiner). A refiner is a detailer / upscaler pass with no txt2img sampler:
    its prompts, model and LoRA are still those of the image, but its seed/steps/cfg are not the generation ones."""
    best, best_score = None, None
    for nid, n in _sampler_nodes(prompt):
        ins, ct = n["inputs"], n.get("class_type", "")
        score = 0
        if r.empty_latent(ins.get("latent_image")):
            score += 4                                    # txt2img from an empty latent
        denoise = r.value(ins.get("denoise", 1.0))
        if not isinstance(denoise, (int, float)) or denoise >= 0.999:
            score += 2
        if any(s in ct for s in ("Detailer", "Upscale", "Detail")):
            score -= 3
        key = (score, -int(nid) if str(nid).isdigit() else 0)
        if best_score is None or key > best_score:
            best, best_score = n, key
    return best, (best_score is not None and best_score[0] < 0)


def parameters_from_prompt(prompt) -> str:
    """Returns A1111-style parameters text built from a ComfyUI API prompt, or "" if no sampler is found."""
    if isinstance(prompt, str):
        try:
            prompt = json.loads(prompt)
        except ValueError:
            return ""
    if not isinstance(prompt, dict) or not prompt:
        return ""
    r = _Resolver(prompt)
    s, refiner = _main_sampler(prompt, r)
    if not s:
        return ""
    ins = s["inputs"]

    positive = r.prompt_text(ins.get("positive"), "positive")
    negative = r.prompt_text(ins.get("negative"), "negative")
    seed = r.value(ins.get("seed", ins.get("noise_seed")))
    steps, cfg = r.value(ins.get("steps")), r.value(ins.get("cfg"))
    sampler, scheduler = r.value(ins.get("sampler_name")), r.value(ins.get("scheduler"))
    size = r.latent_size(ins.get("latent_image"))
    model, loras = r.model_and_loras(ins.get("model"))
    clip = r.clip_skip(ins.get("positive")) if _is_link(ins.get("positive")) else None
    if clip is None:
        enc = next((n for n, _ in r.follow(ins.get("positive"), CONDITIONING_KEYS) if "clip" in n.get("inputs", {})), None)
        if enc:
            for node, _ in r.follow(enc["inputs"].get("clip"), ("clip",)):
                if node.get("class_type") == "CLIPSetLastLayer":
                    v = r.value(node["inputs"].get("stop_at_clip_layer"))
                    clip = v if isinstance(v, int) else None
                    break

    if refiner:  # only a detailer / upscaler pass in the graph: its sampling settings are not the generation ones
        seed = steps = cfg = sampler = scheduler = None
    settings = []
    if isinstance(steps, int):
        settings.append(f"Steps: {steps}")
    if isinstance(sampler, str):
        settings.append(f"Sampler: {sampler}")
    if isinstance(scheduler, str):
        settings.append(f"Schedule type: {scheduler}")
    if isinstance(cfg, (int, float)):
        settings.append(f"CFG scale: {cfg}")
    if isinstance(seed, int) and seed >= 0:               # negative = "random" in some seed nodes
        settings.append(f"Seed: {seed}")
    if size:
        settings.append(f"Size: {size[0]}x{size[1]}")
    if isinstance(clip, int) and clip:
        settings.append(f"Clip skip: {abs(clip)}")
    if loras:
        tags = " ".join(f"<lora:{name}:{w}>" for name, w in loras)
        settings.append(f"Lora stack: {tags}")
    if model:
        settings.append(f"Model: {model}")
    settings.append("Version: ComfyUI (rebuilt from prompt)")

    text = positive if isinstance(positive, str) else ""
    if isinstance(negative, str):
        text += f"\nNegative prompt: {negative}"
    return text + "\n" + ", ".join(settings)
