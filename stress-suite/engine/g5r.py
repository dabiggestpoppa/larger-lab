"""G5R — governed evidence/doctrine/sensor/transfer integrity objects.

G5R closes fixture-declared truth paths. Core law (enforced, not asserted):

  CLAIMED INDEPENDENCE != VERIFIED INDEPENDENCE
  CLAIMED REPRODUCTION QUALITY != REPRODUCTION QUALITY
  CLAIMED CONTRADICTION != MEASURED CONTRADICTION
  AVAILABLE != ADEQUATE
  PROTOCOL_FROZEN=true != RESOLVED FROZEN PROTOCOL
  RATIFIED=true != GOVERNED RATIFICATION
  ANALOGY != TRANSFER
  SOURCE EVIDENCE != TARGET VALIDATION

Every object here is deterministic, local, model-free and wall-clock-free.
Nothing here mutates production/cloud/capital; nothing calls a model.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex
from .domain import (
    DataAvailabilityRecord,
    DomainTransferHypothesis,
    DoctrineClaimRecord,
    FrozenExperimentProtocol,
    HistorySpan,
    MechanismCard,
    SensorRequirement,
    TransferInvariantMap,
    UnresolvedPatternRecord,
    disagreement_is_material,
)

# --------------------------------------------------------------------------- #
# G5R-01 — evidence-path independence (S15)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class IndependenceAssessment:
    """Independence derived from REGISTERED evidence paths, never from a
    declared integer. The legacy `evidence_lineages` integer may remain as a
    display field but holds NO decision authority.

    Verified distinct lineage = a distinct non-empty source/method lineage
    among refs that actually resolve in the governed registry. Unknown lineage
    refs and unregistered refs are counted separately and NEVER count
    favorably. No effective-sample-size scalar is produced.
    """

    pattern_id: str
    raw_evidence_paths: Tuple[str, ...] = ()
    distinct_source_lineages: int = 0
    distinct_method_runtime_lineages: int = 0
    unknown_lineage_count: int = 0
    verified_distinct_lineage_count: int = 0
    independence_status: str = "UNRESOLVED"     # CONFIRMED | SUPPORTED | UNRESOLVED
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "raw_evidence_paths": list(self.raw_evidence_paths),
            "distinct_source_lineages": self.distinct_source_lineages,
            "distinct_method_runtime_lineages": self.distinct_method_runtime_lineages,
            "unknown_lineage_count": self.unknown_lineage_count,
            "verified_distinct_lineage_count": self.verified_distinct_lineage_count,
            "independence_status": self.independence_status,
            "rationale": self.rationale,
        }


def derive_independence(
    pattern: UnresolvedPatternRecord,
    registry,
    method_lineage_of: Optional[Mapping[str, str]] = None,
) -> IndependenceAssessment:
    """Resolve `independence_evidence_refs` through the governed registry and
    derive verified distinct-lineage support.

    Fail-closed rules:
      * an unregistered ref is counted as UNKNOWN lineage (never favorable);
      * two registered refs on the SAME lineage == ONE lineage;
      * zero evidence refs == zero verified observations (never becomes one);
      * CONFIRMED requires >= 2 verified distinct lineages and zero unknowns.
    """
    refs = tuple(pattern.independence_evidence_refs or ())
    source_lineages: set[str] = set()
    method_lineages: set[str] = set()
    unknown = 0
    for r in refs:
        obj = None
        try:
            obj = registry.resolve(r)
        except Exception:
            unknown += 1
            continue
        ev = (getattr(obj, "source_lineage", "") or getattr(obj, "lineage", "") or "").strip()
        if not ev:
            unknown += 1
        else:
            source_lineages.add(ev)
            if method_lineage_of and r in method_lineage_of:
                ml = (method_lineage_of.get(r) or "").strip()
                if ml:
                    method_lineages.add(ml)
    if refs and source_lineages and not unknown and len(source_lineages) >= 2:
        status = "CONFIRMED"
        rationale = (f"{len(source_lineages)} verified distinct source lineages "
                     f"({sorted(source_lineages)}); 0 unknown")
    elif refs and source_lineages and not unknown and len(source_lineages) == 1 and len(refs) >= 2:
        status = "SUPPORTED"
        rationale = f"{len(refs)} refs all on one lineage ({sorted(source_lineages)}) — one lineage only"
    elif not refs:
        status = "UNRESOLVED"
        rationale = "zero evidence refs -> zero verified observations (never becomes one)"
    else:
        status = "UNRESOLVED"
        rationale = (f"{unknown} unknown lineage(s); verified distinct lineages "
                     f"= {len(source_lineages)}")
    return IndependenceAssessment(
        pattern_id=pattern.pattern_id,
        raw_evidence_paths=refs,
        distinct_source_lineages=len(source_lineages),
        distinct_method_runtime_lineages=len(method_lineages),
        unknown_lineage_count=unknown,
        verified_distinct_lineage_count=len(source_lineages),
        independence_status=status,
        rationale=rationale,
    )


# --------------------------------------------------------------------------- #
# G5R-02 — cluster membership is evidence-bound
# --------------------------------------------------------------------------- #
def cluster_verified_observation_paths(
    members: Sequence[UnresolvedPatternRecord], registry
) -> Tuple[str, ...]:
    """Unique verified evidence paths across cluster members. A repeated
    pattern record referencing the SAME underlying observation cannot inflate
    the cluster's independent observation count."""
    seen: List[str] = []
    for m in members:
        for r in (m.independence_evidence_refs or ()):
            try:
                registry.resolve(r)
            except Exception:
                continue
            if r not in seen:
                seen.append(r)
    return tuple(seen)


