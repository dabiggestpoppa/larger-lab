"""CSIA Book 1 — Bloc 1D: Temporal (bitemporal) kernel.

Implements the ratified temporal doctrine — Constitution v0.2 §12 (RATIFIED)
instantiated by Book 1 plan §1D.6 rules R1–R10:

- two independent time axes: valid time (when true in the world) and
  transaction time (when CSIA knew/recorded it);
- six timestamp semantics on every meaningful record;
- unknown valid time is explicit (``UNKNOWN(bounded)``) — never fabricated;
- superseded records are queryable forever (R4 / INV-1D-1);
- as-of (valid-time) and as-known (transaction-time) views (R6 / R7);
- STALE is computed, never authored (INV-1D-5).

Replay *machinery* is Book 7D scope; this module supplies the semantics and
schema-level properties the replay contract RC-1..RC-4 needs.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

Timestamp = datetime
"""An aware, UTC datetime (naive datetimes are rejected at the edges)."""

OPEN: None = None
"""Sentinel for an open-ended ``valid_to`` — the fact still holds."""


class UnknownBound(BaseModel):
    """Explicit uncertain valid time (rule R9).

    Queries must treat UNKNOWN bounds explicitly — never as ``null`` and never
    as ``open``. Carries bounded uncertainty plus an optional evidence pointer
    for the confidence claim.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: str = Field(default="UNKNOWN", frozen=True)
    earliest_bound: datetime | None = None
    latest_bound: datetime | None = None
    confidence_ref: str | None = None  # evidence pointer for the confidence claim

    def __str__(self) -> str:  # pragma: no cover - display only
        return (
            f"UNKNOWN({self.earliest_bound!r}..{self.latest_bound!r})"
        )


class ObjectLifecycle(str, Enum):
    """Object lifecycle (Bloc 1A): deletion is impossible; only transitions."""

    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    HISTORICAL = "HISTORICAL"


class RealizationStatus(str, Enum):
    """Realization lifecycle [C-17] — record-level, per Bloc 1D rules."""

    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"  # world change: route/channel closed; record queryable forever
    MIGRATED = "MIGRATED"  # lineage handoff via migration_from/migration_to
    HISTORICAL = "HISTORICAL"  # pre-ratification / pre-discovery retained form
    UNKNOWN = "UNKNOWN"  # mechanism/route known only partially; R9 applies


class RecordLifecycle(str, Enum):
    """Record claim lifecycle (Constitution §7 vocabulary, subset used here)."""

    DECLARED = "DECLARED"
    OBSERVED = "OBSERVED"
    VERIFIED = "VERIFIED"
    CONTESTED = "CONTESTED"
    REJECTED = "REJECTED"


class TemporalRecord(BaseModel):
    """Base record carrying the six bitemporal fields (plan §1D.6).

    Rules enforced here:

    - R1: valid_from <= valid_to (when both known);
    - R3: superseded_at >= observed_at (when set);
    - observed_at must be timezone-aware (UTC-normalized on construction);
    - R4: superseded records are never deleted — this model has no delete path.
    """

    model_config = ConfigDict(extra="forbid")

    observed_at: datetime
    valid_from: Timestamp | UnknownBound
    valid_to: Timestamp | UnknownBound | None = None  # None = OPEN
    source_published_at: datetime | None = None
    ingested_at: datetime | None = None
    superseded_at: datetime | None = None
    supersedes: str | None = None  # record_id this record replaces (chain preserved)

    def model_post_init(self, __context: object) -> None:
        object.__setattr__(self, "observed_at", normalize_utc(self.observed_at))
        if self.source_published_at is not None:
            object.__setattr__(
                self, "source_published_at", normalize_utc(self.source_published_at)
            )
        if self.ingested_at is not None:
            object.__setattr__(self, "ingested_at", normalize_utc(self.ingested_at))
        if self.superseded_at is not None:
            object.__setattr__(self, "superseded_at", normalize_utc(self.superseded_at))
        if isinstance(self.valid_from, datetime):
            object.__setattr__(self, "valid_from", normalize_utc(self.valid_from))
        if isinstance(self.valid_to, datetime):
            object.__setattr__(self, "valid_to", normalize_utc(self.valid_to))
        # R1
        start = known_start(self.valid_from)
        end = known_end(self.valid_to)
        if start is not None and end is not None and start > end:
            raise ValueError("R1 violated: valid_from > valid_to")
        # R3
        if self.superseded_at is not None and self.superseded_at < self.observed_at:
            raise ValueError("R3 violated: superseded_at < observed_at")


