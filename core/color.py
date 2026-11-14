"""
Colour correction maths for "Color correction [Rigstools]" (torch only, works on any device, batch-safe).

Images are ComfyUI IMAGE tensors: [B, H, W, 3], sRGB, 0..1. Every picture of a batch gets its own statistics.
Most work is done in CIE Lab (D65): L = lightness 0..100, a / b = green–red / blue–yellow.

Auto steps (each with its own strength 0..1; 0 = off):
  white balance  — the average colour of the near-neutral pixels is moved towards grey (removes a colour cast);
  levels         — lightness is stretched between low / high percentiles (keeps the hue);
  vibrance       — chroma of dull colours is raised more than of saturated ones, skin hues are protected;
  reference      — mean and spread of L, a, b are matched to a reference picture (e.g. the one before upscaling).
Manual adjustments come after the auto steps: exposure, contrast, saturation, temperature, tint, lift / gamma / gain.

Auto mode: the strengths of white balance, levels and vibrance and a small exposure correction are chosen for every
picture from what it measures (auto_strengths). The rules were fitted to the Auto mode of Easy Color Corrector on
25 SDXL generations: a warm cast is taken out gently, a cool one is left, a picture with a raised black point gets
less stretching, a dull one more vibrance, a dark one is kept dark.
"""

import math

import torch
import torch.nn.functional as F

# ---------------------------------------------------------------- sRGB <-> Lab

_M_RGB2XYZ = torch.tensor([[0.4124564, 0.3575761, 0.1804375],
                           [0.2126729, 0.7151522, 0.0721750],
                           [0.0193339, 0.1191920, 0.9503041]])
_M_XYZ2RGB = torch.linalg.inv(_M_RGB2XYZ)
_WHITE = torch.tensor([0.95047, 1.0, 1.08883])


def _lin(x):
    return torch.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055).clamp(min=0) ** 2.4)


def _gam(x):
    x = x.clamp(min=0)
    return torch.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


def rgb_to_lab(rgb):
    m = _M_RGB2XYZ.to(rgb)
    xyz = _lin(rgb) @ m.T / _WHITE.to(rgb)
    e = 216 / 24389
    k = 24389 / 27
    f = torch.where(xyz > e, xyz.clamp(min=1e-12) ** (1 / 3), (k * xyz + 16) / 116)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return torch.stack([L, a, b], dim=-1)


def lab_to_rgb(lab):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (L + 16) / 116
    fx = fy + a / 500
    fz = fy - b / 200
    e = 216 / 24389
    k = 24389 / 27
    xr = torch.where(fx ** 3 > e, fx ** 3, (116 * fx - 16) / k)
    yr = torch.where(L > k * e, fy ** 3, L / k)
    zr = torch.where(fz ** 3 > e, fz ** 3, (116 * fz - 16) / k)
    xyz = torch.stack([xr, yr, zr], dim=-1) * _WHITE.to(lab)
    rgb = xyz @ _M_XYZ2RGB.to(lab).T
    return _gam(rgb).clamp(0, 1)


# ---------------------------------------------------------------- statistics

def _sample(x, limit=1_000_000):
    """Flattened values (…, C) of one picture, thinned out to at most `limit` rows (torch.quantile has a size limit)."""
    flat = x.reshape(-1, x.shape[-1])
    step = max(1, math.ceil(flat.shape[0] / limit))
    return flat[::step]


def _weighted_mean(v, w):
    s = w.sum()
    return (v * w[:, None]).sum(0) / s if s > 0 else v.mean(0)


# ---------------------------------------------------------------- auto steps (one picture, Lab [H, W, 3])

def white_balance(lab, strength, report):
    """Move the average colour of near-neutral pixels to grey. Neutral = low chroma and mid lightness."""
    s = _sample(lab)
    chroma = torch.sqrt(s[:, 1] ** 2 + s[:, 2] ** 2)
    L = s[:, 0]
    w = ((L > 15) & (L < 95)).float() * torch.clamp(1 - chroma / 25, min=0)   # the greyer, the more it counts
    if w.sum() < 50:   # hardly any neutral pixels (a very colourful picture): nothing to measure against
        report.append("white balance: no neutral areas, skipped")
        return lab
    cast = _weighted_mean(s[:, 1:3], w)
    shift = -cast * strength
    out = lab.clone()
    # the shift is applied fully to neutrals and less to saturated colours, so they keep their hue
    c = torch.sqrt(lab[..., 1] ** 2 + lab[..., 2] ** 2)
    k = 1 / (1 + (c / 60) ** 2)
    out[..., 1] = lab[..., 1] + shift[0] * k
    out[..., 2] = lab[..., 2] + shift[1] * k
    report.append(f"white balance: cast a {cast[0]:+.1f} b {cast[1]:+.1f} → shift a {shift[0]:+.1f} b {shift[1]:+.1f}")
    return out


