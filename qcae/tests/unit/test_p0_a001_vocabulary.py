"""P0-A001-01 — gap taxonomy + resolution mode evidence (A-001 §3, §8)."""

from __future__ import annotations

import pytest

from qcae.core.amendments.a001.gaps import (
    GAP_OWNERSHIP,
    GapOwner,
    GapRef,
    GapType,
    MixedGapDecomposition,
)
from qcae.core.amendments.a001.resolution import (
    EXTERNAL_PROCUREMENT_MODES,
    RESEARCH_ROUTING_MODE,
    CapabilityResolutionMode,
)
from qcae.core.amendments.a001.shared import DataRights
from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import QcaeUnknownTypeError
from qcae.core.vocabulary import AcquisitionForm


class TestGapTaxonomy:
    def test_all_gap_type_values(self) -> None:
        assert {g.value for g in GapType} == {
            "KNOWLEDGE_GAP",
            "CAPABILITY_GAP",
            "EXECUTION_FAILURE",
            "INSTITUTIONAL_LEARNING_CANDIDATE",
            "MIXED_GAP",
        }

    def test_single_owner_gaps_route_to_canonical_owner(self) -> None:
        assert GAP_OWNERSHIP[GapType.KNOWLEDGE_GAP] is GapOwner.RESEARCH_MESH
        assert GAP_OWNERSHIP[GapType.CAPABILITY_GAP] is GapOwner.QCAE
        assert (
            GAP_OWNERSHIP[GapType.EXECUTION_FAILURE]
            is GapOwner.EXECUTION_SERVICE_OWNER
        )
        assert (
            GAP_OWNERSHIP[GapType.INSTITUTIONAL_LEARNING_CANDIDATE]
            is GapOwner.INSTITUTION_TRANSFORMATION_GOVERNOR
        )

    def test_mixed_gap_has_no_single_owner(self) -> None:
        """A-001 §3: mixed gaps are decomposed into separately owned linked gaps."""
        assert GapType.MIXED_GAP not in GAP_OWNERSHIP

    def test_mixed_gap_requires_decomposition(self) -> None:
        decomposition = MixedGapDecomposition(
            mixed_gap_id="gap-mixed-001",
            component_gaps=(
                GapRef(gap_id="gap-k-001", gap_type=GapType.KNOWLEDGE_GAP),
                GapRef(gap_id="gap-c-001", gap_type=GapType.CAPABILITY_GAP),
            ),
        )
        decomposition.validate()

    def test_mixed_gap_single_component_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="at least two"):
            MixedGapDecomposition(
                mixed_gap_id="gap-mixed-002",
                component_gaps=(
                    GapRef(gap_id="gap-k-002", gap_type=GapType.KNOWLEDGE_GAP),
                ),
            ).validate()

    def test_mixed_gap_cannot_silently_become_one_owner(self) -> None:
        """Adversarial: an execution failure must not be laundered into a
        capability gap, and a mixed gap must not collapse into QCAE alone."""
        decomposition = MixedGapDecomposition(
            mixed_gap_id="gap-mixed-003",
            component_gaps=(
                GapRef(gap_id="gap-e-003", gap_type=GapType.EXECUTION_FAILURE),
                GapRef(gap_id="gap-c-003", gap_type=GapType.CAPABILITY_GAP),
            ),
        )
        decomposition.validate()
        types = {ref.gap_type for ref in decomposition.component_gaps}
        assert types == {GapType.EXECUTION_FAILURE, GapType.CAPABILITY_GAP}
        # ownership routing stays per-type, never per-decomposition: neither
        # component gap type may inherit ownership from the mixed parent
        assert GAP_OWNERSHIP[GapType.EXECUTION_FAILURE] is GapOwner.EXECUTION_SERVICE_OWNER
        assert GAP_OWNERSHIP[GapType.CAPABILITY_GAP] is GapOwner.QCAE
        assert GapOwner.QCAE is GAP_OWNERSHIP[GapType.CAPABILITY_GAP]

    def test_execution_failure_not_silently_a_capability_gap(self) -> None:
        """A-001 §3: a known capability failing its existing contract is not
        automatically a new capability gap."""
        assert GAP_OWNERSHIP[GapType.EXECUTION_FAILURE] is not GapOwner.QCAE

    def test_invalid_gap_ref_value_rejected(self) -> None:
        ref = GapRef(gap_id="gap-x", gap_type="NOT_A_GAP")
        with pytest.raises(QcaeValidationError, match="GapType"):
            ref.validate()

    def test_gap_ref_bad_id_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="gap_id"):
            GapRef(gap_id="bad id!", gap_type=GapType.KNOWLEDGE_GAP).validate()

    def test_gap_ref_round_trip(self) -> None:
        ref = GapRef(gap_id="gap-rt-1", gap_type=GapType.INSTITUTIONAL_LEARNING_CANDIDATE)
        rebuilt = GapRef.from_dict(ref.to_dict())
        assert rebuilt == ref
        assert rebuilt.gap_type is GapType.INSTITUTIONAL_LEARNING_CANDIDATE

    def test_decomposition_round_trip(self) -> None:
        decomposition = MixedGapDecomposition(
            mixed_gap_id="gap-mixed-004",
            component_gaps=(
                GapRef(gap_id="gap-k-004", gap_type=GapType.KNOWLEDGE_GAP),
                GapRef(gap_id="gap-c-004", gap_type=GapType.CAPABILITY_GAP),
            ),
        )
        rebuilt = MixedGapDecomposition.from_dict(decomposition.to_dict())
        assert rebuilt == decomposition
        assert all(isinstance(ref, GapRef) for ref in rebuilt.component_gaps)


