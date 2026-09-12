"""
Crypto Foundry DATA-1 Provenance Manifest Builder

Every dataset MUST have a manifest before it is considered valid.
Raw files are append-only or immutable by dataset version.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ProvenanceManifest:
    """Provenance record for a single dataset."""
    dataset_id: str
    venue: str
    market: str
    source: str
    source_endpoint_or_contract: str
    collector_version: str
    schema_version: str
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None
    row_count: int = 0
    sha256: Optional[str] = None
    created_at_utc: Optional[str] = None
    duplicate_count: int = 0
    missing_interval_summary: Optional[str] = None
    known_limitations: List[str] = field(default_factory=list)
    status: str = "VALID"  # VALID, PARTIAL, QUARANTINED, FAILED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProvenanceManifest":
        known = d.pop("known_limitations", [])
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__}, known_limitations=known)


def compute_file_sha256(filepath: str | Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_data_sha256(data: bytes) -> str:
    """Compute SHA256 hash of in-memory data."""
    return hashlib.sha256(data).hexdigest()


def build_manifest(
    dataset_id: str,
    venue: str,
    market: str,
    source: str,
    source_endpoint_or_contract: str,
    collector_version: str,
    schema_version: str,
    rows: List[Dict],
    timestamp_field: str = "event_time_utc",
    file_path: Optional[str | Path] = None,
    known_limitations: Optional[List[str]] = None,
    status: str = "VALID",
) -> ProvenanceManifest:
    """Build a provenance manifest from collected data."""
    now = datetime.now(timezone.utc).isoformat()

    first_ts = None
    last_ts = None
    row_count = len(rows)

    if rows and timestamp_field in rows[0]:
        timestamps = [r[timestamp_field] for r in rows if r.get(timestamp_field) is not None]
        if timestamps:
            # Sort timestamps
            def ts_sort_key(ts):
                if isinstance(ts, (int, float)):
                    return ts
                if isinstance(ts, str):
                    try:
                        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                    except (ValueError, TypeError):
                        return 0
                if isinstance(ts, datetime):
                    return ts.timestamp()
                return 0

            sorted_ts = sorted(timestamps, key=ts_sort_key)
            first_ts = str(sorted_ts[0])
            last_ts = str(sorted_ts[-1])

    sha256 = None
    if file_path and os.path.exists(file_path):
        sha256 = compute_file_sha256(file_path)

    return ProvenanceManifest(
        dataset_id=dataset_id,
        venue=venue,
        market=market,
        source=source,
        source_endpoint_or_contract=source_endpoint_or_contract,
        collector_version=collector_version,
        schema_version=schema_version,
        first_timestamp=first_ts,
        last_timestamp=last_ts,
        row_count=row_count,
        sha256=sha256,
        created_at_utc=now,
        known_limitations=known_limitations or [],
        status=status,
    )


def save_manifest(manifest: ProvenanceManifest, output_dir: str | Path) -> Path:
    """Save manifest to JSON file."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{manifest.dataset_id}_manifest.json"
    with open(filepath, "w") as f:
        json.dump(manifest.to_dict(), f, indent=2, default=str)
    return filepath


def load_manifest(filepath: str | Path) -> ProvenanceManifest:
    """Load manifest from JSON file."""
    with open(filepath, "r") as f:
        return ProvenanceManifest.from_dict(json.load(f))
