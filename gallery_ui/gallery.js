// PicoTeka, the gallery page of Rigstools. Talks to /rigstools/gallery/api/*; the language follows the ComfyUI setting Comfy.Locale.
const API = "/rigstools/gallery/api";

const STR = {
  en: {
    title: "PicoTeka", search: "Search prompts and file names", size: "Size", rescan: "Rescan",
    folders: "Folders", addFolder: "+ Add folder", addPrompt: "Full path of a folder with pictures:",
    model: "Model", lora: "LoRA", sampler: "Sampler", tag: "Tags", rating: "Rating", date: "Date", clear: "clear",
    andUp: "and up", more: "{n} more", less: "less", tagAll: "all selected", tagAny: "any of them",
    sort_date: "Newest first", sort_date_asc: "Oldest first", sort_name: "Name", sort_rating: "Rating",
    indexed: "Indexed: {n} pictures", scanning: "Scanning {root}", scanDone: "Up to date", scanError: "Scan failed", unreadable: "Unreadable files: {n}", rootMissing: "Folder not found: {root}", github: "Rigstools on GitHub", badFile: "not a picture or a damaged file", shown: "Shown {n} of {total}",
    empty: "No pictures match the filters", nothing: "Select a picture", noParams: "No generation data in the file",
    rebuilt: "Parameters rebuilt from the ComfyUI prompt", missing: "not in the file",
    allFolders: "All folders", foldersTitle: "Gallery folders", pathPh: "Full path, e.g. D:\\AI\\outputs", add: "Add", remove: "Remove",
    builtin: "ComfyUI output folder", notFolder: "There is no such folder", local_only: "Folders can be changed from this computer only", close: "Close", fresh: "New pictures: {n}", copyParams: "Copy parameters",
    copied: "Copied", addFolderH: "Add a folder", addThis: "Add this folder", upFolder: "Up", homeFolder: "Home", outputFolder: "ComfyUI output", inGallery: "in the gallery", noSubfolders: "No subfolders", noAccess: "No access to this folder", insideRoot: "already in the gallery: inside «{v}»", inside_root: "This folder is inside a gallery folder", holds_root: "This folder holds a gallery folder", holdsRoot: "holds the gallery folder «{v}» — remove that one first", foldersTip: "Ctrl + click: show several folders at once", loading: "Loading…", metaFailed: "Could not read the file data", dateFrom: "from", dateTo: "to", copyPrompt: "Copy the prompt", copyFailed: "Could not copy", fileData: "File data", noData: "nothing", fit: "Fit", full: "100%", info: "Parameters",
    keepZoom: "Keep zoom when paging", of: "{i} of {n}", hintFit: "← → paging | wheel — zoom in / out | double click — fit / 100%",
    hintZoom: "drag — move | double click — fit / 100%", gone: "The file is gone",
    rate: "Rating", tags: "Tags", move: "Move", del: "Delete", compare: "Compare", addTag: "+ tag", tagPh: "tag name, Enter",
    toWfImage: "Picture to workflow", toWfParams: "Parameters to workflow", openWf: "Open workflow",
    sentWf: "Sent to ComfyUI", no_comfy: "ComfyUI is not open in any browser tab", no_workflow: "The file has no workflow",
    network_files: "Deleting and moving files from another computer is off (Settings → Rigstools → PicoTeka)",
    no_send2trash: "The send2trash package is missing: pip install send2trash", not_root: "Not a gallery folder",
    delTitle: "Delete pictures", delText: "Move {n} {pics} to the Windows recycle bin? Tags and rating come back if a file is restored within 30 days.",
    deleted: "Moved to the recycle bin: {n}", moveTitle: "Move pictures", moveText: "Move {n} {pics} to:", newFolder: "new subfolder (optional)",
    moved: "Moved: {n}", rateTitle: "Rating of {n} {pics}", tagsTitle: "Tags of {n} {pics}", tagsAdd: "Add", tagsRemove: "Remove from the pictures",
    manage: "manage", tagsManage: "Tags", rename: "Rename", renamePh: "new name", tagDelete: "Delete the tag",
    pics1: "picture", pics2: "pictures", pics5: "pictures", errors: "Not done: {v}",
    cmpTitle: "Comparison", viewTitle: "Viewer", side: "Side by side", slider: "Slider", hideSame: "Hide equal parameters", param: "Parameter",
    cmpHint: "wheel — zoom in / out | drag — move | double click — fit / 100% | zoom and position are shared by both pictures", needTwo: "Select two pictures (Ctrl + click)",
  },
  ru: {
    title: "PicoTeka", search: "Поиск по промптам и именам файлов", size: "Размер", rescan: "Пересканировать",
    folders: "Папки", addFolder: "+ Добавить папку", addPrompt: "Полный путь к папке с картинками:",
    model: "Модель", lora: "LoRA", sampler: "Сэмплер", tag: "Теги", rating: "Рейтинг", date: "Дата", clear: "сбросить",
    andUp: "и выше", more: "ещё {n}", less: "свернуть", tagAll: "все выбранные", tagAny: "любой из них",
    sort_date: "Сначала новые", sort_date_asc: "Сначала старые", sort_name: "По имени", sort_rating: "По рейтингу",
    indexed: "Индекс: {n} {pics}", scanning: "Сканирование: {root}", scanDone: "Индекс актуален", scanError: "Ошибка сканирования", unreadable: "Не прочитано файлов: {n}", rootMissing: "Папка не найдена: {root}", github: "Rigstools на GitHub", badFile: "не картинка или файл повреждён", shown: "Показано {n} из {total}",
    empty: "Нет картинок под эти фильтры", nothing: "Выберите картинку", noParams: "В файле нет данных генерации",
    rebuilt: "Параметры восстановлены из промпта ComfyUI", missing: "нет в файле",
    allFolders: "Все папки", foldersTitle: "Папки галереи", pathPh: "Полный путь, например D:\\AI\\outputs", add: "Добавить", remove: "Убрать",
    builtin: "папка output ComfyUI", notFolder: "Такой папки нет", local_only: "Папки можно менять только с этого компьютера", close: "Закрыть", fresh: "Новых картинок: {n}", copyParams: "Копировать параметры",
    copied: "Скопировано", addFolderH: "Добавить папку", addThis: "Добавить эту папку", upFolder: "Вверх", homeFolder: "Домашняя папка", outputFolder: "output ComfyUI", inGallery: "уже в галерее", noSubfolders: "Подпапок нет", noAccess: "Нет доступа к этой папке", insideRoot: "уже в галерее: внутри «{v}»", inside_root: "Эта папка внутри папки галереи", holds_root: "Эта папка содержит папку галереи", holdsRoot: "содержит папку галереи «{v}» — сначала уберите её", foldersTip: "Ctrl + щелчок — показать сразу несколько папок", loading: "Загрузка…", metaFailed: "Не удалось прочитать данные файла", dateFrom: "с", dateTo: "по", copyPrompt: "Скопировать промпт", copyFailed: "Не удалось скопировать", fileData: "Данные файла", noData: "нет", fit: "Вписать", full: "100%", info: "Параметры",
    keepZoom: "Сохранять масштаб при листании", of: "{i} из {n}", hintFit: "← → листать | колесо — приблизить / отдалить | двойной клик — вписать / 100%",
    hintZoom: "перетаскивание — сдвиг | двойной клик — вписать / 100%", gone: "Файла больше нет",
    rate: "Рейтинг", tags: "Теги", move: "Переместить", del: "Удалить", compare: "Сравнить", addTag: "+ тег", tagPh: "имя тега, Enter",
    toWfImage: "Картинку в workflow", toWfParams: "Параметры в workflow", openWf: "Открыть workflow",
    sentWf: "Отправлено в ComfyUI", no_comfy: "ComfyUI не открыт ни в одной вкладке браузера", no_workflow: "В файле нет workflow",
    network_files: "Удаление и перемещение файлов с другого компьютера выключено (Настройки → Rigstools → PicoTeka)",
    no_send2trash: "Нет пакета send2trash: pip install send2trash", not_root: "Это не папка галереи",
    delTitle: "Удаление картинок", delText: "Переместить {n} {pics} в корзину Windows? Теги и рейтинг вернутся, если файл восстановить в течение 30 дней.",
    deleted: "Перемещено в корзину: {n}", moveTitle: "Перемещение картинок", moveText: "Переместить {n} {pics} в:", newFolder: "новая подпапка (необязательно)",
    moved: "Перемещено: {n}", rateTitle: "Рейтинг {n} {pics}", tagsTitle: "Теги {n} {pics}", tagsAdd: "Добавить", tagsRemove: "Убрать с картинок",
    manage: "управлять", tagsManage: "Теги", rename: "Переименовать", renamePh: "новое имя", tagDelete: "Удалить тег",
    pics1: "картинку", pics2: "картинки", pics5: "картинок", errors: "Не выполнено: {v}",
    cmpTitle: "Сравнение", viewTitle: "Просмотр", side: "Рядом", slider: "Шторка", hideSame: "Скрыть одинаковые параметры", param: "Параметр",
    cmpHint: "колесо — приблизить / отдалить | перетаскивание — сдвиг | двойной клик — вписать / 100% | масштаб и положение общие для обеих картинок", needTwo: "Выберите две картинки (Ctrl + клик)",
  },
};
let LANG = "en";
// Russian plural: 1 картинка, 2 картинки, 5 картинок
const plural = (n, [one, few, many]) => { const a = Math.abs(n) % 100, b = a % 10;
  return a > 10 && a < 20 ? many : b === 1 ? one : b > 1 && b < 5 ? few : many; };
const t = (k, v = {}) => Object.entries(v).reduce((s, [a, b]) => s.split(`{${a}}`).join(b), (STR[LANG] ?? STR.en)[k] ?? STR.en[k] ?? k);
const $ = (id) => document.getElementById(id);
// Button icons: line icons of Lucide (ISC, see THIRD_PARTY_NOTICES.md) and the two arrows of the comparison slider.
// SVG stays sharp at any screen scale, where the emoji and font symbols did not.
const ICONS = {
  image: `<rect width="18" height="18" x="3" y="3" rx="2" ry="2" /> <circle cx="9" cy="9" r="2" /> <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />`,
  sliders: `<line x1="21" x2="14" y1="4" y2="4" /> <line x1="10" x2="3" y1="4" y2="4" /> <line x1="21" x2="12" y1="12" y2="12" /> <line x1="8" x2="3" y1="12" y2="12" /> <line x1="21" x2="16" y1="20" y2="20" /> <line x1="12" x2="3" y1="20" y2="20" /> <line x1="14" x2="14" y1="2" y2="6" /> <line x1="8" x2="8" y1="10" y2="14" /> <line x1="16" x2="16" y1="18" y2="22" />`,
  help: `<circle cx="12" cy="12" r="10" /> <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /> <path d="M12 17h.01" />`,
  star: `<path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z" />`,
  hash: `<line x1="4" x2="20" y1="9" y2="9" /> <line x1="4" x2="20" y1="15" y2="15" /> <line x1="10" x2="8" y1="3" y2="21" /> <line x1="16" x2="14" y1="3" y2="21" />`,
  move: `<path d="M2 9V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-1" /> <path d="M2 13h10" /> <path d="m9 16 3-3-3-3" />`,
  trash: `<path d="M3 6h18" /> <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" /> <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" /> <line x1="10" x2="10" y1="11" y2="17" /> <line x1="14" x2="14" y1="11" y2="17" />`,
  rescan: `<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" /> <path d="M21 3v5h-5" /> <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" /> <path d="M8 16H3v5" />`,
  send: `<path d="M5 12h14" /> <path d="m12 5 7 7-7 7" />`,
  info: `<circle cx="12" cy="12" r="10" /> <path d="M12 16v-4" /> <path d="M12 8h.01" />`,
  copy: `<rect width="14" height="14" x="8" y="8" rx="2" ry="2" /> <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />`,
  check: `<path d="M20 6 9 17l-5-5" />`,
  close: `<path d="M18 6 6 18" /> <path d="m6 6 12 12" />`,
  workflow: `<rect width="8" height="8" x="3" y="3" rx="2" /> <path d="M7 11v4a2 2 0 0 0 2 2h4" /> <rect width="8" height="8" x="13" y="13" rx="2" />`,
  calendar: `<path d="M8 2v4" /> <path d="M16 2v4" /> <rect width="18" height="18" x="3" y="4" rx="2" /> <path d="M3 10h18" />`,
  search: `<circle cx="11" cy="11" r="8" /> <path d="m21 21-4.3-4.3" />`,
  sortaz: `<path d="m3 16 4 4 4-4" /> <path d="M7 20V4" /> <path d="M20 8h-5" /> <path d="M15 10V6.5a2.5 2.5 0 0 1 5 0V10" /> <path d="M15 14h5l-5 6h5" />`,
  chevron: `<path d="m6 9 6 6 6-6" />`,
  minus: `<path d="M5 12h14" />`,
  plus: `<path d="M5 12h14" /> <path d="M12 5v14" />`,
  folder: `<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />`,
  folderplus: `<path d="M12 10v6" /> <path d="M9 13h6" /> <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />`,
  up: `<path d="m5 12 7-7 7 7" /> <path d="M12 19V5" />`,
  home: `<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8" /> <path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />`,
  drive: `<line x1="22" x2="2" y1="12" y2="12" /> <path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" /> <line x1="6" x2="6.01" y1="16" y2="16" /> <line x1="10" x2="10.01" y1="16" y2="16" />`,
  chevright: `<path d="m9 18 6-6-6-6" />`,
  swap: `<path d="M4 9h16l-4-4"/><path d="M20 15H4l4 4"/>`,
};
const ic = (name) => `<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
  stroke-linejoin="round" aria-hidden="true">${ICONS[name]}</svg>`;
