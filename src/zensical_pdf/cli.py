from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="zensical-pdf",
    help="Generate PDF deliverables from Zensical and MkDocs-style documentation projects.",
    add_completion=False,
)

_err = Console(stderr=True)

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
    _err.print("[yellow]inspect-nav: not yet implemented[/yellow]")
    raise typer.Exit(code=0)


@app.command("aggregate")
def aggregate(
    project_dir: ProjectDir = Path("."),
    permissive: Permissive = False,
) -> None:
    """Aggregate documentation pages into a combined Markdown file and copy local assets."""
    _err.print("[yellow]aggregate: not yet implemented[/yellow]")
    raise typer.Exit(code=0)


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
