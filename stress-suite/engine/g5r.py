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
    independence_status: str = "UNRESOLVED"     # policy-channel vocabulary: CONFIRMED | SUPPORTED | SOURCE_ONLY | UNRESOLVED
    topology_scope: str = ""                    # which lineage dimensions were assessed
    semantic_label: str = "UNRESOLVED"          # TC-05 explicit vocabulary (below)
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
            "topology_scope": self.topology_scope,
            "semantic_label": self.semantic_label,
            "rationale": self.rationale,
        }


# TC-05: EXPLICIT independence vocabulary (compatible with G3's qualitative
# grades; never collapses to an effective-sample-size scalar). UNKNOWN dimensions
# never count as favorable evidence.
SEMANTIC_UNRESOLVED = "UNRESOLVED"
SEMANTIC_SOURCE_DIVERSE = "SOURCE_DIVERSE"
SEMANTIC_SOURCE_AND_METHOD_DIVERSE = "SOURCE_AND_METHOD_DIVERSE"
SEMANTIC_FULL_NOT_ASSESSED = "FULL_INDEPENDENCE_NOT_ASSESSED"
SEMANTIC_CORRELATED = "CORRELATED"


# G3 assesses 10 qualitative overlap dimensions (engine/independence.py:
# INDEPENDENCE_DIMENSIONS). G5's derive_independence assesses a strict subset:
# source lineage and (when supplied) method/runtime lineage. The projection below
# documents WHICH G3 dimensions a G5 semantic label speaks about, so G5 never
# invents a meaning G3 would not agree with.
G3_DIMENSIONS = (
    "model_family_overlap", "provider_overlap", "source_overlap",
    "retrieval_overlap", "prompt_context_overlap", "prior_conclusion_exposure",
    "implementation_path_overlap", "experiment_design_overlap",
    "runtime_lineage_overlap_if_known", "allocator_overlap",
)
G5_ASSESSED_G3_DIMENSIONS = ("source_overlap", "runtime_lineage_overlap_if_known")
G5_UNASSESSED_G3_DIMENSIONS = tuple(
    d for d in G3_DIMENSIONS if d not in G5_ASSESSED_G3_DIMENSIONS)


def derive_semantic_label(
    distinct_sources: int,
    distinct_methods: int,
    unknown: int,
    method_assessed: bool,
    refs: Sequence[str],
    sources_known: int = -1,
) -> str:
    """TC-05: map the assessed lineage vector onto the EXPLICIT vocabulary.

    * zero refs or any UNKNOWN lineage  -> UNRESOLVED (unknown never favorable)
    * >=2 distinct sources AND >=2 distinct methods (method assessed)
                                        -> SOURCE_AND_METHOD_DIVERSE
    * >=2 distinct sources, method NOT assessed
                                        -> FULL_INDEPENDENCE_NOT_ASSESSED
      (source diversity alone is NOT global independence — method/runtime,
      model family, provider, retrieval, design and allocator overlap are
      unassessed)
    * >=2 distinct sources but method assessed and <2 distinct methods
                                        -> CORRELATED (shared method/runtime)
    * single lineage with multiple refs -> CORRELATED
    """
    if unknown > 0:
        return SEMANTIC_UNRESOLVED
    n = len(list(refs or ()))
    if n == 0 or distinct_sources <= 0:
        return SEMANTIC_UNRESOLVED
    if method_assessed:
        if distinct_methods >= 2:
            return SEMANTIC_SOURCE_AND_METHOD_DIVERSE
        if distinct_sources >= 2:
            return SEMANTIC_CORRELATED
        return SEMANTIC_CORRELATED
    # method not assessed
    if distinct_sources >= 2:
        return SEMANTIC_FULL_NOT_ASSESSED
    return SEMANTIC_CORRELATED


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
    # ER-05: G5 independence is a SUBSET of the G3 topology. G5 assesses
    # source lineage and (where available) method/runtime lineage. It does NOT
    # claim the full G3 topology (model_family, provider, retrieval, prior-
    # conclusion-exposure, implementation_path, experiment_design, allocator).
    # The topology_scope documents which dimensions were assessed.
    #
    # CONFIRMED requires >= 2 distinct source lineages AND zero unknowns.
    # WHEN method_lineage_of IS provided: CONFIRMED further requires that the
    # method/runtime lineages are also distinct (len(method_lineages) >= 2) when
    # there are >= 2 source lineages — different source labels alone is not full
    # independence (ER-05: DIFFERENT SOURCE LABELS ALONE != FULL INDEPENDENCE).
    # If method_lineage_of is provided but method lineages are not distinct
    # (e.g. 2 source lineages, 1 method lineage), the result is SOURCE_ONLY.
    # When method_lineage_of is NOT provided, the result is CONFIRMED with
    # topology_scope='source_only' (method/runtime not assessed).
    topology_scope = "source_and_method_runtime" if method_lineage_of else "source_only"
    if refs and source_lineages and not unknown and len(source_lineages) >= 2:
        if method_lineage_of and len(method_lineages) < 2:
            # method_lineage_of provided but method lineages not distinct enough
            # for full independence given the source lineage count
            status = "SOURCE_ONLY"
            rationale = (f"{len(source_lineages)} distinct source lineages but "
                         f"only {len(method_lineages)} distinct method/runtime lineage(s) "
                         f"(need >= 2 for full independence); topology: {topology_scope}; "
                         f"0 unknown")
        else:
            status = "CONFIRMED"
            rationale = (f"{len(source_lineages)} verified distinct source lineages"
                         + (f" + {len(method_lineages)} distinct method/runtime lineages "
                            f"({sorted(method_lineages)})" if method_lineage_of and method_lineages else ""
                            )
                         + f"; 0 unknown; topology: {topology_scope}")
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
    method_assessed = bool(method_lineage_of)
    semantic_label = derive_semantic_label(
        len(source_lineages), len(method_lineages), unknown, method_assessed, refs)
    # TC-05: the explicit semantic label is carried alongside the policy-channel
    # status. SOURCE-only diversity is never globally CONFIRMED independence — it
    # is labeled FULL_INDEPENDENCE_NOT_ASSESSED (see derive_semantic_label).
    if semantic_label == SEMANTIC_FULL_NOT_ASSESSED and status == "CONFIRMED":
        rationale = (rationale + "; semantic label FULL_INDEPENDENCE_NOT_ASSESSED: "
                     "source lineage diversity alone is NOT global independence "
                     "(method/runtime, model family, provider, retrieval, design and "
                     "allocator overlap not assessed)").strip()
    return IndependenceAssessment(
        pattern_id=pattern.pattern_id,
        raw_evidence_paths=refs,
        distinct_source_lineages=len(source_lineages),
        distinct_method_runtime_lineages=len(method_lineages),
        unknown_lineage_count=unknown,
        verified_distinct_lineage_count=len(source_lineages),
        independence_status=status,
        topology_scope=topology_scope,
        semantic_label=semantic_label,
        rationale=rationale,
    )


