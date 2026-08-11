# Feature Specification: zensical-pdf CLI Generator

**Feature Branch**: `001-pdf-cli-generator`

**Created**: 2026-08-10

**Status**: Draft

## Feature summary

zensical-pdf is a reusable Python CLI for generating PDF deliverables from Zensical and MkDocs-style documentation projects.

It reads documentation source files, resolves page order, aggregates Markdown, converts the result to Typst using Pandoc, compiles the PDF using Typst, and writes a final PDF artifact that can be published or shared with customers.

## Problem statement

Zensical does not yet provide complete native PDF conversion support equivalent to the prior MkDocs/Material ecosystem. Teams still need a repeatable way to create customer-friendly PDFs from documentation projects being authored for Zensical web publishing.

Manual PDF creation is too slow and inconsistent for multiple consulting projects. Browser print-to-PDF workflows are not reliable enough for multi-page, multi-section deliverables. Maintaining a parallel MkDocs PDF pipeline introduces long-term maintenance burden.

## Target users

### Primary user

A technical consultant or documentation author who maintains Zensical or MkDocs-style Markdown documentation and needs to generate a polished PDF deliverable.

### Secondary user

A project team that wants GitHub Actions to automatically publish both a Zensical web site and a PDF artifact.

### Tertiary user

A developer who wants to extend or customize the Markdown-to-PDF pipeline for organization-specific documentation templates.

## User goals

1. Generate a PDF from an existing documentation project with one command.
2. Reuse the same tool across many repositories.
3. Avoid manually copying documentation into Word or another PDF authoring tool.
4. Preserve the navigation order from mkdocs.yml where available.
5. Produce actionable diagnostics when PDF generation fails.
6. Customize title, author, version, output path, and template per project.
7. Use the tool locally and in GitHub Actions.
8. Keep the design open for a future native Zensical module or plugin wrapper.

## Non-goals for initial release

- Full reproduction of the visual theme of a Zensical or Material for MkDocs web site.
- Native Zensical plugin implementation.
- Support for every Material for MkDocs extension.
- Browser rendering pipeline.
- Modification of source documentation files.
- Separate PDF-specific copy of documentation content.

## Supported project types

### Required for MVP

- MkDocs-style project with `mkdocs.yml`
- Documentation source directory defined by `docs_dir`, defaulting to `docs` if omitted
- `nav` tree containing Markdown file references
- Markdown files under the docs directory
- Local image assets referenced by relative paths

### Required fallback behavior

If `mkdocs.yml` is not available but a `docs` directory exists, the tool scans Markdown files in stable sorted order and generates a warning that nav ordering was not available.

### Zensical support for initial release

If `zensical.toml` exists, the tool detects it and extracts safe metadata where practical. If page navigation cannot be resolved from `zensical.toml`, the tool falls back to sorted Markdown scanning and warns the user. The implementation must not invent undocumented Zensical behavior.

### Future support (out of scope for v1)

- Richer Zensical configuration support
- Native Zensical extension or module wrapper
- Browser-rendered PDF mode
- Mermaid pre-rendering
- Admonition conversion
- Tabbed content conversion
- Automatic anchor rewriting
- Multi-PDF output sets

---

## User Scenarios & Testing

### User Story 1 - Generate PDF from an MkDocs project (Priority: P1)

A consultant has a documentation project with `mkdocs.yml` and wants to produce a PDF for a customer. They run `zensical-pdf build` from the project root and receive a PDF at `dist/documentation.pdf`.

**Why this priority**: This is the primary value delivery. Everything else supports or extends this scenario.

**Independent Test**: Run `zensical-pdf build` against a sample MkDocs project with `mkdocs.yml`, `docs/` directory, and at least two Markdown pages. Verify the PDF is written to `dist/documentation.pdf`.

**Acceptance Scenarios**:

1. **Given** a valid MkDocs project with `mkdocs.yml` and `nav`, **When** the user runs `zensical-pdf build`, **Then** a PDF is written to the configured output path.
2. **Given** Pandoc is not installed, **When** the user runs `zensical-pdf build`, **Then** the command exits with an actionable error explaining that Pandoc is required.
3. **Given** Typst is not installed, **When** the user runs `zensical-pdf build`, **Then** the command exits with an actionable error explaining that Typst is required.
4. **Given** a successful build, **When** the command completes, **Then** a build manifest describing inputs and outputs is written.

---

### User Story 2 - Inspect navigation without building a PDF (Priority: P2)

A consultant wants to verify which pages will be included in the PDF and in what order before committing to a full build.

