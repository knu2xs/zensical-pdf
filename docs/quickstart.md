# Quick Start

Get your first PDF generated in 5 minutes.

## Prerequisites

Before you begin, install the required tools:

**Python 3.10+**
```bash
python --version  # Should show 3.10 or later
```

**Pandoc 3.1.2+** (with Typst writer support)
```bash
# macOS
brew install pandoc

# Linux (Ubuntu/Debian)
sudo apt-get install pandoc

# Windows
choco install pandoc
# or download from https://pandoc.org/installing.html

# Verify installation
pandoc --version  # Should show 3.1.2 or later
```

**Typst 0.8.0+**
```bash
# macOS
brew install typst

# Linux
# Download from https://github.com/typst/typst/releases
# or use distro package manager

# Windows
choco install typst
# or download from https://github.com/typst/typst/releases

# Verify installation
typst --version  # Should show 0.8.0 or later
```

### Verify Your Environment

```bash
zensical-pdf doctor
```

You should see a table with ✓ (pass) status for all checks:

- Python version ✓
- Pandoc installed & version ✓
- Typst installed & version ✓
- Project config found ✓
- Docs directory exists ✓
- Output directory writable ✓

If any checks fail, see [Troubleshooting](#troubleshooting) below.

## Installation

Install zensical-pdf from PyPI:

```bash
pip install zensical-pdf
```

Or install from source (development):

```bash
git clone https://github.com/zensical/zensical-pdf.git
cd zensical-pdf
pip install -e .
```

## Step 1: Set Up Your Documentation

You should have a docs folder with Markdown files and a project config file (`zensical.toml` recommended):

```
your-project/
├── docs/
│   ├── index.md
│   ├── guide.md
│   ├── api/
│   │   ├── overview.md
│   │   └── reference.md
│   └── images/
│       └── logo.png
├── zensical.toml (recommended)
└── zensical-pdf.toml (optional)
```

### zensical.toml (recommended)

Define your documentation structure:

```toml
[project]
site_name = "My Project"
site_description = "Project documentation"
docs_dir = "docs"
nav = [
  { "Home" = "index.md" },
  { "Guide" = "guide.md" },
  { "API" = [
    { "Overview" = "api/overview.md" },
    { "Reference" = "api/reference.md" },
  ] },
]
```

zensical-pdf uses this to determine the order and hierarchy of pages in your PDF.

For legacy projects without `zensical.toml`, `mkdocs.yml` is still supported.

### zensical-pdf.toml (optional)

Create a config file in your project root to customize PDF metadata:

```toml
[project]
title = "My Project Documentation"
subtitle = "A complete guide"
author = "Your Name"
version = "1.0.0"

[paths]
output = "dist/my-docs.pdf"
```

## Step 2: Inspect Your Documentation Structure

Preview how zensical-pdf will aggregate your docs:

```bash
zensical-pdf inspect-nav
```

You should see a list of pages in order, including any nested sections. Verify the order is correct before proceeding.

## Step 3: Build Your PDF

Generate the PDF:

```bash
zensical-pdf build
```

This does everything:

1. **Aggregates** all Markdown files into a single document
2. **Copies** local images to the build directory
3. **Rewrites** image paths
4. **Converts** Markdown → Typst using Pandoc
5. **Compiles** Typst → PDF

The PDF appears at `dist/documentation.pdf` (or your configured output path).

## Step 4: Verify the Output

Open your PDF:

```bash
# macOS
open dist/documentation.pdf

# Linux
xdg-open dist/documentation.pdf

# Windows
start dist/documentation.pdf
```

**Success!** 🎉 Your documentation is now a PDF.

---

## Troubleshooting

### "pandoc not found"

Install Pandoc using the prerequisites section above, or ensure it's in your PATH:

```bash
which pandoc  # macOS/Linux
where pandoc  # Windows
```

### "typst not found"

Install Typst using the prerequisites section above.

### "Python version X.Y is not 3.10 or later"

Upgrade Python:

```bash
python3.11 --version  # Use Python 3.11+ binary directly
python3.11 -m pip install zensical-pdf
python3.11 -m zensical_pdf build
```

### "Configuration file not found"
Create a `zensical-pdf.toml` in your project root, or pass `--project-dir` to point to your docs folder:
```bash
zensical-pdf --project-dir . build
```

### Images not appearing in PDF
Verify images are local files (not external URLs) and are referenced correctly:
```bash
zensical-pdf inspect-nav  # Shows aggregated content
```

Check that image paths are relative to your docs folder:
```markdown
![Logo](images/logo.png)  # ✓ Correct
![Logo](/images/logo.png) # ✗ Absolute path won't work
```

### "Permission denied" on output directory
Ensure the output directory is writable:
```bash
zensical-pdf doctor  # Will show detailed error
```

If output dir doesn't exist, zensical-pdf creates it automatically.

---

## Next Steps

- **[Full Guide](guide.md)** — Explore all features, configuration options, and examples
- **[Contributing](contributing.md)** — Contribute to zensical-pdf development
- **[GitHub](https://github.com/zensical/zensical-pdf)** — Report issues, request features

## Need Help?

1. Run `zensical-pdf --help` for CLI options
2. See [Full Guide](guide.md) for comprehensive reference
3. Check [Troubleshooting](guide.md#troubleshooting) for common issues