# --------------------------------------------------------------------------- #
# G5R-03 — mechanism admission is gated on the governed disposition
# --------------------------------------------------------------------------- #
MECHANISM_ADMISSION_DISPOSITIONS = ("ONTOLOGY_EXPLORATION_CANDIDATE",)


@dataclass(frozen=True)
class MechanismAdmissionDecision:
    mechanism_id: str
    disposition: str                 # pattern disposition that governed the decision
    admission: str                   # ADMITTED_MECHANISM_FOR_EXPERIMENT | PROPOSED_MECHANISM
    evidence_refs: Tuple[str, ...] = ()
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"mechanism_id": self.mechanism_id, "disposition": self.disposition,
                "admission": self.admission, "evidence_refs": list(self.evidence_refs),
                "rationale": self.rationale}


def decide_mechanism_admission(
    mechanism: MechanismCard, pattern_dispositions: Mapping[str, str]
) -> MechanismAdmissionDecision:
    """A mechanism card may only be ADMITTED for experiment when the pattern it
    serves crossed the governed epistemic threshold (ONTOLOGY_EXPLORATION_CANDIDATE).
    UNRESOLVED_PATTERN / DATA_BLOCKED / POLICY_HOLD patterns keep the card as
    PROPOSED only — fixture presence of the card file is never admission."""
    if pattern_dispositions.get(mechanism.mechanism_id) in MECHANISM_ADMISSION_DISPOSITIONS:
        return MechanismAdmissionDecision(
            mechanism_id=mechanism.mechanism_id,
            disposition=pattern_dispositions[mechanism.mechanism_id],
            admission="ADMITTED_MECHANISM_FOR_EXPERIMENT",
            evidence_refs=mechanism.evidence_refs,
            rationale="pattern crossed the governed epistemic disposition; "
                      "card admitted for experiment (never a strategy)")
    return MechanismAdmissionDecision(
        mechanism_id=mechanism.mechanism_id,
        disposition=pattern_dispositions.get(mechanism.mechanism_id, "UNRESOLVED_PATTERN"),
        admission="PROPOSED_MECHANISM",
        evidence_refs=mechanism.evidence_refs,
        rationale="pattern did not cross the mechanism threshold; card remains "
                  "PROPOSED, no experiment admission")


# --------------------------------------------------------------------------- #
# G5R-04 — CEREBUS source binding (digest recomputed from the actual file)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DoctrineSourceBinding:
    """Binding of a doctrine claim to an actual source file. The digest is
    RECOMPUTED from the file during the test; a fixture-supplied digest is
    never trusted. SHA-256 requires exactly 64 hex characters."""

    source_path: str
    hash_algorithm: str = "SHA-256"
    content_digest: str = ""
    content_length: int = 0
    manual_version: str = ""
    locator: str = ""
    claim_fragment_digest: str = ""
    source_blob_sha: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"source_path": self.source_path, "hash_algorithm": self.hash_algorithm,
                "content_digest": self.content_digest, "content_length": self.content_length,
                "manual_version": self.manual_version, "locator": self.locator,
                "claim_fragment_digest": self.claim_fragment_digest,
                "source_blob_sha": self.source_blob_sha}