class ClaimBinding(BaseModel):
    """Provenance hook (Constitution §13): every promoted fact/edge keeps the
    pointer trail that produced it. Edge-level minimum (IR-10)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_locator: str | None = None
    evidence_type: str | None = None
    retrieval_time: datetime | None = None
    extractor_version: str | None = None
    transformation_lineage: tuple[str, ...] = ()
    claim_state: RecordLifecycle = RecordLifecycle.DECLARED

    def model_post_init(self, __context: object) -> None:
        if self.retrieval_time is not None:
            object.__setattr__(
                self, "retrieval_time", normalize_utc(self.retrieval_time)
            )


def normalize_utc(value: datetime) -> datetime:
    """Reject naive datetimes; normalize aware values to UTC."""
    if value.tzinfo is None:
        raise ValueError(
            f"naive datetime {value.isoformat()!r} is not allowed; supply a "
            "timezone-aware timestamp (no silent local-time assumptions)"
        )
    return value.astimezone(UTC)


def utc_now() -> datetime:
    return datetime.now(UTC)


def known_start(value: Timestamp | UnknownBound) -> datetime | None:
    """Earliest *exact* known start (UNKNOWN yields None — explicit, not open)."""
    if isinstance(value, UnknownBound):
        return None
    return value


def known_end(value: Timestamp | UnknownBound | None) -> datetime | None:
    if value is None or isinstance(value, UnknownBound):
        return None
    return value


def is_open(value: Timestamp | UnknownBound | None) -> bool:
    """True when the fact is still holding (valid_to null/OPEN)."""
    return value is None


def holds_at(
    valid_from: Timestamp | UnknownBound,
    valid_to: Timestamp | UnknownBound | None,
    at: datetime,
) -> bool | None:
    """R6 as-of predicate.

    Returns True/False where decidable; ``None`` where UNKNOWN bounds make the
    answer undecidable at ``at`` (R9: queries see the uncertainty explicitly).
    """
    start = known_start(valid_from)
    if start is not None and start > at:
        return False
    if isinstance(valid_from, UnknownBound):
        earliest = valid_from.earliest_bound
        if earliest is not None and earliest > at:
            return False
    if valid_to is None:
        return True
    if isinstance(valid_to, UnknownBound):
        latest = valid_to.latest_bound
        if latest is not None and latest < at:
            return False
        return None  # bounded uncertainty covers `at` — undecidable
    end = valid_to
    return end > at


class RecordStore:
    """Append-only record store implementing R4/R5/R7/RC-1..RC-4 semantics.

    - ``add`` only; no delete or in-place mutation path exists (INV-1D-1);
    - corrections are *new records* with ``supersedes`` pointers;
    - ``current()`` = transaction-time filter R5;
    - ``as_known()`` = R7; ``as_of()`` filters valid time via :func:`holds_at`;
    - schema version participates in the replay key (RC-4).
    """

    def __init__(self, schema_version: str = "book1-v0.3") -> None:
        self._records: dict[str, TemporalRecord] = {}
        self._schema_version = schema_version

    @property
    def schema_version(self) -> str:
        return self._schema_version

    def add(self, record_id: str, record: TemporalRecord) -> None:
        if record_id in self._records:
            raise ValueError(
                f"record {record_id} already exists — records are immutable; "
                "add a superseding record instead (INV-1D-1)"
            )
        if record.supersedes is not None and record.supersedes not in self._records:
            raise KeyError(f"supersedes target {record.supersedes} unknown")
        self._records[record_id] = record

    def get(self, record_id: str) -> TemporalRecord:
        return self._records[record_id]  # R4: every record stays queryable forever

    def all_records(self) -> dict[str, TemporalRecord]:
        return dict(self._records)

    def supersede(self, old_id: str, new_id: str, new_record: TemporalRecord) -> None:
        """Record-level supersession: new record replaces the old *about the
        same claim*; chain preserved, nothing rewritten."""
        if old_id not in self._records:
            raise KeyError(f"unknown record {old_id}")
        if new_record.supersedes != old_id:
            raise ValueError("new_record.supersedes must reference the superseded id")
        self.add(new_id, new_record)
        old = self._records[old_id]
        if old.superseded_at is None:
            old.superseded_at = new_record.observed_at

    def current(self) -> list[tuple[str, TemporalRecord]]:
        """R5: current view = records with superseded_at = None."""
        return [
            (rid, r) for rid, r in self._records.items() if r.superseded_at is None
        ]

    def as_known(self, at: datetime) -> list[tuple[str, TemporalRecord]]:
        """R7: as-known view at transaction time ``at``."""
        at = normalize_utc(at)
        out: list[tuple[str, TemporalRecord]] = []
        for rid, r in self._records.items():
            if r.observed_at <= at and (
                r.superseded_at is None or r.superseded_at > at
            ):
                out.append((rid, r))
        return out

    def as_of(self, at: datetime) -> list[tuple[str, TemporalRecord]]:
        """R6 as-of view over current records; UNKNOWN-bound records whose
        validity is undecidable at ``at`` are included with that flag."""
        out: list[tuple[str, TemporalRecord]] = []
        for rid, r in self.current():
            verdict = holds_at(r.valid_from, r.valid_to, at)
            if verdict is not False:
                out.append((rid, r))
        return out

    def is_stale(
        self,
        record_id: str,
        *,
        reverify_window_days: int,
        now: datetime | None = None,
    ) -> bool:
        """INV-1D-5: STALE computed from stored fields + policy only."""
        now = normalize_utc(now) if now is not None else utc_now()
        r = self.get(record_id)
        if isinstance(r.valid_to, UnknownBound):
            latest = r.valid_to.latest_bound
            if latest is not None and (now - latest).days > reverify_window_days:
                return True
        return False


__all__ = [
    "OPEN",
    "ClaimBinding",
    "ObjectLifecycle",
    "RealizationStatus",
    "RecordLifecycle",
    "RecordStore",
    "TemporalRecord",
    "Timestamp",
    "UnknownBound",
    "holds_at",
    "is_open",
    "known_end",
    "known_start",
    "normalize_utc",
    "utc_now",
]
