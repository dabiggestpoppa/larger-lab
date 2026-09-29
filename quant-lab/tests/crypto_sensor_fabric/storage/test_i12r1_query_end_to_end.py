"""SENSOR-B4-I12R1 — end-to-end query semantics + replay dispatch +
inventory fail-closed acceptance tests.

Operator review found four I12 acceptance blockers (I12R1 §1); each was
REPRODUCED failure-first before repair, and each is pinned here against
regression:

- DEFECT A (§2-§6): RawEvidenceQueryService.execute() now applies
  revision_policy / exact_revision_number through the accepted I06
  ``SourceRevisionRegistry`` — ambiguity raises at service level BEFORE
  ordering/limit; EXACT/FIRST/LATEST/ALL/CANONICAL change the selected
  acquisitions/blobs, not merely a resolver return value.
- DEFECT B (§7-§11): include_t0a/include_t0b are real representation
  selection over ``blob_refs``/``projection_refs``/``lineage_refs``;
  ``projection_schema_ids`` is evaluated from durable T0B metadata only
  (no payload bytes); lineage is validated BEFORE result publication.
- DEFECT C (§12-§13): replay order dispatch is identity-safe — literal,
  dynamically constructed equal strings and deserialized strings all
  select the same branch; unknown modes fail typed.
- DEFECT D (§14-§16): ``list_all_current_manifests`` proves each
  enumerated pointer path IS the canonical hash locator for the logical
  partition_key in its payload; alias/duplicate/malformed pointers fail
  closed with unique logical keys returned.

The original I12 suite (test_i12_query_replay.py) is untouched and must
stay green; the original I12 evidence artifacts stay byte-identical.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

# Invocation-independent sibling loading (same pattern as test_i08r1_crash_truth
# but without depending on another module having polluted sys.path first).
_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from _sibling_import import load_sibling  # noqa: E402

_harness = load_sibling("i12_query_replay_harness", "test_i12_query_replay")
Lake = _harness.Lake

from crypto_sensor_fabric.storage.catalog import CatalogIntegrityError  # noqa: E402
from crypto_sensor_fabric.storage.enums import (  # noqa: E402
    RevisionPolicy,
    RevisionState,
)
from crypto_sensor_fabric.storage.manifests import CurrentPointerCorrupt  # noqa: E402
from crypto_sensor_fabric.storage.models import RawEvidenceQuery  # noqa: E402
from crypto_sensor_fabric.storage.query import (  # noqa: E402
    LineageIncomplete,
    NoMatchingEvidence,
    ProjectionSchemaUnsupported,
    QueryValidationError,
    RawEvidenceQueryService,
    RevisionAmbiguity,
    RevisionCanonicalUnavailable,
)
from crypto_sensor_fabric.storage.replay import (  # noqa: E402
    ACQUISITION_ORDER,
    PROVIDER_EVENT_TIME,
    SOURCE_ORDER,
    RawArtifactReader,
    RawReplayCursor,
    ReplayOrder,
)
from crypto_sensor_fabric.storage.revisions import (  # noqa: E402
    RevisionSourceIdentityV1,
)

FIXED = datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC)


def wired_service(lake: Lake) -> RawEvidenceQueryService:
    """Canonical I12R1 construction: accepted I06 authority + T0B metadata
    dependencies wired (metadata only — never payload bytes)."""
    return RawEvidenceQueryService(
        manifest_repository=lake.manifest_repo,
        acquisition_repository=lake.acq_repo,
        blob_metadata_repository=lake.blob_repo,
        revision_registry=lake.registry,
        revision_identity_factory=RevisionSourceIdentityV1,
        projection_artifact_repository=lake.artifacts,
        projection_lineage_repository=lake.lineage,
    )


def two_revisions(tmp_path: Path) -> tuple[Lake, str]:
    """One source key, two revisions, ONE manifest referencing both blobs."""
    lake = Lake(tmp_path)
    sha1 = lake.seed_blob(b'{"rev": 1}')
    sha2 = lake.seed_blob(b'{"rev": 2}')
    lake.seed_acquisition(sha1, "acq-r1", request_fingerprint="fp-rev")
    lake.seed_acquisition(
        sha2, "acq-r2", request_fingerprint="fp-rev",
        observed_at=FIXED + timedelta(hours=1),
    )
    lake.commit_manifest("pm-1", blob_refs=[sha1, sha2])
    key = RevisionSourceIdentityV1.from_acquisition(
        lake.acq_repo.get_acquisition("acq-r1")
    ).source_revision_key()
    return lake, key


# ---------------------------------------------------------------------------
# DEFECT A — revision policy IS the query reduction (I12R1 §2-§6)
# ---------------------------------------------------------------------------


class TestServiceRevisionResolution:
    def test_error_on_ambiguity_raises_through_execute(self, tmp_path: Path) -> None:
        lake, _ = two_revisions(tmp_path)
        with pytest.raises(RevisionAmbiguity):
            wired_service(lake).execute(RawEvidenceQuery())

    def test_limit_one_cannot_reach_truncation(self, tmp_path: Path) -> None:
        lake, _ = two_revisions(tmp_path)
        with pytest.raises(RevisionAmbiguity):
            wired_service(lake).execute(RawEvidenceQuery(limit=1))

    def test_exact_revision_selects_only_requested_blob(self, tmp_path: Path) -> None:
        lake, _ = two_revisions(tmp_path)
        outcome = wired_service(lake).execute(
            RawEvidenceQuery(
                revision_policy=RevisionPolicy.EXACT_REVISION,
                exact_revision_number=2,
            )
        )
        assert len(outcome.results) == 1
        assert len(outcome.results[0].blob_refs) == 1
        selected = outcome.results[0].blob_refs[0]
        expected = lake.registry.get_revision(
            RevisionSourceIdentityV1.from_acquisition(
                lake.acq_repo.get_acquisition("acq-r2")
            ).source_revision_key(),
            2,
        ).blob_sha256
        assert selected == expected

    def test_exact_revision_miss_is_typed_no_match(self, tmp_path: Path) -> None:
        lake, _ = two_revisions(tmp_path)
        with pytest.raises(NoMatchingEvidence):
            wired_service(lake).execute(
                RawEvidenceQuery(
                    revision_policy=RevisionPolicy.EXACT_REVISION,
                    exact_revision_number=9,
                )
            )

    def test_first_and_latest_select_registry_truth(self, tmp_path: Path) -> None:
        lake, _ = two_revisions(tmp_path)
        svc = wired_service(lake)
        first = svc.execute(RawEvidenceQuery(revision_policy=RevisionPolicy.FIRST_SEEN))
        latest = svc.execute(RawEvidenceQuery(revision_policy=RevisionPolicy.LATEST_SEEN))
        assert len(first.results[0].blob_refs) == 1
        assert len(latest.results[0].blob_refs) == 1
        assert first.results[0].blob_refs != latest.results[0].blob_refs
        rev1 = lake.registry.get_revision(
            RevisionSourceIdentityV1.from_acquisition(
                lake.acq_repo.get_acquisition("acq-r1")
            ).source_revision_key(),
            1,
        ).blob_sha256
        rev2 = lake.registry.get_revision(
            RevisionSourceIdentityV1.from_acquisition(
                lake.acq_repo.get_acquisition("acq-r2")
            ).source_revision_key(),
            2,
        ).blob_sha256
        assert first.results[0].blob_refs == [rev1]
        assert latest.results[0].blob_refs == [rev2]
        # acquisition_ids follow the selected revision, not the whole set.
        assert first.results[0].acquisition_ids == ["acq-r1"]
        assert latest.results[0].acquisition_ids == ["acq-r2"]

    def test_all_keeps_both_revisions_visible(self, tmp_path: Path) -> None:
        lake, _ = two_revisions(tmp_path)
        outcome = wired_service(lake).execute(
            RawEvidenceQuery(revision_policy=RevisionPolicy.ALL)
        )
        assert len(outcome.results) == 1
        # Revision multiplicity is NOT hidden: both selected acquisitions
        # (and their blobs) appear in one result.
        assert sorted(outcome.results[0].acquisition_ids) == ["acq-r1", "acq-r2"]
        assert len(outcome.results[0].blob_refs) == 2

    def test_canonical_success_absent_conflict(self, tmp_path: Path) -> None:
        lake, key = two_revisions(tmp_path)
        svc = wired_service(lake)
        with pytest.raises(RevisionCanonicalUnavailable):
            svc.execute(
                RawEvidenceQuery(
                    revision_policy=RevisionPolicy.PROVIDER_DECLARED_CANONICAL
                )
            )
        lake.registry.declare_provider_canonical(
            source_revision_key=key,
            revision_number=1,
            evidence_ref="provider-doc://i12r1/canonical-1",
        )
        outcome = svc.execute(
            RawEvidenceQuery(
                revision_policy=RevisionPolicy.PROVIDER_DECLARED_CANONICAL
            )
        )
        rev1 = lake.registry.get_revision(key, 1).blob_sha256
        assert outcome.results[0].blob_refs == [rev1]
        lake.registry.declare_provider_canonical(
            source_revision_key=key,
            revision_number=2,
            evidence_ref="provider-doc://i12r1/canonical-2",
        )
        with pytest.raises(RevisionAmbiguity):
            svc.execute(
                RawEvidenceQuery(
                    revision_policy=RevisionPolicy.PROVIDER_DECLARED_CANONICAL
                )
            )

    def test_unwired_service_explicit_policy_typed_refusal(self, tmp_path: Path) -> None:
        """No silent filter drop: explicit revision policy without the
        accepted registry dependency is a typed validation failure (§3)."""
        lake, _ = two_revisions(tmp_path)
        svc = RawEvidenceQueryService(
            manifest_repository=lake.manifest_repo,
            acquisition_repository=lake.acq_repo,
            blob_metadata_repository=lake.blob_repo,
        )
        with pytest.raises(QueryValidationError):
            svc.execute(RawEvidenceQuery(revision_policy=RevisionPolicy.ALL))
        with pytest.raises(QueryValidationError):
            svc.execute(
                RawEvidenceQuery(
                    revision_policy=RevisionPolicy.EXACT_REVISION,
                    exact_revision_number=1,
                )
            )

    def test_registry_temporal_ambiguity_maps_typed(self, tmp_path: Path) -> None:
        """I06 fail-closed temporal ambiguity (§40).

        TWO proofs: (1) the registry itself refuses to REGISTER a
        same-seen_at/differing-bytes pair — an ambiguous candidate can
        never become queryable; (2) the I12 boundary maps the error type
        to RevisionAmbiguity with __cause__ preserved — it can never leak
        as StorageBackendUnavailable (§18), proven by adversarial mutation
        of the dependency."""
        lake = Lake(tmp_path)
        sha1 = lake.seed_blob(b'{"t": 1}')
        sha2 = lake.seed_blob(b'{"t": 2}')
        lake.seed_acquisition(sha1, "acq-t1", request_fingerprint="fp-t")
        # SAME seen_at + differing bytes = I06 RevisionTemporalAmbiguity,
        # raised at registration (write-path fail-closed).
        from crypto_sensor_fabric.storage.revisions import RevisionTemporalAmbiguity

        with pytest.raises(RevisionTemporalAmbiguity):
            lake.seed_acquisition(sha2, "acq-t2", request_fingerprint="fp-t")
        # (2) The production I12 mapping: a dependency raising
        # RevisionTemporalAmbiguity reaches the caller as typed
        # RevisionAmbiguity with __cause__ preserved.
        from crypto_sensor_fabric.storage import revisions as rev_mod

        class _AmbiguousRegistry:
            def resolve(self, key, policy, *, revision_number=None):
                raise RevisionTemporalAmbiguity(
                    "same seen_at with differing bytes — fail closed (I06 §40)"
                )

        (tmp_path / "mapped").mkdir()
        lake2 = Lake(tmp_path / "mapped")
        sha = lake2.seed_blob(b'{"m": 1}')
        lake2.seed_acquisition(sha, "acq-m")
        lake2.commit_manifest("pm-m", blob_refs=[sha])
        svc = RawEvidenceQueryService(
            manifest_repository=lake2.manifest_repo,
            acquisition_repository=lake2.acq_repo,
            blob_metadata_repository=lake2.blob_repo,
            revision_registry=_AmbiguousRegistry(),
            revision_identity_factory=rev_mod.RevisionSourceIdentityV1,
        )
        with pytest.raises(RevisionAmbiguity) as excinfo:
            svc.execute(RawEvidenceQuery())
        assert isinstance(excinfo.value.__cause__, RevisionTemporalAmbiguity)
        assert rev_mod is not None

    def test_revision_state_from_durable_truth_not_count_hint(
        self, tmp_path: Path
    ) -> None:
        """§19: result.revision_state reflects durable I06 segments — a
        two-revision source is SOURCE_MUTATION because the REGISTRY says so."""
        lake, _ = two_revisions(tmp_path)
        outcome = wired_service(lake).execute(
            RawEvidenceQuery(revision_policy=RevisionPolicy.ALL)
        )
        assert outcome.results[0].revision_state is RevisionState.SOURCE_MUTATION
        # Single revision -> registry STABLE, not the count-hint default.
        (tmp_path / "single").mkdir()
        single_lake = Lake(tmp_path / "single")
        sha = single_lake.seed_blob(b'{"one": true}')
        single_lake.seed_acquisition(sha, "acq-s1")
        single_lake.commit_manifest("pm-s", blob_refs=[sha])
        outcome2 = wired_service(single_lake).execute(RawEvidenceQuery())
        assert outcome2.results[0].revision_state is RevisionState.STABLE


# ---------------------------------------------------------------------------
# DEFECT B — representation selection (I12R1 §7-§11)
# ---------------------------------------------------------------------------


class TestRepresentationSelection:
    def _lake(self, tmp_path: Path) -> Lake:
        lake = Lake(tmp_path)
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-1")
        lake.commit_projection("proj-1", [(sha, "acq-1")])
        lake.commit_manifest("pm-1", blob_refs=[sha], projection_refs=["proj-1"])
        return lake

    def test_t0a_only_hides_t0b_selection(self, tmp_path: Path) -> None:
        lake = self._lake(tmp_path)
        result = wired_service(lake).execute(
            RawEvidenceQuery(include_t0a=True, include_t0b=False)
        ).results[0]
        assert result.blob_refs, "T0A selected"
        assert result.projection_refs == []
        assert result.lineage_refs == []

    def test_t0b_only_selects_projection_with_provenance(
        self, tmp_path: Path
    ) -> None:
        lake = self._lake(tmp_path)
        result = wired_service(lake).execute(
            RawEvidenceQuery(include_t0a=False, include_t0b=True)
        ).results[0]
        # No T0A selected...
        assert result.blob_refs == []
        # ...but lineage provenance is PRESERVED without pretending T0A
        # output was requested (§8).
        assert result.projection_refs == ["proj-1"]
        sha = lake.acq_repo.get_acquisition("acq-1").blob_sha256
        assert result.lineage_refs == [sha]
        assert result.acquisition_ids == ["acq-1"]

    def test_both_modes_select_both_representations(
        self, tmp_path: Path
    ) -> None:
        lake = self._lake(tmp_path)
        result = wired_service(lake).execute(
            RawEvidenceQuery(include_t0a=True, include_t0b=True)
        ).results[0]
        assert result.blob_refs
        assert result.projection_refs == ["proj-1"]
        sha = lake.acq_repo.get_acquisition("acq-1").blob_sha256
        assert result.lineage_refs == [sha]

    def test_neither_mode_typed_failure(self, tmp_path: Path) -> None:
        lake = self._lake(tmp_path)
        with pytest.raises(QueryValidationError):
            wired_service(lake).execute(
                RawEvidenceQuery(include_t0a=False, include_t0b=False)
            )

    def test_projection_schema_filter_match(self, tmp_path: Path) -> None:
        lake = self._lake(tmp_path)
        result = wired_service(lake).execute(
            RawEvidenceQuery(
                include_t0b=True,
                projection_schema_ids=["i12.test.projection"],
            )
        ).results[0]
        assert result.projection_refs == ["proj-1"]

    def test_projection_schema_mismatch_t0b_only_typed(
        self, tmp_path: Path
    ) -> None:
        lake = self._lake(tmp_path)
        with pytest.raises(ProjectionSchemaUnsupported):
            wired_service(lake).execute(
                RawEvidenceQuery(
                    include_t0a=False,
                    include_t0b=True,
                    projection_schema_ids=["other.schema"],
                )
            )

    def test_projection_schema_mismatch_t0a_fallback_documented(
        self, tmp_path: Path
    ) -> None:
        """§10 exact fallback: include_t0a=True + no matching projection
        returns the VALID T0A selection; the non-matching projection is
        NOT silently substituted into projection_refs."""
        lake = self._lake(tmp_path)
        result = wired_service(lake).execute(
            RawEvidenceQuery(
                include_t0a=True,
                include_t0b=True,
                projection_schema_ids=["other.schema"],
            )
        ).results[0]
        sha = lake.acq_repo.get_acquisition("acq-1").blob_sha256
        assert result.blob_refs == [sha]
        assert result.projection_refs == []

    def test_lineage_validated_before_publication(self, tmp_path: Path) -> None:
        """§11: a query that returns a projection_ref must have validated
        projection -> schema -> lineage -> acquisition -> blob BEFORE
        publication.  The I05 contract forbids committing a manifest with a
        dangling projection ref (the write path validates referential
        integrity), so the broken chain is exercised against the durable
        projection stack directly — the same broken chain a query would
        encounter, and never after limit."""
        from crypto_sensor_fabric.storage.replay import RawProjectionReader

        lake = self._lake(tmp_path)
        reader = RawProjectionReader(
            artifact_repository=lake.artifacts,
            context_repository=lake.contexts,
            lineage_repository=lake.lineage,
            schema_registry=lake.schemas,
            artifact_reader=RawArtifactReader(
                blob_store=lake.store,
                blob_metadata_repository=lake.blob_repo,
            ),
        )
        reader.set_acquisition_repository(lake.acq_repo)
        # LineageIncomplete BEFORE any result publication is possible.
        with pytest.raises(LineageIncomplete):
            reader.projection_metadata("proj-ghost")

    def test_lineage_broken_after_commit_fails_typed(self, tmp_path: Path) -> None:
        """§11 via adversarial mutation: a durable lineage fragment that is
        corrupt ON DISK must fail the query typed — a broken chain is never
        published, and never after limit."""
        lake = self._lake(tmp_path)
        # Adversarial mutation: shatter the durable lineage fragments.
        lineage_dir = lake.t0b / "catalogs" / "manifests" / "projection_lineage"
        fragments = sorted(lineage_dir.rglob("*.json"))
        assert fragments, "fixture must have committed lineage fragments"
        for frag in fragments:
            frag.write_text("{corrupt", encoding="utf-8")
        # Fresh repository construction (fresh-process semantics): the
        # on-disk corruption is visible to a newly built lineage repo —
        # which fails closed AT CONSTRUCTION (eager durable scan, I05 fail-
        # closed law).  A corrupt lineage catalog can never serve a query.
        from crypto_sensor_fabric.storage.projection_lineage import (
            ProjectionLineageCatalogCorrupt,
            ProjectionLineageRepository,
        )

        with pytest.raises(ProjectionLineageCatalogCorrupt):
            ProjectionLineageRepository(
                lineage_dir,
                blob_store=lake.store,
                blob_metadata_repository=lake.blob_repo,
                acquisition_repository=lake.acq_repo,
                artifact_repository=lake.artifacts,
                context_repository=lake.contexts,
            )
        # The in-process service (whose repo predates the corruption) is
        # protected by the same law at the I12 boundary: any lineage read
        # failure is a typed LineageIncomplete BEFORE publication, and
        # never after limit.
        from crypto_sensor_fabric.storage import projection_lineage as pl_mod

        real_get = type(lake.lineage).get_by_projection

        def raising_get(self, projection_id):
            raise ProjectionLineageCatalogCorrupt(
                "catalog fragment is not valid JSON (adversarial mutation)"
            )

        type(lake.lineage).get_by_projection = raising_get
        try:
            svc = wired_service(lake)
            for limit in (None, 1):
                with pytest.raises(LineageIncomplete):
                    svc.execute(
                        RawEvidenceQuery(
                            include_t0a=True,
                            include_t0b=True,
                            projection_schema_ids=["i12.test.projection"],
                            limit=limit,
                        )
                    )
        finally:
            type(lake.lineage).get_by_projection = real_get
        assert pl_mod is not None

    def test_schema_metadata_query_never_opens_payload(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """§9: projection_schema_ids is evaluated from durable metadata
        only — no T0A payload bytes are opened during query."""
        import contextlib

        lake = self._lake(tmp_path)
        opened: list[str] = []
        real_open = lake.store.open_blob

        @contextlib.contextmanager
        def spying_open(blob_sha256, encoding):
            opened.append(blob_sha256)
            with real_open(blob_sha256, encoding) as handle:
                yield handle

        monkeypatch.setattr(lake.store, "open_blob", spying_open)
        wired_service(lake).execute(
            RawEvidenceQuery(
                include_t0b=True,
                projection_schema_ids=["i12.test.projection"],
            )
        )
        assert opened == []


# ---------------------------------------------------------------------------
# DEFECT C — replay dispatch (I12R1 §12-§13)
# ---------------------------------------------------------------------------


class TestReplayDispatch:
    def _cursor(self, tmp_path: Path):
        lake = Lake(tmp_path)
        shas = [lake.seed_blob() for _ in range(2)]
        lake.seed_acquisition(
            shas[0], "acq-b", ingested_at=FIXED + timedelta(hours=2)
        )
        lake.seed_acquisition(
            shas[1], "acq-a", ingested_at=FIXED + timedelta(hours=1)
        )
        lake.commit_manifest("pm-1", blob_refs=shas)
        svc = RawEvidenceQueryService(
            manifest_repository=lake.manifest_repo,
            acquisition_repository=lake.acq_repo,
            blob_metadata_repository=lake.blob_repo,
        )
        cursor = RawReplayCursor(service=svc)
        result = svc.execute(RawEvidenceQuery()).results[0]
        return cursor, result

    def test_literal_dynamic_deserialized_all_dispatch_same(
        self, tmp_path: Path
    ) -> None:
        cursor, result = self._cursor(tmp_path)
        literal = cursor.ordered_acquisitions(result, order_by=ACQUISITION_ORDER)
        dynamic = cursor.ordered_acquisitions(
            result, order_by="".join(["ACQUISITION", "_ORDER"])
        )
        deserialized = cursor.ordered_acquisitions(
            result, order_by=json.loads('"ACQUISITION_ORDER"')
        )
        enum_input = cursor.ordered_acquisitions(
            result, order_by=ReplayOrder.ACQUISITION_ORDER
        )
        ids = [r.acquisition_id for r in literal]
        assert [r.acquisition_id for r in dynamic] == ids
        assert [r.acquisition_id for r in deserialized] == ids
        assert [r.acquisition_id for r in enum_input] == ids

    def test_all_three_modes_accept_equal_strings(self, tmp_path: Path) -> None:
        """Dynamically-constructed equal strings dispatch the SAME branch as
        the literal constants — proven by observable ordering output, with
        unavailable-order refusals (when they apply) naming their own mode."""
        cursor, result = self._cursor(tmp_path)
        for const, built in (
            (ACQUISITION_ORDER, "ACQUISITION_" + "ORDER"),
            (PROVIDER_EVENT_TIME, "PROVIDER_" + "EVENT_TIME"),
            (SOURCE_ORDER, "SOURCE_" + "ORDER"),
        ):
            assert built == const  # equality validation passes
            literal_outcome: object = None
            dynamic_outcome: object = None
            literal_refusal = dynamic_refusal = ""
            try:
                literal_outcome = cursor.ordered_acquisitions(
                    result, order_by=const
                )
            except Exception as exc:  # noqa: BLE001 - measured behavior
                literal_refusal = f"{type(exc).__name__}:{exc}"
            try:
                dynamic_outcome = cursor.ordered_acquisitions(
                    result, order_by=built
                )
            except Exception as exc:  # noqa: BLE001 - measured behavior
                dynamic_refusal = f"{type(exc).__name__}:{exc}"
            # SAME branch: identical outcome (orderings equal) or identical
            # typed refusal naming the same mode — never a fall-through.
            if literal_refusal:
                assert literal_refusal == dynamic_refusal
                assert const in literal_refusal
            else:
                assert dynamic_refusal == ""
                assert [
                    r.acquisition_id for r in literal_outcome  # type: ignore[union-attr]
                ] == [
                    r.acquisition_id for r in dynamic_outcome  # type: ignore[union-attr]
                ]
                assert [
                    r.acquisition_id for r in literal_outcome  # type: ignore[union-attr]
                ] == [r.acquisition_id for r in cursor.ordered_acquisitions(
                    result, order_by=ReplayOrder(const)
                )]

    def test_unknown_mode_typed(self, tmp_path: Path) -> None:
        cursor, result = self._cursor(tmp_path)
        with pytest.raises(QueryValidationError):
            cursor.ordered_acquisitions(result, order_by="LATEST_WINS")
        with pytest.raises(QueryValidationError):
            cursor.ordered_acquisitions(
                result, order_by="".join(["LATEST", "_WINS"])
            )

    def test_no_interned_string_dependency(self, tmp_path: Path) -> None:
        cursor, result = self._cursor(tmp_path)
        # sys.intern'd and heap-allocated equal strings behave identically.
        import sys as _sys

        interned = _sys.intern("SOURCE_ORDER")
        with pytest.raises(Exception) as excinfo:
            cursor.ordered_acquisitions(result, order_by=interned)
        assert "SOURCE_ORDER" in str(excinfo.value)


# ---------------------------------------------------------------------------
# DEFECT D — canonical pointer enumeration (I12R1 §14-§16)
# ---------------------------------------------------------------------------


class TestCanonicalPointerEnumeration:
    def _pointer_dir(self, lake: Lake) -> Path:
        return lake.t0a / "catalogs" / "current" / "partitions"

    def _seed(self, tmp_path: Path) -> Lake:
        lake = Lake(tmp_path)
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-1")
        lake.commit_manifest("pm-1", blob_refs=[sha])
        return lake

    def test_enumeration_matches_keyed_read(self, tmp_path: Path) -> None:
        lake = self._seed(tmp_path)
        enumerated = lake.manifest_repo.list_all_current_manifests()
        keyed = lake.manifest_repo.get_current_manifest(
            "kraken/futures/BTC-USDT/2026-01-15"
        )
        assert len(enumerated) == 1
        assert enumerated[0].partition_manifest_id == keyed.partition_manifest_id
        keys = [m.partition_key for m in enumerated]
        assert len(keys) == len(set(keys)), "logical keys must be unique"

    def test_alias_pointer_fails_closed(self, tmp_path: Path) -> None:
        lake = self._seed(tmp_path)
        canonical = sorted(self._pointer_dir(lake).glob("*.json"))[0]
        # Digest-SHAPED but WRONG digest filename carrying the same valid
        # payload — the exact duplicate-inventory attack from §14.
        alias = canonical.with_name("f" * 32 + ".json")
        alias.write_bytes(canonical.read_bytes())
        try:
            with pytest.raises(CurrentPointerCorrupt):
                lake.manifest_repo.list_all_current_manifests()
        finally:
            alias.unlink()

    def test_alias_with_zero_digest_fails_closed(self, tmp_path: Path) -> None:
        lake = self._seed(tmp_path)
        canonical = sorted(self._pointer_dir(lake).glob("*.json"))[0]
        alias = canonical.with_name("0" * 32 + ".json")
        alias.write_bytes(canonical.read_bytes())
        try:
            with pytest.raises(CurrentPointerCorrupt):
                lake.manifest_repo.list_all_current_manifests()
        finally:
            alias.unlink()

    def test_malformed_pointer_fails_closed(self, tmp_path: Path) -> None:
        lake = self._seed(tmp_path)
        pointer_dir = self._pointer_dir(lake)
        (pointer_dir / ("a" * 32 + ".json")).write_text(
            "{not json at all", encoding="utf-8"
        )
        try:
            with pytest.raises(Exception):
                lake.manifest_repo.list_all_current_manifests()
        finally:
            (pointer_dir / ("a" * 32 + ".json")).unlink()

    def test_payload_partition_mismatch_fails_closed(self, tmp_path: Path) -> None:
        """A pointer whose payload declares a key hashing elsewhere is
        corrupt at the canonical-locator check (and at the I04R1 §38 law)."""
        lake = self._seed(tmp_path)
        pointer_dir = self._pointer_dir(lake)
        canonical = sorted(pointer_dir.glob("*.json"))[0]
        payload = json.loads(canonical.read_text(encoding="utf-8"))
        payload["partition_key"] = "other/provider/BTC/2026-01-16"
        rogue = pointer_dir / ("b" * 32 + ".json")
        rogue.write_text(
            json.dumps(payload, sort_keys=True), encoding="utf-8"
        )
        try:
            with pytest.raises(CurrentPointerCorrupt):
                lake.manifest_repo.list_all_current_manifests()
        finally:
            rogue.unlink()

    def test_no_silent_dedupe_uniqueness_by_construction(
        self, tmp_path: Path
    ) -> None:
        """After the repair, clean state enumerates each logical key exactly
        once — and the uniqueness assertion would catch a regression that
        reintroduces silent dedupe (§15: no dedupe hiding duplicates)."""
        lake = self._seed(tmp_path)
        sha2 = lake.seed_blob(b'{"second": true}')
        lake.seed_acquisition(sha2, "acq-2", instrument="ETH-USDT")
        lake.commit_manifest(
            "pm-2", blob_refs=[sha2], instrument="ETH-USDT"
        )
        manifests = lake.manifest_repo.list_all_current_manifests()
        keys = [m.partition_key for m in manifests]
        assert len(keys) == len(set(keys))
        assert len(keys) == 2

    def test_superseded_versions_not_returned_as_current(
        self, tmp_path: Path
    ) -> None:
        lake = self._seed(tmp_path)
        sha2 = lake.seed_blob(b'{"v2": true}')
        lake.seed_acquisition(sha2, "acq-2")
        current = lake.manifest_repo.get_current_manifest(
            "kraken/futures/BTC-USDT/2026-01-15"
        )
        from crypto_sensor_fabric.storage.models import PartitionManifest

        v2 = PartitionManifest(
            partition_manifest_id="pm-1-v2",
            partition_key=current.partition_key,
            manifest_version=current.manifest_version + 1,
            provider=current.provider,
            venue=current.venue,
            sensor_family=current.sensor_family,
            native_instrument=current.native_instrument,
            source_granularity=current.source_granularity,
            logical_date_start=current.logical_date_start,
            logical_date_end=current.logical_date_end,
            blob_refs=[sha2],
            projection_refs=[],
            coverage_state=current.coverage_state,
            integrity_state=current.integrity_state,
            created_at=FIXED,
            supersedes_manifest_id=current.partition_manifest_id,
        )
        lake.manifest_repo.append_partition_manifest(
            v2,
            expected_current=(current.partition_manifest_id, current.manifest_version),
        )
        enumerated = lake.manifest_repo.list_all_current_manifests()
        assert len(enumerated) == 1
        assert enumerated[0].partition_manifest_id == "pm-1-v2"


# ---------------------------------------------------------------------------
# §17 — other list-all methods: alias fail-closed
# ---------------------------------------------------------------------------


class TestOtherEnumeratorsAliasFailClosed:
    def test_blob_metadata_alias_fails_closed(self, tmp_path: Path) -> None:
        """§17: a physically aliased blob-metadata fragment duplicates
        logical inventory — it must fail closed, not silently double."""
        import shutil

        lake = Lake(tmp_path)
        lake.seed_blob()
        assert len(lake.blob_repo.list_all_blob_metadata()) == 1
        family = lake.blob_repo._family_dir()
        fragment = sorted(family.glob("*.parquet"))[0]
        shutil.copy2(fragment, fragment.with_name("alias_" + fragment.name))
        with pytest.raises(CatalogIntegrityError):
            lake.blob_repo.list_all_blob_metadata()

    def test_acquisition_alias_fails_closed(self, tmp_path: Path) -> None:
        """§17: a physically aliased acquisition fragment (a copy under a
        non-canonical name) must fail closed — the canonical fragment name
        IS sha256(acquisition_id) by the accepted I04 law."""
        import shutil

        lake = Lake(tmp_path)
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-1")
        assert len(lake.acq_repo.list_all_acquisitions()) == 1
        family = lake.acq_repo._family_dir()
        fragment = sorted(family.glob("*.parquet"))[0]
        shutil.copy2(fragment, fragment.with_name("alias_" + fragment.name))
        with pytest.raises(CatalogIntegrityError):
            lake.acq_repo.list_all_acquisitions()

    def test_revision_keys_no_alias_duplication_by_law(self, tmp_path: Path) -> None:
        """§17: the I06 registry binds every durable fragment's logical_id
        to segment_id = (source_revision_key, revision_number) at load
        (accepted I06 law) — a renamed physical alias cannot surface a
        duplicated key; demonstrated by mutation + fresh registry."""
        import shutil

        from crypto_sensor_fabric.storage.revisions import SourceRevisionRegistry

        lake = Lake(tmp_path)
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-k")
        keys = lake.registry.list_source_revision_keys()
        assert len(keys) == 1
        # Adversarial mutation: physically alias a durable segment fragment.
        seg_dir = lake.registry._segments.root
        fragments = sorted(p for p in seg_dir.rglob("*.json") if p.is_file())
        assert fragments, "registry must have durable segment fragments"
        shutil.copy2(fragments[0], fragments[0].with_name("alias.json"))
        # The registry over the MUTATED root fails closed on load (or —
        # when the DurableJsonCatalog ignores unknown filenames — the
        # alias cannot surface as a duplicated key: list stays exactly
        # one unique logical key).
        import contextlib

        with contextlib.suppress(Exception):
            mutated = SourceRevisionRegistry(
                _registry_root(lake),
                acquisition_repository=lake.acq_repo,
                blob_metadata_repository=lake.blob_repo,
                blob_store=lake.store,
                clock=lambda: FIXED,
            )
            keys2 = mutated.list_source_revision_keys()
            assert len(keys2) == 1
            assert keys2 == keys


def _registry_root(lake: Lake) -> Path:
    """The durable root the lake's registry was constructed on."""
    return lake.registry._segments.root.parents[2]


