"""SENSOR-B5-I04A - immutable point-in-time contract terms snapshot (D1).

D1 selects readiness interpretation A: this model is a PROJECTION of the
applicable, verified terms already recorded on the accepted I02
``ContractInstance`` (plus ``quote_asset_id`` from its accepted
``EconomicContract``, required by bloc_05/03 S6).  It is not an independent
terms registry: it establishes no contract existence, no canonical identity,
no economic history, and it manufactures no missing financial term.

Field inventory and authority: see
``evidence/bloc_05/BLOC_05_I04A_SCHEMA_AUTHORITY_MATRIX.json`` (generated).
Plan citations use the compact S<n> form for bloc_05/01 section <n>.

Laws (bloc_05/07 F3/F5, bloc_05/03 S22): Decimals stay Decimal; frozen
immutable (``extra="forbid"`` + ``frozen=True`` via ``IdentityModelBase``);
required economic fields are required; optional terms stay explicitly
optional; provenance references are preserved verbatim, never synthesized.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator

from ..enums import PayoffType
from ..identity.models import IdentityModelBase, SemanticToken, UtcDatetime
from ..models import OpaqueIdentifier, RegistryVersion

__all__ = ["ContractTermsSnapshot"]


def _require_unique_ref(values: tuple[str, ...]) -> tuple[str, ...]:
    """Provenance uniqueness: the same frozen law the identity models enforce
    (duplicate-free evidence references), restated locally rather than
    importing an identity-module private name."""
    if len(set(values)) != len(values):
        raise ValueError("source_evidence_refs must be duplicate-free")
    return values


class ContractTermsSnapshot(IdentityModelBase):
    """Eligible recorded contract terms at one point-in-time query.

    An immutable view over accepted source records only (D1): every field is
    copied from the resolved ``ContractInstance`` or its ``EconomicContract``;
    no field carries a second economic meaning and no default substitutes for
    a recorded value.  Eligibility (valid-time + knowledge-time) is enforced
    by :func:`project_contract_terms` before a snapshot may exist; the model
    itself is a faithful carrier, not an eligibility authority.
    """

    # association (bloc_05/01 S2.5 - explicit contract-instance association)
    contract_instance_id: OpaqueIdentifier
    economic_contract_id: OpaqueIdentifier

    # terms-version reference (bloc_05/01 S7, S15)
    contract_terms_version: RegistryVersion

    # multiplier / quantity semantics (bloc_05/03 S6, S7)
    contract_multiplier: Decimal
    multiplier_unit: SemanticToken

    # unit semantics (bloc_05/01 S2.5)
    price_unit: SemanticToken
    quantity_unit: SemanticToken

    # payoff classification (bloc_05/07 F5, bloc_05/01 S3)
    payoff_type: PayoffType
    inverse_flag: bool
    quanto_flag: bool

    # quote / settlement / margin separation (bloc_05/03 S6, bloc_05/07 F6)
    quote_asset_id: OpaqueIdentifier
    settlement_asset_id: OpaqueIdentifier
    margin_asset_id: OpaqueIdentifier | None = None

    # tick/lot constraints (bloc_05/01 S2.5, S7 terms-version drivers)
    tick_size: Decimal
    lot_size: Decimal

    # optional temporal term (bloc_05/01 S2.5)
    expiry: UtcDatetime | None = None

    # source provenance, preserved verbatim (bloc_05/01 S2.5, A8 law)
    source_evidence_refs: Annotated[
        tuple[str, ...],
        AfterValidator(_require_unique_ref),
    ]
