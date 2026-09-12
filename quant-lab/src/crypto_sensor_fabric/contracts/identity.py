"""Bloc 1 canonical economic instrument identity contract (Bloc 1 §4 / F8).

Asset identity is not contract identity.  A canonical BTC identity does not
erase venue/contract/inverse-vs-linear distinctions: `BTCUSDT` linear perpetual
and inverse `XBTUSD` future both map to BTC exposure but remain distinct
instruments with distinct lifecycle (`instrument_start` / `instrument_end`).

Full PIT identity resolution and lifecycle handling arrive in Bloc 5.  Bloc 1
freezes the field contract and the fail-closed flag semantics.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .enums import ContractType, MarketType, QualityFlag


class InstrumentIdentity(BaseModel):
    """Canonical economic contract identity for one observation.

    `provider` and `venue` are preserved alongside canonical fields: fallback
    never erases provider identity (F3).
    """

    model_config = ConfigDict(extra="forbid")

    provider: str
    venue: str
    market_type: MarketType
    instrument_native: str
    instrument_id_canonical: str | None = None
    base_asset: str | None = None
    quote_asset: str | None = None
    settlement_asset: str | None = None
    contract_type: ContractType | None = None
    contract_multiplier: float | None = None
    is_inverse: bool | None = None
    instrument_start: datetime | None = None
    instrument_end: datetime | None = None
    identity_version: str | None = None


def is_identity_resolved(identity: InstrumentIdentity) -> bool:
    """True when the observation maps to a canonical instrument id."""
    return bool(identity.instrument_id_canonical)


def identity_quality_flags(identity: InstrumentIdentity) -> list[QualityFlag]:
    """Fail-closed flags for an identity (B1-T03 companion helper)."""
    if is_identity_resolved(identity):
        return []
    return [QualityFlag.INSTRUMENT_ID_UNRESOLVED]
