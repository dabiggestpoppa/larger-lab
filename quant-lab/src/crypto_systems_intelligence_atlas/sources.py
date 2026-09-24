"""CSIA Book 2 — Bloc 2A: source registry."""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .identity import ObjectType
from .temporal import normalize_utc
from .types import AuthoritySeed, SourceClass

_SOURCE_ID_RE = re.compile(r"^csia:source:[a-z0-9][a-z0-9_-]*$")


class SourceLifecycle(str, Enum):
    REGISTERED = "REGISTERED"
    VERIFIED = "VERIFIED"
    DEGRADED = "DEGRADED"
    RETIRED = "RETIRED"


class SourceHealth(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    UNREACHABLE = "UNREACHABLE"
    RETIRED = "RETIRED"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"


class AccessMethod(str, Enum):
    DOCUMENT = "DOCUMENT"
    REST_API = "REST_API"
    GRAPHQL = "GRAPHQL"
    RPC = "RPC"
    REPOSITORY = "REPOSITORY"
    OTHER = "OTHER"


class LocatorMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    base_locator: str = Field(min_length=1)
    access_method: AccessMethod
    authentication: str = Field(min_length=1)
    previous_locators: tuple[str, ...] = ()
    access_metadata: tuple[tuple[str, str], ...] = ()


class Source(BaseModel):
    """Immutable source version; the registry preserves every version."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    source_class: SourceClass
    canonical_name: str = Field(min_length=1)
    owner_entity_ref: str | None = None
    object_scope: tuple[ObjectType, ...] = ()
    locator: LocatorMetadata
    authority_metadata: tuple[AuthoritySeed, ...] = ()
    lifecycle: SourceLifecycle = SourceLifecycle.REGISTERED
    health_state: SourceHealth = SourceHealth.HEALTHY
    last_verified_at: datetime | None = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    verification_evidence_refs: tuple[str, ...] = ()
    version: int = Field(default=1, ge=1)
    supersedes_version: int | None = None

    @model_validator(mode="after")
    def _validate_source(self) -> Self:
        if not _SOURCE_ID_RE.match(self.source_id):
            raise ValueError("source_id must be csia:source:<slug>")
        if self.version == 1 and self.supersedes_version is not None:
            raise ValueError("version 1 cannot supersede a source version")
        if self.version > 1 and self.supersedes_version != self.version - 1:
            raise ValueError("source versions must form an append-only chain")
        if self.verification_status is VerificationStatus.VERIFIED and not self.verification_evidence_refs:
            raise ValueError("verified source updates require evidence references")
        if self.last_verified_at is not None:
            normalize_utc(self.last_verified_at)
        return self


class SourceRegistry:
    """Append-only in-memory source registry; locator churn preserves source_id."""

    def __init__(self) -> None:
        self._versions: dict[str, list[Source]] = {}

    def register(self, source: Source) -> Source:
        if source.source_id in self._versions:
            raise ValueError(f"source {source.source_id} is already registered")
        if source.version != 1:
            raise ValueError("first source record must be version 1")
        self._versions[source.source_id] = [source]
        return source

    def add_version(self, source: Source) -> Source:
        history = self._versions.get(source.source_id)
        if history is None:
            raise KeyError(f"unknown source {source.source_id}")
        previous = history[-1]
        if source.source_class is not previous.source_class:
            raise ValueError("source class is immutable across source versions")
        if source.version != previous.version + 1:
            raise ValueError("source version must append exactly one version")
        if source.supersedes_version != previous.version:
            raise ValueError("source version must point to the prior version")
        history.append(source)
        return source

    def require(self, source_id: str) -> Source:
        try:
            return self._versions[source_id][-1]
        except KeyError as exc:
            raise KeyError(f"unknown source {source_id}") from exc

    def get(self, source_id: str) -> Source | None:
        history = self._versions.get(source_id)
        return history[-1] if history else None

    def history(self, source_id: str) -> tuple[Source, ...]:
        try:
            return tuple(self._versions[source_id])
        except KeyError as exc:
            raise KeyError(f"unknown source {source_id}") from exc

    def update_locator(
        self,
        source_id: str,
        *,
        locator: LocatorMetadata,
        verification_evidence_refs: tuple[str, ...],
        at: datetime,
    ) -> Source:
        previous = self.require(source_id)
        if not verification_evidence_refs:
            raise ValueError("locator update requires evidence references")
        updated = Source.model_validate(
            {
                **previous.model_dump(),
                "locator": locator.model_dump(),
                "last_verified_at": at,
                "verification_status": VerificationStatus.VERIFIED,
                "verification_evidence_refs": verification_evidence_refs,
                "version": previous.version + 1,
                "supersedes_version": previous.version,
            }
        )
        return self.add_version(updated)

    def mark_health(
        self,
        source_id: str,
        health_state: SourceHealth,
        *,
        at: datetime,
        evidence_refs: tuple[str, ...] = (),
    ) -> Source:
        previous = self.require(source_id)
        if not evidence_refs:
            raise ValueError("health updates must be evidence-backed")
        updated = Source.model_validate(
            {
                **previous.model_dump(),
                "health_state": health_state,
                "last_verified_at": at,
                "verification_status": VerificationStatus.VERIFIED,
                "verification_evidence_refs": evidence_refs,
                "version": previous.version + 1,
                "supersedes_version": previous.version,
            }
        )
        return self.add_version(updated)

    def __contains__(self, source_id: object) -> bool:
        return isinstance(source_id, str) and source_id in self._versions

    @property
    def sources(self) -> dict[str, Source]:
        return {source_id: versions[-1] for source_id, versions in self._versions.items()}


__all__ = [
    "AccessMethod",
    "LocatorMetadata",
    "Source",
    "SourceHealth",
    "SourceLifecycle",
    "SourceRegistry",
    "VerificationStatus",
]