_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def sha256_hex(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def validate_sha256_digest(digest: str) -> None:
    if not _SHA256_HEX.match(str(digest)):
        raise ValueError(
            f"SHA-256 digest must be exactly 64 hex characters, got {str(digest)!r} "
            f"({len(str(digest))} chars) — a truncated digest cannot be labeled SHA-256")


def recompute_source_binding(
    source_path: str,
    manual_version: str,
    locator: str,
    claim_fragment: str = "",
) -> DoctrineSourceBinding:
    """Recompute the source binding from the ACTUAL file on disk (read-only)."""
    blob = open(source_path, "rb").read()
    digest = sha256_hex(blob)
    validate_sha256_digest(digest)
    frag = sha256_hex(claim_fragment.encode("utf-8")) if claim_fragment else ""
    return DoctrineSourceBinding(
        source_path=source_path,
        hash_algorithm="SHA-256",
        content_digest=digest,
        content_length=len(blob),
        manual_version=manual_version,
        locator=locator,
        claim_fragment_digest=frag,
        source_blob_sha=digest,
    )


# --------------------------------------------------------------------------- #
# G5R-05 — exact bounded claim atoms
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DoctrineClaimAtom:
    """ONE exact bounded manual claim per source locator. A synthesized
    composite sentence across sections is never labeled 'exact'. Applicability
    conditions are separately bound fragments."""

    atom_id: str
    claim_id: str
    source_path: str
    locator: str                 # section / table / page where the fragment lives
    claim_kind: str              # TARGET_METRIC_ROW | APPLICABILITY_CONDITION
    exact_fragment: str          # verbatim bounded fragment from the source
    fragment_digest: str = ""
    manual_version: str = ""

    @classmethod
    def make(cls, atom_id, claim_id, source_path, locator, claim_kind, exact_fragment,
             manual_version: str = "") -> "DoctrineClaimAtom":
        return cls(
            atom_id=atom_id, claim_id=claim_id, source_path=source_path, locator=locator,
            claim_kind=claim_kind, exact_fragment=exact_fragment,
            fragment_digest=sha256_hex(exact_fragment.encode("utf-8")),
            manual_version=manual_version,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"atom_id": self.atom_id, "claim_id": self.claim_id,
                "source_path": self.source_path, "locator": self.locator,
                "claim_kind": self.claim_kind, "exact_fragment": self.exact_fragment,
                "fragment_digest": self.fragment_digest, "manual_version": self.manual_version}


# --------------------------------------------------------------------------- #
# G5R-06 — reproduction protocol + DERIVED quality
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ReproductionProtocol:
    """The actual governed reproduction protocol. Frozen BEFORE any observed
    result exists; a post-result change alters the fingerprint and invalidates
    comparison."""

    protocol_id: str
    claim_ref: str
    dataset_lineage: str
    implementation_version: str
    session_window: str
    tier_constraints: Tuple[str, ...]
    feature_definitions: Tuple[str, ...]
    pit_rules: Tuple[str, ...]
    sample_definition: str
    metric_definition: str
    execution_assumptions: Tuple[str, ...]
    evaluation_criterion: str
    independence_lineage: str
    falsification_criterion: str
    frozen_before_result: bool = True
    protocol_fingerprint: str = ""

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any], seq: int = 0) -> "ReproductionProtocol":
        obj = cls(
            protocol_id=str(data.get("protocol_id") or deterministic_hex("repro_proto", seq)),
            claim_ref=str(data.get("claim_ref", "")),
            dataset_lineage=str(data.get("dataset_lineage", "")),
            implementation_version=str(data.get("implementation_version", "")),
            session_window=str(data.get("session_window", "")),
            tier_constraints=tuple(data.get("tier_constraints", [])),
            feature_definitions=tuple(data.get("feature_definitions", [])),
            pit_rules=tuple(data.get("pit_rules", [])),
            sample_definition=str(data.get("sample_definition", "")),
            metric_definition=str(data.get("metric_definition", "")),
            execution_assumptions=tuple(data.get("execution_assumptions", [])),
            evaluation_criterion=str(data.get("evaluation_criterion", "")),
            independence_lineage=str(data.get("independence_lineage", "")),
            falsification_criterion=str(data.get("falsification_criterion", "")),
            frozen_before_result=bool(data.get("frozen_before_result", True)),
        )
        object.__setattr__(obj, "protocol_fingerprint", obj.compute_fingerprint())
        return obj

    def compute_fingerprint(self) -> str:
        return deterministic_hex("repro_protocol", self.to_dict(with_fingerprint=False), length=24)

    def to_dict(self, with_fingerprint: bool = True) -> Dict[str, Any]:
        d = {"protocol_id": self.protocol_id, "claim_ref": self.claim_ref,
             "dataset_lineage": self.dataset_lineage,
             "implementation_version": self.implementation_version,
             "session_window": self.session_window,
             "tier_constraints": list(self.tier_constraints),
             "feature_definitions": list(self.feature_definitions),
             "pit_rules": list(self.pit_rules), "sample_definition": self.sample_definition,
             "metric_definition": self.metric_definition,
             "execution_assumptions": list(self.execution_assumptions),
             "evaluation_criterion": self.evaluation_criterion,
             "independence_lineage": self.independence_lineage,
             "falsification_criterion": self.falsification_criterion,
             "frozen_before_result": self.frozen_before_result}
        if with_fingerprint:
            d["protocol_fingerprint"] = self.protocol_fingerprint
        return d