const cfgText = (v) => (v == null || v === "" || isNaN(+v) ? v : (+v).toFixed(1));   // CFG: always one decimal, 7 -> 7.0
const SEP = '<i class="sep"></i>';                                                // a thin vertical line between items
const sepHtml = (text) => esc(text).split(" | ").join(SEP);
const icl = (name, text) => `${ic(name)}<span>${esc(text)}</span>`;     // icon + label, for innerHTML

/* The hints of the viewer and of the comparison: a yellow (?) and the hints after it. When the bar has no room for all of
   them, the last ones fold away, a whole hint at a time (none left: only the (?) stays); a click on the (?) shows them
   all in a box. */
function setHint(id, text) {
  const h = $(id);
  if (h.dataset.text === text) return foldHint(h);   // the same hints: only the room may have changed
  h.dataset.text = text;
  h.querySelector(".hint-t").innerHTML = text.split(" | ").map((x, i) => `${i ? SEP : ""}<span class="hi">${esc(x)}</span>`).join("");
  const b = h.querySelector(".hint-ic");
  if (!b.firstChild) { b.innerHTML = ic("help"); b.onclick = (e) => { e.stopPropagation(); hintPop(h); }; }
  b.title = text.split(" | ").join("\n");
  foldHint(h);
}
function foldHint(h) {
  if (!h.offsetParent) return;                       // not on screen (the viewer is closed): measured when it opens
  h.classList.remove("folded");
  const t = h.querySelector(".hint-t"), parts = [...t.children];   // hint, line, hint, line, hint…
  parts.forEach((x) => (x.hidden = false));
  let n = parts.length;
  while (n > 0 && t.scrollWidth > t.clientWidth + 1) {
    parts[--n].hidden = true;                        // the last hint…
    if (n > 0) parts[--n].hidden = true;             // …and the line before it
  }
  if (!n) h.classList.add("folded");
}
const foldHints = () => document.querySelectorAll(".hint").forEach(foldHint);
addEventListener("resize", foldHints);
let popOf = null;
function hintPop(h) {
  let p = $("hint-pop");
  if (popOf === h && p && !p.hidden) { p.hidden = true; popOf = null; return; }
  if (!p) { p = el("div", "hint-pop"); p.id = "hint-pop"; document.body.append(p); }
  p.innerHTML = h.dataset.text.split(" | ").map((x) => `<div>${esc(x)}</div>`).join("");
  p.hidden = false; popOf = h;
  const r = h.querySelector(".hint-ic").getBoundingClientRect(), pr = p.getBoundingClientRect();
  const below = r.top < innerHeight / 2;              // the bar on top: the box below the (?), the bar at the bottom: above it
  p.style.left = Math.max(8, Math.min(innerWidth - pr.width - 8, r.left + r.width / 2 - pr.width / 2)) + "px";
  p.style.top = (below ? r.bottom + 8 : r.top - pr.height - 8) + "px";
}
addEventListener("click", () => { const p = $("hint-pop"); if (p && !p.hidden) { p.hidden = true; popOf = null; } });

const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const num = (n) => Number(n).toLocaleString(LANG === "ru" ? "ru-RU" : "en-US");
// The settings of the page (panel widths, thumbnail size, sort, open folders, comparison mode) are kept by ComfyUI in
// <user folder>/rigstools/gallery.json, so they survive closing the browser and follow the user to another browser.
// The browser storage is only a fallback for the first start and for a ComfyUI that refuses to save.
const PREFS_URL = "/api/userdata/" + encodeURIComponent("rigstools/gallery.json");
const prefs = await (async () => {
  try { const r = await fetch(PREFS_URL, { cache: "no-store" }); if (r.ok) return await r.json(); } catch { /* none yet */ }
  return {};
})();
let prefsTimer;
const savePrefs = () => {
  clearTimeout(prefsTimer);
  prefsTimer = setTimeout(() => fetch(PREFS_URL + "?overwrite=true&full_info=false", { method: "POST", body: JSON.stringify(prefs, null, 1) })
    .catch(() => {}), 400);
};
addEventListener("pagehide", () => { if (prefsTimer) { clearTimeout(prefsTimer); navigator.sendBeacon?.(PREFS_URL + "?overwrite=true", JSON.stringify(prefs)); } });
const store = {
  get(k, d) {
    if (k in prefs) return prefs[k];
    try { return JSON.parse(localStorage.getItem("rig.gallery." + k)) ?? d; } catch { return d; }
  },
  set(k, v) {
    prefs[k] = v; savePrefs();
    try { localStorage.setItem("rig.gallery." + k, JSON.stringify(v)); } catch { /* private window */ }
  },
};

// one tag = one colour, chosen from its name
const PAL = [[199, 80], [340, 70], [120, 45], [28, 85], [265, 60], [170, 55], [48, 80], [90, 55]];
const hash = (s) => { let h = 0; for (const c of s) h = (h * 31 + c.codePointAt(0)) >>> 0; return h; };
function tagHtml(name, tail = "", cls = "") {
  const [h, s] = PAL[hash(String(name).toLowerCase()) % PAL.length];
  return `<span class="tag ${cls}" data-tag="${esc(name)}" style="color:hsl(${h} ${Math.min(90, s + 15)}% 68%);background:hsl(${h} ${Math.round(s * .55)}% 15% / .92)">${esc(name)}${tail}</span>`;
}
const starsText = (r) => "★".repeat(r) + "☆".repeat(5 - r);

const S = {
  locs: [], q: "", sort: store.get("sort", "date"), size: store.get("size", 170),
  model: [], lora: [], sampler: [], tag: [], tag_mode: "any", rating: 0, from: "", to: "",
  items: [], total: 0, loading: false, done: false, cur: null, sel: new Set(), open: {},
  unseen: new Set(), beyond: 0,   // new pictures not seen yet: loaded ones by id, and how many past the loaded part
  held: new Set(),                // new pictures held back so the grid does not shift (see sync)
};

function params(extra = {}) {
  const p = new URLSearchParams();
  for (const k of ["q", "sort", "tag_mode"]) if (S[k]) p.set(k, S[k]);
  for (const l of S.locs) p.append("loc", `${l.root}\t${l.folder}`);       // the folders shown (several with Ctrl + click)
  for (const k of ["model", "lora", "sampler", "tag"]) for (const v of S[k]) p.append(k, v);
  if (S.rating) p.set("rating", S.rating);
  if (S.from) p.set("from", Date.parse(S.from) / 1000);
  if (S.to) p.set("to", Date.parse(S.to) / 1000 + 86400);
  for (const [k, v] of Object.entries(extra)) p.set(k, v);
  return p;
}
const get = async (path, p) => (await fetch(`${API}/${path}${p ? "?" + p : ""}`)).json();

// ---- folders -----------------------------------------------------------------------------------------------------
// Subfolders are collapsed until opened; what is open is remembered. The folders being shown are always visible: their
// parents open by themselves. Several folders can be shown at once: Ctrl + click adds or removes one.
const opened = new Set(store.get("open", []));
const saveOpened = () => store.set("open", [...opened]);

/** The folder tree, the same in the left panel and in the Move dialog. open — the set of open folders ("root|folder";
    a root is open unless "root|#closed"), on(root, folder) — is it chosen, pick(root, folder, event), redraw(). */
function drawTree(tree, roots, { open, on, pick, redraw, counts = true }) {
  for (const r of roots) {
    const hasKids = (f) => f === "" ? r.folders.length > 0 : r.folders.some(([g]) => g.startsWith(f + "/"));
    const isOpen = (f) => f === "" ? !open.has(`${r.path}|#closed`) : open.has(`${r.path}|${f}`);
    const visible = (f) => { const parts = f.split("/"); for (let i = 0; i < parts.length; i++) if (!isOpen(parts.slice(0, i).join("/"))) return false; return true; };
    const row = (label, folder, count, depth) => {
      const can = hasKids(folder), isO = can && isOpen(folder);
      const d = el("div", on(r.path, folder) ? "on" : "",
        `<span class="tn" style="padding-left:${depth * 14}px"><i class="tw ${can ? "" : "none"} ${isO ? "open" : ""}">${can ? ic("chevright") : ""}</i>${esc(label)}</span>` +
        (counts ? `<span class="muted">${num(count)}</span>` : ""));
      d.onclick = (e) => {
        if (e.target.closest(".tw") && can) {                 // the arrow opens or closes, without choosing the folder
          const k = folder === "" ? `${r.path}|#closed` : `${r.path}|${folder}`;
          if (folder === "" ? !isO : isO) open.delete(k); else open.add(k);
          redraw(); return;
        }
        pick(r.path, folder, e);
      };
      d.ondblclick = (e) => { if (!can || e.target.closest(".tw") || e.ctrlKey || e.metaKey) return; d.querySelector(".tw").click(); };
      tree.append(d);
    };
    row(r.label, "", r.count, 0);
    for (const [f, n] of r.folders) if (visible(f)) row(f.split("/").pop(), f, n, f.split("/").length);
  }
}

async function loadFolders() {
  const roots = await get("folders");
  const tree = $("tree");
  const keep = tree.scrollTop;
  tree.replaceChildren();
  for (const l of S.locs) {
    const parts = l.folder ? l.folder.split("/") : [];
    for (let i = 0; i < parts.length; i++) opened.add(`${l.root}|${parts.slice(0, i).join("/")}`);
  }
  const has = (root, folder) => S.locs.some((l) => l.root === root && l.folder === folder);
  drawTree(tree, roots, {
    open: opened, on: has, redraw: () => { saveOpened(); loadFolders(); },
    pick: (root, folder, e) => {
      if (e.ctrlKey || e.metaKey) S.locs = has(root, folder) ? S.locs.filter((l) => !(l.root === root && l.folder === folder)) : [...S.locs, { root, folder }];
      else S.locs = [{ root, folder }];
      reload(); loadFolders();
    },
  });
  const all = el("div", S.locs.length ? "" : "on", `<span class="tn"><i class="tw none"></i>${t("allFolders")}</span><span class="muted">${num(roots.reduce((a, r) => a + r.count, 0))}</span>`);
  all.onclick = () => { S.locs = []; reload(); loadFolders(); };
  tree.prepend(all);
  tree.title = t("foldersTip");
  tree.scrollTop = keep;
  $("add-folder").textContent = t("addFolder");
  $("add-folder").onclick = () => folderDialog(roots);
}

// ---- filters -----------------------------------------------------------------------------------------------------
async function loadFacets() {
  const f = await get("facets", params());
  for (const key of ["model", "lora", "sampler", "tag"]) {
    const box = $("f-" + key);
    const list = f[key] ?? [];
    box.replaceChildren();
    if (!list.length && !S[key].length) continue;
    const head = el("div", "h", `<span>${t(key)}</span>`);
    if (key === "tag") { const a = el("a", "", t("manage")); a.onclick = manageTags; head.append(a); }
    if (S[key].length) { const a = el("a", "", t("clear")); a.onclick = () => { S[key] = []; reload(); }; head.append(a); }
    const chips = el("div", "chips");
    const LIMIT = 8, open = S.open[key];
    list.forEach(([v, n], i) => {
      if (i >= LIMIT && !open && !S[key].includes(v)) return;
      const on = S[key].includes(v);
      const c = key === "tag" ? el("span", "", tagHtml(v, ` <b style="color:#999;font-weight:400">${num(n)}</b>`, on ? "on" : "")).firstChild
        : el("span", `chip ${key === "lora" ? "lora" : ""} ${on ? "on" : ""}`, `${esc(v)}<b>${num(n)}</b>`);
      c.title = v;
      c.onclick = () => { S[key] = on ? S[key].filter((x) => x !== v) : [...S[key], v]; reload(); };
      chips.append(c);
    });
    box.append(head, chips);
    if (list.length > LIMIT) {
      const m = el("div", "more", open ? t("less") : t("more", { n: list.length - LIMIT }));
      m.onclick = () => { S.open[key] = !open; loadFacets(); };
      box.append(m);
    }
    if (key === "tag" && S.tag.length > 1) {
      const m = el("div", "mode", `${S.tag_mode === "all" ? "◉" : "○"} ${t("tagAll")}${SEP}${S.tag_mode === "any" ? "◉" : "○"} ${t("tagAny")}`);
      m.onclick = () => { S.tag_mode = S.tag_mode === "all" ? "any" : "all"; reload(); };
      box.append(m);
    }
  }
  const r = $("rating");
  r.classList.add("ico");
  r.innerHTML = starRow(S.rating) +
    ` <span class="muted" style="letter-spacing:0;font-size:11px">${S.rating ? t("andUp") : ""}</span>`;
  r.onclick = (e) => { const v = starOf(e); if (v) { S.rating = v === S.rating ? 0 : v; reload(); } };
  $("rating-clear").textContent = S.rating ? t("clear") : "";
  $("date-clear").textContent = S.from || S.to ? t("clear") : "";
}

// ---- grid --------------------------------------------------------------------------------------------------------
// the date of the file, 24-hour time: 14.11.2026, 18:32 / 11/14/2026, 18:32
const when = (sec) => sec ? new Date(sec * 1000).toLocaleString(LANG === "ru" ? "ru-RU" : "en-US",
  { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }) : "";

/** Pixels the thumbnail needs: the real cell width (the grid stretches cells) × the screen scale. */
function thumbPx() {
  const g = $("grid"), gap = 10, w = g.clientWidth || 1000;
  const n = Math.max(1, Math.floor((w + gap) / (S.size + gap)));
  return Math.ceil(((w - gap * (n - 1)) / n) * (window.devicePixelRatio || 1));
}

/** A drop-down drawn as the fields (the browser list cannot be styled): mouse and keyboard (↑ ↓ Enter Esc).
    keys() — the items, label(k) — their text, value() — the current one, choose(k) — what a choice does. */
