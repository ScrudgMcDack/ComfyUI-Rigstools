"""
Static output tooltips of the Rigstools nodes, English and Russian.

The first paragraph says what the output is. The paragraph after a blank line explains the amber ✕ that the node
draws on a connected output carrying only a substitute value. With Draftsman installed, the tooltip shows the first
paragraph plus a line about the current picture instead (Draftsman keeps the first paragraph as the title).

English goes to OUTPUT_TOOLTIPS of the nodes (the stock tooltip). The titles in both languages go to
web/tooltip_titles.json (made by write_titles()), which web/rigstools.js gives to Draftsman for the styled tooltip.
Note: ComfyUI's locales/<lang>/nodeDefs.json cannot be used for these nodes — the frontend looks the translation up
by a path built from the node name, and the "[Rigstools]" in the names breaks that path.
"""

import json
from pathlib import Path

X_EN, X_RU = "\n\n✕ on the output: ", "\n\n✕ на выходе: "

# value outputs shared by Parameters extractor and Load image with parameters:
# (name, key, label, about_en, about_ru, empty) — empty: (en, ru) of the ✕ line when an empty string comes out,
# False when a default value comes out instead
VALUES = [
    ("SEED", "seed", "seed", "Seed", "Сид генерации", False),
    ("STEPS", "steps", "steps", "Sampling steps", "Шаги сэмплирования", False),
    ("CFG", "cfg", "cfg", "CFG scale", "CFG", False),
    ("CLIP", "clip_skip", "clip skip", "Clip skip — the value for CLIP Set Last Layer.",
     "Clip skip — значение для CLIP Set Last Layer.", False),
    ("WIDTH", "width", "width", "Image width", "Ширина картинки", False),
    ("HEIGHT", "height", "height", "Image height", "Высота картинки", False),
    ("POSITIVE", "positive", "positive prompt", "Positive prompt exactly as stored in the image (LoRA tags included).",
     "Позитивный промпт ровно как в картинке (с тегами LoRA).", ("no positive prompt.", "нет позитивного промпта.")),
    ("NEGATIVE", "negative", "negative prompt", "Negative prompt exactly as stored in the image.",
     "Негативный промпт ровно как в картинке.", ("no negative prompt.", "нет негативного промпта.")),
    ("MODEL_NAME", "model", "model", "Checkpoint: path in models/checkpoints when the file is found, "
     "otherwise the name from the image.", "Чекпоинт: путь в models/checkpoints, если файл найден, иначе имя из "
     "картинки.", ("no checkpoint.", "нет чекпоинта.")),
    ("SAMPLER", "sampler", "sampler", "Sampler (ComfyUI name)", "Сэмплер (имя ComfyUI)", False),
    ("SCHEDULER", "scheduler", "scheduler", "Scheduler (ComfyUI name)", "Планировщик (имя ComfyUI)", False),
]

LORA_STACK = ("LoRA stack as <lora:name:weight> tags: the 'Lora stack' field, otherwise the LoRA tags of the positive "
              "prompt; None when the image has no LoRA",
              "Стек LoRA тегами <lora:имя:вес>: поле «Lora stack», иначе теги LoRA из позитивного промпта; None, если "
              "в картинке нет LoRA")


def _value(out, key, label, en, ru, empty, source):
    if empty:
        x_en, x_ru = empty
    elif source == "panel":
        x_en = f"the image has no {label} — the default value comes out (type your own in the panel)."
        x_ru = f"в картинке нет {label} — на выход идёт значение по умолчанию (своё можно ввести в панели)."
    else:
        x_en = f"the parameters have no {label} — the value of fallback_{key} comes out."
        x_ru = f"в параметрах нет {label} — на выход идёт значение fallback_{key}."
    return out, en + X_EN + x_en, ru + X_RU + x_ru


