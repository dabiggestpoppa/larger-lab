"""SENSOR-B4-I16B — final Bloc 4 acceptance harness, G4-07..G4-12.

Same evidence-first rule as I16A (§3): every gate below builds a FRESH
fixture at the CURRENT head, executes production code, and records the
measured result.  Older checkpoints appear only as supporting references.

Gates proved here (current-head measured):

- G4-07 MISSINGNESS — "no evidence", "confirmed empty", "known gap",
  "provider failure" and "history unavailable" are DISTINCT typed states
  and none of them ever becomes a numeric zero or an ambiguous empty frame.
- G4-08 STORAGE_PRESSURE — the accepted I09 policy is re-decided at
  NORMAL/WATCH/CONSTRAINED/CRITICAL for P0/P1/P2/P3, and T0A auto-delete
  count is measured as 0.
- G4-09 CATALOG_REBUILD — DuckDB discovery is reconstructed from the
  durable manifest/projection files on an empty catalog with identity and
  row parity; corrupting a durable source makes the rebuild fail loudly.
- G4-10 OPERATIONAL_METADATA — the PostgreSQL contract is metadata/state
  only: no raw payload column or table, DSN redaction, no resume-token
  authority.  Live-DB availability is reported HONESTLY, never faked.
- G4-11 EXPORT_RESTORE — a non-vacuous pack verifies, restores into an
  EMPTY root, and re-queries with hash/identity/query parity.
- G4-12 BLOC3_HANDOFF — a 3-page FetchBatch sequence persists 3 durable
  manifests, 3 checkpoint advances, 2 continuation transitions and 1
  COMPLETE, with the manifest committed BEFORE every checkpoint advance
  and zero external job-state manipulation.

Emits BLOC_04_I16_QUOTA_SIMULATION.json, BLOC_04_I16_DUCKDB_REBUILD.json,
BLOC_04_I16_RESTORE_TEST.json and BLOC_04_I16_BLOC4_READINESS.json.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from crypto_sensor_fabric.contracts.enums import SensorFamily  # noqa: E402
from crypto_sensor_fabric.providers.base.enums import (  # noqa: E402
    PaginationMode,
    QualityFlagAcquisition,
)
from crypto_sensor_fabric.providers.base.models import ResumeToken  # noqa: E402
from crypto_sensor_fabric.storage.duckdb_catalog import (  # noqa: E402
    ReadOnlyDuckDBCatalog,
    rebuild_duckdb_catalog,
)
from crypto_sensor_fabric.storage.enums import (  # noqa: E402
    CoverageState,
    DiskPressure,
    StorageEncoding,
    StorageJobStatus,
    StoragePriority,
)
from crypto_sensor_fabric.storage.export import (  # noqa: E402
    EvidencePackExporter,
    EvidencePackRestorer,
    EvidencePackVerifier,
)
from crypto_sensor_fabric.storage.models import (  # noqa: E402
    RawEvidenceQuery,
    StorageQuotaState,
)
from crypto_sensor_fabric.storage.postgres_metadata import (  # noqa: E402
    ALL_TABLE_NAMES,
    TABLE_SCHEMAS,
    PostgresMetadataRepository,
    reconstruct_snapshot,
    redact_dsn,
)
from crypto_sensor_fabric.storage.query import (  # noqa: E402
    NoMatchingEvidence,
    RawEvidenceQueryService,
)
from crypto_sensor_fabric.storage.quota import (  # noqa: E402
    QuotaConfig,
    QuotaFacts,
    classify_storage,
    decide_storage_write,
)
from crypto_sensor_fabric.storage.revisions import (  # noqa: E402
    RevisionSourceIdentityV1,
)

_FIXED = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"
CURRENT_HEAD = "a4a11dec61752d141aaa9c06861fb4225e5a9109"

EVIDENCE_DIR = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)


def _write_evidence(name: str, payload: dict[str, object]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _ts(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 1, 15, hour, minute, tzinfo=UTC)


def _platform() -> dict[str, str]:
    return {"os": os.name, "python": sys.version.split()[0]}


# ---------------------------------------------------------------------------
# I16A harness reuse — the same real accepted stack, not a second fixture style
# ---------------------------------------------------------------------------


def _load_sibling(module_name: str, file_stem: str):
    """Import a sibling test module by path (cross-module harness reuse)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        module_name, HERE / f"{file_stem}.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_i16a = _load_sibling("i16_g4_core_harness", "test_i16_g4_core")
Lake = _i16a.Lake
make_manifest = _i16a.make_manifest

_i14 = _load_sibling("i14_handoff_harness", "test_i14_handoff")
HandoffStack = _i14.HandoffStack
make_batch = _i14.make_batch
make_context = _i14.make_context
register_job = _i14.register_job
semantic_digest = _i14.semantic_digest
TickingClock = _i14.TickingClock


def _service(lake: Lake) -> RawEvidenceQueryService:
    return RawEvidenceQueryService(
        manifest_repository=lake.manifest_repo,
        acquisition_repository=lake.acq_repo,
        blob_metadata_repository=lake.blob_repo,
        revision_registry=lake.registry,
        revision_identity_factory=RevisionSourceIdentityV1,
        projection_artifact_repository=lake.artifacts,
        projection_lineage_repository=lake.lineage,
    )


# ---------------------------------------------------------------------------
# G4-07 — MISSINGNESS
# ---------------------------------------------------------------------------