function dropdown(box, { keys, label, value, choose, icon }) {
  const btn = box.querySelector(".dd-btn"), menu = box.querySelector(".dd-menu");
  if (icon) btn.querySelector("svg:not(.dd-chev)").outerHTML = ic(icon);
  btn.querySelector(".dd-chev").outerHTML = ic("chevron").replace('class="ic"', 'class="ic dd-chev"');
  let hi = 0;
  const show = () => {
    const ks = keys(), v = value();
    btn.querySelector(".dd-v").textContent = label(v);
    menu.innerHTML = ks.map((k, i) => `<div class="dd-i${k === v ? " on" : ""}${i === hi ? " hi" : ""}" role="option" data-k="${k}">` +
      `${k === v ? ic("check") : '<i class="ic"></i>'}<span>${esc(label(k))}</span></div>`).join("");
  };
  const open = (on) => {
    menu.hidden = !on; box.classList.toggle("open", on);
    if (on) { hi = Math.max(0, keys().indexOf(value())); show(); }
  };
  const pick = (k) => { open(false); if (k != null && k !== String(value())) choose(k); show(); };
  btn.onclick = () => open(menu.hidden);
  menu.onclick = (e) => pick(e.target.closest(".dd-i")?.dataset.k);
  menu.onmousemove = (e) => { const i = keys().indexOf(e.target.closest(".dd-i")?.dataset.k); if (i >= 0 && i !== hi) { hi = i; show(); } };
  btn.onkeydown = (e) => {
    const ks = keys();
    if (menu.hidden) { if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") { open(true); e.preventDefault(); e.stopPropagation(); } return; }
    if (e.key === "ArrowDown" || e.key === "ArrowUp") { hi = (hi + (e.key === "ArrowDown" ? 1 : ks.length - 1)) % ks.length; show(); }
    else if (e.key === "Enter" || e.key === " ") pick(ks[hi]);
    else if (e.key === "Escape") open(false);
    else return;
    e.preventDefault(); e.stopPropagation();
  };
  document.addEventListener("pointerdown", (e) => { if (!box.contains(e.target)) open(false); });
  show();
  return show;
}

/** The sort: a drop-down with the A–Z icon. */
function initSort() {
  dropdown($("sort"), { keys: () => ["date", "date_asc", "name", "rating"], label: (k) => t("sort_" + k), value: () => S.sort, icon: "sortaz",
    choose: (k) => { S.sort = k; store.set("sort", k); reload(); } });
}

/** The zoom control of Windows 11, built inside `root`: presets in % in a drop-down, − / + to the next preset, a round
    slider (linear or logarithmic). get() — the current %, set(p) — what a new % does. Returns update(): call it when the
    zoom changed elsewhere (wheel, fit, window), the control then shows it. */
function zoomHtml() {
  return `<div class="dd zdd"><button class="inp dd-btn" type="button" aria-haspopup="listbox"><span class="dd-v"></span><svg class="ic dd-chev"></svg></button>
    <div class="dd-menu" role="listbox" hidden></div></div><button class="zb zminus" type="button">${ic("minus")}</button>
    <div class="zs" tabindex="0" role="slider"><div class="zs-track"><i></i></div><div class="zs-thumb"><i></i></div></div>
    <button class="zb zplus" type="button">${ic("plus")}</button>`;
}
function zoomControl(root, { min, max, presets, log = false, get, set }) {
  const minus = root.querySelector(".zminus"), plus = root.querySelector(".zplus"), zs = root.querySelector(".zs");
  const thumbEl = zs.querySelector(".zs-thumb"), fill = zs.querySelector(".zs-track i");
  const L = (x) => Math.log(x);
  const toPos = (p) => (log ? (L(p) - L(min)) / (L(max) - L(min)) : (p - min) / (max - min));
  const fromPos = (f) => (log ? Math.exp(L(min) + f * (L(max) - L(min))) : min + f * (max - min));
  const clamp = (p) => Math.max(min, Math.min(max, p));
  const cur = () => Math.round(get());
  zs.setAttribute("aria-valuemin", min); zs.setAttribute("aria-valuemax", max);
  let showDd;
  const update = () => {
    const p = clamp(get()), at = Math.max(0, Math.min(1, toPos(p))) * 100;
    thumbEl.style.left = at + "%"; fill.style.width = at + "%";
    zs.setAttribute("aria-valuenow", Math.round(p));
    minus.disabled = cur() <= min; plus.disabled = cur() >= max;
    showDd?.();
  };
  const go = (p, animate) => { zs.classList.toggle("anim", !!animate); set(Math.round(clamp(p))); update(); };
  const next = (d) => {
    const p = cur();
    const to = d > 0 ? presets.find((x) => x > p) : [...presets].reverse().find((x) => x < p);
    if (to != null) go(to, true);
  };
  minus.onclick = () => next(-1); plus.onclick = () => next(1);
  showDd = dropdown(root.querySelector(".zdd"), { keys: () => presets.map(String), label: (k) => `${k}%`, value: () => String(cur()),
    choose: (k) => go(+k, true) });
  const fromX = (x) => { const r = zs.getBoundingClientRect(); return fromPos(Math.max(0, Math.min(1, (x - r.left) / r.width))); };
  zs.onpointerdown = (e) => {
    if (e.button !== 0) return;
    e.preventDefault(); e.stopPropagation(); zs.focus(); zs.setPointerCapture(e.pointerId); zs.classList.add("drag");
    go(fromX(e.clientX), !e.target.closest(".zs-thumb"));
    zs.onpointermove = (m) => go(fromX(m.clientX), false);
    zs.onpointerup = () => { zs.onpointermove = zs.onpointerup = null; zs.classList.remove("drag"); };
  };
  zs.onkeydown = (e) => {
    const k = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1, PageUp: 5, PageDown: -5 }[e.key];
    if (k) go(log ? cur() * Math.pow(1.1, k) : cur() + 5 * k, true);
    else if (e.key === "Home") go(min, true);
    else if (e.key === "End") go(max, true);
    else return;
    e.preventDefault(); e.stopPropagation();
  };
  root.addEventListener("wheel", (e) => e.stopPropagation(), { passive: true });
  update();
  return update;
}

/** The size of the thumbnails: 100% is the usual size (170 px), 60–200%. */
const ZOOM = { base: 170, min: 60, max: 200, presets: [60, 75, 100, 125, 150, 175, 200] };
function initZoom() {
  const root = $("zoom");
  root.insertAdjacentHTML("beforeend", zoomHtml());
  const setPx = (v) => {
    document.body.style.setProperty("--th", v + "px");
    const before = S.size;
    if (v === before) return;
    S.size = v; store.set("size", v);
    const lvl = (x) => (x < 130 ? 0 : x < 230 ? 1 : 2);
    if (lvl(before) !== lvl(v)) $("grid").replaceChildren(...S.items.map(thumb));   // another level of detail
    sharpen();
  };
  S.size = Math.round(ZOOM.base * Math.max(ZOOM.min, Math.min(ZOOM.max, S.size / ZOOM.base * 100)) / 100);
  setPx(S.size); document.body.style.setProperty("--th", S.size + "px");
  zoomControl(root, { ...ZOOM, get: () => S.size / ZOOM.base * 100, set: (p) => setPx(Math.round(ZOOM.base * p / 100)) });
}

/** The zoom of a picture (viewer and comparison): 5–1600%, logarithmic, as the wheel. */
const PIC_ZOOM = { min: 5, max: 1600, log: true, presets: [10, 25, 50, 66, 75, 100, 150, 200, 300, 400, 800, 1600] };
let vZoomUpdate = null, cZoomUpdate = null;

/** Bigger cells (size, window, panels) need bigger thumbnails: swap them once the cells settle. */
let sharpenTimer;
function sharpen() {
  clearTimeout(sharpenTimer);
  sharpenTimer = setTimeout(() => {
    const px = thumbPx();
    for (const img of $("grid").querySelectorAll(".th img")) {
      const has = +new URL(img.src).searchParams.get("s");
      if (has < px) img.src = img.src.replace(/s=\d+/, "s=" + px);
    }
  }, 250);
}

/** The side panels are resized by dragging their inner edge; the widths are remembered. */
function initSplits() {
  const set = (name, v) => document.body.style.setProperty(name, v + "px");
  const w = { side: store.get("sideW", 250), card: store.get("cardW", 400) };
  set("--side-w", w.side); set("--card-w", w.card);
  const drag = (handle, key, sign, min, max) => {
    handle.onpointerdown = (e) => {
      e.preventDefault();
      handle.setPointerCapture(e.pointerId); handle.classList.add("on");
      const x0 = e.clientX, w0 = w[key];
      handle.onpointermove = (m) => {
        w[key] = Math.max(min, Math.min(max, w0 + sign * (m.clientX - x0))); set(`--${key}-w`, w[key]);
        if (V.open) (V.fit ? fitView() : place());          // the picture of the viewer follows its panel
      };
      handle.onpointerup = () => {
        handle.onpointermove = handle.onpointerup = null; handle.classList.remove("on");
        store.set(key + "W", w[key]); sharpen();
      };
    };
    handle.ondblclick = () => { w[key] = key === "side" ? 250 : 400; set(`--${key}-w`, w[key]); store.set(key + "W", w[key]); sharpen(); };
  };
  drag($("split-side"), "side", 1, 180, 520);
  drag($("split-card"), "card", -1, 300, 760);
  drag($("split-view"), "card", -1, 300, 760);   // the panel of the full-screen viewer: the same width as the card
}

/** The thumbnail URL. The browser keeps thumbnails a day, so the URL carries the file's version (mtime and size): an id
    can come back for another file (SQLite reuses the ids of the newest rows after they are deleted) and a file can be
    written anew under the same name — without the version the browser would show the old picture. */
/** The mark of a compared picture, A or B: the same colour over the pictures and in the table of parameters. */
const abMark = (k) => `<span class="abm ${k}">${k.toUpperCase()}</span>`;
const thumbUrl = (it, s) => `${API}/thumb/${it.id}?s=${s}&v=${Math.round((it.mtime || 0) * 1000)}-${it.size || 0}`;

/** A grid cell: the thumbnail and, under it, the file name, the resolution and the date of the file. */
function thumb(it) {
  const size = S.size, cell = el("div", "cell"), d = el("div", "th");
  cell.dataset.id = it.id;
  let h = `<img loading="lazy" src="${thumbUrl(it, thumbPx())}" alt=""><span class="fmt ${esc(String(it.fmt).toLowerCase())}">${esc(it.fmt)}</span>`;
  const r = it.rating || 0, tags = it.tags || [];
  // stars in the top left corner (the format is in the top right), the tags and the lines at the bottom
  if (r) h += `<span class="st">${size < 130 ? "★".repeat(r) : starsText(r)}</span>`;
  if (size >= 130 && size < 230) {
    if (tags.length) h += `<div class="info"><div class="row1">${tagHtml(tags[0])}` +
      `${tags.length > 1 ? `<span class="line"><i>+${tags.length - 1}</i></span>` : ""}</div></div>`;
  } else if (size >= 230) {
    const lines = [];
    if (it.seed != null) lines.push(`<div class="line"><i>seed</i> ${esc(it.seed)}</div>`);
    const gen = [it.model, it.sampler, it.scheduler, it.steps != null ? `steps ${it.steps}` : null,
      it.cfg != null ? `cfg ${cfgText(it.cfg)}` : null].filter((x) => x != null && x !== "");
    if (gen.length) lines.push(`<div class="line">${esc(gen[0])}${gen.length > 1 ? `${SEP}<i>${gen.slice(1).map(esc).join(SEP)}</i>` : ""}</div>`);
    if (tags.length || lines.length) h += `<div class="info">${tags.length ? `<div class="tags">${tags.map((x) => tagHtml(x)).join("")}</div>` : ""}${lines.join("")}</div>`;
  }
  d.innerHTML = h;
  const cap = el("div", "cap", `<b title="${esc(it.name)}">${esc(it.name)}</b>` +
    `<div><span>${it.width && it.height ? `${it.width}×${it.height}` : ""}</span><span>${esc(when(it.mtime))}</span></div>`);
  cell.append(d, cap);
  if (S.sel.has(it.id)) cell.classList.add("sel");
  if (S.cur === it.id) cell.classList.add("cur");
  cell.onclick = (e) => pick(it.id, e);
  cell.ondblclick = () => openViewer(it.id);
  return cell;
}

let gen = 0;
async function loadMore() {
  if (S.loading || S.done) return;
  S.loading = true;
  const my = gen;
  // the held pictures (see sync) are in the server's list before the loaded end, so they count in the offset
  const r = await get("images", params({ offset: S.items.length + S.held.size, limit: 150 }));
  if (my !== gen) return;
  S.loading = false;
  if (r.error) { S.done = true; return; }
  S.total = r.total;
  const known = new Set(S.items.map((x) => x.id));
  r.items = r.items.filter((x) => !known.has(x.id) && !S.held.has(x.id));   // a list changed in between: no doubles
  S.items.push(...r.items);
  S.done = S.items.length + S.held.size >= r.total || !r.items.length;
  if (S.done && S.beyond) { S.beyond = 0; requestAnimationFrame(showNew); }   // the end of the list is loaded: nothing past it
  const grid = $("grid");
  for (const it of r.items) grid.append(thumb(it));
  if (!S.items.length) grid.replaceChildren(el("div", "empty", t("empty")));
  $("st-shown").textContent = t("shown", { n: num(S.items.length), total: num(S.total) });
  if (!S.cur && S.items.length && !S.cleared) { pick(S.items[0].id); S.picked = false; }
  // keep loading while the sentinel is still on screen
  requestAnimationFrame(() => { if (!S.done && $("sentinel").getBoundingClientRect().top < innerHeight + 400) loadMore(); });
}

