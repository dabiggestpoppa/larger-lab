#!/usr/bin/env python3
"""B6-I0 exact base/head paired comparison.

The B6-I0 stage inherits an exact paired-comparison obligation: the pre-stage main endpoint and
the final implementation endpoint must be executed under identical setup, and every node common
to both endpoints must keep its status. This comparator re-derives that verdict from raw JUnit
evidence; it trusts no badge and no report.

Endpoints are pinned by the committed contract. Missing evidence is never a pass: an absent file,
an unparsable file, an empty population or a disappearing common node all fail closed.

Standard library only, offline, no secrets, repository-relative paths.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import xml.etree.ElementTree as ET

EXPECTED_STATUS = {"pass", "skip"}


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def parse_junit(path: pathlib.Path) -> dict[str, str]:
    """Map ``classname::name`` to a single status, failing closed on an unusable document."""
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    nodes: dict[str, str] = {}
    for suite in suites:
        for case in suite.iter("testcase"):
            key = f"{case.get('classname', '')}::{case.get('name', '')}"
            if case.find("failure") is not None:
                status = "fail"
            elif case.find("error") is not None:
                status = "error"
            elif case.find("skipped") is not None:
                status = "skip"
            else:
                status = "pass"
            nodes[key] = status
    return nodes


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def compare(artifacts: pathlib.Path, contract_path: pathlib.Path) -> dict:
    contract = load(contract_path)
    endpoints = contract["endpoints"]
    population = contract["population"]
    floor = int(population["common_floor"])
    expected_head_only = int(population["head_only_expected"])
    checks: list[dict] = []

    def need(name: str, cond: bool, detail="") -> None:
        checks.append({"check": name, "ok": bool(cond), "detail": "" if cond else str(detail)})

    need("contract/status", contract.get("status") == "FROZEN", contract.get("status"))
    need("contract/floor_positive", floor > 0, floor)

    files = {
        "base": artifacts / "junit-base.xml",
        "head_common": artifacts / "junit-head-common.xml",
        "head_only": artifacts / "junit-head-only.xml",
        "meta_base": artifacts / "meta-base.json",
        "meta_head": artifacts / "meta-head.json",
    }
    missing = [k for k, p in files.items() if not p.exists()]
    need("evidence/present", not missing, missing)
    if missing:
        return {"status": "FAIL", "checks": checks}

    meta_base, meta_head = load(files["meta_base"]), load(files["meta_head"])
    need("identity/base_sha", meta_base.get("sha") == endpoints["base_sha"], meta_base.get("sha"))
    need("identity/base_tree", meta_base.get("tree") == endpoints["base_tree"], meta_base.get("tree"))
    need("identity/head_sha", meta_head.get("sha") == endpoints["head_sha"], meta_head.get("sha"))
    need("identity/head_tree", meta_head.get("tree") == endpoints["head_tree"], meta_head.get("tree"))

    base = parse_junit(files["base"])
    head_common = parse_junit(files["head_common"])
    head_only = parse_junit(files["head_only"])

    common = sorted(set(base) & set(head_common))
    base_only = sorted(set(base) - set(head_common))
    head_only_common = sorted(set(head_common) - set(base))

    need("population/base_nonzero", len(base) >= floor, f"{len(base)} < floor {floor}")
    need("population/head_common_nonzero", len(head_common) >= floor, len(head_common))
    need("population/common_nonzero", len(common) >= floor, f"{len(common)} < floor {floor}")
    need("population/base_only_empty", base_only == [], base_only[:5])

    base_bad = sorted(k for k, v in base.items() if v in ("fail", "error"))
    need("base/no_failures", base_bad == [], base_bad[:5])

    regressions = sorted(k for k in common
                         if base[k] == "pass" and head_common[k] not in EXPECTED_STATUS)
    need("common/no_regressions", regressions == [], regressions[:5])
    new_skips = sorted(k for k in common if base[k] == "pass" and head_common[k] == "skip")
    need("common/no_new_skips", new_skips == [], new_skips[:5])
    vanished = sorted(set(common) ^ (set(base) & set(head_common)))
    need("common/no_disappearance", vanished == [], vanished[:5])

    head_only_bad = sorted(k for k, v in head_only.items() if v != "pass")
    need("head_only/count", len(head_only) == expected_head_only, len(head_only))
    need("head_only/all_green", head_only_bad == [], head_only_bad[:5])
    need("head_only/disjoint", not (set(head_only) & set(head_common)), "overlap")

    verdict = "PASS" if all(c["ok"] for c in checks) else "FAIL"
    return {
        "status": verdict,
        "contract": contract_path.as_posix(),
        "endpoints": {"base_sha": endpoints["base_sha"], "base_tree": endpoints["base_tree"],
                      "head_sha": endpoints["head_sha"], "head_tree": endpoints["head_tree"]},
        "population": {
            "common_floor": floor,
            "base_total": len(base),
            "head_common_total": len(head_common),
            "common_total": len(common),
            "base_only": base_only[:20],
            "head_only_common": head_only_common[:20],
            "head_only_total": len(head_only),
            "head_only_expected": expected_head_only,
        },
        "common_status": {
            "pass": sum(1 for k in common if head_common[k] == "pass"),
            "skip": sum(1 for k in common if head_common[k] == "skip"),
            "fail": sum(1 for k in common if head_common[k] == "fail"),
            "error": sum(1 for k in common if head_common[k] == "error"),
        },
        "checks": checks,
        "failures": [c for c in checks if not c["ok"]],
        "authorizes_publication": False,
        "authorizes_next_stage": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts", required=True)
    ap.add_argument("--contract", required=True)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    try:
        result = compare(pathlib.Path(args.artifacts), pathlib.Path(args.contract))
    except (OSError, ValueError, ET.ParseError) as exc:
        result = {"status": "FAIL", "checks": [], "failures": [{"check": "evidence/parsable",
                                                                "detail": str(exc)}]}
    text = canonical(result)
    if args.json:
        pathlib.Path(args.json).write_bytes(text)
    sys.stdout.write(text.decode("utf-8"))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