def levels(lab, strength, low_pct, high_pct, report):
    """Stretch lightness between the low and high percentiles to 0..100 (hue and chroma stay)."""
    L = _sample(lab[..., :1])[:, 0]
    lo = torch.quantile(L, low_pct / 100).item()
    hi = torch.quantile(L, high_pct / 100).item()
    if hi - lo < 5:
        report.append("levels: almost flat picture, skipped")
        return lab
    # do not stretch more than ×2 — a dark, foggy picture is meant to stay so
    lo_t, hi_t = lo * (1 - strength), hi + (100 - hi) * strength
    scale = min((hi_t - lo_t) / (hi - lo), 2.0)
    out = lab.clone()
    out[..., 0] = ((lab[..., 0] - lo) * scale + lo_t).clamp(0, 100)
    report.append(f"levels: L {lo:.0f}–{hi:.0f} → {lo_t:.0f}–{lo_t + (hi - lo) * scale:.0f}")
    return out


def measure(lab, clip_pct=0.5):
    """What auto mode looks at: the colour cast of the near-neutral areas, the black point, mean lightness and
    mean chroma (Lab units)."""
    s = _sample(lab)
    chroma = torch.sqrt(s[:, 1] ** 2 + s[:, 2] ** 2)
    L = s[:, 0]
    w = ((L > 15) & (L < 95)).float() * torch.clamp(1 - chroma / 25, min=0)
    cast = _weighted_mean(s[:, 1:3], w) if w.sum() >= 50 else None
    return {"cast": None if cast is None else (float(cast[0]), float(cast[1])),
            "black": float(torch.quantile(L, clip_pct / 100)), "lightness": float(L.mean()), "chroma": float(chroma.mean())}


def auto_strengths(m):
    """Strengths for auto mode from measure(): white balance, levels, vibrance and an exposure correction (stops)."""
    clamp = lambda x, lo, hi: max(lo, min(hi, x))
    wb = 0.0
    if m["cast"] is not None:
        a, b = m["cast"]
        size = math.hypot(a, b)
        if b > 0 and size > 0:          # a warm cast: take out about 1 Lab unit of it; a cool cast is left as is
            wb = clamp(1.0 / size, 0.0, 0.6)
    return {"white_balance": round(wb, 2),
            "levels": round(clamp(1.15 - 0.08 * m["black"], 0.4, 1.0), 2),
            "vibrance": round(clamp(0.28 - 0.009 * m["chroma"], 0.03, 0.35), 2),
            "exposure": round(clamp(0.004 * m["lightness"] - 0.17, -0.15, 0.0), 3)}


def _skin_weight(lab):
    """1 for typical skin hues (orange–red, moderate chroma), 0 elsewhere."""
    hue = torch.rad2deg(torch.atan2(lab[..., 2], lab[..., 1]))   # 0° red, 90° yellow
    chroma = torch.sqrt(lab[..., 1] ** 2 + lab[..., 2] ** 2)
    h = torch.clamp(1 - (hue - 55).abs() / 30, min=0)          # 25°…85°
    c = torch.clamp(1 - (chroma - 25).abs() / 25, min=0)        # chroma around 25
    return h * c


def vibrance(lab, strength, protect_skin, report):
    """Raise chroma of dull colours more than of saturated ones."""
    chroma = torch.sqrt(lab[..., 1] ** 2 + lab[..., 2] ** 2)
    dull = torch.clamp(1 - chroma / 80, min=0)
    boost = 1 + 0.6 * strength * dull
    if protect_skin:
        boost = 1 + (boost - 1) * (1 - 0.8 * _skin_weight(lab))
    out = lab.clone()
    out[..., 1] = lab[..., 1] * boost
    out[..., 2] = lab[..., 2] * boost
    report.append(f"vibrance: up to +{60 * strength:.0f}% for dull colours" + (", skin protected" if protect_skin else ""))
    return out


