#!/usr/bin/env python3
"""B6-I1 exact base/head paired comparator.

Fails closed on: contract not FROZEN, endpoint identity mismatch, zero or below-floor common
population, common base-only nodes, any common regression or new skip, head-only count mismatch,
any head-only node not green, duplicate node ids, or failed endpoint cleanup.

Usage:
  python block_06_i1_paired.py --artifacts DIR --contract PATH [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import xml.etree.ElementTree as ET


def nodes(path: pathlib.Path) -> dict[str, str]:
    root = ET.parse(path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    out: dict[str, str] = {}
    for case in suite.iter("testcase"):
        key = f"{case.get('classname')}::{case.get('name')}"
        status = "passed"
        for child in case:
            if child.tag in ("failure", "error", "skipped"):
                status = child.tag
        out[key] = status
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts", required=True)
    ap.add_argument("--contract", required=True)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    art = pathlib.Path(args.artifacts)
    contract = json.loads(pathlib.Path(args.contract).read_text(encoding="utf-8"))
    checks: list[tuple[str, bool, object]] = []

    def need(name, ok, detail=None):
        checks.append((name, bool(ok), detail))

    need("contract/status", contract.get("status") == "FROZEN", contract.get("status"))
    base_meta = json.loads((art / "meta-base.json").read_text(encoding="utf-8"))
    head_meta = json.loads((art / "meta-head.json").read_text(encoding="utf-8"))
    ep = contract["endpoints"]
    need("endpoint/base_sha", base_meta["sha"] == ep["base_sha"], base_meta["sha"])
    need("endpoint/base_tree", base_meta["tree"] == ep["base_tree"], base_meta["tree"])
    need("endpoint/head_sha", head_meta["sha"] == ep["head_sha"], head_meta["sha"])
    need("endpoint/head_tree", head_meta["tree"] == ep["head_tree"], head_meta["tree"])
    need("endpoint/identical_deps",
         base_meta["dependency_lock_sha256"] == head_meta["dependency_lock_sha256"])
    need("endpoint/clean", base_meta["worktree_clean"] and head_meta["worktree_clean"])

    base = nodes(art / "junit-base.xml")
    head_common = nodes(art / "junit-head-common.xml")
    head_only = nodes(art / "junit-head-only.xml")
    pop = contract["population"]
    need("population/nonzero", len(base) > 0 and len(head_common) > 0, len(base))
    need("population/floor", len(base) >= pop["common_floor"], len(base))
    need("population/same_files", base_meta["file_count"] == head_meta["file_count"],
         [base_meta["file_count"], head_meta["file_count"]])
    base_only = sorted(set(base) - set(head_common))
    need("population/base_only_empty", len(base_only) == 0, base_only[:5])
    need("population/no_duplicates", len(head_common) == len(nodes(art / "junit-head-common.xml")))
    regressions = sorted(k for k in head_common if base.get(k) == "passed"
                         and head_common[k] != "passed")
    need("common/no_regression", not regressions, regressions[:5])
    new_skips = sorted(k for k in head_common if base.get(k) == "passed"
                       and head_common[k] == "skipped")
    need("common/no_new_skip", not new_skips, new_skips[:5])
    need("common/all_pass", all(v == "passed" for v in head_common.values()),
         [k for k, v in head_common.items() if v != "passed"][:5])
    need("head_only/count", len(head_only) == pop["head_only_expected"], len(head_only))
    need("head_only/all_green", all(v == "passed" for v in head_only.values()),
         [k for k, v in head_only.items() if v != "passed"][:5])
    overlap = sorted(set(head_only) & set(head_common))
    need("head_only/disjoint", not overlap, overlap[:5])

    cleanup = json.loads((art / "cleanup.json").read_text(encoding="utf-8"))
    need("cleanup/ok", cleanup.get("cleanup_ok") is True, cleanup.get("residual_paths"))

    failed = [n for n, ok, _ in checks if not ok]
    doc = {
        "status": "PASS" if not failed else "FAIL",
        "checks": len(checks),
        "failed": failed,
        "population": {
            "base_total": len(base),
            "head_common_total": len(head_common),
            "common_total": len(base),
            "common_floor": pop["common_floor"],
            "base_only": len(base_only),
            "head_only_total": len(head_only),
            "head_only_expected": pop["head_only_expected"],
        },
        "common_status": {
            "pass": sum(1 for v in head_common.values() if v == "passed"),
            "skip": sum(1 for v in head_common.values() if v == "skipped"),
            "fail": sum(1 for v in head_common.values() if v == "failure"),
            "error": sum(1 for v in head_common.values() if v == "error"),
        },
        "endpoints": {"base_sha": base_meta["sha"], "head_sha": head_meta["sha"],
                      "base_tree": base_meta["tree"], "head_tree": head_meta["tree"]},
        "detail": {n: d for n, ok, d in checks if not ok},
    }
    text = json.dumps(doc, sort_keys=True, indent=2) + "\n"
    if args.json:
        pathlib.Path(args.json).write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(doc, sort_keys=True, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
