# Research: zensical-pdf CLI Generator

**Phase 0 output for**: `specs/001-pdf-cli-generator/plan.md`
**Date**: 2026-08-10

---

## 1. Python src layout packaging

**Decision**: Use `src/zensical_pdf/` layout with `pyproject.toml` (PEP 517/518). Entry point declared under `[project.scripts]` as `zensical-pdf = "zensical_pdf.cli:app"`.

**Rationale**: The `src/` layout prevents accidental imports of the package from the repository root during development, catches missing `pip install -e .` errors early, and is the modern Python packaging standard recommended by PyPA.

**Alternatives considered**:
- Flat layout (`zensical_pdf/` at root) — rejected because it makes it easy to import local code without installing, masking packaging issues.
- Namespace packages — rejected, no need for namespace here.

---

## 2. typer CLI framework

**Decision**: Use `typer` with a single `app = typer.Typer()` and four commands: `inspect_nav`, `aggregate`, `build`, `doctor`. Each command function receives a `project_dir: Path` option defaulting to the current working directory.

**Rationale**: Typer provides automatic `--help`, type-checked argument parsing, and clean subcommand composition. It wraps Click, which is battle-tested for Python CLI tools. It integrates naturally with rich via `rich.console.Console`.

**Key patterns**:
- `typer.Option(Path("."), "--project-dir", "-p", help="Documentation project root")` as shared option across commands.
- `typer.Exit(code=1)` for fatal errors; never `sys.exit()` directly.
- Annotate with `Annotated[Path, typer.Option(...)]` for modern typer style.

**Alternatives considered**:
- `click` directly — rejected; typer adds type safety with minimal overhead.
- `argparse` — rejected; more boilerplate, no modern annotation support.

---

## 3. rich terminal output

**Decision**: Create a single module-level `console = Console(stderr=True)` for warnings/errors and a `stdout_console = Console()` for structured output (e.g., `inspect-nav` file listing). Use `console.print("[yellow]WARNING[/]", ...)` for warnings and `console.print("[red]ERROR[/]", ...)` for fatal errors before `typer.Exit(1)`.

**Rationale**: Separating structured output (stdout) from diagnostics (stderr) allows the tool to be used in pipelines. Rich provides no-dependency fallback on terminals that don't support color (via `Console(force_terminal=False)`).

**Key patterns**:
- `rich.panel.Panel` for `doctor` command results.
- `rich.table.Table` for `inspect-nav` file listing.
- `rich.progress.Progress` for long-running `build` steps.

**Alternatives considered**:
- `click.echo` — rejected; no formatting, no color without extra deps.
- `logging` module — rejected; logs are for library internals, not CLI output.

---

## 4. mkdocs.yml nav parsing

**Decision**: Use `pyyaml` (`yaml.safe_load`) to parse `mkdocs.yml`. Walk the `nav` list recursively. Each leaf is either a `str` (page path) or a dict with one key (section title) mapping to a list (sub-nav). Flatten to an ordered list of `Path` objects relative to `docs_dir`. Skip non-`.md` entries with a warning.

**Rationale**: `pyyaml` is the standard library for YAML in Python. `yaml.safe_load` avoids arbitrary object instantiation from untrusted files. The recursive walk handles arbitrarily nested nav sections.

**Key edge cases**:
- Nav entry is a bare string (page with no title): treat as path directly.
- Nav entry is a dict with a single key: title → [list of children].
- Nav entry references a file that doesn't exist: fatal error unless `--permissive`.
- Nav is absent from `mkdocs.yml`: fall back to sorted scan.
- `docs_dir` absent from `mkdocs.yml`: default to `docs`.

**Alternatives considered**:
- `ruamel.yaml` — rejected; full round-trip YAML is not needed; adds dependency weight.

---

## 5. TOML parsing (zensical-pdf.toml)

**Decision**: Use `tomllib` (Python 3.11+ stdlib) with a fallback to `tomli` for Python 3.10. Detect at import time:

```python
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]
```

Declare `tomli` as an optional dependency in `pyproject.toml` under `[project.optional-dependencies]` as `legacy-python = ["tomli>=2.0"]`, but include it in the default `[project.dependencies]` since Python 3.10 is still in use in many CI environments.

**Decision revised**: Include `tomli` unconditionally in `[project.dependencies]` for Python < 3.11 support. Use the `sys.version_info` guard at import time.

**Rationale**: `tomllib` is in the stdlib from 3.11. `tomli` is a zero-dependency backport that is API-identical. The try/except import pattern is the recommended approach.

**Alternatives considered**:
- Require Python 3.11+ — rejected; too restrictive for current consulting environments.
- Use `tomli` only — rejected; unnecessary dependency on 3.11+.

---

## 6. Pandoc adapter design

**Decision**: Define a `PandocAdapter` class with a single method `convert(input_path: Path, output_path: Path) -> None`. The adapter calls:

```
pandoc input_path --from=markdown --to=typst --output=output_path
```

using `subprocess.run([...], check=True)`. If the process fails, raise a `PandocError` with the stderr content. If `pandoc` is not found (`FileNotFoundError`), raise `PandocNotFoundError` with an install hint.