class TestResolutionMode:
    def test_all_resolution_mode_values(self) -> None:
        assert {m.value for m in CapabilityResolutionMode} == {
            "USE", "BORROW", "RENT", "BUY", "ACQUIRE", "BUILD", "RESEARCH", "DECLINE",
        }

    def test_external_procurement_modes(self) -> None:
        assert EXTERNAL_PROCUREMENT_MODES == {
            CapabilityResolutionMode.RENT,
            CapabilityResolutionMode.BUY,
        }

    def test_research_mode_routes_not_implements(self) -> None:
        """RESEARCH routes unresolved knowledge to Research Mesh; QCAE does not
        become a research institution (A-001 §1, §8)."""
        assert RESEARCH_ROUTING_MODE is CapabilityResolutionMode.RESEARCH

    def test_existing_acquisition_form_compatibility_preserved(self) -> None:
        """Operator repair §11.5: AcquisitionForm vocabulary must remain intact."""
        assert {f.value for f in AcquisitionForm} == {
            "USE_DIRECT", "USE_DEPENDENCY", "WRAP_LIBRARY", "WRAP_SERVICE",
            "FORK", "VENDOR", "EXTRACT_COMPONENT", "EXTRACT_ALGORITHM",
            "EXTRACT_SCHEMA", "EXTRACT_TESTS", "REIMPLEMENT_FROM_SPEC",
            "REIMPLEMENT_FROM_PAPER", "USE_AS_REFERENCE",
            "USE_AS_ARCHITECTURAL_PRIOR", "DEFER", "REJECT",
        }

    def test_resolution_mode_is_separate_type_from_acquisition_form(self) -> None:
        assert CapabilityResolutionMode is not AcquisitionForm
        # Overlapping English words do not merge the vocabularies.
        assert CapabilityResolutionMode("USE") is not AcquisitionForm("USE_DIRECT")

    def test_resolution_mode_round_trip_through_shared_coercion(self) -> None:
        from qcae.core.serialization import coerce_enum

        member = coerce_enum("RENT", CapabilityResolutionMode)
        assert member is CapabilityResolutionMode.RENT
        assert coerce_enum("NOT_A_MODE", CapabilityResolutionMode) == "NOT_A_MODE"


class TestDataRights:
    def test_data_rights_values(self) -> None:
        assert {r.value for r in DataRights} == {
            "PUBLIC", "LICENSED", "CLIENT_CONFIDENTIAL", "INTERNAL", "RESTRICTED",
            "UNKNOWN",
        }

    def test_protected_rights_frozenset(self) -> None:
        from qcae.core.amendments.a001.shared import PROTECTED_DATA_RIGHTS

        assert DataRights.CLIENT_CONFIDENTIAL in PROTECTED_DATA_RIGHTS
        assert DataRights.RESTRICTED in PROTECTED_DATA_RIGHTS
        assert DataRights.PUBLIC not in PROTECTED_DATA_RIGHTS

    def test_malformed_serialization_still_fails_closed(self) -> None:
        """Contract shape safety net: unknown object_type rejected."""
        with pytest.raises(QcaeUnknownTypeError):
            GapRef.from_dict(
                {
                    "schema_version": 1,
                    "object_type": "NotGapRef",
                    "gap_id": "gap-x",
                    "gap_type": "KNOWLEDGE_GAP",
                }
            )
