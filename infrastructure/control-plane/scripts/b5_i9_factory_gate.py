#!/usr/bin/env python3
"""B5-I9 factory gate — deterministic, offline generator and checker.

    python infrastructure/control-plane/scripts/b5_i9_factory_gate.py --emit DIR
    python infrastructure/control-plane/scripts/b5_i9_factory_gate.py --check
    python infrastructure/control-plane/scripts/b5_i9_factory_gate.py --json

`--emit` writes the governed packet to a directory. `--check` regenerates the packet in a
temporary directory outside the repository and compares it byte-for-byte with the
committed packet; it writes nothing into the repository and exits non-zero on any
difference. No network, no secrets, no clock, no host, no absolute path in any artifact.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import b5_i9_gate as gate  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--emit", metavar="DIR", help="write the packet to DIR")
    group.add_argument("--check", action="store_true",
                       help="regenerate and compare with the committed packet")
    parser.add_argument("--json", action="store_true", help="machine-readable result")
    parser.add_argument("--root", default=None, help="repository root (tests and mutations)")
    args = parser.parse_args(argv)

    repo = gate.Repo(args.root)
    out = {"tool": "b5_i9_factory_gate.py", "status": "PASS", "stage": gate.STAGE}
    if args.emit:
        validation = gate.emit(repo, pathlib.Path(args.emit))
        out["emitted"] = str(len(validation["results"])) + " invariants"
        out["packet_digest"] = validation["packet_digest"]
    else:
        problems = gate.diff_packet(repo, repo.packet)
        out["problems"] = problems
        out["status"] = "PASS" if not problems else "FAIL"
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print("B5-I9 factory gate: {}".format(out["status"]))
        for problem in out.get("problems", []):
            print("  " + problem)
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
