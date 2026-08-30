"""Bloc 3 base adapter controlled vocabularies.

Frozen from `bloc_03/01_PRODUCTION_ADAPTER_ARCHITECTURE.md` §9-§17 and
`03_ADAPTER_QA_RESUME_AND_FAILURE_SEMANTICS.md`.  The base layer REUSES the
frozen Bloc 1 / Bloc 2 vocabularies wherever the semantics already exist:

- `SensorFamily` (Bloc 1) — canonical sensor families; never re-declared.
- `Granularity` (Bloc 2) — canonical granularity set.
- `QueryMode` (Bloc 2) — the frozen navigation/pagination vocabulary
  (TIME_RANGE / CURSOR / SEQUENCE / PAGE / DOWNLOAD_FILE / LATEST_ONLY);
  `PaginationMode` is an alias of that same vocabulary, NOT a new concept.
- `FreeOnlyStatus` (Bloc 2) — free-only classification.

Genuinely NEW Bloc 3 members (not present in Bloc 1/2) are declared here:
historical/live modes, fetch purpose, adapter status, retryability, schema
state, and the adapter-layer auth vocabulary required by the frozen access
doctrine (01 §11) — hard-blocked credential classes are new because Bloc 2
never modeled signing/trading credential categories.
"""

from __future__ import annotations

from enum import Enum

from ...contracts.enums import SensorFamily  # noqa: F401  (re-exported)
from ...probes.enums import (
    FreeOnlyStatus as _FreeOnlyStatus,  # re-exported below
)
from ...probes.enums import (
    Granularity as _Granularity,  # re-exported below
)
from ...probes.enums import (
    QueryMode as _QueryMode,  # alias source for PaginationMode
)

Granularity = _Granularity
FreeOnlyStatus = _FreeOnlyStatus


class _StrEnum(str, Enum):
    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class HistoricalMode(_StrEnum):
    """Declared historical acquisition surface (01 §9).

    A provider/sensor may support more than one; the capability records each
    independently (REST history is never conflated with archive history).
    """

    REST_RANGE = "REST_RANGE"
    REST_CURSOR = "REST_CURSOR"
    REST_PAGE = "REST_PAGE"
    BULK_ARCHIVE_DAILY = "BULK_ARCHIVE_DAILY"
    BULK_ARCHIVE_MONTHLY = "BULK_ARCHIVE_MONTHLY"
    PUBLIC_OBJECT_STORAGE = "PUBLIC_OBJECT_STORAGE"
    WEBSOCKET_ONLY = "WEBSOCKET_ONLY"
    LIVE_REST_ONLY = "LIVE_REST_ONLY"
    THIRD_PARTY_ARCHIVE = "THIRD_PARTY_ARCHIVE"


class LiveMode(_StrEnum):
    """Live/recent acquisition surface (01 §10)."""

    LIVE_REST = "LIVE_REST"
    WEBSOCKET = "WEBSOCKET"
    LATEST_SNAPSHOT = "LATEST_SNAPSHOT"
    NONE = "NONE"


#: Pagination vocabulary — the frozen Bloc 2 QueryMode semantics (01 §15).
PaginationMode = _QueryMode


class FetchPurpose(_StrEnum):
    """Acquisition purpose for a FetchRequest (01 §5)."""

    PROBE = "PROBE"
    BACKFILL = "BACKFILL"
    LIVE_RECOVERY = "LIVE_RECOVERY"
    LIVE_POLL = "LIVE_POLL"


class AdapterStatus(_StrEnum):
    """Provider/sensor adapter lifecycle status (03 §24)."""

    PLANNED = "PLANNED"
    IMPLEMENTING = "IMPLEMENTING"
    COMMON_FRAMEWORK_READY = "COMMON_FRAMEWORK_READY"
    ADAPTER_READY = "ADAPTER_READY"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    ACCESS_BLOCKED = "ACCESS_BLOCKED"
    DATA_BLOCKED = "DATA_BLOCKED"


