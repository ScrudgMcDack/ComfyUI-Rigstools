// Rigstools — draws the alembic icon in the title of the Rigstools nodes, right before the title text,
// and shows the metadata state of the image loaders: caption under the image, dimmed outputs, ⓘ button + dialog.
// The stock title dot (collapse / expand) is left untouched. The picture is the same on every OS
// (the ⚗️ emoji is drawn differently by each system font).
// Icon: Noto Emoji "alembic" (U+2697), Apache License 2.0 — see THIRD_PARTY_NOTICES.md.

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const NODE_TYPES = new Set([
  "Metadata extractor [Rigstools]",
  "Parameters extractor [Rigstools]",
  "LoRA hashes for Image Saver [Rigstools]",
  "Load image with metadata [Rigstools]",
  "Load image from folder [Rigstools]",
  "Load image with parameters [Rigstools]",
  "Color correction [Rigstools]",
  "Save image [Rigstools]",
]);
const LOADER = "Load image with metadata [Rigstools]";
const FOLDER = "Load image from folder [Rigstools]";
const PARAMS = "Load image with parameters [Rigstools]";

const icon = new Image();
icon.src = new URL("./alembic.svg", import.meta.url).href;
icon.onload = () => app.canvas?.setDirty?.(true, true);

const LG = () => globalThis.LiteGraph ?? {};

function fitText(ctx, text, maxWidth) {
  if (maxWidth <= 0) return "";
  if (ctx.measureText(text).width <= maxWidth) return text;
  let lo = 0, hi = text.length;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (ctx.measureText(text.slice(0, mid) + "…").width <= maxWidth) lo = mid; else hi = mid - 1;
  }
  return text.slice(0, lo) + "…";
}

/** Same layout as the stock title text, shifted right by the icon. */
function drawTitle(node, ctx, titleHeight, size, scale, font, selected) {
  const L = LG();
  if (scale < 0.6) return; // low-quality zoom: the stock renderer draws no title text either
  ctx.font = font;
  const title = (node.getTitle?.() ?? node.title ?? "") + (node.pinned ? "📌" : "");
  const collapsed = node.collapsed ?? node.flags?.collapsed;
  const textY = (L.NODE_TITLE_TEXT_Y ?? 20) - titleHeight;
  let x = titleHeight;

  // icon (skipped on collapsed nodes: their width is computed from the text only)
  if (!collapsed && icon.complete && icon.naturalWidth) {
    const s = Math.round(titleHeight * 0.62);
    ctx.drawImage(icon, x - 3, -titleHeight / 2 - s / 2, s, s);
    x += s + 2;
  }

  ctx.fillStyle = selected
    ? L.NODE_SELECTED_TITLE_COLOR ?? "#fff"
    : node.constructor.title_text_color ?? app.canvas?.node_title_color ?? L.NODE_TITLE_COLOR ?? "#999";
  ctx.textAlign = "left";
  const text = collapsed ? title.substr(0, 20) : fitText(ctx, title, size[0] - x - titleHeight);
  ctx.fillText(text, x, textY);
}

// ------------------------------------------------------------------ metadata state of the loaders
// 1. the stock caption under the image ("1024 × 1536") is extended: "· PNG · all metadata ✓" / what is missing;
// 2. outputs that carry nothing are dimmed, PARAMETERS rebuilt from the prompt gets "↻" and an amber dot;
// 3. the ⓘ button in the title opens a dialog with the full parameters, copy buttons and "open workflow".

const ON = "#5fb878", REBUILT = "#d9a441", OFF = "#7a7a7a";

const STR = {
  en: {
    whyMeta: "The file has no generation data — only the file info comes out.",
    whyParams: "The file has no parameters and no ComfyUI prompt — an empty string comes out.",
    whyParamsRebuild: "The file has no parameters and they could not be rebuilt from the ComfyUI prompt — an empty string comes out.",
    whyDefault: "No {k} in the image — the default value comes out: {v}", whyEmpty: "No {k} in the image — an empty string comes out.",
    why_noBlock: "No {v} in the metadata — an empty JSON comes out.",
    why_noParams: "The metadata has no parameters and no ComfyUI prompt — an empty string comes out.",
    why_noParamsRebuild: "The metadata has no parameters and they could not be rebuilt from the ComfyUI prompt — an empty string comes out.",
    why_noParamsOff: "The metadata has no parameters and rebuilding from the prompt is off (parameters_from_prompt) — an empty string comes out.",
    why_empty: "No {k} in the parameters — an empty string comes out.",
    why_fallback: "No {k} in the parameters — {input} = {v} comes out.",
    why_lorasMissing: "Not found in models/loras: {v} — their hashes are missing from the string.",
    ln_image: "From the image: {v}", ln_params: "From the parameters: {v}", ln_meta: "From the metadata: {v}",
    ln_typed: "Typed in the panel: {v}", ln_nodes: "From the metadata, nodes: {v}", ln_present: "Present in the metadata",
    ln_count: "Hashes in the string: {v}", ln_loras: "LoRA: {v}", ln_file: "From the file: {v}",
    ln_rebuilt: "↻ Rebuilt from the ComfyUI prompt — the file has no parameters",
    ln_noLora: "No LoRA — None comes out", ln_noHashes: "No LoRA — the string is empty",
    ln_notFound: "Not found: {v}",
    ln_allLoras: "All LoRA were found", ln_position: "File {v}",
    all: "all metadata ✓", rebuilt: "parameters from prompt", noParams: "no parameters", none: "no metadata",
    no: "no", info: "Generation data of the file", copyParams: "Copy parameters", copyPrompt: "Copy prompt (JSON)",
    ccTitle: "Color correction — settings", ccCols: "Setting|What it does",
    ccIntro: "First the automatic steps, each picture of a batch is measured on its own; then the manual adjustments. "
      + "Order: reference → white balance → levels → vibrance → manual adjustments → mask → strength. The automatic steps "
      + "work in Lab, where lightness is separate from colour, so they do not shift hues. A value of 0 turns a step off.",
    ccAuto: "Automatic steps",
    ccAutoRows: "white_balance|Removes a colour cast (a yellow or blue tint). Measures the average colour of the near-grey areas of medium lightness and moves it to neutral grey. Saturated colours are moved less and keep their hue. When there are hardly any near-grey areas (a very colourful picture) the step is skipped. A warm or cold mood that is meant to be there is a cast too — keep the value low for such pictures.\n"
      + "levels|Stretches the lightness: the darkest tones get darker, the lightest lighter — the picture gets more contrast and looks cleaner. Hue and saturation stay. The stretch is at most ×2, so a dark or foggy scene stays dark or foggy; an almost flat picture is skipped.\n"
      + "levels_clip|Percent of the darkest and of the lightest pixels ignored when looking for the black and white points. Protects against single highlights and black dots; more — a stronger stretch, but details in the extreme tones may clip. Works only with levels.\n"
      + "vibrance|Raises the saturation of dull colours more than of already saturated ones (up to +60% at 1): the picture looks livelier without garish spots.\n"
      + "protect_skin|Vibrance hardly touches skin hues (orange–red of moderate saturation), so skin does not glow.",
    ccManual: "Manual adjustments (after the automatic steps)",
    ccManualRows: "exposure|Exposure in stops, in linear light: +1 — twice as bright, −1 — half. Highlights may burn out to white.\n"
      + "contrast|Contrast around the mid-grey: + darker shadows and brighter highlights, − a flatter picture.\n"
      + "saturation|Saturation of all colours alike: −1 — black and white, +1 — twice as saturated.\n"
      + "temperature|Colour temperature: + warmer (towards yellow), − cooler (towards blue).\n"
      + "tint|Tint: + towards magenta, − towards green. With temperature — a manual white balance.\n"
      + "lift|Shadows: + lighter (the shadows fade), − darker. The highlights hardly change.\n"
      + "gamma|Mid-tones: + lighter, − darker; the black and the white points stay.\n"
      + "gain|Highlights: + brighter, − duller. The shadows hardly change.",
    ccOther: "Strength, reference, mask, outputs",
    ccOtherRows: "strength|Overall strength: mixes the result with the original. 0 — the original, 1 — the full correction, 0.5 — half way. Applied last, to everything at once.\n"
      + "reference|Optional picture whose colours to match: the mean and spread of lightness and colour are brought to it (Reinhard colour transfer, the spread changes at most ×2). E.g. the picture before an upscale that shifted the colours. Done first.\n"
      + "reference_strength|How much the colours are matched to the reference; without a reference connected it does nothing.\n"
      + "mask|Optional: correct only where the mask is white; grey values of the mask give a smooth transition.\n"
      + "IMAGE|The corrected picture; an alpha channel is kept.\n"
      + "HISTOGRAM|RGB histograms of the result (filled), the original as an outline — shows what the correction moved. Connect to Preview Image. Details of what was measured: Settings → Rigstools → Debug, in the console.",
    openWf: "Open workflow", copied: "Copied", close: "Close", loading: "Loading…",
    rebuiltNote: "The file has no parameters — rebuilt from the ComfyUI prompt (values that cannot be determined are left out):",
    nothing: "The file has no parameters and no ComfyUI prompt.", short: "Only the beginning is shown — the file is outside the ComfyUI folders.",
  },
  ru: {
    whyMeta: "В файле нет данных генерации — на выход идёт только информация о файле.",
    whyParams: "В файле нет ни parameters, ни промпта ComfyUI — на выход идёт пустая строка.",
    whyParamsRebuild: "В файле нет parameters, а восстановить их из промпта ComfyUI не удалось — на выход идёт пустая строка.",
    whyDefault: "В картинке нет {k} — на выход идёт значение по умолчанию: {v}", whyEmpty: "В картинке нет {k} — на выход идёт пустая строка.",
    why_noBlock: "В метаданных нет {v} — на выход идёт пустой JSON.",
    why_noParams: "В метаданных нет ни parameters, ни промпта ComfyUI — на выход идёт пустая строка.",
    why_noParamsRebuild: "В метаданных нет parameters, а восстановить их из промпта ComfyUI не удалось — на выход идёт пустая строка.",
    why_noParamsOff: "В метаданных нет parameters, а восстановление из промпта выключено (parameters_from_prompt) — на выход идёт пустая строка.",
    why_empty: "В параметрах нет {k} — на выход идёт пустая строка.",
    why_fallback: "В параметрах нет {k} — на выход идёт {input} = {v}.",
    why_lorasMissing: "Не найдены в models/loras: {v} — их хэшей в строке нет.",
    ln_image: "Из картинки: {v}", ln_params: "Из параметров: {v}", ln_meta: "Из метаданных: {v}",
    ln_typed: "Введено вручную: {v}", ln_nodes: "Из метаданных, нод: {v}", ln_present: "Есть в метаданных",
    ln_count: "Хэшей в строке: {v}", ln_loras: "LoRA: {v}", ln_file: "Из файла: {v}",
    ln_rebuilt: "↻ Восстановлено из промпта ComfyUI — в файле parameters нет",
    ln_noLora: "LoRA нет — на выход идёт None", ln_noHashes: "LoRA нет — строка пустая",
    ln_notFound: "Не найдены: {v}",
    ln_allLoras: "Все LoRA найдены", ln_position: "Файл {v}",
    all: "все метаданные ✓", rebuilt: "parameters из prompt", noParams: "без parameters", none: "нет метаданных",
    no: "нет", info: "Данные генерации файла", copyParams: "Копировать parameters", copyPrompt: "Копировать prompt (JSON)",
    ccTitle: "Color correction — настройки", ccCols: "Настройка|Что делает",
    ccIntro: "Сначала автоматические шаги — каждая картинка пакета измеряется отдельно, затем ручные поправки. "
      + "Порядок: образец → баланс белого → уровни → вибранс → ручные поправки → маска → strength. Автоматические шаги "
      + "работают в пространстве Lab, где яркость отделена от цвета, поэтому оттенки не уезжают. Значение 0 выключает шаг.",
    ccAuto: "Автоматические шаги",
    ccAutoRows: "white_balance|Убирает цветовой оттенок (желтизну, синеву). Измеряет средний цвет почти серых участков средней яркости и сдвигает его к нейтральному серому. Насыщенные цвета сдвигаются меньше и сохраняют свой оттенок. Если почти серых участков нет (очень яркая картинка), шаг пропускается. Задуманное тёплое или холодное настроение — тоже «оттенок», для таких картинок держите значение низким.\n"
      + "levels|Растягивает яркость: самые тёмные тона становятся темнее, самые светлые — светлее, картинка становится контрастнее и «чище». Оттенок и насыщенность не меняются. Растяжение не больше чем в 2 раза — тёмная или туманная сцена такой и останется; почти однотонная картинка пропускается.\n"
      + "levels_clip|Сколько процентов самых тёмных и самых светлых пикселей не учитывать при поиске точек чёрного и белого. Защищает от одиночных бликов и чёрных точек; больше — сильнее растяжение, но детали в крайних тонах могут обрезаться. Работает только вместе с levels.\n"
      + "vibrance|Поднимает насыщенность блёклых цветов сильнее, чем уже насыщенных (до +60% при 1): картинка живее, без «кислотных» пятен.\n"
      + "protect_skin|Вибранс почти не трогает оттенки кожи (оранжево-красные умеренной насыщенности), чтобы кожа не «горела».",
    ccManual: "Ручные поправки (после автоматических шагов)",
    ccManualRows: "exposure|Экспозиция в ступенях, в линейном свете: +1 — вдвое светлее, −1 — вдвое темнее. Светлые участки могут выбиться в белый.\n"
      + "contrast|Контраст относительно среднего серого: + тени темнее, света светлее; − картинка площе.\n"
      + "saturation|Насыщенность всех цветов одинаково: −1 — чёрно-белая, +1 — вдвое насыщеннее.\n"
      + "temperature|Цветовая температура: + теплее (в жёлтый), − холоднее (в синий).\n"
      + "tint|Оттенок: + в пурпурный, − в зелёный. Вместе с temperature — ручной баланс белого.\n"
      + "lift|Тени: + светлее (тени «выцветают»), − темнее. Светлые участки почти не меняются.\n"
      + "gamma|Средние тона: + светлее, − темнее; точки чёрного и белого остаются на месте.\n"
      + "gain|Света: + ярче, − тусклее. Тени почти не меняются.",
    ccOther: "Сила, образец, маска, выходы",
    ccOtherRows: "strength|Общая сила: смешивает результат с оригиналом. 0 — оригинал, 1 — полная коррекция, 0.5 — наполовину. Применяется последней, ко всему сразу.\n"
      + "reference|Необязательная картинка-образец: среднее и разброс яркости и цвета подгоняются под неё (перенос цвета Рейнхарда, разброс меняется не больше чем в 2 раза). Например, картинка до апскейла, если апскейл сдвинул цвета. Выполняется первым.\n"
      + "reference_strength|Насколько сильно подгонять цвета под образец; без подключённого образца ни на что не влияет.\n"
      + "mask|Необязательная маска: коррекция только там, где она белая; серые значения дают плавный переход.\n"
      + "IMAGE|Исправленная картинка; альфа-канал сохраняется.\n"
      + "HISTOGRAM|Гистограммы RGB результата (заливка) и оригинала (контур) — видно, что сдвинула коррекция. Подключается к Preview Image. Что именно измерено — в консоли при включённой настройке Rigstools → Debug.",
    openWf: "Открыть workflow", copied: "Скопировано", close: "Закрыть", loading: "Загрузка…",
    rebuiltNote: "В файле нет parameters — они восстановлены из промпта ComfyUI (то, что нельзя определить надёжно, пропущено):",
    nothing: "В файле нет ни parameters, ни промпта ComfyUI.", short: "Показано только начало — файл лежит вне папок ComfyUI.",
  },
};
const t = (k) => {
  const loc = String(app.extensionManager?.setting?.get?.("Comfy.Locale") ?? "en").toLowerCase();
  return (STR[loc.startsWith("ru") ? "ru" : "en"][k]) ?? STR.en[k];
};

