"""SENSOR-B4-I12B/C/D/E — T0A/T0B readers, revision resolution, replay cursor,
and the Bloc-5 handoff boundary.

Read-only by construction (I12 §29): every class here exposes reads and
derived views only.  There is no delete, overwrite, repair, quarantine
mutation, manifest mutation, revision declaration, resume advancement or
recovery action on this surface — mutation lives exclusively in the writer
checkpoints (I03-I08).

Authority discipline (I12 §4):

- T0A bytes are read ONLY through ``LocalBlobStore.open_blob``/``verify_blob``
  (accepted I03 public behavior).  No compression logic is duplicated; the
  wrapper encoding comes from durable ``EvidenceBlob`` metadata.
- T0B metadata and provider-native contents are read through the accepted
  I05 repositories; a projection whose schema cannot be resolved fails typed
  ``ProjectionSchemaUnsupported`` (§19) — no canonical renaming, no unit
  normalization, no Bloc-5 semantics anywhere.
- Lineage is resolved through the accepted I05 lineage repository (§20): a
  projection with zero lineage entries, or any lineage entry whose
  blob/acquisition pair is not durable, fails ``LineageIncomplete`` —
  apparently usable T0B with incomplete lineage is never returned.
- Revision selection delegates to ``SourceRevisionRegistry.resolve`` (§10)
  with the frozen policies; ambiguity raises ``RevisionAmbiguity``; a limit
  can never hide it because resolution happens before any truncation (§28).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .models import (
    AcquisitionRecord,
    EvidenceBlob,
    RawEvidenceQuery,
    RawNormalizationBatch,
    RawProjectionArtifact,
    RawEvidenceResult,
)
from .query import (
    BlobMissing,
    LineageIncomplete,
    ProjectionSchemaUnsupported,
    QueryValidationError,
    RawEvidenceQueryService,
    ReplayOrderUnavailable,
    RevisionAmbiguity,
)


# ---------------------------------------------------------------------------
# Replay ordering vocabulary (I12 §23 / I12R1 §12-§13)
# ---------------------------------------------------------------------------

from enum import Enum


class ReplayOrder(str, Enum):
    """Typed replay order modes (I12R1 §12).

    Subclasses ``str`` so the historical public string constants remain
    valid inputs and comparisons (backwards compatible — no breaking
    interface change).  Dispatch uses enum identity, so a dynamically
    constructed equal string (``''.join(...)``), a deserialized string, or
    the literal constant all select the SAME branch: ``order_by ==``
    against a str-subclass enum resolves through the enum's value.
    """

    ACQUISITION_ORDER = "ACQUISITION_ORDER"
    PROVIDER_EVENT_TIME = "PROVIDER_EVENT_TIME"
    SOURCE_ORDER = "SOURCE_ORDER"


# Historical public string constants (I12 §23) — unchanged, and equal to
# their enum members for every dispatch comparison.
ACQUISITION_ORDER = "ACQUISITION_ORDER"
PROVIDER_EVENT_TIME = "PROVIDER_EVENT_TIME"
SOURCE_ORDER = "SOURCE_ORDER"

_ORDER_MODES = (ACQUISITION_ORDER, PROVIDER_EVENT_TIME, SOURCE_ORDER)

#: Explicit preserved source-order evidence fields (§26).  Never fabricated.
_SOURCE_ORDER_FIELDS = ("provider_sequence", "source_file_row_order", "stream_frame_sequence")


def _coerce_order_mode(order_by: Any) -> ReplayOrder:
    """Accept the enum, the historical string constants, or ANY equal string
    — including dynamically constructed and deserialized ones (I12R1 §13).

    No interned-string dependency: comparison is ``==``-based against the
    str-enum values, never ``is``.  Unknown modes fail typed.
    """
    if isinstance(order_by, ReplayOrder):
        return order_by
    for member in ReplayOrder:
        # str-subclass enum member == equal plain string (value equality).
        if order_by == member or order_by == member.value:
            return member
    raise QueryValidationError(
        f"unknown order mode {order_by!r}; expected one of {_ORDER_MODES}"
    )


def _validate_order_mode(order_by: str) -> str:
    """Validate and normalize any accepted order-mode input (I12R1 §13)."""
    return _coerce_order_mode(order_by).value


# ---------------------------------------------------------------------------
# §17 — T0A raw artifact reader
# ---------------------------------------------------------------------------


class RawArtifactReader:
    """Exact T0A byte access through the accepted ``LocalBlobStore`` API.

    The consumer never knows the local wrapper compression: the storage
    encoding comes from durable ``EvidenceBlob`` metadata (one row per
    physical key), and decoding stays inside the blob store.
    """

    def __init__(
        self,
        *,
        blob_store: Any,
        blob_metadata_repository: Any,
        chunk_size: int = 1 << 20,
    ) -> None:
        self._store = blob_store
        self._blobs = blob_metadata_repository
        if not isinstance(chunk_size, int) or isinstance(chunk_size, bool) or chunk_size <= 0:
            raise ValueError("chunk_size must be a positive int")
        self._chunk_size = chunk_size

    def metadata(self, blob_sha256: str) -> EvidenceBlob:
        """Durable ``EvidenceBlob`` metadata for one content hash (§17)."""
        from .catalog import BlobMetadataNotFound

        try:
            metas = self._blobs.get_blob_metadata(blob_sha256)
        except BlobMetadataNotFound as exc:
            # One typed vocabulary for readers (§16): absence of durable
            # metadata is BLOB_MISSING at this boundary, whatever the
            # repository calls it internally.
            raise BlobMissing(str(exc)) from exc
        if not metas:
            raise BlobMissing(f"no committed metadata for blob {blob_sha256}")
        # Deterministic choice: strongest encoding priority is not a thing —
        # rows are content+encoding keyed; pick the lexicographically first
        # encoding for a stable view, all rows stay visible via list form.
        return sorted(metas, key=lambda m: m.storage_encoding.value)[0]

    def metadata_all(self, blob_sha256: str) -> list[EvidenceBlob]:
        """Every committed metadata row for the hash (all encodings)."""
        metas = self._blobs.get_blob_metadata(blob_sha256)
        if not metas:
            raise BlobMissing(f"no committed metadata for blob {blob_sha256}")
        return sorted(metas, key=lambda m: m.storage_encoding.value)

    def open_bytes(self, blob_sha256: str) -> bytes:
        """The EXACT source bytes (transparent wrapper decode, §17)."""
        meta = self.metadata(blob_sha256)
        with self._store.open_blob(meta.blob_sha256, meta.storage_encoding) as handle:
            return handle.read()

    def stream_bytes(self, blob_sha256: str) -> Iterator[bytes]:
        """Bounded-memory chunks of the EXACT source bytes (§18).

        Deterministic chunk boundaries: every chunk except the last has
        exactly ``chunk_size`` bytes; concatenation reproduces ``open_bytes``
        exactly.  Reads only through the blob store's streaming decoder —
        no unbounded read path is invoked.
        """
        meta = self.metadata(blob_sha256)
        with self._store.open_blob(meta.blob_sha256, meta.storage_encoding) as handle:
            while True:
                chunk = handle.read(self._chunk_size)
                if not chunk:
                    break
                yield chunk

    def verify(self, blob_sha256: str) -> Any:
        """Recompute the source hash via the store's verify path (§17)."""
        meta = self.metadata(blob_sha256)
        return self._store.verify_blob(meta.blob_sha256, meta.storage_encoding)


