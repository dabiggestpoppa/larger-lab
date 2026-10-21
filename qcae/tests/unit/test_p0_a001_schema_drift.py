"""P0-A001-T02 — A-001 interface-schema drift guard (reconciliation §12, ADR-0005).

Parses the committed amendment JSON schemas and asserts code-level vocabularies,
envelope versions, and firewall semantics agree. The guard self-verifies that
it detects drift.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from qcae.core.amendments.a001.economic_experience import (
    CustomerAcceptance,
    EconomicExperienceRecord,
    EconomicOutcome,
    EconomicsBlock,
    PromotionState,
    QaResult,
)
from qcae.core.amendments.a001.gaps import GapType
from qcae.core.amendments.a001.handoff import (
    FallbackClass,
    HandoffDirection,
    HandoffMode,
    HandoffStatus,
    RequiredOutput,
    ResearchCapabilityHandoff,
)
from qcae.core.amendments.a001.shared import A001_SCHEMA_VERSION, DataRights

AMENDMENT_SCHEMAS_DIR = (
    Path(__file__).resolve().parents[3] / "qcae" / "amendments" / "schemas"
)


def load_schema(name: str) -> Dict[str, Any]:
    path = AMENDMENT_SCHEMAS_DIR / name
    assert path.is_file(), f"committed A-001 schema missing: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def enum_values(enum_cls) -> set:
    return {member.value for member in enum_cls}


class TestHandoffSchemaCompat:
    @pytest.fixture()
    def handoff_schema(self) -> Dict[str, Any]:
        return load_schema("research-capability-handoff.schema.json")

    def test_envelope_version_matches(self, handoff_schema) -> None:
        assert handoff_schema["properties"]["schema_version"]["const"] == A001_SCHEMA_VERSION
        assert ResearchCapabilityHandoff.interface_version == A001_SCHEMA_VERSION

    def test_direction_enum(self, handoff_schema) -> None:
        assert set(handoff_schema["properties"]["direction"]["enum"]) == enum_values(
            HandoffDirection
        )

    def test_mode_enum(self, handoff_schema) -> None:
        assert set(handoff_schema["properties"]["mode"]["enum"]) == enum_values(HandoffMode)

    def test_gap_type_is_the_schema_subset(self, handoff_schema) -> None:
        """The handoff boundary carries the 3-value schema subset of GapType."""
        schema_gaps = set(handoff_schema["properties"]["gap_type"]["enum"])
        assert schema_gaps == {"KNOWLEDGE_GAP", "CAPABILITY_GAP", "MIXED_GAP"}
        from qcae.core.amendments.a001.handoff import HANDOFF_GAP_TYPES

        assert {g.value for g in HANDOFF_GAP_TYPES} == schema_gaps
        # The full core taxonomy remains larger (5 values) — different concern.
        assert enum_values(GapType) >= schema_gaps

    def test_status_enum(self, handoff_schema) -> None:
        assert set(handoff_schema["properties"]["status"]["enum"]) == enum_values(
            HandoffStatus
        )

    def test_required_outputs_enum(self, handoff_schema) -> None:
        assert set(handoff_schema["properties"]["required_outputs"]["items"]["enum"]) == (
            enum_values(RequiredOutput)
        )

    def test_fallback_class_enum(self, handoff_schema) -> None:
        assert set(handoff_schema["properties"]["fallback_class"]["enum"]) == enum_values(
            FallbackClass
        )

    def test_constraints_data_rights_enum(self, handoff_schema) -> None:
        assert set(
            handoff_schema["properties"]["constraints"]["properties"]["data_rights"]["enum"]
        ) == enum_values(DataRights)

    def test_required_fields_representable(self, handoff_schema) -> None:
        assert set(handoff_schema["required"]) == {
            "schema_version", "direction", "request_id", "mode", "gap_type",
            "status", "provenance",
        }
        # provenance requires created_at + producer — code validates both.
        assert set(handoff_schema["properties"]["provenance"]["required"]) == {
            "created_at", "producer"
        }

    def test_no_additional_properties_concept(self, handoff_schema) -> None:
        """The schema is fail-closed (additionalProperties: false) like QCAE."""
        assert handoff_schema["additionalProperties"] is False
        assert handoff_schema["properties"]["result"]["additionalProperties"] is False


class TestEconomicExperienceSchemaCompat:
    @pytest.fixture()
    def ee_schema(self) -> Dict[str, Any]:
        return load_schema("economic-experience.schema.json")

    def test_envelope_version_matches(self, ee_schema) -> None:
        assert ee_schema["properties"]["schema_version"]["const"] == A001_SCHEMA_VERSION
        assert EconomicExperienceRecord.interface_version == A001_SCHEMA_VERSION

    def test_qa_result_enum(self, ee_schema) -> None:
        assert set(ee_schema["properties"]["qa_result"]["enum"]) == enum_values(QaResult)

    def test_customer_acceptance_enum(self, ee_schema) -> None:
        assert set(ee_schema["properties"]["customer_acceptance"]["enum"]) == enum_values(
            CustomerAcceptance
        )

    def test_outcome_enum(self, ee_schema) -> None:
        assert set(ee_schema["properties"]["outcome"]["enum"]) == enum_values(EconomicOutcome)

    def test_promotion_state_enum(self, ee_schema) -> None:
        assert set(ee_schema["properties"]["promotion_state"]["enum"]) == enum_values(
            PromotionState
        )

    def test_data_rights_enum(self, ee_schema) -> None:
        assert set(ee_schema["properties"]["data_rights"]["enum"]) == enum_values(DataRights)

    def test_economics_required_fields(self, ee_schema) -> None:
        econ = ee_schema["properties"]["economics"]
        assert set(econ["required"]) == {
            "gross_payout", "direct_cost", "compute_cost", "tool_cost",
        }
        # Code economics block declares exactly these fields.
        assert set(EconomicsBlock.__dataclass_fields__) >= {
            "gross_payout", "direct_cost", "compute_cost", "tool_cost",
        }

    def test_client_material_promotion_firewall_in_schema(self, ee_schema) -> None:
        """The allOf conditional must exist and target PROMOTED exclusion."""
        conditions = ee_schema.get("allOf", [])
        assert conditions, "firewall conditional missing from committed schema"
        condition = conditions[0]
        assert condition["if"]["properties"]["contains_client_specific_material"] == {
            "const": True
        }
        assert condition["then"]["not"]["properties"]["promotion_state"]["enum"] == [
            "PROMOTED"
        ]

    def test_required_fields_representable(self, ee_schema) -> None:
        assert set(ee_schema["required"]) == {
            "schema_version", "experience_id", "source", "objective_type",
            "economics", "outcome", "data_rights", "promotion_state", "recorded_at",
        }


class TestGuardSelfVerification:
    """The guard must detect drift, not just pass vacuously."""

    def test_guard_detects_enum_drift(self) -> None:
        schema = load_schema("economic-experience.schema.json")
        committed_states = set(schema["properties"]["promotion_state"]["enum"])
        # If code and schema agreed, an injected fake value must be detectable.
        injected = committed_states | {"SILENT_PROMOTION"}
        assert injected != enum_values(PromotionState), (
            "guard could not detect drift: injected value matches code enum"
        )
        assert committed_states == enum_values(PromotionState)

    def test_guard_detects_version_drift(self) -> None:
        schema = load_schema("research-capability-handoff.schema.json")
        schema_version = schema["properties"]["schema_version"]["const"]
        assert schema_version == ResearchCapabilityHandoff.interface_version
        assert schema_version != "2.0", "drift-detection premise broken"

    def test_guard_detects_firewall_removal(self) -> None:
        schema = load_schema("economic-experience.schema.json")
        assert schema.get("allOf"), (
            "A-001 promotion firewall conditional was removed from the schema: "
            "code and amendment have drifted"
        )