function reload() {
  gen++;
  S.items = []; S.done = false; S.loading = false; S.cur = null; S.sel.clear(); S.unseen.clear(); S.held.clear(); S.beyond = 0; S.picked = false; S.cleared = false; $("fresh").hidden = true;
  $("grid").replaceChildren();
  $("main").scrollTop = 0;
  loadMore();
  loadFacets();
}

// ---- new and changed pictures after a scan ------------------------------------------------------------------------
// The loaded part of the list is read again and the grid is brought to it in place: gone pictures leave, changed ones
// are redrawn, the picked picture, the selection and the open viewer are kept, and the first picture seen at the top
// stays at the same height. New pictures:
//  - at the very top of the grid with nothing selected and the viewer closed: put in at once (nothing to aim at);
//  - otherwise put in at once only where nothing on screen moves: below what is seen, or whole rows above it;
//  - the rest are held back (S.held) — a cell put in before the seen ones moves every cell after it along its row —
//    until the note is clicked or the grid is scrolled to the very top with nothing selected.
// New pictures out of sight: the note on top of the grid says how many and where.
const SYNC_MAX = 2000;     // more loaded than that: the list is not read again, the note offers to reload instead
let syncing = false, syncAgain = null;
// "nothing selected": no selection and no picture picked by the user (the first one is picked by itself on loading)
const atFreeTop = () => $("main").scrollTop < 50 && S.sel.size === 0 && !S.picked && !V.open;
async function sync(added, force = false) {
  if (syncing) { syncAgain = { added: (syncAgain?.added || 0) + added, force: !!(syncAgain?.force || force) }; return; }
  if (!S.items.length) return reload();
  if (S.items.length + S.held.size + added > SYNC_MAX) { S.beyond += added; return showNew(); }
  // read a little past the loaded end: while the list is read, more pictures may come (the next run finishes); they
  // must not push the last loaded pictures out of the window, where they would look gone
  const want = S.items.length + S.held.size + added + 60;
  syncing = true;
  const my = gen, items = [];
  let total = S.total;
  try {
    while (items.length < want) {
      const r = await get("images", params({ offset: items.length, limit: Math.min(500, want - items.length) }));
      if (my !== gen || r.error) return;
      total = r.total; items.push(...r.items);
      if (items.length >= total || !r.items.length) break;
    }
  } catch { return; } finally {
    syncing = false;
    if (syncAgain) { const n = syncAgain; syncAgain = null; setTimeout(() => sync(n.added, n.force)); }
  }
  // not the whole list: cut after the last picture that was loaded — what comes after it loads with the list
  if (items.length < total) {
    const known = new Set(S.items.map((x) => x.id));
    let last = -1;
    items.forEach((x, i) => { if (known.has(x.id)) last = i; });
    if (last >= 0) items.length = last + 1;
  }
  apply(items, total, force);
}

/** Cells in a row of the grid now. */
function rowCells() {
  const cs = $("grid").querySelectorAll(".cell");
  if (!cs.length) return 1;
  const y = cs[0].offsetTop;
  let n = 0;
  for (const c of cs) { if (c.offsetTop !== y) break; n++; }
  return Math.max(1, n);
}

function apply(items, total, force = false) {
  const main = $("main"), grid = $("grid"), box = main.getBoundingClientRect();
  const old = new Map(S.items.map((x) => [x.id, x]));
  const cellEls = [...grid.querySelectorAll(".cell")];
  const cells = new Map(cellEls.map((c) => [+c.dataset.id, c]));
  // what is seen now: the anchor (the first picture seen at the top) and the ids of the first and the last seen
  let anchorId = null, anchorY = 0, lastSeen = null;
  for (const c of cellEls) {
    const r = c.getBoundingClientRect();
    if (r.bottom <= box.top + 1) continue;
    if (r.top >= box.bottom) break;
    if (anchorId == null) { anchorId = +c.dataset.id; anchorY = r.top; }
    lastSeen = +c.dataset.id;
  }
  // the new pictures and where they would go: above what is seen, among it, or below it
  const oldIdx = new Map(S.items.map((x, i) => [x.id, i]));
  const i0 = anchorId != null ? oldIdx.get(anchorId) : -1, i1 = lastSeen != null ? oldIdx.get(lastSeen) : -1;
  const fresh = [], above = [], inView = [];
  let olds = 0;                                   // old pictures met so far in the new order
  for (const it of items) {
    if (old.has(it.id)) { olds++; continue; }
    fresh.push(it.id);
    if (i0 < 0) continue;
    if (olds <= i0) above.push(it.id); else if (olds <= i1) inView.push(it.id);
  }
  const free = force || i0 < 0 || atFreeTop() || (!inView.length && above.length % rowCells() === 0);
  const hold = new Set(free ? [] : [...above, ...inView]);
  const shown = items.filter((it) => !hold.has(it.id));
  const ids = new Set(items.map((x) => x.id));
  const gone = [...old.keys()].filter((id) => !ids.has(id)).length;
  const curChanged = S.cur != null && JSON.stringify(old.get(S.cur)) !== JSON.stringify(items.find((x) => x.id === S.cur));
  const viewed = V.open ? S.items[V.i]?.id : null;
  const nodes = shown.map((it) => {
    const o = old.get(it.id), c = cells.get(it.id);
    if (!o) { const n = thumb(it); n.classList.add("new"); return n; }
    return c && JSON.stringify(o) === JSON.stringify(it) ? c : thumb(it);
  });
  const before = S.total;
  S.items = shown; S.held = hold; S.total = total; S.done = items.length >= total;
  // new pictures past the loaded part (the end of an oldest-first list): counted, they load with the list
  if (!S.done) S.beyond += Math.max(0, total - before - fresh.length + gone);
  grid.replaceChildren(...nodes);
  if (!items.length) grid.replaceChildren(el("div", "empty", t("empty")));
  const a = anchorId != null && grid.querySelector(`.cell[data-id="${anchorId}"]`);
  if (a) main.scrollTop += a.getBoundingClientRect().top - anchorY;
  // the selection and the picked picture: gone ones drop out
  for (const id of [...S.sel]) if (!ids.has(id)) S.sel.delete(id);
  if (S.cur != null && !ids.has(S.cur)) { if (shown.length) { pick(shown[0].id); S.picked = false; } else showCard(null); }
  else if (curChanged) showCard(shown.find((x) => x.id === S.cur));
  $("b-compare").disabled = S.sel.size !== 2;
  $("b-compare").innerHTML = icl("swap", t("compare") + (S.sel.size ? ` (${S.sel.size})` : ""));
  if (V.open) {
    const i = shown.findIndex((x) => x.id === viewed);
    if (i < 0) closeViewer(); else { V.i = i; $("v-pos").textContent = t("of", { i: num(V.i + 1), n: num(S.total) }); }
  }
  $("st-shown").textContent = t("shown", { n: num(S.items.length), total: num(S.total) });
  for (const id of fresh) if (!hold.has(id)) S.unseen.add(id);
  markSeen();
}

/** New pictures that came on screen are seen: their highlight fades, the note counts the rest. */
function markSeen() {
  const r = $("main").getBoundingClientRect();
  for (const id of [...S.unseen]) {
    const c = $("grid").querySelector(`.cell[data-id="${id}"]`);
    if (!c) { S.unseen.delete(id); continue; }
    const b = c.getBoundingClientRect();
    if (b.bottom > r.top + 20 && b.top < r.bottom - 20) { S.unseen.delete(id); setTimeout(() => c.classList.remove("new"), 2500); }
  }
  showNew();
}

/** The note on top of the grid: how many new pictures are out of sight or held back, with an arrow to where they are. */
function showNew() {
  const b = $("fresh"), top = $("main").getBoundingClientRect().top;
  let up = S.held.size, down = S.beyond;
  for (const id of S.unseen) {
    const c = $("grid").querySelector(`.cell[data-id="${id}"]`);
    if (c && c.getBoundingClientRect().bottom <= top + 20) up++; else down++;
  }
  b.hidden = !(up + down);
  if (b.hidden) return;
  b.innerHTML = `<span>${esc(t("fresh", { n: num(up + down) }))}</span><span class="arr">${up ? "↑" : "↓"}</span>`;
}

/** The note clicked: held pictures go in, then to the nearest new picture out of sight (loading the list further when
    it is past the loaded part). */
async function goToNew() {
  const main = $("main");
  if (S.held.size) { await sync(0, true); if (S.held.size) return; }
  if (S.items.length > SYNC_MAX && S.beyond && S.done) return reload();
  const top = main.getBoundingClientRect().top;
  const cells = [...S.unseen].map((id) => $("grid").querySelector(`.cell[data-id="${id}"]`)).filter(Boolean);
  const up = cells.filter((c) => c.getBoundingClientRect().bottom <= top + 20);
  const target = up.length ? up.reduce((a, c) => (c.getBoundingClientRect().top > a.getBoundingClientRect().top ? c : a)) : cells[0];
  if (!target && S.beyond) {
    if (S.items.length + S.beyond > SYNC_MAX) return reload();
    while (!S.done) { await loadMore(); if (S.loading) break; }
    S.beyond = 0;
    main.scrollTo({ top: main.scrollHeight, behavior: "smooth" });
    return showNew();
  }
  if (target) target.scrollIntoView({ block: "center", behavior: "smooth" });
}

/** Scrolled: new pictures that came on screen are seen; at the very top with nothing selected the held ones go in. */
function onGridScroll() {
  if (S.held.size && atFreeTop()) sync(0, true);
  else if (S.unseen.size) markSeen();
}

/** Nothing picked: Esc in the grid or a click on its empty space. The card asks to pick a picture; at the very top new
    pictures then go in at once (see sync). */
function unpick() {
  if (S.cur == null && !S.sel.size) return;
  S.cur = null; S.sel.clear(); S.picked = false; S.cleared = true;
  for (const d of $("grid").querySelectorAll(".cell.cur, .cell.sel")) d.classList.remove("cur", "sel");
  $("b-compare").disabled = true;
  $("b-compare").innerHTML = icl("swap", t("compare"));
  showCard(null);
  if (S.held.size && atFreeTop()) sync(0, true);
}

function pick(id, e) {
  if (e && (e.ctrlKey || e.metaKey)) {
    // Ctrl + click on the only picked picture: nothing picked (as in Explorer)
    if (!S.sel.size && S.cur === id && S.picked) return unpick();
    if (!S.sel.size && S.cur != null && S.cur !== id) S.sel.add(S.cur);    // the picture picked before joins the selection
    if (S.sel.has(id)) {
      // Ctrl + click on a selected picture takes it out; the current one moves to the last one still selected, so the
      // picture taken out is not left highlighted as the current one
      S.sel.delete(id);
      const rest = [...S.sel];
      if (!rest.length) return unpick();
      if (rest.length === 1) S.sel.clear();      // one left: it is simply the picked picture
      id = rest[rest.length - 1];
    } else S.sel.add(id);
  }
  else if (e && e.shiftKey && S.cur != null) {
    const ids = S.items.map((x) => x.id), a = ids.indexOf(S.cur), b = ids.indexOf(id);
    for (const x of ids.slice(Math.min(a, b), Math.max(a, b) + 1)) S.sel.add(x);
  } else { S.sel.clear(); }
  S.picked = true; S.cleared = false;
  S.cur = id;
  $("b-compare").disabled = S.sel.size !== 2;
  $("b-compare").innerHTML = icl("swap", t("compare") + (S.sel.size ? ` (${S.sel.size})` : ""));
  for (const d of $("grid").children) { d.classList.toggle("cur", +d.dataset.id === id); d.classList.toggle("sel", S.sel.has(+d.dataset.id)); }
  showCard(S.items.find((x) => x.id === id));
}

// ---- card ------------------------------------------------------------------------------------------------------
const fsize = (b) => b > 1048576 ? `${(b / 1048576).toFixed(1)} ${LANG === "ru" ? "МБ" : "MB"}` : `${Math.round(b / 1024)} ${LANG === "ru" ? "КБ" : "KB"}`;
const fileLine = (it) => [`${it.width}×${it.height}`, esc(it.fmt), fsize(it.size), it.folder ? esc(it.folder) : null].filter(Boolean).join(SEP);

