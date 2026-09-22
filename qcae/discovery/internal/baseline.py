"""Internal-first discovery baseline — canon 2.6 (Internal Discovery).

Canon 2.6.1 puts internal discovery first because "external acquisition creates
new burden": before importing anything, QCAE establishes the internal baseline.
This module turns pure retrieval over the P1 registry surfaces into an explicit,
auditable baseline record:

- **Same ontology, no automatic trust (2.6.3, 2.6.10).** Internal candidates use
  the frozen capability model and carry no privileged verification: the record's
  ``internal_trust_level`` is always ``DISCOVERED``. Ownership proves nothing.
- **Prior decisions before repeated investigation (2.6.5).** The P1
  ``decision_reuse_findings`` result is carried into the baseline, so a known
  rejected/blocked path cannot be silently rediscovered.
- **Note the two P1 parameters used for the service identity:** the plan's
  ``capability_id`` argument to ``RegistryQuery``. The plan's ``contract_id`` is
  the capability identity in QCAE's model
  (``CapabilityContract`` is keyed by ``capability_id`` + ``contract_version``),
  and the P1 port expects the version as a string, so the adapter converts at
  exactly this boundary.
- **Partial reuse narrows the external request (2.6.8).** ``external_target_atoms``
  is by construction the requested atoms minus the internally covered ones — one
  of QCAE's strongest anti-framework mechanisms.
- **Fail closed on unknown state (2.6.11).** An unrecognized retrieval shape
  raises instead of being read as "no internal knowledge", because that
  misreading would authorize external discovery on the strength of a bug.

Deliberate non-derivations (recorded in the P3-I0 ledger as derived points):

- ``INTERNAL_IMPLEMENTATION_SUPERIOR``/``INTERNAL_IMPLEMENTATION_INFERIOR``
  require comparative evidence and are **never** emitted from retrieval state
  (they belong to evaluation, Book IV Blocks 9/11).
- ``ABANDONED_BUT_RECOVERABLE`` needs branch/history surfaces the P1 ports do
  not expose yet; it is not inferred from the absence of recent activity, which
  would confuse abandonment with a stable mature component (canon 2.2.8).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable, List, Mapping, Optional, Tuple

from qcae.core.discovery.plan import DiscoveryPlan
from qcae.core.errors import QcaeValidationError
from qcae.core.ports.knowledge_registry import RegistryQuery
from qcae.core.serialization import SerializableRecord, coerce_enum_tuple
from qcae.core.validation import (
    require_enum,
    require_enum_tuple,
    require_identifier,
    require_non_empty_str,
    require_no_duplicates,
    require_str_list,
)
from qcae.core.vocabulary import VerificationLevel

__all__ = [
    "BASELINE_POLICY_VERSION",
    "INTERNAL_FIRST_CATEGORIES",
    "NON_DERIVABLE_CLASSIFICATIONS",
    "SUFFICIENCY_VERDICTS",
    "InternalBaselineClassification",
    "InternalBaselineRecord",
    "InternalDiscoveryBaselineService",
    "InternalDiscoveryPolicy",
    "make_internal_baseline",
]


class InternalBaselineClassification(StrEnum):
    """Internal-baseline findings (canon 2.6.1, verbatim)."""

    FULLY_SATISFIED_INTERNAL = "FULLY_SATISFIED_INTERNAL"
    PARTIALLY_SATISFIED_INTERNAL = "PARTIALLY_SATISFIED_INTERNAL"
    INTERNAL_COMPONENT_REUSABLE = "INTERNAL_COMPONENT_REUSABLE"
    INTERNAL_IMPLEMENTATION_INFERIOR = "INTERNAL_IMPLEMENTATION_INFERIOR"
    INTERNAL_IMPLEMENTATION_SUPERIOR = "INTERNAL_IMPLEMENTATION_SUPERIOR"
    ABANDONED_BUT_RECOVERABLE = "ABANDONED_BUT_RECOVERABLE"
    DUPLICATE_IMPLEMENTATIONS = "DUPLICATE_IMPLEMENTATIONS"
    PRIOR_EXTERNAL_REJECTION_EXISTS = "PRIOR_EXTERNAL_REJECTION_EXISTS"
    NO_INTERNAL_CAPABILITY_FOUND = "NO_INTERNAL_CAPABILITY_FOUND"


#: Exactly one of these is the baseline's sufficiency verdict (canon 2.6.1):
#: either the capability is fully held internally, partially held, or absent.
SUFFICIENCY_VERDICTS: frozenset = frozenset(
    {
        InternalBaselineClassification.FULLY_SATISFIED_INTERNAL,
        InternalBaselineClassification.PARTIALLY_SATISFIED_INTERNAL,
        InternalBaselineClassification.NO_INTERNAL_CAPABILITY_FOUND,
    }
)

#: Classifications that durable retrieval state alone cannot establish (see the
#: module docstring). A retrieval adapter that emitted one of these would be
#: inventing evaluation evidence.
NON_DERIVABLE_CLASSIFICATIONS: frozenset = frozenset(
    {
        InternalBaselineClassification.INTERNAL_IMPLEMENTATION_SUPERIOR,
        InternalBaselineClassification.INTERNAL_IMPLEMENTATION_INFERIOR,
        InternalBaselineClassification.ABANDONED_BUT_RECOVERABLE,
    }
)

#: P1 ``RegistryQuery.internal_first_findings`` category names (its continuation
#: spec §9 A–F taxonomy). Used to fail closed on unrecognized shapes.
INTERNAL_FIRST_CATEGORIES: frozenset = frozenset(
    {
        "CAPABILITY_ACTIVE",
        "EVIDENCE_STALE",
        "CANDIDATE_PREVIOUSLY_FAILED",
        "REVISION_CHANGED",
        "DEFINITION_WITHOUT_IMPLEMENTATION",
        "NO_INTERNAL_KNOWLEDGE",
    }
)

#: Category → baseline classification, retrieval-only mapping (documented in the
#: P3-I0 ledger). Categories that also carry reference lists are kept as
#: first-class record fields rather than folded into the classification.
CATEGORY_CLASSIFICATIONS: Mapping[str, InternalBaselineClassification] = {
    "CAPABILITY_ACTIVE": InternalBaselineClassification.FULLY_SATISFIED_INTERNAL,
    "DEFINITION_WITHOUT_IMPLEMENTATION": InternalBaselineClassification.PARTIALLY_SATISFIED_INTERNAL,
    "EVIDENCE_STALE": InternalBaselineClassification.INTERNAL_COMPONENT_REUSABLE,
    "CANDIDATE_PREVIOUSLY_FAILED": InternalBaselineClassification.PRIOR_EXTERNAL_REJECTION_EXISTS,
    "REVISION_CHANGED": InternalBaselineClassification.INTERNAL_COMPONENT_REUSABLE,
    "NO_INTERNAL_KNOWLEDGE": InternalBaselineClassification.NO_INTERNAL_CAPABILITY_FOUND,
}

BASELINE_POLICY_VERSION = "internal-discovery-policy-1.0"

_COVERAGE_CAPABILITY_GRANULARITY = "CAPABILITY_GRANULARITY_FROM_REGISTRY_STATE"
_COVERAGE_ATOM_ATTRIBUTED = "ATOM_ATTRIBUTED_BY_CALLER"


@dataclass(frozen=True)
class InternalDiscoveryPolicy:
    """Local access/policy envelope for internal discovery (canon 2.6.11).

    Standalone QCAE uses the local policy shim and must fail closed when
    authorization is unclear; the classification travels with the baseline so a
    later consumer can refuse a record it is not entitled to read.
    """

    policy_version: str = BASELINE_POLICY_VERSION
    access_classification: str = "INTERNAL"

    def validate(self) -> None:
        require_non_empty_str(self.policy_version, "policy_version")
        require_non_empty_str(self.access_classification, "access_classification")


@dataclass(frozen=True)
class InternalBaselineRecord(SerializableRecord):
    """The explicit internal baseline canon 2.6.7 requires (immutable)."""

    SCHEMA_VERSION = 1

    baseline_id: str
    capability_id: str
    contract_id: str
    contract_version: int

    requested_atoms: Tuple[str, ...]
    covered_atoms: Tuple[str, ...]
    missing_atoms: Tuple[str, ...]
    external_target_atoms: Tuple[str, ...]

    classifications: Tuple[InternalBaselineClassification, ...]
    sufficiency_verdict: InternalBaselineClassification

    internal_candidate_refs: Tuple[str, ...] = ()
    prior_rejection_refs: Tuple[str, ...] = ()
    stale_evidence_refs: Tuple[str, ...] = ()
    revision_change_refs: Tuple[str, ...] = ()
    requires_revalidation: bool = False
    sufficient_without_discovery: bool = False
    comparison_basis: str = ""
    coverage_basis: str = _COVERAGE_CAPABILITY_GRANULARITY
    access_classification: str = "INTERNAL"
    query_provenance: Tuple[str, ...] = ()
    policy_version: str = BASELINE_POLICY_VERSION
    created_at: str = ""
    created_by: str = ""
    notes: str = ""

    _COERCIONS = {
        "requested_atoms": tuple,
        "covered_atoms": tuple,
        "missing_atoms": tuple,
        "external_target_atoms": tuple,
        "classifications": lambda v: coerce_enum_tuple(v, InternalBaselineClassification),
        "sufficiency_verdict": lambda v: _coerce_classification(v),
        "internal_candidate_refs": tuple,
        "prior_rejection_refs": tuple,
        "stale_evidence_refs": tuple,
        "revision_change_refs": tuple,
        "query_provenance": tuple,
    }

    def validate(self) -> None:
        require_identifier(self.baseline_id, "baseline_id")
        require_identifier(self.capability_id, "capability_id")
        require_identifier(self.contract_id, "contract_id")
        if not isinstance(self.contract_version, int) or isinstance(
            self.contract_version, bool
        ) or self.contract_version < 1:
            raise QcaeValidationError("contract_version must be an integer >= 1")
        require_non_empty_str(self.created_at, "created_at")
        require_non_empty_str(self.created_by, "created_by")
        require_non_empty_str(self.policy_version, "policy_version")
        require_non_empty_str(self.access_classification, "access_classification")
        require_non_empty_str(self.coverage_basis, "coverage_basis")

        for name in ("requested_atoms", "covered_atoms", "missing_atoms",
                     "external_target_atoms", "internal_candidate_refs",
                     "prior_rejection_refs", "stale_evidence_refs",
                     "revision_change_refs", "query_provenance"):
            require_str_list(getattr(self, name), name)
        if not self.requested_atoms:
            raise QcaeValidationError(
                "an internal baseline must state the requested atoms it judged "
                "(canon 2.6.7: every external comparison has an explicit baseline)"
            )
        require_no_duplicates(self.requested_atoms, "requested_atoms")
        require_no_duplicates(self.covered_atoms, "covered_atoms")
        require_no_duplicates(self.missing_atoms, "missing_atoms")
        require_no_duplicates(self.external_target_atoms, "external_target_atoms")

        if not self.query_provenance:
            raise QcaeValidationError(
                "internal discovery records its query provenance (canon 2.6.12 "
                "internal_candidate_record / 2.6.7 baseline)"
            )

        require_enum(
            self.sufficiency_verdict,
            InternalBaselineClassification,
            "sufficiency_verdict",
        )
        require_enum_tuple(
            self.classifications,
            InternalBaselineClassification,
            "classifications",
        )
        if not self.classifications:
            raise QcaeValidationError("a baseline must carry at least one classification")
        require_no_duplicates([c.value for c in self.classifications], "classifications")
        if self.sufficiency_verdict not in SUFFICIENCY_VERDICTS:
            raise QcaeValidationError(
                f"sufficiency_verdict must be one of "
                f"{sorted(v.value for v in SUFFICIENCY_VERDICTS)}, got "
                f"{self.sufficiency_verdict.value}"
            )
        if self.sufficiency_verdict not in self.classifications:
            raise QcaeValidationError(
                "the sufficiency verdict must be one of the record's classifications"
            )
        impossible = sorted(
            c.value for c in self.classifications if c in NON_DERIVABLE_CLASSIFICATIONS
            and not self.comparison_basis.strip()
        )
        if impossible:
            raise QcaeValidationError(
                f"classifications {impossible} require explicit comparative evidence "
                "(canon 2.6.3/2.6.10: internal ownership is not proof, and 'better' "
                "than an external candidate is an evaluation result)"
            )

        # Canon 2.6.8: partial reuse narrows the external request exactly.
        expected_missing = tuple(a for a in self.requested_atoms if a not in set(self.covered_atoms))
        if tuple(self.missing_atoms) != expected_missing:
            raise QcaeValidationError(
                f"missing_atoms must be the requested atoms minus the covered ones: "
                f"expected {expected_missing}, got {tuple(self.missing_atoms)}"
            )
        if tuple(self.external_target_atoms) != expected_missing:
            raise QcaeValidationError(
                f"external_target_atoms must equal the uncovered atoms (canon 2.6.8 "
                f"partial reuse): expected {expected_missing}, got "
                f"{tuple(self.external_target_atoms)}"
            )
        unknown_covered = sorted(set(self.covered_atoms) - set(self.requested_atoms))
        if unknown_covered:
            raise QcaeValidationError(
                f"covered_atoms outside the requested scope: {unknown_covered}"
            )

        if self.sufficiency_verdict == InternalBaselineClassification.FULLY_SATISFIED_INTERNAL:
            if expected_missing:
                raise QcaeValidationError(
                    "FULLY_SATISFIED_INTERNAL cannot leave uncovered atoms; a partial "
                    "result is PARTIALLY_SATISFIED_INTERNAL (canon 2.6.1)"
                )
        if self.sufficient_without_discovery and expected_missing:
            raise QcaeValidationError(
                "sufficient_without_discovery cannot coexist with an external target "
                "(canon 2.6.5/Book IV 9.7: do not spend external discovery budget on "
                "a capability already known)"
            )
        if not self.covered_atoms:
            if self.sufficiency_verdict != InternalBaselineClassification.NO_INTERNAL_CAPABILITY_FOUND:
                raise QcaeValidationError(
                    "a baseline with no covered atoms must be classified "
                    "NO_INTERNAL_CAPABILITY_FOUND (canon 2.6.1)"
                )
        elif self.sufficiency_verdict == InternalBaselineClassification.NO_INTERNAL_CAPABILITY_FOUND:
            raise QcaeValidationError(
                "NO_INTERNAL_CAPABILITY_FOUND cannot be reported when internally "
                "covered atoms exist (canon 2.6.1)"
            )
        if self.requires_revalidation and not (
            self.stale_evidence_refs or self.revision_change_refs
        ):
            raise QcaeValidationError(
                "requires_revalidation must cite the stale evidence or revision change "
                "that forces it (canon 2.6.7 known limitations)"
            )
        if not isinstance(self.requires_revalidation, bool) or not isinstance(
            self.sufficient_without_discovery, bool
        ):
            raise QcaeValidationError("revalidation/sufficiency flags must be booleans")

    # -- derived standing ---------------------------------------------------

    @property
    def internal_trust_level(self) -> VerificationLevel:
        """Always ``DISCOVERED``: internal ownership is not proof (2.6.3, 2.6.10)."""
        return VerificationLevel.DISCOVERED

    @property
    def external_search_required(self) -> bool:
        """Whether external discovery still has work to do (canon 2.6.8)."""
        return bool(self.external_target_atoms)

    @property
    def partial_reuse(self) -> bool:
        """True when some — but not all — requested atoms are held internally."""
        return bool(self.covered_atoms) and bool(self.external_target_atoms)


def _coerce_classification(value: object) -> object:
    if isinstance(value, InternalBaselineClassification) or not isinstance(value, str):
        return value
    try:
        return InternalBaselineClassification(value)
    except ValueError:
        return value


class InternalDiscoveryBaselineService:
    """Builds the internal baseline from durable state (canon 2.6, retrieval only).

    The service performs no search of its own: it asks the injected
    ``RegistryQuery`` port (P1) what QCAE already holds, maps the answer through
    the documented table above, and refuses to guess when the answer is
    unrecognizable.
    """

    def __init__(
        self,
        registry_query: RegistryQuery,
        policy: Optional[InternalDiscoveryPolicy] = None,
    ) -> None:
        self._registry = registry_query
        self._policy = policy or InternalDiscoveryPolicy()
        self._policy.validate()

    @property
    def policy(self) -> InternalDiscoveryPolicy:
        return self._policy

    def build(
        self,
        *,
        baseline_id: str,
        plan: DiscoveryPlan,
        created_at: str,
        created_by: str,
        atom_coverage: Optional[Mapping[str, Iterable[str]]] = None,
        notes: str = "",
    ) -> InternalBaselineRecord:
        """Assemble the baseline for a plan's atom scope.

        ``atom_coverage`` (optional) supplies per-atom internal references when
        the caller can attribute them; without it, coverage is derived at
        capability granularity from registry state and labelled as such, so the
        narrower claim is never silently overstated.
        """
        capability_id = plan.contract_id
        findings = self._registry.internal_first_findings(
            capability_id, plan.contract_id, str(plan.contract_version)
        )
        state = self._registry.known_capability_state(capability_id)
        reuse = self._registry.decision_reuse_findings(
            capability_id, plan.contract_id, str(plan.contract_version)
        )

        categories = self._categories(findings)
        detail = findings.get("detail") or {}
        if not isinstance(detail, dict):
            raise QcaeValidationError(
                "registry internal-first findings returned a non-object detail block"
            )

        internal_atoms = tuple(state.get("atom_ids") or ())
        candidate_refs = tuple(sorted(state.get("candidate_refs") or ()))
        # The registry's two internal-candidate records: known candidates, and
        # active receipts under this exact contract (the same fact that makes
        # CAPABILITY_ACTIVE fire). Coverage and verdict read one basis.
        active_receipt_refs = tuple(sorted(reuse.get("active_receipts") or ()))
        internal_refs = tuple(sorted(set(candidate_refs) | set(active_receipt_refs)))

        if atom_coverage is None:
            covered_atoms, coverage_basis, coverage_refs = self._capability_granularity_coverage(
                plan, internal_atoms, internal_refs
            )
            duplicate_atom_refs: Tuple[Tuple[str, ...], ...] = ()
        else:
            covered_atoms, coverage_refs = self._attributed_coverage(plan, atom_coverage)
            coverage_basis = _COVERAGE_ATOM_ATTRIBUTED
            duplicate_atom_refs = tuple(
                tuple(atom_coverage.get(atom_id, ())) for atom_id in covered_atoms
            )

        missing_atoms = tuple(a for a in plan.atom_ids if a not in set(covered_atoms))
        stale_evidence = tuple(sorted(detail.get("EVIDENCE_STALE") or ()))
        revision_changes = tuple(sorted(detail.get("REVISION_CHANGED") or ()))
        rejections = tuple(sorted(detail.get("CANDIDATE_PREVIOUSLY_FAILED") or ()))
        negative_blocks = tuple(sorted(reuse.get("negative_blocks") or ()))

        classifications = self._classify(
            categories=categories,
            covered_atoms=covered_atoms,
            missing_atoms=missing_atoms,
            candidate_refs=candidate_refs,
            stale_evidence=stale_evidence,
            rejections=rejections,
            duplicate_atom_refs=duplicate_atom_refs,
        )
        verdict = self._verdict(classifications, covered_atoms, missing_atoms)
        # The verdict is always carried in the classification set, so a reader can
        # never see a sufficiency claim that its own findings do not support.
        if verdict not in classifications:
            classifications = tuple(classifications) + (verdict,)

        record = InternalBaselineRecord(
            baseline_id=baseline_id,
            capability_id=capability_id,
            contract_id=plan.contract_id,
            contract_version=plan.contract_version,
            requested_atoms=tuple(plan.atom_ids),
            covered_atoms=covered_atoms,
            missing_atoms=missing_atoms,
            external_target_atoms=missing_atoms,
            classifications=classifications,
            sufficiency_verdict=verdict,
            internal_candidate_refs=tuple(sorted(set(candidate_refs) | set(coverage_refs))),
            prior_rejection_refs=tuple(sorted(set(rejections) | set(negative_blocks))),
            stale_evidence_refs=stale_evidence,
            revision_change_refs=revision_changes,
            requires_revalidation=bool(stale_evidence or revision_changes),
            sufficient_without_discovery=bool(reuse.get("sufficient_without_discovery"))
            and not missing_atoms,
            coverage_basis=coverage_basis,
            access_classification=self._policy.access_classification,
            query_provenance=tuple(plan.internal_baseline_queries),
            policy_version=self._policy.policy_version,
            created_at=created_at,
            created_by=created_by,
            notes=notes,
        )
        record.validate()
        return record

    # -- internals ----------------------------------------------------------

    @staticmethod
    def _categories(findings: Mapping[str, object]) -> Tuple[str, ...]:
        if not isinstance(findings, dict) or "categories" not in findings:
            raise QcaeValidationError(
                "registry internal-first findings are unrecognizable; refusing to read "
                "an unknown answer as 'no internal knowledge' (canon 2.6.11 fail-closed)"
            )
        raw = findings["categories"]
        if not isinstance(raw, (list, tuple)):
            raise QcaeValidationError("internal-first categories must be a sequence")
        for category in raw:
            if category not in INTERNAL_FIRST_CATEGORIES:
                raise QcaeValidationError(
                    f"unknown internal-first category {category!r}; the retrieval "
                    "contract changed and this mapping must be revisited rather than "
                    "silently dropping a finding"
                )
        return tuple(raw)

    @staticmethod
    def _capability_granularity_coverage(plan, internal_atoms, internal_refs):
        """Derive coverage from registry state, labelled as capability-granularity.

        ``internal_refs`` is the registry's evidence that QCAE already holds an
        implementation of this capability: its known candidates *and* any active
        receipt issued under this exact contract (canon 2.6.12 internal candidate
        records). Both are needed, because coverage and the sufficiency verdict
        must read one basis: ``CAPABILITY_ACTIVE`` maps to
        ``FULLY_SATISFIED_INTERNAL``, so a proven implementation with a still-empty
        candidate inventory must not read as no coverage — that combination claims
        full satisfaction with every atom uncovered and the record's own laws
        refuse it, which left the strongest internal state unable to state a
        baseline at all.

        The P1 ports expose which atoms a capability defines and which candidates
        exist, but not a per-atom candidate attribution. When internal evidence
        exists, the internal atoms in the plan's scope are therefore reported as
        covered *at capability granularity*, with those refs recorded as the basis
        — a weaker, explicitly labelled claim rather than an invented one.
        """
        atoms_in_scope = set(plan.atom_ids)
        if not internal_refs:
            return (), _COVERAGE_CAPABILITY_GRANULARITY, ()
        covered = tuple(a for a in plan.atom_ids if a in (set(internal_atoms) & atoms_in_scope))
        return covered, _COVERAGE_CAPABILITY_GRANULARITY, internal_refs

    @staticmethod
    def _attributed_coverage(plan, atom_coverage: Mapping[str, Iterable[str]]):
        unknown = sorted(set(atom_coverage) - set(plan.atom_ids))
        if unknown:
            raise QcaeValidationError(
                f"atom_coverage names atoms outside the plan scope: {unknown}"
            )
        covered: List[str] = []
        refs: List[str] = []
        for atom_id in plan.atom_ids:
            atom_refs = tuple(atom_coverage.get(atom_id, ()))
            if atom_refs:
                covered.append(atom_id)
                refs.extend(atom_refs)
        return tuple(covered), tuple(sorted(set(refs)))

    @staticmethod
    def _classify(
        *,
        categories,
        covered_atoms,
        missing_atoms,
        candidate_refs,
        stale_evidence,
        rejections,
        duplicate_atom_refs: Tuple[Tuple[str, ...], ...] = (),
    ) -> Tuple[InternalBaselineClassification, ...]:
        found: List[InternalBaselineClassification] = []
        for category in categories:
            mapped = CATEGORY_CLASSIFICATIONS[category]
            if mapped not in found:
                found.append(mapped)
        # Canon 2.6.9 duplicate seed: only emitted when the caller could actually
        # attribute two or more implementations to one atom. Capability-granularity
        # candidate counts do not prove duplication, so they are never used here.
        if any(len(refs) > 1 for refs in duplicate_atom_refs):
            found.append(InternalBaselineClassification.DUPLICATE_IMPLEMENTATIONS)
        # Partial internal coverage is its own finding (canon 2.6.8).
        if covered_atoms and missing_atoms:
            partial = InternalBaselineClassification.PARTIALLY_SATISFIED_INTERNAL
            if partial not in found:
                found.append(partial)
        if stale_evidence and InternalBaselineClassification.INTERNAL_COMPONENT_REUSABLE not in found:
            found.append(InternalBaselineClassification.INTERNAL_COMPONENT_REUSABLE)
        if rejections and InternalBaselineClassification.PRIOR_EXTERNAL_REJECTION_EXISTS not in found:
            found.append(InternalBaselineClassification.PRIOR_EXTERNAL_REJECTION_EXISTS)
        return tuple(found)

    @staticmethod
    def _verdict(classifications, covered_atoms, missing_atoms):
        if InternalBaselineClassification.FULLY_SATISFIED_INTERNAL in classifications:
            return InternalBaselineClassification.FULLY_SATISFIED_INTERNAL
        if covered_atoms:
            return InternalBaselineClassification.PARTIALLY_SATISFIED_INTERNAL
        return InternalBaselineClassification.NO_INTERNAL_CAPABILITY_FOUND


def make_internal_baseline(**kwargs) -> InternalBaselineRecord:
    """Build and validate an internal baseline record in one call."""
    record = InternalBaselineRecord(**kwargs)
    record.validate()
    return record
