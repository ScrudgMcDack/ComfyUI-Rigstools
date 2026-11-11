"""
Reading generation metadata from image files (no ComfyUI / torch imports — easy to test).

The result has the same shape as METADATA_RAW from "Load image with metadata" (Crystools):
    {"fileinfo": {...}, "prompt": {...}, "workflow": {...}, "parameters": "...", <other text keys>}
so every node that accepts Crystools metadata accepts this one too.

Where the data is looked for:
  PNG        text chunks (tEXt / iTXt / zTXt): prompt, workflow, parameters, anything else
  JPEG/WebP  EXIF UserComment            → parameters (A1111, Forge, Image Saver)
             EXIF Make / Model / ImageDescription / … in the form "key:{json}"
                                         → prompt / workflow (Image Saver, stock Save Animated WEBP)
             "Prompt:" / "Workflow:" prefixes (older Crystools)
             JPEG comment with A1111 text → parameters (fallback)
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, ExifTags

EXIF_IFD = 0x8769
TAG_USER_COMMENT = 0x9286
TAG_IMAGE_DESCRIPTION = 0x010E
# Make (0x010F) and Model (0x0110) are what Image Saver and ComfyUI use; the stock Save Animated WEBP
# writes extra_pnginfo keys into the tags below Make as well
KEYED_TAGS = range(0x0100, 0x0111)
KEYED_RE = re.compile(r"^\s*([A-Za-z_][\w\- ]{0,40}?)\s*:\s*([\[{].*)$", re.S)
A1111_HINT = re.compile(r"(^|\n)\s*Steps:\s*\d+", re.I)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".avif", ".jfif"}
# small, readable EXIF values are kept under "exif"; long blobs (workflow, maker notes…) are not repeated there
EXIF_VALUE_LIMIT = 300
POINTER_TAGS = {0x8769, 0x8825, 0xA005, 0x927C}  # Exif / GPS / Interop offsets, MakerNote


def human_size(path) -> str:
    size = os.path.getsize(path)
    for unit, power in (("bytes", 0), ("KB", 1), ("MB", 2), ("GB", 3)):
        if size < pow(1024, power + 1) or unit == "GB":
            return f"{size} bytes" if power == 0 else f"{round(size / pow(1024, power), 2)} {unit}"


def is_image_file(name: str) -> bool:
    return Path(name).suffix.lower() in IMAGE_EXTENSIONS


# ---------------------------------------------------------------- text decoding

def _clean(text: str) -> str:
    return text.replace("\x00", "").strip()


def decode_user_comment(value) -> str:
    """EXIF UserComment: 8-byte charset header + text (A1111/piexif write UNICODE = UTF-16)."""
    if value is None:
        return ""
    if isinstance(value, str):
        return _clean(value)
    data = bytes(value)
    head, body = data[:8], data[8:]
    if head.startswith(b"UNICODE"):
        if body[:2] in (b"\xff\xfe", b"\xfe\xff"):
            return _clean(body.decode("utf-16"))
        # piexif / A1111 write big-endian; some tools write little-endian. Pick the one that looks like text.
        be, le = body.decode("utf-16-be", "replace"), body.decode("utf-16-le", "replace")
        score = lambda s: sum(ch.isascii() and (ch.isprintable() or ch in "\n\r\t") for ch in s)
        return _clean(be if score(be) >= score(le) else le)
    if head.startswith(b"ASCII"):
        return _clean(body.decode("latin-1"))
    if head.startswith(b"JIS"):
        return _clean(body.decode("shift_jis", "replace"))
    # undefined header (zeros) or no header at all
    raw = body if head == b"\x00" * 8 else data
    try:
        return _clean(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return _clean(raw.decode("latin-1"))


def _as_text(value) -> str:
    if isinstance(value, bytes):
        try:
            return _clean(value.decode("utf-8"))
        except UnicodeDecodeError:
            return _clean(value.decode("latin-1"))
    return _clean(str(value))


def _json_or_text(text: str):
    try:
        return json.loads(text)
    except Exception:
        return text


# ---------------------------------------------------------------- readers

def _read_png_text(img, metadata):
    """Same rules as Crystools: prompt/workflow parsed as JSON, other text keys JSON-or-string."""
    for key, value in (img.info or {}).items():
        if isinstance(value, bytes) or key in ("icc_profile", "exif", "transparency"):
            continue  # binary blobs, not text chunks
        if key in ("prompt", "workflow"):
            try:
                metadata[key] = json.loads(value)
            except Exception:
                pass
        elif isinstance(value, str):
            metadata[str(key)] = value if key == "parameters" else _json_or_text(value)
        else:
            metadata[str(key)] = str(value)


def _read_exif(img, metadata):
    try:
        exif = img.getexif()
    except Exception:
        return
    if not exif:
        return

    readable = {}
    description = ""

    # "key:{json}" tags — Image Saver: Make = workflow:…, Model = prompt:…; Crystools: Prompt: / Workflow:
    for tag in KEYED_TAGS:
        if tag not in exif:
            continue
        text = _as_text(exif[tag])
        match = KEYED_RE.match(text)
        if match:
            key = match.group(1).strip().lower()
            parsed = _json_or_text(match.group(2))
            if key in ("prompt", "workflow") and not isinstance(parsed, (dict, list)):
                continue
            metadata.setdefault(key, parsed)
        elif tag == TAG_IMAGE_DESCRIPTION:
            description = text

    for tag, value in exif.items():
        if tag in POINTER_TAGS or (tag in KEYED_TAGS and KEYED_RE.match(_as_text(value))):
            continue
        text = _as_text(value)
        if len(text) <= EXIF_VALUE_LIMIT:
            readable[ExifTags.TAGS.get(tag, str(tag))] = text

    try:
        sub = exif.get_ifd(EXIF_IFD)
    except Exception:
        sub = {}
    comment = decode_user_comment(sub.get(TAG_USER_COMMENT)) if sub else ""
    for tag, value in (sub or {}).items():
        if tag == TAG_USER_COMMENT or tag in POINTER_TAGS:
            continue
        text = _as_text(value)
        if len(text) <= EXIF_VALUE_LIMIT:
            readable[ExifTags.TAGS.get(tag, str(tag))] = text

    if comment:
        if comment.lstrip().startswith("{"):
            # some tools put a JSON blob into UserComment (e.g. prompt / workflow / extra data)
            parsed = _json_or_text(comment)
            if isinstance(parsed, dict):
                for k in ("prompt", "workflow", "parameters"):
                    if k in parsed:
                        metadata.setdefault(k, _json_or_text(parsed[k]) if k != "parameters" else parsed[k])
            else:
                metadata.setdefault("parameters", comment)
        else:
            metadata.setdefault("parameters", comment)
    elif description and A1111_HINT.search(description):
        metadata.setdefault("parameters", description)

    if readable:
        metadata["exif"] = readable


def read_metadata(path):
    """Returns (PIL image, metadata dict). The image is left open (lazy) for the caller."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    img = Image.open(path)
    metadata = {
        "fileinfo": {
            "filename": path.as_posix(),
            "resolution": f"{img.width}x{img.height}",
            "date": str(datetime.fromtimestamp(os.path.getmtime(path))),
            "size": human_size(path),
            "format": img.format or "",
        }
    }

    if img.format == "PNG":
        _read_png_text(img, metadata)
    else:
        # WebP / JPEG / TIFF / AVIF… keep text-like info too (e.g. JPEG comment)
        for key, value in (img.info or {}).items():
            if key in ("exif", "icc_profile", "xmp", "dpi", "jfif", "jfif_version", "jfif_density",
                       "jfif_unit", "progressive", "progression", "adobe", "adobe_transform",
                       "loop", "duration", "background", "timestamp", "transparency"):
                continue
            text = _as_text(value)
            if key == "comment" and A1111_HINT.search(text):
                metadata.setdefault("parameters", text)
            elif isinstance(value, (str, bytes)) and text:
                metadata.setdefault(str(key), _json_or_text(text))
        _read_exif(img, metadata)

    params = metadata.get("parameters")
    if params is not None and not isinstance(params, str):
        metadata["parameters"] = json.dumps(params, ensure_ascii=False)
    return img, metadata


def summary(metadata, preview_chars=600):
    """Short description for the node badge."""
    params = metadata.get("parameters") or ""
    info = metadata.get("fileinfo") or {}
    return {
        "parameters": bool(params),
        "prompt": isinstance(metadata.get("prompt"), dict) and bool(metadata.get("prompt")),
        "workflow": isinstance(metadata.get("workflow"), (dict, list)) and bool(metadata.get("workflow")),
        "format": info.get("format", ""),
        "resolution": info.get("resolution", ""),
        "size": info.get("size", ""),
        "preview": params[:preview_chars] + ("…" if len(params) > preview_chars else ""),
    }
