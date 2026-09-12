"""P0-C04 — CapabilityContract domain evidence (canon Book I 1.1)."""

from __future__ import annotations

from typing import Any

import pytest

from qcae.core.contracts.contract import CapabilityContract
from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import QcaeSerializationError
from qcae.core.vocabulary import AcquisitionForm, EvidenceClass

AF = AcquisitionForm
EC = EvidenceClass


def make_contract(**overrides: Any) -> CapabilityContract:
    """Valid baseline contract modeled on canon 1.1.15."""
    fields: dict = {
        "capability_id": "CAP-REPLAY-001",
        "contract_version": 1,
        "request_id": "req-2026-09-12-001",
        "title": "deterministic-order-book-replay",
        "problem_statement": (
            "Reconstruct deterministic L2 order-book state sequences from "
            "timestamped normalized market events."
        ),
        "intent": "research-and-backtest-infrastructure",
        "required_behaviors": [
            "reconstruct L2 book state from ordered event stream",
            "expose state at deterministic checkpoints",
            "preserve event ordering",
        ],
        "optional_behaviors": ["compression at rest"],
        "explicit_non_goals": ["exchange connectivity", "strategy execution"],
        "inputs": ["timestamped normalized market events"],
        "outputs": ["deterministic book snapshots"],
        "acceptance_tests": [
            "reconstructed snapshot at checkpoint k matches reference fixture exactly",
        ],
        "required_evidence_classes": (EC.E2_SOURCE, EC.E5_INDEPENDENT_CONTRACT),
        "forbidden_conditions": ["mandatory external SaaS", "proprietary data egress"],
        "preferred_acquisition_forms": (AF.EXTRACT_COMPONENT, AF.USE_DEPENDENCY),
        "forbidden_acquisition_forms": (AF.FORK,),
        "owner": "quant-lab",
        "created_at": "2026-09-12T00:00:00Z",
    }
    fields.update(overrides)
    return CapabilityContract(**fields)


class TestValidCreation:
    def test_valid_contract_validates(self) -> None:
        contract = make_contract()
        contract.validate()

    def test_minimal_required_fields_only(self) -> None:
        contract = CapabilityContract(
            capability_id="CAP-UTIL-001",
            contract_version=1,
            request_id="req-2",
            title="tiny utility",
            problem_statement="do the one needed thing",
            intent="developer tooling",
            required_behaviors=["parse input string into structured record"],
            acceptance_tests=["output record equals reference for fixture input"],
            required_evidence_classes=(EC.E5_INDEPENDENT_CONTRACT,),
            owner="quant-lab",
            created_at="2026-09-12T00:00:00Z",
        )
        contract.validate()

    def test_quant_flags_accepted(self) -> None:
        make_contract(quant_domain=True, cerebus_relevance=True).validate()


class TestInvalidRejection:
    def test_empty_required_behaviors_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="required_behaviors"):
            make_contract(required_behaviors=()).validate()

    def test_empty_acceptance_tests_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="acceptance_tests"):
            make_contract(acceptance_tests=()).validate()

    def test_empty_evidence_classes_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="required_evidence_classes"):
            make_contract(required_evidence_classes=()).validate()

    def test_malformed_capability_id_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="capability_id"):
            make_contract(capability_id="not a stable id!").validate()

    def test_zero_contract_version_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="contract_version"):
            make_contract(contract_version=0).validate()

    def test_bool_contract_version_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="contract_version"):
            make_contract(contract_version=True).validate()

    def test_missing_owner_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="owner"):
            make_contract(owner="").validate()

    def test_missing_created_at_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="created_at"):
            make_contract(created_at="").validate()

    def test_blank_behavior_entry_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="required_behaviors"):
            make_contract(required_behaviors=("valid behavior", "  ")).validate()

    def test_bad_evidence_class_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="EvidenceClass"):
            make_contract(required_evidence_classes=("E2_SOURCE",)).validate()

    def test_bad_acquisition_form_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="AcquisitionForm"):
            make_contract(preferred_acquisition_forms=("VENDOR",)).validate()


