#!/usr/bin/env python3
"""B6-I0 mutation battery.

Each mutation targets one frozen invariant, is observed on a scratch copy of the packet, must be
refused by a named validator check, and must leave the packet byte-identical afterwards. The
frozen floor is 12 and is never lowered. Standard library only, offline.

Usage:
  python infrastructure/control-plane/scripts/block_06_i0_mutation_battery.py
  python infrastructure/control-plane/scripts/block_06_i0_mutation_battery.py --json out.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

DOCS = "docs/oce-golden-system"
FLOOR = 12
VALIDATOR = "infrastructure/control-plane/scripts/block_06_i0_validate.py"
ARTIFACTS = {
    "scope": f"{DOCS}/OCE_BLOCK_06_I0_SCOPE_DERIVATION_v1.0.json",
    "contract": f"{DOCS}/OCE_BLOCK_06_I0_IMPLEMENTATION_CONTRACT_v1.0.json",
    "decisions": f"{DOCS}/OCE_BLOCK_06_I0_EXTRACTION_DECISION_FREEZE_v1.0.json",
    "api": f"{DOCS}/OCE_BLOCK_06_I0_API_PRINCIPLES_AND_FIREWALL_v1.0.json",
    "compat": f"{DOCS}/OCE_BLOCK_06_I0_COMPATIBILITY_AND_CONFORMANCE_BASELINE_v1.0.json",
    "failures": f"{DOCS}/OCE_BLOCK_06_I0_FAILURE_AND_THREAT_PROOFS_v1.0.json",
    "registry": f"{DOCS}/OCE_BLOCK_06_I0_REQUIREMENT_TEST_REGISTRY_v1.0.json",
    "manifest": f"{DOCS}/OCE_BLOCK_06_I0_MANIFEST_v1.0.json",
}


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def set_decision(data, decision):
    for row in data["candidates"]:
        if row["classification"] == "AUTHORITY_BEARING":
            row["decision"] = decision
            return


def promote_api(data, classification):
    for row in data["symbols"]:
        if row["classification"] == "internal":
            row["classification"] = classification
            return


MUTATIONS = [
    ("M01", "decisions", "candidate eligibility drift",
     lambda d: d["candidates"][0].__setitem__("eligibility",
                                              not d["candidates"][0]["eligibility"]),
     "dec/eligibility_matches_source"),
    ("M02", "decisions", "authority-bearing admission",
     lambda d: set_decision(d, "ADMITTED_FOR_FUTURE_DESIGN"), "dec/authority_never"),
    ("M03", "api", "private API promotion",
     lambda d: promote_api(d, "public_experimental"), "api/distribution"),
    ("M04", "api", "public visibility drift",
     lambda d: d["observed"].__setitem__("exports", 1), "api/exports_zero"),
    ("M05", "compat", "unknown version accepted",
     lambda d: d["refusal"].__setitem__("unknown_version", "ACCEPTED"), "compat/unknown_refused"),
    ("M06", "compat", "silent-latest behaviour",
     lambda d: d["refusal"].__setitem__("silent_latest", True), "compat/no_silent_latest"),
    ("M07", "compat", "compatibility status inflation",
     lambda d: d["compatibility_rows"][0].__setitem__("state", "PROVEN"), "compat/all_unproven"),
    ("M08", "compat", "missing evidence treated as PASS",
     lambda d: d["conformance"].__setitem__("default_state", "PASS"), "compat/default_unproven"),
    ("M09", "contract", "operator hold removal",
     lambda d: d["operator_hold"].__setitem__("b6_i0_merge_authorized", True),
     "contract/operator_hold"),
    ("M10", "contract", "publication authorization",
     lambda d: d["operator_hold"].__setitem__("package_publication_authorized", True),
     "contract/operator_hold"),
    ("M11", "manifest", "manifest tampering",
     lambda d: d["artifacts"][0].__setitem__("sha256", "0" * 64), "manifest/hashes_match"),
    ("M12", "api", "environment-variable authority",
     lambda d: d["prohibitions"].remove("environment_variable_authority"),
     "api/env_authority_absent"),
]


def scratch(root: pathlib.Path, dst: pathlib.Path) -> pathlib.Path:
    shutil.copytree(root / DOCS, dst / DOCS)
    shutil.copytree(root / "infrastructure/control-plane/evidence",
                    dst / "infrastructure/control-plane/evidence")
    shutil.copytree(root / "infrastructure/control-plane/scripts",
                    dst / "infrastructure/control-plane/scripts")
    shutil.copytree(root / "infrastructure/control-plane/tests",
                    dst / "infrastructure/control-plane/tests")
    return dst


def run_validator(root: pathlib.Path) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(root / VALIDATOR), "--root", str(root)],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    ap.add_argument("--root", default=None)
    args = ap.parse_args(argv)
    root = pathlib.Path(args.root).resolve() if args.root else pathlib.Path(__file__).resolve().parents[3]
    results = []
    with tempfile.TemporaryDirectory(prefix="b6i0-mut-") as tmp:
        work = scratch(root, pathlib.Path(tmp) / "packet")
        code, out = run_validator(work)
        if code != 0:
            print(out[-2000:])
            print("pristine packet is already red; refusing to mutate")
            return 2
        for mid, key, label, mutate, expected in MUTATIONS:
            target = work / ARTIFACTS[key]
            pristine = target.read_bytes()
            before = hashlib.sha256(pristine).hexdigest()
            data = json.loads(pristine)
            mutate(data)
            target.write_bytes(canonical(data))
            code, out = run_validator(work)
            checks = [line.split("FAIL ", 1)[1].split(":", 1)[0]
                      for line in out.splitlines() if line.startswith("FAIL ")]
            target.write_bytes(pristine)
            after = hashlib.sha256(target.read_bytes()).hexdigest()
            results.append({
                "id": mid,
                "mutation": label,
                "target": ARTIFACTS[key],
                "expected_check": expected,
                "observed_checks": checks,
                "discriminated": code != 0 and expected in checks,
                "restored": before == after,
                "pre_sha256": before,
                "post_sha256": after,
            })
        if os.name != "nt":
            target = work / ARTIFACTS["scope"]
            pristine = target.read_bytes()
            target.unlink()
            target.symlink_to(work / ARTIFACTS["contract"])
            code, out = run_validator(work)
            checks = [line.split("FAIL ", 1)[1].split(":", 1)[0]
                      for line in out.splitlines() if line.startswith("FAIL ")]
            target.unlink()
            target.write_bytes(pristine)
            results.append({
                "id": "M13",
                "mutation": "symlink escape over a packet artifact",
                "target": ARTIFACTS["scope"],
                "expected_check": "boundary/no_symlinked_artifacts",
                "observed_checks": checks,
                "discriminated": code != 0 and "boundary/no_symlinked_artifacts" in checks,
                "restored": hashlib.sha256(target.read_bytes()).hexdigest()
                == hashlib.sha256(pristine).hexdigest(),
                "pre_sha256": hashlib.sha256(pristine).hexdigest(),
                "post_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            })
        code, out = run_validator(work)
        pristine_green = code == 0
    payload = {
        "battery": "block_06_i0_mutation_battery.py",
        "floor": FLOOR,
        "total": len(results),
        "discriminated": sum(1 for r in results if r["discriminated"]),
        "restored": sum(1 for r in results if r["restored"]),
        "pristine_green_after": pristine_green,
        "all_ok": (sum(1 for r in results if r["discriminated"]) >= FLOOR
                   and all(r["restored"] for r in results) and pristine_green),
        "results": results,
    }
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.json:
        pathlib.Path(args.json).write_text(text, encoding="utf-8", newline="\n")
    print(f"floor {payload['floor']} | mutations {payload['total']} | "
          f"discriminated {payload['discriminated']} | restored {payload['restored']} | "
          f"pristine_green {payload['pristine_green_after']}")
    for row in results:
        status = "OK" if row["discriminated"] and row["restored"] else "BAD"
        print(f"{status} {row['id']} {row['mutation']} -> {row['expected_check']}")
    return 0 if payload["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