const color = (i) => (!i || i.error ? OFF : i.parameters ? ON : i.rebuilt ? REBUILT : OFF);

/** Caption variants from the longest to the shortest; the first one that fits is drawn. */
function captions(base, i) {
  if (!i || i.error) return [base];
  const missing = [!i.prompt && "prompt", !i.workflow && "workflow"].filter(Boolean);
  const p = i.parameters ? "" : i.rebuilt ? t("rebuilt") : t("noParams");
  let state;
  if (!i.parameters && !i.rebuilt && missing.length === 2) state = t("none");
  else if (!p && !missing.length) state = t("all");
  else state = [p, missing.length ? `${t("no")} ${missing.join(", ")}` : ""].filter(Boolean).join(" · ");
  const mark = i.parameters ? (missing.length ? "✓ …" : "✓") : i.rebuilt ? "↻" : "✗";
  return [
    `${base} · ${i.format} · ${state}`,
    `${base} · ${state}`,
    `${base} · ${i.format} · ${mark}`,
    base,
  ];
}

function setInfo(node, info) {
  node._rigInfo = info;
  const b = node._rigButton;
  if (b) b.text = info && !info.error ? "i" : ""; // LGraphBadge.visible is derived from the text
  node.setDirtyCanvas?.(true, false);
}

/** The single-file loader asks the server whenever its image changes (combo, upload, mask editor, load). */
function watchImage(node) {
  const v = node.widgets?.find((w) => w.name === "image")?.value;
  if (!v || node._rigFetched === v) return;
  node._rigFetched = v;
  api.fetchApi(`/rigstools/image_meta?filename=${encodeURIComponent(v)}`)
    .then((r) => r.json())
    .then((info) => { if (node._rigFetched === v) setInfo(node, info); })
    .catch(() => setInfo(node, { error: "unavailable" }));
}

// -------------------------------------------------- ⓘ button in the title

function infoButton(node) {
  if (!node.addTitleButton) return;
  const b = node.addTitleButton({ name: "rig_info", text: "", fontSize: 14, xOffset: -4, yOffset: 0 });
  b.text = "";
  b.getWidth = function () { return this.visible ? 18 : 0; };
  b.draw = function (ctx, x, y) {
    if (!this.visible) return;
    const s = 16, cx = x + this.xOffset + s / 2, cy = -(globalThis.LiteGraph?.NODE_TITLE_HEIGHT ?? 30) / 2;
    this._last_area[0] = cx - s / 2; this._last_area[1] = cy - s / 2; this._last_area[2] = s; this._last_area[3] = s;
    const c = color(node._rigInfo);
    ctx.save();
    ctx.beginPath(); ctx.arc(cx, cy, 7, 0, Math.PI * 2);
    ctx.fillStyle = c + "26"; ctx.fill();
    ctx.lineWidth = 1.2; ctx.strokeStyle = c; ctx.stroke();
    ctx.fillStyle = c; ctx.font = "bold 10px Georgia, 'Times New Roman', serif";
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText("i", cx, cy + 0.5);
    ctx.restore();
  };
  node._rigButton = b;
}

// -------------------------------------------------- dialog

// Our info windows: the size they open with stays, a drag on the bottom-right corner makes them bigger (or smaller)
function resizable(box) {
  const h = box.offsetHeight;
  Object.assign(box.style, { resize: "both", overflow: "hidden", height: `${h}px`, maxHeight: "96vh", maxWidth: "96vw",
    minWidth: "360px", minHeight: "200px" });
  return h;
}
const CLOSE_X = "color:#e5484d;cursor:pointer;font-size:16px;font-weight:bold";

function el(tag, css, text) {
  const e = document.createElement(tag);
  if (css) e.style.cssText = css;
  if (text != null) e.textContent = text;
  return e;
}

function button(label, onClick, disabled) {
  const b = el("button", "background:var(--secondary-background,#3a3a3a);color:var(--fg-color,#ddd);border:0;"
    + "border-radius:6px;padding:6px 14px;font:13px Arial,sans-serif;cursor:pointer" + (disabled ? ";opacity:.4;cursor:default" : ""), label);
  b.disabled = !!disabled;
  b.onclick = () => !b.disabled && onClick(b);
  return b;
}

async function copy(text, btn) {
  try { await navigator.clipboard.writeText(text); }
  catch {
    const ta = el("textarea", "position:fixed;left:-9999px"); ta.value = text; document.body.appendChild(ta);
    ta.select(); document.execCommand("copy"); ta.remove();
  }
  const old = btn.textContent; btn.textContent = t("copied"); setTimeout(() => (btn.textContent = old), 1200);
}

async function openDialog(node) {
  const base = node._rigInfo;
  if (!base) return;
  document.getElementById("rigstools-info")?.remove();

  const back = el("div", "position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:10000;display:flex;"
    + "align-items:center;justify-content:center");
  back.id = "rigstools-info";
  const box = el("div", "width:min(720px,92vw);max-height:84vh;display:flex;flex-direction:column;"
    + "background:var(--comfy-menu-bg,#2b2b2b);color:var(--fg-color,#ddd);border:1px solid var(--border-color,#444);"
    + "border-radius:10px;box-shadow:0 10px 40px rgba(0,0,0,.6);font:13px Arial,sans-serif");
  back.appendChild(box);
  const close = () => { back.remove(); document.removeEventListener("keydown", onKey, true); };
  const onKey = (e) => { if (e.key === "Escape") { e.stopPropagation(); close(); } };
  document.addEventListener("keydown", onKey, true);
  back.addEventListener("pointerdown", (e) => { if (e.target === back) close(); });

  const head = el("div", "display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--border-color,#3a3a3a)");
  head.appendChild(el("b", "font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap", base.file || base.name || ""));
  head.appendChild(el("span", "color:#888;white-space:nowrap",
    [base.position, base.format, base.resolution?.replace("x", "×"), base.size].filter(Boolean).join(" · ")));
  head.appendChild(el("span", "flex:1"));
  const x = el("span", CLOSE_X, "✕"); x.title = t("close"); x.onclick = close;
  head.appendChild(x);
  box.appendChild(head);

  const chips = el("div", "display:flex;gap:6px;padding:10px 16px 0");
  const chip = (label, c) => chips.appendChild(el("span", `padding:2px 10px;border-radius:9px;border:1px solid ${c}99;`
    + `color:${c};background:${c === OFF ? "transparent" : c + "22"}`, label));
  chip(base.parameters ? "parameters" : base.rebuilt ? "parameters ↻" : "parameters", color(base));
  chip("prompt", base.prompt ? ON : OFF);
  chip("workflow", base.workflow ? ON : OFF);
  box.appendChild(chips);

  const note = el("div", "padding:10px 16px 0;color:#999");
  const pre = el("pre", "margin:10px 16px;padding:10px;background:var(--comfy-input-bg,#1f1f1f);border-radius:6px;"
    + "overflow:auto;white-space:pre-wrap;word-break:break-word;font:12px Consolas,'Courier New',monospace;"
    + "color:var(--input-text,#cfcfcf);min-height:60px;flex:1", t("loading"));
  box.appendChild(note); box.appendChild(pre);
  const actions = el("div", "display:flex;gap:8px;justify-content:flex-end;padding:0 16px 14px");
  box.appendChild(actions);
  document.body.appendChild(back);

  let full = null;
  if (base.name) {
    try {
      const r = await api.fetchApi(`/rigstools/image_meta?full=1&filename=${encodeURIComponent(base.name)}`);
      if (r.ok) full = await r.json();
    } catch { /* falls back to the preview */ }
  }
  const text = full ? full.text : base.preview || "";
  if (!full && text) note.textContent = t("short");
  else if (!text) note.textContent = t("nothing");
  else if (!(full ?? base).parameters && (full ?? base).rebuilt) note.textContent = t("rebuiltNote");
  else note.remove();
  pre.textContent = text.replace(/^\s+/, "") || "—";

  actions.appendChild(button(t("copyParams"), (b) => copy(text, b), !text));
  const prompt = full?.prompt_json;
  actions.appendChild(button(t("copyPrompt"), (b) => copy(JSON.stringify(prompt, null, 2), b), !prompt));
  const wf = full?.workflow_json;
  actions.appendChild(button(t("openWf"), async () => {
    close();
    await app.loadGraphData(wf, true, true, (base.file || "workflow").replace(/\.[^.]+$/, ""));
  }, !wf || typeof wf !== "object"));
  resizable(box);   // with the text in: the window keeps this size until it is dragged
}

// -------------------------------------------------- drawing hooks (only on the two loader types)

const WARN = "#e8a33a";
const PREVIEW_INSET = 12;   // px between the preview picture and the node border

function drawCross(ctx, at) {
  if (!at) return;
  const [x, y] = at, d = 4.5;
  ctx.save();
  ctx.strokeStyle = WARN; ctx.lineWidth = 2.2; ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(x - d, y - d); ctx.lineTo(x + d, y + d);
  ctx.moveTo(x + d, y - d); ctx.lineTo(x - d, y + d);
  ctx.stroke();
  ctx.restore();
}

/** State of the outputs of any Rigstools node: {OUT: "off" | "rebuilt" | "warn"} and the reason per output.
 *  Loaders know it from the file; the other nodes predict it from the loader upstream or take it from the last run. */
function outputStates(node) {
  if (node?._rigInfo && [LOADER, FOLDER, PARAMS].includes(node.type)) {
    const info = node._rigInfo;
    if (info.error) return null;
    const states = {
      METADATA_RAW: info.prompt || info.workflow || info.parameters ? "on" : "off",
      PARAMETERS: info.parameters ? "on" : info.rebuilt ? "rebuilt" : "off",
      ...(node._rigPanel?.slotStates?.() ?? {}),
    };
    const reason = (name) => {
      if (name === "METADATA_RAW" && states.METADATA_RAW === "off") return t("whyMeta");
      if (name === "PARAMETERS" && states.PARAMETERS === "off") return t(info.prompt ? "whyParamsRebuild" : "whyParams");
      return node._rigPanel?.reason?.(name) ?? null;
    };
    return { states, reason };
  }
  const st = node?._rigPredicted ?? node?._rigState;
  if (!st) return null;
  const states = {};
  for (const k of st.off ?? []) states[k] = "off";
  for (const k of st.rebuilt ?? []) states[k] = "rebuilt";
  for (const k of st.warn ?? []) states[k] = states[k] === "off" ? "off" : "warn";
  return { states, reason: (name) => reasonText(st.reasons?.[name]) };
}

/** Name of a value in the messages: as in the A1111 text / the panel fields. */
const keyName = (k) => ({ clip_skip: "clip skip", positive: "positive prompt", negative: "negative prompt" }[k] ?? k ?? "");

function reasonText(r) {
  if (!r?.code) return null;
  return t("why_" + r.code).replace("{k}", keyName(r.k)).replace("{v}", r.v ?? "").replace("{input}", r.input ?? "");
}

function outputReason(node, name) {
  return outputStates(node)?.reason(name) ?? null;
}

/** Outputs: dim the ones that carry nothing, ↻ for rebuilt parameters, amber ✕ on a connected output whose value
 *  is a substitute (a default / fallback, an empty string, incomplete hashes). */
function patchSlots(proto) {
  const drawSlots = proto.drawSlots;
  proto.drawSlots = function (ctx, ...rest) {
    const os = ctx ? outputStates(this) : null;
    if (!os) return drawSlots.call(this, ctx, ...rest);
    const touched = [];
    for (const slot of this._concreteOutputs ?? []) {
      const st = os.states[slot.name];
      if (!st || st === "on") continue;
      const draw = slot.draw;
      touched.push([slot, draw, slot.label, slot.color_on, slot.color_off]);
      if (st === "rebuilt") {
        slot.label = (slot.label || slot.localized_name || slot.name) + " ↻";
        slot.color_on = slot.color_off = REBUILT;
      }
      const cross = st === "warn" || (st === "off" && !!os.reason(slot.name));   // "no LoRA" has no reason: no ✕
      slot.draw = function (c, opts) {
        const alpha = c.globalAlpha;
        if (st === "off") c.globalAlpha = alpha * 0.4;
        try { return draw.call(this, c, opts); }
        finally {
          c.globalAlpha = alpha;
          if (cross && this.isConnected && !opts?.lowQuality) drawCross(c, this._centreOffset);
        }
      };
    }
    try { return drawSlots.call(this, ctx, ...rest); }
    finally {
      for (const [slot, draw, label, on, off] of touched) {
        slot.draw = draw; slot.label = label; slot.color_on = on; slot.color_off = off;
        if (draw === Object.getPrototypeOf(slot).draw) delete slot.draw;
      }
    }
  };
}

function patchLoader(proto) {
  // caption under the image: the preview widget draws "W × H" with fillText inside drawWidgets
  const drawWidgets = proto.drawWidgets;
  proto.drawWidgets = function (ctx, ...rest) {
    const info = this._rigInfo;
    if (!info || info.error || !ctx) return drawWidgets.call(this, ctx, ...rest);
    const node = this;
    const own = Object.prototype.hasOwnProperty.call(ctx, "fillText");
    const original = ctx.fillText;
    ctx.fillText = function (text, x, y, ...more) {
      if (typeof text === "string" && /^\d+ × \d+$/.test(text)) {
        const room = node.size[0] - 12;
        const fit = captions(text, info).find((c) => this.measureText(c).width <= room) ?? text;
        return original.call(this, fit, x, y, ...more);
      }
      return original.call(this, text, x, y, ...more);
    };
    try { return drawWidgets.call(this, ctx, ...rest); }
    finally { if (own) ctx.fillText = original; else delete ctx.fillText; }
  };

  patchSlots(proto);
}

// -------------------------------------------------- "Load image with parameters": picture + parameter fields

const PANEL_STR = {
  en: { edited: "Changed by hand — goes to the output instead of the value from the image. ↺ returns it",
    reset: "Return the value from the image", missing: "Not in the image — the default value is used",
    loraMissing: "Not found in models/loras", modelMissing: "Not found in models/checkpoints — the name is passed as is",
    noLora: "no LoRA", loading: "…",
    head: "Parameters from the file", lgFile: "from the file", lgEdited: "changed by hand", lgMissing: "not in the file",
    lgPrompt: "LoRA from the prompt", lgLoraMissing: "LoRA not found", lgLoraFound: "LoRA found",
    loraPrompt: "a <lora:…> tag in the prompt (the file has no Lora stack)" },
  ru: { edited: "Изменено вручную — на выход идёт это значение вместо значения из картинки. ↺ — вернуть",
    reset: "Вернуть значение из картинки", missing: "Нет в картинке — используется значение по умолчанию",
    loraMissing: "Не найдена в models/loras", modelMissing: "Не найден в models/checkpoints — имя передаётся как есть",
    noLora: "нет LoRA", loading: "…",
    head: "Параметры из файла", lgFile: "из файла", lgEdited: "изменено вручную", lgMissing: "нет в файле",
    lgPrompt: "LoRA из промпта", lgLoraMissing: "LoRA не найдена", lgLoraFound: "LoRA найдена",
    loraPrompt: "тег <lora:…> в промпте (в файле нет Lora stack)" },
};
const pt = (k) => {
  const loc = String(app.extensionManager?.setting?.get?.("Comfy.Locale") ?? "en").toLowerCase();
  return PANEL_STR[loc.startsWith("ru") ? "ru" : "en"][k] ?? PANEL_STR.en[k];
};

