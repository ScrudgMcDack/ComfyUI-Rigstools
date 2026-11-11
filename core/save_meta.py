"""
What "Save image [Rigstools]" writes into a file: the generation parameters are collected from the ComfyUI graph
(the API prompt) by walking back from the image that is saved, so nothing has to be wired by hand.

collect()      -> values + where each one came from ("graph" / "input" / "missing"), LoRA, passes
a1111_text()   -> A1111-style parameters text (what A1111, Forge, Civitai and our loaders read)
render_name()  -> file name from the pattern (%date, %model, %seed, %counter<4>, …)

No ComfyUI imports at module level except through the helpers passed in, so it is easy to test.
"""

import re
from datetime import datetime
from pathlib import PurePath

from .prompt_graph import _Resolver, _is_link, CONDITIONING_KEYS

# ComfyUI sampler -> A1111 / Civitai name (the reader in nodes/parameters.py maps them back)
A1111_SAMPLER = {
    "euler_ancestral": "Euler a", "euler": "Euler", "lms": "LMS", "heun": "Heun", "dpm_2": "DPM2",
    "dpm_2_ancestral": "DPM2 a", "dpmpp_2s_ancestral": "DPM++ 2S a", "dpmpp_2m": "DPM++ 2M", "dpmpp_sde": "DPM++ SDE",
    "dpmpp_2m_sde": "DPM++ 2M SDE", "dpmpp_3m_sde": "DPM++ 3M SDE", "dpmpp_2m_sde_heun": "DPM++ 2M SDE Heun",
    "dpm_fast": "DPM fast", "dpm_adaptive": "DPM adaptive", "ddim": "DDIM", "plms": "PLMS", "uni_pc": "UniPC",
    "uni_pc_bh2": "UniPC", "lcm": "LCM", "ddpm": "DDPM", "deis": "DEIS", "ipndm": "iPNDM", "ipndm_v": "iPNDM_v",
}
# ComfyUI scheduler -> A1111 "Schedule type"
A1111_SCHEDULE = {
    "karras": "Karras", "exponential": "Exponential", "sgm_uniform": "SGM Uniform", "simple": "Simple",
    "normal": "Normal", "beta": "Beta", "kl_optimal": "KL Optimal", "ddim_uniform": "DDIM",
}

FIELDS = ("positive", "negative", "seed", "steps", "cfg", "sampler", "scheduler", "clip_skip", "model", "denoise",
          "width", "height")
PREFER = ("input", "graph", "file")   # the "Preference" switch of Save image: which source wins
# override inputs of the node -> field
INPUTS = {"positive": "positive", "negative": "negative", "seed": "seed", "steps": "steps", "cfg": "cfg",
          "sampler_name": "sampler", "scheduler": "scheduler", "clip_skip": "clip_skip", "model_name": "model",
          "denoise": "denoise"}
MODEL_EXT = (".safetensors", ".ckpt", ".pt", ".pth", ".bin", ".sft", ".gguf", ".onnx")


def model_stem(name):
    """File name without the folder and a model extension: 'a/GENESIS_MK0.4' -> 'GENESIS_MK0.4' (a dot in the
    name is kept), 'x/model.safetensors' -> 'model'."""
    base = str(name or "").replace("\\", "/").rsplit("/", 1)[-1]
    low = base.lower()
    for ext in MODEL_EXT:
        if low.endswith(ext):
            return base[: -len(ext)]
    return base


EMBEDDING = re.compile(r"embedding:([^,\s()\[\]:]+)", re.IGNORECASE)
LORA_TAG = re.compile(r"<lora:([^>:]+)(?::([^>:]+))?[^>]*>", re.IGNORECASE)


def is_sampler(n):
    ins = n.get("inputs", {}) if isinstance(n, dict) else {}
    return "steps" in ins and "cfg" in ins and "sampler_name" in ins and ("seed" in ins or "noise_seed" in ins)


def _ancestors(prompt, link):
    """{node id: distance} of everything the linked output depends on (breadth-first, shortest distance)."""
    depth, queue = {}, [(str(link[0]), 1)] if _is_link(link) else []
    while queue:
        nid, d = queue.pop(0)
        if nid in depth or nid not in prompt:
            continue
        depth[nid] = d
        for v in (prompt[nid].get("inputs") or {}).values():
            if _is_link(v):
                queue.append((str(v[0]), d + 1))
    return depth


