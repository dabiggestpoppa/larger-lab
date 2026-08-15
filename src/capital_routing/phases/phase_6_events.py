"""
Phase 6 - Forward Routing Study primitives: frozen Phase 5 inputs, fixed
outcome horizons, temporal development/holdout split.
CR-P6-FORWARD-ROUTING-STUDY-01

Phase 6 measures what happens AFTER each frozen Phase 5 event. It NEVER
recomputes Phase 5 thresholds, never alters event timestamps, and never
optimises on the holdout. All statistics are deterministic.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Canonical identity
# ---------------------------------------------------------------------------

TASK = "CR-P6-FORWARD-ROUTING-STUDY-01"
PHASE5_SEAL_COMMIT = "f0fc54ab3a2c182df8653569c6805db08f257bab"
PHASE4_SEAL_COMMIT = "71b8188dd9a83c78e51ea5f8e6028c8066d95079"
PHASE4_ENGINE_COMMIT = "f54ffff8b6041242e707d332075dea1c7b96f0d1"

CURRENCIES: List[str] = ["EUR", "GBP", "USD", "CHF", "JPY"]

PAIRS: List[str] = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "EURGBP",
    "EURJPY", "GBPJPY", "CHFJPY", "EURCHF", "GBPCHF",
]

# Fixed outcome horizons (hours). Core reporting uses ONLY these.
HORIZONS: List[int] = [1, 2, 4, 6, 8, 12, 24, 48]
# Optional supplementary horizons (+72h, +5 trading sessions ~ 120h). These are
# reported in the raw forward outcome tables only; all matrices and the report
# use HORIZONS.
HORIZONS_OPTIONAL: List[int] = [72, 120]

# ---------------------------------------------------------------------------
# Frozen input hashes (recorded from the ACCEPTED Phase 5 commit f0fc54ab).
# A mismatch is a hard failure: Phase 6 refuses to consume un-frozen inputs.
# ---------------------------------------------------------------------------

PHASE5_INPUT_HASHES = {
    "routing_events.parquet": "de08df601a008e0efd6c0bc1523e8a9be25105324466ed3c7a19a0e561cf8607",
    "origin_events.parquet": "072b80b277bafc152ebe51e794023610bab2cb0a2acb043fa05a954297bca5dd",
    "residual_shock_events.parquet": "ded85fed8a09efaee5967ad55a460ec68a75fe14556f38498c1bd3f68c6db0a4",
    "network_dislocation_events.parquet": "15d30cfbf09e4110af496623c17c5775e36b38337a755ac42d7b4e2715a2b055",
    "event_components.parquet": "a1c96a006288cefa6eeac7a1a2bc655cfd8f77ac8fa4b24d6b12075dc7e903b6",
    "threshold_manifest.json": "dedebb88dacfc32e6bfdfd9f74e93f58ff67a0525971b55e6b26a24c3c980093",
}

PHASE4_INPUT_HASHES = {
    "currency_factors_h1.parquet": "04ec94e515287f96d98c5093926410c062cf9971c1703b78752851a7b5064c2d",
    "pair_residuals_h1.parquet": "ea5edc04eefcbc9d4771ad8bcca4b88e14d63c9b45a51f0320548c9491ec44c8",
    "factor_features_h1.parquet": "0c464199988ddf68635ae7311977a3315f4dbf9f6db48e669cc90f8d14cc7302",
}

# Price source for pair-space outcomes: frozen Phase 3 strict common panel.
PHASE3_PANEL_HASH = "a0da64a3b0cd8976b61e3f4e8defa55906098373efa1bcdf79dc2d628b8c6896"
PHASE5_INPUT_MANIFEST_HASH = "49dd9d1ace05952a61247a4a267cae2ee1cf7faabfb1340d3ff68a0ac80cb947"
PHASE4_OUTPUT_MANIFEST_HASH = "402b768fccda95bc0640de83a065ec20dac873561b6d38499e9714a85adeece1"

# ---------------------------------------------------------------------------
# Temporal split (frozen BEFORE any ranking of results).
# Development: 2023-07 through 2025-06. Holdout: 2025-07 through 2026-05.
# ---------------------------------------------------------------------------

DEVELOPMENT_START = pd.Timestamp("2023-07-01", tz="UTC")
DEVELOPMENT_END = pd.Timestamp("2025-06-30 23:59:59", tz="UTC")
HOLDOUT_START = pd.Timestamp("2025-07-01", tz="UTC")
HOLDOUT_END = pd.Timestamp("2026-05-31 23:59:59", tz="UTC")

DEV_SUBPERIODS = [
    ("2023H2", pd.Timestamp("2023-07-01", tz="UTC"), pd.Timestamp("2023-12-31 23:59:59", tz="UTC")),
    ("2024H1", pd.Timestamp("2024-01-01", tz="UTC"), pd.Timestamp("2024-06-30 23:59:59", tz="UTC")),
    ("2024H2", pd.Timestamp("2024-07-01", tz="UTC"), pd.Timestamp("2024-12-31 23:59:59", tz="UTC")),
    ("2025H1", pd.Timestamp("2025-01-01", tz="UTC"), pd.Timestamp("2025-06-30 23:59:59", tz="UTC")),
]

SESSIONS = ["Asia", "London", "NY_Overlap", "NY_Late"]
SEVERITIES = ["LOW", "MEDIUM", "EXTREME"]  # HIGH is structurally absent in Phase 5 buckets


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Frozen input loading
# ---------------------------------------------------------------------------


def load_frozen_phase5(phase5_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load the six accepted Phase 5 inputs, rejecting any hash mismatch."""
    frames = {}
    for fname, expected in PHASE5_INPUT_HASHES.items():
        path = phase5_dir / fname
        actual = _sha256(path)
        if actual != expected:
            raise ValueError(
                f"Phase 5 input hash mismatch for {fname}: expected {expected}, "
                f"got {actual}. Refusing to consume an un-frozen input."
            )
        if fname.endswith(".json"):
            frames[fname] = json.loads(path.read_text(encoding="utf-8"))
        else:
            frames[fname] = pd.read_parquet(path)
    return frames


