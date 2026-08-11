from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from zensical_pdf.aggregator import AggregatedDocument
from zensical_pdf.config import PdfConfig
from zensical_pdf.nav import NavResult


def _manifest_body(
    config: PdfConfig,
    nav_result: NavResult,
    agg_doc: AggregatedDocument,
    intermediate_typst: Optional[Path],
    output: Optional[Path],
) -> dict:
    config_file: Optional[str] = None
    if config.detected_config:
        try:
            config_file = str(config.detected_config.relative_to(config.project_dir))
        except ValueError:
            config_file = str(config.detected_config)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_dir": str(config.project_dir),
        "config_file": config_file,
        "docs_dir": str(config.docs_dir),
        "nav_source": nav_result.source,
        "pages": [str(e.relative_path) for e in nav_result.entries if e.exists],
        "assets": [
            {"source": str(a.source_path), "copied_to": str(a.dest_path)}
            for a in agg_doc.assets
        ],
        "intermediate_markdown": str(agg_doc.output_path),
        "intermediate_typst": str(intermediate_typst) if intermediate_typst else None,
        "output": str(output) if output else None,
    }


def write_aggregation_manifest(
    config: PdfConfig,
    nav_result: NavResult,
    agg_doc: AggregatedDocument,
) -> Path:
    """Write build/pdf/manifest.json after aggregation and return its path."""
    body = _manifest_body(config, nav_result, agg_doc, None, None)
    out = config.build_dir / "manifest.json"
    out.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return out


def write_build_manifest(
    config: PdfConfig,
    nav_result: NavResult,
    agg_doc: AggregatedDocument,
    typst_path: Path,
) -> Path:
    """Write dist/manifest.json after a complete build and return its path."""
    body = _manifest_body(config, nav_result, agg_doc, typst_path, config.output)
    out = config.output.parent / "manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return out
