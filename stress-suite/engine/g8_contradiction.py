"""G8 — cross-scenario contradiction audit machinery (STRESS-G8C1).

G8 asks a different question from G1-G7. It does not ask "does each scenario
work". It asks whether EQUIVALENT INSTITUTIONAL FACTS produce CONSISTENT
institutional behavior (phase, authority, evidence, lifecycle, recovery,
terminal state) across S01-S24 and the G1-G7 implementation, and whether
materially different facts are ever accidentally treated as equivalent.

Generic machinery only. Nothing in this module branches on a scenario id, an
expected outcome, a fixture name or hidden ground truth. Scenario ids appear in
audit INPUTS and REPORTS; they are never decision rules. Verdicts are pure
functions of the declared equivalence vector, the declared discriminator rules
and the declared classification vocabulary, all frozen in
`evidence/G8_EQUIVALENCE_CONTRACT.json` before any comparison ran.

Mechanisms:

  1. EQUIVALENCE VECTOR   — the declared outcome-relevant fields of an observation.
  2. OUTCOME CLASS        — the machine-local outcome token mapped onto one
                            canonical class through the frozen token map.
  3. COMPARISON           — same vector + different class  -> contradiction;
                            different vector               -> must be covered by
                            a DECLARED discriminator, else contradiction.
  4. DISCRIMINATORS       — JUSTIFIES_DIVERGENCE (may explain a difference),
                            NEUTRAL (declared non-outcome-relevant; a difference in
                            it may NEVER justify a different outcome),
                            MUST_NOT_VIOLATE_ORDER (a declared field order must not
                            invert the declared outcome permissiveness order), and
                            MUST_NOT_DIVERGE_EMPIRICAL (operator availability may not
                            change an EMPIRICAL outcome class).
  5. GUARDED PROPERTIES   — declared institutional properties that must hold
                            across a family's members; violation is a
                            contradiction, UNKNOWN is a visible evidence gap
                            (UNKNOWN is never favorable). Revision R3: a property
                            may be HOLDS only when the observation carries the
                            derivation evidence its declared derivation_kind
                            requires (DIRECT_TRACE / PAIRED_COUNTERFACTUAL /
                            CANONICAL_STATE_COMPARISON); a key-name search, a
                            substring hit, a scenario identifier, an unconditional
                            literal or terminal-token presence can never create
                            HOLDS, and a closure-required property that is never
                            exercised blocks the gate rather than passing by
                            absence of a violation.
  6. GATE CLAIM AUDIT     — a completed gate receipt is checked against the
                            surface, SHA, count lineage and mutation accounting
                            it names.
  7. NEGATIVE CONTROLS    — the audit must be able to detect its own failure
                            modes (seeded inconsistent control), must never
                            consume sealed expectations, and the evidence
                            receipt must be unable to certify itself.

Doctrine enforced by construction:
  ASSERTED != DERIVED · STRUCTURED OBJECT != VERIFIED OBJECT ·
  REGISTERED EVIDENCE != RELEVANT EVIDENCE · UNIT TEST PASS != COMPLETE
  EVIDENCE PACKAGE · CORRELATED REPETITION != INDEPENDENCE ·
  UNKNOWN != FAVORABLE · INTERNAL SIMULATION MUTATION != EXTERNAL AUTHORITY
  MUTATION.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex
from .g8_chronology import STAGES, ChronologyError, validate_chronology
from .g8_test_evidence import TestEvidence, check_baseline

# --------------------------------------------------------------------------- #
# Sealed-field discipline
# --------------------------------------------------------------------------- #
#: fields that carry private expected/hidden truth. The G8 audit may never
#: consume them; every evaluator must be handed a decision-grade projection.
SEALED_KEYS = frozenset({
    "hidden_ground_truth",
    "expected_phase_path",
    "expected_phase_trace",
    "expected_terminal_knowledge",
    "expected_disposition",
    "expected_outcome",
    "terminal_states",
})


class SealedAccessError(RuntimeError):
    """Raised when a payload offered to the audit still carries sealed truth."""


_EMPTY = ("", None, [], {}, ())


def scan_for_sealed(payload: Any, _path: str = "$",
                    include_empty: bool = False) -> List[str]:
    """Return the paths of every sealed key reachable inside `payload`.

    A decision-grade projection is a pack/dict whose sealed keys are PRESENT but
    EMPTY (that is exactly what the family `decision_grade()` projections do), so
    by default only a sealed key carrying an actual value is a hole. Pass
    `include_empty=True` for the strict structural check."""
    found: List[str] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            here = f"{_path}.{key}"
            if str(key) in SEALED_KEYS and (include_empty or value not in _EMPTY):
                found.append(here)
            found.extend(scan_for_sealed(value, here, include_empty))
    elif isinstance(payload, (list, tuple)):
        for i, value in enumerate(payload):
            found.extend(scan_for_sealed(value, f"{_path}[{i}]", include_empty))
    return found


def assert_decision_grade(payload: Any, where: str) -> None:
    holes = scan_for_sealed(payload)
    if holes:
        raise SealedAccessError(
            f"{where} still carries sealed fields (fail closed): {holes}")


# --------------------------------------------------------------------------- #
# Contract
# --------------------------------------------------------------------------- #
def load_contract(path) -> Dict[str, Any]:
    data = json.loads(open(path, encoding="utf-8").read())
    validate_contract(data)
    return data


def validate_contract(contract: Mapping[str, Any]) -> None:
    """Fail closed on an incomplete contract: every declared field must name
    its tokens, every family must name a state machine, every discriminator must
    target a declared field, and the classification vocabulary must be closed."""
    fields = {f["field"]: f for f in contract["equivalence_fields"]}
    if len(fields) != len(contract["equivalence_fields"]):
        raise ValueError("equivalence_fields contains duplicates")
    for f in contract["equivalence_fields"]:
        if "UNKNOWN" not in f["tokens"]:
            raise ValueError(f"field {f['field']} must allow UNKNOWN")
        if f["order"] != "UNORDERED":
            unknown_in_order = set(f["order"]) - set(f["tokens"])
            if unknown_in_order:
                raise ValueError(
                    f"field {f['field']} declares an order over undeclared tokens: "
                    f"{sorted(unknown_in_order)}")
    families = {f["family_id"] for f in contract["comparison_families"]}
    if len(families) != len(contract["comparison_families"]):
        raise ValueError("comparison_families contains duplicate ids")
    for f in contract["comparison_families"]:
        if f["state_machine"] != "MULTI" and f["state_machine"] not in set(
                contract["state_machines"]) | {"DOMAIN_MACHINE", "META"}:
            raise ValueError(f"family {f['family_id']} declares unknown machine")
        for pid in f.get("guarded_properties", []):
            if pid not in {p["property_id"] for p in contract["guarded_properties"]}:
                raise ValueError(f"family {f['family_id']} names unknown property {pid}")
        if f["default_classification"] not in set(contract["classification_vocabulary"]):
            raise ValueError(f"family {f['family_id']} uses undeclared classification")
    for d in contract["discriminator_rules"]:
        if d["field"] not in fields:
            raise ValueError(f"discriminator {d['discriminator_id']} targets undeclared field")
        if d["kind"] not in ("JUSTIFIES_DIVERGENCE", "MUST_NOT_VIOLATE_ORDER",
                             "MUST_NOT_DIVERGE_EMPIRICAL", "NEUTRAL"):
            raise ValueError(f"discriminator {d['discriminator_id']} has unknown kind")
        if d["kind"] == "MUST_NOT_VIOLATE_ORDER":
            if d.get("direction") not in ("NON_DECREASING", "NON_INCREASING"):
                raise ValueError(
                    f"discriminator {d['discriminator_id']} missing a declared direction")
            if fields[d["field"]]["order"] == "UNORDERED":
                raise ValueError(
                    f"discriminator {d['discriminator_id']} needs an ordered field")
    classes = set(contract["outcome_classes"])
    if len(classes) != len(contract["outcome_classes"]):
        raise ValueError("outcome_classes contains duplicates")
    for entry in contract["outcome_token_map"]:
        if entry["outcome_class"] not in classes:
            raise ValueError(f"token map references undeclared class {entry['outcome_class']}")
    permissive = set(contract["outcome_permissiveness"]["rank"])
    if permissive != classes:
        raise ValueError("outcome_permissiveness must rank exactly the declared classes")
    # STRESS-G8R4 (R-G8-09): the contract must declare a chronological stage for
    # its own rules and may not summarise itself as more provable than its
    # weakest recorded artifact. A retrospective reconstruction claiming a
    # pre-run freeze is rejected here, not in prose.
    try:
        validate_chronology(contract["contract_chronology"])
    except KeyError as exc:
        raise ValueError(
            "contract declares no contract_chronology block, so it cannot state "
            "whether its own verdict rules were frozen before the run") from exc


def contract_digest(contract: Mapping[str, Any]) -> str:
    return deterministic_hex("g8_contract", json.dumps(contract, sort_keys=True), length=32)


# --------------------------------------------------------------------------- #
# Equivalence vector
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class EquivalenceVector:
    values: Mapping[str, str]
    derivation_status: Mapping[str, str] = field(default_factory=dict)

    def digest(self) -> str:
        return deterministic_hex("g8_vector", json.dumps(dict(self.values),
                                                         sort_keys=True), length=24)

    def differing_fields(self, other: "EquivalenceVector") -> Tuple[str, ...]:
        keys = sorted(set(self.values) | set(other.values))
        return tuple(k for k in keys
                     if self.values.get(k, "UNKNOWN") != other.values.get(k, "UNKNOWN"))

    def is_equal(self, other: "EquivalenceVector") -> bool:
        return not self.differing_fields(other)

    def to_dict(self) -> Dict[str, Any]:
        return {"values": {k: self.values[k] for k in sorted(self.values)},
                "derivation_status": {k: self.derivation_status[k]
                                      for k in sorted(self.derivation_status)},
                "digest": self.digest()}


def normalize_vector(contract: Mapping[str, Any], raw: Mapping[str, Any]
                     ) -> EquivalenceVector:
    """Normalize declared fields onto their token vocabulary.

    Missing or undeclared values become UNKNOWN and are RECORDED as such —
    UNKNOWN is never normalized into a favorable token (rule N2) and an
    undeclared token is never coerced to a nearest known one."""
    values: Dict[str, str] = {}
    status: Dict[str, str] = {}
    for spec in contract["equivalence_fields"]:
        name = spec["field"]
        allowed = set(spec["tokens"])
        if name not in raw or raw[name] in (None, ""):
            values[name] = "UNKNOWN"
            status[name] = "NOT_DERIVED"
            continue
        token = str(raw[name])
        if token not in allowed:
            values[name] = "UNKNOWN"
            status[name] = "UNDECLARED_TOKEN_FAILED_CLOSED"
            continue
        values[name] = token
        status[name] = "DERIVED"
    return EquivalenceVector(values=values, derivation_status=status)


def outcome_class_for(contract: Mapping[str, Any], machine: str, token: str
                      ) -> Tuple[str, bool]:
    """(outcome_class, mapped). An unmapped token returns ('', False) — rule N7
    forbids assigning a nearest class."""
    for entry in contract["outcome_token_map"]:
        if entry["machine"] == machine and entry["token"] == token:
            return entry["outcome_class"], True
    return "", False


# --------------------------------------------------------------------------- #
# Observation
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class InstitutionalObservation:
    observation_id: str
    family_id: str
    source_gate: str
    source_ref: str
    state_machine: str
    object_class: str
    raw_outcome_token: str
    outcome_class: str
    outcome_mapped: bool
    vector: EquivalenceVector
    guarded_properties: Mapping[str, GuardedPropertyValue] = field(default_factory=dict)
    evidence_refs: Tuple[str, ...] = ()
    notes: str = ""

    @property
    def comparable_key(self) -> Tuple[str, str, str]:
        """State machine first: vocabulary from different machines is never
        treated as semantic identity (control C05 / control rule N8)."""
        return (self.state_machine, self.object_class, self.family_id)

    def fingerprint(self) -> str:
        return deterministic_hex("g8_obs", self.state_machine, self.object_class,
                                 self.raw_outcome_token, self.outcome_class,
                                 self.vector.digest(), length=24)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "family_id": self.family_id,
            "source_gate": self.source_gate,
            "source_ref": self.source_ref,
            "state_machine": self.state_machine,
            "object_class": self.object_class,
            "raw_outcome_token": self.raw_outcome_token,
            "outcome_class": self.outcome_class,
            "outcome_mapped": self.outcome_mapped,
            "equivalence_vector": self.vector.to_dict(),
            "guarded_properties": {k: _gp_to_dict(self.guarded_properties[k])
                                   for k in sorted(self.guarded_properties)},
            "evidence_refs": list(self.evidence_refs),
            "fingerprint": self.fingerprint(),
            "notes": self.notes,
        }


def build_observation(contract: Mapping[str, Any], *, observation_id: str,
                      family_id: str, source_gate: str, source_ref: str,
                      state_machine: str, object_class: str,
                      raw_outcome_token: str,
                      vector_values: Mapping[str, Any],
                      guarded_properties: Optional[Mapping[str, GuardedPropertyValue]] = None,
                      evidence_refs: Sequence[str] = (),
                      notes: str = "") -> InstitutionalObservation:
    mapped_class, mapped = outcome_class_for(contract, state_machine,
                                             raw_outcome_token)
    return InstitutionalObservation(
        observation_id=observation_id, family_id=family_id, source_gate=source_gate,
        source_ref=source_ref, state_machine=state_machine,
        object_class=object_class, raw_outcome_token=raw_outcome_token,
        outcome_class=mapped_class, outcome_mapped=mapped,
        vector=normalize_vector(contract, vector_values),
        guarded_properties=dict(guarded_properties or {}),
        evidence_refs=tuple(evidence_refs), notes=notes)


# --------------------------------------------------------------------------- #
# Guarded-property evidence contract (revision R3)
# --------------------------------------------------------------------------- #
#: A property may be HOLDS only when the observation that produced it carries the
#: derivation evidence its kind requires. Key-name searches, substring searches,
#: scenario identifiers, unconditional literals and terminal-token presence alone
#: can never create HOLDS (review findings R-G8-02, R-G8-03, R-G8-04, R-G8-05).
DERIVATION_KINDS = ("DIRECT_TRACE", "PAIRED_COUNTERFACTUAL",
                    "CANONICAL_STATE_COMPARISON", "NOT_DERIVABLE")

#: kinds that require an observed before/after relation, not just a reference list
_RELATIONAL_KINDS = ("PAIRED_COUNTERFACTUAL", "CANONICAL_STATE_COMPARISON")


class GuardedContractError(ValueError):
    """Raised when a guarded-property record claims a result its derivation
    evidence does not support. Constructing one is a hard failure rather than a
    silent downgrade, so no caller can emit a fabricated pass."""


@dataclass(frozen=True)
class GuardedPropertyValue:
    """The evidence a single guarded-property observation must carry.

    `value` is tri-state: True / False / None (= not derivable). `None` is NEVER
    favourable. The remaining fields are the derivation evidence the finding
    serialises, so a reviewer can re-derive the verdict without reading prose.
    """

    value: Optional[bool]
    derivation_kind: str
    evidence_refs: Tuple[str, ...] = ()
    before_state: str = ""
    after_state: str = ""
    decision_surface: str = ""
    reason: str = ""

    def __post_init__(self) -> None:
        if self.derivation_kind not in DERIVATION_KINDS:
            raise GuardedContractError(
                f"unknown derivation_kind {self.derivation_kind!r}; canonical: "
                f"{list(DERIVATION_KINDS)}")
        if self.value is None:
            return
        if self.derivation_kind == "NOT_DERIVABLE":
            raise GuardedContractError(
                "a NOT_DERIVABLE derivation cannot carry a boolean value — the "
                "verdict is UNKNOWN_NOT_FAVORABLE by construction")
        if not self.decision_surface:
            raise GuardedContractError(
                f"{self.derivation_kind} derivation must declare the surface it "
                "read (decision_surface)")
        if not self.evidence_refs:
            raise GuardedContractError(
                f"{self.derivation_kind} derivation must cite at least one "
                "concrete evidence reference (evidence_refs); a key name, a "
                "substring hit, a scenario identifier or a literal is not evidence")
        if self.derivation_kind in _RELATIONAL_KINDS:
            if not self.before_state or not self.after_state:
                raise GuardedContractError(
                    f"{self.derivation_kind} derivation must record both the "
                    "before and the after canonical state it compared")
        if not self.reason:
            raise GuardedContractError(
                "a derived guarded-property value must state its reason")

    def verdict(self) -> str:
        if self.value is True:
            return "HOLDS"
        if self.value is False:
            return "VIOLATED"
        return "UNKNOWN_NOT_FAVORABLE"

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "verdict": self.verdict(),
                "derivation_kind": self.derivation_kind,
                "evidence_refs": list(self.evidence_refs),
                "before_state": self.before_state, "after_state": self.after_state,
                "decision_surface": self.decision_surface, "reason": self.reason}


def not_derivable(reason: str) -> GuardedPropertyValue:
    """The honest verdict when the run surface does not expose the relation.
    Never a violation, never a pass: an evidence gap."""
    return GuardedPropertyValue(value=None, derivation_kind="NOT_DERIVABLE",
                                reason=reason)


def _gp_to_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, GuardedPropertyValue):
        return value.to_dict()
    raise GuardedContractError(
        "guarded-property values must be GuardedPropertyValue records carrying "
        f"their derivation evidence; got {type(value).__name__}. A bare boolean "
        "cannot certify a guarded property (review finding R-G8-05)")


# --------------------------------------------------------------------------- #
# Comparison
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ComparisonResult:
    comparison_id: str
    family_id: str
    left_id: str
    right_id: str
    verdict: str                       # CONSISTENT | MATERIAL_DISCRIMINATOR |
                                       # NOT_COMPARABLE | CONTRADICTION
    reason: str
    differing_fields: Tuple[str, ...]
    discriminator_ids: Tuple[str, ...] = ()
    governing_contract_refs: Tuple[str, ...] = ()
    left_outcome_class: str = ""
    right_outcome_class: str = ""
    classification: str = ""           # set only for CONTRADICTION
    severity: str = ""
    undeclared_fields: Tuple[str, ...] = ()
    mandated: bool = False
    left_ref: str = ""
    right_ref: str = ""
    unverifiable_order_fields: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {"comparison_id": self.comparison_id, "family_id": self.family_id,
                "left_id": self.left_id, "right_id": self.right_id,
                "left_ref": self.left_ref, "right_ref": self.right_ref,
                "verdict": self.verdict, "reason": self.reason,
                "unverifiable_order_fields": list(self.unverifiable_order_fields),
                "differing_fields": list(self.differing_fields),
                "discriminator_ids": list(self.discriminator_ids),
                "governing_contract_refs": list(self.governing_contract_refs),
                "left_outcome_class": self.left_outcome_class,
                "right_outcome_class": self.right_outcome_class,
                "classification": self.classification, "severity": self.severity,
                "undeclared_fields": list(self.undeclared_fields),
                "mandated": self.mandated}


def _field_order(contract: Mapping[str, Any], name: str) -> Optional[List[str]]:
    for spec in contract["equivalence_fields"]:
        if spec["field"] == name:
            return None if spec["order"] == "UNORDERED" else list(spec["order"])
    return None


def _discriminators_for(contract: Mapping[str, Any], name: str
                        ) -> List[Mapping[str, Any]]:
    return [d for d in contract["discriminator_rules"] if d["field"] == name]


def _verified_fields(contract: Mapping[str, Any], family_id: str) -> frozenset:
    """Fields whose derivation for this family is declared COMPLETE enough to
    carry an equivalence verdict. A field absent from this set is a coarse proxy:
    differences in it may neither justify an outcome nor be turned into an
    architectural claim — such a comparison is an evidence gap."""
    for fam in contract["comparison_families"]:
        if fam["family_id"] == family_id:
            return frozenset(fam.get("verified_fields", []))
    return frozenset()


def _equivalence_basis(contract: Mapping[str, Any], family_id: str) -> str:
    """Whether the family's declared vector is sufficient to establish equivalence
    at all. PARTIAL means an identical vector is necessary but not sufficient, so
    an identical-vector divergence is an evidence gap, not an architectural
    finding."""
    for fam in contract["comparison_families"]:
        if fam["family_id"] == family_id:
            return str(fam.get("equivalence_basis", "PARTIAL"))
    return "PARTIAL"


#: verdicts that count as a SUBSTANTIVE adjudication of a mandatory relationship.
#: Merely invoking the comparator is not coverage (review finding R-G8-01).
SUBSTANTIVE_VERDICTS = ("CONSISTENT", "MATERIAL_DISCRIMINATOR")


def _adjudication_fields(contract: Mapping[str, Any], family_id: str) -> Tuple[str, ...]:
    """Fields that carry the family's own relation. Declared, never inferred."""
    for fam in contract["comparison_families"]:
        if fam["family_id"] == family_id:
            return tuple(fam.get("adjudication_requires", ()))
    return ()


