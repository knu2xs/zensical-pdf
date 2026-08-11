# Data Model: zensical-pdf CLI Generator

**Phase 1 output for**: `specs/001-pdf-cli-generator/plan.md`
**Date**: 2026-08-10

---

## Core entities

### PdfConfig

The resolved configuration for a single build. Produced by `config.py` by merging CLI arguments, `zensical-pdf.toml`, `mkdocs.yml`, and conventional defaults in priority order.

| Field | Type | Source | Default |
|-------|------|--------|---------|
| `project_dir` | `Path` | CLI arg / cwd | `Path(".")` |
| `docs_dir` | `Path` | `zensical-pdf.toml [paths].docs_dir` → `mkdocs.yml docs_dir` → default | `project_dir / "docs"` |
| `output` | `Path` | `zensical-pdf.toml [paths].output` → CLI arg | `project_dir / "dist" / "documentation.pdf"` |
| `build_dir` | `Path` | derived | `project_dir / "build" / "pdf"` |
| `title` | `str` | `zensical-pdf.toml [project].title` → `mkdocs.yml site_name` | `"Documentation"` |
| `subtitle` | `str \| None` | `zensical-pdf.toml [project].subtitle` | `None` |
| `author` | `str \| None` | `zensical-pdf.toml [project].author` | `None` |
| `version` | `str \| None` | `zensical-pdf.toml [project].version` | `None` |
| `template` | `Path \| None` | `zensical-pdf.toml [paths].template` | `None` (use bundled default) |
| `normalize_headings` | `bool` | `zensical-pdf.toml [pdf].normalize_headings` | `True` |
| `include_toc` | `bool` | `zensical-pdf.toml [pdf].include_toc` | `True` |
| `number_sections` | `bool` | `zensical-pdf.toml [pdf].number_sections` | `False` |
| `missing_asset_policy` | `Literal["warn", "error"]` | `zensical-pdf.toml [pdf].missing_asset_policy` | `"warn"` |
| `permissive` | `bool` | CLI flag `--permissive` | `False` |
| `detected_config` | `Path \| None` | set during discovery | `None` |

**Validation rules**:
- `docs_dir` must exist when any command runs (except `doctor`).
- `output` must be under `project_dir / "dist"` unless explicitly overridden and `permissive` is set.
- `template`, if set, must exist on disk.

**State transitions**: None. `PdfConfig` is immutable after construction.

---

### NavEntry

A single resolved page in the navigation. Produced by `nav.py`.

| Field | Type | Notes |
|-------|------|-------|
| `path` | `Path` | Absolute path to the Markdown source file |
| `relative_path` | `Path` | Path relative to `docs_dir` |
| `title` | `str \| None` | Title from nav entry dict key, if present |
| `exists` | `bool` | Whether the file exists on disk |

**Validation rules**:
- If `exists` is `False` and `permissive` is `False`, the nav resolver raises `NavResolutionError`.

---

### NavResult

The complete resolved navigation for a project. Produced by `nav.py`.

| Field | Type | Notes |
|-------|------|-------|
| `entries` | `list[NavEntry]` | Ordered list of resolved pages |
| `source` | `Literal["nav", "scan"]` | Whether nav came from config or directory scan |
| `warnings` | `list[str]` | Non-fatal issues (missing nav, skipped entries) |

---

### AggregatedDocument

The intermediate combined Markdown document. Produced by `aggregator.py`.

| Field | Type | Notes |
|-------|------|-------|
| `output_path` | `Path` | Absolute path to `build/pdf/combined.md` |
| `pages_included` | `list[Path]` | Source files included, in order |
| `assets` | `list[AssetCopy]` | All asset copy operations performed |
| `warnings` | `list[str]` | Non-fatal issues during aggregation |

---

### AssetCopy

Represents one local image asset that was copied into the build directory. Produced by `assets.py`.