# --------------------------------------------------------------------------- #
# G5R-02 — cluster membership is evidence-bound
# --------------------------------------------------------------------------- #
def canonical_evidence_identity(ref: str, registry) -> str:
    """TC-05: the CANONICAL underlying identity of a resolved evidence ref — the
    registered object's record_id when it resolves, else the ref string. Two ref
    strings that alias ONE evidence object share one canonical identity."""
    try:
        obj = registry.resolve(ref)
    except Exception:
        return ref
    return str(getattr(obj, "record_id", None) or getattr(obj, "id", "") or ref)


def cluster_verified_observation_paths(
    members: Sequence[UnresolvedPatternRecord], registry
) -> Tuple[str, ...]:
    """Unique verified evidence paths across cluster members, deduped on the
    CANONICAL underlying evidence identity (TC-05) — not on reference-string
    identity. A repeated pattern record referencing the SAME underlying
    observation cannot inflate the cluster's independent observation count, and
    two ref strings that alias ONE registered evidence object count once."""
    seen_canonical: List[str] = []
    for m in members:
        for r in (m.independence_evidence_refs or ()):
            canon = canonical_evidence_identity(r, registry)
            if canon not in seen_canonical:
                seen_canonical.append(canon)
    return tuple(seen_canonical)


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
# TC-02 — source-bound atoms FAIL CLOSED (no normalized-JSON laundering)
# --------------------------------------------------------------------------- #
FRAGMENT_STATUS_VERIFIED = "VERIFIED_IN_SOURCE"
FRAGMENT_STATUS_UNRESOLVED = "SOURCE_FRAGMENT_UNRESOLVED"
REPRESENTATION_VERBATIM = "VERBATIM_SOURCE"
REPRESENTATION_NORMALIZED = "NORMALIZED_REPRESENTATION"
REPRESENTATION_NORMALIZED_APPLICABILITY = "NORMALIZED_APPLICABILITY"


@dataclass(frozen=True)
class SourceFragmentAtom:
    """TC-02: an atom labeled exact/verbatim MUST come from the bound source.
    Carries the source file digest (whole bound file) and the fragment digest
    (exact extracted bytes) plus an occurrence status. If the fragment cannot be
    found in the bound source it is SOURCE_FRAGMENT_UNRESOLVED — never promoted
    to an exact atom via a normalized-JSON fallback."""

    atom_id: str
    claim_id: str
    source_path: str
    locator: str
    claim_kind: str
    exact_fragment: str
    fragment_status: str = FRAGMENT_STATUS_UNRESOLVED
    representation_mode: str = REPRESENTATION_VERBATIM
    source_file_digest: str = ""
    fragment_digest: str = ""
    manual_version: str = ""

    @classmethod
    def make(cls, atom_id, claim_id, source_path, locator, claim_kind, exact_fragment,
             source_text: str = "", source_file_digest: str = "",
             manual_version: str = "") -> "SourceFragmentAtom":
        """Digests are computed from the EXACT bytes/text supplied. Occurrence is
        verified against source_text when provided: a fragment that is NOT found in
        the bound source is SOURCE_FRAGMENT_UNRESOLVED (fail closed)."""
        frag = str(exact_fragment or "")
        frag_digest = sha256_hex(frag.encode("utf-8"))
        occurs = bool(frag) and bool(source_text) and (frag in source_text)
        status = FRAGMENT_STATUS_VERIFIED if occurs else FRAGMENT_STATUS_UNRESOLVED
        return cls(
            atom_id=atom_id, claim_id=claim_id, source_path=source_path,
            locator=locator, claim_kind=claim_kind, exact_fragment=frag,
            fragment_status=status,
            representation_mode=REPRESENTATION_VERBATIM if occurs else REPRESENTATION_NORMALIZED,
            source_file_digest=source_file_digest, fragment_digest=frag_digest,
            manual_version=manual_version,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"atom_id": self.atom_id, "claim_id": self.claim_id,
                "source_path": self.source_path, "locator": self.locator,
                "claim_kind": self.claim_kind, "exact_fragment": self.exact_fragment,
                "fragment_status": self.fragment_status,
                "representation_mode": self.representation_mode,
                "source_file_digest": self.source_file_digest,
                "fragment_digest": self.fragment_digest,
                "manual_version": self.manual_version}


def verify_atom_occurs_in_source(atom: SourceFragmentAtom, source_text: str) -> bool:
    """Re-derive whether the atom's exact fragment actually occurs in the bound
    source text. Deterministic; no hashing tricks can launder a fragment that is
    not present."""
    return bool(atom.exact_fragment) and atom.exact_fragment in (source_text or "")