// field key -> output name (used to dim the outputs that get a default value)
const FIELD_OUT = { positive: "POSITIVE", negative: "NEGATIVE", seed: "SEED", steps: "STEPS", cfg: "CFG",
  clip_skip: "CLIP", width: "WIDTH", height: "HEIGHT", sampler: "SAMPLER", scheduler: "SCHEDULER", model: "MODEL_NAME" };

// the card both panels (Load image with parameters, Save image) put their values in: a header, the fields, a legend
const DOT_KINDS = ["graph", "input", "file", "edited", "missing"];
function dot(kind) { const i = el("i"); i.className = "rig-dot " + kind; return i; }
function setDot(i, kind) { for (const k of DOT_KINDS) i.classList.toggle(k, k === kind); }
// The mouse wheel as over the stock multiline text widget: over a field that can scroll (a prompt, the LoRA list)
// it only scrolls — also at the end of the text; Ctrl + wheel, sideways scrolling and everything else zoom the canvas.
function wheelLikeStock(root) {
  root.addEventListener("wheel", (e) => {
    const box = e.target.closest?.("textarea,.rig-loras,.rig-t > .rig-v");
    const canvas = app.canvas;
    const toCanvas = () => {
      e.preventDefault(); e.stopPropagation();
      if (canvas?.processMouseWheel) canvas.processMouseWheel(e);
      else canvas?.canvas?.dispatchEvent(new WheelEvent("wheel", e));
    };
    if (e.ctrlKey || Math.abs(e.deltaX) > Math.abs(e.deltaY)) return toCanvas();
    if (box && box.scrollHeight > box.clientHeight + 1) { e.stopPropagation(); return; }
    toCanvas();
  }, { passive: false });
}

// legend marks of the LoRA chips, only for the kinds that are on the node: [chip class, text, shown]
function loraLegend(leg, items) {
  for (const [cls, text, on] of items) {
    if (!on) continue;
    const sp = el("span"), mark = el("i"); mark.className = cls; sp.className = "lx";
    sp.append(mark, document.createTextNode(text)); leg.appendChild(sp);
  }
}

function legend(items) {
  const leg = el("div"); leg.className = "rig-leg";
  for (const [kind, text] of items) { const sp = el("span"); sp.append(dot(kind), document.createTextNode(text)); leg.appendChild(sp); }
  return leg;
}

let panelCss = false;
// settings sidebar: our own icon instead of the generic folder — Lucide "flask-conical", the outline style of the other
// icons there (the colour alembic of the nodes reads poorly at that size as an outline)
const SETTINGS_ICON = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2" ` +
  `stroke-linecap="round" stroke-linejoin="round"><path d="M14 2v6a2 2 0 0 0 .245.96l5.51 10.08A2 2 0 0 1 18 22H6a2 2 0 0 1` +
  `-1.755-2.96l5.51-10.08A2 2 0 0 0 10 8V2"/><path d="M6.453 15h11.094"/><path d="M8.5 2h7"/></svg>`;
(() => {
  const st = document.createElement("style");
  const url = `url("data:image/svg+xml,${encodeURIComponent(SETTINGS_ICON)}")`;
  st.textContent = `[data-nav-id="root/Rigstools"] > i{-webkit-mask-image:${url} !important;mask-image:${url} !important}`;
  document.head.appendChild(st);
})();

function addPanelCss() {
  if (panelCss) return;
  panelCss = true;
  const st = document.createElement("style");
  // labels, field background and outline as the stock widgets and slot names draw them (LiteGraph settings)
  const LG = globalThis.LiteGraph ?? {};
  const font = `${LG.NODE_SUBTEXT_SIZE ?? 12}px ${LG.NODE_FONT ?? "Inter"}, Arial, sans-serif`;
  st.textContent = `
  .rig-panel{--rig-label-font:${font};--rig-label:${LG.WIDGET_SECONDARY_TEXT_COLOR ?? "#999"};
    --rig-slot:${LG.NODE_TEXT_COLOR ?? "#aaa"};--rig-field:${LG.WIDGET_BGCOLOR ?? "#222"};--rig-outline:${LG.WIDGET_OUTLINE_COLOR ?? "#666"}}
  .rig-card{background:rgba(0,0,0,.2);border-radius:8px;padding:5px 5px 6px;box-sizing:border-box;flex:0 0 auto}
  .rig-card .rig-fields,.rig-card .rig-row{gap:4px}
  .rig-card .rig-f{padding:0 5px}.rig-card .rig-f > label{margin-right:4px}
  .rig-card-head{color:var(--rig-slot);font:var(--rig-label-font);text-transform:uppercase;margin:0 3px 5px;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .rig-leg{display:flex;flex-wrap:wrap;gap:3px 12px;font-size:10px;color:#888;margin:6px 3px 0}
  .rig-leg span{display:block;white-space:nowrap}
  .rig-leg .rig-dot{margin:0 4px 0 0}
  .rig-dot{width:6px;height:6px;border-radius:50%;display:inline-block;flex:0 0 auto;box-sizing:border-box;vertical-align:middle}
  label > .rig-dot{margin:0 3px 0 0;vertical-align:calc(.36em - 3px)}
  .rig-dot.graph{background:#8a8a8a}.rig-dot.input{background:#4fc3ff}.rig-dot.file{background:#81c784}
  .rig-dot.edited{background:#e8b75a}.rig-dot.missing{background:transparent;box-shadow:inset 0 0 0 1.3px #8a8a8a}
  .rig-panel{display:flex;flex-direction:column;gap:6px;font:12px Arial,sans-serif;color:var(--input-text,#ddd);
    box-sizing:border-box;height:100%;padding:0 2px 4px}
  .rig-panel .rig-img{flex:1 1 auto;min-height:220px;display:flex;align-items:center;justify-content:center;overflow:hidden}
  .rig-panel .rig-img{position:relative}
  .rig-panel .rig-img img{max-width:100%;max-height:100%;object-fit:contain;display:block}
  .rig-panel .rig-img.wait img,.rig-panel .rig-img.fail img{visibility:hidden}
  .rig-panel .rig-img.wait::after{content:"";position:absolute;left:50%;top:50%;width:28px;height:28px;margin:-14px 0 0 -14px;
    border:3px solid #8888;border-top-color:transparent;border-radius:50%;animation:rig-spin .9s linear infinite}
  @keyframes rig-spin{to{transform:rotate(360deg)}}
  .rig-panel .rig-cap{flex:0 0 auto;color:#888;font-size:10px;line-height:13px;text-align:center;margin-top:-3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .rig-panel .rig-fields{display:flex;flex-direction:column;gap:6px;flex:0 0 auto}
  .rig-panel .rig-row{display:grid;gap:6px}
  .rig-panel .rig-f{position:relative;background:var(--rig-field);border:1px solid var(--rig-outline);border-radius:8px;
    display:flex;align-items:baseline;min-width:0;height:24px;box-sizing:border-box;padding:0 7px}
  .rig-panel .rig-f > label{flex:1 20 auto;min-width:2.4em;color:var(--rig-label);font:var(--rig-label-font);margin-right:5px;white-space:nowrap;overflow:hidden;
    text-overflow:ellipsis;pointer-events:none}
  .rig-panel .rig-f input,.rig-panel .rig-f select{flex:0 1 auto;min-width:1.6em;text-overflow:ellipsis;background:transparent;border:0;outline:0;
    color:inherit;font:inherit;text-align:right;padding:0;appearance:none;-webkit-appearance:none;cursor:text}
  .rig-panel .rig-f select{cursor:pointer;text-align:right;text-align-last:right}
  .rig-panel textarea,.rig-panel .rig-loras{overscroll-behavior:contain}
  .rig-panel .rig-f > .rig-v.tail{direction:rtl}
  .rig-panel .rig-f > .rig-tail{display:none;position:absolute;top:0;height:22px;line-height:22px;pointer-events:none;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;direction:rtl;text-align:right}
  .rig-panel .rig-f.tailon > .rig-tail{display:block}
  .rig-panel .rig-f.tailon > input{color:transparent}
  .rig-panel .ovr > .rig-tail{color:#e8b75a}.rig-panel .miss > .rig-tail{color:#777;font-style:italic}
  .rig-panel .rig-f select option{background:var(--comfy-menu-bg,#2b2b2b);color:var(--input-text,#ddd)}
  .rig-panel .rig-t{position:relative;background:var(--rig-field);border:1px solid var(--rig-outline);border-radius:8px;
    padding:4px 8px;box-sizing:border-box}
  .rig-panel .rig-t > label{display:block;color:var(--rig-label);font:var(--rig-label-font);margin-bottom:2px;pointer-events:none;white-space:nowrap}
  .rig-panel .rig-t textarea{width:100%;box-sizing:border-box;background:transparent;border:0;outline:0;resize:none;
    overflow-y:auto;min-height:30px;scrollbar-width:thin;
    color:inherit;font:12px/15px Arial,sans-serif;padding:0;display:block}
  .rig-panel .ovr{border-color:#d9a441aa}
  .rig-panel .ovr input,.rig-panel .ovr select,.rig-panel .ovr textarea{color:#e8b75a}
  .rig-panel .miss input,.rig-panel .miss select,.rig-panel .miss textarea{color:#777;font-style:italic}
  .rig-panel .bad input{color:#d77}
  .rig-panel .rig-reset{display:none;position:absolute;right:4px;top:3px;color:#d9a441;cursor:pointer;font-size:12px;
    background:var(--rig-field);padding:0 3px;border-radius:4px;line-height:16px}
  .rig-panel .rig-f .rig-reset{top:50%;transform:translateY(-50%)}
  .rig-panel .ovr > .rig-reset{display:block}
  .rig-panel .ovr.rig-f input,.rig-panel .ovr.rig-f select{margin-right:16px;margin-left:-16px;position:relative;
    background:var(--rig-field)}
  .rig-panel .rig-loras{display:flex;flex-wrap:wrap;gap:4px;align-items:baseline;min-height:24px;max-height:64px;overflow-y:auto;
    scrollbar-width:thin;
    background:var(--rig-field);border:1px solid var(--rig-outline);border-radius:8px;padding:3px 8px;box-sizing:border-box}
  .rig-panel .rig-loras > label{color:var(--rig-label);font:var(--rig-label-font);margin-right:2px}
  .rig-panel .rig-chip{border:1px solid #5fb87866;color:#cfe9d6;border-radius:9px;padding:0 7px;line-height:16px;
    white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:ellipsis}
  .rig-panel .rig-chip.bad{border-color:#d7777799;color:#e59a9a}
  .rig-panel .rig-chip.prev{border-style:dashed}
  .rig-panel .rig-chip.tag{border-style:dotted;border-width:1.5px}
  .rig-leg .rig-prev.tag{border-style:dotted;border-width:1.5px}
  .rig-leg .rig-prev.bad{border-style:solid;border-color:#d77777cc}
  .rig-leg .rig-prev.ok{border-style:solid}
  .rig-leg .rig-prev{display:inline-block;width:12px;height:7px;border:1px dashed #5fb878aa;border-radius:4px;margin-right:4px;box-sizing:border-box}
  .rig-panel .rig-chip b{font-weight:normal;color:#8a8a8a;margin-left:4px}
  .rig-panel .rig-none{color:#777;font-style:italic}
  .rig-panel .rig-f.keep > label{flex:0 0 auto}
  .rig-panel .rig-f.keep input{flex:0 1 auto;min-width:2em}
  .rig-panel .rig-f.keep{justify-content:space-between}
  .rig-panel .rig-f > .rig-v{flex:0 1 auto;min-width:1.6em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:right}
  .rig-panel .rig-t > .rig-v{line-height:15px;overflow:hidden;display:-webkit-box;-webkit-box-orient:vertical;word-break:break-word}
  .rig-panel .miss > .rig-v{color:#777;font-style:italic}
  .rig-panel .rig-f > label,.rig-panel .rig-f > .rig-v,.rig-panel .rig-f input,.rig-panel .rig-f select{line-height:22px;height:22px}`;
  document.head.appendChild(st);
}

function viewUrl(name) {
  const m = /\s*\[(input|output|temp)\]\s*$/i.exec(name || "");
  const type = m ? m[1].toLowerCase() : "input";
  const path = m ? name.slice(0, m.index) : name;
  const i = path.lastIndexOf("/");
  const q = new URLSearchParams({ filename: path.slice(i + 1), subfolder: i >= 0 ? path.slice(0, i) : "", type });
  return api.apiURL(`/view?${q}`);
}

// Settings → Rigstools → Debug: every step of loading a picture goes to the browser console (the server side writes
// what it read from the file to the ComfyUI console)
const dbg = (...a) => { if (app.extensionManager?.setting?.get?.("Rigstools.Debug.Log")) console.info(...a); };

/** Why a /view URL did not give a picture: the HTTP answer, the type and size of the body, whether it decodes. */
async function diagnose(url) {
  const out = {};
  try {
    const t0 = performance.now();
    const r = await fetch(url, { cache: "no-store" });
    out.status = r.status;
    out.type = r.headers.get("content-type");
    const blob = await r.blob();
    out.bytes = blob.size;
    out.fetchMs = Math.round(performance.now() - t0);
    if (r.ok) {
      try { const bmp = await createImageBitmap(blob); out.decodes = `${bmp.width}×${bmp.height}`; bmp.close?.(); }
      catch (e) { out.decodes = `no: ${e?.message ?? e}`; }
    } else out.body = (await blob.text()).slice(0, 200);
  } catch (e) { out.fetch = `failed: ${e?.message ?? e}`; }
  return out;
}