class TestRequiredPreferredForbidden:
    def test_behavior_required_and_forbidden_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="required and forbidden"):
            make_contract(
                required_behaviors=("replay events",),
                forbidden_conditions=("replay events",),
            ).validate()

    def test_behavior_required_and_optional_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="required and optional"):
            make_contract(
                required_behaviors=("replay events",),
                optional_behaviors=("replay events",),
            ).validate()

    def test_form_preferred_and_forbidden_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="preferred and forbidden"):
            make_contract(
                preferred_acquisition_forms=(AF.VENDOR,),
                forbidden_acquisition_forms=(AF.VENDOR,),
            ).validate()

    def test_preferences_do_not_become_constraints(self) -> None:
        """PREFERRED forms influence ranking only; they must not hard-fail."""
        contract = make_contract(preferred_acquisition_forms=(AF.VENDOR,))
        contract.validate()
        assert AF.VENDOR in contract.preferred_acquisition_forms
        assert AF.VENDOR not in contract.forbidden_acquisition_forms


class TestContractVersioning:
    def test_version_evolution_same_capability_id(self) -> None:
        v1 = make_contract()
        v3 = make_contract(
            contract_version=3,
            required_behaviors=v1.required_behaviors
            + ("deterministic replay requirement",),
            supersedes_contract="CAP-REPLAY-001:v2",
        )
        v1.validate()
        v3.validate()
        assert v1.capability_id == v3.capability_id
        assert v3.contract_version > v1.contract_version

    def test_supersedes_contract_round_trips(self) -> None:
        v2 = make_contract(contract_version=2, supersedes_contract="CAP-REPLAY-001:v1")
        rebuilt = CapabilityContract.from_dict(v2.to_dict())
        assert rebuilt.supersedes_contract == "CAP-REPLAY-001:v1"
        assert rebuilt == v2

    def test_verdict_scoping_fields_distinguish_versions(self) -> None:
        """Candidate verdicts scope to contract versions, so versions must differ
        in identity-relevant fields while sharing capability_id."""
        v1 = make_contract()
        v2 = make_contract(contract_version=2)
        assert v1.digest() != v2.digest()
        assert v1.capability_id == v2.capability_id


class TestSerialization:
    def test_round_trip_full_contract(self) -> None:
        contract = make_contract(
            quant_domain=True,
            cerebus_relevance=True,
            performance_requirements=("replay 1M events < 60s",),
            security_class="internal-only",
        )
        rebuilt = CapabilityContract.from_dict(contract.to_dict())
        assert rebuilt == contract

    def test_round_trip_preserves_enums(self) -> None:
        contract = make_contract(
            required_evidence_classes=(
                EC.E2_SOURCE, EC.E5_INDEPENDENT_CONTRACT, EC.E7_DOMAIN_VALIDATION,
            ),
        )
        rebuilt = CapabilityContract.from_dict(contract.to_dict())
        assert all(isinstance(e, EC) for e in rebuilt.required_evidence_classes)
        assert rebuilt.required_evidence_classes == contract.required_evidence_classes

    def test_envelope_shape(self) -> None:
        payload = make_contract().to_dict()
        assert payload["schema_version"] == 1
        assert payload["object_type"] == "CapabilityContract"
        assert payload["capability_id"] == "CAP-REPLAY-001"

    def test_schema_version_bump_fails_closed(self) -> None:
        payload = make_contract().to_dict()
        payload["schema_version"] = 2
        with pytest.raises(Exception, match="schema_version"):
            CapabilityContract.from_dict(payload)

    def test_digest_stable_and_discriminating(self) -> None:
        a = make_contract()
        b = make_contract()
        assert a.digest() == b.digest()
        assert a.digest() != make_contract(title="different title").digest()

    def test_unknown_field_rejected(self) -> None:
        payload = make_contract().to_dict()
        payload["invented_field"] = 1
        with pytest.raises(QcaeSerializationError, match="unknown"):
            CapabilityContract.from_dict(payload)
