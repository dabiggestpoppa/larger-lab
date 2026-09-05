"""ProviderEnvelope — storage/provenance metadata around raw source content.

This is NOT a canonical market observation (Bloc 1 §6 / 02 §3).  Every future
provider adapter must first emit a provider envelope before any normalization;
research consumers never see envelopes as canonical mechanics.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..contracts.base import normalize_utc_datetimes
from ..contracts.enums import AccessClass, QualityFlag, RetrievalMode, SensorFamily


class ProviderEnvelope(BaseModel):
    """Provenance envelope bound to an immutable raw object (T0 pointer)."""

    model_config = ConfigDict(extra="forbid")

    envelope_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    venue_hint: str | None = None
    sensor_family_hint: SensorFamily
    endpoint_id: str = Field(min_length=1)
    request_id: str | None = None
    retrieval_mode: RetrievalMode
    request_started_at: datetime
    response_received_at: datetime
    source_symbol: str | None = None
    source_interval: str | None = None
    requested_start: datetime | None = None
    requested_end: datetime | None = None
    raw_object_uri: str = Field(min_length=1)
    raw_checksum: str = Field(min_length=1)
    http_status: int | None = None
    access_class: AccessClass
    adapter_version: str = Field(min_length=1)
    quality_flags: list[QualityFlag] = Field(default_factory=list)
    source_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _normalize_timestamps_utc(self) -> ProviderEnvelope:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]
