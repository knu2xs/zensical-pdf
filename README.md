# zensical-pdf

Generate PDF deliverables from Zensical and MkDocs-style documentation projects.

## Installation

```bash
pip install zensical-pdf
```

Requires [Pandoc](https://pandoc.org/installing.html) ≥ 3.1.2 and [Typst](https://typst.app) installed and on PATH.

## Quick start

```bash
# Check your environment
zensical-pdf doctor

# Preview page order
zensical-pdf inspect-nav

# Build the PDF
zensical-pdf build
```

## Configuration

Place a `zensical-pdf.toml` file in your documentation project root:

```toml
[project]
title = "My Documentation"
author = "Your Name"

[paths]
output = "dist/documentation.pdf"
```
