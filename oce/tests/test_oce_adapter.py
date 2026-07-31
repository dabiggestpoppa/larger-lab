"""
OCE Adapter Integration Tests
=============================
Tests for the SRRA-OPH substrate adapter that powers OCE.

Validates:
- Adapter initialization
- Observer status retrieval
- Health checks
- Entropy economics metrics
- Attractor state
- Memory access
- Event emission
- Prediction contracts
"""

import asyncio
import sys
import os
import pytest

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from srrs_adapter import SRRSAdapter, get_adapter


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def adapter():
    """Create a fresh adapter instance."""
    return SRRSAdapter()


@pytest.fixture
def initialized_adapter(adapter):
    """Create and initialize an adapter."""
    asyncio.run(adapter.initialize())
    return adapter


# ─── Initialization Tests ─────────────────────────────────────────────────────

class TestAdapterInitialization:
    pytestmark = pytest.mark.asyncio
    """Test adapter initialization."""

    @pytest.mark.asyncio
    async def test_initialize_creates_patches(self, adapter):
        """Adapter should create all 4 observer patches."""
        await adapter.initialize()
        assert len(adapter._patches) == 4
        assert "planner" in adapter._patches
        assert "execution" in adapter._patches
        assert "memory" in adapter._patches
        assert "repair" in adapter._patches

    @pytest.mark.asyncio
    async def test_initialize_creates_entropy_components(self, adapter):
        """Adapter should create all Phase 9 entropy economics components."""
        await adapter.initialize()
        assert adapter._coherence_analyzer is not None
        assert adapter._entropy_budget is not None
        assert adapter._recoverability is not None
        assert adapter._compression is not None
        assert adapter._sync_optimizer is not None
        assert adapter._resource_cognition is not None
        assert adapter._governance is not None

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, adapter):
        """Multiple initialize calls should be safe."""
        await adapter.initialize()
        await adapter.initialize()  # Should not raise
        assert adapter._initialized is True

    @pytest.mark.asyncio
    async def test_singleton_get_adapter(self):
        """get_adapter should return the same instance."""
        a1 = await get_adapter()
        a2 = await get_adapter()
        assert a1 is a2


# ─── Observer Status Tests ────────────────────────────────────────────────────

class TestObserverStatus:
    pytestmark = pytest.mark.asyncio
    """Test observer status retrieval."""

    @pytest.mark.asyncio
    async def test_get_observer_status_returns_all(self, initialized_adapter):
        """Should return status for all 4 observers."""
        status = await initialized_adapter.get_observer_status()
        assert len(status) == 4

    @pytest.mark.asyncio
    async def test_observer_status_has_required_fields(self, initialized_adapter):
        """Each observer status should have observer_id, state, entropy, task."""
        status = await initialized_adapter.get_observer_status()
        for s in status:
            assert "observer_id" in s
            assert "state" in s
            assert "entropy" in s
            assert "task" in s

    @pytest.mark.asyncio
    async def test_observers_are_active(self, initialized_adapter):
        """All observers should be active after initialization."""
        status = await initialized_adapter.get_observer_status()
        for s in status:
            assert s["state"] == "active"


# ─── Health Check Tests ───────────────────────────────────────────────────────

class TestHealthCheck:
    pytestmark = pytest.mark.asyncio
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_health_returns_healthy(self, initialized_adapter):
        """Health check should return healthy status."""
        health = await initialized_adapter.health_check()
        assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_reports_all_patches(self, initialized_adapter):
        """Health check should report all 4 patches."""
        health = await initialized_adapter.health_check()
        assert health["total_patches"] == 4
        assert len(health["patches"]) == 4

    @pytest.mark.asyncio
    async def test_health_patches_are_healthy(self, initialized_adapter):
        """All patches should be healthy after initialization."""
        health = await initialized_adapter.health_check()
        for name, patch_health in health["patches"].items():
            assert patch_health["healthy"] is True, f"Patch {name} not healthy"


# ─── Entropy Economics Tests ──────────────────────────────────────────────────

class TestEntropyEconomics:
    pytestmark = pytest.mark.asyncio
    """Test entropy economics metrics."""

    @pytest.mark.asyncio
    async def test_entropy_metrics_has_all_sections(self, initialized_adapter):
        """Entropy metrics should have all 6 sections."""
        metrics = await initialized_adapter.get_entropy_metrics()
        assert "budget" in metrics
        assert "coherence" in metrics
        assert "compression" in metrics
        assert "sync" in metrics
        assert "resources" in metrics
        assert "governance" in metrics

    @pytest.mark.asyncio
    async def test_budget_section_has_fields(self, initialized_adapter):
        """Budget section should have global, consumed, remaining, critical_count."""
        metrics = await initialized_adapter.get_entropy_metrics()
        budget = metrics["budget"]
        assert "global" in budget
        assert "consumed" in budget
        assert "remaining" in budget
        assert "critical_count" in budget

    @pytest.mark.asyncio
    async def test_coherence_section_has_fields(self, initialized_adapter):
        """Coherence section should have system_yield and operation_count."""
        metrics = await initialized_adapter.get_entropy_metrics()
        coherence = metrics["coherence"]
        assert "system_yield" in coherence
        assert "operation_count" in coherence

    @pytest.mark.asyncio
    async def test_system_yield_is_bounded(self, initialized_adapter):
        """System yield should be between 0 and 1."""
        metrics = await initialized_adapter.get_entropy_metrics()
        yield_score = metrics["coherence"]["system_yield"]
        assert 0.0 <= yield_score <= 1.0


