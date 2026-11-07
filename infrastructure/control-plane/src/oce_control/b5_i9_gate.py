"""B5-I9 factory gate — canonical, deterministic, offline, standard library only.

This module is the single source of the B5-I9 implementation outputs. Everything it
emits is derived from committed bytes: the frozen P0 registry, the extraction boundary
table, the implementation contract and the ledger. Nothing is typed in by hand, nothing
depends on wall-clock time, host, user, absolute path or network.

Two rules govern the module and every artifact it produces:

* R1 — import is not promotion. A module a test can import is not therefore a contract.
* R2 — authority is contagious. A pattern that embeds one authority decision is
  authority-bearing even when its data structure is generic.

The stage that this module implements produces *evidence and a proposed contract*. It
performs no extraction: no file under ``infrastructure/control-plane`` is copied,
re-exported or relabelled, and Book 6 stays unauthorized.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re

VERSION = "1.0"
IMPL_BASE = "e81bef4335de5e222fb6647c602080a129dea543"
STAGE = "B5-I9-IMPLEMENTATION"
STATUS = "IMPLEMENTED_PENDING_OPERATOR_REVIEW"
BASE = "833f7d1b9f2dfec2986fb9516d0abde06bf23dae"
LEDGER_PREFIX_LEN = 191950
LEDGER_PREFIX_SHA = "83a40ac7bb2d80ae2cc9176e1b1ba91d8bfeb189680572ce3939134b6aeb5c30"
MAX_ARTIFACT_BYTES = 262144

DOCS_DIR = "docs/oce-golden-system"
PACKET_DIR = "infrastructure/control-plane/evidence/b5-i9"

REGISTRY = "OCE_B5_I9_REQUIREMENT_TEST_REGISTRY_v1.0.json"
BOUNDARY = "OCE_B5_I9_EXTRACTION_AND_PACKAGING_BOUNDARY_v1.0.md"
CONTRACT = "OCE_B5_I9_IMPLEMENTATION_CONTRACT_v1.0.md"
FAILURE = "OCE_B5_I9_FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md"
PLAN = "OCE_B5_I9_CONSTRUCTION_PLAN_v1.0.md"
ACCEPTANCE = "OCE_B5_I9_ACCEPTANCE_MATRIX_v1.0.md"
RATIFICATION = "OCE_B5_I9_P0_OPERATOR_RATIFICATION_v1.0.md"
LEDGER = "OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md"

CLASSES = (
    "EXTRACTABLE_PATTERN",
    "EXTRACTABLE_WITH_LIMITATION",
    "REFERENCE_ONLY",
    "PLATFORM_INTERNAL",
    "PRIVATE_API",
    "AUTHORITY_BEARING",
    "PROHIBITED",
    "DEFERRED_TO_BOOK_6",
    "NOT_APPLICABLE",
)
FROZEN_COUNTS = {
    "EXTRACTABLE_PATTERN": 7,
    "EXTRACTABLE_WITH_LIMITATION": 5,
    "REFERENCE_ONLY": 4,
    "PLATFORM_INTERNAL": 3,
    "PRIVATE_API": 2,
    "AUTHORITY_BEARING": 3,
    "PROHIBITED": 1,
    "DEFERRED_TO_BOOK_6": 1,
    "NOT_APPLICABLE": 1,
}
EXTRACTABLE = ("EXTRACTABLE_PATTERN", "EXTRACTABLE_WITH_LIMITATION")
#: Paths whose semantics are private or platform-internal regardless of any table cell.
PRIVATE_INTERNAL_MARKERS = (
    "job_store.py",
    "worker_leases.py",
    "pg_store.py",
    "health.py",
    "recovery.py",
    "authority.py",
    "panel.py",
    "b5_i8_audit_support.py",
)
DECIDES_MARKERS = ("decides", "would create")
DRIVE_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")
ABS_PATH = re.compile(r"(^|[\s\"'(])/(home|Users|tmp|var|opt|etc)/")
HOST_PATTERN = re.compile(r"\bhttps?://|[a-z0-9-]+\.(com|net|org|io|dev|app)\b", re.I)
PROVIDER_NAMES = ("aws", "amazon", "azure", "gcp", "cloudflare", "heroku", "stripe", "twilio",
                  "sendgrid", "datadog", "sentry", "telegram", "discord", "openai")
PROVIDER_PATTERN = re.compile(
    r"\b(" + "|".join(PROVIDER_NAMES) + r")\b", re.I)


def has_provider(body):
    """Word-boundary provider scan: 'laws' is not 'aws'."""
    return bool(PROVIDER_PATTERN.search(body))
SECRET_PATTERNS = (
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


class GateViolation(RuntimeError):
    """A named invariant refused the input."""

    def __init__(self, check, detail):
        super().__init__("{}: {}".format(check, detail))
        self.check = check
        self.detail = detail


def _fail(check, detail):
    raise GateViolation(check, detail)


def repo_root():
    return pathlib.Path(__file__).resolve().parents[4]


def canon(obj):
    """Canonical bytes: sorted keys, 2-space indent, LF, UTF-8."""
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normalize(data):
    return data.replace(b"\r\n", b"\n")


class Repo:
    """A repository root; every path is repository-relative."""

    def __init__(self, root=None):
        self.root = pathlib.Path(root) if root is not None else repo_root()
        self.docs = self.root / DOCS_DIR
        self.packet = self.root / PACKET_DIR

    def read(self, name):
        return (self.docs / name).read_bytes()

    def text(self, name):
        return self.read(name).decode("utf-8")

    def norm(self, name):
        return normalize(self.read(name))

    def registry(self):
        return json.loads(self.text(REGISTRY))

    def exists(self, rel):
        return (self.root / rel).exists()


def resolve_citation(repo, citation):
    """Resolve ``file#clause``. Returns (ok, detail). A citation is data, not a path."""
    if "#" not in citation:
        return False, "no clause anchor: " + citation
    name, anchor = citation.split("#", 1)
    target = repo.docs / name
    if not target.exists():
        return False, "missing file: " + name
    body = target.read_bytes().decode("utf-8", "replace")
    if name.endswith(".json"):
        doc = json.loads(body)
        node = doc
        for part in anchor.strip().split("."):
            if not isinstance(node, dict) or part not in node:
                return False, "json path {} absent from {}".format(anchor, name)
            node = node[part]
        return True, "ok"
    tokens = [t for t in re.split(r"\s+", anchor.strip()) if t]
    if not tokens:
        return False, "empty anchor: " + citation
    head = tokens[0]
    if head not in body:
        return False, "clause {} absent from {}".format(head, name)
    for token in tokens[1:]:
        if len(token) >= 3 and token not in body:
            return False, "clause token {} absent from {}".format(token, name)
    return True, "ok"


