"""TEST-ONLY Bloc 5 downstream consumer probe — SENSOR-B4-I16 §23/§24.

This module represents what Bloc 5 would do when it receives the frozen
Bloc 4 handoff.  It is deliberately NARROW and deliberately DEPENDENT ONLY
ON PUBLIC CONTRACTS:

  * it imports only ``crypto_sensor_fabric.storage`` public names,
  * it performs no filesystem glob / rglob / walk,
  * it reads no absolute path and no private storage attribute,
  * it calls no provider adapter package.

It answers one question per required evidence dimension and never guesses:
when a dimension is not reachable through a public typed contract it reports
``NOT_REACHABLE`` rather than inventing a value.  ``UNIT_UNVERIFIED`` is a
value Bloc 4 would have to *supply*; this consumer never manufactures it.
"""

from __future__ import annotations

from typing import Any

# PUBLIC storage contract surface only (SENSOR-B4-I16 §23/§24).
from crypto_sensor_fabric.storage import (  # noqa: F401
    AcquisitionRecord,
    AcquisitionRepository,
    BlobMetadataRepository,
    CoverageState,
    LocalBlobStore,
    PartitionManifestRepository,
    ProjectionSchemaDefinition,
    ProjectionSchemaRegistry,
    RawEvidenceQuery,
    RawEvidenceQueryService,
    RawNormalizationBatch,
    RevisionResolver,
    RevisionState,
    SourceRevision,
    StorageEncoding,
)

# The four dimensions the frozen Bloc 4 -> Bloc 5 handoff must carry.
SOURCE = "source"
TIME = "time"
UNIT = "unit"
LINEAGE = "lineage"

NOT_REACHABLE = "NOT_REACHABLE"

# Field-name families that would carry a SOURCE unit through a public typed
# contract.  This is a NAME SEARCH over the public models a Bloc 5 consumer
# can actually see; it is not a claim that bytes contain the answer.
_UNIT_FIELD_TOKENS = (
    "unit",
    "units",
    "native_unit",
    "provider_unit",
    "unit_state",
    "quote_unit",
    "base_unit",
    "measurement_unit",
)


def _public_field_names(model: Any) -> set[str]:
    """Field names of a public pydantic model, via its public API only."""
    fields = getattr(model, "model_fields", None)
    if fields is None:
        return set()
    return set(fields)


def discover_unit_contract() -> dict[str, Any]:
    """Search the PUBLIC storage models for any source-unit field.

    Returns the measured answer rather than an assumption: which public models
    were inspected, which unit-named fields exist, and whether any public
    unit-state vocabulary (``UNIT_UNVERIFIED`` and friends) is exported.
    """
    inspected = {
        "RawNormalizationBatch": _public_field_names(RawNormalizationBatch),
        "AcquisitionRecord": _public_field_names(AcquisitionRecord),
        "SourceRevision": _public_field_names(SourceRevision),
        "ProjectionSchemaDefinition": _public_field_names(
            ProjectionSchemaDefinition
        ),
    }
    batch_fields = inspected["RawNormalizationBatch"]
    unit_fields = sorted(
        name
        for name in batch_fields
        if any(token in name.lower() for token in _UNIT_FIELD_TOKENS)
    )

    import crypto_sensor_fabric.storage as public_storage

    exported = sorted(getattr(public_storage, "__all__", ()))
    unit_exports = sorted(
        name
        for name in exported
        if "unit" in name.lower()
    )
    unit_unverified_available = any(
        "UNIT_UNVERIFIED" in str(getattr(obj, "__members__", {}))
        for obj in vars(public_storage).values()
        if isinstance(obj, type) and issubclass(obj, __import__("enum").Enum)
    )
    return {
        "public_models_inspected": sorted(inspected),
        "raw_normalization_batch_field_count": len(batch_fields),
        "raw_normalization_batch_fields": sorted(batch_fields),
        "unit_named_fields_on_batch": unit_fields,
        "unit_named_public_exports": unit_exports,
        "unit_unverified_state_available": unit_unverified_available,
        "reachable": bool(unit_fields) or bool(unit_exports),
    }


