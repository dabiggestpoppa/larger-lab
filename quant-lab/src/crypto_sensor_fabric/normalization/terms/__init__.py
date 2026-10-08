"""SENSOR-B5-I04A - Bloc 5 point-in-time contract terms boundary.

The I04-specific terms subpackage: an immutable :class:`ContractTermsSnapshot`
projection of accepted ``ContractInstance``/``EconomicContract`` terms (D1)
and the pure :func:`project_contract_terms` eligibility/verification gate
(D2).  This package deliberately owns NO conversion math (linear/inverse
primitives are I04B+), NO common-unit or stablecoin conversion (I08 owns
``normalization/common/``), NO identity resolution (I03 owns ``identity/``),
and NO time-semantics registry (I05).  The top-level normalization surface
stays exactly the 24 ratified B5-I01 public symbols: these names are reached
only through ``crypto_sensor_fabric.normalization.terms``.

Plan citations use the compact S<n> form for bloc_05/01 section <n>.
"""

from __future__ import annotations

from .projection import project_contract_terms
from .snapshot import ContractTermsSnapshot

__all__ = [
    "ContractTermsSnapshot",
    "project_contract_terms",
]
