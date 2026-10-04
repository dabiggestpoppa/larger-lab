"""TEST-ONLY Bloc 5 downstream consumer probe — SENSOR-B4-I16R2.

Successor of ``i16r1_bloc5_consumer_probe`` (the accepted I16R1 probe).  This
module represents what Bloc 5 does with the repaired unit handoff, and it is
deliberately NARROW and DEPENDENT ONLY ON PUBLIC CONTRACTS:

  * it imports only ``crypto_sensor_fabric.storage`` public names,
  * it performs no filesystem glob / rglob / walk,
  * it reads no absolute path and no private storage attribute,
  * it calls no provider adapter package and no normalization package,
  * it NEVER scans projection rows — unit truth is established at the T0B
    commit boundary and is only INTERPRETED here.

The consumer must distinguish five unit states from public typed data:

    STATIC_VERIFIED                 a proven batch-level native lexeme
    UNIT_UNVERIFIED                 explicit unknown, never a guessed value
    ROW_NATIVE_LOCATION             durable per-row/per-level unit location
    NO_UNIT_FIELDS                  explicit declaration: no unit field
    HISTORICAL_UNIT_CONTRACT_ABSENT absent declaration (old descriptors)

``resolved_schema_declaration_matches_batch`` independently re-resolves the
batch's declared schema against the public registry and compares, so a test
can prove the evidence was copied from the durable contract and not patched
onto the batch.
"""

from __future__ import annotations

from typing import Any

# PUBLIC storage contract surface only (SENSOR-B4-I16R2 §22).
from crypto_sensor_fabric.storage import (
    ProjectionSchemaRegistry,
    RawNormalizationBatch,
    SourceUnitContract,
    SourceUnitState,
    SourceUnitVariability,
)

STATIC_VERIFIED = "STATIC_VERIFIED"
UNIT_UNVERIFIED = "UNIT_UNVERIFIED"
ROW_NATIVE_LOCATION = "ROW_NATIVE_LOCATION"

NO_UNIT_FIELDS = "NO_UNIT_FIELDS"
UNIT_EVIDENCE_DECLARED = "UNIT_EVIDENCE_DECLARED"
HISTORICAL_UNIT_CONTRACT_ABSENT = "HISTORICAL_UNIT_CONTRACT_ABSENT"


def _entry_view(evidence: Any) -> dict[str, Any]:
    """One public evidence entry, classified for Bloc 5."""
    if evidence.field_path is not None:
        field_path = list(evidence.field_path)
    else:
        field_path = [evidence.field_name]
    if evidence.state == SourceUnitState.VERIFIED_NATIVE:
        classification = STATIC_VERIFIED
    elif evidence.variability == SourceUnitVariability.ROW_NATIVE:
        classification = ROW_NATIVE_LOCATION
    else:
        classification = UNIT_UNVERIFIED
    return {
        "field_path": field_path,
        "state": evidence.state.value,
        "variability": (
            evidence.variability.value
            if evidence.variability is not None
            else None
        ),
        "native_unit_lexeme": evidence.native_unit_lexeme,
        "classification": classification,
    }


def unit_evidence_view(
    batch: RawNormalizationBatch,
    *,
    schemas: ProjectionSchemaRegistry | None = None,
) -> dict[str, Any]:
    """The public UNIT view a Bloc 5 pass starts from.

    Everything is read through public typed contracts on the handoff batch
    (and optionally the public schema registry); no row payload is read here.
    """
    entries = [_entry_view(evidence) for evidence in batch.source_unit_evidence]
    if batch.source_unit_contract == SourceUnitContract.NO_UNIT_FIELDS:
        contract_state = NO_UNIT_FIELDS
    elif batch.source_unit_contract == SourceUnitContract.UNIT_EVIDENCE_DECLARED:
        contract_state = UNIT_EVIDENCE_DECLARED
    elif entries:
        # I16R1-era explicit declaration list (no marker key).
        contract_state = UNIT_EVIDENCE_DECLARED
    else:
        contract_state = HISTORICAL_UNIT_CONTRACT_ABSENT
    view = {
        "contract_state": contract_state,
        "entries": entries,
        "static_verified": [
            entry for entry in entries if entry["classification"] == STATIC_VERIFIED
        ],
        "unverified": [
            entry for entry in entries if entry["classification"] == UNIT_UNVERIFIED
        ],
        "row_native_locations": [
            entry
            for entry in entries
            if entry["classification"] == ROW_NATIVE_LOCATION
        ],
        "no_unit_bearing_fields": contract_state == NO_UNIT_FIELDS,
        "historical_contract_absent": (
            contract_state == HISTORICAL_UNIT_CONTRACT_ABSENT
        ),
        "guessed_values": [
            entry["native_unit_lexeme"]
            for entry in entries
            if entry["classification"] == UNIT_UNVERIFIED
            and entry["native_unit_lexeme"] is not None
        ],
        "canonical_unit_decisions": 0,
    }
    if schemas is not None:
        try:
            definition = schemas.resolve_by_id(
                batch.projection_schema_id, batch.projection_schema_version
            )
        except Exception:  # noqa: BLE001 - unresolvable schema is a typed absence
            view["schema_resolved"] = False
            view["resolved_schema_declaration_matches_batch"] = False
            view["resolved_contract_matches_batch"] = False
        else:
            resolved = [
                _entry_view(evidence) for evidence in definition.source_unit_evidence
            ]
            view["schema_resolved"] = True
            view["resolved_schema_declaration_matches_batch"] = resolved == entries
            view["resolved_contract_matches_batch"] = (
                definition.source_unit_contract == batch.source_unit_contract
            )
    return view


__all__ = [
    "HISTORICAL_UNIT_CONTRACT_ABSENT",
    "NO_UNIT_FIELDS",
    "ROW_NATIVE_LOCATION",
    "STATIC_VERIFIED",
    "UNIT_EVIDENCE_DECLARED",
    "UNIT_UNVERIFIED",
    "unit_evidence_view",
]
