"""zensical-pdf: Generate PDF deliverables from documentation projects."""

__version__ = "0.1.0"


class ZensicalPdfError(Exception):
    """Base exception for all zensical-pdf errors."""


class ConfigNotFoundError(ZensicalPdfError):
    """No supported configuration file found in the project directory."""


class NavResolutionError(ZensicalPdfError):
    """Navigation could not be resolved from the project configuration."""


class AggregationError(ZensicalPdfError):
    """Markdown aggregation failed."""


class AssetError(ZensicalPdfError):
    """Asset copy or path rewrite failed."""


class PandocNotFoundError(ZensicalPdfError):
    """Pandoc is not available on PATH."""


class PandocError(ZensicalPdfError):
    """Pandoc exited with a non-zero status."""


class TypstNotFoundError(ZensicalPdfError):
    """Typst is not available on PATH."""


class TypstError(ZensicalPdfError):
    """Typst exited with a non-zero status."""