class Retryability(_StrEnum):
    """Retry classification of one failure (01 §13 / 03 §10)."""

    RETRYABLE = "RETRYABLE"
    TERMINAL = "TERMINAL"
    UNKNOWN = "UNKNOWN"


class SchemaState(_StrEnum):
    """Parser schema classification (01 §17)."""

    KNOWN_SCHEMA = "KNOWN_SCHEMA"
    ADDITIVE_SCHEMA_CHANGE = "ADDITIVE_SCHEMA_CHANGE"
    BREAKING_SCHEMA_CHANGE = "BREAKING_SCHEMA_CHANGE"
    UNKNOWN_SCHEMA = "UNKNOWN_SCHEMA"


class AdapterAuthMode(_StrEnum):
    """Adapter-layer auth vocabulary (01 §11).

    Allowed for acquisition: NO_AUTH / FREE_API_KEY / OPTIONAL_PUBLIC_KEY.
    Everything else is a HARD BLOCK: an adapter must never use trading or
    wallet credentials for sensor-fabric ingestion, and must never sign up or
    pay.  FAIL CLOSED on uncertainty.
    """

    NO_AUTH = "NO_AUTH"
    FREE_API_KEY = "FREE_API_KEY"
    OPTIONAL_PUBLIC_KEY = "OPTIONAL_PUBLIC_KEY"
    # --- hard blocks ---
    PAID_KEY = "PAID_KEY"
    TRADING_KEY = "TRADING_KEY"
    WITHDRAWAL_PERMISSION = "WITHDRAWAL_PERMISSION"
    SIGNING_SECRET = "SIGNING_SECRET"
    WALLET_SIGNATURE = "WALLET_SIGNATURE"
    STAKING_UNLOCK = "STAKING_UNLOCK"
    TRANSACTION_REQUIRED = "TRANSACTION_REQUIRED"
    UNVERIFIED = "UNVERIFIED"


#: Adapter auth modes allowed for sensor-fabric acquisition (01 §11).
ALLOWED_AUTH_MODES: frozenset[AdapterAuthMode] = frozenset(
    {
        AdapterAuthMode.NO_AUTH,
        AdapterAuthMode.FREE_API_KEY,
        AdapterAuthMode.OPTIONAL_PUBLIC_KEY,
    }
)

#: Adapter auth modes that are never permitted (01 §11 hard blocks).
HARD_BLOCK_AUTH_MODES: frozenset[AdapterAuthMode] = frozenset(
    {
        AdapterAuthMode.PAID_KEY,
        AdapterAuthMode.TRADING_KEY,
        AdapterAuthMode.WITHDRAWAL_PERMISSION,
        AdapterAuthMode.SIGNING_SECRET,
        AdapterAuthMode.WALLET_SIGNATURE,
        AdapterAuthMode.STAKING_UNLOCK,
        AdapterAuthMode.TRANSACTION_REQUIRED,
    }
)


class DuplicateAnnotation(_StrEnum):
    """Duplicate detection annotation (01 §16 / 03 §8).

    Adapters never destructively deduplicate raw evidence; they may annotate.
    """

    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    REPEATED_PAGE = "REPEATED_PAGE"


class QualityFlagAcquisition(_StrEnum):
    """Acquisition-level quality flags on a FetchBatch (01 §6 / 05 §8)."""

    EMPTY_VALID = "EMPTY_VALID"
    PARTIAL_INTERVAL = "PARTIAL_INTERVAL"
    NON_MONOTONIC_TIMESTAMPS = "NON_MONOTONIC_TIMESTAMPS"
    DUPLICATE_EDGE = "DUPLICATE_EDGE"
    SCHEMA_ADDITIVE = "SCHEMA_ADDITIVE"
    SCHEMA_BREAKING = "SCHEMA_BREAKING"
    GAP_DETECTED = "GAP_DETECTED"
    PROVIDER_REVISION = "PROVIDER_REVISION"
    ACCESS_REVIEW_REQUIRED = "ACCESS_REVIEW_REQUIRED"
    RATE_LIMITED = "RATE_LIMITED"
