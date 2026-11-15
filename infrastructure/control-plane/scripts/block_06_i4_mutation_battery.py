#!/usr/bin/env python3
"""B6-I4 mutation battery: seventeen governed mutations, source floor 4, stage floor 6.

Each mutation must be applied, discriminate a named node or control, be restored byte-exactly and
leave the pristine tree green. A mutation that is not applied, stays green or cannot restore fails.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

INCIDENT = "oce/operator/incident.py"
COST = "oce/operator/cost.py"
IDENTITY = "oce/services/identity.py"
WORKFLOW = "oce/services/workflow.py"
TRACE = "oce/operator/trace.py"
I3_WORKFLOW = ".github/workflows/block-06-i3-validation.yml"
I4_REGISTRATION = "docs/oce-golden-system/OCE_BLOCK_06_I4_STAGE_SCOPE_REGISTRATION_v1.0.json"
TESTS = "infrastructure/control-plane/tests"
CONTROLS = "infrastructure/control-plane/scripts/block_06_i4_stage_controls.py"
FLOOR = 6

MUTATIONS = [
    {"id": "M01", "label": "severity vocabulary check removed", "file": INCIDENT,
     "old": '        if incident["severity"] not in RANK:', "new": "        if False:",
     "kind": "pytest", "target": f"{TESTS}/test_block_06_i4_incident.py::test_invalid_severity_refused"},
    {"id": "M02", "label": "timeline monotonicity check removed", "file": INCIDENT,
     "old": '        if previous is not None and at < previous:', "new": "        if False:",
     "kind": "pytest", "target": f"{TESTS}/test_block_06_i4_incident.py::test_timeline_must_be_monotonic"},
    {"id": "M03", "label": "cost category check removed", "file": COST,
     "old": '        if entry["category"] not in CATEGORIES:', "new": "        if False:",
     "kind": "pytest", "target": f"{TESTS}/test_block_06_i4_cost.py::test_unknown_category_refused"},
    {"id": "M04", "label": "raw secret refusal removed", "file": IDENTITY,
     "old": '            if str(key).lower() in SECRET_KEYS:', "new": "            if False:",
     "kind": "pytest", "target": f"{TESTS}/test_block_06_i4_identity.py::test_raw_secret_refused"},
    {"id": "M05", "label": "cross-app isolation check removed", "file": IDENTITY,
     "old": '    if identity["app"] != app:', "new": "    if False:",
     "kind": "pytest", "target": f"{TESTS}/test_block_06_i4_identity.py::test_cross_app_isolation_refused"},
    {"id": "M06", "label": "lease owner check removed", "file": WORKFLOW,
     "old": '    if lease is None or lease["owner"] != actor or int(now) >= int(lease["expires_at"]):',
     "new": "    if False:",
     "kind": "pytest", "target": f"{TESTS}/test_block_06_i4_workflow.py::test_lease_owner_required"},
    {"id": "M07", "label": "incident owner binding removed", "file": TRACE,
     "old": '            if node["ref"] not in incident_owners:', "new": "            if False:",
     "kind": "pytest", "target": f"{TESTS}/test_block_06_i4_trace.py::test_trace_requires_incident_owner"},
    {"id": "M08", "label": "duplicate incident refusal removed", "file": TRACE,
     "old": '        if row["id"] in incident_index:', "new": "        if False:",
     "kind": "pytest", "target": f"{TESTS}/test_block_06_i4_trace.py::test_trace_duplicate_incident_refused"},
    {"id": "M09", "label": "definition version binding removed", "file": WORKFLOW,
     "old": ('    if (run["definition_id"] != definition["id"]\n'
             '            or int(run["version"]) != int(definition["version"])):'),
     "new": "    if False:",
     "kind": "pytest",
     "target": f"{TESTS}/test_block_06_i4_workflow.py::test_advance_definition_mismatch_refused"},
    {"id": "M10", "label": "strict integer cost check removed", "file": COST,
     "old": "    if type(value) is not int or value < 0:", "new": "    if value < 0:",
     "kind": "pytest", "target": f"{TESTS}/test_block_06_i4_cost.py::test_fractional_cost_refused"},
    {"id": "M11", "label": "nested mapping secret recursion removed", "file": IDENTITY,
     "old": "            _refuse_raw_secret(nested)", "new": "            pass",
     "kind": "pytest", "target": f"{TESTS}/test_block_06_i4_identity.py::test_nested_map_secret_refused"},
    {"id": "M12", "label": "nested sequence secret recursion removed", "file": IDENTITY,
     "old": "            _refuse_raw_secret(item)", "new": "            pass",
     "kind": "pytest", "target": f"{TESTS}/test_block_06_i4_identity.py::test_nested_sequence_secret_refused"},
    {"id": "M13", "label": "I3 replay head endpoint removed", "file": I3_WORKFLOW,
     "old": ("            eda33f43e6d058891a8009e98e968c9f00252220 \\\n"
             "            018b164f249bbf075334d5d03ad37e80dcbbede0 || true\n"
             "          git checkout --quiet --detach "
             "eda33f43e6d058891a8009e98e968c9f00252220"),
     "new": ("            018b164f249bbf075334d5d03ad37e80dcbbede0 || true\n"
             "          git checkout --quiet --detach "
             "018b164f249bbf075334d5d03ad37e80dcbbede0"),
     "kind": "controls", "target": "i3_workflow_present_frozen"},
    {"id": "M14", "label": "I3 replay base endpoint removed", "file": I3_WORKFLOW,
     "old": ("            018b164f249bbf075334d5d03ad37e80dcbbede0 || true\n"
             "          git checkout --quiet --detach "
             "eda33f43e6d058891a8009e98e968c9f00252220\n"
             "          git update-ref refs/remotes/origin/main "
             "018b164f249bbf075334d5d03ad37e80dcbbede0"),
     "new": ("            eda33f43e6d058891a8009e98e968c9f00252220 || true\n"
             "          git checkout --quiet --detach "
             "eda33f43e6d058891a8009e98e968c9f00252220\n"
             "          git update-ref refs/remotes/origin/main "
             "eda33f43e6d058891a8009e98e968c9f00252220"),
     "kind": "controls", "target": "i3_workflow_present_frozen"},
    {"id": "M16", "label": "run definition_id presence check removed", "file": WORKFLOW,
     "old": ("        if key not in run:\n"
             '            raise OperatorRefusal("REFUSED_INVALID_RECORD", f"run.{key}")'),
     "new": ("        if key not in run:\n"
             "            pass"),
     "kind": "pytest",
     "target": f"{TESTS}/test_block_06_i4_workflow.py::test_advance_missing_definition_id_refused"},
    {"id": "M17", "label": "run None-field governed refusal removed", "file": WORKFLOW,
     "old": ("        if run[key] is None:\n"
             '            raise OperatorRefusal("REFUSED_INVALID_RECORD", f"run.{key}=null")'),
     "new": ("        if run[key] is None:\n"
             "            pass"),
     "kind": "pytest",
     "target": f"{TESTS}/test_block_06_i4_workflow.py::test_advance_null_definition_id_refused"},
    {"id": "M15", "label": "I3 workflow registration declaration omitted",
     "file": I4_REGISTRATION,
     "old": ',\n      ".github/workflows/block-06-i3-validation.yml"', "new": "",
     "kind": "controls", "target": "i3_workflow_registered", "commit": True},
]


def git(cwd, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


def run_pytest(root: pathlib.Path, node: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-m", "pytest", node, "-q", "-p", "no:cacheprovider",
                           "-o", "addopts="], cwd=str(root), capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


COLLECTION_MARKERS = ("found no collectors", "ERROR collecting", "errors during collection")


def node_name(node: str) -> str:
    return node.split("::")[-1]


def compile_source(path: pathlib.Path) -> tuple[bool, str]:
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except SyntaxError as exc:
        return False, f"{type(exc).__name__}: {exc}"
    return True, ""


def collect_node(root: pathlib.Path, node: str) -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", node, "--collect-only", "-q",
         "-p", "no:cacheprovider", "-o", "addopts="],
        cwd=str(root), capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    ok = (proc.returncode == 0 and node_name(node) in out
          and not any(marker in out for marker in COLLECTION_MARKERS))
    return ok, out


def junit_case(path: pathlib.Path, name: str) -> tuple[str, str]:
    if not path.exists():
        return "absent", ""
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    for suite in suites:
        for case in suite.findall("testcase"):
            if case.get("name") != name:
                continue
            failure = case.find("failure")
            if failure is not None:
                message = failure.get("message") or (failure.text or "")
                return "failed", message[:400]
            if case.find("error") is not None:
                return "error", ""
            if case.find("skipped") is not None:
                return "skipped", ""
            return "passed", ""
    return "absent", ""


def run_node(root: pathlib.Path, node: str, junit: pathlib.Path):
    if junit.exists():
        junit.unlink()
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", node, f"--junitxml={junit}", "-q",
         "-p", "no:cacheprovider", "-o", "addopts="],
        cwd=str(root), capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    status, message = junit_case(junit, node_name(node))
    return proc.returncode, out, status, message


def run_controls(root: pathlib.Path) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, CONTROLS, "--root", str(root)], cwd=str(root),
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def control_failed(out: str, target: str) -> bool:
    try:
        payload = json.loads(out[out.index("{"):])
    except Exception:
        return False
    return any(row.get("control") == target and row.get("ok") is False
               for row in payload.get("results", []))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    ap.add_argument("--root", default=None)
    args = ap.parse_args(argv)
    root = (pathlib.Path(args.root).resolve() if args.root
            else pathlib.Path(__file__).resolve().parents[3])
    results = []
    pristine_green = False
    worktree_clean = False
    with tempfile.TemporaryDirectory(prefix="b6i4-mut-") as tmp:
        work = pathlib.Path(tmp) / "wt"
        subprocess.run(["git", "-C", str(root), "worktree", "add", "--detach", "--quiet",
                        "--no-checkout", str(work), "HEAD"], check=True)
        # Only the governed surfaces are checked out: the repository carries large unrelated data
        # directories, and a full scratch checkout can exhaust the runner disk.
        subprocess.run(["git", "-C", str(work), "sparse-checkout", "init", "--cone"],
                       check=True)
        subprocess.run(["git", "-C", str(work), "sparse-checkout", "set",
                        "oce", "infrastructure", "docs", ".github"], check=True)
        subprocess.run(["git", "-C", str(work), "checkout", "--quiet", "HEAD"], check=True)
        try:
            modules = [str(p) for p in sorted((work / TESTS).glob("test_block_06_i4_*.py"))]
            if not modules:
                print("scratch worktree has no focused test modules")
                return 2
            code = subprocess.run([sys.executable, "-m", "pytest", *modules, "-q",
                                   "-p", "no:cacheprovider", "-o", "addopts="],
                                  cwd=str(work), capture_output=True, text=True)
            if code.returncode != 0:
                print(code.stdout[-3000:])
                print("pristine worktree is red; refusing to mutate")
                return 2
            for item in MUTATIONS:
                pre_head = git(work, "rev-parse", "HEAD").stdout.strip()
                target = work / item["file"]
                pristine = target.read_bytes()
                text = pristine.decode("utf-8")
                if item["old"] not in text:
                    results.append({"id": item["id"], "mutation": item["label"],
                                    "expected_target": item["target"], "applied": False,
                                    "discriminated": False, "restored": True,
                                    "error": "anchor not found"})
                    continue
                target.write_text(text.replace(item["old"], item["new"], 1), encoding="utf-8",
                                  newline="\n")
                applied = target.read_bytes() != pristine
                if item.get("commit"):
                    git(work, "add", "-A")
                    git(work, "-c", "user.email=ci@example.com", "-c", "user.name=ci",
                        "commit", "-qm", f"mutation-{item['id']}")
                compiled = collected = executed = None
                compile_error = collection_error = ""
                node_status = failure_message = ""
                if item["kind"] == "pytest":
                    compiled, compile_error = compile_source(target)
                    if compiled:
                        collected, collect_out = collect_node(work, item["target"])
                        collection_error = next(
                            (m for m in COLLECTION_MARKERS if m in collect_out), "")
                        observed_rc, out, node_status, failure_message = run_node(
                            work, item["target"], work / ".mutation-junit.xml")
                        executed = node_status == "failed"
                        discriminated = (observed_rc == 1 and collected and executed
                                         and not collection_error)
                        discriminator_ok = discriminated
                    else:
                        observed_rc, out = 0, compile_error
                        discriminated = discriminator_ok = False
                else:
                    observed_rc, out = run_controls(work)
                    discriminated = observed_rc != 0
                    discriminator_ok = control_failed(out, item["target"])
                if item.get("commit"):
                    git(work, "reset", "-q", "--hard", pre_head)
                else:
                    target.write_bytes(pristine)
                restored = (target.read_bytes() == pristine
                            and git(work, "rev-parse", "HEAD").stdout.strip() == pre_head)
                pristine_named_green = None
                if item["kind"] == "pytest" and restored:
                    rc_named, _ = run_pytest(work, item["target"])
                    pristine_named_green = rc_named == 0
                results.append({
                    "id": item["id"], "mutation": item["label"],
                    "expected_target": item["target"], "applied": applied,
                    "compiled": compiled, "compile_error": compile_error,
                    "collected": collected, "collection_error": collection_error,
                    "executed": executed, "node_status": node_status,
                    "failure_message": failure_message,
                    "observed_rc": observed_rc, "discriminated": discriminated,
                    "discriminator_ok": discriminator_ok, "restored": restored,
                    "pristine_named_green": pristine_named_green,
                    "pre_sha256": hashlib.sha256(pristine).hexdigest(),
                    "post_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                })
            code = subprocess.run([sys.executable, "-m", "pytest", *modules, "-q",
                                   "-p", "no:cacheprovider", "-o", "addopts="],
                                  cwd=str(work), capture_output=True, text=True)
            pristine_green = code.returncode == 0
            worktree_clean = git(work, "status", "--porcelain").stdout.strip() == ""
        finally:
            subprocess.run(["git", "-C", str(root), "worktree", "remove", "--force", str(work)],
                           check=False)
    payload = {
        "battery": "block_06_i4_mutation_battery.py",
        "floor": FLOOR,
        "total": len(results),
        "applied": sum(1 for row in results if row.get("applied") is True),
        "discriminated": sum(1 for row in results if row["discriminated"]),
        "restored": sum(1 for row in results if row["restored"]),
        "pristine_green_after": pristine_green,
        "worktree_clean_after": worktree_clean,
        "witness_law": "S2: compile, collect, execute, fail with rc=1, restore, pristine",
        "all_ok": (sum(1 for row in results if row["discriminated"]) >= FLOOR
                   and all(row.get("applied") is True for row in results)
                   and all(row.get("discriminator_ok") for row in results)
                   and all(row["restored"] for row in results)
                   and all(row.get("compiled") is not True
                           or row.get("pristine_named_green") is True for row in results)
                   and pristine_green and worktree_clean),
        "results": results,
    }
    text = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    if args.json:
        pathlib.Path(args.json).write_text(text, encoding="utf-8", newline="\n")
    print(f"floor {FLOOR} | mutations {len(results)} | applied {payload['applied']} "
          f"| discriminated {payload['discriminated']} | restored {payload['restored']} "
          f"| pristine_green {pristine_green} | clean {worktree_clean}")
    for row in results:
        ok = (row.get("applied") and row["discriminated"] and row.get("discriminator_ok")
              and row["restored"] and (row.get("compiled") is not True
                                       or row.get("pristine_named_green") is True))
        print(("OK " if ok else "BAD ")
              + f"{row['id']} {row['mutation']} -> {row['expected_target'].split('::')[-1]}")
    return 0 if payload["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
