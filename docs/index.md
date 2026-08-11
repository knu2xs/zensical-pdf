# zensical-pdf

[![Tests](https://github.com/zensical/zensical-pdf/actions/workflows/tests.yml/badge.svg)](https://github.com/zensical/zensical-pdf/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/zensical-pdf.svg)](https://pypi.org/project/zensical-pdf/)
[![License](https://img.shields.io/github/license/zensical/zensical-pdf)](LICENSE)

A powerful CLI tool that aggregates Markdown documentation and compiles it to PDF with a single command.

## The Problem

You have documentation spread across multiple Markdown files, organized in a docs folder with a navigation structure defined in `mkdocs.yml`. You want to generate a **single, cohesive PDF** that includes all your content, properly formatted with:
- A title page with metadata
- Automatic table of contents
- Proper heading hierarchy
- Cross-file asset handling
- Consistent styling

**zensical-pdf solves this.** It treats your documentation as a unified project and produces publication-ready PDFs.

## Key Features

✨ **Markdown Aggregation**
- Scans your docs folder following your `mkdocs.yml` navigation structure
- Aggregates all Markdown files into a single document
- Preserves heading hierarchy with automatic normalization

📦 **Asset Management**
- Finds and copies local images into the build directory
- Rewrites image paths in both Markdown and HTML references
- Deduplicates assets using content hashing
- Passes through external URLs unchanged

⚙️ **Configuration Hierarchy**
- CLI arguments (highest priority)
- `zensical-pdf.toml` project config
- `mkdocs.yml` metadata extraction
- Built-in defaults (lowest priority)

📄 **PDF Generation**
- Converts Markdown → Typst via Pandoc (3.1.2+)
- Compiles Typst → PDF with custom templates
- Supports heading numbering, TOC generation, custom branding
- Configurable fonts, colors, and document options

🔍 **Validation & Diagnostics**
- `doctor` command checks Python version, Pandoc, Typst, config, and directories
- Comprehensive error messages with troubleshooting hints
- Permissive mode to skip missing files

## Quick Links

- **[Getting Started →](quickstart.md)** — Install and generate your first PDF in 5 minutes
- **[Full Guide →](guide.md)** — Comprehensive reference, examples, troubleshooting
- **[Contributing →](contributing.md)** — Development setup, testing, pull request process

## Installation

```bash
pip install zensical-pdf
```

**Prerequisites:**
- Python 3.10 or later
- Pandoc 3.1.2 or later (with Typst writer support)
- Typst 0.8.0 or later

## Quick Example

```bash
# Check your environment
zensical-pdf doctor

# Inspect your documentation structure
zensical-pdf inspect-nav

# Aggregate your docs
zensical-pdf aggregate

# Build the PDF
zensical-pdf build
```

Your PDF will be available at `dist/documentation.pdf`.

## Example Project

A complete example project is included in the `example/` directory. It demonstrates:
- Project configuration with `zensical-pdf.toml`
- Navigation structure via `mkdocs.yml`
- Multiple documentation pages
- Local image assets

## License

MIT License — see [LICENSE](../LICENSE) for details.

---

**Questions?** See the [Full Guide](guide.md) or [Contributing](contributing.md) for more information.