// the name, rating, tags and parameters of a picture — the card and the viewer panel show the same block
function infoHtml(it) {
  const dot = (v) => `<span class="dot ${v == null || v === "" ? "none" : ""}"></span>`;
  const f = (label, v) => `<div class="f" title="${esc(v ?? t("missing"))}"><label>${dot(v)}${label}</label><span>${esc(v ?? "—")}</span></div>`;
  const tx = (label, v, cls = "") => `<div class="t ${cls}"><label>${dot(v)}${label}${v ? `<button class="cp" data-copy="${label}" title="${t("copyPrompt")}">${ic("copy")}</button>` : ""}</label>${esc(v || "—")}</div>`;
  const loras = (it.loras || []).map(([n, w]) => `<span class="lora">${esc(n)} <i>×${w}</i></span>`).join("") || "—";
  return `<div class="ih"><div class="name"><div><b>${esc(it.name)}</b><div class="muted">${fileLine(it)}</div></div>${starsHtml(it.rating || 0)}</div>
    <div class="chips tagline">${(it.tags || []).map((x) => tagHtml(x, ' <i class="x">✕</i>')).join("")}<span class="chip addtag">${t("addTag")}</span></div></div>
    <div class="ib">${it.has_params ? `<div class="rcard">${tx("positive", it.positive, "pos")}${tx("negative", it.negative, "neg")}
      <div class="row" style="grid-template-columns:1.8fr 1fr">${f("seed", it.seed)}${f("steps", it.steps)}</div>
      <div class="row" style="grid-template-columns:1fr 1fr${it.denoise != null ? " 1fr" : ""}">${f("cfg", cfgText(it.cfg))}${f("clip skip", it.clip_skip)}${it.denoise != null ? f("denoise", it.denoise) : ""}</div>
      <div class="row" style="grid-template-columns:1fr 1fr">${f("sampler", it.sampler)}${f("scheduler", it.scheduler)}</div>
      <div class="row" style="grid-template-columns:2fr 1fr">${f("model", it.model)}${f("size", it.gen_width ? `${it.gen_width}×${it.gen_height}` : null)}</div>
      <div class="t lor"><label>${dot(it.loras?.length ? 1 : null)}lora</label>${loras}</div></div>
      ${it.rebuilt ? `<div class="note">${t("rebuilt")}</div>` : ""}` : `<div class="note">${t("noParams")}</div>`}</div>
    <div class="acts"><button class="btn pri" data-act="image">${icl("send", t("toWfImage"))}</button>
      <button class="btn pri" data-act="params" ${it.has_params ? "" : "disabled"}>${icl("send", t("toWfParams"))}</button>
      <button class="btn" data-act="workflow" ${it.has_workflow ? "" : "disabled"}>${icl("workflow", t("openWf"))}</button>
      <button class="btn" data-act="copy" ${it.has_params ? "" : "disabled"}>${icl("copy", t("copyParams"))}</button>
      <button class="btn" data-act="meta">${icl("info", t("fileData"))}</button>
      <button class="btn dang" data-act="delete">${icl("trash", t("del"))}</button></div>`;
}
// rating stars as the icon of the Rating button: filled when given, an outline when not (the thumbnails keep font stars)
const starRow = (r, cls = "") => [1, 2, 3, 4, 5].map((i) => `<span data-r="${i}" class="sv ${i <= r ? "on" : "off"} ${cls}">${ic("star")}</span>`).join("");
const starsHtml = (r) => `<div class="stars rate ico">${starRow(r)}</div>`;
const starOf = (e) => +(e.target.closest("[data-r]")?.dataset.r || 0);

function wireInfo(box, it) {
  box.querySelector(".rate").onclick = (e) => { const r = starOf(e); if (r) setRating([it.id], r === it.rating ? 0 : r); };
  const line = box.querySelector(".tagline");
  line.onclick = (e) => {
    const x = e.target.closest(".x");
    if (x) editTags([it.id], [], [x.closest(".tag").dataset.tag]);
    else if (e.target.closest(".addtag")) tagInput(line, (name) => editTags([it.id], [name], []));
  };
  box.querySelector('[data-act="copy"]').onclick = async (e) => {
    const btn = e.currentTarget;
    let m;
    try { m = await readMeta(it.id); } catch (err) { toast(`${t("metaFailed")}: ${err.message}`, true); return; }
    try { await navigator.clipboard.writeText(m.parameters || ""); btn.innerHTML = icl("check", t("copied")); } catch { toast(t("copyFailed"), true); }
  };
  for (const b of box.querySelectorAll("[data-copy]")) b.onclick = async (e) => {
    e.stopPropagation();
    try { await navigator.clipboard.writeText(it[b.dataset.copy] || ""); toast(t("copied")); b.innerHTML = ic("check"); setTimeout(() => (b.innerHTML = ic("copy")), 1200); }
    catch { toast(t("copyFailed"), true); }
  };
  box.querySelector('[data-act="meta"]').onclick = () => openMeta(it);
  for (const kind of ["image", "params", "workflow"]) box.querySelector(`[data-act="${kind}"]`).onclick = () => sendToComfy(it.id, kind);
  box.querySelector('[data-act="delete"]').onclick = () => deleteDialog([it.id]);
}

/** After a change to pictures: their cells, the card and the open viewer show it. */
function refreshItems(ids) {
  for (const id of ids) {
    const it = S.items.find((x) => x.id === id);
    const cell = $("grid").querySelector(`.cell[data-id="${id}"]`);
    if (it && cell) cell.replaceWith(thumb(it));
  }
  const cur = S.items.find((x) => x.id === S.cur);
  if (cur && ids.includes(cur.id)) {
    const c = $("card");
    c.innerHTML = infoHtml(cur);
    wireInfo(c, cur);
    if (V.open) showInViewer(false, true);
  }
}

function showCard(it) {
  const c = $("card");
  if (!it) { c.innerHTML = `<div class="empty">${t("nothing")}</div>`; return; }
  c.innerHTML = infoHtml(it);
  wireInfo(c, it);
}