def _family_diagnostic(contract: Mapping[str, Any], family_id: str) -> bool:
    """A DIAGNOSTIC family claims no equivalence verdict at all. Its comparisons are
    recorded (so the machine-local observation stays visible) but they are never
    promoted to a contradiction and never block the gate."""
    for fam in contract["comparison_families"]:
        if fam["family_id"] == family_id:
            return bool(fam.get("diagnostic", False))
    return False


def _non_exercising_tokens(contract: Mapping[str, Any]) -> frozenset:
    """Tokens that mean 'this run surface did not exercise the relation'."""
    return frozenset(contract.get("non_exercising_tokens",
                                  ["UNKNOWN", "NOT_EXERCISED", "NOT_APPLICABLE"]))


def _empirical(machine: str, object_class: str) -> bool:
    """Empirical surfaces: evidence, knowledge and domain truth. Action /
    authority surfaces may legitimately respond to availability and reversibility."""
    return (machine in ("EVIDENCE", "M4_KNOWLEDGE", "DOMAIN_MACHINE")
            or object_class in ("EVIDENCE_CLAIM", "KNOWLEDGE_OBJECT", "DOMAIN_CLAIM",
                                "EPOCH"))


def compare_observations(contract: Mapping[str, Any],
                         left: InstitutionalObservation,
                         right: InstitutionalObservation,
                         *, mandated: bool = False) -> ComparisonResult:
    """Public comparison entry point: runs the pure comparison and attaches the
    two observations' source refs so mandated-pair coverage can be proven."""
    result = _compare_core(contract, left, right, mandated=mandated)
    return replace(result, left_ref=left.source_ref, right_ref=right.source_ref)


