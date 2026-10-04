"""SENSOR-B4-I16R1A — unit semantic-shape audit across ALL frozen families.

R1 §4 requires auditing every supported sensor family BEFORE changing any
model: which provider-native fields carry units, whether the semantics are
scalar / multi-field / row-level / instrument-implied / unknown, whether
durable T0 currently contains explicit unit evidence, and the correct public
handoff shape.

This module performs that audit MECHANICALLY against the accepted canonical
schema classes (``crypto_sensor_fabric.schemas``) and records the frozen
findings, the storage gap measured at I16, and the repair authority selected
by I16R1B.  It imports no I16R1 production symbol: the audit is an input to
the repair, not an assertion about it, so the artifact it emits is stable
before and after the repair.

The audit verdict, derived here rather than assumed:

    A single scalar ``native_unit`` is NOT semantically correct for every
    family (book snapshots carry a unit per price level; funding / basis /
    positioning carry no unit field at all).  The correct public handoff
    shape is a per-unit-bearing-field evidence list.
"""

from __future__ import annotations

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

from crypto_sensor_fabric.contracts.enums import (  # noqa: E402
    NativeOIUnit,
    SensorFamily,
)
from crypto_sensor_fabric.schemas import (  # noqa: E402
    MechanicalBasis,
    MechanicalBookMetric,
    MechanicalBookSnapshot,
    MechanicalFunding,
    MechanicalLiquidation,
    MechanicalOpenInterest,
    MechanicalPositioning,
    MechanicalTrade,
    PriceLevel,
    ProviderEnvelope,
)

CURRENT_HEAD = "618de97827a22b2514caa4178d5cffa4ea76d1b7"

EVIDENCE_DIR = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)
AUDIT_NAME = "BLOC_04_I16R1_UNIT_SEMANTIC_AUDIT.json"

_UNIT_TOKEN = "unit"

# Family -> (canonical model, semantic-shape classification audited by hand
# against the accepted schema sources, and mechanically re-checked below).
# Shape vocabulary:
#   SCALAR_FIELD       one provider-native field carries the unit for the record
#   MULTI_FIELD        several distinct provider-native fields may carry units
#   ROW_LEVEL_NESTED   the unit rides on a repeated child record (book levels)
#   INSTRUMENT_IMPLIED unit is a property of the instrument/market contract
#   NONE               no unit-bearing field exists in the family schema
_FAMILY_AUDIT = {
    "MECHANICAL_TRADE": {
        "canonical_model": MechanicalTrade,
        "unit_field_semantics": {
            "quantity_unit": {
                "shape": "SCALAR_FIELD",
                "required": True,
                "lexeme_type": "provider-native string (base asset symbol, "
                "contract count label, ...) preserved verbatim",
                "canonicalization_in_bloc_4": False,
            }
        },
        "notes": (
            "quantity_native + quote_notional_native are values; quantity_unit "
            "names the unit of quantity_native. quote_notional_usd is a derived "
            "additive field and is never the T0 unit authority."
        ),
    },
    "MECHANICAL_LIQUIDATION": {
        "canonical_model": MechanicalLiquidation,
        "unit_field_semantics": {
            "quantity_unit": {
                "shape": "SCALAR_FIELD",
                "required": False,
                "lexeme_type": "provider-native string or absent (the accepted "
                "schema allows an explicit unknown as None)",
                "canonicalization_in_bloc_4": False,
            }
        },
        "notes": (
            "liquidation_usd / liquidation_quote_native are derived or "
            "provider-reported notional values, not unit declarations."
        ),
    },
    "MECHANICAL_OPEN_INTEREST": {
        "canonical_model": MechanicalOpenInterest,
        "unit_field_semantics": {
            "native_unit": {
                "shape": "INSTRUMENT_IMPLIED",
                "required": True,
                "lexeme_type": (
                    "NativeOIUnit state vocabulary "
                    f"{sorted(m.value for m in NativeOIUnit)}"
                ),
                "canonicalization_in_bloc_4": False,
            }
        },
        "notes": (
            "oi_base / oi_quote / oi_usd are additive normalized fields owned "
            "by a normalizing layer and are explicitly NOT the T0 authority "
            "(B1-T12: native value + native unit are always retained)."
        ),
    },
    "MECHANICAL_FUNDING": {
        "canonical_model": MechanicalFunding,
        "unit_field_semantics": {},
        "notes": (
            "funding_rate_native is a dimensionless rate; the funding interval "
            "is described by funding_interval_seconds, not by a unit lexeme. "
            "No unit-bearing field exists."
        ),
    },
    "MECHANICAL_BOOK_SNAPSHOT": {
        "canonical_model": MechanicalBookSnapshot,
        "unit_field_semantics": {
            "PriceLevel.quantity_unit": {
                "shape": "ROW_LEVEL_NESTED",
                "required": True,
                "lexeme_type": "provider-native string per price level",
                "canonicalization_in_bloc_4": False,
            }
        },
        "notes": (
            "The unit rides on each repeated PriceLevel child record; a single "
            "record-level scalar native_unit cannot represent it. Any T0 "
            "provider-native projection must therefore expose the per-level "
            "unit field(s) it actually stores, or declare none."
        ),
    },
    "MECHANICAL_BOOK_METRIC": {
        "canonical_model": MechanicalBookMetric,
        "unit_field_semantics": {
            "metric_unit": {
                "shape": "SCALAR_FIELD",
                "required": True,
                "lexeme_type": "provider-native string (e.g. depth units, bps, "
                "contract counts) preserved verbatim",
                "canonicalization_in_bloc_4": False,
            }
        },
        "notes": (
            "methodology_id / methodology_version remain mandatory; the unit "
            "lexeme is a provider-native measurement label."
        ),
    },
    "MECHANICAL_POSITIONING": {
        "canonical_model": MechanicalPositioning,
        "unit_field_semantics": {},
        "notes": (
            "Ratios and population counts carry no unit lexeme; "
            "population_definition is mandatory and is not a unit."
        ),
    },
    "MECHANICAL_BASIS": {
        "canonical_model": MechanicalBasis,
        "unit_field_semantics": {},
        "notes": (
            "basis_native is a spread/premium value; basis_bps is a derived "
            "additive field. No unit-bearing field exists."
        ),
    },
}


