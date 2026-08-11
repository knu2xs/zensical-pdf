from __future__ import annotations

import subprocess
from pathlib import Path

from zensical_pdf import PandocError, PandocNotFoundError

# Typst writer requires Pandoc ≥ 3.1.2
_MIN_VERSION = (3, 1, 2)
_TYPST_EMPTY_FONT_DEFAULT = "font: (),"
_TYPST_SAFE_FONT_DEFAULT = 'font: ("New Computer Modern"),'


def _parse_version_tuple(text: str) -> tuple[int, ...]:
    """Extract (major, minor, patch) from a version string like '3.2.1'."""
    try:
        return tuple(int(x) for x in text.strip().split("."))
    except (ValueError, AttributeError):
        return (0,)


class PandocAdapter:
    """Wraps the pandoc subprocess; injectable for testing via a fake."""

    def version(self) -> str | None:
        """Return the installed pandoc version string, or None if not found."""
        try:
            result = subprocess.run(
                ["pandoc", "--version"],
                capture_output=True,
                text=True,
            )
            for line in result.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and parts[0].lower() == "pandoc":
                    return parts[1]
        except FileNotFoundError:
            pass
        return None

    def meets_minimum_version(self) -> bool:
        """Return True if the installed pandoc version meets the minimum requirement."""
        v = self.version()
        if v is None:
            return False
        return _parse_version_tuple(v) >= _MIN_VERSION

    def convert(self, input_path: Path, output_path: Path) -> None:
        """Convert a Markdown file to Typst using pandoc."""
        cmd = [
            "pandoc",
            str(input_path),
            "--from=markdown",
            "--to=typst",
            "--standalone",
            "--variable=font:New Computer Modern",
            f"--output={output_path}",
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            self._ensure_nonempty_font_default(output_path)
        except FileNotFoundError as exc:
            raise PandocNotFoundError(
                "Pandoc is not available on PATH. "
                "The build command requires Pandoc ≥ 3.1.2 to convert Markdown to Typst.\n"
                "Install Pandoc: https://pandoc.org/installing.html"
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise PandocError(
                f"Pandoc exited with code {exc.returncode}.\n"
                f"Stderr: {exc.stderr.strip()}"
            ) from exc

    def _ensure_nonempty_font_default(self, typst_path: Path) -> None:
        """Patch Pandoc Typst output so Typst always gets a non-empty font fallback list."""
        if not typst_path.exists():
            return

        try:
            content = typst_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise PandocError(f"Cannot read generated Typst file '{typst_path}': {exc}") from exc

        if _TYPST_EMPTY_FONT_DEFAULT not in content:
            return

        patched = content.replace(_TYPST_EMPTY_FONT_DEFAULT, _TYPST_SAFE_FONT_DEFAULT, 1)
        try:
            typst_path.write_text(patched, encoding="utf-8")
        except OSError as exc:
            raise PandocError(f"Cannot update generated Typst file '{typst_path}': {exc}") from exc