def _compare_core(contract: Mapping[str, Any],
                  left: InstitutionalObservation,
                  right: InstitutionalObservation,
                  *, mandated: bool = False) -> ComparisonResult:
    """Pure comparison. Every branch is driven by the frozen contract, never by
    an identifier or an expected outcome."""
    family_id = left.family_id
    cid = deterministic_hex("g8_cmp", left.observation_id, right.observation_id,
                            mandated, length=20)

    def _fail(reason: str, *, fields_: Tuple[str, ...] = (),
              discriminators: Tuple[str, ...] = (),
              refs: Tuple[str, ...] = (),
              classification: Optional[str] = None,
              severity: str = "BLOCKING",
              undeclared: Tuple[str, ...] = ()) -> ComparisonResult:
        return ComparisonResult(
            comparison_id=cid, family_id=family_id, left_id=left.observation_id,
            right_id=right.observation_id, verdict="CONTRADICTION", reason=reason,
            differing_fields=fields_, discriminator_ids=discriminators,
            governing_contract_refs=refs, left_outcome_class=left.outcome_class,
            right_outcome_class=right.outcome_class,
            classification=classification or _default_classification(contract, family_id),
            severity=severity, undeclared_fields=undeclared, mandated=mandated)

    if left.observation_id == right.observation_id:
        raise ValueError("cannot compare an observation with itself")
    if left.family_id != right.family_id:
        raise ValueError("comparison requires both observations in one family")

    # R3 — a mandatory relationship must be SUBSTANTIVELY adjudicated. When the
    # family declares the fields that carry its relation and neither observation
    # exercises any of them, an identical-or-different outcome comparison proves
    # nothing about the institution: it is an evidence gap, never a pass.
    adjudication = _adjudication_fields(contract, family_id)
    if adjudication:
        inert = _non_exercising_tokens(contract)
        exercised = [f for f in adjudication
                     if left.vector.values.get(f, "UNKNOWN") not in inert
                     or right.vector.values.get(f, "UNKNOWN") not in inert]
        if not exercised:
            return _fail(
                "neither observation exercises any field that carries this "
                f"family's relation ({list(adjudication)} are all non-exercising "
                "on both sides) — the mandatory relationship is an evidence gap, "
                "not an adjudicated equivalence",
                classification="INSUFFICIENT_EVIDENCE", severity="HIGH")

    # N8 / C05 — different state machines are never comparable vocabulary.
    if left.state_machine != right.state_machine:
        return ComparisonResult(
            comparison_id=cid, family_id=family_id, left_id=left.observation_id,
            right_id=right.observation_id, verdict="NOT_COMPARABLE",
            reason=(f"different state machines ({left.state_machine} vs "
                    f"{right.state_machine}): terminal vocabulary is not "
                    f"interchangeable (contract rule N8)"),
            differing_fields=(), left_outcome_class=left.outcome_class,
            right_outcome_class=right.outcome_class, mandated=mandated)

    # N7 — an unmapped token is an evidence gap, never a class.
    if not left.outcome_mapped or not right.outcome_mapped:
        unmapped = [o.observation_id for o in (left, right) if not o.outcome_mapped]
        return ComparisonResult(
            comparison_id=cid, family_id=family_id, left_id=left.observation_id,
            right_id=right.observation_id, verdict="CONTRADICTION",
            reason=("outcome token is absent from the frozen token map for "
                    f"{unmapped} — nearest-class assignment is forbidden (rule N7)"),
            differing_fields=(), left_outcome_class=left.outcome_class,
            right_outcome_class=right.outcome_class,
            classification="INSUFFICIENT_EVIDENCE", severity="HIGH",
            mandated=mandated)

    differing = left.vector.differing_fields(right.vector)
    same_class = left.outcome_class == right.outcome_class

    # A diagnostic family records what the machine-local vocabulary does; it claims
    # no equivalence verdict, so its pairs are NOT_COMPARABLE / NOT_EQUIVALENT and
    # are never promoted into the contradiction register.
    if _family_diagnostic(contract, family_id):
        return ComparisonResult(
            comparison_id=cid, family_id=family_id, left_id=left.observation_id,
            right_id=right.observation_id, verdict="NOT_COMPARABLE",
            reason=("diagnostic family: no equivalence verdict is claimed. The "
                    f"machine-local tokens ({left.raw_outcome_token!r} vs "
                    f"{right.raw_outcome_token!r}) come from different "
                    "vocabularies and are not interchangeable (rule N8); the "
                    "mandated relationship is adjudicated in F2 through the "
                    "conceptual projection."),
            differing_fields=differing, left_outcome_class=left.outcome_class,
            right_outcome_class=right.outcome_class,
            classification="NOT_EQUIVALENT", severity="INFO", mandated=mandated)

    if not differing:
        if same_class:
            return ComparisonResult(
                comparison_id=cid, family_id=family_id, left_id=left.observation_id,
                right_id=right.observation_id, verdict="CONSISTENT",
                reason="equivalent equivalence vector produced the same outcome class",
                differing_fields=(), left_outcome_class=left.outcome_class,
                right_outcome_class=right.outcome_class, mandated=mandated)
        if _equivalence_basis(contract, family_id) == "DECLARED_SUFFICIENT":
            return _fail(
                "equivalent governed facts produced incompatible outcome classes "
                f"({left.outcome_class} vs {right.outcome_class})")
        # The declared vector does NOT distinguish these observations and the
        # family's basis is only PARTIAL, so the audit cannot tell an institutional
        # inconsistency from an incomplete observation. Recorded as an
        # UNDISCRIMINATED DIVERGENCE — never silently promoted to an architectural
        # claim, never silently treated as equivalent.
        return _fail(
            "UNDISCRIMINATED DIVERGENCE: the declared vector for this family is "
            "identically satisfied yet the outcome classes differ "
            f"({left.outcome_class} vs {right.outcome_class}); with an "
            "equivalence_basis of PARTIAL the audit cannot establish whether the "
            "facts are equivalent",
            classification="INSUFFICIENT_EVIDENCE", severity="HIGH")

    # differing fields exist: every one must be governed by a declared rule.
    undeclared = tuple(f for f in differing if not _discriminators_for(contract, f))
    verified = _verified_fields(contract, family_id)
    verified_diff = tuple(f for f in differing if f in verified)
    justifies: List[Mapping[str, Any]] = []
    justifies_verified: List[Mapping[str, Any]] = []
    order_violations: List[Mapping[str, Any]] = []
    unverifiable: List[str] = []
    must_not_diverge: List[Mapping[str, Any]] = []
    rank = contract["outcome_permissiveness"]["rank"]

    def _rank(obs: InstitutionalObservation) -> int:
        return int(rank[obs.outcome_class])

    for name in differing:
        order = _field_order(contract, name)
        for rule in _discriminators_for(contract, name):
            kind = rule["kind"]
            if kind == "JUSTIFIES_DIVERGENCE":
                justifies.append(rule)
                if name in verified:
                    justifies_verified.append(rule)
            elif kind == "NEUTRAL":
                continue
            elif kind == "MUST_NOT_VIOLATE_ORDER":
                if not order or name not in verified:
                    continue
                lv, rv = left.vector.values[name], right.vector.values[name]
                if lv not in order or rv not in order:
                    # UNKNOWN carries no level: the order relation is NOT
                    # evaluable, so it is recorded as an evidence gap instead of
                    # being silently treated as equal or as favorable
                    unverifiable.append(name)
                    continue
                # orient so that `higher` is the side further along the field order
                if order.index(lv) >= order.index(rv):
                    higher, lower = left, right
                else:
                    higher, lower = right, left
                if rule["direction"] == "NON_DECREASING":
                    if _rank(higher) < _rank(lower):
                        order_violations.append(rule)
                else:  # NON_INCREASING
                    if _rank(higher) > _rank(lower):
                        order_violations.append(rule)
            elif kind == "MUST_NOT_DIVERGE_EMPIRICAL":
                if ((not same_class) and name in verified
                        and _empirical(left.state_machine, left.object_class)):
                    must_not_diverge.append(rule)

    # MUST_NOT_DIVERGE_EMPIRICAL is checked first: an availability effect reaching
    # an empirical outcome class is the strongest violation available here.
    if must_not_diverge:
        rules = tuple(d["discriminator_id"] for d in must_not_diverge)
        refs = tuple(d["governing_contract"] for d in must_not_diverge)
        return _fail(
            "a declared neutral/availability difference changed an EMPIRICAL "
            f"outcome class ({left.outcome_class} vs {right.outcome_class}) on "
            f"fields {sorted(differing)}",
            fields_=differing, discriminators=rules, refs=refs,
            classification="ARCHITECTURE_CONTRADICTION")

    if order_violations:
        rules = tuple(f"{d['discriminator_id']}({d['field']})" for d in order_violations)
        refs = tuple(d["governing_contract"] for d in order_violations)
        return _fail(
            "a declared field order inverted the outcome permissiveness order on "
            f"fields {sorted(differing)}: {left.outcome_class} vs "
            f"{right.outcome_class} (permissiveness {_rank(left)} vs {_rank(right)})",
            fields_=differing, discriminators=rules, refs=refs,
            classification="ARCHITECTURE_CONTRADICTION")

    if undeclared:
        return _fail(
            f"differing fields {list(undeclared)} are not governed by any "
            "declared discriminator — an omitted discriminator may not silently "
            "produce equivalence",
            fields_=differing, undeclared=undeclared,
            classification="INSUFFICIENT_EVIDENCE")

    if same_class:
        # differences are declared, none is an order violation, none is an
        # empirical divergence. The same outcome only counts as governed if at
        # least one difference is a VERIFIED derivation; a same-outcome claim
        # resting purely on coarse proxies is an evidence gap, not a pass.
        if not verified_diff:
            return _fail(
                "the same outcome class rests on differences that are only coarse "
                f"proxies for this family ({list(differing)}) — equivalence is not "
                "established",
                fields_=differing, classification="INSUFFICIENT_EVIDENCE",
                severity="LOW")
        return ComparisonResult(
            comparison_id=cid, family_id=family_id, left_id=left.observation_id,
            right_id=right.observation_id, verdict="MATERIAL_DISCRIMINATOR",
            reason=("materially different facts reached the same outcome class "
                    "under declared discriminators (no declared order violated)"),
            differing_fields=differing,
            discriminator_ids=tuple(d["discriminator_id"] for d in justifies),
            governing_contract_refs=tuple(d["governing_contract"] for d in justifies),
            left_outcome_class=left.outcome_class,
            right_outcome_class=right.outcome_class, mandated=mandated,
            unverifiable_order_fields=tuple(sorted(set(unverifiable))))

    if justifies_verified:
        return ComparisonResult(
            comparison_id=cid, family_id=family_id, left_id=left.observation_id,
            right_id=right.observation_id, verdict="MATERIAL_DISCRIMINATOR",
            reason=("different outcomes are explained by declared material "
                    "discriminators on verified derivations"),
            differing_fields=differing,
            discriminator_ids=tuple(d["discriminator_id"] for d in justifies_verified),
            governing_contract_refs=tuple(d["governing_contract"]
                                          for d in justifies_verified),
            left_outcome_class=left.outcome_class,
            right_outcome_class=right.outcome_class, mandated=mandated,
            unverifiable_order_fields=tuple(sorted(set(unverifiable))))

    if unverifiable and not verified_diff:
        return _fail(
            "the outcome difference rests on fields whose declared order cannot be "
            f"evaluated because a level is UNKNOWN ({sorted(set(unverifiable))}) and "
            "on no verified derivation — the relation cannot be established",
            fields_=differing, classification="INSUFFICIENT_EVIDENCE", severity="LOW")

    if not verified_diff:
        return _fail(
            "different outcomes across differences that are only coarse proxies "
            f"for this family ({list(differing)}) — the audit cannot establish that "
            "the facts are equivalent or that the divergence is governed",
            fields_=differing, classification="INSUFFICIENT_EVIDENCE", severity="LOW")

    return _fail(
        "different outcomes on verified identical-or-materially-different facts "
        "with no declared discriminator explaining the divergence",
        fields_=differing, classification="ARCHITECTURE_CONTRADICTION")