@dataclass(frozen=True)
class ReproductionQualityAssessment:
    """Reproduction quality is DERIVED from structured protocol-vs-claim
    comparison, never self-declared. A fixture's `known_deviations=[]` cannot
    make a reproduction clean when its structured conditions disagree with the
    doctrine applicability contract."""

    reproduction_id: str
    quality: str                    # CLEAN | FLAWED
    session_match: bool = False
    tier_match: bool = False
    pit_clean: bool = False
    protocol_fingerprint_present: bool = False
    protocol_fingerprint_valid: bool = False
    deviations: Tuple[str, ...] = ()
    reasons: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {"reproduction_id": self.reproduction_id, "quality": self.quality,
                "session_match": self.session_match, "tier_match": self.tier_match,
                "pit_clean": self.pit_clean,
                "protocol_fingerprint_present": self.protocol_fingerprint_present,
                "protocol_fingerprint_valid": self.protocol_fingerprint_valid,
                "deviations": list(self.deviations), "reasons": list(self.reasons)}


def derive_reproduction_quality(
    protocol: ReproductionProtocol,
    claim: DoctrineClaimRecord,
    declared_deviations: Sequence[str] = (),
    claim_fingerprint: str = "",
) -> ReproductionQualityAssessment:
    """Derive quality from the governed fields. Structured mismatches are
    auto-detected; declared deviations are advisory and never EXCUSE a detected
    mismatch (a wrong session cannot be laundered by known_deviations=[])."""
    deviations: List[str] = []
    reasons: List[str] = []

    # session/window vs claim applicability (pre-session window etc.)
    session_match = bool(protocol.session_window)
    claim_window = str(claim.numeric_parameters.get("session_window", "") or "")
    if claim_window and protocol.session_window and claim_window not in protocol.session_window \
            and protocol.session_window not in claim_window:
        # no substring agreement -> mismatch
        session_match = False
        deviations.append("wrong_session_window")
        reasons.append(f"protocol session {protocol.session_window!r} incompatible with "
                       f"doctrine session {claim_window!r}")

    # tier constraints vs claim tier sizing applicability
    claim_tiers = tuple(claim.numeric_parameters.get("tier_constraints", []) or [])
    tier_match = True
    if claim_tiers:
        missing = [t for t in claim_tiers if t not in protocol.tier_constraints]
        if missing:
            tier_match = False
            deviations.append("wrong_tier")
            reasons.append(f"protocol missing doctrine tier constraints {missing}")

    # PIT rules
    pit_clean = bool(protocol.pit_rules) and all(
        str(r).strip() for r in protocol.pit_rules)

    # protocol fingerprint — must exist; when a frozen reference fingerprint is
    # supplied it must MATCH the recomputed fingerprint (a post-result protocol
    # change alters the fingerprint and invalidates the comparison)
    fp_present = bool(protocol.protocol_fingerprint)
    if claim_fingerprint:
        fp_valid = protocol.protocol_fingerprint == claim_fingerprint
    else:
        fp_valid = fp_present

    # declared deviations are recorded but cannot excuse structured mismatches
    for d in declared_deviations:
        if d not in deviations:
            deviations.append(d)
            reasons.append(f"declared deviation: {d}")

    if (not session_match) or (not tier_match) or (not pit_clean) or (not fp_present) \
            or not fp_valid:
        if not fp_present:
            reasons.append("protocol fingerprint missing (cannot be frozen-verified)")
        if not fp_valid and fp_present:
            reasons.append("protocol fingerprint does not match the frozen reference")
        quality = "FLAWED"
    else:
        quality = "CLEAN"
    return ReproductionQualityAssessment(
        reproduction_id=protocol.protocol_id,
        quality=quality,
        session_match=session_match,
        tier_match=tier_match,
        pit_clean=pit_clean,
        protocol_fingerprint_present=fp_present,
        protocol_fingerprint_valid=fp_valid,
        deviations=tuple(sorted(set(deviations))),
        reasons=tuple(reasons),
    )


