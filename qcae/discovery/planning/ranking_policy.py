"""Ranking vocabulary and the versioned ranking policy — canon 2.7.10/2.7.11.

Ranking is triage, not a verdict. Canon 2.7.4 is the governing sentence: a
top-ranked candidate means "inspect this first", and 2.7.16 invariant 1 repeats
that ranking "allocates investigation budget; it does not approve acquisition".

This module owns what a ranking policy *is*: the closed dimension set every
policy must weigh, the ceiling on how much popularity may ever influence order,
and the validation that makes an under-specified or popularity-heavy policy
unrepresentable. It decides nothing about how a dimension is derived, how
candidates are grouped, or how they are ordered — those live in ``scoring``,
``families`` and ``ranking``.

What this module implements:

- **Preliminary ranking dimensions (2.7.10).** The full canon dimension set, in
  canon order, as the closed vocabulary every policy and score must speak.
- **Popularity firewall (2.7.11/2.7.16 invariant 2).** Popularity enters through
  a bounded blend; this module owns the cap that keeps it from overwhelming
  semantic fit, constraints or evidence availability.
- **Auditable policy (2.7.16 invariant 7).** A versioned record that must weight
  every dimension, must not invent dimensions, and must sum semantic weights to
  1.0 — so an unauditable policy cannot be constructed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Dict, Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord
from qcae.core.validation import require_non_empty_str

__all__ = [
    "DIMENSIONS",
    "DERIVABLE_DIMENSIONS",
    "POPULARITY_WEIGHT_CAP",
    "RankingDimension",
    "RankingPolicy",
]


class RankingDimension(StrEnum):
    """Preliminary ranking dimensions (canon 2.7.10, verbatim order)."""

    SEMANTIC_FIT = "semantic_fit"
    COVERAGE_POTENTIAL = "coverage_potential"
    CONSTRAINT_FIT = "constraint_fit"
    FOCUS_EXTRACTABILITY_PRIOR = "focus_extractability_prior"
    EVIDENCE_AVAILABILITY = "evidence_availability"
    MAINTENANCE_PRIOR = "maintenance_prior"
    DEPENDENCY_PRIOR = "dependency_prior"
    LICENSE_PRIOR = "license_prior"
    NOVELTY = "novelty"
    EXPECTED_INVESTIGATION_COST = "expected_investigation_cost"
    EXPECTED_INFORMATION_GAIN = "expected_information_gain"


#: Every dimension must be scored, even when the value is a neutral prior.
DIMENSIONS: Tuple[RankingDimension, ...] = tuple(RankingDimension)

#: Canon 2.7.11: popularity may influence only a *bounded* portion of preliminary
#: ranking and must not overwhelm semantic fit, constraints or evidence
#: availability. 0.10 is the policy ceiling for that portion.
POPULARITY_WEIGHT_CAP = 0.10

#: Dimensions that are derivable from discovery observations alone. Everything
#: else is reported at the policy's neutral prior and labelled as neutral
#: (2.7.2/2.7.10): no dimension is silently invented from popularity.
DERIVABLE_DIMENSIONS: frozenset = frozenset(
    {
        RankingDimension.SEMANTIC_FIT,
        RankingDimension.COVERAGE_POTENTIAL,
        RankingDimension.CONSTRAINT_FIT,
        RankingDimension.FOCUS_EXTRACTABILITY_PRIOR,
        RankingDimension.EVIDENCE_AVAILABILITY,
        RankingDimension.NOVELTY,
        RankingDimension.EXPECTED_INVESTIGATION_COST,
        RankingDimension.EXPECTED_INFORMATION_GAIN,
    }
)


@dataclass(frozen=True)
class RankingPolicy(SerializableRecord):
    """Versioned, auditable ranking policy (canon 2.7.11, 2.7.16 invariant 7)."""

    SCHEMA_VERSION = 1

    policy_version: str
    weights: Dict[str, float]
    popularity_weight: float = 0.0
    neutral_prior: float = 0.5
    max_per_family_in_wave_one: int = 1
    max_per_source_class_in_wave_one: int = 2

    def validate(self) -> None:
        require_non_empty_str(self.policy_version, "policy_version")
        if not isinstance(self.weights, (dict, MappingProxyType)):
            raise QcaeValidationError("weights must be a mapping of dimension to weight")
        missing = sorted(d.value for d in DIMENSIONS if d.value not in self.weights)
        if missing:
            raise QcaeValidationError(
                f"ranking policy must weight every dimension; missing {missing} "
                "(canon 2.7.10)"
            )
        unknown = sorted(set(self.weights) - {d.value for d in DIMENSIONS})
        if unknown:
            raise QcaeValidationError(f"unknown ranking dimensions: {unknown}")
        total = 0.0
        for name, weight in self.weights.items():
            if not isinstance(weight, (int, float)) or isinstance(weight, bool):
                raise QcaeValidationError(f"weight {name!r} must be a number")
            if weight < 0:
                raise QcaeValidationError(f"weight {name!r} must be >= 0, got {weight!r}")
            total += float(weight)
        if abs(total - 1.0) > 1e-6:
            raise QcaeValidationError(
                f"semantic dimension weights must sum to 1.0, got {total!r}"
            )
        if not (0.0 <= float(self.popularity_weight) <= POPULARITY_WEIGHT_CAP + 1e-9):
            raise QcaeValidationError(
                f"popularity_weight must be within [0, {POPULARITY_WEIGHT_CAP}]: "
                "popularity is a weak signal that must never overwhelm semantic fit "
                "(canon 2.7.11, 2.7.16 invariant 2)"
            )
        if not (0.0 <= float(self.neutral_prior) <= 1.0):
            raise QcaeValidationError("neutral_prior must be within [0, 1]")
        for name in ("max_per_family_in_wave_one", "max_per_source_class_in_wave_one"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise QcaeValidationError(f"{name} must be an integer >= 1")
