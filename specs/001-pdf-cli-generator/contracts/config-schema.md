# Contract: Configuration Schema

## zensical-pdf.toml

Per-project configuration file. Placed in the documentation project root.

```toml
[project]
title = "Enterprise Upgrade Guide"
subtitle = "Customer-ready technical documentation"
author = "Joel McCune"
version = "0.1.0"

[paths]
docs_dir = "docs"
output = "dist/documentation.pdf"
template = "templates/default.typ"

[pdf]
normalize_headings = true
include_toc = true
number_sections = false
missing_asset_policy = "warn"
```

### [project] section

| Key | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| `title` | string | No | `"Documentation"` | Document title in the PDF |
| `subtitle` | string | No | none | Optional subtitle |
| `author` | string | No | none | Author name in the PDF |
| `version` | string | No | none | Version string in the PDF |

### [paths] section

| Key | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| `docs_dir` | string | No | `"docs"` | Path to Markdown source directory, relative to project root |
| `output` | string | No | `"dist/documentation.pdf"` | Output PDF path, relative to project root |
| `template` | string | No | bundled default | Path to custom Typst template, relative to project root |

### [pdf] section

| Key | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| `normalize_headings` | bool | No | `true` | Shift H1 headings to H2 before aggregation |
| `include_toc` | bool | No | `true` | Include table of contents in PDF |
| `number_sections` | bool | No | `false` | Number sections in PDF |
| `missing_asset_policy` | string | No | `"warn"` | `"warn"` or `"error"` — behavior when a local image is missing |

---

## mkdocs.yml (relevant fields)

The tool reads only these fields from `mkdocs.yml`. All other fields are ignored.

| Key | Type | Used for |
|-----|------|---------|
| `site_name` | string | Fallback document title if `zensical-pdf.toml` has no `[project].title` |
| `docs_dir` | string | Documentation source directory (default: `docs`) |
| `nav` | list | Page ordering — list of strings or dicts |

### nav format

```yaml
nav:
  - Home: index.md                         # dict: title → path
  - index.md                               # bare string: no title
  - Guide:                                 # section grouping
      - Overview: guide/overview.md
      - Setup: guide/setup.md
  - Reference:
      - API: reference/api.md
```

Supported leaf entry types:
- `"path/to/file.md"` — bare string path
- `{"Title": "path/to/file.md"}` — single-key dict (title → path)
- `{"Section": [...]}` — section grouping (title → list of children, processed recursively)

Unsupported entry types (emit warning and skip):
- External URLs in nav entries
- Entries that reference non-`.md` files

---

## Configuration discovery priority

```
1. Explicit CLI arguments (--project-dir, --output, --permissive)
2. zensical-pdf.toml  (project root)
3. mkdocs.yml         (docs_dir, site_name, nav)
4. zensical.toml      (metadata only; nav not supported in v1)
5. Conventional defaults
```

If no configuration file is found and no `docs/` directory exists, the tool exits with `ConfigNotFoundError`.
