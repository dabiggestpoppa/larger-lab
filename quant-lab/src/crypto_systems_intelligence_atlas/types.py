"""Shared deterministic value types for the CSIA Book 2 kernel."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .temporal import Timestamp, UnknownBound, normalize_utc


class SourceClass(str, Enum):
    """The ratified Bloc 2A fourteen source classes."""

    NATIVE_TECHNICAL = "NATIVE_TECHNICAL"
    NATIVE_OPERATIONAL = "NATIVE_OPERATIONAL"
    REPOSITORY = "REPOSITORY"
    RPC = "RPC"
    EXPLORER = "EXPLORER"
    GOVERNANCE = "GOVERNANCE"
    STATUS_SYSTEM = "STATUS_SYSTEM"
    DATASET = "DATASET"
    SECURITY_AUDIT = "SECURITY_AUDIT"
    ACADEMIC = "ACADEMIC"
    ANALYTICS = "ANALYTICS"
    AGGREGATOR = "AGGREGATOR"
    NEWS = "NEWS"
    SOCIAL = "SOCIAL"


class ClaimFamily(str, Enum):
    """The ratified authority-matrix claim families."""

    CHAIN_ARCHITECTURE = "CHAIN_ARCHITECTURE"
    DEPLOYMENT_ACTIVATION = "DEPLOYMENT / ACTIVATION"
    GOVERNANCE_EXECUTION = "GOVERNANCE EXECUTION"
    GOVERNANCE_PROPOSAL = "GOVERNANCE PROPOSAL"
    INTEGRATION = "INTEGRATION"
    NARRATIVE = "NARRATIVE"
    SECURITY_EVENT = "SECURITY EVENT"
    TOKEN_ROLE_MECHANICS = "TOKEN ROLE / MECHANICS"
    BRIDGE_ROUTE_STATE = "BRIDGE / ROUTE STATE"
    VALIDATOR_SET_EPOCH_STATE = "VALIDATOR SET / EPOCH STATE"
    HISTORICAL_GENESIS_SPEC = "HISTORICAL GENESIS / SPEC"
    IDENTITY_ATTRIBUTES = "IDENTITY ATTRIBUTES"
    MARKET_DATA = "MARKET DATA"


class AuthorityTier(str, Enum):
    """Claim-family-scoped authority tiers; never a global source score."""

    PRIMARY = "PRIMARY"
    SUPPORTING = "SUPPORTING"
    INSUFFICIENT = "INSUFFICIENT"
    UNREGISTERED = "UNREGISTERED"


class AuthoritySeed(BaseModel):
    """Source-owned metadata that seeds family/time authority resolution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_family: ClaimFamily
    tier: AuthorityTier
    valid_from: Timestamp | UnknownBound
    valid_to: Timestamp | UnknownBound | None = None
    policy_version: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _validate_times(self) -> "AuthoritySeed":
        start = self.valid_from
        end = self.valid_to
        if isinstance(start, datetime):
            normalize_utc(start)
        if isinstance(end, datetime):
            normalize_utc(end)
        if isinstance(start, datetime) and isinstance(end, datetime) and start > end:
            raise ValueError("authority valid_from > valid_to")
        return self


__all__ = [
    "AuthoritySeed",
    "AuthorityTier",
    "ClaimFamily",
    "SourceClass",
]