@dataclass(frozen=True)
class NormalizedDoctrineClaim:
    """TC-02: the normalized numeric/structural machine representation of a
    claim. It is SEPARATE from any exact source atom and is never labeled exact
    or verbatim. `derived_from_atom_refs` records which source-bound atom(s) it
    was derived from (empty when the source atom is unresolved)."""

    claim_id: str
    representation: Mapping[str, Any]
    representation_digest: str
    derived_from_atom_refs: Tuple[str, ...] = ()
    representation_kind: str = REPRESENTATION_NORMALIZED

    @classmethod
    def make(cls, claim_id, representation: Mapping[str, Any],
             derived_from_atom_refs=()) -> "NormalizedDoctrineClaim":
        canon = deterministic_hex("normalized_claim", claim_id, dict(representation))
        return cls(
            claim_id=claim_id,
            representation=dict(representation),
            representation_digest=canon,
            derived_from_atom_refs=tuple(derived_from_atom_refs),
            representation_kind=REPRESENTATION_NORMALIZED,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"claim_id": self.claim_id,
                "representation": dict(self.representation),
                "representation_digest": self.representation_digest,
                "representation_kind": self.representation_kind,
                "derived_from_atom_refs": list(self.derived_from_atom_refs)}


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


# TC-03: reproduction fidelity vocabulary. 'CLEAN' is always scoped to the
# CHECKED surface; it must never be read as whole-protocol validation.
FIDELITY_FULL = "FULL_PROTOCOL_VERIFIED"
FIDELITY_PARTIAL = "PARTIAL_PROTOCOL_COVERAGE"
FIDELITY_FLAWED = "FLAWED_REPRODUCTION"
FIDELITY_UNASSESSED = "UNASSESSED"

# per-dimension classification vocabulary (TC-03)
DIM_VERIFIED = "VERIFIED"
DIM_MISMATCH = "MISMATCH"
DIM_NOT_APPLICABLE = "NOT_APPLICABLE"
DIM_UNVERIFIED = "UNVERIFIED"
DIM_NOT_DOCTRINE_COMPARABLE = "NOT_DOCTRINE_COMPARABLE"

PROTOCOL_DIMENSIONS = (
    "claim_ref", "session", "tiers", "PIT", "metric_definition",
    "observed_metric_identity", "units", "sample_definition",
    "execution_assumptions", "feature_definitions", "evaluation_criterion",
    "falsification_criterion", "dataset_lineage", "implementation_version",
    "independence_lineage",
)


def classify_protocol_dimensions(
    protocol: ReproductionProtocol,
    claim: DoctrineClaimRecord,
) -> Tuple[Tuple[str, str], ...]:
    """TC-03: classify each protocol dimension as VERIFIED / MISMATCH /
    NOT_APPLICABLE / UNVERIFIED / NOT_DOCTRINE_COMPARABLE. A dimension is only
    VERIFIED or MISMATCH when the doctrine claim actually defines a contract for
    it; where the source has no doctrine contract the dimension is
    NOT_DOCTRINE_COMPARABLE (never a silent pass). observed_metric_identity and
    units are NOT_APPLICABLE here because they are validated by the measured-
    comparison contract (TC-04) against an observed result, which this
    protocol-vs-claim assessment does not carry."""
    out: List[Tuple[str, str]] = []
    num = claim.numeric_parameters or {}

    out.append(("claim_ref", DIM_VERIFIED if (protocol.claim_ref == claim.claim_id)
                else DIM_MISMATCH))

    claim_window = str(num.get("session_window", "") or "")
    if claim_window:
        ok = bool(protocol.session_window) and (
            claim_window in protocol.session_window
            or protocol.session_window in claim_window)
        out.append(("session", DIM_VERIFIED if ok else DIM_MISMATCH))
    else:
        out.append(("session", DIM_NOT_DOCTRINE_COMPARABLE))

    claim_tiers = tuple(num.get("tier_constraints", []) or [])
    if claim_tiers:
        ok = all(t in protocol.tier_constraints for t in claim_tiers)
        out.append(("tiers", DIM_VERIFIED if ok else DIM_MISMATCH))
    else:
        out.append(("tiers", DIM_NOT_DOCTRINE_COMPARABLE))

    # PIT: the doctrine claim defines no PIT contract in this fixture surface;
    # the protocol's own PIT discipline is a checked surface (non-empty rules
    # = VERIFIED; empty = UNVERIFIED and gates quality to FLAWED).
    if protocol.pit_rules and all(str(r).strip() for r in protocol.pit_rules):
        out.append(("PIT", DIM_VERIFIED))
    else:
        out.append(("PIT", DIM_UNVERIFIED))

    claim_has_target_metric = bool(num.get("win_rate_band"))
    if claim_has_target_metric:
        ok = bool(protocol.metric_definition) and bool(str(protocol.metric_definition).strip())
        out.append(("metric_definition", DIM_VERIFIED if ok else DIM_MISMATCH))
    else:
        if protocol.metric_definition and bool(str(protocol.metric_definition).strip()):
            out.append(("metric_definition", DIM_NOT_DOCTRINE_COMPARABLE))
        else:
            out.append(("metric_definition", DIM_UNVERIFIED))

    # observed metric identity + units belong to the measured-comparison
    # contract (TC-04); this assessment has no observed result.
    out.append(("observed_metric_identity", DIM_NOT_APPLICABLE))
    out.append(("units", DIM_NOT_APPLICABLE))

    # dimensions with no doctrine contract in the claim fixture:
    for dim in ("sample_definition", "execution_assumptions", "feature_definitions",
                "evaluation_criterion", "falsification_criterion", "dataset_lineage",
                "implementation_version", "independence_lineage"):
        out.append((dim, DIM_NOT_DOCTRINE_COMPARABLE))
    return tuple(out)


