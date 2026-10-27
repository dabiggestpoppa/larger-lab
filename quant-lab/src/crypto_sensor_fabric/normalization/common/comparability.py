"""SENSOR-B5-I09 - the library-level cross-provider comparability gate (03 §18).

bloc_05/03 §18 verbatim: "Before two normalized fields can be compared,
validate" the eight conditions, and "this gate belongs in the canonical
library so research cannot bypass it casually."  Ownership is settled by the
I09E1 directive BOOK 00 Q3: **I09 implements the library-level gate**, I19
retains canonical query-time application, I21 retains property/regression
validation.

Design laws:

* **It is a predicate, never a synthesis (07 F24, 03 §20).**  The decision
  object carries admissibility and reasons only -- no value, no merged record,
  no consensus.  Two venues' fields may be *comparable*; that is not a
  licence to pool them, and pooling remains the upstream ``is_poolable`` law
  plus Bloc 6 eligibility.
* **Condition 8 delegates, it does not re-derive (Q3 non-duplication).**
  ``EQUIVALENCE_CLASS_PERMITS_COMPARISON`` is answered by the ratified Bloc 1
  ``is_poolable`` predicate, imported from
  ``registry/semantic_equivalence.py``.  There is no second pooling table in
  this package, and the gate cannot drift from the accepted law.
* **Facts are declared, never fetched.**  The caller (canonical library, I19)
  supplies each side's declared facts; a missing fact is a REFUSAL with a
  reason, never an exception and never a default (06 §1 G9).
* **Fail-closed postures for the carried I08 limitations (BOOK 00 Q8).**  The
  gate computes no numbers (L1), refuses an asset-required unit without
  declared asset identity (L2), trusts no ambient state, treats an
  unclassified interval convention as a refusal (L3/L5 posture), and requires
  venue scope and identity resolution to be declared rather than assumed
  (L6/L7).  No ``common/conversion.py`` behaviour is changed.
* **A refusal is typed (05 §12, readiness §6).**  A refused comparison names
  its ``MissingnessReason`` -- semantics, conversion, identity or quarantine
  -- so a blocked comparison stays distinguishable from a verified zero and
  from a generic ``missing=true``.
"""

from __future__ import annotations

from enum import Enum

from pydantic import ConfigDict, Field

from ...contracts.enums import SemanticEquivalence, SensorFamily
from ...registry.semantic_equivalence import is_poolable
from ..enums import BLOCKING_QUALITY_FLAGS, MissingnessReason, NormalizationQualityFlag
from ..models import NormalizationModelBase
from .units import ASSET_IDENTITY_REQUIRED, SELF_IDENTIFYING, CanonicalQuantityUnit
from .semantic_registry import IntervalDataScope

__all__ = [
    "ComparableFieldFacts",
    "ComparabilityCondition",
    "ComparabilityDecision",
    "ConditionVerdict",
    "evaluate_comparability",
]


class _StrEnum(str, Enum):
    """Deterministic string-valued enum base (values equal member names)."""


class ComparabilityCondition(_StrEnum):
    """The eight bloc_05/03 §18 conditions, in frozen document order."""

    SENSOR_FAMILY_SAME = "SENSOR_FAMILY_SAME"
    ECONOMIC_DEFINITION_COMPATIBLE = "ECONOMIC_DEFINITION_COMPATIBLE"
    INTERVAL_SEMANTICS_COMPATIBLE = "INTERVAL_SEMANTICS_COMPATIBLE"
    UNITS_COMPATIBLE_AFTER_EXPLICIT_CONVERSION = (
        "UNITS_COMPATIBLE_AFTER_EXPLICIT_CONVERSION"
    )
    VENUE_SCOPE_KNOWN = "VENUE_SCOPE_KNOWN"
    IDENTITY_RESOLVED = "IDENTITY_RESOLVED"
    NO_BLOCKING_QUALITY_FLAGS = "NO_BLOCKING_QUALITY_FLAGS"
    EQUIVALENCE_CLASS_PERMITS_COMPARISON = "EQUIVALENCE_CLASS_PERMITS_COMPARISON"


