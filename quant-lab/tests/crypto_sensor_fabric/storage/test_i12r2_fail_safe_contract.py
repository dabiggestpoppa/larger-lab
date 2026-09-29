"""SENSOR-B4-I12R2 — fail-safe default revision authority + explicit
representation satisfaction.

Operator review of the sealed I12 -> I12R1 chain found two remaining
blockers; each was REPRODUCED failure-first (scripted run recorded in the
I12R2 narrative) and is pinned here against regression:

- BLOCKER A (I12R2 §2-§6): the DEFAULT revision policy (ERROR_ON_AMBIGUITY)
  is itself a revision-resolution policy and can never be honored without
  the accepted I06 ``SourceRevisionRegistry``.  ``execute()`` on a service
  constructed without ``revision_registry`` now raises a typed
  ``RevisionAuthorityUnavailable`` for EVERY policy — the I12R1
  default-policy pass-through (two revisions returned with no authority
  consulted) is closed.  There is NO compatibility switch (§5).
- BLOCKER B (I12R2 §8-§13): ``include_t0b=True`` is an explicit caller
  REQUIREMENT.  A query requesting T0B (with or without T0A) refuses typed
  (``ProjectionSchemaUnsupported``) when no eligible T0B projection exists
  — a valid T0A selection NEVER silently satisfies the requested T0B
  representation (the I12R1 option-A fallback is superseded), and a
  publication-boundary structural assertion keeps every published result
  consistent with the query's include flags.
- §14: T0A-only selection is deterministic whether the optional T0B
  metadata repositories are wired or absent.

The original I12 and I12R1 suites stay green; the only I12R1 artifact
change is the superseded fallback row in REPRESENTATION_SELECTION,
regenerated from production by the same accepted builder (append-only
correction, documented in BLOC_04_I12R2_FAIL_SAFE_CLOSURE.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from _sibling_import import load_sibling  # noqa: E402

_harness = load_sibling("i12r1_e2e", "test_i12r1_query_end_to_end")
Lake = _harness.Lake
two_revisions = _harness.two_revisions
wired_service = _harness.wired_service

from crypto_sensor_fabric.storage.enums import RevisionPolicy  # noqa: E402
from crypto_sensor_fabric.storage.models import RawEvidenceQuery  # noqa: E402
from crypto_sensor_fabric.storage.query import (  # noqa: E402
    ProjectionSchemaUnsupported,
    RawEvidenceQueryService,
    RevisionAuthorityUnavailable,
)
from crypto_sensor_fabric.storage.revisions import (  # noqa: E402
    RevisionSourceIdentityV1,
)


def unwired_service(lake: Lake) -> RawEvidenceQueryService:
    """A service WITHOUT the revision authority (compatibility allowed at
    construction only — execute() refuses, §3/§5)."""
    return RawEvidenceQueryService(
        manifest_repository=lake.manifest_repo,
        acquisition_repository=lake.acq_repo,
        blob_metadata_repository=lake.blob_repo,
    )


def registry_only_service(lake: Lake) -> RawEvidenceQueryService:
    """Authority wired, optional T0B metadata repositories absent."""
    return RawEvidenceQueryService(
        manifest_repository=lake.manifest_repo,
        acquisition_repository=lake.acq_repo,
        blob_metadata_repository=lake.blob_repo,
        revision_registry=lake.registry,
        revision_identity_factory=RevisionSourceIdentityV1,
    )


# ---------------------------------------------------------------------------
# BLOCKER A — revision authority is REQUIRED for every execution (§2-§6)
# ---------------------------------------------------------------------------


class TestAuthorityRequired:
    def test_unwired_default_policy_refused(self, tmp_path: Path) -> None:
        """The reproduced BLOCKER A: default ERROR_ON_AMBIGUITY + no
        registry used to RETURN results (two revisions visible, no
        authority consulted); it now refuses typed."""
        lake, _ = two_revisions(tmp_path)
        with pytest.raises(RevisionAuthorityUnavailable):
            unwired_service(lake).execute(RawEvidenceQuery())

    def test_unwired_first_seen_refused(self, tmp_path: Path) -> None:
        lake, _ = two_revisions(tmp_path)
        with pytest.raises(RevisionAuthorityUnavailable):
            unwired_service(lake).execute(
                RawEvidenceQuery(revision_policy=RevisionPolicy.FIRST_SEEN)
            )

    def test_unwired_exact_revision_refused(self, tmp_path: Path) -> None:
        lake, _ = two_revisions(tmp_path)
        with pytest.raises(RevisionAuthorityUnavailable):
            unwired_service(lake).execute(
                RawEvidenceQuery(
                    revision_policy=RevisionPolicy.EXACT_REVISION,
                    exact_revision_number=1,
                )
            )

    def test_unwired_all_policy_refused(self, tmp_path: Path) -> None:
        lake, _ = two_revisions(tmp_path)
        with pytest.raises(RevisionAuthorityUnavailable):
            unwired_service(lake).execute(
                RawEvidenceQuery(revision_policy=RevisionPolicy.ALL)
            )

    def test_wired_single_revision_default_succeeds(self, tmp_path: Path) -> None:
        lake = Lake(tmp_path)
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-s")
        lake.commit_manifest("pm-s", blob_refs=[sha])
        outcome = wired_service(lake).execute(RawEvidenceQuery())
        assert outcome.no_matching_evidence is False
        assert outcome.results[0].acquisition_ids == ["acq-s"]
        assert outcome.results[0].blob_refs == [sha]

    def test_wired_two_revision_default_is_ambiguity(self, tmp_path: Path) -> None:
        from crypto_sensor_fabric.storage.query import RevisionAmbiguity

        lake, _ = two_revisions(tmp_path)
        with pytest.raises(RevisionAmbiguity):
            wired_service(lake).execute(RawEvidenceQuery())

    def test_authority_refusal_is_not_evidence_or_backend_semantics(
        self, tmp_path: Path
    ) -> None:
        """§7: the unwired refusal is a configuration/authority failure —
        it must NOT be collapsible into StorageBackendUnavailable,
        NoMatchingEvidence or RevisionAmbiguity."""
        from crypto_sensor_fabric.storage.query import (
            NoMatchingEvidence,
            RevisionAmbiguity,
            StorageBackendUnavailable,
        )

        lake, _ = two_revisions(tmp_path)
        try:
            unwired_service(lake).execute(RawEvidenceQuery())
            raise AssertionError("expected RevisionAuthorityUnavailable")
        except RevisionAuthorityUnavailable:
            pass
        # Class check: distinct from every forbidden mapping.
        assert not issubclass(RevisionAuthorityUnavailable, NoMatchingEvidence)
        assert not issubclass(RevisionAuthorityUnavailable, RevisionAmbiguity)
        assert not issubclass(RevisionAuthorityUnavailable, StorageBackendUnavailable)

    def test_limit_still_last_with_wired_authority(self, tmp_path: Path) -> None:
        """With the authority wired, ambiguity still precedes truncation."""
        from crypto_sensor_fabric.storage.query import RevisionAmbiguity

        lake, _ = two_revisions(tmp_path)
        with pytest.raises(RevisionAmbiguity):
            wired_service(lake).execute(RawEvidenceQuery(limit=1))

    def test_no_hidden_compatibility_switch(self) -> None:
        """§5: the public constructor accepts no passthrough/legacy flags."""
        import inspect

        params = inspect.signature(RawEvidenceQueryService.__init__).parameters
        for forbidden in (
            "allow_unresolved_revisions",
            "unsafe_revision_passthrough",
            "legacy_mode",
        ):
            assert forbidden not in params, forbidden


# ---------------------------------------------------------------------------
# BLOCKER B — requested T0B cannot disappear silently (§8-§13)
# ---------------------------------------------------------------------------


class TestRepresentationSatisfaction:
    def _lake(self, tmp_path: Path) -> Lake:
        lake = Lake(tmp_path)
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-1")
        lake.commit_projection("proj-1", [(sha, "acq-1")])
        lake.commit_manifest("pm-1", blob_refs=[sha], projection_refs=["proj-1"])
        return lake

    def test_both_requested_schema_mismatch_fails_typed(
        self, tmp_path: Path
    ) -> None:
        """The reproduced BLOCKER B: T0A+T0B with a non-matching schema used
        to return the valid T0A selection with projection_refs=[] — it now
        refuses typed (the I12R1 option-A fallback is superseded)."""
        lake = self._lake(tmp_path)
        with pytest.raises(ProjectionSchemaUnsupported):
            wired_service(lake).execute(
                RawEvidenceQuery(
                    include_t0a=True,
                    include_t0b=True,
                    projection_schema_ids=["nonmatching.schema"],
                )
            )

    def test_t0b_only_no_projection_at_all_fails_typed(
        self, tmp_path: Path
    ) -> None:
        """include_t0b=True with a manifest carrying NO projections: a
        valid T0A selection never satisfies the requested T0B."""
        lake = Lake(tmp_path)
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-np")
        lake.commit_manifest("pm-np", blob_refs=[sha])
        with pytest.raises(ProjectionSchemaUnsupported):
            wired_service(lake).execute(
                RawEvidenceQuery(include_t0a=True, include_t0b=True)
            )

    def test_empty_schema_filter_still_requires_t0b(self, tmp_path: Path) -> None:
        """§11: projection_schema_ids=[] + include_t0b=True still requires at
        least one otherwise-valid T0B projection."""
        lake = self._lake(tmp_path)
        result = wired_service(lake).execute(
            RawEvidenceQuery(include_t0a=True, include_t0b=True,
                             projection_schema_ids=[])
        ).results[0]
        assert result.projection_refs == ["proj-1"]
        (tmp_path / "np").mkdir()
        lake_np = Lake(tmp_path / "np")
        sha = lake_np.seed_blob()
        lake_np.seed_acquisition(sha, "acq-np2")
        lake_np.commit_manifest("pm-np2", blob_refs=[sha])
        with pytest.raises(ProjectionSchemaUnsupported):
            wired_service(lake_np).execute(
                RawEvidenceQuery(include_t0a=True, include_t0b=True,
                                 projection_schema_ids=[])
            )

    def test_t0a_only_success_projection_refs_empty(self, tmp_path: Path) -> None:
        lake = self._lake(tmp_path)
        result = wired_service(lake).execute(
            RawEvidenceQuery(include_t0a=True, include_t0b=False)
        ).results[0]
        assert result.blob_refs
        assert result.projection_refs == []

    def test_t0b_only_success_requires_projection(self, tmp_path: Path) -> None:
        lake = self._lake(tmp_path)
        result = wired_service(lake).execute(
            RawEvidenceQuery(include_t0a=False, include_t0b=True)
        ).results[0]
        assert result.projection_refs == ["proj-1"]
        assert result.blob_refs == []

    def test_both_requested_success_carries_both(self, tmp_path: Path) -> None:
        lake = self._lake(tmp_path)
        result = wired_service(lake).execute(
            RawEvidenceQuery(include_t0a=True, include_t0b=True)
        ).results[0]
        assert result.blob_refs
        assert result.projection_refs == ["proj-1"]
        assert result.lineage_refs

    def test_neither_requested_is_query_validation_error(
        self, tmp_path: Path
    ) -> None:
        from crypto_sensor_fabric.storage.query import QueryValidationError

        lake = self._lake(tmp_path)
        with pytest.raises(QueryValidationError):
            wired_service(lake).execute(
                RawEvidenceQuery(include_t0a=False, include_t0b=False)
            )

    def test_lineage_broken_t0b_request_fails_typed(self, tmp_path: Path) -> None:
        """Lineage incompleteness is part of the satisfaction law: a broken
        T0B chain cannot be silently replaced by T0A."""
        from crypto_sensor_fabric.storage.query import LineageIncomplete

        lake = self._lake(tmp_path)
        lineage_dir = lake.t0b / "catalogs" / "manifests" / "projection_lineage"
        fragments = sorted(lineage_dir.rglob("*.json"))
        assert fragments, "fixture must have committed lineage fragments"
        for frag in fragments:
            frag.write_text("{corrupt", encoding="utf-8")
        from crypto_sensor_fabric.storage import projection_lineage as pl_mod

        real_get = type(lake.lineage).get_by_projection

        def raising_get(self, projection_id):  # noqa: ANN001
            raise pl_mod.ProjectionLineageCatalogCorrupt(
                "catalog fragment is not valid JSON (adversarial mutation)"
            )

        type(lake.lineage).get_by_projection = raising_get
        try:
            with pytest.raises(LineageIncomplete):
                wired_service(lake).execute(
                    RawEvidenceQuery(include_t0a=True, include_t0b=True)
                )
        finally:
            type(lake.lineage).get_by_projection = real_get


# ---------------------------------------------------------------------------
# §14 — T0A-only determinism with/without optional T0B readers wired
# ---------------------------------------------------------------------------


class TestT0AOnlyWiringDeterminism:
    def test_t0a_only_selection_identical_wired_or_not(self, tmp_path: Path) -> None:
        """A caller asking ONLY for T0A gets the same eligibility whether
        the optional T0B metadata repositories are wired or absent."""
        lake = Lake(tmp_path)
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-1")
        lake.commit_projection("proj-1", [(sha, "acq-1")])
        lake.commit_manifest("pm-1", blob_refs=[sha], projection_refs=["proj-1"])
        q = RawEvidenceQuery(include_t0a=True, include_t0b=False)
        wired = wired_service(lake).execute(q).results[0]
        unwired_t0b = registry_only_service(lake).execute(q).results[0]
        assert wired.blob_refs == unwired_t0b.blob_refs
        assert wired.acquisition_ids == unwired_t0b.acquisition_ids
        assert wired.projection_refs == [] == unwired_t0b.projection_refs
        assert wired.lineage_refs == unwired_t0b.lineage_refs

    def test_t0a_only_without_projections_identical(self, tmp_path: Path) -> None:
        lake = Lake(tmp_path)
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-plain")
        lake.commit_manifest("pm-plain", blob_refs=[sha])
        q = RawEvidenceQuery(include_t0a=True, include_t0b=False)
        wired = wired_service(lake).execute(q).results[0]
        unwired_t0b = registry_only_service(lake).execute(q).results[0]
        assert wired.blob_refs == unwired_t0b.blob_refs == [sha]


# ---------------------------------------------------------------------------
# §15 — QueryOutcome documentation matches public behavior
# ---------------------------------------------------------------------------


class TestQueryOutcomeContract:
    def test_no_match_raises_exception_not_condition(self, tmp_path: Path) -> None:
        """execute() RAISES typed NoMatchingEvidence; the outcome flag is
        only True on success-with-no-results semantics."""
        import pytest as _pytest

        from crypto_sensor_fabric.storage.query import NoMatchingEvidence

        lake = Lake(tmp_path)
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-1")
        lake.commit_manifest("pm-1", blob_refs=[sha])
        svc = wired_service(lake)
        with _pytest.raises(NoMatchingEvidence):
            svc.execute(RawEvidenceQuery(providers=["nobody"]))
        outcome = svc.execute(RawEvidenceQuery())
        assert outcome.no_matching_evidence is False