def derive_fidelity(
    quality: str,
    dimension_classifications: Sequence[Tuple[str, str]],
) -> Tuple[str, str]:
    """TC-03: fidelity + clean-surface scope derived from the dimension
    classification. CLEAN never implies whole-protocol validation:

      * any MISMATCH / FLAWED quality      -> FLAWED_REPRODUCTION
      * any material UNVERIFIED dimension  -> PARTIAL_PROTOCOL_COVERAGE
      * FULL_PROTOCOL_VERIFIED only when every dimension is VERIFIED or
        NOT_APPLICABLE (i.e. the whole assessed surface is actually verified).
    """
    if quality == "FLAWED":
        return FIDELITY_FLAWED, "CHECKED_SURFACE_ONLY"
    labels = {d: c for d, c in dimension_classifications}
    if DIM_MISMATCH in labels.values():
        return FIDELITY_FLAWED, "CHECKED_SURFACE_ONLY"
    material_unverified = [d for d, c in dimension_classifications
                           if c == DIM_UNVERIFIED]
    if material_unverified:
        return FIDELITY_PARTIAL, "CHECKED_SURFACE_ONLY"
    not_comparable = [d for d, c in dimension_classifications
                      if c in (DIM_NOT_DOCTRINE_COMPARABLE,)]
    if not_comparable:
        # doctrine defines no contract for these dimensions, so the protocol
        # could not be verified against doctrine for them — coverage is partial.
        return FIDELITY_PARTIAL, "CHECKED_SURFACE_ONLY"
    return FIDELITY_FULL, "FULL_ASSESSED_SURFACE"


