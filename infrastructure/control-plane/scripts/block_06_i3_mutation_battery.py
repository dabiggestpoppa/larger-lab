#!/usr/bin/env python3
"""B6-I3 mutation battery: six governed mutations, floor 3, restored byte-exact."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

CAPABILITY = "oce/operator/capability.py"
APPROVALS = "oce/operator/approvals.py"
EVIDENCE = "oce/operator/evidence.py"
TESTS = "infrastructure/control-plane/tests"
FLOOR = 6

MUTATIONS = [
    ("M01", "proven evidence check removed", CAPABILITY,
     '        if record["proven"] and record.get("evidence_sha256") not in evidence_index:',
     "        if False:",
     f"{TESTS}/test_block_06_i3_capability.py::test_proven_requires_evidence"),
    ("M02", "self-approval refusal removed", APPROVALS,
     '    if decision == "APPROVE" and actor == request["requester"]:',
     "    if False:",
     f"{TESTS}/test_block_06_i3_approvals.py::test_self_approval_refused"),
    ("M03", "nonce replay check removed", APPROVALS,
     '    if request["nonce"] in consumed:',
     "    if False:",
     f"{TESTS}/test_block_06_i3_approvals.py::test_replay_refused"),
    ("M04", "expiry check removed", APPROVALS,
     '    if int(now) >= int(request["expires_at"]):',
     "    if False:",
     f"{TESTS}/test_block_06_i3_approvals.py::test_stale_refused"),
    ("M05", "target digest check removed", APPROVALS,
     '    if actual_target_sha256 != request["target_sha256"]:',
     "    if False:",
     f"{TESTS}/test_block_06_i3_approvals.py::test_wrong_target_refused"),
    ("M06", "parent link check removed", EVIDENCE,
     '        if previous is not None and node["parent"] != previous:',
     "        if False:",
     f"{TESTS}/test_block_06_i3_evidence.py::test_broken_link_refused"),
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
    with tempfile.TemporaryDirectory(prefix="b6i3-mut-") as tmp:
        work = pathlib.Path(tmp) / "wt"
        subprocess.run(["git", "-C", str(root), "worktree", "add", "--detach", "--quiet",
                        str(work), "HEAD"], check=True)
        try:
            modules = [str(p) for p in sorted((work / TESTS).glob("test_block_06_i3_*.py"))]
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
        "battery": "block_06_i3_mutation_battery.py",
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
