#!/usr/bin/env python3
"""Book 6 P0 planning validator.

Deterministic, offline, standard library only. It validates the committed
planning packet; it never generates, repairs or simulates implementation.

Usage:
  python infrastructure/control-plane/scripts/block_06_p0_validate.py
  python infrastructure/control-plane/scripts/block_06_p0_validate.py --json out.json
  python infrastructure/control-plane/scripts/block_06_p0_validate.py --root <scratch-copy>
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

DOCS = "docs/oce-golden-system"
P = "OCE_BLOCK_06_P0_"
FILES = {
    "authority": f"{DOCS}/{P}AUTHORITY_AND_SOURCE_MAP_v1.0.md",
    "identity": f"{DOCS}/{P}IDENTITY_AND_SCOPE_CONTRACT_v1.0.md",
    "candidates": f"{DOCS}/{P}CANDIDATE_EXTRACTION_DISPOSITION_v1.0.json",
    "api": f"{DOCS}/{P}PUBLIC_PRIVATE_API_FIREWALL_v1.0.json",
    "registry": f"{DOCS}/{P}REQUIREMENT_TEST_REGISTRY_v1.0.json",
    "construction": f"{DOCS}/{P}CONSTRUCTION_PLAN_v1.0.md",
    "sequence": f"{DOCS}/{P}CONSTRUCTION_SEQUENCE_v1.0.json",
    "failure_plan": f"{DOCS}/{P}FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md",
    "failure_registry": f"{DOCS}/{P}FAILURE_AND_THREAT_REGISTRY_v1.0.json",
    "threat": f"{DOCS}/{P}SECURITY_AND_THREAT_MODEL_v1.0.md",
    "versioning": f"{DOCS}/{P}VERSIONING_AND_COMPATIBILITY_CONTRACT_v1.0.md",
    "compat": f"{DOCS}/{P}COMPATIBILITY_AND_REPRODUCIBILITY_PLAN_v1.0.json",
    "repro": f"{DOCS}/{P}REPRODUCIBILITY_AND_PROVENANCE_PLAN_v1.0.md",
    "evaluation": f"{DOCS}/{P}EVALUATION_READINESS_HANDOFF_v1.0.md",
    "acceptance": f"{DOCS}/{P}ACCEPTANCE_MATRIX_v1.0.md",
    "ledger": f"{DOCS}/{P}PROGRESS_EVIDENCE_LEDGER_v1.0.md",
}
VALIDATOR = "infrastructure/control-plane/scripts/block_06_p0_validate.py"
BASE_SHA = "a794a9af80ae8deddacf2991de17b7d71e445756"
BASE_TREE = "762dc5696f2135a14455f11d13d5c958ba812723"
G16_PACKET = "infrastructure/control-plane/evidence/b5-i9/g16-limitation.json"
HANDOFF = "infrastructure/control-plane/evidence/b5-i9/handoff-input-readiness.json"
B5_REGISTRY = f"{DOCS}/OCE_B5_I9_REQUIREMENT_TEST_REGISTRY_v1.0.json"
ALLOWED_PREFIXES = (f"{DOCS}/{P}", VALIDATOR)
FORBIDDEN_DIFF_PREFIXES = (
    "infrastructure/control-plane/src/", "infrastructure/console/src/",
    "infrastructure/control-plane/tests/", ".github/", "oce/frontend/",
    "infrastructure/control-plane/evidence/b5-i9/", "pyproject.toml",
    "package.json", "requirements", "uv.lock", "poetry.lock",
)
STATES = {"PLANNED", "DEFERRED_WITH_OWNER", "BLOCKED"}
BINDINGS = {"static", "attestation", "deferred", "blocked"}
CLASSES = ["EXTRACTABLE_PATTERN", "EXTRACTABLE_WITH_LIMITATION", "REFERENCE_ONLY",
           "PLATFORM_INTERNAL", "PRIVATE_API", "AUTHORITY_BEARING", "PROHIBITED",
           "DEFERRED_TO_BOOK_6", "NOT_APPLICABLE"]
EXPECTED_DIST = {"EXTRACTABLE_PATTERN": 7, "EXTRACTABLE_WITH_LIMITATION": 5,
                 "REFERENCE_ONLY": 4, "PLATFORM_INTERNAL": 3, "PRIVATE_API": 2,
                 "AUTHORITY_BEARING": 3, "PROHIBITED": 1, "DEFERRED_TO_BOOK_6": 1,
                 "NOT_APPLICABLE": 1}
NEVER_ELIGIBLE = {"PLATFORM_INTERNAL", "PRIVATE_API", "AUTHORITY_BEARING", "PROHIBITED",
                  "REFERENCE_ONLY", "NOT_APPLICABLE"}
FORBIDDEN_CLAIMS = ("PASS", "IMPLEMENTED", "COMPLETE", "VERIFIED")
SECRET_PATTERNS = [
    re.compile(r"BEGIN (RSA|OPENSSH|EC|PGP) PRIVATE KEY"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)\bclient_secret\s*[:=]"),
    re.compile(r"(?i)\bpassword\s*[:=]\s*\S"),
]
URL_PATTERN = re.compile(r"https?://", re.I)


class Checker:
    def __init__(self, root: pathlib.Path) -> None:
        self.root = root
        self.failures: list[dict] = []
        self.checks: list[str] = []

    def ok(self, name: str) -> None:
        self.checks.append(name)

    def fail(self, name: str, detail) -> None:
        self.failures.append({"check": name, "detail": detail})

    def need(self, name: str, cond: bool, detail="") -> None:
        if cond:
            self.ok(name)
        else:
            self.fail(name, detail or "condition false")

    def path(self, rel: str) -> pathlib.Path:
        return self.root / rel

    def text(self, rel: str) -> str:
        return self.path(rel).read_text(encoding="utf-8")

    def data(self, key: str):
        return json.loads(self.path(FILES[key]).read_text(encoding="utf-8"))


def check_packet_files(c: Checker) -> None:
    missing = [v for v in FILES.values() if not c.path(v).exists()]
    c.need("packet/files_present", not missing, missing)
    if c.root == repo_root():
        c.need("packet/validator_present", c.path(VALIDATOR).exists(), VALIDATOR)


def check_canonical_json(c: Checker) -> None:
    bad = []
    for key in ("candidates", "api", "registry", "sequence", "failure_registry", "compat"):
        raw = c.path(FILES[key]).read_bytes()
        parsed = json.loads(raw.decode("utf-8"))
        canon = (json.dumps(parsed, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
        if canon != raw:
            bad.append(FILES[key])
    c.need("json/canonical_bytes", not bad, bad)


def check_identity_and_locks(c: Checker) -> None:
    r = c.data("registry")
    ident = r["identity"]
    c.need("identity/block_6", ident["block"] == 6 and ident["name"] == "Reusable Platform Surfaces", ident)
    c.need("identity/sections_25", ident["sections"] == 25 and ident["chapters"] == 5, ident)
    c.need("identity/first_increment", ident["first_implementation_increment"] == "B6-I0", ident)
    c.need("identity/proposed_p0", ident["proposed_p0_stage"] == "B6-P0", ident)
    c.need("identity/base_sha", r["base_sha"] == BASE_SHA and r["base_tree"] == BASE_TREE, r["base_sha"])
    locks = r["locks"]
    c.need("locks/implementation_false", locks["book_6_implementation_started"] is False, locks)
    c.need("locks/authorized_false", locks["book_6_authorized"] is False, locks)
    c.need("locks/package_false", locks["book_6_package_exists"] is False, locks)
    c.need("locks/extraction_false", locks["reusable_extraction_started"] is False, locks)
    c.need("locks/evaluation_false", locks["post_book_6_evaluation_started"] is False, locks)
    c.need("locks/merge_false", locks["merge_authorized"] is False, locks)
    c.need("locks/cost_zero", locks["cost_usd"] == 0 and locks["cloud_mutations"] == 0, locks)
    c.need("locks/capital_none", locks["capital_authority"] == "none", locks)
    c.need("locks/book5_closed", locks["book_5_governance_complete"] is True, locks)


def check_requirements(c: Checker) -> None:
    r = c.data("registry")
    reqs = r["requirements"]
    ids = [x["id"] for x in reqs]
    c.need("req/unique_ids", len(ids) == len(set(ids)), "duplicate requirement id")
    c.need("req/id_pattern", all(re.fullmatch(r"B6-P0-[A-Z0-9-]+", i) for i in ids), ids)
    bad_state = [x["id"] for x in reqs if x["state"] not in STATES]
    c.need("req/state_vocabulary", not bad_state, bad_state)
    c.need("req/no_pass", not [x for x in reqs if x["state"] == "PASS"], "PASS claim present")
    bad_binding = [x["id"] for x in reqs if x["binding"] not in BINDINGS]
    c.need("req/binding_vocabulary", not bad_binding, bad_binding)
    mismatch = []
    for x in reqs:
        if x["state"] == "PLANNED" and x["binding"] not in {"static", "attestation"}:
            mismatch.append(x["id"])
        if x["state"] == "DEFERRED_WITH_OWNER" and x["binding"] != "deferred":
            mismatch.append(x["id"])
        if x["state"] == "BLOCKED" and x["binding"] != "blocked":
            mismatch.append(x["id"])
    c.need("req/state_binding_consistency", not mismatch, mismatch)
    required = ("id", "category", "statement", "authority", "owner", "state", "binding",
                "proof", "failure_observable", "negative_control", "future_stage",
                "failure_class")
    empty = [x["id"] for x in reqs for f in required if x.get(f) in (None, "", [])]
    c.need("req/fields_non_empty", not empty, empty)
    deferred = [x for x in reqs if x["state"] == "DEFERRED_WITH_OWNER"]
    c.need("req/deferred_owner", all(x["deferred_owner"] and x["deferral_reason"] for x in deferred),
           [x["id"] for x in deferred if not (x["deferred_owner"] and x["deferral_reason"])])
    blocked = [x for x in reqs if x["state"] == "BLOCKED"]
    c.need("req/blocked_has_owner", all(x["owner"] for x in blocked), [x["id"] for x in blocked])
    c.need("req/no_orphan_failures", all(x["failure_class"].startswith("F") for x in reqs),
           [x["id"] for x in reqs if not x["failure_class"].startswith("F")])
    holds = {"B6-P0-HOLD-01", "B6-P0-HOLD-02"}
    c.need("req/operator_holds_present", holds <= set(ids), sorted(holds - set(ids)))
    cats = {x["category"] for x in reqs}
    arith = r["arithmetic"]
    recomputed = {
        "requirements_total": len(reqs),
        "by_category": {k: sum(1 for x in reqs if x["category"] == k) for k in sorted(cats)},
        "by_state": {k: sum(1 for x in reqs if x["state"] == k) for k in sorted(STATES)},
        "by_binding": {k: sum(1 for x in reqs if x["binding"] == k) for k in sorted(BINDINGS)},
        "pass_claims": 0,
    }
    c.need("req/arithmetic_matches", recomputed == arith, {"declared": arith, "computed": recomputed})
    c.need("req/total_47", arith["requirements_total"] == 47, arith["requirements_total"])


def check_candidates(c: Checker) -> None:
    d = c.data("candidates")
    rows = d["candidates"]
    c.need("cand/total_27", len(rows) == 27 and d["candidate_total"] == 27, len(rows))
    c.need("cand/ids_unique", len({x["id"] for x in rows}) == 27, "duplicate candidate id")
    dist = {k: sum(1 for x in rows if x["classification"] == k) for k in CLASSES}
    c.need("cand/distribution", dist == EXPECTED_DIST and d["distribution"] == EXPECTED_DIST, dist)
    elig = [x["id"] for x in rows if x["classification"] in NEVER_ELIGIBLE and x["eligible_for_extraction"]]
    c.need("cand/forbidden_not_eligible", not elig, elig)
    missing_lim = [x["id"] for x in rows if x["classification"] == "EXTRACTABLE_WITH_LIMITATION"
                   and x["limitation_or_prohibition"] in ("", "none")]
    c.need("cand/limitations_retained", not missing_lim, missing_lim)
    unresolved = [x["id"] for x in rows if x["source_path"] and not x["source_resolved_at_p0"]]
    c.need("cand/source_refs_resolve", not unresolved, unresolved)
    c.need("cand/no_drift", d["drift_findings"] == [], d["drift_findings"])
    c.need("cand/b5_arithmetic_unchanged", sum(EXPECTED_DIST.values()) == 27, dist)
    names = {x["name"] for x in rows}
    c.need("cand/authority_bearing_never", all(
        x["book6_disposition"] in ("never_extractable_authority", "not_available_platform_internal",
                                   "not_available_private_api", "forbidden_constitutional",
                                   "study_only_no_copy", "none_absent", "design_input_rederive",
                                   "design_input_with_limitation", "book6_work_after_authorization")
        for x in rows), names)


def check_api(c: Checker) -> None:
    d = c.data("api")
    rows = d["symbols"]
    c.need("api/exports_zero", d["export_policy"]["exports_at_p0"] == 0, d["export_policy"])
    c.need("api/public_stable_zero", d["export_policy"]["public_stable_symbols"] == 0, d["distribution"])
    c.need("api/no_exported_rows", not any(x["exported_at_p0"] for x in rows), "exported at p0")
    syms = [x["symbol"] for x in rows if x["section"] != "PROHIBITED"]
    c.need("api/symbols_unique", len(syms) == len(set(syms)), "duplicate symbol")
    sections = {x["section"] for x in rows if x["section"] != "PROHIBITED"}
    c.need("api/all_sections_mapped", len(sections) == 25, sorted(sections))
    pub = [x for x in rows if x["classification"] == "public_experimental"]
    fields = ("typed_inputs", "typed_outputs", "error_behavior", "version_introduced",
              "compatibility_promise", "documentation_obligation", "tests_planned",
              "examples_planned", "owner")
    gaps = [x["symbol"] for x in pub for f in fields if x.get(f) in (None, "", [])]
    c.need("api/public_fields_complete", not gaps, gaps)
    c.need("api/prohibited_named", sum(1 for x in rows if x["classification"] == "prohibited") >= 5,
           d["distribution"])
    c.need("api/no_private", d["distribution"].get("private", 0) == 0, d["distribution"])
    computed = {k: sum(1 for x in rows if x["classification"] == k)
                for k in ("public_stable", "public_experimental", "internal", "private", "prohibited", "deferred")}
    c.need("api/classification_matches", computed == d["distribution"] and computed["public_stable"] == 0,
           {"declared": d["distribution"], "computed": computed})
    c.need("api/no_wildcards", not any("*" in s for s in syms), "wildcard export")


def check_sequence(c: Checker) -> None:
    d = c.data("sequence")
    stages = d["stages"]
    ids = [s["id"] for s in stages]
    c.need("stage/unique_ids", len(ids) == len(set(ids)), "duplicate stage")
    c.need("stage/count_11", len(stages) == 11, len(stages))
    c.need("stage/i0_to_i9", all(f"B6-I{i}" in ids for i in range(10)), ids)
    c.need("stage/p0_present", "B6-P0" in ids, ids)
    deps = {s["id"]: s["depends_on"] for s in stages}
    bad = [s for s in ids if any(dep not in deps for dep in deps[s])]
    c.need("stage/deps_resolve", not bad, bad)
    seen: set[str] = set()
    stack: set[str] = set()

    def visit(n: str) -> bool:
        if n in stack:
            return False
        if n in seen:
            return True
        stack.add(n)
        for dep in deps[n]:
            if not visit(dep):
                return False
        stack.discard(n)
        seen.add(n)
        return True

    c.need("stage/acyclic", all(visit(n) for n in ids), "cycle detected")
    mapped = [sec for s in stages for sec in s["sections"]]
    c.need("stage/sections_cover_25", sorted(mapped) == sorted(
        f"C{ch}.S{se}" for ch in range(1, 6) for se in range(1, 6)), (len(mapped), len(set(mapped))))
    c.need("stage/sections_unique", len(mapped) == len(set(mapped)), "duplicate section mapping")
    c.need("stage/recommend_i0", d["recommended_next_authorization"] == "B6-I0", d["recommended_next_authorization"])
    locked = [s["id"] for s in stages if s["kind"] == "implementation" and s["status"] != "LOCKED"]
    c.need("stage/others_locked", not locked, locked)
    c.need("stage/no_implementation_claim", not any(
        s["status"] == "COMPLETE" for s in stages), "completion claim")


def check_failures_and_threats(c: Checker) -> None:
    d = c.data("failure_registry")
    f = d["failure_classes"]
    c.need("fail/count_23", len(f) == 23 and d["failure_classes_total"] == 23, len(f))
    c.need("fail/unique", len({x["id"] for x in f}) == 23, "duplicate failure id")
    fields = ("trigger", "expected_refusal", "observable", "planned_test", "owner", "stage", "recovery", "negative_control")
    gaps = [x["id"] for x in f for k in fields if not x.get(k)]
    c.need("fail/fields", not gaps, gaps)
    vacuous = [x["id"] for x in f if x["negative_control"].strip().lower() == x["trigger"].strip().lower()]
    c.need("fail/negative_controls", not vacuous, vacuous)
    c.need("fail/all_bound", all(x["bound"] for x in f), "unbound failure class")
    t = d["threats"]
    c.need("threat/count_20", len(t) == 20 and d["threats_total"] == 20, len(t))
    tf = ("asset", "attacker_capability", "trust_boundary", "required_refusal",
          "planned_proof", "owner", "stage", "evidence_artifact")
    tg = [x["id"] for x in t for k in tf if not x.get(k)]
    c.need("threat/fields", not tg, tg)
    c.need("threat/mitigation_unclaimed", all(x["mitigation_state"] == "PLANNED_NOT_IMPLEMENTED" for x in t),
           "mitigation claimed")
    nc = d["negative_controls"]
    c.need("nc/count_16", len(nc) == 16, len(nc))


def check_compat(c: Checker) -> None:
    d = c.data("compat")
    v = d["versioning"]
    c.need("compat/versioning_fields", all(v.get(k) for k in v), "empty versioning field")
    rows = d["compatibility_matrix"]["rows"]
    c.need("compat/matrix_rows_25", len(rows) == 25, len(rows))
    c.need("compat/matrix_unproven", all(r["state"] == "UNPROVEN" for r in rows), "proven row")
    c.need("compat/no_latest", "latest" in v["unsupported_version_refusal"].lower(), v["unsupported_version_refusal"])
    rep = d["reproducibility"]
    c.need("repro/all_planned", rep["state"] == "ALL_PLANNED_NOT_IMPLEMENTED", rep["state"])
    c.need("repro/no_external", rep["external_service"] == "none" and rep["recurring_cost_usd"] == 0, rep)
    c.need("repro/requirements_15", len(rep["requirements"]) == 15, len(rep["requirements"]))


def check_handoff(c: Checker) -> None:
    g16 = json.loads(c.path(G16_PACKET).read_text(encoding="utf-8"))
    c.need("g16/open", g16["status_value"] == "OPEN" and g16["blocker"] == "B5I8-DF05", g16)
    handoff = json.loads(c.path(HANDOFF).read_text(encoding="utf-8"))
    c.need("g16/blocks_independence", "independence" in " ".join(handoff["g16"]["blocks"]), handoff["g16"])
    c.need("handoff/token", handoff["authorization_token_required"] == "AUTHORIZED_STAGE=B6-I0",
           handoff["authorization_token_required"])
    reg = c.data("registry")["locks"]["g16"]
    c.need("g16/registry_lock", reg == {"status": "OPEN", "blocker": "B5I8-DF05"}, reg)
    b5 = json.loads(c.path(B5_REGISTRY).read_text(encoding="utf-8"))
    c.need("g16/b5_registry_lock", b5["locks"]["g16"]["status"] == "OPEN", b5["locks"]["g16"])
    text = c.text(FILES["ledger"])
    c.need("g16/ledger_carries", "B5I8-DF05" in text and "OPEN" in text, "ledger omits G16")


def base_inventory(c: Checker) -> set[str]:
    if not (c.root / ".git").exists():
        return set()
    code, out = git(c, ["ls-tree", "-r", "--name-only", BASE_SHA])
    return set(out.splitlines()) if code == 0 else set()


def check_boundary(c: Checker) -> None:
    impl = [p for p in c.root.rglob("*") if p.is_file() and ".git" not in p.parts]
    base = base_inventory(c)
    rel = [str(p.relative_to(c.root)).replace("\\", "/") for p in impl]
    new_files = [r for r in rel if r not in base]
    hits = [r for r in new_files
            if re.search(r"(book[_-]?6|b6)[_-]", r.rsplit("/", 1)[-1], re.I)
            and not r.startswith(DOCS + "/" + P)]
    c.need("boundary/no_book6_named_artifacts", not hits, hits)
    tests = [r for r in new_files if "tests" in r.split("/") and re.search(r"b6|block_06", r, re.I)]
    c.need("boundary/no_b6_tests", not tests, tests)
    workflows = [r for r in new_files if ".github" in r.split("/") and re.search(r"b6|block.?06", r, re.I)]
    c.need("boundary/no_b6_workflow", not workflows, workflows)
    pkg = [r for r in new_files if r.rsplit("/", 1)[-1] in ("pyproject.toml", "setup.py", "setup.cfg")]
    c.need("boundary/no_new_packaging", not pkg, pkg)


def check_text_hygiene(c: Checker) -> None:
    trailing, mixed, noeol = [], [], []
    for key in FILES:
        raw = c.path(FILES[key]).read_bytes()
        if raw and not raw.endswith(b"\n"):
            noeol.append(FILES[key])
        crlf = b"\r\n" in raw
        lf_only = raw.replace(b"\r\n", b"").count(b"\n") > 0
        if crlf and lf_only:
            mixed.append(FILES[key])
        text = raw.decode("utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if line != line.rstrip():
                trailing.append(f"{FILES[key]}:{i}")
    c.need("text/final_newline", not noeol, noeol)
    c.need("text/consistent_newlines", not mixed, mixed)
    c.need("text/no_trailing_whitespace", not trailing, trailing[:10])


def check_secrets_and_urls(c: Checker) -> None:
    secrets, urls = [], []
    for key in FILES:
        text = c.text(FILES[key])
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                secrets.append(F"{FILES[key]}:{pat.pattern[:20]}")
        if URL_PATTERN.search(text):
            urls.append(FILES[key])
    c.need("security/no_secrets", not secrets, secrets)
    c.need("security/no_external_urls", not urls, urls)


def check_docs_tokens(c: Checker) -> None:
    need = {
        "authority": ["Constitution", "Block 6", "B5-I9", "G16"],
        "identity": ["BOOK_6_IDENTITY", "BOOK_6_FIRST_STAGE", "BOOK_6_ENTRY_GATE",
                     "BOOK_6_COMPLETION_GATE", "BOOK_6_IMPLEMENTATION_STARTED = false"],
        "construction": ["B6-I0", "B6-I9", "LOCKED", "mutation"],
        "failure_plan": ["F01", "F23", "negative"],
        "threat": ["T01", "T20", "trust"],
        "versioning": ["semver", "UNPROVEN", "refus"],
        "repro": ["SHA-256", "provenance", "deterministic"],
        "evaluation": ["POST_BOOK_6_EVALUATION_SYSTEM — RESERVED, NOT AUTHORIZED"],
        "acceptance": ["P0-01", "P0-28"],
        "ledger": ["B5I8-DF05", BASE_SHA, "BOOK_6_IMPLEMENTATION_STARTED = false"],
    }
    for key, tokens in need.items():
        text = c.text(FILES[key])
        missing = [t for t in tokens if t not in text]
        c.need(f"docs/{key}_content", not missing, missing)


def check_acceptance_matrix(c: Checker) -> None:
    text = c.text(FILES["acceptance"])
    rows = re.findall(r"^\| (P0-\d{2}) \|", text, re.M)
    c.need("acceptance/rows_28", len(rows) == 28, len(rows))
    c.need("acceptance/ids_unique", len(set(rows)) == 28, "duplicate acceptance id")


def git(c: Checker, args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(["git", *args], cwd=c.root, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def check_git(c: Checker) -> None:
    if not (c.root / ".git").exists():
        c.ok("git/skipped_scratch_root")
        return
    code, base = git(c, ["rev-parse", "origin/main"])
    if code != 0:
        c.fail("git/base_resolves", base)
        return
    c.need("git/base_is_locked", base == BASE_SHA, base)
    code, out = git(c, ["diff", "--name-only", f"{BASE_SHA}..HEAD"])
    changed = [x for x in out.splitlines() if x.strip()]
    outside = [p for p in changed if not p.startswith(ALLOWED_PREFIXES)]
    c.need("git/changed_boundary", not outside, outside)
    forbidden = [p for p in changed if p.startswith(FORBIDDEN_DIFF_PREFIXES)]
    c.need("git/forbidden_surfaces", not forbidden, forbidden)
    code, out = git(c, ["diff", "--check", f"{BASE_SHA}..HEAD"])
    c.need("git/diff_check", code == 0, out)
    code, tree = git(c, ["rev-parse", "HEAD^{tree}"])
    c.need("git/tree_resolves", code == 0, tree)


def run(root: pathlib.Path) -> dict:
    c = Checker(root)
    for fn in (check_packet_files, check_canonical_json, check_identity_and_locks,
               check_requirements, check_candidates, check_api, check_sequence,
               check_failures_and_threats, check_compat, check_handoff, check_boundary,
               check_text_hygiene, check_secrets_and_urls, check_docs_tokens,
               check_acceptance_matrix, check_git):
        fn(c)
    status = "PASS" if not c.failures else "FAIL"
    payload = {
        "validator": "block_06_p0_validate.py",
        "status": status,
        "checks": len(c.checks),
        "failures": len(c.failures),
        "failure_detail": c.failures,
        "base_sha": BASE_SHA,
        "root": "." if root == repo_root() else str(root),
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
    if payload["failures"]:
        for f in payload["failure_detail"]:
            print(f"FAIL {f['check']}: {f['detail']}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
