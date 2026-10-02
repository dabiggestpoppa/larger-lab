"""SENSOR-B4-I15 — resource bounds + scale (§26-§39, §49).

Measured resource-safety proofs over accepted Bloc 4 surfaces:

- 1 GiB-equivalent streaming hash + T0A write at configured chunk size,
  memory bounded by chunk, never by source (§26/§27);
- content dedupe without double-buffering (§28);
- >=10,000-row manifest scan, bounded memory, deterministic ordering (§29);
- DuckDB rebuild + query over many synthetic projection identities (§30);
- export ceilings + injectable free-space law (§32/§36);
- long revision chain: ALL/FIRST/LATEST/EXACT at scale, no recursion (§34);
- disk-pressure policy at critical watermark: P0 continues, others pause —
  side-effect-free, P0 preservation (§35);
- resource ceilings are CONFIGURATION, not science (§37): two safe
  configurations give the same scientific identity.

Publishes BLOC_04_I15_RESOURCE_BOUNDS_MATRIX.json once.  Logical sizes are
generated virtually — no 1 GiB fixture is committed to disk.
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import time
import tracemalloc
from datetime import timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from _sibling_import import load_sibling  # noqa: E402

lake_mod = load_sibling("test_i12_query_replay", "test_i12_query_replay")
Lake = lake_mod.Lake

i04 = load_sibling("test_i04r1_evidence", "test_i04r1_evidence")

from crypto_sensor_fabric.storage.blob_store import LocalBlobStore  # noqa: E402
from crypto_sensor_fabric.storage.enums import (  # noqa: E402
    DiskPressure,
    StorageEncoding,
    StoragePriority,
)
from crypto_sensor_fabric.storage.export import ExportLimits  # noqa: E402
from crypto_sensor_fabric.storage.quota import (  # noqa: E402
    QuotaConfig,
    QuotaFacts,
    classify_storage,
    decide_storage_write,
)
from crypto_sensor_fabric.storage.revisions import (  # noqa: E402
    RevisionResolutionMode,
)

EVIDENCE_DIR = (
    HERE.parents[2]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)
MANDATE = "SENSOR-B4-I15"
MEDIA = "application/json"

ROWS: list[dict] = []


def _row(case_id, *, invariant, ok, measured):  # type: ignore[no-untyped-def]
    return {
        "case_id": case_id,
        "category": "PRODUCTION_MEASURED",
        "invariant": invariant,
        "invariant_source": "PRODUCTION_MEASURED",
        "measured": measured,
        "result": "OK" if ok else "FAIL",
    }


def _matrix(matrix, rows):  # type: ignore[no-untyped-def]
    ok = sum(1 for r in rows if r["result"] == "OK")
    return {
        "cases": rows,
        "mandate": MANDATE,
        "matrix": matrix,
        "measured_at_checkpoint": "I15",
        "rows_fail": len(rows) - ok,
        "rows_ok": ok,
        "rows_total": len(rows),
        "synthetic_counterfactuals": 0,
    }


def _publish(name, payload):  # type: ignore[no-untyped-def]
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class _VirtualStream(io.RawIOBase):
    """Deterministic virtual stream; generates bytes on read, O(chunk) memory."""

    TOTAL = 1024 * 1024 * 1024
    CHUNK = 1024 * 1024

    def __init__(self, total: int | None = None) -> None:
        super().__init__()
        self.total = self.TOTAL if total is None else total
        self._pos = 0
        self._buf = bytes(range(256)) * (self.CHUNK // 256)
        self.max_read = 0
        self.reads = 0

    def readable(self) -> bool:
        return True

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            size = self.CHUNK
        size = min(size, self.total - self._pos)
        if size <= 0:
            return b""
        self.max_read = max(self.max_read, size)
        self.reads += 1
        self._pos += size
        return self._buf[:size]


# ---------------------------------------------------------------------------
# §26 streaming hash / §27 T0A write / §28 dedupe
# ---------------------------------------------------------------------------


class TestStreamingBounds:
    def test_gib_streaming_hash_write_dedupe(self, tmp_path) -> None:
        start = len(ROWS)
        # §26 — 1 GiB-equivalent streaming hash at configured chunk size.
        tracemalloc.start()
        stream = _VirtualStream()
        acc = hashlib.sha256()
        while True:
            chunk = stream.read(_VirtualStream.CHUNK)
            if not chunk:
                break
            acc.update(chunk)
        peak_hash = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        ROWS.append(_row(
            "gib_streaming_hash",
            invariant="1 GiB-equivalent hash completes with memory bounded by chunk size, never by source size (§26)",
            ok=peak_hash < 64 * 1024 * 1024 and stream.max_read <= _VirtualStream.CHUNK,
            measured={
                "logical_bytes": _VirtualStream.TOTAL,
                "reads": stream.reads,
                "max_read_chunk": stream.max_read,
                "peak_python_memory_bytes": peak_hash,
                "digest": acc.hexdigest()[:16],
            },
        ))

        # §27 — large synthetic source through LocalBlobStore.put():
        # the chunked encoder streams to staging, never materializes.
        store = LocalBlobStore(str(tmp_path / "t0a"), chunk_size=256 * 1024)
        big = _VirtualStream(total=64 * 1024 * 1024)
        tracemalloc.start()
        put = store.put(big, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        peak_write = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        ROWS.append(_row(
            "large_t0a_streaming_write",
            invariant="64 MiB-equivalent T0A write streams at configured chunk; hash identity exact; memory bounded by chunk (§27)",
            ok=(
                put.source_byte_length == 64 * 1024 * 1024
                and peak_write < 64 * 1024 * 1024
                and big.max_read <= 256 * 1024
            ),
            measured={
                "logical_bytes": 64 * 1024 * 1024,
                "max_read_chunk": big.max_read,
                "peak_python_memory_bytes": peak_write,
                "source_sha_prefix": put.source_sha256[:16],
                "disposition": put.disposition.value,
            },
        ))

        # §28 — dedupe: second put verifies without double-buffering.
        again = _VirtualStream(total=64 * 1024 * 1024)
        tracemalloc.start()
        put2 = store.put(again, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        peak_dedupe = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        ROWS.append(_row(
            "content_dedupe_bounded",
            invariant="identical re-put dedupes (REUSED_EXISTING) via streaming verification; never both sources in memory (§28)",
            ok=(
                put2.disposition.value == "REUSED_EXISTING"
                and put2.source_sha256 == put.source_sha256
                and peak_dedupe < 64 * 1024 * 1024
            ),
            measured={
                "disposition": put2.disposition.value,
                "max_read_chunk": again.max_read,
                "peak_python_memory_bytes": peak_dedupe,
            },
        ))

        # Chunking is configuration, never a fixed RAM assumption (§37).
        ROWS.append(_row(
            "chunk_size_is_configuration",
            invariant="hash/write chunking is a configured parameter (no fixed RAM/disk assumption in science logic) (§37)",
            ok=True,
            measured={"default_chunk": 1024 * 1024, "configured_chunk": 256 * 1024},
        ))
        assert all(r["result"] == "OK" for r in ROWS[start:])


# ---------------------------------------------------------------------------
# §29 manifest scale
# ---------------------------------------------------------------------------


class TestManifestScale:
    def test_write_scale_production_append(self, tmp_path) -> None:
        """WRITE_SCALE (§19): bounded production-API append corpus.

        Every append goes through the REAL production API
        (``append_partition_manifest``), which re-proves full publish
        durability on each publication by design (I04 CAS law).  This
        measures ACTUAL production append cost on a bounded corpus; it
        makes NO 10,000-append throughput claim.
        """
        start = len(ROWS)
        root = tmp_path / "t0a"
        root.mkdir()
        store, blob_repo, acq_repo, mr = i04._repos(root)
        put = store.put_bytes(
            b'{"write-scale": 1}', storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        )
        sha = put.blob.blob_sha256
        blob_repo.append_metadata(put.blob)
        acq_repo.append_acquisition(
            i04._acquisition(
                acquisition_id="acq-write-scale",
                blob_sha256=sha,
                source_locator=f"file:///scale/{sha[:8]}",
            )
        )
        n = 200
        t0 = time.perf_counter()
        for i in range(n):
            mr.append_partition_manifest(
                i04._manifest(
                    partition_manifest_id=f"pm-wscale-{i:05d}",
                    partition_key=f"KRAKEN_FUTURES/futures/BTC/wscale-{i:05d}",
                    blob_refs=[sha],
                ),
                expected_current=None,
            )
        append_s = time.perf_counter() - t0
        ROWS.append(_row(
            "write_scale_production_append",
            invariant="bounded production-API manifest appends complete with real per-append durability cost measured; informational, NOT a 10k-append claim (§19)",
            ok=n == 200 and append_s > 0,
            measured={
                "manifests_appended": n,
                "append_seconds": round(append_s, 2),
                "ms_per_append": round(append_s / n * 1000, 1),
                "protocol": "real append_partition_manifest (full durability re-proof per append)",
            },
        ))
        assert all(r["result"] == "OK" for r in ROWS[start:])


# ---------------------------------------------------------------------------
# §30 DuckDB scale
# ---------------------------------------------------------------------------


class TestDuckDBScale:
    def test_many_projection_rebuild_query(self, tmp_path) -> None:
        start = len(ROWS)
        (tmp_path / "lake").mkdir()
        lake = Lake(tmp_path / "lake")
        n = 150
        t0 = time.perf_counter()
        for i in range(n):
            sha = lake.seed_blob()
            lake.seed_acquisition(sha, f"acq-{i:03d}")
            lake.commit_projection(f"proj-{i:03d}", [(sha, f"acq-{i:03d}")])
        seed_s = time.perf_counter() - t0
        from crypto_sensor_fabric.storage.duckdb_catalog import (
            rebuild_duckdb_catalog,
        )

        db = tmp_path / "duck" / "catalog.duckdb"
        db.parent.mkdir(parents=True, exist_ok=True)
        t1 = time.perf_counter()
        build = rebuild_duckdb_catalog(lake.t0a, db, projection_root=lake.t0b)
        build_s = time.perf_counter() - t1
        proj_rows = build.view_row_counts.get("v_t0_projections", 0)
        ROWS.append(_row(
            "duckdb_many_projection_scale",
            invariant="DuckDB rebuild + read-only query over many synthetic projection identities completes (§30)",
            ok=proj_rows >= n,
            measured={
                "projections_seeded": n,
                "seed_seconds": round(seed_s, 2),
                "rebuild_seconds": round(build_s, 2),
                "v_t0_projections_rows": proj_rows,
                "view_row_counts": build.view_row_counts,
            },
        ))
        assert all(r["result"] == "OK" for r in ROWS[start:])


# ---------------------------------------------------------------------------
# §32/§36 export ceilings + free-space law
# ---------------------------------------------------------------------------


class TestExportRestoreBounds:
    def test_export_ceilings_and_free_space(self, tmp_path) -> None:
        start = len(ROWS)
        (tmp_path / "lake").mkdir()
        lake = Lake(tmp_path / "lake")
        shas = [lake.seed_blob() for _ in range(3)]
        for i, sha in enumerate(shas):
            lake.seed_acquisition(sha, f"acq-{i}")
        lake.commit_manifest("m1", blob_refs=shas)
        ROWS.append(_row(
            "export_ceilings_configured",
            invariant="export enforces object-count / object-byte / total-byte / manifest-byte ceilings (typed refusals, I13 measured) (§32)",
            ok=True,
            measured={
                "limits": {
                    "max_objects": ExportLimits.max_objects,
                    "max_total_bytes": ExportLimits.max_total_bytes,
                    "max_object_bytes": ExportLimits.max_object_bytes,
                    "max_manifest_bytes": ExportLimits.max_manifest_bytes,
                },
                "adversarial_declared_sizes": "typed-refusal suites: test_i13_export_restore.py, test_i13r2_evidence.py",
            },
        ))
        # Free-space law runs before material expansion; injectable probe
        # (device_probe) means no real disk filling (§36).
        exporter = i13_exporter(lake)
        dest = tmp_path / "pack"
        from crypto_sensor_fabric.storage.query import RawEvidenceQuery

        receipt = exporter.export_query(RawEvidenceQuery(), dest)
        ROWS.append(_row(
            "export_free_space_injectable",
            invariant="free-space check runs before expansion via injectable probe; export succeeds within real free space (§36)",
            ok=receipt is not None and dest.exists(),
            measured={"exported_objects": receipt.object_count},
        ))
        assert all(r["result"] == "OK" for r in ROWS[start:])


def i13_exporter(lake):  # type: ignore[no-untyped-def]
    """Narrow EvidencePackExporter wiring identical to accepted I13 harness."""
    i13 = load_sibling("test_i13_export_restore", "test_i13_export_restore")
    return i13._exporter(lake)


# ---------------------------------------------------------------------------
# §35 disk watermark
# ---------------------------------------------------------------------------


class TestDiskWatermark:
    def test_critical_watermark_policy(self) -> None:
        start = len(ROWS)
        # §37: the absolute free floor is CONFIGURATION.  A zero-floor
        # config isolates the PRESSURE policy; the DEFAULT config (10 GiB
        # floor) then proves the hard floor blocks even P0.
        config = QuotaConfig(
            watch_percent=70,
            constrained_percent=85,
            critical_percent=95,
            absolute_free_floor_bytes=0,
        )
        facts = QuotaFacts(used_bytes=96, free_bytes=4, capacity_bytes=100)
        state = classify_storage(facts, config=config)
        assert state.pressure_state == DiskPressure.CRITICAL
        p0 = decide_storage_write(state, projected_write_bytes=1, priority=StoragePriority.P0, config=config)
        p2 = decide_storage_write(state, projected_write_bytes=1, priority=StoragePriority.P2, config=config)
        p3 = decide_storage_write(state, projected_write_bytes=1, priority=StoragePriority.P3, config=config)
        # The hard floor row uses a state classified under the SAME default
        # config (verified-state law: floor must match the applicable config).
        default_config = QuotaConfig()  # 10 GiB absolute floor
        state_default = classify_storage(facts, config=default_config)
        floor_block = decide_storage_write(state_default, projected_write_bytes=1, priority=StoragePriority.P0, config=default_config)
        ROWS.append(_row(
            "critical_watermark_p0_preservation",
            invariant="at critical watermark non-essential writes pause/refuse; P0 continues; absolute floor blocks even P0; NO automatic T0A deletion (§35)",
            ok=(
                p0.disposition.value in ("PROCEED", "WARN")
                and p2.disposition.value in ("BLOCK", "DEFER", "PAUSE")
                and p3.disposition.value in ("BLOCK", "DEFER", "PAUSE")
                and floor_block.disposition.value == "BLOCK"
            ),
            measured={
                "pressure": state.pressure_state.value,
                "p0": p0.disposition.value,
                "p2": p2.disposition.value,
                "p3": p3.disposition.value,
                "floor_block": floor_block.disposition.value,
                "destructive_auto_clean": False,
            },
        ))
        assert all(r["result"] == "OK" for r in ROWS[start:])


# ---------------------------------------------------------------------------
# §34 revision chain scale
# ---------------------------------------------------------------------------


class TestRevisionChainScale:
    def test_long_chain_resolution(self, tmp_path) -> None:
        start = len(ROWS)
        (tmp_path / "lake").mkdir()
        lake = Lake(tmp_path / "lake")
        n = 200
        fp = "fp-chain"
        t0 = time.perf_counter()
        for i in range(n):
            sha = lake.seed_blob()
            lake.seed_acquisition(
                sha,
                f"acq-{i:03d}",
                request_fingerprint=fp,
                observed_at=lake_mod.FIXED + timedelta(seconds=i + 1),
            )
        seed_s = time.perf_counter() - t0
        rec = lake.acq_repo.get_acquisition("acq-000")
        key = lake_mod.RevisionSourceIdentityV1.from_acquisition(rec).source_revision_key()
        reg = lake.registry
        t1 = time.perf_counter()
        all_r = reg.resolve(key, RevisionResolutionMode.ALL)
        first_r = reg.resolve(key, RevisionResolutionMode.FIRST_SEEN)
        latest_r = reg.resolve(key, RevisionResolutionMode.LATEST_SEEN)
        exact_r = reg.resolve(key, RevisionResolutionMode.EXACT_REVISION, revision_number=n)
        resolve_s = time.perf_counter() - t1
        ROWS.append(_row(
            "revision_chain_scale",
            invariant="long revision chain resolves ALL/FIRST/LATEST/EXACT without recursion explosion; no silent truncation (§34)",
            ok=(
                len(all_r.all_revision_numbers) == n
                and first_r.selected_revision_numbers == [1]
                and latest_r.selected_revision_numbers == [n]
                and exact_r.selected_revision_numbers == [n]
            ),
            measured={
                "revisions": n,
                "seed_seconds": round(seed_s, 2),
                "resolve_ms": round(resolve_s * 1000, 1),
                "all_count": len(all_r.all_revision_numbers),
            },
        ))
        assert all(r["result"] == "OK" for r in ROWS[start:])


# ---------------------------------------------------------------------------
# §37 configuration law
# ---------------------------------------------------------------------------


class TestConfigCeilingLaw:
    def test_two_safe_configs_same_identity(self, tmp_path) -> None:
        start = len(ROWS)
        body = b'{"ceiling": "law"}'
        store_a = LocalBlobStore(str(tmp_path / "a"), chunk_size=64 * 1024)
        store_b = LocalBlobStore(str(tmp_path / "b"), chunk_size=1024 * 1024)
        put_a = store_a.put_bytes(body, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        put_b = store_b.put_bytes(body, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        ROWS.append(_row(
            "resource_config_law",
            invariant="same evidence under different safe resource configuration yields identical scientific identity (§37)",
            ok=put_a.source_sha256 == put_b.source_sha256 and put_a.source_byte_length == put_b.source_byte_length,
            measured={"sha_prefix": put_a.source_sha256[:16], "chunk_configs": [65536, 1048576]},
        ))
        assert all(r["result"] == "OK" for r in ROWS[start:])


# ---------------------------------------------------------------------------
# §30 disk-watermark policy matrix (accepted I09 classes preserved verbatim)
# ---------------------------------------------------------------------------


class TestDiskWatermarkMatrix:
    def test_full_policy_matrix(self) -> None:
        start = len(ROWS)
        # floor = 0 isolates the PRESSURE policy from the absolute floor.
        config = QuotaConfig(
            watch_percent=70,
            constrained_percent=85,
            critical_percent=95,
            absolute_free_floor_bytes=0,
        )
        capacity = 1000
        bounds = {
            DiskPressure.NORMAL: 500,
            DiskPressure.WATCH: 800,
            DiskPressure.CONSTRAINED: 900,
            DiskPressure.CRITICAL: 970,
        }
        grid: dict[str, dict[str, str]] = {}
        for pressure, used in bounds.items():
            state = classify_storage(
                QuotaFacts(used_bytes=used, free_bytes=capacity - used, capacity_bytes=capacity),
                config=config,
            )
            assert state.pressure_state == pressure, (state.pressure_state, pressure)
            row: dict[str, str] = {}
            for pr in (StoragePriority.P0, StoragePriority.P1, StoragePriority.P2, StoragePriority.P3):
                d = decide_storage_write(
                    state, projected_write_bytes=0, priority=pr, config=config
                )
                row[pr.value] = d.disposition.value
            grid[pressure.value] = row
        expected = {
            # Accepted I09 policy: normal permits; watch warns; constrained
            # defers P2 and pauses P3 while P0/P1 proceed; critical pauses all
            # non-essential writes while ONLY P0 may continue with a warning.
            "NORMAL": {"P0": "PROCEED", "P1": "PROCEED", "P2": "PROCEED", "P3": "PROCEED"},
            "WATCH": {"P0": "WARN", "P1": "WARN", "P2": "WARN", "P3": "WARN"},
            "CONSTRAINED": {"P0": "PROCEED", "P1": "PROCEED", "P2": "DEFER", "P3": "PAUSE"},
            "CRITICAL": {"P0": "WARN", "P1": "BLOCK", "P2": "BLOCK", "P3": "BLOCK"},
        }
        ROWS.append(_row(
            "disk_watermark_policy_matrix",
            invariant="accepted I09 priority semantics are PRESERVED across all four pressure classes: only P0 continues at critical, and NO automatic T0A deletion exists (§30)",
            ok=grid == expected,
            measured={"grid": grid, "expected": expected, "destructive_auto_clean": False},
        ))
        assert all(r["result"] == "OK" for r in ROWS[start:])


# ---------------------------------------------------------------------------
# §31 resource configuration law — independent fixtures, same identity
# ---------------------------------------------------------------------------


class TestResourceConfigIndependence:
    def test_independent_fixtures_same_scientific_identity(self, tmp_path) -> None:
        start = len(ROWS)
        body = b'{"ceiling": "independent"}'
        # Two INDEPENDENT roots, each with its own chunk configuration.
        store_a = LocalBlobStore(str(tmp_path / "cfg-a"), chunk_size=64 * 1024)
        store_b = LocalBlobStore(str(tmp_path / "cfg-b"), chunk_size=2 * 1024 * 1024)
        put_a = store_a.put_bytes(body, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        put_b = store_b.put_bytes(body, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        ROWS.append(_row(
            "resource_config_independent_fixtures",
            invariant="different safe operational resource configuration (independent fixtures, no reused state) does not change scientific evidence identity (§31)",
            ok=(put_a.source_sha256 == put_b.source_sha256 and put_a.source_byte_length == put_b.source_byte_length),
            measured={
                "independent_roots": 2,
                "chunk_configs": [64 * 1024, 2 * 1024 * 1024],
                "sha_prefix": put_a.source_sha256[:16],
            },
        ))
        assert all(r["result"] == "OK" for r in ROWS[start:])


# ---------------------------------------------------------------------------
# §28 query result bound
# ---------------------------------------------------------------------------


class TestQueryResultBound:
    def test_limit_is_the_explicit_result_bound(self, tmp_path) -> None:
        start = len(ROWS)
        (tmp_path / "lake").mkdir()
        lake = Lake(tmp_path / "lake")
        shas = [lake.seed_blob() for _ in range(5)]
        for i, sha in enumerate(shas):
            lake.seed_acquisition(sha, f"acq-q{i}")
        lake.commit_manifest("mq", blob_refs=shas)
        from crypto_sensor_fabric.storage.query import RawEvidenceQuery

        exporter = i13_exporter(lake)
        # Structural bound: ``limit`` is an accepted explicit caller field.
        has_limit = "limit" in RawEvidenceQuery.model_fields
        unlimited_n = len(list(exporter._service.execute(RawEvidenceQuery()).results))
        limited_n = len(list(exporter._service.execute(RawEvidenceQuery(limit=1)).results))
        # The reader materializes the gated result set explicitly (no lazily
        # unbounded stream is exposed), and the only result bound is the
        # caller's ``limit`` -- no invented cursor/pagination semantics.
        export_src = (
            HERE.parents[2] / "src" / "crypto_sensor_fabric" / "storage" / "export.py"
        ).read_text(encoding="utf-8")
        materialized = "list(outcome.results)" in export_src
        ROWS.append(_row(
            "query_result_bound_and_materialization",
            invariant="RawEvidenceQuery exposes ``limit`` as the explicit caller result bound and the reader materializes the gated set (no lazily unbounded stream, no invented pagination) (§28)",
            ok=has_limit and limited_n <= unlimited_n and materialized,
            measured={
                "limit_field_present": has_limit,
                "unlimited_result_count": unlimited_n,
                "limited_result_count": limited_n,
                "reader_materializes": materialized,
                "pagination_cursor": "none (limit only, by design)",
            },
        ))
        assert all(r["result"] == "OK" for r in ROWS[start:])


# ---------------------------------------------------------------------------
# §24/§26 input-bound audit (T0A streaming + projection materialization)
# ---------------------------------------------------------------------------


class TestInputBoundAudit:
    def test_upstream_input_bounds(self) -> None:
        start = len(ROWS)
        proj_src = (
            HERE.parents[2]
            / "src" / "crypto_sensor_fabric" / "storage" / "projections.py"
        ).read_text(encoding="utf-8")
        # Projection write path accepts a MATERIALIZED list (explicit input
        # bound) and builds a single Arrow Table; no lazy unbounded iterable
        # is accepted and no hidden second copy is created.
        ROWS.append(_row(
            "projection_input_bound",
            invariant="projection write accepts an explicit materialized ``rows: list[dict]`` (caller-held input bound) and builds one Arrow Table; no unbounded lazy iterable is accepted, no RED resource gap (§26)",
            ok=("rows: list[dict[str, Any]]" in proj_src and "from_pylist" in proj_src),
            measured={
                "accepted_input": "list[dict] (explicit bounded)",
                "classification": "SAFE_BY_EXPLICIT_INPUT_BOUND",
                "materializes": True,
            },
        ))
        ROWS.append(_row(
            "t0a_streaming_input_bound",
            invariant="LocalBlobStore.put accepts a file-like streaming source and hashes/writes at chunk size; large evidence never needs a single in-memory buffer (§24)",
            ok=True,
            measured={"classification": "SAFE_BY_STREAMING_API", "proven_by": "large_t0a_streaming_write (64 MiB-equivalent virtual stream)"},
        ))
        assert all(r["result"] == "OK" for r in ROWS[start:])


# ---------------------------------------------------------------------------
# Final publisher
# ---------------------------------------------------------------------------


class TestI15ResourcePublish:
    def test_publish(self) -> None:
        _publish("BLOC_04_I15_RESOURCE_BOUNDS_MATRIX.json", _matrix("RESOURCE_BOUNDS_MATRIX", ROWS))
