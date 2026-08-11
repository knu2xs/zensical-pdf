# Contract: Manifest Schema

Build manifests are JSON files written to the build and dist directories after each pipeline phase.

---

## Aggregation manifest

**Written to**: `<build_dir>/manifest.json` after `aggregate` completes.

```json
{
  "generated_at": "2026-08-10T14:32:00Z",
  "project_dir": "/Users/joel/projects/my-docs",
  "config_file": "mkdocs.yml",
  "docs_dir": "/Users/joel/projects/my-docs/docs",
  "nav_source": "nav",
  "pages": [
    "index.md",
    "guide/overview.md",
    "guide/setup.md",
    "reference/api.md"
  ],
  "assets": [
    {
      "source": "/Users/joel/projects/my-docs/docs/assets/diagram.png",
      "copied_to": "/Users/joel/projects/my-docs/build/pdf/assets/diagram.png"
    }
  ],
  "intermediate_markdown": "/Users/joel/projects/my-docs/build/pdf/combined.md",
  "intermediate_typst": null,
  "output": null
}
```

---

## Full build manifest

**Written to**: `dist/manifest.json` after `build` completes. Contains all fields from the aggregation manifest, plus:

```json
{
  "generated_at": "2026-08-10T14:32:45Z",
  "project_dir": "/Users/joel/projects/my-docs",
  "config_file": "mkdocs.yml",
  "docs_dir": "/Users/joel/projects/my-docs/docs",
  "nav_source": "nav",
  "pages": ["index.md", "guide/overview.md", "guide/setup.md", "reference/api.md"],
  "assets": [
    {
      "source": "/Users/joel/projects/my-docs/docs/assets/diagram.png",
      "copied_to": "/Users/joel/projects/my-docs/build/pdf/assets/diagram.png"
    }
  ],
  "intermediate_markdown": "/Users/joel/projects/my-docs/build/pdf/combined.md",
  "intermediate_typst": "/Users/joel/projects/my-docs/build/pdf/document.typ",
  "output": "/Users/joel/projects/my-docs/dist/documentation.pdf"
}
```

---

## Field reference

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `generated_at` | string (ISO 8601 UTC) | No | Timestamp when this manifest was written |
| `project_dir` | string (absolute path) | No | Documentation project root |
| `config_file` | string (relative path) or null | Yes | Detected config filename, relative to project_dir |
| `docs_dir` | string (absolute path) | No | Resolved documentation source directory |
| `nav_source` | `"nav"` or `"scan"` | No | Whether page order came from `nav` config or directory scan |
| `pages` | array of strings | No | Relative paths of included pages, in aggregation order |
| `assets` | array of objects | No | Each entry has `source` and `copied_to` (both absolute paths) |
| `intermediate_markdown` | string (absolute path) | No | Path to `combined.md` |
| `intermediate_typst` | string (absolute path) or null | Yes | Path to generated `.typ` file; null until build phase |
| `output` | string (absolute path) or null | Yes | Path to final PDF; null until build phase |