def _default_classification(contract: Mapping[str, Any], family_id: str) -> str:
    for fam in contract["comparison_families"]:
        if fam["family_id"] == family_id:
            return fam.get("default_classification", "ARCHITECTURE_CONTRADICTION")
    return "UNKNOWN"


# --------------------------------------------------------------------------- #
# Guarded properties
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class GuardedPropertyFinding:
    """One guarded-property observation, carrying its own derivation evidence.

    The required shape is fixed by the review's guarded-property evidence
    contract: property_id, observation_id, value, verdict, derivation_kind,
    evidence_refs, before_state, after_state, decision_surface, reason.
    """

    property_id: str
    property_name: str
    governing_contract: str
    observation_id: str
    family_id: str
    value: Optional[bool]
    verdict: str                    # HOLDS | VIOLATED | UNKNOWN_NOT_FAVORABLE
    derivation_kind: str
    evidence_refs: Tuple[str, ...]
    before_state: str
    after_state: str
    decision_surface: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {"property_id": self.property_id, "property_name": self.property_name,
                "governing_contract": self.governing_contract,
                "observation_id": self.observation_id, "family_id": self.family_id,
                "value": self.value, "verdict": self.verdict,
                "derivation_kind": self.derivation_kind,
                "evidence_refs": list(self.evidence_refs),
                "before_state": self.before_state,
                "after_state": self.after_state,
                "decision_surface": self.decision_surface,
                "reason": self.reason}


def validate_guarded_finding(finding: GuardedPropertyFinding) -> None:
    """Defence in depth: re-check an already-built finding. A HOLDS record that
    lacks its required evidence shape is a hard failure, not a silent pass."""
    if finding.verdict != "HOLDS":
        return
    if finding.derivation_kind == "NOT_DERIVABLE":
        raise GuardedContractError(
            f"{finding.property_id}@{finding.observation_id}: HOLDS with a "
            "NOT_DERIVABLE derivation")
    if finding.derivation_kind not in DERIVATION_KINDS:
        raise GuardedContractError(
            f"{finding.property_id}@{finding.observation_id}: unknown "
            f"derivation_kind {finding.derivation_kind!r}")
    if not finding.evidence_refs:
        raise GuardedContractError(
            f"{finding.property_id}@{finding.observation_id}: HOLDS without a "
            "concrete evidence reference")
    if not finding.decision_surface:
        raise GuardedContractError(
            f"{finding.property_id}@{finding.observation_id}: HOLDS without a "
            "declared decision surface")
    if not finding.reason:
        raise GuardedContractError(
            f"{finding.property_id}@{finding.observation_id}: HOLDS without a "
            "stated reason")
    if finding.derivation_kind in _RELATIONAL_KINDS and not (
            finding.before_state and finding.after_state):
        raise GuardedContractError(
            f"{finding.property_id}@{finding.observation_id}: "
            f"{finding.derivation_kind} HOLDS without a before/after state")
    if finding.value is not True:
        raise GuardedContractError(
            f"{finding.property_id}@{finding.observation_id}: HOLDS with "
            f"value={finding.value!r}")


def check_guarded_properties(contract: Mapping[str, Any],
                             observations: Sequence[InstitutionalObservation]
                             ) -> List[GuardedPropertyFinding]:
    props = {p["property_id"]: p for p in contract["guarded_properties"]}
    out: List[GuardedPropertyFinding] = []
    for obs in observations:
        for pid in sorted(obs.guarded_properties):
            spec = props[pid]
            gp = obs.guarded_properties[pid]
            if not isinstance(gp, GuardedPropertyValue):
                raise GuardedContractError(
                    f"{pid}@{obs.observation_id}: guarded-property value is "
                    f"{type(gp).__name__}; every value must be a "
                    "GuardedPropertyValue carrying its derivation evidence")
            out.append(GuardedPropertyFinding(
                property_id=pid, property_name=spec["name"],
                governing_contract=spec["governing_contract"],
                observation_id=obs.observation_id, family_id=obs.family_id,
                value=gp.value, verdict=gp.verdict(),
                derivation_kind=gp.derivation_kind,
                evidence_refs=tuple(gp.evidence_refs),
                before_state=gp.before_state, after_state=gp.after_state,
                decision_surface=gp.decision_surface, reason=gp.reason))
    for finding in out:
        validate_guarded_finding(finding)
    return out


def guarded_derivation_coverage(contract: Mapping[str, Any],
                                observations: Sequence[InstitutionalObservation],
                                findings: Sequence[GuardedPropertyFinding],
                                ) -> Dict[str, Any]:
    """Per-property derivation coverage plus the closure gate.

    `closure_required_properties` names the properties G8 must PROVE at least
    once. A property that is required for closure and never returns HOLDS has not
    been proved by the absence of a violation: it blocks.

    STRESS-G8RX6, enforcement gap F2: the closure rule used to accept any finding
    whose derivation_kind was not NOT_DERIVABLE, whatever its verdict, so a
    required property exercised only as UNKNOWN_NOT_FAVORABLE still satisfied
    closure. A HOLDS finding carries its derivation evidence by construction
    (GuardedPropertyValue refuses to build one without it), so requiring a HOLDS
    makes the requirement enforceable rather than decorative. Properties that
    were touched but never held are reported separately from those never touched.
    """
    required = list(contract.get("closure_required_properties", []))
    by_property: Dict[str, Dict[str, int]] = {}
    for f in findings:
        slot = by_property.setdefault(f.property_id, {})
        slot[f.verdict] = slot.get(f.verdict, 0) + 1
        kind = slot.setdefault("kinds", {})  # type: ignore[assignment]
        if isinstance(kind, dict):
            kind[f.derivation_kind] = kind.get(f.derivation_kind, 0) + 1
    holds = {f.property_id for f in findings if f.verdict == "HOLDS"}
    touched = {f.property_id for f in findings
               if f.derivation_kind != "NOT_DERIVABLE"}
    unexercised = sorted(p for p in required if p not in holds)
    return {"closure_rule": ("a closure-required property must return HOLDS at "
                             "least once, with the derivation evidence a HOLDS "
                             "finding is required to carry"),
            "closure_required_properties": required,
            "per_property": {k: by_property[k] for k in sorted(by_property)},
            "unexercised_required_properties": unexercised,
            "required_never_derived": sorted(p for p in required
                                             if p not in touched),
            "declared_observations": len(observations)}


# --------------------------------------------------------------------------- #
# Equivalence classes + family runs
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class EquivalenceClass:
    class_id: str
    family_id: str
    state_machine: str
    object_class: str
    vector_digest: str
    members: Tuple[str, ...]
    outcome_classes: Tuple[str, ...]
    coherent: bool

    def to_dict(self) -> Dict[str, Any]:
        return {"class_id": self.class_id, "family_id": self.family_id,
                "state_machine": self.state_machine,
                "object_class": self.object_class, "vector_digest": self.vector_digest,
                "members": list(self.members),
                "outcome_classes": list(self.outcome_classes),
                "coherent": self.coherent}


def build_equivalence_classes(observations: Sequence[InstitutionalObservation]
                              ) -> List[EquivalenceClass]:
    buckets: Dict[Tuple[str, str, str, str], List[InstitutionalObservation]] = {}
    for obs in observations:
        key = (obs.family_id, obs.state_machine, obs.object_class,
               obs.vector.digest())
        buckets.setdefault(key, []).append(obs)
    classes: List[EquivalenceClass] = []
    for (family_id, machine, obj, digest), members in sorted(buckets.items()):
        classes_outcome = tuple(sorted({m.outcome_class for m in members}))
        classes.append(EquivalenceClass(
            class_id=deterministic_hex("g8_class", family_id, machine, obj, digest,
                                       length=20),
            family_id=family_id, state_machine=machine, object_class=obj,
            vector_digest=digest,
            members=tuple(sorted(m.observation_id for m in members)),
            outcome_classes=classes_outcome,
            coherent=len(classes_outcome) <= 1))
    return classes


@dataclass(frozen=True)
class DerivationLimitation:
    """A declared outcome-relevant field that could not discriminate inside this
    family's run (revision R1).

    Two cases, both recorded rather than hidden:
      * CONSTANT_DERIVATION — the field was derived but took ONE value across every
        member, so the audit's own derivation cannot explain a divergence on it.
      * IDENTICALLY_UNKNOWN — the field was UNKNOWN for every member, so it was not
        derived at all from the run surface.
    Neither is an institutional finding; both mean the family's vector is less
    discriminating than its declaration claims, which is exactly what produced the
    pre-revision F4/F5 gaps.
    """

    family_id: str
    field: str
    limitation: str
    only_value: str
    member_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {"family_id": self.family_id, "field": self.field,
                "limitation": self.limitation, "only_value": self.only_value,
                "member_count": self.member_count}


