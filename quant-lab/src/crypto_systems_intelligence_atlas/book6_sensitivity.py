"""Book 6 sensitivity — methodology sensitivity and cross-source parity.

Two ratified descriptive surfaces (validation stress matrix v0.1 §6D.2, §6D.4)
that exist to make disagreement VISIBLE instead of resolved by fiat.

**Methodology sensitivity.** Two reasonable methodologies routinely yield
different measured results — "active accounts" under an EOA definition and
under a cluster definition, gross versus net volume, fees versus revenue,
native capital versus valued capital, developer contributors versus commits. The
finding here names the variants, preserves each value, and reports
``METHODOLOGY_SENSITIVE`` as descriptive metadata. It never picks a winner:
there is no ``preferred``, ``canonical``, ``best`` or ``default`` field, and
choosing one would be a Class B/C state without a ratified rule.

**Cross-source parity.** A native source, an official dashboard, an independent
indexer and a secondary analytics provider each measure the same construct
differently. Their measurements are preserved side by side. There is no
"consensus number": this module computes no mean, median or trimmed estimate, so
no averaging path exists to be taken.

**No tolerance is invented.** Deciding whether two floats "agree" needs a
tolerance, and a tolerance is a ``tolerance_ref`` on a Class C state that
requires an individually ratified rule. With zero ratified rules the only
licensed notion of agreement here is EXACT equality; everything else is reported
as divergence rather than silently smoothed.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from .book6_definitions import SourceFamily
from .book6_frozen import Book6FrozenModel
from .book6_records import MeasurementObservation
from .book6_registry import Book6MeasurementRegistry


class SensitivityError(ValueError):
    """A sensitivity or parity finding is not licensable from the inputs given."""


class SensitivityOutcome(str, Enum):
    """Descriptive outcome. Never a quality, severity or confidence reading."""

    #: Every observed variant returned exactly the same value.
    METHODOLOGY_INDEPENDENT = "METHODOLOGY_INDEPENDENT"
    #: Two or more reasonable methodologies disagree. Descriptive, not a defect.
    METHODOLOGY_SENSITIVE = "METHODOLOGY_SENSITIVE"
    #: At least one variant has no observed value, so no comparison is licensed.
    UNDETERMINED = "UNDETERMINED"


class ParityOutcome(str, Enum):
    """Descriptive cross-source outcome. Never a trust ranking."""

    SOURCES_AGREE = "SOURCES_AGREE"
    SOURCES_DIVERGE = "SOURCES_DIVERGE"
    UNDETERMINED = "UNDETERMINED"


class MethodologyVariant(Book6FrozenModel):
    """One named methodology's measurement of the same construct."""

    methodology_ref: str
    methodology_version: str
    declared_meaning: str
    measurement_id: str
    value: float | None

    @property
    def identity(self) -> str:
        return f"{self.methodology_ref}@{self.methodology_version}"


class SensitivityFinding(Book6FrozenModel):
    """What the methodologies disagree about. No winner is named."""

    subject_ref: str
    construct_label: str
    as_of_valid_time: datetime
    variants: tuple[MethodologyVariant, ...]
    outcome: SensitivityOutcome
    note: str


class SourceMeasurement(Book6FrozenModel):
    """One source family's measurement of the same construct."""

    source_family: SourceFamily
    source_ref: str
    measurement_id: str
    value: float | None
    valid_time: datetime


class SourceParityFinding(Book6FrozenModel):
    """What the sources disagree about. No consensus value is computed."""

    subject_ref: str
    construct_label: str
    as_of_valid_time: datetime
    measurements: tuple[SourceMeasurement, ...]
    outcome: ParityOutcome
    note: str