def parse_boundary_rows(body):
    """Parse the 27 candidate rows of the boundary table."""
    rows = []
    for line in normalize(body.encode("utf-8")).decode("utf-8").splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        number = int(cells[0])
        rows.append({
            "number": number,
            "candidate": cells[1],
            "source": cells[2].strip("`"),
            "class": cells[3].strip("`"),
            "visibility": cells[4],
            "authority": cells[5],
            "reason": cells[6],
        })
    return rows


def _limitation(row):
    if row["class"] != "EXTRACTABLE_WITH_LIMITATION":
        return "none"
    match = re.search(r"Limitation:\s*(.+)$", row["reason"])
    return match.group(1).strip() if match else row["reason"].strip()


REFUSAL = {
    "EXTRACTABLE_PATTERN": "a consumer that lacks a declared input must refuse and name it; it must not decide admission",
    "EXTRACTABLE_WITH_LIMITATION": "a consumer that lacks a declared input must refuse and name it; the limitation cannot be waived",
    "REFERENCE_ONLY": "copying is refused; study only",
    "PLATFORM_INTERNAL": "extraction refused by NP-1/NP-3/NP-5; ownership stays in the control plane",
    "PRIVATE_API": "exposure refused by NP-2; the interface is not published",
    "AUTHORITY_BEARING": "extraction refused by NP-4; the decision is not transferable",
    "PROHIBITED": "extraction refused by charter §5 law 5 and Constitution §7.8",
    "DEFERRED_TO_BOOK_6": "refused until a fresh operator authorization names B6-I0",
    "NOT_APPLICABLE": "nothing exists to consume; refusal is vacuous",
}
RECOVERY = {
    "EXTRACTABLE_PATTERN": "consumer discards the derived artifact and regenerates from its own sources; no state is restored here",
    "EXTRACTABLE_WITH_LIMITATION": "consumer discards the derived artifact and regenerates under the recorded limitation; no state is restored here",
    "REFERENCE_ONLY": "no artifact created; nothing to recover",
    "PLATFORM_INTERNAL": "no artifact created; the single owner keeps recovery authority",
    "PRIVATE_API": "no artifact created; nothing to recover",
    "AUTHORITY_BEARING": "no artifact created; the authority owner keeps recovery authority",
    "PROHIBITED": "no artifact created; nothing to recover",
    "DEFERRED_TO_BOOK_6": "no artifact created; B6 owns the future recovery statement",
    "NOT_APPLICABLE": "no artifact created; nothing to recover",
}
DISPOSITION = {
    "EXTRACTABLE_PATTERN": "design input, re-derived by the consumer",
    "EXTRACTABLE_WITH_LIMITATION": "design input with the limitation carried verbatim",
    "REFERENCE_ONLY": "study only; not consumable",
    "PLATFORM_INTERNAL": "excluded from any public surface",
    "PRIVATE_API": "excluded from any public surface",
    "AUTHORITY_BEARING": "excluded; never extracted",
    "PROHIBITED": "excluded; never extracted",
    "DEFERRED_TO_BOOK_6": "Book 6, after a fresh operator authorization",
    "NOT_APPLICABLE": "none",
}