def _kind(ct):
    low = ct.lower()
    if "upscale" in low:
        return "upscale"
    if "detailer" in low or "detail" in low:
        return "detailer"
    return "sampler"


INPAINT_WORDS = ("inpaint", "setlatentnoisemask")


def _inpaint(prompt, n):
    """True for a sampler that repaints a part of the picture: its latent or its conditioning comes through an inpaint
    node (VAEEncodeForInpaint, SetLatentNoiseMask, InpaintModelConditioning, a ControlNet fed by InpaintPreprocessor…).
    The walk does not go through other samplers, nor into model / clip / vae."""
    ins = n.get("inputs", {})
    queue, seen = [ins.get(k) for k in ("latent_image", "positive") if _is_link(ins.get(k))], set()
    while queue:
        link = queue.pop()
        nid = str(link[0])
        if nid in seen or nid not in prompt or len(seen) > 200:
            continue
        seen.add(nid)
        m = prompt[nid]
        if any(w in m.get("class_type", "").lower() for w in INPAINT_WORDS):
            return True
        if is_sampler(m):
            continue
        queue += [v for k, v in m.get("inputs", {}).items() if _is_link(v) and k not in ("model", "clip", "vae")]
    return False


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def collect(prompt, node_id, overrides=None, external=None, source=None, runtime=None, prefer="input"):
    """Values for the save node `node_id` of the API prompt.
    source(resolver, image link) -> {"size": (w, h) | None, "values": {...} | None, "file": name}: what a picture
    loaded from a file brings (its size and its generation data) — for img2img and for re-saving a loaded picture.
    overrides: {field: value} of the connected override inputs (at run time); when None they are resolved from
    the prompt (preview before a run). A connected input always wins over the graph.
    runtime: core.runtime.Outputs at run time — the graph walk then takes what the nodes really output in this run
    (e.g. the text a concatenation gave), the field source is "runtime". Returns a dict, see the keys below."""
    out = {"fields": {k: {"v": None, "src": "missing"} for k in FIELDS}, "loras": [], "stages": [],
           "hires": None, "embeddings": [], "lora_src": "graph"}
    node = prompt.get(str(node_id)) if isinstance(prompt, dict) else None
    if not node:
        return out
    r = _Resolver(prompt, external, runtime)
    ins = node.get("inputs", {})
    depth = _ancestors(prompt, ins.get("images"))

    samplers = [(nid, prompt[nid]) for nid in depth if is_sampler(prompt[nid])]
    ids = {nid for nid, _ in samplers}
    memo = {}

    def upstream(nid):                                 # everything a node depends on (without itself)
        if nid not in memo:
            memo[nid] = set(_ancestors(prompt, [nid, 0])) - {nid}
        return memo[nid]

    before = {nid: upstream(nid) & ids for nid in ids}   # samplers that run before this one
    order = sorted(samplers, key=lambda x: len(before[x[0]]))          # the order they run in
    kinds = {nid: "inpaint" if _kind(n.get("class_type", "")) == "sampler" and _inpaint(prompt, n)
             else _kind(n.get("class_type", "")) for nid, n in samplers}
    # Passes that redraw the whole picture: samplers and upscalers. Detailers and inpaint samplers repaint only a part
    # and are not taken. txt2img (a generation from an empty latent): the main values come from it, the Hires fields
    # from the last whole pass after it. img2img (no such generation): the main values come from the last whole
    # pass — it made the picture; no Hires fields.
    full = [x for x in order if kinds[x[0]] in ("sampler", "upscale")]
    gen = [x for x in full if kinds[x[0]] == "sampler" and r.empty_latent(x[1]["inputs"].get("latent_image"))]
    base = hires_item = None
    if gen:
        base = gen[0]
        after = [x for x in full if base[0] in before[x[0]]]
        hires_item = after[-1] if after else None
    elif full:
        base = full[-1]
    out["base_id"] = base[0] if base else None

    prev = None                                          # generation data of the loaded picture (earlier pass)

    def put(field, value, src="graph"):
        if src == "graph" and r.hit:                   # the value came from this run's node outputs
            src = "runtime"
        elif src == "graph" and r.file_hit:            # read from a file (Parameters extractor, our loaders)
            src = "file"
        r.hit = r.file_hit = False
        if value is not None and value != "":
            out["fields"][field] = {"v": value, "src": src}

    if base:
        nid, n = base
        i = n["inputs"]
        put("positive", r.prompt_text(i.get("positive"), "positive"))
        put("negative", r.prompt_text(i.get("negative"), "negative"))
        seed = r.value(i.get("seed", i.get("noise_seed")))
        if isinstance(seed, int) and seed >= 0:
            put("seed", seed)
        put("steps", _num(r.value(i.get("steps"))))
        put("cfg", _num(r.value(i.get("cfg"))))
        s = r.value(i.get("sampler_name"))
        put("sampler", s if isinstance(s, str) else None)
        s = r.value(i.get("scheduler"))
        put("scheduler", s if isinstance(s, str) else None)
        model, loras = r.model_and_loras(i.get("model"))
        put("model", model if isinstance(model, str) else None)
        out["loras"] = [{"name": nm, "weight": _weight(w)} for nm, w in loras]
        size = r.latent_size(i.get("latent_image"))
        if size:
            put("width", size[0])
            put("height", size[1])
        if source:                                     # img2img: the picture that was encoded
            enc = next((x for x, _ in r.follow(i.get("latent_image"), ("samples", "latent", "latent_image", "LATENT"))
                        if _is_link(x.get("inputs", {}).get("pixels"))), None)
            # no latent (Ultimate SD Upscale and the like take the picture itself): the picture input of the pass
            pic = enc["inputs"]["pixels"] if enc else next((i[k] for k in ("image", "upscaled_image", "pixels")
                                                            if _is_link(i.get(k))), None)
            src = source(r, pic) if pic else None
            r.hit = r.file_hit = False
            prev = (src or {}).get("values")
            # prompts the graph does not give: those of the loaded picture
            for k in ("positive", "negative"):
                if out["fields"][k]["v"] is None and prev and prev.get(k) and k not in set(prev.get("missing") or []):
                    put(k, prev[k], "file")
            if not size and src and src.get("size"):  # its size
                put("width", src["size"][0], "file" if src.get("from_file") else "graph")
                put("height", src["size"][1], "file" if src.get("from_file") else "graph")
        d = _num(r.value(i.get("denoise", 1.0)))
        put("denoise", d if d is not None else 1.0)
        clip = None
        enc = next((x for x, _ in r.follow(i.get("positive"), CONDITIONING_KEYS) if "clip" in x.get("inputs", {})), None)
        if enc:
            for x, _ in r.follow(enc["inputs"].get("clip"), ("clip",)):
                if x.get("class_type") == "CLIPSetLastLayer":
                    v = r.value(x["inputs"].get("stop_at_clip_layer"))
                    clip = v if isinstance(v, int) else None
                    break
        put("clip_skip", clip)

        # all passes in the order they run, with what each was used for (the log shows them)
        for sid, sn in order:
            si = sn["inputs"]
            out["stages"].append({
                "id": sid, "type": sn.get("class_type", ""), "kind": kinds[sid],
                "used": "main" if sid == nid else "hires" if hires_item and sid == hires_item[0] else None,
                "steps": _num(r.value(si.get("steps"))), "cfg": _num(r.value(si.get("cfg"))),
                "denoise": _num(r.value(si.get("denoise", 1.0))), "upscale_by": _num(r.value(si.get("upscale_by"))),
            })
        hires = next((st for st in out["stages"] if st["used"] == "hires"), None)
        if hires:
            # the upscale model used for the Hires pass: of the upscale nodes after the base pass and before the Hires
            # one that take an upscale model loader, the one closest to the Hires pass
            users = []
            for x in depth:
                n = prompt[x]
                if "upscale" not in n.get("class_type", "").lower() or nid not in upstream(x) \
                        or (x != hires["id"] and x not in upstream(hires["id"])):
                    continue
                for v in n.get("inputs", {}).values():
                    src = r.node(v) if _is_link(v) else None
                    if src and "model_name" in src.get("inputs", {}) and "upscale" in src.get("class_type", "").lower():
                        users.append((len(upstream(x) & ids), src))
            name = r.value(max(users, key=lambda t: t[0])[1]["inputs"]["model_name"]) if users else None
            out["hires"] = {"steps": hires["steps"], "denoise": hires["denoise"], "upscale_by": hires["upscale_by"],
                            "upscaler": model_stem(name) if isinstance(name, str) else None,
                            "type": hires["type"]}

    # no sampler above the picture (a loaded picture is upscaled / corrected and saved again): the generation data
    # of the source file
    if not base and source:
        src = source(r, ins.get("images"))
        vals = (src or {}).get("values")
        if vals:
            prev = vals
            out["source_file"] = src.get("file")
            missing = set(vals.get("missing") or [])
            for k in ("positive", "negative", "seed", "steps", "cfg", "sampler", "scheduler", "clip_skip", "model",
                      "width", "height"):
                if k not in missing:
                    put(k, vals.get("model_text") or vals.get(k) if k == "model" else vals.get(k), "file")

    # override inputs (connected wires)
    if overrides is None:
        overrides = {}
        r.partial = False                              # a connected input: unknown until it runs, never a part
        for key, field in INPUTS.items():
            if _is_link(ins.get(key)):
                overrides[field] = r.value(ins[key])
        if _is_link(ins.get("lora_stack")):
            overrides["lora_stack"] = r.value(ins["lora_stack"])

    # Which source wins (the "Preference" switch of the node): the preferred one first, then the others in the usual
    # order input → graph → file. input (default): a connected input, else the graph walk (which falls back to the
    # source file itself), else the file; graph: the graph walk, else an input, else the file; file: the generation
    # data of the source picture, else an input, else the graph. A connected input counts even when its value comes
    # only when it runs. The size never comes from the source file here: an upscaled picture has another size.
    prefer = prefer if prefer in PREFER else "input"
    out["prefer"] = prefer
    G = {k: dict(v) for k, v in out["fields"].items()}
    I = {f: {"v": v if v is not None and v != "" else None, "src": "input"}
         for f, v in overrides.items() if f in out["fields"]}
    F = {}
    if prev:
        missing = set(prev.get("missing") or [])
        for k in FIELDS:
            if k in ("width", "height") or k in missing:
                continue
            v = prev.get("model_text") or prev.get(k) if k == "model" else prev.get(k)
            if v is not None and v != "":
                F[k] = {"v": v, "src": "file"}
    order = {"input": (I, G, F), "graph": (G, I, F), "file": (F, I, G)}[prefer]
    for k in out["fields"]:
        pick = next((S[k] for S in order if k in S and (S is I or S[k]["v"] is not None)
                     and not (S is F and k in ("width", "height"))), None)
        out["fields"][k] = pick if pick else G[k]

    # LoRA lists of the three sources.
    # input: the lora_stack input — it replaces the whole list.
    wired_list = None
    v = overrides.get("lora_stack")
    if isinstance(v, str):
        wired_list = [{"name": model_stem(m[0].strip()), "weight": _weight(m[1])} for m in LORA_TAG.findall(v)]
    # graph: the loaders of this pass, preceded by the LoRA of earlier passes — of the loaded picture (<lora:…> tags
    # in its positive prompt, then its Lora stack) and <lora:…> tags in the current positive prompt; they ran first.
    # from: "file_prompt" / "stack" — an earlier pass (the loaded picture), "prompt" — a tag in this pass's prompt.
    # A LoRA met twice keeps the entry of this pass, else the first one.
    graph_list, graph_src = list(out["loras"]), "graph"
    earlier = []
    if prev:
        earlier += [(m, "file_prompt") for m in LORA_TAG.findall(prev.get("positive") or "")]
        earlier += [(m, "stack") for m in LORA_TAG.findall(prev.get("lora_stack") or "")]
    pos = out["fields"]["positive"]["v"]
    earlier += [(m, "prompt") for m in LORA_TAG.findall(pos if isinstance(pos, str) else "")]
    have = {l["name"].lower() for l in graph_list}
    added = []
    for m, origin in earlier:
        name = model_stem(m[0].strip())
        if name and name.lower() not in have:
            have.add(name.lower())
            added.append({"name": name, "weight": _weight(m[1]), "from": origin})
    if added and not graph_list and not base:
        graph_src = "file"                               # a loaded picture saved again: all its LoRA are the file's
    graph_list = added + graph_list
    # file: the LoRA of the source picture only
    file_list, have = [], set()
    if prev:
        for m in LORA_TAG.findall(prev.get("positive") or "") + LORA_TAG.findall(prev.get("lora_stack") or ""):
            name = model_stem(m[0].strip())
            if name and name.lower() not in have:
                have.add(name.lower())
                file_list.append({"name": name, "weight": _weight(m[1])})
    lists = {"input": (wired_list, "input"), "graph": (graph_list, graph_src), "file": (file_list, "file")}
    seq = {"input": ("input", "graph", "file"), "graph": ("graph", "input", "file"),
           "file": ("file", "input", "graph")}[prefer]
    # a connected lora_stack counts even when empty; the graph and the file only when they found LoRA
    # (with the input preferred, the graph list is taken as it is: no LoRA there is a valid answer)
    for key in seq:
        lst, src = lists[key]
        if lst is None:
            continue
        if lst or key == "input" or (prefer == "input" and key == "graph"):
            out["loras"], out["lora_src"] = lst, src
            break
    else:
        out["loras"], out["lora_src"] = graph_list, graph_src

    texts = [out["fields"][k]["v"] for k in ("positive", "negative") if isinstance(out["fields"][k]["v"], str)]
    seen = []
    for t in texts:
        for e in EMBEDDING.findall(t):
            name = model_stem(e)
            if name not in seen:
                seen.append(name)
    out["embeddings"] = seen
    return out


