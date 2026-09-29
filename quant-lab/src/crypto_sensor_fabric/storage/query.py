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

SENSOR-B4-I12R1 — end-to-end query semantics (operator review §1-§11):

- Revision resolution is part of the PUBLIC query reduction.  ``execute``
  derives each candidate acquisition's source_revision_key through the
  accepted I06 identity law and delegates selection to the accepted
  ``SourceRevisionRegistry.resolve`` — never a duplicated policy.  The
  service accepts ``revision_registry`` + ``revision_identity_factory``;
  when they are absent, a query carrying a non-default revision policy is
  a typed validation failure, never a silently-ignored filter.
- Include modes are real representation selection: ``blob_refs`` is the
  selected/available T0A representation, ``projection_refs`` the selected
  T0B representation, ``lineage_refs`` the durable T0A sources required by
  the selected T0B.  Nothing is populated blindly from the manifest.
- ``projection_schema_ids`` is evaluated from durable projection METADATA
  only (no T0A payload bytes are opened during query).
- T0B lineage is validated BEFORE result publication and therefore before
  any limit: a returned projection_ref has already passed the
  projection→schema→lineage→acquisition→blob chain.
- Pipeline order (§10): enumeration → metadata filters → time filters →
  revision resolution → integrity admissibility → T0A/T0B eligibility →
  projection schema filtering → lineage validation → deterministic
  ordering → limit LAST.  ``limit`` can never suppress a revision
  ambiguity raised during reduction.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from .enums import IntegrityState, RevisionPolicy, RevisionState
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


class RevisionPolicyInvalid(QueryValidationError):
    """The revision selector itself is unusable (I12R1 §18):
    EXACT_REVISION without a number, a number without EXACT_REVISION, or a
    registry configuration refusal — never collapsed into a generic
    backend failure."""