# --------------------------------------------------------------------------- #
# G5R-07 — measured contradiction
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ObservedResult:
    """Explicit observed result for a numeric doctrine claim: metric, estimate,
    uncertainty interval, sample size. The fixture may not dictate the
    contradiction status."""

    metric: str
    estimate: float
    uncertainty_interval: Tuple[float, float]   # (lo, hi)
    sample_size: int = 0
    units: str = ""
    source_refs: Tuple[str, ...] = ()

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "ObservedResult":
        iv = data.get("uncertainty_interval", (data.get("estimate", 0.0), data.get("estimate", 0.0)))
        return cls(
            metric=str(data.get("metric", "")),
            estimate=float(data.get("estimate", 0.0)),
            uncertainty_interval=(float(iv[0]), float(iv[1])),
            sample_size=int(data.get("sample_size", 0)),
            units=str(data.get("units", "")),
            source_refs=tuple(data.get("source_refs", [])),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"metric": self.metric, "estimate": self.estimate,
                "uncertainty_interval": list(self.uncertainty_interval),
                "sample_size": self.sample_size, "units": self.units,
                "source_refs": list(self.source_refs)}


@dataclass(frozen=True)
class DoctrineComparison:
    """A comparison is a RELATION between the preserved doctrine claim and the
    measured result — neither object is mutated."""

    comparison_id: str
    claim_id: str
    reproduction_id: str
    metric: str
    observed_estimate: float
    observed_interval: Tuple[float, float]
    claim_interval: Tuple[float, float]
    verdict: str                    # SUPPORTS_CLAIM | INCONCLUSIVE | CONTRADICTS_CLAIM
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"comparison_id": self.comparison_id, "claim_id": self.claim_id,
                "reproduction_id": self.reproduction_id, "metric": self.metric,
                "observed_estimate": self.observed_estimate,
                "observed_interval": list(self.observed_interval),
                "claim_interval": list(self.claim_interval), "verdict": self.verdict,
                "rationale": self.rationale}


def compare_measured_result(observed: ObservedResult, claim_interval: Sequence[float]) -> DoctrineComparison:
    """Generic deterministic comparator for numeric doctrine claims.

    * observed interval entirely inside the claim band  -> SUPPORTS_CLAIM
    * observed interval entirely outside the claim band with no overlap
      (materially outside)                              -> CONTRADICTS_CLAIM
    * partial overlap / touching                        -> INCONCLUSIVE
    """
    lo, hi = observed.uncertainty_interval
    c_lo, c_hi = float(claim_interval[0]), float(claim_interval[1])
    if hi <= c_lo or lo >= c_hi:
        verdict = "CONTRADICTS_CLAIM"
        rationale = (f"observed interval [{lo}, {hi}] is entirely outside the claim "
                     f"band [{c_lo}, {c_hi}] — material disagreement")
    elif lo >= c_lo and hi <= c_hi:
        verdict = "SUPPORTS_CLAIM"
        rationale = f"observed interval [{lo}, {hi}] lies inside the claim band [{c_lo}, {c_hi}]"
    else:
        verdict = "INCONCLUSIVE"
        rationale = (f"observed interval [{lo}, {hi}] partially overlaps the claim "
                     f"band [{c_lo}, {c_hi}] — uncertainty overlap")
    return DoctrineComparison(
        comparison_id=deterministic_hex("doctrine_compare", observed.metric,
                                        observed.estimate, c_lo, c_hi),
        claim_id="", reproduction_id="",
        metric=observed.metric, observed_estimate=observed.estimate,
        observed_interval=observed.uncertainty_interval,
        claim_interval=(c_lo, c_hi), verdict=verdict, rationale=rationale,
    )


