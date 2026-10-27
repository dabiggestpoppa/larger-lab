"""B5-I6 X1 paired full-regression comparator (fail-closed, raw-evidence only).

AUTHORIZED_STAGE=B5-I6-POST-MERGE-CLOSURE-X1-AUTHORITATIVE-EXECUTION.

Consumes the artifact directory produced by
``.github/workflows/b5-i6-post-merge-paired-comparison-x1.yml`` and derives
EVERY verdict from raw evidence (JUnit XML, collect registries, shared-runner
evidence directory, mutation-battery outputs, cleanup record). Summary fields
written by earlier steps are cross-checked, never trusted alone.

Surfaces reported separately (mission section 5):
  A. shared authoritative regression runner at BOTH immutable SHAs;
  B. adjacent B5-I2..B5-I5 suites at BOTH SHAs (raw node registries);
  C. B5-I6 head-only suite (absent at base; exactly 27 nodes at head).

Comparison law (mission section 7): fails closed unless BOTH revisions ran
the authoritative surface, the common population meets the governed floor
(>0 and >= MIN_COMMON_PYTEST_NODES), every common node is compared by full
node ID, no unexplained failure/error/skip regression, no silent common-node
disappearance, exactly the 27 expected B5-I6 nodes are head-only, duplicate
node IDs = 0, orphan files = 0, cleanup passes, every artifact structurally
valid, and SHA/tree identity is exact.

Also independently recomputes the seven-row evidence manifest (sha256 +
size from raw bytes) and validates the 11-row mutation battery.

Usage:
    python infrastructure/control-plane/scripts/b5_x1_compare.py ARTIFACT_DIR

Exit codes: 0 = PAIRED_COMPARISON_X1_OK (no problems); 1 = FAIL (problems
listed in the report and printed).
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Frozen identities (must match the workflow env and the v1.1 contract)
# ---------------------------------------------------------------------------

BASE_SHA = "6e10a326f0eb70affca8f1f627481a52d7062aac"
BASE_TREE = "6683530158d674407bba4ce3b05943b12eeab19a"
HEAD_SHA = "335862bc4059ac0e0074d724bec8f630dfd3b79c"
HEAD_TREE = "3a11bfb8caee6a2a51275ae0cf8a3069967c45d3"

SHARED_REGISTRY_FILE = "infrastructure/cloud-ground/tests/test_regression.py"
SHARED_EXPECTED = {"registered": 67, "static_total": 35, "adversarial_total": 49}

SUITES = {
    "b5i2": {"files": ["infrastructure/control-plane/tests/test_console_contracts.py"],
             "floor": 24, "glob": None},
    "b5i3": {"files": ["infrastructure/control-plane/tests/test_b5_i3_requirement_registry.py"],
             "floor": 51, "glob": "test_b5_i3_*.py"},
    "b5i4": {"files": ["infrastructure/control-plane/tests/test_b5_i4_console_kernel.py"],
             "floor": 23, "glob": "test_b5_i4_*.py"},
    "b5i5": {"files": ["infrastructure/control-plane/tests/test_b5_i5_timeline.py"],
             "floor": 45, "glob": "test_b5_i5_*.py"},
}
B5I6_FILES = [
    "infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py",
    "infrastructure/control-plane/tests/test_b5_i6_console_restart.py",
    "infrastructure/control-plane/tests/test_b5_i6_fail_closed.py",
    "infrastructure/control-plane/tests/test_b5_i6_deploy_pkg.py",
]
B5I6_FLOOR = 23
B5I6_EXPECTED = 27
MIN_COMMON_PYTEST_NODES = 100  # contract v1.1 minimum_required_common_node_population

REQUIRED_EXIT_FILES = (
    ["exit-shared-base.txt", "exit-shared-head.txt",
     "exit-b5i6-absent-base.txt", "exit-b5i6-head.txt", "exit-mutation.txt",
     "exit-cleanup.txt"]
    + [f"exit-{s}-{r}.txt" for s in SUITES for r in ("base", "head")]
)

RANK = {"PASS": 0, "SKIP": 1, "ERROR": 2, "FAIL": 3, "MISSING": 4}


class Problems(list):
    def add(self, msg: str) -> None:
        self.append(msg)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_collect(path: Path, files: list[str]) -> tuple[list[str], int | None, list[str]]:
    """Return (node_ids, declared_count, problems)."""
    probs: list[str] = []
    if not path.is_file():
        return [], None, [f"collect file missing: {path.name}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    nodes: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        for tf in files:
            if tf + "::" in line:
                nodes.append(line[line.index(tf):])
                break
    m = re.search(r"^(\d+) tests? collected", text, re.M)
    declared = int(m.group(1)) if m else None
    if declared is None:
        probs.append(f"{path.name}: collection summary missing")
    elif declared != len(nodes):
        probs.append(f"{path.name}: declared {declared} != parsed {len(nodes)}")
    dupes = sorted({n for n in nodes if nodes.count(n) > 1})
    if dupes:
        probs.append(f"{path.name}: duplicate node ids {dupes}")
    return nodes, declared, probs


def junit_key_to_node_map(nodes: list[str]) -> dict[tuple[str, str], str]:
    """(dotted_classname, method) -> full node id, derived from collect nodes."""
    out: dict[tuple[str, str], str] = {}
    for node in nodes:
        parts = node.split("::")
        if len(parts) != 3:
            continue
        path, cls, meth = parts
        classname = path[:-3].replace("/", ".") + "." + cls
        out[(classname, meth)] = node
    return out


def parse_junit(path: Path, collect_nodes: list[str]) -> dict[str, Any]:
    """Totals + per-node status/skip-reason + structural problems."""
    probs: list[str] = []
    result: dict[str, Any] = {
        "totals": {"tests": 0, "failures": 0, "errors": 0, "skipped": 0},
        "status": {}, "skip_reasons": {}, "problems": probs,
    }
    if not path.is_file():
        probs.append(f"junit missing: {path.name}")
        return result
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        probs.append(f"{path.name}: junit parse error: {exc}")
        return result
    suites = list(root.iter("testsuite"))
    result["totals"] = {k: sum(int(s.get(k) or 0) for s in suites)
                        for k in ("tests", "failures", "errors", "skipped")}
    key_map = junit_key_to_node_map(collect_nodes)
    cases = list(root.iter("testcase"))
    seen: set[tuple[str, str]] = set()
    for case in cases:
        key = (case.get("classname", ""), case.get("name", ""))
        if key in seen:
            probs.append(f"{path.name}: duplicate testcase {key}")
        seen.add(key)
        node = key_map.get(key)
        if node is None:
            probs.append(f"{path.name}: junit testcase outside collect registry: {key}")
            continue
        status = "PASS"
        reason = ""
        for child in case:
            if child.tag == "failure":
                status = "FAIL"
            elif child.tag == "error":
                status = "ERROR"
            elif child.tag == "skipped":
                status = "SKIP"
                reason = child.get("message", "") or (child.text or "").strip()
        result["status"][node] = status
        if status == "SKIP":
            result["skip_reasons"][node] = reason
    missing = [n for n in collect_nodes if n not in result["status"]]
    if missing:
        probs.append(f"{path.name}: collected nodes without junit case: {missing}")
    if result["totals"]["tests"] != len(cases):
        probs.append(f"{path.name}: suite totals != testcase count")
    if result["totals"]["tests"] != len(collect_nodes):
        probs.append(f"{path.name}: junit tests {result['totals']['tests']} "
                     f"!= collected {len(collect_nodes)}")
    return result


def registry_deltas(base: set[str], head: set[str],
                    base_status: dict[str, str], head_status: dict[str, str],
                    base_skips: dict[str, str], head_skips: dict[str, str]) -> dict[str, Any]:
    common = sorted(base & head)
    only_base = sorted(base - head)
    only_head = sorted(head - base)
    status_changes, regressions, skip_changes = [], [], []
    for node in common:
        b, h = base_status.get(node, "MISSING"), head_status.get(node, "MISSING")
        if b != h:
            status_changes.append({"node": node, "base": b, "head": h})
            if RANK.get(h, 4) > RANK.get(b, 3):
                regressions.append({"node": node, "base": b, "head": h})
        bs, hs = base_skips.get(node), head_skips.get(node)
        if bs != hs:
            skip_changes.append({"node": node, "base": bs, "head": hs})
    return {
        "common": common, "only_base": only_base, "only_head": only_head,
        "status_changes": status_changes, "regressions": regressions,
        "skip_changes": skip_changes,
        "unexplained_removals": only_base,
    }


# ---------------------------------------------------------------------------
# Shared runner surface (A)
# ---------------------------------------------------------------------------

def parse_shared(art: Path, role: str, expect_sha: str, expect_tree: str,
                 probs: Problems) -> dict[str, Any]:
    base = art / "shared" / role
    ev = base / "evidence"
    out: dict[str, Any] = {"role": role}
    if not ev.is_dir():
        probs.add(f"shared/{role}: evidence directory missing")
        return out

    # registry (display \t fn) exported by the workflow from the SHA's own tree
    reg_path = art / f"registry-shared-{role}.txt"
    registry: dict[str, str] = {}
    if not reg_path.is_file():
        probs.add(f"registry-shared-{role}.txt missing")
    else:
        for line in reg_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) != 2:
                probs.add(f"registry-shared-{role}: malformed line {line!r}")
                continue
            display, fn = parts
            if display in registry or fn in set(registry.values()):
                probs.add(f"registry-shared-{role}: duplicate registry entry {display}")
            registry[display] = fn
    nodes = sorted(SHARED_REGISTRY_FILE + "::" + fn for fn in registry.values())
    node_by_display = {d: SHARED_REGISTRY_FILE + "::" + f for d, f in registry.items()}
    out["nodes"] = nodes
    out["registered"] = len(nodes)
    if len(nodes) != SHARED_EXPECTED["registered"]:
        probs.add(f"shared/{role}: registered {len(nodes)} != "
                  f"{SHARED_EXPECTED['registered']} (contract)")

    # statuses from the runner's own regression output
    status: dict[str, str] = {}
    regr = ev / "regression-output.txt"
    totals = {"total": None, "pass": None, "fail": None}
    if not regr.is_file():
        probs.add(f"shared/{role}: regression-output.txt missing")
    else:
        text = regr.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            if line.startswith("PASS: ") and line[6:].strip():
                disp = line[6:].strip()
                if disp in status:
                    probs.add(f"shared/{role}: duplicate PASS line for {disp!r}")
                status[disp] = "PASS"
            elif line.startswith("FAIL: "):
                disp = line[6:].split(":")[0].strip()
                status[disp] = "FAIL"
        m_t = re.search(r"^\s+Total:\s+(\d+)", text, re.M)
        m_p = re.search(r"^\s+PASS:\s+(\d+)", text, re.M)
        m_f = re.search(r"^\s+FAIL:\s+(\d+)", text, re.M)
        totals = {"total": int(m_t.group(1)) if m_t else None,
                  "pass": int(m_p.group(1)) if m_p else None,
                  "fail": int(m_f.group(1)) if m_f else None}
        if None in totals.values():
            probs.add(f"shared/{role}: regression summary block unparsable")
    unaccounted = [d for d in registry if d not in status]
    if unaccounted:
        probs.add(f"shared/{role}: registry displays without status: {unaccounted[:5]}")
    node_status = {node_by_display[d]: s for d, s in status.items()
                   if d in node_by_display}
    out["totals"] = totals
    out["status"] = node_status
    out["skip_reasons"] = {}
    out["collected"] = len(nodes)
    out["executed"] = (totals["pass"] or 0) + (totals["fail"] or 0)
    out["passed"] = totals["pass"]
    out["failed"] = totals["fail"]
    out["errors"] = 0
    out["skipped"] = 0
    out["duplicate_full_node_ids"] = len(nodes) - len(set(nodes))
    out["orphan_files"] = 0
    out["orphan_nodes"] = len(unaccounted)
    if None in totals.values() or totals["total"] != len(nodes) \
            or totals["pass"] != len(nodes) or totals["fail"] != 0:
        probs.add(f"shared/{role}: regression totals not green/consistent: {totals}")

    # static / adversarial / gate / identity / cleanup from evidence
    try:
        static = read_json(ev / "static-validation-results.json")
        st = static.get("totals", {})
        out["static"] = {"totals": st, "tested_commit": static.get("tested_commit"),
                         "tested_tree": static.get("tested_tree"),
                         "gate": static.get("gate")}
        if st.get("PASS") != SHARED_EXPECTED["static_total"] or st.get("FAIL") != 0:
            probs.add(f"shared/{role}: static totals {st} != 35/0 (contract)")
        if static.get("tested_commit") != expect_sha or static.get("tested_tree") != expect_tree:
            probs.add(f"shared/{role}: static identity {static.get('tested_commit')}/"
                      f"{static.get('tested_tree')} != {expect_sha}/{expect_tree}")
    except Exception as exc:  # noqa: BLE001 - fail-closed on any parse issue
        probs.add(f"shared/{role}: static-validation-results.json unreadable: {exc}")
    try:
        adv = read_json(ev / "adversarial-results.json")
        at = adv.get("totals", {})
        out["adversarial"] = {"totals": at, "suite_result": adv.get("suite_result")}
        if at.get("total") != SHARED_EXPECTED["adversarial_total"] \
                or at.get("PASS") != SHARED_EXPECTED["adversarial_total"] \
                or at.get("FAIL") != 0 or adv.get("suite_result") != "PASS":
            probs.add(f"shared/{role}: adversarial totals/suite {at}/"
                      f"{adv.get('suite_result')} != 49/49 PASS (contract)")
    except Exception as exc:  # noqa: BLE001
        probs.add(f"shared/{role}: adversarial-results.json unreadable: {exc}")
    try:
        stage = read_json(ev / "stage-status.json")
        out["stage"] = {"gate_status": stage.get("gate_status"),
                        "implementation_commit": stage.get("implementation_commit"),
                        "implementation_tree": stage.get("implementation_tree"),
                        "totals": stage.get("totals")}
        if stage.get("gate_status") != "READY_FOR_OPERATOR_REVIEW":
            probs.add(f"shared/{role}: gate_status {stage.get('gate_status')}")
        if stage.get("implementation_commit") != expect_sha:
            probs.add(f"shared/{role}: stage commit {stage.get('implementation_commit')} "
                      f"!= {expect_sha}")
        if stage.get("implementation_tree") != expect_tree:
            probs.add(f"shared/{role}: stage tree {stage.get('implementation_tree')} "
                      f"!= {expect_tree}")
    except Exception as exc:  # noqa: BLE001
        probs.add(f"shared/{role}: stage-status.json unreadable: {exc}")
    try:
        cleanup = read_json(ev / "worktree-cleanup.json")
        out["runner_worktree_cleanup"] = cleanup
        if not (cleanup.get("removed") is True and cleanup.get("pruned") is True):
            probs.add(f"shared/{role}: runner worktree cleanup {cleanup}")
    except Exception as exc:  # noqa: BLE001
        probs.add(f"shared/{role}: worktree-cleanup.json unreadable: {exc}")
    log = base / "runner.log"
    out["runner_log_bytes"] = log.stat().st_size if log.is_file() else None
    if not log.is_file():
        probs.add(f"shared/{role}: runner.log missing")
    return out


# ---------------------------------------------------------------------------
# Manifest (8) — seven-row independent recomputation from raw bytes
# ---------------------------------------------------------------------------

def verify_manifest(art: Path, expect_sha: str, expect_tree: str,
                    probs: Problems) -> dict[str, Any]:
    ev = art / "shared" / "head" / "evidence"
    out: dict[str, Any] = {
        "tested_sha": expect_sha, "tested_tree": expect_tree,
        "source": "shared/head/evidence/evidence-manifest.json",
        "rows": [], "matched": 0, "total": 0,
        "verdict": "FAIL", "verifier_exit_code": 1,
    }
    man_path = ev / "evidence-manifest.json"
    if not man_path.is_file():
        probs.add("manifest: evidence-manifest.json missing at head")
        _write_json(art / "b5-x1-manifest-verify.json", out)
        return out
    try:
        man = read_json(man_path)
    except Exception as exc:  # noqa: BLE001
        probs.add(f"manifest: unparsable: {exc}")
        _write_json(art / "b5-x1-manifest-verify.json", out)
        return out
    if man.get("schema_version") != "3.6.0":
        probs.add(f"manifest: schema {man.get('schema_version')} != 3.6.0")
    rows = []
    matched = 0
    for i, entry in enumerate(man.get("artifacts", []), start=1):
        path = entry.get("path", "")
        exp_sha = entry.get("sha256", "")
        exp_size = entry.get("size")
        obs_sha, obs_size, verdict = "", None, "MISSING"
        target = ev / path
        if target.is_file():
            data = target.read_bytes()
            obs_sha = sha256_bytes(data)
            obs_size = len(data)
            verdict = "MATCH" if (obs_sha == exp_sha and obs_size == exp_size) else "MISMATCH"
        if verdict == "MATCH":
            matched += 1
        rows.append({
            "n": i, "artifact_path": path,
            "expected_sha256": exp_sha, "observed_sha256": obs_sha,
            "expected_bytes": exp_size, "observed_bytes": obs_size,
            "verdict": verdict,
        })
    out["rows"] = rows
    out["matched"] = matched
    out["total"] = len(rows)
    ok = len(rows) == 7 and matched == 7
    if not ok:
        probs.add(f"manifest: {matched}/{len(rows)} matched (required exactly 7/7)")
    out["verdict"] = "7/7 MATCH" if ok else f"{matched}/{len(rows)} (FAIL)"
    out["verifier_exit_code"] = 0 if ok else 1
    _write_json(art / "b5-x1-manifest-verify.json", out)
    return out


# ---------------------------------------------------------------------------
# Mutation battery (9) — 11-row table from harness canonical + raw outputs
# ---------------------------------------------------------------------------

def verify_mutation(art: Path, probs: Problems) -> dict[str, Any]:
    out: dict[str, Any] = {"rows": [], "verdict": "FAIL"}
    try:
        canon = read_json(art / "b5-x1-mutation-report.json")
        raw = read_json(art / "b5-x1-mutation-raw.json")
    except Exception as exc:  # noqa: BLE001
        probs.add(f"mutation: harness outputs unreadable: {exc}")
        return out
    raw_by_id = {o["id"]: o for o in raw.get("observations", [])}
    rows = []
    for m in canon.get("mutations", []):
        r = raw_by_id.get(m["id"], {})
        rows.append({
            "mutation": m["id"],
            "weakened_invariant": m["description"],
            "target": m["target"],
            "expected_discriminating_test": m["expected_discriminator"],
            "observed_failing_nodes": r.get("observed_failures", []),
            "mutation_returncode": r.get("returncode"),
            "pristine_sha256": m.get("pristine_sha256"),
            "restored_sha256": m.get("restored_sha256"),
            "restore_verified": m.get("restore_verified"),
            "outcome": m.get("outcome"),
        })
    out["rows"] = rows
    out["schema"] = canon.get("schema")
    out["harness_sha256"] = canon.get("implementation", {}).get("harness_sha256")
    out["baseline"] = canon.get("baseline", {})
    out["mutation_count"] = canon.get("mutation_count")
    out["discriminated_count"] = canon.get("discriminated_count")
    ok = (
        canon.get("verdict") == "ALL_DISCRIMINATED"
        and canon.get("mutation_count") == 11
        and canon.get("discriminated_count") == 11
        and canon.get("unresolved_mutations") == 0
        and canon.get("skipped_mutations") == 0
        and canon.get("baseline", {}).get("control_green") is True
        and canon.get("baseline", {}).get("restore_control_green") is True
        and canon.get("baseline", {}).get("collected") == B5I6_EXPECTED
        and canon.get("caller_tracked_worktree_unmodified") is True
        and len(rows) == 11
        and all(r["outcome"] == "DISCRIMINATED" and r["restore_verified"] is True
                and r["mutation_returncode"] not in (None, 0)
                and r["observed_failing_nodes"] for r in rows)
        and raw.get("target_head") == HEAD_SHA
        and raw.get("target_tree") == HEAD_TREE
    )
    if not ok:
        probs.add("mutation: battery did not satisfy 11/11 + controls + restore + "
                  "exact-head requirements")
    out["verdict"] = "11/11 DISCRIMINATED, controls green, restores verified" \
        if ok else "FAIL"
    return out


# ---------------------------------------------------------------------------
# Cleanup (10)
# ---------------------------------------------------------------------------

def verify_cleanup(art: Path, probs: Problems) -> dict[str, Any]:
    out: dict[str, Any] = {"verdict": "FAIL"}
    path = art / "b5-x1-cleanup-record.json"
    if not path.is_file():
        probs.add("cleanup: b5-x1-cleanup-record.json missing")
        return out
    try:
        rec = read_json(path)
    except Exception as exc:  # noqa: BLE001
        probs.add(f"cleanup: unparsable: {exc}")
        return out
    out = rec
    residuals = rec.get("residual_resources", [])
    ok = (
        rec.get("cleanup_exit_code") == 0
        and residuals == []
        and rec.get("temp_checkouts_removed") is True
        and rec.get("containers_created") == []
        and rec.get("volumes_created") == []
        and rec.get("database_runtime_paths") == []
        and rec.get("pip_cache_purged") is True
    )
    if not ok:
        probs.add(f"cleanup: record does not prove clean state: exit="
                  f"{rec.get('cleanup_exit_code')} residuals={residuals}")
    rec = dict(rec)
    rec["verdict"] = "PASS" if ok else "FAIL"
    return rec


def _write_json(path: Path, doc: Any) -> None:
    path.write_text(json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
                    encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: b5_x1_compare.py ARTIFACT_DIR", file=sys.stderr)
        return 1
    art = Path(argv[1])
    probs = Problems()
    report: dict[str, Any] = {
        "schema": "oce.b5-i6.x1-paired-comparison",
        "schema_version": "1.0.0",
        "contract": "docs/oce-golden-system/"
                    "OCE_B5_I6_POST_MERGE_PAIRED_COMPARISON_CONTRACT_v1.1.json",
        "base": {"sha": BASE_SHA, "tree": BASE_TREE},
        "head": {"sha": HEAD_SHA, "tree": HEAD_TREE},
    }

    # ---- environment + meta identity -------------------------------------
    meta: dict[str, Any] = {}
    for role, sha, tree in (("base", BASE_SHA, BASE_TREE),
                            ("head", HEAD_SHA, HEAD_TREE)):
        path = art / f"meta-{role}.json"
        if not path.is_file():
            probs.add(f"meta-{role}.json missing")
            continue
        m = read_json(path)
        meta[role] = m
        if m.get("sha") != sha:
            probs.add(f"meta-{role}: sha {m.get('sha')} != pinned {sha}")
        if m.get("tree") != tree:
            probs.add(f"meta-{role}: tree {m.get('tree')} != pinned {tree}")
        if m.get("identity_verified") is not True:
            probs.add(f"meta-{role}: post-checkout identity verification not recorded")
    if meta.get("base") and meta.get("head"):
        for key in ("python_version", "runner_image", "pip_freeze_sha256"):
            if meta["base"].get(key) != meta["head"].get(key):
                probs.add(f"environment differs across roles for {key}: "
                          f"{meta['base'].get(key)} vs {meta['head'].get(key)}")
    report["environment"] = {
        "base": meta.get("base", {}), "head": meta.get("head", {})}

    # ---- every required exit code ----------------------------------------
    exit_codes: dict[str, int] = {}
    for name in REQUIRED_EXIT_FILES:
        path = art / name
        if not path.is_file():
            probs.add(f"exit code file missing: {name}")
            continue
        try:
            rc = int(path.read_text(encoding="utf-8").strip())
        except ValueError:
            probs.add(f"exit code file unparsable: {name}")
            continue
        exit_codes[name] = rc
        if rc != 0:
            probs.add(f"nonzero exit captured: {name} = {rc}")
    report["exit_codes"] = exit_codes

    # ---- surface A: shared runner ----------------------------------------
    shared_base = parse_shared(art, "base", BASE_SHA, BASE_TREE, probs)
    shared_head = parse_shared(art, "head", HEAD_SHA, HEAD_TREE, probs)
    sb_nodes = set(shared_base.get("nodes", []))
    sh_nodes = set(shared_head.get("nodes", []))
    shared_delta = registry_deltas(
        sb_nodes, sh_nodes,
        shared_base.get("status", {}), shared_head.get("status", {}),
        shared_base.get("skip_reasons", {}), shared_head.get("skip_reasons", {}))
    if shared_delta["only_head"]:
        probs.add(f"shared runner: head-only registry nodes: "
                  f"{shared_delta['only_head'][:5]}")
    if shared_delta["regressions"]:
        probs.add(f"shared runner: regressions: "
                  f"{[r['node'] for r in shared_delta['regressions']][:5]}")
    if len(shared_delta["common"]) != SHARED_EXPECTED["registered"]:
        probs.add(f"shared runner: common {len(shared_delta['common'])} != "
                  f"{SHARED_EXPECTED['registered']}")
    report["section_a_shared_runner"] = {
        "base": {k: shared_base.get(k) for k in
                 ("collected", "executed", "passed", "failed", "errors", "skipped",
                  "duplicate_full_node_ids", "orphan_files", "orphan_nodes",
                  "totals", "static", "adversarial", "stage",
                  "runner_worktree_cleanup", "runner_log_bytes")},
        "head": {k: shared_head.get(k) for k in
                 ("collected", "executed", "passed", "failed", "errors", "skipped",
                  "duplicate_full_node_ids", "orphan_files", "orphan_nodes",
                  "totals", "static", "adversarial", "stage",
                  "runner_worktree_cleanup", "runner_log_bytes")},
        "common_full_node_ids": shared_delta["common"],
        "base_only": shared_delta["only_base"],
        "head_only": shared_delta["only_head"],
        "status_changes": shared_delta["status_changes"],
        "skip_reason_changes": shared_delta["skip_changes"],
        "unexplained_removals": shared_delta["unexplained_removals"],
        "regression_verdict": "NO_REGRESSION"
        if not (shared_delta["regressions"] or shared_delta["only_base"]
                or shared_delta["only_head"]) else "REGRESSION",
    }

    # ---- surface B: adjacent suites --------------------------------------
    adjacent: dict[str, Any] = {}
    common_total = 0
    all_regressions: list[dict[str, Any]] = []
    for suite, spec in SUITES.items():
        entry: dict[str, Any] = {"files": spec["files"], "floor": spec["floor"]}
        nodes_by_role: dict[str, list[str]] = {}
        status_by_role: dict[str, dict[str, str]] = {}
        skips_by_role: dict[str, dict[str, str]] = {}
        for role in ("base", "head"):
            files_existing = [f for f in spec["files"]]
            nodes, declared, cprobs = parse_collect(
                art / f"collect-{suite}-{role}.txt", files_existing)
            for p in cprobs:
                probs.add(f"{suite}/{role}: {p}")
            if len(nodes) < spec["floor"]:
                probs.add(f"{suite}/{role}: collected {len(nodes)} < floor "
                          f"{spec['floor']}")
            junit = parse_junit(art / f"junit-{suite}-{role}.xml", nodes)
            for p in junit["problems"]:
                probs.add(f"{suite}/{role}: {p}")
            t = junit["totals"]
            if t["failures"] or t["errors"] or t["skipped"]:
                probs.add(f"{suite}/{role}: junit totals {t} not 0/0/0")
            nodes_by_role[role] = nodes
            status_by_role[role] = junit["status"]
            skips_by_role[role] = junit["skip_reasons"]
            entry[role] = {"collected": len(nodes), "declared": declared,
                           "executed": t["tests"],
                           "passed": (t["tests"] - t["failures"]
                                     - t["errors"] - t["skipped"]),
                           "failed": t["failures"], "errors": t["errors"],
                           "skipped": t["skipped"]}
        delta = registry_deltas(set(nodes_by_role["base"]), set(nodes_by_role["head"]),
                                status_by_role["base"], status_by_role["head"],
                                skips_by_role["base"], skips_by_role["head"])
        if delta["only_base"] or delta["only_head"]:
            probs.add(f"{suite}: adjacent registry differs across SHAs "
                      f"(base-only={len(delta['only_base'])}, "
                      f"head-only={len(delta['only_head'])}) — adjacent suites "
                      f"must be unchanged")
        if delta["regressions"]:
            probs.add(f"{suite}: regressions {[r['node'] for r in delta['regressions']]}")
        common_total += len(delta["common"])
        all_regressions.extend(delta["regressions"])
        entry.update({
            "common": len(delta["common"]),
            "base_only": len(delta["only_base"]),
            "head_only": len(delta["only_head"]),
            "regressions": delta["regressions"],
            "status_changes": delta["status_changes"],
            "skip_reason_changes": delta["skip_changes"],
            "common_nodes": delta["common"],
        })
        # orphan-file detection from the SHA's own tree (recorded by workflow)
        for role in ("base", "head"):
            meta_role = meta.get(role, {})
            glob_files = meta_role.get("suite_globs", {}).get(suite)
            if glob_files is None:
                probs.add(f"meta-{role}: suite_globs.{suite} missing")
            elif sorted(glob_files) != sorted(spec["files"]):
                probs.add(f"{suite}/{role}: orphan/missing test files "
                          f"{sorted(glob_files)} != {sorted(spec['files'])}")
        adjacent[suite] = entry
    report["section_b_adjacent_suites"] = {
        "suites": adjacent,
        "common_total": common_total,
        "derived_from_raw_registries": True,
        "min_common_required": MIN_COMMON_PYTEST_NODES,
    }
    if common_total == 0:
        probs.add("common_regression_nodes == 0 (refusal condition)")
    elif common_total < MIN_COMMON_PYTEST_NODES:
        probs.add(f"common pytest population {common_total} below governed floor "
                  f"{MIN_COMMON_PYTEST_NODES}")

    # ---- surface C: B5-I6 head-only --------------------------------------
    b5i6: dict[str, Any] = {"floor": B5I6_FLOOR, "expected": B5I6_EXPECTED}
    base_files_present = meta.get("base", {}).get("b5_i6_files_present")
    if base_files_present is None:
        probs.add("meta-base: b5_i6_files_present missing")
    elif base_files_present != []:
        probs.add(f"B5-I6 files present at base: {base_files_present}")
    b5i6["base_files_present"] = base_files_present
    b5i6["base_absent"] = base_files_present == []
    head_glob = meta.get("head", {}).get("suite_globs", {}).get("b5i6")
    if sorted(head_glob or []) != sorted(B5I6_FILES):
        probs.add(f"b5i6/head: file glob {head_glob} != the four B5-I6 suites")
    b5i6["head_files"] = head_glob
    b5i6["head_file_count"] = len(head_glob or [])
    nodes6, declared6, cprobs6 = parse_collect(art / "collect-b5i6-head.txt", B5I6_FILES)
    for p in cprobs6:
        probs.add(f"b5i6/head: {p}")
    junit6 = parse_junit(art / "junit-b5i6-head.xml", nodes6)
    for p in junit6["problems"]:
        probs.add(f"b5i6/head: {p}")
    t6 = junit6["totals"]
    if len(nodes6) != B5I6_EXPECTED:
        probs.add(f"b5i6/head: collected {len(nodes6)} != {B5I6_EXPECTED}")
    if len(nodes6) < B5I6_FLOOR:
        probs.add(f"b5i6/head: collected {len(nodes6)} < floor {B5I6_FLOOR}")
    if t6 != {"tests": B5I6_EXPECTED, "failures": 0, "errors": 0, "skipped": 0}:
        probs.add(f"b5i6/head: junit totals {t6}")
    dupes6 = len(nodes6) - len(set(nodes6))
    if dupes6:
        probs.add(f"b5i6/head: duplicate node ids {dupes6}")
    b5i6.update({
        "collected": len(nodes6), "declared": declared6, "executed": t6["tests"],
        "passed": t6["tests"] - t6["failures"] - t6["errors"] - t6["skipped"],
        "failed": t6["failures"], "errors": t6["errors"], "skipped": t6["skipped"],
        "duplicate_full_node_ids": dupes6,
        "orphan_files": 0 if sorted(head_glob or []) == sorted(B5I6_FILES) else 1,
        "orphan_nodes": len(nodes6) - len(set(nodes6)),
        "nodes": sorted(nodes6),
    })
    report["section_c_b5_i6_head_only"] = b5i6

    # ---- overall deltas over the pytest population ------------------------
    base_all: set[str] = set()
    head_all: set[str] = set()
    base_status: dict[str, str] = {}
    head_status: dict[str, str] = {}
    base_skips: dict[str, str] = {}
    head_skips: dict[str, str] = {}
    for suite in SUITES:
        # re-parse statuses (kept simple and independent)
        nb, _, _ = parse_collect(art / f"collect-{suite}-base.txt", SUITES[suite]["files"])
        nh, _, _ = parse_collect(art / f"collect-{suite}-head.txt", SUITES[suite]["files"])
        jb = parse_junit(art / f"junit-{suite}-base.xml", nb)
        jh = parse_junit(art / f"junit-{suite}-head.xml", nh)
        base_all.update(nb)
        head_all.update(nh)
        base_status.update(jb["status"])
        head_status.update(jh["status"])
        base_skips.update(jb["skip_reasons"])
        head_skips.update(jh["skip_reasons"])
    head_all.update(nodes6)
    overall = registry_deltas(base_all, head_all, base_status, head_status,
                              base_skips, head_skips)
    expected_head_only = set(nodes6)
    if set(overall["only_head"]) != expected_head_only:
        probs.add("overall: head-only population is not exactly the 27 expected "
                  f"B5-I6 nodes (extra={sorted(set(overall['only_head']) - expected_head_only)[:5]}, "
                  f"missing={sorted(expected_head_only - set(overall['only_head']))[:5]})")
    if overall["only_base"]:
        probs.add(f"overall: unexplained base-only (disappeared) nodes: "
                  f"{overall['only_base'][:5]}")
    if overall["regressions"]:
        probs.add(f"overall: common-node regressions: "
                  f"{[r['node'] for r in overall['regressions']][:5]}")
    if overall["skip_changes"]:
        probs.add(f"overall: skip-reason changes on common nodes: "
                  f"{overall['skip_changes'][:5]}")
    report["deltas"] = {
        "pytest_common": len(overall["common"]),
        "pytest_base_only": overall["only_base"],
        "pytest_head_only_count": len(overall["only_head"]),
        "expected_head_only_count": len(expected_head_only),
        "expected_head_only_identified": sorted(expected_head_only),
        "status_changes": overall["status_changes"],
        "regressions": overall["regressions"],
        "skip_reason_changes": overall["skip_changes"],
        "unexplained_removals": overall["unexplained_removals"],
    }

    # ---- proofs: manifest, mutation, cleanup ------------------------------
    report["manifest_verification"] = verify_manifest(art, HEAD_SHA, HEAD_TREE, probs)
    report["mutation_verification"] = verify_mutation(art, probs)
    report["cleanup_verification"] = verify_cleanup(art, probs)

    # ---- verdict ----------------------------------------------------------
    report["problems"] = probs
    report["verdict"] = "PAIRED_COMPARISON_X1_OK" if not probs \
        else "PAIRED_COMPARISON_X1_FAIL"
    _write_json(art / "b5-x1-comparison-report.json", report)
    print(json.dumps({
        "verdict": report["verdict"],
        "common_pytest": len(overall["common"]),
        "shared_common": len(shared_delta["common"]),
        "head_only": len(overall["only_head"]),
        "manifest": report["manifest_verification"].get("verdict"),
        "mutation": report["mutation_verification"].get("verdict"),
        "cleanup": report["cleanup_verification"].get("verdict"),
        "problems": probs,
    }, indent=2))
    return 0 if not probs else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