class RevisionCanonicalUnavailable(RawQueryError):
    """PROVIDER_DECLARED_CANONICAL found no explicit provider declaration
    evidence (I12R1 §18/§4): typed unavailability — the absent claim is
    never silently replaced by a temporal pick."""


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
        revision_registry: Any = None,
        revision_identity_factory: Any = None,
        projection_artifact_repository: Any = None,
        projection_lineage_repository: Any = None,
    ) -> None:
        self._manifests_repo = manifest_repository
        self._acquisitions_repo = acquisition_repository
        self._blobs_repo = blob_metadata_repository
        # I12R1: revision authority stays the accepted I06 registry; the
        # service only wires it into the public query reduction (§3).
        self._revision_registry = revision_registry
        self._identity_factory = revision_identity_factory
        # I12R1: read-only T0B metadata dependencies (metadata ONLY — no
        # projection payload bytes are ever opened by a query, §9).
        self._artifacts_repo = projection_artifact_repository
        self._lineage_repo = projection_lineage_repository
        self._snapshot = self._build_snapshot()

    # -- revision resolution through the accepted I06 law (I12R1 §2-§4) ------

    def _revision_selected(
        self, acquisition: AcquisitionRecord, query: RawEvidenceQuery
    ) -> bool:
        """True when the acquisition's revision is SELECTED by the query
        policy under the accepted I06 registry resolution (§3).

        Delegates every decision to ``SourceRevisionRegistry.resolve`` —
        the I12 boundary only maps registry failures into the I12 typed
        vocabulary, preserving ``__cause__`` (§18):

        - ``RevisionAmbiguityError``  -> ``RevisionAmbiguity``
        - ``RevisionNotFound``        -> ``NoMatchingEvidence``
        - ``RevisionResolutionUnavailable`` -> ``RevisionCanonicalUnavailable``
        - ``RevisionConfigurationError``/catalog corruption
                                      -> ``RevisionPolicyInvalid``

        Epistemic ambiguity is NEVER mapped to ``StorageBackendUnavailable``.
        """
        from .revisions import (  # local: authority module, no cycles
            RevisionAmbiguityError,
            RevisionConfigurationError,
            RevisionNotFound,
            RevisionResolutionUnavailable,
            RevisionSourceIdentityV1,
            RevisionTemporalAmbiguity,
            SourceRevisionCatalogCorrupt,
        )

        registry = self._revision_registry
        factory = self._identity_factory or RevisionSourceIdentityV1
        try:
            key = factory.from_acquisition(acquisition).source_revision_key()
            resolution = registry.resolve(
                key,
                query.revision_policy,
                revision_number=query.exact_revision_number,
            )
        except (RevisionAmbiguityError, RevisionTemporalAmbiguity) as exc:
            # Both are epistemic ambiguity (§40 temporal ambiguity included):
            # never mapped to StorageBackendUnavailable (I12R1 §18).
            raise RevisionAmbiguity(str(exc)) from exc
        except RevisionNotFound as exc:
            raise NoMatchingEvidence(str(exc)) from exc
        except RevisionResolutionUnavailable as exc:
            raise RevisionCanonicalUnavailable(str(exc)) from exc
        except (RevisionConfigurationError, SourceRevisionCatalogCorrupt) as exc:
            raise RevisionPolicyInvalid(str(exc)) from exc
        # The acquisition's durable binding: revision_number derived from the
        # registry's own reverse lookup (durable truth, never a count hint).
        binding = registry.revision_for_acquisition(acquisition.acquisition_id)
        if binding is None:
            raise NoMatchingEvidence(
                f"acquisition {acquisition.acquisition_id} has no durable "
                "revision binding in the accepted registry"
            )
        _key, revision_number = binding
        return revision_number in set(resolution.selected_revision_numbers)

    def _resolve_revision_state(
        self, manifest: PartitionManifest, acquisitions: list[AcquisitionRecord]
    ) -> RevisionState:
        """Durable I06 revision state for the selected acquisitions (§19).

        Reads the registry's own segment classification for the selected
        revisions — the manifest's ``revision_count`` hint is NEVER the
        authority.  Falls back to UNKNOWN_REVISION only when no revision
        dependency is wired (a caller that never queries revision semantics
        keeps the I12 legacy default explicitly, documented)."""
        from .revisions import RevisionSourceIdentityV1  # noqa: F401

        registry = self._revision_registry
        if registry is None or not acquisitions:
            return RevisionState.UNKNOWN_REVISION
        states: list[RevisionState] = []
        for acquisition in sorted(acquisitions, key=lambda a: a.acquisition_id):
            binding = registry.revision_for_acquisition(acquisition.acquisition_id)
            if binding is None:
                continue
            key, number = binding
            revision = registry.get_revision(key, number)
            if revision is not None:
                states.append(revision.revision_state)
        if not states:
            return RevisionState.UNKNOWN_REVISION
        # Deterministic fold: the strongest CLAIM wins; SOURCE_MUTATION
        # dominates STABLE because it must stay visible.
        if any(s is RevisionState.SOURCE_MUTATION for s in states):
            return RevisionState.SOURCE_MUTATION
        if any(s is RevisionState.PROVIDER_DECLARED_REVISION for s in states):
            return RevisionState.PROVIDER_DECLARED_REVISION
        if all(s is RevisionState.IDENTICAL_REFETCH for s in states):
            return RevisionState.IDENTICAL_REFETCH
        if all(s is RevisionState.STABLE for s in states):
            return RevisionState.STABLE
        return RevisionState.SOURCE_MUTATION

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
        """Reduce ``query`` over the complete inventory (I12 §6-§15, I12R1 §10).

        Pipeline order is pinned (I12R1 §10):

        1. authoritative inventory enumeration (frozen snapshot)
        2. metadata filters
        3. time filters
        4. revision resolution (accepted I06 law)          <- I12R1
        5. integrity admissibility
        6. coverage semantics (via metadata filters)
        7. T0A/T0B eligibility (representation selection)  <- I12R1
        8. projection schema filtering                     <- I12R1
        9. lineage validation BEFORE publication           <- I12R1
        10. canonical deterministic ordering
        11. limit LAST
        """
        if not query.include_t0a and not query.include_t0b:
            # §21: T0A=False/T0B=False is a validation failure, typed here at
            # execution because the model must stay accepted-contract-faithful.
            raise QueryValidationError(
                "include_t0a=False and include_t0b=False selects nothing; "
                "at least one include mode must be True"
            )
        # I12R1 §2: revision policy is REAL.  When the caller wants revision
        # semantics beyond the research-safe default they must wire the
        # accepted authority; a missing dependency is a typed refusal, never
        # a silently-ignored filter.
        if (
            self._revision_registry is None
            and (
                query.revision_policy is not RevisionPolicy.ERROR_ON_AMBIGUITY
                or query.exact_revision_number is not None
            )
        ):
            raise QueryValidationError(
                "the query carries an explicit revision policy but the "
                "service was constructed without revision_registry — the "
                "accepted I06 SourceRevisionRegistry is the only revision "
                "authority (I12R1 §3); re-query with the default policy or "
                "wire the registry"
            )

        # 1+2. inventory + metadata filters
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
            selected_records: list[AcquisitionRecord] = []
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
                # 4. REVISION RESOLUTION (I12R1 §2-§4): every candidate
                # acquisition passes through the accepted I06 registry under
                # the query's policy.  Ambiguity raises here — BEFORE any
                # result is built, before ordering, before limit.  With no
                # registry wired and the default policy, resolution is a
                # pass-through (the explicit-policy case is refused above).
                if self._revision_registry is not None:
                    kept: list[AcquisitionRecord] = []
                    for r in usable:
                        try:
                            if self._revision_selected(r, query):
                                kept.append(r)
                        except NoMatchingEvidence:
                            # This acquisition's revision is NOT selected by
                            # the policy (e.g. EXACT_REVISION names another
                            # revision, or the policy selected a different
                            # revision for this source key).  The acquisition
                            # is deselected — NOT a manifest-level failure;
                            # other blobs/manifests may still match.
                            pass
                    usable = kept
                if not usable:
                    # Every acquisition of this blob was deselected by the
                    # revision policy: this blob has no selected
                    # representation — skip the blob, keep the manifest.
                    continue
                blob_refs.append(blob_sha)
                acquisition_ids.extend(r.acquisition_id for r in usable)
                selected_records.extend(usable)
                for r in usable:
                    if ingested_max is None or r.ingested_at > ingested_max:
                        ingested_max = r.ingested_at
                    if observed_max is None or r.response_observed_at > observed_max:
                        observed_max = r.response_observed_at

            # Assemble the result ONLY when at least one blob has a selected
            # representation — a manifest whose every blob was deselected by
            # the revision policy contributes nothing (not an empty-shell
            # result) and falls through to the typed no-match below.
            if not blob_refs:
                continue

            # 5. integrity admissibility
            integrity = self._combined_integrity(
                manifest, blob_refs, query.integrity_minimum
            )
            if integrity is None:
                continue  # below threshold (§14) — candidate dropped
            # 7-9. representation selection + lineage BEFORE publication
            result = self._build_result(
                manifest,
                acquisitions=selected_records,
                blob_refs=blob_refs,
                integrity=integrity,
                query=query,
            )
            if result is None:
                continue
            results.append(result)

        if not results:
            # Candidates existed but every one was filtered by time cuts,
            # revision selection, representation eligibility or integrity —
            # still a typed no-match, never an empty list.
            raise NoMatchingEvidence(
                "candidate manifests exist but none satisfy the time/revision/"
                "representation/integrity constraints"
            )

        # 10. canonical deterministic ordering
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

        # 11. limit LAST — it can never suppress a refusal raised above.
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

    # -- result assembly (§13 + I12R1 §8/§10/§11) --------------------------------

    def _projection_metadata(
        self, projection_id: str, query: RawEvidenceQuery
    ) -> dict[str, Any] | None:
        """Durable T0B metadata for one manifest projection ref (metadata ONLY).

        Returns None when the projection does not satisfy the query's T0B
        eligibility (missing artifact/schema/lineage or filtered schema id).
        Never opens projection payload bytes or T0A payload bytes (§9).
        Raises ``LineageIncomplete`` when lineage is BROKEN (not merely
        absent-by-filter) so a broken chain never publishes (§11).
        """
        artifacts = self._artifacts_repo
        lineage = self._lineage_repo
        if artifacts is None or lineage is None:
            raise ProjectionSchemaUnsupported(
                "the query requested T0B representation but the service was "
                "constructed without the projection metadata repositories "
                "(projection_artifact_repository / projection_lineage_repository)"
            )
        try:
            artifact = artifacts.get(projection_id)
        except Exception as exc:  # noqa: BLE001 - typed re-wrap
            # The artifact repository signals missing projections by raising
            # (e.g. ProjectionChainBroken); a missing projection is a broken
            # lineage chain before publication (§11), not a backend error.
            raise LineageIncomplete(
                f"manifest references projection {projection_id} which has "
                f"no committed artifact: {exc}"
            ) from exc
        if artifact is None:
            raise LineageIncomplete(
                f"manifest references projection {projection_id} which has "
                "no committed artifact — lineage broken before publication"
            )
        if (
            query.projection_schema_ids
            and artifact.projection_schema_id not in query.projection_schema_ids
        ):
            return None  # filtered by schema id (not broken — just not selected)
        try:
            entries = lineage.get_by_projection(projection_id)
        except Exception as exc:  # noqa: BLE001 - typed re-wrap
            # A corrupt lineage fragment is a broken chain, not a backend
            # outage — typed refusal BEFORE publication (I12R1 §11/§18).
            raise LineageIncomplete(
                f"projection {projection_id} lineage is not readable: {exc}"
            ) from exc
        if not entries:
            raise LineageIncomplete(
                f"projection {projection_id} has zero lineage entries — "
                "lineage broken before publication"
            )
        # Every lineage entry must bind to durable, acquisition-backed T0A
        # (§11): the query contract claims lineage validation before limit.
        for entry in sorted(entries, key=lambda e: e.source_order):
            try:
                acquisition = self._acquisitions_repo.get_acquisition(
                    entry.source_acquisition_id
                )
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
            try:
                metas = self._blobs_repo.get_blob_metadata(entry.source_blob_sha256)
            except Exception as exc:  # noqa: BLE001 - typed re-wrap
                raise LineageIncomplete(
                    f"lineage blob {entry.source_blob_sha256} for projection "
                    f"{projection_id} has no committed metadata: {exc}"
                ) from exc
            if not metas:
                raise LineageIncomplete(
                    f"lineage blob {entry.source_blob_sha256} for projection "
                    f"{projection_id} has no committed metadata"
                )
        return {
            "projection_id": artifact.projection_id,
            "projection_schema_id": artifact.projection_schema_id,
            "projection_schema_version": artifact.projection_schema_version,
            "source_blobs": sorted(
                {e.source_blob_sha256 for e in entries}
            ),
        }

    def _build_result(
        self,
        manifest: PartitionManifest,
        *,
        acquisitions: list[AcquisitionRecord],
        blob_refs: list[str],
        integrity: IntegrityState,
        query: RawEvidenceQuery,
    ) -> RawEvidenceResult | None:
        """Assemble the result with representation selection (I12R1 §8).

        - ``blob_refs``      = selected/available T0A representation under
          the query's include flags;
        - ``projection_refs``= selected T0B representation (schema-filtered,
          lineage-validated BEFORE publication);
        - ``lineage_refs``   = the durable T0A sources REQUIRED by the
          selected T0B (provenance, not selection — a T0B-only query
          references T0A without pretending the caller selected T0A output).

        Returns None when the manifest carries no selected representation
        (e.g. T0B-only with no matching schema) — the caller drops the
        candidate or raises a typed representation failure, per §10.
        """
        selected_blobs = sorted(blob_refs) if query.include_t0a else []
        lineage_refs: list[str] = []
        projection_refs: list[str] = []
        if query.include_t0b:
            for projection_id in sorted(manifest.projection_refs):
                meta = self._projection_metadata(projection_id, query)
                if meta is None:
                    continue  # schema-filtered
                projection_refs.append(meta["projection_id"])
                lineage_refs.extend(meta["source_blobs"])
            if not projection_refs and not query.include_t0a:
                # §10: T0B-only, manifest has projections but none match the
                # requested schema ids (or none exist) — typed representation
                # failure; a non-matching projection is never substituted.
                raise ProjectionSchemaUnsupported(
                    f"manifest {manifest.partition_manifest_id} carries no T0B "
                    f"projection matching projection_schema_ids "
                    f"{sorted(query.projection_schema_ids)} and include_t0a is "
                    "False — no silent substitution"
                )
        elif manifest.projection_refs and self._artifacts_repo is not None:
            # T0A-only query: T0B stays UNSELECTED (not claimed in
            # projection_refs); if the T0B chain is broken we still refuse to
            # publish a manifest whose declared lineage is corrupt — the
            # failure is the manifest's, not the representation's (§11).
            for projection_id in sorted(manifest.projection_refs):
                self._projection_metadata(projection_id, query)
        else:
            # T0A-only, no T0B metadata wired, or manifest without
            # projections: manifest-level projection refs stay unselected.
            pass
        lineage_refs = sorted(set(lineage_refs))
        return RawEvidenceResult(
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
            acquisition_ids=sorted(a.acquisition_id for a in acquisitions),
            blob_refs=selected_blobs,
            projection_refs=sorted(projection_refs),
            revision_state=self._resolve_revision_state(manifest, acquisitions),
            quality_flags=[],
            lineage_refs=lineage_refs,
        )

    def _revision_state_hint(self, manifest: PartitionManifest) -> Any:
        """Deprecated I12 count hint — retained ONLY for the historical I12
        evidence byte-stability; I12R1 resolution uses
        ``_resolve_revision_state`` (durable I06 truth, §19)."""
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
    "RevisionCanonicalUnavailable",
    "RevisionPolicyInvalid",
    "StorageBackendUnavailable",
]