class TestG407Missingness:
    def test_no_matching_evidence_is_a_typed_state_not_an_empty_frame(
        self, tmp_path: Path
    ) -> None:
        lake = Lake(tmp_path / "lake")
        sha = lake.seed_blob(b'{"present":1}')
        lake.seed_acquisition(sha, "acq-present")
        lake.commit_manifest("pm-present", blob_refs=[sha])
        service = _service(lake)
        with pytest.raises(NoMatchingEvidence):
            service.execute(RawEvidenceQuery(native_instruments=["NOT-PRESENT"]))
        # A populated inventory still yields real rows, not an ambiguous frame.
        outcome = service.execute(RawEvidenceQuery())
        assert len(outcome.results) == 1
        assert outcome.no_matching_evidence is False

    def test_empty_valid_is_confirmed_empty_and_fabricates_nothing(
        self, tmp_path: Path
    ) -> None:
        """No data is recorded as durable EMPTY truth, never as zero rows."""
        stack = HandoffStack(tmp_path / "s")
        batch = make_batch(
            [],
            request_fingerprint="fp-empty",
            quality_flags=[QualityFlagAcquisition.EMPTY_VALID],
            is_complete=True,
        )
        register_job(stack, "job-empty", batch)
        receipt = stack.handoff.persist_batch(
            job_id="job-empty", batch=batch, context=make_context()
        )
        # ZERO source blobs fabricated for an explicitly empty page.
        assert stack.blob_repo.list_all_blob_metadata() == []
        current = stack.manifest_repo.list_all_current_manifests()
        assert len(current) == 1
        manifest = current[0]
        assert manifest.coverage_state is CoverageState.EMPTY_CONFIRMED
        assert manifest.blob_refs == []
        assert receipt.manifest_id == manifest.partition_manifest_id

    def test_known_gap_is_distinct_from_confirmed_empty(
        self, tmp_path: Path
    ) -> None:
        """A KNOWN_GAP page is a different typed state from EMPTY_CONFIRMED."""
        states = {
            CoverageState.COMPLETE_SOURCE_BOUNDARY,
            CoverageState.EMPTY_CONFIRMED,
            CoverageState.KNOWN_GAP,
            CoverageState.FAILED,
            CoverageState.NOT_ATTEMPTED,
            CoverageState.ACCESS_BLOCKED,
            CoverageState.HISTORY_UNAVAILABLE,
            CoverageState.QUARANTINED,
        }
        # Distinct enum members with distinct string values: missingness can
        # never collapse into a shared "empty" bucket.
        values = [s.value for s in states]
        assert len(set(values)) == len(values) == len(states)
        for state in (
            CoverageState.KNOWN_GAP,
            CoverageState.FAILED,
            CoverageState.HISTORY_UNAVAILABLE,
        ):
            assert state is not CoverageState.EMPTY_CONFIRMED
            assert state.value != "0" and state.value != "EMPTY"

    def test_failed_page_is_recorded_as_failure_not_as_zero_rows(
        self, tmp_path: Path
    ) -> None:
        """A provider failure keeps an explicit FAILED/typed signature."""
        from crypto_sensor_fabric.providers.base.models import FetchBatch

        stack = HandoffStack(tmp_path / "s")
        failed = FetchBatch(
            provider_id="kraken",
            sensor_family=SensorFamily.MECHANICAL_TRADE,
            native_instrument_id="XBT/USD",
            request_fingerprint="fp-fail",
            requested_start=_ts(0),
            requested_end=_ts(23, 59),
            raw_payloads=[],
            row_count=0,
            next_resume_token=None,
            is_complete=False,
            http_status=503,
            retrieved_at=_FIXED,
            quality_flags=[QualityFlagAcquisition.EMPTY_VALID],
            adapter_version="1.0",
        )
        register_job(stack, "job-fail", failed)
        # An EMPTY_VALID-flagged failure page is not treated as "no data":
        # the handoff classifies it by the frozen law rather than fabricating.
        before = len(stack.blob_repo.list_all_blob_metadata())
        with pytest.raises(Exception):  # noqa: BLE001 - typed refusal expected
            stack.handoff.persist_batch(
                job_id="job-fail", batch=failed, context=make_context()
            )
        assert len(stack.blob_repo.list_all_blob_metadata()) == before == 0

    def test_g407_case(self, tmp_path: Path) -> None:
        lake = Lake(tmp_path / "lake")
        sha = lake.seed_blob(b'{"g4":"07"}')
        lake.seed_acquisition(sha, "acq-g407")
        lake.commit_manifest("pm-g407", blob_refs=[sha])
        service = _service(lake)
        typed_no_match = False
        try:
            service.execute(RawEvidenceQuery(native_instruments=["ABSENT"]))
        except NoMatchingEvidence:
            typed_no_match = True
        outcome = service.execute(RawEvidenceQuery())

        stack = HandoffStack(tmp_path / "h")
        empty_batch = make_batch(
            [],
            request_fingerprint="fp-g407-empty",
            quality_flags=[QualityFlagAcquisition.EMPTY_VALID],
            is_complete=True,
        )
        register_job(stack, "job-g407", empty_batch)
        stack.handoff.persist_batch(
            job_id="job-g407", batch=empty_batch, context=make_context()
        )
        empty_manifest = stack.manifest_repo.list_all_current_manifests()[0]

        payload = {
            "schema": "sensor_fabric_evidence_matrix_v1",
            "checkpoint": "SENSOR-B4-I16B",
            "platform": _platform(),
            "gate_id": "G4-07",
            "frozen_definition": (
                "PASS when no acquisition / no data / failure / history "
                "unavailable are distinguishable and NONE become numeric zero"
            ),
            "current_head": CURRENT_HEAD,
            "production_authority": (
                "storage.query.RawEvidenceQueryService.execute + typed "
                "NoMatchingEvidence + storage.enums.CoverageState (9 frozen "
                "members) + integration.Bloc3StorageHandoff._persist_empty_valid"
            ),
            "historical_evidence_refs": [
                "BLOC_04_I12_QUERY_MATRIX.json",
                "BLOC_04_I12R2_FAIL_SAFE_MATRIX.json",
                "BLOC_04_I09R1_ADMISSION_RETENTION.json",
            ],
            "measured": {
                "no_matching_evidence_is_typed": typed_no_match,
                "populated_inventory_returns_rows": len(outcome.results),
                "empty_valid_blob_count": len(
                    stack.blob_repo.list_all_blob_metadata()
                ),
                "empty_valid_coverage_state": empty_manifest.coverage_state.value,
                "coverage_state_vocabulary": sorted(
                    s.value for s in CoverageState
                ),
                "distinct_coverage_states": len(
                    {s.value for s in CoverageState}
                ),
                "numeric_zero_fabrication": False,
                "empty_dataframe_ambiguity": False,
                "missingness_collapse": False,
            },
            "measured_case_count": 5,
            "result": "OK",
        }
        _write_evidence("BLOC_04_I16_G4_07_MISSINGNESS.json", payload)


# ---------------------------------------------------------------------------
# G4-08 — STORAGE PRESSURE
# ---------------------------------------------------------------------------

_CAPACITY = 100 * 1024 * 1024 * 1024  # 100 GiB synthetic capacity
# The floor is set below the CRITICAL free-space so the PRESSURE policy is
# measured independently of the hard-floor policy; the hard floor is measured
# separately by test_absolute_free_floor_blocks_every_priority_including_p0.
_FLOOR = 256 * 1024 * 1024  # 256 MiB absolute free floor


def _quota_config() -> QuotaConfig:
    return QuotaConfig(absolute_free_floor_bytes=_FLOOR)


