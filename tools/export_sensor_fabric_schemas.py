"""Regenerate committed JSON-schema snapshots for the sensor fabric.

Usage (from repo root):

    python tools/export_sensor_fabric_schemas.py

Run after any Bloc-1 contract/schema change so that schema drift is visible
in Git.  The snapshot test (`contracts/test_versioning.py`) fails when the
committed snapshots no longer match the models.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "quant-lab" / "src"))

from crypto_sensor_fabric.schemas.export import (
    SCHEMA_SNAPSHOT_DIR,
    write_snapshots,
)


def main() -> None:
    written = write_snapshots()
    print(f"Wrote {len(written)} JSON-schema snapshots to {SCHEMA_SNAPSHOT_DIR}")


if __name__ == "__main__":
    main()