def census(repo):
    """The 27-candidate census, derived from the frozen boundary table."""
    body = repo.text(BOUNDARY)
    digest = sha256(repo.norm(BOUNDARY))
    rows = parse_boundary_rows(body)
    out = []
    for row in rows:
        cls = row["class"]
        if cls not in CLASSES:
            _fail("test_every_candidate_classified_once",
                  "unknown class {} on row {}".format(cls, row["number"]))
        out.append({
            "id": "C{:02d}".format(row["number"]),
            "candidate": row["candidate"],
            "source": row["source"],
            "class": cls,
            "visibility": row["visibility"],
            "authority_impact": row["authority"],
            "reason": row["reason"],
            "limitation": _limitation(row),
            "refusal": REFUSAL[cls],
            "recovery": RECOVERY[cls],
            "book6_disposition": DISPOSITION[cls],
            "provenance": {"document": BOUNDARY, "sha256": digest, "row": row["number"]},
        })
    return out


def census_counts(rows):
    counts = {name: 0 for name in CLASSES}
    for row in rows:
        counts[row["class"]] += 1
    return counts


# ---------------------------------------------------------------- named invariants
# Each name is the mutation discriminator recorded in the frozen failure matrix.

def test_requirement_ids_unique(ctx):
    ids = [r["id"] for r in ctx["registry"]["requirements"]]
    if len(ids) != len(set(ids)):
        _fail("test_requirement_ids_unique", "duplicate requirement id")
    return True


def test_zero_pass_claims(ctx):
    reg = ctx["registry"]
    states = [r["state"] for r in reg["requirements"]]
    if "PASS" in states or reg["arithmetic"].get("pass_claims") != 0:
        _fail("test_zero_pass_claims", "PASS claimed at implementation stage")
    return True


def test_every_requirement_has_one_binding(ctx):
    for row in ctx["registry"]["requirements"]:
        if not row.get("binding"):
            _fail("test_every_requirement_has_one_binding", row["id"] + " has no binding")
    declared = ctx["registry"]["arithmetic"]["by_binding"]
    if sum(declared.values()) != len(ctx["registry"]["requirements"]):
        _fail("test_every_requirement_has_one_binding", "binding arithmetic does not sum")
    return True


def test_every_test_requirement_maps_to_a_planned_node(ctx):
    inventory = ctx["nodes"]
    for row in ctx["registry"]["requirements"]:
        if row["binding"] != "test":
            continue
        if not row.get("node"):
            _fail("test_every_test_requirement_maps_to_a_planned_node", row["id"])
        if row["node"] not in inventory:
            _fail("test_every_test_requirement_maps_to_a_planned_node",
                  "{} -> {}".format(row["id"], row["node"]))
    return True


def test_base_sha_is_the_merged_main(ctx):
    packet = ctx["packet"].get("factory-gate-packet.json") or {}
    for value, where in ((packet.get("base_sha"), "factory-gate-packet"),
                        (ctx["registry"].get("base_sha"), "registry")):
        if value != BASE:
            _fail("test_base_sha_is_the_merged_main", "{} = {}".format(where, value))
    return True


def test_book6_states_remain_false(ctx):
    locks = ctx["locks"]
    if locks.get("book_6_authorized") is not False:
        _fail("test_book6_states_remain_false", "authorized")
    if locks.get("book_6_started") is not False:
        _fail("test_book6_states_remain_false", "started")
    return True


def test_g16_remains_open_with_owner(ctx):
    g16 = ctx["locks"].get("g16") or {}
    if g16.get("status") != "OPEN" or g16.get("blocker") != "B5I8-DF05":
        _fail("test_g16_remains_open_with_owner", str(g16))
    if "independent auditor" not in str(g16.get("owner", "")):
        _fail("test_g16_remains_open_with_owner", "owner")
    return True


