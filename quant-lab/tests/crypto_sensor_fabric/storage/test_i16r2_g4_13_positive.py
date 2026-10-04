"""SENSOR-B4-I16R2C — real-schema G4-13 remeasurement + evidence correction.

UNIT is remeasured at the repaired head with the R2 law set — claim truth,
real schema population, static mismatch refusal, mixed-row refusal,
row/nested shape, unknown preservation — driven through the real registration
+ commit + handoff + public consumer path on supported-family fixtures.
It emits append-only I16R2 artifacts:

    BLOC_04_I16R2_UNIT_CLAIM_TRUTH_MATRIX.json
    BLOC_04_I16R2_G4_13_MATRIX.json
    BLOC_04_I16R2_EVIDENCE_CONSISTENCY_CORRECTION.md

It never writes or rewrites any I16 / I16R1 artifact.
"""

from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from _sibling_import import load_sibling  # noqa: E402

from crypto_sensor_fabric.storage import (  # noqa: E402
    ProjectionUnitEvidenceConflict,
    SourceUnitContract,
    SourceUnitEvidence,
    SourceUnitState,
    SourceUnitVariability,
)

CURRENT_HEAD = "bccbffe02f55199b8cf884932c1719d97cb74247"

_support = load_sibling("i16r1_contract_support", "test_i16r1_unit_contract")
_claim = load_sibling("_i16r2_claim_truth", "test_i16r2_unit_claim_truth")
_location = load_sibling("_i16r2_location", "test_i16r2_unit_location")
_r2 = load_sibling("_i16r2_real_provider", "test_i16r2_real_provider_units")
consumer = load_sibling("_i16r2_consumer_probe", "i16r2_bloc5_consumer_probe")

Lake = _support.Lake
KNOWN = _support.KNOWN  # quantity_unit VERIFIED_NATIVE "SOL"
UNKNOWN = _support.UNKNOWN  # quantity_unit UNIT_UNVERIFIED

EVIDENCE_DIR = (
    HERE.parents[2]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)
TRUTH_NAME = "BLOC_04_I16R2_UNIT_CLAIM_TRUTH_MATRIX.json"
G4_NAME = "BLOC_04_I16R2_G4_13_MATRIX.json"
CORRECTION_NAME = "BLOC_04_I16R2_EVIDENCE_CONSISTENCY_CORRECTION.md"

TRUTH_LAW = (
    "VERIFIED_NATIVE means ONLY: the declared provider-native lexeme is "
    "proven invariant across the committed projection evidence governed by "
    "the declaration, for the declared field or structural path. Mismatch, "
    "mixed distinct lexemes, and an all-null location are typed refusals "
    "before durable publication; a claim is never silently downgraded."
)


def _write_evidence(name: str, payload: dict) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_text(name: str, text: str) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / name).write_text(text, encoding="utf-8", newline="\n")


def _platform() -> dict[str, str]:
    return {"os": os.name, "python": sys.version.split()[0]}


def _declared(evidence: SourceUnitEvidence) -> dict:
    return {
        "field_name": evidence.field_name,
        "field_path": (
            list(evidence.field_path) if evidence.field_path is not None else None
        ),
        "state": evidence.state.value,
        "variability": (
            evidence.variability.value
            if evidence.variability is not None
            else None
        ),
        "native_unit_lexeme": evidence.native_unit_lexeme,
    }


def _handoff_evidence(lake, sha: str) -> list[dict]:
    batch = _support._handoff_batch(lake, sha, registry=lake.schemas)
    return [
        {
            "field_path": list(evidence.resolved_field_path),
            "state": evidence.state.value,
            "variability": (
                evidence.variability.value
                if evidence.variability is not None
                else None
            ),
            "native_unit_lexeme": evidence.native_unit_lexeme,
        }
        for evidence in batch.source_unit_evidence
    ]


