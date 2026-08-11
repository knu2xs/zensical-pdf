from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from zensical_pdf.aggregator import AggregatedDocument
from zensical_pdf.config import PdfConfig
from zensical_pdf.nav import NavResult


def write_aggregation_manifest(
    config: PdfConfig,
    nav_result: NavResult,
    agg_doc: AggregatedDocument,
) -> Path:
    """Write build/pdf/manifest.json and return its path."""
    config_file: Optional[str] = None
    if config.detected_config:
        try:
            config_file = str(config.detected_config.relative_to(config.project_dir))
        except ValueError:
            config_file = str(config.detected_config)

    manifest = {
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
        "intermediate_typst": None,
        "output": None,
    }

    out = config.build_dir / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out