def test_private_interfaces_never_promoted(ctx):
    for row in ctx["rows"]:
        if row["class"] not in EXTRACTABLE:
            continue
        if any(marker in row["source"] for marker in PRIVATE_INTERNAL_MARKERS):
            _fail("test_private_interfaces_never_promoted",
                  "{} ({})".format(row["source"], row["class"]))
        if row["visibility"] in {"Test-only", "Internal"} and row["class"] == "EXTRACTABLE_PATTERN":
            _fail("test_private_interfaces_never_promoted", row["source"] + " promoted to pattern")
    surface = ctx["packet"].get("handoff-contract.json") or {}
    allowed_classes = set(surface.get("allowed_classes") or [])
    if not allowed_classes <= set(EXTRACTABLE):
        _fail("test_private_interfaces_never_promoted", sorted(allowed_classes - set(EXTRACTABLE)))
    return True


def test_authority_bearing_items_are_never_extractable(ctx):
    for row in ctx["rows"]:
        authority = row["authority_impact"].lower()
        if any(marker in authority for marker in DECIDES_MARKERS) and row["class"] in EXTRACTABLE:
            _fail("test_authority_bearing_items_are_never_extractable",
                  "{} ({})".format(row["candidate"], row["class"]))
    return True


def test_no_environment_specific_paths(ctx):
    for name, body in ctx["texts"].items():
        if DRIVE_PATH.search(body):
            _fail("test_no_environment_specific_paths", name + ": drive-qualified path")
        if ABS_PATH.search(body):
            _fail("test_no_environment_specific_paths", name + ": absolute path")
    return True


CHECKS = {
    "test_requirement_ids_unique": test_requirement_ids_unique,
    "test_zero_pass_claims": test_zero_pass_claims,
    "test_every_requirement_has_one_binding": test_every_requirement_has_one_binding,
    "test_every_test_requirement_maps_to_a_planned_node":
        test_every_test_requirement_maps_to_a_planned_node,
    "test_base_sha_is_the_merged_main": test_base_sha_is_the_merged_main,
    "test_book6_states_remain_false": test_book6_states_remain_false,
    "test_g16_remains_open_with_owner": test_g16_remains_open_with_owner,
    "test_private_interfaces_never_promoted": test_private_interfaces_never_promoted,
    "test_authority_bearing_items_are_never_extractable":
        test_authority_bearing_items_are_never_extractable,
    "test_no_environment_specific_paths": test_no_environment_specific_paths,
}


# ---------------------------------------------------------------- packet construction

def planned_files(reg):
    return {f["path"]: list(f["nodes"]) for f in reg["planned_surface"]["files"]}


def planned_nodes(reg):
    nodes = []
    for f in reg["planned_surface"]["files"]:
        nodes.extend(f["nodes"])
    return nodes


IDENTITY_CLAIMS = (
    ("factory gate", "OCE_BLOCK_05_REFERENCE_APPLICATION_FACTORY_PLAN_v1.0.md#B5-I9 row"),
    ("learning closure", "OCE_BLOCK_05_REFERENCE_APPLICATION_FACTORY_PLAN_v1.0.md#B5.C5.S4"),
    ("B6 reusable-extraction contract", CONTRACT + "#A contract, not an extraction"),
    ("operator hold", "OCE_BLOCK_05_REFERENCE_APPLICATION_FACTORY_PLAN_v1.0.md#Operator-only completion"),
)
NON_IDENTITY_CLAIMS = (
    ("extraction execution", "OCE_BLOCK_06_REUSABLE_PLATFORM_SURFACES_PLAN_v1.0.md#Freeze extraction decisions"),
    ("packaging of code", CONTRACT + "#No packaging of code"),
    ("Book 6", CONTRACT + "#start Book 6"),
)