function paramsPanel(node, inputName) {
  addPanelCss();
  const state = { image: null, values: {} };   // serialized: the hand-typed values of this picture
  let data = null;                              // what the server read from the file
  let fetched = null;
  const root = el("div"); root.className = "rig-panel";
  const imgBox = el("div"); imgBox.className = "rig-img";
  const img = el("img"); imgBox.appendChild(img);
  const cap = el("div"); cap.className = "rig-cap";
  const fieldsBox = el("div"); fieldsBox.className = "rig-fields";
  const card = el("div"); card.className = "rig-card";
  const cardHead = el("div", null, pt("head")); cardHead.className = "rig-card-head";
  const leg = legend([["file", pt("lgFile")], ["edited", pt("lgEdited")], ["missing", pt("lgMissing")]]);
  // the LoRA chip kinds, always listed: found (solid), a tag in the prompt (dotted), not found (red)
  loraLegend(leg, [["rig-prev ok", pt("lgLoraFound"), true], ["rig-prev tag", pt("lgPrompt"), true],
                   ["rig-prev bad", pt("lgLoraMissing"), true]]);
  card.append(cardHead, fieldsBox, leg);
  root.append(imgBox, cap, card);
  for (const ev of ["pointerdown", "keydown"]) {
    fieldsBox.addEventListener(ev, (e) => { if (e.target.closest("input,select,textarea")) e.stopPropagation(); });
  }
  wheelLikeStock(root);

  const controls = {};
  const wrap = {};
  const dots = {};
  const shown = (k) => (k in state.values ? state.values[k] : data?.fields?.[k]);

  function markAll() {
    const missing = new Set(data?.missing ?? []);
    for (const k of Object.keys(controls)) {
      const w = wrap[k];
      w.classList.toggle("ovr", k in state.values);
      w.classList.toggle("miss", !(k in state.values) && missing.has(k));
      w.title = k in state.values ? pt("edited") : missing.has(k) ? pt("missing") : "";
      setDot(dots[k], k in state.values ? "edited" : missing.has(k) || !data || data.error ? "missing" : "file");
      if (k === "model") {
        const bad = data && !(k in state.values) && !missing.has("model") && !data.model_found;
        w.classList.toggle("bad", !!bad);
        if (bad) w.title = pt("modelMissing");
      }
    }
    node.setDirtyCanvas?.(true, false);
  }

  function commit(k) {
    const c = controls[k];
    const orig = data?.fields?.[k];
    const v = c.value;
    sizeControl(c);
    const same = k === "cfg" && v !== "" && !isNaN(v) ? Number(v) === Number(orig) : String(v) === String(orig);
    if (orig != null && same) delete state.values[k];
    else state.values[k] = v;
    state.image = node.widgets?.find((w) => w.name === "image")?.value ?? state.image;
    markAll();
    node.graph?.change?.();
  }

  function field(k, label, kind = "input", extra = {}) {
    const w = el("div"); w.className = (kind === "textarea" ? "rig-t" : "rig-f") + (extra.keepLabel ? " keep" : "");
    const d = dot("missing"); dots[k] = d;
    const l = el("label"); l.append(d, document.createTextNode(label)); w.appendChild(l);
    let c;
    if (kind === "textarea") { c = el("textarea"); c.rows = extra.rows ?? 3; c.spellcheck = false; }
    else if (kind === "select") { c = el("select"); }
    else { c = el("input"); c.type = "text"; c.size = 1; c.spellcheck = false; if (extra.mode) c.inputMode = extra.mode; }
    c.addEventListener("change", () => commit(k));
    if (kind === "input") c.addEventListener("input", () => sizeControl(c));
    if (kind !== "select") c.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && kind !== "textarea") { c.blur(); }
      if (e.key === "Escape") { c.value = k === "cfg" ? fmtCfg(shown(k) ?? "") : shown(k) ?? ""; c.blur(); }
    });
    w.appendChild(c);
    if (extra.tailCut) {
      // a long value (the model path) is cut at the start, so the file name stays visible: while the field is not
      // being edited, a copy of the value with "…" at the start lies over the input
      const tail = el("span"), bdi = el("bdi"); tail.className = "rig-tail"; tail.appendChild(bdi); w.appendChild(tail);
      c._rigTail = () => {
        const cut = document.activeElement !== c && c.scrollWidth > c.clientWidth + 1;
        w.classList.toggle("tailon", cut);
        if (!cut) return;
        bdi.textContent = c.value;
        tail.style.left = `${c.offsetLeft}px`; tail.style.width = `${c.offsetWidth}px`;
      };
      c.addEventListener("focus", c._rigTail); c.addEventListener("blur", c._rigTail);
      new ResizeObserver(() => c._rigTail()).observe(w);
    }
    const r = el("span", null, "↺"); r.className = "rig-reset"; r.title = pt("reset");
    r.addEventListener("pointerdown", (e) => { e.preventDefault(); e.stopPropagation();
      delete state.values[k]; c.value = k === "cfg" ? fmtCfg(data?.fields?.[k] ?? "") : data?.fields?.[k] ?? "";
      sizeControl(c); markAll(); node.graph?.change?.(); });
    w.appendChild(r);
    controls[k] = c; wrap[k] = w;
    return w;
  }
  const row = (cols, ...items) => { const r = el("div"); r.className = "rig-row"; r.style.gridTemplateColumns = cols; r.append(...items); return r; };

  fieldsBox.append(
    field("positive", "positive", "textarea", { rows: 4 }),
    field("negative", "negative", "textarea", { rows: 4 }),
    row("repeat(4, auto)", field("seed", "seed", "input", { mode: "numeric" }), field("steps", "steps", "input", { mode: "numeric" }),
      field("cfg", "cfg", "input", { mode: "decimal" }), field("clip_skip", "clip", "input", { mode: "numeric" })),
    row("repeat(2, auto)", field("sampler", "sampler", "select"), field("scheduler", "scheduler", "select")),
    row("1fr auto auto", field("model", "model", "input", { keepLabel: true, tailCut: true }), field("width", "width", "input", { mode: "numeric" }),
      field("height", "height", "input", { mode: "numeric" })),
  );
  const loraBox = el("div"); loraBox.className = "rig-loras";
  fieldsBox.appendChild(loraBox);

  function fillSelect(sel, list, value) {
    if (sel._list !== list) {
      sel.replaceChildren(...list.map((v) => { const o = el("option", null, v); o.value = v; return o; }));
      sel._list = list;
    }
    sel.value = value;
  }

  const mctx = document.createElement("canvas").getContext("2d");
  const measure = (t) => { mctx.font = "12px Arial, sans-serif"; return mctx.measureText(String(t ?? "")).width; };

  /** The value keeps the width of its text and the label gets shortened first ("sched…"). */
  function sizeControl(c) {
    if (c.tagName === "TEXTAREA") return;
    c.title = String(c.value ?? "");   // full value when it is cut off
    c.style.width = `${Math.ceil(measure(c.value) + (c.tagName === "SELECT" ? 4 : 2))}px`;
    if (c._rigTail) requestAnimationFrame(c._rigTail);
  }

  function render() {
    if (!data || data.error) {
      cap.textContent = data?.error ?? "";
      return;
    }
    const f = data.fields;
    for (const k of Object.keys(controls)) {
      const c = controls[k];
      if (document.activeElement === c) continue;
      if (k === "sampler") fillSelect(c, data.samplers, shown(k));
      else if (k === "scheduler") fillSelect(c, data.schedulers, shown(k));
      else c.value = k === "cfg" ? fmtCfg(shown(k) ?? "") : shown(k) ?? "";
      sizeControl(c);
    }
    const info = data.info;
    const [w, h] = String(info.resolution || "").split("x");
    const base = w && h ? `${w} × ${h}` : "";
    const ctx = document.createElement("canvas").getContext("2d");
    ctx.font = "10px Arial";
    cap.textContent = captions(base, info).find((c) => ctx.measureText(c).width <= root.clientWidth - 8) ?? base;

    const ll = el("label"); ll.append(dot(data.loras.length ? "file" : "missing"), document.createTextNode("lora"));
    loraBox.replaceChildren(ll);
    if (!data.loras.length) loraBox.appendChild(el("span", null, pt("noLora"))).className = "rig-none";
    const fromPrompt = data.lora_from === "prompt";   // the file has no Lora stack: the LoRA are its <lora:…> tags
    for (const l of data.loras) {
      const chip = el("span"); chip.className = "rig-chip" + (l.file ? "" : " bad") + (fromPrompt ? " tag" : "");
      const name = l.file ? l.file.replace(/\\/g, "/").split("/").pop().replace(/\.[^.]+$/, "") : l.name;   // the path is in the tooltip
      chip.append(name, el("b", null, `×${l.weight}`));
      chip.title = (l.file ? l.file : `${l.name} — ${pt("loraMissing")}`) + (fromPrompt ? ` — ${pt("loraPrompt")}` : "");
      loraBox.appendChild(chip);
    }
    markAll();
  }

  // the picture: spinner while it loads; when /view fails (the upload is not finished yet, the file is being
  // written…) it is asked again a few times with a fresh URL instead of showing a broken image
  // The picture is loaded the way the stock preview does it (same /view URL with the preview format and a fresh
  // rand, a time limit per attempt, a spinner meanwhile), with more attempts. Failures are always written to the
  // browser console with a diagnosis; with Settings → Rigstools → Debug on, every step is.
  let tries = 0, retry = null, timer = null, started = 0, current = "";
  const MAX_TRIES = 6, TIME_LIMIT = 8192;
  const tag = () => `[Rigstools] Load image with parameters #${node.id}`;
  img.addEventListener("load", () => {
    clearTimeout(timer);
    imgBox.classList.remove("wait", "fail");
    dbg(`${tag()}: picture loaded`, { image: fetched, attempt: tries + 1, ms: Math.round(performance.now() - started),
      size: `${img.naturalWidth}×${img.naturalHeight}` });
    tries = 0;
  });
  img.addEventListener("error", () => failed("error event"));
  function failed(why) {
    clearTimeout(timer);
    if (!fetched || !current) return;
    const image = fetched, url = current, attempt = tries + 1, ms = Math.round(performance.now() - started);
    diagnose(url).then((d) => console.warn(`${tag()}: picture attempt ${attempt}/${MAX_TRIES} failed (${why})`,
      { image, url, ms, ...d, connected: root.isConnected, visible: root.offsetParent !== null }));
    if (tries + 1 < MAX_TRIES) {
      tries += 1;
      clearTimeout(retry);
      retry = setTimeout(() => { if (fetched === image) showPicture(image); }, 300 * 2 ** Math.min(tries - 1, 4));
    } else {
      imgBox.classList.remove("wait"); imgBox.classList.add("fail");
      // the ComfyUI console gets one line too; the details stay in the browser console
      api.fetchApi("/rigstools/log", { method: "POST", body: JSON.stringify({ message: `Load image with parameters `
        + `#${node.id}: could not show the picture ${image} after ${MAX_TRIES} attempts (${why}); details in the `
        + `browser console (F12)` }) }).catch(() => {});
    }
  }
  function showPicture(image) {
    imgBox.classList.add("wait"); imgBox.classList.remove("fail");
    current = viewUrl(image) + (app.getPreviewFormatParam?.() ?? "") + (app.getRandParam?.() ?? `&rand=${Math.random()}`);
    started = performance.now();
    dbg(`${tag()}: picture attempt ${tries + 1}`, { image, url: current });
    clearTimeout(timer);
    timer = setTimeout(() => { if (current && !img.complete) { img.removeAttribute("src"); failed(`no answer in ${TIME_LIMIT} ms`); } }, TIME_LIMIT);
    img.src = current;
  }

  async function load(image, why = "") {
    fetched = image;
    tries = 0;
    dbg(`${tag()}: load`, { image, why });
    showPicture(image);
    data = { loading: true };
    const t0 = performance.now();
    try {
      const r = await api.fetchApi(`/rigstools/image_params?filename=${encodeURIComponent(image)}&node=${node.id}`);
      const j = await r.json();
      dbg(`${tag()}: image_params`, { image, status: r.status, ms: Math.round(performance.now() - t0), error: j.error });
      if (j.error) console.warn(`${tag()}: image_params answered ${r.status}`, { image, error: j.error });
      if (fetched !== image) return;
      if (j.error === "not found" && (load.misses = (load.misses ?? 0) + 1) <= 5) {   // not there yet: ask again
        setTimeout(() => { if (fetched === image) load(image, "retry: not found"); }, 400 * load.misses);
        return;
      }
      load.misses = 0;
      if (!j.error && imgBox.classList.contains("fail")) { tries = 0; showPicture(image); }   // the file is there now
      data = j;
      if (state.image !== image) { state.image = image; state.values = {}; }  // another picture: typed values go
      setInfo(node, j.error ? { error: j.error } : j.info);
    } catch (e) {
      console.warn(`${tag()}: image_params failed`, { image, error: String(e) });
      data = { error: String(e) };
    }
    render();
    requestAnimationFrame(() => {   // grow the node when the fields need more room than it has
      const need = node.computeSize?.()[1];
      if (need && node.size[1] < need) node.setSize?.([node.size[0], need]);
      node.setDirtyCanvas?.(true, true);
    });
  }

  const widget = node.addDOMWidget(inputName, "RIGSTOOLS_PARAMS", root, {
    getValue: () => JSON.stringify(state),
    setValue: (v) => {
      try {
        const o = typeof v === "string" ? JSON.parse(v || "{}") : v || {};
        state.image = o.image ?? null;
        state.values = o.values && typeof o.values === "object" ? { ...o.values } : {};
      } catch { state.image = null; state.values = {}; }
      render();
    },
    getMinHeight: () => (card.offsetHeight || 460) + 250,
    hideOnZoom: true,          // zoomed far out the panel is not drawn, as the other DOM widgets
  });

  node._rigPanel = {
    watch() {
      const v = node.widgets?.find((w) => w.name === "image")?.value;
      if (v && v !== fetched) load(v, fetched ? `image changed from ${fetched}` : "first draw");
    },
    value: (k) => shown(k),
    typed: (k) => k in state.values,
    loras: () => (data?.loras ?? []).map((l) => `${l.file ? l.file.replace(/\\/g, "/").replace(/\.[^./]+$/, "") : l.name} ×${l.weight}`),
    reason(outName) {
      const k = Object.keys(FIELD_OUT).find((key) => FIELD_OUT[key] === outName);
      if (!k || !data?.fields || k in state.values || !(data.missing ?? []).includes(k)) return null;
      const v = data.fields[k];
      return (v === "" || v == null ? t("whyEmpty") : t("whyDefault").replace("{v}", v)).replace("{k}", keyName(k));
    },
    slotStates() {
      if (!data?.fields) return {};
      const out = {};
      for (const k of data.missing ?? []) if (FIELD_OUT[k] && !(k in state.values)) out[FIELD_OUT[k]] = "off";
      if (!data.loras?.length) out.LORA_STACK = "off";
      return out;
    },
  };
  return widget;
}

// -------------------------------------------------- styled tooltips (drawn by Draftsman when it is installed)
// Contract: node.getStyledOutputTooltip(index) -> { lines: [{ kind: "info" | "warn" | "muted", text }] } | null.
// Draftsman keeps the first paragraph of the stock tooltip as the title and puts these lines under it; without
// Draftsman nothing calls this and the stock (static) tooltip is shown.

const clip = (v, n = 90) => { const s = String(v ?? "").replace(/\s+/g, " ").trim(); return s.length > n ? s.slice(0, n) + "…" : s; };
const OUT_FIELD = Object.fromEntries(Object.entries({ positive: "POSITIVE", negative: "NEGATIVE", seed: "SEED",
  steps: "STEPS", cfg: "CFG", clip_skip: "CLIP", width: "WIDTH", height: "HEIGHT", sampler: "SAMPLER",
  scheduler: "SCHEDULER", model: "MODEL_NAME" }).map(([k, v]) => [v, k]));

