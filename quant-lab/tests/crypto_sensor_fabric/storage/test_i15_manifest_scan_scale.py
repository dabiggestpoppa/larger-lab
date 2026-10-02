"""SENSOR-B4-I15 — manifest scan scale (§18-§22).

The frozen resource benchmark requires scanning >=10,000 ACTUAL VALID
``PartitionManifest`` ROWS.  Pointer files, provenance fragments,
acquisition rows and filesystem objects are explicitly NOT manifest rows
and are never relabelled to satisfy the gate (§18).

This module is SPLIT OUT of ``test_i15_resource_bounds.py`` on purpose
(§21): the accepted manifest catalog physically requires ONE immutable
parquet fragment per manifest row, so building the corpus plus running the
production scan on this machine costs several minutes -- close enough to a
bounded-command ceiling that a separate module keeps the seal repeatable.
Corpus construction is benchmark-fixture setup (§20); the ACTUAL scan uses
production reader code.

Publishes BLOC_04_I15_MANIFEST_SCAN_MATRIX.json once.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import tracemalloc
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from _sibling_import import load_sibling  # noqa: E402

i04 = load_sibling("test_i04r1_evidence", "test_i04r1_evidence")

from crypto_sensor_fabric.storage.enums import StorageEncoding  # noqa: E402
from crypto_sensor_fabric.storage.manifests import (  # noqa: E402
    MANIFEST_SCHEMA,
    _manifest_row,
    _partition_hash,
)
from crypto_sensor_fabric.storage.recovery import RecoveryEngine  # noqa: E402

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

# The frozen benchmark row count.  Do NOT lower and relabel side-state.
ROWS_REQUIRED = 10_000

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


class TestManifestScanScale:
    def test_scan_scale_10k_real_manifest_rows(self, tmp_path) -> None:
        """SCAN_SCALE (§18-§22): >=10,000 ACTUAL VALID manifest rows.

        Corpus construction (§20): the accepted manifest catalog
        physically requires ONE immutable parquet fragment per manifest
        row (``_load_manifest_fragment``: ``len(rows) != 1`` is a
        ``CatalogIntegrityError``), so the production WRITE protocol
        cannot build 10k rows inside one bounded command.  The corpus is
        built as an EXPLICIT benchmark fixture using the canonical
        accepted serializer + schema
        (``pa.Table.from_pylist([_manifest_row(m)], schema=MANIFEST_SCHEMA)``
        then ``pq.write_table`` -- byte-for-byte the serialization step
        ``publish_immutable_fragment`` performs) into the production
        on-disk layout.  Every row is a valid accepted ``PartitionManifest``
        built by the canonical test factory; no malformed row, no parser
        bypass, no dictionary shortcut.

        The ACTUAL scan uses PRODUCTION reader code
        (``RecoveryEngine._all_manifests`` -> ``read_fragment`` +
        ``_manifest_from_row``), the same decoder ``get_manifest`` and the
        I08 recovery scan use.
        """
        import pyarrow as pa
        import pyarrow.parquet as pq

        root = tmp_path / "t0a"
        root.mkdir()
        store, blob_repo, acq_repo, mr = i04._repos(root)
        put = store.put_bytes(
            b'{"scan-scale": 1}',
            storage_encoding=StorageEncoding.NONE,
            source_media_type=MEDIA,
        )
        sha = put.blob.blob_sha256
        blob_repo.append_metadata(put.blob)
        acq_repo.append_acquisition(
            i04._acquisition(
                acquisition_id="acq-scan-scale",
                blob_sha256=sha,
                source_locator=f"file:///scale/{sha[:8]}",
            )
        )

        # -- benchmark-fixture corpus construction (§20) --------------------
        n = ROWS_REQUIRED
        partitions_root = root / "catalogs" / "manifests" / "partitions"
        t_build = time.perf_counter()
        expected_ids: set[str] = set()
        for i in range(n):
            m = i04._manifest(
                partition_manifest_id=f"pm-scan-{i:06d}",
                partition_key=f"KRAKEN_FUTURES/futures/BTC/scan-{i:06d}",
                blob_refs=[sha],
            )
            partition_dir = partitions_root / _partition_hash(m.partition_key)
            partition_dir.mkdir(parents=True, exist_ok=True)
            name = (
                f"v{m.manifest_version:08d}-"
                f"{hashlib.sha256(m.partition_manifest_id.encode('utf-8')).hexdigest()[:32]}"
                ".parquet"
            )
            pq.write_table(
                pa.Table.from_pylist([_manifest_row(m)], schema=MANIFEST_SCHEMA),
                str(partition_dir / name),
            )
            expected_ids.add(m.partition_manifest_id)
        build_s = time.perf_counter() - t_build

        # -- ACTUAL production scan (§18/§22) -------------------------------
        engine = RecoveryEngine(
            root,
            blob_store=store,
            blob_metadata_repository=blob_repo,
            acquisition_repository=acq_repo,
            manifest_repository=mr,
        )
        tracemalloc.start()
        t_scan = time.perf_counter()
        manifests = engine._all_manifests()
        scan_s = time.perf_counter() - t_scan
        scan_peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()

        scanned_ids = [m.partition_manifest_id for m in manifests]
        rows_scanned = len(manifests)
        duplicate_rows = rows_scanned - len(set(scanned_ids))
        order_key = [
            (m.partition_key, m.manifest_version, m.partition_manifest_id)
            for m in manifests
        ]
        order_ok = order_key == sorted(order_key)
        # invalid_rows == 0 without a second read pass: the production
        # scan decodes every fragment exactly once and yielded one row per
        # fragment.  fragment_files is counted from the filesystem (no
        # parse), so a skipped or duplicated fragment would make
        # rows_scanned != fragment_files.
        fragment_files = sum(1 for _ in partitions_root.rglob("v*.parquet"))
        invalid_rows = n - rows_scanned

        gate_ok = (
            rows_scanned >= ROWS_REQUIRED
            and rows_scanned == n
            and set(scanned_ids) == expected_ids
            and duplicate_rows == 0
            and invalid_rows == 0
            and fragment_files == n
            and order_ok
            and scan_peak < 512 * 1024 * 1024
        )
        ROWS.append(
            _row(
                "manifest_scan_scale_10k_real_rows",
                invariant=(
                    "scan >=10,000 ACTUAL VALID PartitionManifest ROWS with "
                    "production reader code: rows_scanned == rows_created, "
                    "invalid_rows == 0, duplicate logical ids == 0, "
                    "deterministic order, bounded memory (§18-§22)"
                ),
                ok=gate_ok,
                measured={
                    "manifest_rows_created": n,
                    "manifest_rows_scanned": rows_scanned,
                    "rows_required": ROWS_REQUIRED,
                    "invalid_rows": invalid_rows,
                    "duplicate_logical_ids": duplicate_rows,
                    "fragment_files": fragment_files,
                    "deterministic_order": order_ok,
                    "corpus_construction": (
                        "benchmark_fixture (canonical serializer + schema, "
                        "production on-disk layout) — NOT append throughput"
                    ),
                    "scan_reader": (
                        "RecoveryEngine._all_manifests -> read_fragment + "
                        "_manifest_from_row (production)"
                    ),
                    "per_record_rows": 1,
                    "build_seconds_informational": round(build_s, 2),
                    "scan_seconds_informational": round(scan_s, 2),
                    "scan_peak_memory_bytes": scan_peak,
                },
            )
        )
        assert all(r["result"] == "OK" for r in ROWS)


class TestI15ManifestScanPublish:
    def test_publish(self) -> None:
        _publish(
            "BLOC_04_I15_MANIFEST_SCAN_MATRIX.json",
            _matrix("MANIFEST_SCAN_MATRIX", ROWS),
        )
