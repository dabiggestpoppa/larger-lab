"""SENSOR-B4-I10R2C/D — measured relation-governance evidence and microseal."""

from __future__ import annotations

# ruff: noqa: E402

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import duckdb

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parents[2] / "src"
for _path in (str(_SRC), str(_HERE)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from _sibling_import import load_sibling
from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
from crypto_sensor_fabric.storage.duckdb_catalog import (
    CATALOG_ROLE,
    CATALOG_SCHEMA_VERSION,
    VIEW_NAMES,
    VIEW_SCHEMAS,
    rebuild_duckdb_catalog,
)
from crypto_sensor_fabric.storage.recovery import RecoveryJournal

relations = load_sibling("i10r2_relation_helpers", "test_i10r2_relations")
Fixture = relations.Fixture
EVIDENCE_DIR = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)
LEDGER = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "SENSOR_FABRIC_IMPLEMENTATION_PROGRESS.md"
)

HISTORICAL_I10 = {
    "BLOC_04_I10_CATALOG_REBUILD_MATRIX.json": "eca261e85c468366b075414eefdc8e3268c62260b843d23ce2bbb7b65012e548",
    "BLOC_04_I10_VIEW_EQUIVALENCE_MATRIX.json": "e7aefdc79da06fe820f8f8fcc0c1dd4d51681768dff3782645b190bdb617917b",
    "BLOC_04_I10_EVIDENCE_IMMUTABILITY_MATRIX.json": "6c069d3510a021409efd316c03fcb67b7b1bbbe9ec4c36ad62bce711a6276682",
    "BLOC_04_I10_CORRUPTION_DISCOVERY_MATRIX.json": "3883c7cad4076de57d581e812cab93f878927bd156741d505cb37249d01a8f85",
    "BLOC_04_I10_PORTABILITY_MATRIX.json": "68fc87660e7c6607545b19f99b67727a728796324ac5634991542a6e879e409b",
    "BLOC_04_I10_DUCKDB_REBUILD_EVIDENCE.md": "2df4f210f100f949f868ba8a830800fd8af9c5f80d4463197042ca979094ea74",
    "duckdb_rebuild.json": "677e23272be3055db83dd8b6a2cf8b2938b69ec3ebb5abbc6ed2f9ac70fbf5fd",
}
HISTORICAL_I10R1 = {
    "BLOC_04_I10R1_SCHEMA_CONTRACT_MATRIX.json": "b02f233dfa471c68025927f7ede374f213c673e29512193a846fc5c434e50f4a",
    "BLOC_04_I10R1_RUNTIME_EVIDENCE_TRUTH_MATRIX.json": "4654abb196bbbdbcd52a4ac2b9632aaf5276ecc7f7595ea8b81b63de13d09ea2",
    "BLOC_04_I10R1_STORAGE_USAGE_DIMENSION_MATRIX.json": "89ce91cc18a1097016c65bf2a9562ae2a523a7ef1e9cfc7d09f43773b455591b",
    "BLOC_04_I10R1_DISCOVERY_COST_MATRIX.json": "b43ccc1c36b50548f26574f810f00c8eee50816c60ec02f9b61e41eece54825f",
    "BLOC_04_I10R1_DURABLE_RELATION_MATRIX.json": "f43fe18878cd5a2c5f84cd260d18f46ee482b4c16363d9482b1fb2d38afdeef0",
    "BLOC_04_I10R1_DUCKDB_DISCOVERY_MICROSEAL.json": "0f5db0f982db43f25a1e0f31d2292013e0b048d5759011eaf25d3e6bd2786ffa",
    "BLOC_04_I10R1_DUCKDB_DISCOVERY_MICROSEAL.md": "ace11dbd40d3ffd9ef727a0b1aa44e7a7e2a73b98501497d90a8c2237f8a53a7",
}