// ---- editing: rating, tags, deleting, moving, sending to ComfyUI ---------------------------------------------------
const picsWord = (n) => LANG === "ru" ? plural(n, [t("pics1"), t("pics2"), t("pics5")]) : (n === 1 ? t("pics1") : t("pics2"));
const targets = () => (S.sel.size ? [...S.sel] : S.cur != null ? [S.cur] : []);
const post = async (path, body) => {
  const r = await fetch(`${API}/${path}`, { method: "POST", body: JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || r.status);
  return j;
};
function toast(text, bad = false) {
  const d = el("div", "toast" + (bad ? " bad" : ""), esc(text));
  document.body.append(d);
  setTimeout(() => d.remove(), bad ? 6000 : 2500);
}
const fail = (e) => toast(t(e.message) !== e.message ? t(e.message) : String(e.message), true);

async function setRating(ids, rating) {
  try { await post("rate", { ids, rating }); } catch (e) { return fail(e); }
  for (const it of S.items) if (ids.includes(it.id)) it.rating = rating;
  refreshItems(ids);
  if (S.rating || S.sort === "rating") loadFacets();
}

async function editTags(ids, add, remove) {
  try { S.allTags = await post("tags", { ids, add, remove }); } catch (e) { return fail(e); }
  for (const it of S.items) if (ids.includes(it.id)) {
    it.tags = [...new Set([...(it.tags || []).filter((x) => !remove.includes(x)), ...add])].sort((a, b) => a.localeCompare(b));
  }
  refreshItems(ids);
  loadFacets();
}

/** An input in place of the "+ tag" chip; Enter adds, Esc cancels. The known tags are offered as you type. */
async function tagInput(line, done) {
  if (line.querySelector("input")) return;
  S.allTags ??= await get("tags");
  const list = el("datalist"); list.id = "tag-list-" + Math.random().toString(36).slice(2);
  list.append(...S.allTags.map(([n]) => new Option(n)));
  const inp = el("input", "inp taginp"); inp.placeholder = t("tagPh"); inp.setAttribute("list", list.id);
  line.querySelector(".addtag").replaceWith(inp);
  line.append(list);
  inp.focus();
  inp.onkeydown = (e) => {
    e.stopPropagation();
    if (e.key === "Enter" && inp.value.trim()) done(inp.value.trim());
    if (e.key === "Escape") refreshItems([S.cur]);
  };
}

function deleteDialog(ids) {
  if (!ids.length) return;
  const body = el("div", "dlg-b", `<div>${esc(t("delText", { n: num(ids.length), pics: picsWord(ids.length) }))}</div>`);
  const go = el("button", "btn dang", icl("trash", t("del")));
  const line = el("div", "addline"); line.style.justifyContent = "flex-end"; line.append(go);
  body.append(line);
  const close = dialog(t("delTitle"), body);
  go.focus();
  go.onclick = async () => {
    close();
    let r;
    try { r = await post("delete", { ids }); } catch (e) { return fail(e); }
    removeItems(r.done);
    toast(t("deleted", { n: num(r.done.length) }));
    if (r.errors.length) toast(t("errors", { v: r.errors.map((x) => x[0]).join(", ") }), true);
  };
}

function removeItems(ids) {
  if (!ids.length) return;
  const i = S.items.findIndex((x) => ids.includes(x.id));
  S.items = S.items.filter((x) => !ids.includes(x.id));
  S.total -= ids.length;
  for (const id of ids) { $("grid").querySelector(`.cell[data-id="${id}"]`)?.remove(); S.sel.delete(id); }
  $("st-shown").textContent = t("shown", { n: num(S.items.length), total: num(S.total) });
  const next = S.items[Math.min(i, S.items.length - 1)];
  if (V.open) { if (next) { V.i = S.items.indexOf(next); showInViewer(false); } else closeViewer(); }
  if (next) pick(next.id); else showCard(null);
  loadFolders(); loadFacets();
}

async function moveDialog(ids) {
  if (!ids.length) return;
  const roots = await get("folders");
  const body = el("div", "dlg-b", `<div>${esc(t("moveText", { n: num(ids.length), pics: picsWord(ids.length) }))}</div>`);
  // the same tree as in the left panel, starting with what is open there (opening here is not remembered)
  const tree = el("div", "tree pickfolder"), open = new Set(opened);
  const first = S.locs[0] ?? (roots[0] ? { root: roots[0].path, folder: "" } : null);
  let dest = first ? { ...first } : null;
  const redraw = () => {
    const keep = tree.scrollTop;
    tree.replaceChildren();
    drawTree(tree, roots, { open, on: (root, folder) => dest?.root === root && dest?.folder === folder,
      pick: (root, folder) => { dest = { root, folder }; redraw(); }, redraw });
    tree.scrollTop = keep;
  };
  redraw();
  const sub = el("input", "inp"); sub.placeholder = t("newFolder");
  const go = el("button", "btn pri", t("move"));
  const line = el("div", "addline"); line.append(sub, go);
  body.append(tree, line);
  const close = dialog(t("moveTitle"), body);
  go.onclick = async () => {
    if (!dest) return;
    const folder = [dest.folder, sub.value.trim().replace(/[\\/]+/g, "/").replace(/^\/|\/$/g, "")].filter(Boolean).join("/");
    close();
    let r;
    try { r = await post("move", { ids, root: dest.root, folder }); } catch (e) { return fail(e); }
    toast(t("moved", { n: num(r.done.length) }));
    if (r.errors.length) toast(t("errors", { v: r.errors.map((x) => x[0]).join(", ") }), true);
    if (S.locs.length) removeItems(r.done); else { reload(); loadFolders(); }
  };
}

function rateDialog(ids) {
  if (!ids.length) return;
  const body = el("div", "dlg-b");
  const st = el("div", "stars big ico", starRow(0) + ` <a class="muted clear0">${t("clear")}</a>`);
  body.append(st);
  const close = dialog(t("rateTitle", { n: num(ids.length), pics: picsWord(ids.length) }), body);
  st.onclick = (e) => { const r = starOf(e) || (e.target.classList.contains("clear0") ? 0 : null); if (r != null) { close(); setRating(ids, r); } };
}

async function tagsDialog(ids) {
  if (!ids.length) return;
  S.allTags = await get("tags");
  const have = new Map();
  for (const it of S.items) if (ids.includes(it.id)) for (const x of it.tags || []) have.set(x, (have.get(x) || 0) + 1);
  const body = el("div", "dlg-b");
  const cur = el("div", "chips");
  const draw = () => cur.replaceChildren(...[...have.keys()].sort().map((x) => {
    const c = el("span", "", tagHtml(x, ` <b style="color:#999;font-weight:400">${have.get(x)}</b> <i class="x">✕</i>`)).firstChild;
    c.title = t("tagsRemove");
    c.onclick = async () => { await editTags(ids, [], [x]); have.delete(x); draw(); };
    return c;
  }));
  draw();
  const list = el("datalist"); list.id = "tags-all"; list.append(...S.allTags.map(([n]) => new Option(n)));
  const inp = el("input", "inp"); inp.placeholder = t("tagPh"); inp.setAttribute("list", "tags-all");
  const go = el("button", "btn pri", t("tagsAdd"));
  go.onclick = async () => { const n = inp.value.trim(); if (!n) return; await editTags(ids, [n], []); have.set(n, ids.length); inp.value = ""; draw(); };
  inp.onkeydown = (e) => { if (e.key === "Enter") go.click(); };
  const line = el("div", "addline"); line.append(inp, go);
  body.append(cur, line, list);
  dialog(t("tagsTitle", { n: num(ids.length), pics: picsWord(ids.length) }), body);
  inp.focus();
}

async function manageTags() {
  const body = el("div", "dlg-b");
  const box = el("div", "roots");
  const draw = (tags) => box.replaceChildren(...tags.map(([name, n]) => {
    const row = el("div", "root", `<div>${tagHtml(name)} <span class="muted">${num(n)}</span></div>`);
    const ren = el("button", "btn", t("rename"));
    ren.onclick = () => {
      const inp = el("input", "inp"); inp.value = name; inp.placeholder = t("renamePh");
      ren.replaceWith(inp); inp.focus(); inp.select();
      inp.onkeydown = async (e) => {
        if (e.key === "Escape") { e.stopPropagation(); draw(tags); }
        if (e.key === "Enter" && inp.value.trim() && inp.value.trim() !== name) {
          try { draw(S.allTags = await post("tag", { rename: name, to: inp.value.trim() })); } catch (er) { fail(er); }
          reload();
        }
      };
    };
    const del = el("button", "btn dang", t("tagDelete"));
    del.onclick = async () => { draw(S.allTags = await post("tag", { delete: name })); reload(); };
    const btns = el("div", "addline"); btns.append(ren, del); row.append(btns);
    return row;
  }));
  draw(S.allTags = await get("tags"));
  body.append(box);
  dialog(t("tagsManage"), body);
}

async function sendToComfy(id, kind) {
  try { await post("send", { id, kind }); toast(t("sentWf")); } catch (e) { fail(e); }
}

// ---- dialogs -----------------------------------------------------------------------------------------------------
function dialog(title, body, wide = false) {
  const back = el("div", "modal");
  const box = el("div", "dlg" + (wide ? " wide" : ""), `<div class="dlg-h"><b>${esc(title)}</b><button class="btn x" title="${t("close")}">${ic("close")}</button></div>`);
  box.append(body);
  back.append(box);
  const close = () => { back.remove(); document.removeEventListener("keydown", key, true); };
  const key = (e) => { if (e.key === "Escape") { e.stopPropagation(); close(); } };
  back.onclick = (e) => { if (e.target === back) close(); };
  box.querySelector(".x").onclick = close;
  document.addEventListener("keydown", key, true);
  document.body.append(back);
  return close;
}

function folderDialog(roots) {
  const body = el("div", "dlg-b");
  const list = el("div", "roots");
  const draw = (rs) => {
    list.replaceChildren(...rs.map((r) => {
      const row = el("div", "root", `<div><b>${esc(r.label)}</b><div class="muted">${esc(r.path)}${r.builtin ? `${SEP}${t("builtin")}` : ""}</div></div>`);
      if (!r.builtin) {
        const b = el("button", "btn", t("remove"));
        b.onclick = async () => draw(await send({ remove: r.path }));
        row.append(b);
      }
      return row;
    }));
  };
  const err = el("div", "err");
  const send = async (payload) => {
    const r = await fetch(`${API}/roots`, { method: "POST", body: JSON.stringify(payload) });
    const b = await r.json();
    err.textContent = r.ok ? "" : b.error === "not_folder" ? t("notFolder") : t(b.error);
    if (r.ok) { loadFolders(); poll(); return b; }
    return roots;
  };
  // choosing a folder: a browser of the folders of this computer (the server lists them); the path can still be typed
  const pick = el("div", "fpick");
  const bar = el("div", "fbar");
  const up = el("button", "btn fup", ic("up")); up.title = t("upFolder");
  const inp = el("input", "inp"); inp.placeholder = t("pathPh");
  bar.append(up, inp);
  const places = el("div", "fplaces");
  const dirs = el("div", "tree fdirs");
  const go = el("button", "btn pri", icl("folderplus", t("addThis")));
  let cur = null;
  // a folder already in the gallery, inside one or holding one cannot be added (its pictures would be indexed twice)
  const key = (x) => String(x).toLowerCase().replace(/\\/g, "/").replace(/\/+$/, "");
  const isRoot = (path) => roots.some((r) => key(r.path) === key(path));
  const why = (path) => {
    const k = key(path);
    if (!k) return "";
    for (const r of roots) {
      const rk = key(r.path);
      if (k === rk) return t("inGallery");
      if (k.startsWith(rk + "/")) return t("insideRoot", { v: r.label });
      if (rk.startsWith(k + "/")) return t("holdsRoot", { v: r.label });
    }
    return "";
  };
  const open = async (path) => {
    let r, b;
    try { r = await fetch(`${API}/browse?path=${encodeURIComponent(path)}`); b = await r.json(); } catch (e) { err.textContent = String(e); return; }
    if (!r.ok) { err.textContent = b.error === "not_folder" ? t("notFolder") : b.error === "no_access" ? t("noAccess") : t(b.error); return; }
    err.textContent = ""; cur = b;
    inp.value = b.path; up.disabled = b.parent == null;
    places.innerHTML = b.places.map((p) => `<span class="chip" data-p="${esc(p.path)}">${ic(p.drive ? "drive" : p.name === "home" ? "home" : "folder")}` +
      `${esc(p.drive ? p.path : t(p.name === "home" ? "homeFolder" : "outputFolder"))}</span>`).join("");
    dirs.replaceChildren(...(b.dirs.length ? b.dirs.map((d) => {
      const row = el("div", "", `<span class="tn">${ic(b.path ? "folder" : "drive")}${esc(d.name)}</span>${isRoot(d.path) ? `<span class="muted">${t("inGallery")}</span>` : ""}`);
      row.onclick = () => open(d.path);
      return row;
    }) : [el("div", "muted fempty", t("noSubfolders"))]));
    dirs.scrollTop = 0;
    const no = why(b.path);
    go.disabled = !b.path || !!no; note.textContent = no;
  };
  places.onclick = (e) => { const c = e.target.closest("[data-p]"); if (c) open(c.dataset.p); };
  up.onclick = () => { if (cur && cur.parent != null) open(cur.parent); };
  inp.onkeydown = (e) => { if (e.key === "Enter") open(inp.value.trim()); };
  go.onclick = async () => {
    if (!cur?.path) return;
    roots = await send({ path: cur.path }); draw(roots);
    if (!err.textContent) open(cur.path);
  };
  const note = el("span", "muted");
  pick.append(el("div", "h", `<span>${t("addFolderH")}</span>`), places, bar, dirs, el("div", "fgo"));
  pick.lastChild.append(note, go);
  body.append(list, pick, err);
  draw(roots);
  dialog(t("foldersTitle"), body, true);
  open("");
}

/** What is written in the file. The dialog opens at once ("loading…"); a missing file or a server error is said in it. */
async function readMeta(id) {
  const r = await fetch(`${API}/meta/${id}`);
  if (r.status === 404) throw new Error(t("gone"));
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}
async function openMeta(it) {
  const pre = el("pre", "raw", esc(t("loading"))), wrap = el("div", "dlg-b");
  wrap.append(pre);
  const close = dialog(`${t("fileData")} — ${it.name}`, wrap, true);
  try { const m = await readMeta(it.id); wrap.replaceWith(metaBody(m)); }
  catch (e) { pre.className = "raw err"; pre.textContent = `${t("metaFailed")}: ${e.message}`; }
  return close;
}
function metaBody(m) {
  const pretty = (v) => (v == null ? t("noData") : typeof v === "string" ? v : JSON.stringify(v, null, 2));
  const body = el("div", "dlg-b");
  const tabs = el("div", "seg");
  const pre = el("pre", "raw");
  const parts = [["parameters", m.parameters || null], ["prompt", m.prompt], ["workflow", m.workflow]];
  parts.forEach(([name, v], i) => {
    const b = el("span", i ? "" : "on", name);
    b.onclick = () => { for (const x of tabs.children) x.classList.toggle("on", x === b); pre.textContent = pretty(v); };
    tabs.append(b);
  });
  pre.textContent = pretty(parts[0][1]);
  body.append(tabs, pre);
  return body;
}

// ---- viewer ------------------------------------------------------------------------------------------------------
const V = { open: false, i: 0, scale: 1, x: 0, y: 0, fit: true, keep: store.get("keepZoom", false), panel: store.get("viewerPanel", true), w: 0, h: 0 };

function openViewer(id) {
  V.i = S.items.findIndex((x) => x.id === id);
  if (V.i < 0) return;
  V.open = true;
  $("viewer").hidden = false;
  showInViewer(true);
}

function closeViewer() {
  V.open = false;
  $("viewer").hidden = true;
  const it = S.items[V.i];
  if (it) pick(it.id);
}

function showInViewer(first, panelOnly = false) {
  const it = S.items[V.i];
  if (!it) return;
  if (panelOnly) { const panel = $("v-panel"); panel.innerHTML = infoHtml(it); wireInfo(panel, it); $("v-rate").innerHTML = starsHtml(it.rating || 0); return; }
  if (S.cur !== it.id) pick(it.id);
  const img = $("v-img");
  img.onload = () => {
    V.w = img.naturalWidth; V.h = img.naturalHeight;
    if (first || !V.keep || V.fit) fitView(); else place();
  };
  img.onerror = () => { $("v-zoom").textContent = t("gone"); };
  img.src = `${API}/file/${it.id}`;
  $("v-mini-img").src = thumbUrl(it, 192);
  $("v-file").innerHTML = `<span>${esc(it.name)}</span><span>${fileLine(it)}</span>`;
  $("v-pos").textContent = t("of", { i: num(V.i + 1), n: num(S.total) });
  $("v-rate").innerHTML = starsHtml(it.rating || 0);
  const panel = $("v-panel");
  panel.hidden = !V.panel;
  panel.innerHTML = infoHtml(it);
  wireInfo(panel, it);
  $("v-info").classList.toggle("pri", V.panel);
  // the next pictures are loaded while paging, so the last loaded one is not the end
  if (V.i > S.items.length - 5) loadMore();
}

function stageBox() { return $("v-stage").getBoundingClientRect(); }
const BAR_TOP = 48, BAR_BOT = 34;          // the bars of the viewer: a fitted picture sits between them, not under them
function fitView() {
  const r = stageBox();
  V.fit = true;
  V.scale = Math.min((r.width - 40) / V.w, (r.height - BAR_TOP - BAR_BOT - 24) / V.h, 4);
  V.x = (r.width - V.w * V.scale) / 2; V.y = (r.height - V.h * V.scale) / 2;
  place();
}
function zoomTo(scale, cx, cy) {
  const r = stageBox();
  cx ??= r.width / 2; cy ??= r.height / 2;
  scale = Math.max(0.05, Math.min(16, scale));
  V.x = cx - (cx - V.x) * scale / V.scale; V.y = cy - (cy - V.y) * scale / V.scale;
  V.scale = scale; V.fit = false;
  place();
}
function place() {
  const img = $("v-img"), r = stageBox();
  const w = V.w * V.scale, h = V.h * V.scale;
  // a picture smaller than the window stays centred; a bigger one cannot be dragged out of it
  V.x = w <= r.width ? (r.width - w) / 2 : Math.min(0, Math.max(r.width - w, V.x));
  // vertically: centred between the bars; a taller picture can be moved until its edge reaches a bar
  const room = r.height - BAR_TOP - BAR_BOT;
  V.y = h <= room ? BAR_TOP + (room - h) / 2 : Math.min(BAR_TOP, Math.max(r.height - BAR_BOT - h, V.y));
  img.style.width = w + "px"; img.style.height = h + "px";
  img.style.transform = `translate(${V.x}px, ${V.y}px)`;
  img.style.imageRendering = V.scale >= 2 ? "pixelated" : "auto";
  $("v-zoom").textContent = "";
  $("v-fit").classList.toggle("pri", V.fit);
  vZoomUpdate?.();
  // minimap: shown while the picture does not fit
  const mini = $("v-mini"), big = w > r.width + 1 || h > r.height + 1;
  mini.hidden = !big;
  if (big) {
    const mw = 180, mh = Math.round(180 * V.h / V.w);
    mini.style.height = mh + "px";
    const fr = $("v-mini-frame");
    // the frame: the part of the picture seen between the bars
    const top = Math.max(0, (BAR_TOP - V.y) / h), bot = Math.min(1, (r.height - BAR_BOT - V.y) / h);
    fr.style.left = Math.max(0, -V.x / w * mw) + "px"; fr.style.top = (top * mh) + "px";
    fr.style.width = Math.min(mw, r.width / w * mw) + "px"; fr.style.height = Math.max(0, bot - top) * mh + "px";
  }
  setHint("v-hint", big ? t("hintZoom") : t("hintFit"));
}
/** The top bar of the viewer on a narrow window: when it has no room, buttons drop their names (the icon and the
    tooltip stay), the least needed first — the two "to workflow" buttons, then Tags and Parameters; on a very narrow
    window the title goes, then the zoom slider (the % list and − / + stay). */
const V_SHRINK = 4;
function fitViewerBar() {
  const bar = document.querySelector(".v-top");
  if (!bar.offsetParent) return;
  bar.classList.remove("shrink1", "shrink2", "shrink3", "shrink4");
  for (let k = 1; k <= V_SHRINK && bar.scrollWidth > bar.clientWidth + 1; k++) bar.classList.add("shrink" + k);
}

function step(d) {
  const n = V.i + d;
  if (n < 0 || n >= S.items.length) return;
  V.i = n;
  showInViewer(false);
}

function initViewer() {
  $("v-close").innerHTML = icl("close", t("close"));
  $("v-title").textContent = t("viewTitle");
  $("v-fit").textContent = t("fit");
  $("v-info").innerHTML = icl("info", t("info"));
  $("v-keep-l").textContent = t("keepZoom");
  const keep = $("v-keep");
  keep.checked = V.keep;
  keep.onchange = () => { V.keep = keep.checked; store.set("keepZoom", V.keep); };
  $("v-close").onclick = closeViewer;
  $("v-fit").onclick = fitView;
  const vz = $("v-zoomctl");
  vz.innerHTML = zoomHtml();
  vZoomUpdate = zoomControl(vz, { ...PIC_ZOOM, get: () => V.scale * 100, set: (p) => zoomTo(p / 100) });
  $("v-prev").onclick = () => step(-1);
  $("v-next").onclick = () => step(1);
  $("v-info").onclick = () => { V.panel = !V.panel; store.set("viewerPanel", V.panel); $("v-panel").hidden = !V.panel; $("v-info").classList.toggle("pri", V.panel);
    requestAnimationFrame(() => (V.fit ? fitView() : place())); };
  const stage = $("v-stage");
  // the top and bottom bars, the arrows and the minimap lie over the picture: what happens on them is not for the picture
  const onCtl = (e) => !!e.target.closest(".v-top, .v-bot, .v-nav, .v-mini, .v-zoom, .dd-menu");
  stage.addEventListener("wheel", (e) => {
    if (onCtl(e)) return;
    e.preventDefault();
    const r = stageBox();
    zoomTo(V.scale * Math.pow(1.0015, -e.deltaY), e.clientX - r.left, e.clientY - r.top);
  }, { passive: false });
  let drag = null;
  stage.addEventListener("pointerdown", (e) => { if (e.button === 0 && e.target === $("v-img")) { drag = { x: e.clientX - V.x, y: e.clientY - V.y }; stage.setPointerCapture(e.pointerId); stage.classList.add("drag"); } });
  stage.addEventListener("pointermove", (e) => { if (drag) { V.x = e.clientX - drag.x; V.y = e.clientY - drag.y; V.fit = false; place(); } });
  stage.addEventListener("pointerup", () => { drag = null; stage.classList.remove("drag"); });
  stage.addEventListener("dblclick", (e) => {
    if (onCtl(e)) return;
    const r = stageBox();
    if (V.fit) zoomTo(1, e.clientX - r.left, e.clientY - r.top); else fitView();
  });
  $("v-mini").addEventListener("pointerdown", (e) => {     // a click on the minimap brings that point to the centre
    const m = $("v-mini").getBoundingClientRect(), r = stageBox();
    const fx = (e.clientX - m.left) / m.width, fy = (e.clientY - m.top) / m.height;
    V.x = r.width / 2 - fx * V.w * V.scale; V.y = BAR_TOP + (r.height - BAR_TOP - BAR_BOT) / 2 - fy * V.h * V.scale; V.fit = false;
    place();
  });
  addEventListener("resize", () => { if (V.open) (V.fit ? fitView() : place()); });
}

// ---- compare two pictures --------------------------------------------------------------------------------------
const C = { a: null, b: null, mode: store.get("cmpMode", "slider"), hide: store.get("cmpHide", false), cut: 0.5,
  scale: 1, x: 0, y: 0, fit: true, w: 0, h: 0 };

function openCompare() {
  const ids = [...S.sel].slice(0, 2);
  if (ids.length !== 2) { toast(t("needTwo"), true); return; }
  [C.a, C.b] = ids.map((id) => S.items.find((x) => x.id === id));
  $("compare").hidden = false;
  $("c-title").textContent = t("cmpTitle");
  $("c-side").textContent = t("side"); $("c-slider").textContent = t("slider");
  setHint("c-hint", t("cmpHint")); requestAnimationFrame(() => foldHint($("c-hint")));
  $("c-hide-l").textContent = t("hideSame");
  $("c-hide").checked = C.hide;
  const ia = $("c-img-a"), ib = $("c-img-b");
  let n = 0;
  const ready = () => { if (++n < 2) return; C.w = ia.naturalWidth; C.h = ia.naturalHeight; C.wb = ib.naturalWidth; C.hb = ib.naturalHeight; cFit(); };
  ia.onload = ib.onload = ready;
  ia.src = `${API}/file/${C.a.id}`; ib.src = `${API}/file/${C.b.id}`;
  // the names are shown once, over the pictures; the table of parameters has only the A / B marks (the name in a tooltip)
  $("c-lab-a").innerHTML = `${abMark("a")} ${esc(C.a.name)}`; $("c-lab-b").innerHTML = `${abMark("b")} ${esc(C.b.name)}`;
  cMode(C.mode);
  cTable();
}
const closeCompare = () => { $("compare").hidden = true; };

function cMode(m) {
  C.mode = m; store.set("cmpMode", m);
  $("c-side").classList.toggle("on", m === "side"); $("c-slider").classList.toggle("on", m === "slider");
  $("c-stage").classList.toggle("sbs", m === "side");
  if (C.w) cFit();
}
// both pictures are drawn at the same scale and position; in "side" mode each half of the stage shows one
function cBox() { const r = $("c-stage").getBoundingClientRect(); return C.mode === "side" ? { width: r.width / 2 - 4, height: r.height } : r; }
function cFit() {
  const r = cBox();
  C.fit = true; C.scale = Math.min(r.width / C.w, r.height / C.h, 4);
  C.x = (r.width - C.w * C.scale) / 2; C.y = (r.height - C.h * C.scale) / 2;
  cPlace();
}
function cZoom(scale, cx, cy) {
  scale = Math.max(0.05, Math.min(16, scale));
  C.x = cx - (cx - C.x) * scale / C.scale; C.y = cy - (cy - C.y) * scale / C.scale; C.scale = scale; C.fit = false;
  cPlace();
}
function cPlace() {
  const r = cBox(), w = C.w * C.scale, h = C.h * C.scale;
  C.x = w <= r.width ? (r.width - w) / 2 : Math.min(0, Math.max(r.width - w, C.x));
  C.y = h <= r.height ? (r.height - h) / 2 : Math.min(0, Math.max(r.height - h, C.y));
  // B keeps its own proportions: it is fitted into the frame of A and centred in it
  const k = Math.min(C.w / C.wb, C.h / C.hb), wb = C.wb * k * C.scale, hb = C.hb * k * C.scale;
  const boxes = [["c-img-a", C.x, C.y, w, h], ["c-img-b", C.x + (w - wb) / 2 + (C.mode === "side" ? r.width + 8 : 0), C.y + (h - hb) / 2, wb, hb]];
  for (const [id, x, y, iw, ih] of boxes) {
    const img = $(id);
    img.style.width = iw + "px"; img.style.height = ih + "px";
    img.style.transform = `translate(${x}px, ${y}px)`;
    img.style.imageRendering = C.scale >= 2 ? "pixelated" : "auto";
  }
  const st = $("c-stage").getBoundingClientRect();
  // the slider stays on the picture: between its left and right edges (or the edges of the stage, when zoomed in)
  const lo = Math.max(0, C.x), hi = Math.min(st.width, C.x + w);
  const cut = Math.max(lo, Math.min(hi, C.cut * st.width));
  if (st.width) C.cut = cut / st.width;
  $("c-img-b").style.clipPath = C.mode === "slider" ? `inset(0 0 0 ${Math.max(0, cut - (C.x + (w - wb) / 2))}px)` : "none";
  $("c-handle").style.left = cut + "px";
  $("c-handle").hidden = C.mode !== "slider";
  $("c-fit").classList.toggle("pri", !!C.fit);
  cZoomUpdate?.();
}

// words of a prompt: the comma-separated parts; the parts only one picture has are marked
const parts = (s) => String(s ?? "").split(/,|\n/).map((x) => x.trim()).filter(Boolean);
function markDiff(a, b) {
  const other = new Set(parts(b).map((x) => x.toLowerCase()));
  return String(a ?? "").split(/(,|\n)/).map((p) => {
    const tr = p.trim();
    return tr && p !== "," && p !== "\n" && !other.has(tr.toLowerCase()) ? p.replace(tr, `<mark>${esc(tr)}</mark>`) : esc(p);
  }).join("");
}
function loraDiff(a, b) {
  const mb = new Map((b || []).map(([n, w]) => [n, w]));
  return (a || []).map(([n, w]) => (!mb.has(n) ? `<mark>${esc(n)} ×${w}</mark>` : mb.get(n) !== w ? `${esc(n)} <mark>×${w}</mark>` : `${esc(n)} ×${w}`)).join("<br>") || "—";
}
function cTable() {
  const A = C.a, B = C.b;
  const size = (it) => (it.gen_width ? `${it.gen_width}×${it.gen_height}` : null);
  const rows = [["positive", A.positive, B.positive, "prompt"], ["negative", A.negative, B.negative, "prompt"],
    ["seed", A.seed, B.seed], ["steps", A.steps, B.steps], ["cfg", cfgText(A.cfg), cfgText(B.cfg)], ["clip skip", A.clip_skip, B.clip_skip],
    ["sampler", A.sampler, B.sampler], ["scheduler", A.scheduler, B.scheduler], ["denoise", A.denoise, B.denoise],
    ["size", size(A), size(B)], ["model", A.model, B.model], ["lora", A.loras, B.loras, "lora"],
    [LANG === "ru" ? "файл" : "file", `${A.width}×${A.height}, ${A.fmt}`, `${B.width}×${B.height}, ${B.fmt}`]];
  const same = (x, y, kind) => kind === "lora" ? JSON.stringify(x || []) === JSON.stringify(y || []) : String(x ?? "") === String(y ?? "");
  const head = (it, col) => `<th title="${esc(it.name)}">${abMark(col.toLowerCase())}<span class="cmpsend" data-id="${it.id}">
    <button class="btn" data-k="image">${icl("send", t("toWfImage"))}</button><button class="btn" data-k="params" ${it.has_params ? "" : "disabled"}>${icl("send", t("toWfParams"))}</button></span></th>`;
  let html = `<table class="cmp"><tr><th>${t("param")}</th>${head(A, "A")}${head(B, "B")}</tr>`;
  for (const [name, x, y, kind] of rows) {
    const eq = same(x, y, kind);
    if (eq && C.hide) continue;
    const cell = (v, o) => kind === "prompt" ? markDiff(v, o) || "—" : kind === "lora" ? loraDiff(v, o) : esc(v ?? "—");
    html += `<tr class="${eq ? "" : "d"}"><td>${name}</td><td>${cell(x, y)}</td><td>${cell(y, x)}</td></tr>`;
  }
  $("c-table").innerHTML = html + "</table>";
  for (const sp of $("c-table").querySelectorAll(".cmpsend")) sp.onclick = (e) => { const k = e.target.closest("[data-k]")?.dataset.k; if (k) sendToComfy(+sp.dataset.id, k); };
}

function initCompare() {
  $("c-close").innerHTML = icl("close", t("close"));
  $("c-fit").textContent = t("fit");
  $("c-fit").onclick = () => { if (C.w) cFit(); };
  const cz = $("c-zoomctl");
  cz.innerHTML = zoomHtml();
  cZoomUpdate = zoomControl(cz, { ...PIC_ZOOM, get: () => (C.scale || 1) * 100,
    set: (p) => { if (!C.w) return; const r = cBox(); cZoom(p / 100, r.width / 2, r.height / 2); } });
  $("c-close").onclick = closeCompare;
  $("c-side").onclick = () => cMode("side");
  $("c-slider").onclick = () => cMode("slider");
  $("c-hide").onchange = () => { C.hide = $("c-hide").checked; store.set("cmpHide", C.hide); cTable(); };
  const stage = $("c-stage");
  stage.addEventListener("wheel", (e) => {
    e.preventDefault();
    const r = stage.getBoundingClientRect(), half = C.mode === "side" && e.clientX - r.left > r.width / 2 ? r.width / 2 + 4 : 0;
    cZoom(C.scale * Math.pow(1.0015, -e.deltaY), e.clientX - r.left - half, e.clientY - r.top);
  }, { passive: false });
  let drag = null;
  stage.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    stage.setPointerCapture(e.pointerId);
    drag = e.target.closest("#c-handle") ? { cut: true } : { x: e.clientX - C.x, y: e.clientY - C.y };
  });
  stage.addEventListener("pointermove", (e) => {
    if (!drag) return;
    if (drag.cut) { const r = stage.getBoundingClientRect(); C.cut = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)); }
    else { C.x = e.clientX - drag.x; C.y = e.clientY - drag.y; C.fit = false; }
    cPlace();
  });
  stage.addEventListener("pointerup", () => { drag = null; });
  stage.addEventListener("dblclick", (e) => { if (e.target.closest("#c-handle, .c-lab")) return; const r = stage.getBoundingClientRect(); if (C.fit) cZoom(1, e.clientX - r.left, e.clientY - r.top); else cFit(); });
  addEventListener("resize", () => { if (!$("compare").hidden && C.w) (C.fit ? cFit() : cPlace()); });
  // the height of the pictures against the table: a share of the window, remembered
  const box = $("compare"), split = $("c-split");
  const setH = (k) => { C.stageH = Math.max(.2, Math.min(.85, k)); box.style.setProperty("--c-stage-h", (C.stageH * 100).toFixed(1) + "%"); };
  setH(store.get("cmpH", .55));
  split.onpointerdown = (e) => {
    e.preventDefault(); split.setPointerCapture(e.pointerId); split.classList.add("on");
    const r = box.getBoundingClientRect(), top = $("c-stage").getBoundingClientRect().top;
    split.onpointermove = (m) => { setH((m.clientY - top) / (r.height - 24)); if (C.w) (C.fit ? cFit() : cPlace()); };
    split.onpointerup = () => { split.onpointermove = split.onpointerup = null; split.classList.remove("on"); store.set("cmpH", C.stageH); };
  };
  split.ondblclick = () => { setH(.55); store.set("cmpH", C.stageH); if (C.w) (C.fit ? cFit() : cPlace()); };
}