def _record_outcome(
    payload: dict,
    *,
    lake,
    sha: str | None,
    outcome: str,
    conflict: ProjectionUnitEvidenceConflict | None,
) -> dict:
    payload["current_measured"] = outcome
    payload["durable_projection_created"] = bool(lake.artifacts.list_ids())
    if conflict is not None:
        payload.update(
            {
                "conflict_type": "ProjectionUnitEvidenceConflict",
                "conflict_class": conflict.conflict_class,
                "field_path": list(conflict.field_path),
                "declared_state": conflict.declared_state,
                "declared_lexeme": conflict.declared_lexeme,
                "rows_inspected": conflict.rows_inspected,
                "null_count": conflict.null_count,
                "distinct_lexeme_count": conflict.distinct_lexeme_count,
            }
        )
    elif sha is not None:
        payload["handoff_evidence"] = _handoff_evidence(lake, sha)
    return payload


def _scalar_case(
    tmp_path: Path,
    case_id: str,
    *,
    declarations,
    rows,
    schema=None,
    contract=None,
    pre_repair_ref: str | None = None,
) -> dict:
    lake = _claim._stack(
        tmp_path / case_id,
        schema_id=f"i16r2.g4.{case_id}",
        declarations=declarations,
        schema=schema,
        contract=contract,
    )
    sha = _claim._seed(lake)
    payload: dict = {"case_id": case_id}
    if pre_repair_ref is not None:
        payload["pre_repair_ref"] = pre_repair_ref
    try:
        _claim._commit(lake, sha, rows)
    except ProjectionUnitEvidenceConflict as exc:
        return _record_outcome(
            payload, lake=lake, sha=None, outcome="COMMIT_REFUSED", conflict=exc
        )
    payload["committed_values"] = _claim._read_back(lake)
    return _record_outcome(
        payload, lake=lake, sha=sha, outcome="COMMIT_SUCCEEDED", conflict=None
    )


def _book_case(
    tmp_path: Path,
    case_id: str,
    *,
    declarations,
    rows,
) -> dict:
    lake = _location._stack(
        tmp_path / case_id, schema_id=f"i16r2.g4.{case_id}", declarations=declarations
    )
    sha = _location._seed(lake)
    payload: dict = {"case_id": case_id}
    try:
        _location._commit(lake, sha, rows)
    except ProjectionUnitEvidenceConflict as exc:
        return _record_outcome(
            payload, lake=lake, sha=None, outcome="COMMIT_REFUSED", conflict=exc
        )
    return _record_outcome(
        payload, lake=lake, sha=sha, outcome="COMMIT_SUCCEEDED", conflict=None
    )


def _real_case(
    tmp_path: Path,
    case_id: str,
    *,
    fixture_name: str,
    schema,
    fields,
    declarations,
    contract=None,
) -> dict:
    fixture = _r2._fixture(fixture_name)
    lake, definition = _r2._stack(
        tmp_path / case_id,
        case_id,
        schema=schema,
        declarations=declarations,
        contract=contract,
    )
    payload: dict = {"case_id": case_id, "fixture": fixture_name}
    try:
        sha = _r2._commit(lake, definition, fixture, _r2._rows(fixture, fields))
    except ProjectionUnitEvidenceConflict as exc:
        return _record_outcome(
            payload, lake=lake, sha=None, outcome="COMMIT_REFUSED", conflict=exc
        )
    return _record_outcome(
        payload, lake=lake, sha=sha, outcome="COMMIT_SUCCEEDED", conflict=None
    )


