"""CSIA Book 2 — Bloc 2B: immutable raw evidence."""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .sources import SourceRegistry
from .temporal import Timestamp, UnknownBound, normalize_utc


class EvidenceTier(str, Enum):
    DEPLOYED_STATE = "DEPLOYED_STATE"
    FIRST_PARTY_DOC = "FIRST_PARTY_DOC"
    THIRD_PARTY = "THIRD_PARTY"
    AGGREGATOR = "AGGREGATOR"
    SOCIAL = "SOCIAL"
    NARRATIVE = "NARRATIVE"


class EvidenceStatus(str, Enum):
    CAPTURED = "CAPTURED"
    PARSED = "PARSED"
    CONTESTED = "CONTESTED"
    WITHDRAWN = "WITHDRAWN"


class TimeHint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str = Field(min_length=1)
    value: Timestamp | UnknownBound


class RawEvidence(BaseModel):
    """Immutable source observation; corrections create new evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    retrieved_at: datetime
    source_published_at: datetime | None = None
    content_locator: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    raw_snapshot_ref: str = Field(min_length=1)
    extractor_version: str = Field(min_length=1)
    parser_version: str = Field(min_length=1)
    object_refs: tuple[str, ...] = ()
    claim_refs: tuple[str, ...] = ()
    valid_time_hints: tuple[TimeHint, ...] = ()
    evidence_tier: EvidenceTier
    evidence_status: EvidenceStatus = EvidenceStatus.CAPTURED
    transformation_lineage: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _timestamps_and_hash(self) -> "RawEvidence":
        normalize_utc(self.retrieved_at)
        if self.source_published_at is not None:
            normalize_utc(self.source_published_at)
        if not self.content_hash.startswith("sha256:"):
            raise ValueError("content_hash must use the deterministic sha256: form")
        if not self.transformation_lineage and self.evidence_status is EvidenceStatus.PARSED:
            raise ValueError("parsed evidence requires transformation lineage")
        return self


def canonical_bytes(value: bytes | str) -> bytes:
    """Return the exact byte fixture used by deterministic content hashes."""
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8")


def content_hash_for(value: bytes | str) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


class EvidenceStore:
    """Append-only evidence store with no delete or in-place edit path."""

    def __init__(self, source_registry: SourceRegistry | None = None) -> None:
        self._source_registry = source_registry
        self._evidence: dict[str, RawEvidence] = {}

    def _require_source(self, source_id: str) -> None:
        if self._source_registry is not None and source_id not in self._source_registry:
            raise KeyError(f"unregistered source {source_id}")

    def add(self, evidence: RawEvidence) -> RawEvidence:
        self._require_source(evidence.source_id)
        if evidence.evidence_id in self._evidence:
            raise ValueError(f"evidence {evidence.evidence_id} already exists")
        self._evidence[evidence.evidence_id] = evidence
        return evidence

    def capture(
        self,
        *,
        source_id: str,
        retrieved_at: datetime,
        content: bytes | str,
        content_locator: str,
        raw_snapshot_ref: str,
        extractor_version: str,
        parser_version: str,
        object_refs: Iterable[str] = (),
        claim_refs: Iterable[str] = (),
        valid_time_hints: Iterable[TimeHint] = (),
        evidence_tier: EvidenceTier,
        source_published_at: datetime | None = None,
    ) -> RawEvidence:
        self._require_source(source_id)
        content_hash = content_hash_for(content)
        identity = f"{source_id}|{content_hash}|{normalize_utc(retrieved_at).isoformat()}|{content_locator}"
        evidence_id = "csia:evidence:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]
        return self.add(
            RawEvidence(
                evidence_id=evidence_id,
                source_id=source_id,
                retrieved_at=retrieved_at,
                source_published_at=source_published_at,
                content_locator=content_locator,
                content_hash=content_hash,
                raw_snapshot_ref=raw_snapshot_ref,
                extractor_version=extractor_version,
                parser_version=parser_version,
                object_refs=tuple(object_refs),
                claim_refs=tuple(claim_refs),
                valid_time_hints=tuple(valid_time_hints),
                evidence_tier=evidence_tier,
            )
        )

    def derive(
        self,
        parent: RawEvidence,
        *,
        evidence_id: str,
        retrieved_at: datetime,
        content: bytes | str,
        content_locator: str,
        raw_snapshot_ref: str,
        extractor_version: str,
        parser_version: str,
        evidence_tier: EvidenceTier,
        claim_refs: Iterable[str] = (),
    ) -> RawEvidence:
        """Create a new parsed evidence record without mutating ``parent``."""
        if parent.evidence_status is EvidenceStatus.WITHDRAWN:
            raise ValueError("withdrawn evidence cannot seed a new parse")
        return self.add(
            RawEvidence(
                evidence_id=evidence_id,
                source_id=parent.source_id,
                retrieved_at=retrieved_at,
                content_locator=content_locator,
                content_hash=content_hash_for(content),
                raw_snapshot_ref=raw_snapshot_ref,
                extractor_version=extractor_version,
                parser_version=parser_version,
                object_refs=parent.object_refs,
                claim_refs=tuple(claim_refs),
                valid_time_hints=parent.valid_time_hints,
                evidence_tier=evidence_tier,
                evidence_status=EvidenceStatus.PARSED,
                transformation_lineage=(
                    *parent.transformation_lineage,
                    f"parse:{parent.evidence_id}",
                ),
            )
        )

    def require(self, evidence_id: str) -> RawEvidence:
        try:
            return self._evidence[evidence_id]
        except KeyError as exc:
            raise KeyError(f"unknown evidence {evidence_id}") from exc

    def get(self, evidence_id: str) -> RawEvidence | None:
        return self._evidence.get(evidence_id)

    @property
    def all_records(self) -> dict[str, RawEvidence]:
        return dict(self._evidence)

    def __len__(self) -> int:
        return len(self._evidence)


__all__ = [
    "EvidenceStatus",
    "EvidenceStore",
    "EvidenceTier",
    "RawEvidence",
    "TimeHint",
    "canonical_bytes",
    "content_hash_for",
]
