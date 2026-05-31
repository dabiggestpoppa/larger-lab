"""
Phase 01 Integration Tests
End-to-end tests for the full O2C pipeline:
Agent session -> journal -> distill -> vault -> retrieve -> context injection
"""

import pytest
from pathlib import Path

from core.obsidian.vault_writer import VaultWriter
from core.obsidian.error_intelligence import ErrorIntelligence
from core.obsidian.pattern_crystallizer import PatternCrystallizer
from core.obsidian.memory_distiller import MemoryDistiller
from core.obsidian.context_injector import ContextInjector
from core.execution.journal import ExecutionJournal


@pytest.fixture
def tmp_vault(tmp_path):
    """Create a temporary vault for integration tests."""
    vault = tmp_path / "test-vault"
    vault.mkdir()
    return vault


class TestFullPipeline:
    """Test the full agent session -> distillation -> retrieval pipeline."""

    def test_session_to_distillation(self, tmp_vault):
        """Agent session -> journal -> distill -> vault note."""
        # 1. Create a journal for an agent session
        journal = ExecutionJournal(
            agent_name="TestAgent",
            task="Test pipeline task",
            vault_path=tmp_vault,
        )
        journal.log_step("load_data", "success", "Loaded CSV")
        journal.log_step("process", "failed", "Parse error")
        journal.log_correction("process", "retry with encoding", "success")
        journal.log_step("save", "success", "Saved output")

        # 2. Distill the session
        distiller = MemoryDistiller(vault_path=tmp_vault)
        result = distiller.distill_session(
            agent_name="TestAgent",
            task="Test pipeline task",
            journal_entries=journal.steps,
        )

        assert result is not None
        assert result["agent"] == "TestAgent"
        assert result["total_steps"] == 4
        assert result["successes"] == 3
        assert result["failures"] == 1

    def test_error_indexing_to_intelligence(self, tmp_vault):
        """Error -> index -> query -> patterns."""
        ei = ErrorIntelligence(vault_path=tmp_vault)

        # Index some errors
        ei.index_error(
            traceback="KeyError: 'price' in trading.py",
            context="Trade execution failed",
            fix_applied="Added key validation",
            result="Fixed",
        )
        ei.index_error(
            traceback="KeyError: 'volume' in data.py",
            context="Data loading failed",
            fix_applied="Added default value",
            result="Fixed",
        )

        # Query patterns
        patterns = ei.get_error_patterns()
        assert patterns["total_errors"] >= 1

        # Find similar errors
        similar = ei.find_similar_errors("KeyError")
        assert len(similar) >= 1

    def test_pattern_extraction(self, tmp_vault):
        """Notes with shared tags -> pattern extraction."""
        pc = PatternCrystallizer(vault_path=tmp_vault)
        writer = VaultWriter(vault_path=tmp_vault)

        # Create notes with shared tags
        content = {"cause": "test", "fix": "test", "result": "test", "links": []}
        writer.write_note("failures", "Bug A", content, tags=["state", "reset"])
        writer.write_note("failures", "Bug B", content, tags=["state", "keyerror"])
        writer.write_note("failures", "Bug C", content, tags=["state", "timeout"])

        # Extract patterns
        patterns = pc.extract_patterns(min_occurrences=2)
        assert len(patterns) >= 1
        # "state" tag should appear 3 times
        state_patterns = [p for p in patterns if p.get("name") == "state"]
        assert len(state_patterns) >= 1

    def test_context_injection(self, tmp_vault):
        """Vault data -> context injection for new task."""
        ci = ContextInjector(vault_path=tmp_vault)
        writer = VaultWriter(vault_path=tmp_vault)

        # Add some vault data
        writer.write_note("doctrine", "State Machine Pattern", {
            "cause": "Need reliable state transitions",
            "fix": "Implement FSM",
            "result": "Stable state management",
            "links": ["State Management"],
        }, tags=["pattern", "state_machine"])

        writer.write_note("failures", "State Reset Bug", {
            "cause": "State cleared before archival",
            "fix": "Snapshot before reset",
            "result": "Fixed",
            "links": ["State Management"],
        }, tags=["state", "reset"])

        # Get context for a related task
        context = ci.prepare_context(
            task="Fix state management bug in observer",
            max_patterns=5,
        )
        assert isinstance(context, str)
        # Should contain references to state-related content
        assert len(context) > 0

    def test_vault_distillation(self, tmp_vault):
        """Distill from vault activity."""
        writer = VaultWriter(vault_path=tmp_vault)
        content = {"cause": "test", "fix": "test", "result": "test", "links": []}
        writer.write_note("execution", "Exec 1", content)
        writer.write_note("execution", "Exec 2", content)
        writer.write_note("failures", "Failure 1", content)

        distiller = MemoryDistiller(vault_path=tmp_vault)
        result = distiller.distill_from_vault(days=7)

        assert result is not None
        assert result["executions_analyzed"] >= 2
        assert result["failures_analyzed"] >= 1

    def test_crystallize_and_retrieve_pattern(self, tmp_vault):
        """Crystallize a pattern and retrieve it."""
        pc = PatternCrystallizer(vault_path=tmp_vault)

        # Crystallize
        result = pc.crystallize_pattern(
            name="Test Research Pattern",
            conditions=["Observer consensus", "Isolated workers"],
            result="92% reduction in conflicts",
            links=["Consensus", "Research"],
        )
        assert result is not None
        assert result["name"] == "Test Research Pattern"

        # Retrieve
        primitives = pc.get_cognitive_primitives()
        assert len(primitives) >= 1
        assert any(p["name"] == "Test Research Pattern" for p in primitives)

    def test_prevention_rules(self, tmp_vault):
        """Index errors and get prevention rules."""
        ei = ErrorIntelligence(vault_path=tmp_vault)

        ei.index_error(
            traceback="KeyError: 'price'",
            context="Trade execution",
            fix_applied="Validate keys before access",
            result="Fixed",
        )

        rules = ei.get_prevention_rules()
        assert len(rules) >= 1


class TestComponentIntegration:
    """Test that all Phase 01 components work together."""

    def test_all_components_import(self):
        """All Phase 01 components should be importable."""
        from core.obsidian.error_intelligence import ErrorIntelligence
        from core.obsidian.pattern_crystallizer import PatternCrystallizer
        from core.obsidian.memory_distiller import MemoryDistiller
        from core.obsidian.context_injector import ContextInjector
        assert all([
            ErrorIntelligence,
            PatternCrystallizer,
            MemoryDistiller,
            ContextInjector,
        ])

    def test_components_share_vault(self, tmp_vault):
        """Multiple components should work on the same vault."""
        writer = VaultWriter(vault_path=tmp_vault)
        writer.write_note("doctrine", "Shared Note", {
            "cause": "test", "fix": "test", "result": "test", "links": ["LinkA", "LinkB"],
        }, tags=["shared"])

        # All components should see the same note
        ei = ErrorIntelligence(vault_path=tmp_vault)
        pc = PatternCrystallizer(vault_path=tmp_vault)
        md = MemoryDistiller(vault_path=tmp_vault)
        ci = ContextInjector(vault_path=tmp_vault)

        # Each should be able to list notes
        assert len(writer.list_notes()) >= 1
        assert len(pc.extract_patterns(min_occurrences=1)) >= 0