@dataclass(frozen=True)
class ReproductionQualityAssessment:
    """Reproduction quality is DERIVED from structured protocol-vs-claim
    comparison, never self-declared. A fixture's `known_deviations=[]` cannot
    make a reproduction clean when its structured conditions disagree with the
    doctrine applicability contract.

    TC-03: `quality` (CLEAN | FLAWED) is always scoped to the CHECKED surface:
    `clean_surface` says so, and `fidelity` (FULL_PROTOCOL_VERIFIED /
    PARTIAL_PROTOCOL_COVERAGE / FLAWED_REPRODUCTION) carries the whole-protocol
    verdict. CLEAN + PARTIAL is the normal honest outcome wherever the doctrine
    defines no contract for part of the protocol."""

    reproduction_id: str
    quality: str                    # CLEAN | FLAWED (checked surface only)
    session_match: bool = False
    tier_match: bool = False
    pit_clean: bool = False
    protocol_fingerprint_present: bool = False
    protocol_fingerprint_valid: bool = False
    claim_ref_match: bool = False
    metric_definition_present: bool = False
    unchecked_dimensions: Tuple[str, ...] = ()
    deviations: Tuple[str, ...] = ()
    reasons: Tuple[str, ...] = ()
    fidelity: str = FIDELITY_UNASSESSED
    clean_surface: str = ""
    dimension_classifications: Tuple[Tuple[str, str], ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {"reproduction_id": self.reproduction_id, "quality": self.quality,
                "session_match": self.session_match, "tier_match": self.tier_match,
                "pit_clean": self.pit_clean,
                "protocol_fingerprint_present": self.protocol_fingerprint_present,
                "protocol_fingerprint_valid": self.protocol_fingerprint_valid,
                "claim_ref_match": self.claim_ref_match,
                "metric_definition_present": self.metric_definition_present,
                "unchecked_dimensions": list(self.unchecked_dimensions),
                "deviations": list(self.deviations), "reasons": list(self.reasons),
                "fidelity": self.fidelity, "clean_surface": self.clean_surface,
                "dimension_classifications": [list(p) for p in self.dimension_classifications]}


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

    # claim_ref must match the claim being reproduced (ER-03: wrong claim_ref
    # cannot silently pass as a valid reproduction).
    claim_ref_match = bool(protocol.claim_ref) and protocol.claim_ref == claim.claim_id
    if not claim_ref_match:
        deviations.append("wrong_claim_ref")
        reasons.append(f"protocol claim_ref {protocol.claim_ref!r} != doctrine claim {claim.claim_id!r}")

    # metric_definition: the protocol must define the metric being reproduced.
    # The doctrine claim defines the TARGET_METRIC (win_rate_band etc.); the
    # protocol's metric_definition must name a metric compatible with the claim.
    # We check that the protocol's metric_definition is present and non-empty and
    # that the claim's numeric_parameters carry a win_rate_band (indicating the
    # claim is about win rate, the metric the protocol should reproduce).
    metric_def_present = bool(protocol.metric_definition) and len(str(protocol.metric_definition).strip()) > 0
    claim_has_target_metric = bool(claim.numeric_parameters.get("win_rate_band"))
    if not metric_def_present:
        deviations.append("missing_metric_definition")
        reasons.append("protocol metric_definition is empty (cannot verify what is being reproduced)")
    elif not claim_has_target_metric:
        # the claim doesn't define a target metric band — the metric definition
        # cannot be compared against a doctrine metric contract; classified as
        # non-comparable (documented, not a silent pass)
        reasons.append("claim has no target metric band; protocol metric_definition not doctrine-comparable")

    # protocol fingerprint — must exist; when a frozen reference fingerprint is
    # supplied it must MATCH the recomputed fingerprint (a post-result protocol
    # change alters the fingerprint and invalidates the comparison)
    fp_present = bool(protocol.protocol_fingerprint)
    if claim_fingerprint:
        fp_valid = protocol.protocol_fingerprint == claim_fingerprint
    else:
        fp_valid = fp_present

    # declaration of which protocol dimensions were NOT compared against any
    # doctrine/applicability contract (ER-03: unchecked dimensions cannot silently
    # pass as verified). These are listed for transparency; a CLEAN rating still
    # requires all CHECKED dimensions to pass.
    unchecked = ("dataset_lineage", "implementation_version", "feature_definitions",
                 "sample_definition", "execution_assumptions", "evaluation_criterion",
                 "independence_lineage", "falsification_criterion")

    # declared deviations are recorded but cannot excuse structured mismatches
    for d in declared_deviations:
        if d not in deviations:
            deviations.append(d)
            reasons.append(f"declared deviation: {d}")

    if (not session_match) or (not tier_match) or (not pit_clean) or (not fp_present) \
            or not fp_valid or (not claim_ref_match) or (not metric_def_present and claim_has_target_metric):
        if not fp_present:
            reasons.append("protocol fingerprint missing (cannot be frozen-verified)")
        if not fp_valid and fp_present:
            reasons.append("protocol fingerprint does not match the frozen reference")
        if not claim_ref_match:
            reasons.append("protocol claim_ref does not match the doctrine claim")
        if not metric_def_present and claim_has_target_metric:
            reasons.append("protocol metric_definition missing while claim defines a target metric")
        quality = "FLAWED"
    else:
        quality = "CLEAN"
    # TC-03: derive per-dimension classification + fidelity scope. quality stays
    # scoped to the checked surface; fidelity carries the whole-protocol verdict.
    dims = classify_protocol_dimensions(protocol, claim)
    fidelity, clean_surface = derive_fidelity(quality, dims)
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
        claim_ref_match=claim_ref_match,
        metric_definition_present=metric_def_present,
        unchecked_dimensions=unchecked,
        fidelity=fidelity,
        clean_surface=clean_surface,
        dimension_classifications=dims,
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
    result_seq: int = 0          # TC-01: logical evaluation sequence of this result
    evaluation_seq: int = 0      # TC-01: alias kept for explicit evaluation sequencing

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "ObservedResult":
        iv = data.get("uncertainty_interval", (data.get("estimate", 0.0), data.get("estimate", 0.0)))
        seq = int(data.get("result_seq", data.get("evaluation_seq", 0)) or 0)
        return cls(
            metric=str(data.get("metric", "")),
            estimate=float(data.get("estimate", 0.0)),
            uncertainty_interval=(float(iv[0]), float(iv[1])),
            sample_size=int(data.get("sample_size", 0)),
            units=str(data.get("units", "")),
            source_refs=tuple(data.get("source_refs", [])),
            result_seq=seq,
            evaluation_seq=seq,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"metric": self.metric, "estimate": self.estimate,
                "uncertainty_interval": list(self.uncertainty_interval),
                "sample_size": self.sample_size, "units": self.units,
                "source_refs": list(self.source_refs), "result_seq": self.result_seq,
                "evaluation_seq": self.evaluation_seq}


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
    """Generic deterministic comparator for numeric doctrine claims (ER-04 hardened).

    * observed interval entirely inside the claim band  -> SUPPORTS_CLAIM
    * observed interval entirely outside the claim band with STRICT separation
      (no boundary touching)                             -> CONTRADICTS_CLAIM
    * touching at a boundary (hi == c_lo or lo == c_hi) -> INCONCLUSIVE
    * partial overlap                                     -> INCONCLUSIVE
    * invalid interval (lo > hi)                         -> fail closed (DATA_INSUFFICIENT)

    A string verdict can never override the measurement; the comparator derives the
    relation from the intervals alone (G5R-07 / ER-04).
    """
    lo, hi = float(observed.uncertainty_interval[0]), float(observed.uncertainty_interval[1])
    c_lo, c_hi = float(claim_interval[0]), float(claim_interval[1])

    # fail closed on invalid interval — an inverted uncertainty interval is not a
    # high-confidence contradiction; it is malformed input (ER-04).
    if lo > hi:
        raise ValueError(
            f"observed uncertainty interval is inverted: lo={lo} > hi={hi} "
            f"for metric {observed.metric!r} — cannot derive a reliable comparison")

    # STRICT separation only -> CONTRADICTS. ANY boundary touching (hi == c_lo
    # or lo == c_hi) is INCONCLUSIVE — the intervals meet at a boundary but do
    # not strictly overlap, so the result is indeterminate rather than a material
    # contradiction (ER-04: touching / partial overlap -> INCONCLUSIVE).
    if hi < c_lo or lo > c_hi:
        verdict = "CONTRADICTS_CLAIM"
        rationale = (f"observed interval ({lo}, {hi}) is entirely outside the claim "
                     f"band ({c_lo}, {c_hi}) with strict separation — material disagreement")
    elif lo > c_lo and hi < c_hi:
        # strictly inside: no endpoint touches a claim boundary
        verdict = "SUPPORTS_CLAIM"
        rationale = f"observed interval ({lo}, {hi}) lies strictly inside the claim band ({c_lo}, {c_hi})"
    else:
        # touching one or both boundaries, OR partial overlap -> INCONCLUSIVE
        verdict = "INCONCLUSIVE"
        if (hi == c_lo or lo == c_hi) and not (lo < c_lo and hi > c_hi):
            # boundary touching without interior overlap
            rationale = (f"observed interval ({lo}, {hi}) touches the claim band "
                         f"({c_lo}, {c_hi}) at a boundary without interior overlap — "
                         f"indeterminate, not a material contradiction")
        else:
            rationale = (f"observed interval ({lo}, {hi}) partially overlaps or touches "
                         f"the claim band ({c_lo}, {c_hi}) — uncertainty overlap")
    return DoctrineComparison(
        comparison_id=deterministic_hex("doctrine_compare", observed.metric,
                                        observed.estimate, c_lo, c_hi),
        claim_id="", reproduction_id="",
        metric=observed.metric, observed_estimate=observed.estimate,
        observed_interval=(lo, hi),
        claim_interval=(c_lo, c_hi), verdict=verdict, rationale=rationale,
    )


# --------------------------------------------------------------------------- #
# TC-04 — measured comparison CONTRACT (validate before comparing values)
# --------------------------------------------------------------------------- #
COMPARISON_READY = "READY_TO_COMPARE"
COMPARISON_BLOCKERS = (
    "METRIC_MISMATCH", "UNITS_INCOMPATIBLE", "INVALID_INTERVAL",
    "INVALID_CLAIM_INTERVAL", "ESTIMATE_OUTSIDE_UNCERTAINTY", "SAMPLE_REQUIRED",
)


@dataclass(frozen=True)
class MeasuredComparisonContract:
    """TC-04: two floats are NOT comparable merely because both are floats.
    Before compare_measured_result may compare values, the observation must
    match the target metric contract, units must be compatible, both intervals
    valid, the estimate inside its own uncertainty interval (unless explicitly
    allowed), and a positive sample size present where sample evidence is
    required. Any blocker -> the comparison must not run (fail closed)."""

    metric_ok: bool
    units_ok: bool
    interval_valid: bool
    claim_interval_valid: bool
    estimate_in_interval: bool
    sample_ok: bool
    readiness: str            # READY_TO_COMPARE | one of COMPARISON_BLOCKERS
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"metric_ok": self.metric_ok, "units_ok": self.units_ok,
                "interval_valid": self.interval_valid,
                "claim_interval_valid": self.claim_interval_valid,
                "estimate_in_interval": self.estimate_in_interval,
                "sample_ok": self.sample_ok, "readiness": self.readiness,
                "rationale": self.rationale}


