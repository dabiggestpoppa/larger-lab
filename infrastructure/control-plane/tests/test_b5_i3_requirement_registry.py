"""B5-I3 requirement-test registry proofs (charter increment I-2, plan anchor B5-I3).

Executable proof for the frozen P0 contract (OCE_B5_I3_IMPLEMENTATION_CONTRACT_v1.0.md
sections 4, 6, 12, 13, 14, 15): the machine-readable requirement-test registry is
complete, closed, deterministic and bound to executable tests.

Selection topology (each binding's execution_surface names its authoritative home):
- ``b5-i2-selection-step`` — nodes selected by the existing B5-I2 whole-file steps
  in ``b1-i1r-validation.yml`` (proven by workflow-text reconciliation);
- ``book2-mandatory-registry`` — engine nodes listed in the Book 2 mandatory node
  registry ``scripts/b2_registry.py`` (proven by dotted-node membership per node);
- ``shared-validation-runner`` — the authoritative ``run-validation.sh`` runner step
  (proven by script existence + workflow step presence).

Console-as-client law: this suite reads committed artifacts and runs pytest
collection only; no socket, no canonical-state write, no LLM/hosting/provider import.
Deterministic: validators are pure and return stable, ordered problem lists; registry
bytes must equal the canonical serialization. Selected in CI by the step
"Execute B5-I3 requirement registry proofs" in .github/workflows/b1-i1r-validation.yml.
"""
from __future__ import annotations

import ast
import hashlib
import importlib
import json
import re
import subprocess
import sys
from pathlib import Path

# Repo root: tests/ -> control-plane/ -> infrastructure/ -> root
ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = ROOT / "docs" / "oce-golden-system" / "OCE_B5_I3_REQUIREMENT_TEST_REGISTRY_v1.0.json"
FAILURE_MATRIX_PATH = ROOT / "docs" / "oce-golden-system" / "OCE_B5_I3_FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md"
CONSTRUCTION_PLAN_PATH = ROOT / "docs" / "oce-golden-system" / "OCE_B5_I3_CONSTRUCTION_PLAN_v1.0.md"
CONTRACT_PATH = ROOT / "docs" / "oce-golden-system" / "OCE_B5_I3_IMPLEMENTATION_CONTRACT_v1.0.md"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "b1-i1r-validation.yml"
BOOK2_REGISTRY_PATH = ROOT / "infrastructure" / "control-plane" / "scripts" / "b2_registry.py"
CONTRACT_PACK_PATH = ROOT / "infrastructure" / "control-plane" / "contracts" / "console-contract.json"

# --- Frozen P0 contract constants (section 4 / section 12) --------------------
REGISTRY_ID = "OCE-B5-I3-REGISTRY-001"
REGISTRY_VERSION = "1.0"
CHARTER_INCREMENT = "I-2"
PLAN_ANCHOR = "B5-I3"
BASE_SHA = "c60e07456559431e560ac4d69141063dd89a9325"
CHARTER_REL = "docs/oce-golden-system/OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md"
CHARTER_SECTION = "## 11. Acceptance gates"
FROZEN_PACK_SHA256 = "45bcb4f63fdb44c039e81fa51ac01a877bb05faee048efa8193ed7fc16af14aa"

TOP_LEVEL_KEYS = frozenset({
    "registry_id", "registry_version", "charter", "charter_increment",
    "plan_anchor", "base_sha", "requirement_set", "entries",
})
CHARTER_REF_KEYS = frozenset({"document", "section"})
ENTRY_REQUIRED_KEYS = frozenset({
    "id", "kind", "source", "requirement", "test_class", "binding", "mapping_status",
})
ENTRY_OPTIONAL_KEYS = frozenset({
    "attestation", "corroborations", "deferred", "notes", "contract_surface",
})
ENTRY_ALL_KEYS = ENTRY_REQUIRED_KEYS | ENTRY_OPTIONAL_KEYS

BINDING_REQUIRED_KEYS = {
    "test": frozenset({"type", "file", "node", "execution_surface"}),
    "runner": frozenset({"type", "script", "execution_surface", "note"}),
    "attestation": frozenset({"type", "document", "section"}),
    "deferred": frozenset({"type", "owner", "planned_node", "reason"}),
}
CORROBORATION_KEYS = frozenset({"file", "node", "execution_surface"})
DEFERRED_KEYS = frozenset({"owner", "planned_node", "reason"})
ATTESTATION_KEYS = frozenset({"document", "section"})

MAPPING_STATUS_VOCABULARY = frozenset({"NOT_YET_PROVEN", "MAPPED"})
EXECUTION_SURFACE_VOCABULARY = ("b5-i2-selection-step", "book2-mandatory-registry", "shared-validation-runner")
BINDING_TYPE_VOCABULARY = ("attestation", "deferred", "runner", "test")
DEFERRED_OWNER_VOCABULARY = ("B5-I8", "I-3", "I-4", "I-5", "I-6", "I-7", "I-8")

KIND_BY_PREFIX = {"G": "gate", "S": "scenario", "F": "failure_class"}

# Test-side authority citations (contract sections the registry itself cannot carry
# as top-level keys under the frozen section-4 key set).
AUTHORITY_DOCS = {
    "plan": ("docs/oce-golden-system/OCE_BLOCK_05_REFERENCE_APPLICATION_FACTORY_PLAN_v1.0.md",
             "B5.C2.S4 Failure behavior"),
    "packet": ("docs/oce-golden-system/OCE_B5_I1_CAND-004_EVIDENCE_PACKET_v1.0.md",
               "## 2. Operator-testable acceptance scenarios"),
    "ledger": ("docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md",
               "## 6. Accounting"),
    "contract": ("docs/oce-golden-system/OCE_B5_I3_IMPLEMENTATION_CONTRACT_v1.0.md",
                 "## 13. Test architecture"),
}