def compare_methodology_variants(
    registry: Book6MeasurementRegistry,
    *,
    subject_ref: str,
    construct_label: str,
    as_of_valid_time: datetime,
    measurement_ids: tuple[str, ...],
) -> SensitivityFinding:
    """Compare several methodologies over one construct, choosing none of them.

    Each measurement is resolved through the registry so live Book 2 authority
    governs: a variant whose cited claim has decayed contributes no value and the
    finding becomes ``UNDETERMINED`` rather than a comparison against a stale
    number.
    """

    if len(measurement_ids) < 2:
        raise SensitivityError(
            "methodology sensitivity compares at least two methodologies; a "
            "single methodology cannot be sensitive to itself"
        )
    variants: list[MethodologyVariant] = []
    for measurement_id in measurement_ids:
        observation: MeasurementObservation = registry.resolve_current(measurement_id)
        value = observation.value if observation.is_value_bearing else None
        variants.append(
            MethodologyVariant(
                methodology_ref=observation.methodology_ref,
                methodology_version=observation.methodology_version,
                declared_meaning=observation.native_scope,
                measurement_id=measurement_id,
                value=value,
            )
        )
    observed = [variant.value for variant in variants if variant.value is not None]
    if len(observed) < len(variants):
        outcome = SensitivityOutcome.UNDETERMINED
        note = (
            "at least one methodology has no observed value, so no comparison is "
            "licensed; absence is not zero and is not agreement"
        )
    elif len(set(observed)) == 1:
        outcome = SensitivityOutcome.METHODOLOGY_INDEPENDENT
        note = "all observed methodologies returned exactly the same value"
    else:
        outcome = SensitivityOutcome.METHODOLOGY_SENSITIVE
        note = (
            "reasonable methodologies disagree on this construct; the divergence "
            "is descriptive and no methodology is preferred here, because "
            "preferring one is a state derivation that requires a ratified rule"
        )
    return SensitivityFinding(
        subject_ref=subject_ref,
        construct_label=construct_label,
        as_of_valid_time=as_of_valid_time,
        variants=tuple(variants),
        outcome=outcome,
        note=note,
    )


def compare_sources(
    registry: Book6MeasurementRegistry,
    *,
    subject_ref: str,
    construct_label: str,
    as_of_valid_time: datetime,
    measurement_ids: tuple[str, ...],
) -> SourceParityFinding:
    """Preserve each source's measurement of one construct without averaging.

    Agreement is EXACT equality only. No tolerance is applied because a
    tolerance is a Class C ``tolerance_ref`` requiring an individually ratified
    rule, and none is ratified; anything short of exact equality is reported as
    divergence rather than smoothed into agreement.
    """

    if len(measurement_ids) < 2:
        raise SensitivityError(
            "cross-source parity compares at least two sources; a single source "
            "is trivially in agreement with itself"
        )
    measurements: list[SourceMeasurement] = []
    for measurement_id in measurement_ids:
        observation = registry.resolve_current(measurement_id)
        definition = registry.definition(observation.metric_definition_ref)
        value = observation.value if observation.is_value_bearing else None
        measurements.append(
            SourceMeasurement(
                source_family=definition.allowed_source_families[0],
                source_ref=(
                    observation.source_claim_refs[0] if observation.source_claim_refs else ""
                ),
                measurement_id=measurement_id,
                value=value,
                valid_time=observation.valid_time,
            )
        )
    observed = [m.value for m in measurements if m.value is not None]
    if len(observed) < len(measurements):
        outcome = ParityOutcome.UNDETERMINED
        note = (
            "at least one source has no observed value, so no parity finding is "
            "licensed; a missing source is not a source that agrees"
        )
    elif len(set(observed)) == 1:
        outcome = ParityOutcome.SOURCES_AGREE
        note = "every source returned exactly the same value under its own definition"
    else:
        outcome = ParityOutcome.SOURCES_DIVERGE
        note = (
            "sources disagree under their own definitions; the divergence is "
            "preserved and no consensus value is computed, because no ratified "
            "methodology authorises combining source families"
        )
    return SourceParityFinding(
        subject_ref=subject_ref,
        construct_label=construct_label,
        as_of_valid_time=as_of_valid_time,
        measurements=tuple(measurements),
        outcome=outcome,
        note=note,
    )


#: Canonical invariants asserted by the accepted implementation.
NO_PREFERRED_METHODOLOGY: Final[bool] = True
NO_CONSENSUS_VALUE_IS_COMPUTED: Final[bool] = True
NO_TOLERANCE_IS_INVENTED: Final[bool] = True


__all__ = [
    "MethodologyVariant",
    "NO_CONSENSUS_VALUE_IS_COMPUTED",
    "NO_PREFERRED_METHODOLOGY",
    "NO_TOLERANCE_IS_INVENTED",
    "ParityOutcome",
    "SensitivityError",
    "SensitivityFinding",
    "SensitivityOutcome",
    "SourceMeasurement",
    "SourceParityFinding",
    "compare_methodology_variants",
    "compare_sources",
]