LOADER_COMMON = [
    ("IMAGE", "The image (RGB)", "Картинка (RGB)"),
    ("MASK", "Mask from the alpha channel (transparent = 1). Mask-editor masks are kept",
     "Маска из альфа-канала (прозрачное = 1). Маски из редактора масок сохраняются"),
    ("METADATA_RAW",
     "File metadata (prompt, workflow, parameters, fileinfo…). Connect it to Metadata extractor"
     + X_EN + "the file has no generation data.",
     "Метаданные файла (prompt, workflow, parameters, fileinfo…). Подключается к Metadata extractor"
     + X_RU + "в файле нет данных генерации."),
    ("PARAMETERS",
     "A1111 parameters. Connect it to Parameters extractor. ↻ — the parameters are rebuilt from the prompt"
     + X_EN + "no values.",
     "Параметры A1111. Подключается к Parameters extractor. ↻ — параметры восстановлены из prompt"
     + X_RU + "нет значений."),
]
FILENAME = ("FILENAME", "File name with extension", "Имя файла с расширением")

# Load image with parameters: what differs from the shared texts above
LIP = {
    "PARAMETERS": ("A1111 parameters. Values typed in the panel are not written into them. ↻ — the parameters are "
                   "rebuilt from the prompt" + X_EN + "no values.",
                   "Параметры A1111. Значения, введённые в панели, в них не попадают. ↻ — параметры восстановлены из "
                   "prompt" + X_RU + "нет значений."),
}


def _lip(rows):
    return [(out, *LIP[out]) if out in LIP else (out, en, ru) for out, en, ru in rows]


