from __future__ import annotations

import subprocess
from pathlib import Path

from zensical_pdf import PandocError, PandocNotFoundError

# Typst writer requires Pandoc ≥ 3.1.2
_MIN_VERSION = (3, 1, 2)


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
            f"--output={output_path}",
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
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