function valueLine(node, name) {
  const info = node._rigInfo;
  if ([LOADER, FOLDER, PARAMS].includes(node.type) && info && !info.error) {
    if (name === "IMAGE") return info.resolution ? t("ln_image").replace("{v}", [info.resolution.replace("x", " × "), info.format].filter(Boolean).join(" · ")) : null;
    if (name === "METADATA_RAW") return t("ln_file").replace("{v}", ["prompt", "workflow", "parameters"].filter((k) => info[k]).join(", ") || "fileinfo");
    if (name === "PARAMETERS" && info.parameters) return t("ln_file").replace("{v}", `«${clip(info.preview)}»`);
    if (name === "FILENAME" && info.file) return info.file;
    if ((name === "INDEX" || name === "COUNT") && info.position) return t("ln_position").replace("{v}", info.position);
    const panel = node._rigPanel;
    if (panel) {
      const k = OUT_FIELD[name];
      if (k) {
        const v = panel.value(k);
        if (v == null || v === "") return null;
        return t(panel.typed(k) ? "ln_typed" : "ln_image").replace("{v}", clip(v));
      }
      if (name === "LORA_STACK") { const l = panel.loras(); return l.length ? t("ln_loras").replace("{v}", clip(l.join(", "))) : null; }
    }
    return null;
  }
  const st = node._rigPredicted ?? node._rigState;
  const v = st?.values?.[name];
  if (!v) return null;
  const src = node.type === PEXT ? "ln_params" : "ln_meta";
  if (v.code === "nodes") return t("ln_nodes").replace("{v}", v.v);
  if (v.code === "present") return t("ln_present");
  if (v.code === "text") return t(src).replace("{v}", `«${clip(v.v)}»`);
  if (v.code === "count") return t("ln_count").replace("{v}", v.v);
  if (v.code === "loras") return t("ln_loras").replace("{v}", v.v);
  return t(src).replace("{v}", clip(v.v));
}

// titles of the output tooltips in both languages (from core/tooltips.py); the stock tooltip is English only,
// because a locales/ru/nodeDefs.json translation does not work for node names with "[...]"
let TITLES = {};
fetch(new URL("./tooltip_titles.json", import.meta.url)).then((r) => r.json()).then((j) => { TITLES = j || {}; }).catch(() => {});
function titleOf(node, name) {
  const loc = String(app.extensionManager?.setting?.get?.("Comfy.Locale") ?? "en").toLowerCase();
  const tt = TITLES[node.type]?.[name];
  return tt ? (loc.startsWith("ru") ? tt.ru : tt.en) : undefined;
}

function styledLines(node, index) {
  const name = node.outputs?.[index]?.name;
  if (!name) return null;
  const res = styledBody(node, name);
  if (res) res.title = titleOf(node, name);
  return res;
}

function styledBody(node, name) {
  const os = outputStates(node);
  if (!os) return null;
  const st = os.states[name];
  const why = os.reason(name);
  const lines = [];
  if (st === "rebuilt") lines.push({ kind: "info", text: t("ln_rebuilt") });
  if ((st === "off" || st === "warn") && why) lines.push({ kind: "warn", text: why });
  if (st === "off" && !why) {
    if (name === "LORA_STACK") lines.push({ kind: "muted", text: t("ln_noLora") });
    else if (name === "ADDITIONAL_HASHES") lines.push({ kind: "muted", text: t("ln_noHashes") });
  }
  if (name === "NOT_FOUND") {
    const r = (node._rigPredicted ?? node._rigState)?.reasons?.ADDITIONAL_HASHES;
    lines.push(r?.v ? { kind: "muted", text: t("ln_notFound").replace("{v}", r.v) } : { kind: "info", text: t("ln_allLoras") });
    return { lines };
  }
  if (st !== "off") {
    const v = valueLine(node, name);
    if (v) lines.push({ kind: "info", text: v });
  }
  return lines.length ? { lines } : null;
}

// -------------------------------------------------- Metadata / Parameters extractor, LoRA hashes:
// the state of their outputs is predicted from our loader upstream (before a run) or comes from the last run.

const META = "Metadata extractor [Rigstools]";
const PEXT = "Parameters extractor [Rigstools]";
const HASHES = "LoRA hashes for Image Saver [Rigstools]";
const READERS = [META, PEXT, HASHES];
const PARAM_KEYS = { seed: "SEED", steps: "STEPS", cfg: "CFG", clip_skip: "CLIP", width: "WIDTH", height: "HEIGHT",
  sampler: "SAMPLER", scheduler: "SCHEDULER", positive: "POSITIVE", negative: "NEGATIVE", model: "MODEL_NAME" };

function upstream(node, inputName) {
  const inp = node.inputs?.find((i) => i.name === inputName);
  if (inp?.link == null || !node.graph) return null;
  const links = node.graph.links;
  const link = links?.get ? links.get(inp.link) : links?.[inp.link];
  const src = link && node.graph.getNodeById(link.origin_id);
  return src ? { node: src, slot: src.outputs?.[link.origin_slot]?.name } : null;
}

const widgetValue = (node, name) => node.widgets?.find((w) => w.name === name)?.value;
const isLoader = (n) => [LOADER, FOLDER, PARAMS].includes(n?.type);
const imageOf = (loader) => (loader.type === FOLDER ? loader._rigInfo?.name : widgetValue(loader, "image"));

/** Where the parameters text of `node`'s input comes from: {loader, image, info, text: has the text} or null. */
function paramsSource(up) {
  if (!up) return null;
  if (isLoader(up.node) && up.slot === "PARAMETERS") {
    const info = up.node._rigInfo;
    return info && !info.error ? { image: imageOf(up.node), info, text: !!(info.parameters || info.rebuilt) } : null;
  }
  if (up.node.type === META && up.slot === "PARAMETERS") {
    const m = upstream(up.node, "metadata_raw");
    if (!m || !isLoader(m.node) || m.slot !== "METADATA_RAW") return null;
    const info = m.node._rigInfo;
    if (!info || info.error) return null;
    const flag = widgetValue(up.node, "parameters_from_prompt") !== false;
    return { image: imageOf(m.node), info, text: !!(info.parameters || (flag && info.rebuilt)) };
  }
  return null;
}

/** Same lookup as Load image with parameters: missing values and LoRA files of a picture (cached for a while). */
const paramsCache = new Map();
function imageParams(image) {
  const hit = paramsCache.get(image);
  if (hit && Date.now() - hit.at < 15000) return hit.value;
  const entry = { at: Date.now(), value: null };
  paramsCache.set(image, entry);
  api.fetchApi(`/rigstools/image_params?filename=${encodeURIComponent(image)}`)
    .then((r) => r.json()).then((j) => { entry.value = j.error ? { error: j.error } : j; app.canvas?.setDirty?.(true, false); })
    .catch(() => { entry.value = { error: "unavailable" }; });
  return hit?.value ?? null;   // the previous value while the new one is loading
}

const ALL_MISSING = Object.keys(PARAM_KEYS);

function predictParams(node, src) {
  let missing, loras, fields = null;
  if (!src.text) { missing = ALL_MISSING; loras = []; }
  else {
    const d = imageParams(src.image);
    if (!d || d.error) return null;
    missing = d.missing ?? []; loras = d.loras ?? []; fields = d.fields;
  }
  const st = { off: [], rebuilt: [], warn: [], reasons: {} };
  for (const k of missing) {
    const out = PARAM_KEYS[k];
    if (!out) continue;
    st.off.push(out);
    if (["positive", "negative", "model"].includes(k)) st.reasons[out] = { code: "empty", k };
    else {
      const w = node.inputs?.find((i) => i.name === `fallback_${k}`)?.link != null ? "…" : widgetValue(node, `fallback_${k}`);
      st.reasons[out] = { code: "fallback", k, v: w, input: `fallback_${k}` };
    }
  }
  if (!loras.length) st.off.push("LORA_STACK");
  st.values = {};
  if (fields) for (const [k, out] of Object.entries(PARAM_KEYS)) if (!missing.includes(k)) st.values[out] = { code: "value", v: fields[k] };
  if (loras.length) st.values.LORA_STACK = { code: "loras", v: loras.length };
  return st;
}

function predict(node) {
  if (node.type === META) {
    const m = upstream(node, "metadata_raw");
    if (!m || !isLoader(m.node) || m.slot !== "METADATA_RAW") return null;
    const info = m.node._rigInfo;
    if (!info || info.error) return null;
    const flag = widgetValue(node, "parameters_from_prompt") !== false;
    const st = { off: [], rebuilt: [], warn: [], reasons: {} };
    for (const [k, have] of [["PROMPT", info.prompt], ["WORKFLOW", info.workflow]]) {
      if (!have) { st.off.push(k); st.reasons[k] = { code: "noBlock", v: k.toLowerCase() }; }
    }
    st.values = {};
    if (info.prompt) st.values.PROMPT = { code: "present" };
    if (info.workflow) st.values.WORKFLOW = { code: "present" };
    st.values.FILEINFO = { code: "value", v: [info.resolution, info.size].filter(Boolean).join(" · ") };
    if (info.parameters || (flag && info.rebuilt)) st.values.PARAMETERS = { code: "text", v: info.preview };
    if (!info.parameters) {
      if (flag && info.rebuilt) st.rebuilt.push("PARAMETERS");
      else {
        st.off.push("PARAMETERS");
        st.reasons.PARAMETERS = { code: info.prompt ? (flag ? "noParamsRebuild" : "noParamsOff") : "noParams" };
      }
    }
    return st;
  }
  if (node.type === PEXT) {
    const src = paramsSource(upstream(node, "parameters"));
    return src ? predictParams(node, src) : null;
  }
  if (node.type === HASHES) {
    const up = upstream(node, "lora_stack");
    if (!up || up.slot !== "LORA_STACK") return null;
    let loras;
    if (up.node.type === PARAMS) {
      const info = up.node._rigInfo;
      if (!info || info.error) return null;
      const d = imageParams(imageOf(up.node));
      if (!d || d.error) return null;
      loras = d.loras ?? [];
    } else if (up.node.type === PEXT) {
      const src = paramsSource(upstream(up.node, "parameters"));
      if (!src) return null;
      if (!src.text) loras = [];
      else { const d = imageParams(src.image); if (!d || d.error) return null; loras = d.loras ?? []; }
    } else return null;
    const lost = loras.filter((l) => !l.file).map((l) => l.name);
    const prefix = String(widgetValue(node, "additional_hashes") ?? "").trim();
    const st = { off: [], rebuilt: [], warn: [], reasons: {} };
    if (!loras.length && !prefix) st.off.push("ADDITIONAL_HASHES");          // no LoRA: dimmed, no ✕
    if (lost.length) {
      if (lost.length === loras.length && !prefix) st.off = ["ADDITIONAL_HASHES"];
      else st.warn.push("ADDITIONAL_HASHES");
      st.reasons.ADDITIONAL_HASHES = { code: "lorasMissing", v: lost.join(", ") };
    }
    const found = loras.length - lost.length;
    if (found) st.values = { ADDITIONAL_HASHES: { code: "count", v: found } };
    return st;
  }
  return null;
}

// -------------------------------------------------- "Save image": what will be written, what was written
// Before a run the panel shows the values the server collects from the graph (POST /rigstools/save_preview with
// the API prompt); after a run — what ended up in the file. The dot of a value: grey = from the graph,
// blue = from a connected input, amber = not found.

const SAVE = "Save image [Rigstools]";
const SRC_COLOR = { graph: "#8a8a8a", input: "#4fc3ff", file: "#81c784", missing: "#8a8a8a" };