// ---- keyboard ----------------------------------------------------------------------------------------------------
function cols() {
  const g = $("grid"), first = g.children[0];
  if (!first) return 1;
  return Math.max(1, Math.round(g.clientWidth / (first.offsetWidth + parseFloat(getComputedStyle(g).columnGap || 10))));
}
document.addEventListener("keydown", (e) => {
  if (e.target.closest?.("input, select, textarea") || document.querySelector(".modal")) return;
  if (!$("compare").hidden) {
    // the same keys as in the viewer: + / − zoom by a step around the middle, Ctrl + 0 fits, Esc closes
    const mid = () => { const r = cBox(); return [r.width / 2, r.height / 2]; };
    if (e.key === "Escape") closeCompare();
    else if (!C.w) return;
    else if (e.key === "+" || e.key === "=") cZoom(C.scale * 1.25, ...mid());
    else if (e.key === "-") cZoom(C.scale / 1.25, ...mid());
    else if (e.key === "0" && e.ctrlKey) cFit();
    else return;
    e.preventDefault();
    return;
  }
  const ids0 = V.open ? [S.items[V.i]?.id].filter((x) => x != null) : targets();
  if (/^[0-5]$/.test(e.key) && !e.ctrlKey && !e.metaKey) { if (ids0.length) setRating(ids0, +e.key); e.preventDefault(); return; }
  if (e.key === "Delete") { deleteDialog(ids0); e.preventDefault(); return; }
  if (e.code === "KeyT") { tagsDialog(ids0); e.preventDefault(); return; }
  if (e.code === "KeyM" && !V.open) { moveDialog(ids0); e.preventDefault(); return; }
  if (e.code === "KeyC" && !V.open && !e.ctrlKey && !e.metaKey) { openCompare(); e.preventDefault(); return; }
  if (V.open) {
    if (e.key === "Escape") closeViewer();
    else if (e.key === "ArrowRight") step(1);
    else if (e.key === "ArrowLeft") step(-1);
    else if (e.code === "KeyI") $("v-info").click();
    else if (e.key === "0" && e.ctrlKey) fitView();
    else if (e.key === "+" || e.key === "=") zoomTo(V.scale * 1.25);
    else if (e.key === "-") zoomTo(V.scale / 1.25);
    else return;
    e.preventDefault();
    return;
  }
  const ids = S.items.map((x) => x.id), i = ids.indexOf(S.cur);
  const go = (n) => { n = Math.max(0, Math.min(ids.length - 1, n)); if (ids[n] == null) return; pick(ids[n]);
    $("grid").children[n]?.scrollIntoView({ block: "nearest" }); if (n > ids.length - cols() * 3) loadMore(); };
  if (e.key === "ArrowRight") go(i + 1);
  else if (e.key === "ArrowLeft") go(i - 1);
  else if (e.key === "ArrowDown") go(i + cols());
  else if (e.key === "ArrowUp") go(i - cols());
  else if (e.key === "Home") go(0);
  else if (e.key === "End") go(ids.length - 1);
  else if (e.key === "Enter" && S.cur != null) openViewer(S.cur);
  else if (e.key === "Escape") unpick();
  else return;
  e.preventDefault();
});