def match_reference(lab, ref_lab, strength, report):
    """Reinhard colour transfer: match mean and spread of L, a, b to the reference."""
    s, r = _sample(lab), _sample(ref_lab)
    mu, sd = s.mean(0), s.std(0).clamp(min=1e-3)
    rmu, rsd = r.mean(0), r.std(0).clamp(min=1e-3)
    ratio = (rsd / sd).clamp(0.5, 2.0)   # no wild stretching
    matched = (lab - mu) * ratio + rmu
    out = lab + (matched - lab) * strength
    out[..., 0] = out[..., 0].clamp(0, 100)
    report.append(f"reference: L {mu[0]:.0f}→{rmu[0]:.0f}, a {mu[1]:+.1f}→{rmu[1]:+.1f}, b {mu[2]:+.1f}→{rmu[2]:+.1f}")
    return out


# ---------------------------------------------------------------- manual adjustments (sRGB [H, W, 3])

def manual(rgb, exposure=0.0, contrast=0.0, saturation=0.0, temperature=0.0, tint=0.0, lift=0.0, gamma=0.0, gain=0.0):
    x = rgb
    if exposure:
        x = _gam(_lin(x) * (2 ** exposure)).clamp(0, 1)
    if lift or gamma or gain:
        g = 2 ** (-gamma)                          # gamma > 0 brightens the mid-tones
        x = (x * (1 + gain) + lift * (1 - x)).clamp(0, 1) ** g
    if contrast:
        k = 1 + contrast                           # around the mid-grey in perceptual space
        x = ((x - 0.5) * k + 0.5).clamp(0, 1)
    if saturation or temperature or tint:
        lab = rgb_to_lab(x)
        lab[..., 1:] *= (1 + saturation)
        lab[..., 2] += 20 * temperature            # yellow / blue
        lab[..., 1] += 20 * tint                   # magenta / green
        x = lab_to_rgb(lab)
    return x.clamp(0, 1)


# ---------------------------------------------------------------- histogram picture

def histogram_image(before, after, width=1024, height=400, ss=4):
    """[1, height, width, 3] picture: RGB histograms of the result (filled), the original as an outline.
    Drawn ss times larger and scaled down, so the curves and the fill edges are smooth (anti-aliased)."""
    bins = 256
    out_w, out_h = width, height
    px = max(1, round(width / 512)) * ss                          # line thickness / top margin, in drawing pixels
    width, height = width * ss, height * ss

    def hist(x):
        s = _sample(x.float().cpu(), 2_000_000)
        h = torch.stack([torch.histc(s[:, c], bins=bins, min=0, max=1) for c in range(3)])
        # light smoothing, so 8-bit "combing" does not turn the curves into spikes
        k = torch.tensor([[[1.0, 2.0, 3.0, 2.0, 1.0]]]) / 9
        return F.conv1d(h[:, None], k, padding=2)[:, 0]

    hb, ha = hist(before), hist(after)
    peak = max(float(ha.max()), float(hb.max()), 1.0)
    # bins -> pixel columns
    xs = torch.linspace(0, bins - 1, width)
    i0 = xs.floor().long().clamp(max=bins - 1)
    i1 = (i0 + 1).clamp(max=bins - 1)
    fr = xs - i0
    col = lambda h: h[:, i0] * (1 - fr) + h[:, i1] * fr
    top_a = (col(ha) / peak) ** 0.5 * (height - 6 * px)
    top_b = (col(hb) / peak) ** 0.5 * (height - 6 * px)
    rows = torch.arange(height).flip(0).float()[:, None]          # 0 at the bottom
    colors = torch.tensor([[1.0, 0.32, 0.32], [0.3, 0.95, 0.4], [0.35, 0.55, 1.0]])
    img = torch.full((height, width, 3), 0.07)
    for c in range(3):
        fill = (rows < top_a[c][None, :]).float()[..., None]
        img = img + fill * colors[c] * 0.38
    for c in range(3):
        t = top_b[c]
        lo = torch.minimum(t, torch.roll(t, 1)).clamp(min=0) - px
        hi = torch.maximum(t, torch.roll(t, 1)) + px
        edge = ((rows >= lo[None, :]) & (rows <= hi[None, :])).float()
        # widen sideways too, so steep parts of the curve are as thick as flat ones
        edge = F.max_pool2d(edge[None, None], (1, 2 * px + 1), stride=1, padding=(0, px))[0, 0][..., None]
        img = img * (1 - edge * 0.85) + edge * colors[c] * 0.85
    img = F.avg_pool2d(img.permute(2, 0, 1)[None], ss)[0].permute(1, 2, 0)
    return img.clamp(0, 1)[None]