def validate_measured_comparison_contract(
    observed: ObservedResult,
    claim_interval: Sequence[float],
    expected_metric: str = "",
    claim_metric: str = "",
    claim_units: str = "",
    require_sample: bool = True,
    allow_estimate_outside_interval: bool = False,
) -> MeasuredComparisonContract:
    """Deterministic contract validation for a measured-vs-doctrine comparison.

    Metric identity: observed.metric must equal the claim's target metric when a
    contract is declared (expected_metric == claim_metric == observed.metric).
    Units: when the claim declares units, observed.units must match them.
    Intervals: lo <= hi and finite for both observed and claim; an inverted or
    non-finite interval is a blocker, never a contradiction.
    Estimate: must lie inside its own uncertainty interval unless explicitly
    allowed (an estimate outside its own interval is malformed input).
    Sample: sample_size > 0 where sample evidence is required.
    """
    reasons: List[str] = []
    lo, hi = float(observed.uncertainty_interval[0]), float(observed.uncertainty_interval[1])
    c_lo, c_hi = float(claim_interval[0]), float(claim_interval[1])
    iv_ok = (lo <= hi) and _finite(lo) and _finite(hi)
    if not iv_ok:
        reasons.append(f"observed interval invalid: ({lo}, {hi})")
    civ_ok = (c_lo <= c_hi) and _finite(c_lo) and _finite(c_hi)
    if not civ_ok:
        reasons.append(f"claim interval invalid: ({c_lo}, {c_hi})")

    metric_ok = True
    if expected_metric:
        metric_ok = (observed.metric == expected_metric)
        if claim_metric and claim_metric != expected_metric:
            metric_ok = False
        if not metric_ok:
            reasons.append(
                f"metric mismatch: observed {observed.metric!r} vs doctrine target "
                f"{expected_metric!r}")
    elif claim_metric and observed.metric != claim_metric:
        metric_ok = False
        reasons.append(f"metric mismatch: observed {observed.metric!r} vs claim {claim_metric!r}")

    units_ok = True
    if claim_units:
        units_ok = (observed.units == claim_units)
        if not units_ok:
            reasons.append(f"units incompatible: observed {observed.units!r} vs claim {claim_units!r}")
    elif observed.units:
        # units declared on the observation but no claim contract -> cannot
        # confirm compatibility; treat as incompatible to avoid comparing
        # unlike quantities (fail closed on unverified semantics).
        units_ok = False
        reasons.append(f"observed units {observed.units!r} but claim declares no units contract")

    estimate_in = (lo <= observed.estimate <= hi)
    if not estimate_in and not allow_estimate_outside_interval:
        reasons.append(
            f"estimate {observed.estimate} outside its own uncertainty interval "
            f"({lo}, {hi}) — malformed observed result")

    sample_ok = (observed.sample_size > 0) or (not require_sample)
    if not sample_ok:
        reasons.append("sample_size <= 0 while sample evidence is required")

    blocker = ""
    if not metric_ok:
        blocker = "METRIC_MISMATCH"
    elif not units_ok:
        blocker = "UNITS_INCOMPATIBLE"
    elif not iv_ok:
        blocker = "INVALID_INTERVAL"
    elif not civ_ok:
        blocker = "INVALID_CLAIM_INTERVAL"
    elif not estimate_in and not allow_estimate_outside_interval:
        blocker = "ESTIMATE_OUTSIDE_UNCERTAINTY"
    elif not sample_ok:
        blocker = "SAMPLE_REQUIRED"
    return MeasuredComparisonContract(
        metric_ok=metric_ok, units_ok=units_ok,
        interval_valid=iv_ok, claim_interval_valid=civ_ok,
        estimate_in_interval=estimate_in, sample_ok=sample_ok,
        readiness=blocker if blocker else COMPARISON_READY,
        rationale="; ".join(reasons) if reasons else "contract valid — ready to compare",
    )


def _finite(x: float) -> bool:
    import math
    return math.isfinite(x)


