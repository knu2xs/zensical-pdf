# Project Constitution: zensical-pdf

## Core principles

### 1. Documentation source remains authoritative

The tool must never require users to duplicate documentation content for PDF output. Markdown files in the documentation project remain the source of truth.

### 2. Companion CLI before plugin implementation

The first implementation must be a standalone CLI. Do not depend on unstable or undocumented Zensical internals. The design may expose reusable library functions that could later be wrapped by a native Zensical module or plugin.

### 3. Predictable, inspectable build pipeline

Every major build phase must produce inspectable intermediate output.

Required intermediate outputs:

- aggregated Markdown
- copied asset directory
- generated Typst file
- final PDF

The tool must support commands that allow users to inspect navigation resolution and aggregation without generating a PDF.

### 4. Test-first implementation

Navigation parsing, Markdown aggregation, path rewriting, configuration detection, and command construction must have unit tests. External tools such as Pandoc and Typst should be isolated behind small adapter functions so behavior can be tested without requiring those tools in every unit test.

### 5. Cross-platform support

The tool must support Windows, macOS, and Linux. Do not hard-code POSIX-only shell behavior in Python code. Prefer pathlib, subprocess argument arrays, and explicit path normalization.

### 6. Safe file handling

The tool may write to build and dist directories only. It must not modify source Markdown files. It must not delete user content outside its own generated output directories.

### 7. Practical Markdown compatibility

The first version should support common Markdown, local images, YAML front matter, fenced code blocks, tables, and nested navigation. Material for MkDocs and Zensical-specific syntax that is not supported must generate warnings rather than silent failures when possible.

### 8. Good diagnostics over magic

When configuration cannot be resolved, assets are missing, Pandoc is unavailable, Typst is unavailable, or Markdown contains unsupported constructs, the tool must report actionable messages.

### 9. Minimal dependencies

Use small, well-known Python dependencies. Avoid large framework dependencies unless clearly justified.

### 10. Reusable across consulting projects

The tool should support per-project configuration through zensical-pdf.toml so each documentation project can define title, author, output path, template, and PDF options without changing the reusable package.