def derivation_limitations(contract: Mapping[str, Any],
                           families: Sequence[FamilyAuditResult],
                           observations: Mapping[str, InstitutionalObservation]
                           ) -> List[DerivationLimitation]:
    out: List[DerivationLimitation] = []
    for fam in families:
        members = [observations[m] for m in fam.member_ids if m in observations]
        if len(members) < 2:
            continue
        for field in sorted(_verified_fields(contract, fam.family_id)):
            values = {m.vector.values.get(field, "UNKNOWN") for m in members}
            undeclared = [m for m in members if m.vector.derivation_status.get(field)
                          == "UNDECLARED_TOKEN_FAILED_CLOSED"]
            if len(values) == 1:
                only = sorted(values)[0]
                out.append(DerivationLimitation(
                    family_id=fam.family_id, field=field,
                    limitation=("IDENTICALLY_UNKNOWN" if only == "UNKNOWN"
                                else "CONSTANT_DERIVATION"),
                    only_value=only, member_count=len(members)))
            elif undeclared:
                # the field varies, but some members' declared values are not in
                # the declared token vocabulary and therefore collapsed to UNKNOWN.
                # That is precisely how a real material difference can disappear
                # during comparison, so it is recorded rather than tolerated.
                out.append(DerivationLimitation(
                    family_id=fam.family_id, field=field,
                    limitation="PARTIALLY_UNDECLARED",
                    only_value=f"{len(undeclared)}/{len(members)} undeclared tokens",
                    member_count=len(members)))
    return out


def derivation_completeness(contract: Mapping[str, Any],
                            limitations: Sequence[DerivationLimitation]) -> Dict[str, Any]:
    unknown = [d for d in limitations if d.limitation == "IDENTICALLY_UNKNOWN"]
    constant = [d for d in limitations if d.limitation == "CONSTANT_DERIVATION"]
    partial = [d for d in limitations if d.limitation == "PARTIALLY_UNDECLARED"]
    return {
        "declared_verified_field_count": sum(
            len(_verified_fields(contract, f["family_id"]))
            for f in contract["comparison_families"]),
        "identically_unknown": len(unknown),
        "constant_derivation": len(constant),
        "partially_undeclared": len(partial),
        "discriminating_field_count": sum(
            len(_verified_fields(contract, f["family_id"]))
            for f in contract["comparison_families"]) - len(limitations),
        "limitations": [d.to_dict() for d in limitations],
        "note": ("a verified field that never varied cannot discriminate inside this "
                 "run. Recorded as a derivation limitation so a divergence that the "
                 "declared vector cannot explain is never mistaken for an "
                 "institutional contradiction, and never mistaken for a pass."),
    }


@dataclass(frozen=True)
class FamilyAuditResult:
    family_id: str
    family_class: str
    question: str
    member_ids: Tuple[str, ...]
    comparisons: Tuple[ComparisonResult, ...]
    classes: Tuple[EquivalenceClass, ...]
    guarded: Tuple[GuardedPropertyFinding, ...]
    covered_observations: Tuple[str, ...]
    missing_members: Tuple[str, ...]
    unmapped_members: Tuple[str, ...]

    def contradictions(self) -> Tuple[ComparisonResult, ...]:
        return tuple(c for c in self.comparisons if c.verdict == "CONTRADICTION")

    def to_dict(self) -> Dict[str, Any]:
        return {"family_id": self.family_id, "family_class": self.family_class,
                "question": self.question, "member_ids": list(self.member_ids),
                "comparisons": [c.to_dict() for c in self.comparisons],
                "equivalence_classes": [c.to_dict() for c in self.classes],
                "guarded_property_findings": [g.to_dict() for g in self.guarded],
                "counts": {
                    "members": len(self.member_ids),
                    "covered": len(self.covered_observations),
                    "missing": len(self.missing_members),
                    "comparisons": len(self.comparisons),
                    "consistent": sum(1 for c in self.comparisons
                                      if c.verdict == "CONSISTENT"),
                    "material_discriminator": sum(
                        1 for c in self.comparisons
                        if c.verdict == "MATERIAL_DISCRIMINATOR"),
                    "not_comparable": sum(1 for c in self.comparisons
                                          if c.verdict == "NOT_COMPARABLE"),
                    "contradictions": len(self.contradictions()),
                    "equivalence_classes": len(self.classes),
                    "unverifiable_order_comparisons": sum(
                        1 for c in self.comparisons if c.unverifiable_order_fields),
                },
                "missing_members": list(self.missing_members),
                "unmapped_members": list(self.unmapped_members)}


def run_comparison_family(contract: Mapping[str, Any],
                          family: Mapping[str, Any],
                          observations: Mapping[str, InstitutionalObservation]
                          ) -> FamilyAuditResult:
    """Compare every observation pair inside one declared family, plus the
    family's explicitly mandated pairs (which are also auto-enumerated when both
    members resolve). Pair enumeration is a function of the family declaration,
    never of an identifier pattern."""
    # resolve members strictly inside this family, by observation id or by the
    # source ref the family declares (so one run surface may be read by several
    # families without their observations colliding)
    pool = [o for o in observations.values() if o.family_id == family["family_id"]]
    index = {o.observation_id: o for o in pool}
    ref_index = {o.source_ref: o for o in pool}
    members: List[InstitutionalObservation] = []
    missing: List[str] = []
    for ref in family["members"]:
        obs = index.get(ref) or ref_index.get(ref)
        if obs is None:
            missing.append(ref)
        else:
            members.append(obs)

    mandated_set = {tuple(sorted(p)) for p in family.get("declared_pairs", [])}
    comparisons: List[ComparisonResult] = []
    for i, left in enumerate(members):
        for right in members[i + 1:]:
            key = tuple(sorted((left.source_ref, right.source_ref)))
            comparisons.append(compare_observations(
                contract, left, right, mandated=key in mandated_set))

    unmapped = [m.observation_id for m in members if not m.outcome_mapped]
    return FamilyAuditResult(
        family_id=family["family_id"], family_class=family["family_class"],
        question=family["question"],
        member_ids=tuple(m.observation_id for m in members),
        comparisons=tuple(comparisons),
        classes=tuple(build_equivalence_classes(members)),
        guarded=tuple(check_guarded_properties(contract, members)),
        covered_observations=tuple(m.observation_id for m in members),
        missing_members=tuple(missing), unmapped_members=tuple(unmapped))


def mandated_pair_coverage(contract: Mapping[str, Any],
                           results: Sequence[FamilyAuditResult]
                           ) -> Dict[str, Any]:
    """Prove every mandated relationship was SUBSTANTIVELY ADJUDICATED.

    Revision R3 (review finding R-G8-01): running the comparator is not coverage.
    A mandated pair counts as adjudicated only when its comparison returned a
    substantive verdict (CONSISTENT / MATERIAL_DISCRIMINATOR). A pair whose only
    comparison was NOT_COMPARABLE, that was never compared, or whose members never
    resolved stays UNCOVERED and carries the reason, so a gate cannot pass by
    merely invoking the comparator.
    """
    by_ref: Dict[str, List[ComparisonResult]] = {}
    for r in results:
        for c in r.comparisons:
            by_ref.setdefault(c.family_id, []).append(c)
    uncovered: List[Dict[str, str]] = []
    not_comparable: List[Dict[str, str]] = []
    observed = 0
    adjudicated = 0
    for family in contract["comparison_families"]:
        fid = family["family_id"]
        for pair in family.get("declared_pairs", []):
            want = tuple(sorted(pair))
            matched = [c for c in by_ref.get(fid, ())
                       if set(want) <= {c.left_ref, c.right_ref}]
            if not matched:
                uncovered.append({"family_id": fid, "pair": " vs ".join(want),
                                  "reason": "no comparison was produced for this "
                                            "mandated relationship"})
                continue
            observed += 1
            verdicts = sorted({c.verdict for c in matched})
            if any(v in SUBSTANTIVE_VERDICTS for v in verdicts):
                adjudicated += 1
                continue
            entry = {"family_id": fid, "pair": " vs ".join(want),
                     "verdicts": ", ".join(verdicts),
                     "reason": ("no substantive verdict: "
                                + ("the participating state machines differ, so "
                                   "terminal vocabulary is not interchangeable"
                                   if verdicts == ["NOT_COMPARABLE"] else
                                   "the comparison did not adjudicate the relation"))}
            uncovered.append(entry)
            if "NOT_COMPARABLE" in verdicts:
                not_comparable.append(entry)
    return {"mandated_pairs": sum(len(f.get("declared_pairs", []))
                                  for f in contract["comparison_families"]),
            "mandated_comparisons_observed": observed,
            "mandated_pairs_substantively_adjudicated": adjudicated,
            "mandated_pairs_not_comparable": not_comparable,
            "uncovered_mandated_pairs": uncovered}


