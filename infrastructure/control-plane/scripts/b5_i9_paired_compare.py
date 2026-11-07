"""B5-I9 post-merge paired comparison: independent base-versus-head verdict.

Two modes:

* ``--verify-manifest <repo-root> --json <out>`` re-hashes the committed B5-I9 packet with a
  path that never imports the generator.
* ``--artifacts <dir> --contract <path>`` parses the two endpoints' JUnit and collection
  evidence and decides the paired verdict, writing ``paired-comparison-report.json``.

Standard library only; read-only over the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import xml.etree.ElementTree as ET


def status_of(case: ET.Element) -> str:
    for child in case:
        if child.tag == "failure":
            return "FAIL"
        if child.tag == "error":
            return "ERROR"
        if child.tag == "skipped":
            return "SKIP"
    return "PASS"


def parse_junit(path: pathlib.Path):
    root = ET.parse(path).getroot()
    nodes: dict[str, str] = {}
    duplicates: list[str] = []
    for case in root.iter("testcase"):
        key = "{}::{}".format(case.get("classname", ""), case.get("name", ""))
        if key in nodes:
            duplicates.append(key)
        nodes[key] = status_of(case)
    totals = {name: 0 for name in ("tests", "failures", "errors", "skipped")}
    for suite in root.iter("testsuite"):
        for name in totals:
            totals[name] += int(suite.get(name) or 0)
    if totals["tests"] == 0:
        totals["tests"] = len(nodes)
    return nodes, duplicates, totals


def collected_count(path: pathlib.Path) -> int:
    if not path.exists():
        return -1
    return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
               if "::" in line and line.strip().startswith("infrastructure/"))


def counts(nodes: dict[str, str]) -> dict[str, int]:
    out = {name: 0 for name in ("PASS", "FAIL", "ERROR", "SKIP")}
    for status in nodes.values():
        out[status] += 1
    return out


def verify_manifest(root: pathlib.Path) -> dict:
    packet = root / "infrastructure/control-plane/evidence/b5-i9"
    manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
    problems = []
    rows = manifest["artifacts"]
    for row in rows:
        body = (packet / row["path"]).read_bytes().replace(b"\r\n", b"\n")
        digest = hashlib.sha256(body).hexdigest()
        if digest != row["sha256"] or len(body) != row["size_bytes"]:
            problems.append(row["path"])
    on_disk = sorted(p.name for p in packet.iterdir() if p.is_file())
    accounted = sorted(row["path"] for row in rows) + ["manifest.json"]
    doc = {
        "artifact_count": manifest["artifact_count"],
        "rows": len(rows),
        "files_on_disk": len(on_disk),
        "hash_or_size_mismatches": problems,
        "unaccounted_files": sorted(set(on_disk) - set(accounted)),
        "missing_files": sorted(set(accounted) - set(on_disk)),
        "ok": not problems
              and manifest["artifact_count"] == len(rows)
              and not (set(on_disk) - set(accounted))
              and not (set(accounted) - set(on_disk)),
    }
    return doc


def compare(art: pathlib.Path, contract: pathlib.Path) -> int:
    spec = json.loads(contract.read_text(encoding="utf-8"))
    pop = spec["population"]
    art.mkdir(parents=True, exist_ok=True)
    reasons: list[str] = []

    base_nodes, base_dupes, base_totals = parse_junit(art / "junit-base.xml")
    head_nodes, head_dupes, head_totals = parse_junit(art / "junit-head.xml")
    base_collected = collected_count(art / "collect-base.txt")
    head_collected = collected_count(art / "collect-head.txt")

    common = sorted(set(base_nodes) & set(head_nodes))
    only_base = sorted(set(base_nodes) - set(head_nodes))
    only_head = sorted(set(head_nodes) - set(base_nodes))
    transitions = {key: [base_nodes[key], head_nodes[key]] for key in common
                   if base_nodes[key] != head_nodes[key]}

    if base_dupes or head_dupes:
        reasons.append("duplicate node ids: base={} head={}".format(base_dupes, head_dupes))
    if base_collected != base_totals["tests"]:
        reasons.append("base collection/execution mismatch: {} vs {}".format(
            base_collected, base_totals["tests"]))
    if head_collected != head_totals["tests"]:
        reasons.append("head collection/execution mismatch: {} vs {}".format(
            head_collected, head_totals["tests"]))
    if not common:
        reasons.append("common population is zero")
    if len(common) < int(pop["common_floor"]):
        reasons.append("common population {} below floor {}".format(
            len(common), pop["common_floor"]))
    if only_base:
        reasons.append("base-only nodes disappeared: {}".format(len(only_base)))
    if len(only_head) != int(pop["head_only_expected"]):
        reasons.append("head-only count {} != {}".format(
            len(only_head), pop["head_only_expected"]))
    stray = [key for key in only_head if pop["head_only_prefix"] not in key]
    if stray:
        reasons.append("head-only nodes outside the B5-I9 prefix: {}".format(stray[:5]))
    regressions = {key: value for key, value in transitions.items() if value[1] != "PASS"}
    if regressions:
        reasons.append("common-node regressions: {}".format(len(regressions)))
    if head_totals["failures"] or head_totals["errors"]:
        reasons.append("head failures/errors present")
    if head_totals["skipped"]:
        reasons.append("head skipped count is {}".format(head_totals["skipped"]))
    if counts(head_nodes).get("FAIL") or counts(head_nodes).get("ERROR"):
        reasons.append("head node-level FAIL/ERROR present")

    proofs = {}
    for name, filename, predicate in (
        ("validator", "validator.json", lambda d: d.get("status") == "PASS"
         and int(d.get("failures", -1)) == 0),
        ("mutations", "mutations.json", lambda d: d.get("verdict") == "PASS"
         and int(d.get("discriminated", -1)) == 10
         and int(d.get("applied", -1)) == 10
         and bool(d.get("restored_byte_exact")) and bool(d.get("pristine_green"))),
        ("determinism", "determinism.json", lambda d: bool(d.get("identical"))),
        ("manifest", "manifest-check.json", lambda d: bool(d.get("ok"))),
    ):
        path = art / filename
        if not path.exists():
            proofs[name] = {"present": False, "ok": False}
            reasons.append("missing proof evidence: " + filename)
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        ok = bool(predicate(doc))
        proofs[name] = {"present": True, "ok": ok}
        if not ok:
            reasons.append("proof failed: " + name)

    cleanup = {}
    cleanup_path = art / "cleanup.json"
    if cleanup_path.exists():
        cleanup = json.loads(cleanup_path.read_text(encoding="utf-8"))
        if not cleanup.get("cleanup_ok"):
            reasons.append("cleanup not proven")
    else:
        reasons.append("missing cleanup record")

    report = {
        "document_id": "OCE-B5-I9-PAIRED-COMPARISON-REPORT-001",
        "base_sha": spec["endpoints"]["base_sha"],
        "head_sha": spec["endpoints"]["head_sha"],
        "base": {"nodes": len(base_nodes), "collected": base_collected,
                 "totals": base_totals, "status": counts(base_nodes)},
        "head": {"nodes": len(head_nodes), "collected": head_collected,
                 "totals": head_totals, "status": counts(head_nodes)},
        "common_nodes": len(common),
        "common_floor": int(pop["common_floor"]),
        "only_base": only_base,
        "only_head": only_head,
        "head_only_count": len(only_head),
        "duplicates": {"base": base_dupes, "head": head_dupes},
        "status_transitions": transitions,
        "regressions": regressions,
        "proofs": proofs,
        "cleanup": cleanup,
        "reasons": reasons,
        "verdict": "PASS" if not reasons else "FAIL",
    }
    (art / "paired-comparison-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in
                      ("verdict", "common_nodes", "only_base", "head_only_count",
                       "reasons")}, indent=2, sort_keys=True))
    return 0 if report["verdict"] == "PASS" else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts")
    parser.add_argument("--contract")
    parser.add_argument("--verify-manifest")
    parser.add_argument("--json")
    args = parser.parse_args(argv)
    if args.verify_manifest:
        doc = verify_manifest(pathlib.Path(args.verify_manifest))
        text = json.dumps(doc, indent=2, sort_keys=True) + "\n"
        if args.json:
            pathlib.Path(args.json).write_text(text, encoding="utf-8")
        print(text)
        return 0 if doc["ok"] else 1
    if not args.artifacts or not args.contract:
        parser.error("--artifacts and --contract are required for a comparison")
    return compare(pathlib.Path(args.artifacts), pathlib.Path(args.contract))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