const SAVE_STR = {
  en: {
    head: "What will be written", saved: "Saved", next: "Will be saved as", file: "saved as",
    pref: "Preference", prefFile: "File", prefGraph: "Graph", prefInput: "Input",
    prefTipInput: "A connected input wins; without one — the graph, then the source file",
    prefTipGraph: "The values found in the graph win; then a connected input, then the source file",
    prefTipFile: "The generation data of the source picture win; then a connected input, then the graph. The size is "
      + "not taken from the file",
    lgGraph: "from the graph", lgInput: "from an input", lgFile: "from the source file", lgMissing: "not found",
    lgPrev: "LoRA of an earlier pass", lgPrompt: "LoRA from the prompt", lgLoraMissing: "LoRA not found", lgLoraFound: "LoRA found",
    dlgNotePreview: "What the next run will write, as the node sees the graph now. Some values become known only when "
      + "the workflow runs (a prompt joined from several nodes, the size of a picture that is upscaled) — what was "
      + "actually written: the ComfyUI console with Settings → Rigstools → Debug on.",
    dlgNoteSaved: "The last save: these values were computed when the workflow ran and written into the file. Details: "
      + "the ComfyUI console with Settings → Rigstools → Debug on.",
    help: "🛟 Node Help", helpTitle: "Save image — file name and folder",
    helpIntro: "The variables work in filename and in path. path is a subfolder of the ComfyUI output folder "
      + "(a path that leads outside it is refused); / in path makes nested folders.",
    helpVars: "Variables",
    helpCols: "Variable|Description|Example", helpDateCols: "Code|Meaning|Example", helpExCols: "Pattern|Result",
    helpRows: "%date|date of saving|2026-11-08\n%date<format>|date and time in the given format, codes below|%date<%Y%m%d> → 20261108\n"
      + "%time|time of saving|143205\n%model|model file name without the folder and the extension|ilustmix_v111\n"
      + "%seed|seed|845041538454657\n%steps|steps|25\n%cfg|CFG|6.5\n%sampler|sampler|dpmpp_2m\n%scheduler|scheduler|karras\n"
      + "%width, %height|size of the saved picture|2256, 3376\n"
      + "%counter|next free number in the folder|1, 2, 3…\n%counter<N>|the same, N digits with leading zeros|%counter<4> → 0001",
    helpDate: "Codes of %date<…>",
    helpDateRows: "%Y|year|2026\n%y|year, two digits|26\n%m|month|11\n%d|day|08\n%H|hours (24 h)|14\n%M|minutes|32\n"
      + "%S|seconds|05\n%b|month, short name|Nov\n%B|month, full name|November\n%a|weekday, short|Sun\n%A|weekday, full|Sunday",
    helpRules: "Rules",
    helpRuleList: "A value that is not found becomes unknown.\n"
      + "Values known only at run time are shown in [ ] in the predicted name on the node.\n"
      + "An existing file is never overwritten: without %counter the next name gets _2, _3…\n"
      + "The characters < > : \" | ? * are removed; / in filename becomes _.",
    helpExamples: "Examples",
    helpExampleRows: "%date_%model_%seed_%counter<4>|2026-11-08_ilustmix_v111_845041538454657_0001.png\n"
      + "path: txt2img/%date|output/txt2img/2026-11-08/\npath: %model/%date<%Y-%m>|output/ilustmix_v111/2026-11/\n"
      + "STEP_1_%date<%Y-%m-%d-%H'%M'%S>_%model_%seed|STEP_1_2026-11-08-14'32'05_ilustmix_v111_845041538454657.png",
    loraPrompt: "from a <lora:…> tag in the prompt", loraFilePrompt: "an earlier pass: from a <lora:…> tag in the source file's prompt",
    loraStack: "an earlier pass: from the Lora stack of the source file",
    noLora: "no LoRA", size: "size", waiting: "Looking at the graph…",
    sec: "{n} file(s) · {s} s", ph: "Values in [ ] are determined at run time", atRun: "at run time",
    dlgWarn: "Warnings and notes", dlgDone: "Saving",
    paramsOk: "Parameters (A1111) written: passes: {v}, LoRA: {loras}", workflowIn: "Workflow embedded",
    workflowOff: "Workflow not embedded (metadata: parameters only)", metaNone: "No metadata written (metadata: none)",
    workflowBig: "Workflow ({v} KB) does not fit into the JPEG metadata (64 KB) — not embedded",
    workflowHint: "Turn on workflow_json to save the workflow next to the picture",
    workflowFile: "Workflow saved next to it: {v}", promptBig: "The API prompt does not fit into JPEG — only the workflow is embedded",
    paramsBig: "Even the parameters do not fit into JPEG — the file has no metadata",
    modelHash: "Model hash: {v} · {h}", modelMissing: "Model {v} not found in the models folders — no hash: by it Civitai recognises the model",
    loraMissing: "LoRA {v} not found in models/loras — no hash: by it Civitai recognises the LoRA",
    embeddingMissing: "Embedding {v} not found in models/embeddings — no hash: by it Civitai recognises the embedding",
    willHash: "Hash of {v} will be calculated on the first save", hashed: "Hash of {v} calculated for the first time ({size} MB, {sec} s) and cached",
    noSampler: "No sampler node is connected in the workflow and no values are connected — the file gets no parameters", badPath: "Wrong path: {v}",
    fromFile: "No sampler node is connected in the workflow — the values come from the source file {v}",
    jpegLimit: "JPEG holds up to 64 KB of metadata — a big workflow will not fit",
    civitaiIds: "Civitai IDs: {v} of {n} (with the LoRA weights) — {src}",
    noCivitaiId: "No Civitai ID: {v} — Civitai finds it by the hash, a LoRA without its weight. Settings → Rigstools → Civitai looks the IDs up by the hash",
    noCivitaiIdOnline: "Not on Civitai or no answer yet: {v} — found by the hash, a LoRA without its weight",
    src_cache: "cache", "src_.metadata.json": "LoRA Manager", "src_.civitai.info": ".civitai.info", src_civitai: "Civitai",
    dlgTitle: "What goes into the file", dlgParams: "Parameters (A1111)", dlgPreview: "Preview", dlgPending: "“…” — model, LoRA and embedding hashes will be calculated when the image is saved",
    dlgBlocks: "Written into the file",
    b_parameters: "parameters (A1111) — read by A1111, Forge, Civitai and our loaders",
    b_workflow: "workflow (ComfyUI) — dropping the picture onto ComfyUI opens the workflow",
    b_prompt: "prompt (ComfyUI API) — what was run",
    b_workflow_json: "the workflow next to the picture as .json (workflow_json)",
    b_limit: "JPEG: only if it fits into 64 KB", b_dropped: "did not fit into JPEG", b_off: "off",
    why_hashesMissing: "No hash for: {v} — not found in the models folders. By the hashes Civitai recognises the models used.",
    why_noSampler: "No sampler node is connected in the workflow and no values are connected — the files get no parameters.",
    ln_saved: "Saved: {v}", ln_next: "Will be saved as: {v}", ln_params: "{v} values from the graph", ln_hashes: "Hashes: {v}",
  },
  ru: {
    head: "Что будет записано", saved: "Сохранено", next: "Будет сохранён как", file: "сохранён как",
    pref: "Приоритет", prefFile: "Файл", prefGraph: "Граф", prefInput: "Вход",
    prefTipInput: "Главный — подключённый вход; без него — граф, затем исходный файл",
    prefTipGraph: "Главные — значения из графа; затем подключённый вход, затем исходный файл",
    prefTipFile: "Главные — данные генерации исходной картинки; затем подключённый вход, затем граф. Размер из файла "
      + "не берётся",
    lgGraph: "из графа", lgInput: "из входа", lgFile: "из исходного файла", lgMissing: "не найдено",
    lgPrev: "LoRA предыдущего прохода", lgPrompt: "LoRA из промпта", lgLoraMissing: "LoRA не найдена", lgLoraFound: "LoRA найдена",
    dlgNotePreview: "Что запишет следующий запуск — так нода видит граф сейчас. Часть значений становится известна "
      + "только при запуске (промпт, собранный из нескольких нод, размер увеличенной картинки) — фактически "
      + "записанное смотрите в консоли ComfyUI при включённой настройке Rigstools → Debug.",
    dlgNoteSaved: "Последнее сохранение: эти значения вычислены при выполнении воркфлоу и записаны в файл. "
      + "Подробности — в консоли ComfyUI при включённой настройке Rigstools → Debug.",
    help: "🛟 Справка по ноде", helpTitle: "Save image — имя файла и папка",
    helpIntro: "Переменные работают в filename и в path. path — подпапка внутри папки output ComfyUI "
      + "(путь за её пределы не принимается); / в path создаёт вложенные папки.",
    helpVars: "Переменные",
    helpCols: "Переменная|Описание|Пример", helpDateCols: "Код|Значение|Пример", helpExCols: "Шаблон|Результат",
    helpRows: "%date|дата сохранения|2026-11-08\n%date<формат>|дата и время в заданном формате, коды ниже|%date<%Y%m%d> → 20261108\n"
      + "%time|время сохранения|143205\n%model|имя файла модели без папки и расширения|ilustmix_v111\n"
      + "%seed|seed|845041538454657\n%steps|шаги|25\n%cfg|CFG|6.5\n%sampler|сэмплер|dpmpp_2m\n%scheduler|планировщик|karras\n"
      + "%width, %height|размер сохраняемой картинки|2256, 3376\n"
      + "%counter|следующий свободный номер в папке|1, 2, 3…\n%counter<N>|то же, N цифр с ведущими нулями|%counter<4> → 0001",
    helpDate: "Коды для %date<…>",
    helpDateRows: "%Y|год|2026\n%y|год, две цифры|26\n%m|месяц|11\n%d|день|08\n%H|часы (24 ч)|14\n%M|минуты|32\n"
      + "%S|секунды|05\n%b|месяц, кратко (язык системы)|Nov\n%B|месяц полностью (язык системы)|November\n"
      + "%a|день недели, кратко|Sun\n%A|день недели полностью|Sunday",
    helpRules: "Правила",
    helpRuleList: "Если значение не найдено, подставляется unknown.\n"
      + "Значения, известные только при выполнении, в имени на ноде показаны в [ ].\n"
      + "Существующий файл не перезаписывается: без %counter к имени добавляется _2, _3…\n"
      + "Символы < > : \" | ? * удаляются; / в filename заменяется на _.",
    helpExamples: "Примеры",
    helpExampleRows: "%date_%model_%seed_%counter<4>|2026-11-08_ilustmix_v111_845041538454657_0001.png\n"
      + "path: txt2img/%date|output/txt2img/2026-11-08/\npath: %model/%date<%Y-%m>|output/ilustmix_v111/2026-11/\n"
      + "STEP_1_%date<%Y-%m-%d-%H'%M'%S>_%model_%seed|STEP_1_2026-11-08-14'32'05_ilustmix_v111_845041538454657.png",
    loraPrompt: "из тега <lora:…> в промпте", loraFilePrompt: "предыдущий проход: из тега <lora:…> в промпте исходного файла",
    loraStack: "предыдущий проход: из Lora stack исходного файла",
    noLora: "LoRA нет", size: "размер", waiting: "Смотрю граф…",
    sec: "файлов: {n} · {s} с", ph: "Значения в [ ] определяются при выполнении", atRun: "при выполнении",
    dlgWarn: "Предупреждения и замечания", dlgDone: "Сохранение",
    paramsOk: "Параметры A1111 записаны: проходов {v}, LoRA {loras}", workflowIn: "Workflow встроен в файл",
    workflowOff: "Workflow не встроен (metadata: parameters only)", metaNone: "Метаданные не записаны (metadata: none)",
    workflowBig: "Workflow ({v} КБ) не влезает в метаданные JPEG (64 КБ) — не встроен",
    workflowHint: "Включите workflow_json, чтобы сохранять workflow рядом с картинкой",
    workflowFile: "Workflow сохранён рядом: {v}", promptBig: "API-промпт не влезает в JPEG — встроен только workflow",
    paramsBig: "Даже параметры не влезают в JPEG — в файле нет метаданных",
    modelHash: "Хэш модели: {v} · {h}", modelMissing: "Модель {v} не найдена в папках моделей — без хэша: по нему Civitai узнаёт модель",
    loraMissing: "LoRA {v} не найдена в models/loras — без хэша: по нему Civitai узнаёт LoRA",
    embeddingMissing: "Embedding {v} не найден в models/embeddings — без хэша: по нему Civitai узнаёт embedding",
    willHash: "Хэш {v} будет посчитан при первом сохранении", hashed: "Хэш {v} посчитан впервые ({size} МБ, {sec} с) и сохранён в кэш",
    noSampler: "В воркфлоу нет подключённой ноды сэмплера и не подключены значения — параметров в файле не будет", badPath: "Неверный путь: {v}",
    fromFile: "В воркфлоу нет подключённой ноды сэмплера — значения взяты из исходного файла {v}",
    jpegLimit: "В JPEG помещается до 64 КБ метаданных — большой workflow не влезет",
    civitaiIds: "ID Civitai: {v} из {n} (с весами LoRA) — {src}",
    noCivitaiId: "Нет ID Civitai: {v} — Civitai найдёт по хэшу, LoRA без веса. Искать ID по хэшу: Настройки → Rigstools → Civitai",
    noCivitaiIdOnline: "Нет на Civitai или ещё нет ответа: {v} — найдётся по хэшу, LoRA без веса",
    src_cache: "кэш", "src_.metadata.json": "LoRA Manager", "src_.civitai.info": ".civitai.info", src_civitai: "Civitai",
    dlgTitle: "Что записывается в файл", dlgParams: "Параметры (A1111)", dlgPreview: "Предпросмотр", dlgPending: "“…” — хэши моделей, LoRA и embedding будут вычислены во время сохранения изображения",
    dlgBlocks: "Записывается в файл",
    b_parameters: "parameters (A1111) — их читают A1111, Forge, Civitai и наши загрузчики",
    b_workflow: "workflow (ComfyUI) — картинка, брошенная в ComfyUI, открывает workflow",
    b_prompt: "prompt (API ComfyUI) — что было запущено",
    b_workflow_json: "workflow рядом с картинкой файлом .json (workflow_json)",
    b_limit: "JPEG: только если влезет в 64 КБ", b_dropped: "не влез в JPEG", b_off: "выключено",
    why_hashesMissing: "Нет хэша у: {v} — не найдены в папках моделей. По хэшам Civitai узнаёт, какие модели использованы.",
    why_noSampler: "В воркфлоу нет подключённой ноды сэмплера и не подключены значения — параметров в файлах нет.",
    ln_saved: "Сохранено: {v}", ln_next: "Будет сохранён как: {v}", ln_params: "Значений из графа: {v}", ln_hashes: "Хэши: {v}",
  },
};
const st_ = (k, vars) => {
  const loc = String(app.extensionManager?.setting?.get?.("Comfy.Locale") ?? "en").toLowerCase();
  let s = SAVE_STR[loc.startsWith("ru") ? "ru" : "en"][k] ?? SAVE_STR.en[k] ?? k;
  for (const [a, b] of Object.entries(vars ?? {})) s = s.split(`{${a}}`).join(b ?? "");
  return s;
};
for (const lang of ["en", "ru"]) {   // reasons of the ✕ on the outputs, shown by the shared tooltip code
  STR[lang].why_hashesMissing = SAVE_STR[lang].why_hashesMissing;
  STR[lang].why_noSampler = SAVE_STR[lang].why_noSampler;
}


let saveCss = false;
function addSaveCss() {
  if (saveCss) return;
  saveCss = true;
  const s = document.createElement("style");
  s.textContent = `
  .rig-save{font:12px Arial,sans-serif;color:var(--input-text,#ddd);box-sizing:border-box;padding:0 2px 4px;
    display:flex;flex-direction:column;gap:6px;height:auto}
  .rig-save .rs-box{background:var(--comfy-input-bg,#222);border-radius:8px;padding:6px 8px;box-sizing:border-box}
  .rig-save .rs-head{display:flex;justify-content:space-between;color:#8a8a8a;font-size:10.5px;text-transform:uppercase;
    letter-spacing:.04em;margin-bottom:5px;gap:8px}
  .rig-save .rs-head span:last-child{text-transform:none;letter-spacing:0;white-space:nowrap}
  .rig-save .rig-f{cursor:default}
  .rig-save .rig-f > label,.rig-save .rig-t > label{pointer-events:auto}
  .rig-save .rs-top{display:flex;align-items:center;gap:8px;margin:0 3px 5px}
  .rig-save .rs-top .rig-card-head{margin:0;flex:1 1 auto;min-width:0}
  .rig-save .rs-pref{display:flex;align-items:center;gap:6px;flex:0 0 auto;color:var(--rig-label);font:var(--rig-label-font);font-size:10.5px}
  .rig-save .rs-seg{display:inline-flex;border:1px solid var(--rig-outline);border-radius:8px;overflow:hidden;background:var(--rig-field)}
  .rig-save .rs-seg button{all:unset;cursor:pointer;display:inline-flex;align-items:center;padding:0 7px;line-height:17px;
    color:var(--rig-label);font:var(--rig-label-font);font-size:10.5px;pointer-events:auto}
  .rig-save .rs-seg button + button{border-left:1px solid var(--rig-outline)}
  .rig-save .rs-seg button .rig-dot{margin-right:4px}
  .rig-save .rs-seg button:hover{color:var(--input-text,#ddd)}
  .rig-save .rs-seg button.on{color:var(--input-text,#eee)}
  .rig-save .rs-seg button.on.file{background:#81c78433}.rig-save .rs-seg button.on.graph{background:#8a8a8a40}
  .rig-save .rs-seg button.on.input{background:#4fc3ff33}
  .rig-save .rs-next > label{flex:0 0 auto;min-width:0}
  .rig-save .rs-next > .rig-v{flex:1 1 auto;text-align:right}
  .rig-save .rs-next i{font-style:normal;color:#9ab}
  .rig-save .rs-ph{color:#888;font-size:10px;margin:0 0 2px}
  .rig-save .rs-msg{line-height:15px}
  .rig-save .rs-msg.ok{color:#81c784}.rig-save .rs-msg.warn{color:#ffb74d}.rig-save .rs-msg.info{color:#9ab}
  .rig-save .rs-msg.muted{color:#888}
`;
  document.head.appendChild(s);
}

const MARK = { ok: "✓", warn: "⚠", info: "ⓘ", muted: "·" };
// messages of the preview / the last save: warnings, notes (what the user may want to know), the rest is how it went
const NOTE_CODES = new Set(["noCivitaiId", "noCivitaiIdOnline"]);
function sortStatus(list) {
  const warn = list.filter((s) => s.kind === "warn");
  const notes = list.filter((s) => s.kind === "info" || (s.kind === "muted" && NOTE_CODES.has(s.code)));
  const done = list.filter((s) => !warn.includes(s) && !notes.includes(s));
  return { warn, notes, done };
}
function statusText(s) {
  const src = s.src ? Object.entries(s.src).map(([k, n]) => `${st_("src_" + k)}: ${n}`).join(", ") : "";
  return st_(s.code, { v: s.v, h: s.h, n: s.n, loras: s.loras, size: s.size, sec: s.sec, src });
}

// CFG is shown with at least one decimal (7.0, 6.5), as A1111 writes it
const fmtCfg = (v) => (v === "" || v == null || isNaN(v) || !Number.isInteger(+v) ? v : (+v).toFixed(1));

function fmtValue(k, v) {
  if (v == null || v === "") return "—";
  if (k === "cfg" && typeof v === "number") return fmtCfg(v);
  if (k === "model") return String(v).replace(/\\/g, "/").split("/").pop().replace(/\.(safetensors|ckpt|pt|pth|sft|gguf)$/i, "");
  if (typeof v === "number" && !Number.isInteger(v)) return String(+v.toFixed(4));
  return String(v);
}