**Rationale**: Wrapping in a class enables the CLI to accept a `pandoc_adapter` argument during testing, allowing tests to inject a `FakePandocAdapter` without patching `subprocess`. This is simpler and more reliable than `unittest.mock.patch`.

**Key flags**:
- `--from=markdown` — explicit input format.
- `--to=typst` — Typst output format (supported since Pandoc 3.1.2).
- `--standalone` — optional; produces a complete Typst document.
- `--output=<path>` — explicit output file; do not rely on stdout.

**Pandoc version requirement**: Typst writer requires Pandoc ≥ 3.1.2. The `doctor` command checks `pandoc --version` output and warns if below this version.

**Alternatives considered**:
- `pypandoc` Python wrapper — rejected; adds an opaque dependency layer and complicates version checks. Direct `subprocess` is more transparent and avoids an extra install step.

---

## 7. Typst adapter design

**Decision**: Define a `TypstAdapter` class with method `compile(input_path: Path, output_path: Path) -> None`. The adapter calls:

```
typst compile input_path output_path
```

using `subprocess.run([...], check=True)`. If the process fails, raise `TypstError` with stderr content. If `typst` is not found, raise `TypstNotFoundError` with an install hint.

**Rationale**: Same rationale as Pandoc adapter — injectable for tests, simple subprocess interface.

**Alternatives considered**:
- `pytypst` or similar — no mature Python wrapper exists for Typst. Subprocess is the correct approach.

---

## 8. Image path rewriting

**Decision**: Use a regex-based scan of each Markdown file's content for image references in both Markdown syntax (`![alt](path)`) and HTML `<img src="path">` patterns. For each match:
1. If the path starts with `http://` or `https://`, leave unchanged.
2. If the path is a relative local path, resolve it against the source file's directory.
3. Copy the resolved file to `build/pdf/assets/<flat-name>` (using a hash prefix if names collide).
4. Rewrite the image reference to point to the new relative path from `build/pdf/combined.md`.

**Rationale**: Regex is sufficient for the common patterns in MkDocs documentation. Full HTML parsing is not needed for v1. The flat copy approach avoids directory traversal complexity.

**Missing asset policy**: Configurable — default is `warn` (emit warning, continue); can be set to `error` in `zensical-pdf.toml` under `[pdf] missing_asset_policy = "error"`.

**Alternatives considered**:
- `mistune` or `markdown-it-py` for AST-based rewriting — rejected for v1; adds dependency and complexity beyond what's needed.

---

## 9. Build manifest format

**Decision**: Write a JSON manifest to `build/pdf/manifest.json` after aggregation and to `dist/manifest.json` after the full build. Structure:

```json
{
  "generated_at": "<ISO 8601 timestamp>",
  "project_dir": "<absolute path>",
  "config_file": "<path or null>",
  "docs_dir": "<path>",
  "pages": ["<relative path>", ...],
  "assets": [{"source": "<original path>", "copied_to": "<build path>"}],
  "output": "<path to final PDF>"
}
```

**Rationale**: JSON is readable by humans and machines. The manifest supports CI artifact tracking and debugging.

**Alternatives considered**:
- TOML manifest — rejected; TOML has no standard write library in stdlib (only read via `tomllib`).
- Plain text — rejected; structured data requires structured format.

---

## 10. GitHub Actions workflow

**Decision**: Provide a `.github/workflows/pdf.yml` that:
1. Checks out the calling repository.
2. Sets up Python.
3. Installs `pandoc` and `typst` via the official install actions or direct download.
4. Runs `pip install zensical-pdf`.
5. Runs `zensical-pdf build`.
6. Uploads `dist/` as a workflow artifact.

The workflow runs on `push` to `main` and can be triggered manually via `workflow_dispatch`.

**Rationale**: Provides a ready-to-use CI template that secondary users (project teams) can copy into their documentation repositories with minimal modification.

**Pandoc install**: Use `pandoc/actions/setup@v1` or direct download from GitHub Releases since no official GitHub Action exists for all platforms.
**Typst install**: Use `typst-community/setup-typst@v4` GitHub Action.

---

## 11. Heading normalization strategy

**Decision**: When `normalize_headings = true` in `[pdf]` config, shift all headings in each source file so that the top-level heading becomes H2 (reserving H1 for the document title injected by the Typst template). This prevents multiple H1s from appearing in the final PDF.

**Algorithm**: For each Markdown file, find the minimum heading level present. If it is H1 (`#`), add 1 to all heading levels in that file before aggregation.

**Rationale**: Most MkDocs documentation uses H1 as the page title. When aggregated, multiple H1s break document structure. Shifting to H2 preserves relative hierarchy while allowing the Typst template to inject a document-level H1.

**Alternatives considered**:
- Always shift regardless of presence — rejected; would corrupt documents that correctly start at H2.
- Never shift — rejected; multiple H1s produce poor PDF structure.

---

## 12. YAML front matter handling

**Decision**: Strip YAML front matter (content between `---` delimiters at the start of a file) before aggregating file content. Front matter is not included in the combined Markdown.

**Rationale**: YAML front matter is metadata for the web publishing system. Including it in the aggregated Markdown would cause it to appear as document content or confuse Pandoc.

**Alternatives considered**:
- Extract and use front matter fields (e.g., `title`) — deferred to future version; not needed for v1.