TIPS = {
    "Load image with metadata [Rigstools]": LOADER_COMMON + [FILENAME],
    "Load image from folder [Rigstools]": LOADER_COMMON + [
        FILENAME,
        ("INDEX", "Number of the loaded file in the list (after wrapping around)",
         "Номер загруженного файла в списке (после возврата к началу)"),
        ("COUNT", "Number of files that match", "Сколько файлов подходит под фильтр"),
    ],
    "Load image with parameters [Rigstools]": _lip([
        LOADER_COMMON[0], LOADER_COMMON[1],
        ("METADATA_RAW", LOADER_COMMON[2][1], LOADER_COMMON[2][2]),
        ("PARAMETERS",
         "A1111-style parameters text as stored in the file (rebuilt from the ComfyUI prompt when the file has none, ↻); "
         "values typed in the panel are not written into it" + X_EN + "neither parameters nor a ComfyUI prompt to "
         "rebuild them from — an empty string comes out.",
         "Текст параметров A1111 как в файле (восстановленный из промпта ComfyUI, если в файле его нет, ↻); значения, "
         "введённые в панели, в него не попадают" + X_RU + "нет ни parameters, ни промпта ComfyUI, из которого их "
         "можно восстановить, — на выход идёт пустая строка."),
    ] + [_value(*v, source="panel") for v in VALUES if v[0] in ("POSITIVE", "NEGATIVE")]
      + [_value(*v, source="panel") for v in VALUES if v[0] not in ("POSITIVE", "NEGATIVE", "MODEL_NAME",
                                                                     "SAMPLER", "SCHEDULER")]
      + [_value(*v, source="panel") for v in VALUES if v[0] in ("SAMPLER", "SCHEDULER", "MODEL_NAME")]
      + [("LORA_STACK", LORA_STACK[0] + " — e.g. for LoRA hashes for Image Saver",
          LORA_STACK[1] + " — например, для LoRA hashes for Image Saver")]),
    "Parameters extractor [Rigstools]": [_value(*v, source="fallback") for v in VALUES if v[0] not in
                                         ("SAMPLER", "SCHEDULER")]
    + [("LORA_STACK", *LORA_STACK)]
    + [_value(*v, source="fallback") for v in VALUES if v[0] in ("SAMPLER", "SCHEDULER")],
    "Metadata extractor [Rigstools]": [
        ("PROMPT", "ComfyUI API prompt stored in the image (JSON)" + X_EN + "no prompt in the metadata — an empty "
         "JSON comes out.", "Промпт ComfyUI (API-формат), сохранённый в картинке (JSON)" + X_RU + "в метаданных нет "
         "prompt — на выход идёт пустой JSON."),
        ("WORKFLOW", "ComfyUI workflow stored in the image (JSON)" + X_EN + "no workflow in the metadata — an empty "
         "JSON comes out.", "Workflow ComfyUI, сохранённый в картинке (JSON)" + X_RU + "в метаданных нет workflow — "
         "на выход идёт пустой JSON."),
        ("FILEINFO", "File information: name, resolution, date, size (JSON)",
         "Информация о файле: имя, разрешение, дата, размер (JSON)"),
        ("PARAMETERS",
         "A1111 parameters. Connect it to Parameters extractor. ↻ — the parameters are rebuilt from the prompt"
         + X_EN + "no values (or parameters_from_prompt is off).",
         "Параметры A1111. Подключается к Parameters extractor. ↻ — параметры восстановлены из prompt"
         + X_RU + "нет значений (или выключен parameters_from_prompt)."),
        ("RAW2JSON", "All metadata as JSON", "Все метаданные в JSON"),
        ("RAW2PROPERTIES", "All metadata as key=value lines", "Все метаданные строками ключ=значение"),
        ("RAW2CSV", "All metadata as tab-separated key/value lines",
         "Все метаданные строками «ключ — значение» через табуляцию"),
    ],
    "Color correction [Rigstools]": [
        ("IMAGE", "The corrected image", "Исправленная картинка"),
        ("HISTOGRAM", "RGB histograms of the result; the original is drawn as an outline",
         "Гистограммы RGB результата; оригинал нарисован контуром"),
    ],
    "Save image [Rigstools]": [
        ("FILEPATH", "Full paths of the saved files", "Полные пути сохранённых файлов"),
        ("PARAMETERS", "A1111-style parameters text written into the files (empty when no sampler was found and no "
         "value is connected)" + X_EN + "no sampler node is connected in the workflow and no values are connected — the "
         "files get no parameters.",
         "Текст параметров A1111, записанный в файлы (пусто, если сэмплер не найден и значения не подключены)" + X_RU +
         "в воркфлоу нет подключённой ноды сэмплера и не подключены значения — параметров в файлах нет."),
        ("HASHES", "Hashes of the model, LoRA and embeddings: 'name:HASH' separated by commas" + X_EN + "some files "
         "were not found in the models folders — their hashes are missing (by the hashes Civitai recognises the "
         "models used).",
         "Хэши модели, LoRA и embeddings: «имя:ХЭШ» через запятую" + X_RU + "часть файлов не найдена в папках "
         "моделей — их хэшей нет (по хэшам Civitai узнаёт, какие модели использованы)."),
    ],
    "LoRA hashes for Image Saver [Rigstools]": [
        ("ADDITIONAL_HASHES", "Connect to the additional_hashes input of Image Saver: 'Name:HASH[:weight]' entries "
         "separated by commas" + X_EN + "some LoRA were not found in models/loras — their hashes are missing "
         "(see NOT_FOUND).", "Подключается ко входу additional_hashes у Image Saver: записи «Имя:ХЭШ[:вес]» через "
         "запятую" + X_RU + "часть LoRA не найдена в models/loras — их хэшей в строке нет (см. NOT_FOUND)."),
        ("NOT_FOUND", "LoRA names from the stack that were not found in models/loras (empty when all were found)",
         "Имена LoRA из стека, не найденных в models/loras (пусто, если найдены все)"),
    ],
}


def output_tooltips(node_name, return_names):
    """English tooltips in the order of RETURN_NAMES."""
    by = {out: en for out, en, _ in TIPS[node_name]}
    return tuple(by[n] for n in return_names)


def write_titles(root):
    """web/tooltip_titles.json: the first paragraph of every output tooltip, English and Russian."""
    first = lambda text: text.split("\n\n")[0]
    data = {node: {out: {"en": first(en), "ru": first(ru)} for out, en, ru in rows} for node, rows in TIPS.items()}
    path = Path(root) / "web" / "tooltip_titles.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path