def build(repo):
    """Build every packet artifact except manifest.json and validation.json."""
    reg = repo.registry()
    rows = census(repo)
    counts = census_counts(rows)
    for name, expected in FROZEN_COUNTS.items():
        if counts[name] != expected:
            _fail("test_every_candidate_classified_once",
                  "{} = {} (frozen {})".format(name, counts[name], expected))
    if len(rows) != 27:
        _fail("test_every_candidate_classified_once", "row count {}".format(len(rows)))

    nodes = planned_nodes(reg)
    surface = planned_files(reg)
    arith = reg["arithmetic"]
    if len(nodes) != 41 or len(surface) != 5:
        _fail("test_every_test_requirement_maps_to_a_planned_node",
              "nodes {} files {}".format(len(nodes), len(surface)))

    sources = {
        "boundary_sha256": sha256(repo.norm(BOUNDARY)),
        "registry_sha256": sha256(repo.norm(REGISTRY)),
        "contract_sha256": sha256(repo.norm(CONTRACT)),
        "failure_matrix_sha256": sha256(repo.norm(FAILURE)),
        "construction_plan_sha256": sha256(repo.norm(PLAN)),
        "acceptance_matrix_sha256": sha256(repo.norm(ACCEPTANCE)),
    }

    packet = {
        "document_id": "OCE-B5-I9-FACTORY-GATE-001",
        "version": VERSION,
        "status": STATUS,
        "stage": STAGE,
        "base_sha": BASE,
        "gate": {
            "result": "FROZEN_SURFACES_VERIFIED",
            "requirements_total": len(reg["requirements"]),
            "by_binding": arith["by_binding"],
            "by_state": arith["by_state"],
            "planned_nodes": len(nodes),
            "planned_files": len(surface),
            "failure_classes": arith["failure_classes_declared"],
            "mutations_planned": arith["mutations_planned"],
            "pass_claims": 0,
            "implementation_executed": True,
            "extraction_executed": False,
        },
        "identity": {
            "components": [{"name": n, "citation": c} for n, c in IDENTITY_CLAIMS],
            "non_identities": [{"name": n, "citation": c} for n, c in NON_IDENTITY_CLAIMS],
        },
        "census_counts": counts,
        "census_total": len(rows),
        "sources": sources,
        "packaging": {
            "runtime_package_produced": False,
            "owner": "B5-I6 release packaging; B6.C1.S3 templates and install sets",
            "deployable_claim": False,
        },
    }

    census_doc = {
        "document_id": "OCE-B5-I9-CENSUS-001",
        "version": VERSION,
        "status": STATUS,
        "stage": STAGE,
        "base_sha": BASE,
        "counts": counts,
        "total": len(rows),
        "rules": [
            "R1 import is not promotion: classification is by ownership and authority",
            "R2 authority is contagious: one embedded authority decision makes an item authority-bearing",
        ],
        "rows": rows,
    }

    learning = {
        "document_id": "OCE-B5-I9-LEARNING-001",
        "version": VERSION,
        "status": STATUS,
        "stage": STAGE,
        "base_sha": BASE,
        "principle": "no meaningful observation is silently discarded",
        "observations": learning_observations(repo, counts),
    }

    contract = {
        "document_id": "OCE-B5-I9-HANDOFF-CONTRACT-001",
        "version": VERSION,
        "status": STATUS,
        "stage": STAGE,
        "base_sha": BASE,
        "title": "proposed Book 6 reusable-extraction contract (proposal, not authorization)",
        "allowed_classes": ["EXTRACTABLE_PATTERN", "EXTRACTABLE_WITH_LIMITATION"],
        "allowed_design_inputs": [
            {"id": r["id"], "candidate": r["candidate"], "class": r["class"],
             "limitation": r["limitation"]}
            for r in rows if r["class"] in EXTRACTABLE
        ],
        "excluded_candidates": [
            {"id": r["id"], "candidate": r["candidate"], "class": r["class"]}
            for r in rows if r["class"] not in EXTRACTABLE
             and r["class"] != "DEFERRED_TO_BOOK_6"
        ],
        "deferred": [
            {"id": r["id"], "candidate": r["candidate"], "class": r["class"],
             "disposition": r["book6_disposition"]}
            for r in rows if r["class"] == "DEFERRED_TO_BOOK_6"
        ],
        "obligations": [
            "consume classifications, never re-decide them",
            "re-derive every design input; copy no source file",
            "carry each limitation verbatim",
            "keep canonical state, admission, refusal, recovery and spend inside the owner",
        ],
        "contains_extracted_source": False,
        "files_copied": [],
        "public_surface_paths": [],
        "canonical_state": {"owner": "control-plane", "consumer_stores": []},
        "configuration_truth": {"source": "control-plane configuration schema", "duplicates": []},
        "authority_owners": {
            "admission": "control-plane admission gate",
            "refusal_reason": "control-plane refusal vocabulary",
            "recovery": "control-plane recovery",
            "evidence": "control-plane workflow",
            "configuration": "control-plane configuration schema",
            "spend": None,
            "execution": None,
            "broker": None,
        },
        "start_preconditions": [
            "AUTHORIZED_STAGE=B6-I0 issued by the operator after this stage's review",
            "B5-I9 operator review accepted",
            "no extraction before that authorization",
        ],
        "authorization": {"book_6_authorized": False, "book_6_started": False},
    }

    handoff = {
        "document_id": "OCE-B5-I9-HANDOFF-READINESS-001",
        "version": VERSION,
        "status": STATUS,
        "stage": STAGE,
        "base_sha": BASE,
        "seven_states": [
            {"state": "Book 5 evidence complete", "value": True, "owner": "occurred",
             "source": "B5-I8 §16; ledger §20"},
            {"state": "Book 5 implementation complete", "value": True, "owner": "occurred",
             "source": "Block 5 plan §7 B5-I1–I8"},
            {"state": "Book 5 governance complete", "value": False, "owner": "operator",
             "source": "Block 5 plan §7 gate"},
            {"state": "B5-I9 complete", "value": False, "owner": "operator",
             "source": "Block 5 plan §6 B5.C5.S5; ledger §1"},
            {"state": "Book 6 input-ready", "value": True, "owner": "occurred",
             "source": "Block 6 plan dependency; B6-I0 (narrow: upstream evidence only)"},
            {"state": "Book 6 authorized", "value": False, "owner": "operator",
             "source": "roadmap §10"},
            {"state": "Book 6 started", "value": False, "owner": "operator",
             "source": "Block 6 plan §1"},
        ],
        "non_implications": [
            "input-ready never implies authorized",
            "authorized never implies started",
            "evidence completeness never implies governance completeness",
            "no state transitions on CI success alone",
            "B5-I9 is not complete because a packet exists",
        ],
        "consumable_evidence": [
            {"item": "ratified Product Charter", "path": "OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md"},
            {"item": "frozen lifecycle model", "path": "OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md"},
            {"item": "deterministic kernel contract", "path": "OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md"},
            {"item": "B5-I4–I8 evidence records", "path": RATIFICATION},
            {"item": "refusal and recovery laws", "path": "OCE_B5_I9_EXTRACTION_AND_PACKAGING_BOUNDARY_v1.0.md"},
            {"item": "usability limitations including G16", "path": RATIFICATION},
            {"item": "extraction classification and limitations", "path": "OCE_B5_I9_EXTRACTION_AND_PACKAGING_BOUNDARY_v1.0.md"},
            {"item": "remaining limitations and open decisions", "path": "OCE_B5_I9_IMPLEMENTATION_CONTRACT_v1.0.md"},
            {"item": "cost and authority boundaries", "path": "OCE_B5_I9_IMPLEMENTATION_CONTRACT_v1.0.md"},
            {"item": "manifests and hashes", "path": "OCE_B5_I9_IMPLEMENTATION_CONTRACT_v1.0.md"},
            {"item": "exact merged-main identity", "path": "OCE_B5_I9_IMPLEMENTATION_CONTRACT_v1.0.md"},
        ],
        "g16": {"status": "OPEN", "blocker": "B5I8-DF05",
                "condition": "an independent operator, distinct from the implementer, repeats the usability measurement",
                "owner": "Operator (independent auditor distinct from the implementer)",
                "blocks": ["any independence claim"], "does_not_block": ["B5-I9 planning or implementation"]},
        "start_conditions": [
            "fresh operator authorization naming AUTHORIZED_STAGE=B6-I0",
            "operator review of this stage accepted",
            "classifications consumed, not re-decided",
        ],
        "authorization_token_required": "AUTHORIZED_STAGE=B6-I0",
    }

    provenance = {
        "document_id": "OCE-B5-I9-PROVENANCE-001",
        "version": VERSION,
        "status": STATUS,
        "stage": STAGE,
        "base_sha": BASE,
        "generator": "infrastructure/control-plane/scripts/b5_i9_factory_gate.py",
        "generator_library": "infrastructure/control-plane/src/oce_control/b5_i9_gate.py",
        "language": "python3 standard library only",
        "network_access": False,
        "secrets_required": False,
        "wall_clock_values": False,
        "sources": sources,
        "reproduce": "python infrastructure/control-plane/scripts/b5_i9_factory_gate.py --check",
        "determinism": "sorted keys, LF, UTF-8, no timestamps, repository-relative paths only",
    }

    hold = {
        "document_id": "OCE-B5-I9-OPERATOR-HOLD-001",
        "version": VERSION,
        "status": STATUS,
        "stage": STAGE,
        "base_sha": BASE,
        "hold": "this stage ends at operator review; the operator performs completion",
        "extraction": "NOT_PERFORMED",
        "book_6": "UNAUTHORIZED",
        "merge_authorized": False,
        "ratification_authorized": False,
        "b5_i9_complete": False,
        "book_5_governance_complete": False,
        "g16": "OPEN",
        "post_book_6_evaluation": "UNSTARTED",
        "capital_authority": "none",
        "cost_usd": 0,
        "freebuff_touched": False,
    }

    reproduction = {
        "document_id": "OCE-B5-I9-REPRODUCTION-001",
        "version": VERSION,
        "status": STATUS,
        "stage": STAGE,
        "base_sha": BASE,
        "steps": [
            "python infrastructure/control-plane/scripts/b5_i9_factory_gate.py --check",
            "python infrastructure/control-plane/scripts/b5_i9_factory_gate.py --emit <temporary directory outside the repository>",
            "python infrastructure/control-plane/scripts/b5_i9_p0_validate.py --self-check",
            "python -m pytest infrastructure/control-plane/tests/test_b5_i9_stage_identity_and_scope.py infrastructure/control-plane/tests/test_b5_i9_extraction_classification.py infrastructure/control-plane/tests/test_b5_i9_no_platform_extraction.py infrastructure/control-plane/tests/test_b5_i9_packet_packaging_and_provenance.py infrastructure/control-plane/tests/test_b5_i9_book6_handoff.py",
            "python infrastructure/control-plane/scripts/b5_i9_mutation_battery.py --json <evidence path>",
        ],
        "guarantees": [
            "no network access",
            "no secret or credential input",
            "no wall-clock, hostname or absolute path in any artifact",
            "byte-identical regeneration from the same commit",
        ],
    }

    g16_note = {
        "document_id": "OCE-B5-I9-G16-LIMITATION-001",
        "version": VERSION,
        "status": STATUS,
        "stage": STAGE,
        "base_sha": BASE,
        "status_value": "OPEN",
        "blocker": "B5I8-DF05",
        "missing_condition": "an independent operator, distinct from the implementer, repeats the usability measurement",
        "owner": "Operator (independent auditor distinct from the implementer)",
        "note": "B5-I9 implementation changes nothing about independence; same-agent evidence stays same-agent",
    }

    return {
        "factory-gate-packet.json": packet,
        "classification-census.json": census_doc,
        "learning-closure.json": learning,
        "handoff-contract.json": contract,
        "handoff-input-readiness.json": handoff,
        "provenance.json": provenance,
        "operator-hold.json": hold,
        "reproduction.json": reproduction,
        "g16-limitation.json": g16_note,
    }


