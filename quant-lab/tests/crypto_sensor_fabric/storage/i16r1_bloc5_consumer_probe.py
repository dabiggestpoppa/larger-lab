"""TEST-ONLY Bloc 5 downstream consumer probe — SENSOR-B4-I16R1.

Successor of ``i16_bloc5_consumer_probe`` (the frozen I16 negative probe).
This module represents what Bloc 5 does when it receives the repaired
handoff, and it is deliberately NARROW and DEPENDENT ONLY ON PUBLIC
CONTRACTS:

  * it imports only ``crypto_sensor_fabric.storage`` public names,
  * it performs no filesystem glob / rglob / walk,
  * it reads no absolute path and no private storage attribute,
  * it calls no provider adapter package and no normalization package.

It starts from the public handoff object (``RawNormalizationBatch``) and
answers SOURCE / TIME / UNIT / LINEAGE / coverage / revision through public
typed contracts only.  For UNIT it reports exactly the durable source-unit
evidence the batch carries — including the explicit ``UNIT_UNVERIFIED``
state — and it never manufactures a lexeme.  ``resolved_schema_declaration_
matches_batch`` independently re-resolves the batch's declared
``projection_schema_id`` / ``projection_schema_version`` against the durable
projection-schema registry and compares, so the test can prove the evidence
was not patched onto the batch.
"""

from __future__ import annotations

from typing import Any

# PUBLIC storage contract surface only (SENSOR-B4-I16R1 §13/§14).
from crypto_sensor_fabric.storage import (
    AcquisitionRepository,
    BlobMetadataRepository,
    PartitionManifestRepository,
    ProjectionSchemaRegistry,
    RawNormalizationBatch,
    RawProjectionReader,
    SourceUnitState,
)

SOURCE = "source"
TIME = "time"
UNIT = "unit"
LINEAGE = "lineage"

NOT_REACHABLE = "NOT_REACHABLE"

# The timestamp facts Bloc 4 may preserve.  ``FIELD_PUBLICLY_AVAILABLE`` is
# measured from the public acquisition contract; ``FIXTURE_VALUE_PRESENT``
# records whether this particular fixture actually set a value (§18: an
# unset fixture value is NOT a structurally unavailable field).
_PROVIDER_LEXICAL_TIME_FACTS = (
    "provider_time_raw",
    "provider_time_parsed",
    "provider_time_unit_assumption",
    "provider_publication_time",
)


def _unit_entries(batch: RawNormalizationBatch) -> list[dict[str, Any]]:
    """The batch's durable source-unit evidence, verbatim, in order."""
    return [
        {
            "field_name": evidence.field_name,
            "state": evidence.state.value,
            "native_unit_lexeme": evidence.native_unit_lexeme,
        }
        for evidence in batch.source_unit_evidence
    ]