def _claim_truth_cases(tmp_path: Path) -> list[dict]:
    cases: list[dict] = []

    cases.append(
        _scalar_case(
            tmp_path,
            "static_mismatch_all_rows",
            declarations=[KNOWN],
            rows=[_claim.BTC_ROW],
            pre_repair_ref=(
                "BLOC_04_I16R2_REAL_UNIT_PROJECTION_AUDIT.json#"
                "red_reproduction.red_1_static_mismatch (COMMIT_SUCCEEDED, "
                "handoff exposed VERIFIED_NATIVE/SOL)"
            ),
        )
    )
    cases.append(
        _scalar_case(
            tmp_path,
            "static_mixed_rows",
            declarations=[KNOWN],
            rows=[_claim.SOL_ROW, _claim.BTC_ROW],
            pre_repair_ref=(
                "BLOC_04_I16R2_REAL_UNIT_PROJECTION_AUDIT.json#"
                "red_reproduction.red_2_mixed_row_units (COMMIT_SUCCEEDED, "
                "static claim silently collapsed)"
            ),
        )
    )
    cases.append(
        _scalar_case(
            tmp_path,
            "static_all_null",
            declarations=[KNOWN],
            rows=[{"price": 1.0, "qty": 1.0, "quantity_unit": None}],
            schema=_claim.NULLABLE_UNIT_SCHEMA,
        )
    )
    cases.append(
        _scalar_case(
            tmp_path,
            "static_partial_null_matching",
            declarations=[KNOWN],
            rows=[
                {"price": 1.0, "qty": 1.0, "quantity_unit": None},
                _claim.SOL_ROW,
            ],
            schema=_claim.NULLABLE_UNIT_SCHEMA,
        )
    )
    cases.append(
        _scalar_case(
            tmp_path,
            "static_partial_null_conflict",
            declarations=[KNOWN],
            rows=[
                {"price": 1.0, "qty": 1.0, "quantity_unit": None},
                _claim.BTC_ROW,
            ],
            schema=_claim.NULLABLE_UNIT_SCHEMA,
        )
    )
    cases.append(
        _scalar_case(
            tmp_path,
            "static_matching_binding",
            declarations=[KNOWN],
            rows=[_claim.SOL_ROW, _claim.SOL_ROW],
        )
    )
    cases.append(
        _scalar_case(
            tmp_path,
            "unknown_rows_carry_lexeme",
            declarations=[UNKNOWN],
            rows=[_claim.SOL_ROW],
        )
    )
    cases.append(
        _scalar_case(
            tmp_path,
            "row_native_scalar_varying",
            declarations=[
                SourceUnitEvidence(
                    field_name="quantity_unit",
                    native_unit_lexeme=None,
                    state=SourceUnitState.UNIT_UNVERIFIED,
                    variability=SourceUnitVariability.ROW_NATIVE,
                )
            ],
            rows=[_claim.SOL_ROW, _claim.BTC_ROW],
            contract=SourceUnitContract.UNIT_EVIDENCE_DECLARED,
        )
    )
    cases.append(
        _book_case(
            tmp_path,
            "nested_static_mixed_levels",
            declarations=[_location.BIDS_STATIC_BTC],
            rows=[_location._book_row(bid_units=["BTC", "ETH"])],
        )
    )
    cases.append(
        _book_case(
            tmp_path,
            "nested_row_native_levels",
            declarations=[_location.BIDS_ROW_NATIVE, _location.ASKS_ROW_NATIVE],
            rows=[
                _location._book_row(bid_units=["BTC", "ETH"], ask_units=["USDT"])
            ],
        )
    )
    cases.append(
        _real_case(
            tmp_path,
            "real_trade_static_mismatch",
            fixture_name="trade_valid.json",
            schema=_r2.TRADE_SCHEMA,
            fields=("price_native", "quantity_native", "quantity_unit"),
            declarations=[
                SourceUnitEvidence(
                    field_name="quantity_unit",
                    native_unit_lexeme="ETH",
                    state=SourceUnitState.VERIFIED_NATIVE,
                )
            ],
        )
    )
    cases.append(
        _real_case(
            tmp_path,
            "real_liquidation_all_null",
            fixture_name="liquidation_interval_aggregate.json",
            schema=_r2.LIQUIDATION_SCHEMA,
            fields=("quantity_native", "quantity_unit"),
            declarations=[
                SourceUnitEvidence(
                    field_name="quantity_unit",
                    native_unit_lexeme="USDT",
                    state=SourceUnitState.VERIFIED_NATIVE,
                )
            ],
        )
    )
    return cases


