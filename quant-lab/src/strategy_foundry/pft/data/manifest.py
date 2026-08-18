"""Raw data manifest: provenance, evidence grades, SHA256 fingerprints."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from .loading import load_canonical

# Evidence grades per build prompt section 20.
GRADES = {
    "A": "exchange/broker executable historical source",
    "B": "institutional-quality vendor",
    "C": "reputable historical source",
    "D": "reconstructed/proxy",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_raw_manifest_entry(
    path: Path,
    family: str,
    timeframe: str,
    role: str,
    evidence_grade: str,
    venue: str,
    timestamp_semantics: str,
    contract_type: str,
    execution_or_reference: str,
    notes: str = "",
) -> dict:
    """One RAW_DATA_MANIFEST entry with structural facts + sha256."""
    res = load_canonical(path)
    frame = res.frame
    return {
        "dataset_id": f"{family}.{timeframe}.{path.stem}",
        "path": str(path),
        "source": "repository local data dir",
        "source_type": "local CSV export",
        "symbol": path.stem,
        "underlying": family,
        "instrument_type": "CFD/spot" if "PRO" in path.stem or "fetched" in path.stem else "vendor series",
        "venue": venue,
        "timezone": "UTC (naive timestamps, empirically resolved)",
        "timestamp_semantics": timestamp_semantics,
        "timeframe": timeframe,
        "native_start": frame.index.min().isoformat() if len(frame) else None,
        "native_end": frame.index.max().isoformat() if len(frame) else None,
        "rows_after_validation": int(len(frame)),
        "raw_rows": res.total_rows,
        "dropped_rows": res.dropped_rows,
        "ohlc_violations": res.ohlc_violations,
        "price_fields": ["open", "high", "low", "close"],
        "volume_fields": [c for c in ("volume", "tick_volume", "real_volume") if c in frame.columns],
        "bid_ask_available": "spread" in frame.columns,
        "contract_type": contract_type,
        "roll_convention": "not available (continuous broker series; roll metadata absent)",
        "adjustment_convention": "unknown (no adjustment metadata)",
        "execution_or_reference": execution_or_reference,
        "evidence_grade": evidence_grade,
        "evidence_grade_definition": GRADES[evidence_grade],
        "sha256": sha256_file(path),
        "notes": notes,
    }