def collect_handoff_evidence(
    *,
    batch: RawNormalizationBatch,
    acquisitions: AcquisitionRepository,
    blobs: BlobMetadataRepository,
    manifests: PartitionManifestRepository,
    schemas: ProjectionSchemaRegistry,
    projection_reader: RawProjectionReader | None = None,
    projection_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Collect the Bloc 5 evidence a PIT normalization pass needs.

    Every value is read through a public typed contract.  Anything a public
    contract does not expose is reported as ``NOT_REACHABLE``.
    """
    report: dict[str, Any] = {
        SOURCE: {"reachable": False},
        TIME: {"reachable": False},
        UNIT: {"reachable": False},
        LINEAGE: {"reachable": False},
        "coverage_state": NOT_REACHABLE,
        "revision_state": NOT_REACHABLE,
    }

    # -- SOURCE identity: public on the handoff batch ----------------------
    report[SOURCE] = {
        "reachable": True,
        "provider": batch.provider,
        "venue": batch.venue,
        "sensor_family": str(batch.sensor_family),
        "native_instrument": batch.native_instrument,
        "source_granularity": (
            str(batch.source_granularity)
            if batch.source_granularity is not None
            else NOT_REACHABLE
        ),
        "projection_schema_id": batch.projection_schema_id,
        "projection_schema_version": batch.projection_schema_version,
        "parser_version": batch.parser_version,
        "raw_rows_or_reader": batch.raw_rows_or_reader,
    }

    # -- UNIT evidence: the repaired dimension -----------------------------
    entries = _unit_entries(batch)
    resolved_declaration: list[dict[str, Any]] = []
    schema_resolved = True
    try:
        definition = schemas.resolve_by_id(
            batch.projection_schema_id, batch.projection_schema_version
        )
        resolved_declaration = [
            {
                "field_name": evidence.field_name,
                "state": evidence.state.value,
                "native_unit_lexeme": evidence.native_unit_lexeme,
            }
            for evidence in definition.source_unit_evidence
        ]
    except Exception:  # noqa: BLE001 - unresolvable schema is a typed absence
        schema_resolved = False
    report[UNIT] = {
        "reachable": True,
        "entries": entries,
        "declared_field_count": len(entries),
        "verified_native_fields": [
            entry["field_name"]
            for entry in entries
            if entry["state"] == SourceUnitState.VERIFIED_NATIVE.value
        ],
        "unverified_fields": [
            entry["field_name"]
            for entry in entries
            if entry["state"] == SourceUnitState.UNIT_UNVERIFIED.value
        ],
        "guessed_values": [
            entry["native_unit_lexeme"]
            for entry in entries
            if entry["state"] == SourceUnitState.UNIT_UNVERIFIED.value
            and entry["native_unit_lexeme"] is not None
        ],
        "schema_resolved": schema_resolved,
        "resolved_schema_declaration_matches_batch": (
            schema_resolved and resolved_declaration == entries
        ),
        "canonical_unit_decisions": 0,
    }

    # -- TIME evidence: preserved T0 facts, never canonical PIT semantics --
    time_evidence: dict[str, Any] = {"reachable": True}
    manifest = None
    partition_key = (
        f"{batch.provider}/{batch.venue}/{batch.native_instrument}/"
        f"{batch.logical_time_range_start.date().isoformat()}"
    )
    try:
        manifest = manifests.get_current_manifest(partition_key)
    except Exception:  # noqa: BLE001 - absent manifest is a typed absence
        manifest = None
    time_evidence["logical_time_range_start"] = (
        batch.logical_time_range_start.isoformat()
    )
    time_evidence["logical_time_range_end"] = (
        batch.logical_time_range_end.isoformat()
    )
    first_acquisition = None
    if batch.acquisition_refs:
        first_acquisition = acquisitions.get_acquisition(batch.acquisition_refs[0])
    if first_acquisition is not None:
        time_evidence["requested_start"] = (
            first_acquisition.requested_start.isoformat()
        )
        time_evidence["requested_end"] = first_acquisition.requested_end.isoformat()
        time_evidence["request_started_at"] = (
            first_acquisition.request_started_at.isoformat()
        )
        time_evidence["response_observed_at"] = (
            first_acquisition.response_observed_at.isoformat()
        )
        time_evidence["ingested_at"] = first_acquisition.ingested_at.isoformat()
        actual_start = first_acquisition.actual_start
        actual_end = first_acquisition.actual_end
        time_evidence["actual_start"] = (
            actual_start.isoformat() if actual_start else NOT_REACHABLE
        )
        time_evidence["actual_end"] = (
            actual_end.isoformat() if actual_end else NOT_REACHABLE
        )
        time_evidence["actual_start_field_publicly_available"] = (
            "actual_start" in type(first_acquisition).model_fields
        )
        time_evidence["actual_end_field_publicly_available"] = (
            "actual_end" in type(first_acquisition).model_fields
        )
        time_evidence["actual_start_fixture_value_present"] = actual_start is not None
        time_evidence["actual_end_fixture_value_present"] = actual_end is not None
    else:
        time_evidence["acquisitions_resolved"] = 0
    time_evidence["date_basis"] = (
        str(manifest.date_basis) if manifest is not None else NOT_REACHABLE
    )
    time_evidence["manifest_id"] = (
        manifest.partition_manifest_id if manifest is not None else NOT_REACHABLE
    )
    for absent in _PROVIDER_LEXICAL_TIME_FACTS:
        time_evidence[absent] = NOT_REACHABLE
    report[TIME] = time_evidence

    # -- LINEAGE: batch -> acquisition -> blob -> projection -> revision ---
    lineage: dict[str, Any] = {
        "reachable": False,
        "acquisition_refs": list(batch.acquisition_refs),
        "source_blob_refs": list(batch.source_blob_refs),
        "path_parsing_used": False,
        "private_map_used": False,
    }
    if batch.acquisition_refs and batch.source_blob_refs:
        acquisition = acquisitions.get_acquisition(batch.acquisition_refs[0])
        blob_meta = blobs.get_blob_metadata(batch.source_blob_refs[0])
        lineage.update(
            {
                "reachable": True,
                "acquisition_id": acquisition.acquisition_id,
                "acquisition_blob_ref": acquisition.blob_sha256,
                "blob_sha256": batch.source_blob_refs[0],
                "blob_metadata_resolved": bool(blob_meta),
                "blob_storage_encoding": (
                    str(blob_meta[0].storage_encoding) if blob_meta else NOT_REACHABLE
                ),
                "manifest_id": lineage.get("manifest_id", NOT_REACHABLE),
            }
        )
        lineage["manifest_id"] = (
            manifest.partition_manifest_id if manifest is not None else NOT_REACHABLE
        )
        projection_lineage: list[dict[str, Any]] = []
        if projection_reader is not None and projection_ids:
            lineage["projection_lineage_reachable"] = True
            lineage["projection_refs"] = list(projection_ids)
            for projection_id in projection_ids:
                metadata = projection_reader.projection_metadata(projection_id)
                projection_lineage.append(
                    {
                        "projection_id": metadata["projection_id"],
                        "projection_schema_id": metadata["projection_schema_id"],
                        "projection_schema_version": metadata[
                            "projection_schema_version"
                        ],
                        "source_lineage_count": len(metadata["source_lineage"]),
                        "schema_matches_batch": (
                            metadata["projection_schema_id"]
                            == batch.projection_schema_id
                            and metadata["projection_schema_version"]
                            == batch.projection_schema_version
                        ),
                    }
                )
        else:
            lineage["projection_lineage_reachable"] = False
        lineage["projection_lineage"] = projection_lineage
    report[LINEAGE] = lineage

    report["coverage_state"] = str(batch.coverage_state)
    report["revision_state"] = str(batch.revision_state)
    report["revision_state_public_api"] = "RawNormalizationBatch.revision_state"
    report["quality_flags"] = [str(flag) for flag in batch.quality_flags]
    return report


def build_batch_view(report: dict[str, Any]) -> dict[str, Any]:
    """The public evidence VIEW a Bloc 5 pass starts from.

    Built from the same public contracts with no filesystem assumption and
    no absolute path; the path-independence proof compares this view across
    two different storage roots.
    """
    unit = report[UNIT]
    return {
        "source": {
            key: value
            for key, value in report[SOURCE].items()
            if key != "raw_rows_or_reader"
        },
        "time": {
            key: value
            for key, value in report[TIME].items()
            if key != "date_basis" and key != "manifest_id"
        },
        "unit": {
            "entries": unit["entries"],
            "declared_field_count": unit["declared_field_count"],
            "verified_native_fields": unit["verified_native_fields"],
            "unverified_fields": unit["unverified_fields"],
            "guessed_values": unit["guessed_values"],
            "canonical_unit_decisions": unit["canonical_unit_decisions"],
        },
        "lineage": {
            key: value
            for key, value in report[LINEAGE].items()
            if key not in ("manifest_id",)
        },
        "coverage_state": report["coverage_state"],
        "revision_state": report["revision_state"],
    }


__all__ = [
    "LINEAGE",
    "NOT_REACHABLE",
    "SOURCE",
    "TIME",
    "UNIT",
    "build_batch_view",
    "collect_handoff_evidence",
]