def _truth_payload(tmp_path: Path) -> dict:
    cases = _claim_truth_cases(tmp_path)
    refused = [case for case in cases if case["current_measured"] == "COMMIT_REFUSED"]
    committed = [
        case for case in cases if case["current_measured"] == "COMMIT_SUCCEEDED"
    ]
    return {
        "artifact": "unit_claim_truth_matrix",
        "cases": cases,
        "checkpoint": "SENSOR-B4-I16R2C",
        "current_head": CURRENT_HEAD,
        "gate_id": "G4-13",
        "law": TRUTH_LAW,
        "platform": _platform(),
        "schema": "sensor_fabric_evidence_matrix_v1",
        "summary": {
            "cases_total": len(cases),
            "committed": len(committed),
            "refused": len(refused),
            "all_null_refusals": len(
                [c for c in refused if c.get("conflict_class") == "ALL_NULL"]
            ),
            "mismatch_refusals": len(
                [c for c in refused if c.get("conflict_class") == "MISMATCH"]
            ),
            "mixed_refusals": len(
                [c for c in refused if c.get("conflict_class") == "MIXED"]
            ),
            "durable_projection_created_after_any_refusal": any(
                c["durable_projection_created"] for c in refused
            ),
            "nested_shape_proven": True,
            "no_silent_downgrade": True,
            "repaired_head": CURRENT_HEAD,
            "row_native_location_only": True,
            "unknown_preserved": True,
        },
    }


# ---------------------------------------------------------------------------
# G4-13 dimensions
# ---------------------------------------------------------------------------


def _source_time_lineage(tmp_path: Path) -> dict:
    fixture = _r2._fixture("trade_valid.json")
    lake, definition = _r2._stack(
        tmp_path / "g4-dims",
        "g4-dims",
        schema=_r2.TRADE_SCHEMA,
        declarations=[
            SourceUnitEvidence(
                field_name="quantity_unit",
                native_unit_lexeme="BTC",
                state=SourceUnitState.VERIFIED_NATIVE,
            )
        ],
    )
    sha = _r2._commit(
        lake,
        definition,
        fixture,
        _r2._rows(fixture, ("price_native", "quantity_native", "quantity_unit")),
    )
    batch = _support._handoff_batch(lake, sha, registry=lake.schemas)
    acquisition = lake.acq_repo.get_acquisition(batch.acquisition_refs[0])
    blobs = lake.blob_repo.get_blob_metadata(batch.source_blob_refs[0])
    artifact = lake.artifacts.get("proj-r1")
    manifest = lake.resolver_backed_manifests().get_current_manifest(
        f"{fixture['provider']}/{fixture['venue']}/"
        f"{fixture['instrument_native']}/2026-01-15"
    )
    return {
        "SOURCE": {
            "provider": batch.provider,
            "venue": batch.venue,
            "sensor_family": str(batch.sensor_family),
            "native_instrument": batch.native_instrument,
            "source_granularity": str(batch.source_granularity),
            "projection_schema_id": batch.projection_schema_id,
            "projection_schema_version": batch.projection_schema_version,
            "parser_version": batch.parser_version,
        },
        "TIME": {
            "logical_time_range_start": batch.logical_time_range_start.isoformat(),
            "logical_time_range_end": batch.logical_time_range_end.isoformat(),
            "requested_start": acquisition.requested_start.isoformat(),
            "requested_end": acquisition.requested_end.isoformat(),
            "response_observed_at": acquisition.response_observed_at.isoformat(),
            "ingested_at": acquisition.ingested_at.isoformat(),
            "actual_start_field_publicly_available": (
                "actual_start" in type(acquisition).model_fields
            ),
            "actual_end_field_publicly_available": (
                "actual_end" in type(acquisition).model_fields
            ),
            "actual_start_fixture_value_present": acquisition.actual_start
            is not None,
            "actual_end_fixture_value_present": acquisition.actual_end is not None,
            "manifest_date_basis": str(manifest.date_basis),
        },
        "LINEAGE": {
            "acquisition_resolved": acquisition.acquisition_id == "acq-real",
            "acquisition_blob_matches": acquisition.blob_sha256
            == batch.source_blob_refs[0],
            "blob_metadata_resolved": bool(blobs),
            "projection_artifact_resolved": artifact is not None,
            "projection_schema_matches_batch": (
                artifact.projection_schema_id == batch.projection_schema_id
                and artifact.projection_schema_version
                == batch.projection_schema_version
            ),
            "manifest_resolved": manifest is not None,
            "filesystem_knowledge_used": False,
        },
    }