// ---- status ------------------------------------------------------------------------------------------------------
let pollTimer = null, lastFinished = null, lastAdded = 0, lastChanges = 0, lastAuto = 0;
// while the page is open and seen: a scan every N s catches pictures added outside ComfyUI runs.
// N comes with the status (Settings → Rigstools → PicoTeka → Auto refresh; 0 = off)
let AUTO_SCAN = 10000;
async function poll() {
  clearTimeout(pollTimer);
  let s;
  try { s = await get("status"); } catch { pollTimer = setTimeout(poll, 5000); return; }
  if (typeof s.auto_scan === "number") AUTO_SCAN = s.auto_scan * 1000;
  if (AUTO_SCAN && !s.running && document.visibilityState === "visible" && Date.now() - lastAuto > AUTO_SCAN) {
    lastAuto = Date.now();
    fetch(`${API}/scan`, { method: "POST" }).catch(() => {});   // on opening the page too: it may have been closed for hours
  }
  $("st-index").textContent = t("indexed", { n: num(s.indexed), pics: plural(s.indexed, ["картинка", "картинки", "картинок"]) });
  // the index state: a yellow pulsing dot while scanning, green when up to date, red pulsing on a problem
  const sc = $("st-scan");
  const missing = s.missing || [], failed = s.failed_files || [];
  let state = "ok", text = t("scanDone"), tip = "";
  if (s.running) {
    const pct = s.total ? Math.round(s.done / s.total * 100) : 0;
    state = "busy";
    text = `${esc(t("scanning", { root: s.root }))} <span class="bar"><i style="width:${pct}%"></i></span> ${pct}%`;
  } else if (s.error || missing.length || s.failed) {
    state = "bad";
    text = esc(s.error ? t("scanError") : missing.length ? t("rootMissing", { root: missing.map((m) => m.label).join(", ") })
      : t("unreadable", { n: num(s.failed) }));
    tip = [s.error, ...missing.map((m) => m.path), ...failed.map((f) => `${f.file} — ${f.code === "bad_file" ? t("badFile") : f.error}`),
      s.failed > failed.length ? "…" : ""].filter(Boolean).join("\n");
  } else text = esc(text);
  sc.className = state;
  sc.title = tip;
  sc.innerHTML = `<i class="sdot ${state}"></i><span>${text}</span>`;
  // running totals of the finished scans (s.last), not the counters of one scan: between two asks there may have been
  // several scans, and the next one may already be running with its counters reset
  const last = s.last || {};
  if (last.finished && last.finished !== lastFinished) {
    const first = lastFinished === null, added = last.added_total - lastAdded, changed = last.changes !== lastChanges;
    lastFinished = last.finished; lastAdded = last.added_total; lastChanges = last.changes;
    if (!first && changed) { loadFolders(); loadFacets(); sync(Math.max(0, added)); }
  }
  pollTimer = setTimeout(poll, s.running ? 1000 : 5000);
}

// ---- the picox.club mark and pixels ------------------------------------------------------------------------------
const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/** Now and then (every 30–60 s) the squares of the mark play: red swaps with green, yellow with blue, then they all
    shake and go back to their places. */
function startMark() {
  const box = $("mark"), [red, yellow, blue, green] = box.children, D = 12;
  const at = (el, x, y) => { el.style.transform = x || y ? `translate(${x}px, ${y}px)` : ""; };
  async function play() {
    if (!document.hidden) {
      // each step takes 0.6 s, then a pause of 1.5 s, so the play can be followed
      at(red, D, D); at(green, -D, -D);
      await wait(600 + 1500);
      at(yellow, -D, D); at(blue, D, -D);
      await wait(600 + 1500);
      box.classList.add("shake");
      const home = [[red, D, D], [yellow, -D, D], [blue, D, -D], [green, -D, -D]];
      for (let k = 0; k < 8; k++) {
        for (const [el, x, y] of home) at(el, x + (Math.random() * 4 - 2), y + (Math.random() * 4 - 2));
        await wait(90);
      }
      box.classList.remove("shake");
      for (const el of box.children) at(el, 0, 0);
    }
    setTimeout(play, 30000 + Math.random() * 30000);
  }
  if (!still) setTimeout(play, 30000 + Math.random() * 30000);
}

/** Where the thumbnails are, relative to `w0` (the pixels' box): the full rows and the filled part of the last row,
    each with a margin of 6 px. The grid is even, so the first cells and the count tell it all. */
function busyRects(w0) {
  const cs = $("grid").children, n = cs.length;
  if (!n || !cs[0].classList.contains("cell")) return [];
  const f = cs[0].getBoundingClientRect();
  let cols = 1;
  while (cols < n && cs[cols].offsetTop === cs[0].offsetTop) cols++;
  const sx = cols > 1 ? cs[1].getBoundingClientRect().left - f.left : f.width;
  const sy = n > cols ? cs[cols].getBoundingClientRect().top - f.top : f.height;
  const rows = Math.ceil(n / cols), last = n - (rows - 1) * cols, m = 6;
  const x0 = f.left - w0.left - m, y0 = f.top - w0.top - m, right = (k) => x0 + (k - 1) * sx + f.width + 2 * m;
  const out = [];
  if (rows > 1) out.push([x0, y0, right(cols), y0 + (rows - 2) * sy + f.height + 2 * m]);
  const ly = y0 + (rows - 1) * sy;
  out.push([x0, ly, right(last), ly + f.height + 2 * m]);
  return out;
}

/** Behind the grid, as on picox.club: rare pixels in the four colours of the mark slowly light up and fade out. */
function startPixels() {
  const cv = $("px"), ctx = cv.getContext("2d"), wrap = cv.parentElement;
  const colors = ["#ff5c7a", "#ffc857", "#4cc9f0", "#7bdc8c"], P = 22;
  let W = 0, H = 0, cols = 0, rows = 0, cells = [];
  const spawn = () => ({ x: Math.random() * cols | 0, y: Math.random() * rows | 0, c: colors[Math.random() * 4 | 0],
    t: Math.random() * Math.PI * 2, s: 0.004 + Math.random() * 0.01 });
  const resize = () => {
    const d = devicePixelRatio || 1;
    W = wrap.clientWidth; H = wrap.clientHeight;
    cv.width = W * d; cv.height = H * d; ctx.setTransform(d, 0, 0, d, 0, 0);
    cols = Math.ceil(W / P); rows = Math.ceil(H / P);
    cells = Array.from({ length: Math.round(cols * rows * 0.035) }, spawn);
  };
  const frame = () => {
    if (!document.hidden && $("viewer").hidden && $("compare").hidden) {
      ctx.clearRect(0, 0, W, H);
      // only on the free area: not on the thumbnails and the gaps between them, but on the free cells of the last row
      const busy = busyRects(wrap.getBoundingClientRect());
      for (const p of cells) {
        p.t += p.s;
        if (p.t > Math.PI * 2) Object.assign(p, spawn(), { t: 0 });
        const px = p.x * P, py = p.y * P;
        if (busy.some(([x0, y0, x1, y1]) => px + P > x0 && px < x1 && py + P > y0 && py < y1)) continue;
        ctx.globalAlpha = Math.max(0, Math.sin(p.t)) * 0.35;
        ctx.fillStyle = p.c;
        ctx.fillRect(p.x * P + 4, p.y * P + 4, P - 8, P - 8);
      }
    }
    if (!still) requestAnimationFrame(frame);
  };
  new ResizeObserver(resize).observe(wrap);
  resize(); frame();
}

// ---- start -------------------------------------------------------------------------------------------------------
async function init() {
  try {
    const loc = await (await fetch("/api/settings/Comfy.Locale")).json();
    if (String(loc || "").toLowerCase().startsWith("ru")) LANG = "ru";
  } catch { /* English */ }
  document.documentElement.lang = LANG;
  $("gh").title = t("github");
  startMark(); startPixels();
  document.title = t("title");
  for (const e of document.querySelectorAll("[data-t]")) e.textContent = t(e.dataset.t);
  $("q").placeholder = t("search");
  $("rescan").innerHTML = icl("rescan", t("rescan"));
  document.querySelector(".search svg").outerHTML = ic("search");
  const qc = $("q-clear");                      // our clear cross (the browser one is bright blue)
  qc.innerHTML = ic("close"); qc.title = t("clear");
  $("q").addEventListener("input", () => { qc.hidden = !$("q").value; });
  qc.onclick = () => { $("q").value = ""; qc.hidden = true; S.q = ""; reload(); $("q").focus(); };
  initSort();
  initZoom();
  addEventListener("resize", () => sharpen());
  initSplits();
  let timer;
  $("q").oninput = () => { clearTimeout(timer); timer = setTimeout(() => { S.q = $("q").value.trim(); reload(); }, 300); };
  for (const id of ["from", "to"]) {
    const inp = $(id), box = inp.closest(".date");
    box.querySelector("svg").outerHTML = ic("calendar");
    const mark = () => box.classList.toggle("blank", !inp.value);
    mark();
    inp.addEventListener("click", () => { try { inp.showPicker(); } catch { /* old browser: its own button */ } });
    inp.onchange = () => { mark(); S[id] = inp.value; reload(); };
  }
  $("rating-clear").onclick = () => { S.rating = 0; reload(); };
  $("date-clear").onclick = () => { S.from = S.to = ""; $("from").value = $("to").value = ""; for (const b of document.querySelectorAll(".date")) b.classList.add("blank"); reload(); };
  $("rescan").onclick = async () => { lastAuto = Date.now(); await fetch(`${API}/scan`, { method: "POST" }); poll(); };
  // back to the tab after a while: scan now, not at the next tick
  document.addEventListener("visibilitychange", () => {
    if (AUTO_SCAN && document.visibilityState === "visible" && Date.now() - lastAuto > AUTO_SCAN) { lastAuto = 0; poll(); }
  });
  new IntersectionObserver((e) => { if (e[0].isIntersecting) loadMore(); }, { root: $("main"), rootMargin: "400px" }).observe($("sentinel"));
  $("fresh").onclick = () => goToNew();
  // a click on the empty space of the grid (not on a picture or the note): nothing picked
  $("main").addEventListener("click", (e) => { if (!e.target.closest(".cell, .fresh")) unpick(); });
  $("main").addEventListener("scroll", () => { if (S.unseen.size || S.held.size) requestAnimationFrame(onGridScroll); }, { passive: true });
  for (const [id, key, fn] of [["b-rate", "rate", () => rateDialog(targets())], ["b-tags", "tags", () => tagsDialog(targets())],
    ["b-move", "move", () => moveDialog(targets())], ["b-del", "del", () => deleteDialog(targets())], ["b-compare", "compare", openCompare]]) {
    $(id).innerHTML = icl({ rate: "star", tags: "hash", move: "move", del: "trash", compare: "swap" }[key], t(key));
    $(id).onclick = fn;
  }
  $("b-compare").disabled = true;
  $("v-rate").onclick = (e) => { const it = S.items[V.i]; const r = starOf(e); if (it && r) setRating([it.id], r === it.rating ? 0 : r); };
  $("v-tags").innerHTML = icl("hash", t("tags")); $("v-tags").onclick = () => tagsDialog([S.items[V.i]?.id].filter((x) => x != null));
  $("v-del").innerHTML = ic("trash"); $("v-del").title = t("del"); $("v-del").onclick = () => deleteDialog([S.items[V.i]?.id].filter((x) => x != null));
  // with names: an arrow; icons only (narrow window): a picture and sliders, so the two buttons differ
  const alt = (name) => ic(name).replace('class="ic"', 'class="ic alt"');
  $("v-img-wf").innerHTML = icl("send", t("toWfImage")) + alt("image"); $("v-img-wf").onclick = () => sendToComfy(S.items[V.i].id, "image");
  $("v-par-wf").innerHTML = icl("send", t("toWfParams")) + alt("sliders"); $("v-par-wf").onclick = () => sendToComfy(S.items[V.i].id, "params");
  // the names in tooltips too: on a narrow window the buttons may show only their icons (see fitViewerBar)
  for (const [id, k] of [["v-img-wf", "toWfImage"], ["v-par-wf", "toWfParams"], ["v-tags", "tags"], ["v-info", "info"]]) $(id).title = t(k);
  new ResizeObserver(fitViewerBar).observe(document.querySelector(".v-top"));
  initCompare();
  initViewer();
  showCard(null);
  await loadFolders();
  reload();
  await fetch(`${API}/scan`, { method: "POST" });      // pick up what was saved since the last scan
  poll();
}
init();
