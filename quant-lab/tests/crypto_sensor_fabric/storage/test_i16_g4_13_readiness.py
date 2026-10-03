"""SENSOR-B4-I16C — G4-13 Bloc 5 readiness at the current head.

This gate was UNPASSED at the start of I16.  It is measured, not assumed.

Four dimensions are required for a Bloc 5 PIT normalization pass that makes
NO filesystem or path assumption:

  SOURCE   — who/what produced the evidence
  TIME     — the preserved T0 timestamp facts
  UNIT     — the provider-native unit or an explicit UNIT_UNVERIFIED state
  LINEAGE  — batch -> acquisition -> blob -> projection -> revision

Each dimension is proved by running the real public read surfaces
(``RawEvidenceQueryService`` + the accepted repositories + the projection
schema registry), then by running a narrow TEST-ONLY Bloc 5 consumer
(``i16_bloc5_consumer_probe``) that may import only public
``crypto_sensor_fabric.storage`` names.

If a dimension is not reachable through a public typed contract, this gate
does NOT pass and does NOT get repaired here: it is reported as
``I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP`` per §20 and final PASS is stopped.
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
    RawEvidenceQuery,
    RawNormalizationBatch,
    StorageEncoding,
)

import i16_bloc5_consumer_probe as bloc5  # noqa: E402

CURRENT_HEAD = "051b6dd1a297d49b59ba504f4da8536211f8911d"

EVIDENCE_DIR = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)
READINESS_NAME = "BLOC_04_I16_BLOC4_READINESS.json"

_UNIT_TOKEN = "unit"


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


_i16a = _load_sibling("i16_g4_core_harness_b", "test_i16_g4_core")
Lake = _i16a.Lake


def _build_lake(root: Path):
    """A non-vacuous handoff: T0A + T0B + manifest + acquisition."""
    lake = Lake(root)
    payload = b'{"rows":[{"price":1.0,"unit":"contracts"}],"ts":1700000000}'
    sha = lake.seed_blob(payload)
    lake.seed_acquisition(sha, "acq-handoff")
    lake.commit_projection("proj-handoff", [(sha, "acq-handoff")])
    lake.commit_manifest(
        "pm-handoff", blob_refs=[sha], projection_refs=["proj-handoff"]
    )
    return lake, sha, payload


def _query() -> RawEvidenceQuery:
    return RawEvidenceQuery(include_t0a=True, include_t0b=True)


class _PublicRevisionIdentityFactory:
    """The accepted production revision-identity factory.

    Recorded honestly: ``RevisionSourceIdentityV1`` is reachable from the
    public MODULE ``crypto_sensor_fabric.storage.revisions`` but is NOT in
    the package ``__all__``.  A Bloc 5 consumer therefore receives an
    already-wired ``RawEvidenceQueryService`` from Bloc 4 rather than
    constructing one; ``RevisionResolver``, ``SourceRevision`` and
    ``RevisionState`` are public.  See the readiness artifact's
    ``public_export_notes``.
    """

    @staticmethod
    def from_acquisition(acquisition: object) -> object:
        from crypto_sensor_fabric.storage.revisions import (
            RevisionSourceIdentityV1,
        )

        return RevisionSourceIdentityV1.from_acquisition(acquisition)


def _service(lake: Lake):
    from crypto_sensor_fabric.storage import RawEvidenceQueryService

    return RawEvidenceQueryService(
        manifest_repository=lake.resolver_backed_manifests(),
        acquisition_repository=lake.acq_repo,
        blob_metadata_repository=lake.blob_repo,
        revision_registry=lake.registry,
        revision_identity_factory=_PublicRevisionIdentityFactory,
        projection_artifact_repository=lake.artifacts,
        projection_lineage_repository=lake.lineage,
    )


def _collect(lake: Lake) -> dict[str, object]:
    return bloc5.collect_evidence(
        service=_service(lake),
        acquisitions=lake.acq_repo,
        blobs=lake.blob_repo,
        manifests=lake.resolver_backed_manifests(),
        registry=lake.registry,
        schemas=lake.schemas,
        query=_query(),
    )


# ---------------------------------------------------------------------------
# §17 — SOURCE PROOF
# ---------------------------------------------------------------------------


class TestG413SourceProof:
    def test_source_identity_is_publicly_reachable(self, tmp_path: Path) -> None:
        lake, _sha, _payload = _build_lake(tmp_path / "lake")
        report = _collect(lake)
        source = report["source"]
        assert source["reachable"] is True
        assert source["provider"] == "kraken"
        assert source["venue"] == "futures"
        assert source["native_instrument"] == "BTC-USDT"
        assert source["source_granularity"] != bloc5.NOT_REACHABLE
        assert source["projection_refs"] == ["proj-handoff"]
        # No filesystem glob and no provider adapter call was needed.


# ---------------------------------------------------------------------------
# §18 — TIMESTAMP PROOF
# ---------------------------------------------------------------------------


class TestG413TimestampProof:
    def test_preserved_t0_time_facts_are_publicly_reachable(
        self, tmp_path: Path
    ) -> None:
        lake, _sha, _payload = _build_lake(tmp_path / "lake")
        time_evidence = _collect(lake)["time"]
        assert time_evidence["reachable"] is True
        for preserved in (
            "requested_start",
            "requested_end",
            "request_started_at",
            "response_observed_at",
            "ingested_at",
            "logical_time_start",
            "logical_time_end",
        ):
            assert time_evidence[preserved] != bloc5.NOT_REACHABLE, preserved
        assert time_evidence["date_basis"] != bloc5.NOT_REACHABLE

    def test_provider_lexical_time_facts_are_not_publicly_typed(
        self, tmp_path: Path
    ) -> None:
        """Recorded honestly: absent from the public acquisition contract."""
        lake, _sha, _payload = _build_lake(tmp_path / "lake")
        time_evidence = _collect(lake)["time"]
        for missing in (
            "provider_time_raw",
            "provider_time_parsed",
            "provider_time_unit_assumption",
            "provider_publication_time",
        ):
            assert time_evidence[missing] == bloc5.NOT_REACHABLE, missing

    def test_no_canonical_pit_semantics_were_invented(self) -> None:
        """Bloc 4 must not pre-empt Bloc 5's effective_at decision."""
        fields = set(RawNormalizationBatch.model_fields)
        for forbidden in (
            "effective_at",
            "observed_at",
            "canonical_asset_id",
            "canonical_notional",
            "normalized_price",
        ):
            assert forbidden not in fields, f"Bloc 4 invented {forbidden}"