def learning_observations(repo, counts):
    """Observations made while implementing, each with its correction and evidence."""
    contract = repo.text(CONTRACT)
    return [
        {
            "id": "L01",
            "observation": "the frozen P0 validator asserts that no B5-I9 test or workflow exists and that planned files do not exist",
            "consequence": "implementing without a stage-aware validator would make its mandatory checks fail by construction and invite deleting them",
            "correction": "the validator gained a stage branch: in implementation it requires the five files, the 41 nodes, the workflow selection and the packet, and it keeps every P0 check",
            "disposition": "repaired forward in the validator; no P0 check removed",
        },
        {
            "id": "L02",
            "observation": "the frozen boundary check treats any filename matching book6-/b6- as a Book 6 artifact",
            "consequence": "naming this stage's handoff files book6-handoff.json would be reported as a Book 6 artifact, which would be false",
            "correction": "the packet files are handoff-contract.json and handoff-input-readiness.json; the Book 6 state lives inside them",
            "disposition": "naming constraint recorded; classification unchanged",
        },
        {
            "id": "L03",
            "observation": "the 41-node inventory is frozen and the validator rejects orphan nodes",
            "consequence": "the 10 mutation discriminators named by the failure matrix cannot be added as extra collected nodes",
            "correction": "each discriminator is a named invariant invoked by a frozen node and executed by the battery; the battery resolves discriminators by name",
            "disposition": "design constraint recorded; node count remains exactly 41",
        },
        {
            "id": "L04",
            "observation": "registry rows B5I9-EX-01 and B5I9-EX-09 describe the census as 26 rows while the frozen total, the table and the arithmetic are 27",
            "consequence": "a literal reader would see a contradiction between the observable text and the table",
            "correction": "the two observable strings were corrected to 27 in a separate narrow repair commit; statements, ids, bindings and states are unchanged",
            "disposition": "repaired forward as B5-I9-X1; history preserved",
        },
        {
            "id": "L05",
            "observation": "mutation M08 targets a packet artifact copy, not the boundary document",
            "consequence": "scanning only the boundary document would leave the packet path rule unproven",
            "correction": "the environment-path invariant scans every emitted packet artifact as well as the boundary text",
            "disposition": "implemented in the gate library",
        },
        {
            "id": "L07",
            "observation": "the frozen boundary check rejects any filename matching book6-/b6-, and the frozen planned surface itself contains test_b5_i9_book6_handoff.py",
            "consequence": "a naive scan reports the frozen planned node file as a Book 6 artifact, which would be false",
            "correction": "the scan exempts the frozen planned surface and the B5-I9 evidence directory, and keeps a negative control proving a planted Book 6 name is still caught",
            "disposition": "repaired forward in the validator and in the test node",
        },
        {
            "id": "L08",
            "observation": "the stage branch initially compared executed nodes against the mutation count",
            "consequence": "one check would have been permanently red for a reason unrelated to the state it guards",
            "correction": "nodes_executed is compared with the planned nodes and mutations_executed with the mutations",
            "disposition": "repaired forward in the validator",
        },
        {
            "id": "L06",
            "observation": "the census counts sum to 27 only if all nine classes are present",
            "consequence": "a future classifier that silently drops a class would still look arithmetically plausible",
            "correction": "every class has a frozen count, and the generator refuses a census that differs",
            "disposition": "enforced at generation time and asserted by the tests",
        },
    ]