function savePanel(node) {
  addPanelCss(); addSaveCss();
  const root = el("div"); root.className = "rig-panel rig-save";
  wheelLikeStock(root);
  const fieldsBox = el("div"); fieldsBox.className = "rig-card";
  const statusBox = el("div"); statusBox.className = "rig-card rs-file";
  root.append(fieldsBox, statusBox);

  // the same fields as in "Load image with parameters", read-only; the dot tells where a value comes from
  const label = (src, text) => { const l = el("label"); l.append(dot(src), document.createTextNode(text)); return l; };
  function pill(label_, src, value, tailCut = false) {
    const f = el("div"); f.className = "rig-f" + (src === "missing" ? " miss" : "");
    // tailCut: a long value is cut at the start ("…" first), so the end (the model file name) stays visible
    const v = el("span", null, tailCut ? null : value); v.className = "rig-v" + (tailCut ? " tail" : ""); v.title = value;
    if (tailCut) v.appendChild(el("bdi", null, value));
    f.append(label(src, label_), v);
    return f;
  }
  function area(label_, src, value, lines) {
    const f = el("div"); f.className = "rig-t" + (src === "missing" ? " miss" : "");
    const v = el("div", `-webkit-line-clamp:${lines}`, value); v.className = "rig-v"; v.title = value;
    f.append(label(src, label_), v);
    return f;
  }
  const row = (cols, ...items) => { const r = el("div"); r.className = "rig-row"; r.style.gridTemplateColumns = cols; r.append(...items); return r; };

  // Preference: which source wins — a three-way switch over the hidden "preference" widget
  const prefWidget = () => node.widgets?.find((w) => w.name === "preference");
  function prefSwitch() {
    const box = el("div"); box.className = "rs-pref";
    box.appendChild(el("span", null, st_("pref")));
    const seg = el("div"); seg.className = "rs-seg";
    const cur = prefWidget()?.value ?? "input";
    for (const [v, src, txt, tip] of [["file", "file", "prefFile", "prefTipFile"], ["graph", "graph", "prefGraph", "prefTipGraph"],
      ["input", "input", "prefInput", "prefTipInput"]]) {
      const b = el("button"); b.type = "button"; b.className = (v === cur ? "on " : "") + src; b.title = st_(tip);
      b.append(dot(src), document.createTextNode(st_(txt)));
      b.addEventListener("pointerdown", (e) => e.stopPropagation());
      b.addEventListener("click", (e) => {
        e.stopPropagation();
        const w = prefWidget();
        if (!w || w.value === v) return;
        w.value = v; w.callback?.(v);
        node.setDirtyCanvas?.(true, true);
        app.graph?.change?.();
        render();
        refreshSavePreviews(true);
      });
      seg.appendChild(b);
    }
    box.appendChild(seg);
    return box;
  }

  function render() {
    const d = node._rigPreview, saved = node._rigSaved;
    fieldsBox.replaceChildren(); statusBox.replaceChildren();
    const top = el("div"); top.className = "rs-top";
    const head = el("div", null, st_("head")); head.className = "rig-card-head";
    top.append(head, prefSwitch());
    fieldsBox.appendChild(top);
    if (!d || d.error) {
      fieldsBox.appendChild(el("div", "color:#888", d?.error ? d.error : st_("waiting")));
    } else {
      const F = d.fields ?? {};
      const late = (k) => F[k]?.src === "input" && (F[k]?.v == null || F[k]?.v === "");   // connected, known when it runs
      const val = (k) => (late(k) ? `[${st_("atRun")}]` : fmtValue(k, F[k]?.v));
      const src = (k) => (late(k) ? "input" : F[k]?.v == null || F[k]?.v === "" ? "missing" : F[k]?.src ?? "missing");
      const box = el("div"); box.className = "rig-fields";
      const sz = F.width?.v && F.height?.v ? `${F.width.v}×${F.height.v}` : "—";
      box.append(
        area("positive", src("positive"), val("positive"), 2),
        area("negative", src("negative"), val("negative"), 2),
        row("repeat(4, auto)", pill("seed", src("seed"), val("seed")), pill("steps", src("steps"), val("steps")),
          pill("cfg", src("cfg"), val("cfg")), pill("clip", src("clip_skip"), val("clip_skip"))),
        row("repeat(3, auto)", pill("sampler", src("sampler"), val("sampler")), pill("scheduler", src("scheduler"), val("scheduler")),
          pill("denoise", src("denoise"), val("denoise"))),
        row("1fr auto", pill("model", src("model"), val("model"), true), pill(st_("size"), sz === "—" ? "missing" : F.width.src, sz)),
      );
      const loras = d.loras ?? [];
      const lost = new Set((d.status ?? []).filter((s) => s.code === "loraMissing").map((s) => s.v));
      const lb = el("div"); lb.className = "rig-loras";
      lb.appendChild(label(!loras.length ? "missing" : ["input", "file"].includes(d.lora_src) ? d.lora_src : "graph", "lora"));
      if (!loras.length) { const n = el("span", null, st_("noLora")); n.className = "rig-none"; lb.appendChild(n); }
      for (const l of loras) {
        const chip = el("span"); chip.className = "rig-chip" + (lost.has(l.name) ? " bad" : "") + (l.from === "prompt" ? " tag" : l.from ? " prev" : "");
        chip.append(l.name, el("b", null, `×${fmtValue("w", l.weight)}`));
        chip.title = `${l.name} ${l.weight}` + (l.from ? ` — ${st_({ stack: "loraStack", file_prompt: "loraFilePrompt" }[l.from] ?? "loraPrompt")}` : "");
        lb.appendChild(chip);
      }
      box.appendChild(lb);
      fieldsBox.appendChild(box);

      fieldsBox.appendChild(legend([["graph", st_("lgGraph")], ["input", st_("lgInput")], ["file", st_("lgFile")],
        ["missing", st_("lgMissing")]]));
      // dashed chip: LoRA of an earlier pass (the loaded picture); dotted chip: a <lora:…> tag in this prompt
      // the LoRA chip kinds, always listed
      loraLegend(fieldsBox.lastChild, [["rig-prev ok", st_("lgLoraFound"), true], ["rig-prev", st_("lgPrev"), true],
        ["rig-prev tag", st_("lgPrompt"), true], ["rig-prev bad", st_("lgLoraMissing"), true]]);
    }

    // the name of the next file, as a field like the ones above (values in [ ] become known when it runs)
    if (d && !d.error && d.next) {
      const f = el("div"); f.className = "rig-f rs-next";
      const v = el("span"); v.className = "rig-v"; v.title = d.path ?? d.next;
      for (const part of d.next.split(/(\[[^\]]*\])/)) if (part) v.append(part.startsWith("[") ? el("i", null, part) : document.createTextNode(part));
      const l = el("label", null, st_("next"));
      f.append(l, v);
      statusBox.appendChild(f);
      const ph = el("div", null, st_("ph")); ph.className = "rig-leg"; statusBox.appendChild(ph);   // always, as the legend
    }
    statusBox.style.display = statusBox.childNodes.length ? "" : "none";
    requestAnimationFrame(fit);
  }

  // the node is as tall as the panel needs (+ room for the saved pictures when they are shown)
  const content = () => fieldsBox.offsetHeight + (statusBox.style.display === "none" ? 0 : statusBox.offsetHeight + 6) + 6;
  function fit() {
    const top = widget?.y ?? widget?.last_y;
    if (top == null || !fieldsBox.offsetHeight) return;
    const pics = node.imgs?.length || app.nodeOutputs?.[node.id]?.images?.length ? 300 : 0;
    const need = Math.ceil(top + content() + 10 + pics);
    if (need > node.size[1] + 2) node.setSize?.([node.size[0], need]);   // grow only: a height set by hand stays
    node.setDirtyCanvas?.(true, true);
  }

  let widget = null;
  widget = node.addDOMWidget("rig_save_panel", "RIGSTOOLS_SAVE_PANEL", root, {
    serialize: false, hideOnZoom: true,
    getMinHeight: () => (fieldsBox.offsetHeight ? content() : 300),
    getMaxHeight: () => (fieldsBox.offsetHeight ? content() : 300),
  });
  widget.serialize = false;
  node._rigSavePanel = { render, fit };
  render();
  return widget;
}

// one request at a time for all save nodes; only when the graph changed
let saveBusy = false, saveSig = "";
function graphSignature(graph) {
  const parts = [];
  for (const n of graph?._nodes ?? []) {
    const w = (n.widgets ?? []).map((x) => (typeof x.value === "string" ? x.value.length + x.value.slice(0, 24) : String(x.value))).join(",");
    parts.push(`${n.id}:${n.mode}:${n.type}:${w}`);
  }
  const links = graph?.links;
  const ids = links ? [...(links.values?.() ?? Object.values(links))].map((l) => l && `${l.origin_id}.${l.origin_slot}>${l.target_id}.${l.target_slot}`) : [];
  return parts.join("|") + "#" + ids.join(",");
}

async function refreshSavePreviews(force) {
  if (saveBusy) return;
  const graph = app.graph;
  const nodes = (graph?._nodes ?? []).filter((n) => n.type === SAVE);
  if (!nodes.length) return;
  const sig = graphSignature(graph);
  if (!force && sig === saveSig) return;
  saveBusy = true;
  try {
    const p = await app.graphToPrompt();
    saveSig = sig;
    for (const n of nodes) {
      const r = await api.fetchApi("/rigstools/save_preview", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: p.output, node: String(n.id) }) });
      const j = await r.json();
      n._rigPreview = j;
      n._rigPredicted = j.error ? null : j.state;
      n._rigSavePanel?.render();
    }
  } catch (e) { console.debug("[Rigstools] save preview", e); }
  finally { saveBusy = false; }
}
setInterval(() => { if (!document.hidden) refreshSavePreviews(false); }, 1500);

function saveInfoButton(node) {
  if (!node.addTitleButton) return;
  const b = node.addTitleButton({ name: "rig_save_info", text: "i", fontSize: 14, xOffset: -4, yOffset: 0 });
  b.getWidth = function () { return 18; };
  b.draw = function (ctx, x) {
    const s = 16, cx = x + this.xOffset + s / 2, cy = -(globalThis.LiteGraph?.NODE_TITLE_HEIGHT ?? 30) / 2;
    this._last_area[0] = cx - s / 2; this._last_area[1] = cy - s / 2; this._last_area[2] = s; this._last_area[3] = s;
    const warn = (node._rigSaved?.status ?? node._rigPreview?.status ?? []).some((x) => x.kind === "warn");
    const c = warn ? WARN : ON;
    ctx.save();
    ctx.beginPath(); ctx.arc(cx, cy, 7, 0, Math.PI * 2);
    ctx.fillStyle = c + "26"; ctx.fill(); ctx.lineWidth = 1.2; ctx.strokeStyle = c; ctx.stroke();
    ctx.fillStyle = c; ctx.font = "bold 10px Georgia, 'Times New Roman', serif";
    ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText("i", cx, cy + 0.5);
    ctx.restore();
  };
}

function openSaveDialog(node) {
  const d = node._rigPreview, saved = node._rigSaved;
  const text = saved?.text || d?.text || "";
  document.getElementById("rigstools-info")?.remove();
  const back = el("div", "position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:10000;display:flex;align-items:center;justify-content:center");
  back.id = "rigstools-info";
  const box = el("div", "width:min(720px,92vw);max-height:84vh;display:flex;flex-direction:column;background:var(--comfy-menu-bg,#2b2b2b);"
    + "color:var(--fg-color,#ddd);border:1px solid var(--border-color,#444);border-radius:10px;box-shadow:0 10px 40px rgba(0,0,0,.6);font:13px Arial,sans-serif");
  back.appendChild(box);
  const close = () => { back.remove(); document.removeEventListener("keydown", onKey, true); };
  const onKey = (e) => { if (e.key === "Escape") { e.stopPropagation(); close(); } };
  document.addEventListener("keydown", onKey, true);
  back.addEventListener("pointerdown", (e) => { if (e.target === back) close(); });
  const head = el("div", "display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--border-color,#3a3a3a)");
  head.appendChild(el("b", "font-size:14px;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap",
    saved ? saved.files.at(-1) : st_("dlgTitle")));
  const x = el("span", CLOSE_X, "✕"); x.title = t("close"); x.onclick = close; head.appendChild(x);
  box.appendChild(head);
  const body = el("div", "padding:10px 16px;overflow:auto;flex:1;min-height:0");
  // before the run this is what the node expects; after it, what was written
  body.appendChild(el("div", "color:#9ab;margin-bottom:10px;padding:6px 10px;border-left:3px solid #4fc3ff66;"
    + "background:rgba(79,195,255,.06);border-radius:4px", st_(saved ? "dlgNoteSaved" : "dlgNotePreview")));
  const blocks = saved?.blocks ?? d?.blocks ?? [];
  if (blocks.length) {
    body.appendChild(el("div", "color:#aaa;font-size:11px;text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px", st_("dlgBlocks")));
    const list = el("div", "margin-bottom:12px;line-height:19px");
    for (const blk of blocks) {
      const note = blk.dropped ? st_("b_dropped") : !blk.on ? st_("b_off") : blk.limit ? st_("b_limit") : "";
      const row = el("div", `color:${blk.dropped ? "#ffb74d" : blk.on ? "#ddd" : "#777"}`, `${blk.on ? "✓" : blk.dropped ? "⚠" : "—"} ${st_("b_" + blk.key)}`);
      if (note) row.appendChild(el("span", "color:#888", ` · ${note}`));
      list.appendChild(row);
    }
    body.appendChild(list);
  }
  const list = saved?.status ?? d?.status ?? [];
  const section = (title, items) => {
    if (!items.length) return;
    body.appendChild(el("div", "color:#aaa;font-size:11px;text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px", title));
    const box = el("div", "margin-bottom:12px;line-height:18px");
    for (const s of items) box.appendChild(el("div", `color:${{ warn: "#ffb74d", info: "#9ab", ok: "#81c784" }[s.kind] ?? "#888"}`,
      `${MARK[s.kind] ?? "·"} ${statusText(s)}`));
    body.appendChild(box);
  };
  const sorted = sortStatus(list);
  section(st_("dlgWarn"), [...sorted.warn, ...sorted.notes]);
  if (saved) section(st_("dlgDone"), sorted.done);
  body.appendChild(el("div", "color:#aaa;font-size:11px;text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px", st_("dlgParams")));
  if (!saved) body.appendChild(el("div", "color:#888;margin-bottom:4px", st_("dlgPreview")));
  const pending = !saved && !!d?.pending_hashes;
  const pre = el("pre", `margin:0 0 ${pending ? 4 : 12}px;padding:10px;`
    + "background:var(--comfy-input-bg,#1f1f1f);border-radius:6px;white-space:pre-wrap;max-height:38vh;overflow:auto;"
    + "word-break:break-word;font:12px Consolas,'Courier New',monospace;color:var(--input-text,#cfcfcf)", text || "—");
  body.appendChild(pre);
  if (pending) body.appendChild(el("div", "color:#888;margin-bottom:12px", st_("dlgPending")));
  box.appendChild(body);
  const actions = el("div", "display:flex;gap:8px;justify-content:flex-end;padding:0 16px 14px");
  actions.appendChild(button(t("copyParams"), (b) => copy(text, b), !text));
  actions.appendChild(button(t("close"), close));
  box.appendChild(actions);
  document.body.appendChild(back);
  // a bigger window gives the parameters text the extra height
  const h0 = resizable(box);
  new ResizeObserver(() => { pre.style.maxHeight = `calc(38vh + ${Math.max(0, box.offsetHeight - h0)}px)`; }).observe(box);
}

