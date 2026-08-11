# Tasks: zensical-pdf CLI Generator

**Input**: Design documents from `specs/001-pdf-cli-generator/`

**Prerequisites**: plan.md ✓ | spec.md ✓ | research.md ✓ | data-model.md ✓ | contracts/ ✓ | quickstart.md ✓

**Tests**: Unit tests included for all pure-Python logic. Integration test included for example project aggregation. Pandoc and Typst invocations are tested via injectable fake adapters — no real tools required for the unit suite.

**Organization**: Tasks are grouped by implementation dependency order. US2 and US3 are implemented before US1 because the build pipeline depends on nav resolution and aggregation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no blocking dependencies on other in-progress tasks)
- **[Story]**: User story this task delivers ([US1]–[US5] from spec.md)
- Exact file paths are included in every task description

## Path Conventions

- Source: `src/zensical_pdf/`
- Tests: `tests/unit/`, `tests/integration/`
- Example project: `example/`
- Config: `pyproject.toml` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the project scaffold — packaging, entry point, error hierarchy, and test infrastructure.

- [x] T001 Create `pyproject.toml` with `[build-system]`, `[project]` (name, version, requires-python ≥ 3.10, dependencies: typer, rich, pyyaml, tomli), `[project.scripts]` entry point `zensical-pdf = "zensical_pdf.cli:app"`, and `[project.optional-dependencies]` dev group (pytest)
- [x] T002 Create `src/zensical_pdf/__init__.py` defining `ZensicalPdfError(Exception)` and all domain exception subclasses: `ConfigNotFoundError`, `NavResolutionError`, `AggregationError`, `AssetError`, `PandocNotFoundError`, `PandocError`, `TypstNotFoundError`, `TypstError`
- [x] T003 [P] Create `src/zensical_pdf/adapters/__init__.py` (empty package marker)
- [x] T004 [P] Create `tests/unit/` and `tests/integration/` directories with `__init__.py` files; create `tests/conftest.py` with a shared `project_dir` fixture using `tmp_path`
- [x] T005 [P] Create `example/mkdocs.yml` with `site_name`, `docs_dir: docs`, and a two-page `nav` (index.md and guide.md); create `example/docs/index.md`, `example/docs/guide.md`, and `example/docs/assets/diagram.png` (1×1 pixel PNG) as the integration test fixture

**Checkpoint**: `pip install -e .[dev]` succeeds; `zensical-pdf --help` shows the app name; pytest collects zero tests without errors.

---

## Phase 2: Foundational — PdfConfig and Configuration Discovery

**Purpose**: Core configuration model that all four commands depend on. Covers all config sources including `zensical-pdf.toml` (US5), `mkdocs.yml` metadata, and conventional defaults.

⚠️ CRITICAL: No user story implementation can begin until this phase is complete.

- [x] T006 Define `PdfConfig` dataclass in `src/zensical_pdf/config.py` with all fields from data-model.md: `project_dir`, `docs_dir`, `output`, `build_dir`, `title`, `subtitle`, `author`, `version`, `template`, `normalize_headings`, `include_toc`, `number_sections`, `missing_asset_policy`, `permissive`, `detected_config`
- [x] T007 [P] Implement `load_toml_config(project_dir: Path) -> dict` in `src/zensical_pdf/config.py` using `tomllib`/`tomli` try/except import pattern; reads `zensical-pdf.toml` if present
- [x] T008 [P] Implement `load_mkdocs_metadata(project_dir: Path) -> dict` in `src/zensical_pdf/config.py` using `yaml.safe_load`; extracts `site_name` and `docs_dir` only (nav is read separately by `nav.py`)
- [x] T009 Implement `resolve_config(project_dir: Path, **cli_overrides) -> PdfConfig` in `src/zensical_pdf/config.py` applying priority order: CLI args → `zensical-pdf.toml` → `mkdocs.yml` → `zensical.toml` → defaults; raise `ConfigNotFoundError` if no config and no `docs/` directory found
- [x] T010 [P] Write unit tests for config discovery priority, TOML loading, mkdocs.yml metadata extraction, and `ConfigNotFoundError` in `tests/unit/test_config.py`

**Checkpoint**: `resolve_config(Path("example/"))` returns a `PdfConfig` with `docs_dir = example/docs` and `title = "Example Guide"` (from `example/mkdocs.yml`).

---

## Phase 3: User Story 2 — inspect-nav Command

**Goal**: Users can inspect the resolved page order before committing to a full build.

**Independent Test**: `zensical-pdf inspect-nav --project-dir example/` lists two pages in nav order without errors.

**Spec priority**: P2 — but required before US1 (build depends on nav resolution).

### Tests for User Story 2

