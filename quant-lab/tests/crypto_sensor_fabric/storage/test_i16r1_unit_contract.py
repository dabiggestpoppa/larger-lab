"""SENSOR-B4-I16R1 — source-unit handoff contract tests.

I16R1A lands these tests RED (the contract does not exist yet); I16R1B makes
them GREEN by adding the smallest additive source-unit contract justified by
``BLOC_04_I16R1_UNIT_SEMANTIC_AUDIT.json``:

    SourceUnitState:  VERIFIED_NATIVE | UNIT_UNVERIFIED
    SourceUnitEvidence: {field_name, native_unit_lexeme, state}
    ProjectionSchemaDefinition: additive durable source-unit declarations
    Bloc5Handoff.to_batch: copies the durable declarations into
        RawNormalizationBatch.source_unit_evidence

Frozen laws exercised here:

  * §5/§6 — Bloc 4 preserves provider-native lexemes and explicit unknown
    state; it never decides canonical units or guesses one.
  * §8 — evidence originates from the durable projection-schema contract,
    never from provider-name heuristics, instrument parsing, hard-coded
    sensor maps, fixtures, Bloc 5 rules or raw-byte key search.
  * §10 — historical descriptors and batches remain loadable; absence means
    UNKNOWN HISTORICAL CONTRACT, never VERIFIED_NATIVE.
  * §16 — contradictory evidence fails closed; no silent dedupe.
  * §17 — deterministic canonical serialization.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pyarrow as pa
import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from crypto_sensor_fabric.storage import (  # noqa: E402
    Bloc5Handoff,
    ProjectionSchemaConflict,
    ProjectionSchemaDefinition,
    ProjectionSchemaRegistry,
    ProjectionSchemaUnsupported,
    RawEvidenceQuery,
    RawEvidenceQueryService,
    RawNormalizationBatch,
    SourceUnitEvidence,
    SourceUnitState,
    compute_schema_fingerprint,
)
from crypto_sensor_fabric.storage.projection_schema import (  # noqa: E402
    ProjectionSchemaCatalogCorrupt,
)

CURRENT_HEAD = "618de97827a22b2514caa4178d5cffa4ea76d1b7"

R1_NATIVE_SCHEMA = pa.schema(
    [
        pa.field("price", pa.float64(), nullable=False),
        pa.field("qty", pa.float64(), nullable=False),
        pa.field("quantity_unit", pa.string(), nullable=False),
    ]
)

R1_MULTI_SCHEMA = pa.schema(
    [
        pa.field("price", pa.float64(), nullable=False),
        pa.field("qty", pa.float64(), nullable=False),
        pa.field("quantity_unit", pa.string(), nullable=False),
        pa.field("metric_unit", pa.string(), nullable=True),
    ]
)

KNOWN = SourceUnitEvidence(
    field_name="quantity_unit",
    native_unit_lexeme="SOL",
    state=SourceUnitState.VERIFIED_NATIVE,
)
UNKNOWN = SourceUnitEvidence(
    field_name="quantity_unit",
    native_unit_lexeme=None,
    state=SourceUnitState.UNIT_UNVERIFIED,
)
UNKNOWN_METRIC = SourceUnitEvidence(
    field_name="metric_unit",
    native_unit_lexeme=None,
    state=SourceUnitState.UNIT_UNVERIFIED,
)


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


_i16a = _load_sibling("i16_g4_core_harness_r1", "test_i16_g4_core")
Lake = _i16a.Lake


class _PublicRevisionIdentityFactory:
    @staticmethod
    def from_acquisition(acquisition: object) -> object:
        from crypto_sensor_fabric.storage.revisions import (
            RevisionSourceIdentityV1,
        )

        return RevisionSourceIdentityV1.from_acquisition(acquisition)


def _register_definition(
    lake,
    *,
    schema_id: str,
    declarations=None,
    schema=None,
):
    definition = ProjectionSchemaDefinition(
        schema_id,
        "1.0.0",
        schema if schema is not None else R1_NATIVE_SCHEMA,
        source_unit_evidence=declarations,
    )
    lake.schemas.register(definition)
    # The Lake harness commits projections with its own definition attribute.
    lake.schema_definition = definition
    return definition


def _commit_projection(lake, *, projection_id: str = "proj-r1", rows):
    # The raw source payload carries a unit-looking string on purpose: R1
    # proves that unit EVIDENCE comes from the durable schema contract, not
    # from a byte search (the no-guess proof).
    sha = lake.seed_blob(
        b'{"rows":[{"price":1.0,"qty":1.0,"quantity_unit":"SOL"}],'
        b'"ts":1700000000}'
    )
    lake.seed_acquisition(sha, "acq-r1")
    lake.projection_service.commit_projection(
        rows=rows,
        schema_definition=lake.schema_definition,
        projection_id=projection_id,
        source_blob_sha256=[sha],
        acquisition_ids=["acq-r1"],
        provider="kraken",
        venue="futures",
        sensor_family="MECHANICAL_TRADE",
        native_instrument="BTC-USDT",
        native_granularity="1m",
        parser_version="1.0.0",
        partition_key="kraken/futures/BTC-USDT/2026-01-15",
        logical_year=2026,
        logical_month=1,
        logical_day=15,
        lineage_manifest_id=f"lm-{projection_id}",
    )
    lake.commit_manifest("pm-r1", blob_refs=[sha], projection_refs=[projection_id])
    return sha


def _service(lake):
    return RawEvidenceQueryService(
        manifest_repository=lake.resolver_backed_manifests(),
        acquisition_repository=lake.acq_repo,
        blob_metadata_repository=lake.blob_repo,
        revision_registry=lake.registry,
        revision_identity_factory=_PublicRevisionIdentityFactory,
        projection_artifact_repository=lake.artifacts,
        projection_lineage_repository=lake.lineage,
    )


def _handoff_batch(
    lake,
    sha: str,
    *,
    registry,
    projection_id: str = "proj-r1",
) -> RawNormalizationBatch:
    service = _service(lake)
    result = service.execute(
        RawEvidenceQuery(include_t0a=True, include_t0b=True)
    ).results[0]
    handoff = Bloc5Handoff(
        batch_id_factory=lambda r: "batch-r1", schema_registry=registry
    )
    return handoff.to_batch(
        result,
        projections=[lake.artifacts.get(projection_id)],
        acquisitions=lake.acq_repo.list_acquisitions_for_blob(sha),
        parser_version="1.0.0",
        raw_rows_or_reader="descriptor://proj-r1",
    )


def _unit_stack(tmp_path: Path, *, schema_id: str, declarations, rows=None, schema=None):
    lake = Lake(tmp_path / "lake")
    _register_definition(
        lake, schema_id=schema_id, declarations=declarations, schema=schema
    )
    sha = _commit_projection(
        lake,
        rows=rows
        if rows is not None
        else [{"price": 1.0, "qty": 1.0, "quantity_unit": "SOL"}],
    )
    return lake, sha


# ---------------------------------------------------------------------------
# §5/§6/§7 — vocabulary and model
# ---------------------------------------------------------------------------


class TestSourceUnitVocabulary:
    def test_state_members_are_the_frozen_pair(self) -> None:
        assert [m.name for m in SourceUnitState] == [
            "VERIFIED_NATIVE",
            "UNIT_UNVERIFIED",
        ]
        assert SourceUnitState.VERIFIED_NATIVE.value == "VERIFIED_NATIVE"
        assert SourceUnitState.UNIT_UNVERIFIED.value == "UNIT_UNVERIFIED"

    def test_vocabulary_is_publicly_exported(self) -> None:
        import crypto_sensor_fabric.storage as public_storage

        for name in ("SourceUnitState", "SourceUnitEvidence"):
            assert name in public_storage.__all__, f"{name} is not exported"
            assert hasattr(public_storage, name)


class TestSourceUnitEvidenceFailClosed:
    def test_verified_native_requires_a_lexeme(self) -> None:
        with pytest.raises(ValueError):
            SourceUnitEvidence(
                field_name="quantity_unit",
                native_unit_lexeme=None,
                state=SourceUnitState.VERIFIED_NATIVE,
            )
        for blank in ("", "   "):
            with pytest.raises(ValueError):
                SourceUnitEvidence(
                    field_name="quantity_unit",
                    native_unit_lexeme=blank,
                    state=SourceUnitState.VERIFIED_NATIVE,
                )

    def test_unverified_must_not_carry_a_lexeme(self) -> None:
        for guessed in ("contracts", "USD", "SOL", "base"):
            with pytest.raises(ValueError):
                SourceUnitEvidence(
                    field_name="quantity_unit",
                    native_unit_lexeme=guessed,
                    state=SourceUnitState.UNIT_UNVERIFIED,
                )

    def test_field_identity_must_be_nonempty_and_unreserved(self) -> None:
        with pytest.raises(ValueError):
            SourceUnitEvidence(
                field_name="",
                native_unit_lexeme=None,
                state=SourceUnitState.UNIT_UNVERIFIED,
            )
        with pytest.raises(ValueError):
            SourceUnitEvidence(
                field_name="   ",
                native_unit_lexeme=None,
                state=SourceUnitState.UNIT_UNVERIFIED,
            )
        with pytest.raises(ValueError):
            SourceUnitEvidence(
                field_name="_t0_projection_id",
                native_unit_lexeme=None,
                state=SourceUnitState.UNIT_UNVERIFIED,
            )

    def test_invalid_state_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            SourceUnitEvidence(
                field_name="quantity_unit",
                native_unit_lexeme=None,
                state="MAYBE",  # type: ignore[arg-type]
            )

    def test_descriptor_round_trip_is_lossless(self) -> None:
        for evidence in (KNOWN, UNKNOWN):
            descriptor = evidence.to_descriptor()
            assert set(descriptor) == {
                "field_name",
                "native_unit_lexeme",
                "state",
            }
            rebuilt = SourceUnitEvidence.from_descriptor(descriptor)
            assert rebuilt == evidence
            assert rebuilt.to_descriptor() == descriptor

    def test_contradictory_descriptors_fail_closed(self) -> None:
        with pytest.raises(ValueError):
            SourceUnitEvidence.from_descriptor(
                {
                    "field_name": "quantity_unit",
                    "native_unit_lexeme": None,
                    "state": "VERIFIED_NATIVE",
                }
            )
        with pytest.raises(ValueError):
            SourceUnitEvidence.from_descriptor(
                {
                    "field_name": "quantity_unit",
                    "native_unit_lexeme": "contracts",
                    "state": "UNIT_UNVERIFIED",
                }
            )


# ---------------------------------------------------------------------------
# §8/§9/§10 — durable schema declarations
# ---------------------------------------------------------------------------


class TestSchemaDeclarationContract:
    def test_declaration_enters_the_fingerprint(self) -> None:
        legacy = ProjectionSchemaDefinition("r1.id", "1.0.0", R1_NATIVE_SCHEMA)
        declared = ProjectionSchemaDefinition(
            "r1.id", "1.0.0", R1_NATIVE_SCHEMA, source_unit_evidence=[KNOWN]
        )
        assert legacy.schema_fingerprint == compute_schema_fingerprint(
            R1_NATIVE_SCHEMA
        )
        assert declared.schema_fingerprint != legacy.schema_fingerprint

    def test_legacy_descriptor_loads_under_historical_contract(self) -> None:
        legacy = ProjectionSchemaDefinition("r1.legacy", "1.0.0", R1_NATIVE_SCHEMA)
        payload = legacy.to_descriptor()
        assert "source_unit_evidence" not in payload
        rebuilt = ProjectionSchemaDefinition.from_descriptor(payload)
        assert rebuilt.schema_fingerprint == legacy.schema_fingerprint
        assert list(rebuilt.source_unit_evidence) == []

    def test_declared_descriptor_round_trips_with_fingerprint(self) -> None:
        declared = ProjectionSchemaDefinition(
            "r1.declared",
            "1.0.0",
            R1_MULTI_SCHEMA,
            source_unit_evidence=[UNKNOWN_METRIC, KNOWN],
        )
        payload = declared.to_descriptor()
        assert payload["source_unit_evidence"] == [
            UNKNOWN_METRIC.to_descriptor(),
            KNOWN.to_descriptor(),
        ]
        rebuilt = ProjectionSchemaDefinition.from_descriptor(payload)
        assert rebuilt.schema_fingerprint == declared.schema_fingerprint
        assert list(rebuilt.source_unit_evidence) == [UNKNOWN_METRIC, KNOWN]

    def test_declarations_are_canonically_ordered(self) -> None:
        declared = ProjectionSchemaDefinition(
            "r1.order",
            "1.0.0",
            R1_MULTI_SCHEMA,
            source_unit_evidence=[KNOWN, UNKNOWN_METRIC],
        )
        assert [e.field_name for e in declared.source_unit_evidence] == [
            "metric_unit",
            "quantity_unit",
        ]

    def test_declaration_for_unknown_field_fails_closed(self) -> None:
        with pytest.raises(ValueError):
            ProjectionSchemaDefinition(
                "r1.unknownfield",
                "1.0.0",
                R1_NATIVE_SCHEMA,
                source_unit_evidence=[
                    SourceUnitEvidence(
                        field_name="metric_unit",
                        native_unit_lexeme=None,
                        state=SourceUnitState.UNIT_UNVERIFIED,
                    )
                ],
            )

    def test_duplicate_declarations_fail_closed(self) -> None:
        with pytest.raises(ValueError):
            ProjectionSchemaDefinition(
                "r1.dup",
                "1.0.0",
                R1_MULTI_SCHEMA,
                source_unit_evidence=[
                    KNOWN,
                    SourceUnitEvidence(
                        field_name="quantity_unit",
                        native_unit_lexeme="BTC",
                        state=SourceUnitState.VERIFIED_NATIVE,
                    ),
                ],
            )

    def test_registry_restart_validates_the_declaration(self, tmp_path: Path) -> None:
        root = tmp_path / "catalogs" / "projection_schemas"
        registry = ProjectionSchemaRegistry(root)
        registry.register(
            ProjectionSchemaDefinition(
                "r1.restart",
                "1.0.0",
                R1_NATIVE_SCHEMA,
                source_unit_evidence=[KNOWN],
            )
        )
        reloaded = ProjectionSchemaRegistry(root)
        definition = reloaded.resolve_by_id("r1.restart", "1.0.0")
        assert list(definition.source_unit_evidence) == [KNOWN]

    def test_registry_conflict_on_same_identity_different_declaration(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "catalogs" / "projection_schemas"
        registry = ProjectionSchemaRegistry(root)
        registry.register(
            ProjectionSchemaDefinition(
                "r1.conflict",
                "1.0.0",
                R1_NATIVE_SCHEMA,
                source_unit_evidence=[KNOWN],
            )
        )
        with pytest.raises(ProjectionSchemaConflict):
            registry.register(
                ProjectionSchemaDefinition(
                    "r1.conflict",
                    "1.0.0",
                    R1_NATIVE_SCHEMA,
                    source_unit_evidence=[UNKNOWN],
                )
            )

    def test_registry_reload_rejects_tampered_declaration(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "catalogs" / "projection_schemas"
        registry = ProjectionSchemaRegistry(root)
        registry.register(
            ProjectionSchemaDefinition(
                "r1.tamper",
                "1.0.0",
                R1_NATIVE_SCHEMA,
                source_unit_evidence=[KNOWN],
            )
        )
        from crypto_sensor_fabric.storage.json_catalog import catalog_physical_key

        fragment = root / catalog_physical_key("r1.tamper@1.0.0")
        payload = json.loads(fragment.read_text(encoding="utf-8"))
        payload["source_unit_evidence"][0]["native_unit_lexeme"] = "BTC"
        fragment.write_text(
            json.dumps(payload, sort_keys=True), encoding="utf-8", newline="\n"
        )
        with pytest.raises(ProjectionSchemaCatalogCorrupt):
            ProjectionSchemaRegistry(root)


# ---------------------------------------------------------------------------
# §16/§17 — batch evidence: fail closed, canonical order, determinism
# ---------------------------------------------------------------------------


def _batch(**overrides) -> RawNormalizationBatch:
    from datetime import UTC, datetime

    base = dict(
        batch_id="b",
        provider="kraken",
        venue="futures",
        sensor_family=__import__(
            "crypto_sensor_fabric.contracts.enums", fromlist=["SensorFamily"]
        ).SensorFamily.MECHANICAL_TRADE,
        native_instrument="BTC-USDT",
        projection_schema_id="r1.batch",
        projection_schema_version="1.0.0",
        parser_version="1.0.0",
        raw_rows_or_reader="descriptor://proj-r1",
        source_blob_refs=["a" * 64],
        acquisition_refs=["acq-r1"],
        logical_time_range_start=datetime(2026, 1, 15, tzinfo=UTC),
        logical_time_range_end=datetime(2026, 1, 15, 1, tzinfo=UTC),
    )
    base.update(overrides)
    return RawNormalizationBatch(**base)


class TestBatchEvidenceContract:
    def test_historical_batch_constructs_without_evidence(self) -> None:
        batch = _batch()
        assert list(batch.source_unit_evidence) == []

    def test_evidence_is_canonically_ordered(self) -> None:
        batch = _batch(source_unit_evidence=[KNOWN, UNKNOWN_METRIC])
        fields = [e.field_name for e in batch.source_unit_evidence]
        assert fields == sorted(fields)
        assert fields == ["metric_unit", "quantity_unit"]

    def test_duplicate_field_names_fail_closed(self) -> None:
        other = SourceUnitEvidence(
            field_name="quantity_unit",
            native_unit_lexeme="BTC",
            state=SourceUnitState.VERIFIED_NATIVE,
        )
        with pytest.raises(ValueError):
            _batch(source_unit_evidence=[KNOWN, other])
        with pytest.raises(ValueError):
            _batch(source_unit_evidence=[KNOWN, KNOWN])

    def test_serialization_is_deterministic_under_permutation(self) -> None:
        first = _batch(source_unit_evidence=[UNKNOWN_METRIC, KNOWN])
        second = _batch(source_unit_evidence=[KNOWN, UNKNOWN_METRIC])
        assert first.model_dump_json() == second.model_dump_json()

    def test_no_canonicalization_fields_were_added(self) -> None:
        fields = set(RawNormalizationBatch.model_fields)
        for forbidden in (
            "effective_at",
            "observed_at",
            "canonical_asset_id",
            "canonical_notional",
            "native_unit",
            "unit_state",
        ):
            assert forbidden not in fields, forbidden


# ---------------------------------------------------------------------------
# §11 — Bloc5Handoff wiring
# ---------------------------------------------------------------------------


class TestHandoffWiring:
    def test_known_unit_case(self, tmp_path: Path) -> None:
        lake, sha = _unit_stack(
            tmp_path, schema_id="i16r1.units.known", declarations=[KNOWN]
        )
        batch = _handoff_batch(lake, sha, registry=lake.schemas)
        assert len(batch.source_unit_evidence) == 1
        evidence = batch.source_unit_evidence[0]
        assert evidence.field_name == "quantity_unit"
        assert evidence.state == SourceUnitState.VERIFIED_NATIVE
        assert evidence.native_unit_lexeme == "SOL"

    def test_unknown_unit_case(self, tmp_path: Path) -> None:
        lake, sha = _unit_stack(
            tmp_path, schema_id="i16r1.units.unknown", declarations=[UNKNOWN]
        )
        batch = _handoff_batch(lake, sha, registry=lake.schemas)
        assert len(batch.source_unit_evidence) == 1
        evidence = batch.source_unit_evidence[0]
        assert evidence.state == SourceUnitState.UNIT_UNVERIFIED
        assert evidence.native_unit_lexeme is None

    def test_multiple_unit_bearing_fields(self, tmp_path: Path) -> None:
        lake, sha = _unit_stack(
            tmp_path,
            schema_id="i16r1.units.multi",
            declarations=[UNKNOWN_METRIC, KNOWN],
            rows=[
                {
                    "price": 1.0,
                    "qty": 1.0,
                    "quantity_unit": "SOL",
                    "metric_unit": "bps",
                }
            ],
            schema=R1_MULTI_SCHEMA,
        )
        batch = _handoff_batch(lake, sha, registry=lake.schemas)
        assert [
            (e.field_name, e.state, e.native_unit_lexeme)
            for e in batch.source_unit_evidence
        ] == [
            ("metric_unit", SourceUnitState.UNIT_UNVERIFIED, None),
            ("quantity_unit", SourceUnitState.VERIFIED_NATIVE, "SOL"),
        ]

    def test_evidence_is_copied_verbatim_from_the_durable_contract(
        self, tmp_path: Path
    ) -> None:
        lake, sha = _unit_stack(
            tmp_path, schema_id="i16r1.units.known", declarations=[KNOWN]
        )
        registered = lake.schemas.resolve_by_id("i16r1.units.known", "1.0.0")
        batch = _handoff_batch(lake, sha, registry=lake.schemas)
        assert list(batch.source_unit_evidence) == list(
            registered.source_unit_evidence
        )

    def test_unresolvable_schema_fails_closed(self, tmp_path: Path) -> None:
        lake, sha = _unit_stack(
            tmp_path, schema_id="i16r1.units.known", declarations=[KNOWN]
        )
        empty_registry = ProjectionSchemaRegistry(
            tmp_path / "elsewhere" / "catalogs" / "projection_schemas"
        )
        with pytest.raises(ProjectionSchemaUnsupported):
            _handoff_batch(lake, sha, registry=empty_registry)

    def test_legacy_handoff_without_registry_keeps_historical_contract(
        self, tmp_path: Path
    ) -> None:
        lake, sha = _unit_stack(
            tmp_path, schema_id="i16r1.units.known", declarations=[KNOWN]
        )
        batch = _handoff_batch(lake, sha, registry=None)
        assert list(batch.source_unit_evidence) == []

    def test_schema_without_declarations_yields_no_unit_claim(
        self, tmp_path: Path
    ) -> None:
        lake, sha = _unit_stack(
            tmp_path, schema_id="i16r1.units.undeclared", declarations=None
        )
        batch = _handoff_batch(lake, sha, registry=lake.schemas)
        assert list(batch.source_unit_evidence) == []