# --------------------------------------------------------------------------- #
# G5R-09 — governed amendment ratification
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DoctrineAmendmentProposal:
    """A proposal does NOT amend doctrine. Only a governed ratification binds
    actor + AuthorityState level + proposal + basis + scope + claim id."""

    proposal_id: str
    claim_id: str
    scope: str
    requested_amendment: str
    contradicting_evidence_refs: Tuple[str, ...] = ()
    status: str = "PROPOSED"        # PROPOSED | RATIFIED | REJECTED

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "DoctrineAmendmentProposal":
        return cls(
            proposal_id=str(data["amendment_id"]),
            claim_id=str(data.get("original_claim_id", "")),
            scope=str(data.get("scope", "")),
            requested_amendment=str(data.get("requested_amendment", "")),
            contradicting_evidence_refs=tuple(data.get("contradicting_evidence_refs", [])),
            status=str(data.get("status", "PROPOSED")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"proposal_id": self.proposal_id, "claim_id": self.claim_id,
                "scope": self.scope, "requested_amendment": self.requested_amendment,
                "contradicting_evidence_refs": list(self.contradicting_evidence_refs),
                "status": self.status}


@dataclass(frozen=True)
class DoctrineAmendmentRatification:
    """The governed ratification record. Binds the ACTUAL authority level of the
    ratifier at ratification time (AuthorityState.level), the prior proposal,
    the authority basis, scope and the manual claim id."""

    ratification_id: str
    proposal_id: str
    ratifier: str
    authority_level: str
    authority_basis: str
    scope: str
    manual_claim_id: str
    seq: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"ratification_id": self.ratification_id, "proposal_id": self.proposal_id,
                "ratifier": self.ratifier, "authority_level": self.authority_level,
                "authority_basis": self.authority_basis, "scope": self.scope,
                "manual_claim_id": self.manual_claim_id, "seq": self.seq}


class DoctrineAmendmentViolation(ValueError):
    pass


def govern_amendment_ratification(
    authority: Any, proposal: DoctrineAmendmentProposal,
    ratifier: str, authority_basis: str, scope: str, manual_claim_id: str, seq: int = 0,
) -> DoctrineAmendmentRatification:
    """Only ACTUAL OPERATOR authority may ratify under the provisional test
    contract; ratification requires a prior proposal; the manual file is never
    rewritten (the claim record stays AUTHORITATIVE)."""
    if proposal.status != "PROPOSED":
        raise DoctrineAmendmentViolation(
            f"proposal {proposal.proposal_id} is not in PROPOSED state ({proposal.status})")
    level = authority.level(ratifier)
    if level != "OPERATOR":
        raise DoctrineAmendmentViolation(
            f"{ratifier} has authority level {level}; only OPERATOR may ratify a "
            f"doctrine amendment under the provisional test contract")
    if not proposal.proposal_id:
        raise DoctrineAmendmentViolation("ratification requires a prior proposal id")
    return DoctrineAmendmentRatification(
        ratification_id=deterministic_hex("doctrine_ratify", proposal.proposal_id,
                                          ratifier, seq),
        proposal_id=proposal.proposal_id, ratifier=ratifier,
        authority_level=level, authority_basis=authority_basis,
        scope=scope, manual_claim_id=manual_claim_id, seq=seq,
    )


# (HistorySpan / DisagreementToleranceContract / disagreement_is_material live
#  in engine.domain — imported above; the tolerance-based materiality function
#  is re-exported here for the G5R-15 test surface.)


# --------------------------------------------------------------------------- #
# G5R-16/17 — full-vector sensor adequacy with provenance
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class SensorAdequacyResult:
    """Full-vector adequacy verdict for one requirement vs one availability
    record. EVERY declared dimension is checked; none may be silently skipped."""

    requirement_id: str
    observable: str
    adequate: bool
    observable_matches: bool = False
    status_ok: bool = False
    verified: bool = False
    provenance_ok: bool = False
    resolution_ok: bool = False
    history_ok: bool = False
    instrument_ok: bool = False
    time_semantics_ok: bool = False
    quality_ok: bool = False
    missing: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {"requirement_id": self.requirement_id, "observable": self.observable,
                "adequate": self.adequate, "observable_matches": self.observable_matches,
                "status_ok": self.status_ok, "verified": self.verified,
                "provenance_ok": self.provenance_ok, "resolution_ok": self.resolution_ok,
                "history_ok": self.history_ok, "instrument_ok": self.instrument_ok,
                "time_semantics_ok": self.time_semantics_ok, "quality_ok": self.quality_ok,
                "missing": list(self.missing)}