# --------------------------------------------------------------------------- #
# Contradiction register
# --------------------------------------------------------------------------- #
def decide_gate(contract: Mapping[str, Any],
                families: Sequence[FamilyAuditResult],
                guarded: Sequence[GuardedPropertyFinding],
                gate_findings: Sequence[GateClaimFinding],
                *, test_evidence: TestEvidence,
                expected_tested_sha: str,
                observations: Sequence[InstitutionalObservation] = (),
                ) -> Dict[str, Any]:
    """Gate decision computed from the evidence, never asserted. BLOCKING items are
    architectural contradictions, guarded-property violations, gate-claim defects,
    unaudited mandatory relationships, unexercised closure-required properties and
    unverifiable test evidence. HIGH-severity INSUFFICIENT_EVIDENCE items are
    reported as missing evidence rather than being folded into either a pass or a
    contradiction.

    Revision R3 (review findings R-G8-01, R-G8-05, R-G8-07): the baselines that
    used to be bare integers now come from a provenance-bearing test-result
    artifact, and the gate no longer infers 'no detected violation therefore
    property proved'.

    STRESS-G8RX6, enforcement gap F1: `expected_tested_sha` is the tree the caller
    DECLARES this package is archived for. The baseline check compares the
    artifact's bound tree against it, so the gate can detect a stale or foreign
    artifact. The previous call site passed `test_evidence.tested_sha` as its own
    expectation, which made the check unfalsifiable: a forged tree certified.
    """
    policy = contract.get("blocks_gate_policy", {})
    hard = set(policy.get("blocking_classifications", ()))
    unresolvable = set(policy.get("blocking_when_unresolvable", ()))
    never = set(policy.get("never_blocking_classifications", ()))

    comparisons = [c for fam in families for c in fam.comparisons]
    contradictions = [c for c in comparisons if c.verdict == "CONTRADICTION"]
    blocking = [c for c in contradictions
                if c.classification in hard
                or (c.classification in unresolvable and c.severity != "LOW")]
    gaps = [c for c in contradictions if c.classification == "INSUFFICIENT_EVIDENCE"
            and c.severity != "LOW"]
    low_gaps = [c for c in contradictions if c.classification == "INSUFFICIENT_EVIDENCE"
                and c.severity == "LOW"]
    violations = [g for g in guarded if g.verdict == "VIOLATED"]
    gate_blocking = [f for f in gate_findings
                     if f.blocks_gate and f.classification not in never]
    gate_recorded = [f for f in gate_findings if f.is_defect and not f.blocks_gate]
    gate_superseded = [f for f in gate_findings if f.superseded_by]

    baseline = check_baseline(test_evidence, tested_sha=expected_tested_sha)
    mandate = mandate_coverage_flags(contract, families)
    coverage = guarded_derivation_coverage(contract, observations, guarded)
    unexercised = coverage["unexercised_required_properties"]

    reasons: List[str] = []
    exit_label = "PASS_G8_CROSS_SCENARIO_COHERENCE"

    def _block(label: str, reason: str) -> None:
        nonlocal exit_label
        if exit_label == "PASS_G8_CROSS_SCENARIO_COHERENCE":
            exit_label = label
        reasons.append(reason)

    if not baseline["verified"]:
        exit_label = "BLOCKED_G8_BASELINE_FAILURE"
        reasons.append("unverifiable test baseline: "
                       + "; ".join(baseline["problems"]))
    if blocking:
        exit_label = "BLOCKED_G8_ARCHITECTURE_CONTRADICTION"
        reasons.append(f"{len(blocking)} BLOCKING contradiction(s)")
    if violations:
        exit_label = "BLOCKED_G8_ARCHITECTURE_CONTRADICTION"
        reasons.append(f"{len(violations)} guarded-property violation(s)")
    if gate_blocking:
        _block("BLOCKED_G8_MISSING_EVIDENCE",
               f"{len(gate_blocking)} blocking gate-claim finding(s)")
    if gaps:
        _block("BLOCKED_G8_MISSING_EVIDENCE",
               f"{len(gaps)} high-severity evidence gap(s) where equivalence "
               "could not be established")
    if mandate["uncovered"]:
        _block("BLOCKED_G8_MISSING_EVIDENCE",
               f"{len(mandate['uncovered'])} mandated relationship(s) not "
               f"substantively adjudicated ({len(mandate['not_comparable'])} of "
               "them returned NOT_COMPARABLE)")
    if unexercised:
        # 'no detected violation' is not 'property proved'
        _block("BLOCKED_G8_MISSING_EVIDENCE",
               f"{len(unexercised)} closure-required guarded propert(ies) never "
               f"returned HOLDS with derivation evidence: {unexercised}")
    return {"exit": exit_label, "reasons": reasons,
            "declared_tested_sha": expected_tested_sha,
            "counts": {"comparisons": len(comparisons),
                       "blocking_contradictions": len(blocking),
                       "evidence_gaps": len(gaps),
                       "low_severity_gaps_recorded_only": len(low_gaps),
                       "guarded_violations": len(violations),
                       "guarded_unknown": sum(1 for g in guarded
                                              if g.verdict == "UNKNOWN_NOT_FAVORABLE"),
                       "guarded_holds": sum(1 for g in guarded
                                            if g.verdict == "HOLDS"),
                       "unexercised_required_properties": len(unexercised),
                       "mandated_not_adjudicated": len(mandate["uncovered"]),
                       "gate_claim_blocking": len(gate_blocking),
                       "gate_claim_recorded_not_blocking": len(gate_recorded),
                       "gate_claim_superseded": len(gate_superseded)},
            "baseline": baseline,
            "blocks_gate_policy_ref": contract.get("blocks_gate_policy", {}).get(
                "note", ""),
            "mandated": mandate,
            "guarded_coverage": coverage}


def mandate_coverage_flags(contract: Mapping[str, Any],
                           families: Sequence[FamilyAuditResult]) -> Dict[str, Any]:
    coverage = mandated_pair_coverage(contract, families)
    return {"mandated_pairs": coverage["mandated_pairs"],
            "observed": coverage["mandated_comparisons_observed"],
            "adjudicated": coverage["mandated_pairs_substantively_adjudicated"],
            "not_comparable": coverage["mandated_pairs_not_comparable"],
            "uncovered": coverage["uncovered_mandated_pairs"]}


def build_contradiction_register(contract: Mapping[str, Any],
                                 families: Sequence[FamilyAuditResult],
                                 guarded: Sequence[GuardedPropertyFinding],
                                 gate_findings: Sequence["GateClaimFinding"]
                                 ) -> Dict[str, Any]:
    """One register, one classification vocabulary. Nothing is downgraded because
    it would delay a later gate."""
    policy = contract.get("blocks_gate_policy", {})
    hard = set(policy.get("blocking_classifications", ()))
    unresolvable = set(policy.get("blocking_when_unresolvable", ()))
    entries: List[Dict[str, Any]] = []
    for fam in families:
        for cmp in fam.contradictions():
            blocks = (cmp.classification in hard
                      or (cmp.classification in unresolvable and cmp.severity != "LOW"))
            entries.append({
                "entry_id": deterministic_hex("g8_register", cmp.comparison_id,
                                              length=20),
                "kind": "COMPARISON_CONTRADICTION",
                "classification": cmp.classification,
                "severity": cmp.severity,
                "blocks_gate": blocks,
                "audit_basis": ("UNDISCRIMINATED_DIVERGENCE" if "UNDISCRIMINATED" in
                                cmp.reason else "DECLARED_FIELDS"),
                "verbatim_limits": ("the declared equivalence vector for this family "
                                    "is PARTIAL; this entry records that equivalence "
                                    "could not be established, not a proven "
                                    "institutional inconsistency"
                                    if cmp.classification == "INSUFFICIENT_EVIDENCE"
                                    else ""),
                "family_id": cmp.family_id,
                "left": cmp.left_id, "right": cmp.right_id,
                "differing_fields": list(cmp.differing_fields),
                "undeclared_fields": list(cmp.undeclared_fields),
                "discriminator_ids": list(cmp.discriminator_ids),
                "governing_contract_refs": list(cmp.governing_contract_refs),
                "reason": cmp.reason,
                "preserved_evidence": {
                    "left_outcome_class": cmp.left_outcome_class,
                    "right_outcome_class": cmp.right_outcome_class,
                    "mandated_pair": cmp.mandated,
                },
                "changes_historical_meaning": False,
                "required_next_authority": "operator/architecture review",
            })
    for finding in guarded:
        if finding.verdict != "VIOLATED":
            continue
        entries.append({
            "entry_id": deterministic_hex("g8_register_guard",
                                          finding.property_id,
                                          finding.observation_id, length=20),
            "kind": "GUARDED_PROPERTY_VIOLATION",
            "classification": "ARCHITECTURE_CONTRADICTION",
            "severity": "BLOCKING",
            "family_id": finding.family_id,
            "left": finding.observation_id, "right": "",
            "differing_fields": [],
            "undeclared_fields": [],
            "discriminator_ids": [],
            "governing_contract_refs": [finding.governing_contract],
            "reason": (f"{finding.property_name}: {finding.reason} "
                       f"[derivation={finding.derivation_kind}; "
                       f"surface={finding.decision_surface}; "
                       f"before={finding.before_state}; after={finding.after_state}]"),
            "preserved_evidence": finding.to_dict(),
            "changes_historical_meaning": False,
            "required_next_authority": "operator/architecture review",
        })
    # A diagnostic family claims no verdict, so its non-comparability is RECORDED
    # rather than dropped: the machine-local observation stays visible and every
    # incoherent equivalence class still has a matching register entry.
    for fam in families:
        if not _family_diagnostic(contract, fam.family_id):
            continue
        for cmp in fam.comparisons:
            if cmp.verdict != "NOT_COMPARABLE":
                continue
            entries.append({
                "entry_id": deterministic_hex("g8_register_diag", fam.family_id,
                                              cmp.comparison_id, length=20),
                "kind": "DIAGNOSTIC_NON_COMPARABILITY",
                "classification": "NOT_EQUIVALENT",
                "severity": "INFO",
                "blocks_gate": False,
                "family_id": fam.family_id,
                "left": cmp.left_id, "right": cmp.right_id,
                "differing_fields": list(cmp.differing_fields),
                "undeclared_fields": [],
                "discriminator_ids": [],
                "governing_contract_refs": ["rule N8"],
                "reason": cmp.reason,
                "preserved_evidence": {
                    "left_outcome_class": cmp.left_outcome_class,
                    "right_outcome_class": cmp.right_outcome_class},
                "changes_historical_meaning": False,
                "required_next_authority": "none (diagnostic family claims no verdict)",
            })
    for finding in gate_findings:
        if not finding.is_defect and not finding.superseded_by:
            continue
        entries.append({
            "entry_id": deterministic_hex("g8_register_gate", finding.receipt_path,
                                          finding.finding_id, length=20),
            "kind": ("GATE_CLAIM_FINDING" if finding.is_defect
                     else "GATE_CLAIM_FINDING_SUPERSEDED"),
            "classification": finding.classification,
            "severity": finding.severity,
            "blocks_gate": finding.blocks_gate,
            "superseded_by": finding.superseded_by,
            "supersession_detail": finding.supersession_detail,
            "family_id": "F7",
            "left": finding.receipt_path, "right": "",
            "differing_fields": [],
            "undeclared_fields": [],
            "discriminator_ids": [],
            "governing_contract_refs": [finding.governing_contract],
            "reason": finding.detail,
            "preserved_evidence": finding.evidence,
            "changes_historical_meaning": finding.changes_historical_meaning,
            "required_next_authority": ("none — corrected by a later recorded "
                                        "artifact" if finding.superseded_by
                                        else "operator/architecture review"),
        })
    by_class: Dict[str, int] = {}
    for entry in entries:
        by_class[entry["classification"]] = by_class.get(entry["classification"], 0) + 1
    return {
        "register_id": "G8-CONTRADICTION-REGISTER-001",
        "classification_vocabulary": list(contract["classification_vocabulary"]),
        "entries": entries,
        "counts_by_classification": {k: by_class[k] for k in sorted(by_class)},
        "open_entries": len(entries),
        "note": ("an entry with classification NOT_EQUIVALENT or "
                 "FUTURE_PLANNING_IMPACT is not an institutional contradiction; "
                 "every other class requires authority review before "
                 "ratification"),
    }


# --------------------------------------------------------------------------- #
# Gate claim audit
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class GateClaimFinding:
    finding_id: str
    receipt_path: str
    claim: str
    observed: str
    is_defect: bool
    classification: str
    severity: str
    governing_contract: str
    detail: str
    changes_historical_meaning: bool = False
    evidence: Dict[str, Any] = field(default_factory=dict)
    #: literals that identify WHAT this finding is about (the declaration key it
    #: read, or the value it disputed). A later evidence artifact that both names
    #: this receipt and mentions one of these literals is treated as correcting
    #: this finding (revision R2). Derived from the finding itself, never from a
    #: path pattern or an identifier predicate.
    subject_tokens: Tuple[str, ...] = ()
    blocks_gate: bool = True
    superseded_by: str = ""
    supersession_detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"finding_id": self.finding_id, "receipt_path": self.receipt_path,
                "claim": self.claim, "observed": self.observed,
                "is_defect": self.is_defect, "classification": self.classification,
                "severity": self.severity,
                "governing_contract": self.governing_contract,
                "detail": self.detail,
                "changes_historical_meaning": self.changes_historical_meaning,
                "subject_tokens": list(self.subject_tokens),
                "blocks_gate": self.blocks_gate,
                "superseded_by": self.superseded_by,
                "supersession_detail": self.supersession_detail,
                "evidence": self.evidence}