def collect_evidence(
    *,
    service: RawEvidenceQueryService,
    acquisitions: AcquisitionRepository,
    blobs: BlobMetadataRepository,
    manifests: PartitionManifestRepository,
    registry: Any,
    schemas: ProjectionSchemaRegistry,
    query: RawEvidenceQuery,
) -> dict[str, Any]:
    """Collect the Bloc 5 evidence a normalization pass would need.

    Every value below is read through a PUBLIC typed contract.  Anything a
    public contract does not expose is reported as ``NOT_REACHABLE``.
    """
    outcome = service.execute(query)
    report: dict[str, Any] = {
        SOURCE: {"reachable": False},
        TIME: {"reachable": False},
        UNIT: {"reachable": False},
        LINEAGE: {"reachable": False},
        "coverage_state": NOT_REACHABLE,
        "revision_state": NOT_REACHABLE,
        "results": 0,
    }
    if not outcome.results:
        report["reason"] = "no_matching_evidence"
        return report

    report["results"] = len(outcome.results)
    result = outcome.results[0]
    acq = acquisitions.get_acquisition(result.acquisition_ids[0])

    # The manifest is resolved through the PUBLIC manifest repository by the
    # partition key carried on the result's own identity, never by parsing a
    # path or reading a private field.
    partition_key = (
        f"{result.provider}/{result.venue}/{result.native_instrument}/"
        f"{result.logical_time_start.date().isoformat()}"
    )
    try:
        manifest = manifests.get_current_manifest(partition_key)
        date_basis: Any = manifest.date_basis
        manifest_id: Any = manifest.partition_manifest_id
        manifest_version: Any = manifest.manifest_version
    except Exception:  # noqa: BLE001 - absent manifest is a typed absence
        date_basis = NOT_REACHABLE
        manifest_id = NOT_REACHABLE
        manifest_version = NOT_REACHABLE

    # -- SOURCE identity: fully public on the query result -----------------
    report[SOURCE] = {
        "reachable": True,
        "provider": result.provider,
        "venue": result.venue,
        "sensor_family": str(result.sensor_family),
        "native_instrument": result.native_instrument,
        "source_granularity": (
            str(result.source_granularity)
            if result.source_granularity is not None
            else NOT_REACHABLE
        ),
        "projection_refs": list(result.projection_refs or []),
    }

    # -- TIME evidence: preserved T0 facts, never canonical PIT semantics --
    report[TIME] = {
        "reachable": True,
        "requested_start": acq.requested_start.isoformat(),
        "requested_end": acq.requested_end.isoformat(),
        "actual_start": (
            acq.actual_start.isoformat() if acq.actual_start else NOT_REACHABLE
        ),
        "actual_end": (
            acq.actual_end.isoformat() if acq.actual_end else NOT_REACHABLE
        ),
        "request_started_at": acq.request_started_at.isoformat(),
        "response_observed_at": acq.response_observed_at.isoformat(),
        "ingested_at": acq.ingested_at.isoformat(),
        "date_basis": str(date_basis),
        "logical_time_start": result.logical_time_start.isoformat(),
        "logical_time_end": result.logical_time_end.isoformat(),
        "provider_time_raw": NOT_REACHABLE,
        "provider_time_parsed": NOT_REACHABLE,
        "provider_time_unit_assumption": NOT_REACHABLE,
        "provider_publication_time": NOT_REACHABLE,
    }

    # -- UNIT evidence: the decisive dimension ------------------------------
    unit_contract = discover_unit_contract()
    artifact_schema_units: list[str] = []
    try:
        definition = schemas.resolve_by_id("i16.g4.projection", "1.0.0")
    except Exception:  # noqa: BLE001 - absent schema is a typed absence
        definition = None
    if definition is not None:
        descriptor = definition.to_descriptor()
        for field in descriptor.get("provider_native_fields", []):
            if any(token in str(field).lower() for token in _UNIT_FIELD_TOKENS):
                artifact_schema_units.append(
                    f"provider_native_field.{field.get('name')}"
                )
    report[UNIT] = {
        "reachable": bool(unit_contract["reachable"] or artifact_schema_units),
        "contract_probe": unit_contract,
        "schema_native_field_units": artifact_schema_units,
        "native_unit": NOT_REACHABLE,
        "unit_state": NOT_REACHABLE,
        "UNIT_UNVERIFIED_supplied_by_bloc4": False,
    }

    # -- LINEAGE: batch -> acquisition -> blob -> projection -> revision -----
    blob_meta = blobs.get_blob_metadata(result.blob_refs[0])
    report[LINEAGE] = {
        "reachable": True,
        "acquisition_id": acq.acquisition_id,
        "acquisition_blob_ref": acq.blob_sha256,
        "blob_sha256": result.blob_refs[0],
        "blob_storage_encoding": str(blob_meta[0].storage_encoding),
        "manifest_id": manifest_id,
        "manifest_version": manifest_version,
        "partition_key": partition_key,
        "lineage_refs": list(result.lineage_refs),
        "projection_refs": list(result.projection_refs or []),
        "revision_state": str(result.revision_state),
        "revision_state_public_type": str(RevisionState.STABLE),
        "segment_level_revision_numbers": NOT_REACHABLE,
        "segment_level_note": (
            "SourceRevisionRegistry / RevisionSourceIdentityV1 are NOT in "
            "crypto_sensor_fabric.storage.__all__; Bloc 5 reads revision "
            "state through the public RawEvidenceResult.revision_state and "
            "the public RevisionState vocabulary."
        ),
    }

    report["coverage_state"] = str(result.coverage_state)
    report["revision_state"] = str(result.revision_state)
    report["revision_state_public_api"] = "RawEvidenceResult.revision_state"
    report["quality_flags"] = [str(f) for f in result.quality_flags]
    return report


def build_batch_view(report: dict[str, Any]) -> dict[str, Any]:
    """The public evidence VIEW a Bloc 5 pass would start from.

    Built from the same public contracts, with no filesystem assumption and
    no absolute path: this is what the path-independence proof compares
    across two different storage roots.
    """
    return {
        "source": report[SOURCE],
        "time": report[TIME],
        "unit_state": report[UNIT].get("unit_state", NOT_REACHABLE),
        "unit_reachable": report[UNIT]["reachable"],
        "lineage": report[LINEAGE],
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
    "collect_evidence",
    "discover_unit_contract",
]

# Referenced so the public imports are not mistaken for dead code by linters.
_PUBLIC_TYPES = (
    LocalBlobStore,
    PartitionManifestRepository,
    StorageEncoding,
    CoverageState,
)