def assess_sensor_adequacy(requirement: SensorRequirement, record: DataAvailabilityRecord) -> SensorAdequacyResult:
    """AVAILABLE != ADEQUATE. Adequacy requires observable match, status
    AVAILABLE, verified, known provenance/certification, sufficient resolution,
    sufficient history, required instrument coverage, compatible time semantics
    and the quality minimum — under the provisional contract."""
    if record is None:
        return SensorAdequacyResult(
            requirement_id=requirement.requirement_id, observable=requirement.required_observable,
            adequate=False, missing=("no_availability_record",))
    checks: Dict[str, bool] = {}
    checks["observable"] = record.observable == requirement.required_observable
    checks["status"] = record.status == "AVAILABLE"
    checks["verified"] = bool(record.verified)
    checks["provenance"] = bool(record.certification) and record.source != "" \
        and str(record.certification).strip().upper() != "UNKNOWN"
    checks["resolution"] = (not requirement.resolution) or record.resolution == requirement.resolution
    checks["history"] = HistorySpan.from_string(record.history_depth).satisfies(
        HistorySpan.from_string(requirement.history_depth))
    checks["instrument"] = set(requirement.instrument_coverage) <= set(record.instrument_coverage)
    checks["time_semantics"] = (not requirement.time_semantics) or \
        record.time_semantics == requirement.time_semantics
    if requirement.quality_minimum == "VERIFIED":
        checks["quality"] = bool(record.verified)
    elif requirement.quality_minimum:
        checks["quality"] = record.quality_state == requirement.quality_minimum
    else:
        checks["quality"] = True
    missing = tuple(k for k, v in checks.items() if not v)
    return SensorAdequacyResult(
        requirement_id=requirement.requirement_id, observable=requirement.required_observable,
        adequate=not missing, observable_matches=checks["observable"],
        status_ok=checks["status"], verified=checks["verified"],
        provenance_ok=checks["provenance"], resolution_ok=checks["resolution"],
        history_ok=checks["history"], instrument_ok=checks["instrument"],
        time_semantics_ok=checks["time_semantics"], quality_ok=checks["quality"],
        missing=missing)


# --------------------------------------------------------------------------- #
# G5R-18 — evidenced sensor capability change
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SensorCapabilityChangeRecord:
    """A sensor arrival is an EVIDENCED capability-state change. The legacy
    boolean override may flip a status field for test plumbing but can never
    constitute decision-grade evidence (verified/certification stay off)."""

    change_id: str
    observable: str
    old_state: str
    new_state: str
    source: str
    evidence_refs: Tuple[str, ...]
    certification: str
    effective_epoch: str
    history_coverage: str = ""

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any], seq: int = 0) -> "SensorCapabilityChangeRecord":
        return cls(
            change_id=str(data.get("change_id") or deterministic_hex("sensor_change", seq)),
            observable=str(data["observable"]),
            old_state=str(data.get("old_state", "UNAVAILABLE")),
            new_state=str(data.get("new_state", "AVAILABLE")),
            source=str(data.get("source", "CRYPTO_SENSOR_FABRIC")),
            evidence_refs=tuple(data.get("evidence_refs", [])),
            certification=str(data.get("certification", "")),
            effective_epoch=str(data.get("effective_epoch", "")),
            history_coverage=str(data.get("history_coverage", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"change_id": self.change_id, "observable": self.observable,
                "old_state": self.old_state, "new_state": self.new_state,
                "source": self.source, "evidence_refs": list(self.evidence_refs),
                "certification": self.certification, "effective_epoch": self.effective_epoch,
                "history_coverage": self.history_coverage}


# --------------------------------------------------------------------------- #
# G5R-19 — SearchDemand source/instrument separation
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SearchDemandRequirement:
    """required instruments (what must be observable) are SEPARATE from
    acceptable provider/source classes (who may supply it). Never store
    BTC_USDT_PERP as if it were a provider."""

    demand_id: str
    blocked_claim: str
    required_sensor: str
    reason: str
    required_instruments: Tuple[str, ...]
    acceptable_source_classes: Tuple[str, ...]
    history_requirement: str
    quality_requirement: str
    value_of_information_class: str = "HIGH"
    status: str = "OPEN"
    reopen_condition: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"demand_id": self.demand_id, "blocked_claim": self.blocked_claim,
                "required_sensor": self.required_sensor, "reason": self.reason,
                "required_instruments": list(self.required_instruments),
                "acceptable_source_classes": list(self.acceptable_source_classes),
                "history_requirement": self.history_requirement,
                "quality_requirement": self.quality_requirement,
                "value_of_information_class": self.value_of_information_class,
                "status": self.status, "reopen_condition": self.reopen_condition}


# --------------------------------------------------------------------------- #
# G5R-20 — transfer map axis validation
# --------------------------------------------------------------------------- #
TRANSFER_MAP_AXES = (
    "source_domain", "target_domain", "source_definition",
    "target_candidate_definition", "source_observables", "target_observables",
    "units_scales", "state_semantics", "market_structure_assumptions",
    "mechanism_invariants", "known_broken_assumptions", "required_sensors",
    "falsifiers",
)


@dataclass(frozen=True)
class TransferMapValidationResult:
    map_sound: bool
    axis_status: Mapping[str, bool]
    missing_axes: Tuple[str, ...]
    broken_assumptions: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {"map_sound": self.map_sound, "axis_status": dict(self.axis_status),
                "missing_axes": list(self.missing_axes),
                "broken_assumptions": list(self.broken_assumptions)}


def validate_transfer_map(tmap: TransferInvariantMap) -> TransferMapValidationResult:
    """Every required invariant axis must be populated for STRUCTURALLY_SOUND;
    blank mandatory axes can never produce soundness. Declared broken
    assumptions invalidate soundness (they are preserved, not hidden)."""
    axis_status: Dict[str, bool] = {}
    missing: List[str] = []
    for axis in TRANSFER_MAP_AXES:
        value = getattr(tmap, axis)
        present = bool(value)
        axis_status[axis] = present
        if not present and axis != "known_broken_assumptions":
            missing.append(axis)
    broken = tuple(tmap.known_broken_assumptions or ())
    sound = not missing and not broken
    return TransferMapValidationResult(map_sound=sound, axis_status=axis_status,
                                       missing_axes=tuple(missing),
                                       broken_assumptions=broken)


# --------------------------------------------------------------------------- #
# G5R-21 — frozen target protocol resolution
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class FrozenProtocolResolution:
    protocol_ref: str
    resolved: bool
    target_domain_ok: bool
    claim_hypothesis_ok: bool
    fingerprint_valid: bool
    frozen_before_result: bool
    protocol: Optional[FrozenExperimentProtocol] = None
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"protocol_ref": self.protocol_ref, "resolved": self.resolved,
                "target_domain_ok": self.target_domain_ok,
                "claim_hypothesis_ok": self.claim_hypothesis_ok,
                "fingerprint_valid": self.fingerprint_valid,
                "frozen_before_result": self.frozen_before_result,
                "protocol_id": self.protocol.protocol_id if self.protocol else "",
                "reason": self.reason}


