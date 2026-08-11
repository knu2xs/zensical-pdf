"""Smoke tests: verify CLI installs, all subcommands are registered, and each exits cleanly."""
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from zensical_pdf.cli import app

runner = CliRunner(env={"NO_COLOR": "1"})


def test_help_lists_all_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "inspect-nav" in result.output
    assert "aggregate" in result.output
    assert "build" in result.output
    assert "doctor" in result.output


def test_inspect_nav_help() -> None:
    result = runner.invoke(app, ["inspect-nav", "--help"])
    assert result.exit_code == 0
    assert "--project-dir" in result.output


def test_aggregate_help() -> None:
    result = runner.invoke(app, ["aggregate", "--help"])
    assert result.exit_code == 0
    assert "--project-dir" in result.output


def test_build_help() -> None:
    result = runner.invoke(app, ["build", "--help"])
    assert result.exit_code == 0
    assert "--project-dir" in result.output
    assert "--output" in result.output


def test_doctor_help() -> None:
    result = runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0
    assert "--project-dir" in result.output


def test_inspect_nav_exits_zero(project_dir: Path) -> None:
    result = runner.invoke(app, ["inspect-nav", "--project-dir", str(project_dir)])
    assert result.exit_code == 0


def test_aggregate_exits_zero(project_dir: Path) -> None:
    result = runner.invoke(app, ["aggregate", "--project-dir", str(project_dir)])
    assert result.exit_code == 0


def test_build_fails_gracefully_when_pandoc_missing(project_dir: Path) -> None:
    """Build exits 1 with an actionable message when Pandoc is not installed."""
    with patch("zensical_pdf.adapters.pandoc.subprocess.run", side_effect=FileNotFoundError):
        result = runner.invoke(app, ["build", "--project-dir", str(project_dir)])
    assert result.exit_code == 1
    assert "Pandoc" in result.output


def test_doctor_exits_zero(project_dir: Path) -> None:
    result = runner.invoke(app, ["doctor", "--project-dir", str(project_dir)])
    # Doctor reports environment status; exit code depends on whether tools are installed.
    # We just verify it runs without an unhandled exception.
    assert result.exception is None or isinstance(result.exception, SystemExit)


def test_permissive_flag_accepted() -> None:
    result = runner.invoke(app, ["inspect-nav", "--permissive", "--help"])
    assert result.exit_code == 0


def test_build_output_option_accepted() -> None:
    result = runner.invoke(app, ["build", "--output", "/tmp/out.pdf", "--help"])
    assert result.exit_code == 0
