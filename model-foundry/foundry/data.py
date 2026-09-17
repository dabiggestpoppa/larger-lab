"""MF-B2 — Data Constitution + Source Registry.

Answers:

    Which data may exist in the Foundry, under what rights, in which role, and
    with what ancestry?

Doctrine enforced here:

    ACCESS != RIGHTS
    AVAILABLE DATA != TRAINABLE DATA
    REGISTERED SOURCE != CLEAN SOURCE
    UNKNOWN != FAVORABLE

Deterministic and fixture-based: no network calls, no semantic model judgment.
Rights decisions come from recorded *basis evidence*; an unresolved basis can
never become a training permission simply because a record mentions a licence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .core import (
    FrozenMap,
    OceTestDouble,
    PolicyBlocked,
    VersionedRegistry,
    fingerprint,
)
from .enums import (
    CLAIM_DEGRADING_CONTAMINATION,
    CONTAMINATION_SEVERITY,
    ContaminationClass,
    ContaminationType,
    RightsBasis,
    RightsState,
    SourceRole,
    TrustClass,
)

DATA_DOUBLE = OceTestDouble(
    fixture="FoundryLocalEvidenceLedger",
    canonical_oce_target="OCE EvidenceGraph / evidence registry",
    replacement_condition="replace when convergence branch exposes canonical evidence graph",
    retirement_evidence="evidence refs carry canonical OCE envelope ids",
)

#: Content markers identifying CEREBUS-family withheld doctrine. Matching is
#: structural (payload class + token-level doctrine shape), not vocabulary-only.
CEREBUS_FAMILY_PROHIBITED_PAYLOAD_CLASSES: tuple[str, ...] = (
    "cerebus_doctrine",
    "cerebus_rule_table",
    "cerebus_threshold_set",
    "rlt_doctrine",
    "pc_alm_doctrine",
)


# --------------------------------------------------------------------------
# Rights
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RightsDisposition:
    """A rights decision and the evidence that produced it.

    ``basis_ref`` must resolve inside the registry; a bare basis string is a
    *claim*, not a disposition. This mirrors MF-B4's claim-vs-verified split.
    """

    subject: str
    basis: RightsBasis
    basis_ref: str
    basis_resolved: bool
    basis_scope: str
    decided_utc: str

    @property
    def state(self) -> RightsState:
        if not self.basis_resolved:
            return RightsState.REVIEW_REQUIRED
        if self.basis is RightsBasis.PROHIBITED:
            return RightsState.EXCLUDED_BY_POLICY
        if self.basis is RightsBasis.UNKNOWN:
            return RightsState.RIGHTS_UNKNOWN
        if self.basis is RightsBasis.RIGHTS_REVIEW_REQUIRED:
            return RightsState.REVIEW_REQUIRED
        if self.basis in {
            RightsBasis.EXPLICIT_OPEN_LICENSE,
            RightsBasis.PUBLIC_DOMAIN,
            RightsBasis.OPERATOR_OWNED,
            RightsBasis.DIRECT_PERMISSION,
        }:
            return RightsState.RIGHTS_VERIFIED_BY_POLICY
        # PROVIDER_TERMS_ALLOW verifies only when the terms scope is recorded
        # and non-empty; otherwise it is restricted.
        return (
            RightsState.RIGHTS_VERIFIED_BY_POLICY
            if self.basis_scope.strip()
            else RightsState.RIGHTS_RESTRICTED
        )

    def permits_training(self) -> bool:
        return self.state == RightsState.RIGHTS_VERIFIED_BY_POLICY

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "basis": self.basis.value,
            "basis_ref": self.basis_ref,
            "basis_resolved": self.basis_resolved,
            "basis_scope": self.basis_scope,
            "decided_utc": self.decided_utc,
            "derived_state": self.state.value,
            "permits_training": self.permits_training(),
        }


# --------------------------------------------------------------------------
# Contamination
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ContaminationRelation:
    """A typed, graded relationship between two sources.

    Direction is metadata, not immunity: an eval-side relation degrades the eval
    side, and a train-side relation degrades the train side, but either way the
    relation is *recorded* and the grade is computable from any node.
    """

    left: str
    right: str
    contamination_type: ContaminationType
    evidence_ref: str
    detected_by: str

    @property
    def grade(self) -> ContaminationClass:
        return self.contamination_type.severity

    def involves(self, source_id: str) -> bool:
        return source_id in {self.left, self.right}

    def other(self, source_id: str) -> str:
        if source_id == self.left:
            return self.right
        if source_id == self.right:
            return self.left
        raise PolicyBlocked("CONTAMINATION_EDGE_NOT_INCIDENT", f"{source_id!r} is not on this edge")

    def to_dict(self) -> dict[str, Any]:
        return {
            "left": self.left,
            "right": self.right,
            "contamination_type": self.contamination_type.value,
            "grade": self.grade.value,
            "evidence_ref": self.evidence_ref,
            "detected_by": self.detected_by,
        }


@dataclass(frozen=True)
class ContaminationGraph:
    relations: tuple[ContaminationRelation, ...]

    def edges_for(self, source_id: str) -> tuple[ContaminationRelation, ...]:
        return tuple(r for r in self.relations if r.involves(source_id))

    def worst_grade(self, source_id: str) -> ContaminationClass:
        """Worst observed grade incident to a source; absence is not cleanliness."""

        edges = self.edges_for(source_id)
        if not edges:
            return ContaminationClass.C0_NO_OBSERVED_OVERLAP
        return max(edges, key=lambda r: CONTAMINATION_SEVERITY[r.grade]).grade

    def grade_between(self, left: str, right: str) -> ContaminationClass:
        matching = [r for r in self.relations if {r.left, r.right} == {left, right}]
        if not matching:
            return ContaminationClass.C0_NO_OBSERVED_OVERLAP
        return max(matching, key=lambda r: CONTAMINATION_SEVERITY[r.grade]).grade

    def claim_blocking_edges(self, source_id: str) -> tuple[ContaminationRelation, ...]:
        return tuple(
            r for r in self.edges_for(source_id) if r.grade in CLAIM_DEGRADING_CONTAMINATION
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "relations": [r.to_dict() for r in self.relations],
            "edge_count": len(self.relations),
            "unobserved_overlap_is_not_cleanliness": True,
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


# --------------------------------------------------------------------------
# Source records
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceRecord:
    """A registered data source. Registration is *not* a cleanliness claim."""

    source_id: str
    title: str
    locator: str
    source_family: str
    payload_class: str
    observed_utc: str
    event_time_start: str | None
    event_time_end: str | None
    known_at_utc: str | None
    upstream_ancestry: str
    upstream_provenance_known: bool
    integrity_digest: str
    record_count: int
    trust_class: TrustClass
    rights: RightsDisposition
    role: SourceRole
    secret_bearing: bool = False
    synthetic: bool = False
    synthetic_of: tuple[str, ...] = ()
    mirror_of: str | None = None
    lineage_key: str | None = None
    contains_prohibited_payload_classes: tuple[str, ...] = ()
    doctrine_shape_tokens: tuple[str, ...] = ()
    notes: str = ""

    @property
    def authoritative_lineage(self) -> str:
        """Alias/mirror copies collapse onto one lineage: fake diversity is not diversity."""

        return self.lineage_key or self.mirror_of or self.upstream_ancestry or self.source_id

    def rights_state(self) -> RightsState:
        return self.rights.state

    def trainable(self) -> bool:
        """Rights alone permit training. Role may still forbid it."""

        from .boundary import rights_permit_training

        return rights_permit_training(self.rights.state)

    def role_permits_training(self) -> bool:
        return self.role in {
            SourceRole.TRAIN_CPT,
            SourceRole.TRAIN_SFT,
            SourceRole.TRAIN_PREFERENCE,
        }

    def eligible_for_training(self) -> bool:
        """Both rights and role must allow it; either alone is insufficient."""

        return self.trainable() and self.role_permits_training()

    def carries_withheld_doctrine(self) -> bool:
        return bool(
            set(self.contains_prohibited_payload_classes)
            & set(CEREBUS_FAMILY_PROHIBITED_PAYLOAD_CLASSES)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "locator": self.locator,
            "source_family": self.source_family,
            "payload_class": self.payload_class,
            "observed_utc": self.observed_utc,
            "event_time_start": self.event_time_start,
            "event_time_end": self.event_time_end,
            "known_at_utc": self.known_at_utc,
            "upstream_ancestry": self.upstream_ancestry,
            "upstream_provenance_known": self.upstream_provenance_known,
            "integrity_digest": self.integrity_digest,
            "record_count": self.record_count,
            "trust_class": self.trust_class.value,
            "rights": self.rights.to_dict(),
            "role": self.role.value,
            "secret_bearing": self.secret_bearing,
            "synthetic": self.synthetic,
            "synthetic_of": list(self.synthetic_of),
            "mirror_of": self.mirror_of,
            "lineage_key": self.authoritative_lineage,
            "contains_prohibited_payload_classes": list(self.contains_prohibited_payload_classes),
            "doctrine_shape_tokens": list(self.doctrine_shape_tokens),
            "notes": self.notes,
            "registration_is_cleanliness_claim": False,
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


# --------------------------------------------------------------------------
# Role machine
# --------------------------------------------------------------------------


#: Transitions that require a *new* rights disposition (new evidence), because
#: the new role grants powers the old one did not.
ROLE_TRANSITIONS_REQUIRING_RIGHTS_REVERIFICATION: frozenset[tuple[SourceRole, SourceRole]] = frozenset(
    {
        (SourceRole.RETRIEVAL_ONLY, SourceRole.TRAIN_CPT),
        (SourceRole.RETRIEVAL_ONLY, SourceRole.TRAIN_SFT),
        (SourceRole.RETRIEVAL_ONLY, SourceRole.TRAIN_PREFERENCE),
        (SourceRole.DEV, SourceRole.TRAIN_CPT),
        (SourceRole.DEV_EVAL, SourceRole.TRAIN_CPT),
        (SourceRole.PUBLIC_EVAL, SourceRole.TRAIN_CPT),
        (SourceRole.PROMOTION_EVAL, SourceRole.TRAIN_CPT),
        (SourceRole.HIDDEN_EVAL, SourceRole.TRAIN_CPT),
        (SourceRole.SEALED_CONFIRMATION, SourceRole.TRAIN_CPT),
        (SourceRole.BLIND_DISCOVERY, SourceRole.TRAIN_CPT),
        (SourceRole.QUARANTINED, SourceRole.TRAIN_CPT),
    }
)


def assert_role_transition_allowed(
    previous: SourceRole,
    requested: SourceRole,
    *,
    rights: RightsDisposition,
    actor: str,
    human_review_ref: str | None = None,
) -> None:
    """Role transitions create history and cannot silently launder restrictions."""

    if requested == previous:
        raise PolicyBlocked(
            "ROLE_TRANSITION_NOOP",
            "a role transition must change the role; no-op transitions pollute provenance",
        )
    if requested in {
        SourceRole.TRAIN_CPT,
        SourceRole.TRAIN_SFT,
        SourceRole.TRAIN_PREFERENCE,
    }:
        from .boundary import rights_permit_training

        if not rights_permit_training(rights.state):
            raise PolicyBlocked(
                "RIGHTS_BLOCKED",
                f"role {requested.value} requires a rights disposition permitting training",
                rights_state=rights.state.value,
            )
    if (previous, requested) in ROLE_TRANSITIONS_REQUIRING_RIGHTS_REVERIFICATION:
        if not human_review_ref:
            raise PolicyBlocked(
                "ROLE_LAUNDERING_REFUSED",
                (
                    f"{previous.value} -> {requested.value} expands data powers and requires "
                    "explicit review evidence, not a role edit"
                ),
            )
    if requested is SourceRole.EXCLUDED and previous is SourceRole.SEALED_CONFIRMATION:
        raise PolicyBlocked(
            "SEALED_ROLE_RETIREMENT_REQUIRES_OPERATOR",
            "sealed confirmation material may only be retired through the operator",
        )


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------


@dataclass
class SourceRegistry:
    """Versioned source registry with role history and provenance-preserving edits."""

    double: OceTestDouble = field(default=DATA_DOUBLE)
    _registry: VersionedRegistry = field(init=False)
    _role_history: dict[str, list[tuple[SourceRole, str, str, str | None]]] = field(
        default_factory=dict, init=False
    )

    def __post_init__(self) -> None:
        self._registry = VersionedRegistry("source_registry", self.double)

    def register(self, record: SourceRecord, *, actor: str, reason: str) -> Any:
        if not record.integrity_digest.strip():
            raise PolicyBlocked(
                "SOURCE_INTEGRITY_DIGEST_REQUIRED",
                f"{record.source_id}: a source without an integrity digest cannot be registered",
            )
        if record.secret_bearing and record.role in {
            SourceRole.TRAIN_CPT,
            SourceRole.TRAIN_SFT,
            SourceRole.TRAIN_PREFERENCE,
        }:
            raise PolicyBlocked(
                "SECRET_BEARING_SOURCE_TRAIN_ROLE_REFUSED",
                f"{record.source_id}: secret-bearing material cannot hold a training role",
            )
        entry = self._registry.put(record.source_id, record, actor=actor, reason=reason)
        self._role_history.setdefault(record.source_id, []).append(
            (record.role, reason, actor, None)
        )
        return entry

    def get(self, source_id: str) -> SourceRecord:
        return self._registry.get(source_id)

    def resolve(self, source_id: str) -> bool:
        return self._registry.resolve(source_id)

    def history(self, source_id: str) -> tuple[Any, ...]:
        return self._registry.history(source_id)

    def role_history(self, source_id: str) -> tuple[tuple[SourceRole, str, str, str | None], ...]:
        return tuple(self._role_history.get(source_id, ()))

    def version(self, source_id: str) -> int:
        """How many versions of this source exist; a change never overwrites."""

        return self._registry.version(source_id)

    def source_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._registry.keys()))

    def transition_role(
        self,
        source_id: str,
        requested: SourceRole,
        *,
        actor: str,
        reason: str,
        human_review_ref: str | None = None,
        rights: RightsDisposition | None = None,
    ) -> SourceRecord:
        import dataclasses

        current = self.get(source_id)
        effective_rights = rights or current.rights
        assert_role_transition_allowed(
            current.role,
            requested,
            rights=effective_rights,
            actor=actor,
            human_review_ref=human_review_ref,
        )
        updated = dataclasses.replace(current, role=requested, rights=effective_rights)
        self._registry.put(source_id, updated, actor=actor, reason=reason)
        self._role_history.setdefault(source_id, []).append(
            (requested, reason, actor, human_review_ref)
        )
        return updated

    def digest(self) -> str:
        return self._registry.digest()

    def role_distribution(self) -> dict[str, int]:
        distribution: dict[str, int] = {}
        for source_id in self.source_ids():
            role = self.get(source_id).role.value
            distribution[role] = distribution.get(role, 0) + 1
        return distribution

    # -- derived views ----------------------------------------------------

    def lineage_of(self, source_id: str, *, _depth: int = 0) -> str:
        """Resolve a source to its authoritative lineage, following mirror aliases.

        A mirror of a mirror still resolves to one lineage; copies therefore
        cannot manufacture diversity by being registered repeatedly.
        """

        if _depth > 8:
            raise PolicyBlocked(
                "MIRROR_CHAIN_TOO_DEEP",
                f"mirror chain from {source_id!r} exceeds the resolution bound",
            )
        record = self.get(source_id)
        if record.lineage_key:
            return record.lineage_key
        if record.mirror_of:
            if not self.resolve(record.mirror_of):
                raise PolicyBlocked(
                    "MIRROR_TARGET_UNRESOLVED",
                    f"{source_id!r} mirrors unresolved source {record.mirror_of!r}",
                )
            return self.lineage_of(record.mirror_of, _depth=_depth + 1)
        return record.upstream_ancestry or source_id

    def effective_diversity(self, source_ids: list[str] | None = None) -> dict[str, Any]:
        """Aliases, mirrors, and copies do not manufacture source diversity."""

        ids = source_ids if source_ids is not None else list(self.source_ids())
        families: dict[str, set[str]] = {}
        lineages: set[str] = set()
        for source_id in ids:
            record = self.get(source_id)
            lineage = self.lineage_of(source_id)
            families.setdefault(record.source_family, set()).add(lineage)
            lineages.add(lineage)
        collapsed = sorted(
            source_id
            for source_id in ids
            if self.get(source_id).mirror_of or self.get(source_id).lineage_key
        )
        return {
            "requested_sources": len(ids),
            "effective_lineages": len(lineages),
            "distinct_families": len(families),
            "families_with_multiple_lineages": sorted(
                family for family, lin in families.items() if len(lin) > 1
            ),
            "collapsed_aliases": collapsed,
            "diversity_is_claimed_not_effective": len(collapsed) > 0,
            "lineage_map": {source_id: self.lineage_of(source_id) for source_id in ids},
        }

    def trainable_sources(self) -> tuple[str, ...]:
        """Sources that are eligible: rights permit training *and* the role allows it."""

        return tuple(
            source_id
            for source_id in self.source_ids()
            if self.get(source_id).eligible_for_training()
        )

    def rights_permissive_but_role_forbidden(self) -> dict[str, str]:
        """Permissions are not roles: this is where that difference becomes visible."""

        return {
            source_id: self.get(source_id).role.value
            for source_id in self.source_ids()
            if self.get(source_id).trainable()
            and not self.get(source_id).role_permits_training()
        }

    def rights_blocked_sources(self) -> dict[str, str]:
        """Every registered source whose rights do NOT authorize training."""

        blocked = {}
        for source_id in self.source_ids():
            record = self.get(source_id)
            if not record.trainable():
                blocked[source_id] = record.rights_state().value
        return blocked

    def doctrine_bearing_sources(self) -> tuple[str, ...]:
        return tuple(
            source_id
            for source_id in self.source_ids()
            if self.get(source_id).carries_withheld_doctrine()
        )

    def assert_doctrine_withheld(self, source_id: str) -> None:
        """CEREBUS-family material is withheld from every model-facing path."""

        record = self.get(source_id)
        if record.carries_withheld_doctrine():
            raise PolicyBlocked(
                "CEREBUS_FAMILY_WITHHELD",
                f"{source_id} carries withheld doctrine and cannot enter model-facing paths",
                payload_classes=list(record.contains_prohibited_payload_classes),
            )

    def assert_no_doctrine_leak(self, source_ids: list[str]) -> None:
        for source_id in source_ids:
            self.assert_doctrine_withheld(source_id)

    def provenance_summary(self, source_ids: list[str]) -> dict[str, Any]:
        """Unknown provenance reduces claim strength; it never silently passes."""

        unknown = [
            source_id for source_id in source_ids if not self.get(source_id).upstream_provenance_known
        ]
        return {
            "sources": len(source_ids),
            "unknown_ancestry_sources": sorted(unknown),
            "claim_strength_penalty": bool(unknown),
            "unknown_is_not_favorable": True,
        }


def fixture_registry(*records: SourceRecord) -> SourceRegistry:
    registry = SourceRegistry()
    for record in records:
        registry.register(record, actor="mf-b2-fixture", reason="fixture load")
    return registry


__all__ = [
    "CEREBUS_FAMILY_PROHIBITED_PAYLOAD_CLASSES",
    "DATA_DOUBLE",
    "ROLE_TRANSITIONS_REQUIRING_RIGHTS_REVERIFICATION",
    "ContaminationGraph",
    "ContaminationRelation",
    "RightsDisposition",
    "SourceRecord",
    "SourceRegistry",
    "assert_role_transition_allowed",
    "fixture_registry",
]