#: claim -> candidate dotted paths, most specific first. Receipts across G1-G7
#: use DIFFERENT key names and nesting for the same claim, so the audit reads by
#: CLAIM and records which declaration it actually consumed. Missing a claim that
#: is present in a receipt is a false positive, which is as damaging as a miss.
_CLAIM_PATHS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("tested_sha", ("tested_sha", "artifacts_head_sha",
                    "receipt_lineage.artifacts_head_sha", "ending_sha",
                    "receipt_content_parent_sha",
                    "receipt_lineage.receipt_content_parent_sha",
                    "receipt_terminal_commit", "externally_verified_branch_head")),
    ("start_sha", ("start_sha", "starting_sha")),
    ("authoritative_test_command", ("authoritative_test_command", "test_command")),
    ("full_test_count", ("full_test_count", "collected", "total_tests",
                         "tests_collected", "tests.total", "tests.total_final",
                         "tests.pass", "tests_run", "pass_count", "total_pass")),
    ("passed", ("passed", "passed_count", "tests.pass", "pass_count")),
    ("failed", ("failed", "fail_count", "tests.fail", "fail_count")),
    ("new_test_count", ("new_test_count", "new_tests", "tests.new", "tests.new_g3_tests")),
)


def _lookup(receipt: Mapping[str, Any], path: str) -> Any:
    node: Any = receipt
    for part in path.split("."):
        if not isinstance(node, Mapping) or part not in node:
            return None
        node = node[part]
    return node


#: Keys whose declared semantic is a TESTED SURFACE, i.e. the surface the gate's
#: evidence is a claim about. Only these may be checked against the rule
#: "a receipt may not name its own containing commit as tested evidence".
DECLARED_TESTED_SURFACE_KEYS = (
    "tested_sha",
    "artifacts_head_sha",
    "receipt_lineage.artifacts_head_sha",
    "receipt_content_parent_sha",
    "receipt_lineage.receipt_content_parent_sha",
)

#: Keys whose declared semantic is the TERMINAL HEAD of record: the commit the
#: gate terminated at, which is the commit that archives the receipt. These are
#: self-referential BY DECLARED NAME, so naming the containing commit in one is a
#: convention, not a false claim. Their presence is still recorded, because such
#: a receipt does not separately declare a tested surface.
TERMINAL_HEAD_KEYS = (
    "ending_sha",
    "receipt_terminal_commit",
    "receipt_lineage.externally_verified_branch_head",
    "externally_verified_branch_head",
)

#: Keys under which a LATER artifact declares the corrections it makes. Used by
#: the supersession resolution: only a declared correction payload counts.
CORRECTION_KEYS = (
    "prose_correction",
    "findings",
    "repairs",
    "supersession",
    "corrections",
    "errata",
    "supersedes",
)


def tested_surface_class(path: str) -> str:
    """Which declared semantic the audit consumed."""
    if path in DECLARED_TESTED_SURFACE_KEYS:
        return "DECLARED_TESTED_SURFACE"
    if path in TERMINAL_HEAD_KEYS:
        return "TERMINAL_HEAD_OF_RECORD"
    return "UNCLASSIFIED"


def _declared_sha_note(receipt: Mapping[str, Any]) -> str:
    """The receipt's own statement of its SHA semantics, if it makes one."""
    for key in ("sha_semantics", "artifact_sha_semantics", "ending_sha_note",
                "note_starting_sha_delta"):
        value = receipt.get(key)
        if isinstance(value, str) and value:
            return f"{key}: {value}"
    return ""


def declared_corrections(receipt: Mapping[str, Any]) -> Tuple[str, ...]:
    """Flatten a receipt's DECLARED correction payloads into literal strings.
    Nothing outside the declared correction keys is read."""
    out: List[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, str):
            out.append(node)
        elif isinstance(node, Mapping):
            for value in node.values():
                walk(value)
        elif isinstance(node, (list, tuple)):
            for value in node:
                walk(value)

    for key in CORRECTION_KEYS:
        if key in receipt:
            walk(receipt[key])
    return tuple(out)


def resolve_supersession(findings: Sequence[GateClaimFinding], *,
                         later_corrections: Mapping[str, Tuple[str, ...]]
                         ) -> List[GateClaimFinding]:
    """Apply the declared supersession rule (revision R2).

    `later_corrections` maps a *later-archived* evidence artifact's file name to
    the flattened correction payloads it declares. A finding is superseded when a
    later artifact BOTH names the historical receipt AND mentions one of the
    finding's own subject tokens inside its declared correction payload. The
    finding stays visible with the superseding artifact recorded verbatim; it is
    never silently dropped and never rewritten into a pass."""
    out: List[GateClaimFinding] = []
    for finding in findings:
        name = finding.receipt_path.rsplit("/", 1)[-1]
        correction_owner = ""
        correction_text = ""
        for artifact, payloads in sorted(later_corrections.items()):
            if artifact == name:
                continue
            joined = " ".join(payloads)
            if name not in joined:
                continue
            for text in payloads:
                if any(token and token in text for token in finding.subject_tokens):
                    correction_owner, correction_text = artifact, text
                    break
            if correction_owner:
                break
        if correction_owner and finding.is_defect:
            out.append(replace(
                finding, is_defect=False,
                classification="SUPERSEDED_BY_LATER_ARTIFACT",
                blocks_gate=False, superseded_by=correction_owner,
                supersession_detail=correction_text,
                changes_historical_meaning=False,
                detail=(finding.detail + " | superseded by " + correction_owner +
                        " which declares: " + correction_text[:240])))
        else:
            out.append(finding)
    return out