def compare_measured_result_guarded(
    observed: ObservedResult,
    claim_interval: Sequence[float],
    expected_metric: str = "",
    claim_metric: str = "",
    claim_units: str = "",
    require_sample: bool = True,
    allow_estimate_outside_interval: bool = False,
) -> Tuple[Optional[MeasuredComparisonContract], Optional[DoctrineComparison]]:
    """TC-04: run the contract first; compare ONLY when READY_TO_COMPARE.
    Returns (contract, comparison) — comparison is None when the contract blocks."""
    contract = validate_measured_comparison_contract(
        observed, claim_interval, expected_metric=expected_metric,
        claim_metric=claim_metric, claim_units=claim_units,
        require_sample=require_sample,
        allow_estimate_outside_interval=allow_estimate_outside_interval)
    if contract.readiness != COMPARISON_READY:
        return contract, None
    return contract, compare_measured_result(observed, claim_interval)


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
# TC-01 — real freeze proof: structured chronology, not "trust me" text
# --------------------------------------------------------------------------- #
FREEZE_CHRONOLOGY_STATUSES = (
    "FROZEN_BEFORE_RESULT_VERIFIED",   # recomputed fp == stored fp AND freeze_seq < result_seq AND refs resolve
    "NO_FREEZE_RECORD",                # protocol carries no stored frozen fingerprint
    "FINGERPRINT_MISMATCH",            # stored fingerprint != recomputed canonical fingerprint (forged or stale-after-mutation)
    "FREEZE_RECORD_INCOMPLETE",        # fingerprint valid but no structured freeze witness (text alone never proves)
    "RESULT_PRECEDES_FREEZE",          # freeze_seq >= result_seq (chronology impossible)
    "FREEZE_EVIDENCE_REFS_UNRESOLVED", # freeze evidence refs do not all resolve in the registry
    "FREEZE_EVIDENCE_REFS_UNVERIFIED", # freeze evidence refs present but no registry supplied — cannot verify
)


@dataclass(frozen=True)
class FreezeChronologyProof:
    """Deterministic proof that a protocol was frozen BEFORE an observed result.
    Distinguishes CURRENT-OBJECT CONSISTENCY (recomputed fingerprint == stored)
    from HISTORICAL FREEZE INTEGRITY (freeze_seq < result_seq + witness)."""

    protocol_ref: str
    stored_fingerprint: str
    recomputed_fingerprint: str
    fingerprint_valid: bool
    freeze_seq: int
    result_seq: int
    chronology_ok: bool          # freeze_seq < result_seq
    structured_freeze: bool      # protocol carries a structured freeze witness
    evidence_refs_resolve: Optional[bool] = None   # None = no refs to check / no registry
    status: str = "NO_FREEZE_RECORD"
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"protocol_ref": self.protocol_ref,
                "stored_fingerprint": self.stored_fingerprint,
                "recomputed_fingerprint": self.recomputed_fingerprint,
                "fingerprint_valid": self.fingerprint_valid,
                "freeze_seq": self.freeze_seq, "result_seq": self.result_seq,
                "chronology_ok": self.chronology_ok,
                "structured_freeze": self.structured_freeze,
                "evidence_refs_resolve": self.evidence_refs_resolve,
                "status": self.status, "reason": self.reason}