def load_frozen_phase3_panel(phase3_dir: Path) -> pd.DataFrame:
    """Load the frozen Phase 3 strict common panel (pair prices)."""
    path = phase3_dir / "h1_strict_common_panel.parquet"
    actual = _sha256(path)
    if actual != PHASE3_PANEL_HASH:
        raise ValueError(
            f"Phase 3 panel hash mismatch: expected {PHASE3_PANEL_HASH}, got {actual}."
        )
    return pd.read_parquet(path)


def write_p5_event_freeze(phase5_dir: Path, phase6_dir: Path) -> Dict:
    """Freeze the Phase 5 event set: SHA-256 for the six listed files."""
    freeze = {
        "phase": "6",
        "task": TASK,
        "phase5_seal_commit": PHASE5_SEAL_COMMIT,
        "frozen_at_commit": PHASE5_SEAL_COMMIT,
        "note": "Frozen Phase 5 event set. No Phase 6 routine may alter or "
                "regenerate event timestamps.",
        "inputs": {},
    }
    for fname in PHASE5_INPUT_HASHES:
        path = phase5_dir / fname
        freeze["inputs"][fname] = {
            "sha256": _sha256(path),
            "expected": PHASE5_INPUT_HASHES[fname],
            "bytes": path.stat().st_size,
        }
    out = phase6_dir / "p5_event_freeze.json"
    out.write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    return freeze


def write_input_hash_manifest(phase5_dir: Path, phase4_dir: Path,
                              phase3_dir: Path, phase6_dir: Path) -> Dict:
    """Record every input consumed by Phase 6 with its frozen hash."""
    ev = pd.read_parquet(phase5_dir / "routing_events.parquet")
    manifest = {
        "phase": "6",
        "task": TASK,
        "phase5_seal_commit": PHASE5_SEAL_COMMIT,
        "phase4_seal_commit": PHASE4_SEAL_COMMIT,
        "phase4_engine_commit": PHASE4_ENGINE_COMMIT,
        "inputs": {
            **{f"phase_05/{fname}": {"sha256": PHASE5_INPUT_HASHES[fname]}
               for fname in PHASE5_INPUT_HASHES},
            **{f"phase_04/{fname}": {"sha256": PHASE4_INPUT_HASHES[fname]}
               for fname in PHASE4_INPUT_HASHES},
            "phase_04/output_hash_manifest.json": {"sha256": PHASE4_OUTPUT_MANIFEST_HASH},
            "phase_03/h1_strict_common_panel.parquet": {"sha256": PHASE3_PANEL_HASH},
            "phase_05/input_hash_manifest.json": {"sha256": PHASE5_INPUT_MANIFEST_HASH},
        },
        "event_rows": int(len(ev)),
        "event_window_start": str(pd.to_datetime(ev["event_start"].min(), utc=True)),
        "event_window_end": str(pd.to_datetime(ev["event_start"].max(), utc=True)),
        "note": "All inputs frozen at Phase 5 seal. Mismatch => refused.",
    }
    (phase6_dir / "input_hash_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


# ---------------------------------------------------------------------------
# Split assignment
# ---------------------------------------------------------------------------


def assign_split(ts: pd.Timestamp) -> str:
    """Assign an event timestamp to development or holdout (frozen windows)."""
    ts = pd.Timestamp(ts)
    if DEVELOPMENT_START <= ts <= DEVELOPMENT_END:
        return "development"
    if HOLDOUT_START <= ts <= HOLDOUT_END:
        return "holdout"
    return "outside"


def assign_subperiod(ts: pd.Timestamp) -> str:
    """Assign to a development subperiod, HOLDOUT, or outside."""
    ts = pd.Timestamp(ts)
    for name, start, end in DEV_SUBPERIODS:
        if start <= ts <= end:
            return name
    if HOLDOUT_START <= ts <= HOLDOUT_END:
        return "HOLDOUT"
    return "OUTSIDE"


def write_split_manifest(events: pd.DataFrame, phase6_dir: Path) -> Dict:
    """Freeze the chronological split BEFORE discovery and record it."""
    ts = pd.to_datetime(events["event_start"], utc=True)
    manifest = {
        "phase": "6",
        "task": TASK,
        "development": {
            "start": str(DEVELOPMENT_START), "end": str(DEVELOPMENT_END),
            "n_events": int(((ts >= DEVELOPMENT_START) & (ts <= DEVELOPMENT_END)).sum()),
        },
        "holdout": {
            "start": str(HOLDOUT_START), "end": str(HOLDOUT_END),
            "n_events": int(((ts >= HOLDOUT_START) & (ts <= HOLDOUT_END)).sum()),
        },
        "outside_window": int(((ts < DEVELOPMENT_START) | (ts > HOLDOUT_END)).sum()),
        "frozen_before_discovery": True,
        "holdout_policy": "Holdout is touched ONLY after candidate relationships "
                          "are frozen from development.",
    }
    (phase6_dir / "split_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def parse_events(events_df: pd.DataFrame) -> pd.DataFrame:
    """Parse event_start into a UTC datetime column and return the frame."""
    out = events_df.copy()
    out["event_ts"] = pd.to_datetime(out["event_start"], utc=True)
    return out