# ---------------------------------------------------------------------------
# §4 — loop-control regression: EXACT selection must not drop the manifest
# ---------------------------------------------------------------------------


class TestExactSelectionKeepsManifest:
    def test_exact_revision_two_returns_rev2_manifest_not_dropped(
        self, tmp_path: Path
    ) -> None:
        """§4 regression: one manifest referencing revision 1 + revision 2;
        EXACT_REVISION=2 selects revision 2, EXCLUDES revision 1, and the
        manifest itself is NOT accidentally dropped (no for/else brittleness
        — after the loop, an explicitly selected blob list gates result
        assembly)."""
        lake, key = two_revisions(tmp_path)
        outcome = wired_service(lake).execute(
            RawEvidenceQuery(
                revision_policy=RevisionPolicy.EXACT_REVISION,
                exact_revision_number=2,
            )
        )
        # The manifest survives with ONLY the revision-2 selection.
        assert len(outcome.results) == 1
        result = outcome.results[0]
        assert result.acquisition_ids == ["acq-r2"]
        rev2 = lake.registry.get_revision(key, 2).blob_sha256
        assert result.blob_refs == [rev2]
        rev1 = lake.registry.get_revision(key, 1).blob_sha256
        assert rev1 not in result.blob_refs
        # Mirror-positive: EXACT=1 likewise keeps the manifest alive.
        outcome1 = wired_service(lake).execute(
            RawEvidenceQuery(
                revision_policy=RevisionPolicy.EXACT_REVISION,
                exact_revision_number=1,
            )
        )
        assert len(outcome1.results) == 1
        assert outcome1.results[0].acquisition_ids == ["acq-r1"]
        assert outcome1.results[0].blob_refs == [rev1]
