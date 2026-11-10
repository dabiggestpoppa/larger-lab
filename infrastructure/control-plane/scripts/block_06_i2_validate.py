#!/usr/bin/env python3
"""B6-I2 conformance validator.

Recomputes the frozen packet, the API surface, compatibility rows, registry, failure and threat
matrix, the B6-I1 accounting correction, the stage registration, the manifest and the changed-file
boundary. Standard library only, offline, no secret, no network.

Usage:
  python infrastructure/control-plane/scripts/block_06_i2_validate.py [--json out.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import block_06_stage_scope as stage_scope  # noqa: E402

DOCS = "docs/oce-golden-system"
PREFIX = "OCE_BLOCK_06_I2_"
BASE_SHA = "4496d548078660efd7ad4f93e7fff461d34ea538"
BASE_TREE = "c6638bde3e9c8f71482f4d96fde42d0484d9a624"
I0_HEAD = "c5d7bfcc5ea99837985ba82a3c91fd1e76d85a81"
I1_HEAD = "96e3b81714321f4eea7abcb300ef471e93be0962"
TESTS = "infrastructure/control-plane/tests"
SCRIPTS = "infrastructure/control-plane/scripts"
ALLOWED_PREFIXES = (
    f"{DOCS}/{PREFIX}",
    f"{SCRIPTS}/block_06_i2_",
    f"{TESTS}/test_block_06_i2_",
    f"{TESTS}/stage_scope/test_block_06_i2_",
    f"{TESTS}/test_block_06_i0_stage_contract.py",
    f"{TESTS}/test_block_06_i1_authority_and_boundary.py",
    f"{SCRIPTS}/block_06_stage_scope.py",
    f"{SCRIPTS}/block_06_i0_validate.py",
    f"{SCRIPTS}/block_06_i1_validate.py",
    f"{TESTS}/stage_scope/test_i0_stage_scope_amendment_controls.py",
    ".github/workflows/block-06-i2-validation.yml",
    ".github/workflows/block-06-i2-paired-comparison.yml",
    ".github/workflows/block-06-i1-validation.yml",
    "oce/templates/", "oce/harness/",
)
FORBIDDEN_PREFIXES = (
    "packages/", "dist/", "build/", "pyproject.toml", "package.json", "uv.lock", "poetry.lock",
    "infrastructure/control-plane/src/", "infrastructure/console/src/",
    f"{DOCS}/OCE_BLOCK_06_P0_", f"{DOCS}/OCE_BLOCK_06_I0_", f"{DOCS}/OCE_BLOCK_06_I1_",
    "oce/api/", "oce/sdk/", "oce/compat/",
)
FORBIDDEN_TOKENS = ("B6_I2_RATIFIED", "B6_I2_MERGED", "PACKAGE_PUBLISHED",
                    "BOOK_6_COMPLETE = true", "MERGE_AUTHORIZED = true")


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def git(root: pathlib.Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


class Checker:
    def __init__(self, root: pathlib.Path) -> None:
        self.root = root
        self.checks: list[str] = []
        self.failures: list[str] = []

    def need(self, name: str, ok: bool, detail=None) -> None:
        self.checks.append(name)
        if not ok:
            self.failures.append(f"{name}: {detail}")

    def load(self, name: str) -> dict:
        return json.loads((self.root / DOCS / f"{PREFIX}{name}").read_text(encoding="utf-8"))


def check_packet(c: Checker) -> None:
    files = sorted(p.name for p in (c.root / DOCS).glob(f"{PREFIX}*.json"))
    c.need("packet/count", len(files) == 11, files)
    for name in files:
        raw = (c.root / DOCS / name).read_bytes()
        c.need(f"packet/canonical/{name}", raw == canonical(json.loads(raw)))
        c.need(f"packet/lf/{name}", b"\r\n" not in raw and raw.endswith(b"\n"))
    scope = c.load("SCOPE_DERIVATION_v1.0.json")
    contract = c.load("IMPLEMENTATION_CONTRACT_v1.0.json")
    c.need("stage/id", scope["stage"] == "B6-I2" and contract["stage"] == "B6-I2")
    c.need("stage/purpose", scope["purpose"] == "C1 templates and local harness")
    c.need("stage/sections", scope["sections"] == ["C1.S3", "C1.S4"])
    c.need("stage/surfaces", scope["implementation_surfaces"] == ["templates", "harness"])
    c.need("stage/outputs", scope["outputs"] == ["template", "harness"])
    c.need("stage/gate", scope["exit_gate"] == "fresh generated app starts locally")
    c.need("stage/stop", scope["stop_conditions"] == ["stop if cloud is required"])
    c.need("stage/non_goal", scope["non_goals"] == ["cloud dependency"])
    c.need("stage/base", scope["base_sha"] == BASE_SHA and scope["base_tree"] == BASE_TREE)
    c.need("contract/frozen", contract["status"] == "FROZEN"
           and contract["frozen_before_results"] is True)
    c.need("contract/floors", contract["implementation_floor"]
           == {"mutations": 6, "source_mutation_floor": 3, "test_nodes": 30})
    c.need("contract/paired", contract["paired_comparison"]
           == {"base_only_expected": 0, "base_sha": BASE_SHA, "common_floor": 208,
               "head_only_expected": 30})
    c.need("contract/common_floor", contract["adjacent_floors"]["common_regression_nodes"] == 208)
    c.need("contract/determinism", all(contract["determinism"].values()))
    c.need("contract/bounds", contract["bounds"] == {"archive_bytes": 1048576, "entries": 256,
                                                     "entry_bytes": 262144, "input_bytes": 65536})
    c.need("contract/template", "safe tar" in contract["template"]["archive"] or
           contract["template"]["cloud_dependency"] is False)
    c.need("contract/harness", contract["harness"]["opens_sockets"] is False
           and contract["harness"]["refuses_undeclared_network_calls"] is True)
    c.need("contract/refusal_classes", {row["class"] for row in contract["refusals"]}
           >= {"F13", "F14", "F15", "F16", "F19", "F21"})
    sys.path.insert(0, str(c.root))
    from oce.templates import refusals  # noqa: PLC0415
    declared_codes = {row["code"] for row in contract["refusals"]}
    c.need("contract/refusal_codes_bound", declared_codes <= set(refusals.CODES),
           sorted(declared_codes - set(refusals.CODES)))
    c.need("contract/refusal_codes_unique", len(declared_codes) == len(contract["refusals"]))


def check_api(c: Checker) -> None:
    api = c.load("API_TEMPLATE_AND_HARNESS_CONTRACT_v1.0.json")
    rows = {row["symbol"]: row for row in api["symbols"]}
    c.need("api/symbols", set(rows) == {"template:oce-app-skeleton", "oce.harness.local.up"})
    c.need("api/template_deferred", rows["template:oce-app-skeleton"]["classification"]
           == "deferred" and rows["template:oce-app-skeleton"]["exported"] is False)
    c.need("api/harness_experimental",
           rows["oce.harness.local.up"]["classification"] == "public_experimental"
           and rows["oce.harness.local.up"]["exported"] is True)
    c.need("api/no_stable", all(row["classification"] != "stable" for row in rows.values()))
    c.need("api/prohibitions", "no stable private symbol" in api["prohibitions"]
           and "no client supplied authority" in api["prohibitions"])
    c.need("api/section_binding", {row["section"] for row in rows.values()} == {"C1.S3", "C1.S4"})


def check_compat(c: Checker) -> None:
    compat = c.load("COMPATIBILITY_MATRIX_v1.0.json")
    c.need("compat/rows", compat["rows_total"] == 2
           and {row["surface"] for row in compat["rows"]} == {"C1.S3", "C1.S4"})
    c.need("compat/unproven", all(row["state"] == "UNPROVEN" for row in compat["rows"])
           and compat["observed"]["proven_rows"] == 0)
    c.need("compat/consumer_evidence", all(row["consumer_evidence"] == "none"
                                           for row in compat["rows"]))
    c.need("compat/no_silent_latest", compat["refusal"]["silent_latest"] is False)
    c.need("compat/unknown_refused", compat["refusal"]["unknown_version"] == "REFUSED")


def check_registry(c: Checker) -> None:
    registry = c.load("REQUIREMENT_TEST_REGISTRY_v1.0.json")
    c.need("registry/requirements", registry["requirements_total"] == 30)
    c.need("registry/nodes", registry["inventory"]["nodes"]
           and len(registry["inventory"]["nodes"]) == 30
           and len(set(registry["inventory"]["nodes"])) == 30)
    c.need("registry/modules", len(registry["inventory"]["modules"]) == 6)
    c.need("registry/no_orphans", [row for row in registry["requirements"]
                                   if row["binding_node"] not in registry["inventory"]["nodes"]]
           == [])
    c.need("registry/no_later_stage", not [n for n in registry["inventory"]["nodes"]
                                          if any(f"i{i}" in n for i in range(3, 10))])
    defined = set()
    for module in sorted((c.root / TESTS).glob("test_block_06_i2_*.py")):
        text = module.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("def test_"):
                defined.add(f"{module.name}::{line[4:line.index('(')]}")
    c.need("registry/declared_equals_defined", defined == set(registry["inventory"]["nodes"]),
           sorted(defined ^ set(registry["inventory"]["nodes"])))


def check_failures(c: Checker) -> None:
    proofs = c.load("FAILURE_AND_THREAT_PROOFS_v1.0.json")
    c.need("failures/classes", proofs["failure_classes_total"] == 6)
    c.need("failures/ids", {row["id"] for row in proofs["failure_classes"]}
           == {"F13", "F14", "F15", "F16", "F19", "F21"})
    c.need("failures/bound", all(row["proof_state"] for row in proofs["failure_classes"]))
    c.need("failures/threats", proofs["threats_total"] == 13)
    c.need("threats/ids", {row["id"] for row in proofs["threats"]}
           == {"T01", "T02", "T03", "T06", "T10", "T11", "T12", "T13", "T15", "T16", "T17",
               "T18", "T19"})
    c.need("failures/no_cloud", proofs["policy"]["cloud_refused"] is True)


def check_correction_and_registration(c: Checker) -> None:
    correction = c.load("ACCOUNTING_CORRECTION_v1.0.json")
    findings = {row["id"]: row for row in correction["findings"]}
    c.need("correction/append_only", correction["append_only"] is True
           and correction["rewrites_history"] is False)
    c.need("correction/classifications",
           findings["C-01"]["classification"] == "BOOKKEEPING_WORDING"
           and findings["C-02"]["classification"] == "AUTHORITATIVE_RECORD_DEFECT")
    population = correction["authoritative_mutation_population"]
    c.need("correction/population", population["rows_total"] == 13
           and population["floor"] == 12 and population["discriminated_linux"] == 12
           and population["restored"] == 13)
    registration = c.load("STAGE_SCOPE_REGISTRATION_v1.0.json")
    stage = registration["this_stage"]
    c.need("registration/frozen", registration["status"] == "FROZEN"
           and registration["frozen_before_results"] is True)
    c.need("registration/prior", registration["prior_stages"]["B6-I0"]["head"] == I0_HEAD
           and registration["prior_stages"]["B6-I1"]["head"] == I1_HEAD)
    c.need("registration/base", stage["base"] == BASE_SHA and stage["base_tree"] == BASE_TREE)
    c.need("registration/allowed", "oce/templates/" in stage["allowed_prefixes"]
           and "oce/harness/" in stage["allowed_prefixes"])
    for stage_id in ("B6-I3", "B6-I4", "B6-I5", "B6-I6", "B6-I7", "B6-I8", "B6-I9"):
        c.need(f"registration/locked/{stage_id}", registration["locks"][stage_id] == "LOCKED")


def check_amendment(c: Checker) -> None:
    amendment = c.load("PROOF_CLOSURE_AMENDMENT_v1.0.json")
    c.need("amendment/frozen", amendment["status"] == "FROZEN"
           and amendment["frozen_before_results"] is True)
    c.need("amendment/supersedes", len(amendment["supersedes"]) == 2
           and {row["clause"] for row in amendment["supersedes"]}
           == {"IMPLEMENTATION_CONTRACT_v1.0.template.start",
               "ACCOUNTING_CORRECTION_v1.0.authoritative_mutation_population"})
    m13 = amendment["m13"]
    correction = c.load("ACCOUNTING_CORRECTION_v1.0.json")["authoritative_mutation_population"]
    c.need("amendment/m13_disposition", m13["disposition"] == "POSIX_ENVIRONMENTAL_PROBE"
           and m13["governed_rows"] == 12 and m13["probe_rows"] == 1
           and m13["floor"] == correction["floor"] == 12
           and m13["governed_rows"] + m13["probe_rows"] == correction["rows_total"] == 13)
    c.need("amendment/m13_probe_not_claimed", m13["probe_discriminated_linux"] is False
           and m13["governed_discriminated_linux"] == 12)
    start = amendment["local_start"]
    c.need("amendment/local_start", start["mode"] == "SUBPROCESS_START_WITH_READINESS"
           and start["evidence_node"]
           == "test_block_06_i2_templates.py::test_generated_app_starts_locally"
           and start["exit_code"] == 0 and start["network"] is False)
    dispositions = {key: row["disposition"] for key, row in amendment["compatibility"].items()}
    c.need("amendment/compat", dispositions == {"C1.S3": "UNPROVEN_BUT_EXIT_GATE_ALLOWS",
                                                "C1.S4": "UNPROVEN_BUT_EXIT_GATE_ALLOWS"})
    c.need("amendment/prior_tests_restored",
           set(amendment["prior_stage_preservation"]["restored_byte_identical"])
           == {"infrastructure/control-plane/tests/test_block_06_i0_stage_contract.py",
               "infrastructure/control-plane/tests/test_block_06_i1_authority_and_boundary.py"})
    c.need("amendment/floors", amendment["floors"] == {"test_nodes": 30, "stage_mutations": 6,
                                                       "i0_governed_mutations": 12,
                                                       "common_regression_nodes": 208})
    c.need("amendment/locks", amendment["locks"]["B6-I3_through_I9"] == "LOCKED"
           and amendment["locks"]["MERGE_AUTHORIZED"] is False
           and amendment["locks"]["BOOK_6_COMPLETE"] is False)


def check_manifest(c: Checker) -> None:
    manifest = c.load("MANIFEST_v1.0.json")
    c.need("manifest/status", manifest["status"] == "FROZEN")
    c.need("manifest/base", manifest["base_sha"] == BASE_SHA)
    c.need("manifest/artifacts", manifest["totals"]["artifacts"] == 9)
    c.need("manifest/code", manifest["totals"]["code"] >= 7)
    for row in manifest["artifacts"] + manifest["code"]:
        path = c.root / row["path"]
        c.need(f"manifest/exists/{row['path']}", path.is_file())
        if path.is_file():
            data = path.read_bytes()
            c.need(f"manifest/hash/{row['path']}",
                   row["sha256"] == hashlib.sha256(data).hexdigest()
                   and row["bytes"] == len(data))
    c.need("manifest/no_manifest_self", all(row["path"].endswith("MANIFEST_v1.0.json")
                                            is False for row in manifest["artifacts"]))


def check_boundary(c: Checker) -> None:
    if not (c.root / ".git").exists():
        c.need("boundary/skipped_scratch", False, "not a git checkout")
        return
    code, status = git(c.root, "status", "--porcelain")
    c.need("boundary/tracked_clean", code == 0 and status == "", status[:400])
    code, out = git(c.root, "diff", "--name-only", f"{BASE_SHA}..HEAD")
    changed = [line for line in out.splitlines() if line.strip()]
    c.need("boundary/changed", bool(changed), changed)
    outside = [p for p in changed if not p.startswith(ALLOWED_PREFIXES)]
    c.need("boundary/only_allowed_paths", not outside, outside)
    blocked = [p for p in changed if p.startswith(FORBIDDEN_PREFIXES)]
    c.need("boundary/no_prohibited_surface", not blocked, blocked)
    # Both prior packets are frozen at the B6-I1 ratification head; the I0 amendment was amended
    # there, so I0_HEAD is not the immutable baseline.
    for label in ("i0", "i1"):
        code, diff = git(c.root, "diff", "--name-only", f"{I1_HEAD}..HEAD", "--", DOCS)
        frozen = [line for line in diff.splitlines()
                  if f"OCE_BLOCK_06_{label.upper()}_" in line]
        c.need(f"boundary/{label}_packet_frozen", not frozen, frozen)
    code, diff = git(c.root, "diff", "--name-only", f"{BASE_SHA}..HEAD", "--",
                     "docs/oce-golden-system/OCE_BLOCK_06_P0_")
    c.need("boundary/p0_frozen", not diff.strip(), diff)
    for rel in ("infrastructure/control-plane/tests/test_block_06_i0_stage_contract.py",
                "infrastructure/control-plane/tests/test_block_06_i1_authority_and_boundary.py"):
        code, _ = git(c.root, "diff", "--quiet", f"{BASE_SHA}..HEAD", "--", rel)
        c.need(f"boundary/prior_test_bytes/{rel.rsplit('/', 1)[-1]}", code == 0)
    code, later = git(c.root, "ls-tree", "-r", "--name-only", "HEAD")
    forbidden = [p for p in later.splitlines()
                 if any(f"OCE_BLOCK_06_I{i}_" in p for i in range(3, 10))]
    c.need("boundary/no_later_stage_artifact", not forbidden, forbidden)
    if status == "":
        try:
            resolved = stage_scope.resolve(c.root, "auto")
            c.need("stage/resolver_identity", resolved.get("mode") == "i2"
                   and resolved.get("stage") == "B6-I2", resolved.get("mode"))
            stage_allowed = set(resolved.get("allowed", ()))
            c.need("stage/resolver_covers_changes",
                   all(p in stage_allowed or p.startswith(tuple(stage_allowed))
                       for p in changed),
                   sorted(p for p in changed if not p.startswith(tuple(stage_allowed))))
        except stage_scope.StageScopeError as exc:
            c.need("stage/resolver_identity", False, f"{exc.check}: {exc.detail}")


def check_text(c: Checker) -> None:
    scope = c.load("SCOPE_DERIVATION_v1.0.json")
    locks = scope["locks"]
    c.need("locks/book6", locks["BOOK_6_COMPLETE"] is False)
    c.need("locks/holds", locks["MERGE_AUTHORIZED"] is False
           and locks["RATIFICATION_AUTHORIZED"] is False)
    c.need("locks/g16", locks["G16"] == "OPEN" and locks["G16_OWNER"] == "B5I8-DF05")
    c.need("locks/evaluation", locks["evaluation_system"] == "RESERVED_NOT_AUTHORIZED")
    c.need("locks/cloud", locks["cloud_hosting"] == "NOT_AUTHORIZED")
    c.need("locks/cost", scope["cost_usd"] == 0 and scope["capital_authority"] == "none")
    for path in sorted((c.root / DOCS).glob(f"{PREFIX}*")):
        text = path.read_text(encoding="utf-8")
        bad = [token for token in FORBIDDEN_TOKENS if token in text]
        c.need(f"text/no_claim/{path.name}", not bad, bad)
        c.need(f"text/no_abs_path/{path.name}",
               "C:\\" not in text and "/home/" not in text and "/Users/" not in text)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    root = (pathlib.Path(args.root).resolve() if args.root
            else pathlib.Path(__file__).resolve().parents[3])
    c = Checker(root)
    for check in (check_packet, check_api, check_compat, check_registry, check_failures,
                  check_correction_and_registration, check_amendment, check_manifest,
                  check_boundary, check_text):
        try:
            check(c)
        except Exception as exc:  # a missing artifact is a failure, not a crash
            c.need(f"{check.__name__}/exception", False, repr(exc))
    status = "PASS" if not c.failures else "FAIL"
    doc = {"status": status, "checks": len(c.checks), "failures": len(c.failures),
           "detail": c.failures[:12], "stage": "B6-I2",
           "base_sha": BASE_SHA, "cost_usd": 0, "capital_authority": "none"}
    text = json.dumps(doc, sort_keys=True, indent=2) + "\n"
    if args.json:
        pathlib.Path(args.json).write_text(text, encoding="utf-8", newline="\n")
    print("\n".join(f"FAIL {row}" for row in c.failures))
    print(f"{status} {len(c.checks) - len(c.failures)}/{len(c.checks)} checks")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
