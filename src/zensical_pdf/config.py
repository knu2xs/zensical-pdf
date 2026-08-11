from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional

import yaml

# tomllib is stdlib from Python 3.11; tomli is the backport for 3.10
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

from zensical_pdf import ConfigNotFoundError


@dataclass
class PdfConfig:
    project_dir: Path
    docs_dir: Path
    output: Path
    build_dir: Path
    title: str
    subtitle: Optional[str]
    author: Optional[str]
    version: Optional[str]
    template: Optional[Path]
    normalize_headings: bool
    include_toc: bool
    number_sections: bool
    missing_asset_policy: Literal["warn", "error"]
    permissive: bool
    detected_config: Optional[Path]


def load_toml_config(project_dir: Path) -> dict[str, Any]:
    """Load zensical-pdf.toml if present; return empty dict otherwise."""
    toml_path = project_dir / "zensical-pdf.toml"
    if not toml_path.is_file():
        return {}
    with toml_path.open("rb") as f:
        return tomllib.load(f)


def load_zensical_metadata(project_dir: Path) -> dict[str, Any]:
    """Extract relevant metadata from zensical.toml's [project] scope."""
    zensical_path = project_dir / "zensical.toml"
    if not zensical_path.is_file():
        return {}
    with zensical_path.open("rb") as f:
        data = tomllib.load(f)
    project = data.get("project", {})
    if not isinstance(project, dict):
        return {}
    return {
        "site_name": project.get("site_name"),
        "docs_dir": project.get("docs_dir"),
        "site_author": project.get("site_author"),
    }


def load_mkdocs_metadata(project_dir: Path) -> dict[str, Any]:
    """Extract only site_name and docs_dir from mkdocs.yml (nav is read by nav.py)."""
    yml_path = project_dir / "mkdocs.yml"
    if not yml_path.is_file():
        return {}
    with yml_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {
        "site_name": data.get("site_name"),
        "docs_dir": data.get("docs_dir"),
    }


def _detect_config_file(project_dir: Path) -> Optional[Path]:
    """Return the first config file found in priority order."""
    for name in ("zensical-pdf.toml", "zensical.toml", "mkdocs.yml"):
        candidate = project_dir / name
        if candidate.is_file():
            return candidate
    return None


def resolve_config(
    project_dir: Path,
    output: Optional[Path] = None,
    permissive: bool = False,
) -> PdfConfig:
    """Build PdfConfig by merging all config sources in priority order.

    Priority: CLI args > zensical-pdf.toml > zensical.toml > mkdocs.yml > defaults.
    """
    project_dir = project_dir.resolve()

    toml = load_toml_config(project_dir)
    zensical = load_zensical_metadata(project_dir)
    mkdocs = load_mkdocs_metadata(project_dir)
    detected_config = _detect_config_file(project_dir)

    # If zensical.toml exists, prefer it as the source of project metadata and docs_dir.
    if (project_dir / "zensical.toml").is_file():
        mkdocs = {}

    # docs_dir: toml [paths].docs_dir → zensical.toml [project].docs_dir → mkdocs.yml docs_dir → "docs"
    raw_docs_dir: str = (
        toml.get("paths", {}).get("docs_dir")
        or zensical.get("docs_dir")
        or mkdocs.get("docs_dir")
        or "docs"
    )
    docs_dir = (project_dir / raw_docs_dir).resolve()

    if detected_config is None and not docs_dir.is_dir():
        raise ConfigNotFoundError(
            f"No configuration file (zensical-pdf.toml, zensical.toml, mkdocs.yml) "
            f"found in '{project_dir}' and docs directory '{docs_dir}' does not exist."
        )

    # output: CLI arg → toml [paths].output → default
    raw_output: str = (
        str(output) if output is not None
        else toml.get("paths", {}).get("output", "dist/documentation.pdf")
    )
    resolved_output = (project_dir / raw_output).resolve()

    raw_template = toml.get("paths", {}).get("template")
    template = (project_dir / raw_template).resolve() if raw_template else None

    # title: toml → zensical site_name → mkdocs site_name → default
    title: str = (
        toml.get("project", {}).get("title")
        or zensical.get("site_name")
        or mkdocs.get("site_name")
        or "Documentation"
    )

    return PdfConfig(
        project_dir=project_dir,
        docs_dir=docs_dir,
        output=resolved_output,
        build_dir=(project_dir / "build" / "pdf").resolve(),
        title=title,
        subtitle=toml.get("project", {}).get("subtitle"),
        author=toml.get("project", {}).get("author") or zensical.get("site_author"),
        version=toml.get("project", {}).get("version"),
        template=template,
        normalize_headings=bool(toml.get("pdf", {}).get("normalize_headings", True)),
        include_toc=bool(toml.get("pdf", {}).get("include_toc", True)),
        number_sections=bool(toml.get("pdf", {}).get("number_sections", False)),
        missing_asset_policy=toml.get("pdf", {}).get("missing_asset_policy", "warn"),
        permissive=permissive,
        detected_config=detected_config,
    )
