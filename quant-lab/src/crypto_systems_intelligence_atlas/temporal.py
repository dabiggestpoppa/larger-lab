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

    Construction invariants (fail-closed):

    - naive (timezone-less) bounds are rejected;
    - aware bounds are normalized to UTC;
    - ``earliest_bound <= latest_bound`` whenever both are present.

    Allowed explicit states: both bounds, earliest only, latest only, both
    absent. UNKNOWN never converts to OPEN and never fabricates a date.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: str = Field(default="UNKNOWN", frozen=True)
    earliest_bound: datetime | None = None
    latest_bound: datetime | None = None
    confidence_ref: str | None = None  # evidence pointer for the confidence claim

    def model_post_init(self, __context: object) -> None:
        earliest = self.earliest_bound
        latest = self.latest_bound
        if earliest is not None:
            if earliest.tzinfo is None:
                raise ValueError(
                    "UnknownBound.earliest_bound must be timezone-aware "
                    "(no naive datetimes)"
                )
            object.__setattr__(self, "earliest_bound", normalize_utc(earliest))
            earliest = self.earliest_bound
        if latest is not None:
            if latest.tzinfo is None:
                raise ValueError(
                    "UnknownBound.latest_bound must be timezone-aware "
                    "(no naive datetimes)"
                )
            object.__setattr__(self, "latest_bound", normalize_utc(latest))
            latest = self.latest_bound
        if earliest is not None and latest is not None and earliest > latest:
            raise ValueError(
                "UnknownBound invariant violated: earliest_bound > latest_bound"
            )

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
    """Shared record/claim lifecycle for Book 1 bindings and Book 2 claims.

    Book 1 originally exposed the Constitution §7 subset used by its
    kernel. Book 2's ratified state machine adds explicit inference,
    corroboration, unresolved, freshness, and supersession states. Keeping
    one enum prevents a provenance binding from silently losing that state.
    """

    DECLARED = "DECLARED"
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    VERIFIED = "VERIFIED"
    CORROBORATED = "CORROBORATED"
    CONTESTED = "CONTESTED"
    UNRESOLVED = "UNRESOLVED"
    STALE = "STALE"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


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
    """R6 as-of predicate with explicit UNKNOWN-bound semantics (R9).

    Truth table (no fabricated certainty):

    ============  ===========  ==========================================
    start         end          semantics
    ============  ===========  ==========================================
    KNOWN         KNOWN        normal interval logic (start inclusive)
    KNOWN         OPEN         True at/after start, False before
    KNOWN         UNKNOWN      False before start; None inside end
                               uncertainty; False after latest end bound
    UNKNOWN       OPEN         False before earliest start bound; None
                               within [earliest, latest) start bounds;
                               True at/after latest start bound
    UNKNOWN       UNKNOWN      False before earliest start; None while
                               start OR end uncertain; False after
                               latest end bound
    ============  ===========  ==========================================

    Returns True/False where decidable; ``None`` where UNKNOWN bounds make
    the answer undecidable at ``at`` (R9: queries see the uncertainty
    explicitly — never a silently-fabricated True).
    """
    # -- resolve start ------------------------------------------------------
    if isinstance(valid_from, UnknownBound):
        earliest = valid_from.earliest_bound
        latest_start = valid_from.latest_bound
        if earliest is not None and earliest > at:
            return False  # start certainly has not occurred yet
        if latest_start is None:
            start_decided = None  # no upper certainty bound: may or may not have begun
        elif latest_start <= at:
            start_decided = True  # start has necessarily occurred by at
        else:
            return None  # earliest <= at < latest: start uncertain
    else:
        if valid_from > at:
            return False
        start_decided = True

    # -- resolve end --------------------------------------------------------
    if valid_to is None:
        return start_decided
    if isinstance(valid_to, UnknownBound):
        latest_end = valid_to.latest_bound
        if latest_end is not None and latest_end <= at:
            return False  # ended certainly before at
        earliest_end = valid_to.earliest_bound
        if earliest_end is not None and earliest_end > at:
            # end certainly has not occurred yet — start decision stands
            return start_decided
        # end is uncertain at `at`: the fact may still hold or may have ended
        # inside the UNKNOWN window — undecidable regardless of start state.
        return None
    # KNOWN end
    if valid_to <= at:
        return False
    return start_decided


class RecordStore:
    """Append-only record store implementing R4/R5/R7/RC-1..RC-4 semantics.

    - ``add`` only; no delete or in-place mutation path exists (INV-1D-1);
    - records are STRICTLY immutable once committed — supersession metadata
      lives in store-level envelopes, never as in-place edits of a committed
      record (INV-1D-1: "no record is ever deleted or mutated in place");
    - corrections are *new records* with ``supersedes`` pointers;
    - ``current()`` = transaction-time filter R5;
    - ``as_known()`` = R7; ``as_of()`` filters valid time via :func:`holds_at`;
    - schema version participates in the replay key (RC-4).
    """

    def __init__(self, schema_version: str = "book1-v0.3") -> None:
        self._records: dict[str, TemporalRecord] = {}
        self._superseded_at: dict[str, datetime] = {}  # store-level txn metadata
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
        """Return the record (R4: queryable forever). ``superseded_at`` is
        overlaid from store metadata WITHOUT mutating the committed object."""
        record = self._records[record_id]
        ts = self._superseded_at.get(record_id)
        if ts is None or record.superseded_at == ts:
            return record
        return record.model_copy(update={"superseded_at": ts})

    def superseded_at(self, record_id: str) -> datetime | None:
        """Transaction-time supersession metadata for a record."""
        return self._superseded_at.get(record_id, self._records[record_id].superseded_at)

    def all_records(self) -> dict[str, TemporalRecord]:
        return {rid: self.get(rid) for rid in self._records}

    def supersede(self, old_id: str, new_id: str, new_record: TemporalRecord) -> None:
        """Record-level supersession: new record replaces the old *about the
        same claim*. The old record object is NEVER mutated — the supersession
        timestamp is recorded in store-level metadata (INV-1D-1)."""
        if old_id not in self._records:
            raise KeyError(f"unknown record {old_id}")
        if new_record.supersedes != old_id:
            raise ValueError("new_record.supersedes must reference the superseded id")
        self.add(new_id, new_record)
        self._superseded_at[old_id] = new_record.observed_at

    def current(self) -> list[tuple[str, TemporalRecord]]:
        """R5: current view = records not superseded (metadata view)."""
        return [
            (rid, self.get(rid))
            for rid in self._records
            if rid not in self._superseded_at
        ]

    def as_known(self, at: datetime) -> list[tuple[str, TemporalRecord]]:
        """R7: as-known view at transaction time ``at``."""
        at = normalize_utc(at)
        out: list[tuple[str, TemporalRecord]] = []
        for rid in self._records:
            r = self.get(rid)
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
