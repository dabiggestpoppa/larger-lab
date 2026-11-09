#!/usr/bin/env python3
"""Book 6 B6-I0 packet generator.

Deterministic, offline, standard library only. It derives every B6-I0 artifact from the
committed P0 sources plus the frozen stage decisions in this file, and writes canonical
bytes (sorted keys, two-space indent, LF, final newline). Running it twice from clean
checkouts must produce identical bytes.

Usage:
  python infrastructure/control-plane/scripts/block_06_i0_generate.py
  python infrastructure/control-plane/scripts/block_06_i0_generate.py --out <scratch-dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

DOCS = "docs/oce-golden-system"
I0 = "OCE_BLOCK_06_I0_"
P0 = "OCE_BLOCK_06_P0_"
BASE_SHA = "5e76dc12207bf1674ff7ccd94aed0f36b12dd3e6"
BASE_TREE = "34fef9633a2fe496ed2bef352858b3994b91b4e2"
P0_SHA = "e2aa8ac71dc9f0de4287fbcaa8a17ff127d5356f"
P0_TREE = "34fef9633a2fe496ed2bef352858b3994b91b4e2"
CONTRACT_FLOOR = 12
SOURCE_FLOOR = 0

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

MODULES = {
    "stage": "infrastructure/control-plane/tests/test_block_06_i0_stage_contract.py",
    "decisions": "infrastructure/control-plane/tests/test_block_06_i0_decisions_and_api.py",
    "compat": "infrastructure/control-plane/tests/test_block_06_i0_compat_and_failures.py",
    "authority": "infrastructure/control-plane/tests/test_block_06_i0_authority_and_boundary.py",
    "regression": "infrastructure/control-plane/tests/test_block_06_i0_book5_regression.py",
    "repro": "infrastructure/control-plane/tests/test_block_06_i0_reproducibility_and_ci.py",
}

NODES = {
    "stage": [
        "test_contract_frozen_before_evidence",
        "test_scope_bindings_match_p0_sources",
        "test_requirement_inventory_19",
        "test_g16_open_and_blocker",
        "test_g16_condition_verbatim",
        "test_no_independence_claim",
        "test_g16_states_distinct",
        "test_no_implementation_or_package",
        "test_operator_hold_intact",
        "test_no_packaging_artifacts",
        "test_p0_packet_unchanged",
        "test_contract_declares_zero_extraction",
    ],
    "decisions": [
        "test_candidate_total_27",
        "test_arithmetic_rederived",
        "test_eligibility_scan",
        "test_reference_only_not_copied",
        "test_no_authority_bearing_admitted",
        "test_zero_extracted_files",
        "test_limitations_binding",
        "test_operator_decision_pending",
        "test_census_30_rows",
        "test_public_stable_zero",
        "test_exported_at_p0_historical",
        "test_prohibited_symbols_absent",
        "test_no_wildcard_or_private_reexport",
        "test_public_surface_contract_fields",
        "test_environment_authority_absent",
    ],
    "compat": [
        "test_matrix_25_rows_unproven",
        "test_unknown_version_fails_closed",
        "test_no_silent_latest",
        "test_deprecation_and_removal_declared",
        "test_fingerprint_deterministic",
        "test_conformance_vocabulary_closed",
        "test_declaration_without_test_not_proven",
        "test_schema_identifiers_pinned",
        "test_failure_classes_six",
        "test_each_failure_has_trigger_and_refusal",
        "test_threats_seven_bound",
        "test_later_threats_remain_planned",
        "test_no_new_failure_ids",
        "test_recovery_declared",
    ],
    "authority": [
        "test_np_1",
        "test_np_2",
        "test_np_3",
        "test_np_4",
        "test_np_5",
        "test_np_6",
        "test_np_7",
        "test_np_8",
        "test_negative_control_per_law",
        "test_traversal_refused",
        "test_symlink_escape_refused",
        "test_symlink_cannot_hide_tracked_path",
        "test_symlink_cleanup",
    ],
    "regression": [
        "test_b5_i9_41_nodes",
        "test_authorized_paths_pass",
        "test_unauthorized_mutation_fails",
        "test_tracked_cache_name_fails",
        "test_untracked_residue_passes",
        "test_fake_amendment_fails",
        "test_post_anchor_change_fails",
    ],
    "repro": [
        "test_double_generation_identical",
        "test_manifest_independent_verify",
        "test_no_environment_fields",
        "test_canonical_bytes",
        "test_p0_validator_green_at_its_head",
        "test_workflow_present",
        "test_pinned_actions",
        "test_no_secrets_or_providers",
        "test_node_inventory_selected",
        "test_failure_evidence_uploaded",
        "test_linux_symlink_job",
    ],
}

REQUIREMENT_BINDINGS = {
    "B6-P0-SEC-05": ("B6-I0", "compat", "test_unknown_version_fails_closed"),
    "B6-P0-NP-01": ("B6-I0", "authority", "test_np_1"),
    "B6-P0-NP-02": ("B6-I0", "authority", "test_np_2"),
    "B6-P0-NP-03": ("B6-I0", "authority", "test_np_3"),
    "B6-P0-NP-04": ("B6-I0", "authority", "test_np_4"),
    "B6-P0-NP-05": ("B6-I0", "authority", "test_np_5"),
    "B6-P0-NP-06": ("B6-I0", "authority", "test_np_6"),
    "B6-P0-NP-07": ("B6-I0", "authority", "test_np_7"),
    "B6-P0-NP-08": ("B6-I0", "authority", "test_np_8"),
    "B6-P0-CLS-01": ("B6-I0", "decisions", "test_arithmetic_rederived"),
    "B6-P0-CLS-02": ("B6-I0", "decisions", "test_eligibility_scan"),
    "B6-P0-CLS-03": ("B6-I0", "decisions", "test_reference_only_not_copied"),
    "B6-P0-G16-01": ("B6-I0", "stage", "test_g16_open_and_blocker"),
    "B6-P0-G16-02": ("B6-I0", "stage", "test_g16_condition_verbatim"),
    "B6-P0-G16-03": ("B6-I0", "stage", "test_no_independence_claim"),
    "B6-P0-G16-04": ("B6-I0", "stage", "test_g16_states_distinct"),
    "B6-P0-HOLD-01": ("B6-I0", "stage", "test_no_implementation_or_package"),
    "B6-P0-HOLD-02": ("B6-I0", "stage", "test_operator_hold_intact"),
    "B6-P0-PKG-01": ("B6-I0", "stage", "test_no_packaging_artifacts"),
}

STAGE_PROOF_BINDINGS = {
    "contract": ["stage:test_contract_frozen_before_evidence",
                 "stage:test_scope_bindings_match_p0_sources",
                 "stage:test_requirement_inventory_19",
                 "stage:test_contract_declares_zero_extraction",
                 "stage:test_p0_packet_unchanged"],
    "F01 unauthorized_candidate": ["decisions:test_eligibility_scan"],
    "F02 prohibited_candidate": ["decisions:test_no_authority_bearing_admitted",
                                 "decisions:test_reference_only_not_copied"],
    "F03 authority_bearing_candidate": ["authority:test_np_4", "authority:test_np_8"],
    "F04 private_api": ["decisions:test_no_wildcard_or_private_reexport",
                        "decisions:test_prohibited_symbols_absent"],
    "F17 secret_reference": ["repro:test_no_secrets_or_providers"],
    "F20 unlicensed_dependency": ["authority:test_np_7", "authority:test_np_2"],
    "T04 dependency confusion": ["repro:test_no_secrets_or_providers",
                                 "authority:test_np_2"],
    "T05 namespace collision": ["authority:test_traversal_refused"],
    "T07 manifest tampering": ["repro:test_manifest_independent_verify"],
    "T08 provenance forgery": ["repro:test_manifest_independent_verify",
                               "repro:test_double_generation_identical"],
    "T09 secret leakage": ["repro:test_no_secrets_or_providers"],
    "T14 environment variable authority": ["decisions:test_environment_authority_absent"],
    "T20 authority-bearing extraction": ["decisions:test_zero_extracted_files",
                                         "authority:test_np_1"],
    "C1.S5 conformance": ["compat:test_matrix_25_rows_unproven",
                          "compat:test_conformance_vocabulary_closed",
                          "compat:test_fingerprint_deterministic"],
    "boundary": ["regression:test_b5_i9_41_nodes",
                 "regression:test_authorized_paths_pass",
                 "regression:test_unauthorized_mutation_fails",
                 "regression:test_tracked_cache_name_fails",
                 "regression:test_untracked_residue_passes",
                 "regression:test_fake_amendment_fails",
                 "regression:test_post_anchor_change_fails",
                 "authority:test_symlink_escape_refused",
                 "authority:test_symlink_cannot_hide_tracked_path"],
    "reproducibility": ["repro:test_no_environment_fields", "repro:test_canonical_bytes",
                        "repro:test_p0_validator_green_at_its_head"],
    "ci": ["repro:test_workflow_present", "repro:test_pinned_actions",
           "repro:test_node_inventory_selected", "repro:test_failure_evidence_uploaded",
           "repro:test_linux_symlink_job"],
}

CLASSIFICATIONS = ["EXTRACTABLE_PATTERN", "EXTRACTABLE_WITH_LIMITATION", "REFERENCE_ONLY",
                   "PLATFORM_INTERNAL", "PRIVATE_API", "AUTHORITY_BEARING", "PROHIBITED",
                   "DEFERRED_TO_BOOK_6", "NOT_APPLICABLE"]
ADMISSIBLE = {"EXTRACTABLE_PATTERN", "EXTRACTABLE_WITH_LIMITATION", "DEFERRED_TO_BOOK_6"}
NEVER = "NEVER"
TARGETS = {
    "design_input_rederive": "owning_stage_rederive_no_copy",
    "design_input_with_limitation": "owning_stage_rederive_no_copy",
    "book6_work_after_authorization": "owning_stage_under_new_authorization",
    "study_only_no_copy": "study_only_no_copy",
    "never_extractable_authority": NEVER,
    "not_available_private_api": NEVER,
    "not_available_platform_internal": NEVER,
    "forbidden_constitutional": NEVER,
    "none_absent": "not_applicable",
}


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def p0(root: pathlib.Path, name: str):
    return json.loads((root / DOCS / f"{P0}{name}").read_text(encoding="utf-8"))


def node_ids() -> list[str]:
    return sorted(f"{MODULES[m]}::{n}" for m, ns in NODES.items() for n in ns)


def build_scope(root: pathlib.Path) -> dict:
    seq = p0(root, "CONSTRUCTION_SEQUENCE_v1.0.json")
    stage = {s["id"]: s for s in seq["stages"]}["B6-I0"]
    reg = p0(root, "REQUIREMENT_TEST_REGISTRY_v1.0.json")
    api = p0(root, "PUBLIC_PRIVATE_API_FIREWALL_v1.0.json")
    cand = p0(root, "CANDIDATE_EXTRACTION_DISPOSITION_v1.0.json")
    compat = p0(root, "COMPATIBILITY_AND_REPRODUCIBILITY_PLAN_v1.0.json")
    fail = p0(root, "FAILURE_AND_THREAT_REGISTRY_v1.0.json")
    reqs = [r for r in reg["requirements"] if r["future_stage"] == "B6-I0"]
    return {
        "document_id": "OCE-B6-I0-SCOPE-001",
        "kind": "book6_i0_scope_derivation",
        "version": "1.0.0",
        "stage": "AUTHORIZED_STAGE=B6-I0",
        "base_sha": BASE_SHA,
        "base_tree": BASE_TREE,
        "p0_ratification_sha": P0_SHA,
        "p0_ratification_tree": P0_TREE,
        "source_authority": [
            f"{DOCS}/{P0}CONSTRUCTION_SEQUENCE_v1.0.json#B6-I0",
            f"{DOCS}/{P0}REQUIREMENT_TEST_REGISTRY_v1.0.json",
            f"{DOCS}/{P0}PUBLIC_PRIVATE_API_FIREWALL_v1.0.json",
            f"{DOCS}/{P0}CANDIDATE_EXTRACTION_DISPOSITION_v1.0.json",
            f"{DOCS}/{P0}COMPATIBILITY_AND_REPRODUCIBILITY_PLAN_v1.0.json",
            f"{DOCS}/{P0}FAILURE_AND_THREAT_REGISTRY_v1.0.json",
            f"{DOCS}/{P0}IDENTITY_AND_SCOPE_CONTRACT_v1.0.md",
            f"{DOCS}/OCE_BLOCK_06_REUSABLE_PLATFORM_SURFACES_PLAN_v1.0.md#7",
            f"{DOCS}/{P0}OPERATOR_RATIFICATION_v1.0.md",
        ],
        "stage_binding": {
            "id": stage["id"],
            "kind": stage["kind"],
            "scope": stage["scope"],
            "purpose": stage["purpose"],
            "sections": stage["sections"],
            "outputs": stage["outputs"],
            "non_goals": stage["non_goals"],
            "implementation_surfaces": stage["implementation_surfaces"],
            "entry_gate": stage["entry_gate"],
            "exit_gate": stage["exit_gate"],
            "stop_conditions": stage["stop_conditions"],
            "tests": stage["tests"],
            "source_mutation_floor": stage["mutation_floor"],
        },
        "requirements": sorted(r["id"] for r in reqs),
        "requirement_states": {r["id"]: r["state"] for r in sorted(reqs, key=lambda x: x["id"])},
        "sections": stage["sections"],
        "candidates": sorted(c["id"] for c in cand["candidates"]),
        "api_rows": sorted(s["symbol"] for s in api["symbols"]),
        "failure_classes": sorted(f["id"] for f in fail["failure_classes"]
                                  if f["stage"] == "B6-I0"),
        "threats": sorted(t["id"] for t in fail["threats"] if t["stage"] == "B6-I0"),
        "compatibility_rows": [r["surface"] for r in compat["compatibility_matrix"]["rows"]],
        "provenance_obligations": [r[0] for r in compat["reproducibility"]["requirements"]],
        "planned_tests": node_ids(),
        "mutation_floor": {
            "source": SOURCE_FLOOR,
            "contract": CONTRACT_FLOOR,
            "rule": "the source floor is a planning minimum; the frozen stage contract may "
                    "raise it before results are observed and never lower it afterwards",
        },
        "entry_gate": "operator AUTHORIZED_STAGE=B6-I0 + ratified P0 packet + only B5-proven reuse",
        "exit_gate": "contract frozen and validated; only B5-proven reuse included",
        "non_goals": sorted(set(stage["non_goals"]) | {
            "extraction implementation", "package construction", "package publication",
            "second-application reuse", "cloud deployment", "stable API release",
            "evaluation framework", "benchmark scoring", "B6-I1 through B6-I9",
        }),
        "stop_conditions": sorted(set(stage["stop_conditions"]) | {
            "an authority-bearing candidate is admitted",
            "an unknown classification is treated as eligible",
            "evidence is missing and treated as PASS",
            "an unknown version would be accepted",
            "a package or distribution artifact appears",
        }),
        "counts": {
            "requirements": len(reqs),
            "sections": len(stage["sections"]),
            "candidates": len(cand["candidates"]),
            "api_rows": len(api["symbols"]),
            "failure_classes": sum(1 for f in fail["failure_classes"] if f["stage"] == "B6-I0"),
            "threats": sum(1 for t in fail["threats"] if t["stage"] == "B6-I0"),
            "compatibility_rows": len(compat["compatibility_matrix"]["rows"]),
            "provenance_obligations": len(compat["reproducibility"]["requirements"]),
            "planned_tests": len(node_ids()),
        },
    }


def build_contract(root: pathlib.Path, scope: dict) -> dict:
    return {
        "document_id": "OCE-B6-I0-CONTRACT-001",
        "kind": "book6_i0_implementation_contract",
        "version": "1.0.0",
        "stage": "AUTHORIZED_STAGE=B6-I0",
        "frozen_before_results": True,
        "base_sha": BASE_SHA,
        "base_tree": BASE_TREE,
        "p0_ratification_sha": P0_SHA,
        "p0_ratification_tree": P0_TREE,
        "decision": {
            "mode": "decision_artifacts_plus_conformance_tooling",
            "creates_governed_decision_artifacts": True,
            "creates_executable_conformance_tooling": True,
            "creates_experimental_interfaces": False,
            "permits_code_extraction": False,
            "extracted_source_files": 0,
            "rationale": "the frozen B6-I0 stage declares non_goals=['extraction of code'] and "
                         "implementation_surfaces=['contracts']; the conformance baseline is a "
                         "shared conformance validator over decision artifacts, not an API",
        },
        "requirement_ids": scope["requirements"],
        "candidate_ids": scope["candidates"],
        "api_rows": scope["api_rows"],
        "failure_classes": scope["failure_classes"],
        "threats": scope["threats"],
        "compatibility_rows": scope["compatibility_rows"],
        "provenance_obligations": scope["provenance_obligations"],
        "source_authorities": scope["source_authority"],
        "allowed_paths": [
            f"{DOCS}/{I0}",
            "infrastructure/control-plane/scripts/block_06_i0_generate.py",
            "infrastructure/control-plane/scripts/block_06_i0_validate.py",
            "infrastructure/control-plane/scripts/block_06_i0_mutation_battery.py",
            "infrastructure/control-plane/tests/test_block_06_i0_",
            "infrastructure/control-plane/tests/block_06_i0_support.py",
            ".github/workflows/block-06-i0-validation.yml",
        ],
        "prohibited_paths": [
            "infrastructure/control-plane/src/", "infrastructure/console/src/", "oce/",
            "packages/", "dist/", "build/", "pyproject.toml", "package.json",
            "infrastructure/control-plane/requirements", "uv.lock", "poetry.lock",
            ".github/workflows/b1-i1r-validation.yml",
            ".github/workflows/b5-i8-audit-validation.yml",
            ".github/workflows/b5-i9-factory-gate-validation.yml",
            f"{DOCS}/{P0}",
            f"{DOCS}/OCE_BLOCK_06_REUSABLE_PLATFORM_SURFACES_PLAN_v1.0.md",
            "infrastructure/control-plane/tests/test_b5_i9_stage_identity_and_scope.py",
        ],
        "classifications": {
            "public_stable": 0,
            "public_experimental": 8,
            "internal": 10,
            "private": 0,
            "prohibited": 5,
            "deferred": 7,
            "exports_at_b6_i0": 0,
            "exports_at_p0_historical": 0,
        },
        "schemas": {
            "compatibility": {
                "columns": ["surface", "version", "supported_from", "supported_to",
                            "consumer_evidence", "state"],
                "states": ["UNPROVEN", "PLANNED", "DEFERRED", "PROVEN"],
                "proven_requires": ["consumer_evidence", "discriminating_test"],
            },
            "conformance": {
                "vocabulary": ["PASS", "FAIL", "UNPROVEN", "REFUSED"],
                "result_fields": ["subject", "state", "evidence", "reason"],
                "closure": "unknown fields are rejected",
            },
            "versioning": {
                "api_version": "1.0.0-draft",
                "schema_version": "1.0.0",
                "package_version_format": "semver",
                "unknown_version": "REFUSED",
                "silent_latest": False,
            },
        },
        "failure_controls": {f: "implemented" for f in scope["failure_classes"]},
        "threat_controls": {t: "implemented" for t in scope["threats"]},
        "mutation_floor": {"source": SOURCE_FLOOR, "frozen": CONTRACT_FLOOR},
        "test_inventory": {
            "modules": sorted(MODULES.values()),
            "nodes": scope["planned_tests"],
            "node_total": len(scope["planned_tests"]),
        },
        "adjacent_floors": {
            "b5_i9_nodes": 41,
            "b5_i9_suite": "infrastructure/control-plane/tests/test_b5_i9_*.py",
            "b5_i8_audit_workflow": "green on the same head",
            "b1_i1r_workflow": "green on the same head",
            "p0_validator": "PASS at the P0 ratification head e2aa8ac7; B6-I0 must not "
                            "change a single P0 byte",
            "p0_packet_files": 17,
        },
        "evidence_schema": {
            "fields": ["schema_version", "stage", "head_sha", "head_tree", "run_id",
                       "check_ids", "artifact_name", "totals", "cleanup", "cost_usd"],
            "forbidden": ["timestamp", "hostname", "username", "random_id", "temp_path"],
            "schema_version": "1.0.0",
        },
        "cleanup": ["no scratch directory survives a run",
                    "no untracked file is created inside the repository",
                    "mutation targets are restored byte-exactly"],
        "identity_rules": {
            "implementation_evidence_separate_heads": True,
            "evidence_commit_is_docs_only": True,
            "ci_binds_head_sha_tree_and_run_id": True,
            "pr_remains_draft": True,
        },
        "operator_hold": {
            "state": "HELD",
            "b6_i0_ratification_authorized": False,
            "b6_i0_merge_authorized": False,
            "b6_i1_through_i9_authorized": False,
            "package_publication_authorized": False,
            "evaluation_authorized": False,
            "cost_usd": 0,
            "capital_authority": "none",
        },
    }


def build_decisions(root: pathlib.Path) -> dict:
    cand = p0(root, "CANDIDATE_EXTRACTION_DISPOSITION_v1.0.json")
    rows = []
    for c in sorted(cand["candidates"], key=lambda x: x["id"]):
        admissible = c["classification"] in ADMISSIBLE
        eligible = bool(c["eligible_for_extraction"])
        if not admissible:
            decision = "REFUSED"
            reason = f"classification {c['classification']} is never admissible at B6-I0"
        elif not eligible:
            decision = "REFUSED"
            reason = "classification is admissible but the row is not marked eligible"
        else:
            decision = "ADMITTED_FOR_FUTURE_DESIGN"
            reason = ""
        rows.append({
            "id": c["id"],
            "name": c["name"],
            "source_path": c["source_path"],
            "book5_evidence": c["evidence_citation"],
            "classification": c["classification"],
            "eligibility": eligible,
            "limitation": c["limitation_or_prohibition"],
            "dependency_closure": c["dependency_closure"],
            "authority": c["authority_implications"],
            "state_ownership": "consumer" if admissible else "none",
            "configuration_ownership": "consumer" if admissible else "none",
            "public_private": "public_experimental" if admissible else "never",
            "target_stage": TARGETS[c["book6_disposition"]],
            "required_proof": ("re-derivation at the owning stage with a named consumer and a "
                               "discriminating test" if admissible else "none — refused"),
            "rejection_reason": reason,
            "decision": decision,
            "operator_decision": ("PENDING_OPERATOR_REVIEW" if decision.startswith("ADMITTED")
                                  else "REFUSED"),
            "extracted_at_b6_i0": False,
            "copied_files": 0,
        })
    dist = {k: sum(1 for r in rows if r["classification"] == k) for k in CLASSIFICATIONS}
    return {
        "document_id": "OCE-B6-I0-DECISIONS-001",
        "kind": "book6_i0_extraction_decision_freeze",
        "version": "1.0.0",
        "stage": "AUTHORIZED_STAGE=B6-I0",
        "base_sha": BASE_SHA,
        "p0_source": f"{DOCS}/{P0}CANDIDATE_EXTRACTION_DISPOSITION_v1.0.json",
        "candidate_total": len(rows),
        "distribution": dist,
        "arithmetic": {
            "total": len(rows),
            "admitted": sum(1 for r in rows if r["decision"] == "ADMITTED_FOR_FUTURE_DESIGN"),
            "refused": sum(1 for r in rows if r["decision"] == "REFUSED"),
            "extracted": sum(1 for r in rows if r["extracted_at_b6_i0"]),
            "copied_files": sum(r["copied_files"] for r in rows),
        },
        "rules": {
            "authority_bearing_never": True,
            "private_api_never": True,
            "platform_internal_never": True,
            "reference_only_never_copied": True,
            "unknown_classification_refused": True,
            "missing_evidence_refused": True,
            "book5_rows_byte_identical": True,
        },
        "candidates": rows,
    }


def build_api(root: pathlib.Path) -> dict:
    api = p0(root, "PUBLIC_PRIVATE_API_FIREWALL_v1.0.json")
    rows = []
    for s in sorted(api["symbols"], key=lambda x: (x["section"], x["symbol"])):
        rows.append({
            "symbol": s["symbol"],
            "section": s["section"],
            "classification": s["classification"],
            "owner": s["owner"],
            "typed_inputs": s["typed_inputs"],
            "typed_outputs": s["typed_outputs"],
            "deterministic": s["deterministic"],
            "error_behavior": s["error_behavior"],
            "refusal_semantics": s["error_behavior"],
            "version_introduced": "1.0.0-draft",
            "compatibility_promise": s["compatibility_promise"],
            "compatibility_status": "UNPROVEN",
            "documentation_obligation": s["documentation_obligation"],
            "tests_planned": s["tests_planned"],
            "examples_planned": s["examples_planned"],
            "dependency_boundary": "standard_library_only",
            "authority": ("prohibited" if s["classification"] == "prohibited"
                          else "none"),
            "exported_at_p0": bool(s["exported_at_p0"]),
            "exported_at_b6_i0": False,
            "observed_state": "NOT_IMPLEMENTED",
        })
    return {
        "document_id": "OCE-B6-I0-API-001",
        "kind": "book6_i0_api_principles_and_firewall",
        "version": "1.0.0",
        "stage": "AUTHORIZED_STAGE=B6-I0",
        "base_sha": BASE_SHA,
        "p0_source": f"{DOCS}/{P0}PUBLIC_PRIVATE_API_FIREWALL_v1.0.json",
        "principles": [
            "explicit visibility classification for every symbol",
            "explicit single owner per surface",
            "typed input and output contract before any implementation",
            "deterministic semantics or an explicit refusal",
            "refusal semantics declared, never inferred",
            "a version identifier from first appearance",
            "compatibility status tracked separately from planning state",
            "documentation, test and example obligations recorded per public surface",
            "dependency boundary declared per surface",
            "authority status declared per surface, prohibited by default",
            "no wildcard, implicit or private-name re-export",
            "no database handle, hidden global state or environment-variable authority",
        ],
        "distribution": api["distribution"],
        "export_policy": api["export_policy"],
        "observed": {"exports": 0, "public_stable": 0, "implemented_symbols": 0,
                     "packaged": False},
        "prohibitions": ["wildcard_export", "implicit_export", "private_name_reexport",
                         "source_path_as_api", "database_handle", "hidden_global_state",
                         "environment_variable_authority", "canonical_state_duplication",
                         "decision_authority_duplication", "provider_credentials",
                         "broker_capital_execution_api"],
        "rows_total": len(rows),
        "symbols": rows,
    }


def build_compat(root: pathlib.Path) -> dict:
    plan = p0(root, "COMPATIBILITY_AND_REPRODUCIBILITY_PLAN_v1.0.json")
    src_rows = plan["compatibility_matrix"]["rows"]
    rows = []
    for r in src_rows:
        rows.append({
            "surface": r["surface"],
            "version": "1.0.0-draft",
            "supported_from": "1.0.0",
            "supported_to": "1.x",
            "consumer_evidence": "none",
            "state": "UNPROVEN",
            "discriminating_test": None,
        })
    fingerprint = hashlib.sha256(canonical(rows)).hexdigest()
    return {
        "document_id": "OCE-B6-I0-COMPAT-001",
        "kind": "book6_i0_compatibility_and_conformance_baseline",
        "version": "1.0.0",
        "stage": "AUTHORIZED_STAGE=B6-I0",
        "base_sha": BASE_SHA,
        "p0_source": f"{DOCS}/{P0}COMPATIBILITY_AND_REPRODUCIBILITY_PLAN_v1.0.json",
        "identifiers": {
            "api_version": "1.0.0-draft",
            "schema_version": "1.0.0",
            "package_version_format": "semver",
            "conformance_version": "1.0.0",
        },
        "structural_fingerprint": {
            "algorithm": "sha256 over canonical JSON of the compatibility rows",
            "value": fingerprint,
            "covers": "rows",
        },
        "compatibility_rows": rows,
        "rows_total": len(rows),
        "refusal": {
            "unknown_version": "REFUSED",
            "silent_latest": False,
            "unsupported_version": "REFUSED with the supported range named",
            "rule": "an unknown or unsupported version is refused explicitly; the platform "
                    "never silently resolves to the latest version",
        },
        "deprecation": {
            "required_fields": ["surface", "since_version", "removal_version", "replacement"],
            "state": "DECLARED_NOT_APPLIED",
        },
        "removal": {
            "requires_migration_evidence": True,
            "state": "DECLARED_NOT_APPLIED",
        },
        "migration_evidence": {"required": True, "state": "ABSENT"},
        "backward_compatibility": {
            "rule": "an admitted version keeps its documented behaviour for its supported range",
            "state": "UNPROVEN",
        },
        "conformance": {
            "vocabulary": ["PASS", "FAIL", "UNPROVEN", "REFUSED"],
            "default_state": "UNPROVEN",
            "pass_requires": "an executed discriminating test with recorded evidence",
            "declaration_without_test": "UNPROVEN",
            "evidence_schema": {
                "required": ["subject", "state", "evidence", "reason"],
                "state_vocabulary": ["PASS", "FAIL", "UNPROVEN", "REFUSED"],
                "closure": "unknown fields are rejected",
            },
        },
        "observed": {
            "proven_rows": 0,
            "unproven_rows": len(rows),
            "consumer_available": False,
        },
    }


def build_failures(root: pathlib.Path) -> dict:
    reg = p0(root, "FAILURE_AND_THREAT_REGISTRY_v1.0.json")
    classes = []
    for f in sorted(reg["failure_classes"], key=lambda x: x["id"]):
        if f["stage"] != "B6-I0":
            continue
        classes.append({
            "id": f["id"],
            "name": f["name"],
            "trigger": f["trigger"],
            "expected_refusal": f["expected_refusal"],
            "observable": f["observable"],
            "recovery": f["recovery"],
            "negative_control": f["negative_control"],
            "owner": f["owner"],
            "bound": f["bound"],
            "planned_test": f["planned_test"],
            "implemented_proof": STAGE_PROOF_BINDINGS.get(
                f"{f['id']} {f['name']}", STAGE_PROOF_BINDINGS.get(f["id"], [])),
            "proof_state": "BOUND_PENDING_EVIDENCE",
        })
    threats = []
    for t in sorted(reg["threats"], key=lambda x: x["id"]):
        if t["stage"] != "B6-I0":
            continue
        threats.append({
            "id": t["id"],
            "threat": t["threat"],
            "asset": t["asset"],
            "trust_boundary": t["trust_boundary"],
            "required_refusal": t["required_refusal"],
            "negative_control": STAGE_PROOF_BINDINGS.get(f"{t['id']} {t['threat']}", []),
            "evidence_artifact": f"{DOCS}/{I0}FAILURE_AND_THREAT_PROOFS_v1.0.json",
            "owner": t["owner"],
            "state": "BOUND_PENDING_EVIDENCE",
        })
    later = sorted(t["id"] for t in reg["threats"] if t["stage"] != "B6-I0")
    later_classes = sorted(f["id"] for f in reg["failure_classes"] if f["stage"] != "B6-I0")
    return {
        "document_id": "OCE-B6-I0-PROOFS-001",
        "kind": "book6_i0_failure_and_threat_proofs",
        "version": "1.0.0",
        "stage": "AUTHORIZED_STAGE=B6-I0",
        "base_sha": BASE_SHA,
        "p0_source": f"{DOCS}/{P0}FAILURE_AND_THREAT_REGISTRY_v1.0.json",
        "failure_classes_total": len(classes),
        "threats_total": len(threats),
        "failure_classes": classes,
        "threats": threats,
        "later_failure_classes": later_classes,
        "later_failure_state": "PLANNED_NOT_IMPLEMENTED",
        "later_threats": later,
        "later_threat_state": "PLANNED_NOT_IMPLEMENTED",
        "policy": {
            "no_later_stage_pulled_forward": True,
            "text_scan_only_insufficient": True,
            "structural_parsing_required": True,
        },
    }


def build_registry(root: pathlib.Path, scope: dict) -> dict:
    reg = p0(root, "REQUIREMENT_TEST_REGISTRY_v1.0.json")
    by_id = {r["id"]: r for r in reg["requirements"]}
    rows = []
    for rid in scope["requirements"]:
        r = by_id[rid]
        module, node = REQUIREMENT_BINDINGS[rid][1], REQUIREMENT_BINDINGS[rid][2]
        rows.append({
            "id": rid,
            "category": r["category"],
            "state": r["state"],
            "owner": r["owner"],
            "binding_node": f"{MODULES[module]}::{node}",
            "failure_observable": r["failure_observable"],
            "negative_control": r["negative_control"],
            "evidence_path": f"{DOCS}/{I0}PROGRESS_EVIDENCE_LEDGER_v1.0.md",
            "source_authority": f"{DOCS}/{P0}REQUIREMENT_TEST_REGISTRY_v1.0.json",
            "claim": "NONE — a binding is not a result; execution evidence lives in the ledger",
        })
    stage_proofs = {k: [f"{MODULES[n.split(':')[0]]}::{n.split(':')[1]}" for n in v]
                    for k, v in STAGE_PROOF_BINDINGS.items()}
    covered = {r["binding_node"] for r in rows}
    covered |= {n for v in stage_proofs.values() for n in v}
    remainder = sorted(set(node_ids()) - covered)
    if remainder:
        stage_proofs["stage_surface"] = remainder
    return {
        "document_id": "OCE-B6-I0-REGISTRY-001",
        "kind": "book6_i0_requirement_test_registry",
        "version": "1.0.0",
        "stage": "AUTHORIZED_STAGE=B6-I0",
        "base_sha": BASE_SHA,
        "requirements_total": len(rows),
        "state_vocabulary": reg["state_vocabulary"],
        "arithmetic": {
            "requirements_total": len(rows),
            "by_state": {s: sum(1 for r in rows if r["state"] == s)
                         for s in ("PLANNED", "DEFERRED_WITH_OWNER", "BLOCKED")},
            "pass_claims": 0,
        },
        "requirements": rows,
        "stage_proofs": stage_proofs,
        "inventory": {
            "modules": sorted(set(MODULES.values())),
            "nodes": node_ids(),
            "node_total": len(node_ids()),
        },
    }


def manifest_entry(root: pathlib.Path, rel: str) -> dict:
    raw = (root / rel).read_bytes()
    return {"path": rel, "sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw)}


def emit(root: pathlib.Path, out: pathlib.Path) -> dict:
    scope = build_scope(root)
    contract = build_contract(root, scope)
    payloads = {
        "scope": scope,
        "contract": contract,
        "decisions": build_decisions(root),
        "api": build_api(root),
        "compat": build_compat(root),
        "failures": build_failures(root),
        "registry": build_registry(root, scope),
    }
    out.mkdir(parents=True, exist_ok=True)
    for key, obj in payloads.items():
        target = out / ARTIFACTS[key]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(canonical(obj))
    manifest = {
        "document_id": "OCE-B6-I0-MANIFEST-001",
        "kind": "book6_i0_packet_manifest",
        "version": "1.0.0",
        "stage": "AUTHORIZED_STAGE=B6-I0",
        "base_sha": BASE_SHA,
        "generator": "block_06_i0_generate.py",
        "schema_version": "1.0.0",
        "artifacts": [manifest_entry(out, ARTIFACTS[k]) for k in payloads],
    }
    (out / ARTIFACTS["manifest"]).write_bytes(canonical(manifest))
    return manifest


def repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    root = pathlib.Path(args.root).resolve() if args.root else repo_root()
    out = pathlib.Path(args.out).resolve() if args.out else root
    manifest = emit(root, out)
    print(f"artifacts {len(manifest['artifacts'])}")
    for row in manifest["artifacts"]:
        print(f"{row['sha256'][:12]} {row['size']:6d} {row['path'].rsplit('/', 1)[-1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