def _weight(text):
    try:
        return float(str(text or "1").split(":")[0])
    except ValueError:
        return 1.0


def _fmt(v):
    if isinstance(v, float):
        return f"{v:g}" if abs(v - round(v, 4)) < 1e-9 else f"{v:.4g}"
    return str(v)


def _quote(text):
    """A1111 quotes a value that has commas, colons or quotes in it."""
    text = str(text)
    if any(ch in text for ch in ',:"\n'):
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    return text


def a1111_text(info, final_size=None, hashes=None):
    """Parameters text from collect() output. final_size: (w, h) of the saved picture; hashes: {"model": h10,
    "loras": {name: h10}, "embeddings": {name: h10}}. Returns (text, used_fields)."""
    f = {k: v["v"] for k, v in info["fields"].items()}
    hashes = hashes or {}
    parts = []
    if isinstance(f["steps"], (int, float)):
        parts.append(("Steps", _fmt(f["steps"])))
    if f["sampler"]:
        s = str(f["sampler"]).replace("_gpu", "")
        parts.append(("Sampler", A1111_SAMPLER.get(s, s)))
    if f["scheduler"]:
        parts.append(("Schedule type", A1111_SCHEDULE.get(str(f["scheduler"]), str(f["scheduler"]))))
    if isinstance(f["cfg"], (int, float)):
        parts.append(("CFG scale", f"{float(f['cfg']):.1f}" if float(f["cfg"]).is_integer() else _fmt(f["cfg"])))
    if isinstance(f["seed"], int):
        parts.append(("Seed", str(f["seed"])))
    base_w, base_h = f["width"], f["height"]
    hires = info.get("hires")
    if not (isinstance(base_w, int) and isinstance(base_h, int)):
        base_w, base_h = final_size if final_size else (None, None)
        if hires and final_size:      # no empty latent: the size before the upscale is not known
            hires = dict(hires, unknown_base=True)
    if base_w:
        parts.append(("Size", f"{base_w}x{base_h}"))
    # a resource with a Civitai version id goes only into "Civitai resources" (as Image Saver does), the others are
    # found by their hashes — so Civitai does not list a model twice
    by_id = {(r.get("_kind"), r.get("_name")) for r in hashes.get("resources") or []}
    model_hash = hashes.get("model") if ("model", model_stem(str(f["model"] or ""))) not in by_id else None
    if model_hash:
        parts.append(("Model hash", model_hash))
    if f["model"]:
        parts.append(("Model", _quote(model_stem(str(f["model"])))))
    denoise = None
    if hires and isinstance(hires.get("denoise"), (int, float)):
        denoise = hires["denoise"]
    elif isinstance(f["denoise"], (int, float)) and f["denoise"] < 0.999:
        denoise = f["denoise"]
    if denoise is not None:
        parts.append(("Denoising strength", _fmt(denoise)))
    if isinstance(f["clip_skip"], int) and f["clip_skip"]:
        parts.append(("Clip skip", str(abs(f["clip_skip"]))))
    if hires:
        scale = hires.get("upscale_by")
        if not scale and final_size and base_w and not hires.get("unknown_base"):
            scale = round(final_size[0] / base_w, 2)
        if scale and scale != 1:
            parts.append(("Hires upscale", _fmt(scale)))
        if isinstance(hires.get("steps"), int):
            parts.append(("Hires steps", str(hires["steps"])))
        if hires.get("upscaler"):
            parts.append(("Hires upscaler", _quote(hires["upscaler"])))
    loras = info.get("loras") or []
    lh = {n: h for n, h in (hashes.get("loras") or {}).items() if ("lora", n) not in by_id}
    if lh:
        parts.append(("Lora hashes", '"' + ", ".join(f"{n}: {h}" for n, h in lh.items()) + '"'))
    th = {n: h for n, h in (hashes.get("embeddings") or {}).items() if ("embedding", n) not in by_id}
    if th:
        parts.append(("TI hashes", '"' + ", ".join(f"{n}: {h}" for n, h in th.items()) + '"'))
    if loras:   # read back by our loaders (LORA_STACK output); A1111 and Civitai keep unknown keys as they are
        parts.append(("Lora stack", _quote(" ".join(f"<lora:{l['name']}:{_fmt(l['weight'])}>" for l in loras))))
    civ = {}
    if model_hash:
        civ["model"] = model_hash
    civ.update({f"LORA:{n}": h for n, h in lh.items()})
    civ.update({f"embed:{n}": h for n, h in th.items()})
    if civ:
        import json
        parts.append(("Hashes", json.dumps(civ, separators=(",", ":"))))
    if hashes.get("resources"):   # Civitai version ids and the LoRA weights (Civitai reads the weights only here)
        import json
        res = [{k: v for k, v in r.items() if not k.startswith("_")} for r in hashes["resources"]]
        parts.append(("Civitai resources", json.dumps(res, separators=(",", ":"))))
    parts.append(("Version", "ComfyUI"))

    text = (f["positive"] or "").strip()
    text += "\nNegative prompt: " + (f["negative"] or "").strip() if f["negative"] else ""
    return text + "\n" + ", ".join(f"{k}: {v}" for k, v in parts), [k for k, _ in parts]