// -------------------------------------------------- Help of Save image (node context menu)

// A help window in our style: title, then fill(api) adds the sections. api.table takes "a|b|c" lines; in a 3-column
// table the first and the last column are code (names, examples), in a 2-column one the first is, unless plain2
function openHelp(title, fill) {
  document.getElementById("rigstools-info")?.remove();
  const back = el("div", "position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:10000;display:flex;align-items:center;justify-content:center");
  back.id = "rigstools-info";
  const box = el("div", "width:min(760px,92vw);max-height:84vh;display:flex;flex-direction:column;background:var(--comfy-menu-bg,#2b2b2b);"
    + "color:var(--fg-color,#ddd);border:1px solid var(--border-color,#444);border-radius:10px;box-shadow:0 10px 40px rgba(0,0,0,.6);font:13px Arial,sans-serif");
  back.appendChild(box);
  const close = () => { back.remove(); document.removeEventListener("keydown", onKey, true); };
  const onKey = (e) => { if (e.key === "Escape") { e.stopPropagation(); close(); } };
  document.addEventListener("keydown", onKey, true);
  back.addEventListener("pointerdown", (e) => { if (e.target === back) close(); });
  const head = el("div", "display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--border-color,#3a3a3a)");
  head.appendChild(el("b", "font-size:14px;flex:1", "🛟 " + title));
  const x = el("span", CLOSE_X, "✕"); x.title = t("close"); x.onclick = close; head.appendChild(x);
  box.appendChild(head);
  const body = el("div", "padding:10px 16px;overflow:auto;flex:1;min-height:0;line-height:18px");
  const code = "font:12px Consolas,'Courier New',monospace;color:#cfe8ff;white-space:nowrap";
  fill({
    text: (s) => body.appendChild(el("div", "color:#bbb", s)),
    heading: (s) => body.appendChild(el("div", "color:#aaa;font-size:11px;text-transform:uppercase;letter-spacing:.04em;margin:12px 0 4px", s)),
    bullets: (s) => { for (const r of s.split("\n")) body.appendChild(el("div", "color:#ccc;margin:2px 0", "• " + r)); },
    table: (cols, lines, plain2 = false) => {
      cols = cols.split("|");
      const n = cols.length, rows = lines.split("\n").map((r) => r.split("|"));
      const tb = el("div", `display:grid;grid-template-columns:${n === 3 ? "auto 1fr auto" : "auto 1fr"};`
        + "border:1px solid var(--border-color,#3a3a3a);border-radius:6px;overflow:hidden");
      for (const c of cols) tb.append(el("div", "padding:5px 10px;background:rgba(255,255,255,.05);color:#aaa;font-size:11px;"
        + "text-transform:uppercase;letter-spacing:.04em", c));
      rows.forEach((r, i) => r.forEach((v, j) => tb.append(el("div", "padding:4px 10px;border-top:1px solid var(--border-color,#333);"
        + (i % 2 ? "background:rgba(255,255,255,.02);" : "")
        + (j === 0 || (n === 3 && j === 2) || (n === 2 && j === 1 && !plain2) ? code : "color:#ccc"), v))));
      body.appendChild(tb);
    },
  });
  box.appendChild(body);
  const actions = el("div", "display:flex;gap:8px;justify-content:flex-end;padding:8px 16px 14px");
  actions.appendChild(button(t("close"), close));
  box.appendChild(actions);
  document.body.appendChild(back);
  resizable(box);
}

function openSaveHelp() {
  openHelp(st_("helpTitle"), (h) => {
    h.text(st_("helpIntro"));
    h.heading(st_("helpVars")); h.table(st_("helpCols"), st_("helpRows"));
    h.heading(st_("helpDate")); h.table(st_("helpDateCols"), st_("helpDateRows"));
    h.heading(st_("helpRules")); h.bullets(st_("helpRuleList"));
    h.heading(st_("helpExamples")); h.table(st_("helpExCols"), st_("helpExampleRows"));
  });
}

function openColorHelp() {
  openHelp(t("ccTitle"), (h) => {
    h.text(t("ccIntro"));
    h.heading(t("ccAuto")); h.table(t("ccCols"), t("ccAutoRows"), true);
    h.heading(t("ccManual")); h.table(t("ccCols"), t("ccManualRows"), true);
    h.heading(t("ccOther")); h.table(t("ccCols"), t("ccOtherRows"), true);
  });
}

function saveValueLine(node, name) {
  const saved = node._rigSaved, d = node._rigPreview;
  if (name === "FILEPATH") {
    if (saved?.files?.length) return st_("ln_saved", { v: saved.paths?.at(-1) ?? (saved.subfolder ? saved.subfolder + "/" : "") + saved.files.at(-1) });
    return d?.next ? st_("ln_next", { v: d.path || d.next }) : null;
  }
  if (name === "PARAMETERS" && d?.fields) {
    const n = Object.values(d.fields).filter((f) => f.src !== "missing").length;
    return st_("ln_params", { v: n });
  }
  return null;
}

app.registerExtension({
  name: "Rigstools.NodeIcon",
  settings: [
    { id: "Rigstools.Civitai.Lookup", category: ["Rigstools", "Civitai", "Lookup"],
      name: "Look models up on Civitai by their hash (Save image)",
      tooltip: "For the \"Civitai resources\" block, where Civitai takes the LoRA weights from. Sends the SHA-256 of the "
        + "model, LoRA and embedding files to civitai.com (no API key) — Civitai learns which models you use. The "
        + "answers are kept in <ComfyUI user folder>/rigstools/civitai.json. Off: only that cache and the files next "
        + "to the models (LoRA Manager .metadata.json, .civitai.info of Image Saver / Civitai Helper) are used.",
      type: "boolean", defaultValue: false },
    { id: "Rigstools.Debug.Log", category: ["Rigstools", "Debug", "Log"],
      name: "Debug: write details of the nodes' work to the console",
      tooltip: "Into the ComfyUI console (log). Save image, on each save: the files, the passes (samplers) in the order "
        + "they run, where the Hires fields come from, every value with its source, the LoRA and the warnings. "
        + "Load image with parameters, Parameters extractor, Metadata extractor: what was read from the file, which "
        + "values are defaults or typed, whether the model was found. Color correction: what the automatic steps "
        + "measured and changed. Loading a picture into the panel step by step goes to the browser console (F12).",
      type: "boolean", defaultValue: false },
  ],
  getCustomWidgets() {
    return { RIGSTOOLS_PARAMS: (node, inputName) => ({ widget: paramsPanel(node, inputName) }) };
  },
  beforeRegisterNodeDef(nodeType, nodeData) {
    if (!NODE_TYPES.has(nodeData?.name)) return;
    // A node saved in a workflow keeps the outputs it had then. Outputs we have since removed (MISSING, REPORT) are
    // dropped and changed output types (MODEL_NAME → *) are updated when the workflow loads; the other links stay.
    if (nodeData.name === "Color correction [Rigstools]") {
      // the settings of the reference are off while no reference picture is connected
      const syncRef = (node) => {
        const i = node.inputs?.findIndex((x) => x.name === "reference") ?? -1;
        const on = i >= 0 && node.inputs[i].link != null;
        for (const w of node.widgets ?? []) if (w.name === "reference_strength") w.disabled = !on;
        node.setDirtyCanvas?.(true, true);
      };
      const created0 = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function () { const r = created0?.apply(this, arguments); syncRef(this); return r; };
      const conf0 = nodeType.prototype.onConfigure;
      nodeType.prototype.onConfigure = function () { const r = conf0?.apply(this, arguments); syncRef(this); return r; };
      const conn0 = nodeType.prototype.onConnectionsChange;
      nodeType.prototype.onConnectionsChange = function () { const r = conn0?.apply(this, arguments); syncRef(this); return r; };
    }
    if (nodeData.name === "Color correction [Rigstools]") {   // "🛟 Node Help": what every setting does
      const menu0 = nodeType.prototype.getExtraMenuOptions;
      nodeType.prototype.getExtraMenuOptions = function (canvas, options) {
        const r = menu0?.apply(this, arguments);
        const at = options.findIndex((o) => o?.content === "Properties Panel");
        const item = { content: st_("help"), callback: () => openColorHelp() };
        if (at >= 0) options.splice(at, 0, item); else options.push(null, item);
        return r;
      };
    }
    const configure0 = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      const r = configure0?.apply(this, arguments);
      const names = nodeData.output_name ?? [], types = nodeData.output ?? [];
      for (let i = (this.outputs?.length ?? 0) - 1; i >= 0; i--) {
        const j = names.indexOf(this.outputs[i].name);
        if (j < 0) this.removeOutput(i);
        else if (typeof types[j] === "string" && this.outputs[i].type !== types[j]) this.outputs[i].type = types[j];
      }
      return r;
    };
    nodeType.prototype.onDrawTitleText = function (ctx, titleHeight, size, scale, font, selected) {
      try { drawTitle(this, ctx, titleHeight, size, scale, font, selected); }
      catch (e) { console.warn("[Rigstools] title", e); }
    };

    if (nodeData.name === SAVE) {
      patchSlots(nodeType.prototype);
      nodeType.prototype.getStyledOutputTooltip = function (index) {
        try {
          const name = this.outputs?.[index]?.name;
          const res = styledBody(this, name) ?? { lines: [] };
          const v = saveValueLine(this, name);
          if (v && !res.lines.some((l) => l.text === v)) res.lines.push({ kind: "info", text: v });
          res.title = titleOf(this, name);
          return res.lines.length ? res : null;
        } catch { return null; }
      };
      const created1 = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function () {
        const r = created1?.apply(this, arguments);
        try { savePanel(this); saveInfoButton(this); } catch (e) { console.warn("[Rigstools] save panel", e); }
        // the preference widget is set by the switch on the panel
        const pw = this.widgets?.find((w) => w.name === "preference");
        if (pw) { pw.hidden = true; pw.computeSize = () => [0, -4]; }
        this.size = [Math.max(this.size[0], 470), this.size[1]];
        setTimeout(() => refreshSavePreviews(true), 300);
        return r;
      };
      const ex1 = nodeType.prototype.onExecuted;
      nodeType.prototype.onExecuted = function (message) {
        const r = ex1?.apply(this, arguments);
        const s = message?.rig_save?.[0];
        // the node and ⓘ always show what the next run will write (the new file name included); what this run
        // wrote is in the console (Settings → Rigstools → Debug)
        if (s) { this._rigSaved = null; setTimeout(() => refreshSavePreviews(true), 200);
          setTimeout(() => this._rigSavePanel?.fit(), 600); }
        return r;
      };
      const cc1 = nodeType.prototype.onConnectionsChange;
      nodeType.prototype.onConnectionsChange = function () {
        const r = cc1?.apply(this, arguments);
        this._rigSaved = null;   // the last save no longer describes what will be written
        this._rigSavePanel?.render();
        return r;
      };
      const click1 = nodeType.prototype.onTitleButtonClick;
      nodeType.prototype.onTitleButtonClick = function (btn) {
        if (btn?.name === "rig_save_info") { openSaveDialog(this); return; }
        return click1?.apply(this, arguments);
      };
      // "Help" in the node context menu, as rgthree nodes have it: the file name / folder variables
      const menu0 = nodeType.prototype.getExtraMenuOptions;
      nodeType.prototype.getExtraMenuOptions = function (canvas, options) {
        const r = menu0?.apply(this, arguments);
        const at = options.findIndex((o) => o?.content === "Properties Panel");
        const item = { content: st_("help"), callback: () => openSaveHelp() };
        if (at >= 0) options.splice(at, 0, item); else options.push(null, item);
        return r;
      };
      return;
    }
    if (READERS.includes(nodeData.name) || [LOADER, FOLDER, PARAMS].includes(nodeData.name)) {
      nodeType.prototype.getStyledOutputTooltip = function (index) {
        try { return styledLines(this, index); } catch { return null; }
      };
    }
    if (READERS.includes(nodeData.name)) {
      patchSlots(nodeType.prototype);
      const created0 = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function () {
        const r = created0?.apply(this, arguments);
          return r;
      };
      const fg0 = nodeType.prototype.onDrawForeground;
      nodeType.prototype.onDrawForeground = function () {
        const r = fg0?.apply(this, arguments);
        try { this._rigPredicted = predict(this); } catch { this._rigPredicted = null; }
        return r;
      };
      const ex0 = nodeType.prototype.onExecuted;
      nodeType.prototype.onExecuted = function (message) {
        const r = ex0?.apply(this, arguments);
        const st = message?.rig_state?.[0];
        if (st) { this._rigState = st; this.setDirtyCanvas?.(true, false); }
        return r;
      };
      const cc0 = nodeType.prototype.onConnectionsChange;
      nodeType.prototype.onConnectionsChange = function (side) {
        const r = cc0?.apply(this, arguments);
        if (side === (globalThis.LiteGraph?.INPUT ?? 1)) this._rigState = null;   // the last run no longer applies
        return r;
      };
      return;
    }
    if (![LOADER, FOLDER, PARAMS].includes(nodeData.name)) return;
    patchLoader(nodeType.prototype);

    const created = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = created?.apply(this, arguments);
      try { infoButton(this); } catch (e) { console.warn("[Rigstools] info button", e); }
      if (this.type !== PARAMS) {
        // the stock preview is drawn over the full width of the node; inset it like the panel of
        // Load image with parameters, so both loaders look the same
        const add0 = this.addCustomWidget;
        this.addCustomWidget = function (w) {
          if (w?.name === "$$canvas-image-preview" && typeof w.drawWidget === "function" && !w._rigInset) {
            const draw = w.drawWidget;
            w._rigInset = true;
            w.drawWidget = function (ctx, opts) {
              const width = opts?.width ?? this.node?.size?.[0] ?? 0;
              if (width <= 2 * PREVIEW_INSET + 40) return draw.call(this, ctx, opts);
              ctx.save();
              ctx.translate(PREVIEW_INSET, 0);
              try { return draw.call(this, ctx, { ...opts, width: width - 2 * PREVIEW_INSET }); }
              finally { ctx.restore(); }
            };
          }
          return add0.call(this, w);
        };
      }
      if (this.type === PARAMS) {
        const add = this.addCustomWidget;
        this.addCustomWidget = function (w) {   // the panel draws the picture itself
          return w?.name === "$$canvas-image-preview" ? w : add.call(this, w);
        };
        const i = this.widgets?.findIndex((w) => w.name === "values") ?? -1;   // panel after the upload button
        if (i >= 0) this.widgets.push(...this.widgets.splice(i, 1));
        this.size = [Math.max(this.size[0], 470), Math.max(this.size[1], 1080)];
      }
      return r;
    };
    const fg = nodeType.prototype.onDrawForeground;
    nodeType.prototype.onDrawForeground = function () {
      const r = fg?.apply(this, arguments);
      if (this.type === LOADER) watchImage(this);
      else if (this.type === PARAMS) this._rigPanel?.watch();
      return r;
    };
    const executed = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      const r = executed?.apply(this, arguments);
      const info = message?.rig_meta?.[0];
      if (info) setInfo(this, info);
      return r;
    };
    const click = nodeType.prototype.onTitleButtonClick;
    nodeType.prototype.onTitleButtonClick = function (btn, canvas) {
      if (btn?.name === "rig_info") { openDialog(this); return; }
      return click?.apply(this, arguments);
    };
  },
});
