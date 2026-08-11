# Quickstart Validation Guide: zensical-pdf CLI Generator

**Phase 1 output for**: `specs/001-pdf-cli-generator/plan.md`
**Date**: 2026-08-10

This guide documents how to validate the feature works end-to-end after implementation. It is a run/test guide, not an implementation guide.

---

## Prerequisites

- Python 3.10 or later
- Pandoc 3.1.2 or later installed and on PATH
- Typst installed and on PATH
- The `example/` directory from this repository

Verify your environment:

```bash
zensical-pdf doctor --project-dir example/
```

Expected: all checks pass.

---

## Scenario 1: Inspect navigation

Validates that nav resolution from `mkdocs.yml` works correctly.

```bash
zensical-pdf inspect-nav --project-dir example/
```

**Expected output (stdout)**:
```
Project directory : example
Config file       : mkdocs.yml
Docs directory    : example/docs
Pages (2 total)   :
  1. docs/index.md
  2. docs/guide.md
```

**Pass criteria**:
- Exit code 0
- Files listed in nav order (matching order in `example/mkdocs.yml`)
- No errors on stderr

---

## Scenario 2: Aggregate without building

Validates Markdown aggregation, source boundary markers, and asset copying.

```bash
zensical-pdf aggregate --project-dir example/
```

**Pass criteria**:
- Exit code 0
- `example/build/pdf/combined.md` exists
- `combined.md` contains a source boundary comment before each page's content
- `example/build/pdf/assets/diagram.png` exists (copied from `example/docs/assets/`)
- Image reference in `combined.md` points to `assets/diagram.png`
- `example/build/pdf/manifest.json` exists and is valid JSON
- Source Markdown files in `example/docs/` are unmodified

**Verify combined.md content**:

```bash
grep -c "<!-- source:" example/build/pdf/combined.md  # should be 2 (one per page)
grep "assets/diagram.png" example/build/pdf/combined.md  # should find rewritten path
```

---

## Scenario 3: Full build

Validates the complete pipeline from nav through PDF.

```bash
zensical-pdf build --project-dir example/
```

**Pass criteria**:
- Exit code 0
- `example/dist/documentation.pdf` exists
- `example/build/pdf/document.typ` exists (Typst intermediate)
- `example/dist/manifest.json` exists with `output` field set
- Source files in `example/docs/` are unmodified

---

## Scenario 4: Doctor in complete environment

```bash
zensical-pdf doctor --project-dir example/
```

**Pass criteria**:
- Exit code 0
- All six checks shown with status ✓ pass
- No check shows ✗ fail

---

## Scenario 5: Doctor with missing Pandoc (negative test)

Temporarily rename or remove pandoc from PATH, then run:

```bash
zensical-pdf doctor --project-dir example/
```

**Pass criteria**:
- Exit code 1
- Pandoc check shows ✗ fail
- Output includes install hint (URL to pandoc.org)
- No files modified

---

## Scenario 6: Build fails gracefully when Pandoc missing

```bash
# With pandoc not on PATH:
zensical-pdf build --project-dir example/
```

**Pass criteria**:
- Exit code 1
- Stderr contains: `ERROR: Pandoc is not available on PATH.`
- Stderr contains an install hint
- No partial output left in `dist/`

---

## Scenario 7: Missing nav file (strict mode)

Edit `example/mkdocs.yml` to reference a file that does not exist, then:

```bash
zensical-pdf inspect-nav --project-dir example/
```

**Pass criteria**:
- Exit code 1
- Error message identifies the missing file by path

---

## Scenario 8: Missing nav file (permissive mode)

Same setup as Scenario 7, but run:

```bash
zensical-pdf inspect-nav --project-dir example/ --permissive
```

**Pass criteria**:
- Exit code 0
- Warning emitted on stderr for the missing file
- Remaining valid pages still listed

---

## Scenario 9: External image URL is not rewritten

Add an external image to one of the example docs:

```markdown
![logo](https://example.com/logo.png)
```

Run `zensical-pdf aggregate --project-dir example/` and inspect `combined.md`.

**Pass criteria**:
- The URL `https://example.com/logo.png` is unchanged in `combined.md`
- No asset copy entry for this URL in `build/pdf/manifest.json`

---

## Scenario 10: Custom output path via config

Create `example/zensical-pdf.toml`:

```toml
[project]
title = "Example Guide"

[paths]
output = "dist/example-guide.pdf"
```

Run `zensical-pdf build --project-dir example/`.

**Pass criteria**:
- PDF written to `example/dist/example-guide.pdf`
- Not written to `example/dist/documentation.pdf`

---

## Unit test pass criteria (no Pandoc or Typst required)

Run the full unit test suite:

```bash
pytest tests/unit/ -v
```

**Pass criteria**:
- All unit tests pass without Pandoc or Typst installed
- Tests cover: config discovery, nav parsing (mkdocs.yml with and without nav), aggregation, source boundary insertion, heading normalization, image path rewriting (local and external), asset copy logic, manifest generation, doctor checks

---

## Integration test pass criteria

```bash
pytest tests/integration/ -v
```

**Pass criteria**:
- `test_aggregate_example.py` produces a valid `combined.md` from the `example/` project
- Aggregation result matches expected page count and includes boundary markers
- No source files are modified

---

## References

- CLI contract: [contracts/cli-schema.md](contracts/cli-schema.md)
- Config contract: [contracts/config-schema.md](contracts/config-schema.md)
- Manifest contract: [contracts/manifest-schema.md](contracts/manifest-schema.md)
- Data model: [data-model.md](data-model.md)
- Implementation slices: vertical order defined in [plan.md](plan.md)