def write_packet(packet_dir, artifacts):
    packet_dir = pathlib.Path(packet_dir)
    packet_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for name in sorted(artifacts):
        data = canon(artifacts[name])
        if len(data) > MAX_ARTIFACT_BYTES:
            _fail("test_artifact_size_rule_enforced",
                  "{} is {} bytes (limit {})".format(name, len(data), MAX_ARTIFACT_BYTES))
        (packet_dir / name).write_bytes(data)
        written[name] = data
    return written


def manifest_rows(packet_dir):
    packet_dir = pathlib.Path(packet_dir)
    rows = []
    for path in sorted(packet_dir.iterdir()):
        if not path.is_file() or path.name == "manifest.json":
            continue
        raw = path.read_bytes()
        body = normalize(raw)
        try:
            doc = json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            _fail("test_every_artifact_records_identity", path.name + " is not JSON")
        rows.append({
            "path": path.name,
            "sha256": sha256(body),
            "size_bytes": len(body),
            "document_id": doc.get("document_id"),
            "version": doc.get("version"),
            "stage": doc.get("stage"),
            "status": doc.get("status"),
            "kind": "json",
        })
    return rows


def ctx(repo):
    """Everything the invariants read, from files only."""
    reg = repo.registry()
    rows = census(repo)
    packet = {}
    if repo.packet.exists():
        for path in sorted(repo.packet.iterdir()):
            if path.is_file() and path.suffix == ".json":
                packet[path.name] = json.loads(path.read_bytes().decode("utf-8"))
    texts = {"boundary": repo.text(BOUNDARY)}
    for path in sorted(repo.packet.iterdir()) if repo.packet.exists() else []:
        if path.is_file():
            texts[path.name] = path.read_bytes().decode("utf-8", "replace")
    return {
        "registry": reg,
        "rows": rows,
        "nodes": planned_nodes(reg),
        "locks": reg["locks"],
        "packet": packet,
        "texts": texts,
    }