class ComparableFieldFacts(NormalizationModelBase):
    """One side's DECLARED comparability facts.

    The gate interprets facts; it never fetches, infers or defaults them.
    Unset fields are how a caller says "not established", and every condition
    that needs an unset field refuses.  ``identity_resolved`` defaults to
    ``False`` and ``conversion_registered`` to ``False`` so a careless caller
    fails closed rather than open.

    ``conversion_registered``/``conversion_methodology_id`` describe the
    conversion THIS side's value would undergo to reach the other side's
    unit; a registered conversion must name the methodology that backs it.
    ``quality_flags`` are the I01 canonical flags; the gate intersects them
    with the ratified ``BLOCKING_QUALITY_FLAGS`` set (reused, never forked).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str = Field(min_length=1)
    sensor_family: SensorFamily | None = None
    canonical_field: str | None = Field(default=None, min_length=1)
    economic_definition: str | None = Field(default=None, min_length=1)
    interval_data_scope: IntervalDataScope | None = None
    unit: CanonicalQuantityUnit | None = None
    asset_id: str | None = Field(default=None, min_length=1)
    conversion_registered: bool = False
    conversion_methodology_id: str | None = Field(default=None, min_length=1)
    venue_scope: str | None = Field(default=None, min_length=1)
    identity_resolved: bool = False
    quality_flags: frozenset[NormalizationQualityFlag] = Field(default_factory=frozenset)
    equivalence_class: SemanticEquivalence | None = None


class ConditionVerdict(NormalizationModelBase):
    """One condition's verdict with its reason (never an empty reason)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    condition: ComparabilityCondition
    satisfied: bool
    reason: str = Field(min_length=1)


