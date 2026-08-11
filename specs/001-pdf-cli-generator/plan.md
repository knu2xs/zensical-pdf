# Implementation Plan: zensical-pdf CLI Generator

**Branch**: `001-pdf-cli-generator` | **Date**: 2026-08-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-pdf-cli-generator/spec.md`

## Summary

zensical-pdf is a Python CLI tool that generates PDF deliverables from MkDocs-style documentation projects. It resolves navigation from `mkdocs.yml`, aggregates Markdown into a single intermediate document, converts to Typst via Pandoc, and compiles the final PDF via Typst. The tool is packaged with a `src/` layout, exposes four subcommands (`inspect-nav`, `aggregate`, `build`, `doctor`), and is fully unit-testable without Pandoc or Typst installed.

---

## Technical Context

**Language/Version**: Python 3.11+ (uses `tomllib` from stdlib; `tomli` backport for 3.10)

**Primary Dependencies**:
- `typer` — CLI framework with subcommand support
- `rich` — terminal output, progress, warnings, and error formatting
- `pyyaml` — `mkdocs.yml` parsing
- `tomllib` (stdlib, Python 3.11+) / `tomli` (backport for < 3.11) — `zensical-pdf.toml` parsing
- `pytest` — unit and integration testing
- `pathlib` — all path handling (no `os.path`)
- `subprocess.run` with argument arrays — Pandoc and Typst invocations

**Storage**: Files only — reads from documentation source tree; writes to `build/pdf/` and `dist/`.

**Testing**: pytest with isolated `tmp_path` fixtures. Pandoc and Typst adapters are abstracted behind a `Runner` protocol so they can be replaced by fakes in tests.

**Target Platform**: macOS, Linux, Windows (cross-platform via `pathlib` and `subprocess` argument arrays; no POSIX shell strings).

**Project Type**: Python CLI tool packaged as `zensical-pdf` entry point, installable via `pip install`.

**Performance Goals**: Full pipeline completes in under 2 minutes for a 50-page documentation project on standard developer hardware with Pandoc and Typst pre-installed.

**Constraints**:
- Must not modify source Markdown files under any code path.
- Must not write outside `build/` or `dist/` unless explicitly configured.
- All path operations use `pathlib.Path`; no hardcoded POSIX separators.
- External tool invocations use `subprocess.run` with list arguments, never shell strings.

**Scale/Scope**: Single-project documentation repositories of up to ~200 pages. Multi-PDF and multi-project orchestration are out of scope for v1.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Documentation source is authoritative | PASS | Tool reads sources; never writes to them |
| Companion CLI before plugin | PASS | No Zensical plugin code; pure standalone CLI |
| Predictable, inspectable pipeline | PASS | `inspect-nav` and `aggregate` expose intermediate outputs |
| Test-first implementation | PASS | All logic tested via unit tests; adapters mockable |
| Cross-platform support | PASS | `pathlib` + `subprocess` array args throughout |
| Safe file handling | PASS | Writes only to `build/` and `dist/` |
| Practical Markdown compatibility | PASS | Warnings for unsupported constructs, not silent failures |
| Good diagnostics over magic | PASS | `doctor` command + actionable error messages in all adapters |
| Minimal dependencies | PASS | 5 runtime deps: typer, rich, pyyaml, tomli/tomllib, pathlib (stdlib) |
| Reusable across projects | PASS | Per-project config via `zensical-pdf.toml` |

**Constitution Check Result: ALL GATES PASS**

Re-checked after Phase 1 design — no violations introduced.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-pdf-cli-generator/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── cli-schema.md
│   ├── config-schema.md
│   └── manifest-schema.md
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
zensical-pdf/                      # repository root
├── src/
│   └── zensical_pdf/
│       ├── __init__.py
│       ├── cli.py                 # typer app; subcommand registration
│       ├── config.py              # config discovery and PdfConfig dataclass
│       ├── nav.py                 # mkdocs.yml nav resolution
│       ├── aggregator.py          # Markdown aggregation and page boundary insertion
│       ├── assets.py              # local image detection, copy, and path rewriting
│       ├── manifest.py            # build manifest generation
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── pandoc.py          # Pandoc subprocess adapter
│       │   └── typst.py           # Typst subprocess adapter
│       └── doctor.py              # environment validation checks
├── tests/
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_nav.py
│   │   ├── test_aggregator.py
│   │   ├── test_assets.py
│   │   ├── test_manifest.py
│   │   └── test_doctor.py
│   └── integration/
│       └── test_aggregate_example.py
├── example/                       # minimal sample documentation project
│   ├── mkdocs.yml
│   └── docs/
│       ├── index.md
│       ├── guide.md
│       └── assets/
│           └── diagram.png
├── .github/
│   └── workflows/
│       └── pdf.yml                # GitHub Actions PDF build workflow
├── pyproject.toml
└── README.md
```

**Structure Decision**: Single-project `src/` layout. The `adapters/` subpackage isolates external-tool invocations so tests can inject fakes without patching `subprocess` directly. The `example/` directory doubles as the integration test fixture.

---

## Complexity Tracking

No constitution violations requiring justification.