def run_checks(context, names=None):
    """Run named invariants; return list of {id,status,detail}."""
    results = []
    for name in (names or list(CHECKS)):
        try:
            CHECKS[name](context)
            results.append({"id": name, "status": "PASS", "detail": ""})
        except GateViolation as exc:
            results.append({"id": name, "status": "FAIL", "detail": exc.detail})
    return results


def emit(repo, outdir):
    """Build, write and self-validate the packet. Returns the validation document."""
    artifacts = build(repo)
    outdir = pathlib.Path(outdir)
    write_packet(outdir, artifacts)
    scratch = Repo(repo.root)
    scratch.packet = outdir
    context = ctx(scratch)
    results = run_checks(context)
    failures = [r for r in results if r["status"] != "PASS"]
    digest = sha256(b"".join(canon(artifacts[n]) for n in sorted(artifacts)))
    validation = {
        "document_id": "OCE-B5-I9-VALIDATION-001",
        "version": VERSION,
        "status": STATUS if not failures else "FAILED",
        "stage": STAGE,
        "base_sha": BASE,
        "checks_total": len(results),
        "failures": len(failures),
        "packet_digest": digest,
        "results": results,
    }
    write_packet(outdir, {"validation.json": validation})
    rows = manifest_rows(outdir)
    manifest = {
        "document_id": "OCE-B5-I9-MANIFEST-001",
        "version": VERSION,
        "status": STATUS,
        "stage": STAGE,
        "base_sha": BASE,
        "artifact_count": len(rows),
        "artifacts": rows,
    }
    write_packet(outdir, {"manifest.json": manifest})
    if failures:
        raise GateViolation(
            "packet/validation",
            "; ".join("{}: {}".format(r["id"], r["detail"]) for r in failures),
        )
    return validation


def diff_packet(repo, candidate_dir):
    """Compare a candidate packet directory with what the repository generates."""
    import tempfile

    candidate = pathlib.Path(candidate_dir)
    with tempfile.TemporaryDirectory() as tmp:
        emit(repo, tmp)
        fresh = pathlib.Path(tmp)
        names = sorted(p.name for p in fresh.iterdir() if p.is_file())
        have = sorted(p.name for p in candidate.iterdir() if p.is_file())
        problems = []
        if names != have:
            problems.append("file list differs: {}".format(sorted(set(names) ^ set(have))))
        for name in names:
            if name not in have:
                continue
            if normalize((fresh / name).read_bytes()) != normalize((candidate / name).read_bytes()):
                problems.append(name + " differs")
    return problems