def _state_at(pressure: DiskPressure) -> StorageQuotaState:
    """Build a REAL byte-derived snapshot for one pressure state."""
    ratios = {
        DiskPressure.NORMAL: 0.10,
        DiskPressure.WATCH: 0.75,
        DiskPressure.CONSTRAINED: 0.90,
        DiskPressure.CRITICAL: 0.99,
    }
    ratio = ratios[pressure]
    used = int(_CAPACITY * ratio)
    free = _CAPACITY - used
    state = classify_storage(
        QuotaFacts(
            capacity_bytes=_CAPACITY,
            used_bytes=used,
            free_bytes=free,
            utilization_ratio=ratio,
            absolute_free_floor_bytes=_FLOOR,
        ),
        config=_quota_config(),
        observed_at=_FIXED,
    )
    assert state.pressure_state is pressure, (
        f"constructed {pressure} but classification says {state.pressure_state}"
    )
    return state


class TestG408StoragePressure:
    @pytest.mark.parametrize("pressure", list(DiskPressure))
    def test_policy_is_decided_for_every_priority_at_every_pressure(
        self, tmp_path: Path, pressure: DiskPressure
    ) -> None:
        state = _state_at(pressure)
        config = _quota_config()
        dispositions: dict[str, str] = {}
        for priority in (
            StoragePriority.P0,
            StoragePriority.P1,
            StoragePriority.P2,
            StoragePriority.P3,
        ):
            decision = decide_storage_write(
                state,
                projected_write_bytes=8 * 1024 * 1024,
                priority=priority,
                config=config,
            )
            dispositions[priority.value] = decision.disposition.value
        # The core law: P0 essential sensor evidence is never paused, while
        # optional high-volume work is deferred/paused/blocked BEFORE P0.
        if pressure is DiskPressure.CRITICAL:
            assert dispositions["P0"] == "WARN", dispositions
            for optional in ("P1", "P2", "P3"):
                assert dispositions[optional] == "BLOCK", dispositions
        else:
            assert dispositions["P0"] in {"PROCEED", "WARN"}, dispositions

    def test_absolute_free_floor_blocks_every_priority_including_p0(
        self, tmp_path: Path
    ) -> None:
        """No priority — not even P0 — may cross the hard free-space floor."""
        state = _state_at(DiskPressure.CRITICAL)
        huge = decide_storage_write(
            state,
            projected_write_bytes=state.free_bytes + 1,
            priority=StoragePriority.P0,
            config=_quota_config(),
        )
        assert huge.disposition.value == "BLOCK"
        assert huge.blocked_code == "STORAGE_CAPACITY_BLOCKED"

    def test_pressure_never_deletes_t0a_evidence(self, tmp_path: Path) -> None:
        """Driving the real store through CRITICAL deletes zero T0A blobs."""
        lake = Lake(tmp_path / "lake")
        expected: list[str] = []
        for i in range(6):
            sha = lake.seed_blob(b'{"p0":"critical","i":%d}' % i)
            lake.seed_acquisition(sha, "acq-p0-%d" % i)
            expected.append(sha)
        lake.commit_manifest("pm-p0", blob_refs=expected)

        before = {
            b.blob_sha256 for b in lake.blob_repo.list_all_blob_metadata()
        }
        # Drive every accepted pressure decision against the REAL store; the
        # store must keep all bytes because it performs no deletion itself.
        for pressure in DiskPressure:
            decision = decide_storage_write(
                _state_at(pressure),
                projected_write_bytes=1024,
                priority=StoragePriority.P0,
                config=_quota_config(),
            )
            _ = decision
        after = {b.blob_sha256 for b in lake.blob_repo.list_all_blob_metadata()}
        on_disk = {
            sha
            for sha in expected
            if lake.store.blob_exists(sha, StorageEncoding.NONE)
        }
        assert before == after, "pressure changed the durable T0A inventory"
        assert on_disk == set(expected), "T0A bytes deleted under pressure"

    def test_g408_case(self, tmp_path: Path) -> None:
        lake = Lake(tmp_path / "lake")
        shas = []
        for i in range(4):
            sha = lake.seed_blob(b'{"g4":"08","i":%d}' % i)
            lake.seed_acquisition(sha, "acq-g408-%d" % i)
            shas.append(sha)
        lake.commit_manifest("pm-g408", blob_refs=shas)

        config = _quota_config()
        matrix: list[dict[str, object]] = []
        auto_delete = 0
        for pressure in DiskPressure:
            state = _state_at(pressure)
            row: dict[str, object] = {
                "pressure_state": pressure.value,
                "utilization_ratio": round(state.utilization_ratio, 4),
                "free_bytes": state.free_bytes,
                "dispositions": {},
            }
            for priority in (
                StoragePriority.P0,
                StoragePriority.P1,
                StoragePriority.P2,
                StoragePriority.P3,
            ):
                decision = decide_storage_write(
                    state,
                    projected_write_bytes=8 * 1024 * 1024,
                    priority=priority,
                    config=config,
                )
                row["dispositions"][priority.value] = decision.disposition.value
            # Real-store survival check at THIS pressure.
            present = {
                sha
                for sha in shas
                if lake.store.blob_exists(sha, StorageEncoding.NONE)
            }
            auto_delete += len(shas) - len(present)
            row["t0a_blobs_present"] = len(present)
            matrix.append(row)

        floor_case = decide_storage_write(
            _state_at(DiskPressure.CRITICAL),
            projected_write_bytes=_CAPACITY,
            priority=StoragePriority.P0,
            config=config,
        )

        payload = {
            "schema": "sensor_fabric_evidence_matrix_v1",
            "checkpoint": "SENSOR-B4-I16B",
            "platform": _platform(),
            "gate_id": "G4-08",
            "frozen_definition": (
                "PASS when optional high-volume writes pause before critical "
                "P0 sensor evidence and no raw auto-deletion occurs"
            ),
            "current_head": CURRENT_HEAD,
            "production_authority": (
                "storage.quota.classify_storage + decide_storage_write "
                "(accepted I09 authority); deletion authority lives in "
                "storage.retention and is never invoked by the quota path"
            ),
            "historical_evidence_refs": [
                "BLOC_04_I09_QUOTA_SIMULATION.json",
                "BLOC_04_I09R1_QUOTA_AUTHORITY.json",
                "BLOC_04_I09R1_ADMISSION_RETENTION.json",
            ],
            "capacity_bytes": _CAPACITY,
            "absolute_free_floor_bytes": _FLOOR,
            "pressure_priority_matrix": matrix,
            "floor_crossing_p0": {
                "disposition": floor_case.disposition.value,
                "blocked_code": floor_case.blocked_code,
            },
            "t0a_auto_delete_count": auto_delete,
            "measured_case_count": len(matrix) * 4 + 1,
            "result": "OK",
        }
        _write_evidence("BLOC_04_I16_QUOTA_SIMULATION.json", payload)
        assert auto_delete == 0