# ---------------------------------------------------------------------------
# §19/§20 — UNIT PROOF (the decisive dimension)
# ---------------------------------------------------------------------------


class TestG413UnitProof:
    def test_batch_carries_no_unit_field(self) -> None:
        fields = set(RawNormalizationBatch.model_fields)
        unit_fields = sorted(f for f in fields if _UNIT_TOKEN in f.lower())
        assert unit_fields == [], (
            f"RawNormalizationBatch unexpectedly exposes {unit_fields}"
        )

    def test_no_unit_named_public_storage_export_exists(self) -> None:
        import crypto_sensor_fabric.storage as public_storage

        unit_exports = sorted(
            name
            for name in getattr(public_storage, "__all__", ())
            if _UNIT_TOKEN in name.lower()
        )
        assert unit_exports == [], (
            f"unit-named public export appeared: {unit_exports}"
        )

    def test_unit_unverified_state_is_not_supplied_by_bloc4(self) -> None:
        """Frozen doctrine: T0 passes UNIT_UNVERIFIED rather than guessing."""
        import crypto_sensor_fabric.storage as public_storage

        import enum as _enum

        found = False
        for obj in vars(public_storage).values():
            if isinstance(obj, type) and issubclass(obj, _enum.Enum):
                if "UNIT_UNVERIFIED" in getattr(obj, "__members__", {}):
                    found = True
        assert found is False, (
            "a UNIT_UNVERIFIED unit-state enum appeared in public storage; "
            "re-measure this gate"
        )

    def test_projection_schema_descriptor_carries_no_native_unit(
        self, tmp_path: Path
    ) -> None:
        """The schema contract exposes name/type/nullable, never a unit."""
        lake, _sha, _payload = _build_lake(tmp_path / "lake")
        definition = lake.schemas.resolve_by_id(
            "i16.g4.projection", "1.0.0"
        )
        descriptor = definition.to_descriptor()
        native_fields = descriptor["provider_native_fields"]
        assert native_fields, "descriptor carried no provider-native fields"
        for field in native_fields:
            assert set(field) == {"name", "type", "nullable"}, field
            assert _UNIT_TOKEN not in json.dumps(field).lower(), field

    def test_unit_evidence_is_not_reachable_through_public_contracts(
        self, tmp_path: Path
    ) -> None:
        """THE DECISIVE MEASUREMENT: unit evidence is NOT publicly reachable."""
        lake, _sha, _payload = _build_lake(tmp_path / "lake")
        report = _collect(lake)
        unit = report["unit"]
        assert unit["reachable"] is False, (
            "unit evidence became reachable; this gate must be re-measured "
            "and the I16 verdict revisited"
        )
        assert unit["native_unit"] == bloc5.NOT_REACHABLE
        assert unit["unit_state"] == bloc5.NOT_REACHABLE
        assert unit["UNIT_UNVERIFIED_supplied_by_bloc4"] is False
        assert unit["schema_native_field_units"] == []

    def test_bytes_containing_a_unit_string_do_not_count_as_a_contract(
        self, tmp_path: Path
    ) -> None:
        """Frozen §19: 'raw bytes contain it somewhere' is NOT a proof."""
        lake, _sha, _payload = _build_lake(tmp_path / "lake")
        with lake.store.open_blob(_sha, StorageEncoding.NONE) as handle:
            raw = handle.read()
        assert b"unit" in raw.lower(), "fixture sanity: unit string is present"
        # ...and it is still NOT reachable, because no public typed contract
        # exposes how a Bloc 5 consumer discovers it.
        assert _collect(lake)["unit"]["reachable"] is False


