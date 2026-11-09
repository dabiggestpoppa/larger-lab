#!/usr/bin/env python3
"""B6-I1 mutation battery.

Each mutation edits one live implementation invariant inside an isolated detached Git worktree,
must turn a named governed node red, and must restore the pristine bytes exactly. A detached
worktree (rather than a plain copy) keeps the boundary node meaningful, because the checkout has
real Git topology. The authority floor is 3; this stage freezes 6 and never lowers it.

Usage:
  python infrastructure/control-plane/scripts/block_06_i1_mutation_battery.py [--json out.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

SERVICE = "oce/api/v1/service.py"
TESTS = "infrastructure/control-plane/tests"
FLOOR = 6

MUTATIONS = [
    ("M01", "scope check removed",
     "        if required not in scopes:",
     "        if False:",
     f"{TESTS}/test_block_06_i1_denial.py::test_missing_scope_refused"),
    ("M02", "version refusal removed (silent coercion)",
     "        if version != C.API_VERSION:",
     "        if False:",
     f"{TESTS}/test_block_06_i1_denial.py::test_unknown_version_refused_and_echoed"),
    ("M03", "exact payload schema relaxed",
     "        if set(payload) != set(spec[\"typed_inputs\"]):",
     "        if False:",
     f"{TESTS}/test_block_06_i1_denial.py::test_extra_payload_key_refused"),
    ("M04", "storage internals returned to the caller",
     "        result = self._dispatch(operation, actor, payload)",
     "        result = {\"store_path\": \"/srv/oce/store.db\", \"operation\": operation}",
     f"{TESTS}/test_block_06_i1_authority_and_boundary.py"
     "::test_no_private_store_or_path_in_any_result"),
    ("M05", "self-approval allowed",
     "            if actor == row[\"requester\"]:",
     "            if False:",
     f"{TESTS}/test_block_06_i1_authority_and_boundary.py::test_self_approval_refused"),
    ("M06", "client-supplied authority accepted",
     "        if keys & set(C.ENVELOPE_FORBIDDEN):",
     "        if False:",
     f"{TESTS}/test_block_06_i1_denial.py::test_client_authority_field_refused"),
]


def run_node(root: pathlib.Path, nodes) -> tuple[int, str]:
    args = [nodes] if isinstance(nodes, str) else list(nodes)
    proc = subprocess.run([sys.executable, "-m", "pytest", *args, "-q", "-p", "no:cacheprovider",
                           "-o", "addopts="], cwd=str(root), capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    ap.add_argument("--root", default=None)
    args = ap.parse_args(argv)
    root = pathlib.Path(args.root).resolve() if args.root else pathlib.Path(__file__).resolve().parents[3]
    results = []
    with tempfile.TemporaryDirectory(prefix="b6i1-mut-") as tmp:
        work = pathlib.Path(tmp) / "wt"
        subprocess.run(["git", "-C", str(root), "worktree", "add", "--detach", "--quiet", str(work)],
                       check=True)
        try:
            all_nodes = [str(p) for p in sorted((work / TESTS).glob("test_block_06_i1_*.py"))]
            code, out = run_node(work, all_nodes)
            if code != 0:
                print(out[-3000:])
                print("pristine worktree is red; refusing to mutate")
                return 2
            for mid, label, old, new, node in MUTATIONS:
                target = work / SERVICE
                pristine = target.read_bytes()
                text = pristine.decode("utf-8")
                if old not in text:
                    results.append({"id": mid, "mutation": label, "expected_node": node,
                                    "discriminated": False, "restored": True,
                                    "error": "anchor not found"})
                    continue
                target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
                code, out = run_node(work, node)
                target.write_bytes(pristine)
                restored = (hashlib.sha256(target.read_bytes()).hexdigest()
                            == hashlib.sha256(pristine).hexdigest())
                results.append({"id": mid, "mutation": label, "expected_node": node,
                                "observed_rc": code, "discriminated": code != 0,
                                "restored": restored,
                                "pre_sha256": hashlib.sha256(pristine).hexdigest(),
                                "post_sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
            code, out = run_node(work, all_nodes)
            pristine_green = code == 0
        finally:
            subprocess.run(["git", "-C", str(root), "worktree", "remove", "--force", str(work)],
                           check=False)
    payload = {
        "battery": "block_06_i1_mutation_battery.py",
        "floor": FLOOR,
        "total": len(results),
        "discriminated": sum(1 for r in results if r["discriminated"]),
        "restored": sum(1 for r in results if r["restored"]),
        "pristine_green_after": pristine_green,
        "all_ok": (sum(1 for r in results if r["discriminated"]) >= FLOOR
                   and all(r["restored"] for r in results) and pristine_green),
        "results": results,
    }
    text = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    if args.json:
        pathlib.Path(args.json).write_text(text, encoding="utf-8", newline="\n")
    print(f"floor {payload['floor']} | mutations {payload['total']} | "
          f"discriminated {payload['discriminated']} | restored {payload['restored']} | "
          f"pristine_green {pristine_green}")
    for row in results:
        print(("OK " if row["discriminated"] and row["restored"] else "BAD ") +
              f"{row['id']} {row['mutation']} -> {row['expected_node'].split('::')[-1]}")
    return 0 if payload["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