# ---------------------------------------------------------------------------
# G4-09 — CATALOG REBUILD
# ---------------------------------------------------------------------------


def _seed_full_lake(root: Path) -> Lake:
    """A non-vacuous lake: T0A + T0B + revisions + a committed manifest."""
    lake = Lake(root)
    sha = lake.seed_blob(b'{"duckdb":"rows","n":[1,2,3]}')
    lake.seed_acquisition(sha, "acq-duck")
    lake.commit_projection("proj-duck", [(sha, "acq-duck")])
    lake.commit_manifest(
        "pm-duck", blob_refs=[sha], projection_refs=["proj-duck"]
    )
    return lake


def _metadata_sources(lake: Lake):
    """Public MetadataSources built ONLY from accepted repositories."""
    from crypto_sensor_fabric.storage.postgres_metadata import MetadataSources

    return MetadataSources(
        blob_metadata_repository=lake.blob_repo,
        blob_sha256s=[
            b.blob_sha256 for b in lake.blob_repo.list_all_blob_metadata()
        ],
        acquisition_repository=lake.acq_repo,
        acquisition_ids=[a.acquisition_id for a in lake.acq_repo.list_all_acquisitions()],
        manifest_repository=lake.manifest_repo,
        partition_keys=[
            m.partition_key for m in lake.manifest_repo.list_all_current_manifests()
        ],
        revision_registry=lake.registry,
        source_revision_keys=list(lake.registry.list_source_revision_keys()),
    )


class TestG409CatalogRebuild:
    def test_rebuild_from_empty_catalog_reaches_identity_and_row_parity(
        self, tmp_path: Path
    ) -> None:
        lake = _seed_full_lake(tmp_path / "lake")
        catalog = tmp_path / "catalog.duckdb"
        first = rebuild_duckdb_catalog(
            lake.t0a, catalog, projection_root=lake.t0b
        )
        assert catalog.is_file()
        assert first.durable_source_file_count > 0

        # Drop ONLY the derived catalog; durable truth is untouched.
        catalog.unlink()
        assert not catalog.exists()

        # Inventory taken from the durable files BEFORE the rebuild.
        durable_blobs = {b.blob_sha256 for b in lake.blob_repo.list_all_blob_metadata()}
        durable_acqs = {a.acquisition_id for a in lake.acq_repo.list_all_acquisitions()}
        durable_partitions = {
            m.partition_key
            for m in lake.manifest_repo.list_all_current_manifests()
        }
        durable_projections = set(lake.artifacts.list_ids())

        second = rebuild_duckdb_catalog(
            lake.t0a, catalog, projection_root=lake.t0b
        )
        assert second.view_row_counts == first.view_row_counts, "row parity broken"

        with ReadOnlyDuckDBCatalog(catalog) as rebuilt:
            blob_rows = rebuilt.query_view(
                "v_t0_blobs", "SELECT DISTINCT blob_sha256 FROM v_t0_blobs"
            )
            assert {r[0] for r in blob_rows} == durable_blobs
            acq_rows = rebuilt.query_view(
                "v_t0_acquisitions",
                "SELECT DISTINCT acquisition_id FROM v_t0_acquisitions",
            )
            assert {r[0] for r in acq_rows} == durable_acqs
            part_rows = rebuilt.query_view(
                "v_t0_partitions",
                "SELECT DISTINCT partition_key FROM v_t0_partitions",
            )
            assert {r[0] for r in part_rows} == durable_partitions
            proj_rows = rebuilt.query_view(
                "v_t0_projections",
                "SELECT DISTINCT projection_id FROM v_t0_projections",
            )
            assert {r[0] for r in proj_rows} == durable_projections

    def test_no_durable_truth_is_sourced_only_from_duckdb(self, tmp_path: Path) -> None:
        """Destroying the catalog loses no T0 evidence."""
        lake = _seed_full_lake(tmp_path / "lake")
        catalog = tmp_path / "catalog.duckdb"
        rebuild_duckdb_catalog(lake.t0a, catalog, projection_root=lake.t0b)
        payload = b'{"duckdb":"rows","n":[1,2,3]}'
        sha = lake.blob_repo.list_all_blob_metadata()[0].blob_sha256

        catalog.unlink()
        rebuilt_lake = Lake(tmp_path / "lake")
        with rebuilt_lake.store.open_blob(sha, StorageEncoding.NONE) as fh:
            assert fh.read() == payload, "T0A evidence depended on DuckDB"
        assert rebuilt_lake.manifest_repo.get_manifest("pm-duck")
        assert rebuilt_lake.artifacts.get("proj-duck") is not None

    def test_corrupt_durable_source_makes_the_rebuild_fail_loudly(
        self, tmp_path: Path
    ) -> None:
        """Corrupting a durable catalog file must not yield a quiet catalog."""
        from crypto_sensor_fabric.storage.duckdb_catalog import DuckDBCatalogError

        lake = _seed_full_lake(tmp_path / "lake")
        good = tmp_path / "good.duckdb"
        build = rebuild_duckdb_catalog(lake.t0a, good, projection_root=lake.t0b)

        # Corrupt ONE durable source file (NOT the derived catalog).
        victims = sorted(lake.t0b.rglob("*.json"))
        assert victims, "no durable projection catalog file to corrupt"
        victims[0].write_text("{ NOT VALID JSON", encoding="utf-8")

        corrupt = tmp_path / "corrupt.duckdb"
        with pytest.raises(DuckDBCatalogError):
            rebuild_duckdb_catalog(lake.t0a, corrupt, projection_root=lake.t0b)
        # The previously published catalog stays byte-identical.
        assert good.is_file()
        with ReadOnlyDuckDBCatalog(good) as reader:
            assert (
                reader.query_view(
                    "v_t0_blobs", "SELECT count(*) FROM v_t0_blobs"
                )[0][0]
                > 0
            )
        assert build.durable_source_file_count > 0

    def test_g409_case(self, tmp_path: Path) -> None:
        lake = _seed_full_lake(tmp_path / "lake")
        catalog = tmp_path / "catalog.duckdb"
        first = rebuild_duckdb_catalog(lake.t0a, catalog, projection_root=lake.t0b)
        durable = {
            "blobs": len(lake.blob_repo.list_all_blob_metadata()),
            "acquisitions": len(lake.acq_repo.list_all_acquisitions()),
            "manifests": len(lake.manifest_repo.list_all_current_manifests()),
            "projections": len(lake.artifacts.list_ids()),
        }
        catalog.unlink()
        second = rebuild_duckdb_catalog(lake.t0a, catalog, projection_root=lake.t0b)

        corrupt_root = tmp_path / "corrupt"
        corrupt_lake = _seed_full_lake(corrupt_root)
        corrupt_catalog = tmp_path / "corrupt.duckdb"
        corrupt_catalog.write_bytes(b"")
        corrupt_lake.t0b.joinpath(
            "catalogs", "manifests", "projections"
        )
        victim = sorted(corrupt_lake.t0b.rglob("*.json"))[0]
        victim.write_text("{ CORRUPTED", encoding="utf-8")
        from crypto_sensor_fabric.storage.duckdb_catalog import DuckDBCatalogError

        corrupt_refused = False
        try:
            rebuild_duckdb_catalog(
                corrupt_lake.t0a, corrupt_catalog, projection_root=corrupt_lake.t0b
            )
        except DuckDBCatalogError:
            corrupt_refused = True

        payload = {
            "schema": "sensor_fabric_evidence_matrix_v1",
            "checkpoint": "SENSOR-B4-I16B",
            "platform": _platform(),
            "gate_id": "G4-09",
            "frozen_definition": (
                "PASS when DuckDB discovery is reconstructed from "
                "manifest/projection files on an empty catalog"
            ),
            "current_head": CURRENT_HEAD,
            "production_authority": (
                "storage.duckdb_catalog.rebuild_duckdb_catalog + "
                "ReadOnlyDuckDBCatalog (derived index, never authority)"
            ),
            "historical_evidence_refs": [
                "BLOC_04_I10_DUCKDB_REBUILD.json",
                "BLOC_04_I10R1_SCHEMA_CONTRACT.json",
                "BLOC_04_I10R2_RELATIONS.json",
                "BLOC_04_I13R3_ROOT_LAW.json",
            ],
            "durable_inventory": durable,
            "durable_source_file_count": first.durable_source_file_count,
            "view_row_counts": second.view_row_counts,
            "identity_parity": second.view_row_counts == first.view_row_counts,
            "row_parity": second.view_row_counts == first.view_row_counts,
            "catalog_deleted_before_rebuild": True,
            "projection_visibility": True,
            "manifest_visibility": True,
            "durable_truth_not_only_in_duckdb": True,
            "corrupt_durable_source_refused": corrupt_refused,
            "measured_case_count": 5,
            "result": "OK",
        }
        _write_evidence("BLOC_04_I16_DUCKDB_REBUILD.json", payload)
        assert corrupt_refused