| Field | Type | Notes |
|-------|------|-------|
| `source_path` | `Path` | Original absolute path of the image file |
| `dest_path` | `Path` | Absolute path where the image was copied in `build/pdf/assets/` |
| `original_reference` | `str` | The original image path as it appeared in Markdown |
| `rewritten_reference` | `str` | The replacement path written into `combined.md` |

**Naming collision handling**: If two source images have the same filename, the destination is prefixed with a short hash of the source path to ensure uniqueness.

---

### BuildManifest

Describes a completed build phase. Written by `manifest.py` to `build/pdf/manifest.json` (after aggregation) and `dist/manifest.json` (after full build).

| Field | Type | Notes |
|-------|------|-------|
| `generated_at` | `str` | ISO 8601 UTC timestamp |
| `project_dir` | `str` | Absolute path to the project root |
| `config_file` | `str \| None` | Detected config file path or `null` |
| `docs_dir` | `str` | Resolved docs directory path |
| `pages` | `list[str]` | Relative paths of included Markdown files, in order |
| `assets` | `list[AssetManifestEntry]` | Copied asset entries |
| `intermediate_markdown` | `str` | Path to `combined.md` |
| `intermediate_typst` | `str \| None` | Path to generated `.typ` file, or `null` if not yet produced |
| `output` | `str \| None` | Path to final PDF, or `null` if not yet produced |

---

### AssetManifestEntry

JSON-serializable representation of an `AssetCopy`, used in `BuildManifest`.

| Field | Type |
|-------|------|
| `source` | `str` |
| `copied_to` | `str` |

---

### DoctorResult

The outcome of running all `doctor` checks. Produced by `doctor.py`.

| Field | Type | Notes |
|-------|------|-------|
| `checks` | `list[DoctorCheck]` | All checks run, in order |
| `all_pass` | `bool` | `True` if no check has `status == "fail"` |

---

### DoctorCheck

One environment validation check performed by the `doctor` command.

| Field | Type | Notes |
|-------|------|-------|
| `name` | `str` | Human-readable check label |
| `status` | `Literal["pass", "warn", "fail"]` | Check outcome |
| `detail` | `str` | Explanation (install hint, version found, error message) |

**Doctor checks** (in display order):
1. Python version (pass if ≥ 3.10)
2. Pandoc availability and version (pass if `pandoc --version` succeeds and version ≥ 3.1.2)
3. Typst availability (pass if `typst --version` succeeds)
4. Project configuration detected (`mkdocs.yml`, `zensical.toml`, or `zensical-pdf.toml` found)
5. Docs directory exists and is readable
6. Build output directory is writable (or can be created)

---

## Error types

| Exception | Module | Raised when |
|-----------|--------|-------------|
| `ConfigNotFoundError` | `config.py` | No config file detected and no docs directory found |
| `NavResolutionError` | `nav.py` | Nav entry references a missing file and `permissive=False` |
| `AggregationError` | `aggregator.py` | A source Markdown file cannot be read |
| `AssetError` | `assets.py` | Missing asset and `missing_asset_policy="error"` |
| `PandocNotFoundError` | `adapters/pandoc.py` | `pandoc` binary not found on PATH |
| `PandocError` | `adapters/pandoc.py` | Pandoc exits non-zero |
| `TypstNotFoundError` | `adapters/typst.py` | `typst` binary not found on PATH |
| `TypstError` | `adapters/typst.py` | Typst exits non-zero |

All errors inherit from `ZensicalPdfError(Exception)` defined in `__init__.py`.

---

## Module dependency graph

```
cli.py
  ├── config.py          (PdfConfig)
  ├── nav.py             (NavResult, NavEntry)
  ├── aggregator.py      (AggregatedDocument)
  │     └── assets.py   (AssetCopy)
  ├── manifest.py        (BuildManifest)
  ├── adapters/
  │     ├── pandoc.py   (PandocAdapter)
  │     └── typst.py    (TypstAdapter)
  └── doctor.py          (DoctorResult, DoctorCheck)
```

`cli.py` is the only module that imports from all others. All other modules are independent of each other (no circular imports).