# ---------------------------------------------------------------- file names

VAR = re.compile(r"%(date|time|model|seed|steps|cfg|sampler|scheduler|width|height|counter)(?:<([^>]*)>)?")
UNSAFE = re.compile(r'[<>:"|?*\x02-\x1f]')   # \x00 marks %counter, \x01 a value known only when saving
TIME_CODES = re.compile(r"%[HIMSpfXcT]")


def render_name(pattern, values, now=None, counter=None, unknown=()):
    """Pattern -> text. %counter is left as '\\0' (a marker) when counter is None, so the caller can find the next
    free number. %date<fmt> takes a strftime format. Keys in `unknown` (the preview before a run: "time", "width",
    "height") become '\\x01key\\x01' markers — shown as [key], their value is known only when saving."""
    now = now or datetime.now()

    def sub(m):
        key, arg = m.group(1), m.group(2)
        if key in unknown:
            return "\x01" + key + "\x01"
        if key == "date":
            if arg and "time" in unknown and TIME_CODES.search(arg):   # the time part is known only when saving
                arg = re.sub(r"(?:%[HIMSpfXcT](?:[^%A-Za-z0-9](?=%[HIMSpfXcT]))?)+", "\x01time\x01", arg)
            try:
                return now.strftime(arg) if arg else now.strftime("%Y-%m-%d")
            except ValueError:
                return now.strftime("%Y-%m-%d")
        if key == "time":
            return now.strftime("%H%M%S")
        if key == "counter":
            if counter is None:
                return "\0" + (arg or "") + "\0"
            width = int(arg) if arg and arg.isdigit() else 0
            return str(counter).zfill(width)
        v = values.get(key)
        if v is None or v == "":
            return "unknown"
        if key == "model":
            v = model_stem(str(v))
        return _fmt(v)

    return VAR.sub(sub, pattern or "")


def clean_part(text):
    text = UNSAFE.sub("", text.replace("\\", "/"))
    parts = [p.strip().rstrip(". ") for p in text.split("/")]
    return "/".join(p for p in parts if p and p not in (".", ".."))
