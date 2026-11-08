#!/usr/bin/env python3
"""Book 6 B6-I0 conformance validator.

Deterministic, offline, standard library only. It reads the canonical B6-I0 decision
artifacts, recomputes every total from the committed P0 sources, and refuses to convert
missing evidence into PASS. It never authorizes publication, B6-I1 or a merge.

Usage:
  python infrastructure/control-plane/scripts/block_06_i0_validate.py
  python infrastructure/control-plane/scripts/block_06_i0_validate.py --root <scratch-copy>
  python infrastructure/control-plane/scripts/block_06_i0_validate.py --json out.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

DOCS = "docs/oce-golden-system"
I0 = "OCE_BLOCK_06_I0_"
P0 = "OCE_BLOCK_06_P0_"
ARTIFACTS = {
    "scope": f"{DOCS}/{I0}SCOPE_DERIVATION_v1.0.json",
    "contract": f"{DOCS}/{I0}IMPLEMENTATION_CONTRACT_v1.0.json",
    "decisions": f"{DOCS}/{I0}EXTRACTION_DECISION_FREEZE_v1.0.json",
    "api": f"{DOCS}/{I0}API_PRINCIPLES_AND_FIREWALL_v1.0.json",
    "compat": f"{DOCS}/{I0}COMPATIBILITY_AND_CONFORMANCE_BASELINE_v1.0.json",
    "failures": f"{DOCS}/{I0}FAILURE_AND_THREAT_PROOFS_v1.0.json",
    "registry": f"{DOCS}/{I0}REQUIREMENT_TEST_REGISTRY_v1.0.json",
    "manifest": f"{DOCS}/{I0}MANIFEST_v1.0.json",
}
LEDGER = f"{DOCS}/{I0}PROGRESS_EVIDENCE_LEDGER_v1.0.md"
CONTRACT_MD = f"{DOCS}/{I0}IMPLEMENTATION_CONTRACT_v1.0.md"
BASE_SHA = "5e76dc12207bf1674ff7ccd94aed0f36b12dd3e6"
P0_SHA = "e2aa8ac71dc9f0de4287fbcaa8a17ff127d5356f"
FLOOR = 12
ALLOWED_PREFIXES = (
    f"{DOCS}/{I0}",
    "infrastructure/control-plane/scripts/block_06_i0_",
    "infrastructure/control-plane/scripts/block_06_i0_",
    "infrastructure/control-plane/tests/test_block_06_i0_",
    "infrastructure/control-plane/tests/block_06_i0_support.py",
    ".github/workflows/block-06-i0-validation.yml",
)
PROHIBITED_PREFIXES = (
    "infrastructure/control-plane/src/", "infrastructure/console/src/", "oce/",
    "packages/", "dist/", "build/", "pyproject.toml", "package.json", "uv.lock",
    "poetry.lock", f"{DOCS}/{P0}",
)
P0_FILES = [f"{DOCS}/{P0}{name}" for name in (
    "AUTHORITY_AND_SOURCE_MAP_v1.0.md", "IDENTITY_AND_SCOPE_CONTRACT_v1.0.md",
    "CANDIDATE_EXTRACTION_DISPOSITION_v1.0.json", "PUBLIC_PRIVATE_API_FIREWALL_v1.0.json",
    "REQUIREMENT_TEST_REGISTRY_v1.0.json", "CONSTRUCTION_PLAN_v1.0.md",
    "CONSTRUCTION_SEQUENCE_v1.0.json", "FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md",
    "FAILURE_AND_THREAT_REGISTRY_v1.0.json", "SECURITY_AND_THREAT_MODEL_v1.0.md",
    "VERSIONING_AND_COMPATIBILITY_CONTRACT_v1.0.md",
    "COMPATIBILITY_AND_REPRODUCIBILITY_PLAN_v1.0.json",
    "REPRODUCIBILITY_AND_PROVENANCE_PLAN_v1.0.md",
    "EVALUATION_READINESS_HANDOFF_v1.0.md", "ACCEPTANCE_MATRIX_v1.0.md",
    "PROGRESS_EVIDENCE_LEDGER_v1.0.md", "OPERATOR_RATIFICATION_v1.0.md",
)] + ["infrastructure/control-plane/scripts/block_06_p0_validate.py"]
G16_PACKET = "infrastructure/control-plane/evidence/b5-i9/g16-limitation.json"
HANDOFF = "infrastructure/control-plane/evidence/b5-i9/handoff-input-readiness.json"
ADMISSIBLE = {"EXTRACTABLE_PATTERN", "EXTRACTABLE_WITH_LIMITATION", "DEFERRED_TO_BOOK_6"}
CLASSES = ["EXTRACTABLE_PATTERN", "EXTRACTABLE_WITH_LIMITATION", "REFERENCE_ONLY",
           "PLATFORM_INTERNAL", "PRIVATE_API", "AUTHORITY_BEARING", "PROHIBITED",
           "DEFERRED_TO_BOOK_6", "NOT_APPLICABLE"]
EXPECTED_DIST = {"EXTRACTABLE_PATTERN": 7, "EXTRACTABLE_WITH_LIMITATION": 5,
                 "REFERENCE_ONLY": 4, "PLATFORM_INTERNAL": 3, "PRIVATE_API": 2,
                 "AUTHORITY_BEARING": 3, "PROHIBITED": 1, "DEFERRED_TO_BOOK_6": 1,
                 "NOT_APPLICABLE": 1}
FORBIDDEN_FLAGS = ("BOOK_6_IMPLEMENTATION_STARTED = true", "B6_I0_RATIFIED",
                   "B6_I0_MERGED", "PACKAGE_PUBLISHED", "IMPLEMENTED_AND_RELEASED")
SECRET_PATTERNS = [
    re.compile(r"BEGIN (RSA|OPENSSH|EC|PGP) PRIVATE KEY"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)\bclient_secret\s*[:=]"),
    re.compile(r"(?i)\bpassword\s*[:=]\s*\S"),
    re.compile(r"(?i)\bapi[_-]?key\s*[:=]\s*\S"),
]
URL_PATTERN = re.compile(r"https?://", re.I)
ABS_PATH = re.compile(r"(?<![A-Za-z0-9_])(?:[A-Za-z]:\\\\|/home/|/Users/|/tmp/)")
ENV_FIELDS = ("timestamp", "generated_at", "hostname", "username", "user", "tmpdir",
              "temp_path", "random_seed", "run_started")


class Checker:
    def __init__(self, root: pathlib.Path) -> None:
        self.root = root
        self.failures: list[dict] = []
        self.checks: list[str] = []

    def ok(self, name: str) -> None:
        self.checks.append(name)

    def need(self, name: str, cond: bool, detail="") -> None:
        if cond:
            self.ok(name)
        else:
            self.failures.append({"check": name, "detail": detail or "condition false"})

    def path(self, rel: str) -> pathlib.Path:
        return self.root / rel

    def data(self, key: str):
        return json.loads(self.path(ARTIFACTS[key]).read_text(encoding="utf-8"))

    def p0(self, name: str):
        return json.loads(self.path(f"{DOCS}/{P0}{name}").read_text(encoding="utf-8"))

    def text(self, rel: str) -> str:
        return self.path(rel).read_text(encoding="utf-8")


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def git(c: Checker, args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(["git", *args], cwd=c.root, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def check_files(c: Checker) -> None:
    missing = [p for p in ARTIFACTS.values() if not c.path(p).exists()]
    c.need("files/artifacts_present", not missing, missing)
    docs = [p for p in (LEDGER, CONTRACT_MD) if not c.path(p).exists()]
    c.need("files/documents_present", not docs, docs)


def check_canonical(c: Checker) -> None:
    bad = []
    for key, rel in ARTIFACTS.items():
        try:
            raw = c.path(rel).read_bytes()
            canon = canonical(json.loads(raw.decode("utf-8")))
        except (ValueError, UnicodeDecodeError) as exc:  # pragma: no cover - schema guard
            bad.append(f"{rel}:{exc}")
            continue
        if raw != canon:
            bad.append(rel)
    c.need("json/canonical_bytes", not bad, bad)
    c.need("json/no_crlf", not any(b"\r\n" in c.path(p).read_bytes() for p in ARTIFACTS.values()),
           "CRLF in a canonical artifact")


def scan_untrusted_links(root: pathlib.Path, prefix: str) -> list[str]:
    """Paths under prefix that are symlinks or resolve outside the root.

    The scan deliberately does not follow links: a symlink is reported rather than resolved,
    because a link can otherwise present an out-of-tree file as if it were a packet artifact.
    """
    base = root / prefix
    found: list[str] = []
    if not base.exists():
        return found
    for path in base.rglob("*"):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            found.append(rel)
            continue
        try:
            path.resolve().relative_to(root.resolve())
        except ValueError:
            found.append(rel)
    return sorted(found)


def check_containment(c: Checker) -> None:
    bad = []
    for rel in ARTIFACTS.values():
        path = c.path(rel)
        if path.is_symlink():
            bad.append(f"{rel}:symlink")
            continue
        try:
            path.resolve().relative_to(c.root.resolve())
        except ValueError:
            bad.append(f"{rel}:escape")
    c.need("boundary/no_symlinked_artifacts", not bad, bad)
    links = scan_untrusted_links(c.root, f"{DOCS}/{I0}".rstrip("/"))
    c.need("boundary/no_links_in_packet_dir", not links, links)


def check_manifest(c: Checker) -> None:
    m = c.data("manifest")
    rows = m["artifacts"]
    bad_paths = [r["path"] for r in rows
                 if r["path"].startswith(("/", "..", "."))
                 or ".." in r["path"].split("/")
                 or "\\" in r["path"]]
    c.need("manifest/relative_paths", not bad_paths and len({r["path"] for r in rows}) == len(rows),
           bad_paths)
    c.need("manifest/schema", m["schema_version"] == "1.0.0" and m["stage"] == "AUTHORIZED_STAGE=B6-I0", m)
    c.need("manifest/base", m["base_sha"] == BASE_SHA, m["base_sha"])
    covered = {r["path"] for r in rows}
    expected = {ARTIFACTS[k] for k in ARTIFACTS if k != "manifest"}
    c.need("manifest/covers_artifacts", covered == expected, sorted(covered ^ expected))
    bad = []
    for row in rows:
        path = c.path(row["path"])
        if not path.exists():
            bad.append(f"{row['path']}:missing")
            continue
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["sha256"] or len(raw) != row["size"]:
            bad.append(row["path"])
    c.need("manifest/hashes_match", not bad, bad)
    c.need("manifest/no_self_hash", ARTIFACTS["manifest"] not in covered, "manifest hashes itself")


def check_scope(c: Checker) -> None:
    s = c.data("scope")
    seq = c.p0("CONSTRUCTION_SEQUENCE_v1.0.json")
    stage = {x["id"]: x for x in seq["stages"]}["B6-I0"]
    c.need("scope/stage_binding",
           s["stage_binding"]["id"] == "B6-I0"
           and s["stage_binding"]["sections"] == stage["sections"]
           and s["stage_binding"]["non_goals"] == stage["non_goals"]
           and s["stage_binding"]["outputs"] == stage["outputs"], s["stage_binding"])
    c.need("scope/base_identity", s["base_sha"] == BASE_SHA and s["p0_ratification_sha"] == P0_SHA,
           (s["base_sha"], s["p0_ratification_sha"]))
    reg = c.p0("REQUIREMENT_TEST_REGISTRY_v1.0.json")
    reqs = sorted(r["id"] for r in reg["requirements"] if r["future_stage"] == "B6-I0")
    c.need("scope/requirements_exact", s["requirements"] == reqs, sorted(set(s["requirements"]) ^ set(reqs)))
    api = c.p0("PUBLIC_PRIVATE_API_FIREWALL_v1.0.json")
    c.need("scope/api_rows_exact", s["api_rows"] == sorted(x["symbol"] for x in api["symbols"]),
           "api rows differ")
    cand = c.p0("CANDIDATE_EXTRACTION_DISPOSITION_v1.0.json")
    c.need("scope/candidates_exact", s["candidates"] == sorted(x["id"] for x in cand["candidates"]),
           "candidate set differs")
    fail = c.p0("FAILURE_AND_THREAT_REGISTRY_v1.0.json")
    c.need("scope/failure_classes_exact",
           s["failure_classes"] == sorted(f["id"] for f in fail["failure_classes"] if f["stage"] == "B6-I0"),
           s["failure_classes"])
    c.need("scope/threats_exact",
           s["threats"] == sorted(t["id"] for t in fail["threats"] if t["stage"] == "B6-I0"),
           s["threats"])
    compat = c.p0("COMPATIBILITY_AND_REPRODUCIBILITY_PLAN_v1.0.json")
    c.need("scope/compat_rows_exact",
           s["compatibility_rows"] == [r["surface"] for r in compat["compatibility_matrix"]["rows"]],
           "compat rows differ")
    c.need("scope/provenance_15", len(s["provenance_obligations"]) == 15, len(s["provenance_obligations"]))
    c.need("scope/counts", s["counts"] == {
        "requirements": 19, "sections": 1, "candidates": 27, "api_rows": 30,
        "failure_classes": 6, "threats": 7, "compatibility_rows": 25,
        "provenance_obligations": 15, "planned_tests": len(s["planned_tests"])}, s["counts"])
    c.need("scope/floor_raised_not_lowered",
           s["mutation_floor"]["source"] == 0 and s["mutation_floor"]["contract"] == FLOOR, s["mutation_floor"])


def check_contract(c: Checker) -> None:
    k = c.data("contract")
    s = c.data("scope")
    c.need("contract/decision_mode",
           k["decision"]["mode"] == "decision_artifacts_plus_conformance_tooling"
           and k["decision"]["permits_code_extraction"] is False
           and k["decision"]["extracted_source_files"] == 0
           and k["decision"]["creates_experimental_interfaces"] is False, k["decision"])
    c.need("contract/frozen_before_results", k["frozen_before_results"] is True, k["frozen_before_results"])
    c.need("contract/inventory_matches_scope",
           k["requirement_ids"] == s["requirements"] and k["candidate_ids"] == s["candidates"]
           and k["api_rows"] == s["api_rows"], "contract inventory differs from derivation")
    c.need("contract/floor", k["mutation_floor"] == {"source": 0, "frozen": FLOOR}, k["mutation_floor"])
    c.need("contract/test_inventory",
           k["test_inventory"]["nodes"] == s["planned_tests"]
           and k["test_inventory"]["node_total"] == len(s["planned_tests"]), k["test_inventory"]["node_total"])
    c.need("contract/adjacent_floor", k["adjacent_floors"]["b5_i9_nodes"] == 41, k["adjacent_floors"])
    c.need("contract/operator_hold",
           k["operator_hold"]["b6_i0_merge_authorized"] is False
           and k["operator_hold"]["b6_i1_through_i9_authorized"] is False
           and k["operator_hold"]["package_publication_authorized"] is False
           and k["operator_hold"]["cost_usd"] == 0
           and k["operator_hold"]["capital_authority"] == "none", k["operator_hold"])
    c.need("contract/allowed_paths_declared",
           any(p.startswith(f"{DOCS}/{I0}") for p in k["allowed_paths"])
           and any(p.startswith("infrastructure/control-plane/tests/test_block_06_i0_") for p in k["allowed_paths"]),
           k["allowed_paths"])
    c.need("contract/prohibited_paths_declared",
           "infrastructure/control-plane/src/" in k["prohibited_paths"]
           and f"{DOCS}/{P0}" in k["prohibited_paths"], k["prohibited_paths"])
    c.need("contract/zero_extraction_flag", k["decision"]["zero_extraction"] if "zero_extraction" in k["decision"]
           else k["decision"]["extracted_source_files"] == 0, k["decision"])


def check_decisions(c: Checker) -> None:
    d = c.data("decisions")
    rows = d["candidates"]
    c.need("dec/total_27", d["candidate_total"] == 27 == len(rows), len(rows))
    c.need("dec/ids_unique", len({r["id"] for r in rows}) == 27, "duplicate candidate id")
    dist = {k: sum(1 for r in rows if r["classification"] == k) for k in CLASSES}
    c.need("dec/distribution", dist == EXPECTED_DIST, dist)
    inadmissible = [r["id"] for r in rows
                    if r["classification"] not in ADMISSIBLE
                    and r["decision"] != "REFUSED"]
    c.need("dec/no_ineligible_admitted", not inadmissible, inadmissible)
    authority = [r["id"] for r in rows
                 if r["classification"] in {"AUTHORITY_BEARING", "PROHIBITED", "PRIVATE_API",
                                            "PLATFORM_INTERNAL", "REFERENCE_ONLY",
                                            "NOT_APPLICABLE"}
                 and r["decision"] != "REFUSED"]
    c.need("dec/authority_never", not authority, authority)
    copies = [r["id"] for r in rows if r["extracted_at_b6_i0"] or r["copied_files"] != 0]
    c.need("dec/zero_copies", not copies, copies)
    arith = d["arithmetic"]
    computed = {
        "total": len(rows),
        "admitted": sum(1 for r in rows if r["decision"] == "ADMITTED_FOR_FUTURE_DESIGN"),
        "refused": sum(1 for r in rows if r["decision"] == "REFUSED"),
        "extracted": sum(1 for r in rows if r["extracted_at_b6_i0"]),
        "copied_files": sum(r["copied_files"] for r in rows),
    }
    c.need("dec/arithmetic", arith == computed, {"declared": arith, "computed": computed})
    src = c.p0("CANDIDATE_EXTRACTION_DISPOSITION_v1.0.json")["candidates"]
    expected_admitted = sum(1 for x in src
                            if x["classification"] in ADMISSIBLE and x["eligible_for_extraction"])
    c.need("dec/admitted_matches_eligibility",
           computed["admitted"] == expected_admitted
           and computed["refused"] == 27 - expected_admitted, computed)
    source = {c["id"]: c for c in
              c.p0("CANDIDATE_EXTRACTION_DISPOSITION_v1.0.json")["candidates"]}
    drifted = [r["id"] for r in rows
               if bool(r["eligibility"]) != bool(source[r["id"]]["eligible_for_extraction"])]
    c.need("dec/eligibility_matches_source", not drifted, drifted)
    limits = [r["id"] for r in rows
              if r["classification"] == "EXTRACTABLE_WITH_LIMITATION"
              and r["limitation"] in ("", "none", None)]
    c.need("dec/limitations_binding", not limits, limits)
    unproven = [r["id"] for r in rows if r["decision"] == "REFUSED" and not r["rejection_reason"]]
    c.need("dec/refusals_explained", not unproven, unproven)
    c.need("dec/operator_pending_not_ratified",
           all(r["operator_decision"] in {"PENDING_OPERATOR_REVIEW", "REFUSED"} for r in rows),
           "operator decision invented")


def check_api(c: Checker) -> None:
    d = c.data("api")
    rows = d["symbols"]
    c.need("api/rows_30", d["rows_total"] == 30 == len(rows), len(rows))
    computed = {k: sum(1 for r in rows if r["classification"] == k)
                for k in ("public_stable", "public_experimental", "internal", "private",
                          "prohibited", "deferred")}
    c.need("api/distribution", computed == d["distribution"], {"declared": d["distribution"],
                                                              "computed": computed})
    c.need("api/public_stable_zero", computed["public_stable"] == 0, computed["public_stable"])
    c.need("api/exports_zero", d["observed"]["exports"] == 0 and d["observed"]["public_stable"] == 0,
           d["observed"])
    c.need("api/historical_exports_zero", d["export_policy"]["exports_at_p0"] == 0, d["export_policy"])
    c.need("api/no_row_exported", not any(r["exported_at_b6_i0"] for r in rows), "row exported")
    c.need("api/no_wildcards", not any("*" in r["symbol"] for r in rows), "wildcard symbol")
    prohibited = [r["symbol"] for r in rows if r["classification"] == "prohibited"]
    c.need("api/prohibited_five", len(prohibited) == 5, prohibited)
    c.need("api/prohibited_not_implemented",
           all(r["observed_state"] == "NOT_IMPLEMENTED" for r in rows
               if r["classification"] == "prohibited"), "prohibited symbol implemented")
    fields = ("typed_inputs", "typed_outputs", "error_behavior", "version_introduced",
              "compatibility_promise", "documentation_obligation", "tests_planned",
              "examples_planned", "owner")
    gaps = [r["symbol"] for r in rows
            if r["classification"] == "public_experimental"
            for f in fields if r.get(f) in (None, "", [])]
    c.need("api/public_contract_fields", not gaps, gaps)
    c.need("api/principles_12", len(d["principles"]) == 12, len(d["principles"]))
    c.need("api/env_authority_absent",
           "environment_variable_authority" in d["prohibitions"], d["prohibitions"])
    c.need("api/sections_25", len({r["section"] for r in rows if r["section"] != "PROHIBITED"}) == 25,
           "section coverage")


def check_compat(c: Checker) -> None:
    d = c.data("compat")
    rows = d["compatibility_rows"]
    c.need("compat/rows_25", d["rows_total"] == 25 == len(rows), len(rows))
    c.need("compat/all_unproven", all(r["state"] == "UNPROVEN" for r in rows), "proven row appeared")
    c.need("compat/no_consumer_evidence",
           all(r["consumer_evidence"] == "none" for r in rows), "consumer evidence invented")
    c.need("compat/no_test_bound",
           all(r["discriminating_test"] is None for r in rows), "test bound without proof")
    c.need("compat/unknown_refused", d["refusal"]["unknown_version"] == "REFUSED", d["refusal"])
    c.need("compat/no_silent_latest", d["refusal"]["silent_latest"] is False, d["refusal"])
    c.need("compat/rule_names_latest", "latest" in d["refusal"]["rule"].lower(), d["refusal"]["rule"])
    c.need("compat/deprecation_declared", bool(d["deprecation"]["required_fields"]), d["deprecation"])
    c.need("compat/removal_needs_migration",
           d["removal"]["requires_migration_evidence"] is True, d["removal"])
    c.need("compat/migration_absent", d["migration_evidence"]["state"] == "ABSENT", d["migration_evidence"])
    fp = d["structural_fingerprint"]
    recomputed = hashlib.sha256(canonical(rows)).hexdigest()
    c.need("compat/fingerprint", fp["value"] == recomputed, {"declared": fp["value"],
                                                            "computed": recomputed})
    c.need("compat/vocabulary", d["conformance"]["vocabulary"] == ["PASS", "FAIL", "UNPROVEN", "REFUSED"],
           d["conformance"]["vocabulary"])
    c.need("compat/default_unproven", d["conformance"]["default_state"] == "UNPROVEN", d["conformance"])
    c.need("compat/declaration_without_test",
           d["conformance"]["declaration_without_test"] == "UNPROVEN", d["conformance"])
    c.need("compat/proven_zero", d["observed"]["proven_rows"] == 0, d["observed"])
    c.need("compat/identifiers", all(d["identifiers"].get(k) for k in
                                     ("api_version", "schema_version", "package_version_format",
                                      "conformance_version")), d["identifiers"])


def check_failures(c: Checker) -> None:
    d = c.data("failures")
    rows = d["failure_classes"]
    c.need("fail/classes_six", d["failure_classes_total"] == 6 == len(rows), len(rows))
    c.need("fail/ids", [r["id"] for r in rows] == ["F01", "F02", "F03", "F04", "F17", "F20"],
           [r["id"] for r in rows])
    gaps = [r["id"] for r in rows for k in ("trigger", "expected_refusal", "observable",
                                            "recovery", "negative_control", "bound")
            if not r.get(k)]
    c.need("fail/fields", not gaps, gaps)
    c.need("fail/proofs_bound", all(r["implemented_proof"] for r in rows),
           [r["id"] for r in rows if not r["implemented_proof"]])
    c.need("fail/no_pass_claim", all(r["proof_state"] == "BOUND_PENDING_EVIDENCE" for r in rows),
           "proof claimed")
    t = d["threats"]
    c.need("threat/seven", d["threats_total"] == 7 == len(t), len(t))
    c.need("threat/ids", [x["id"] for x in t] == ["T04", "T05", "T07", "T08", "T09", "T14", "T20"],
           [x["id"] for x in t])
    c.need("threat/controls", all(x["negative_control"] for x in t),
           [x["id"] for x in t if not x["negative_control"]])
    c.need("threat/later_locked",
           d["later_threat_state"] == "PLANNED_NOT_IMPLEMENTED" and len(d["later_threats"]) == 13,
           len(d["later_threats"]))
    c.need("threat/no_later_pulled", d["policy"]["no_later_stage_pulled_forward"] is True, d["policy"])
    c.need("fail/structural_not_text_only", d["policy"]["structural_parsing_required"] is True, d["policy"])


def check_registry(c: Checker) -> None:
    d = c.data("registry")
    rows = d["requirements"]
    c.need("reg/rows_19", d["requirements_total"] == 19 == len(rows), len(rows))
    ids = [r["id"] for r in rows]
    c.need("reg/unique_ids", len(set(ids)) == 19, "duplicate requirement")
    s = c.data("scope")
    c.need("reg/matches_scope", sorted(ids) == s["requirements"], "registry drifted from derivation")
    nodes = [r["binding_node"] for r in rows]
    c.need("reg/unique_nodes", len(set(nodes)) == 19, "duplicate binding")
    c.need("reg/one_binding_each", all(r["binding_node"].count("::") == 1 for r in rows), "malformed binding")
    c.need("reg/no_pass", d["arithmetic"]["pass_claims"] == 0
           and not any(r["state"] == "PASS" for r in rows), "PASS claim")
    c.need("reg/no_claim", all(r["claim"].startswith("NONE") for r in rows), "result claim in registry")
    module_names = {r["binding_node"].split("::")[0] for r in rows}
    missing = [m for m in module_names if not c.path(m).exists()]
    c.need("reg/modules_exist", not missing, missing)
    declared = {n for v in d["stage_proofs"].values() for n in v} | set(nodes)
    c.need("reg/inventory_equals_nodes", declared == set(d["inventory"]["nodes"]),
           sorted(declared ^ set(d["inventory"]["nodes"])))
    defined: set[str] = set()
    for module in sorted(set(d["inventory"]["modules"])):
        path = c.path(module)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        found = re.findall(r"^def (test_[a-z0-9_]+)\(", text, re.M)
        defined |= {f"{module}::{n}" for n in found}
    c.need("reg/no_orphan_tests", defined == set(d["inventory"]["nodes"]),
           sorted(defined ^ set(d["inventory"]["nodes"])))
    c.need("reg/no_b6_i1_nodes",
           not any("b6_i1" in n.lower() or "b6_i2" in n.lower() for n in d["inventory"]["nodes"]),
           "later-stage node referenced")


def check_boundary(c: Checker) -> None:
    if not (c.root / ".git").exists():
        c.ok("git/skipped_scratch_root")
        return
    code, base = git(c, ["rev-parse", "origin/main"])
    c.need("git/base", code == 0 and base == BASE_SHA, base)
    code, out = git(c, ["diff", "--name-only", f"{BASE_SHA}..HEAD"])
    changed = [x for x in out.splitlines() if x.strip()]
    outside = [p for p in changed if not p.startswith(ALLOWED_PREFIXES)]
    c.need("boundary/only_allowed_paths", not outside, outside)
    blocked = [p for p in changed if p.startswith(PROHIBITED_PREFIXES)]
    c.need("boundary/no_prohibited_surface", not blocked, blocked)
    code, p0 = git(c, ["diff", "--name-only", f"{P0_SHA}..HEAD", "--", DOCS])
    p0_changed = [x for x in p0.splitlines() if x.strip() and f"{I0}" not in x]
    c.need("boundary/p0_packet_untouched", not p0_changed, p0_changed)
    code, v = git(c, ["diff", "--name-only", f"{P0_SHA}..HEAD", "--",
                      "infrastructure/control-plane/scripts/block_06_p0_validate.py"])
    c.need("boundary/p0_validator_untouched", not v.strip(), v)
    code, status = git(c, ["status", "--porcelain"])
    c.need("boundary/tracked_clean", not status.strip(), status[:400])
    code, out = git(c, ["diff", "--check", f"{BASE_SHA}..HEAD"])
    c.need("boundary/diff_check", code == 0, out)


def _env_keys(obj, parent: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in ENV_FIELDS and parent not in ("forbidden", "forbidden_fields"):
                found.append(key)
            if key in ("forbidden", "forbidden_fields", "fields", "required"):
                continue
            found.extend(_env_keys(value, key))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_env_keys(item, parent))
    return found


def check_hygiene(c: Checker) -> None:
    texts = {k: c.text(v) for k, v in ARTIFACTS.items()}
    texts["contract_md"] = c.text(CONTRACT_MD)
    texts["ledger"] = c.text(LEDGER)
    secrets = [f"{k}:{p.pattern[:18]}" for k, t in texts.items() for p in SECRET_PATTERNS if p.search(t)]
    c.need("security/no_secrets", not secrets, secrets)
    urls = [k for k, t in texts.items() if URL_PATTERN.search(t)]
    c.need("security/no_urls", not urls, urls)
    flags = [k for k, t in texts.items() if any(f in t for f in FORBIDDEN_FLAGS)]
    c.need("governance/no_authorization_flags", not flags, flags)
    for key in ARTIFACTS:
        raw = c.path(ARTIFACTS[key]).read_bytes()
        c.need(f"text/{key}_newline", raw.endswith(b"\n"), "missing final newline")
        c.need(f"text/{key}_no_trailing_space",
               not any(line != line.rstrip() for line in raw.decode("utf-8").splitlines()),
               "trailing whitespace")
    env = [k for k, rel in ARTIFACTS.items() if _env_keys(c.data(k))]
    c.need("text/no_environment_fields", not env, env)
    abs_paths = [k for k, t in texts.items() if ABS_PATH.search(t)]
    c.need("text/no_absolute_paths", not abs_paths, abs_paths)


def check_documents(c: Checker) -> None:
    md = c.text(CONTRACT_MD)
    need = ("AUTHORIZED_STAGE=B6-I0", "B6-I0", "extraction of code", "UNPROVEN",
            "OPERATOR HOLD", "zero", "Mutation floor", "C1.S5")
    missing = [t for t in need if t not in md]
    c.need("docs/contract_content", not missing, missing)
    led = c.text(LEDGER)
    need_led = ("B6I0", "G16", "B5I8-DF05", "PASS 0", "READY_FOR_OPERATOR_REVIEW",
                "NOT MERGE AUTHORIZED")
    missing = [t for t in need_led if t not in led]
    c.need("docs/ledger_content", not missing, missing)


def check_g16(c: Checker) -> None:
    g16 = json.loads(c.path(G16_PACKET).read_text(encoding="utf-8"))
    c.need("g16/open", g16["status_value"] == "OPEN" and g16["blocker"] == "B5I8-DF05", g16)
    handoff = json.loads(c.path(HANDOFF).read_text(encoding="utf-8"))
    c.need("g16/token", handoff["authorization_token_required"] == "AUTHORIZED_STAGE=B6-I0",
           handoff["authorization_token_required"])
    c.need("g16/blocks_independence",
           "independence" in " ".join(handoff["g16"]["blocks"]), handoff["g16"])


def check_no_implementation(c: Checker) -> None:
    if not (c.root / ".git").exists():
        c.ok("impl/skipped_scratch_root")
        return
    code, out = git(c, ["diff", "--name-only", "--diff-filter=A", f"{BASE_SHA}..HEAD"])
    added = [f for f in out.splitlines() if f.strip()]
    packages = [f for f in added if f.startswith(("packages/", "dist/", "build/"))
                or f.endswith((".whl", ".egg-info", ".tar.gz"))]
    c.need("impl/no_packages", not packages, packages)
    modules = [f for f in added if f.startswith(("oce/", "infrastructure/control-plane/src/"))]
    c.need("impl/no_book6_modules", not modules, modules)
    code, files = git(c, ["ls-files"])
    c.need("impl/tracked_paths_stable", bool(files.strip()), "empty inventory")


def run(root: pathlib.Path) -> dict:
    c = Checker(root)
    for fn in (check_files, check_canonical, check_containment, check_manifest, check_scope, check_contract,
               check_decisions, check_api, check_compat, check_failures, check_registry,
               check_boundary, check_hygiene, check_documents, check_g16,
               check_no_implementation):
        fn(c)
    payload = {
        "validator": "block_06_i0_validate.py",
        "status": "PASS" if not c.failures else "FAIL",
        "checks": len(c.checks),
        "failures": len(c.failures),
        "failure_detail": c.failures,
        "stage": "AUTHORIZED_STAGE=B6-I0",
        "base_sha": BASE_SHA,
        "root": "." if root == repo_root() else "<scratch>",
    }
    return payload


def repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    root = pathlib.Path(args.root).resolve() if args.root else repo_root()
    payload = run(root)
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.json:
        pathlib.Path(args.json).write_text(text, encoding="utf-8", newline="\n")
    print(f"status {payload['status']}")
    print(f"checks {payload['checks']} | failures {payload['failures']}")
    for f in payload["failure_detail"]:
        print(f"FAIL {f['check']}: {f['detail']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