class ComparabilityDecision(NormalizationModelBase):
    """The gate's only output: admissibility, verdicts and a typed cause.

    By construction this object can carry no value and no merged record --
    there is no field in which a synthesized number could ever live (07 F24).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    admitted: bool
    verdicts: tuple[ConditionVerdict, ...]
    refused_conditions: tuple[ComparabilityCondition, ...]
    missingness_reason: MissingnessReason | None = None


#: The typed cause of a refusal, by the first refused condition in frozen
#: order (readiness §6: a semantic decision blocks a value by naming WHY).
_CONDITION_CAUSE: dict[ComparabilityCondition, MissingnessReason] = {
    ComparabilityCondition.SENSOR_FAMILY_SAME: MissingnessReason.SEMANTICS_BLOCKED,
    ComparabilityCondition.ECONOMIC_DEFINITION_COMPATIBLE: (
        MissingnessReason.SEMANTICS_BLOCKED
    ),
    ComparabilityCondition.INTERVAL_SEMANTICS_COMPATIBLE: (
        MissingnessReason.SEMANTICS_BLOCKED
    ),
    ComparabilityCondition.UNITS_COMPATIBLE_AFTER_EXPLICIT_CONVERSION: (
        MissingnessReason.CONVERSION_BLOCKED
    ),
    ComparabilityCondition.VENUE_SCOPE_KNOWN: MissingnessReason.SEMANTICS_BLOCKED,
    ComparabilityCondition.IDENTITY_RESOLVED: MissingnessReason.IDENTITY_BLOCKED,
    ComparabilityCondition.NO_BLOCKING_QUALITY_FLAGS: (
        MissingnessReason.SEMANTICS_BLOCKED
    ),  # refined below by the intersecting flag's class
    ComparabilityCondition.EQUIVALENCE_CLASS_PERMITS_COMPARISON: (
        MissingnessReason.SEMANTICS_BLOCKED
    ),
}

#: Condition 7 refinement: which typed cause a blocking flag implies, in
#: deterministic priority order (identity > time > semantics > conversion >
#: lineage/quarantine).
_FLAG_CAUSE_PRIORITY: tuple[tuple[frozenset[NormalizationQualityFlag], MissingnessReason], ...] = (
    (
        frozenset(
            {
                NormalizationQualityFlag.IDENTITY_AMBIGUOUS,
                NormalizationQualityFlag.IDENTITY_TERMS_UNVERIFIED,
            }
        ),
        MissingnessReason.IDENTITY_BLOCKED,
    ),
    (
        frozenset(
            {
                NormalizationQualityFlag.TIME_SEMANTICS_UNVERIFIED,
                NormalizationQualityFlag.TIME_MARKET_AVAILABILITY_UNKNOWN,
            }
        ),
        MissingnessReason.TIME_BLOCKED,
    ),
    (
        frozenset({NormalizationQualityFlag.SEMANTICS_UNVERIFIED}),
        MissingnessReason.SEMANTICS_BLOCKED,
    ),
    (
        frozenset(
            {
                NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED,
                NormalizationQualityFlag.STABLECOIN_CONVERSION_UNAVAILABLE,
                NormalizationQualityFlag.REFERENCE_PRICE_UNAVAILABLE,
            }
        ),
        MissingnessReason.CONVERSION_BLOCKED,
    ),
    (
        frozenset({NormalizationQualityFlag.LINEAGE_BROKEN}),
        MissingnessReason.QUARANTINED,
    ),
)


def _blocking_flags(
    flags: frozenset[NormalizationQualityFlag],
) -> list[NormalizationQualityFlag]:
    return sorted(flags & BLOCKING_QUALITY_FLAGS, key=lambda flag: flag.value)


def _flag_cause(
    flags: frozenset[NormalizationQualityFlag],
) -> MissingnessReason:
    blocked = flags & BLOCKING_QUALITY_FLAGS
    for candidates, cause in _FLAG_CAUSE_PRIORITY:
        if blocked & candidates:
            return cause
    return MissingnessReason.SEMANTICS_BLOCKED


def _sensor_family_verdict(
    left: ComparableFieldFacts, right: ComparableFieldFacts
) -> ConditionVerdict:
    condition = ComparabilityCondition.SENSOR_FAMILY_SAME
    if left.sensor_family is None or right.sensor_family is None:
        return ConditionVerdict(
            condition=condition,
            satisfied=False,
            reason="sensor family is not declared on both sides; the comparison "
            "cannot be asserted (fail closed)",
        )
    if left.sensor_family is not right.sensor_family:
        return ConditionVerdict(
            condition=condition,
            satisfied=False,
            reason=f"sensor families differ: {left.label}={left.sensor_family.value}, "
            f"{right.label}={right.sensor_family.value}",
        )
    return ConditionVerdict(
        condition=condition,
        satisfied=True,
        reason=f"both sides are {left.sensor_family.value}",
    )


def _economic_definition_verdict(
    left: ComparableFieldFacts, right: ComparableFieldFacts
) -> ConditionVerdict:
    condition = ComparabilityCondition.ECONOMIC_DEFINITION_COMPATIBLE
    if left.economic_definition is None or right.economic_definition is None:
        return ConditionVerdict(
            condition=condition,
            satisfied=False,
            reason="the economic definition is not stated on both sides; a "
            "comparison of undefined quantities is refused",
        )
    if left.canonical_field is None or right.canonical_field is None:
        return ConditionVerdict(
            condition=condition,
            satisfied=False,
            reason="the canonical field is not declared on both sides",
        )
    if left.canonical_field != right.canonical_field:
        return ConditionVerdict(
            condition=condition,
            satisfied=False,
            reason=f"canonical fields differ: {left.canonical_field!r} vs "
            f"{right.canonical_field!r}; the sides are not the same economic quantity",
        )
    return ConditionVerdict(
        condition=condition,
        satisfied=True,
        reason=f"both sides state the same canonical quantity {left.canonical_field!r} "
        "with their native definitions",
    )


def _interval_semantics_verdict(
    left: ComparableFieldFacts, right: ComparableFieldFacts
) -> ConditionVerdict:
    condition = ComparabilityCondition.INTERVAL_SEMANTICS_COMPATIBLE
    for side in (left, right):
        if side.interval_data_scope is None:
            return ConditionVerdict(
                condition=condition,
                satisfied=False,
                reason=f"{side.label}: interval/cumulative semantics are not declared",
            )
        if side.interval_data_scope is IntervalDataScope.PROVIDER_NATIVE_UNKNOWN:
            return ConditionVerdict(
                condition=condition,
                satisfied=False,
                reason=f"{side.label}: interval semantics are PROVIDER_NATIVE_UNKNOWN; "
                "an unclassified convention is a refusal, never a compatibility "
                "(bloc_05/02 §7)",
            )
    left_scope = left.interval_data_scope
    right_scope = right.interval_data_scope
    if left_scope is None or right_scope is None:
        raise AssertionError("unreachable: the loop above refuses undeclared scopes")
    if left_scope is not right_scope:
        return ConditionVerdict(
            condition=condition,
            satisfied=False,
            reason=f"interval semantics differ: {left.label}="
            f"{left_scope.value}, {right.label}="
            f"{right_scope.value} (a cumulative counter is not an "
            "interval aggregate; a snapshot is not a window)",
        )
    return ConditionVerdict(
        condition=condition,
        satisfied=True,
        reason=f"both sides are {left_scope.value}",
    )


def _units_verdict(
    left: ComparableFieldFacts, right: ComparableFieldFacts
) -> ConditionVerdict:
    condition = ComparabilityCondition.UNITS_COMPATIBLE_AFTER_EXPLICIT_CONVERSION
    if left.unit is None or right.unit is None:
        return ConditionVerdict(
            condition=condition,
            satisfied=False,
            reason="unit is not declared on both sides",
        )
    # 03 §4 asset-identity completeness (and the carried L2 posture): an
    # asset-required unit without declared asset identity is incomplete, and a
    # self-identifying unit beside a second identity is a contradiction.
    for side in (left, right):
        if side.unit in ASSET_IDENTITY_REQUIRED and side.asset_id is None:
            return ConditionVerdict(
                condition=condition,
                satisfied=False,
                reason=f"{side.label}: unit {side.unit.value} carries no asset "
                "identity; '1000 BASE_ASSET' without BTC/ETH identity is incomplete "
                "(bloc_05/03 §4)",
            )
        if side.unit in SELF_IDENTIFYING and side.asset_id is not None:
            return ConditionVerdict(
                condition=condition,
                satisfied=False,
                reason=f"{side.label}: unit {side.unit.value} is its own identity; a "
                "second asset identity beside it is a contradiction (03 §22 inv.3)",
            )
    if left.unit is right.unit:
        if (
            left.unit in ASSET_IDENTITY_REQUIRED
            and left.asset_id != right.asset_id
        ):
            return ConditionVerdict(
                condition=condition,
                satisfied=False,
                reason=f"same unit token {left.unit.value} but different asset "
                f"identity: {left.asset_id!r} vs {right.asset_id!r}",
            )
        return ConditionVerdict(
            condition=condition,
            satisfied=True,
            reason=f"both sides are {left.unit.value}; no conversion is required",
        )
    declaring = [side for side in (left, right) if side.conversion_registered]
    if not declaring:
        return ConditionVerdict(
            condition=condition,
            satisfied=False,
            reason=f"units differ ({left.unit.value} vs {right.unit.value}) and no "
            "explicit registered conversion is declared; compatibility is never "
            "assumed from similar-looking units",
        )
    for side in declaring:
        if side.conversion_methodology_id is None:
            return ConditionVerdict(
                condition=condition,
                satisfied=False,
                reason=f"{side.label}: a conversion is registered without a "
                "methodology id; every derived amount needs methodology + lineage "
                "(06 §1 G5)",
            )
    return ConditionVerdict(
        condition=condition,
        satisfied=True,
        reason=f"units differ ({left.unit.value} vs {right.unit.value}); an explicit "
        f"registered conversion is declared by {', '.join(side.label for side in declaring)} "
        "under a named methodology",
    )


def _venue_scope_verdict(
    left: ComparableFieldFacts, right: ComparableFieldFacts
) -> ConditionVerdict:
    condition = ComparabilityCondition.VENUE_SCOPE_KNOWN
    for side in (left, right):
        if side.venue_scope is None:
            return ConditionVerdict(
                condition=condition,
                satisfied=False,
                reason=f"{side.label}: venue scope is not declared; T1 stays "
                "provider/venue explicit (07 F24)",
            )
    return ConditionVerdict(
        condition=condition,
        satisfied=True,
        reason=f"venue scope declared: {left.label}={left.venue_scope}, "
        f"{right.label}={right.venue_scope}",
    )


def _identity_verdict(
    left: ComparableFieldFacts, right: ComparableFieldFacts
) -> ConditionVerdict:
    condition = ComparabilityCondition.IDENTITY_RESOLVED
    for side in (left, right):
        if not side.identity_resolved:
            return ConditionVerdict(
                condition=condition,
                satisfied=False,
                reason=f"{side.label}: identity is not resolved; comparability cannot "
                "be asserted over unresolved identity (readiness §10 stop 8)",
            )
    return ConditionVerdict(
        condition=condition,
        satisfied=True,
        reason="identity resolved on both sides",
    )


def _quality_flags_verdict(
    left: ComparableFieldFacts, right: ComparableFieldFacts
) -> ConditionVerdict:
    condition = ComparabilityCondition.NO_BLOCKING_QUALITY_FLAGS
    blocked: list[str] = []
    for side in (left, right):
        blocked.extend(
            f"{side.label}:{flag.value}" for flag in _blocking_flags(side.quality_flags)
        )
    if blocked:
        return ConditionVerdict(
            condition=condition,
            satisfied=False,
            reason="blocking quality flags present: " + ", ".join(sorted(blocked)),
        )
    return ConditionVerdict(
        condition=condition,
        satisfied=True,
        reason="no blocking quality flags on either side (label-only flags do not block)",
    )


def _equivalence_class_verdict(
    left: ComparableFieldFacts, right: ComparableFieldFacts
) -> ConditionVerdict:
    condition = ComparabilityCondition.EQUIVALENCE_CLASS_PERMITS_COMPARISON
    for side in (left, right):
        if side.equivalence_class is None:
            return ConditionVerdict(
                condition=condition,
                satisfied=False,
                reason=f"{side.label}: equivalence class is not declared; the class "
                "law is a requirement, never a default",
            )
    left_class = left.equivalence_class
    right_class = right.equivalence_class
    if left_class is None or right_class is None:
        raise AssertionError("unreachable: the loop above refuses undeclared classes")
    # Delegation, not re-derivation (Q3): the ratified Bloc 1 pooling law IS
    # condition 8's substance, so this gate cannot drift from it.
    if not is_poolable(left_class) or not is_poolable(right_class):
        return ConditionVerdict(
            condition=condition,
            satisfied=False,
            reason=f"equivalence class refuses cross-provider canonical comparison: "
            f"{left.label}={left_class.value}, "
            f"{right.label}={right_class.value} (CORROBORATION_ONLY and "
            "NOT_COMPARABLE never pool, B1-T42; provider-native analytics stay "
            "provider-native evidence, 07 F16)",
        )
    return ConditionVerdict(
        condition=condition,
        satisfied=True,
        reason=f"both classes permit comparison: {left.label}="
        f"{left_class.value}, {right.label}={right_class.value}",
    )


_CONDITION_EVALUATORS = (
    _sensor_family_verdict,
    _economic_definition_verdict,
    _interval_semantics_verdict,
    _units_verdict,
    _venue_scope_verdict,
    _identity_verdict,
    _quality_flags_verdict,
    _equivalence_class_verdict,
)


def evaluate_comparability(
    left: ComparableFieldFacts, right: ComparableFieldFacts
) -> ComparabilityDecision:
    """Evaluate the eight bloc_05/03 §18 conditions over two declared sides.

    Admitted only when EVERY condition is satisfied.  Never raises for a
    missing fact, never merges, never pools, never returns a value: the output
    is an admissibility decision whose refusal is a typed missingness cause.
    """
    verdicts = tuple(evaluate(left, right) for evaluate in _CONDITION_EVALUATORS)
    refused = tuple(
        verdict.condition for verdict in verdicts if not verdict.satisfied
    )
    if not refused:
        return ComparabilityDecision(
            admitted=True,
            verdicts=verdicts,
            refused_conditions=(),
            missingness_reason=None,
        )
    first = refused[0]
    if first is ComparabilityCondition.NO_BLOCKING_QUALITY_FLAGS:
        cause = _flag_cause(left.quality_flags | right.quality_flags)
    else:
        cause = _CONDITION_CAUSE[first]
    return ComparabilityDecision(
        admitted=False,
        verdicts=verdicts,
        refused_conditions=refused,
        missingness_reason=cause,
    )