- [x] T011 [P] [US2] Write unit tests for `resolve_nav()` covering: nav with nested sections, no nav (sorted scan fallback + warning), missing file strict mode (raises `NavResolutionError`), missing file permissive mode (warning + continues), external URL nav entries (skipped with warning) in `tests/unit/test_nav.py`

### Implementation for User Story 2

- [x] T012 [P] [US2] Define `NavEntry` and `NavResult` dataclasses in `src/zensical_pdf/nav.py` with fields from data-model.md
- [x] T013 [US2] Implement `_walk_nav(nav_list, docs_dir, permissive) -> list[NavEntry]` recursive walker in `src/zensical_pdf/nav.py`; handle bare string entries, single-key dict entries (title → path), and section-grouping dict entries (title → list); skip non-`.md` entries with a warning
- [x] T014 [US2] Implement `_scan_docs_dir(docs_dir) -> list[NavEntry]` sorted fallback scanner in `src/zensical_pdf/nav.py`
- [x] T015 [US2] Implement `resolve_nav(config: PdfConfig) -> NavResult` in `src/zensical_pdf/nav.py`; try `mkdocs.yml` nav first, fall back to scan, set `NavResult.source` accordingly
- [x] T016 [US2] Implement `inspect_nav` typer command in `src/zensical_pdf/cli.py`; print summary header and rich Table of resolved pages to stdout; emit warnings to stderr via `Console(stderr=True)`; exit 1 on `NavResolutionError`

**Checkpoint**: `zensical-pdf inspect-nav --project-dir example/` exits 0 and lists `index.md`, `guide.md` in nav order.

---

## Phase 4: User Story 3 — aggregate Command

**Goal**: Users can produce the combined Markdown intermediate and inspect it before running the full PDF build.

**Independent Test**: `zensical-pdf aggregate --project-dir example/` writes `example/build/pdf/combined.md` with source boundary markers, copies `diagram.png` to `build/pdf/assets/`, and leaves source files unmodified.

**Spec priority**: P2 — but required before US1 (build depends on aggregation).

### Tests for User Story 3

- [ ] T017 [P] [US3] Write unit tests for YAML front matter stripping in `tests/unit/test_aggregator.py`
- [ ] T018 [P] [US3] Write unit tests for heading normalization (H1 → H2 shift when `normalize_headings=True`, no change when already H2+) in `tests/unit/test_aggregator.py`
- [ ] T019 [P] [US3] Write unit tests for image path detection (local relative, external URL, HTML img tag) in `tests/unit/test_assets.py`
- [ ] T020 [P] [US3] Write unit tests for asset copy and path rewrite, collision handling (hash prefix), and missing asset policy (`warn` vs `error`) in `tests/unit/test_assets.py`
- [ ] T021 [P] [US3] Write unit tests for manifest JSON serialization and field completeness in `tests/unit/test_manifest.py`
- [ ] T022 [US3] Write integration test: run aggregation against `example/` project using `tmp_path`; assert `combined.md` exists, contains boundary markers for both pages, image path is rewritten, source files unmodified in `tests/integration/test_aggregate_example.py`

### Implementation for User Story 3

- [ ] T023 [P] [US3] Implement `strip_front_matter(content: str) -> str` in `src/zensical_pdf/aggregator.py`; remove YAML block between leading `---` delimiters
- [ ] T024 [P] [US3] Implement `normalize_headings(content: str) -> str` in `src/zensical_pdf/aggregator.py`; detect minimum heading level; if H1 present, shift all headings up by 1
- [ ] T025 [P] [US3] Implement `find_local_images(content: str) -> list[str]` in `src/zensical_pdf/assets.py` using regex matching `![alt](path)` and `<img src="path">`; exclude `http://` and `https://` URLs
- [ ] T026 [US3] Implement `copy_asset(src_path: Path, assets_dir: Path) -> Path` in `src/zensical_pdf/assets.py`; resolve collisions with a short SHA-256 prefix on the filename
- [ ] T027 [US3] Implement `rewrite_image_paths(content: str, source_file: Path, assets_dir: Path, missing_policy: str, warnings: list) -> tuple[str, list[AssetCopy]]` in `src/zensical_pdf/assets.py`; copies files, rewrites references, respects missing policy
- [ ] T028 [US3] Implement `aggregate(config: PdfConfig, nav_result: NavResult) -> AggregatedDocument` in `src/zensical_pdf/aggregator.py`; iterates pages, strips front matter, optionally normalizes headings, inserts `<!-- source: <relative_path> -->` boundary markers, calls asset rewriting for each page, writes `build/pdf/combined.md`
- [ ] T029 [P] [US3] Define `BuildManifest` and `AssetManifestEntry` dataclasses in `src/zensical_pdf/manifest.py`
- [ ] T030 [US3] Implement `write_aggregation_manifest(config, nav_result, agg_doc) -> Path` in `src/zensical_pdf/manifest.py`; writes JSON to `build/pdf/manifest.json` per manifest-schema.md contract
- [ ] T031 [US3] Implement `aggregate` typer command in `src/zensical_pdf/cli.py`; call `resolve_config`, `resolve_nav`, `aggregate`, `write_aggregation_manifest`; use `rich.progress.Progress` for page-by-page feedback; exit 1 on `AggregationError` or `AssetError`

