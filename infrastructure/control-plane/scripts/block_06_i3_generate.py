#!/usr/bin/env python3
"""Regenerate the B6-I3 evidence manifest from the frozen packet and code."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

DOCS = "docs/oce-golden-system"
PREFIX = "OCE_BLOCK_06_I3_"
SCRIPTS = "infrastructure/control-plane/scripts"
BASE_SHA = "018b164f249bbf075334d5d03ad37e80dcbbede0"


def rows(root: pathlib.Path, paths) -> list[dict]:
    out = []
    for path in sorted(paths):
        data = path.read_bytes()
        out.append({"path": path.relative_to(root).as_posix(), "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest()})
    return out


def build(root: pathlib.Path) -> dict:
    artifacts = [p for p in sorted((root / DOCS).glob(f"{PREFIX}*.json"))
                 if not p.name.endswith("MANIFEST_v1.0.json")]
    code = sorted((root / "oce/operator").glob("*.py")) + sorted(
        (root / SCRIPTS).glob("block_06_i3_*.py"))
    return {
        "schema": "oce.block_06_i3.manifest.v1",
        "document_id": "OCE-B6-I3-MANIFEST-001",
        "stage": "B6-I3",
        "status": "FROZEN",
        "base_sha": BASE_SHA,
        "hash": "sha256",
        "size": "bytes",
        "artifacts": rows(root, artifacts),
        "code": rows(root, code),
        "totals": {"artifacts": len(artifacts), "code": len(code)},
        "verification": {"independent": True, "excludes_manifest": True},
        "locks": {"B6-I4_through_I9": "LOCKED", "BOOK_6_COMPLETE": False,
                  "MERGE_AUTHORIZED": False, "RATIFICATION_AUTHORIZED": False,
                  "capital_authority": "none", "cost_usd": 0},
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    root = pathlib.Path(args.root).resolve() if args.root else pathlib.Path(__file__).resolve().parents[3]
    manifest = root / DOCS / f"{PREFIX}MANIFEST_v1.0.json"
    text = json.dumps(build(root), sort_keys=True, indent=2) + "\n"
    if args.check:
        current = manifest.read_text(encoding="utf-8") if manifest.exists() else ""
        if current != text:
            print("manifest is stale")
            return 1
        print("manifest is current")
        return 0
    manifest.write_text(text, encoding="utf-8", newline="\n")
    doc = json.loads(text)
    print(f"wrote {manifest.name}: {doc['totals']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
