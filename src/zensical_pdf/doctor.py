from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from zensical_pdf.adapters.pandoc import PandocAdapter
    from zensical_pdf.adapters.typst import TypstAdapter
    from zensical_pdf.config import PdfConfig


@dataclass
class DoctorCheck:
    name: str
    status: Literal["pass", "warn", "fail"]
    detail: str


@dataclass
class DoctorResult:
    checks: list[DoctorCheck] = field(default_factory=list)
    all_pass: bool = True


def check_python_version() -> DoctorCheck:
    vi = sys.version_info
    version_str = f"{vi[0]}.{vi[1]}.{vi[2]}"
    if (vi[0], vi[1]) >= (3, 10):
        return DoctorCheck("Python", "pass", version_str)
    return DoctorCheck("Python", "fail", f"{version_str} (requires ≥ 3.10)")


def check_pandoc(adapter: PandocAdapter) -> DoctorCheck:
    version = adapter.version()
    if version is None:
        return DoctorCheck(
            "Pandoc",
            "fail",
            "not found — install Pandoc ≥ 3.1.2: https://pandoc.org/installing.html",
        )
    if adapter.meets_minimum_version():
        return DoctorCheck("Pandoc", "pass", f"{version} (≥ 3.1.2 ✓)")
    return DoctorCheck(
        "Pandoc",
        "warn",
        f"{version} (< 3.1.2 required for Typst output — upgrade recommended)",
    )


def check_typst(adapter: TypstAdapter) -> DoctorCheck:
    version = adapter.version()
    if version is None:
        return DoctorCheck(
            "Typst",
            "fail",
            "not found — install Typst: https://typst.app",
        )
    return DoctorCheck("Typst", "pass", version)


def check_project_config(project_dir: Path) -> DoctorCheck:
    for name in ("zensical-pdf.toml", "mkdocs.yml", "zensical.toml"):
        if (project_dir / name).is_file():
            return DoctorCheck("Config detected", "pass", name)
    return DoctorCheck(
        "Config detected",
        "fail",
        f"no config file found in '{project_dir}' "
        "(expected zensical-pdf.toml, mkdocs.yml, or zensical.toml)",
    )


def check_docs_dir(config: PdfConfig) -> DoctorCheck:
    if config.docs_dir.is_dir():
        try:
            label = str(config.docs_dir.relative_to(config.project_dir))
        except ValueError:
            label = str(config.docs_dir)
        return DoctorCheck("Docs directory", "pass", f"{label}/ (exists, readable)")
    return DoctorCheck(
        "Docs directory",
        "fail",
        f"'{config.docs_dir}' does not exist",
    )


def check_output_dir(config: PdfConfig) -> DoctorCheck:
    output_parent = config.output.parent
    try:
        label = str(output_parent.relative_to(config.project_dir))
    except ValueError:
        label = str(output_parent)

    if output_parent.is_dir():
        return DoctorCheck("Output directory", "pass", f"{label}/ (writable)")
    if output_parent.parent.is_dir():
        return DoctorCheck("Output directory", "pass", f"{label}/ (will be created)")
    return DoctorCheck(
        "Output directory",
        "warn",
        f"'{output_parent}' does not exist and its parent directory is not accessible",
    )


def run_doctor(
    project_dir: Path,
    pandoc: PandocAdapter,
    typst: TypstAdapter,
) -> DoctorResult:
    """Run all six environment checks and return a DoctorResult."""
    checks: list[DoctorCheck] = [
        check_python_version(),
        check_pandoc(pandoc),
        check_typst(typst),
        check_project_config(project_dir),
    ]

    # Config-dependent checks — best-effort; safe to fail individually
    try:
        from zensical_pdf.config import resolve_config
        config = resolve_config(project_dir)
        checks.append(check_docs_dir(config))
        checks.append(check_output_dir(config))
    except Exception as exc:
        detail = f"cannot resolve config: {exc}"
        checks.append(DoctorCheck("Docs directory", "fail", detail))
        checks.append(DoctorCheck("Output directory", "fail", detail))

    return DoctorResult(
        checks=checks,
        all_pass=all(c.status != "fail" for c in checks),
    )