**Checkpoint**: `pytest tests/unit/test_aggregator.py tests/unit/test_assets.py tests/unit/test_manifest.py tests/integration/` all pass without Pandoc or Typst installed.

---

## Phase 5: User Story 1 — build Command (Priority: P1) 🎯 MVP

**Goal**: Users can generate a PDF from an existing MkDocs documentation project with one command.

**Independent Test**: `zensical-pdf build --project-dir example/` (with Pandoc and Typst installed) writes `example/dist/documentation.pdf`, leaves source files unmodified, and writes `dist/manifest.json`.

### Tests for User Story 1

- [ ] T032 [P] [US1] Write unit tests for `PandocAdapter` using a `FakePandocAdapter` that records calls; assert correct arguments (input path, `--from=markdown`, `--to=typst`, `--output`) in `tests/unit/test_pandoc_adapter.py`
- [ ] T033 [P] [US1] Write unit tests for `TypstAdapter` using a `FakeTypstAdapter` that records calls; assert correct arguments (compile, input, output) in `tests/unit/test_typst_adapter.py`

### Implementation for User Story 1

- [ ] T034 [P] [US1] Implement `PandocAdapter` class in `src/zensical_pdf/adapters/pandoc.py` with `convert(input_path: Path, output_path: Path) -> None`; call `subprocess.run(["pandoc", str(input_path), "--from=markdown", "--to=typst", "--standalone", f"--output={output_path}"], check=True, capture_output=True)`; raise `PandocNotFoundError` on `FileNotFoundError`, `PandocError` on non-zero exit
- [ ] T035 [P] [US1] Implement `TypstAdapter` class in `src/zensical_pdf/adapters/typst.py` with `compile(input_path: Path, output_path: Path) -> None`; call `subprocess.run(["typst", "compile", str(input_path), str(output_path)], check=True, capture_output=True)`; raise `TypstNotFoundError` on `FileNotFoundError`, `TypstError` on non-zero exit
- [ ] T036 [US1] Implement `write_build_manifest(config, nav_result, agg_doc, typst_path) -> Path` in `src/zensical_pdf/manifest.py`; writes final manifest JSON to `dist/manifest.json` with `intermediate_typst` and `output` fields populated
- [ ] T037 [US1] Implement `build` typer command in `src/zensical_pdf/cli.py`; accept optional `--output` override; call `resolve_config` → `resolve_nav` → `aggregate` → `write_aggregation_manifest` → `PandocAdapter.convert` → `TypstAdapter.compile` → `write_build_manifest`; use `rich.progress.Progress` with named steps; exit 1 with actionable message on any adapter error

**Checkpoint**: Unit tests pass without Pandoc/Typst. With real tools installed: `zensical-pdf build --project-dir example/` produces `example/dist/documentation.pdf`.

---

## Phase 6: User Story 4 — doctor Command

**Goal**: Users and CI environments can validate that all required tools are present before running a build.

**Independent Test**: `zensical-pdf doctor --project-dir example/` exits 0 in a complete environment and prints all six checks with status ✓.

**Spec priority**: P3 — implemented after the core pipeline; does not block US1–US3.

### Tests for User Story 4

- [ ] T038 [P] [US4] Write unit tests for each `DoctorCheck` function in `tests/unit/test_doctor.py`; mock `subprocess.run` return values to simulate Pandoc/Typst present, absent, and wrong-version scenarios

### Implementation for User Story 4

- [ ] T039 [P] [US4] Define `DoctorCheck` and `DoctorResult` dataclasses in `src/zensical_pdf/doctor.py`
- [ ] T040 [P] [US4] Implement `check_python_version() -> DoctorCheck` in `src/zensical_pdf/doctor.py`; pass if `sys.version_info >= (3, 10)`
- [ ] T041 [P] [US4] Implement `check_pandoc() -> DoctorCheck` in `src/zensical_pdf/doctor.py`; run `["pandoc", "--version"]`, parse version string, pass if ≥ 3.1.2, warn if found but below minimum, fail if not found
- [ ] T042 [P] [US4] Implement `check_typst() -> DoctorCheck` in `src/zensical_pdf/doctor.py`; run `["typst", "--version"]`, pass if found, fail with install hint if not found
- [ ] T043 [P] [US4] Implement `check_project_config(project_dir: Path) -> DoctorCheck` in `src/zensical_pdf/doctor.py`; pass if any of `zensical-pdf.toml`, `mkdocs.yml`, `zensical.toml` is found
- [ ] T044 [P] [US4] Implement `check_docs_dir(config: PdfConfig) -> DoctorCheck` in `src/zensical_pdf/doctor.py`; pass if `config.docs_dir` exists and is a directory
- [ ] T045 [P] [US4] Implement `check_output_dir(config: PdfConfig) -> DoctorCheck` in `src/zensical_pdf/doctor.py`; pass if `config.output.parent` exists or can be created
- [ ] T046 [US4] Implement `run_doctor(config: PdfConfig) -> DoctorResult` in `src/zensical_pdf/doctor.py`; run all six checks and return `DoctorResult`
- [ ] T047 [US4] Implement `doctor` typer command in `src/zensical_pdf/cli.py`; render `DoctorResult` as a rich `Panel` with ✓/⚠/✗ symbols; exit 1 if any check has `status == "fail"`