**Why this priority**: Builds confidence in output before running the full pipeline. Allows troubleshooting nav issues without a slow build cycle.

**Independent Test**: Run `zensical-pdf inspect-nav` against a project with a known `nav` structure. Verify the output lists files in `nav` order with the correct docs directory path.

**Acceptance Scenarios**:

1. **Given** `mkdocs.yml` with a `nav` section, **When** the user runs `zensical-pdf inspect-nav`, **Then** the output lists Markdown files in nav order.
2. **Given** `mkdocs.yml` without a `nav` section, **When** the user runs `zensical-pdf inspect-nav`, **Then** Markdown files are listed in stable sorted order with a warning.
3. **Given** a nav entry that references a file that does not exist, **When** the user runs `zensical-pdf inspect-nav`, **Then** a fatal error is reported for the missing file.

---

### User Story 3 - Aggregate Markdown without generating a PDF (Priority: P2)

A consultant wants to inspect the combined Markdown before it is passed to Pandoc, to verify content order and identify any image path issues.

**Why this priority**: Provides an inspectable intermediate artifact and supports debugging without requiring external tools.

**Independent Test**: Run `zensical-pdf aggregate` against a sample project. Verify that `build/pdf/combined.md` is written, contains source boundary markers, and that referenced local images are copied to `build/pdf/assets/` with rewritten paths.

**Acceptance Scenarios**:

1. **Given** a valid documentation project, **When** the user runs `zensical-pdf aggregate`, **Then** `build/pdf/combined.md` is written.
2. **Given** a Markdown file containing a local image reference, **When** aggregation runs, **Then** the image is copied to `build/pdf/assets/` and the path is rewritten.
3. **Given** a Markdown file containing an external image URL, **When** aggregation runs, **Then** the URL is left unchanged.
4. **Given** a Markdown image that references a missing local file, **When** aggregation runs, **Then** a warning or fatal error is emitted according to the configured missing asset policy.

---

### User Story 4 - Validate local environment with doctor (Priority: P3)

A developer setting up a new machine or CI environment wants to confirm that all required tools are available before running a build.

**Why this priority**: Reduces friction for first-time adoption and CI environment setup. Does not block MVP value delivery.

**Independent Test**: Run `zensical-pdf doctor` in a project root. Verify the output reports the status of Pandoc, Typst, Python version, config detection, docs directory detection, and output directory write access.

**Acceptance Scenarios**:

1. **Given** a complete environment, **When** the user runs `zensical-pdf doctor`, **Then** all checks pass and the output shows each item as valid.
2. **Given** Pandoc is missing, **When** the user runs `zensical-pdf doctor`, **Then** the missing dependency is reported without modifying any project files.
3. **Given** the current directory is not a supported documentation project, **When** the user runs `zensical-pdf doctor`, **Then** the project detection check fails with an explanation.

---

### User Story 5 - Configure PDF output per project (Priority: P3)

A consultant working across multiple repositories wants each project to have its own title, author, output path, and options without editing the shared tool.

**Why this priority**: Required for multi-project reuse but can be demonstrated with a simple default configuration.

**Independent Test**: Create a `zensical-pdf.toml` with a custom `title`, `author`, and `output` path. Run `zensical-pdf build` and verify the PDF is written to the configured path.

**Acceptance Scenarios**:

1. **Given** a `zensical-pdf.toml` with a custom output path, **When** the user runs `zensical-pdf build`, **Then** the PDF is written to the configured path.
2. **Given** no `zensical-pdf.toml`, **When** the user runs `zensical-pdf build`, **Then** the PDF is written to `dist/documentation.pdf`.
3. **Given** a CLI argument that conflicts with `zensical-pdf.toml`, **When** any command runs, **Then** the CLI argument takes precedence.

---

### Edge Cases

- What happens when `mkdocs.yml` has nested nav sections (section groupings with children)?
- What happens when the docs directory contains non-Markdown files (images only, PDFs)?
- What happens when two nav entries point to the same Markdown file?
- What happens when heading levels in source documents are inconsistent across files?
- What happens when a `zensical-pdf.toml` specifies an output path in a directory that does not yet exist?
- What happens when Pandoc produces a Typst file but Typst fails to compile it?

---

## Requirements

### Functional Requirements

