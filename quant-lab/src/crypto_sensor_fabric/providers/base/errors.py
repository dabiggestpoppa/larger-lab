"""Typed acquisition errors (01 §21 / 03 §12-§13).

Every error carries provider identity, sensor family, the request fingerprint
(where available), retryability and redacted provider-native context.  No
secret material is ever attached.  Unsupported capability is a TYPED error
(CapabilityUnavailable), never `[]` / `0` / `None` as an ambiguous substitute.
"""

from __future__ import annotations

from typing import Any

from ...contracts.enums import SensorFamily
from .enums import Retryability
from .models import AdapterEvidenceRef, RawPayloadEnvelope


class AcquisitionError(Exception):
    """Base class for all typed acquisition errors (01 §21)."""

    failure_type = "AcquisitionError"

    def __init__(
        self,
        provider_id: str,
        sensor_family: SensorFamily,
        *,
        request_fingerprint: str | None = None,
        retryability: Retryability = Retryability.UNKNOWN,
        provider_native_context_redacted: dict[str, Any] | None = None,
        evidence_ref: AdapterEvidenceRef | None = None,
        raw_payload_envelope: RawPayloadEnvelope | None = None,
        detail: str | None = None,
    ) -> None:
        self.provider_id = provider_id
        self.sensor_family = sensor_family
        self.request_fingerprint = request_fingerprint
        self.retryability = retryability
        self.provider_native_context_redacted = provider_native_context_redacted or {}
        self.evidence_ref = evidence_ref
        self.raw_payload_envelope = raw_payload_envelope
        self.detail = detail
        super().__init__(detail or self.failure_type)


class ProviderUnavailable(AcquisitionError):
    """Provider/endpoint unavailable (transport-level, transient)."""

    failure_type = "ProviderUnavailable"


class CapabilityUnavailable(AcquisitionError):
    """Sensor capability not supported by this provider.

    The typed answer to an unsupported `fetch_*` call.  Never `[]`/`0`/`None`.
    """

    failure_type = "CapabilityUnavailable"


class AuthenticationRequired(AcquisitionError):
    """Provider requires authentication the adapter does not hold."""

    failure_type = "AuthenticationRequired"


class AccessClassViolation(AcquisitionError):
    """Access drifted from the frozen free-only contract (01 §23 / 03 §12).

    Emitted when a previously free endpoint demands payment/subscription/
    trading-auth/wallet/stake — the adapter must NOT sign up or fall through
    to a paid path.
    """

    failure_type = "AccessClassViolation"


class RateLimited(AcquisitionError):
    """Provider rate limit (429 / quota).  Retry honors Retry-After."""

    failure_type = "RateLimited"


class GeoRestricted(AcquisitionError):
    """Provider geo-restriction (451/403-region).  Distinct from history/auth."""

    failure_type = "GeoRestricted"


class InvalidInstrument(AcquisitionError):
    """Native instrument not listed / unknown to the provider.

    Distinct from unsupported sensor: the request was well-formed, the symbol
    is not valid for this surface.
    """

    failure_type = "InvalidInstrument"


class UnsupportedGranularity(AcquisitionError):
    """Requested granularity not offered for this provider/sensor."""

    failure_type = "UnsupportedGranularity"


class HistoricalRangeUnavailable(AcquisitionError):
    """Provider does not serve the requested historical range (retention)."""

    failure_type = "HistoricalRangeUnavailable"


class PaginationFailure(AcquisitionError):
    """Pagination loop / repeated cursor / non-monotonic traversal (03 §8)."""

    failure_type = "PaginationFailure"


class ArchiveIntegrityFailure(AcquisitionError):
    """Bulk archive checksum/length/parse integrity failure (03 §17)."""

    failure_type = "ArchiveIntegrityFailure"


class SchemaDrift(AcquisitionError):
    """Breaking/unknown schema — raw payload archived, parsed output fails closed.

    `raw_payload_envelope` carries the exact preserved raw acquisition artifact
    (body + integrity hash + provider/sensor/fingerprint/retrieval metadata) so
    the failure path itself is evidence-bearing.  Other error types leave the
    attachment None by default.
    """

    failure_type = "SchemaDrift"


class ProviderSemanticError(AcquisitionError):
    """Provider-native semantic error (units/timestamps/side conventions)."""

    failure_type = "ProviderSemanticError"


class TransportFailure(AcquisitionError):
    """Transport failure (timeout / DNS / TLS / connection reset)."""

    failure_type = "TransportFailure"


class RetryExhausted(AcquisitionError):
    """Attempt budget exhausted for a transiently retryable failure."""

    failure_type = "RetryExhausted"


#: Failure type name -> error class (serialization registry).
ERROR_TYPES: dict[str, type[AcquisitionError]] = {
    cls.failure_type: cls
    for cls in (
        ProviderUnavailable,
        CapabilityUnavailable,
        AuthenticationRequired,
        AccessClassViolation,
        RateLimited,
        GeoRestricted,
        InvalidInstrument,
        UnsupportedGranularity,
        HistoricalRangeUnavailable,
        PaginationFailure,
        ArchiveIntegrityFailure,
        SchemaDrift,
        ProviderSemanticError,
        TransportFailure,
        RetryExhausted,
    )
}


def error_from_failure_type(
    failure_type: str,
    provider_id: str,
    sensor_family: SensorFamily,
    **kwargs: Any,
) -> AcquisitionError:
    """Rebuild a typed error from its serialized failure type."""
    cls = ERROR_TYPES.get(failure_type, AcquisitionError)
    return cls(provider_id, sensor_family, **kwargs)