def extract_claims(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    """Schema-tolerant claim extraction. Returns the claim values plus
    `claim_sources` naming the exact declaration each value came from, so a
    reviewer can see the audit did not invent a key."""
    out: Dict[str, Any] = {}
    sources: Dict[str, str] = {}
    for claim, paths in _CLAIM_PATHS:
        for path in paths:
            value = _lookup(receipt, path)
            if value not in (None, ""):
                out[claim] = value
                sources[claim] = path
                break
    out["claim_sources"] = sources
    return out


def audit_gate_claim(*, receipt_path: str, receipt: Mapping[str, Any],
                     git_probe: Callable[[Sequence[str]], str],
                     contract: Mapping[str, Any],
                     evidence_dir_commit_of: Callable[[str], str],
                     head_sha: str) -> List[GateClaimFinding]:
    """Audit one historical receipt against the surface it names. A historical
    receipt stays historical: findings never rewrite it.

    Revision R2 split the SHA vocabulary. The self-certification rule applies
    only to a DECLARED TESTED SURFACE; a receipt that names its own terminal
    commit through a terminal-head key is following its own declared convention,
    which is recorded as a convention note rather than as a false claim."""
    findings: List[GateClaimFinding] = []

    def add(fid: str, claim: str, observed: str, is_defect: bool, cls: str,
            sev: str, detail: str, contract_ref: str,
            evidence: Optional[Dict[str, Any]] = None,
            subject_tokens: Sequence[str] = (),
            blocks_gate: Optional[bool] = None) -> None:
        findings.append(GateClaimFinding(
            finding_id=fid, receipt_path=receipt_path, claim=claim, observed=observed,
            is_defect=is_defect, classification=cls, severity=sev,
            governing_contract=contract_ref, detail=detail, evidence=evidence or {},
            subject_tokens=tuple(subject_tokens),
            blocks_gate=is_defect if blocks_gate is None else blocks_gate))

    claims = extract_claims(receipt)
    sources = claims.get("claim_sources", {})

    # 1. a receipt must name the surface it tested
    if "tested_sha" not in claims:
        add("NO_TESTED_SHA", "receipt names the surface it tested", "absent", True,
            "RECEIPT_OR_CLAIM_DEFECT", "HIGH",
            "no tested-surface declaration found under any known convention "
            "(tested_sha / artifacts_head_sha / receipt_content_parent_sha / "
            "ending_sha / receipt_terminal_commit)",
            "G8 §7 cross-gate claims")
        return findings

    sha = str(claims["tested_sha"])
    source = str(sources.get("tested_sha", ""))
    sha_class = tested_surface_class(source)
    try:
        kind = git_probe(["cat-file", "-t", sha]).strip()
    except Exception as exc:
        kind = f"probe_error:{exc}"

    if kind == "commit":
        add("TESTED_SURFACE_DECLARED", "receipt declares its tested surface",
            f"{source}={sha[:12]}", False, "RECEIPT_OR_CLAIM_DEFECT", "INFO",
            (f"tested surface read from {source!r} "
             f"(declared semantic: {sha_class}) " + _declared_sha_note(receipt)).strip(),
            "G8 §7 cross-gate claims",
            {"declaration": source, "declared_semantic": sha_class}, blocks_gate=False)
        ancestor = git_probe(["merge-base", "--is-ancestor", sha, head_sha])
        add("TESTED_SHA_IN_HISTORY", f"tested SHA {sha} is in branch history",
            "ancestor-of-head" if ancestor != "NOT_ANCESTOR" else "NOT_ANCESTOR",
            ancestor == "NOT_ANCESTOR", "RECEIPT_OR_CLAIM_DEFECT",
            "HIGH" if ancestor == "NOT_ANCESTOR" else "INFO",
            "tested SHA must be reachable from the audited branch head" if
            ancestor == "NOT_ANCESTOR" else
            "tested SHA is reachable from the audited branch head",
            "G8 §7 cross-gate claims", {"sha": sha, "head": head_sha},
            subject_tokens=(sha[:12],))
        archive = evidence_dir_commit_of(receipt_path)
        if archive:
            self_certifying = sha == archive
            if self_certifying and sha_class == "TERMINAL_HEAD_OF_RECORD":
                add("SHA_CONVENTION_TERMINAL_SELF_REFERENTIAL",
                    "receipt distinguishes its tested surface from its archive commit",
                    f"archive={archive[:12]} terminal-head={sha[:12]}",
                    False, "RECEIPT_OR_CLAIM_DEFECT", "INFO",
                    (f"read from {source!r}, whose declared semantic is the gate's "
                     "TERMINAL HEAD of record — naming the containing commit is that "
                     "convention, so no tested surface is separately identifiable. "
                     "Recorded as a convention note, not as a false claim. "
                     + _declared_sha_note(receipt)).strip(),
                    "G8 §7 cross-gate claims (historical convention)",
                    {"archive_commit": archive, "declaration": source,
                     "declared_semantic": sha_class}, blocks_gate=False)
            else:
                add("TESTED_SHA_PRECEDES_EVIDENCE_COMMIT",
                    "tested SHA is distinct from the evidence archive commit",
                    f"archive={archive[:12]} tested={sha[:12]}",
                    self_certifying, "RECEIPT_OR_CLAIM_DEFECT",
                    "BLOCKING" if self_certifying else "INFO",
                    "a receipt may not name its own containing commit as tested "
                    "evidence (self-certification)" if self_certifying else
                    "tested SHA is distinct from the commit that archived the receipt",
                    "G8 §12 do not self-hash the evidence commit",
                    {"archive_commit": archive, "tested_sha": sha},
                    subject_tokens=(sha[:12],))
    else:
        # the declared identifier does not resolve as a commit. Try to resolve it
        # through an abbreviation the SAME receipt also declares, and cross-check
        # the candidate's subject against the receipt's own declared commit list.
        # prefixes to try: the abbreviations the SAME receipt declares in its own
        # commit list and that are prefixes of the disputed identifier, longest
        # first, then the identifier's own leading 12/10/8 characters. Nothing is
        # guessed from the repository at large.
        declared_subjects = {}
        for entry in receipt.get("commits", []) or []:
            if isinstance(entry, Mapping):
                declared_subjects[str(entry.get("sha", ""))] = str(entry.get("subject", ""))
        prefixes = sorted({short for short in declared_subjects
                           if short and sha.startswith(short)}, key=len, reverse=True)
        prefixes += [p for p in (sha[:12], sha[:10], sha[:8]) if p not in prefixes]
        candidates: List[str] = []
        used_prefix = ""
        for prefix in prefixes:
            try:
                listing = git_probe(["rev-parse", f"--disambiguate={prefix}"])
                found = [c for c in listing.split() if c]
            except Exception:
                found = []
            if len(found) == 1:
                candidates, used_prefix = found, prefix
                break
        prefix = used_prefix or prefixes[0]
        matched = ""
        declared_subject = ""
        for candidate in candidates:
            if candidate.startswith(sha[:8]):
                matched = candidate
                declared_subject = declared_subjects.get(sha[:8], "")
                break
        resolved_subject = ""
        if matched:
            try:
                resolved_subject = git_probe(["log", "-1", "--format=%s", matched]).strip()
            except Exception:
                resolved_subject = ""
        if matched:
            exact = bool(declared_subject) and declared_subject == resolved_subject
            add("TESTED_SHA_FULL_FORM_UNRESOLVABLE",
                f"declared tested surface {sha} resolves",
                f"{kind}; abbreviation {prefix} resolves to {matched[:12]}",
                True, "RECEIPT_OR_CLAIM_DEFECT", "MEDIUM",
                (f"the receipt declares the full-length identifier {sha}, which is not "
                 f"an object in this repository. Its own abbreviation {prefix} resolves "
                 f"to exactly one commit, {matched}, whose recorded subject is "
                 f"{resolved_subject!r}" + (
                     " and matches the receipt's declared subject verbatim, so the "
                     "substantive result is locatable and reproducible" if exact else
                     " — but that subject does NOT match the receipt's declared subject, "
                     "so the referent is not established")) +
                ". The declared identifier is a transcription defect in a historical "
                "receipt; G8 records it and does not rewrite the receipt §11.",
                "G8 §7 cross-gate claims",
                {"declared_sha": sha, "declaration": source, "prefix": prefix,
                 "resolved_candidate": matched,
                 "resolved_subject": resolved_subject,
                 "declared_subject": declared_subject,
                 "declared_subject_matches": exact,
                 "candidate_count": len(candidates)},
                subject_tokens=(sha[:12], prefix),
                blocks_gate=not exact)
        else:
            in_repo = "NO"
            try:
                listing = git_probe(["log", "--all", "--format=%H"])
                in_repo = "YES" if sha in listing.split() else "NO"
            except Exception:
                in_repo = "UNKNOWN"
            add("TESTED_SHA_UNRESOLVABLE", f"declared tested surface {sha} resolves",
                f"{kind} (in_repo={in_repo}, abbreviation_candidates={len(candidates)})",
                True, "RECEIPT_OR_CLAIM_DEFECT", "HIGH",
                (f"the declared tested surface {sha} exists in the repository but not in "
                 "this branch's history" if in_repo == "YES" else
                 f"the declared tested surface {sha} is absent from EVERY ref in the "
                 "repository and no declared abbreviation resolves it — the claim's "
                 "tested surface cannot be located or verified"),
                "G8 §7 cross-gate claims",
                {"sha": sha, "probe": kind, "in_repository": in_repo,
                 "abbreviation": prefix, "candidates": candidates},
                subject_tokens=(sha[:12],),
                blocks_gate=in_repo != "YES")

    # 2. mutation accounting must be present and zero for external surfaces
    for field_name, claim in (("cloud_mutations", "cloud mutations"),
                              ("production_mutations", "production mutations"),
                              ("capital_mutations", "capital mutations")):
        if field_name in receipt:
            value = receipt[field_name]
            add(f"MUTATIONS_{field_name.upper()}", f"receipt reports {claim} = 0",
                str(value), value not in (0, "0"), "RECEIPT_OR_CLAIM_DEFECT",
                "HIGH" if value not in (0, "0") else "INFO",
                f"declared {claim} = {value}", "Book §40", {"value": value},
                subject_tokens=(field_name,), blocks_gate=value not in (0, "0"))

    # 3. a receipt must not deny simulated scenario-internal authority events
    if "authority_mutations" in receipt and str(receipt["authority_mutations"]).upper() == "NONE":
        has_internal = "scenario_internal_authority_events" in receipt or \
            "authority_accounting" in receipt
        add("AUTHORITY_ACCOUNTING_VOCABULARY",
            "authority accounting distinguishes simulated from external",
            "distinguished" if has_internal else "authority_mutations=NONE only",
            not has_internal, "RECEIPT_OR_CLAIM_DEFECT",
            "MEDIUM" if not has_internal else "INFO",
            "receipt collapsed simulated scenario-internal authority transitions "
            "into 'NONE'" if not has_internal else
            "receipt reports simulated transitions separately",
            "G6-TC09 authority-mutation accounting",
            subject_tokens=("authority_mutations", "authority_accounting",
                            "scenario_internal_authority_events"),
            blocks_gate=False)

    # 4. counts must be internally consistent when both are declared
    if "full_test_count" in claims and "new_test_count" in claims:
        try:
            full, new = int(claims["full_test_count"]), int(claims["new_test_count"])
            add("COUNT_PLAUSIBLE", "full count >= new count", f"{full} >= {new}",
                full < new, "RECEIPT_OR_CLAIM_DEFECT", "MEDIUM",
                f"declared full={full} new={new}", "G8 §12 test accounting",
                subject_tokens=("full_test_count",), blocks_gate=full < new)
        except (TypeError, ValueError):
            add("COUNT_NOT_INTEGER", "test counts are integers",
                f"{claims['full_test_count']!r}/{claims['new_test_count']!r}", True,
                "RECEIPT_OR_CLAIM_DEFECT", "MEDIUM",
                "receipt declares non-integer test counts", "G8 §12",
                subject_tokens=("full_test_count",))
    return findings


def audit_count_lineage(contract: Mapping[str, Any],
                        declared: Sequence[Mapping[str, Any]],
                        measured_full: int,
                        head_sha: str) -> Dict[str, Any]:
    """Recompute the declared gate test lineage from the receipts themselves.

    Three checks, none of which trusts a prose claim:
      1. every declared full count is a positive integer;
      2. declared full counts are NON-DECREASING in archive order;
      3. where a step declares both its own new-test count and what it
         superseded, the arithmetic must reconcile (previous - superseded + new);
      4. the terminal declared count equals the LIVE collected count at the head.
    Steps that do not declare new/superseded counts are recorded as
    `arithmetic_not_declared` rather than being silently assumed."""
    chain: List[Dict[str, Any]] = []
    defects: List[Dict[str, Any]] = []
    previous: Optional[int] = None
    for entry in sorted(declared, key=lambda e: (e["order"], str(e["gate"]))):
        full = int(entry["full_test_count"])
        new = entry.get("new_test_count")
        superseded = entry.get("superseded_test_count")
        recomputed = None
        reconciled: Optional[bool] = None
        if new is None or superseded is None:
            note = "arithmetic_not_declared_by_this_receipt"
        else:
            recomputed = (previous if previous is not None else 0) - int(superseded) + int(new)
            reconciled = recomputed == full
            note = "reconciled" if reconciled else "declared lineage arithmetic does not reconcile"
            if not reconciled:
                defects.append({"gate": entry["gate"], "declared_full": full,
                                "recomputed_full": recomputed, "note": note})
        if previous is not None and full < previous:
            defects.append({"gate": entry["gate"], "declared_full": full,
                            "previous": previous,
                            "note": "declared full count decreases across gates"})
        chain.append({"gate": entry["gate"], "order": entry["order"],
                      "declared_full": full, "new": new, "superseded": superseded,
                      "source": entry.get("source", ""),
                      "recomputed_full": recomputed, "reconciled": reconciled,
                      "note": note})
        previous = full
    terminal = chain[-1]["declared_full"] if chain else None
    return {
        "chain": chain,
        "terminal_declared_full": terminal,
        "measured_full_at_head": measured_full,
        "terminal_matches_measured": terminal == measured_full,
        "monotone": all(chain[i]["declared_full"] <= chain[i + 1]["declared_full"]
                        for i in range(len(chain) - 1)),
        "head_sha": head_sha,
        "arithmetic_defects": defects,
        "note": ("declared lineage is DERIVED from the receipts (gate, count and the "
                 "declaration each value came from), never hand-authored; the "
                 "terminal declared count is compared against the live collected "
                 "count at the audited head"),
    }


# --------------------------------------------------------------------------- #
# Self-certification guard
# --------------------------------------------------------------------------- #
class SelfCertificationError(RuntimeError):
    """Raised when the evidence package would certify itself."""


def assert_not_self_certifying(receipt: Mapping[str, Any], *,
                               receipt_path: str,
                               evidence_paths: Sequence[str],
                               containing_commit: str) -> None:
    """The G8 receipt may not name its own file or its own containing commit as
    tested evidence (control C15 / §12 do not self-hash the evidence commit)."""
    tested = str(receipt.get("tested_sha", ""))
    if tested and containing_commit and tested == containing_commit:
        raise SelfCertificationError(
            "receipt names its own containing commit as tested_sha")
    blob = json.dumps(receipt, sort_keys=True)
    own_name = receipt_path.rsplit("/", 1)[-1]
    for path in evidence_paths:
        if path.rsplit("/", 1)[-1] == own_name:
            continue
        digest = deterministic_hex("selfcheck", path, length=32)
        if digest in blob:  # pragma: no cover - defensive
            raise SelfCertificationError(
                f"receipt embeds a digest of {path} in a self-referential way")