- **FR-001**: The package MUST expose a command named `zensical-pdf` with subcommands `inspect-nav`, `aggregate`, `build`, and `doctor`.
- **FR-002**: `inspect-nav` MUST detect project configuration and print resolved Markdown files in nav order, including project directory, detected config file, resolved docs directory, file count, ordered file list, and warnings for missing files or unsupported entries.
- **FR-003**: `aggregate` MUST write `build/pdf/combined.md`, include source boundary markers, copy local image assets to `build/pdf/assets/`, rewrite image references in the aggregated output, and write a build manifest.
- **FR-004**: `build` MUST execute the complete pipeline: resolve config → resolve nav → aggregate Markdown → convert to Typst via Pandoc → compile to PDF via Typst → write PDF to the configured output path under `dist/`.
- **FR-005**: `doctor` MUST validate Python version, Pandoc availability, Typst availability, project detection, and output directory write access without modifying source content.
- **FR-006**: The tool MUST discover configuration in priority order: CLI arguments → `zensical-pdf.toml` → `mkdocs.yml` → `zensical.toml` → conventional defaults.
- **FR-007**: The tool MUST support a `zensical-pdf.toml` file with `[project]` (title, subtitle, author, version), `[paths]` (docs_dir, output, template), and `[pdf]` (normalize_headings, include_toc, number_sections) sections.
- **FR-008**: The tool MUST NOT modify source Markdown files under any command.
- **FR-009**: The tool MUST write output only under configured build and dist directories unless explicitly configured otherwise.
- **FR-010**: When `mkdocs.yml` defines `docs_dir`, the tool MUST use that value as the documentation source directory; when absent, the tool MUST default to `docs`.
- **FR-011**: When no nav ordering is available, the tool MUST fall back to stable sorted order and emit a warning.
- **FR-012**: When a nav entry references a missing file, the tool MUST report a fatal error unless permissive mode is explicitly enabled.
- **FR-013**: When a local image in aggregated Markdown is missing, the tool MUST emit a warning or fatal error according to the configured missing asset policy.
- **FR-014**: When an image reference is an external URL, the tool MUST leave the URL unchanged.
- **FR-015**: Each major build phase MUST produce inspectable intermediate output: aggregated Markdown, copied asset directory, generated Typst file, and final PDF.

### Key Entities

- **Documentation Project**: A directory containing a configuration file (`mkdocs.yml`, `zensical.toml`, or `zensical-pdf.toml`) and a docs source directory.
- **Navigation**: An ordered list of Markdown file paths resolved from the project configuration's `nav` section or by directory scan.
- **Aggregated Document**: The single intermediate Markdown file produced by concatenating resolved pages in order with source boundary markers.
- **Build Manifest**: A file written alongside each intermediate and final artifact describing source files, copied assets, and output paths.
- **PDF Configuration**: Values from `zensical-pdf.toml` that control document metadata and output options for a specific project.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: A new user can install the tool and generate a PDF from a sample MkDocs documentation project in under 5 minutes, following only the README.
- **SC-002**: The tool processes a documentation project of 50 or more pages in under 2 minutes on standard developer hardware, assuming Pandoc and Typst are pre-installed.
- **SC-003**: Every known failure mode — missing tool, missing file, unsupported configuration — produces an error message that identifies the cause and suggests a resolution step.
- **SC-004**: The tool runs without platform-specific modification on macOS, Linux, and Windows.
- **SC-005**: Navigation parsing, Markdown aggregation, image path rewriting, and configuration detection are each covered by unit tests that pass without Pandoc or Typst installed.
- **SC-006**: The tool can be added to a GitHub Actions workflow with no modifications to the documentation source repository.
- **SC-007**: Each documentation repository can define its own title, author, output path, and PDF options through `zensical-pdf.toml` without changes to the shared tool package.

---

## Assumptions

- Pandoc and Typst are installed by the user or CI environment; the tool does not bundle or install them.
- Documentation projects use UTF-8 encoded Markdown files.
- The tool is run from the project root or with an explicit `--project-dir` argument.
- Zensical-specific admonitions and Material for MkDocs custom extensions that are not standard Markdown may not render perfectly in v1 and will generate warnings rather than errors.
- The first version ships with a single default Typst template; custom template support via `zensical-pdf.toml` is included as a path configuration but the template authoring workflow is out of scope for this specification.
- Remote or HTTP image URLs are out of scope for asset copying; only local relative paths are rewritten.
- YAML front matter in source Markdown files is stripped before aggregation to prevent it from appearing as document content.
- The build and dist output directories are created by the tool if they do not exist.
- Nested nav sections (section groupings) in `mkdocs.yml` are flattened to an ordered file list; section titles are treated as optional heading separators and are not required for the tool to function.
