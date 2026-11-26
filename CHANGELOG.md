# Changelog

<p align="center"><b>English</b> · <a href="CHANGELOG.ru.md">Русский</a></p>

All notable changes to Rigstools. Versions follow [Semantic Versioning](https://semver.org/).

## [2.1.0] — 2026-11-26
### Added
- PicoTeka: **To Civitai** — one Civitai post of the selected pictures, in the order they were selected (drag to
  reorder, ✕ to take out; the first is the cover): title, description, a draft by default (or published at once), with
  or without the ComfyUI workflow in the uploaded copy; warnings on the thumbnails, progress on them, the post link.
  The window can be hidden to a progress bar on the status bar while the pictures go up. Posted pictures get a
  **CIVITAI** chip (grey — in an unpublished draft, blue — published on civitai.com, red — a post rated R, X or XXX
  (adult content) is available on civitai.red, and the link goes there too) that lists their posts (the picture or the
  whole post can be deleted on Civitai from there; what is deleted on the site is forgotten), and the Civitai rating
  (PG…XXX) once Civitai has checked them. Tools and Techniques of the pictures (ComfyUI; workflow, txt2img, img2img by
  default, the choice is kept) are set on Civitai right after the post is made. Civitai finds the models and LoRA in
  the pictures' data itself. Pictures over 10 MB (the limit of Civitai's MCP) go, the first that fits: PNG compressed
  harder without loss (oxipng, a new dependency), WebP without loss, JPEG; the thumbnails say which. From this
  computer only; off until Settings → Rigstools → Civitai → **Allow posting from PicoTeka to Civitai** is on (off,
  nothing is sent to Civitai).
- PicoTeka → To Civitai. Big pictures (10 MB+) are processed one by one as soon as the form opens. While a picture is
  compressed, its thumbnail shows an animation: a yellow ring squeezes a blue circle. After processing, the thumbnails
  show the format each picture will be posted to Civitai in. The send button “waits” until everything is ready. A
  status line at the bottom of the window shows the preparation, “your turn”, the steps of sending and the post link
  with a reminder about moderation.
- Settings → Rigstools → Civitai → **API key**: a write-only field — the key is checked on Civitai and kept by the
  ComfyUI server, never in the ComfyUI settings and never sent back to a page; the `CIVITAI_API_KEY` environment
  variable wins.

### Changed
- PicoTeka: the card has **To Civitai** (or, with posting off, a wide **File data**) in place of **Delete** (deleting stays on the top bar, in the viewer and on the
  Delete key). On a narrow window the buttons of the top bar and of the comparison drop their names, as the
  viewer's do (Compare keeps the count as a small number at its icon); Fit has an icon.
- PicoTeka: tags are set and taken off in a drop-down list with search, opened with the “**+ tag**” chip (in the
  viewer, on the top bar and with the T hotkey). Several tags can be chosen at once; “–” means the tag is on some of
  the selected pictures only (“k of n” on the right). A new tag is made right from the search.

## [2.0.1] — 2026-11-21
### Added
- PicoTeka: **Shift + Delete** (or Shift + click on a Delete button) deletes pictures permanently, past the recycle
  bin, after a warning; Cancel is in focus there, so a stray Enter deletes nothing.

### Changed
- PicoTeka: the delete dialog has a **Cancel** button and speaks of the system recycle bin (not only Windows); every
  Delete button has a red border; File data has a green (i).

### Fixed
- README banner: the names stand symmetric to the alembic; the Comfy Registry and ComfyUI-Manager get a banner
  of their own (21:9).
- PicoTeka: Fit, Parameters, Side by side / Slider and the tabs of File data no longer grow wider when turned on, so
  the buttons next to them do not shift.

## [2.0.0] — 2026-11-21
### Added
- **PicoTeka** — a fast and simple gallery for the pictures you generate, opened by a button on the ComfyUI top bar
  (in its own browser tab): a folder tree (the output folder and any folders you add, chosen in a folder browser;
  Ctrl + click shows several at once), search by prompt and file name, filters by model, LoRA, sampler, tag, rating and
  date, a card with all the parameters.