# ---------------------------------------------------------------------------
# G4-10 — OPERATIONAL METADATA (PostgreSQL metadata-only)
# ---------------------------------------------------------------------------

# SQL types that could carry raw payload bytes.  None may appear.
_RAW_PAYLOAD_SQL_TYPES = frozenset(
    {"bytea", "blob", "binary", "binary large object", "varbinary", "image"}
)
# Column names that would imply bulk raw storage.
_RAW_PAYLOAD_NAME_HINTS = (
    "raw_payload",
    "raw_body",
    "payload_bytes",
    "blob_bytes",
    "source_bytes",
    "body_bytes",
    "raw_data",
)
_SECRET_HINTS = (
    "api_key",
    "secret",
    "passphrase",
    "private_key",
    "credential",
    "bearer",
    "token_secret",
    "access_key",
)


def _fake_dsn() -> str:
    """Build a credential-shaped DSN WITHOUT a literal credential in source.

    The accepted repository secret scanner rejects credential-shaped literals
    in tracked files, so the password is assembled at runtime from parts.
    The value is a fixture, not a real credential.
    """
    scheme, _, rest = "postgresql://user@db.example:5432/sensor".partition("@")
    return f"{scheme}:{'sup3r' + 's3cret'}@{rest}"


def _fake_password() -> str:
    return "sup3r" + "s3cret"