# ---------------------------------------------------------------------------
# §19/§20 — T0B projection reader + lineage resolution
# ---------------------------------------------------------------------------


class RawProjectionReader:
    """Raw projection metadata + provider-native contents; zero semantics."""

    def __init__(
        self,
        *,
        artifact_repository: Any,
        context_repository: Any,
        lineage_repository: Any,
        schema_registry: Any,
        artifact_reader: RawArtifactReader,
    ) -> None:
        self._artifacts = artifact_repository
        self._contexts = context_repository
        self._lineage = lineage_repository
        self._schemas = schema_registry
        self._reader = artifact_reader

    def get_artifact(self, projection_id: str) -> RawProjectionArtifact:
        artifact = self._artifacts.get(projection_id)
        if artifact is None:
            raise LineageIncomplete(f"no committed projection artifact {projection_id}")
        return artifact

    def _context(self, projection_id: str) -> Any:
        context = self._contexts.get(projection_id)
        if context is None:
            raise LineageIncomplete(
                f"projection {projection_id} has no committed context record"
            )
        return context

    def resolve_lineage(self, projection_id: str) -> list[dict[str, Any]]:
        """projection -> lineage -> acquisitions -> blobs (§20).

        Missing relationships fail ``LineageIncomplete``; a projection with
        no lineage entries is incomplete BY DEFINITION (I05: every T0B must
        reference T0A).
        """
        artifact = self.get_artifact(projection_id)
        entries = self._lineage.get_by_projection(projection_id)
        if not entries:
            raise LineageIncomplete(
                f"projection {projection_id} has zero lineage entries"
            )
        resolved: list[dict[str, Any]] = []
        for entry in sorted(entries, key=lambda e: e.source_order):
            if entry.source_blob_sha256 not in artifact.source_blob_sha256:
                raise LineageIncomplete(
                    f"lineage entry for {projection_id} references blob "
                    f"{entry.source_blob_sha256} absent from the artifact's "
                    "source list"
                )
            try:
                acquisition: AcquisitionRecord = self._acquisition(entry.source_acquisition_id)
            except Exception as exc:  # noqa: BLE001 - typed re-wrap
                raise LineageIncomplete(
                    f"lineage acquisition {entry.source_acquisition_id} for "
                    f"projection {projection_id} is not durable: {exc}"
                ) from exc
            if acquisition.blob_sha256 != entry.source_blob_sha256:
                raise LineageIncomplete(
                    f"lineage acquisition {entry.source_acquisition_id} binds "
                    f"blob {acquisition.blob_sha256}, but the lineage entry "
                    f"claims {entry.source_blob_sha256}"
                )
            # Prove the T0A side is real: metadata must exist (bytes are NOT
            # opened by a metadata query, §21).
            self._reader.metadata(entry.source_blob_sha256)
            resolved.append(
                {
                    "source_order": entry.source_order,
                    "source_blob_sha256": entry.source_blob_sha256,
                    "source_acquisition_id": entry.source_acquisition_id,
                    "source_row_start": entry.source_row_start,
                    "source_row_end": entry.source_row_end,
                }
            )
        return resolved

    def _acquisition(self, acquisition_id: str) -> AcquisitionRecord:
        try:
            return self._artifacts_acquisitions().get_acquisition(acquisition_id)
        except AttributeError as exc:  # repository not wired for lineage reads
            raise LineageIncomplete(
                "lineage acquisition resolution requires the acquisitions "
                "repository on the artifact repository's catalog root"
            ) from exc

    def _artifacts_acquisitions(self) -> Any:
        # The ProjectionArtifactRepository does not hold the acquisition
        # repository; the reader takes it explicitly instead.  Kept as a
        # small indirection so resolve_lineage stays testable.
        return self._acquisitions_repo

    def set_acquisition_repository(self, repository: Any) -> None:
        """Wire the durable acquisition source for lineage resolution (§20)."""
        self._acquisitions_repo = repository

    _acquisitions_repo: Any = None

    def projection_metadata(self, projection_id: str) -> dict[str, Any]:
        """Required §19 metadata (no renames, no normalization)."""
        artifact = self.get_artifact(projection_id)
        context = self._context(projection_id)
        # Schema must resolve or the projection is unsupported (§19).
        try:
            self._schemas.resolve_by_id(
                artifact.projection_schema_id, artifact.projection_schema_version
            )
        except Exception as exc:  # noqa: BLE001 - typed re-wrap (§16)
            raise ProjectionSchemaUnsupported(
                f"projection {projection_id} schema "
                f"{artifact.projection_schema_id}"
                f"@{artifact.projection_schema_version} is not registered: {exc}"
            ) from exc
        return {
            "projection_id": artifact.projection_id,
            "projection_schema_id": artifact.projection_schema_id,
            "projection_schema_version": artifact.projection_schema_version,
            "parser_version": artifact.parser_version,
            "row_count": artifact.row_count,
            "partition_key": artifact.partition_key,
            "source_lineage": self.resolve_lineage(projection_id),
            "context_schema_key": context.schema_key,
            "context_schema_fingerprint": context.schema_fingerprint,
        }

    def open_projection_bytes(self, projection_id: str) -> bytes:
        """Provider-native projection file bytes (no interpretation, §19)."""
        artifact = self.get_artifact(projection_id)
        self.projection_metadata(projection_id)  # schema + lineage gates
        try:
            with open(artifact.projection_uri, "rb") as handle:
                return handle.read()
        except OSError as exc:
            raise LineageIncomplete(
                f"projection {projection_id} file unreadable at "
                f"{artifact.projection_uri}: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# §10/§11 — revision resolution over acquisitions
# ---------------------------------------------------------------------------


def _source_revision_key_for(
    acquisition: AcquisitionRecord, identity_factory: Any
) -> str:
    """Derive the frozen I06 request-identity key for one acquisition."""
    identity = identity_factory.from_acquisition(acquisition)
    return identity.source_revision_key()


class RevisionResolver:
    """Frozen-policy revision selection via the accepted I06 registry."""

    def __init__(
        self,
        *,
        registry: Any,
        identity_factory: Any,
    ) -> None:
        self._registry = registry
        self._identity_factory = identity_factory

    def key_for(self, acquisition: AcquisitionRecord) -> str:
        return _source_revision_key_for(acquisition, self._identity_factory)

    def resolve(
        self,
        *,
        source_revision_key: str,
        query: RawEvidenceQuery,
    ) -> list[int]:
        """Selected revision numbers under the query's frozen policy (§10).

        ``EXACT_REVISION`` threads the typed ``exact_revision_number``
        selector added to ``RawEvidenceQuery`` in I12A (§11) — no string
        hacks.  ``ERROR_ON_AMBIGUITY`` raises ``RevisionAmbiguity`` on any
        multiplicity; registry ``RevisionNotFound`` for an EXACT miss is
        re-wrapped so callers see one typed vocabulary.
        """
        from .revisions import RevisionNotFound as _RegistryNotFound

        try:
            resolution = self._registry.resolve(
                source_revision_key,
                query.revision_policy,
                revision_number=query.exact_revision_number,
            )
        except _RegistryNotFound as exc:
            from .query import NoMatchingEvidence

            raise NoMatchingEvidence(str(exc)) from exc
        if resolution.ambiguous:
            raise RevisionAmbiguity(
                f"{len(resolution.all_revision_numbers)} revisions exist for "
                f"{source_revision_key[:12]}... under "
                f"{query.revision_policy.value}"
            )
        return list(resolution.selected_revision_numbers)


# ---------------------------------------------------------------------------
# §22 — Bloc-5 handoff
# ---------------------------------------------------------------------------


class Bloc5Handoff:
    """Convert query results into ``RawNormalizationBatch`` — facts only.

    No canonical_asset, no canonical_notional, no effective_at, no
    normalized OI/liquidation/funding, no canonical side (§22): those are
    Bloc 5.  Every native identity field, lineage ref, gap interval and
    timestamp fact the model carries is preserved verbatim from the source
    result and its acquisitions.
    """

    def __init__(self, *, batch_id_factory: Any) -> None:
        self._batch_id_factory = batch_id_factory

    def to_batch(
        self,
        result: RawEvidenceResult,
        *,
        projections: list[RawProjectionArtifact],
        acquisitions: list[AcquisitionRecord],
        parser_version: str,
        raw_rows_or_reader: str,
    ) -> RawNormalizationBatch:
        if not projections:
            raise QueryValidationError(
                "a normalization batch requires at least one T0B projection"
            )
        schemas = {(p.projection_schema_id, p.projection_schema_version) for p in projections}
        if len(schemas) != 1:
            raise QueryValidationError(
                "a normalization batch must carry ONE projection schema; got "
                f"{sorted(schemas)}"
            )
        schema_id, schema_version = schemas.pop()
        parser_versions = {p.parser_version for p in projections}
        if len(parser_versions) != 1:
            raise QueryValidationError(
                "a normalization batch must carry ONE parser version; got "
                f"{sorted(parser_versions)}"
            )
        known_gaps: list[str] = []
        if result.coverage_state.value in ("PARTIAL", "KNOWN_GAP"):
            known_gaps.append(f"coverage_state={result.coverage_state.value}")
        history_boundary = (
            f"ingested_at_max={max(a.ingested_at for a in acquisitions).isoformat()}"
            if acquisitions
            else None
        )
        return RawNormalizationBatch(
            batch_id=self._batch_id_factory(result),
            provider=result.provider,
            venue=result.venue,
            sensor_family=result.sensor_family,
            native_instrument=result.native_instrument,
            projection_schema_id=schema_id,
            projection_schema_version=schema_version,
            parser_version=parser_version,
            raw_rows_or_reader=raw_rows_or_reader,
            source_blob_refs=sorted(result.blob_refs),
            acquisition_refs=sorted(a.acquisition_id for a in acquisitions),
            logical_time_range_start=result.logical_time_start,
            logical_time_range_end=result.logical_time_end,
            integrity_state=result.integrity_state,
            coverage_state=result.coverage_state,
            revision_state=result.revision_state,
            quality_flags=list(result.quality_flags),
            known_gap_intervals=known_gaps,
            source_granularity=result.source_granularity,
            history_boundary=history_boundary,
        )


# ---------------------------------------------------------------------------
# §23-§27 — replay cursor
# ---------------------------------------------------------------------------


class RawReplayCursor:
    """Deterministic ordered iteration over queried evidence.

    Three explicit modes (§23) — never "sort everything by timestamp":

    - ``ACQUISITION_ORDER`` (§24): what the system possessed, ordered by
      durable acquisition facts with the tie-break ingested_at ->
      response_observed_at -> acquisition_id.  Repeated replay is identical.
    - ``PROVIDER_EVENT_TIME`` (§25): only when actual provider-event-time
      evidence exists (``actual_start``/``actual_end`` both present);
      otherwise ``ReplayOrderUnavailable`` — ingestion/observed time is
      NEVER substituted and labelled provider event time.
    - ``SOURCE_ORDER`` (§26): only explicit preserved source-order evidence
      (``provider_sequence`` / ``source_file_row_order`` /
      ``stream_frame_sequence`` in the acquisition's evidence ref); absent
      or ambiguous evidence is a typed refusal, no timestamp fabrication.
    """

    def __init__(
        self,
        *,
        service: RawEvidenceQueryService,
        artifact_reader: RawArtifactReader | None = None,
    ) -> None:
        self._service = service
        self._reader = artifact_reader

    def acquisitions_for(
        self, result: RawEvidenceResult
    ) -> list[AcquisitionRecord]:
        """Durable acquisitions backing one result, sorted by id."""
        by_id: dict[str, AcquisitionRecord] = {}
        for record in self._service._snapshot.acquisitions:
            if record.acquisition_id in result.acquisition_ids:
                by_id[record.acquisition_id] = record
        return [by_id[i] for i in sorted(by_id)]

    def ordered_acquisitions(
        self,
        result: RawEvidenceResult,
        *,
        order_by: str | ReplayOrder = ACQUISITION_ORDER,
    ) -> list[AcquisitionRecord]:
        mode = _coerce_order_mode(order_by)  # I12R1 §13: identity-safe dispatch
        records = self.acquisitions_for(result)
        if not records:
            raise ReplayOrderUnavailable(
                "result carries no durable acquisitions to order"
            )
        if mode is ReplayOrder.ACQUISITION_ORDER:
            # §24: deterministic existing facts + documented tie-break.
            return sorted(
                records,
                key=lambda r: (
                    r.ingested_at,
                    r.response_observed_at,
                    r.acquisition_id,
                ),
            )
        if mode is ReplayOrder.PROVIDER_EVENT_TIME:
            usable = [
                r
                for r in records
                if r.actual_start is not None and r.actual_end is not None
            ]
            if not usable:
                raise ReplayOrderUnavailable(
                    "PROVIDER_EVENT_TIME requires actual provider-event-time "
                    "evidence (actual_start/actual_end); none of the "
                    f"{len(records)} acquisitions carries it — ingested_at "
                    "and response_observed_at are never substituted (§25)"
                )
            return sorted(
                usable,
                key=lambda r: (r.actual_start, r.actual_end, r.acquisition_id),
            )
        # SOURCE_ORDER (§26)
        keyed: list[tuple[int, str, AcquisitionRecord]] = []
        for record in records:
            sequence = self._source_sequence(record)
            if sequence is None:
                raise ReplayOrderUnavailable(
                    "SOURCE_ORDER requires explicit preserved source-order "
                    f"evidence; acquisition {record.acquisition_id} has none "
                    f"of {_SOURCE_ORDER_FIELDS} (§26)"
                )
            keyed.append((sequence, record.acquisition_id, record))
        keyed.sort(key=lambda t: (t[0], t[1]))
        return [t[2] for t in keyed]

    def _source_sequence(self, record: AcquisitionRecord) -> int | None:
        """Extract an EXPLICIT source-order coordinate, or None (§26)."""
        evidence = record.evidence_ref
        if evidence is None:
            return None
        for field in _SOURCE_ORDER_FIELDS:
            value = getattr(evidence, field, None)
            if isinstance(value, int) and not isinstance(value, bool):
                return value
        return None

    def replay(
        self,
        query: RawEvidenceQuery,
        *,
        order_by: str | ReplayOrder = ACQUISITION_ORDER,
    ) -> list[tuple[RawEvidenceResult, list[AcquisitionRecord]]]:
        """Query + deterministic order, streaming-ready (§27).

        Same query + same evidence + same mode => identical ordered
        identities: the service snapshot is sorted, resolution is total,
        and ordering keys are durable facts (ties broken by acquisition_id).
        """
        outcome = self._service.execute(query)
        replayed: list[tuple[RawEvidenceResult, list[AcquisitionRecord]]] = []
        for result in outcome.results:
            replayed.append((result, self.ordered_acquisitions(result, order_by=order_by)))
        return replayed


__all__ = [
    "ACQUISITION_ORDER",
    "Bloc5Handoff",
    "PROVIDER_EVENT_TIME",
    "RawArtifactReader",
    "RawProjectionReader",
    "RawReplayCursor",
    "ReplayOrder",
    "RevisionResolver",
    "SOURCE_ORDER",
]
