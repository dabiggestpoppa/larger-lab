"""P0-A001-04 — CapabilityContract validation repair evidence (reconciliation §8)."""

from __future__ import annotations

import pytest

from qcae.core.contracts.contract import CapabilityContract
from qcae.core.errors import QcaeValidationError
from qcae.tests.unit.test_p0_contract import make_contract


class TestRequestIdValidation:
    def test_valid_request_id_still_accepted(self) -> None:
        make_contract(request_id="req-2026-09-12-001").validate()

    def test_empty_request_id_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="request_id"):
            make_contract(request_id="").validate()

    def test_malformed_request_id_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="request_id"):
            make_contract(request_id="not a stable id!").validate()

    def test_non_string_request_id_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="request_id"):
            make_contract(request_id=12345).validate()

    def test_request_id_in_round_trip(self) -> None:
        contract = make_contract(request_id="req-rt-42")
        rebuilt = CapabilityContract.from_dict(contract.to_dict())
        assert rebuilt.request_id == "req-rt-42"
        assert rebuilt == contract


class TestStringTupleValidation:
    """Every declared string-tuple field must reject malformed runtime values."""

    @pytest.mark.parametrize(
        "field_name",
        [
            "inputs",
            "outputs",
            "forbidden_conditions",
            "performance_requirements",
            "precision_requirements",
            "latency_requirements",
            "throughput_requirements",
            "runtime_constraints",
            "platform_constraints",
            "language_constraints",
            "integration_constraints",
            "license_constraints",
            "cost_constraints",
            "maintenance_constraints",
        ],
    )
    def test_blank_entry_rejected(self, field_name: str) -> None:
        with pytest.raises(QcaeValidationError, match=field_name):
            make_contract(**{field_name: ("valid entry", "   ")}).validate()

    @pytest.mark.parametrize(
        "field_name",
        [
            "inputs",
            "outputs",
            "forbidden_conditions",
            "performance_requirements",
            "runtime_constraints",
            "license_constraints",
        ],
    )
    def test_non_string_entry_rejected(self, field_name: str) -> None:
        with pytest.raises(QcaeValidationError, match=field_name):
            make_contract(**{field_name: (123,)}).validate()

    @pytest.mark.parametrize(
        "field_name",
        ["inputs", "outputs", "forbidden_conditions", "runtime_constraints"],
    )
    def test_non_sequence_rejected(self, field_name: str) -> None:
        with pytest.raises(QcaeValidationError, match=field_name):
            make_contract(**{field_name: "just a plain string"}).validate()


class TestDuplicateValidationExtended:
    def test_duplicate_optional_behaviors_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="duplicate"):
            make_contract(optional_behaviors=("compression", "compression")).validate()

    def test_duplicate_non_goals_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="duplicate"):
            make_contract(explicit_non_goals=("charting", "charting")).validate()

    def test_duplicate_forbidden_conditions_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="duplicate"):
            make_contract(
                forbidden_conditions=("proprietary data egress", "proprietary data egress")
            ).validate()


class TestSerializationUnchanged:
    def test_digest_stability_preserved(self) -> None:
        """The repair must not change canonical serialization semantics."""
        contract = make_contract(
            inputs=("events",),
            runtime_constraints=("linux",),
        )
        rebuilt = CapabilityContract.from_dict(contract.to_dict())
        assert rebuilt.digest() == contract.digest()

    def test_valid_contract_with_all_fields_still_passes(self) -> None:
        make_contract(
            inputs=("timestamped normalized market events",),
            outputs=("deterministic book snapshots",),
            performance_requirements=("replay 1M events < 60s",),
            precision_requirements=("float64 state",),
            latency_requirements=("checkpoint < 10ms",),
            throughput_requirements=("100k events/s",),
            runtime_constraints=("linux", "python 3.12"),
            platform_constraints=("x86_64",),
            language_constraints=("python",),
            integration_constraints=("quant-lab boundary",),
            license_constraints=("permissive only",),
            cost_constraints=("no per-seat SaaS",),
            maintenance_constraints=("single maintainer acceptable",),
        ).validate()