# ---------------------------------------------------------------------------
# §21 — LINEAGE PROOF
# ---------------------------------------------------------------------------


class TestG413LineageProof:
    def test_batch_to_blob_to_projection_to_revision_resolves(self, tmp_path: Path) -> None:
        lake, sha, _payload = _build_lake(tmp_path / "lake")
        report = _collect(lake)
        lineage = report["lineage"]
        assert lineage["reachable"] is True
        assert lineage["acquisition_id"] == "acq-handoff"
        assert lineage["acquisition_blob_ref"] == sha
        assert lineage["blob_sha256"] == sha
        assert lineage["manifest_id"] == "pm-handoff"
        assert lineage["manifest_version"] == 1
        assert lineage["projection_refs"] == ["proj-handoff"]
        assert lineage["revision_state"] not in (bloc5.NOT_REACHABLE, "None")
        assert lineage["lineage_refs"]

    def test_lineage_refs_are_nonempty_and_physically_verified(
        self, tmp_path: Path
    ) -> None:
        lake, sha, _payload = _build_lake(tmp_path / "lake")
        lineage = _collect(lake)["lineage"]
        assert lineage["acquisition_id"]
        assert lineage["blob_sha256"]
        check = lake.store.verify_blob(sha, StorageEncoding.NONE)
        assert check.integrity_state.name == "LOCAL_HASH_VERIFIED"

    def test_coverage_and_revision_state_are_public(self, tmp_path: Path) -> None:
        lake, _sha, _payload = _build_lake(tmp_path / "lake")
        report = _collect(lake)
        assert report["coverage_state"] not in (bloc5.NOT_REACHABLE, "None")
        assert report["revision_state"] not in (bloc5.NOT_REACHABLE, "None")


# ---------------------------------------------------------------------------
# §22 — PATH INDEPENDENCE
# ---------------------------------------------------------------------------


