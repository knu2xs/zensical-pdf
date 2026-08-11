"""Smoke tests: verify CLI installs, all subcommands are registered, and each exits cleanly."""
from pathlib import Path

from typer.testing import CliRunner

from zensical_pdf.cli import app

runner = CliRunner()


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


def test_build_exits_zero(tmp_path: Path) -> None:
    result = runner.invoke(app, ["build", "--project-dir", str(tmp_path)])
    assert result.exit_code == 0


def test_doctor_exits_zero(tmp_path: Path) -> None:
    result = runner.invoke(app, ["doctor", "--project-dir", str(tmp_path)])
    assert result.exit_code == 0


def test_permissive_flag_accepted() -> None:
    result = runner.invoke(app, ["inspect-nav", "--permissive", "--help"])
    assert result.exit_code == 0


def test_build_output_option_accepted() -> None:
    result = runner.invoke(app, ["build", "--output", "/tmp/out.pdf", "--help"])
    assert result.exit_code == 0
