#!/usr/bin/env python3
"""B6-I2 deterministic P0 artifact generator (stdlib only, no timestamps, no host identity)."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess

DOCS = "docs/oce-golden-system"
P = "OCE_BLOCK_06_I2_"
BASE = "4496d548078660efd7ad4f93e7fff461d34ea538"
BASE_TREE = "c6638bde3e9c8f71482f4d96fde42d0484d9a624"
I1_HEAD = "96e3b81714321f4eea7abcb300ef471e93be0962"
I0_HEAD = "c5d7bfcc5ea99837985ba82a3c91fd1e76d85a81"
TESTS = "infrastructure/control-plane/tests"
SCRIPTS = "infrastructure/control-plane/scripts"
WF = ".github/workflows"
MODULES = (
    "test_block_06_i2_contract.py",
    "test_block_06_i2_templates.py",
    "test_block_06_i2_archive_safety.py",
    "test_block_06_i2_harness.py",
    "test_block_06_i2_determinism_and_compat.py",
    "test_block_06_i2_evidence_and_cleanup.py",
)
NODES = (
    "test_block_06_i2_contract.py::test_inventory_equals_collection",
    "test_block_06_i2_contract.py::test_contract_frozen_before_results",
    "test_block_06_i2_contract.py::test_scope_binds_construction_sequence",
    "test_block_06_i2_contract.py::test_locks_and_cost",
    "test_block_06_i2_contract.py::test_allowed_and_forbidden_paths_declared",
    "test_block_06_i2_templates.py::test_generated_app_starts_locally",
    "test_block_06_i2_templates.py::test_template_declares_inherited_versions",
    "test_block_06_i2_templates.py::test_deterministic_build_byte_identical",
    "test_block_06_i2_templates.py::test_invalid_manifest_refused",
    "test_block_06_i2_templates.py::test_template_readme_present",
    "test_block_06_i2_templates.py::test_cloud_dependency_declared_absent",
    "test_block_06_i2_archive_safety.py::test_path_traversal_refused",
    "test_block_06_i2_archive_safety.py::test_symlink_escape_refused",
    "test_block_06_i2_archive_safety.py::test_malformed_archive_refused",
    "test_block_06_i2_archive_safety.py::test_absolute_entry_refused",
    "test_block_06_i2_archive_safety.py::test_oversized_archive_refused",
    "test_block_06_i2_archive_safety.py::test_digest_mismatch_refused",
    "test_block_06_i2_harness.py::test_up_returns_endpoint_set",
    "test_block_06_i2_harness.py::test_missing_service_refused",
    "test_block_06_i2_harness.py::test_unknown_profile_refused",
    "test_block_06_i2_harness.py::test_undeclared_network_call_refused",
    "test_block_06_i2_harness.py::test_evidence_capture_deterministic",
    "test_block_06_i2_harness.py::test_environment_fingerprint_stable",
    "test_block_06_i2_determinism_and_compat.py::test_no_silent_latest",
    "test_block_06_i2_determinism_and_compat.py::test_compat_rows_remain_unproven",
    "test_block_06_i2_determinism_and_compat.py::test_private_symbol_not_stable",
    "test_block_06_i2_determinism_and_compat.py::test_dirty_build_input_refused",
    "test_block_06_i2_evidence_and_cleanup.py::test_manifest_hashes_recompute",
    "test_block_06_i2_evidence_and_cleanup.py::test_cleanup_no_scratch_residue",
    "test_block_06_i2_evidence_and_cleanup.py::test_prior_stage_artifacts_unchanged",
)
ALLOWED = [
    "oce/templates/", "oce/harness/",
    f"{DOCS}/{P}", f"{SCRIPTS}/block_06_i2_",
    f"{TESTS}/test_block_06_i2_", f"{TESTS}/stage_scope/",
    f"{WF}/block-06-i2-validation.yml", f"{WF}/block-06-i2-paired-comparison.yml",
    "infrastructure/control-plane/scripts/block_06_stage_scope.py",
    "infrastructure/control-plane/scripts/block_06_i0_validate.py",
    "infrastructure/control-plane/scripts/block_06_i1_validate.py",
    "infrastructure/control-plane/tests/block_06_i1_support.py",
    "infrastructure/control-plane/tests/test_block_06_i1_authority_and_boundary.py",
    f"{DOCS}/OCE_BLOCK_06_I0_STAGE_SCOPE_AMENDMENT_001_v1.0.json",
]
FORBIDDEN = [
    "packages/", "dist/", "build/", "pyproject.toml", "package.json", "uv.lock", "poetry.lock",
    "infrastructure/control-plane/src/", "infrastructure/console/src/",
    f"{DOCS}/OCE_BLOCK_06_P0_", f"{DOCS}/OCE_BLOCK_06_I0_", f"{DOCS}/OCE_BLOCK_06_I1_",
    f"{WF}/b1-i1r-validation.yml", f"{WF}/b5-i8-audit-validation.yml",
    f"{WF}/b5-i9-factory-gate-validation.yml", f"{WF}/block-06-i0-validation.yml",
    "cloud/", "deploy/", "terraform/", "k8s/",
]
SERVICES = ("app", "db", "queue", "evidence")
PROFILES = {"local": {"services": list(SERVICES), "network": False, "cloud": False},
            "minimal": {"services": ["app"], "network": False, "cloud": False}}
REFUSALS = (
    ("REFUSED_PATH_TRAVERSAL", "F13", "entry escapes the root"),
    ("REFUSED_SYMLINK_ESCAPE", "F14", "link resolves outside the root"),
    ("REFUSED_NONDETERMINISTIC_BUILD", "F15", "two builds differ"),
    ("REFUSED_NETWORK", "F16", "undeclared network call"),
    ("REFUSED_DIRTY_INPUT", "F19", "unclean build input"),
    ("REFUSED_MALFORMED_ARCHIVE", "F21", "archive cannot be parsed safely"),
    ("REFUSED_ABSOLUTE_ENTRY", "F13", "absolute entry path"),
    ("REFUSED_OVERSIZE", "T15", "payload over the declared bound"),
    ("REFUSED_DIGEST", "T06", "digest mismatch"),
    ("REFUSED_UNKNOWN_PROFILE", "F16", "profile not declared"),
    ("REFUSED_MISSING_SERVICE", "F16", "declared service missing"),
    ("REFUSED_INVALID_MANIFEST", "F21", "manifest invalid"),
    ("REFUSED_LATER_STAGE", "T19", "B6-I3 through B6-I9 remain locked"),
    ("REFUSED_CLOUD", "T19", "cloud is not authorized"),
)


def canon(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def scope() -> dict:
    return {
        "schema": "oce.block_06_i2.scope.v1", "document_id": "OCE-B6-I2-SCOPE-001",
        "stage": "B6-I2", "purpose": "C1 templates and local harness",
        "sections": ["C1.S3", "C1.S4"], "implementation_surfaces": ["templates", "harness"],
        "outputs": ["template", "harness"], "base_sha": BASE, "base_tree": BASE_TREE,
        "authority_sources": [
            f"{DOCS}/OCE_BLOCK_06_P0_CONSTRUCTION_SEQUENCE_v1.0.json#B6-I2",
            f"{DOCS}/OCE_BLOCK_06_P0_CONSTRUCTION_PLAN_v1.0.md#B6-I2",
            f"{DOCS}/OCE_BLOCK_06_REUSABLE_PLATFORM_SURFACES_PLAN_v1.0.md#B6.C1.S3",
            f"{DOCS}/OCE_BLOCK_06_REUSABLE_PLATFORM_SURFACES_PLAN_v1.0.md#B6.C1.S4",
            f"{DOCS}/OCE_BLOCK_06_P0_REQUIREMENT_TEST_REGISTRY_v1.0.json#B6-P0-SEC-03",
            f"{DOCS}/OCE_BLOCK_06_P0_REQUIREMENT_TEST_REGISTRY_v1.0.json#B6-P0-SEC-04",
        ],
        "requirements": ["B6-P0-SEC-03", "B6-P0-SEC-04"],
        "api_symbols": ["template:oce-app-skeleton", "oce.harness.local.up"],
        "compatibility_rows": ["C1.S3", "C1.S4"],
        "failure_classes": ["F13", "F14", "F15", "F16", "F19", "F21"],
        "threats": ["T01", "T02", "T03", "T06", "T10", "T11", "T12", "T13", "T15", "T16",
                    "T17", "T18", "T19"],
        "provenance_obligations": [
            "template manifest binds sha256 and byte size of every emitted file",
            "generated app declares inherited API, schema and harness versions",
            "harness endpoint set is deterministic and carries an environment fingerprint",
            "evidence capture is canonical JSON with no timestamp, host or user identity",
            "archive install verifies digest before any entry is written",
            "prior stage artifacts remain byte-identical and are never re-hashed as new",
        ],
        "test_categories": ["contract", "generated app start", "archive safety", "harness",
                            "determinism and compatibility", "evidence and cleanup"],
        "mutation_floor": {"source": 3, "stage": 6},
        "minimum_nodes": len(NODES),
        "common_regression_floor": 208,
        "exit_gate": "fresh generated app starts locally",
        "stop_conditions": ["stop if cloud is required"],
        "non_goals": ["cloud dependency"],
        "adjacent_floors": {"b6_i0_nodes": 72, "b6_i1_nodes": 42, "b5_i9_nodes": 41,
                            "common_regression_nodes": 208},
        "locks": {"B6-I3": "LOCKED", "B6-I4": "LOCKED", "B6-I5": "LOCKED", "B6-I6": "LOCKED",
                  "B6-I7": "LOCKED", "B6-I8": "LOCKED", "B6-I9": "LOCKED",
                  "BOOK_6_COMPLETE": False, "G16": "OPEN", "G16_OWNER": "B5I8-DF05",
                  "MERGE_AUTHORIZED": False, "RATIFICATION_AUTHORIZED": False,
                  "evaluation_system": "RESERVED_NOT_AUTHORIZED", "cloud_hosting": "NOT_AUTHORIZED",
                  "package_publication": "NOT_AUTHORIZED"},
        "cost_usd": 0, "capital_authority": "none",
    }


def contract() -> dict:
    return {
        "schema": "oce.block_06_i2.contract.v1", "document_id": "OCE-B6-I2-CONTRACT-001",
        "stage": "B6-I2", "status": "FROZEN", "frozen_before_results": True,
        "base_sha": BASE, "base_tree": BASE_TREE, "i0_ratification_sha": I0_HEAD,
        "i1_ratification_sha": I1_HEAD,
        "implementation_floor": {"test_nodes": len(NODES), "mutations": 6,
                                 "source_mutation_floor": 3},
        "test_inventory": {"modules": [f"{TESTS}/{m}" for m in MODULES],
                           "nodes": list(NODES), "node_total": len(NODES),
                           "collection_equals_execution": True,
                           "zero": ["failures", "errors", "skipped", "xfail"]},
        "requirements": ["B6-P0-SEC-03", "B6-P0-SEC-04"],
        "api_symbols": ["template:oce-app-skeleton", "oce.harness.local.up"],
        "api_rules": {"template": {"classification": "deferred", "exported": False,
                                   "compatibility": "not_published",
                                   "error_behavior": "refuse_invalid_manifest"},
                      "harness": {"classification": "public_experimental", "exported": True,
                                  "compatibility": "additive_minor",
                                  "error_behavior": "refuse_missing_service",
                                  "typed_inputs": ["profile"], "typed_outputs": ["endpoint_set"]}},
        "compatibility": {"rows": ["C1.S3", "C1.S4"], "state": "UNPROVEN",
                          "unknown_refused": True, "silent_latest": False,
                          "consumer_evidence": "none"},
        "provenance": {"manifest": "sha256 plus byte size over LF-normalised bytes",
                       "app_declares_inherited_versions": True,
                       "evidence_canonical": True, "no_timestamp_or_host_identity": True},
        "determinism": {"canonical_json": True, "sorted_entries": True, "no_timestamps": True,
                        "no_random_ids": True, "byte_identical_rebuild": True},
        "template": {"archive": "safe tar with traversal, symlink, absolute, malformed, oversize "
                                "and digest refusals",
                     "emitted": ["app.json", "README.md", "migrations/0001_init.sql",
                                 "tests/test_app.py", "telemetry.json", "deploy.json"],
                     "cloud_dependency": False,
                     "start": "in-process validation of manifest, migrations, tests, telemetry "
                              "and deployment declaration; no socket and no network"},
        "harness": {"profiles": PROFILES, "services": list(SERVICES), "opens_sockets": False,
                    "refuses_undeclared_network_calls": True,
                    "endpoint_set": "logical local endpoints plus environment fingerprint"},
        "refusals": [{"code": c, "class": f, "meaning": m} for c, f, m in REFUSALS],
        "bounds": {"archive_bytes": 1048576, "entry_bytes": 262144, "entries": 256,
                   "input_bytes": 65536},
        "cleanup": {"scratch_prefix": ".b6i2-", "residue_refused": True},
        "paired_comparison": {"base_sha": BASE, "common_floor": 208,
                              "head_only_expected": len(NODES), "base_only_expected": 0},
        "adjacent_floors": {"b5_i9_nodes": 41, "b6_i0_nodes": 72, "b6_i1_nodes": 42,
                            "common_regression_nodes": 208},
        "locks": {"B6-I3_through_I9": "LOCKED", "MERGE_AUTHORIZED": False,
                  "RATIFICATION_AUTHORIZED": False, "BOOK_6_COMPLETE": False,
                  "G16": "OPEN", "evaluation_system": "RESERVED_NOT_AUTHORIZED",
                  "cloud_hosting": "NOT_AUTHORIZED", "package_publication": "NOT_AUTHORIZED"},
        "cost_usd": 0, "capital_authority": "none",
    }


def registry() -> dict:
    rows = []
    for i, node in enumerate(NODES, start=1):
        rows.append({"id": f"B6I2-{i:02d}", "binding_node": node, "state": "PLANNED",
                     "claim": "NONE until evidence", "category": node.split("::")[0]})
    return {"schema": "oce.block_06_i2.registry.v1", "document_id": "OCE-B6-I2-REGISTRY-001",
            "stage": "B6-I2", "requirements_total": len(rows), "requirements": rows,
            "inventory": {"modules": [f"{TESTS}/{m}" for m in MODULES], "nodes": list(NODES)},
            "arithmetic": {"pass_claims": 0}}



def api_contract() -> dict:
    return {"schema": "oce.block_06_i2.api.v1", "document_id": "OCE-B6-I2-API-001",
            "stage": "B6-I2", "status": "FROZEN",
            "symbols": [
                {"symbol": "template:oce-app-skeleton", "section": "C1.S3",
                 "classification": "deferred", "exported": False,
                 "compatibility": "not_published", "version": "B6-I2",
                 "error_behavior": "refuse_invalid_manifest",
                 "documentation": "template README", "example": "generated app",
                 "tests": "generated app starts"},
                {"symbol": "oce.harness.local.up", "section": "C1.S4",
                 "classification": "public_experimental", "exported": True,
                 "compatibility": "additive_minor", "version": "B6-I2",
                 "typed_inputs": ["profile"], "typed_outputs": ["endpoint_set"],
                 "error_behavior": "refuse_missing_service",
                 "documentation": "harness README", "example": "one profile",
                 "tests": "fresh-machine path"},
            ],
            "prohibitions": ["no wildcard scope", "no stable private symbol",
                             "no silent latest", "no client supplied authority",
                             "no socket opened by the harness", "no cloud dependency"]}


def compat() -> dict:
    return {"schema": "oce.block_06_i2.compat.v1", "document_id": "OCE-B6-I2-COMPAT-001",
            "stage": "B6-I2", "window": {"from": "v1", "to": "v1"},
            "rows": [
                {"surface": "C1.S3", "state": "UNPROVEN", "supported_from": "UNPROVEN",
                 "supported_to": "UNPROVEN", "consumer_evidence": "none",
                 "discriminating_test": None},
                {"surface": "C1.S4", "state": "UNPROVEN", "supported_from": "UNPROVEN",
                 "supported_to": "UNPROVEN", "consumer_evidence": "none",
                 "discriminating_test": None},
            ],
            "rows_total": 2,
            "observed": {"proven_rows": 0},
            "refusal": {"unknown_version": "REFUSED", "silent_latest": False,
                        "rule": "an unknown version is refused; latest is never assumed"},
            "conformance": {"vocabulary": ["PASS", "FAIL", "UNPROVEN", "REFUSED"],
                            "default_state": "UNPROVEN",
                            "declaration_without_test": "UNPROVEN"}}


def failures() -> dict:
    classes = [
        ("F13", "path_traversal", "an archive entry escapes the root", "extraction refused",
         "entry named", "REFUSED_PATH_TRAVERSAL"),
        ("F14", "symlink_escape", "a symlink points outside the root", "extraction refused",
         "link named", "REFUSED_SYMLINK_ESCAPE"),
        ("F15", "nondeterministic_build", "two builds differ byte-wise", "build refused",
         "differing files listed", "REFUSED_NONDETERMINISTIC_BUILD"),
        ("F16", "hidden_network_call", "a unit performs an undeclared network call",
         "run refused", "call site named", "REFUSED_NETWORK"),
        ("F19", "dirty_build_input", "a build uses an unclean or untracked input",
         "build refused", "input listed", "REFUSED_DIRTY_INPUT"),
        ("F21", "malformed_archive", "an archive cannot be parsed safely", "install refused",
         "format error shown", "REFUSED_MALFORMED_ARCHIVE"),
    ]
    rows = [{"id": i, "name": n, "stage": "B6-I2", "trigger": t, "expected_refusal": r,
             "observable": o, "refusal_code": c, "recovery": "cause removed and rerun",
             "negative_control": f"plant the {n} condition and require {i} refusal",
             "proof_state": "BOUND_PENDING_EVIDENCE"} for i, n, t, r, o, c in classes]
    threats = [
        ("T01", "path traversal", "crafted archive entry", "filesystem", "reject entry"),
        ("T02", "symlink escape", "crafted symlink", "filesystem", "reject link"),
        ("T03", "malicious archive contents", "hostile archive", "build host", "reject archive"),
        ("T06", "package substitution", "serving a different artifact", "artifact identity",
         "refuse on digest mismatch"),
        ("T10", "unsafe deserialization", "hostile payload", "runtime", "refuse untyped decode"),
        ("T11", "dynamic imports", "import by attacker string", "runtime",
         "refuse undeclared import"),
        ("T12", "plugin injection", "unregistered plugin", "runtime",
         "refuse uncertified plugin"),
        ("T13", "arbitrary code execution", "executed payload", "host", "refuse execution surface"),
        ("T15", "unbounded inputs", "oversized payload", "resources", "refuse over limit"),
        ("T16", "denial of service", "resource exhaustion", "availability", "bound and quarantine"),
        ("T17", "nondeterministic outputs", "unstable ordering or clock", "evidence",
         "refuse differing rebuild"),
        ("T18", "stale compatibility metadata", "outdated matrix", "compatibility",
         "refuse unsupported claim"),
        ("T19", "unauthorized publication", "publish without hold release", "release",
         "refuse publication"),
    ]
    trows = [{"id": i, "threat": n, "attacker_capability": a, "asset": asset,
              "required_refusal": r, "stage": "B6-I2",
              "owner": "operator" if i == "T19" else "builder",
              "mitigation_state": "PLANNED_NOT_IMPLEMENTED",
              "planned_proof": f"{i} adversarial fixture refused by the named boundary check"}
             for i, n, a, asset, r in threats]
    return {"schema": "oce.block_06_i2.failures.v1", "document_id": "OCE-B6-I2-FAIL-001",
            "stage": "B6-I2", "failure_classes_total": len(rows), "failure_classes": rows,
            "threats_total": len(trows), "threats": trows,
            "policy": {"no_later_stage_pulled_forward": True,
                       "structural_parsing_required": True, "cloud_refused": True}}


def correction() -> dict:
    return {
        "schema": "oce.block_06.correction.v1",
        "document_id": "OCE-B6-I1-ACCOUNTING-CORRECTION-001",
        "stage": "B6-I2",
        "status": "SUPERSEDING_CORRECTION",
        "applies_to": ["B6-I0 mutation accounting",
                       "B6-I0-STAGE-SCOPE-AMENDMENT-001 revision 2"],
        "append_only": True,
        "rewrites_history": False,
        "findings": [
            {"id": "C-01", "question": "what '13 restored' counts",
             "records": ["B6-I0 mutation battery payload", "B6-I0 evidence 42648199671"],
             "finding": ("the mutation population is 13 rows: twelve governed JSON mutations "
                         "M01..M12 plus one POSIX-only symlink probe M13. 'restored' sums rows "
                         "whose bytes returned to their pre-mutation digest; it is not a count "
                         "of restoration events and not a pristine rerun."),
             "classification": "BOOKKEEPING_WORDING",
             "correction": ("state the population as 13 rows with floor 12, and state that M13 "
                            "did not produce its named check in Linux CI because the validator "
                            "raised on the symlinked scope artifact before reporting "
                            "boundary/no_symlinked_artifacts; the battery passed because the "
                            "floor is 12 and every row restored."),
             "severity": "record clarity only; no floor was lowered and no mutation was added"},
            {"id": "C-02", "question": "did the amendment allowlist change across revisions",
             "records": ["OCE_BLOCK_06_I0_STAGE_SCOPE_AMENDMENT_001_v1.0.json"],
             "finding": ("revision 2 added "
                         "infrastructure/control-plane/tests/test_block_06_i0_book5_regression.py "
                         "to authorized_paths, which is the same list the resolver pins as "
                         "AMENDMENT_PATHS and admits as authority; revision 1 also renamed an "
                         "entry. The 'surface list' is therefore the authority allowlist, not a "
                         "separate test inventory, and the revision note claiming no allowlist "
                         "entry changed is inaccurate."),
             "classification": "AUTHORITATIVE_RECORD_DEFECT",
             "correction": ("read revision 1 as a rename and revision 2 as an addition of one "
                            "admitted path; the pinned set is exactly the nine committed paths, "
                            "and no validation law, floor or lock changed in either revision."),
             "severity": "no authority was exercised beyond the pinned set; the record is corrected"},
        ],
        "authoritative_mutation_population": {
            "governed_json_mutations": 12, "posix_symlink_probe": 1, "rows_total": 13,
            "floor": 12, "discriminated_linux": 12, "restored": 13,
            "pristine_rerun_counts_as_mutation": False,
            "i1_battery_is_separate": {"rows": 6, "floor": 6, "discriminated": 6,
                                       "restored": 6}},
        "locks": {"B6-I3_through_I9": "LOCKED", "MERGE_AUTHORIZED": False,
                  "RATIFICATION_AUTHORIZED": False, "cost_usd": 0,
                  "capital_authority": "none"},
    }


def registration() -> dict:
    return {
        "schema": "oce.block_06.stage_scope_registration.v1",
        "document_id": "OCE-B6-I2-STAGE-SCOPE-REGISTRATION-001",
        "status": "FROZEN",
        "frozen_before_results": True,
        "registers": "B6-I2",
        "prior_stages": {
            "B6-I0": {"head": I0_HEAD, "base": "5e76dc12207bf1674ff7ccd94aed0f36b12dd3e6"},
            "B6-I1": {"head": I1_HEAD, "base": "6783bf7638f5ecd4e42ec2eb8141d1aa57dfaa3e"},
        },
        "this_stage": {"id": "B6-I2", "base": BASE, "base_tree": BASE_TREE,
                       "contract": f"{DOCS}/{P}IMPLEMENTATION_CONTRACT_v1.0.json",
                       "scope": f"{DOCS}/{P}SCOPE_DERIVATION_v1.0.json",
                       "allowed_prefixes": ALLOWED},
        "refusals": ["stage/identity_missing", "stage/identity_unknown",
                     "stage/identity_spoofed", "stage/identity_tampered",
                     "stage/base_moved", "stage/later_stage_absent",
                     "stage/branch_spoof", "stage/contract_absent"],
        "locks": {"B6-I3": "LOCKED", "B6-I4": "LOCKED", "B6-I5": "LOCKED",
                  "B6-I6": "LOCKED", "B6-I7": "LOCKED", "B6-I8": "LOCKED",
                  "B6-I9": "LOCKED", "MERGE_AUTHORIZED": False,
                  "RATIFICATION_AUTHORIZED": False, "cost_usd": 0,
                  "capital_authority": "none"},
    }


def proof_closure() -> dict:
    return {
        "schema": "oce.block_06_i2.proof_closure_amendment.v1",
        "document_id": "OCE-B6-I2-PROOF-CLOSURE-AMENDMENT-001",
        "amendment_id": "B6-I2-PROOF-CLOSURE-AMENDMENT-001",
        "stage": "B6-I2",
        "status": "FROZEN",
        "frozen_before_results": True,
        "frozen_at_head": "e082609e916f6b5213ae213e9686524701ff0238",
        "authority": [
            "operator mission B6-I2-RATIFICATION / B6-I2-PROOF-CLOSURE",
            "docs/oce-golden-system/OCE_BLOCK_06_P0_CONSTRUCTION_SEQUENCE_v1.0.json#B6-I2",
            "docs/oce-golden-system/OCE_BLOCK_06_REUSABLE_PLATFORM_SURFACES_PLAN_v1.0.md#B6.C1.S3",
            "docs/oce-golden-system/OCE_BLOCK_06_REUSABLE_PLATFORM_SURFACES_PLAN_v1.0.md#B6.C1.S4",
        ],
        "supersedes": [
            {"clause": "IMPLEMENTATION_CONTRACT_v1.0.template.start",
             "frozen_text": "in-process validation of manifest, migrations, tests, telemetry and deployment declaration; no socket and no network",
             "effective": "subprocess execution of the generated app/__main__.py entrypoint with readiness, bounded timeout, orderly stop and exit 0; no socket and no network",
             "reason": "B6.C1.S3 requires that the generated app starts cleanly; file inspection is not a start and the generated README already documented an entrypoint that did not exist"},
            {"clause": "ACCOUNTING_CORRECTION_v1.0.authoritative_mutation_population",
             "frozen_text": "13 rows with floor 12 and M13 counted as a row of the population",
             "effective": "12 governed JSON mutations M01..M12 with floor 12; M13 is a POSIX environmental probe excluded from mutation arithmetic",
             "reason": "M13 never produced its named check in Linux CI; a row that cannot discriminate cannot sit inside a claimed mutation population"},
        ],
        "defects": [
            {"id": "PC-01", "class": "EXIT_GATE_UNPROVEN",
             "finding": "the generated skeleton had no runnable entrypoint and start() only verified that files existed, while the README and the exit gate claimed the app starts locally",
             "repair": "emit app/__init__.py and app/__main__.py, execute them in a subprocess, observe READY, send stop, require STOPPED and exit 0 within a bounded timeout, run twice and scan the entrypoint for network modules"},
            {"id": "PC-02", "class": "VACUOUS_MUTATION_ROW",
             "finding": "M13 replaced a packet artifact with a symlink, but a content/digest check aborted the validator before boundary/no_symlinked_artifacts was reported, so the named discriminator never fired",
             "repair": "reclassify M13 as a POSIX environmental probe outside the governed population, keep the frozen floor of 12, and carry the POSIX symlink refusal proof on the B6-I2 archive surface where the refusal is emitted by the archive installer itself"},
            {"id": "PC-03", "class": "PRIOR_STAGE_TEST_ADAPTATION",
             "finding": "two prior-stage test files were edited to admit B6-I2 paths at the B6-I2 head",
             "repair": "restore both files byte-identical to the B6-I1 merge and execute the prior suites at the prior ratified head in a detached worktree with origin/main rewound to the B6-I0 merge"},
            {"id": "PC-04", "class": "COMPATIBILITY_UNDISPOSITIONED",
             "finding": "C1.S3 and C1.S4 were declared UNPROVEN without a disposition or owner",
             "repair": "record UNPROVEN_BUT_EXIT_GATE_ALLOWS with named owners; the exit gate proves a local start, not a published compatibility window"},
        ],
        "m13": {
            "disposition": "POSIX_ENVIRONMENTAL_PROBE",
            "governed_ids": [f"M{i:02d}" for i in range(1, 13)],
            "governed_rows": 12,
            "probe_rows": 1,
            "rows_total": 13,
            "floor": 12,
            "governed_discriminated_linux": 12,
            "probe_discriminated_linux": False,
            "earlier_check": "packet/canonical/OCE_BLOCK_06_I0_SCOPE_DERIVATION_v1.0.json",
            "named_check": "boundary/no_symlinked_artifacts",
            "precedence_required": "a symlink refusal must precede content, canonical or digest checks on the same artifact",
            "separate_proof": "test_block_06_i2_archive_safety.py::test_symlink_escape_refused",
            "claims_corrected": [
                "the governed mutation population is 12, not 13",
                "13 restored counts all 13 physical rows including the probe",
                "the battery passes on the frozen floor of 12 governed discriminations",
            ],
        },
        "local_start": {
            "mode": "SUBPROCESS_START_WITH_READINESS",
            "evidence_node": "test_block_06_i2_templates.py::test_generated_app_starts_locally",
            "fresh_empty_directory": True,
            "dependency_free": True,
            "entrypoint": "app/__main__.py",
            "readiness": "READY app",
            "shutdown": "STOPPED",
            "timeout_seconds": 15,
            "exit_code": 0,
            "network": False,
            "second_run": True,
            "dirty_destination_refused": True,
        },
        "compatibility": {
            "C1.S3": {"disposition": "UNPROVEN_BUT_EXIT_GATE_ALLOWS", "owner": "B6-I7",
                      "reason": "the local start is the stage exit gate; a published v1 compatibility window belongs to the conformance kit"},
            "C1.S4": {"disposition": "UNPROVEN_BUT_EXIT_GATE_ALLOWS", "owner": "B6-I7",
                      "reason": "the local harness is exercised in-process; a fresh-machine consumer window is not part of this exit gate"},
        },
        "prior_stage_preservation": {
            "restored_byte_identical": [
                "infrastructure/control-plane/tests/test_block_06_i0_stage_contract.py",
                "infrastructure/control-plane/tests/test_block_06_i1_authority_and_boundary.py",
            ],
            "stage_aware_proof_tooling": [
                "infrastructure/control-plane/scripts/block_06_stage_scope.py",
                "infrastructure/control-plane/scripts/block_06_i0_validate.py",
                "infrastructure/control-plane/scripts/block_06_i1_validate.py",
                "infrastructure/control-plane/tests/stage_scope/test_i0_stage_scope_amendment_controls.py",
                ".github/workflows/block-06-i1-validation.yml",
            ],
            "replay_head": "96e3b81714321f4eea7abcb300ef471e93be0962",
            "replay_origin_main": "6783bf7638f5ecd4e42ec2eb8141d1aa57dfaa3e",
            "replay_rule": "the prior suites run in a detached worktree at the prior head with origin/main rewound to the prior merge; strict B6-I0 mode is additionally exercised directly",
        },
        "authority_sets": {
            "i0": [],
            "i0_merge": "6783bf7638f5ecd4e42ec2eb8141d1aa57dfaa3e",
            "i1_merge": "4496d548078660efd7ad4f93e7fff461d34ea538",
            "i1": "exact B6-I1 allowed_paths plus the pinned B6-I0 amendment surfaces; no oce/templates or oce/harness",
            "i2_added": ["oce/templates/", "oce/harness/"],
            "future_stage_leak": False,
        },
        "floors": {"test_nodes": 30, "stage_mutations": 6, "i0_governed_mutations": 12,
                   "common_regression_nodes": 208},
        "paired_endpoint_rule": "base 4496d548, head the final governed implementation head; common >= 208, base-only 0, head-only 30, zero common regressions",
        "cleanup": {"scratch_prefix": ".b6i2-", "residue_refused": True},
        "rollback": "revert this amendment and every descendant repair commit; the frozen packet and the B6-I1 merge are unaffected",
        "locks": {"B6-I3_through_I9": "LOCKED", "BOOK_6_COMPLETE": False, "G16": "OPEN",
                  "package_publication": "NOT_AUTHORIZED",
                  "evaluation_system": "RESERVED_NOT_AUTHORIZED",
                  "cloud_hosting": "NOT_AUTHORIZED", "MERGE_AUTHORIZED": False,
                  "cost_usd": 0, "capital_authority": "none"},
    }


ARTIFACT_BUILDERS = {
    f"{P}SCOPE_DERIVATION_v1.0.json": scope,
    f"{P}IMPLEMENTATION_CONTRACT_v1.0.json": contract,
    f"{P}API_TEMPLATE_AND_HARNESS_CONTRACT_v1.0.json": api_contract,
    f"{P}COMPATIBILITY_MATRIX_v1.0.json": compat,
    f"{P}REQUIREMENT_TEST_REGISTRY_v1.0.json": registry,
    f"{P}FAILURE_AND_THREAT_PROOFS_v1.0.json": failures,
    f"{P}ACCOUNTING_CORRECTION_v1.0.json": correction,
    f"{P}STAGE_SCOPE_REGISTRATION_v1.0.json": registration,
    f"{P}PROOF_CLOSURE_AMENDMENT_v1.0.json": proof_closure,
}

CODE_PATHS = ("oce/templates/__init__.py", "oce/templates/refusals.py",
              "oce/templates/archive.py", "oce/templates/skeleton.py",
              "oce/harness/__init__.py", "oce/harness/evidence.py",
              "oce/harness/local.py")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DOCS)
    ap.add_argument("--head", default=None)
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, builder in ARTIFACT_BUILDERS.items():
        raw = canon(builder())
        path = out / name
        path.write_bytes(raw)
        rows.append({"path": str(path).replace("\\", "/"),
                     "sha256": hashlib.sha256(raw).hexdigest(),
                     "bytes": len(raw)})
    code = []
    for rel in CODE_PATHS:
        if args.head:
            proc = subprocess.run(["git", "show", f"{args.head}:{rel}"],
                                  capture_output=True)
            data = proc.stdout if proc.returncode == 0 else None
        else:
            path = pathlib.Path(rel)
            data = path.read_bytes() if path.is_file() else None
        if data is not None:
            code.append({"path": rel,
                         "sha256": hashlib.sha256(data).hexdigest(),
                         "bytes": len(data)})
    manifest = {
        "schema": "oce.block_06_i2.manifest.v1",
        "document_id": "OCE-B6-I2-MANIFEST-001",
        "stage": "B6-I2", "status": "FROZEN", "hash": "sha256", "size": "bytes",
        "base_sha": BASE, "artifacts": rows, "code": code,
        "totals": {"artifacts": len(rows), "code": len(code)},
        "verification": {"independent": True, "excludes_manifest": True},
        "locks": {"B6-I3_through_I9": "LOCKED", "MERGE_AUTHORIZED": False,
                  "RATIFICATION_AUTHORIZED": False, "cost_usd": 0,
                  "capital_authority": "none"},
    }
    (out / f"{P}MANIFEST_v1.0.json").write_bytes(canon(manifest))
    print(json.dumps({"artifacts": len(rows), "code": len(code)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
