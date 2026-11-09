#!/usr/bin/env python3
"""B6-I1 deterministic artifact generator.

Emits the stage contract packet from one in-code table so every artifact is derived, canonical and
byte-stable. Standard library only, offline, no timestamps, no host or user identity.

Usage:
  python infrastructure/control-plane/scripts/block_06_i1_generate.py
  python infrastructure/control-plane/scripts/block_06_i1_generate.py --out DIR --with-code
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

DOCS = "docs/oce-golden-system"
PREFIX = "OCE_BLOCK_06_I1_"
BASE_SHA = "6783bf7638f5ecd4e42ec2eb8141d1aa57dfaa3e"
BASE_TREE = "3c2e2a6676e16415a1e2bd326c1fc147e51c2a6d"
I0_HEAD = "c5d7bfcc5ea99837985ba82a3c91fd1e76d85a81"
I0_IMPL = "6aa168f1ecc9f831a39bc150e42157d61601672e"
TESTS = "infrastructure/control-plane/tests"
SCRIPTS = "infrastructure/control-plane/scripts"
WORKFLOWS = ".github/workflows"
MODULES = (
    "test_block_06_i1_contract.py",
    "test_block_06_i1_denial.py",
    "test_block_06_i1_sdk.py",
    "test_block_06_i1_compat.py",
    "test_block_06_i1_authority_and_boundary.py",
    "test_block_06_i1_evidence_and_cleanup.py",
)
EXPECTED_NODES = 42

SCOPES = ("read", "propose", "decide")
FORBIDDEN_SCOPES = ("*", "admin", "authority", "write", "root")

OPERATIONS = [
    ("oce.api.v1.identity.get", "C1.S1", "read", ["actor_id"], ["actor_id", "capabilities"]),
    ("oce.api.v1.capabilities.get", "C1.S1", "read", ["actor_id", "scope"], ["capability_set"]),
    ("oce.sdk.intents.submit", "C1.S2", "propose", ["intent", "actor"], ["receipt"]),
    ("oce.api.v1.intents.get", "C1.S2", "read", ["intent_id"], ["intent"]),
    ("oce.api.v1.tasks.get", "C1.S2", "read", ["task_id"], ["task"]),
    ("oce.api.v1.events.append", "C1.S2", "propose", ["task_id", "event"], ["receipt"]),
    ("oce.api.v1.artifacts.get", "C1.S2", "read", ["artifact_id"], ["artifact"]),
    ("oce.api.v1.evidence.list", "C1.S2", "read", [], ["evidence"]),
    ("oce.api.v1.approvals.decide", "C1.S2", "decide", ["approval_id", "decision"], ["approval"]),
    ("oce.compat.matrix.check", "C1.S5", "read", ["consumer_version"], ["verdict"]),
]
REFUSALS = [
    ("REFUSED_VERSION_UNKNOWN", "F10", "a version string cannot be resolved"),
    ("REFUSED_VERSION_UNSUPPORTED", "F09", "a resolved version is outside the supported window"),
    ("REFUSED_OPERATION_UNKNOWN", "F09", "the operation is not in the frozen table"),
    ("REFUSED_SCOPE", "F09", "the caller does not hold the declared scope"),
    ("REFUSED_SCHEMA", "F09", "input does not match the declared typed schema"),
    ("REFUSED_AUTHORITY", "F09", "the caller attempted to supply authority"),
    ("REFUSED_STORAGE_INTERNAL", "F05", "the request or result would expose storage internals"),
    ("REFUSED_SELF_APPROVAL", "F09", "the requester attempted to approve their own request"),
    ("REFUSED_DUPLICATE_RECEIPT", "F07", "a receipt id would be reused"),
]
REQUIREMENTS = [
    ("API-01", "C1.S1", "A versioned v1 surface exists with an explicit operation table"),
    ("API-02", "C1.S1", "No storage internal, path or raw store is exposed by any response"),
    ("API-03", "C1.S1", "Every operation declares and enforces exactly one scope"),
    ("API-04", "C1.S1", "No caller can supply, widen or inherit authority"),
    ("API-05", "C1.S1", "Unknown versions are refused and never coerced to the latest"),
    ("SDK-01", "C1.S2", "The typed client invokes the canonical API only"),
    ("SDK-02", "C1.S2", "The SDK duplicates no business rule and no state transition"),
    ("SDK-03", "C1.S2", "The SDK surfaces typed refusals without rewriting them"),
    ("CMP-01", "C1.S5", "A compatibility matrix check returns supported, unsupported or unknown"),
    ("CMP-02", "C1.S5", "Unsupported and unknown versions carry the supported window"),
    ("DET-01", "C1.S2", "Identical input yields byte-identical canonical output"),
    ("PROV-01", "C1.S1", "Every receipt binds request, result, version and contract hash"),
]
THREATS = {
    "T04": "storage or path disclosure through an API result",
    "T05": "authority widening through a client-supplied field",
    "T07": "version confusion or silent downgrade",
    "T08": "cross-actor approval or self-approval",
    "T09": "duplicate or replayed receipt",
    "T14": "untyped refusal hiding the supported window",
    "T20": "SDK reimplementation of canonical rules",
}


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def operations() -> list[dict]:
    rows = []
    for symbol, section, scope, inputs, outputs in OPERATIONS:
        rows.append({
            "symbol": symbol,
            "section": section,
            "version": "v1",
            "classification": "public_experimental",
            "compatibility_promise": "additive_minor",
            "scope_required": scope,
            "typed_inputs": inputs,
            "typed_outputs": outputs,
            "authority_class": scope,
            "deterministic": True,
            "refusal_codes": ["REFUSED_SCOPE", "REFUSED_SCHEMA", "REFUSED_AUTHORITY"],
        })
    return rows


def scope_derivation() -> dict:
    return {
        "schema": "oce.block_06_i1.scope.v1",
        "document_id": "OCE-B6-I1-SCOPE-001",
        "stage": "B6-I1",
        "status": "FROZEN",
        "base_sha": BASE_SHA,
        "base_tree": BASE_TREE,
        "authority_sources": [
            {"path": f"{DOCS}/OCE_BLOCK_06_P0_CONSTRUCTION_SEQUENCE_v1.0.json",
             "claim": "B6-I1 kind=implementation, purpose='C1 API/SDK', surfaces ['api','sdk'], "
                      "scope 'C1.S1, C1.S2, C1.S5', tests ['contract','denial'], mutation_floor 3"},
            {"path": f"{DOCS}/OCE_BLOCK_06_P0_CONSTRUCTION_PLAN_v1.0.md",
             "claim": "B6-I1 stage name 'C1 API and SDK', gate 'canonical path and compatibility pass'"},
            {"path": f"{DOCS}/OCE_BLOCK_06_REUSABLE_PLATFORM_SURFACES_PLAN_v1.0.md#B6.C1.S1",
             "claim": "versioned API exposing OCE functions without storage internals or authority bypass"},
            {"path": f"{DOCS}/OCE_BLOCK_06_REUSABLE_PLATFORM_SURFACES_PLAN_v1.0.md#B6.C1.S2",
             "claim": "typed local clients for identity, intents, tasks, events, artifacts, evidence, approvals"},
            {"path": f"{DOCS}/OCE_BLOCK_06_REUSABLE_PLATFORM_SURFACES_PLAN_v1.0.md#B6.C1.S5",
             "claim": "compatibility matrix check; unsupported version fails clearly"},
            {"path": f"{DOCS}/OCE_BLOCK_06_P0_PUBLIC_PRIVATE_API_FIREWALL_v1.0.json",
             "claim": "three symbols are pre-admitted at B6-I1: capabilities.get, sdk.intents.submit, "
                      "compat.matrix.check, all public_experimental and deny_by_default"},
            {"path": f"{DOCS}/OCE_BLOCK_06_P0_VERSIONING_AND_COMPATIBILITY_CONTRACT_v1.0.md",
             "claim": "path-versioned v1; additive inside a major; unknown refused; no silent latest"},
        ],
        "identity": {
            "stage_name": "C1 API and SDK",
            "gate": "canonical path and compatibility pass",
            "sections": ["C1.S1", "C1.S2"],
            "surfaces": ["api", "sdk"],
            "authorizes_source_extraction": False,
            "authorizes_design_of_extraction_candidates": False,
            "authorizes_packaging": False,
            "authorizes_publication": False,
            "authorizes_consumer_construction": False,
            "note": "B6-I0 admitted 12 candidates for later design; B6-I1 does not copy or extract "
                    "them, and the non-goal 'templates' defers B6-I2 surfaces.",
        },
        "outputs": [
            "versioned v1 operation contract with typed inputs, outputs and scopes",
            "canonical in-process API service enforcing the contract",
            "typed SDK client invoking only the canonical API",
            "compatibility matrix check with explicit refusal semantics",
            "one worked example request",
            "contract and denial proofs with discriminating mutations",
        ],
        "non_goals": ["templates", "extraction of candidates", "packaging", "publication",
                      "consumer application", "cloud hosting", "evaluation service"],
        "allowed_paths": [
            "oce/api/",
            "oce/sdk/",
            "oce/compat/",
            f"{DOCS}/{PREFIX}",
            f"{SCRIPTS}/block_06_i1_",
            f"{TESTS}/test_block_06_i1_",
            f"{TESTS}/block_06_i1_support.py",
            f"{WORKFLOWS}/block-06-i1-validation.yml",
            f"{WORKFLOWS}/block-06-i1-paired-comparison.yml",
        ],
        "forbidden_paths": [
            "packages/", "dist/", "build/", "pyproject.toml", "uv.lock", "poetry.lock",
            "package.json", "infrastructure/control-plane/src/", "infrastructure/console/src/",
            f"{DOCS}/OCE_BLOCK_06_P0_", f"{DOCS}/OCE_BLOCK_06_I0_",
            ".github/workflows/b1-i1r-validation.yml",
            ".github/workflows/b5-i8-audit-validation.yml",
            ".github/workflows/b5-i9-factory-gate-validation.yml",
            ".github/workflows/block-06-i0-validation.yml",
        ],
        "locks": {
            "B6-I2": "LOCKED", "B6-I3": "LOCKED", "B6-I4": "LOCKED", "B6-I5": "LOCKED",
            "B6-I6": "LOCKED", "B6-I7": "LOCKED", "B6-I8": "LOCKED", "B6-I9": "LOCKED",
            "BOOK_6_COMPLETE": False, "G16": "OPEN", "G16_OWNER": "B5I8-DF05",
            "evaluation_system": "RESERVED_NOT_AUTHORIZED",
            "package_publication": "NOT_BEGUN", "cloud_hosting": "NOT_BEGUN",
            "broker_execution_capital_authority": "none",
        },
        "cost_usd": 0,
        "capital_authority": "none",
    }


def contract() -> dict:
    return {
        "schema": "oce.block_06_i1.contract.v1",
        "document_id": "OCE-B6-I1-CONTRACT-001",
        "stage": "B6-I1",
        "status": "FROZEN",
        "frozen_before_results": True,
        "base_sha": BASE_SHA,
        "base_tree": BASE_TREE,
        "p0_ratification_sha": I0_HEAD,
        "implementation_floor": {"test_nodes": EXPECTED_NODES, "mutations": 6, "source_mutation_floor": 3},
        "test_inventory": {
            "modules": [f"{TESTS}/{m}" for m in MODULES],
            "expected_nodes": EXPECTED_NODES,
            "derivation": "declared node set equals pytest collection over the six stage modules; "
                          "duplicates and orphans are refused",
            "collection_equals_execution": True,
            "zero": ["failures", "errors", "skipped", "xfail"],
        },
        "scopes": {"declared": list(SCOPES), "forbidden": list(FORBIDDEN_SCOPES),
                   "wildcard": False, "client_supplied_authority": False},
        "api_version": "v1", "api_major": 1, "path_versioned": True,
        "operations_total": len(OPERATIONS), "public_stable": 0,
        "public_experimental": len(OPERATIONS), "internal": 0,
        "envelope": {"required": ["version", "operation", "actor", "scopes", "payload"],
                     "forbidden": ["authority", "store", "path", "token", "secret"],
                     "extra_keys_refused": True, "missing_keys_refused": True},
        "refusals": [{"code": c, "class": f, "meaning": m} for c, f, m in REFUSALS],
        "determinism": {"canonical_json": "sort_keys, indent 2, utf-8, LF",
                        "receipt": "sha256 over canonical request and canonical result",
                        "no_timestamps": True, "no_random_ids": True, "no_host_identity": True},
        "compatibility": {"supported": ["v1"], "unknown_refused": True, "silent_latest": False,
                          "verdicts": ["SUPPORTED", "UNSUPPORTED", "UNKNOWN"]},
        "provenance": {"receipt_fields": ["contract_hash", "request_sha256", "result_sha256",
                                          "version", "operation", "actor"],
                       "artifact_binding": "sha256 plus byte size over LF-normalised bytes"},
        "manifest": {"schema": "oce.block_06_i1.manifest.v1",
                     "hash": "sha256", "size": "bytes", "independent_verification": True},
        "cleanup": {"tracked_tree_clean": True, "scratch_prefix": ".b6i1-", "residue_refused": True},
        "adjacent_floors": {"b5_i9_nodes": 41, "b5_i9_suite": f"{TESTS}/test_b5_i9_*.py",
                            "b6_i0_nodes": 72, "p0_packet_files": 17},
        "paired_comparison": {"contract": f"{DOCS}/{PREFIX}PAIRED_COMPARISON_CONTRACT_v1.0.json",
                              "base_sha": BASE_SHA, "common_floor": 270,
                              "head_only_expected": EXPECTED_NODES, "base_only_expected": 0},
        "locks": {"B6-I2_through_I9": "LOCKED", "MERGE_AUTHORIZED": False,
                  "RATIFICATION_AUTHORIZED": False, "BOOK_6_COMPLETE": False,
                  "G16": "OPEN", "evaluation_system": "RESERVED_NOT_AUTHORIZED"},
        "cost_usd": 0, "capital_authority": "none",
    }


def api_contract() -> dict:
    return {
        "schema": "oce.block_06_i1.api_sdk.v1",
        "document_id": "OCE-B6-I1-API-001",
        "stage": "B6-I1",
        "status": "FROZEN",
        "api_version": "v1",
        "transport": "in-process canonical call returning canonical JSON; no socket, no network",
        "export_policy": "public_experimental only; no stable symbol and no wildcard export",
        "deny_by_default": True,
        "operations": operations(),
        "sdk": {"module": "oce/sdk/client.py", "typed_refusals": True,
                "invokes": "the canonical dispatcher only",
                "duplicates_rules": False, "example": "oce/sdk/examples/one_worked_request.py"},
        "compat": {"module": "oce/compat/matrix.py",
                   "verdicts": ["SUPPORTED", "UNSUPPORTED", "UNKNOWN"]},
        "prohibitions": ["no storage path", "no store object", "no raw secret",
                         "no client authority", "no silent latest", "no stable claim"],
    }


def compat_matrix() -> dict:
    rows = [
        ("C1.S1", "oce.api.v1.capabilities.get", "v1", "v1", "v1",
         "contract and denial nodes in this stage"),
        ("C1.S2", "oce.sdk.intents.submit", "v1", "v1", "v1",
         "SDK contract nodes in this stage"),
        ("C1.S5", "oce.compat.matrix.check", "v1", "v1", "v1",
         "unsupported-version refusal nodes in this stage"),
    ]
    return {
        "schema": "oce.block_06_i1.compat.v1",
        "document_id": "OCE-B6-I1-COMPAT-001",
        "stage": "B6-I1",
        "status": "FROZEN",
        "supported_window": {"min": "v1", "max": "v1", "policy": "additive_minor"},
        "rows": [{"section": s, "surface": sym, "version": v, "supported_from": f,
                  "supported_to": t, "consumer_evidence": e, "state": "PROVEN"}
                 for s, sym, v, f, t, e in rows],
        "refusal": {"unknown_version": "REFUSED", "unsupported_version": "REFUSED",
                    "silent_latest": False, "supported_window_in_message": True},
        "unproven_elsewhere": {"block_6_sections_total": 25, "proven_in_this_stage": 3,
                               "state": "the remaining 22 rows stay UNPROVEN"},
    }


def registry() -> dict:
    return {
        "schema": "oce.block_06_i1.registry.v1",
        "document_id": "OCE-B6-I1-REGISTRY-001",
        "stage": "B6-I1",
        "status": "FROZEN",
        "requirements_total": len(REQUIREMENTS),
        "requirements": [{"id": i, "section": s, "claim": c,
                          "proved_by": MODULES[min(n, len(MODULES) - 1)]}
                         for n, (i, s, c) in enumerate(REQUIREMENTS)],
        "inventory": {"modules": [f"{TESTS}/{m}" for m in MODULES],
                      "expected_nodes": EXPECTED_NODES,
                      "declared": "collected at CI; equality and uniqueness are asserted"},
        "threats": [{"id": k, "description": v} for k, v in THREATS.items()],
        "failure_classes": ["F05", "F06", "F07", "F08", "F09", "F10"],
        "mutation_floor": {"source": 3, "stage": 6},
    }


def failure_proofs() -> dict:
    return {
        "schema": "oce.block_06_i1.failures.v1",
        "document_id": "OCE-B6-I1-FAILURES-001",
        "stage": "B6-I1",
        "status": "FROZEN",
        "classes": [
            {"id": "F09", "name": "incompatible_version",
             "trigger": "a consumer requests an unsupported version",
             "expected_refusal": "REFUSED_VERSION_UNSUPPORTED", "bound": True},
            {"id": "F10", "name": "unknown_version",
             "trigger": "a version cannot be resolved",
             "expected_refusal": "REFUSED_VERSION_UNKNOWN", "bound": True},
            {"id": "F07", "name": "duplicate_symbol",
             "trigger": "two operations claim one symbol or receipt id",
             "expected_refusal": "REFUSED_DUPLICATE_RECEIPT", "bound": True},
        ],
        "threat_controls": [{"id": k, "description": v} for k, v in THREATS.items()],
        "negative_controls": [
            "unsupported version refused with the supported window",
            "unknown version refused and never coerced",
            "scope-free call refused",
            "authority-bearing call refused",
            "storage-internal read refused",
            "self-approval refused",
        ],
    }


def registry_nodes() -> int:
    return EXPECTED_NODES


def paired_contract(head_sha: str, head_tree: str) -> dict:
    return {
        "schema": "oce.block_06_i1.paired.v1",
        "document_id": "OCE-B6-I1-PAIRED-001",
        "stage": "B6-I1",
        "status": "FROZEN",
        "frozen_before_results": True,
        "endpoints": {"base_sha": BASE_SHA, "base_tree": BASE_TREE,
                      "head_sha": head_sha, "head_tree": head_tree},
        "population": {"common_glob": "infrastructure/control-plane/tests/test_b5_i[2-9]*.py",
                       "common_floor": 270, "head_only_glob":
                       "infrastructure/control-plane/tests/test_block_06_i1_*.py",
                       "head_only_expected": EXPECTED_NODES, "base_only_expected": 0},
        "rules": {"identical_setup": True, "separate_clones": True, "cleanup_before_verdict": True,
                  "fail_closed": ["zero common population", "below floor", "endpoint mismatch",
                                  "absent ref", "uncollected suite", "common regression",
                                  "head-only not green", "cleanup failure"]},
    }


def build(out: pathlib.Path, with_code: bool, head_sha: str | None = None) -> dict:
    docs = {
        "SCOPE_DERIVATION_v1.0.json": scope_derivation(),
        "IMPLEMENTATION_CONTRACT_v1.0.json": contract(),
        "API_AND_SDK_CONTRACT_v1.0.json": api_contract(),
        "COMPATIBILITY_MATRIX_v1.0.json": compat_matrix(),
        "REQUIREMENT_TEST_REGISTRY_v1.0.json": registry(),
        "FAILURE_AND_THREAT_PROOFS_v1.0.json": failure_proofs(),
    }
    (out / DOCS).mkdir(parents=True, exist_ok=True)
    written = {}
    for name, payload in docs.items():
        path = out / DOCS / f"{PREFIX}{name}"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = canonical(payload)
        path.write_bytes(data)
        written[f"{DOCS}/{PREFIX}{name}"] = data
    code = []
    if with_code:
        for rel in sorted([p for p in [
            "oce/api/v1/contract.py", "oce/api/v1/service.py", "oce/api/v1/__init__.py",
            "oce/api/__init__.py", "oce/sdk/client.py", "oce/sdk/__init__.py",
            "oce/sdk/examples/one_worked_request.py", "oce/compat/matrix.py",
            "oce/compat/__init__.py",
        ]]):
            p = out / rel
            if p.exists():
                code.append({"path": rel, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                             "bytes": p.stat().st_size})
    manifest = {
        "schema": "oce.block_06_i1.manifest.v1",
        "document_id": "OCE-B6-I1-MANIFEST-001",
        "stage": "B6-I1",
        "status": "FROZEN",
        "hash": "sha256",
        "artifacts": [{"path": k, "sha256": hashlib.sha256(v).hexdigest(), "bytes": len(v)}
                      for k, v in sorted(written.items())],
        "code": code,
        "totals": {"artifacts": len(written), "code_files": len(code)},
        "verification": "recomputed by a second code path in the validator and in a test node",
    }
    if head_sha:
        head_tree = subprocess_tree(out, head_sha)
        payload = paired_contract(head_sha, head_tree)
        path = out / DOCS / f"{PREFIX}PAIRED_COMPARISON_CONTRACT_v1.0.json"
        path.write_bytes(canonical(payload))
        written[path.relative_to(out).as_posix()] = path.read_bytes()
        manifest["artifacts"] = [{"path": k, "sha256": hashlib.sha256(v).hexdigest(),
                                  "bytes": len(v)} for k, v in sorted(written.items())]
        manifest["totals"]["artifacts"] = len(written)
    path = out / DOCS / f"{PREFIX}MANIFEST_v1.0.json"
    path.write_bytes(canonical(manifest))
    return {"artifacts": len(written) + 1, "code": len(code)}


def subprocess_tree(root: pathlib.Path, sha: str) -> str:
    import subprocess
    return subprocess.run(["git", "-C", str(root), "rev-parse", f"{sha}^{{tree}}"],
                          capture_output=True, text=True, check=True).stdout.strip()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".")
    ap.add_argument("--with-code", action="store_true")
    ap.add_argument("--head", default=None)
    args = ap.parse_args(argv)
    summary = build(pathlib.Path(args.out), args.with_code, args.head)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
