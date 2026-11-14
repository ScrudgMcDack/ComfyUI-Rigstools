import time

import torch
import torch.nn.functional as F

from ..core import CATEGORY, logger
from ..core import color as cc
from ..core.settings import debug


def _f(default, lo, hi, step, tip):
    return ("FLOAT", {"default": default, "min": lo, "max": hi, "step": step, "tooltip": tip})


class CColorCorrection:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {"tooltip": "Picture to correct"}),
                # first: it decides which of the sliders below are used (old workflows: see rigstools.js)
                "mode": (["manual", "auto"], {"default": "manual",
                         "tooltip": "manual — white_balance, levels and vibrance are set by hand; auto — their strengths "
                                    "and a small exposure correction are chosen for every picture from what it "
                                    "measures (the sliders are then off; manual adjustments still apply on top)"}),
                "strength": _f(1.0, 0.0, 1.0, 0.05, "Overall strength: 0 — the original, 1 — the full correction"),
                "white_balance": _f(0.3, 0.0, 1.0, 0.05, "Removes a colour cast: the average colour of the "
                                    "near-neutral areas is moved towards grey. Saturated colours keep their hue. A warm or cold mood that "
                                    "is meant to be there is a cast too — keep it low for such pictures"),
                "levels": _f(0.5, 0.0, 1.0, 0.05, "Stretches the lightness between the darkest and the lightest "
                             "tones (see levels_clip). Hue and saturation stay"),
                "levels_clip": _f(0.5, 0.0, 5.0, 0.1, "Percent of the darkest / lightest pixels ignored when "
                                  "looking for the black and white points"),
                "vibrance": _f(0.3, 0.0, 1.0, 0.05, "Raises the saturation of dull colours more than of "
                               "saturated ones"),
                "protect_skin": ("BOOLEAN", {"default": True,
                                             "tooltip": "Vibrance hardly touches skin hues, so skin does not glow"}),
                "reference_strength": _f(0.7, 0.0, 1.0, 0.05, "Used only with a reference connected: how much the "
                                         "colours are matched to it (mean and spread of lightness and colour)"),
                "exposure": _f(0.0, -2.0, 2.0, 0.05, "Exposure in stops (linear light)"),
                "contrast": _f(0.0, -1.0, 1.0, 0.05, "Contrast around the mid-grey"),
                "saturation": _f(0.0, -1.0, 1.0, 0.05, "Saturation of all colours"),
                "temperature": _f(0.0, -1.0, 1.0, 0.05, "Colour temperature: + warmer (yellow), − cooler (blue)"),
                "tint": _f(0.0, -1.0, 1.0, 0.05, "Tint: + magenta, − green"),
                "lift": _f(0.0, -0.5, 0.5, 0.01, "Lift: raises (+) or lowers (−) the shadows"),
                "gamma": _f(0.0, -1.0, 1.0, 0.05, "Gamma: brightens (+) or darkens (−) the mid-tones"),
                "gain": _f(0.0, -0.5, 0.5, 0.01, "Gain: brightens (+) or darkens (−) the highlights"),
            },
            "optional": {
                "reference": ("IMAGE", {"tooltip": "Picture whose colours to match — e.g. the image before "
                                                   "upscaling / detailing, when they shifted the colours"}),
                "mask": ("MASK", {"tooltip": "Correct only where the mask is white"}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    CATEGORY = CATEGORY.MAIN.value + CATEGORY.IMAGE.value
    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("IMAGE", "HISTOGRAM")
    DESCRIPTION = (
        "Automatic colour correction: white balance, levels and vibrance, matching to a reference picture, exposure, "
        "contrast, saturation, temperature, tint and lift / gamma / gain. Every picture of a batch is measured on its "
        "own. In auto mode the node also chooses the strengths of white balance, levels and vibrance and a small "
        "exposure correction for every picture.\n"
        "HISTOGRAM shows the RGB histograms of the result (the original as an outline). With Settings → Rigstools → "
        "Debug on, what the automatic steps measured and changed goes to the console."
    )
    FUNCTION = "execute"

    def execute(self, image, strength=1.0, white_balance=0.3, levels=0.5, levels_clip=0.5, vibrance=0.3,
                protect_skin=True, reference_strength=0.7, exposure=0.0, contrast=0.0, saturation=0.0,
                temperature=0.0, tint=0.0, lift=0.0, gamma=0.0, gain=0.0, mode="manual", reference=None, mask=None,
                unique_id=None):
        t0 = time.time()
        src = image.float()
        out, reports = [], []
        for i in range(src.shape[0]):
            rgb = src[i, ..., :3]
            rep = []
            lab = cc.rgb_to_lab(rgb)
            if reference is not None and reference_strength > 0:
                ref = reference[i % reference.shape[0], ..., :3].float().to(rgb.device)
                lab = cc.match_reference(lab, cc.rgb_to_lab(ref), reference_strength, rep)
            wb, lv, vb, ex = white_balance, levels, vibrance, 0.0
            if mode == "auto":           # the strengths come from what this picture measures
                m = cc.measure(lab, levels_clip)
                a = cc.auto_strengths(m)
                wb, lv, vb, ex = a["white_balance"], a["levels"], a["vibrance"], a["exposure"]
                cast = "no neutral areas" if m["cast"] is None else f"cast a {m['cast'][0]:+.1f} b {m['cast'][1]:+.1f}"
                rep.append(f"auto: measured {cast}, black point L {m['black']:.0f}, lightness {m['lightness']:.0f}, "
                           f"chroma {m['chroma']:.0f} → white balance {wb:g}, levels {lv:g}, vibrance {vb:g}, "
                           + (f"exposure {ex:+g}" if ex else "exposure 0"))
            if wb > 0:
                lab = cc.white_balance(lab, wb, rep)
            if lv > 0:
                lab = cc.levels(lab, lv, levels_clip, 100 - levels_clip, rep)
            if vb > 0:
                lab = cc.vibrance(lab, vb, protect_skin, rep)
            res = cc.lab_to_rgb(lab)
            res = cc.manual(res, exposure + ex, contrast, saturation, temperature, tint, lift, gamma, gain)
            if mask is not None:
                m = mask[i % mask.shape[0]] if mask.dim() == 3 else mask
                m = m.float().to(res.device)
                if m.shape != res.shape[:2]:
                    m = F.interpolate(m[None, None], size=res.shape[:2], mode="bilinear", align_corners=False)[0, 0]
                res = rgb + (res - rgb) * m[..., None]
            res = rgb + (res - rgb) * strength
            out.append(res.clamp(0, 1))
            reports.append(f"#{i + 1}: " + ("; ".join(rep) if rep else "no automatic steps"))
        result = torch.stack(out).to(image.dtype)
        if image.shape[-1] == 4:   # keep an alpha channel if there is one
            result = torch.cat([result, image[..., 3:]], dim=-1)
        hist = cc.histogram_image(src[0, ..., :3], result[0, ..., :3])
        auto = ([f"auto mode (strengths chosen per picture)"] if mode == "auto" else
                [f"{k} {v:g}" for k, v in (("white balance", white_balance), ("levels", levels), ("vibrance", vibrance))
                 if v > 0]) + ([f"reference {reference_strength:g}"] if reference is not None and reference_strength > 0 else [])
        manual = [f"{k} {v:+g}" for k, v in (("exposure", exposure), ("contrast", contrast), ("saturation", saturation),
                                             ("temperature", temperature), ("tint", tint), ("lift", lift),
                                             ("gamma", gamma), ("gain", gain)) if v]
        debug("\n".join([f"Color correction #{unique_id}: {src.shape[0]} picture(s) {src.shape[2]}x{src.shape[1]}, "
                          f"strength {strength:g}" + (", with a mask" if mask is not None else "")
                          + f", {time.time() - t0:.1f} s",
                          "  automatic: " + (", ".join(auto) if auto else "off"),
                          "  manual: " + (", ".join(manual) if manual else "none")]
                         + [f"  {r}" for r in reports]))
        return (result, hist)