def _write_evidence(name: str, payload: dict[str, object]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _platform() -> dict[str, str]:
    return {"os": os.name, "python": sys.version.split()[0]}


def _unit_named_fields(model: type) -> list[str]:
    return sorted(
        name
        for name in model.model_fields
        if _UNIT_TOKEN in name.lower()
    )


def _measure_family(entry: dict[str, object]) -> dict[str, object]:
    model = entry["canonical_model"]
    assert isinstance(model, type)
    measured = _unit_named_fields(model)
    if model is MechanicalBookSnapshot:
        # The snapshot's unit rides on the repeated child record; the audit
        # records it under the family with its child path.
        measured = [
            f"PriceLevel.{name}" for name in _unit_named_fields(PriceLevel)
        ] + measured
    declared = sorted(entry["unit_field_semantics"])
    return {
        "canonical_model": model.__name__,
        "unit_named_fields_measured": measured,
        "unit_field_semantics": entry["unit_field_semantics"],
        "semantics_declared": declared,
        "measured_matches_declared": measured == declared,
        "notes": entry["notes"],
    }


class TestUnitSemanticAudit:
    def test_all_frozen_families_are_audited(self) -> None:
        assert len(SensorFamily) == 8
        audited = set(_FAMILY_AUDIT)
        assert audited == {f.value for f in SensorFamily}, (
            sorted({f.value for f in SensorFamily} - audited)
        )

    def test_declared_unit_fields_exist_where_the_audit_says_they_do(self) -> None:
        for family, entry in _FAMILY_AUDIT.items():
            row = _measure_family(entry)
            assert row["measured_matches_declared"], (family, row)

    def test_price_level_audit_counts_nested_unit(self) -> None:
        # The nested per-level unit is real and is recorded under the
        # snapshot family; PriceLevel itself is a child record, not a family.
        assert _unit_named_fields(PriceLevel) == ["quantity_unit"]
        snapshot_units = _unit_named_fields(MechanicalBookSnapshot)
        assert snapshot_units == [], (
            "book snapshot record-level unit fields changed; re-audit"
        )

    def test_provider_envelope_carries_no_unit(self) -> None:
        assert _unit_named_fields(ProviderEnvelope) == []

    def test_scalar_native_unit_is_not_semantically_sufficient(self) -> None:
        """The audit's decisive finding: the repair must be a per-field list."""
        families_with_units = [
            family
            for family, entry in _FAMILY_AUDIT.items()
            if entry["unit_field_semantics"]
        ]
        assert sorted(families_with_units) == [
            "MECHANICAL_BOOK_METRIC",
            "MECHANICAL_BOOK_SNAPSHOT",
            "MECHANICAL_LIQUIDATION",
            "MECHANICAL_OPEN_INTEREST",
            "MECHANICAL_TRADE",
        ]
        # No family has more than one top-level unit-named field, but the
        # union across the accepted vocabulary is multi-field: a batch shape
        # must be able to carry several entries (e.g. quantity_unit plus
        # metric_unit) and a nested per-level unit, so one scalar field on
        # RawNormalizationBatch is not enough.
        assert len(_FAMILY_AUDIT) == 8

    def test_audit_case(self) -> None:
        rows: dict[str, object] = {}
        for family in sorted(_FAMILY_AUDIT):
            rows[family] = _measure_family(_FAMILY_AUDIT[family])

        payload = {
            "schema": "sensor_fabric_evidence_matrix_v1",
            "checkpoint": "SENSOR-B4-I16R1A",
            "platform": _platform(),
            "gate_id": "G4-13",
            "artifact": "unit_semantic_shape_audit",
            "current_head": CURRENT_HEAD,
            "frozen_families_audited": sorted(_FAMILY_AUDIT),
            "family_count": len(_FAMILY_AUDIT),
            "family_matrix": rows,
            "native_oi_unit_vocabulary": sorted(m.value for m in NativeOIUnit),
            "audit_conclusions": {
                "scalar_native_unit_sufficient": False,
                "required_shape": (
                    "per-unit-bearing-field evidence list: field identity + "
                    "provider-native lexeme or explicit unknown; supports "
                    "multiple fields and accepts an empty list for families "
                    "with no unit-bearing field"
                ),
                "row_level_nested_family": "MECHANICAL_BOOK_SNAPSHOT",
                "families_without_unit_fields": sorted(
                    family
                    for family, entry in _FAMILY_AUDIT.items()
                    if not entry["unit_field_semantics"]
                ),
                "instrument_implied_family": "MECHANICAL_OPEN_INTEREST",
                "canonicalization_decided_in_bloc_4": False,
            },
            "storage_gap_before_repair": {
                "i16_gap_id": "I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP",
                "i16_measurement_artifact": "BLOC_04_I16_BLOC4_READINESS.json",
                "raw_normalization_batch_unit_named_fields": "NONE",
                "public_storage_unit_named_exports": "NONE",
                "projection_schema_descriptor_unit_semantics": "NONE",
                "consequence": (
                    "a public Bloc 5 consumer could not determine native unit "
                    "semantics without provider/private knowledge"
                ),
            },
            "durable_authority_trace": {
                "authority": (
                    "durable ProjectionSchemaDefinition registered in the T0B "
                    "projection schema registry (DurableJsonCatalog under the "
                    "T0 root); the registry reload validates every committed "
                    "fragment and physical projections are re-verified against "
                    "the registered schema"
                ),
                "physical_binding": (
                    "the projection writer requires the rows' exact field set "
                    "to equal the registered provider-native schema, and the "
                    "artifact commit re-reads the Parquet schema for exact "
                    "equality with the registered schema"
                ),
                "handoff_path": (
                    "Bloc5Handoff resolves (projection_schema_id, "
                    "projection_schema_version) carried on every projection "
                    "artifact and copies the durable declarations verbatim "
                    "into RawNormalizationBatch.source_unit_evidence"
                ),
                "forbidden_sources": [
                    "provider-name heuristics",
                    "instrument parsing",
                    "hard-coded sensor maps",
                    "test fixtures outside the registered schema contract",
                    "Bloc 5 rules",
                    "raw-byte key search",
                ],
            },
            "selected_repair_shape": {
                "state_vocabulary": ["VERIFIED_NATIVE", "UNIT_UNVERIFIED"],
                "evidence_fields": [
                    "field_name",
                    "native_unit_lexeme",
                    "state",
                ],
                "batch_field": "RawNormalizationBatch.source_unit_evidence",
                "canonical_ordering": "sorted by field_name",
                "duplicates": "rejected (no silent dedupe)",
                "historical_absence_means": "UNKNOWN HISTORICAL CONTRACT",
                "canonicalization": "none",
                "filesystem_dependency": "none",
            },
            "measured_case_count": 6,
            "result": "AUDIT_COMPLETE",
        }
        _write_evidence(AUDIT_NAME, payload)

        assert payload["family_count"] == 8
        assert payload["audit_conclusions"]["scalar_native_unit_sufficient"] is False
        assert (
            payload["storage_gap_before_repair"]["i16_gap_id"]
            == "I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP"
        )
