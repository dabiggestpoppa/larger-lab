"""Tests for Nested Repair System."""

import pytest
from oce.backend.multiscale.nested_repair import NestedRepairSystem, RepairRequest, RepairEscalation


class TestNestedRepairSystem:
    def test_submit_repair(self):
        system = NestedRepairSystem()
        request = system.submit_repair("drift", 0.5, "local", "test issue")
        assert request.issue_type == "drift"
        assert request.severity == 0.5

    def test_escalation_local(self):
        system = NestedRepairSystem()
        request = system.submit_repair("drift", 0.2, "local", "minor issue")
        assert request.escalation_level == RepairEscalation.LOCAL

    def test_escalation_regional(self):
        system = NestedRepairSystem()
        request = system.submit_repair("drift", 0.7, "local", "major issue")
        assert request.escalation_level == RepairEscalation.REGIONAL

    def test_escalation_global(self):
        system = NestedRepairSystem()
        request = system.submit_repair("drift", 0.95, "local", "critical issue")
        assert request.escalation_level == RepairEscalation.GLOBAL

    def test_get_pending_repairs(self):
        system = NestedRepairSystem()
        system.submit_repair("drift", 0.2, "local", "minor")
        system.submit_repair("drift", 0.7, "local", "major")
        local = system.get_pending_repairs(RepairEscalation.LOCAL)
        assert len(local) == 1

    def test_process_repair(self):
        system = NestedRepairSystem()
        request = system.submit_repair("drift", 0.5, "local", "test")
        result = system.process_repair(request.request_id, "fixed")
        assert result.resolution == "fixed"
        assert len(system._repair_queue) == 0
