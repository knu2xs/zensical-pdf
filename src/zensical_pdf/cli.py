from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from zensical_pdf import AggregationError, AssetError, ConfigNotFoundError, NavResolutionError
from zensical_pdf.aggregator import aggregate as _do_aggregate
from zensical_pdf.config import resolve_config
from zensical_pdf.manifest import write_aggregation_manifest
from zensical_pdf.nav import resolve_nav

app = typer.Typer(
    name="zensical-pdf",
    help="Generate PDF deliverables from Zensical and MkDocs-style documentation projects.",
    add_completion=False,
)

_err = Console(stderr=True)
_out = Console()

# Reusable Annotated type aliases — default value is always set on the function parameter.
ProjectDir = Annotated[
    Path,
    typer.Option("--project-dir", "-p", help="Root directory of the documentation project."),
]
Permissive = Annotated[
    bool,
    typer.Option("--permissive", help="Continue on missing nav files or assets instead of exiting with an error."),
]


@app.command("inspect-nav")
def inspect_nav(
    project_dir: ProjectDir = Path("."),
    permissive: Permissive = False,
) -> None:
    """Print the resolved page order without producing any output files."""
    try:
        config = resolve_config(project_dir.resolve(), permissive=permissive)
    except ConfigNotFoundError as exc:
        _err.print(f"[red]ERROR:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    try:
        nav = resolve_nav(config)
    except NavResolutionError as exc:
        _err.print(f"[red]ERROR:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    for warning in nav.warnings:
        _err.print(f"[yellow]WARNING:[/yellow] {warning}")

    detected = config.detected_config.name if config.detected_config else "none"
    try:
        docs_display = config.docs_dir.relative_to(config.project_dir)
    except ValueError:
        docs_display = config.docs_dir

    _out.print(f"Project directory : {config.project_dir}")
    _out.print(f"Config file       : {detected}")
    _out.print(f"Docs directory    : {docs_display}")
    _out.print(f"Pages ({len(nav.entries)} total)   :")
    for i, entry in enumerate(nav.entries, 1):
        title_part = f" ({entry.title})" if entry.title else ""
        _out.print(f"  {i}. {entry.relative_path}{title_part}")


@app.command("aggregate")
def aggregate(
    project_dir: ProjectDir = Path("."),
    permissive: Permissive = False,
) -> None:
    """Aggregate documentation pages into a combined Markdown file and copy local assets."""
    try:
        config = resolve_config(project_dir.resolve(), permissive=permissive)
    except ConfigNotFoundError as exc:
        _err.print(f"[red]ERROR:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    try:
        nav = resolve_nav(config)
    except NavResolutionError as exc:
        _err.print(f"[red]ERROR:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    for warning in nav.warnings:
        _err.print(f"[yellow]WARNING:[/yellow] {warning}")

    try:
        agg_doc = _do_aggregate(config, nav)
        manifest_path = write_aggregation_manifest(config, nav, agg_doc)
    except (AggregationError, AssetError) as exc:
        _err.print(f"[red]ERROR:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    for warning in agg_doc.warnings:
        _err.print(f"[yellow]WARNING:[/yellow] {warning}")

    _out.print(f"Written  : {agg_doc.output_path}")
    _out.print(f"Manifest : {manifest_path}")
    _out.print(f"Pages    : {len(agg_doc.pages_included)}")
    _out.print(f"Assets   : {len(agg_doc.assets)}")


@app.command("build")
def build(
    project_dir: ProjectDir = Path("."),
    output: Annotated[
        Optional[Path],
        typer.Option("--output", help="Override the PDF output path."),
    ] = None,
    permissive: Permissive = False,
) -> None:
    """Run the complete pipeline: nav → aggregate → Pandoc → Typst → PDF."""
    _err.print("[yellow]build: not yet implemented[/yellow]")
    raise typer.Exit(code=0)


@app.command("doctor")
def doctor(
    project_dir: ProjectDir = Path("."),
) -> None:
    """Validate the local environment (Python, Pandoc, Typst, project config)."""
    _err.print("[yellow]doctor: not yet implemented[/yellow]")
    raise typer.Exit(code=0)