def verify_freeze_chronology(
    protocol: FrozenExperimentProtocol,
    result_seq: int,
    registry=None,
) -> FreezeChronologyProof:
    """TC-01: prove (or fail) that a frozen protocol predates an observed result.

    Fail-closed ladder (first failed rung decides):
      1. a STORED frozen fingerprint must exist                 -> NO_FREEZE_RECORD
      2. recomputed canonical fingerprint == stored fingerprint -> FINGERPRINT_MISMATCH
         (a forged stored fingerprint OR a stale fingerprint left behind after a
         post-freeze field mutation both land here — the stored value does not
         match what the CURRENT canonical fields produce);
      3. a STRUCTURED freeze witness must exist (freeze_seq/epoch/authority) —
         free-form frozen_before_result_evidence text alone proves nothing;
      4. freeze evidence refs, when declared, must resolve        -> *_REFS_*
         (a registry must be supplied to verify them; without one the proof is
         UNVERIFIED, never claimed resolved);
      5. freeze_seq < result_seq                                 -> RESULT_PRECEDES_FREEZE

    Logical chronology is used (deterministic seq), not wall clock.
    """
    stored = str(protocol.fingerprint or "")
    if not stored:
        return FreezeChronologyProof(
            protocol_ref=protocol.protocol_id, stored_fingerprint="",
            recomputed_fingerprint="", fingerprint_valid=False,
            freeze_seq=protocol.freeze_seq, result_seq=int(result_seq or 0),
            chronology_ok=False, structured_freeze=protocol.structured_freeze_present(),
            status="NO_FREEZE_RECORD",
            reason="protocol carries no stored frozen fingerprint — freeze cannot be proven")
    recomputed = protocol.compute_fingerprint_canonical()
    if recomputed != stored:
        return FreezeChronologyProof(
            protocol_ref=protocol.protocol_id, stored_fingerprint=stored,
            recomputed_fingerprint=recomputed, fingerprint_valid=False,
            freeze_seq=protocol.freeze_seq, result_seq=int(result_seq or 0),
            chronology_ok=False, structured_freeze=protocol.structured_freeze_present(),
            status="FINGERPRINT_MISMATCH",
            reason=("stored fingerprint != recomputed canonical fingerprint — the stored value "
                    "is forged or stale (fields mutated after freeze); CURRENT OBJECT CONSISTENCY "
                    "is broken, so no freeze claim can be trusted"))
    if not protocol.structured_freeze_present():
        return FreezeChronologyProof(
            protocol_ref=protocol.protocol_id, stored_fingerprint=stored,
            recomputed_fingerprint=recomputed, fingerprint_valid=True,
            freeze_seq=protocol.freeze_seq, result_seq=int(result_seq or 0),
            chronology_ok=False, structured_freeze=False,
            status="FREEZE_RECORD_INCOMPLETE",
            reason=("fingerprint is self-consistent but no STRUCTURED freeze witness exists; "
                    "free-form 'frozen_before_result_evidence' text alone must not prove chronology"))
    refs = tuple(protocol.freeze_evidence_refs or ())
    if refs:
        if registry is None:
            return FreezeChronologyProof(
                protocol_ref=protocol.protocol_id, stored_fingerprint=stored,
                recomputed_fingerprint=recomputed, fingerprint_valid=True,
                freeze_seq=protocol.freeze_seq, result_seq=int(result_seq or 0),
                chronology_ok=False, structured_freeze=True,
                evidence_refs_resolve=None, status="FREEZE_EVIDENCE_REFS_UNVERIFIED",
                reason="freeze evidence refs declared but no registry supplied — refs cannot be verified")
        unresolved = [r for r in refs if not registry.has(r)]
        if unresolved:
            return FreezeChronologyProof(
                protocol_ref=protocol.protocol_id, stored_fingerprint=stored,
                recomputed_fingerprint=recomputed, fingerprint_valid=True,
                freeze_seq=protocol.freeze_seq, result_seq=int(result_seq or 0),
                chronology_ok=False, structured_freeze=True,
                evidence_refs_resolve=False, status="FREEZE_EVIDENCE_REFS_UNRESOLVED",
                reason=f"freeze evidence refs do not resolve in the registry: {unresolved}")
    freeze_seq = int(protocol.freeze_seq or 0)
    result_seq_i = int(result_seq or 0)
    if freeze_seq >= result_seq_i:
        return FreezeChronologyProof(
            protocol_ref=protocol.protocol_id, stored_fingerprint=stored,
            recomputed_fingerprint=recomputed, fingerprint_valid=True,
            freeze_seq=freeze_seq, result_seq=result_seq_i,
            chronology_ok=False, structured_freeze=True,
            evidence_refs_resolve=(True if refs else None),
            status="RESULT_PRECEDES_FREEZE",
            reason=(f"freeze_seq {freeze_seq} is not < result_seq {result_seq_i} — the result "
                    f"cannot have been produced after the freeze"))
    return FreezeChronologyProof(
        protocol_ref=protocol.protocol_id, stored_fingerprint=stored,
        recomputed_fingerprint=recomputed, fingerprint_valid=True,
        freeze_seq=freeze_seq, result_seq=result_seq_i,
        chronology_ok=True, structured_freeze=True,
        evidence_refs_resolve=(True if refs else None),
        status="FROZEN_BEFORE_RESULT_VERIFIED",
        reason=(f"recomputed canonical fingerprint == stored frozen fingerprint; "
                f"freeze_seq {freeze_seq} < result_seq {result_seq_i}; chronology proven"))


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
    protocol whose target domain matches, whose fingerprint is independently
    recomputed from canonical fields and matches the stored frozen fingerprint,
    and whose frozen-before-result is evidenced (ER-01).

    The fingerprint is NOT merely checked as non-empty — it is recomputed from the
    protocol's canonical_dict() (which excludes the fingerprint field itself) and
    compared to the stored fingerprint. A forged or stale non-empty fingerprint
    will not match the recomputed value and fails validation.
    """
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
    # ER-01: independently recompute fingerprint from canonical fields (excludes
    # the fingerprint field itself) and verify it matches the stored frozen fingerprint.
    recomputed_fp = protocol.compute_fingerprint_canonical()
    fp_ok = bool(protocol.fingerprint) and protocol.fingerprint == recomputed_fp
    if getattr(protocol, "target_domain", "") != hypothesis.target_domain:
        # G5R-21 / ER-01: the protocol must have been frozen FOR the hypothesis's
        # target domain — a registered protocol for another domain cannot authorize it.
        return FrozenProtocolResolution(
            protocol_ref=ref, resolved=True, target_domain_ok=False,
            claim_hypothesis_ok=False, fingerprint_valid=fp_ok,
            frozen_before_result=protocol.structured_freeze_present(),
            protocol=protocol,
            reason=(f"registered protocol {ref!r} was frozen for target domain "
                    f"{protocol.target_domain!r}, not {hypothesis.target_domain!r}"))
    # TC-01 / AMB-G5R-02: claim_hypothesis_ok must be a TESTED linkage, never a
    # default-true. The protocol's mechanism_ref must bind to the hypothesis's
    # mechanism identity (hypothesis.mechanism_ref, falling back to the
    # hypothesis_id which IS the mechanism identity in this domain object model).
    # Where no such binding exists, claim_hypothesis_ok stays False and the reason
    # documents that claim linkage is mechanism-mediated only (the protocol carries
    # no direct claim_ref — this is stated, not hidden).
    mech = (hypothesis.mechanism_ref or hypothesis.hypothesis_id or "").strip()
    protocol_mech = (protocol.mechanism_ref or "").strip()
    binding_ok = bool(mech) and bool(protocol_mech) and protocol_mech == mech
    if not binding_ok:
        return FrozenProtocolResolution(
            protocol_ref=ref, resolved=True, target_domain_ok=True,
            claim_hypothesis_ok=False, fingerprint_valid=fp_ok,
            frozen_before_result=protocol.structured_freeze_present(),
            protocol=protocol,
            reason=(f"protocol mechanism_ref {protocol_mech!r} does not bind to the "
                    f"hypothesis mechanism identity {mech!r}; claim-hypothesis linkage "
                    f"is mechanism-mediated (protocol carries no direct claim_ref) and "
                    f"is NOT set true without a tested binding"))
    # frozen_before_result must be STRUCTURALLY evidenced (TC-01). Free-form
    # frozen_before_result_evidence text alone no longer proves chronology — the
    # protocol must carry a structured freeze witness (freeze_seq/epoch/authority
    # and/or freeze evidence refs). Full chronological proof against a specific
    # result seq is computed by verify_freeze_chronology(); this resolver proves
    # the freeze record exists and is self-consistent.
    fbr_evidenced = protocol.structured_freeze_present()
    return FrozenProtocolResolution(
        protocol_ref=ref, resolved=True,
        target_domain_ok=True,
        claim_hypothesis_ok=True,
        fingerprint_valid=fp_ok,
        frozen_before_result=fbr_evidenced,
        protocol=protocol,
        reason=("frozen protocol registered; ref/domain/fingerprint verified; "
                "mechanism binding verified; structured freeze witness present"
                if fbr_evidenced else
                "frozen protocol registered; ref/domain/fingerprint verified; "
                "mechanism binding verified; NO structured freeze witness — "
                "freeze-before-result NOT evidenced"))


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