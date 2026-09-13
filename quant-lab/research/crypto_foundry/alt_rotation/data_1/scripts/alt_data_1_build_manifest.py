#!/usr/bin/env python3
"""ALT-DATA-1 — provenance manifest builder.

Chains raw -> normalized -> features:

  artifacts:   every committed artifact under data_1/ with sha256,
               generator, and (for derived) parent hashes
  raw_inputs:  per-date meta sidecars (probes/raw/*.meta.json) with the
               body sha256 recorded at collection time
  parent_data: DATA-0 / DATA-0.1 inputs reused (HL funding, OKX swaps,
               CG/CP lists) with their sha256

Deterministic (no timestamps inside the emitted JSON except retrieved_at
values already recorded in the metas).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D0RAW = ROOT.parent / "data_0" / "probes" / "raw"

ARTIFACT_GENERATORS = {
    "ALT_DATA_1_PREREGISTRATION.md": "written",
    "ALT_DATA_1_COLLECTION_CONTRACT.json": "written",
    "ALT_DATA_1_FEATURE_DEFINITIONS.json":
        "scripts/alt_data_1_build_pipeline.py",
    "ALT_DATA_1_FEATURE_REGISTRY_HASH.json":
        "scripts/alt_data_1_build_pipeline.py",
    "ALT_DATA_1_IDENTITY_MAP.parquet":
        "scripts/alt_data_1_build_pipeline.py",
    "ALT_DATA_1_PIT_UNIVERSE.parquet":
        "scripts/alt_data_1_build_pipeline.py",
    "ALT_DATA_1_PERP_ELIGIBILITY.parquet":
        "scripts/alt_data_1_build_pipeline.py",
    "ALT_DATA_1_ASSET_MULTISCALE_FEATURES.parquet":
        "scripts/alt_data_1_build_pipeline.py",
    "ALT_DATA_1_RANK_BAND_FEATURES.parquet":
        "scripts/alt_data_1_build_pipeline.py",
    "ALT_DATA_1_SECTOR_FEATURES.parquet":
        "scripts/alt_data_1_build_pipeline.py",
    "ALT_DATA_1_SECTOR_MEMBERSHIP.parquet":
        "scripts/alt_data_1_build_pipeline.py",
    "ALT_DATA_1_MARKET_TERRAIN_FEATURES.parquet":
        "scripts/alt_data_1_build_pipeline.py",
    "ALT_DATA_1_SURVIVORSHIP.parquet":
        "scripts/alt_data_1_build_survivorship.py",
    "ALT_DATA_1_DATA_QUALITY_REPORT.md": "written",
    "ALT_DATA_1_COVERAGE_REPORT.md": "written",
    "ALT_DATA_1_PROVENANCE_MANIFEST.json":
        "scripts/alt_data_1_build_manifest.py",
    "ALT_DATA_1_REPORT.md": "written",
    "ALT_DATA_1_DECISION.json": "written",
}

PARENT_INPUTS = [
    "hyperliquid_funding_first_history.json",
    "okx_instruments_swap.json",
    "coingecko_coins_list.json",
    "coinpaprika_coins.json",
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    artifacts = []
    for name, gen in ARTIFACT_GENERATORS.items():
        p = ROOT / name
        if not p.exists():
            if name == "ALT_DATA_1_PROVENANCE_MANIFEST.json":
                continue  # not yet written
            print(f"WARN missing artifact: {name}", flush=True)
            continue
        artifacts.append({
            "artifact": name, "sha256": sha256_file(p), "bytes": p.stat().st_size,
            "generator": gen,
            "parent_hashes": (["ALT_DATA_1_PIT_UNIVERSE.parquet"]
                              if name == "ALT_DATA_1_SURVIVORSHIP.parquet"
                              else []),
        })
    meta_dir = ROOT / "probes" / "raw"
    raw = []
    for mp in sorted(meta_dir.glob("*.meta.json")):
        m = json.loads(mp.read_text(encoding="utf-8"))
        raw.append({
            "date": m["historical_date"],
            "probe": m["probe"],
            "rows": m.get("rows"),
            "http_status": m["http_status"],
            "sha256": m["sha256"],
            "bytes": m["bytes"],
            "access_class": m["access_class"],
            "source_authority": m["source_authority"],
            "retrieved_at": m["retrieved_at"],
            "known_limitations": m["known_limitations"],
        })
    parents = []
    for name in PARENT_INPUTS:
        p = D0RAW / name
        if not p.exists():
            print(f"WARN missing parent input: {name}", flush=True)
            continue
        parents.append({"artifact": f"data_0/probes/raw/{name}",
                        "sha256": sha256_file(p)})
    manifest = {
        "checkpoint": "CRYPTO-ALT-DATA-1-CANONICAL-POINT-IN-TIME-UNIVERSE-AND-MULTISCALE-FEATURE-PANEL",
        "manifest_version": "1.0.0",
        "chain": "raw(meta sidecars with body sha256) -> normalized "
                 "(parquet) -> features (parquet) -> registry (frozen hash)",
        "artifacts": artifacts,
        "raw_inputs": raw,
        "parent_data_0_inputs": parents,
        "n_artifacts": len(artifacts),
        "n_raw_inputs": len(raw),
    }
    (ROOT / "ALT_DATA_1_PROVENANCE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"manifest: {len(artifacts)} artifacts, {len(raw)} raw inputs, "
          f"{len(parents)} parent inputs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
