# zensical-pdf

Generate customer-ready PDF deliverables from [Zensical](https://zensical.com) and MkDocs-style documentation projects.

`zensical-pdf` reads your existing Markdown source, resolves navigation order, aggregates pages, converts to [Typst](https://typst.app) via [Pandoc](https://pandoc.org), and compiles the final PDF — without touching your source files.

---

## Documentation

📚 **[View Full Documentation](docs/index.md)**

- **[Quick Start](docs/quickstart.md)** — Get started in 5 minutes
- **[Complete Guide](docs/guide.md)** — Comprehensive reference, configuration, examples
- **[Contributing Guide](docs/contributing.md)** — Development setup, testing, pull requests

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | ≥ 3.10 | [python.org](https://python.org) |
| Pandoc | ≥ 3.1.2 | [pandoc.org/installing](https://pandoc.org/installing.html) |
| Typst | any | [typst.app](https://typst.app) |

---

## Installation

```bash
pip install zensical-pdf
```

Or install from source (editable, with dev dependencies):

```bash
git clone https://github.com/your-org/zensical-pdf
cd zensical-pdf
pip install -e ".[dev]"
```

---

## Quick start

```bash
# 1. Check your environment
zensical-pdf doctor

# 2. Preview which pages will be included and in what order
zensical-pdf inspect-nav

# 3. Inspect the aggregated Markdown without building a PDF
zensical-pdf aggregate

# 4. Build the PDF
zensical-pdf build
```

All commands accept `--project-dir <path>` to point at a documentation project other than the current directory:

```bash
zensical-pdf build --project-dir /path/to/my-docs
```

---

## Configuration

Place a `zensical-pdf.toml` file in your documentation project root to customise each project independently:

```toml
[project]
title = "Enterprise Upgrade Guide"
subtitle = "Customer-ready technical documentation"
author = "Joel McCune"
version = "1.0.0"

[paths]
docs_dir = "docs"
output = "dist/documentation.pdf"

[pdf]
normalize_headings = true
include_toc = true
number_sections = false
missing_asset_policy = "warn"
```

### Configuration priority

Settings are resolved in this order, with earlier entries taking precedence:

1. CLI arguments (`--output`, `--permissive`)
2. `zensical-pdf.toml`
3. `mkdocs.yml` (`docs_dir`, `site_name`, `nav`)
4. `zensical.toml` (metadata only)
5. Built-in defaults

---

## Custom Typst template

Copy `src/zensical_pdf/templates/default.typ` from this repository and place it in your project:

```toml
[paths]
template = "templates/my-template.typ"
```

The template receives `$title$`, `$author$`, `$subtitle$`, `$version$`, `$date$`, and `$body$` from Pandoc.

---

## GitHub Actions

Add a workflow to your documentation repository to publish the PDF alongside your Zensical site:

```yaml
# .github/workflows/pdf.yml
name: Build PDF

on:
  push:
    branches: [main]

jobs:
  build-pdf:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Pandoc
        run: |
          wget -q https://github.com/jgm/pandoc/releases/download/3.2.1/pandoc-3.2.1-1-amd64.deb
          sudo dpkg -i pandoc-3.2.1-1-amd64.deb

      - uses: typst-community/setup-typst@v4

      - name: Install zensical-pdf
        run: pip install zensical-pdf

      - name: Build PDF
        run: zensical-pdf build

      - uses: actions/upload-artifact@v4
        with:
          name: pdf
          path: dist/
```

---

## Supported source types

| Feature | Status |
|---------|--------|
| MkDocs project with `mkdocs.yml` | ✅ |
| Nested `nav` sections | ✅ |
| Local image assets (Markdown + HTML `<img>`) | ✅ |
| YAML front matter stripping | ✅ |
| Heading normalisation (H1 → H2) | ✅ |
| Fallback sorted scan (no `nav`) | ✅ |
| Zensical project detection | ✅ (metadata only) |
| External image URLs | ✅ (passed through) |

---

## Known limitations (v1)

- **No Zensical-specific syntax**: admonitions, tabbed content, and MkDocs Material extensions are passed through as-is; Pandoc renders them as plain Markdown.
- **No Mermaid rendering**: Mermaid code blocks are included as code blocks, not as diagrams.
- **No remote images**: only local relative image paths are copied and rewritten. HTTP/HTTPS image URLs are passed through to Typst unmodified.
- **Single PDF output**: multi-PDF output sets are not supported in v1.
- **No native Zensical plugin**: this is a standalone CLI companion. Native plugin support is planned for a future release.

---

## Troubleshooting

### `ERROR: Pandoc is not available on PATH`

Pandoc is not installed or not on your system PATH. Install Pandoc ≥ 3.1.2 from [pandoc.org/installing.html](https://pandoc.org/installing.html) and verify with `pandoc --version`.

### `ERROR: Typst is not available on PATH`

Typst is not installed. Install it from [typst.app](https://typst.app) and verify with `typst --version`.

### PDF is missing some images

Run `zensical-pdf aggregate` and inspect `build/pdf/manifest.json` — the `assets` array lists every image that was copied. Missing images generate a `WARNING` on stderr. Set `missing_asset_policy = "error"` in `[pdf]` to turn warnings into failures.

### Pages are in the wrong order

Run `zensical-pdf inspect-nav` to see the resolved page order. If it does not match your expected order, check your `mkdocs.yml` `nav` section. If no `nav` is configured, pages are included in stable sorted alphabetical order.

### Typst compilation fails with a syntax error

Inspect `build/pdf/document.typ` — the Typst source generated by Pandoc. The error message from Typst will identify the line number and the unsupported construct.

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run all tests (no Pandoc or Typst required)
pytest tests/ -v

# Run only unit tests
pytest tests/unit/ -v
```