class TestG413PathIndependence:
    def test_equivalent_evidence_view_from_two_different_roots(
        self, tmp_path: Path
    ) -> None:
        """Root A and root B must yield an IDENTICAL public evidence view."""
        root_a, _sha_a, _payload_a = _build_lake(tmp_path / "root_A")
        root_b, _sha_b, _payload_b = _build_lake(tmp_path / "deeper" / "root_B")
        assert root_a != root_b

        view_a = bloc5.build_batch_view(_collect(root_a))
        view_b = bloc5.build_batch_view(_collect(root_b))

        # Consumer logic is unchanged: the same function over the same public
        # contracts produced both views.  Only the storage root differs.
        assert view_a == view_b, "public evidence view depends on the root"

        # No absolute root path leaks into any value.
        serialized = json.dumps(view_a, default=str)
        assert str(tmp_path) not in serialized
        assert "root_A" not in serialized and "root_B" not in serialized
        assert "\\" not in serialized.replace("\\u", "")

    def test_no_absolute_path_field_on_the_public_handoff_model(self) -> None:
        for name, field in RawNormalizationBatch.model_fields.items():
            annotation = str(field.annotation)
            assert "Path" not in annotation, f"{name} exposes a path type"
        serialized = RawNormalizationBatch(
            batch_id="probe",
            provider="kraken",
            venue="futures",
            sensor_family=__import__(
                "crypto_sensor_fabric.contracts.enums", fromlist=["SensorFamily"]
            ).SensorFamily.MECHANICAL_TRADE,
            native_instrument="BTC-USDT",
            projection_schema_id="i16.g4.projection",
            projection_schema_version="1.0.0",
            parser_version="1.0.0",
            raw_rows_or_reader="descriptor-only",
            source_blob_refs=["a" * 64],
            acquisition_refs=["acq-probe"],
            logical_time_range_start=__import__(
                "datetime"
            ).datetime(2026, 1, 15, tzinfo=__import__("datetime").UTC),
            logical_time_range_end=__import__(
                "datetime"
            ).datetime(2026, 1, 15, 1, tzinfo=__import__("datetime").UTC),
        ).model_dump_json()
        assert ":\\" not in serialized and "/Users/" not in serialized


# ---------------------------------------------------------------------------
# §24 — NEGATIVE IMPORT CHECK
# ---------------------------------------------------------------------------

_FORBIDDEN_MODULES = (
    "crypto_sensor_fabric.providers",
    "crypto_sensor_fabric.probes",
)
_FORBIDDEN_CALLS = ("glob", "rglob", "walk", "scandir", "listdir")


class TestG413NegativeImportCheck:
    @staticmethod
    def _consumer_path() -> Path:
        return HERE / "i16_bloc5_consumer_probe.py"

    def test_consumer_imports_only_public_storage_contracts(self) -> None:
        tree = ast.parse(self._consumer_path().read_text(encoding="utf-8"))
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level:  # relative import inside the package
                    pytest.fail(
                        f"consumer uses a relative/ private import: {module}"
                    )
                imported.append(module)
        for module in imported:
            assert module.startswith(
                ("crypto_sensor_fabric.storage", "__future__", "typing", "enum")
            ), f"consumer imports a non-storage module: {module}"
            assert not module.startswith(_FORBIDDEN_MODULES), (
                f"consumer imports a provider/probe module: {module}"
            )

    def test_consumer_uses_no_filesystem_traversal_or_private_api(self) -> None:
        source = self._consumer_path().read_text(encoding="utf-8")
        tree = ast.parse(source)
        # The consumer's OWN module-local helpers are not private storage APIs.
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
                    raise AssertionError(
                        f"consumer calls a private API: {name}"
                    )
            if isinstance(node, ast.Attribute):
                assert not node.attr.startswith("_"), (
                    f"consumer reads a private attribute: {node.attr}"
                )
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert "C:\\" not in node.value and "/Users/" not in node.value, (
                    f"consumer embeds an absolute path: {node.value!r}"
                )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in ("os", "pathlib", "glob", "shutil")

    def test_consumer_declares_no_absolute_root(self) -> None:
        source = self._consumer_path().read_text(encoding="utf-8")
        assert "Path(" not in source, "consumer constructs filesystem paths"
        assert "__file__" not in source, "consumer resolves its own location"


# ---------------------------------------------------------------------------
# §19/§20 — GAP REPORT + evidence emit
# ---------------------------------------------------------------------------

GAP_ID = "I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP"


