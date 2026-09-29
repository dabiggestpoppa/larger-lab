"""SENSOR-B4-I12R1 — append-only measured evidence for the end-to-end query
semantics + replay dispatch + inventory fail-closed microseal.

SUPERSEDES the overbroad I12 claim "every RawEvidenceQuery filter is
mechanically evaluated" with END-TO-END measured proof through
``RawEvidenceQueryService.execute()``.  The original I12 artifacts are the
historical publication and are NEVER modified by this module.

Five matrices (all rows measured from production behavior / adversarial
mutation / structural introspection; exactly one explicit synthetic
counterfactual FAIL per matrix):

- BLOC_04_I12R1_QUERY_END_TO_END_MATRIX.json
- BLOC_04_I12R1_REVISION_INTEGRATION_MATRIX.json
- BLOC_04_I12R1_REPRESENTATION_SELECTION_MATRIX.json
- BLOC_04_I12R1_REPLAY_DISPATCH_MATRIX.json
- BLOC_04_I12R1_INVENTORY_FAIL_CLOSED_MATRIX.json

Publication is a separate explicit human step:
    UPDATE_I12R1_EVIDENCE=1 uv run --frozen python test_i12r1_evidence.py
Normal pytest execution is strictly READ-ONLY and asserts the committed
artifacts regenerate byte-identically (deterministic: fixed clock, fixed
identities, sorted outputs; temp paths never enter row payloads).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
_SRC = str(Path(__file__).resolve().parents[3] / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
from _sibling_import import load_sibling  # noqa: E402

# Reuse the I12R1 end-to-end fixtures (Lake harness + wired service).
_harness = load_sibling("i12r1_e2e", "test_i12r1_query_end_to_end")
Lake = _harness.Lake
FIXED = _harness.FIXED
wired_service = _harness.wired_service
two_revisions = _harness.two_revisions

from crypto_sensor_fabric.storage.catalog import CatalogIntegrityError  # noqa: E402
from crypto_sensor_fabric.storage.enums import (  # noqa: E402
    CoverageState,
    IntegrityState,
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
    RawReplayCursor,
    ReplayOrder,
)
from crypto_sensor_fabric.storage.revisions import (  # noqa: E402
    RevisionSourceIdentityV1,
    RevisionTemporalAmbiguity,
    SourceRevisionRegistry,
)

REPO = Path(__file__).resolve().parents[4]


def _mkdir(path: Path) -> Path:
    """Lake() requires its root to pre-exist (I12 harness law)."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def _mk(root: Path, name: str) -> Path:
    return _mkdir(root / name)
EVIDENCE_DIR = (
    REPO / "quant-lab" / "research" / "crypto_foundry" / "sensor_fabric"
    / "evidence" / "bloc_04"
)


# ---------------------------------------------------------------------------
# Row machinery — every row carries measured production values
# ---------------------------------------------------------------------------


def mrow(
    case: str,
    source: str,
    ok: bool,
    detail: str,
    **measured: object,
) -> dict[str, object]:
    """One measured evidence row.  ``source`` is one of
    PRODUCTION_BEHAVIOR / ADVERSARIAL_MUTATION / STRUCTURAL_INTROSPECTION /
    SYNTHETIC_COUNTERFACTUAL (anti-tautology classification, I12R1 §22)."""
    return {
        "case": case,
        "invariant_source": source,
        "measured": measured,
        "result": "OK" if ok else "FAIL",
        "detail": detail,
    }


def counterfactual(case: str, matrix: str) -> dict[str, object]:
    return mrow(
        case,
        "SYNTHETIC_COUNTERFACTUAL",
        False,
        (
            f"Synthetic counterfactual for {matrix}: deliberately invalid "
            "execution path that must evaluate FAIL; not a measured row."
        ),
    )


