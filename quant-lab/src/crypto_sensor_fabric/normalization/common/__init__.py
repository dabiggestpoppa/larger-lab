"""SENSOR-B5-I08E1 - common units / numeric / stablecoin conversion surface.

The ``common/`` package (bloc_05/03 §21) as scoped by the I08E1 directive
and the I08-Q1 split recorded in ``BLOC_05_I08_IMPLEMENTATION_EVIDENCE.md``:

* ``units`` -- the frozen 13-unit quantity vocabulary and the asset-identity
  law (§4);
* ``numeric`` -- the §3 precision policy: precision declared, widening
  measured, rounding absent;
* ``conversion`` -- the §9/§10 stablecoin-fiat + cross-currency conversion
  over caller-supplied PIT rate evidence (depeg-preserving, fail-closed).

Deliberately ABSENT from this package (06 §19 ownership, I08-Q1):

* ``methodologies.py`` / ``semantic_registry.py`` -- I09's "methodology +
  semantic-equivalence registries";
* ``envelope.py`` -- bloc_05/03 §2's full ``T1ObservationEnvelope`` needs
  methodology identity owned by I09, so the frozen-name composite stays
  unexported exactly as the I01 base layer records;
* ``comparability.py`` (§18 gate, needs I09 equivalence classes) and
  ``missingness.py`` (the §14 null/zero laws already live in the I01 base
  models and enums).

Only the symbols below are public contract for this package.  The top-level
``crypto_sensor_fabric.normalization`` surface stays the ratified 24 I01
symbols; I08 names are reached only through ``...normalization.common``.

No network, no wall clock, no filesystem access: value in, answer out.
"""

from __future__ import annotations

from .conversion import (
    METHODOLOGY_VERSION,
    ConversionRateObservation,
    CrossCurrencyResult,
    StablecoinConversionResult,
    convert_stablecoin_to_usd,
    cross_convert_via_usd,
)
from .numeric import (
    PrecisionRecord,
    decimal_places,
    precision_widened,
)
from .units import (
    ASSET_IDENTITY_REQUIRED,
    SELF_IDENTIFYING,
    CanonicalQuantityUnit,
    QuantityUnitIdentity,
)

__all__ = [
    "ASSET_IDENTITY_REQUIRED",
    "METHODOLOGY_VERSION",
    "SELF_IDENTIFYING",
    "CanonicalQuantityUnit",
    "ConversionRateObservation",
    "CrossCurrencyResult",
    "PrecisionRecord",
    "QuantityUnitIdentity",
    "StablecoinConversionResult",
    "convert_stablecoin_to_usd",
    "cross_convert_via_usd",
    "decimal_places",
    "precision_widened",
]
