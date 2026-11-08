#!/usr/bin/env python3
"""B6-I0 stage gate runner.

Executes the frozen Book 5 gate the stage must not weaken: the factory-gate packet check and the
41 frozen nodes. It lives in a script rather than in the workflow body so the frozen B5-I9
authority keeps exactly one workflow that selects it, while B6-I0 CI still runs it.

Offline, standard library only, no secrets, no network.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

TESTS = (
    "test_b5_i9_stage_identity_and_scope.py",
    "test_b5_i9_extraction_classification.py",
    "test_b5_i9_no_platform_extraction.py",
    "test_b5_i9_packet_packaging_and_provenance.py",
    "test_b5_i9_book6_handoff.py",
)
EXPECTED_NODES = 41


def run(args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    root = pathlib.Path(__file__).resolve().parents[3]
    factory = root / "infrastructure/control-plane/scripts/b5_i9_factory_gate.py"
    packet = run([sys.executable, str(factory), "--check"], root)
    files = [str(root / "infrastructure/control-plane/tests" / name) for name in TESTS]
    nodes = run([sys.executable, "-m", "pytest", *files, "-q", "--no-header",
                 "-p", "no:cacheprovider"], root)
    payload = {
        "gate": "block_06_i0_gate.py",
        "factory_gate_rc": packet.returncode,
        "nodes_rc": nodes.returncode,
        "expected_nodes": EXPECTED_NODES,
        "nodes_passed": f"{EXPECTED_NODES} passed" in nodes.stdout,
        "factory_tail": packet.stdout.strip().splitlines()[-3:],
        "nodes_tail": nodes.stdout.strip().splitlines()[-2:],
    }
    payload["ok"] = (payload["factory_gate_rc"] == 0 and payload["nodes_rc"] == 0
                     and payload["nodes_passed"])
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.json:
        pathlib.Path(args.json).write_text(text, encoding="utf-8", newline="\n")
    print(text)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
