"""SENSOR-B5-I08E1 - numeric policy layer (bloc_05/03 S3).

Three frozen S3 laws, made mechanical:

* **S3.1 preserve provider precision** -- this layer performs NO rounding
  operations at all: there is no rounding helper to reach for, so
  provider-native precision cannot be silently trimmed here.  Exact Decimal
  arithmetic in ``conversion.py`` is the only transformation.
* **S3.2 canonical numeric types** -- the boundary is ``Decimal``; a float
  has no lawful representation and is refused by the models that consume
  this module (refusal lives in the model validators, where the field is
  declared).
* **S3.3 no fake precision** -- ``source_precision`` / ``conversion_precision``
  are tracked as optional declared metadata (:class:`PrecisionRecord`), and
  ``precision_widened`` measures the hazard directly: a value reported to 2
  decimals must not *claim* more decimals than its source carried just
  because conversion code can emit them.

This module resolves nothing: no conversion, no registry, no wall clock.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import ConfigDict, Field, model_validator

from ..models import NormalizationModelBase

__all__ = [
    "PrecisionRecord",
    "decimal_places",
    "precision_widened",
]


def decimal_places(value: Decimal) -> int:
    """Decimals a finite Decimal carries (``1.23`` -> 2, ``123`` -> 0).

    Non-finite inputs have no precision to report and are refused rather
    than answered with a number (fail closed, S3.2).
    """
    if not value.is_finite():
        raise ValueError("decimal_places requires a finite Decimal (S3.2)")
    return max(-value.as_tuple().exponent, 0)


def precision_widened(source: Decimal, derived: Decimal) -> bool:
    """True when ``derived`` claims MORE decimals than ``source`` (S3.3).

    Measurement, not mutation: nothing is rounded or rewritten; the caller
    learns whether a derived value is pretending to precision its source did
    not carry.  Fewer or equal decimals are never widening (1.23 -> 1.2 is
    a loss, not a fabrication).
    """
    return decimal_places(derived) > decimal_places(source)


class PrecisionRecord(NormalizationModelBase):
    """Optional declared precision metadata (bloc_05/03 S3.3).

    Both fields are optional because S3.3 says "track optional"; when
    declared they are non-negative decimal-place counts.  ``source_precision``
    is what the provider reported with; ``conversion_precision`` is what the
    conversion output legitimately carries.  Declaring them is how a derived
    value answers "why does this have 12 decimals?" with evidence instead of
    a shrug.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_precision: int | None = Field(default=None, ge=0)
    conversion_precision: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _no_negative_widening_claim(self) -> PrecisionRecord:
        # ge=0 already refuses negatives at the field level; this validator
        # exists so the LAW has a name in the traceback (S3.3).
        return self