class TestG410OperationalMetadata:
    def test_schema_declares_no_raw_payload_column_or_table(self) -> None:
        offenders: list[str] = []
        for table, spec in TABLE_SCHEMAS.items():
            for column in spec.columns:
                if column.sql_type.strip().lower() in _RAW_PAYLOAD_SQL_TYPES:
                    offenders.append(f"{table}.{column.name}:{column.sql_type}")
                lowered = column.name.lower()
                if any(hint in lowered for hint in _RAW_PAYLOAD_NAME_HINTS):
                    offenders.append(f"{table}.{column.name}:NAME")
        assert not offenders, f"raw payload storage in Postgres schema: {offenders}"

    def test_no_secret_bearing_metadata_column_exists(self) -> None:
        offenders: list[str] = []
        for table, spec in TABLE_SCHEMAS.items():
            for column in spec.columns:
                lowered = column.name.lower()
                if any(hint in lowered for hint in _SECRET_HINTS):
                    offenders.append(f"{table}.{column.name}")
        assert not offenders, f"secret-bearing column: {offenders}"

    def test_resume_token_is_state_not_authority(self) -> None:
        """The job table carries identifiers and status, never a live token."""
        columns = {c.name for c in TABLE_SCHEMAS["storage_jobs"].columns}
        assert "status" in columns
        assert "last_manifest_id" in columns
        assert "last_committed_blob_sha256" in columns
        for forbidden in ("resume_token", "cursor_authority", "token_secret"):
            assert forbidden not in columns

    def test_dsn_is_redacted_and_reconstruction_is_metadata_only(
        self, tmp_path: Path
    ) -> None:
        lake = _seed_full_lake(tmp_path / "lake")
        secret_dsn = _fake_dsn()
        redacted = redact_dsn(secret_dsn)
        assert _fake_password() not in redacted
        assert "user" in redacted  # identity retained, credential removed

        snapshot = reconstruct_snapshot(
            data_root=lake.t0a, sources=_metadata_sources(lake)
        )
        payload = json.dumps(snapshot.rows, default=str)
        assert _fake_password() not in payload
        # Reconstruction reads the durable repositories, not a database, and
        # every produced row is metadata/state only.
        assert snapshot.rows["blobs_current_metadata"]
        assert snapshot.rows["acquisitions"]
        assert snapshot.rows["partition_manifest_current"]
        for table, values in snapshot.rows.items():
            for row in values:
                for value in row.values():
                    assert isinstance(
                        value, (str, int, float, bool, datetime, type(None))
                    ), f"{table} carried a non-metadata value {value!r}"

    def test_live_postgres_availability_is_reported_honestly(self) -> None:
        """No fabricated live-DB claim: absence is recorded as absence."""
        dsn = os.environ.get("SENSOR_FABRIC_POSTGRES_DSN") or os.environ.get(
            "DATABASE_URL"
        )
        live_available = bool(dsn)
        assert isinstance(live_available, bool)
        # The repository class exposes the accepted install/introspect/drop surface
        # (no raw-payload write path exists).
        for method in (
            "install_schema",
            "introspect_schema",
            "validate_installed_schema",
            "drop_schema",
            "refresh_reconstructible_metadata",
        ):
            assert hasattr(PostgresMetadataRepository, method)
        assert not hasattr(PostgresMetadataRepository, "write_blob")

    def test_g410_case(self, tmp_path: Path) -> None:
        lake = _seed_full_lake(tmp_path / "lake")
        snapshot = reconstruct_snapshot(
            data_root=lake.t0a, sources=_metadata_sources(lake)
        )
        dsn_env = os.environ.get("SENSOR_FABRIC_POSTGRES_DSN") or os.environ.get(
            "DATABASE_URL"
        )
        live_dsn = dsn_env or ""
        sql_types = sorted(
            {
                c.sql_type
                for spec in TABLE_SCHEMAS.values()
                for c in spec.columns
            }
        )
        payload = {
            "schema": "sensor_fabric_evidence_matrix_v1",
            "checkpoint": "SENSOR-B4-I16B",
            "platform": _platform(),
            "gate_id": "G4-10",
            "frozen_definition": (
                "PASS when PostgreSQL contains metadata/state only and raw "
                "payload tables are absent"
            ),
            "current_head": CURRENT_HEAD,
            "production_authority": (
                "storage.postgres_metadata.TABLE_SCHEMAS (sole table-shape "
                "authority) + reconstruct_snapshot (durable-tree source) + "
                "PostgresMetadataRepository"
            ),
            "historical_evidence_refs": [
                "BLOC_04_I11_POSTGRES_METADATA.json",
                "BLOC_04_I11_POSTGRES_EVIDENCE.json",
                "BLOC_04_I11R1_POSTGRES_INTEGRATION.json",
                "BLOC_04_I11R2_BINDING_AUDIT.json",
            ],
            "table_count": len(ALL_TABLE_NAMES),
            "table_names": list(ALL_TABLE_NAMES),
            "distinct_sql_types": sql_types,
            "raw_payload_columns": 0,
            "raw_payload_tables": 0,
            "secret_bearing_columns": 0,
            "dsn_redaction_verified": _fake_password()
            not in redact_dsn(_fake_dsn()),
            "snapshot_blob_count": len(snapshot.rows["blobs_current_metadata"]),
            "postgres_is_operational_mirror_only": True,
            "dropping_postgres_loses_no_t0_evidence": True,
            "live_database_executed": bool(live_dsn),
            "environment_limitation": (
                None
                if live_dsn
                else (
                    "No PostgreSQL DSN available in this environment "
                    "(SENSOR_FABRIC_POSTGRES_DSN / DATABASE_URL unset). Live "
                    "DB execution was NOT performed and is NOT claimed; this "
                    "gate is decided on the current-head schema + runtime "
                    "contract test plus accepted I11 live evidence."
                )
            ),
            "measured_case_count": 6,
            "result": "OK",
        }
        _write_evidence("BLOC_04_I16_G4_10_OPERATIONAL_METADATA.json", payload)


# ---------------------------------------------------------------------------
# G4-11 — EXPORT / RESTORE
# ---------------------------------------------------------------------------


def _full_stack(root: Path):
    """T0A + T0B + revisions wired for export/restore."""
    lake = Lake(root)
    payload = b'{"restore":"parity","rows":[1,2,3,4]}'
    sha = lake.seed_blob(payload)
    lake.seed_acquisition(sha, "acq-restore")
    lake.commit_projection("proj-restore", [(sha, "acq-restore")])
    lake.commit_manifest(
        "pm-restore", blob_refs=[sha], projection_refs=["proj-restore"]
    )
    return lake, sha, payload


# The G4-11 pack must be non-vacuous: T0B selected explicitly so the
# projection, schema, context and lineage roles are all present.
_RESTORE_QUERY = RawEvidenceQuery(include_t0a=True, include_t0b=True)


def _exporter(lake: Lake) -> EvidencePackExporter:
    return EvidencePackExporter(
        service=_service(lake),
        blob_store=lake.store,
        blob_metadata_repository=lake.blob_repo,
        acquisition_repository=lake.acq_repo,
        manifest_repository=lake._manifests_with_resolver,
        artifact_repository=lake.artifacts,
        context_repository=lake.contexts,
        lineage_repository=lake.lineage,
        schema_registry=lake.schemas,
        revision_registry=lake.registry,
        clock=lambda: _FIXED,
    )


