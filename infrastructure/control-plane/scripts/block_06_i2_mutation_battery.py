#!/usr/bin/env python3
"""B6-I2 mutation battery.

Six governed mutations, each anchored in live B6-I2 code inside an isolated detached worktree.
A mutation may remove more than one guard when the same failure class is enforced at more than one
layer; it must still turn exactly one named node red. Every mutation must restore the pristine
bytes exactly; the worktree must be green before mutating and after restoration. The authority
floor is 3; this stage freezes 6 and never lowers it.

Usage:
  python infrastructure/control-plane/scripts/block_06_i2_mutation_battery.py [--json out.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

ARCHIVE = "oce/templates/archive.py"
SKELETON = "oce/templates/skeleton.py"
LOCAL = "oce/harness/local.py"
TESTS = "infrastructure/control-plane/tests"
FLOOR = 6

TRAVERSAL_SCHEMA_GUARD = (
    '    if any(part in ("..", ".") for part in parts):\n'
    '        refuse("REFUSED_PATH_TRAVERSAL", path)\n'
)
TRAVERSAL_INSTALL_GUARD = (
    "        try:\n"
    "            resolved.relative_to(root)\n"
    "        except ValueError:\n"
    '            refuse("REFUSED_PATH_TRAVERSAL", entry["path"])\n'
)

MUTATIONS = [
    ("M01", "both path traversal guards removed", ARCHIVE,
     (TRAVERSAL_SCHEMA_GUARD, TRAVERSAL_INSTALL_GUARD),
     ("    if False:\n        pass\n", "        if False:\n            pass\n"),
     f"{TESTS}/test_block_06_i2_archive_safety.py::test_path_traversal_refused"),
    ("M02", "symlink refusal removed", ARCHIVE,
     '        if entry["mode"] == "symlink":', "        if False:",
     f"{TESTS}/test_block_06_i2_archive_safety.py::test_symlink_escape_refused"),
    ("M03", "payload digest check removed", ARCHIVE,
     '    if manifest["payload_digest"] != payload_digest(checked):', "    if False:",
     f"{TESTS}/test_block_06_i2_archive_safety.py::test_digest_mismatch_refused"),
    ("M04", "nondeterministic build nonce added", SKELETON,
     "    app = dict(APP, name=name)",
     '    app = dict(APP, name=name, nonce=__import__("uuid").uuid4().hex)',
     f"{TESTS}/test_block_06_i2_templates.py::test_deterministic_build_byte_identical"),
    ("M05", "unknown profile fallback", LOCAL,
     "    if profile not in PROFILES:", "    if False:",
     f"{TESTS}/test_block_06_i2_harness.py::test_unknown_profile_refused"),
    ("M06", "network import refusal removed", LOCAL,
     "        if root in NETWORK_MODULES:", "        if False:",
     f"{TESTS}/test_block_06_i2_harness.py::test_undeclared_network_call_refused"),
]


def run_node(root: pathlib.Path, nodes) -> tuple[int, str]:
    args = [nodes] if isinstance(nodes, str) else list(nodes)
    proc = subprocess.run([sys.executable, "-m", "pytest", *args, "-q", "-p", "no:cacheprovider",
                           "-o", "addopts="], cwd=str(root), capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def apply(text: str, olds, news) -> tuple[str, str | None]:
    old_list = olds if isinstance(olds, (tuple, list)) else (olds,)
    new_list = news if isinstance(news, (tuple, list)) else (news,)
    if len(old_list) != len(new_list):
        return text, "anchor arity mismatch"
    for old, new in zip(old_list, new_list):
        if old not in text:
            return text, f"anchor not found: {old.splitlines()[0][:60]}"
        text = text.replace(old, new, 1)
    return text, None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    ap.add_argument("--root", default=None)
    args = ap.parse_args(argv)
    root = (pathlib.Path(args.root).resolve() if args.root
            else pathlib.Path(__file__).resolve().parents[3])
    results = []
    with tempfile.TemporaryDirectory(prefix="b6i2-mut-") as tmp:
        work = pathlib.Path(tmp) / "wt"
        subprocess.run(["git", "-C", str(root), "worktree", "add", "--detach", "--quiet",
                        str(work), "HEAD"], check=True)
        try:
            all_nodes = [str(p) for p in sorted((work / TESTS).glob("test_block_06_i2_*.py"))]
            code, out = run_node(work, all_nodes)
            if code != 0:
                print(out[-3000:])
                print("pristine worktree is red; refusing to mutate")
                return 2
            for mid, label, relative, old, new, node in MUTATIONS:
                target = work / relative
                pristine = target.read_bytes()
                mutated, error = apply(pristine.decode("utf-8"), old, new)
                if error:
                    results.append({"id": mid, "mutation": label, "expected_node": node,
                                    "discriminated": False, "restored": True, "error": error})
                    continue
                target.write_text(mutated, encoding="utf-8", newline="\n")
                mutated_code, mutated_out = run_node(work, node)
                target.write_bytes(pristine)
                restored = (hashlib.sha256(target.read_bytes()).hexdigest()
                            == hashlib.sha256(pristine).hexdigest())
                results.append({"id": mid, "mutation": label, "expected_node": node,
                                "observed_rc": mutated_code, "discriminated": mutated_code != 0,
                                "discriminator_ok": node.split("::")[-1] in mutated_out,
                                "restored": restored,
                                "pre_sha256": hashlib.sha256(pristine).hexdigest(),
                                "post_sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
            code, out = run_node(work, all_nodes)
            pristine_green = code == 0
        finally:
            subprocess.run(["git", "-C", str(root), "worktree", "remove", "--force", str(work)],
                           check=False)
    payload = {
        "battery": "block_06_i2_mutation_battery.py",
        "floor": FLOOR,
        "total": len(results),
        "discriminated": sum(1 for row in results if row["discriminated"]),
        "restored": sum(1 for row in results if row["restored"]),
        "pristine_green_after": pristine_green,
        "all_ok": (sum(1 for row in results if row["discriminated"]) >= FLOOR
                   and all(row["discriminator_ok"] for row in results)
                   and all(row["restored"] for row in results) and pristine_green),
        "results": results,
    }
    text = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    if args.json:
        pathlib.Path(args.json).write_text(text, encoding="utf-8", newline="\n")
    print(f"floor {payload['floor']} | mutations {payload['total']} | "
          f"discriminated {payload['discriminated']} | restored {payload['restored']} | "
          f"pristine_green {pristine_green}")
    for row in results:
        print(("OK " if row["discriminated"] and row["restored"] else "BAD ")
              + f"{row['id']} {row['mutation']} -> {row['expected_node'].split('::')[-1]}"
              + (f" [{row.get('error')}]" if row.get("error") else ""))
    return 0 if payload["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
