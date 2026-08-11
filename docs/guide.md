# Complete Guide

Comprehensive reference for zensical-pdf features, configuration, and examples.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Navigation Structure](#navigation-structure)
- [CLI Commands](#cli-commands)
- [Asset Handling](#asset-handling)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Known Limitations](#known-limitations)

---

## Overview

**zensical-pdf** is a tool for converting Markdown documentation to PDF. It:

1. **Reads** your documentation from a `docs/` folder
2. **Follows** your navigation structure from `zensical.toml` (or `mkdocs.yml` fallback)
3. **Aggregates** all Markdown files into one document
4. **Handles** images, metadata, and styling
5. **Compiles** to a production-ready PDF via Pandoc and Typst

### Why Use zensical-pdf?

- **Single-pass PDF generation** — one command, one PDF
- **Respects your documentation structure** — uses your configured nav for page order
- **Handles images automatically** — finds, copies, and rewrites image paths
- **Customizable metadata** — title, author, version, branding
- **Flexible configuration** — CLI args, project config, environment defaults
- **Validation & diagnostics** — `doctor` command to verify setup

---

## Installation

### From PyPI (Recommended)

```bash
pip install zensical-pdf
```

### From Source (Development)

```bash
git clone https://github.com/zensical/zensical-pdf.git
cd zensical-pdf
pip install -e .  # Editable install for development
```

### Minimum Requirements

- **Python 3.10 or later**
- **Pandoc 3.1.2 or later** (with Typst writer)
- **Typst 0.8.0 or later**

Verify installation:

```bash
zensical-pdf doctor
```

---

## Configuration

zensical-pdf uses a **5-tier priority hierarchy** for configuration:

### 1. CLI Arguments (Highest Priority)

```bash
zensical-pdf \
  --project-dir . \
  --docs-dir ./documentation \
  --output ./dist/manual.pdf \
  --title "Custom Title" \
  --author "Your Name" \
  build
```

### 2. zensical-pdf.toml (Project Config)

Create `zensical-pdf.toml` in your project root:

```toml
[project]
# PDF metadata
title = "My Project"
subtitle = "Complete Documentation"
author = "Your Name"
version = "1.0.0"

[paths]
# Paths
docs_dir = "docs"
output = "dist/documentation.pdf"
template = "templates/default.typ"

[pdf]
# Features
include_toc = true
number_sections = true
normalize_headings = true

# Asset Handling
missing_asset_policy = "warn"  # warn or error
```

### 3. zensical.toml (Project Content Config)

zensical-pdf reads navigation and metadata from `zensical.toml` when present:

```toml
[project]
site_name = "My Project"
site_author = "Your Name"
docs_dir = "docs"
nav = [
  { "Home" = "index.md" },
  { "Getting Started" = "quickstart.md" },
  { "Reference" = [
    { "Config" = "reference/config.md" },
    { "CLI" = "reference/cli.md" },
  ] },
  { "Contributing" = "contributing.md" },
]
```

### 4. mkdocs.yml (Legacy Fallback)

When `zensical.toml` is not present, zensical-pdf reads MkDocs metadata and nav:

```yaml
site_name: My Project
docs_dir: docs

nav:
  - Home: index.md
  - Getting Started: quickstart.md
```

### 5. Defaults (Lowest Priority)

Built-in defaults when nothing is specified:

- `docs_dir: "docs"`
- `output: "dist/documentation.pdf"`
- `build_dir: ".zensical"`
- `include_toc: true`
- `normalize_headings: true`
- `missing_asset_policy: "warn"`

### Configuration Reference

| Option | Type | Default | Description |
| ------ | ---- | ------- | ----------- |
| `project_dir` | Path | `.` | Root of your project |
| `docs_dir` | Path | `docs` | Folder containing Markdown files |
| `output` | Path | `dist/documentation.pdf` | Output PDF path |
| `build_dir` | Path | `.zensical` | Temporary build directory |
| `title` | String | From zensical.toml/mkdocs.yml or "Documentation" | PDF title page text |
| `subtitle` | String | empty | Subtitle on title page |
| `author` | String | From zensical.toml or empty | Author attribution |
| `version` | String | empty | Version number |
| `template` | Path or "default" | "default" | Typst template file |
| `include_toc` | Boolean | `true` | Generate table of contents |
| `number_sections` | Boolean | `false` | Add section numbers to headings |
| `normalize_headings` | Boolean | `true` | Normalize heading levels (H1 → H2) |
| `missing_asset_policy` | String | `"warn"` | How to handle missing images: "warn", "skip", or "fail" |
| `permissive` | Boolean | `false` | Skip validation; best-effort build |

---

## Navigation Structure

zensical-pdf determines page order and hierarchy from:

### 1. zensical.toml (Recommended)

Define navigation explicitly:

```toml
[project]
nav = [
  { "Home" = "index.md" },
  { "User Guide" = [
    { "Installation" = "guide/install.md" },
    { "Configuration" = "guide/config.md" },
  ] },
  { "API Reference" = [
    { "Getting Started" = "api/intro.md" },
    { "Endpoints" = "api/endpoints.md" },
  ] },
  { "Contributing" = "contributing.md" },
]
```

Pages are included in the order specified. Nested sections become nested heading levels.

### 2. mkdocs.yml (Legacy Fallback)

If `zensical.toml` does not exist, zensical-pdf uses `mkdocs.yml` `nav`.

### 3. Directory Scan (Fallback)

If no nav is configured, zensical-pdf scans your `docs/` folder:

- Finds all `.md` files recursively
- Sorts them alphabetically within each directory
- Uses folder names as section headings
- Falls back if configured nav is missing or malformed

### 4. Permissive Mode

Use `--permissive` to skip missing files and continue:

```bash
zensical-pdf --permissive build
```

---

## CLI Commands

### build

Generate the complete PDF:

```bash
zensical-pdf build
```

Steps:

1. Aggregates Markdown files
2. Copies images to build directory
3. Rewrites image paths
4. Converts to Typst
5. Compiles to PDF

**Options:**

```bash
zensical-pdf build --project-dir . --output dist/output.pdf
```

### aggregate

Aggregates Markdown into a single file without generating PDF:

```bash
zensical-pdf aggregate
```

Output:

- `dist/combined.md` — aggregated Markdown
- `dist/assets/` — copied image files
- `.zensical/aggregation-manifest.json` — build metadata

Useful for:

- Previewing the aggregated content
- Debugging navigation order
- Custom post-processing before PDF generation

### inspect-nav

Preview your documentation structure and page order:

```bash
zensical-pdf inspect-nav
```

Shows:

- All pages in order
- Section nesting levels
- File paths

Useful for:

- Verifying configured navigation is correct
- Understanding heading hierarchy
- Debugging missing or unexpected pages

### doctor

Validate your environment and project setup:

```bash
zensical-pdf doctor
```

Checks:

- ✓ Python version (3.10+)
- ✓ Pandoc installed and version (3.1.2+)
- ✓ Typst installed and version
- ✓ Project config exists (or uses defaults)
- ✓ Docs directory exists and is readable
- ✓ Output directory is writable

Exit code: 0 if all pass, 1 if any fail.

Use `--permissive` to see warnings instead of errors:

```bash
zensical-pdf --permissive doctor
```

---

## Asset Handling

### Finding Images

zensical-pdf automatically finds images referenced in Markdown and HTML:

```markdown
# Markdown image reference
![Alt text](images/logo.png)

<!-- HTML image reference -->
<img src="images/screenshot.png" alt="Screenshot" />
```

### Image Path Requirements

Images must be:

- **Local files** relative to your `docs/` folder
- **Accessible** from the project root or docs directory

Examples of valid image references:

```markdown
![Image](images/logo.png)        # ✓ Relative path
![Image](./images/logo.png)      # ✓ Explicit relative
![Image](../images/shared.png)   # ✓ Parent directory
```

External URLs are passed through unchanged:

```markdown
![Image](https://example.com/img.png)  # ✓ External URL, not copied
```

### Asset Deduplication

zensical-pdf uses **SHA256 content hashing** to deduplicate assets:

- If two files have identical content, only one copy is stored
- Saves space in the PDF and build directory
- Different filenames with same content are merged automatically

### Image Path Rewriting

After aggregating content, zensical-pdf rewrites all image paths to point to the build directory:

```text
Before:  ![Logo](docs/images/logo.png)
After:   ![Logo](.zensical/assets/logo.png)
```

This ensures images are found during PDF compilation.

### Missing Asset Policy

Configure behavior when images can't be found:

```toml
# zensical-pdf.toml
missing_asset_policy = "warn"  # Default: show warning but continue
```

Options:

- `"warn"` — Show warning, skip the image, continue
- `"skip"` — Silently skip missing images
- `"fail"` — Stop and fail if any image is missing

CLI override:

```bash
zensical-pdf --missing-asset-policy fail build
```

---

## Examples

### Example 1: Simple Project

**Directory structure:**

```text
my-docs/
├── docs/
│   ├── index.md
│   ├── guide.md
│   └── faq.md
└── zensical.toml
```

**zensical.toml:**

```toml
[project]
site_name = "My Docs"
nav = [
  { "Home" = "index.md" },
  { "Guide" = "guide.md" },
  { "FAQ" = "faq.md" },
]
```

**Build:**

```bash
cd my-docs
zensical-pdf build
# Output: dist/documentation.pdf
```

### Example 2: Complex Navigation with Sections

**zensical.toml:**

```toml
[project]
site_name = "Complete Reference"
site_description = "Comprehensive documentation"
site_author = "Your Name"
nav = [
  { "Home" = "index.md" },
  { "Getting Started" = [
    { "Installation" = "quickstart/install.md" },
    { "Configuration" = "quickstart/config.md" },
  ] },
  { "User Guide" = [
    { "Basic Usage" = "guide/basic.md" },
    { "Advanced Features" = "guide/advanced.md" },
  ] },
  { "API Reference" = [
    { "Overview" = "api/overview.md" },
    { "Types" = "api/types.md" },
    { "Functions" = "api/functions.md" },
  ] },
  { "Contributing" = "contributing.md" },
]
```

**Custom config:**

**zensical-pdf.toml:**

```toml
[project]
title = "Complete Reference"
author = "Your Name"
version = "2.0.0"

[paths]
output = "dist/reference.pdf"

[pdf]
include_toc = true
number_sections = true
```

**Build:**

```bash
zensical-pdf build
# Generates: dist/reference.pdf with TOC and numbered sections
```

### Example 3: Using CLI Overrides

```bash
zensical-pdf \
  --title "Custom PDF Title" \
  --author "Jane Doe" \
  --version "1.5.0" \
  --output dist/custom.pdf \
  --number-sections \
  build
```

### Example 4: With Images

**Directory structure:**

```text
project/
├── docs/
│   ├── index.md
│   ├── guide/
│   │   ├── getting-started.md
│   │   └── images/
│   │       ├── screenshot1.png
│   │       └── screenshot2.png
│   └── images/
│       └── logo.png
└── zensical.toml
```

**Markdown files:**

`docs/index.md`:

```markdown
# Welcome

![Logo](images/logo.png)

See [Getting Started](guide/getting-started.md).
```

`docs/guide/getting-started.md`:

```markdown
# Getting Started

Follow these steps:

![Step 1](images/screenshot1.png)
![Step 2](images/screenshot2.png)
```

**Build:**

```bash
zensical-pdf build
# Copies all images to .zensical/assets/
# Rewrites paths in aggregated Markdown
# Generates PDF with all images embedded
```

---

## Troubleshooting

### "pandoc not found" Error

**Cause:** Pandoc is not installed or not in PATH.

**Solution:**

```bash
# Install Pandoc
brew install pandoc  # macOS
sudo apt-get install pandoc  # Ubuntu/Debian
choco install pandoc  # Windows

# Verify
pandoc --version  # Should show 3.1.2 or later
```

### "typst not found" Error

**Cause:** Typst is not installed or not in PATH.

**Solution:**

```bash
# Install Typst
brew install typst  # macOS
# Download from https://github.com/typst/typst/releases  # Linux/Windows
choco install typst  # Windows

# Verify
typst --version  # Should show 0.8.0 or later
```

### "Python version X.Y is not 3.10 or later"

**Cause:** You're running Python < 3.10.

**Solution:**

```bash
# Check your Python version
python --version

# Use Python 3.10+ explicitly
python3.10 -m pip install zensical-pdf
python3.10 -m zensical_pdf build

# Or upgrade Python via your package manager
```

### "Configuration file not found"

**Cause:** No `zensical-pdf.toml` and no project directory specified.

**Solution:**

```bash
# Specify project directory
zensical-pdf --project-dir . build

# Or create a zensical-pdf.toml
cat > zensical-pdf.toml << EOF
[project]
title = "My Docs"
EOF
zensical-pdf build
```

### Images Not Appearing in PDF

**Cause:** Image paths are incorrect or files don't exist.

**Solution:**

1. Verify images exist:

```bash
ls -la docs/images/
```

1. Verify image references in Markdown use relative paths:

```markdown
![Image](images/logo.png)  # ✓ Correct
![Image](/images/logo.png)  # ✗ Wrong (absolute path)
```

1. Inspect aggregated content:

```bash
zensical-pdf aggregate
cat dist/combined.md  # Review image references
```

1. Check asset directory:

```bash
ls -la .zensical/assets/
```

### "Permission denied" on Output Directory

**Cause:** Output directory is not writable.

**Solution:**

```bash
# Check directory permissions
ls -la dist/

# Make writable if needed
chmod -R u+w dist/

# Or specify a different output directory
zensical-pdf --output /tmp/output.pdf build
```

### PDF File is Corrupted or Won't Open

**Cause:** PDF generation failed or was interrupted.

**Solution:**

1. Clean up and rebuild:

```bash
rm -rf dist/ .zensical/
zensical-pdf build
```

1. Check for errors:

```bash
zensical-pdf doctor  # Verify environment
zensical-pdf inspect-nav  # Verify navigation
zensical-pdf aggregate  # Verify aggregation
```

1. Try with permissive mode:

```bash
zensical-pdf --permissive build
```

### Missing Pages in PDF

**Cause:** Pages not included in configured nav (`zensical.toml` or `mkdocs.yml`) or aren't found during directory scan.

**Solution:**

1. Check structure:

```bash
zensical-pdf inspect-nav
```

1. Verify navigation config:

```toml
[project]
nav = [
  { "Home" = "index.md" },
  { "Guide" = "guide.md" },
  # Add missing pages here
]
```

1. Verify file existence:

```bash
ls -la docs/
```

---

## Known Limitations

### Pandoc Limitations

- Some Markdown extensions may not convert perfectly to Typst
- HTML in Markdown may not render correctly in PDF
- Complex tables may need manual formatting

### Template Limitations

- Default template supports basic Typst features
- Custom branding is limited to title page metadata
- Complex multi-column layouts are not supported

### Platform Limitations

- PDF output quality depends on Typst renderer
- Font availability varies by system
- Path handling may differ on Windows vs. macOS/Linux

### Performance Limitations

- Very large documentation (1000+ pages) may be slow
- Large images may increase PDF file size significantly
- No incremental builds; every run is full regeneration

### Feature Limitations

- No support for page-specific styling
- No cross-document references or bookmarks
- No support for embedded fonts in PDF (uses system fonts)
- Limited syntax highlighting for code blocks

---

## FAQ

**Q: Can I use custom Typst templates?**

A: Yes! Specify a template in `zensical-pdf.toml`:

```toml
template = "path/to/custom.typ"
```

**Q: Can I generate multiple PDFs from one docs folder?**

A: Yes! Use different configs or CLI args:

```bash
zensical-pdf --output dist/full.pdf build
zensical-pdf --output dist/summary.pdf --docs-dir docs/intro build
```

**Q: Does it support multiple languages?**

A: Not yet. Typst language support depends on the template and fonts used.

**Q: Can I customize the PDF title page?**

A: Yes! Use metadata in `zensical-pdf.toml` (or fallback from `zensical.toml`):

```toml
title = "Custom Title"
subtitle = "With subtitle"
author = "Your Name"
version = "1.0"
```

**Q: How do I handle very large image files?**

A: Compress images before adding to docs:

```bash
# Example: reduce PNG size
pngquant --ext .png images/*.png
```

---

## Next Steps

- [Quick Start](quickstart.md) — Get started in 5 minutes
- [Contributing](contributing.md) — Contribute to development
- [GitHub Issues](https://github.com/zensical/zensical-pdf/issues) — Report bugs or request features