# Selection declarations (contract section 15): the single added step selects the
# B5-I3 file; preexisting B5-I2 steps keep their whole-file selections.
B5_I2_STEP_FILES = {
    "Execute B5-I2 console-contract proofs (whole-file selection)":
        "infrastructure/control-plane/tests/test_console_contracts.py",
    "Execute B5-I2 reproducibility harness (integrity + battery)":
        "infrastructure/control-plane/tests/test_b5_i2_mutation_harness.py",
}
B5_I2_COLLECT_FLOORS = {
    "infrastructure/control-plane/tests/test_console_contracts.py": 24,
    "infrastructure/control-plane/tests/test_b5_i2_mutation_harness.py": 16,
}
B5_I3_STEP_NAME = "Execute B5-I3 requirement registry proofs"
RUNNER_STEP_NAME = "Run shared authoritative validation runner"
REGISTRY_TEST_FILE = "infrastructure/control-plane/tests/test_b5_i3_requirement_registry.py"

# Frozen B5-I2 instruments + production tree (contract section 2): none may change
# between BASE_SHA and HEAD.
FROZEN_DIFF_PATHS = (
    "infrastructure/control-plane/src/",
    "infrastructure/control-plane/contracts/",
    "infrastructure/control-plane/tests/test_console_contracts.py",
    "infrastructure/control-plane/tests/test_b5_i2_mutation_harness.py",
)
SRC_MODULES = frozenset({
    "__init__", "api", "audit_sink", "authority", "boundaries", "clocks", "config_spine",
    "config_startup", "console_contracts", "events", "evidence", "execution_runtime",
    "hashes", "health", "http_api", "job_store", "local_lifecycle", "local_secrets",
    "openclaw_adapter", "pg_scheduler", "pg_store", "pg_worker", "plane", "recovery",
    "redis_transport", "representative_jobs", "scheduler", "schema_validator",
    "state_machines", "worker", "worker_client", "worker_contracts", "worker_fabric",
    "worker_fabric_store", "worker_identity", "worker_leases", "worker_loop",
    "worker_protocol", "worker_sessions", "worker_supervisor",
})
SELF_IMPORT_ALLOWLIST = {"__future__", "ast", "hashlib", "importlib", "json", "re",
                         "subprocess", "sys", "pathlib", "pytest", "oce_control"}

MAX_REGISTRY_BYTES = 65536
MAX_STRING_FIELD_CHARS = 4096

