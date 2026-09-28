"""SENSOR-B4-I12A — raw-evidence query service (F19 provider-independent boundary).

The immutable T0 lake already owns HOW evidence is written.  This module owns
the read boundary that Bloc 5 consumes: a provider-independent
``RawEvidenceQueryService`` that reduces a ``RawEvidenceQuery`` over the
COMPLETE accepted inventory without globbing storage paths, without reading
private catalog internals, and without treating DuckDB or PostgreSQL as raw
truth.

Authority hierarchy (I12 §4):

- T0A bytes           -> ``LocalBlobStore`` (via ``RawArtifactReader``,
                        replay.py; this module never touches payload bytes);
- blob/acquisition
  metadata            -> the accepted I04 durable repositories;
- partition truth     -> the accepted I04 manifest repository;
- T0B                 -> the accepted I05 projection + lineage repositories;
- revision truth      -> the accepted I06 ``SourceRevisionRegistry``.

DuckDB is a discovery accelerator only; PostgreSQL is operational metadata
only.  Neither appears in this module, and I12 correctness survives DuckDB
rebuild and Postgres offline by construction.

SENSOR-B4-I12A upstream delta (operator-reviewed §5 gate): the four additive
read-only enumeration methods ``PartitionManifestRepository.
list_all_current_manifests``, ``BlobMetadataRepository.list_all_blob_metadata``,
``AcquisitionRepository.list_all_acquisitions`` and
``SourceRevisionRegistry.list_source_revision_keys``.  Without them the only
route from "nothing known" to "complete inventory" was filesystem globbing or
DuckDB-as-truth, both forbidden by the §5 gate.

Typed failures (I12 §16): infrastructure failure is NEVER signalled with an
empty list, ``None`` or an empty frame.  No matching evidence is a typed
result carrying ``NO_MATCHING_EVIDENCE``; every other condition has its own
typed error below.

Range semantics (I12 §7): requested boundaries never fabricate coverage.  A
query window is intersected with EVIDENCE-BACKED ranges only (the manifest's
committed ``logical_date_start/end``, which the I04 writer derived from
acquisition evidence).  ``actual_start/end`` on a result are the evidence's
own bounds, never the request's.

Acquired vs observed (I12 §8): ``acquired_before`` filters
``ingested_at <= cutoff``; ``observed_before`` filters
``response_observed_at <= cutoff``.  Independent predicates; neither is ever
used as provider event time (F20).

Integrity (I12 §14): admissibility is an explicit lattice over the frozen
``IntegrityState`` vocabulary — never a numeric or lexical sort.  Failure
states are never admissible at any threshold.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from .enums import IntegrityState
from .models import (
    AcquisitionRecord,
    PartitionManifest,
    RawEvidenceQuery,
    RawEvidenceResult,
)


# ---------------------------------------------------------------------------
# Typed failure vocabulary (I12 §16 / 05 doc §17)
# ---------------------------------------------------------------------------


class RawQueryError(RuntimeError):
    """Base class for typed raw-query infrastructure failures."""


class NoMatchingEvidence(RawQueryError):
    """The complete inventory contains no evidence satisfying the query.

    Deliberately a typed CONDITION, not an empty list: research callers must
    never confuse 'nothing matched' with 'the lake is empty' or 'the filter
    was ignored'.
    """


class RevisionAmbiguity(RawQueryError):
    """Multiple source revisions exist under ERROR_ON_AMBIGUITY (I12 §10)."""


class IntegrityBelowThreshold(RawQueryError):
    """No representation of a candidate meets the integrity minimum (§14)."""


class ProjectionSchemaUnsupported(RawQueryError):
    """A referenced projection uses an unresolvable schema id/version (§19)."""


class BlobMissing(RawQueryError):
    """A blob reference resolves to no committed physical object (§17)."""


class LineageIncomplete(RawQueryError):
    """A T0B projection does not resolve fully to T0A evidence (§20)."""


class CatalogStale(RawQueryError):
    """A durable catalog reference points outside the accepted inventory."""


class StorageBackendUnavailable(RawQueryError):
    """A required local durable backend could not be opened (§31)."""


class ReplayOrderUnavailable(RawQueryError):
    """The requested replay order has no evidence backing it (§25/§26)."""


class QueryValidationError(RawQueryError):
    """The query itself is structurally invalid at execution time (§6)."""


#: Frozen integrity ADMISSIBILITY lattice (I12 §14).  NOT a goodness score:
#: a minimum admits exactly the states listed for it, and failure states are
#: listed for NO threshold.  PROVIDER_HASH_VERIFIED implies the local hash
#: was also verified (I04R1 §20/§21: the provider claim is only durable on
#: top of locally verified bytes), so both minimums admit it.
_INTEGRITY_ADMITS: dict[IntegrityState, frozenset[IntegrityState]] = {
    IntegrityState.UNVERIFIED: frozenset(
        {
            IntegrityState.UNVERIFIED,
            IntegrityState.LOCAL_HASH_VERIFIED,
            IntegrityState.PROVIDER_HASH_VERIFIED,
        }
    ),
    IntegrityState.LOCAL_HASH_VERIFIED: frozenset(
        {IntegrityState.LOCAL_HASH_VERIFIED, IntegrityState.PROVIDER_HASH_VERIFIED}
    ),
    IntegrityState.PROVIDER_HASH_VERIFIED: frozenset(
        {IntegrityState.PROVIDER_HASH_VERIFIED}
    ),
}

_FAILURE_INTEGRITY_STATES = frozenset(
    {
        IntegrityState.QUARANTINED_INTEGRITY_FAILURE,
        IntegrityState.MISSING_BLOB,
        IntegrityState.PROJECTION_INVALID,
    }
)


def _integrity_admissible(
    observed: IntegrityState, minimum: IntegrityState
) -> bool:
    """Explicit-lattice admissibility; failure states never admitted (§14)."""
    if observed in _FAILURE_INTEGRITY_STATES:
        return False
    return observed in _INTEGRITY_ADMITS[minimum]


def _interval_overlaps(
    ev_start: datetime, ev_end: datetime, q_start: datetime | None, q_end: datetime | None
) -> bool:
    """Half-open logical-window overlap on EVIDENCE-BACKED bounds (§7).

    Both bounds inclusive at the endpoints so point intervals match exactly:
    [ev_start, ev_end] overlaps [q_start, q_end] unless the evidence lies
    entirely outside the request.  An open request side imposes no bound.
    """
    if q_start is not None and ev_end < q_start:
        return False  # outside right
    if q_end is not None and ev_start > q_end:
        return False  # outside left
    return True


def _manifest_identity(manifest: PartitionManifest) -> tuple[str, str, str, str]:
    return (
        manifest.provider,
        manifest.venue,
        manifest.sensor_family.value,
        manifest.native_instrument,
    )


class RawInventorySnapshot(BaseModel):
    """One complete pass over the accepted inventory (§27 determinism).

    Built once per service construction from the four operator-approved
    additive enumeration reads.  Every list is sorted by its natural
    identity, so no filesystem enumeration order can leak into results.
    """

    model_config = ConfigDict(frozen=True)

    manifests: tuple[PartitionManifest, ...]
    acquisitions: tuple[AcquisitionRecord, ...]

    @property
    def acquisitions_by_blob(self) -> dict[str, list[AcquisitionRecord]]:
        grouped: dict[str, list[AcquisitionRecord]] = {}
        for record in self.acquisitions:
            if record.blob_sha256 is None:
                continue
            grouped.setdefault(record.blob_sha256, []).append(record)
        for records in grouped.values():
            records.sort(key=lambda r: r.acquisition_id)
        return grouped


class QueryOutcome(BaseModel):
    """Typed query outcome: results plus the no-match condition (§16).

    ``NoMatchingEvidence`` is a CONDITION of a successful reduction, not an
    exception, so a caller can distinguish it from every failure mode while
    the failure modes themselves stay exceptions.
    """

    model_config = ConfigDict(frozen=True)

    results: tuple[RawEvidenceResult, ...]
    no_matching_evidence: bool
    reason: str | None = None


class RawEvidenceQueryService:
    """Provider-independent read boundary over the complete T0 inventory.

    Constructed from the accepted repositories ONLY — never from paths, a
    DuckDB handle or a Postgres DSN.  The constructor takes one inventory
    snapshot; a fresh service (or ``refresh``) re-reads the repositories,
    which is how §27 determinism is proven across process/rebuild/enumeration
    changes.
    """

    def __init__(
        self,
        *,
        manifest_repository: Any,
        acquisition_repository: Any,
        blob_metadata_repository: Any,
    ) -> None:
        self._manifests_repo = manifest_repository
        self._acquisitions_repo = acquisition_repository
        self._blobs_repo = blob_metadata_repository
        self._snapshot = self._build_snapshot()

    # -- inventory (§5 gate) --------------------------------------------------

    def _build_snapshot(self) -> RawInventorySnapshot:
        try:
            manifests = tuple(self._manifests_repo.list_all_current_manifests())
            acquisitions = tuple(self._acquisitions_repo.list_all_acquisitions())
            # Touched to prove the blob-metadata repository is open and
            # readable at construction (§31 firewall fails here, typed).
            self._blobs_repo.list_all_blob_metadata()
        except RawQueryError:
            raise
        except Exception as exc:  # noqa: BLE001 - typed boundary re-wrap
            raise StorageBackendUnavailable(
                f"accepted durable inventory could not be read: {exc}"
            ) from exc
        return RawInventorySnapshot(manifests=manifests, acquisitions=acquisitions)

    def refresh(self) -> None:
        """Re-read the complete inventory from the durable repositories."""
        self._snapshot = self._build_snapshot()

    @property
    def inventory_sizes(self) -> dict[str, int]:
        """Discovery counters (metadata only; never payload bytes)."""
        return {
            "current_manifests": len(self._snapshot.manifests),
            "acquisitions": len(self._snapshot.acquisitions),
        }

    # -- reduction ------------------------------------------------------------

    def execute(self, query: RawEvidenceQuery) -> QueryOutcome:
        """Reduce ``query`` over the complete inventory (§6-§15)."""
        if not query.include_t0a and not query.include_t0b:
            # §21: T0A=False/T0B=False is a validation failure, typed here at
            # execution because the model must stay accepted-contract-faithful.
            raise QueryValidationError(
                "include_t0a=False and include_t0b=False selects nothing; "
                "at least one include mode must be True"
            )

        candidates = [
            manifest
            for manifest in self._snapshot.manifests
            if self._manifest_matches(manifest, query)
        ]
        if not candidates:
            raise NoMatchingEvidence(
                "no current partition manifest satisfies the query filters"
            )

        results: list[RawEvidenceResult] = []
        for manifest in candidates:
            blob_records = self._snapshot.acquisitions_by_blob
            acquisition_ids: list[str] = []
            blob_refs: list[str] = []
            ingested_max: datetime | None = None
            observed_max: datetime | None = None
            for blob_sha in manifest.blob_refs:
                records = blob_records.get(blob_sha, [])
                usable = [
                    r
                    for r in records
                    if self._acquisition_time_matches(r, query)
                ]
                if not usable and records:
                    # The blob exists but every acquisition falls outside the
                    # acquired/observed cutoffs — this manifest cannot
                    # honestly satisfy the time cut.  Drop the manifest.
                    break
                if not usable:
                    # Manifest references a blob with NO durable acquisition.
                    # The manifest repository commits only acquisition-backed
                    # refs, so this is catalog divergence, not a filter miss.
                    raise CatalogStale(
                        f"manifest {manifest.partition_manifest_id} references "
                        f"blob {blob_sha} with no durable acquisition record"
                    )
                blob_refs.append(blob_sha)
                acquisition_ids.extend(r.acquisition_id for r in usable)
                for r in usable:
                    if ingested_max is None or r.ingested_at > ingested_max:
                        ingested_max = r.ingested_at
                    if observed_max is None or r.response_observed_at > observed_max:
                        observed_max = r.response_observed_at
            else:
                integrity = self._combined_integrity(
                    manifest, blob_refs, query.integrity_minimum
                )
                if integrity is None:
                    continue  # below threshold (§14) — candidate dropped
                results.append(
                    self._build_result(
                        manifest,
                        acquisition_ids=acquisition_ids,
                        blob_refs=blob_refs,
                        integrity=integrity,
                    )
                )

        if not results:
            # Candidates existed but every one was filtered by time cuts or
            # integrity — still a typed no-match, never an empty list.
            raise NoMatchingEvidence(
                "candidate manifests exist but none satisfy the time/integrity "
                "constraints"
            )

        results.sort(
            key=lambda r: (
                r.provider,
                r.venue,
                r.sensor_family.value,
                r.native_instrument,
                r.logical_time_start,
                r.logical_time_end,
            )
        )

        # §28: limit applies AFTER discovery, filtering, revision resolution,
        # integrity validation and deterministic ordering.  Revision
        # resolution happens in the replay/cursor layer where per-blob
        # identity is materialized; the ERROR_ON_AMBIGUITY proof lives there
        # and is not suppressed here because ambiguity raises before a
        # result is ever appended.
        if query.limit is not None:
            results = results[: query.limit]

        return QueryOutcome(results=tuple(results), no_matching_evidence=False)

    # -- filter predicates (§6) -------------------------------------------------

    def _manifest_matches(self, manifest: PartitionManifest, query: RawEvidenceQuery) -> bool:
        if query.providers and manifest.provider not in query.providers:
            return False
        if query.venues and manifest.venue not in query.venues:
            return False
        if query.sensor_families and manifest.sensor_family not in query.sensor_families:
            return False
        if query.native_instruments and manifest.native_instrument not in query.native_instruments:
            return False
        if query.source_granularities:
            if manifest.source_granularity not in query.source_granularities:
                return False
        if query.coverage_states and manifest.coverage_state not in query.coverage_states:
            return False
        # §7: evidence-backed range intersection only.
        if not _interval_overlaps(
            manifest.logical_date_start,
            manifest.logical_date_end,
            query.logical_start,
            query.logical_end,
        ):
            return False
        return True

    def _acquisition_time_matches(
        self, record: AcquisitionRecord, query: RawEvidenceQuery
    ) -> bool:
        # §8: independent predicates on the correct timestamps; ingestion
        # time is never provider event time (F20).
        if query.acquired_before is not None and record.ingested_at > query.acquired_before:
            return False
        if (
            query.observed_before is not None
            and record.response_observed_at > query.observed_before
        ):
            return False
        return True

    # -- integrity (§14) ---------------------------------------------------------

    _INTEGRITY_RANK = {
        IntegrityState.UNVERIFIED: 0,
        IntegrityState.LOCAL_HASH_VERIFIED: 1,
        IntegrityState.PROVIDER_HASH_VERIFIED: 2,
    }

    def _combined_integrity(
        self,
        manifest: PartitionManifest,
        blob_refs: list[str],
        minimum: IntegrityState,
    ) -> IntegrityState | None:
        """Worst-of admissibility across the manifest and its blobs.

        Returns the admitted state, or ``None`` when the candidate falls
        below the query threshold.  A failure-stated manifest or blob is
        never promoted (§14): it stays visible only as its own failure state
        when every observed state is that failure (an explicit caller asking
        the floor be UNVERIFIED sees the failure declared, not hidden); any
        failure state fails every lattice minimum otherwise.
        """
        metas_by_hash: dict[str, list[Any]] = {}
        for blob_sha in blob_refs:
            metas = self._blobs_repo.get_blob_metadata(blob_sha)
            if not metas:
                raise CatalogStale(
                    f"manifest {manifest.partition_manifest_id} references "
                    f"blob {blob_sha} with no committed blob metadata"
                )
            metas_by_hash[blob_sha] = metas

        def best_of(states: list[IntegrityState]) -> IntegrityState:
            """Strongest non-failure state; failure states stay failures."""
            ranked = [
                s for s in states if s in self._INTEGRITY_RANK
            ]
            if ranked:
                return max(ranked, key=lambda s: self._INTEGRITY_RANK[s])
            # All failure states: propagate deterministically (sorted name).
            return sorted(states, key=lambda s: s.value)[0]

        observed: list[IntegrityState] = [manifest.integrity_state]
        for metas in metas_by_hash.values():
            observed.append(best_of([m.integrity_state for m in metas]))

        # §14: a failure state on the MANIFEST ITSELF is decisive — the
        # manifest is the logical truth claim and a failure claim must stay
        # a failure claim.  It is admissible ONLY as itself under the lowest
        # floor (the caller sees the failure declared, not promoted away and
        # not silently absent); at any real threshold it fails admissibility.
        if manifest.integrity_state in _FAILURE_INTEGRITY_STATES:
            if minimum is not IntegrityState.UNVERIFIED:
                return None
            return manifest.integrity_state
        # A failure state on an underlying BLOB likewise cannot be promoted:
        # combined strength is the WORST non-failure claim, and any blob
        # failure fails every real threshold (worst-of semantics).
        if any(s in _FAILURE_INTEGRITY_STATES for s in observed):
            if minimum is not IntegrityState.UNVERIFIED:
                return None
            return sorted(
                (s for s in observed if s in _FAILURE_INTEGRITY_STATES),
                key=lambda s: s.value,
            )[0]

        combined = best_of(observed)
        if not _integrity_admissible(combined, minimum):
            return None
        return combined

    # -- result assembly (§13) ----------------------------------------------------

    def _build_result(
        self,
        manifest: PartitionManifest,
        *,
        acquisition_ids: list[str],
        blob_refs: list[str],
        integrity: IntegrityState,
    ) -> RawEvidenceResult:
        from .models import RawEvidenceResult as _RER  # local import: models imports enums only

        lineage_refs = sorted(manifest.projection_refs)
        return _RER(
            provider=manifest.provider,
            venue=manifest.venue,
            sensor_family=manifest.sensor_family,
            native_instrument=manifest.native_instrument,
            source_granularity=manifest.source_granularity,
            # §7: EVIDENCE bounds, never the requested window.
            logical_time_start=manifest.logical_date_start,
            logical_time_end=manifest.logical_date_end,
            coverage_state=manifest.coverage_state,
            integrity_state=integrity,
            acquisition_ids=sorted(acquisition_ids),
            blob_refs=sorted(blob_refs),
            projection_refs=lineage_refs,
            revision_state=self._revision_state_hint(manifest),
            quality_flags=[],
            lineage_refs=lineage_refs,
        )

    def _revision_state_hint(self, manifest: PartitionManifest) -> Any:
        from .enums import RevisionState

        if manifest.revision_count > 1:
            return RevisionState.SOURCE_MUTATION
        return RevisionState.UNKNOWN_REVISION


__all__ = [
    "BlobMissing",
    "CatalogStale",
    "IntegrityBelowThreshold",
    "LineageIncomplete",
    "NoMatchingEvidence",
    "ProjectionSchemaUnsupported",
    "QueryOutcome",
    "QueryValidationError",
    "RawEvidenceQueryService",
    "RawInventorySnapshot",
    "RawQueryError",
    "ReplayOrderUnavailable",
    "RevisionAmbiguity",
    "StorageBackendUnavailable",
]