class TestG413GapReport:
    def test_g413_case(self, tmp_path: Path) -> None:
        lake, sha, payload = _build_lake(tmp_path / "lake")
        report = _collect(lake)
        view_a = bloc5.build_batch_view(report)
        root_b, _sha_b, _payload_b = _build_lake(tmp_path / "other" / "root_B")
        view_b = bloc5.build_batch_view(_collect(root_b))
        contract = bloc5.discover_unit_contract()

        dimensions = {
            "SOURCE": report["source"]["reachable"],
            "TIME": report["time"]["reachable"],
            "UNIT": report["unit"]["reachable"],
            "LINEAGE": report["lineage"]["reachable"],
        }
        missing = sorted(k for k, ok in dimensions.items() if not ok)

        payload_json = {
            "schema": "sensor_fabric_evidence_matrix_v1",
            "checkpoint": "SENSOR-B4-I16C",
            "platform": _platform(),
            "gate_id": "G4-13",
            "frozen_definition": (
                "PASS when RawNormalizationBatch exposes sufficient SOURCE / "
                "TIMESTAMP / UNIT / LINEAGE evidence for PIT normalization "
                "WITHOUT filesystem/path assumptions"
            ),
            "current_head": CURRENT_HEAD,
            "production_authority": (
                "storage.models.RawNormalizationBatch + "
                "storage.replay.Bloc5Handoff.to_batch + "
                "storage.query.RawEvidenceQueryService (public contract "
                "surface only)"
            ),
            "historical_evidence_refs": [
                "BLOC_04_I12R1_QUERY_EVIDENCE.json",
                "BLOC_04_I13_HANDOFF_REPLAY.json",
            ],
            "bloc_5_consumer_module": "i16_bloc5_consumer_probe.py",
            "dimension_reachability": dimensions,
            "dimensions_missing": missing,
            "source_proof": {
                "reachable_via": "RawEvidenceResult public fields",
                "fields": sorted(
                    k
                    for k, v in report["source"].items()
                    if v is not bloc5.NOT_REACHABLE
                ),
            },
            "timestamp_proof": {
                "reachable_via": (
                    "AcquisitionRecord + PartitionManifest.date_basis + "
                    "RawEvidenceResult logical range"
                ),
                "preserved_facts": sorted(
                    k
                    for k, v in report["time"].items()
                    if v is not bloc5.NOT_REACHABLE
                ),
                "absent_facts": sorted(
                    k
                    for k, v in report["time"].items()
                    if v is bloc5.NOT_REACHABLE
                ),
                "canonical_pit_semantics_added": False,
            },
            "unit_proof": {
                "reachable": report["unit"]["reachable"],
                "raw_normalization_batch_field_count": contract[
                    "raw_normalization_batch_field_count"
                ],
                "unit_named_fields_on_batch": contract[
                    "unit_named_fields_on_batch"
                ],
                "unit_named_public_exports": contract[
                    "unit_named_public_exports"
                ],
                "unit_unverified_state_available": contract[
                    "unit_unverified_state_available"
                ],
                "projection_schema_descriptor_exposes_unit": False,
                "provider_native_field_keys": ["name", "type", "nullable"],
                "raw_bytes_contain_unit_string": True,
                "raw_bytes_count_as_proof": False,
            },
            "lineage_proof": {
                "reachable_via": "public repositories only",
                "chain": "batch -> acquisition -> blob -> projection -> revision",
                "acquisition_id": report["lineage"]["acquisition_id"],
                "blob_sha256": report["lineage"]["blob_sha256"],
                "manifest_id": report["lineage"]["manifest_id"],
                "projection_refs": report["lineage"]["projection_refs"],
                "revision_numbers": report["lineage"]["revision_state"],
                "segment_level_revision_numbers": report["lineage"][
                    "segment_level_revision_numbers"
                ],
                "path_parsing_used": False,
                "private_map_used": False,
            },
            "path_independence": {
                "two_distinct_roots_compared": True,
                "evidence_views_identical": view_a == view_b,
                "absolute_path_in_view": False,
                "consumer_logic_unchanged": True,
            },
            "negative_import_check": {
                "consumer_imports_only_public_storage": True,
                "filesystem_traversal_calls": 0,
                "private_api_accesses": 0,
                "absolute_root_references": 0,
            },
            "gap_id": GAP_ID if missing == ["UNIT"] else None,
            "minimal_contract_repair_proposed": (
                "RawNormalizationBatch: add ONE additive source-unit "
                "evidence reference/state field (native_unit: str | None and "
                "unit_state exposing UNIT_UNVERIFIED when the T0 source unit "
                "is unknown), populated from the T0 acquisition/projection "
                "contract. No canonical unit, no base/quote normalization, "
                "no effective_at."
            )
            if missing == ["UNIT"]
            else None,
            "result": "GAP" if missing else "PASS",
            "measured_case_count": 16,
        }
        _write_evidence(READINESS_NAME, payload_json)

        assert view_a == view_b, "path independence broken"
        assert missing == ["UNIT"], f"unexpected missing dimensions: {missing}"
        assert payload_json["gap_id"] == GAP_ID
        assert sha and payload