**Checkpoint**: `zensical-pdf doctor --project-dir example/` exits 0 with all checks ✓ (when Pandoc and Typst are installed). Doctor command does not create or modify any files.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: CI integration, documentation, and end-to-end validation.

- [ ] T048 [P] Create `.github/workflows/pdf.yml` GitHub Actions workflow: checkout → setup Python → install pandoc via direct download → install typst via `typst-community/setup-typst@v4` → `pip install .` → `zensical-pdf build --project-dir example/` → upload `example/dist/` as artifact; trigger on push to main and `workflow_dispatch`
- [ ] T049 [P] Add `example/zensical-pdf.toml` with `[project]` title/author and `[paths]` output demonstrating per-project configuration (validates US5 scenario from quickstart.md)
- [ ] T050 [P] Write `README.md` covering: installation (`pip install zensical-pdf`), prerequisites (Pandoc ≥ 3.1.2, Typst), quick start (doctor → inspect-nav → build), `zensical-pdf.toml` configuration reference, and link to `example/`
- [ ] T051 Run all quickstart.md validation scenarios locally against `example/`; document any deviations from expected output

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
  └── Phase 2 (Foundational / PdfConfig)
        ├── Phase 3 (US2 / inspect-nav)
        ├── Phase 4 (US3 / aggregate)   ← depends on Phase 3 (uses NavResult)
        │     └── Phase 5 (US1 / build) ← depends on Phase 4 (uses AggregatedDocument)
        └── Phase 6 (US4 / doctor)      ← independent; can start after Phase 2
Phase 7 (Polish) ← depends on all phases complete
```

### Parallel Opportunities Within Phases

**Phase 1**: T001, T002, T003, T004, T005 can all start in parallel once the repo is cloned.

**Phase 2**: T007 and T008 can be written in parallel; T009 can start after T006 is defined.

**Phase 3**: T011 (tests) and T012 (dataclasses) are parallel; T013, T014, T015 are sequential; T016 (CLI) follows T015.

**Phase 4**: Test tasks T017–T021 are all parallel; implementation tasks T023–T025 are parallel; T026, T027 follow their respective dependencies; T028 follows T023–T027; T029 is parallel to T028.

**Phase 5**: T032, T033 (tests) and T034, T035 (adapters) can be written in parallel since they operate on different files.

**Phase 6**: All DoctorCheck functions T040–T045 are parallel.

**Phase 7**: T048, T049, T050 are parallel.

### Implementation Strategy

**MVP** (minimum to deliver US1 end-to-end value):
Complete Phases 1–5 in order. After Phase 5, `zensical-pdf build` produces a PDF. This is the primary deliverable.

**Incremental delivery**:
- After Phase 3: US2 fully functional (inspect-nav)
- After Phase 4: US3 fully functional (aggregate); US2 remains functional
- After Phase 5: US1 fully functional (build); US2 and US3 remain functional
- After Phase 6: US4 fully functional (doctor)
- After Phase 7: US5 demonstrated (example/zensical-pdf.toml); CI workflow ready

---

## Summary

| Phase | Tasks | User Story | Parallel opportunities |
|-------|-------|------------|----------------------|
| 1 — Setup | T001–T005 | Foundation | T001–T005 all parallel |
| 2 — Foundational | T006–T010 | US5 (config) | T007, T008, T010 parallel |
| 3 — inspect-nav | T011–T016 | US2 (P2) | T011, T012 parallel |
| 4 — aggregate | T017–T031 | US3 (P2) | T017–T025, T029 parallel |
| 5 — build | T032–T037 | US1 (P1) 🎯 | T032–T035 parallel |
| 6 — doctor | T038–T047 | US4 (P3) | T038–T045 parallel |
| 7 — Polish | T048–T051 | All | T048–T050 parallel |

**Total tasks**: 51
**Parallelizable tasks**: 30 (marked [P])
**Suggested MVP scope**: Phases 1–5 (T001–T037)