# ─── Attractor State Tests ────────────────────────────────────────────────────

class TestAttractorState:
    pytestmark = pytest.mark.asyncio
    """Test attractor state retrieval."""

    @pytest.mark.asyncio
    async def test_attractor_has_required_fields(self, initialized_adapter):
        """Attractor state should have goal, confidence, entropy_pressure, convergence."""
        state = await initialized_adapter.get_attractor_state()
        assert "goal" in state
        assert "confidence" in state
        assert "entropy_pressure" in state
        assert "convergence" in state

    @pytest.mark.asyncio
    async def test_attractor_confidence_bounded(self, initialized_adapter):
        """Attractor confidence should be between 0 and 1."""
        state = await initialized_adapter.get_attractor_state()
        assert 0.0 <= state["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_attractor_convergence_bounded(self, initialized_adapter):
        """Attractor convergence should be between 0 and 1."""
        state = await initialized_adapter.get_attractor_state()
        assert 0.0 <= state["convergence"] <= 1.0


# ─── Memory Access Tests ──────────────────────────────────────────────────────

class TestMemoryAccess:
    pytestmark = pytest.mark.asyncio
    """Test memory access methods."""

    @pytest.mark.asyncio
    async def test_trajectory_memory_returns_list(self, initialized_adapter):
        """Trajectory memory should return a list."""
        memory = await initialized_adapter.get_trajectory_memory()
        assert isinstance(memory, list)

    @pytest.mark.asyncio
    async def test_trajectory_memory_respects_limit(self, initialized_adapter):
        """Trajectory memory should respect the limit parameter."""
        memory = await initialized_adapter.get_trajectory_memory(limit=5)
        assert len(memory) <= 5

    @pytest.mark.asyncio
    async def test_structural_memory_has_fields(self, initialized_adapter):
        """Structural memory should have topology, collar_count, drift_signals."""
        memory = await initialized_adapter.get_structural_memory()
        assert "topology" in memory
        assert "collar_count" in memory
        assert "drift_signals" in memory
        assert "reinforcement_anchors" in memory


# ─── Event Emission Tests ─────────────────────────────────────────────────────

class TestEventEmission:
    pytestmark = pytest.mark.asyncio
    """Test event emission."""

    @pytest.mark.asyncio
    async def test_emit_event_returns_id(self, initialized_adapter):
        """Emitting an event should return an event ID (UUID or event_ prefix)."""
        event_id = await initialized_adapter.emit_event("test.event", {"key": "value"})
        assert event_id  # Non-empty string
        assert isinstance(event_id, str)
        assert len(event_id) > 0

    @pytest.mark.asyncio
    async def test_emit_multiple_events(self, initialized_adapter):
        """Should be able to emit multiple events with unique IDs."""
        ids = []
        for i in range(5):
            eid = await initialized_adapter.emit_event(f"test.event.{i}", {"index": i})
            ids.append(eid)
        assert len(set(ids)) == 5  # All unique
        assert all(isinstance(i, str) and len(i) > 0 for i in ids)


# ─── Prediction Contract Tests ────────────────────────────────────────────────

class TestPredictionContracts:
    pytestmark = pytest.mark.asyncio
    """Test prediction contract creation and validation."""

    @pytest.mark.asyncio
    async def test_create_contract(self, initialized_adapter):
        """Should create a prediction contract."""
        contract = await initialized_adapter.create_prediction_contract(
            mutation_type="weaken_edge",
            target="planner"
        )
        assert "contract_id" in contract
        assert contract["mutation_type"] == "weaken_edge"
        assert contract["target"] == "planner"

    @pytest.mark.asyncio
    async def test_validate_contract(self, initialized_adapter):
        """Should validate a prediction contract."""
        contract = await initialized_adapter.create_prediction_contract(
            mutation_type="strengthen_edge",
            target="execution"
        )
        result = await initialized_adapter.validate_contract(contract["contract_id"])
        assert "contract_id" in result
        assert "valid" in result


# ─── Integration Tests ────────────────────────────────────────────────────────

class TestIntegration:
    pytestmark = pytest.mark.asyncio
    """Integration tests combining multiple adapter methods."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, initialized_adapter):
        """Test a full workflow: status → entropy → attractor → health."""
        status = await initialized_adapter.get_observer_status()
        assert len(status) == 4

        entropy = await initialized_adapter.get_entropy_metrics()
        assert "budget" in entropy

        attractor = await initialized_adapter.get_attractor_state()
        assert attractor["convergence"] >= 0.0

        health = await initialized_adapter.health_check()
        assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_event_then_status(self, initialized_adapter):
        """Events should not break observer status."""
        await initialized_adapter.emit_event("test.integration", {})
        status = await initialized_adapter.get_observer_status()
        assert len(status) == 4
        for s in status:
            assert s["state"] == "active"

    @pytest.mark.asyncio
    async def test_contract_then_entropy(self, initialized_adapter):
        """Contract creation should not break entropy metrics."""
        await initialized_adapter.create_prediction_contract("test", "target")
        metrics = await initialized_adapter.get_entropy_metrics()
        assert "budget" in metrics