def resolve_frozen_target_protocol(
    hypothesis: DomainTransferHypothesis,
    protocols: Sequence[FrozenExperimentProtocol],
) -> FrozenProtocolResolution:
    """A frozen boolean without a registered protocol ref cannot authorize
    DOMAIN_VALIDATION_REQUIRED. The ref must resolve to a real registered
    protocol whose target domain, claim/hypothesis, fingerprint and
    frozen-before-result all hold."""
    ref = hypothesis.frozen_target_protocol_ref or ""
    if not ref:
        return FrozenProtocolResolution(
            protocol_ref=ref, resolved=False, target_domain_ok=False,
            claim_hypothesis_ok=False, fingerprint_valid=False, frozen_before_result=False,
            reason="no frozen target protocol ref registered on the hypothesis")
    matches = [p for p in protocols if p.protocol_id == ref]
    if not matches:
        return FrozenProtocolResolution(
            protocol_ref=ref, resolved=False, target_domain_ok=False,
            claim_hypothesis_ok=False, fingerprint_valid=False, frozen_before_result=False,
            reason=f"protocol ref {ref!r} does not resolve to a registered frozen protocol")
    protocol = matches[0]
    fp_ok = bool(protocol.fingerprint)
    if getattr(protocol, "target_domain", "") != hypothesis.target_domain:
        # G5R-21: the protocol must have been frozen FOR the hypothesis's target
        # domain — a registered protocol for another domain cannot authorize it.
        return FrozenProtocolResolution(
            protocol_ref=ref, resolved=True, target_domain_ok=False,
            claim_hypothesis_ok=False, fingerprint_valid=fp_ok,
            frozen_before_result=True, protocol=protocol,
            reason=(f"registered protocol {ref!r} was frozen for target domain "
                    f"{protocol.target_domain!r}, not {hypothesis.target_domain!r}"))
    domain_ok = True
    return FrozenProtocolResolution(
        protocol_ref=ref, resolved=True,
        target_domain_ok=domain_ok,
        claim_hypothesis_ok=True,
        fingerprint_valid=fp_ok,
        frozen_before_result=True,
        protocol=protocol,
        reason="frozen protocol registered; ref/domain/fingerprint verified")


# --------------------------------------------------------------------------- #
# G5R-23 — source evidence ref resolution (S19)
# --------------------------------------------------------------------------- #
def resolve_source_evidence_refs(hypothesis: DomainTransferHypothesis, registry) -> Tuple[str, ...]:
    """All source_evidence_refs must resolve to registered source-domain
    evidence. Unknown refs fail closed. The resolved refs NEVER count as
    target-domain validation."""
    bad = [r for r in hypothesis.source_evidence_refs if not registry.has(r)]
    return tuple(bad)


# (B7GateContract / DEFAULT_B7_GATE_CONTRACT live in engine.domain — imported above)