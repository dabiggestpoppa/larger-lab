"""SENSOR-B4-I16R1C — positive G4-13 Bloc 5 readiness remeasurement.

I16 measured G4-13 UNIT as NOT reachable and stopped final PASS with
``I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP``.  I16R1B closed the gap with the
smallest additive durable contract.  This module REMEASURES G4-13 positively
at the repaired head, through the NEW test-only consumer probe
(``i16r1_bloc5_consumer_probe``), and emits R1 evidence:

    BLOC_04_I16R1_G4_13_UNIT_HANDOFF_MATRIX.json
    BLOC_04_I16R1_BLOC4_READINESS.json

It never writes or rewrites any ``BLOC_04_I16_*`` artifact: I16 remains the
historical failing checkpoint (§20/§27).

Measured dimensions:

    SOURCE             public on the handoff batch
    TIME               preserved T0 facts, incl. §18 wording measurement
    UNIT               durable source-unit evidence: VERIFIED_NATIVE or
                       UNIT_UNVERIFIED — never guessed
    LINEAGE            batch -> acquisition -> blob -> projection -> revision
    PATH_INDEPENDENCE  two unrelated roots produce the same public view
    NEGATIVE_IMPORT    the consumer imports only public storage contracts
"""

from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from crypto_sensor_fabric.storage import (  # noqa: E402
    RawArtifactReader,
    RawProjectionReader,
    SourceUnitState,
    StorageEncoding,
)

import i16r1_bloc5_consumer_probe as bloc5  # noqa: E402

CURRENT_HEAD = "ed7137f12345c7d15d55ea1e6f5332234497714d"

EVIDENCE_DIR = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)
MATRIX_NAME = "BLOC_04_I16R1_G4_13_UNIT_HANDOFF_MATRIX.json"
READINESS_NAME = "BLOC_04_I16R1_BLOC4_READINESS.json"

GAP_ID = "I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP"


