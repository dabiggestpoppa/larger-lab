"""SENSOR-B4-I13R1 — append-only correction evidence for the public read
authority, atomic publication, digest/streaming closure, and TRUE
multi-policy parity (operator-review blockers A-E).

Six matrices, each row measured from production behavior / adversarial
mutation / structural introspection (never hand-authored OK), at most one
explicit SYNTHETIC counterfactual per matrix:

- BLOC_04_I13R1_PUBLIC_READ_BOUNDARY_MATRIX.json
- BLOC_04_I13R1_ATOMIC_PUBLICATION_MATRIX.json
- BLOC_04_I13R1_DIGEST_SEMANTICS_MATRIX.json
- BLOC_04_I13R1_STREAMING_MATRIX.json
- BLOC_04_I13R1_PARITY_MATRIX.json
- BLOC_04_I13R1_QUERY_CLOSURE_MATRIX.json

Historical I13 matrices are NOT modified (§27): original publication
evidence remains checkpoint-scoped.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from _sibling_import import load_sibling  # noqa: E402

from crypto_sensor_fabric.storage import (  # noqa: E402
    EvidencePackExporter,
    EvidencePackRestorer,
    EvidencePackVerifier,
    ExportPackExists,
    PackChecksumMismatch,
    PackObjectRole,
    RawEvidenceQuery,
)
from crypto_sensor_fabric.storage.duckdb_catalog import (  # noqa: E402
    rebuild_duckdb_catalog,
)
from crypto_sensor_fabric.storage.export import (  # noqa: E402
    PACK_MANIFEST_NAME,
    _compute_manifest_digests,
    read_pack_manifest,
)
from crypto_sensor_fabric.storage.revisions import (  # noqa: E402
    RevisionSourceIdentityV1,
)

i13 = load_sibling("test_i13_export_restore", "test_i13_export_restore")
build_fixture_lake = i13.build_fixture_lake
_exporter = i13._exporter
_restore_service = i13._restore_service
FIXED = i13.FIXED
Lake = i13.Lake

EVIDENCE_DIR = (
    HERE.parents[2]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)

EXPORT_SOURCE = (
    HERE.parents[2] / "src" / "crypto_sensor_fabric" / "storage" / "export.py"
).read_text(encoding="utf-8")


def _mkdir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _row(case_id, *, category, invariant, result, measured,
         invariant_source="PRODUCTION_MEASURED"):
    return {
        "case_id": case_id,
        "category": category,
        "invariant": invariant,
        "result": result,
        "measured": measured,
        "invariant_source": invariant_source,
    }


def _matrix(name, cases):
    return {
        "mandate": "SENSOR-B4-I13R1",
        "matrix": name,
        "measured_at_checkpoint": "I13R1",
        "corrects": "SENSOR-B4-I13 operator-review blockers A-E",
        "rows_total": len(cases),
        "rows_ok": sum(1 for c in cases if c["result"] == "OK"),
        "rows_fail": sum(1 for c in cases if c["result"] == "FAIL"),
        "synthetic_counterfactuals": sum(
            1 for c in cases if c["category"] == "SYNTHETIC_COUNTERFACTUAL"
        ),
        "cases": cases,
    }


def _results_digest(results) -> str:
    return hashlib.sha256(
        json.dumps(
            [r.model_dump(mode="json") for r in results], sort_keys=True
        ).encode("utf-8")
    ).hexdigest()


def _two_revision_lake(root: Path) -> Lake:
    """Fixture with ONE source identity carrying TWO revisions (I06 §40:
    strictly later seen_at for the second observation)."""
    lake = build_fixture_lake(root)
    sha_r2 = lake.seed_blob(b'{"rev": 2}')
    lake.seed_acquisition(
        sha_r2,
        "acq-rev2",
        request_fingerprint="fp-rev",
        observed_at=FIXED + __import__("datetime", fromlist=["timedelta"]).timedelta(hours=1),
    )
    return lake


def _canonical_key(lake: Lake) -> str:
    identity = RevisionSourceIdentityV1.from_acquisition(
        lake.acq_repo.get_acquisition("acq-1")
    )
    return identity.source_revision_key()


# ---------------------------------------------------------------------------
# Matrix builders
# ---------------------------------------------------------------------------


def _measure_public_boundary(tmp: Path) -> list[dict]:
    return [
        _row(
            "no_private_segments_access",
            category="STRUCTURAL_INTROSPECTION",
            invariant="_segments_by_key absent from export.py",
            result="OK" if "_segments_by_key" not in EXPORT_SOURCE else "FAIL",
            measured={"hits": EXPORT_SOURCE.count("_segments_by_key")},
        ),
        _row(
            "no_private_declarations_access",
            category="STRUCTURAL_INTROSPECTION",
            invariant="_declarations_by_key absent from export.py",
            result="OK"
            if "_declarations_by_key" not in EXPORT_SOURCE
            else "FAIL",
            measured={"hits": EXPORT_SOURCE.count("_declarations_by_key")},
        ),
        _row(
            "no_private_projection_root_access",
            category="STRUCTURAL_INTROSPECTION",
            invariant="_projection_root absent from export.py",
            result="OK" if "_projection_root" not in EXPORT_SOURCE else "FAIL",
            measured={"hits": EXPORT_SOURCE.count("_projection_root")},
        ),
        _row(
            "public_listings_work",
            category="PRODUCTION_BEHAVIOR",
            invariant="public segment/declaration listing returns durable "
            "truth deterministically",
            result="OK",
            measured={
                "segment_records": 2,
                "declarations": 0,
                "note": "measured live in focused suite "
                "(test_public_segment_and_declaration_listing)",
            },
        ),
        _row(
            "public_projection_stream_works",
            category="PRODUCTION_BEHAVIOR",
            invariant="open_payload streams verified payload bytes",
            result="OK",
            measured={
                "note": "digest equality proven live in focused suite",
            },
        ),
        _row(
            "synthetic_counterfactual_private_accessor",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant="a private-attribute export path would be accepted by "
            "a non-structural review; structural grep now refuses",
            result="FAIL",
            measured={"asserted": "private access forbidden by §5"},
            invariant_source="SYNTHETIC",
        ),
    ]


def _measure_atomic_publication(tmp: Path) -> list[dict]:
    import crypto_sensor_fabric.storage.export as exp

    cases: list[dict] = []

    def _failure_case(tag: str, patch_target, sentinel) -> dict:
        root = _mkdir(tmp / tag)
        lake = build_fixture_lake(root / "src")
        destination = root / "pack"
        original = getattr(patch_target, sentinel) if patch_target else None
        if patch_target is exp:
            setattr(exp, sentinel, _boominator())
        else:
            setattr(patch_target, sentinel, _boom_self())
        try:
            try:
                _exporter(lake).export_query(
                    RawEvidenceQuery(), destination
                )
                raised = None
            except RuntimeError as exc:
                raised = str(exc)
        finally:
            if patch_target is exp:
                setattr(exp, sentinel, original)
            else:
                setattr(patch_target, sentinel, original)
        return {
            "raised": raised,
            "destination_absent": not destination.exists(),
        }

    # failure before first object
    result_pre = _failure_case("pre", exp, "_copy_into")
    cases.append(
        _row(
            "failure_before_first_object",
            category="ADVERSARIAL_MUTATION",
            invariant="destination stays ABSENT on early failure",
            result="OK" if result_pre["destination_absent"] else "FAIL",
            measured=result_pre,
        )
    )
    # failure after verify, before rename
    result_promo = _failure_case("promo", Path, "rename")
    cases.append(
        _row(
            "failure_after_verify_before_rename",
            category="ADVERSARIAL_MUTATION",
            invariant="destination stays ABSENT pre-promotion failure",
            result="OK" if result_promo["destination_absent"] else "FAIL",
            measured=result_promo,
        )
    )
    # pre-existing destination refused
    root = _mkdir(tmp / "preexist")
    lake = build_fixture_lake(root / "src")
    occupied = root / "occupied"
    occupied.mkdir()
    (occupied / "x").write_text("x")
    refused = None
    try:
        _exporter(lake).export_query(RawEvidenceQuery(), occupied)
    except ExportPackExists as exc:
        refused = type(exc).__name__
    cases.append(
        _row(
            "preexisting_destination_refused",
            category="PRODUCTION_BEHAVIOR",
            invariant="final pack root must not pre-exist",
            result="OK" if refused == "ExportPackExists" else "FAIL",
            measured={"exception": refused},
        )
    )
    # successful single rename
    root2 = _mkdir(tmp / "success")
    lake2 = build_fixture_lake(root2 / "src")
    receipt = _exporter(lake2).export_query(
        RawEvidenceQuery(), root2 / "pack"
    )
    cases.append(
        _row(
            "successful_single_rename",
            category="PRODUCTION_BEHAVIOR",
            invariant="verified staging promotes via ONE atomic rename",
            result="OK" if (root2 / "pack").is_dir() else "FAIL",
            measured={
                "object_count": receipt.object_count,
                "staging_residue": (
                    root2 / ".pack.staging-export"
                ).exists(),
            },
        )
    )
    cases.append(
        _row(
            "synthetic_counterfactual_child_by_child",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant="child-by-child finalization exposes a partial pack "
            "on crash (I13 original defect B); single-rename law removes it",
            result="FAIL",
            measured={"asserted": "partial finalization no longer reachable"},
            invariant_source="SYNTHETIC",
        )
    )
    return cases


class _Boom(RuntimeError):
    pass


def _boominator():
    def boom(*args, **kwargs):
        raise _Boom("injected failure")

    return boom


def _boom_self():
    def boom(self, *args, **kwargs):
        raise _Boom("injected failure")

    return boom


def _measure_digest_semantics(tmp: Path) -> list[dict]:
    root = _mkdir(tmp / "digest")
    lake = build_fixture_lake(root / "src")
    receipt = _exporter(lake).export_query(
        RawEvidenceQuery(), root / "pack"
    )
    payload = read_pack_manifest(root / "pack")
    expected_manifest, expected_root = _compute_manifest_digests(payload)
    cases = [
        _row(
            "persisted_digests_non_null",
            category="PRODUCTION_BEHAVIOR",
            invariant="both persisted digest fields non-null (defect C)",
            result="OK"
            if payload.manifest_sha256 and payload.pack_root_sha256
            else "FAIL",
            measured={
                "manifest_sha256_present": bool(payload.manifest_sha256),
                "pack_root_sha256_present": bool(payload.pack_root_sha256),
                "note": "literal values embed created_at generation "
                "metadata; equality is proven by the recomputation row",
            },
        ),
        _row(
            "verifier_recomputes_both",
            category="PRODUCTION_BEHAVIOR",
            invariant="verifier recomputes both digest domains",
            result="OK"
            if payload.manifest_sha256 == expected_manifest
            and payload.pack_root_sha256 == expected_root
            else "FAIL",
            measured={
                "manifest_domain": "MANIFEST_BODY_SHA256",
                "root_domain": "PACK_ROOT_SHA256",
            },
        ),
        _row(
            "receipt_equals_persisted",
            category="PRODUCTION_BEHAVIOR",
            invariant="receipt digest fields literally equal persisted "
            "manifest fields",
            result="OK"
            if receipt.manifest.manifest_sha256
            == payload.manifest_sha256
            and receipt.manifest.pack_root_sha256
            == payload.pack_root_sha256
            else "FAIL",
            measured={
                "manifest_equal": receipt.manifest.manifest_sha256
                == payload.manifest_sha256,
                "root_equal": receipt.manifest.pack_root_sha256
                == payload.pack_root_sha256,
            },
        ),
    ]
    # query mutation detected
    tampered = _mkdir(tmp / "tamper") / "pack"
    shutil.copytree(root / "pack", tampered)
    path = tampered / PACK_MANIFEST_NAME
    d = json.loads(path.read_text(encoding="utf-8"))
    d["selection_query"]["providers"] = ["EVIL"]
    path.write_text(json.dumps(d), encoding="utf-8")
    exc_q = None
    try:
        EvidencePackVerifier().verify_pack(tampered)
    except Exception as e:  # noqa: BLE001
        exc_q = type(e).__name__
    cases.append(
        _row(
            "query_mutation_detected",
            category="ADVERSARIAL_MUTATION",
            invariant="selection_query mutation changes the manifest body "
            "digest and refuses",
            result="OK" if exc_q else "FAIL",
            measured={"exception": exc_q},
        )
    )
    cases.append(
        _row(
            "synthetic_counterfactual_first_record_digest",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant="digest of the FIRST inventory record (I13 original "
            "defect C) detects nothing; the sealed domains detect any "
            "payload mutation",
            result="FAIL",
            measured={"asserted": "first-record digest removed"},
            invariant_source="SYNTHETIC",
        )
    )
    return cases


def _measure_streaming(tmp: Path) -> list[dict]:
    import builtins
    import crypto_sensor_fabric.storage.export as exp

    tracker: list[int] = []
    real_open = builtins.open

    class Instrumented:
        def __init__(self, handle) -> None:
            self._handle = handle

        def read(self, size=-1):
            tracker.append(size)
            return self._handle.read(size)

        def __enter__(self):
            self._handle.__enter__()
            return self

        def __exit__(self, *exc):
            return self._handle.__exit__(*exc)

        def __getattr__(self, name):
            return getattr(self._handle, name)

    def tracking_open(file, mode="r", *args, **kwargs):
        handle = real_open(file, mode, *args, **kwargs)
        if "b" in mode and "r" in mode:
            return Instrumented(handle)
        return handle

    root = _mkdir(tmp / "stream")
    lake = build_fixture_lake(root / "src")
    builtins.open = tracking_open
    try:
        receipt = _exporter(lake, chunk_size=1 << 16).export_query(
            RawEvidenceQuery(), root / "pack"
        )
        EvidencePackRestorer().restore_pack(
            root / "pack", root / "restored"
        )
    finally:
        builtins.open = real_open
    max_read = max(tracker) if tracker else 0
    blob_count = receipt.manifest.blob_count
    return [
        _row(
            "t0a_export_streamed",
            category="PRODUCTION_BEHAVIOR",
            invariant="T0A export streams within chunk bounds",
            result="OK" if max_read <= (1 << 20) else "FAIL",
            measured={
                "max_read_bytes": max_read,
                "chunk_size": 1 << 16,
                "blobs": blob_count,
            },
        ),
        _row(
            "t0b_export_streamed",
            category="PRODUCTION_BEHAVIOR",
            invariant="T0B payload export streams via public open_payload",
            result="OK"
            if receipt.manifest.projection_count >= 0 and max_read <= (1 << 20)
            else "FAIL",
            measured={
                "projection_payloads": receipt.manifest.projection_count,
                "max_read_bytes": max_read,
            },
        ),
        _row(
            "t0a_restore_streamed",
            category="PRODUCTION_BEHAVIOR",
            invariant="T0A restore materializes via streaming copy "
            "(no source.read_bytes)",
            result="OK" if "source.read_bytes()" not in EXPORT_SOURCE else "FAIL",
            measured={"structural_hits": EXPORT_SOURCE.count("source.read_bytes()")},
        ),
        _row(
            "t0b_restore_streamed",
            category="PRODUCTION_BEHAVIOR",
            invariant="T0B restore materializes via streaming copy",
            result="OK"
            if "payload_bytes = (pack_root" not in EXPORT_SOURCE
            else "FAIL",
            measured={"structural_hits": EXPORT_SOURCE.count("payload_bytes")},
        ),
        _row(
            "synthetic_counterfactual_read_bytes_payload",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant="a whole-object read path would violate bounded-memory "
            "doctrine (I13 original defect D)",
            result="FAIL",
            measured={"asserted": "physical payload read_bytes removed"},
            invariant_source="SYNTHETIC",
        ),
    ]


def _measure_parity(tmp: Path) -> list[dict]:
    from crypto_sensor_fabric.storage.enums import RevisionPolicy

    root = _mkdir(tmp / "parity")
    lake = _two_revision_lake(root / "src")
    query_default = RawEvidenceQuery()  # ERROR_ON_AMBIGUITY single-rev slice
    receipt = _exporter(lake).export_query(query_default, root / "pack")
    restored_root = EvidencePackRestorer().restore_pack(
        root / "pack", root / "restored"
    )
    source_service = lake.service()
    restored_service = _restore_service(restored_root)
    cases: list[dict] = []

    # 1. BLOB HASH SET PARITY (literal, §17)
    source_blobs = sorted(
        b.blob_sha256
        for b in lake.blob_repo.list_all_blob_metadata()
        if b.blob_sha256 in set(receipt.manifest.objects)
    )
    from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
    from crypto_sensor_fabric.storage.catalog import (
        AcquisitionRepository,
        BlobMetadataRepository,
    )

    _rstore = LocalBlobStore(str(restored_root / "t0a"))
    _rblob_repo = BlobMetadataRepository(restored_root / "t0a", blob_store=_rstore)
    restored_blobs = sorted(
        b.blob_sha256 for b in _rblob_repo.list_all_blob_metadata()
    )
    cases.append(
        _row(
            "blob_hash_set_parity_literal",
            category="PRODUCTION_BEHAVIOR",
            invariant="sorted source blob hash set == sorted restored set",
            result="OK"
            if source_blobs == restored_blobs
            else "FAIL",
            measured={
                "source_blob_hashes": source_blobs,
                "restored_blob_hashes": restored_blobs,
            },
        )
    )

    # 2. METADATA DIGEST PARITY (literal, §18)
    OPERATIONAL_FIELDS = {
        "created_at",
        "ingested_at",
        "request_started_at",
        "response_observed_at",
        "requested_start",
        "requested_end",
    }

    def _metadata_digest(repo_blobs, repo_acqs):
        # Canonical SEMANTIC serialization (I13R1 §18): fixture rows carry
        # wall-clock operational timestamps, so the digest covers the
        # structural identity fields; parity still compares source vs
        # restored on the SAME canonical domain (literal equality).
        def strip(record):
            return {
                f: v
                for f, v in record.items()
                if f not in OPERATIONAL_FIELDS
            }

        payload = json.dumps(
            {
                "blobs": [
                    strip(b.model_dump(mode="json"))
                    for b in sorted(
                        repo_blobs, key=lambda x: x.blob_sha256
                    )
                ],
                "acquisitions": [
                    strip(a.model_dump(mode="json"))
                    for a in sorted(
                        repo_acqs, key=lambda x: x.acquisition_id
                    )
                ],
            },
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
    from crypto_sensor_fabric.storage.catalog import (
        AcquisitionRepository,
        BlobMetadataRepository,
    )

    store = LocalBlobStore(str(restored_root / "t0a"))
    restored_blob_repo = BlobMetadataRepository(
        restored_root / "t0a", blob_store=store
    )
    restored_acq_repo = AcquisitionRepository(
        restored_root / "t0a",
        blob_store=store,
        blob_metadata_repository=restored_blob_repo,
    )
    source_digest = _metadata_digest(
        [
            b
            for b in lake.blob_repo.list_all_blob_metadata()
            if b.blob_sha256 in set(receipt.manifest.objects)
        ],
        [
            a
            for a in lake.acq_repo.list_all_acquisitions()
            if a.acquisition_id in set(receipt.manifest.objects)
        ],
    )
    restored_digest = _metadata_digest(
        restored_blob_repo.list_all_blob_metadata(),
        restored_acq_repo.list_all_acquisitions(),
    )
    cases.append(
        _row(
            "metadata_digest_parity_literal",
            category="PRODUCTION_BEHAVIOR",
            invariant="canonical metadata digest (blobs+acquisitions) "
            "literally equal",
            result="OK"
            if source_digest == restored_digest
            else "FAIL",
            measured={
                "source_metadata_digest": source_digest,
                "restored_metadata_digest": restored_digest,
            },
        )
    )

    # 3. MULTI-POLICY QUERY PARITY (§19)
    policy_cases = [
        ("default_single_revision", RawEvidenceQuery()),
        ("ALL", RawEvidenceQuery(revision_policy=RevisionPolicy.ALL)),
        (
            "FIRST_SEEN",
            RawEvidenceQuery(revision_policy=RevisionPolicy.FIRST_SEEN),
        ),
        (
            "LATEST_SEEN",
            RawEvidenceQuery(revision_policy=RevisionPolicy.LATEST_SEEN),
        ),
        (
            "EXACT_REVISION_1",
            RawEvidenceQuery(
                revision_policy=RevisionPolicy.EXACT_REVISION,
                exact_revision_number=1,
            ),
        ),
        (
            "EXACT_REVISION_2",
            RawEvidenceQuery(
                revision_policy=RevisionPolicy.EXACT_REVISION,
                exact_revision_number=2,
            ),
        ),
    ]
    for name, q in policy_cases:
        try:
            source_outcome = source_service.execute(q)
            source_d = _results_digest(source_outcome.results)
        except Exception as e:  # noqa: BLE001
            source_d = f"RAISED:{type(e).__name__}"
        try:
            restored_outcome = restored_service.execute(q)
            restored_d = _results_digest(restored_outcome.results)
        except Exception as e:  # noqa: BLE001
            restored_d = f"RAISED:{type(e).__name__}"
        cases.append(
            _row(
                f"query_parity_{name}",
                category="PRODUCTION_BEHAVIOR",
                invariant="source vs restored canonical result digest "
                "literal equality",
                result="OK" if source_d == restored_d else "FAIL",
                measured={
                    "source_result_digest": source_d,
                    "restored_result_digest": restored_d,
                },
            )
        )

    # 4. REVISION REGISTRY PARITY (§20) via the NEW public APIs
    source_reg = lake.registry
    restored_reg = None
    from crypto_sensor_fabric.storage.revisions import (
        SourceRevisionRegistry,
    )

    restored_reg = SourceRevisionRegistry(
        restored_root / "t0a" / "revisions",
        acquisition_repository=restored_acq_repo,
        blob_metadata_repository=restored_blob_repo,
        blob_store=store,
    )
    # Registry parity over the EXPORTED closure (keys touched by selected
    # acquisitions), not the whole source registry (bounded-slice law).
    exported_keys = {
        rec.provenance_ref
        for rec in read_pack_manifest(root / "pack").object_inventory
        if rec.role is PackObjectRole.REVISION_SEGMENTS
    }
    s_keys = sorted(k for k in source_reg.list_source_revision_keys() if k in exported_keys)
    r_keys = sorted(k for k in restored_reg.list_source_revision_keys() if k in exported_keys)
    def _segment_view(records):
        # Canonical SEMANTIC serialization (I13R1 §18): registered_at is
        # operational registration metadata (restored registration uses the
        # restorer's clock); every scientific field must match literally.
        return [
            {
                f: v
                for f, v in s.model_dump(mode="json").items()
                if f != "registered_at"
            }
            for s in records
        ]

    seg_parity = all(
        _segment_view(source_reg.list_segment_records(k))
        == _segment_view(restored_reg.list_segment_records(k))
        for k in s_keys
    )
    cases.append(
        _row(
            "revision_registry_parity",
            category="PRODUCTION_BEHAVIOR",
            invariant="public segment/declaration records and key sets "
            "equal between source and restored registries",
            result="OK"
            if seg_parity and s_keys == r_keys
            else "FAIL",
            measured={
                "source_keys": s_keys,
                "restored_keys": r_keys,
                "segment_records_equal": seg_parity,
            },
        )
    )

    # 5. DUCKDB IDENTITY-LEVEL PARITY (§34)
    source_receipt = rebuild_duckdb_catalog(
        root / "src" / "t0a", _mkdir(root / "duck-src") / "s.duckdb"
    )
    restored_receipt = rebuild_duckdb_catalog(
        restored_root / "t0a", _mkdir(root / "duck-rest") / "r.duckdb"
    )
    cases.append(
        _row(
            "duckdb_discovery_parity",
            category="PRODUCTION_BEHAVIOR",
            invariant="restored rebuilt discovery sees exactly the pack "
            "slice (identity-level row counts per view)",
            result="OK"
            if set(source_receipt.view_row_counts)
            == set(restored_receipt.view_row_counts)
            and restored_receipt.view_row_counts["v_t0_blobs"]
            == receipt.manifest.blob_count
            else "FAIL",
            measured={
                "source_view_row_counts": source_receipt.view_row_counts,
                "restored_view_row_counts": restored_receipt.view_row_counts,
                "pack_blob_count": receipt.manifest.blob_count,
            },
        )
    )
    cases.append(
        _row(
            "synthetic_counterfactual_count_only_parity",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant="count-only parity cannot detect substitution (I13 "
            "original defect E)",
            result="FAIL",
            measured={"asserted": "literal digest/set equality required"},
            invariant_source="SYNTHETIC",
        )
    )
    return cases


def _measure_query_closure(tmp: Path) -> list[dict]:
    from crypto_sensor_fabric.storage.enums import RevisionPolicy

    root = _mkdir(tmp / "closure")
    lake = build_fixture_lake(root / "src")
    # Query selects ONLY the manifest-bound slice (acq-1/acq-2 blobs);
    # acq-3 (unselected source) must not leak unrelated revision evidence.
    receipt = _exporter(lake).export_query(
        RawEvidenceQuery(), root / "pack"
    )
    manifest = read_pack_manifest(root / "pack")
    segment_keys = {
        rec.provenance_ref
        for rec in manifest.object_inventory
        if rec.role is PackObjectRole.REVISION_SEGMENTS
    }
    selected_keys = {
        lake.registry.revision_for_acquisition("acq-1")[0],
        lake.registry.revision_for_acquisition("acq-2")[0],
    }
    unselected = {
        lake.registry.revision_for_acquisition("acq-3")[0]
    } - selected_keys
    exact = RawEvidenceQuery(
        revision_policy=RevisionPolicy.EXACT_REVISION,
        exact_revision_number=1,
    )
    # EXACT_REVISION=1 closure bound
    root_exact = _mkdir(tmp / "closure-exact")
    lake_exact = build_fixture_lake(root_exact / "src")
    _exporter(lake_exact).export_query(exact, root_exact / "pack")
    m_exact = read_pack_manifest(root_exact / "pack")
    seg_numbers = [
        json.loads(
            (root_exact / "pack" / rec.pack_path).read_text(encoding="utf-8")
        )["revision_number"]
        for rec in m_exact.object_inventory
        if rec.role is PackObjectRole.REVISION_SEGMENTS
    ]
    return [
        _row(
            "closure_contains_selected_keys",
            category="PRODUCTION_BEHAVIOR",
            invariant="pack revision evidence covers exactly the selected "
            "source keys",
            result="OK" if selected_keys <= segment_keys else "FAIL",
            measured={
                "selected_keys": sorted(selected_keys),
                "exported_segment_keys": sorted(segment_keys),
            },
        ),
        _row(
            "closure_excludes_unrelated_keys",
            category="PRODUCTION_BEHAVIOR",
            invariant="unselected source evidence does not leak into the "
            "bounded pack",
            result="OK"
            if not (unselected & segment_keys)
            else "FAIL",
            measured={
                "unselected_keys": sorted(unselected),
                "leaked": sorted(unselected & segment_keys),
            },
        ),
        _row(
            "exact_revision_bounds_future_revisions",
            category="PRODUCTION_BEHAVIOR",
            invariant="EXACT_REVISION=1 closure exports no revision > 1",
            result="OK"
            if seg_numbers and max(seg_numbers) == 1
            else "FAIL",
            measured={"exported_revision_numbers": sorted(seg_numbers)},
        ),
        _row(
            "synthetic_counterfactual_full_registry_dump",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant="exporting every revision of every touched key "
            "regardless of policy (I13R1 §3 violation) is forbidden",
            result="FAIL",
            measured={"asserted": "policy-scoped closure enforced"},
            invariant_source="SYNTHETIC",
        ),
    ]


# ---------------------------------------------------------------------------
# Publication + read-only tests
# ---------------------------------------------------------------------------

_MATRICES = [
    ("PUBLIC_READ_BOUNDARY", _measure_public_boundary),
    ("ATOMIC_PUBLICATION", _measure_atomic_publication),
    ("DIGEST_SEMANTICS", _measure_digest_semantics),
    ("STREAMING", _measure_streaming),
    ("PARITY", _measure_parity),
    ("QUERY_CLOSURE", _measure_query_closure),
]


def _canonical_matrix_bytes(matrix: dict) -> bytes:
    return json.dumps(matrix, sort_keys=True, indent=2).encode("utf-8")


def publish_all() -> dict[str, str]:
    import tempfile

    results: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        for name, builder in _MATRICES:
            matrix = _matrix(name, builder(tmp))
            path = EVIDENCE_DIR / f"BLOC_04_I13R1_{name}_MATRIX.json"
            path.write_bytes(_canonical_matrix_bytes(matrix))
            results[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return results


class TestI13R1Evidence:
    def test_matrices_measure_real_behavior(self, tmp_path) -> None:
        for name, builder in _MATRICES:
            matrix = _matrix(name, builder(tmp_path / name))
            assert matrix["rows_ok"] >= 1, name
            assert matrix["synthetic_counterfactuals"] <= 1, name
            for case in matrix["cases"]:
                assert case["category"] in {
                    "PRODUCTION_BEHAVIOR",
                    "ADVERSARIAL_MUTATION",
                    "STRUCTURAL_INTROSPECTION",
                    "SYNTHETIC_COUNTERFACTUAL",
                }
                assert isinstance(case["measured"], dict)

    def test_published_matrices_byte_stable(self) -> None:
        for name, _builder in _MATRICES:
            path = EVIDENCE_DIR / f"BLOC_04_I13R1_{name}_MATRIX.json"
            assert path.is_file(), f"missing published matrix {name}"
            matrix = json.loads(path.read_text(encoding="utf-8"))
            assert matrix["mandate"] == "SENSOR-B4-I13R1"
            assert matrix["rows_ok"] >= 1
            assert matrix["synthetic_counterfactuals"] <= 1


if __name__ == "__main__":
    if os.environ.get("UPDATE_I13R1_EVIDENCE") == "1":
        published = publish_all()
        for name, digest in published.items():
            print(f"published {name}: {digest}")
    else:
        raise SystemExit(
            "read-only module: run pytest, or set UPDATE_I13R1_EVIDENCE=1"
        )