- PicoTeka: the index keeps itself up to date — it looks at the folders after every finished run, wherever the picture
  was saved, and the open page looks by itself every few seconds for pictures added outside ComfyUI. New pictures take
  their places in the grid without a reload and are highlighted for a moment; the grid does not jump under you —
  pictures that would shift the rows in front of you wait behind a **New pictures: N ↑** bar.
- PicoTeka: **tags** with automatic colours (rename, merge, delete), **rating** 0–5, **delete** to the recycle bin
  (tags and rating are kept 30 days) and **move** to another folder — for one picture or for a selection (Ctrl + click,
  Shift + click; Esc or a click on the empty space unpicks); keys for all of it.
- PicoTeka: a full-screen **viewer** with zoom, a minimap and the parameters panel, and a **comparison** of two
  pictures — side by side or with a slider, the names marked A and B, and a table of their parameters with the
  differences highlighted. Both have the same keys (+ / − zoom, Ctrl + 0 fit) and their mouse and key hints behind a
  **?** sign.
- PicoTeka → workflow: **Picture to workflow** (into Load image with parameters / with metadata), **Parameters to
  workflow** and **Open workflow**, sent to the ComfyUI tab used last; a list to choose the node when there are
  several, an offer to add one when there is none.
- **Generation parameters** — a new node that holds parameters without a picture (filled from PicoTeka), with the
  same panel as the loaders and the same outputs as Parameters extractor.
- Settings **Rigstools → PicoTeka**: use the gallery (on by default; off — no button and no indexing), auto refresh of
  the open gallery (10 s by default; 30 s, 60 s or off) and allow deleting and moving files when the gallery is opened
  from another computer (off by default).

### Changed
- New dependency: `send2trash` (for deleting to the recycle bin).

### Documentation
- README rewritten: a banner, why Rigstools exists, a "What's inside" overview, the PicoTeka section with new
  screenshots, the settings as a list; Nodes 2.0 support is planned for one of the next versions.

## [1.1.0] — 2026-11-14
### Added
- **Color correction — auto mode:** a new `mode` switch (manual / auto). In auto mode the node measures every picture
  and chooses the strengths of white balance, levels and vibrance and a small exposure correction itself; the three
  sliders are greyed out meanwhile. With Debug on, the measured values and the chosen strengths go to the console.

### Changed
- Color correction: `mode` is the first setting of the node. Workflows saved with 1.0.0 open in manual mode with all
  values in place.
- Save image: the Preference switch (File / Graph / Input) uses the same font, height and corners as the fields of the
  block, its right edge is aligned with them, and its three cells have the same width.

### Documentation
- README: a Nodes 2.0 section — the new node look is not supported yet, support is planned for the next major release.
- README: a picture of Color correction in auto mode, new screenshots of the loader and Save image.

## [1.0.0] — 2026-11-12
First public version.
- **Load image with metadata**, **Load image with parameters**, **Load image from folder** — load pictures (PNG, JPEG,
  WebP) with their generation data; the parameters as separate outputs, shown and editable right under the picture.
- **Metadata extractor**, **Parameters extractor** — split the metadata and the A1111-style parameters into outputs.
- **LoRA hashes for Image Saver** — the `additional_hashes` string for Image Saver from a LoRA stack.
- **Save image** — saves pictures with their generation data collected from the graph by itself; Civitai-compatible
  parameters and hashes, a preview of what will be written, the Preference switch (File / Graph / Input).
- **Color correction** — automatic colour correction without neural networks: white balance, levels, vibrance,
  matching to a reference, manual adjustments, a histogram.
- Output marks and output tooltips; English and Russian UI; a Debug setting for the console log.

[2.1.0]: https://github.com/ScrudgMcDack/ComfyUI-Rigstools/releases/tag/v2.1.0
[2.0.1]: https://github.com/ScrudgMcDack/ComfyUI-Rigstools/releases/tag/v2.0.1
[2.0.0]: https://github.com/ScrudgMcDack/ComfyUI-Rigstools/releases/tag/v2.0.0
[1.1.0]: https://github.com/ScrudgMcDack/ComfyUI-Rigstools/releases/tag/v1.1.0
[1.0.0]: https://github.com/ScrudgMcDack/ComfyUI-Rigstools/releases/tag/v1.0.0
