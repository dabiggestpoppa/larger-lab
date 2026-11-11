#!/usr/bin/env python3
"""B6-I4 mutation battery: six governed mutations, source floor 4, restored byte-exact."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

INCIDENT = "oce/operator/incident.py"
COST = "oce/operator/cost.py"
IDENTITY = "oce/services/identity.py"
WORKFLOW = "oce/services/workflow.py"
TESTS = "infrastructure/control-plane/tests"
FLOOR = 6

MUTATIONS = [
    ("M01", "severity vocabulary check removed", INCIDENT,
     '        if incident["severity"] not in RANK:',
     "        if False:",
     f"{TESTS}/test_block_06_i4_incident.py::test_invalid_severity_refused"),
    ("M02", "timeline monotonicity check removed", INCIDENT,
     '        if previous is not None and at < previous:',
     "        if False:",
     f"{TESTS}/test_block_06_i4_incident.py::test_timeline_must_be_monotonic"),
    ("M03", "cost category check removed", COST,
     '        if entry["category"] not in CATEGORIES:',
     "        if False:",
     f"{TESTS}/test_block_06_i4_cost.py::test_unknown_category_refused"),
    ("M04", "raw secret refusal removed", IDENTITY,
     '        if str(key).lower() in SECRET_KEYS:',
     "        if False:",
     f"{TESTS}/test_block_06_i4_identity.py::test_raw_secret_refused"),
    ("M05", "cross-app isolation check removed", IDENTITY,
     '    if identity["app"] != app:',
     "    if False:",
     f"{TESTS}/test_block_06_i4_identity.py::test_cross_app_isolation_refused"),
    ("M06", "lease owner check removed", WORKFLOW,
     '    if lease is None or lease["owner"] != actor or int(now) >= int(lease["expires_at"]):',
     "    if False:",
     f"{TESTS}/test_block_06_i4_workflow.py::test_lease_owner_required"),
]


def run_node(root: pathlib.Path, node: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-m", "pytest", node, "-q", "-p", "no:cacheprovider",
                           "-o", "addopts="], cwd=str(root), capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    ap.add_argument("--root", default=None)
    args = ap.parse_args(argv)
    root = (pathlib.Path(args.root).resolve() if args.root
            else pathlib.Path(__file__).resolve().parents[3])
    results = []
    pristine_green = False
    with tempfile.TemporaryDirectory(prefix="b6i4-mut-") as tmp:
        work = pathlib.Path(tmp) / "wt"
        subprocess.run(["git", "-C", str(root), "worktree", "add", "--detach", "--quiet",
                        str(work), "HEAD"], check=True)
        try:
            modules = [str(p) for p in sorted((work / TESTS).glob("test_block_06_i4_*.py"))]
            code = subprocess.run([sys.executable, "-m", "pytest", *modules, "-q",
                                   "-p", "no:cacheprovider", "-o", "addopts="],
                                  cwd=str(work), capture_output=True, text=True)
            if code.returncode != 0:
                print(code.stdout[-3000:])
                print("pristine worktree is red; refusing to mutate")
                return 2
            for mid, label, relative, old, new, node in MUTATIONS:
                target = work / relative
                pristine = target.read_bytes()
                text = pristine.decode("utf-8")
                if old not in text:
                    results.append({"id": mid, "mutation": label, "expected_node": node,
                                    "discriminated": False, "restored": True,
                                    "error": "anchor not found"})
                    continue
                target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
                mutated_code, mutated_out = run_node(work, node)
                target.write_bytes(pristine)
                results.append({
                    "id": mid, "mutation": label, "expected_node": node,
                    "observed_rc": mutated_code, "discriminated": mutated_code != 0,
                    "discriminator_ok": node.split("::")[-1] in mutated_out,
                    "restored": hashlib.sha256(target.read_bytes()).hexdigest()
                    == hashlib.sha256(pristine).hexdigest(),
                    "pre_sha256": hashlib.sha256(pristine).hexdigest(),
                    "post_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                })
            code = subprocess.run([sys.executable, "-m", "pytest", *modules, "-q",
                                   "-p", "no:cacheprovider", "-o", "addopts="],
                                  cwd=str(work), capture_output=True, text=True)
            pristine_green = code.returncode == 0
        finally:
            subprocess.run(["git", "-C", str(root), "worktree", "remove", "--force", str(work)],
                           check=False)
    payload = {
        "battery": "block_06_i4_mutation_battery.py",
        "floor": FLOOR,
        "total": len(results),
        "discriminated": sum(1 for row in results if row["discriminated"]),
        "restored": sum(1 for row in results if row["restored"]),
        "pristine_green_after": pristine_green,
        "all_ok": (sum(1 for row in results if row["discriminated"]) >= FLOOR
                   and all(row.get("discriminator_ok") for row in results)
                   and all(row["restored"] for row in results) and pristine_green),
        "results": results,
    }
    text = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    if args.json:
        pathlib.Path(args.json).write_text(text, encoding="utf-8", newline="\n")
    print(f"floor {FLOOR} | mutations {len(results)} | discriminated {payload['discriminated']} "
          f"| restored {payload['restored']} | pristine_green {pristine_green}")
    for row in results:
        print(("OK " if row["discriminated"] and row["restored"] else "BAD ")
              + f"{row['id']} {row['mutation']} -> {row['expected_node'].split('::')[-1]}")
    return 0 if payload["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
