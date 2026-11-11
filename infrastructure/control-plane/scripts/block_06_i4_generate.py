#!/usr/bin/env python3
"""Regenerate the B6-I4 evidence manifest with independent hashes and sizes.

Standard library only, offline, deterministic: artifacts and code are hashed from disk, sorted by
path, and the manifest excludes itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

DOCS = "docs/oce-golden-system"
PREFIX = "OCE_BLOCK_06_I4_"
BASE = "f0bd9bdd3f776b33d3b70b5b441966e2c80e1f14"
CODE = [
    "infrastructure/control-plane/scripts/block_06_i4_generate.py",
    "infrastructure/control-plane/scripts/block_06_i4_mutation_battery.py",
    "infrastructure/control-plane/scripts/block_06_i4_paired.py",
    "infrastructure/control-plane/scripts/block_06_i4_stage_controls.py",
    "infrastructure/control-plane/scripts/block_06_i4_validate.py",
    "infrastructure/control-plane/scripts/block_06_stage_scope.py",
    "infrastructure/control-plane/scripts/block_06_i0_validate.py",
    "infrastructure/control-plane/scripts/block_06_i1_validate.py",
    "oce/operator/incident.py",
    "oce/operator/cost.py",
    "oce/operator/trace.py",
    "oce/services/__init__.py",
    "oce/services/identity.py",
    "oce/services/workflow.py",
    "oce/services/refusals.py",
]


def row(root: pathlib.Path, rel: str) -> dict:
    data = (root / rel).read_bytes()
    return {"path": rel, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def build(root: pathlib.Path) -> dict:
    artifacts = []
    for path in sorted((root / DOCS).glob(f"{PREFIX}*.json")):
        if path.name.endswith("MANIFEST_v1.0.json"):
            continue
        artifacts.append(row(root, f"{DOCS}/{path.name}"))
    ledger = root / DOCS / f"{PREFIX}EVIDENCE_LEDGER_v1.0.md"
    if ledger.exists():
        artifacts.append(row(root, f"{DOCS}/{ledger.name}"))
    code = [row(root, rel) for rel in CODE]
    return {
        "document_id": "OCE-B6-I4-MANIFEST-001",
        "schema": "oce.block_06_i4.manifest.v1",
        "stage": "B6-I4",
        "status": "FROZEN",
        "hash": "sha256",
        "size": "bytes",
        "base_sha": BASE,
        "artifacts": artifacts,
        "code": code,
        "totals": {"artifacts": len(artifacts), "code": len(code)},
        "verification": {"independent": True, "excludes_manifest": True},
        "locks": {"B6-I5_through_I9": "LOCKED", "BOOK_6_COMPLETE": False,
                  "MERGE_AUTHORIZED": False, "RATIFICATION_AUTHORIZED": False,
                  "capital_authority": "none", "cost_usd": 0},
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    root = (pathlib.Path(args.root).resolve() if args.root
            else pathlib.Path(__file__).resolve().parents[3])
    manifest = build(root)
    text = json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    target = root / DOCS / f"{PREFIX}MANIFEST_v1.0.json"
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            print("manifest is stale")
            return 1
        print("manifest is current")
        return 0
    target.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(manifest["totals"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