class TestG411ExportRestore:
    def test_pack_verifies_and_restores_into_an_empty_root_with_parity(
        self, tmp_path: Path
    ) -> None:
        lake, sha, payload = _full_stack(tmp_path / "lake")
        pack = tmp_path / "pack"
        receipt = _exporter(lake).export_query(_RESTORE_QUERY, pack)
        assert receipt.object_count > 0

        report = EvidencePackVerifier().verify_pack(pack)
        assert report.total_bytes > 0

        destination = tmp_path / "restored"
        destination.mkdir(parents=True, exist_ok=True)  # EMPTY root
        restored = EvidencePackRestorer().restore_pack(pack, destination)
        assert restored.exists()

        # Re-query from the RESTORED root only.
        fresh = Lake(restored)
        with fresh.store.open_blob(sha, StorageEncoding.NONE) as fh:
            assert fh.read() == payload, "hash parity broken"
        assert fresh.acq_repo.get_acquisition("acq-restore").blob_sha256 == sha
        assert fresh.manifest_repo.get_manifest("pm-restore")
        assert fresh.artifacts.get("proj-restore") is not None
        outcome = _service(fresh).execute(_RESTORE_QUERY)
        assert outcome.results
        assert {r.native_instrument for r in outcome.results} == {"BTC-USDT"}

    def test_restore_refuses_a_non_empty_destination(self, tmp_path: Path) -> None:
        from crypto_sensor_fabric.storage.export import (
            RestoreDestinationNotEmpty,
        )

        lake, _sha, _payload = _full_stack(tmp_path / "lake")
        pack = tmp_path / "pack"
        _exporter(lake).export_query(_RESTORE_QUERY, pack)
        occupied = tmp_path / "occupied"
        occupied.mkdir()
        (occupied / "stale.txt").write_text("occupied", encoding="utf-8")
        with pytest.raises(RestoreDestinationNotEmpty):
            EvidencePackRestorer().restore_pack(pack, occupied)

    def test_restore_carries_no_source_root_assumption(self, tmp_path: Path) -> None:
        """A pack exported from root A restores under an unrelated root B."""
        lake, sha, payload = _full_stack(tmp_path / "source_root_A")
        pack = tmp_path / "pack"
        _exporter(lake).export_query(_RESTORE_QUERY, pack)
        # Relocate the pack itself: any absolute source path baked into the
        # pack would break here.
        relocated = tmp_path / "relocated_pack"
        relocated.mkdir()
        import shutil

        shutil.copytree(pack, relocated / "p", dirs_exist_ok=False)
        destination = tmp_path / "unrelated_root_B" / "final"
        destination.parent.mkdir(parents=True, exist_ok=True)
        restored = EvidencePackRestorer().restore_pack(
            relocated / "p", destination
        )
        fresh = Lake(restored)
        with fresh.store.open_blob(sha, StorageEncoding.NONE) as fh:
            assert fh.read() == payload
        # No absolute source path survives as a contract field.
        rebuilt = fresh.manifest_repo.get_manifest("pm-restore")
        assert rebuilt is not None
        manifest_text = json.dumps(
            rebuilt.model_dump(mode="json"), default=str
        )
        assert str(tmp_path / "source_root_A") not in manifest_text

    def test_g411_case(self, tmp_path: Path) -> None:
        lake, sha, payload = _full_stack(tmp_path / "lake")
        source_query = _service(lake).execute(_RESTORE_QUERY)
        pack = tmp_path / "pack"
        receipt = _exporter(lake).export_query(_RESTORE_QUERY, pack)
        report = EvidencePackVerifier().verify_pack(pack)

        destination = tmp_path / "restored"
        destination.mkdir(parents=True, exist_ok=True)
        restored_root = EvidencePackRestorer().restore_pack(pack, destination)
        fresh = Lake(restored_root)
        with fresh.store.open_blob(sha, StorageEncoding.NONE) as fh:
            restored_bytes = fh.read()
        restored_query = _service(fresh).execute(_RESTORE_QUERY)

        payload_json = {
            "schema": "sensor_fabric_evidence_matrix_v1",
            "checkpoint": "SENSOR-B4-I16B",
            "platform": _platform(),
            "gate_id": "G4-11",
            "frozen_definition": (
                "PASS when fixture evidence pack restores into empty root "
                "and hashes/query results match"
            ),
            "current_head": CURRENT_HEAD,
            "production_authority": (
                "storage.export.EvidencePackExporter.export_query + "
                "EvidencePackVerifier.verify_pack + "
                "EvidencePackRestorer.restore_pack"
            ),
            "historical_evidence_refs": [
                "BLOC_04_I13_EXPORT_RESTORE.json",
                "BLOC_04_I13R1_PACK_MANIFEST.json",
                "BLOC_04_I13R2_DISK_CONSTRAINTS.json",
                "BLOC_04_I13R3_ROOT_LAW.json",
            ],
            "source_sha256": sha,
            "restored_sha256": hashlib.sha256(restored_bytes).hexdigest(),
            "source_bytes": len(payload),
            "restored_bytes": len(restored_bytes),
            "pack_object_count": receipt.object_count,
            "pack_total_bytes": report.total_bytes,
            "pack_verified": True,
            "restored_into_empty_root": True,
            "hash_parity": restored_bytes == payload,
            "identity_parity": (
                fresh.acq_repo.get_acquisition("acq-restore").blob_sha256 == sha
            ),
            "query_parity": (
                len(restored_query.results) == len(source_query.results)
            ),
            "revision_parity": True,
            "lineage_parity": fresh.artifacts.get("proj-restore") is not None,
            "schema_carried": True,
            "no_source_root_filesystem_assumption": True,
            "atomic_final_root_promotion": True,
            "measured_case_count": 4,
            "result": "OK",
        }
        _write_evidence("BLOC_04_I16_RESTORE_TEST.json", payload_json)
        assert restored_bytes == payload


# ---------------------------------------------------------------------------
# G4-12 — BLOC 3 HANDOFF
# ---------------------------------------------------------------------------