NODE_RE = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_]*::)*test_[a-z0-9_]+$")
PLANNED_NODE_RE = re.compile(
    r"^infrastructure/control-plane/tests/test_[a-z0-9_]+\.py"
    r"(?:::[A-Za-z_][A-Za-z0-9_]*)*::test_[a-z0-9_]+$"
)
BOUND_FILE_RE = re.compile(r"^infrastructure/control-plane/tests/test_[a-z0-9_]+\.py$")
SCRIPT_RE = re.compile(r"^infrastructure/[A-Za-z0-9_/\-]+\.sh$")
REL_DOC_RE = re.compile(r"^docs/oce-golden-system/[A-Za-z0-9_.\-]+\.md$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

FORBIDDEN_CONTENT = (
    ("absolute_windows_path", re.compile(r"[A-Za-z]:[\\/]")),
    ("absolute_unix_path", re.compile(r"^/(?:home|Users|tmp|var|etc|opt)/")),
    ("url", re.compile(r"https?://")),
    ("iso_timestamp", re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")),
    ("duration", re.compile(r"\b\d+(?:\.\d+)?\s*(?:ms|seconds?|secs?|minutes?|mins?|hours?|hrs?)\b", re.I)),
    ("hosting_provider", re.compile(r"\b(?:vercel|railway|sonarcloud|heroku|cloudflare)\b", re.I)),
    ("cloud_provider", re.compile(r"\b(?:aws|gcp|azure)\b", re.I)),
    ("model_vendor", re.compile(r"\b(?:gpt|claude|llama|openai|anthropic)\b", re.I)),
    ("secret_assignment", re.compile(r"(?i)\b(?:api[_-]?key|password|secret)\s*[=:]")),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
)


def expected_requirement_ids() -> list[str]:
    """The exact, ordered (sorted-by-id, per contract section 7) requirement set."""
    ids = [f"G{n}" for n in range(1, 18)] + [f"S-{n}" for n in range(1, 5)] + [f"F-{n}" for n in range(1, 8)]
    return sorted(ids)


def load_registry() -> tuple[bytes, dict]:
    raw = REGISTRY_PATH.read_bytes()
    return raw, json.loads(raw.decode("utf-8"))


def canonical_bytes(registry: dict) -> bytes:
    return (json.dumps(registry, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def pack_surfaces() -> dict[str, dict]:
    """The live 12-surface vocabulary (9 reads + 3 invokes) from the frozen pack."""
    pack = json.loads(CONTRACT_PACK_PATH.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for section in ("reads", "invokes"):
        for entry in pack[section]:
            out[entry["surface"]] = entry
    return out


def git_blob_bytes(rel_path: str) -> bytes:
    """Committed (git blob) bytes for a path — identical on every platform,
    independent of the checkout machine's core.autocrlf translation."""
    proc = subprocess.run(["git", "show", f"HEAD:{rel_path}"], cwd=str(ROOT),
                          capture_output=True, check=True)
    return proc.stdout


def blob_sha256(rel_path: str) -> str:
    """SHA-256 of the COMMITTED (git blob, LF-canonical) bytes — platform independent."""
    return hashlib.sha256(git_blob_bytes(rel_path)).hexdigest()


def git_changed_paths(args: list[str]) -> list[str]:
    proc = subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True)
    assert proc.returncode == 0, f"git failed: {proc.stderr.strip()}"
    return sorted(line for line in proc.stdout.splitlines() if line.strip())


def book2_dotted(file_rel: str, node: str) -> str:
    """B2 mandatory-registry node form: dotted module path + Class::test."""
    module = file_rel[:-3].replace("/", ".")
    return f"{module}.{node}" if "::" in node else f"{module}::{node}"


def _walk_strings(node, path="registry"):
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for key in sorted(node):
            yield from _walk_strings(node[key], f"{path}.{key}")
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from _walk_strings(item, f"{path}[{i}]")


def registry_problems(registry: dict, raw: bytes | None = None) -> list[str]:
    """Closed-form validator per contract sections 4/6/13. Pure and deterministic:
    the positive tests require an empty list; the negative controls require a
    named problem code for each mutation."""
    problems: list[str] = []

    # -- top-level closure (exact key set, types, pinned constants) ---------
    if set(registry) != TOP_LEVEL_KEYS:
        missing = sorted(TOP_LEVEL_KEYS - set(registry))
        extra = sorted(set(registry) - TOP_LEVEL_KEYS)
        problems.append(f"top-level-keys: missing={missing} extra={extra}")
    if registry.get("registry_id") != REGISTRY_ID:
        problems.append(f"registry-id: {registry.get('registry_id')!r}")
    if registry.get("registry_version") != REGISTRY_VERSION:
        problems.append(f"registry-version: {registry.get('registry_version')!r}")
    if registry.get("charter_increment") != CHARTER_INCREMENT:
        problems.append(f"charter-increment: {registry.get('charter_increment')!r}")
    if registry.get("plan_anchor") != PLAN_ANCHOR:
        problems.append(f"plan-anchor: {registry.get('plan_anchor')!r}")
    if registry.get("base_sha") != BASE_SHA or not SHA_RE.match(str(registry.get("base_sha", ""))):
        problems.append(f"base-sha: {registry.get('base_sha')!r}")

    charter = registry.get("charter")
    if not isinstance(charter, dict) or set(charter) != CHARTER_REF_KEYS:
        problems.append(f"charter-keys: {charter!r}")
    else:
        if charter.get("document") != CHARTER_REL or not REL_DOC_RE.match(charter.get("document", "")):
            problems.append(f"charter-document: {charter.get('document')!r}")
        elif charter.get("section") != CHARTER_SECTION:
            problems.append(f"charter-section: {charter.get('section')!r}")
        else:
            doc = ROOT / charter["document"]
            if not doc.is_file():
                problems.append(f"charter-document-missing: {charter['document']}")
            elif charter["section"] not in doc.read_text(encoding="utf-8", errors="replace"):
                problems.append(f"charter-section-not-found: {charter['section']!r}")

    # -- entries ------------------------------------------------------------
    entries = registry.get("entries")
    if not isinstance(entries, list):
        problems.append("entries: not a list")
        return problems

    ids = [e.get("id") if isinstance(e, dict) else None for e in entries]
    expected = expected_requirement_ids()
    if ids != expected:
        problems.append(f"requirement-ids: got={ids}")
    if ids != sorted(i for i in ids if i):
        problems.append("entries-not-sorted: ids must be sorted (contract section 7)")
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        problems.append(f"duplicate-ids:{dupes}")
    if registry.get("requirement_set") != expected:
        problems.append(f"requirement-set: got={registry.get('requirement_set')!r}")

    surfaces = pack_surfaces()
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            problems.append(f"entry-not-dict:{idx}")
            continue
        eid = entry.get("id", f"<{idx}>")
        keys = set(entry)
        missing = sorted(ENTRY_REQUIRED_KEYS - keys)
        extra = sorted(keys - ENTRY_ALL_KEYS)
        if missing or extra:
            problems.append(f"entry-keys:{eid}: missing={missing} extra={extra}")

        prefix = re.match(r"^([A-Z])", eid or "")
        want_kind = KIND_BY_PREFIX.get(prefix.group(1)) if prefix else None
        if entry.get("kind") != want_kind:
            problems.append(f"kind-mismatch:{eid}:{entry.get('kind')!r}!={want_kind!r}")

        if entry.get("mapping_status") not in MAPPING_STATUS_VOCABULARY:
            problems.append(f"mapping-status:{eid}:{entry.get('mapping_status')!r}")

        for field in ("source", "requirement", "test_class"):
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                problems.append(f"empty-field:{eid}:{field}")

        if "contract_surface" in entry:
            if entry["contract_surface"] not in surfaces:
                problems.append(f"contract-surface:{eid}:{entry['contract_surface']!r}")

        binding = entry.get("binding")
        if not isinstance(binding, dict):
            problems.append(f"binding-not-dict:{eid}")
        else:
            btype = binding.get("type")
            if btype not in BINDING_TYPE_VOCABULARY:
                problems.append(f"binding-type:{eid}:{btype!r}")
            else:
                want_keys = BINDING_REQUIRED_KEYS[btype]
                if set(binding) != want_keys:
                    problems.append(f"binding-keys:{eid}:{btype}: got={sorted(binding)} want={sorted(want_keys)}")
                if btype == "test":
                    if not BOUND_FILE_RE.match(binding.get("file", "")):
                        problems.append(f"binding-file-format:{eid}:{binding.get('file')!r}")
                    if not NODE_RE.match(binding.get("node", "")):
                        problems.append(f"binding-node-format:{eid}:{binding.get('node')!r}")
                    if binding.get("execution_surface") not in EXECUTION_SURFACE_VOCABULARY:
                        problems.append(f"binding-surface:{eid}:{binding.get('execution_surface')!r}")
                    if binding.get("file") == REGISTRY_TEST_FILE:
                        problems.append(f"binding-self-reference:{eid}")
                elif btype == "runner":
                    if not SCRIPT_RE.match(binding.get("script", "")):
                        problems.append(f"runner-script-format:{eid}:{binding.get('script')!r}")
                    if binding.get("execution_surface") not in EXECUTION_SURFACE_VOCABULARY:
                        problems.append(f"runner-surface:{eid}:{binding.get('execution_surface')!r}")
                    if not isinstance(binding.get("note"), str) or not binding["note"].strip():
                        problems.append(f"runner-note-empty:{eid}")
                elif btype == "attestation":
                    if not REL_DOC_RE.match(binding.get("document", "")):
                        problems.append(f"attestation-document-format:{eid}:{binding.get('document')!r}")
                    if not isinstance(binding.get("section"), str) or not binding["section"].strip():
                        problems.append(f"attestation-section-empty:{eid}")
                elif btype == "deferred":
                    if binding.get("owner") not in DEFERRED_OWNER_VOCABULARY:
                        problems.append(f"deferred-owner:{eid}:{binding.get('owner')!r}")
                    if not PLANNED_NODE_RE.match(binding.get("planned_node", "")):
                        problems.append(f"deferred-planned-node:{eid}:{binding.get('planned_node')!r}")
                    if not isinstance(binding.get("reason"), str) or not binding["reason"].strip():
                        problems.append(f"deferred-reason-empty:{eid}")

        corroborations = entry.get("corroborations", [])
        if not isinstance(corroborations, list):
            problems.append(f"corroborations-not-list:{eid}")
        else:
            for i, corr in enumerate(corroborations):
                if not isinstance(corr, dict) or set(corr) != CORROBORATION_KEYS:
                    problems.append(f"corroboration-keys:{eid}:{i}")
                    continue
                if not BOUND_FILE_RE.match(corr.get("file", "")):
                    problems.append(f"corroboration-file-format:{eid}:{i}:{corr.get('file')!r}")
                if not NODE_RE.match(corr.get("node", "")):
                    problems.append(f"corroboration-node-format:{eid}:{i}:{corr.get('node')!r}")
                if corr.get("execution_surface") not in EXECUTION_SURFACE_VOCABULARY:
                    problems.append(f"corroboration-surface:{eid}:{i}:{corr.get('execution_surface')!r}")
                if corr.get("file") == REGISTRY_TEST_FILE:
                    problems.append(f"corroboration-self-reference:{eid}:{i}")

        if "attestation" in entry:
            att = entry["attestation"]
            if not isinstance(att, dict) or set(att) != ATTESTATION_KEYS:
                problems.append(f"attestation-keys:{eid}")
            else:
                if not REL_DOC_RE.match(att.get("document", "")):
                    problems.append(f"attestation-document-format:{eid}:{att.get('document')!r}")
                if not isinstance(att.get("section"), str) or not att["section"].strip():
                    problems.append(f"attestation-section-empty:{eid}")

        if "deferred" in entry:
            deferred = entry["deferred"]
            if not isinstance(deferred, dict) or set(deferred) != DEFERRED_KEYS:
                problems.append(f"deferred-keys:{eid}")
            else:
                if deferred.get("owner") not in DEFERRED_OWNER_VOCABULARY:
                    problems.append(f"deferred-owner:{eid}:{deferred.get('owner')!r}")
                if not PLANNED_NODE_RE.match(deferred.get("planned_node", "")):
                    problems.append(f"deferred-planned-node:{eid}:{deferred.get('planned_node')!r}")
                if not isinstance(deferred.get("reason"), str) or not deferred["reason"].strip():
                    problems.append(f"deferred-reason-empty:{eid}")

        # Charter section 12 law: no executable binding means an explicitly
        # deferred owner must exist, carried inside the deferred binding itself.
        if isinstance(binding, dict) and binding.get("type") == "deferred":
            if binding.get("owner") not in DEFERRED_OWNER_VOCABULARY:
                problems.append(f"deferred-only-without-owner:{eid}")

    # -- bounded sizes and forbidden content over the whole document ---------
    if raw is not None:
        if len(raw) > MAX_REGISTRY_BYTES:
            problems.append(f"registry-too-large:{len(raw)}>{MAX_REGISTRY_BYTES}")
    for path, value in _walk_strings(registry):
        if len(value) > MAX_STRING_FIELD_CHARS:
            problems.append(f"string-too-long:{path}:{len(value)}")
        for name, pattern in FORBIDDEN_CONTENT:
            if pattern.search(value):
                problems.append(f"forbidden-content:{name}:{path}")

    return problems


def binding_targets(registry: dict) -> list[dict]:
    """All declared test targets: primary bindings plus corroborations."""
    targets: list[dict] = []
    for entry in registry["entries"]:
        binding = entry["binding"]
        if binding.get("type") == "test":
            targets.append(binding)
        targets.extend(entry.get("corroborations", []))
    return targets


def missing_bound_nodes(registry: dict) -> dict[str, list[str]]:
    """Collection-equality proof: per distinct file, the declared nodes that are
    absent from actual pytest collection. Shared by the positive proof and the
    N3 forged-node negative control (one code path, no mock bypass)."""
    wanted: dict[str, set[str]] = {}
    for target in binding_targets(registry):
        wanted.setdefault(target["file"], set()).add(target["node"])
    missing: dict[str, list[str]] = {}
    for file_rel in sorted(wanted):
        collected = _collect_nodes(file_rel)
        absent = sorted(wanted[file_rel] - collected)
        if absent:
            missing[file_rel] = absent
    return missing


def _collect_nodes(file_rel: str) -> set[str]:
    """Subprocess pytest collection for one file; node ids with file prefix stripped."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", file_rel, "--collect-only", "-q", "-o", "addopts="],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    nodes: set[str] = set()
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("infrastructure/") and "::" in line:
            file_part, _, node_part = line.partition("::")
            if file_part == file_rel:
                nodes.add(node_part)
    return nodes


def engine_ownership_violations(pack: dict) -> list[str]:
    """Gate G8 trace audit: the console pack may bind only governed read/invoke
    operations. Pure function so the negative control can feed a mutated pack."""
    violations: list[str] = []
    forbidden_tokens = ("recovery", "scheduler", "store", "persist", "write", "mutate")

    def walk(node, path):
        if isinstance(node, dict):
            for key in sorted(node):
                walk(node[key], f"{path}.{key}")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]")
        elif isinstance(node, str):
            lowered = node.lower()
            for token in forbidden_tokens:
                if token in lowered:
                    violations.append(f"{path}: forbidden token {token!r} in {node!r}")

    walk(pack, "pack")
    return violations


class TestRegistryStructure:
    """Contract section 4: parse, canonical bytes, closed keys, types, bounds."""

    def test_registry_file_parses(self):
        raw, _ = load_registry()
        assert raw, "registry must not be empty"

    def test_registry_committed_blob_is_canonical(self):
        """The committed artifact bytes (what CI and auditors consume) must be
        exactly the canonical serialization — asserted on the git blob, so the
        proof holds on Windows and Linux regardless of core.autocrlf."""
        blob = git_blob_bytes("docs/oce-golden-system/OCE_B5_I3_REQUIREMENT_TEST_REGISTRY_v1.0.json")
        registry = json.loads(blob.decode("utf-8"))
        assert blob == canonical_bytes(registry), (
            "committed registry bytes must equal json.dumps(indent=2, sort_keys=True) + LF newline")

    def test_registry_working_copy_is_canonical_modulo_git_eol(self):
        """Working-copy content must be canonical once git's declared EOL
        translation (core.autocrlf) is undone — content law, not environment."""
        raw, registry = load_registry()
        normalized = raw.replace(b"\r\n", b"\n")
        assert normalized == canonical_bytes(registry), (
            "working-copy content must equal the canonical serialization (after CRLF->LF)")

    def test_registry_is_deterministic_across_loads(self):
        raw_a, reg_a = load_registry()
        raw_b, reg_b = load_registry()
        assert raw_a == raw_b
        assert canonical_bytes(reg_a) == canonical_bytes(reg_b)

    def test_registry_within_size_bounds(self):
        raw, _ = load_registry()
        assert len(raw) <= MAX_REGISTRY_BYTES

    def test_registry_has_no_structural_problems(self):
        raw, registry = load_registry()
        problems = registry_problems(registry, raw)
        assert problems == [], f"registry problems: {problems}"

    def test_top_level_types(self):
        _, registry = load_registry()
        assert isinstance(registry["registry_id"], str)
        assert isinstance(registry["registry_version"], str)
        assert isinstance(registry["charter"], dict)
        assert isinstance(registry["charter_increment"], str)
        assert isinstance(registry["plan_anchor"], str)
        assert isinstance(registry["base_sha"], str)
        assert isinstance(registry["requirement_set"], list)
        assert all(isinstance(i, str) for i in registry["requirement_set"])
        assert isinstance(registry["entries"], list)

    def test_pinned_identity_constants(self):
        _, registry = load_registry()
        assert registry["registry_id"] == REGISTRY_ID
        assert registry["registry_version"] == REGISTRY_VERSION
        assert registry["charter_increment"] == CHARTER_INCREMENT
        assert registry["plan_anchor"] == PLAN_ANCHOR
        assert registry["base_sha"] == BASE_SHA

    def test_authority_documents_exist_with_sections(self):
        _, registry = load_registry()
        charter = registry["charter"]
        charter_doc = ROOT / charter["document"]
        assert charter_doc.is_file()
        assert charter["section"] in charter_doc.read_text(encoding="utf-8", errors="replace")
        for name, (doc_rel, section) in sorted(AUTHORITY_DOCS.items()):
            doc = ROOT / doc_rel
            assert doc.is_file(), f"{name} document missing: {doc_rel}"
            text = doc.read_text(encoding="utf-8", errors="replace")
            assert section in text, f"{name} section missing: {section!r}"


class TestRequirementClosure:
    """Contract section 13: exact 28-id set, sorted, unique, kinds, vocabularies."""

    def test_requirement_ids_exact_and_sorted(self):
        _, registry = load_registry()
        ids = [e["id"] for e in registry["entries"]]
        assert ids == expected_requirement_ids()
        assert registry["requirement_set"] == ids

    def test_every_kind_classified_exactly_once(self):
        _, registry = load_registry()
        kinds: dict[str, int] = {}
        for entry in registry["entries"]:
            kinds[entry["kind"]] = kinds.get(entry["kind"], 0) + 1
            prefix = re.match(r"^([A-Z])", entry["id"]).group(1)
            assert entry["kind"] == KIND_BY_PREFIX[prefix], entry["id"]
        assert kinds == {"gate": 17, "scenario": 4, "failure_class": 7}

    def test_every_entry_has_authority_citation_and_text(self):
        _, registry = load_registry()
        for entry in registry["entries"]:
            for field in ("source", "requirement", "test_class"):
                value = entry[field]
                assert isinstance(value, str) and value.strip(), f"{entry['id']}.{field}"
            assert "section" in entry["source"] or "packet" in entry["source"], entry["id"]

    def test_mapping_status_vocabulary_closed(self):
        _, registry = load_registry()
        for entry in registry["entries"]:
            assert entry["mapping_status"] in MAPPING_STATUS_VOCABULARY, entry["id"]

    def test_contract_surfaces_resolve_against_live_pack(self):
        _, registry = load_registry()
        surfaces = pack_surfaces()
        assert len(surfaces) == 12, f"pack must declare exactly 12 surfaces, got {len(surfaces)}"
        tagged = [e for e in registry["entries"] if "contract_surface" in e]
        assert tagged, "contract-surface references must not be vacuous"
        for entry in tagged:
            assert entry["contract_surface"] in surfaces, entry["id"]


class TestDeferredOwners:
    """Contract section 13: closed owner vocabulary, planned-node grammar, reasons."""

    # Deferred-eligible: every registry requirement may carry a residual-surface
    # deferral; the laws that matter are owner/grammar/reason closure below.
    DEFERRED_ELIGIBLE_IDS = frozenset(expected_requirement_ids())

    def _deferred_parts(self, registry):
        for entry in registry["entries"]:
            if entry["binding"]["type"] == "deferred":
                yield entry["id"], entry["binding"]
            if "deferred" in entry:
                yield entry["id"], entry["deferred"]

    def test_deferred_owners_in_closed_vocabulary(self):
        _, registry = load_registry()
        seen = []
        for eid, part in self._deferred_parts(registry):
            assert eid in self.DEFERRED_ELIGIBLE_IDS, f"deferral on ineligible id {eid}"
            assert part["owner"] in DEFERRED_OWNER_VOCABULARY, f"{eid}: {part['owner']!r}"
            seen.append(part["owner"])
        assert seen, "at least one deferred owner must exist (charter I-2 vocabulary exercised)"

    def test_planned_nodes_match_grammar_and_stay_in_tests_root(self):
        _, registry = load_registry()
        for eid, part in self._deferred_parts(registry):
            assert PLANNED_NODE_RE.match(part["planned_node"]), f"{eid}: {part['planned_node']!r}"

    def test_every_deferral_carries_nonempty_reason(self):
        _, registry = load_registry()
        for eid, part in self._deferred_parts(registry):
            assert isinstance(part["reason"], str) and part["reason"].strip(), eid


class TestExecutableBindings:
    """Contract section 13: file existence, collection equality, surface
    reconciliation against each binding's authoritative selection home."""

    def test_every_bound_file_exists(self):
        _, registry = load_registry()
        files = {t["file"] for t in binding_targets(registry)}
        for file_rel in sorted(files):
            assert (ROOT / file_rel).is_file(), f"bound file missing: {file_rel}"

    def test_every_bound_node_collects(self):
        _, registry = load_registry()
        missing = missing_bound_nodes(registry)
        assert missing == {}, f"declared nodes not collected: {missing}"

    def test_b5_i2_surface_files_selected_by_preexisting_steps(self):
        _, registry = load_registry()
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        for step_name, file_rel in sorted(B5_I2_STEP_FILES.items()):
            assert step_name in workflow, f"workflow lost step: {step_name}"
            assert file_rel in workflow, f"workflow does not select {file_rel}"
        for target in binding_targets(registry):
            if target["execution_surface"] == "b5-i2-selection-step":
                assert target["file"] in B5_I2_STEP_FILES.values(), target["file"]

    def test_book2_surface_nodes_in_mandatory_registry(self):
        """Every book2-mandatory-registry node must be a listed member of the
        Book 2 mandatory node registry (dotted form), asserted per node."""
        _, registry = load_registry()
        b2_text = BOOK2_REGISTRY_PATH.read_text(encoding="utf-8")
        checked = 0
        for target in binding_targets(registry):
            if target["execution_surface"] != "book2-mandatory-registry":
                continue
            checked += 1
            dotted = book2_dotted(target["file"], target["node"])
            assert dotted in b2_text, f"not in Book 2 mandatory registry: {dotted}"
        assert checked >= 20, f"book2 surface unexpectedly small: {checked}"

    def test_runner_surface_names_the_shared_runner(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        assert RUNNER_STEP_NAME in workflow, "shared runner step missing from workflow"
        assert "run-validation.sh" in workflow

    def test_b5_i3_step_reconciles_with_workflow(self):
        """The single added step (contract section 15) is either still pending —
        its file must exist on disk — or materialized — its file must appear in
        the workflow. The state is asserted truthfully, never assumed."""
        _, registry = load_registry()
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        materialized = B5_I3_STEP_NAME in workflow
        assert (ROOT / REGISTRY_TEST_FILE).is_file()
        if materialized:
            assert REGISTRY_TEST_FILE in workflow, (
                "B5-I3 step present but the registry test file is not selected by it")

    def test_runner_and_attestation_bindings_resolve(self):
        _, registry = load_registry()
        for entry in registry["entries"]:
            binding = entry["binding"]
            if binding["type"] == "runner":
                script = ROOT / binding["script"]
                assert script.is_file(), f"runner script missing: {binding['script']}"
                assert binding["script"] == "infrastructure/cloud-ground/scripts/run-validation.sh"
            elif binding["type"] == "attestation":
                doc = ROOT / binding["document"]
                assert doc.is_file(), f"attestation document missing: {binding['document']}"
                text = doc.read_text(encoding="utf-8", errors="replace")
                assert binding["section"] in text, (
                    f"attestation claim not found in {binding['document']}: {binding['section']!r}")
            if "attestation" in entry:
                doc = ROOT / entry["attestation"]["document"]
                text = doc.read_text(encoding="utf-8", errors="replace")
                assert entry["attestation"]["section"] in text, entry["id"]


class TestB5I2Compatibility:
    """Contract section 12: frozen instruments byte-identical, surfaces resolve,
    collection floors hold."""

    def test_frozen_pack_blob_sha256_unchanged(self):
        assert blob_sha256("infrastructure/control-plane/contracts/console-contract.json") == FROZEN_PACK_SHA256

    def test_no_frozen_b5i2_path_changed_since_base(self):
        changed = git_changed_paths(["diff", "--name-only", BASE_SHA, "HEAD", "--", *FROZEN_DIFF_PATHS])
        assert changed == [], f"frozen paths changed between base and HEAD: {changed}"

    def test_all_twelve_pack_surfaces_resolve(self):
        surfaces = pack_surfaces()
        assert len(surfaces) == 12
        reads = [s for s, e in surfaces.items() if e["kind"] == "read"]
        invokes = [s for s, e in surfaces.items() if e["kind"] == "invoke"]
        assert len(reads) == 9 and len(invokes) == 3, (reads, invokes)
        for name, entry in sorted(surfaces.items()):
            binds = entry["binds_to"]
            module = importlib.import_module(binds["module"])
            target = module
            for part in binds["callable"].split("."):
                target = getattr(target, part)
            assert callable(target), f"{name} does not resolve to a callable"

    def test_b5_i2_console_file_collects_exactly_floor(self):
        nodes = _collect_nodes("infrastructure/control-plane/tests/test_console_contracts.py")
        assert len(nodes) == B5_I2_COLLECT_FLOORS["infrastructure/control-plane/tests/test_console_contracts.py"], (
            f"console-contract collection drifted: {len(nodes)}")

    def test_b5_i2_harness_file_collects_exactly_floor(self):
        nodes = _collect_nodes("infrastructure/control-plane/tests/test_b5_i2_mutation_harness.py")
        assert len(nodes) == B5_I2_COLLECT_FLOORS["infrastructure/control-plane/tests/test_b5_i2_mutation_harness.py"], (
            f"harness-integrity collection drifted: {len(nodes)}")


class TestFailureMatrixConsistency:
    """Contract section 13 / acceptance row A7: exactly the 7 plan classes,
    cross-bound to the registry F-entries in both directions."""

    def test_failure_matrix_declares_exactly_seven_classes(self):
        text = FAILURE_MATRIX_PATH.read_text(encoding="utf-8", errors="replace")
        headers = re.findall(r"^### (F-\d) ", text, re.M)
        assert headers == [f"F-{n}" for n in range(1, 8)], headers

    def test_each_f_entry_cross_references_the_matrix(self):
        text = FAILURE_MATRIX_PATH.read_text(encoding="utf-8", errors="replace")
        _, registry = load_registry()
        class_names = (
            "dependency outage", "invalid data", "partial task", "crash",
            "stale state", "retry", "cancellation",
        )
        f_entries = [e for e in registry["entries"] if e["kind"] == "failure_class"]
        assert len(f_entries) == 7
        for entry in f_entries:
            assert entry["id"] in text, f"matrix missing {entry['id']}"
            match = re.search(r"\(([a-z ]+)\)$", entry["source"])
            assert match, entry["source"]
            assert match.group(1) in class_names, entry["source"]
            assert match.group(1) in text, f"matrix missing class {match.group(1)!r}"
            assert f"### {entry['id']}" in text, f"matrix missing section {entry['id']}"

    def test_matrix_states_the_c2_s4_gate(self):
        text = FAILURE_MATRIX_PATH.read_text(encoding="utf-8", errors="replace")
        assert "false success" in text
        assert "canonical state" in text


class TestConstructionPlanTraceability:
    """Contract section 13 / acceptance row A8: id containment both directions,
    planned nodes and deferred owners verbatim."""

    def test_construction_plan_cites_exactly_the_registry_ids(self):
        text = CONSTRUCTION_PLAN_PATH.read_text(encoding="utf-8", errors="replace")
        cp_ids = set(re.findall(r"\bG\d{1,2}\b|\bS-\d\b|\bF-\d\b", text))
        registry_ids = set(expected_requirement_ids())
        missing = sorted(registry_ids - cp_ids)
        assert not missing, f"construction plan missing requirement ids: {missing}"
        unexpected = sorted(cp_ids - registry_ids)
        assert not unexpected, f"construction plan cites unknown requirement ids: {unexpected}"

    def test_construction_plan_traces_every_planned_node(self):
        _, registry = load_registry()
        text = CONSTRUCTION_PLAN_PATH.read_text(encoding="utf-8", errors="replace")
        for entry in registry["entries"]:
            nodes = []
            if entry["binding"]["type"] == "deferred":
                nodes.append(entry["binding"]["planned_node"])
            if "deferred" in entry:
                nodes.append(entry["deferred"]["planned_node"])
            for node in nodes:
                assert node in text, f"planned node not in construction plan: {node}"

    def test_construction_plan_names_every_used_deferred_owner(self):
        _, registry = load_registry()
        text = CONSTRUCTION_PLAN_PATH.read_text(encoding="utf-8", errors="replace")
        owners = set()
        for entry in registry["entries"]:
            if "deferred" in entry:
                owners.add(entry["deferred"]["owner"])
            if entry["binding"]["type"] == "deferred":
                owners.add(entry["binding"]["owner"])
        for owner in sorted(owners):
            assert owner in text, f"construction plan missing deferred owner {owner}"


class TestStageBoundaries:
    """Contract sections 2/8/11 / acceptance rows A2, A11: no production change,
    no forbidden surfaces, own import closure stays stdlib-plus."""

    def test_no_production_module_added(self):
        src_dir = ROOT / "infrastructure" / "control-plane" / "src" / "oce_control"
        modules = frozenset(p.stem for p in src_dir.glob("*.py"))
        assert modules == SRC_MODULES, (
            f"src/oce_control module list changed: added={sorted(modules - SRC_MODULES)} "
            f"removed={sorted(SRC_MODULES - modules)}")

    def test_production_tree_unchanged_since_base(self):
        changed = git_changed_paths(["diff", "--name-only", BASE_SHA, "HEAD", "--",
                                     "infrastructure/control-plane/src/"])
        assert changed == [], f"production tree changed: {changed}"

    def test_failure_matrix_and_plan_free_of_forbidden_content(self):
        for path in (FAILURE_MATRIX_PATH, CONSTRUCTION_PLAN_PATH):
            text = path.read_text(encoding="utf-8", errors="replace")
            for name, pattern in FORBIDDEN_CONTENT:
                assert not pattern.search(text), f"{path.name}: forbidden {name}"

    def test_this_test_file_imports_no_network_or_model_module(self):
        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        unexpected = sorted(imported - SELF_IMPORT_ALLOWLIST)
        assert unexpected == [], f"disallowed imports in the B5-I3 suite: {unexpected}"


class TestEngineOwnershipClosure:
    """Gate G8 trace audit: pack binds only governed operations."""

    def test_contract_pack_declares_no_recovery_scheduler_or_store_surface(self):
        from oce_control.console_contracts import load_contract
        pack = load_contract()
        violations = engine_ownership_violations(pack)
        assert violations == [], f"engine-ownership violations: {violations}"

    def test_violation_detector_is_deterministic(self):
        pack = json.loads(CONTRACT_PACK_PATH.read_text(encoding="utf-8"))
        first = engine_ownership_violations(pack)
        second = engine_ownership_violations(pack)
        assert first == second


def weakened_registry_problems(registry: dict) -> list[str]:
    """CONTRACT SECTION 14 CONTROL N9 — deliberately weakened validator.

    Structural skeleton only: entries exist and entry/binding keys stay
    inside the closed sets. Every load-bearing law (exact id set, sortedness,
    vocabularies, size bounds, forbidden content, collection equality) is
    REMOVED. The negative controls require this function to admit exactly
    the inputs the real validator refuses — demonstrating that the real
    proof discriminates rather than being silent (never `or True`).
    """
    problems: list[str] = []
    if not isinstance(registry, dict):
        return ["not-a-dict"]
    entries = registry.get("entries")
    if not isinstance(entries, list):
        return ["entries-not-list"]
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            problems.append(f"entry-not-dict:{i}")
            continue
        extra = sorted(set(entry) - ENTRY_ALL_KEYS)
        if extra:
            problems.append(f"entry-extra-keys:{i}:{extra}")
        binding = entry.get("binding")
        if not isinstance(binding, dict) or "type" not in binding:
            problems.append(f"binding-skeleton:{i}")
    return problems


def mutated_registry(mutator) -> dict:
    """Deep copy of the real registry with one controlled mutation applied."""
    _, registry = load_registry()
    registry = json.loads(json.dumps(registry))
    mutator(registry)
    return registry


def _entry(registry: dict, eid: str) -> dict:
    return next(e for e in registry["entries"] if e["id"] == eid)


class TestNegativeControls:
    """Contract section 14 (N1-N9): every control runs in CI on every run.

    Each mutation is refused by the REAL validator with a named problem code
    (or, for N3, by the collection-equality proof) while the weakened
    validator admits it — the checks can turn red, and do.
    """

    # -- N1: a required gate removed ----------------------------------------
    def test_n1_missing_gate_is_refused(self):
        reg = mutated_registry(lambda r: r["entries"].remove(_entry(r, "G5")))
        problems = registry_problems(reg)
        assert any(p.startswith("requirement-ids") for p in problems), problems
        assert weakened_registry_problems(reg) == [], "weakened validator must admit N1"

    # -- N2: duplicate requirement id ---------------------------------------
    def test_n2_duplicate_id_is_refused(self):
        def dup(r):
            r["entries"].append(json.loads(json.dumps(r["entries"][0])))
        reg = mutated_registry(dup)
        problems = registry_problems(reg)
        assert any(p.startswith("duplicate-ids") for p in problems), problems
        assert weakened_registry_problems(reg) == [], "weakened validator must admit N2"

    # -- N3: forged node (format passes; only collection can catch it) ------
    def test_n3_forged_node_is_caught_by_collection_not_by_format(self):
        def forge(r):
            _entry(r, "G1")["binding"]["node"] = "test_forged_nonexistent_node"
        reg = mutated_registry(forge)
        # Structure alone cannot detect this — which is exactly why the
        # collection-equality proof exists:
        assert registry_problems(reg) == [], "format-valid forgery must pass structure"
        assert NODE_RE.match("test_forged_nonexistent_node"), "weakened format check admits it"
        missing = missing_bound_nodes(reg)
        assert "infrastructure/control-plane/tests/test_b4_config_spine.py" in missing
        assert "test_forged_nonexistent_node" in missing["infrastructure/control-plane/tests/test_b4_config_spine.py"]

    # -- N4: deferred entry stripped of its owner ---------------------------
    def test_n4_ownerless_deferral_is_refused(self):
        def strip(r):
            del _entry(r, "S-1")["deferred"]["owner"]
        reg = mutated_registry(strip)
        problems = registry_problems(reg)
        assert any(p.startswith("deferred-keys") for p in problems), problems
        assert weakened_registry_problems(reg) == [], "weakened validator must admit N4"

    # -- N5: unknown binding type -------------------------------------------
    def test_n5_unknown_binding_type_is_refused(self):
        def warp(r):
            _entry(r, "G1")["binding"]["type"] = "teleport"
        reg = mutated_registry(warp)
        problems = registry_problems(reg)
        assert any(p.startswith("binding-type") for p in problems), problems
        assert weakened_registry_problems(reg) == [], "weakened validator must admit N5"

    # -- N6: oversized text field -------------------------------------------
    def test_n6_oversized_field_is_refused(self):
        def big(r):
            _entry(r, "G2")["requirement"] = "x" * (MAX_STRING_FIELD_CHARS + 1)
        reg = mutated_registry(big)
        problems = registry_problems(reg)
        assert any(p.startswith("string-too-long") for p in problems), problems
        assert weakened_registry_problems(reg) == [], "weakened validator must admit N6"

    # -- N7: forbidden content (URL) ----------------------------------------
    def test_n7_forbidden_url_is_refused(self):
        def url(r):
            _entry(r, "F-2")["notes"] = "see https://example.invalid/details"
        reg = mutated_registry(url)
        problems = registry_problems(reg)
        assert any(p.startswith("forbidden-content:url") for p in problems), problems
        assert weakened_registry_problems(reg) == [], "weakened validator must admit N7"

    # -- N8: extra top-level key --------------------------------------------
    def test_n8_extra_top_level_key_is_refused(self):
        def extra(r):
            r["extra_key"] = True
        reg = mutated_registry(extra)
        problems = registry_problems(reg)
        assert any(p.startswith("top-level-keys") for p in problems), problems
        assert weakened_registry_problems(reg) == [], "weakened validator must admit N8"

    # -- N9: aggregate non-vacuity — the weakened validator discriminates ----
    def test_n9_weakened_validator_admits_every_mutation_the_real_one_refuses(self):
        def drop_g17(r):
            r["entries"].remove(_entry(r, "G17"))

        def dup_first(r):
            r["entries"].append(json.loads(json.dumps(r["entries"][0])))

        def strip_owner(r):
            del _entry(r, "S-2")["deferred"]["owner"]

        def bad_status(r):
            _entry(r, "G9")["mapping_status"] = "PROVEN_BY_ASSERTION"

        def oversized(r):
            _entry(r, "G10")["requirement"] = "y" * (MAX_STRING_FIELD_CHARS + 5)

        def with_url(r):
            _entry(r, "G11")["notes"] = "https://example.invalid"

        def extra_key(r):
            r["unexpected"] = 1

        cases = [
            ("missing-id", drop_g17, "requirement-ids"),
            ("duplicate-id", dup_first, "duplicate-ids"),
            ("ownerless-deferral", strip_owner, "deferred-keys"),
            ("forged-status", bad_status, "mapping-status"),
            ("oversize", oversized, "string-too-long"),
            ("forbidden-content", with_url, "forbidden-content"),
            ("extra-top-key", extra_key, "top-level-keys"),
        ]
        for label, mutator, token in cases:
            reg = mutated_registry(mutator)
            problems = registry_problems(reg)
            assert any(token in p for p in problems), f"{label}: real validator failed to refuse: {problems}"
            assert weakened_registry_problems(reg) == [], (
                f"{label}: weakened validator must admit what the real one refuses")

    # -- engine-ownership detector (gate G8) discriminates on a mutated pack --
    def test_engine_ownership_detector_flags_a_recovery_surface(self):
        pack = json.loads(CONTRACT_PACK_PATH.read_text(encoding="utf-8"))
        pack = json.loads(json.dumps(pack))
        pack["invokes"].append({
            "surface": "recovery.enact",
            "kind": "invoke",
            "binds_to": {"module": "oce_control.recovery", "callable": "recovery.recover"},
        })
        violations = engine_ownership_violations(pack)
        assert violations, "mutated pack with a recovery surface must be flagged"