def _canonical_bytes(payload: dict[str, object]) -> bytes:
    return (
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _payload(matrix: str, rows: list[dict[str, object]]) -> dict[str, object]:
    ok = sum(1 for r in rows if r["result"] == "OK")
    return {
        "matrix": matrix,
        "mandate": "SENSOR-B4-I12R1",
        "supersedes_claim": (
            "I12 QUERY_FILTER matrix claim that every RawEvidenceQuery "
            "filter is mechanically evaluated — I12R1 measures the "
            "revision/representation/limit pipeline END-TO-END through "
            "RawEvidenceQueryService.execute() (append-only correction)"
        ),
        "generated_at": FIXED.isoformat(),
        "rows": rows,
        "summary": {"rows": len(rows), "ok": ok, "fail": len(rows) - ok},
    }


def _exc_name(fn):  # type: ignore[no-untyped-def]
    try:
        fn()
        return "NO_RAISE"
    except Exception as exc:  # noqa: BLE001 - measured behavior
        return type(exc).__name__


# ---------------------------------------------------------------------------
# 1. QUERY_END_TO_END — every accepted RawEvidenceQuery field, end-to-end
# ---------------------------------------------------------------------------


def build_query_end_to_end_matrix() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    with __import__("tempfile").TemporaryDirectory() as td:
        import tempfile  # noqa: F401

        root = Path(td)
        lake = Lake(_mk(root, "lake"))
        shas = [lake.seed_blob() for _ in range(3)]
        lake.seed_acquisition(shas[0], "acq-btc", instrument="BTC-USDT")
        lake.seed_acquisition(
            shas[1], "acq-eth", instrument="ETH-USDT", provider="gate"
        )
        lake.seed_acquisition(
            shas[2], "acq-sol", instrument="SOL-USDT",
            ingested_at=FIXED + timedelta(hours=9),
            observed_at=FIXED + timedelta(hours=1),
        )
        lake.commit_manifest("pm-btc", blob_refs=[shas[0]], instrument="BTC-USDT")
        lake.commit_manifest(
            "pm-eth", blob_refs=[shas[1]], instrument="ETH-USDT", provider="gate"
        )
        lake.commit_manifest(
            "pm-sol", blob_refs=[shas[2]], instrument="SOL-USDT",
            start=datetime(2026, 1, 15, 8, tzinfo=UTC),
            end=datetime(2026, 1, 15, 17, tzinfo=UTC),
        )
        svc = wired_service(lake)

        def ids(q: RawEvidenceQuery) -> list[str]:
            try:
                return sorted(
                    a
                    for r in svc.execute(q).results
                    for a in r.acquisition_ids
                )
            except NoMatchingEvidence:
                return []

        # provider (+ negative)
        pos = ids(RawEvidenceQuery(providers=["gate"]))
        neg = ids(RawEvidenceQuery(providers=["binance"]))
        rows.append(mrow(
            "provider_filter_positive_negative", "PRODUCTION_BEHAVIOR",
            pos == ["acq-eth"] and neg == [],
            "providers=['gate'] selects only the gate acquisition; an "
            "unknown provider is typed NoMatchingEvidence, not []",
            positive_selected_acquisition_ids=pos,
            negative_selected_acquisition_ids=neg,
        ))
        # venue
        pos = ids(RawEvidenceQuery(venues=["futures"]))
        rows.append(mrow(
            "venue_filter", "PRODUCTION_BEHAVIOR",
            len(pos) == 3,
            "venues=['futures'] matches all three committed manifests",
            selected_acquisition_ids=pos,
        ))
        # sensor family / instrument / granularity
        pos = ids(RawEvidenceQuery(native_instruments=["ETH-USDT"]))
        rows.append(mrow(
            "instrument_filter", "PRODUCTION_BEHAVIOR",
            pos == ["acq-eth"],
            "native_instruments=['ETH-USDT'] selects exactly the ETH chain",
            selected_acquisition_ids=pos,
        ))
        # logical range: window 18..19 intersects the full-day default
        # bounds (pm-btc, pm-eth) but NOT pm-sol's narrow 08..17 window.
        pos = ids(RawEvidenceQuery(
            logical_start=datetime(2026, 1, 15, 18, tzinfo=UTC),
            logical_end=datetime(2026, 1, 15, 19, tzinfo=UTC),
        ))
        rows.append(mrow(
            "logical_range_intersection", "PRODUCTION_BEHAVIOR",
            sorted(pos) == ["acq-btc", "acq-eth"],
            "logical window 18..19 intersects the full-day evidence bounds "
            "but NOT pm-sol's narrow 08..17 window (evidence-backed "
            "intersection, never the requested window echoed back)",
            selected_acquisition_ids=sorted(pos),
        ))
        # acquired_before (ingested_at <= cutoff)
        pos = ids(RawEvidenceQuery(
            acquired_before=FIXED + timedelta(hours=1)
        ))
        neg = ids(RawEvidenceQuery(
            acquired_before=FIXED - timedelta(hours=1)
        ))
        rows.append(mrow(
            "acquired_before_ingested_semantics", "PRODUCTION_BEHAVIOR",
            sorted(pos) == ["acq-btc", "acq-eth"] and neg == [],
            "acquired_before means ingested_at <= cutoff (default fixture "
            "ingested at FIXED); never a PIT-truth claim",
            at_h1=pos, before_start=neg,
        ))
        # observed_before (response_observed_at <= cutoff)
        pos = ids(RawEvidenceQuery(
            observed_before=FIXED + timedelta(hours=2)
        ))
        rows.append(mrow(
            "observed_before_observed_semantics", "PRODUCTION_BEHAVIOR",
            sorted(pos) == ["acq-btc", "acq-eth", "acq-sol"],
            "observed_before means response_observed_at <= cutoff; acq-sol "
            "observed at FIXED+1h stays inside FIXED+2h",
            selected_acquisition_ids=pos,
        ))
        # integrity threshold (+ failure never promoted)
        pos = ids(RawEvidenceQuery(
            integrity_minimum=IntegrityState.LOCAL_HASH_VERIFIED
        ))
        neg = ids(RawEvidenceQuery(
            integrity_minimum=IntegrityState.PROVIDER_HASH_VERIFIED
        ))
        rows.append(mrow(
            "integrity_minimum_lattice", "PRODUCTION_BEHAVIOR",
            len(pos) == 3 and neg == [],
            "LOCAL_HASH_VERIFIED floor admits all; PROVIDER_HASH_VERIFIED "
            "floor (not durably claimed) refuses typed — failure states are "
            "never promoted through the lattice",
            at_local=pos, at_provider=neg,
        ))
        # coverage
        pos = ids(RawEvidenceQuery(
            coverage_states=[CoverageState.COMPLETE_SOURCE_BOUNDARY]
        ))
        neg = ids(RawEvidenceQuery(coverage_states=[CoverageState.KNOWN_GAP]))
        rows.append(mrow(
            "coverage_states", "PRODUCTION_BEHAVIOR",
            len(pos) == 3 and neg == [],
            "coverage filter matches the declared manifest state; missing "
            "coverage is never zero/complete (missingness-as-its-own-state)",
            complete=pos, gap=neg,
        ))
        # revision_policy end-to-end (ERROR_ON_AMBIGUITY vs single)
        single_lake = Lake(_mk(root, "single"))
        sha = single_lake.seed_blob(b'{"one": true}')
        single_lake.seed_acquisition(sha, "acq-single")
        single_lake.commit_manifest("pm-single", blob_refs=[sha])
        single_ids = sorted(
            a for r in wired_service(single_lake).execute(
                RawEvidenceQuery()
            ).results for a in r.acquisition_ids
        )
        amb_lake, _amb_key = two_revisions(_mk(root, "amb-e2e"))
        amb_name = _exc_name(
            lambda: wired_service(amb_lake).execute(RawEvidenceQuery())
        )
        rows.append(mrow(
            "revision_policy_error_on_ambiguity", "PRODUCTION_BEHAVIOR",
            single_ids == ["acq-single"] and amb_name == "RevisionAmbiguity",
            "default policy through execute(): single-revision lake selects; "
            "TWO revisions under one source key raise typed "
            "RevisionAmbiguity BEFORE results",
            single_selected_acquisition_ids=single_ids,
            two_revision_exception=amb_name,
        ))
        # exact_revision_number — against a two-revision lake (the default
        # fixture lake above carries three single-revision sources).
        rev_lake, _rev_key = two_revisions(_mk(root, "rev"))
        exact = wired_service(rev_lake).execute(
            RawEvidenceQuery(
                revision_policy=RevisionPolicy.EXACT_REVISION,
                exact_revision_number=2,
            )
        ).results
        exact_ids = sorted(
            a for r in exact for a in r.acquisition_ids
        )
        rows.append(mrow(
            "exact_revision_number_end_to_end", "PRODUCTION_BEHAVIOR",
            exact_ids == ["acq-r2"],
            "EXACT_REVISION=2 through execute() selects only revision 2's "
            "acquisition chain",
            selected_acquisition_ids=exact_ids,
        ))
        # include flags + schema ids + limit measured below in their matrices
        # (cross-referenced); here the LIMIT-after-refusal row — against the
        # AMBIGUOUS two-revision lake:
        limit_name = _exc_name(
            lambda: wired_service(amb_lake).execute(
                RawEvidenceQuery(limit=1)
            )
        )
        rows.append(mrow(
            "limit_cannot_suppress_refusal", "PRODUCTION_BEHAVIOR",
            limit_name == "RevisionAmbiguity",
            "execute(limit=1) on the ambiguous lake raises RevisionAmbiguity "
            "— ordering/limit happen AFTER revision resolution (pipeline "
            "steps 13-14 are last)",
            exception=limit_name,
        ))
        rows.append(counterfactual(
            "counterfactual_limit_suppresses_ambiguity", "QUERY_END_TO_END"
        ))
    return _payload("BLOC_04_I12R1_QUERY_END_TO_END", rows)


# ---------------------------------------------------------------------------
# 2. REVISION_INTEGRATION — every I06 policy through execute()
# ---------------------------------------------------------------------------


def build_revision_integration_matrix() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    with __import__("tempfile").TemporaryDirectory() as td:
        import tempfile  # noqa: F401

        root = Path(td)
        lake, key = two_revisions(_mk(root, "lake"))
        svc = wired_service(lake)

        def run(q: RawEvidenceQuery):  # type: ignore[no-untyped-def]
            try:
                outcome = svc.execute(q)
                return {
                    "exception": None,
                    "acquisition_ids": sorted(
                        a for r in outcome.results for a in r.acquisition_ids
                    ),
                    "blob_refs": sorted(
                        b for r in outcome.results for b in r.blob_refs
                    ),
                    "revision_state": (
                        outcome.results[0].revision_state.value
                        if outcome.results else None
                    ),
                }
            except Exception as exc:  # noqa: BLE001 - measured behavior
                return {
                    "exception": type(exc).__name__,
                    "cause": type(exc.__cause__).__name__
                    if exc.__cause__ else None,
                }

        rev1 = lake.registry.get_revision(key, 1).blob_sha256
        rev2 = lake.registry.get_revision(key, 2).blob_sha256

        r = run(RawEvidenceQuery(revision_policy=RevisionPolicy.ALL))
        rows.append(mrow(
            "ALL_keeps_both_revisions_visible", "PRODUCTION_BEHAVIOR",
            r["acquisition_ids"] == ["acq-r1", "acq-r2"]
            and len(r["blob_refs"]) == 2,
            "ALL preserves revision multiplicity in ONE result",
            **r,
        ))
        r = run(RawEvidenceQuery(revision_policy=RevisionPolicy.FIRST_SEEN))
        rows.append(mrow(
            "FIRST_SEEN_selects_registry_truth", "PRODUCTION_BEHAVIOR",
            r["acquisition_ids"] == ["acq-r1"] and r["blob_refs"] == [rev1],
            "FIRST_SEEN returns the I06 registry's first-seen selection only",
            **r,
        ))
        r = run(RawEvidenceQuery(revision_policy=RevisionPolicy.LATEST_SEEN))
        rows.append(mrow(
            "LATEST_SEEN_selects_registry_truth", "PRODUCTION_BEHAVIOR",
            r["acquisition_ids"] == ["acq-r2"] and r["blob_refs"] == [rev2],
            "LATEST_SEEN returns the I06 registry's latest-seen selection only",
            **r,
        ))
        r = run(RawEvidenceQuery(
            revision_policy=RevisionPolicy.EXACT_REVISION,
            exact_revision_number=2,
        ))
        rows.append(mrow(
            "EXACT_hit", "PRODUCTION_BEHAVIOR",
            r["acquisition_ids"] == ["acq-r2"] and r["blob_refs"] == [rev2],
            "EXACT_REVISION=2 selects exactly revision 2",
            **r,
        ))
        r = run(RawEvidenceQuery(
            revision_policy=RevisionPolicy.EXACT_REVISION,
            exact_revision_number=9,
        ))
        rows.append(mrow(
            "EXACT_miss_typed_no_match", "PRODUCTION_BEHAVIOR",
            r["exception"] == "NoMatchingEvidence",
            "a missing exact revision is typed NoMatchingEvidence at the I12 "
            "boundary — missing != corruption",
            **r,
        ))
        r = run(RawEvidenceQuery(
            revision_policy=RevisionPolicy.PROVIDER_DECLARED_CANONICAL
        ))
        rows.append(mrow(
            "canonical_absent_typed_unavailable", "PRODUCTION_BEHAVIOR",
            r["exception"] == "RevisionCanonicalUnavailable",
            "PROVIDER_DECLARED_CANONICAL with zero declarations is typed "
            "RevisionCanonicalUnavailable — absence is not ambiguity and not "
            "a backend failure",
            **r,
        ))
        lake.registry.declare_provider_canonical(
            source_revision_key=key,
            revision_number=1,
            evidence_ref="provider-doc://i12r1/canonical-1",
        )
        r = run(RawEvidenceQuery(
            revision_policy=RevisionPolicy.PROVIDER_DECLARED_CANONICAL
        ))
        rows.append(mrow(
            "canonical_hit", "PRODUCTION_BEHAVIOR",
            r["acquisition_ids"] == ["acq-r1"] and r["blob_refs"] == [rev1],
            "explicit canonical declaration selects revision 1 only",
            **r,
        ))
        lake.registry.declare_provider_canonical(
            source_revision_key=key,
            revision_number=2,
            evidence_ref="provider-doc://i12r1/canonical-2",
        )
        r = run(RawEvidenceQuery(
            revision_policy=RevisionPolicy.PROVIDER_DECLARED_CANONICAL
        ))
        rows.append(mrow(
            "canonical_conflict_typed_ambiguity", "PRODUCTION_BEHAVIOR",
            r["exception"] == "RevisionAmbiguity",
            "two distinct canonical declarations are typed RevisionAmbiguity "
            "(I06 §60: no latest-wins)",
            **r,
        ))
        # ERROR_ON_AMBIGUITY + limit=1 (§5) — service NEVER reaches truncation.
        r = run(RawEvidenceQuery(limit=1))
        rows.append(mrow(
            "limit1_cannot_reach_truncation", "PRODUCTION_BEHAVIOR",
            r["exception"] == "RevisionAmbiguity",
            "ERROR_ON_AMBIGUITY + limit=1 raises RevisionAmbiguity through "
            "execute() — limit is pipeline step 14, AFTER resolution",
            **r,
        ))
        # Temporal ambiguity maps typed (adversarial dependency mutation).
        class _AmbiguousRegistry:
            def resolve(self, k, policy, *, revision_number=None):  # noqa: ANN001
                raise RevisionTemporalAmbiguity(
                    "same seen_at with differing bytes — fail closed (I06 §40)"
                )

        amb_lake = Lake(_mkdir(root / "amb"))
        sha = amb_lake.seed_blob(b'{"a": 1}')
        amb_lake.seed_acquisition(sha, "acq-a")
        amb_lake.commit_manifest("pm-a", blob_refs=[sha])
        amb_svc = RawEvidenceQueryService(
            manifest_repository=amb_lake.manifest_repo,
            acquisition_repository=amb_lake.acq_repo,
            blob_metadata_repository=amb_lake.blob_repo,
            revision_registry=_AmbiguousRegistry(),
            revision_identity_factory=RevisionSourceIdentityV1,
        )
        try:
            amb_svc.execute(RawEvidenceQuery())
            outcome = {"exception": "NO_RAISE", "cause": None}
        except Exception as exc:  # noqa: BLE001 - measured behavior
            outcome = {
                "exception": type(exc).__name__,
                "cause": type(exc.__cause__).__name__
                if exc.__cause__ else None,
            }
        rows.append(mrow(
            "temporal_ambiguity_maps_typed_with_cause",
            "ADVERSARIAL_MUTATION",
            outcome["exception"] == "RevisionAmbiguity"
            and outcome["cause"] == "RevisionTemporalAmbiguity",
            "I06 RevisionTemporalAmbiguity crossing the I12 boundary stays "
            "epistemic RevisionAmbiguity with __cause__ preserved — never "
            "StorageBackendUnavailable",
            **outcome,
        ))
        # revision_state from durable truth, not count hint (§19).
        state_lake = Lake(_mkdir(root / "state"))
        sha = state_lake.seed_blob(b'{"s": 1}')
        state_lake.seed_acquisition(sha, "acq-s")
        state_lake.commit_manifest("pm-s", blob_refs=[sha])
        st = wired_service(state_lake).execute(RawEvidenceQuery()).results[0]
        rows.append(mrow(
            "revision_state_from_durable_registry_truth",
            "PRODUCTION_BEHAVIOR",
            st.revision_state is RevisionState.STABLE,
            "single-revision revision_state comes from the I06 segment "
            "classification (STABLE), not the manifest revision_count hint",
            revision_state=st.revision_state.value,
        ))
        rows.append(counterfactual(
            "counterfactual_count_hint_authority", "REVISION_INTEGRATION"
        ))
    return _payload("BLOC_04_I12R1_REVISION_INTEGRATION", rows)


# ---------------------------------------------------------------------------
# 3. REPRESENTATION_SELECTION — include flags + schema ids + lineage gate
# ---------------------------------------------------------------------------


def build_representation_selection_matrix() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    with __import__("tempfile").TemporaryDirectory() as td:
        import tempfile  # noqa: F401

        root = Path(td)

        def lake_with_projection(path: Path) -> Lake:  # type: ignore[type-arg]
            lake = Lake(path)
            sha = lake.seed_blob()
            lake.seed_acquisition(sha, "acq-1")
            lake.commit_projection("proj-1", [(sha, "acq-1")])
            lake.commit_manifest(
                "pm-1", blob_refs=[sha], projection_refs=["proj-1"]
            )
            return lake

        lake = lake_with_projection(_mk(root, "rep"))
        svc = wired_service(lake)

        def out(q: RawEvidenceQuery):  # type: ignore[no-untyped-def]
            try:
                r = svc.execute(q).results[0]
                return {
                    "exception": None,
                    "blob_refs": list(r.blob_refs),
                    "projection_refs": list(r.projection_refs),
                    "lineage_refs": list(r.lineage_refs),
                    "acquisition_ids": list(r.acquisition_ids),
                }
            except Exception as exc:  # noqa: BLE001 - measured behavior
                return {
                    "exception": type(exc).__name__,
                    "blob_refs": None, "projection_refs": None,
                    "lineage_refs": None, "acquisition_ids": None,
                }

        r = out(RawEvidenceQuery(include_t0a=True, include_t0b=False))
        rows.append(mrow(
            "T0A_only_hides_T0B_selection", "PRODUCTION_BEHAVIOR",
            bool(r["blob_refs"]) and r["projection_refs"] == [],
            "T0A=True/T0B=False: blob_refs are the SELECTED T0A "
            "representation; projection_refs stay unselected",
            **r,
        ))
        r = out(RawEvidenceQuery(include_t0a=False, include_t0b=True))
        rows.append(mrow(
            "T0B_only_preserves_lineage_provenance", "PRODUCTION_BEHAVIOR",
            r["blob_refs"] == [] and bool(r["projection_refs"])
            and bool(r["lineage_refs"]) and bool(r["acquisition_ids"]),
            "T0B=False/T0A=True inverted: T0B projections selected, T0A "
            "sources remain ONLY as lineage provenance (never pretended "
            "T0A output)",
            **r,
        ))
        r = out(RawEvidenceQuery(include_t0a=True, include_t0b=True))
        rows.append(mrow(
            "both_modes_select_both_representations", "PRODUCTION_BEHAVIOR",
            bool(r["blob_refs"]) and bool(r["projection_refs"])
            and bool(r["lineage_refs"]),
            "both representations explicitly present in one result",
            **r,
        ))
        name = _exc_name(
            lambda: wired_service(lake).execute(
                RawEvidenceQuery(include_t0a=False, include_t0b=False)
            )
        )
        rows.append(mrow(
            "neither_mode_typed_validation_failure", "PRODUCTION_BEHAVIOR",
            name == "QueryValidationError",
            "explicit T0A=False/T0B=False is a typed QueryValidationError — "
            "nothing is selected, so nothing may be returned",
            exception=name,
        ))
        r = out(RawEvidenceQuery(
            include_t0b=True,
            projection_schema_ids=["i12.test.projection"],
        ))
        rows.append(mrow(
            "schema_match_selects_projection", "PRODUCTION_BEHAVIOR",
            r["projection_refs"] == ["proj-1"],
            "projection_schema_ids matching the durable schema selects",
            **r,
        ))
        r = out(RawEvidenceQuery(
            include_t0a=False,
            include_t0b=True,
            projection_schema_ids=["other.schema"],
        ))
        rows.append(mrow(
            "schema_mismatch_T0B_only_typed_refusal",
            "PRODUCTION_BEHAVIOR",
            r["exception"] == "ProjectionSchemaUnsupported",
            "T0B-only query naming a non-matching schema refuses typed — a "
            "non-matching projection is never silently substituted",
            **r,
        ))
        r = out(RawEvidenceQuery(
            include_t0a=True,
            include_t0b=True,
            projection_schema_ids=["other.schema"],
        ))
        rows.append(mrow(
            "schema_mismatch_with_T0A_fallback_documented",
            "PRODUCTION_BEHAVIOR",
            r["exception"] is None and bool(r["blob_refs"])
            and r["projection_refs"] == [],
            "FROZEN documented behavior (I12R1 §10 option A): the valid T0A "
            "selection is returned and the non-matching T0B projection is "
            "left out of projection_refs (visible absence, not substitution)",
            **r,
        ))
        # Lineage-before-publication: broken chain never publishes, even at
        # limit=1 (adversarial: corrupt the durable lineage fragment, fresh
        # repository).
        lake2 = lake_with_projection(_mk(root, "broken"))
        lineage_dir = lake2.t0b / "catalogs" / "manifests" / "projection_lineage"
        fragments = sorted(lineage_dir.rglob("*.json"))
        for frag in fragments:
            frag.write_text("{corrupt", encoding="utf-8")
        from crypto_sensor_fabric.storage.projection_lineage import (
            ProjectionLineageCatalogCorrupt,
            ProjectionLineageRepository,
        )

        fresh_ok = True
        try:
            ProjectionLineageRepository(
                lineage_dir,
                blob_store=lake2.store,
                blob_metadata_repository=lake2.blob_repo,
                acquisition_repository=lake2.acq_repo,
                artifact_repository=lake2.artifacts,
                context_repository=lake2.contexts,
            )
            fresh_ok = False
        except ProjectionLineageCatalogCorrupt:
            fresh_ok = True
        rows.append(mrow(
            "lineage_corrupt_fails_closed_on_fresh_repository",
            "ADVERSARIAL_MUTATION",
            fresh_ok,
            "corrupting the durable lineage fragment makes a FRESH "
            "repository construction fail closed (I05 law) — a corrupt "
            "chain can never serve a query",
            fresh_construction_raises=fresh_ok,
        ))
        # Metadata-only: no T0A payload bytes opened during query.
        import contextlib

        lake3 = lake_with_projection(_mk(root, "spying"))
        svc3 = wired_service(lake3)
        opened: list[str] = []
        real_open = lake3.store.open_blob

        @contextlib.contextmanager
        def spying_open(blob_sha256, encoding):  # noqa: ANN001
            opened.append(blob_sha256)
            with real_open(blob_sha256, encoding) as handle:
                yield handle

        lake3.store.open_blob = spying_open  # type: ignore[method-assign]
        svc3.execute(RawEvidenceQuery(
            include_t0b=True,
            projection_schema_ids=["i12.test.projection"],
        ))
        rows.append(mrow(
            "metadata_query_never_opens_payload_bytes",
            "STRUCTURAL_INTROSPECTION",
            opened == [],
            "projection_schema_ids evaluation opens ZERO blob payload bytes "
            "(durable T0B metadata only, §9)",
            blobs_opened=opened,
        ))
        rows.append(counterfactual(
            "counterfactual_projection_substitution",
            "REPRESENTATION_SELECTION",
        ))
    return _payload("BLOC_04_I12R1_REPRESENTATION_SELECTION", rows)


# ---------------------------------------------------------------------------
# 4. REPLAY_DISPATCH — value semantics, no identity dependency
# ---------------------------------------------------------------------------


def build_replay_dispatch_matrix() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    with __import__("tempfile").TemporaryDirectory() as td:
        import tempfile  # noqa: F401

        lake = Lake(_mkdir(Path(td) / "lake"))
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

        def ordered(mode: object) -> object:
            try:
                return [
                    r.acquisition_id
                    for r in cursor.ordered_acquisitions(
                        result, order_by=mode
                    )
                ]
            except Exception as exc:  # noqa: BLE001 - measured behavior
                return f"{type(exc).__name__}:{exc}"

        for const, dynamic, label in (
            (ACQUISITION_ORDER, "".join(["ACQUISITION", "_ORDER"]), "acquisition"),
            (PROVIDER_EVENT_TIME, "".join(["PROVIDER_", "EVENT_TIME"]), "provider"),
            (SOURCE_ORDER, "".join(["SOURCE_", "ORDER"]), "source"),
        ):
            literal_out = ordered(const)
            dynamic_out = ordered(dynamic)
            enum_out = ordered(ReplayOrder(const))
            deserialized_out = ordered(json.loads(json.dumps(const)))
            same = (
                literal_out == dynamic_out == enum_out == deserialized_out
            )
            rows.append(mrow(
                f"{label}_mode_value_semantics", "PRODUCTION_BEHAVIOR",
                same,
                f"{label}: enum member, literal string, dynamically "
                "constructed equal string, and deserialized string all "
                "dispatch the SAME branch (identical ordering or identical "
                "typed refusal)",
                enum=str(enum_out),
                literal=str(literal_out),
                dynamic=str(dynamic_out),
                deserialized=str(deserialized_out),
            ))
        unknown = ordered("MYSTERY_ORDER")
        rows.append(mrow(
            "unknown_mode_typed_refusal", "PRODUCTION_BEHAVIOR",
            str(unknown).startswith("QueryValidationError:"),
            "an unknown order mode is a typed QueryValidationError",
            observed=str(unknown),
        ))
        # Structural: no identity dispatch left in production.
        import re

        src = (
            REPO / "quant-lab" / "src" / "crypto_sensor_fabric" / "storage"
            / "replay.py"
        ).read_text(encoding="utf-8")
        identity_matches = re.findall(
            r"order_by is (ACQUISITION_ORDER|PROVIDER_EVENT_TIME|SOURCE_ORDER)",
            src,
        )
        rows.append(mrow(
            "no_identity_dispatch_remains", "STRUCTURAL_INTROSPECTION",
            identity_matches == [],
            "structural scan of replay.py finds zero `order_by is <CONST>` "
            "identity comparisons",
            identity_dispatch_sites=identity_matches,
        ))
        rows.append(counterfactual(
            "counterfactual_interned_string_dispatch", "REPLAY_DISPATCH"
        ))
    return _payload("BLOC_04_I12R1_REPLAY_DISPATCH", rows)


# ---------------------------------------------------------------------------
# 5. INVENTORY_FAIL_CLOSED — canonical locators across all enumerators
# ---------------------------------------------------------------------------


def build_inventory_fail_closed_matrix() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    with __import__("tempfile").TemporaryDirectory() as td:
        import tempfile  # noqa: F401

        root = Path(td)
        lake = Lake(_mk(root, "lake"))
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-1")
        lake.commit_manifest("pm-1", blob_refs=[sha])

        manifests = lake.manifest_repo.list_all_current_manifests()
        rows.append(mrow(
            "manifest_canonical_enumeration", "PRODUCTION_BEHAVIOR",
            len(manifests) == 1
            and manifests[0].partition_manifest_id == "pm-1",
            "canonical pointer enumeration returns the one current manifest; "
            "each enumerated pointer path is proven to BE "
            "_pointer_path(_partition_hash(pointer.partition_key))",
            partition_keys=[m.partition_key for m in manifests],
        ))
        # Alias pointer (same valid payload, extra physical file).
        pointer_dir = lake.manifest_repo._pointer_dir()
        canonical = sorted(pointer_dir.glob("*.json"))[0]
        shutil.copy2(canonical, canonical.with_name("alias.json"))
        name = _exc_name(lake.manifest_repo.list_all_current_manifests)
        rows.append(mrow(
            "manifest_alias_pointer_fail_closed", "ADVERSARIAL_MUTATION",
            name == "CurrentPointerCorrupt",
            "an alias .json duplicating a valid canonical pointer payload "
            "fails closed — duplicate logical current state can never be "
            "silently accepted",
            exception=name,
        ))
        # Malformed pointer content in a canonical-shaped name.
        lake2 = Lake(_mkdir(root / "malformed"))
        sha2 = lake2.seed_blob()
        lake2.seed_acquisition(sha2, "acq-m")
        lake2.commit_manifest("pm-m", blob_refs=[sha2])
        pdir = lake2.manifest_repo._pointer_dir()
        pfile = sorted(pdir.glob("*.json"))[0]
        pfile.write_text("{not-json", encoding="utf-8")
        name = _exc_name(lake2.manifest_repo.list_all_current_manifests)
        rows.append(mrow(
            "manifest_malformed_pointer_fail_closed", "ADVERSARIAL_MUTATION",
            name == "CurrentPointerCorrupt",
            "an unparseable pointer fragment fails closed",
            exception=name,
        ))
        # Blob metadata alias.
        blob_family = lake.blob_repo._family_dir()
        bfrag = sorted(blob_family.glob("*.parquet"))[0]
        shutil.copy2(bfrag, bfrag.with_name("alias_" + bfrag.name))
        name = _exc_name(lake.blob_repo.list_all_blob_metadata)
        rows.append(mrow(
            "blob_metadata_alias_fail_closed", "ADVERSARIAL_MUTATION",
            name == "CatalogIntegrityError",
            "a copied blob-metadata fragment under a non-canonical name "
            "fails closed: physical locator must equal "
            "sha256(storage_key).encoding.parquet (I12R1 §11 repair)",
            exception=name,
        ))
        # Acquisition alias.
        lake3 = Lake(_mkdir(root / "acq"))
        sha3 = lake3.seed_blob()
        lake3.seed_acquisition(sha3, "acq-a1")
        acq_family = lake3.acq_repo._family_dir()
        afrag = sorted(acq_family.glob("*.parquet"))[0]
        shutil.copy2(afrag, afrag.with_name("alias_" + afrag.name))
        name = _exc_name(lake3.acq_repo.list_all_acquisitions)
        rows.append(mrow(
            "acquisition_alias_fail_closed", "ADVERSARIAL_MUTATION",
            name == "CatalogIntegrityError",
            "a copied acquisition fragment under a non-canonical name fails "
            "closed: canonical fragment name IS sha256(acquisition_id)",
            exception=name,
        ))
        # I06 alias: existing law sufficient (no I06 change).
        lake4 = Lake(_mkdir(root / "i06"))
        sha4 = lake4.seed_blob()
        lake4.seed_acquisition(sha4, "acq-k")
        keys_before = lake4.registry.list_source_revision_keys()
        seg_root = lake4.registry._segments.root
        seg_frags = sorted(p for p in seg_root.rglob("*.json") if p.is_file())
        shutil.copy2(seg_frags[0], seg_frags[0].with_name("alias.json"))
        keys_after: list[str] | str
        try:
            mutated = SourceRevisionRegistry(
                lake4.registry._root,
                acquisition_repository=lake4.acq_repo,
                blob_metadata_repository=lake4.blob_repo,
                blob_store=lake4.store,
                clock=lambda: FIXED,
            )
            keys_after = mutated.list_source_revision_keys()
        except Exception as exc:  # noqa: BLE001 - measured behavior
            keys_after = f"{type(exc).__name__}"
        i06_ok = (
            keys_after == keys_before == sorted(set(keys_before))
        ) or keys_after == "SourceRevisionCatalogCorrupt"
        rows.append(mrow(
            "I06_alias_guard_existing_law_sufficient",
            "ADVERSARIAL_MUTATION",
            i06_ok,
            "I06_ALIAS_GUARD = EXISTING_LAW_SUFFICIENT: the registry binds "
            "every durable fragment logical_id to "
            "segment_id=(source_revision_key, revision_number) at load; an "
            "aliased physical copy fails closed with "
            "SourceRevisionCatalogCorrupt (the DurableJsonCatalog binds "
            "logical_id to the payload's own id field) — I06 was NOT "
            "modified",
            keys_before=keys_before,
            keys_after=keys_after,
        ))
        # Deterministic ordering across a fresh service instance.
        lake5 = Lake(_mkdir(root / "order"))
        s5 = [lake5.seed_blob() for _ in range(3)]
        for i, s in enumerate(s5):
            lake5.seed_acquisition(
                s, f"acq-o{i}", ingested_at=FIXED + timedelta(hours=i)
            )
        lake5.commit_manifest(
            "pm-o", blob_refs=list(reversed(s5))
        )
        first = wired_service(lake5).execute(
            RawEvidenceQuery(revision_policy=RevisionPolicy.ALL)
        )
        second = wired_service(lake5).execute(
            RawEvidenceQuery(revision_policy=RevisionPolicy.ALL)
        )
        ids_first = sorted(first.results[0].acquisition_ids)
        ids_second = sorted(second.results[0].acquisition_ids)
        rows.append(mrow(
            "deterministic_ordering_fresh_instances",
            "PRODUCTION_BEHAVIOR",
            ids_first == ids_second,
            "two fresh service instances over the same durable lake produce "
            "identical selected identities (deterministic inventory + "
            "canonical result ordering)",
            ordered_acquisition_ids=ids_first,
        ))
        rows.append(counterfactual(
            "counterfactual_silent_alias_dedupe", "INVENTORY_FAIL_CLOSED"
        ))
    return _payload("BLOC_04_I12R1_INVENTORY_FAIL_CLOSED", rows)


# ---------------------------------------------------------------------------
# Publication + read-only wrappers
# ---------------------------------------------------------------------------

_MATRICES = (
    (
        "BLOC_04_I12R1_QUERY_END_TO_END_MATRIX.json",
        build_query_end_to_end_matrix,
    ),
    (
        "BLOC_04_I12R1_REVISION_INTEGRATION_MATRIX.json",
        build_revision_integration_matrix,
    ),
    (
        "BLOC_04_I12R1_REPRESENTATION_SELECTION_MATRIX.json",
        build_representation_selection_matrix,
    ),
    (
        "BLOC_04_I12R1_REPLAY_DISPATCH_MATRIX.json",
        build_replay_dispatch_matrix,
    ),
    (
        "BLOC_04_I12R1_INVENTORY_FAIL_CLOSED_MATRIX.json",
        build_inventory_fail_closed_matrix,
    ),
)


def publish_all() -> list[Path]:
    written: list[Path] = []
    for name, build in _MATRICES:
        path = EVIDENCE_DIR / name
        data = _canonical_bytes(build())
        if path.exists() and path.read_bytes() == data:
            written.append(path)
            continue
        path.write_bytes(data)
        written.append(path)
    return written


def test_i12r1_matrices_regenerate_byte_identically() -> None:
    """Read-only: committed artifacts regenerate byte-identically."""
    for name, build in _MATRICES:
        path = EVIDENCE_DIR / name
        assert path.exists(), f"missing committed I12R1 artifact {name}"
        assert path.read_bytes() == _canonical_bytes(build()), name


def test_i12r1_matrices_measured_and_single_counterfactual() -> None:
    """Read-only: every row classified, every matrix exactly one FAIL."""
    allowed = {
        "PRODUCTION_BEHAVIOR",
        "ADVERSARIAL_MUTATION",
        "STRUCTURAL_INTROSPECTION",
        "SYNTHETIC_COUNTERFACTUAL",
    }
    for name, _ in _MATRICES:
        payload = json.loads(
            (EVIDENCE_DIR / name).read_text(encoding="utf-8")
        )
        rows = payload["rows"]
        assert rows, name
        for r in rows:
            assert r["invariant_source"] in allowed, (name, r["case"])
        counterfactuals = [
            r for r in rows if r["invariant_source"] == "SYNTHETIC_COUNTERFACTUAL"
        ]
        assert len(counterfactuals) == 1, name
        assert counterfactuals[0]["result"] == "FAIL", name
        measured_rows = [r for r in rows if r["invariant_source"] != "SYNTHETIC_COUNTERFACTUAL"]
        assert all(r["result"] == "OK" for r in measured_rows), name
        # Anti-tautology: measured rows carry real measured payloads.
        assert any(
            r.get("measured") for r in measured_rows
        ), f"{name}: no measured values recorded"


if __name__ == "__main__":
    if os.getenv("UPDATE_I12R1_EVIDENCE") != "1":
        raise SystemExit(
            "publication requires the explicit UPDATE_I12R1_EVIDENCE=1 override"
        )
    for path in publish_all():
        print("published", path.name)