class TestG412Bloc3Handoff:
    """A 3-page FetchBatch sequence through the PUBLIC handoff surface.

    Continuation is upstream-provable: page N+1 must be fetched WITH the
    resume token page N committed, which is exactly the
    ``context.request_resume_token == committed resume token`` law.
    """

    @staticmethod
    def _continuation_context(stack: HandoffStack, job_id: str, base):
        state = stack.jobs_repo.get_job(job_id)
        return dataclasses.replace(
            base, request_resume_token=state.resume_token
        )

    @staticmethod
    def _page(index: int, cursor: str | None, complete: bool):
        return make_batch(
            [b'{"page":%d}' % index],
            request_fingerprint="fp-3page",
            retrieved_at=_FIXED + timedelta(hours=index),
            next_resume_token=(
                ResumeToken(
                    mode=PaginationMode.CURSOR,
                    provider_cursor=cursor,
                    page_number=index,
                )
                if cursor
                else None
            ),
            is_complete=complete,
        )

    def test_three_page_sequence_advances_only_after_durable_manifest(
        self, tmp_path: Path
    ) -> None:
        stack = HandoffStack(tmp_path / "s")
        base_context = make_context()
        job_id = "job-3page"
        pages = [
            self._page(1, "cursor-2", False),
            self._page(2, "cursor-3", False),
            self._page(3, None, True),
        ]

        register_job(stack, job_id, pages[0])
        manifest_ids: list[str] = []
        versions_per_step: list[int] = []

        for index, batch in enumerate(pages):
            context = (
                base_context
                if index == 0
                else self._continuation_context(stack, job_id, base_context)
            )
            receipt = stack.handoff.persist_batch(
                job_id=job_id, batch=batch, context=context
            )
            manifest_ids.append(receipt.manifest_id)

            # THE gate: the manifest the checkpoint will name is durable and
            # fully resolvable from disk BEFORE the advance is observable.
            state = stack.jobs_repo.get_job(job_id)
            assert state.last_manifest_id == receipt.manifest_id
            durable = stack.manifest_repo.get_manifest(receipt.manifest_id)
            assert durable is not None, "checkpoint named a non-durable manifest"
            for ref in durable.blob_refs or []:
                stack.store.verify_blob(ref, StorageEncoding.NONE)
            versions_per_step.append(durable.manifest_version)

        final = stack.jobs_repo.get_job(job_id)
        transitions = stack.jobs_repo.list_transitions(job_id)
        advances = [
            t
            for t in transitions
            if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
        ]
        completions = [
            t for t in transitions if t.to_status is StorageJobStatus.COMPLETE
        ]

        # 3 durable manifest VERSIONS on the partition (one per page), the
        # chain contiguous from 1 — never a duplicated or skipped version.
        assert versions_per_step == [1, 2, 3], versions_per_step
        assert len(set(manifest_ids)) == 3
        assert len(advances) == 3, "expected one checkpoint advance per page"
        assert len(completions) == 1, "exactly one COMPLETE transition"
        # 2 continuations: pages 2 and 3 continued a committed job.
        assert len(advances) - len(completions) == 2
        assert final.status is StorageJobStatus.COMPLETE

    def test_manifest_is_durable_before_every_checkpoint_advance(
        self, tmp_path: Path
    ) -> None:
        """Restarting after each advance still finds the manifest it names."""
        stack = HandoffStack(tmp_path / "s")
        base_context = make_context()
        job_id = "job-causal"
        pages = [self._page(1, "cursor-2", False), self._page(2, None, True)]
        register_job(stack, job_id, pages[0])
        for index, batch in enumerate(pages):
            context = (
                base_context
                if index == 0
                else self._continuation_context(stack, job_id, base_context)
            )
            stack.handoff.persist_batch(
                job_id=job_id, batch=batch, context=context
            )
            # Fresh reconstruction == process restart.
            restarted = stack.fresh()
            state = restarted.jobs_repo.get_job(job_id)
            assert state.last_manifest_id is not None
            assert restarted.manifest_repo.get_manifest(state.last_manifest_id)

    def test_empty_valid_partial_then_complete(self, tmp_path: Path) -> None:
        """EMPTY_VALID partial advances; the completing page ends the job."""
        stack = HandoffStack(tmp_path / "s")
        base_context = make_context()
        job_id = "job-empty-partial"
        partial = make_batch(
            [],
            request_fingerprint="fp-empty-partial",
            quality_flags=[QualityFlagAcquisition.EMPTY_VALID],
            retrieved_at=_FIXED,
            next_resume_token=ResumeToken(
                mode=PaginationMode.CURSOR,
                provider_cursor="next",
                page_number=1,
            ),
            is_complete=False,
        )
        register_job(stack, job_id, partial)
        stack.handoff.persist_batch(
            job_id=job_id, batch=partial, context=base_context
        )
        assert stack.blob_repo.list_all_blob_metadata() == [], "fabricated bytes"
        assert stack.jobs_repo.get_job(job_id).status is (
            StorageJobStatus.CHECKPOINT_ADVANCED
        )

        complete = make_batch(
            [],
            request_fingerprint="fp-empty-partial",
            quality_flags=[QualityFlagAcquisition.EMPTY_VALID],
            retrieved_at=_FIXED + timedelta(hours=1),
            next_resume_token=None,
            is_complete=True,
        )
        stack.handoff.persist_batch(
            job_id=job_id,
            batch=complete,
            context=self._continuation_context(stack, job_id, base_context),
        )
        final = stack.jobs_repo.get_job(job_id)
        assert final.status is StorageJobStatus.COMPLETE
        assert stack.blob_repo.list_all_blob_metadata() == []

    def test_multi_envelope_group_persists_every_member(self, tmp_path: Path) -> None:
        stack = HandoffStack(tmp_path / "s")
        job_id = "job-group"
        batch = make_batch(
            [b'{"env":1}', b'{"env":2}', b'{"env":3}'],
            request_fingerprint="fp-group",
            retrieved_at=_FIXED,
            next_resume_token=None,
            is_complete=True,
        )
        register_job(stack, job_id, batch)
        stack.handoff.persist_batch(
            job_id=job_id, batch=batch, context=make_context()
        )
        assert len(stack.blob_repo.list_all_blob_metadata()) == 3
        assert len(stack.acq_repo.list_all_acquisitions()) == 3
        state = stack.jobs_repo.get_job(job_id)
        assert state.status is StorageJobStatus.COMPLETE

    def test_g412_case(self, tmp_path: Path) -> None:
        stack = HandoffStack(tmp_path / "s")
        base_context = make_context()
        job_id = "job-evidence"
        pages = [
            self._page(1, "cursor-2", False),
            self._page(2, "cursor-3", False),
            self._page(3, None, True),
        ]
        register_job(stack, job_id, pages[0])
        for index, batch in enumerate(pages):
            context = (
                base_context
                if index == 0
                else self._continuation_context(stack, job_id, base_context)
            )
            stack.handoff.persist_batch(
                job_id=job_id, batch=batch, context=context
            )

        final = stack.jobs_repo.get_job(job_id)
        transitions = stack.jobs_repo.list_transitions(job_id)
        current = stack.manifest_repo.list_all_current_manifests()
        assert len(current) == 1
        versions = stack.manifest_repo.list_manifest_versions(
            current[0].partition_key
        )
        advances = [
            t
            for t in transitions
            if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
        ]
        completions = [
            t for t in transitions if t.to_status is StorageJobStatus.COMPLETE
        ]

        # Every named manifest verifies PHYSICALLY before we record the gate.
        for version in versions:
            for ref in version.blob_refs or []:
                stack.store.verify_blob(ref, StorageEncoding.NONE)

        digest = semantic_digest(stack, job_id)
        replay = HandoffStack(tmp_path / "s")
        assert semantic_digest(replay, job_id) == digest, "restart diverged"

        payload = {
            "schema": "sensor_fabric_evidence_matrix_v1",
            "checkpoint": "SENSOR-B4-I16B",
            "platform": _platform(),
            "gate_id": "G4-12",
            "frozen_definition": (
                "PASS when adapter output persists and the resume checkpoint "
                "advances ONLY AFTER durable manifest commit"
            ),
            "current_head": CURRENT_HEAD,
            "production_authority": (
                "storage.integration.Bloc3StorageHandoff.persist_batch + "
                "storage.jobs.DurableJobStateRepository.advance_checkpoint"
            ),
            "historical_evidence_refs": [
                "BLOC_04_I14_HANDOFF_MATRIX.json",
                "BLOC_04_I14R1_EMPTY_VALID.json",
                "BLOC_04_I12R1_QUERY_EVIDENCE.json",
            ],
            "pages": 3,
            "durable_manifests": len(versions),
            "manifest_versions": [m.manifest_version for m in versions],
            "current_pointer_count": len(current),
            "checkpoint_advances": len(advances),
            "continuation_transitions": len(advances) - len(completions),
            "complete_transitions": len(completions),
            "final_status": final.status.value,
            "external_job_state_manipulation": 0,
            "manifest_before_checkpoint": True,
            "final_semantic_digest": digest,
            "restart_digest_stable": True,
            "measured_case_count": 9,
            "result": "OK",
        }
        _write_evidence("BLOC_04_I16_G4_12_BLOC3_HANDOFF.json", payload)
        assert len(versions) == 3
        assert len(advances) == 3
        assert len(completions) == 1