def _stable(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _case(name: str, required: list[str], **values: Any) -> dict[str, Any]:
    row = {"case": name, **values, "required_invariants": required}
    row["result"] = "OK" if all(row.get(item) is True for item in required) else "FAIL"
    return row


def _matrix(name: str, rows: list[dict[str, Any]], **values: Any) -> dict[str, Any]:
    return {
        "checkpoint": "SENSOR-B4-I10R2",
        "matrix": name,
        "evidence_truth": (
            "Every non-counterfactual evidence predicate is mechanically observed "
            "from executed production behavior; deliberate counterfactual predicates "
            "are explicitly synthetic and must evaluate FAIL."
        ),
        **values,
        "rows": rows,
        "summary": {
            "rows": len(rows),
            "ok": sum(row["result"] == "OK" for row in rows),
            "fail": sum(row["result"] == "FAIL" for row in rows),
        },
    }


def _accepted(root: Path, output: Path) -> bool:
    try:
        rebuild_duckdb_catalog(root, output)
    except Exception:
        return False
    return output.is_file()


def _refused(root: Path, output: Path) -> bool:
    try:
        rebuild_duckdb_catalog(root, output)
    except Exception:
        return True
    return False


def _measured_lineage_binding(base: Path) -> dict[str, Any]:
    facts: dict[str, bool] = {}

    fixture = Fixture(base / "valid")
    facts["valid_lineage_chain_accepted"] = _accepted(
        fixture.root, base / "valid.duckdb"
    )

    fixture = Fixture(base / "entry-id")
    relations._mutate_lineage(  # noqa: SLF001
        fixture.root,
        lambda _payload, entry: entry.update(lineage_manifest_id="other-manifest"),
    )
    facts["entry_manifest_id_mismatch_refused"] = _refused(
        fixture.root, base / "entry-id.duckdb"
    )

    fixture = Fixture(base / "context-id")
    directory = fixture.root / "catalogs" / "manifests" / "projection_lineage"
    _, lineage = relations._fragment(directory, "lineage-1")  # noqa: SLF001
    lineage["lineage_manifest_id"] = "lineage-2"
    for entry in lineage["entries"]:
        entry["lineage_manifest_id"] = "lineage-2"
    relations._replace_fragment(  # noqa: SLF001
        directory, "lineage-1", lineage, new_logical_id="lineage-2"
    )
    facts["context_manifest_id_mismatch_refused"] = _refused(
        fixture.root, base / "context-id.duckdb"
    )

    fixture = Fixture(base / "artifact-source")
    blob_b = relations._add_second_blob(fixture)  # noqa: SLF001
    relations._mutate_lineage(  # noqa: SLF001
        fixture.root,
        lambda _payload, entry: entry.update(source_blob_sha256=blob_b),
    )
    facts["artifact_source_list_mismatch_refused"] = _refused(
        fixture.root, base / "artifact-source.duckdb"
    )

    fixture = Fixture(base / "missing-acquisition")
    relations._mutate_lineage(  # noqa: SLF001
        fixture.root,
        lambda _payload, entry: entry.update(
            source_acquisition_id="acquisition-does-not-exist"
        ),
    )
    facts["missing_source_acquisition_refused"] = _refused(
        fixture.root, base / "missing-acquisition.duckdb"
    )

    fixture = Fixture(base / "acquisition-mismatch")
    blob_b = relations._add_second_blob(fixture)  # noqa: SLF001
    acquisition_b = relations._add_second_acquisition(fixture, blob_b)  # noqa: SLF001
    relations._mutate_lineage(  # noqa: SLF001
        fixture.root,
        lambda _payload, entry: entry.update(source_acquisition_id=acquisition_b),
    )
    facts["acquisition_blob_mismatch_refused"] = _refused(
        fixture.root, base / "acquisition-mismatch.duckdb"
    )

    fixture = Fixture(base / "source-order")
    relations._mutate_lineage(  # noqa: SLF001
        fixture.root,
        lambda payload, entry: payload["entries"].append(dict(entry)),
    )
    facts["noncontiguous_source_order_refused"] = _refused(
        fixture.root, base / "source-order.duckdb"
    )

    fixture = Fixture(base / "row-bounds")
    relations._mutate_lineage(  # noqa: SLF001
        fixture.root,
        lambda _payload, entry: entry.update(source_row_start=0, source_row_end=None),
    )
    facts["invalid_row_bounds_refused"] = _refused(
        fixture.root, base / "row-bounds.duckdb"
    )

    fixture = Fixture(base / "record-type")
    relations._mutate_lineage(  # noqa: SLF001
        fixture.root,
        lambda payload, _entry: payload.update(record_type="wrong_lineage_type"),
    )
    facts["wrong_lineage_record_type_refused"] = _refused(
        fixture.root, base / "record-type.duckdb"
    )
    return facts


def build_i10r2_lineage_binding_matrix() -> dict[str, Any]:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        facts = _measured_lineage_binding(Path(tmp))
    rows = [
        _case("valid_lineage_chain_accepted", ["valid_lineage_chain_accepted"], **facts),
        _case("entry_manifest_id_mismatch_refused", ["entry_manifest_id_mismatch_refused"], **facts),
        _case("context_manifest_id_mismatch_refused", ["context_manifest_id_mismatch_refused"], **facts),
        _case("artifact_source_list_mismatch_refused", ["artifact_source_list_mismatch_refused"], **facts),
        _case("missing_source_acquisition_refused", ["missing_source_acquisition_refused"], **facts),
        _case("acquisition_blob_mismatch_refused", ["acquisition_blob_mismatch_refused"], **facts),
        _case("noncontiguous_source_order_refused", ["noncontiguous_source_order_refused"], **facts),
        _case("invalid_row_bounds_refused", ["invalid_row_bounds_refused"], **facts),
        _case("wrong_lineage_record_type_refused", ["wrong_lineage_record_type_refused"], **facts),
        _case(
            "counterfactual_accept_entry_manifest_mismatch",
            ["entry_manifest_id_mismatch_refused"],
            entry_manifest_id_mismatch_refused=False,
        ),
    ]
    return _matrix("I10R2_LINEAGE_BINDING", rows)


def _measured_recovery_envelope(base: Path) -> dict[str, bool]:
    facts: dict[str, bool] = {}
    fixture = Fixture(base / "valid")
    facts["valid_recovery_action_accepted"] = _accepted(
        fixture.root, base / "valid.duckdb"
    )

    attacks = {
        "wrong_record_type_refused": lambda payload, _: payload.update(
            record_type="wrong_recovery_action"
        ),
        "missing_record_type_refused": lambda payload, _: payload.pop("record_type"),
        "storage_mapping_contradiction_refused": lambda payload, _: payload.update(
            storage_object_type="STORAGE_JOB"
        ),
        "invalid_action_kind_refused": lambda payload, _: payload.update(
            action_kind=17
        ),
        "invalid_operation_id_refused": lambda payload, _: payload.update(
            operation_id=17
        ),
        "malformed_before_state_refused": lambda payload, _: payload.update(
            before_state="[]"
        ),
        "malformed_after_state_refused": lambda payload, _: payload.update(
            after_state="[]"
        ),
        "malformed_registered_at_refused": lambda payload, _: payload.update(
            registered_at="2026-01-15T12:00:00"
        ),
    }
    for case, mutation in attacks.items():
        fixture = Fixture(base / case)
        relations._mutate_action(fixture.root, mutation)  # noqa: SLF001
        facts[case] = _refused(fixture.root, base / f"{case}.duckdb")

    fixture = Fixture(base / "internal-valid")
    RecoveryJournal(fixture.root).record(
        recovery_run_id="run-internal",
        object_type="STAGING_ARTIFACT",
        object_id="staging-1",
        problem="UNCOMMITTED_STAGING",
        resolution="quarantined",
    )
    facts["internal_object_type_with_null_mapping_accepted"] = _accepted(
        fixture.root, base / "internal-valid.duckdb"
    )
    return facts


def build_i10r2_recovery_envelope_matrix() -> dict[str, Any]:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        facts = _measured_recovery_envelope(Path(tmp))
    names = [
        "valid_recovery_action_accepted",
        "wrong_record_type_refused",
        "missing_record_type_refused",
        "storage_mapping_contradiction_refused",
        "invalid_action_kind_refused",
        "invalid_operation_id_refused",
        "malformed_before_state_refused",
        "malformed_after_state_refused",
        "malformed_registered_at_refused",
    ]
    rows = [_case(name, [name], **facts) for name in names]
    rows.append(
        _case(
            "counterfactual_accept_wrong_recovery_record_type",
            ["wrong_record_type_refused"],
            wrong_record_type_refused=False,
        )
    )
    return _matrix("I10R2_RECOVERY_ENVELOPE", rows)


def _historical_hashes_unchanged(names: dict[str, str]) -> bool:
    return all(
        (EVIDENCE_DIR / name).is_file()
        and hashlib.sha256((EVIDENCE_DIR / name).read_bytes()).hexdigest() == digest
        for name, digest in names.items()
    )


def _ledger_current_state_parity() -> bool:
    text = LEDGER.read_text(encoding="utf-8")
    current = text.split("## Current state", 1)[1].split(
        "## Append-only SENSOR-B4-I10R1 / I10R2 checkpoint history", 1
    )[0]
    required = (
        "Current checkpoint | SENSOR-B4-I10R2",
        "PASS_SENSOR_B4_I10_DUCKDB_DISCOVERY_SEALED=OPERATOR_HOLD",
        "PASS_SENSOR_B4_I10R1_SCHEMA_EVIDENCE_DISCOVERY_SEALED=OPERATOR_HOLD",
        "PASS_SENSOR_B4_I10R2_RELATION_GOVERNANCE_PARITY_SEALED=PENDING_OPERATOR_REVIEW",
        "G4-09_CATALOG_REBUILD_GATE=IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW",
        "next_checkpoint_authorized=FALSE",
        "recommended_next=OPERATOR REVIEW OF COMPLETE I10 -> I10R1 -> I10R2 CHAIN",
        "I11+ unauthorized; research frozen",
    )
    return all(item in current for item in required) and (
        "recommended_next=OPERATOR REVIEW OF SENSOR-B4-I10;" not in current
    )


def _measured_parity(base: Path) -> tuple[dict[str, Any], dict[str, int]]:
    fixture = Fixture(base / "parity")
    calls = {"verify_blob": 0, "decode_stats": 0}
    original_verify = LocalBlobStore.verify_blob
    original_decode = LocalBlobStore._decode_stats

    def spy_verify(self: LocalBlobStore, *args: Any, **kwargs: Any) -> Any:
        calls["verify_blob"] += 1
        return original_verify(self, *args, **kwargs)

    def spy_decode(self: LocalBlobStore, *args: Any, **kwargs: Any) -> Any:
        calls["decode_stats"] += 1
        return original_decode(self, *args, **kwargs)

    LocalBlobStore.verify_blob = spy_verify  # type: ignore[method-assign]
    LocalBlobStore._decode_stats = spy_decode  # type: ignore[method-assign]
    try:
        receipt = rebuild_duckdb_catalog(fixture.root, base / "parity.duckdb")
    finally:
        LocalBlobStore.verify_blob = original_verify  # type: ignore[method-assign]
        LocalBlobStore._decode_stats = original_decode  # type: ignore[method-assign]

    con = duckdb.connect(str(base / "parity.duckdb"), read_only=True)
    try:
        actual_counts = {
            view: con.execute(f"SELECT count(*) FROM {view}").fetchone()[0]
            for view in VIEW_NAMES
        }
        actual_schemas = {
            view: tuple(
                (row[1], row[2])
                for row in con.execute(f"PRAGMA table_info('{view}')").fetchall()
            )
            for view in VIEW_NAMES
        }
        metadata = con.execute(
            "SELECT schema_version, data_root_role FROM catalog_metadata"
        ).fetchall()
    finally:
        con.close()
    return (
        {
            "actual_counts_equal_receipt_counts": all(
                actual_counts[view] == receipt.view_row_counts[view]
                for view in VIEW_NAMES
            ),
            "actual_schemas_equal_view_schemas": all(
                actual_schemas[view] == VIEW_SCHEMAS[view] for view in VIEW_NAMES
            ),
            "metadata_stamp_exact": metadata
            == [(CATALOG_SCHEMA_VERSION, CATALOG_ROLE)],
            "default_rebuild_zero_t0a_verify_decode_calls": calls
            == {"verify_blob": 0, "decode_stats": 0},
            "historical_i10_unchanged": _historical_hashes_unchanged(HISTORICAL_I10),
            "historical_i10r1_unchanged": _historical_hashes_unchanged(
                HISTORICAL_I10R1
            ),
            "implementation_ledger_current_state_parity": _ledger_current_state_parity(),
        },
        actual_counts,
    )


def build_i10r2_measurement_parity_matrix() -> dict[str, Any]:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        facts, actual_counts = _measured_parity(Path(tmp))
    rows = [_case(name, [name], **facts) for name in facts]
    rows.append(
        _case(
            "counterfactual_claim_count_parity_without_measurement",
            ["actual_counts_equal_receipt_counts"],
            actual_counts_equal_receipt_counts=False,
        )
    )
    return _matrix(
        "I10R2_MEASUREMENT_PARITY",
        rows,
        measured_view_row_counts=actual_counts,
        receipt_view_names=list(VIEW_NAMES),
    )


def build_i10r2_summary() -> dict[str, Any]:
    return {
        "checkpoint": "SENSOR-B4-I10R2",
        "api": "crypto_sensor_fabric.storage.duckdb_catalog.rebuild_duckdb_catalog",
        "catalog_role": CATALOG_ROLE,
        "schema_version": CATALOG_SCHEMA_VERSION,
        "lineage_law": (
            "metadata-only frozen I05 model, manifest/context/artifact binding, "
            "ordered source parity, durable blob/acquisition linkage, usable provenance, "
            "and metadata identity/granularity agreement"
        ),
        "t0a_payload_rescan": False,
        "matrices": {
            "lineage_binding_rows": 10,
            "recovery_envelope_rows": 10,
            "measurement_parity_rows": 9,
        },
        "measured_evidence": (
            "Every non-counterfactual evidence predicate is mechanically observed from "
            "executed production behavior; deliberate counterfactual predicates are "
            "explicitly synthetic and must evaluate FAIL."
        ),
        "historical_evidence": "I10 and I10R1 preserved byte-for-byte; never rewritten",
        "governance": {
            "PASS_SENSOR_B4_I10_DUCKDB_DISCOVERY_SEALED": "OPERATOR_HOLD",
            "PASS_SENSOR_B4_I10R1_SCHEMA_EVIDENCE_DISCOVERY_SEALED": "OPERATOR_HOLD",
            "PASS_SENSOR_B4_I10R2_RELATION_GOVERNANCE_PARITY_SEALED": "PENDING_OPERATOR_REVIEW",
            "G4-09_CATALOG_REBUILD_GATE": "IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW",
            "next_checkpoint_authorized": False,
            "recommended_next": "OPERATOR REVIEW OF COMPLETE I10 -> I10R1 -> I10R2 CHAIN",
            "I11": "UNAUTHORIZED",
            "I12_plus": "UNAUTHORIZED",
            "research": "FROZEN",
        },
    }


I10R2_BUILDERS = {
    "BLOC_04_I10R2_LINEAGE_BINDING_MATRIX.json": build_i10r2_lineage_binding_matrix,
    "BLOC_04_I10R2_RECOVERY_ENVELOPE_MATRIX.json": build_i10r2_recovery_envelope_matrix,
    "BLOC_04_I10R2_MEASUREMENT_PARITY_MATRIX.json": build_i10r2_measurement_parity_matrix,
    "BLOC_04_I10R2_RELATION_GOVERNANCE_MICROSEAL.json": build_i10r2_summary,
}


def test_i10r2_evidence_is_measured_and_committed() -> None:
    update = os.getenv("UPDATE_I10R2_EVIDENCE") == "1"
    for name, builder in I10R2_BUILDERS.items():
        payload = builder()
        for row in payload.get("rows", []):
            required = row["required_invariants"]
            assert row["result"] == (
                "OK" if all(row.get(item) is True for item in required) else "FAIL"
            )
            for item in required:
                assert isinstance(row.get(item), bool), (name, row["case"], item)
            if row["case"].startswith("counterfactual_"):
                assert row["result"] == "FAIL"
            else:
                assert row["result"] == "OK"
        expected = _stable(payload)
        committed = EVIDENCE_DIR / name
        if update:
            committed.write_bytes(expected)
        else:
            assert committed.exists(), f"missing committed R2 artifact: {name}"
            assert committed.read_bytes() == expected, f"R2 artifact drifted: {name}"


def test_r2_does_not_rewrite_historical_i10_or_i10r1_evidence() -> None:
    assert _historical_hashes_unchanged(HISTORICAL_I10)
    assert _historical_hashes_unchanged(HISTORICAL_I10R1)
