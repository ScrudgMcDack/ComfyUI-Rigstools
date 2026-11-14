# Changelog

<p align="center"><b>English</b> · <a href="CHANGELOG.ru.md">Русский</a></p>

All notable changes to Rigstools. Versions follow [Semantic Versioning](https://semver.org/).

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

[1.1.0]: https://github.com/ScrudgMcDack/ComfyUI-Rigstools/releases/tag/v1.1.0
[1.0.0]: https://github.com/ScrudgMcDack/ComfyUI-Rigstools/releases/tag/v1.0.0