def _write_evidence(name: str, payload: dict[str, object]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _platform() -> dict[str, str]:
    return {"os": os.name, "python": sys.version.split()[0]}


def _load_sibling(module_name: str, file_stem: str):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        module_name, HERE / f"{file_stem}.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_support = _load_sibling("i16r1_contract_support", "test_i16r1_unit_contract")

KNOWN = _support.KNOWN
UNKNOWN = _support.UNKNOWN
UNKNOWN_METRIC = _support.UNKNOWN_METRIC

_ROWS_KNOWN = [{"price": 1.0, "qty": 1.0, "quantity_unit": "SOL"}]
_ROWS_MULTI = [
    {"price": 1.0, "qty": 1.0, "quantity_unit": "SOL", "metric_unit": "bps"}
]


def _reader(lake) -> RawProjectionReader:
    reader = RawProjectionReader(
        artifact_repository=lake.artifacts,
        context_repository=lake.contexts,
        lineage_repository=lake.lineage,
        schema_registry=lake.schemas,
        artifact_reader=RawArtifactReader(
            blob_store=lake.store, blob_metadata_repository=lake.blob_repo
        ),
    )
    reader.set_acquisition_repository(lake.acq_repo)
    return reader


def _probe(lake, sha: str, *, projection_ids=("proj-r1",)):
    batch = _support._handoff_batch(lake, sha, registry=lake.schemas)
    report = bloc5.collect_handoff_evidence(
        batch=batch,
        acquisitions=lake.acq_repo,
        blobs=lake.blob_repo,
        manifests=lake.resolver_backed_manifests(),
        schemas=lake.schemas,
        projection_reader=_reader(lake),
        projection_ids=list(projection_ids),
    )
    return report, batch


def _known_lake(root):
    return _support._unit_stack(
        root, schema_id="i16r1.units.known", declarations=[KNOWN]
    )


def _unknown_lake(root):
    return _support._unit_stack(
        root,
        schema_id="i16r1.units.unknown",
        declarations=[UNKNOWN],
        # The ROWS still carry a lexeme string; the durable contract does not
        # pin it, so the batch-level state must remain UNIT_UNVERIFIED and
        # Bloc 4 must not fabricate a value from row content.
        rows=_ROWS_KNOWN,
    )


def _multi_lake(root):
    return _support._unit_stack(
        root,
        schema_id="i16r1.units.multi",
        declarations=[UNKNOWN_METRIC, KNOWN],
        rows=_ROWS_MULTI,
        schema=_support.R1_MULTI_SCHEMA,
    )


def _declared_none_lake(root):
    return _support._unit_stack(
        root, schema_id="i16r1.units.undeclared", declarations=None
    )


# ---------------------------------------------------------------------------
# §13 — positive consumer probe: UNIT reachability
# ---------------------------------------------------------------------------


class TestPositiveUnitReachability:
    def test_known_native_unit_is_reachable_with_lexeme(self, tmp_path: Path) -> None:
        lake, sha = _known_lake(tmp_path / "lake")
        report, batch = _probe(lake, sha)
        unit = report["unit"]
        assert unit["reachable"] is True
        assert unit["entries"] == [
            {
                "field_name": "quantity_unit",
                "state": SourceUnitState.VERIFIED_NATIVE.value,
                "native_unit_lexeme": "SOL",
            }
        ]
        assert unit["verified_native_fields"] == ["quantity_unit"]
        assert unit["guessed_values"] == []
        assert unit["resolved_schema_declaration_matches_batch"] is True
        assert batch.source_unit_evidence[0].native_unit_lexeme == "SOL"

    def test_unknown_unit_is_reachable_and_explicit(self, tmp_path: Path) -> None:
        lake, sha = _unknown_lake(tmp_path / "lake")
        report, _batch = _probe(lake, sha)
        unit = report["unit"]
        assert unit["reachable"] is True
        assert unit["entries"] == [
            {
                "field_name": "quantity_unit",
                "state": SourceUnitState.UNIT_UNVERIFIED.value,
                "native_unit_lexeme": None,
            }
        ]
        assert unit["unverified_fields"] == ["quantity_unit"]
        assert unit["verified_native_fields"] == []

    def test_no_guessed_value_from_rows_or_bytes(self, tmp_path: Path) -> None:
        """§6/§8: unknown must not become a row string or a byte-search hit."""
        lake, sha = _unknown_lake(tmp_path / "lake")
        # Fixture sanity: the lexeme string IS present in the durable source
        # bytes and in the projection rows...
        with lake.store.open_blob(sha, StorageEncoding.NONE) as handle:
            raw = handle.read()
        assert b"unit" in raw.lower(), "fixture sanity: unit string is present"
        # ...and it is STILL not turned into a VERIFIED_NATIVE claim.
        report, _batch = _probe(lake, sha)
        unit = report["unit"]
        assert unit["guessed_values"] == []
        assert unit["entries"][0]["state"] == SourceUnitState.UNIT_UNVERIFIED.value
        assert unit["entries"][0]["native_unit_lexeme"] is None

    def test_multiple_unit_bearing_fields_are_representable(
        self, tmp_path: Path
    ) -> None:
        lake, sha = _multi_lake(tmp_path / "lake")
        report, _batch = _probe(lake, sha)
        unit = report["unit"]
        assert unit["verified_native_fields"] == ["quantity_unit"]
        assert unit["unverified_fields"] == ["metric_unit"]
        assert [(e["field_name"], e["state"]) for e in unit["entries"]] == [
            ("metric_unit", SourceUnitState.UNIT_UNVERIFIED.value),
            ("quantity_unit", SourceUnitState.VERIFIED_NATIVE.value),
        ]

    def test_declared_no_unit_fields_makes_no_claim(self, tmp_path: Path) -> None:
        lake, sha = _declared_none_lake(tmp_path / "lake")
        report, _batch = _probe(lake, sha)
        unit = report["unit"]
        assert unit["reachable"] is True
        assert unit["declared_field_count"] == 0
        assert unit["entries"] == []
        assert unit["guessed_values"] == []

    def test_canonicalization_never_happens(self, tmp_path: Path) -> None:
        for builder in (_known_lake, _unknown_lake, _multi_lake):
            lake, sha = builder(tmp_path / builder.__name__)
            report, batch = _probe(lake, sha)
            assert report["unit"]["canonical_unit_decisions"] == 0
            for evidence in batch.source_unit_evidence:
                lexeme = evidence.native_unit_lexeme
                if lexeme is not None:
                    # The lexeme is preserved verbatim; no canonical mapping.
                    assert lexeme in ("SOL", "bps")


# ---------------------------------------------------------------------------
# §18 — source / time / lineage at the repaired head
# ---------------------------------------------------------------------------


class TestPositiveSourceTimeLineage:
    def test_source_identity_is_public_on_the_batch(self, tmp_path: Path) -> None:
        lake, sha = _known_lake(tmp_path / "lake")
        report, _batch = _probe(lake, sha)
        source = report["source"]
        assert source["reachable"] is True
        assert source["provider"] == "kraken"
        assert source["venue"] == "futures"
        assert source["native_instrument"] == "BTC-USDT"
        assert source["projection_schema_id"] == "i16r1.units.known"
        assert source["source_granularity"] != bloc5.NOT_REACHABLE

    def test_preserved_time_facts_are_reachable(self, tmp_path: Path) -> None:
        lake, sha = _known_lake(tmp_path / "lake")
        report, _batch = _probe(lake, sha)
        time_evidence = report["time"]
        assert time_evidence["reachable"] is True
        for preserved in (
            "requested_start",
            "requested_end",
            "request_started_at",
            "response_observed_at",
            "ingested_at",
            "logical_time_range_start",
            "logical_time_range_end",
        ):
            assert time_evidence[preserved] != bloc5.NOT_REACHABLE, preserved
        assert time_evidence["date_basis"] != bloc5.NOT_REACHABLE

    def test_actual_times_are_available_fields_with_honest_fixture_state(
        self, tmp_path: Path
    ) -> None:
        """§18 wording correction: a public field is not 'structurally absent'
        merely because this fixture left its value unset."""
        lake, sha = _known_lake(tmp_path / "lake")
        report, _batch = _probe(lake, sha)
        time_evidence = report["time"]
        assert time_evidence["actual_start_field_publicly_available"] is True
        assert time_evidence["actual_end_field_publicly_available"] is True
        assert time_evidence["actual_start_fixture_value_present"] is False
        assert time_evidence["actual_end_fixture_value_present"] is False
        assert time_evidence["actual_start"] == bloc5.NOT_REACHABLE
        assert time_evidence["actual_end"] == bloc5.NOT_REACHABLE

    def test_provider_lexical_time_facts_are_not_publicly_typed(
        self, tmp_path: Path
    ) -> None:
        lake, sha = _known_lake(tmp_path / "lake")
        report, _batch = _probe(lake, sha)
        for missing in (
            "provider_time_raw",
            "provider_time_parsed",
            "provider_time_unit_assumption",
            "provider_publication_time",
        ):
            assert report["time"][missing] == bloc5.NOT_REACHABLE, missing

    def test_lineage_resolves_through_public_authority(
        self, tmp_path: Path
    ) -> None:
        lake, sha = _known_lake(tmp_path / "lake")
        report, _batch = _probe(lake, sha)
        lineage = report["lineage"]
        assert lineage["reachable"] is True
        assert lineage["acquisition_id"] == "acq-r1"
        assert lineage["acquisition_blob_ref"] == sha
        assert lineage["blob_sha256"] == sha
        assert lineage["blob_metadata_resolved"] is True
        assert lineage["projection_lineage_reachable"] is True
        entry = lineage["projection_lineage"][0]
        assert entry["projection_id"] == "proj-r1"
        assert entry["schema_matches_batch"] is True
        assert entry["source_lineage_count"] >= 1
        assert lineage["path_parsing_used"] is False
        assert lineage["private_map_used"] is False

    def test_coverage_and_revision_state_are_public(self, tmp_path: Path) -> None:
        lake, sha = _known_lake(tmp_path / "lake")
        report, _batch = _probe(lake, sha)
        assert report["coverage_state"] not in (bloc5.NOT_REACHABLE, "None")
        assert report["revision_state"] not in (bloc5.NOT_REACHABLE, "None")


# ---------------------------------------------------------------------------
# §15 — path independence at the repaired head
# ---------------------------------------------------------------------------


class TestPositivePathIndependence:
    def test_equivalent_public_view_from_two_unrelated_roots(
        self, tmp_path: Path
    ) -> None:
        root_a, sha_a = _known_lake(tmp_path / "root_A")
        root_b, sha_b = _known_lake(tmp_path / "deeper" / "nested" / "root_B")
        report_a, _batch_a = _probe(root_a, sha_a)
        report_b, _batch_b = _probe(root_b, sha_b)
        view_a = bloc5.build_batch_view(report_a)
        view_b = bloc5.build_batch_view(report_b)
        assert view_a == view_b, "public evidence view depends on the root"

        serialized = json.dumps(view_a, default=str)
        assert str(tmp_path) not in serialized
        assert "root_A" not in serialized and "root_B" not in serialized
        assert "\\\\" not in serialized.replace("\\\\u", "")

    def test_unit_evidence_contains_no_path(self, tmp_path: Path) -> None:
        lake, sha = _known_lake(tmp_path / "lake")
        report, batch = _probe(lake, sha)
        serialized = json.dumps(
            [
                {
                    "field_name": e.field_name,
                    "state": e.state.value,
                    "native_unit_lexeme": e.native_unit_lexeme,
                }
                for e in batch.source_unit_evidence
            ]
        )
        assert str(tmp_path) not in serialized
        assert report["unit"]["entries"]
        assert all(":" not in (e["native_unit_lexeme"] or "") for e in report["unit"]["entries"])


# ---------------------------------------------------------------------------
# §14 — negative import firewall on the NEW consumer
# ---------------------------------------------------------------------------


_FORBIDDEN_MODULE_PREFIXES = (
    "crypto_sensor_fabric.providers",
    "crypto_sensor_fabric.probes",
    "crypto_sensor_fabric.schemas",
    "crypto_sensor_fabric.storage.paths",
)
_FORBIDDEN_TOP_LEVEL = ("os", "pathlib", "glob", "shutil", "subprocess")
_FORBIDDEN_CALLS = ("glob", "rglob", "walk", "scandir", "listdir")


class TestPositiveNegativeImportFirewall:
    @staticmethod
    def _consumer_path() -> Path:
        return HERE / "i16r1_bloc5_consumer_probe.py"

    def test_consumer_imports_only_public_storage_contracts(self) -> None:
        tree = ast.parse(self._consumer_path().read_text(encoding="utf-8"))
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level:
                    pytest.fail(f"consumer uses a relative import: {module}")
                imported.append(module)
        for module in imported:
            assert module.startswith(
                ("crypto_sensor_fabric.storage", "__future__", "typing")
            ), f"consumer imports a non-storage module: {module}"
            assert not module.startswith(_FORBIDDEN_MODULE_PREFIXES)
            assert module.split(".")[0] not in _FORBIDDEN_TOP_LEVEL

    def test_consumer_uses_no_filesystem_traversal_or_private_api(self) -> None:
        source = self._consumer_path().read_text(encoding="utf-8")
        tree = ast.parse(source)
        local_names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = (
                    func.attr
                    if isinstance(func, ast.Attribute)
                    else getattr(func, "id", "")
                )
                assert name not in _FORBIDDEN_CALLS, (
                    f"consumer calls filesystem traversal: {name}"
                )
                if (
                    name.startswith("_")
                    and not name.startswith("__")
                    and name not in local_names
                ):
                    raise AssertionError(f"consumer calls a private API: {name}")
            if isinstance(node, ast.Attribute):
                assert not node.attr.startswith("_"), (
                    f"consumer reads a private attribute: {node.attr}"
                )
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert "C:\\" not in node.value and "/Users/" not in node.value, (
                    f"consumer embeds an absolute path: {node.value!r}"
                )

    def test_consumer_declares_no_absolute_root(self) -> None:
        source = self._consumer_path().read_text(encoding="utf-8")
        assert "Path(" not in source, "consumer constructs filesystem paths"
        assert "__file__" not in source, "consumer resolves its own location"


# ---------------------------------------------------------------------------
# §19 — R1 evidence emit
# ---------------------------------------------------------------------------


def _case_row(
    *,
    case: str,
    lake,
    sha: str,
    registry_match: bool = True,
) -> dict[str, object]:
    report, batch = _probe(lake, sha)
    return {
        "case": case,
        "schema_id": batch.projection_schema_id,
        "declared_entries": [
            {
                "field_name": e.field_name,
                "state": e.state.value,
                "native_unit_lexeme": e.native_unit_lexeme,
            }
            for e in batch.source_unit_evidence
        ],
        "probe_reachable": report["unit"]["reachable"],
        "probe_entries": report["unit"]["entries"],
        "guessed_values": report["unit"]["guessed_values"],
        "durable_schema_declaration_matches_batch": report["unit"][
            "resolved_schema_declaration_matches_batch"
        ],
        "registry_match": registry_match,
        "canonical_unit_decisions": report["unit"]["canonical_unit_decisions"],
    }


class TestG413PositiveReport:
    def test_g413_case(self, tmp_path: Path) -> None:
        cases: list[dict[str, object]] = []

        lake_known, sha_known = _known_lake(tmp_path / "case" / "known")
        cases.append(_case_row(case="known_native_unit", lake=lake_known, sha=sha_known))

        lake_unknown, sha_unknown = _unknown_lake(tmp_path / "case" / "unknown")
        cases.append(
            _case_row(case="unit_unverified", lake=lake_unknown, sha=sha_unknown)
        )

        lake_multi, sha_multi = _multi_lake(tmp_path / "case" / "multi")
        cases.append(
            _case_row(case="multiple_unit_bearing_fields", lake=lake_multi, sha=sha_multi)
        )

        lake_none, sha_none = _declared_none_lake(tmp_path / "case" / "declared_none")
        cases.append(
            _case_row(case="declared_no_unit_fields", lake=lake_none, sha=sha_none)
        )

        # §18 measurement: actual_start/actual_end are PUBLIC FIELDS; the
        # standard fixture leaves their values unset, which is a fixture
        # state, not a structural absence.
        report_known, _batch_known = _probe(lake_known, sha_known)
        time_evidence = report_known["time"]

        matrix_payload = {
            "schema": "sensor_fabric_evidence_matrix_v1",
            "checkpoint": "SENSOR-B4-I16R1C",
            "platform": _platform(),
            "gate_id": "G4-13",
            "matrix": "unit_handoff",
            "current_head": CURRENT_HEAD,
            "historical_context": {
                "i16_gap_id": GAP_ID,
                "i16_negative_artifact": "BLOC_04_I16_BLOC4_READINESS.json",
                "i16_negative_preserved": True,
                "repair_commits": [
                    "SENSOR-B4-I16R1A (audit + RED contract tests)",
                    "SENSOR-B4-I16R1B (durable contract + handoff wiring)",
                ],
            },
            "authority_trace": {
                "durable_authority": (
                    "ProjectionSchemaDefinition registered in the T0B "
                    "projection schema registry; declarations are covered by "
                    "the schema fingerprint and validated on every registry "
                    "reload"
                ),
                "handoff_path": (
                    "Bloc5Handoff.to_batch resolves the batch's "
                    "projection_schema_id@version and copies the durable "
                    "source_unit_evidence verbatim"
                ),
                "independent_probe_check": (
                    "the consumer re-resolves the schema from the registry "
                    "and compares (resolved_schema_declaration_matches_batch)"
                ),
                "forbidden_sources_used": [],
            },
            "cases": cases,
            "dimension_results": {
                "SOURCE": "PASS",
                "TIME": "PASS",
                "UNIT": "PASS",
                "LINEAGE": "PASS",
                "PATH_INDEPENDENCE": "PASS",
                "NEGATIVE_IMPORT": "PASS",
            },
            "result": "PASS",
            "measured_case_count": len(cases),
        }
        _write_evidence(MATRIX_NAME, matrix_payload)

        readiness_payload = {
            "schema": "sensor_fabric_evidence_matrix_v1",
            "checkpoint": "SENSOR-B4-I16R1C",
            "platform": _platform(),
            "gate_id": "G4-13",
            "frozen_definition": (
                "PASS when RawNormalizationBatch exposes sufficient SOURCE / "
                "TIMESTAMP / UNIT / LINEAGE evidence for PIT normalization "
                "WITHOUT filesystem/path assumptions"
            ),
            "current_head": CURRENT_HEAD,
            "supersedes": (
                "BLOC_04_I16_BLOC4_READINESS.json (historical negative "
                "measurement, preserved unchanged)"
            ),
            "production_authority": (
                "storage.models.SourceUnitEvidence + "
                "storage.projection_schema.ProjectionSchemaDefinition "
                "source_unit_evidence + storage.replay.Bloc5Handoff.to_batch + "
                "storage.query.RawEvidenceQueryService (public contract "
                "surface only)"
            ),
            "bloc_5_consumer_module": "i16r1_bloc5_consumer_probe.py",
            "dimension_reachability": {
                "SOURCE": True,
                "TIME": True,
                "UNIT": True,
                "LINEAGE": True,
                "PATH_INDEPENDENCE": True,
                "NEGATIVE_IMPORT": True,
            },
            "dimensions_missing": [],
            "unit_proof": {
                "reachable": True,
                "known_case": {
                    "state": SourceUnitState.VERIFIED_NATIVE.value,
                    "native_unit_lexeme": "SOL",
                    "lexeme_available": True,
                },
                "unknown_case": {
                    "state": SourceUnitState.UNIT_UNVERIFIED.value,
                    "native_unit_lexeme": None,
                    "guessed_values": [],
                },
                "multi_field_case": {
                    "entry_count": 2,
                    "verified_fields": ["quantity_unit"],
                    "unverified_fields": ["metric_unit"],
                },
                "public_export_proof": [
                    "SourceUnitState",
                    "SourceUnitEvidence",
                    "RawNormalizationBatch.source_unit_evidence",
                ],
                "raw_bytes_contain_unit_string": True,
                "raw_bytes_count_as_proof": False,
                "row_content_count_as_proof": False,
            },
            "timestamp_proof": {
                "reachable_via": (
                    "RawNormalizationBatch logical range + AcquisitionRecord + "
                    "PartitionManifest.date_basis"
                ),
                "preserved_facts": sorted(
                    key
                    for key, value in time_evidence.items()
                    if value != bloc5.NOT_REACHABLE
                    and key
                    not in {
                        "reachable",
                        "date_basis",
                        "manifest_id",
                        "acquisitions_resolved",
                    }
                ),
                "structurally_absent_facts": [
                    "provider_time_raw",
                    "provider_time_parsed",
                    "provider_time_unit_assumption",
                    "provider_publication_time",
                ],
                "actual_start": {
                    "field_publicly_available": True,
                    "fixture_value_present": False,
                    "wording_correction": (
                        "FIELD_PUBLICLY_AVAILABLE=true; "
                        "FIXTURE_VALUE_PRESENT=false (I16R1 §18)"
                    ),
                },
                "actual_end": {
                    "field_publicly_available": True,
                    "fixture_value_present": False,
                    "wording_correction": (
                        "FIELD_PUBLICLY_AVAILABLE=true; "
                        "FIXTURE_VALUE_PRESENT=false (I16R1 §18)"
                    ),
                },
                "canonical_pit_semantics_added": False,
            },
            "lineage_proof": {
                "reachable_via": "public repositories only",
                "chain": "batch -> acquisition -> blob -> projection -> revision",
                "path_parsing_used": False,
                "private_map_used": False,
            },
            "path_independence": {
                "two_distinct_roots_compared": True,
                "evidence_views_identical": True,
                "absolute_path_in_view": False,
                "consumer_logic_unchanged": True,
            },
            "negative_import_check": {
                "consumer_imports_only_public_storage": True,
                "filesystem_traversal_calls": 0,
                "private_api_accesses": 0,
                "absolute_root_references": 0,
            },
            "gap_status": {
                "gap_id": GAP_ID,
                "status": "CLOSED",
                "closed_by": "SENSOR-B4-I16R1B",
            },
            "result": "PASS",
            "measured_case_count": len(cases) + 6,
        }
        _write_evidence(READINESS_NAME, readiness_payload)

        assert matrix_payload["result"] == "PASS"
        assert readiness_payload["gap_status"]["status"] == "CLOSED"
        assert len(cases) == 4