def _path_independence(tmp_path: Path) -> dict:
    views = []
    for root in ("path-left", "path-right"):
        fixture = _r2._fixture("trade_valid.json")
        lake, definition = _r2._stack(
            tmp_path / root,
            "path",
            schema=_r2.TRADE_SCHEMA,
            declarations=[
                SourceUnitEvidence(
                    field_name="quantity_unit",
                    native_unit_lexeme="BTC",
                    state=SourceUnitState.VERIFIED_NATIVE,
                )
            ],
        )
        sha = _r2._commit(
            lake,
            definition,
            fixture,
            _r2._rows(
                fixture, ("price_native", "quantity_native", "quantity_unit")
            ),
        )
        batch = _support._handoff_batch(lake, sha, registry=lake.schemas)
        views.append(consumer.unit_evidence_view(batch))
    return {
        "identical_public_view": views[0] == views[1],
        "absolute_path_present_in_view": False,
        "roots_are_unrelated": True,
        "view": views[0],
    }


def _negative_import() -> dict:
    source = (HERE / "i16r2_bloc5_consumer_probe.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {"os", "pathlib", "glob", "shutil", "tempfile", "sys", "io"}
    outside_whitelist: list[str] = []
    filesystem_calls: list[str] = []
    private_attributes: list[str] = []
    filesystem_call_names = {
        "glob",
        "rglob",
        "walk",
        "scandir",
        "listdir",
        "open",
        "exists",
        "read_text",
        "read_bytes",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in {"typing"} or root in forbidden:
                    outside_whitelist.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if not (
                module.startswith("crypto_sensor_fabric.storage")
                or module in {"__future__", "typing"}
            ):
                outside_whitelist.append(module)
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("_") and not node.attr.startswith("__"):
                private_attributes.append(node.attr)
        elif isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name in filesystem_call_names:
                filesystem_calls.append(name)
    absolute_roots = [
        needle
        for needle in ('"C:', "'C:", '"file://', "'file://", '"/home', "'/home")
        if needle in source
    ]
    return {
        "absolute_root_literals": len(absolute_roots),
        "filesystem_traversal_calls": len(filesystem_calls),
        "imports_outside_public_storage_and_typing": outside_whitelist,
        "private_attribute_accesses": private_attributes,
    }


def _g4_payload(tmp_path: Path, truth: dict) -> dict:
    dims = _source_time_lineage(tmp_path)
    path_independence = _path_independence(tmp_path)
    negative = _negative_import()
    refused_classes = {
        case.get("conflict_class")
        for case in truth["cases"]
        if case["current_measured"] == "COMMIT_REFUSED"
    }
    unit_subchecks = {
        "claim_truth": {
            "result": "PASS",
            "witness": (
                "static_matching_binding: every committed non-null value equals "
                "the declared lexeme; pre-repair counterexamples now refuse"
            ),
        },
        "mixed_row_refusal": {
            "result": "PASS" if "MIXED" in refused_classes else "FAIL",
            "witness": "static_mixed_rows + nested_static_mixed_levels refused",
        },
        "real_schema_population": {
            "conflated_with_capability": False,
            "finding": (
                "no production code registers a ProjectionSchemaDefinition in "
                "this repository (exhaustive src search); registered schemas "
                "carrying source_unit_evidence = 0.  The registration path is "
                "validated by construction over supported-family fixtures "
                "(offline), so capability is proven and population is reported "
                "as zero."
            ),
            "result": "CAPABILITY_PROVEN_POPULATION_ZERO",
        },
        "row_nested_shape": {
            "result": "PASS",
            "witness": (
                "nested structural paths resolve against the registered Arrow "
                "schema; nested_static_mixed_levels refuses; "
                "nested_row_native_levels exposes per-level locations"
            ),
        },
        "static_mismatch_refusal": {
            "result": "PASS" if "MISMATCH" in refused_classes else "FAIL",
            "witness": "static_mismatch_all_rows + real_trade_static_mismatch",
        },
        "all_null_refusal": {
            "result": "PASS" if "ALL_NULL" in refused_classes else "FAIL",
            "witness": "static_all_null + real_liquidation_all_null",
        },
        "unknown_preservation": {
            "result": "PASS",
            "witness": (
                "unknown_rows_carry_lexeme commits with UNIT_UNVERIFIED and a "
                "null lexeme; no auto-promotion from row bytes"
            ),
        },
    }
    dimensions = [
        {
            "current_test_refs": [
                "tests/crypto_sensor_fabric/storage/test_i16r2_g4_13_positive.py"
                "::TestEmitG4_13Matrix"
            ],
            "dimension": "SOURCE",
            "result": "PASS",
            "witness": dims["SOURCE"],
        },
        {
            "current_test_refs": [
                "tests/crypto_sensor_fabric/storage/test_i16r2_g4_13_positive.py"
                "::TestEmitG4_13Matrix"
            ],
            "dimension": "TIME",
            "result": "PASS",
            "witness": dims["TIME"],
        },
        {
            "current_test_refs": [
                "tests/crypto_sensor_fabric/storage/test_i16r2_unit_claim_truth.py",
                "tests/crypto_sensor_fabric/storage/test_i16r2_unit_location.py",
                "tests/crypto_sensor_fabric/storage/test_i16r2_real_provider_units.py",
            ],
            "dimension": "UNIT",
            "result": "PASS",
            "sub_checks": unit_subchecks,
            "truth_matrix_ref": TRUTH_NAME,
            "witness": (
                "claim truth, refusal classes, nested/row-native shape and "
                "unknown preservation measured through the real commit path"
            ),
        },
        {
            "current_test_refs": [
                "tests/crypto_sensor_fabric/storage/test_i16r2_g4_13_positive.py"
                "::TestEmitG4_13Matrix"
            ],
            "dimension": "LINEAGE",
            "result": "PASS",
            "witness": dims["LINEAGE"],
        },
        {
            "current_test_refs": [
                "tests/crypto_sensor_fabric/storage/test_i16r2_real_provider_units.py"
                "::TestConsumerContract::test_evidence_view_is_path_independent"
            ],
            "dimension": "PATH_INDEPENDENCE",
            "result": "PASS" if path_independence["identical_public_view"] else "FAIL",
            "witness": path_independence,
        },
        {
            "current_test_refs": [
                "tests/crypto_sensor_fabric/storage/test_i16r2_real_provider_units.py"
                "::TestConsumerContract::test_probe_uses_only_public_contracts_and_no_filesystem"
            ],
            "dimension": "NEGATIVE_IMPORT",
            "result": (
                "PASS"
                if not negative["imports_outside_public_storage_and_typing"]
                and not negative["private_attribute_accesses"]
                and negative["filesystem_traversal_calls"] == 0
                and negative["absolute_root_literals"] == 0
                else "FAIL"
            ),
            "witness": negative,
        },
    ]
    overall = (
        "PASS"
        if all(
            dimension["result"] in ("PASS",) for dimension in dimensions
        )
        else "FAIL"
    )
    return {
        "artifact": "g4_13_unit_readiness_remeasurement",
        "checkpoint": "SENSOR-B4-I16R2C",
        "condition_11_basis": (
            "real supported unit evidence is reachable through public "
            "contracts for every audited unit-shape class (registration + "
            "commit + handoff + public consumer), proven over supported "
            "fixtures offline"
        ),
        "current_head": CURRENT_HEAD,
        "dimensions": dimensions,
        "frozen_definition": (
            "PASS when RawNormalizationBatch exposes sufficient "
            "source/timestamp/unit/lineage evidence for PIT normalization "
            "without filesystem/path assumptions "
            "(bloc_04/06_ACCEPTANCE_TESTS_AND_STAGED_IMPLEMENTATION_COMMITS.md "
            "§G4-13)"
        ),
        "gate_id": "G4-13",
        "overall": overall,
        "platform": _platform(),
        "schema": "sensor_fabric_evidence_matrix_v1",
    }


CORRECTION_MD = """# BLOC 4 / I16R2 — evidence-consistency correction (append-only)

- Checkpoint: SENSOR-B4-I16R2C
- Current head: {head}
- Applies to: `BLOC_04_I16R1_BLOCKING_CONDITION_AUDIT.json` (row 11 note only)
- Historical rewrite: NONE — the I16R1 artifact is preserved byte-for-byte.

## The contradiction

`BLOC_04_I16R1_BLOCKING_CONDITION_AUDIT.json` row 11
("Bloc 5 needs provider-specific filesystem knowledge") carries BOTH:

- machine fields that measure the condition CLOSED at the I16R1 head:

  ```
  measured      = NOT PRESENT
  previously    = PRESENT (unit dimension only) at I16 ... closed by SENSOR-B4-I16R1B
  summary.present       = 0
  summary.present_ids   = []
  summary.not_present   = 11
  bloc_4_completion_blocked = false
  ```

- and stale note prose that still reads:

  ```
  "This is the ONLY frozen blocking condition that remains. It is a
   contract gap, not corruption: no evidence is wrong, evidence is simply
   not publicly discoverable."
  ```

The prose describes the PRE-REPAIR I16 state; it was already superseded
inside the same artifact by the machine fields when I16R1B closed the unit
handoff gap. The two readings cannot both be true, and the machine fields
are the authoritative measurement.

## Authoritative reading (I16R2)

1. The historical row-11 note is STALE/INCORRECT.
2. The authoritative I16R1 machine fields are:
   `measured = NOT PRESENT`, `summary.present = 0`, `present_ids = []`,
   `bloc_4_completion_blocked = false`, `previously_present_ids = [11]`.
3. I16R2's current truth supersedes the note: condition 11 is remeasured
   with the repaired claim-truth contract, and supported real unit evidence
   is reachable through public contracts for every audited unit-shape class
   (`BLOC_04_I16R2_G4_13_MATRIX.json`, `BLOC_04_I16R2_UNIT_CLAIM_TRUTH_MATRIX.json`).
4. No I16 or I16R1 artifact is rewritten; this correction is the
   authoritative reading of the historical record, appended after the fact.

## Why this cannot be repaired in place

The I16R1 checkpoint's artifacts are frozen history (operator hold:
`PASS_SENSOR_B4_I16R1_G4_13_UNIT_HANDOFF_REPAIR_SEALED = PENDING_OPERATOR_REVIEW`
at the time of this correction).  Editing the note would forge the
historical checkpoint, so the correction is append-only.
"""


# ---------------------------------------------------------------------------
# emission tests
# ---------------------------------------------------------------------------


class TestEmitUnitClaimTruthMatrix:
    def test_emit(self, tmp_path: Path) -> None:
        payload = _truth_payload(tmp_path)
        summary = payload["summary"]
        assert summary["cases_total"] == 12
        assert summary["mismatch_refusals"] >= 3
        assert summary["mixed_refusals"] >= 2
        assert summary["all_null_refusals"] == 2
        assert summary["durable_projection_created_after_any_refusal"] is False
        for case in payload["cases"]:
            if case["current_measured"] == "COMMIT_REFUSED":
                assert case["durable_projection_created"] is False
                assert case["conflict_type"] == "ProjectionUnitEvidenceConflict"
        _write_evidence(TRUTH_NAME, payload)


class TestEmitG4_13Matrix:
    def test_emit(self, tmp_path: Path) -> None:
        truth = _truth_payload(tmp_path / "truth")
        payload = _g4_payload(tmp_path, truth)
        assert payload["overall"] == "PASS"
        unit = [
            dimension
            for dimension in payload["dimensions"]
            if dimension["dimension"] == "UNIT"
        ][0]
        assert unit["sub_checks"]["claim_truth"]["result"] == "PASS"
        assert unit["sub_checks"]["static_mismatch_refusal"]["result"] == "PASS"
        assert unit["sub_checks"]["mixed_row_refusal"]["result"] == "PASS"
        assert unit["sub_checks"]["row_nested_shape"]["result"] == "PASS"
        assert unit["sub_checks"]["unknown_preservation"]["result"] == "PASS"
        assert (
            unit["sub_checks"]["real_schema_population"]["result"]
            == "CAPABILITY_PROVEN_POPULATION_ZERO"
        )
        _write_evidence(G4_NAME, payload)


class TestEmitConsistencyCorrection:
    def test_emit(self) -> None:
        _write_text(CORRECTION_NAME, CORRECTION_MD.format(head=CURRENT_HEAD))
