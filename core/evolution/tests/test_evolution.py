"""Tests for Phase 1.7 — Self-Evolution"""
import pytest
from core.evolution.self_evaluation import SelfEvaluationEngine
from core.evolution.research_generator import AutonomousResearchGenerator
from core.evolution.learning_loop import RecursiveLearningLoop
from core.evolution.architecture import ArchitectureEvolutionEngine
from core.evolution.strategy import StrategyMutationEngine
from core.evolution.capability import CapabilityGenerationEngine
from core.evolution.benchmark import ModelBenchmarkingEngine
from core.evolution.adaptation import LongTermAdaptationEngine


class TestSelfEvaluationEngine:
    def test_record_success(self):
        engine = SelfEvaluationEngine()
        engine.record_success("economics", "research")
        assert "economics" in engine._domain_scores
        assert engine._domain_scores["economics"].success_count == 1

    def test_record_failure(self):
        engine = SelfEvaluationEngine()
        engine.record_failure("biology", "research", "insufficient data")
        assert "biology" in engine._domain_scores
        assert engine._domain_scores["biology"].failure_count == 1

    def test_evaluate(self):
        engine = SelfEvaluationEngine()
        engine.record_success("economics")
        engine.record_success("economics")
        engine.record_failure("biology")
        report = engine.evaluate()
        assert report.overall_confidence > 0
        assert "economics" in report.strong_domains or "economics" in report.domain_scores

    def test_weak_domains(self):
        engine = SelfEvaluationEngine()
        engine.record_failure("quantum_physics")
        engine.record_failure("quantum_physics")
        weak = engine.get_weak_domains()
        assert "quantum_physics" in weak


class TestResearchGenerator:
    def test_generate_from_gap(self):
        gen = AutonomousResearchGenerator()
        obj = gen.generate_from_gap("quantum_computing", 0.2)
        assert obj is not None
        assert obj.target_domain == "quantum_computing"
        assert obj.priority > 0.3

    def test_no_gap_no_objective(self):
        gen = AutonomousResearchGenerator()
        obj = gen.generate_from_gap("economics", 0.9)
        assert obj is None  # Already strong

    def test_get_pending(self):
        gen = AutonomousResearchGenerator()
        gen.generate_from_gap("weak_domain", 0.1)
        pending = gen.get_pending_objectives()
        assert len(pending) > 0

    def test_mark_complete(self):
        gen = AutonomousResearchGenerator()
        obj = gen.generate_from_gap("test_domain", 0.2)
        gen.mark_complete(obj.objective_id)
        assert obj.status == "complete"


class TestRecursiveLearningLoop:
    def test_run_cycle(self):
        import asyncio
        loop = RecursiveLearningLoop()
        result = asyncio.run(loop.run_cycle("test_domain"))
        assert "cycle" in result
        assert "steps" in result

    def test_stats(self):
        import asyncio
        loop = RecursiveLearningLoop()
        asyncio.run(loop.run_cycle("test"))
        stats = loop.get_stats()
        assert stats["cycles_completed"] == 1


class TestArchitectureEvolution:
    def test_record_performance(self):
        engine = ArchitectureEvolutionEngine()
        engine.record_performance("research_workflow", True, 10.0)
        assert len(engine._performance_log) == 1

    def test_suggest_mutation(self):
        engine = ArchitectureEvolutionEngine()
        for _ in range(5):
            engine.record_performance("bad_workflow", False, 10.0, "error")
        suggestion = engine.suggest_mutation("bad_workflow")
        assert suggestion is not None
        assert "failure_rate" in suggestion


class TestStrategyMutation:
    def test_record_result(self):
        engine = StrategyMutationEngine()
        engine.record_result("chain_of_thought", True, 0.8)
        assert engine._strategy_scores["chain_of_thought"] > 0.5

    def test_get_best_strategy(self):
        engine = StrategyMutationEngine()
        engine.record_result("chain_of_thought", True, 0.9)
        engine.record_result("tree_of_thought", True, 0.5)
        best = engine.get_best_strategy()
        assert best == "chain_of_thought"


class TestCapabilityGeneration:
    def test_record_need(self):
        engine = CapabilityGenerationEngine()
        engine.record_need("citation_verification")
        engine.record_need("citation_verification")
        engine.record_need("citation_verification")
        assert engine.should_generate("citation_verification")

    def test_generate_tool(self):
        engine = CapabilityGenerationEngine()
        for _ in range(3):
            engine.record_need("test_capability")
        tool = engine.generate_tool("test_capability")
        assert tool is not None


class TestModelBenchmarking:
    def test_record_result(self):
        engine = ModelBenchmarkingEngine()
        engine.record_result("owl-alpha", "research", True, 1.5, 0.8)
        assert "owl-alpha" in engine._model_scores

    def test_get_best_model(self):
        engine = ModelBenchmarkingEngine()
        engine.record_result("model_a", "research", True, 1.0, 0.9)
        engine.record_result("model_b", "research", True, 1.0, 0.5)
        best = engine.get_best_model("research")
        assert best == "model_a"


class TestLongTermAdaptation:
    def test_record_snapshot(self):
        engine = LongTermAdaptationEngine()
        engine.record_snapshot({"tasks": 10, "confidence": 0.7})
        assert len(engine._history) == 1

    def test_domain_growth(self):
        engine = LongTermAdaptationEngine()
        engine.record_domain_activity("economics")
        engine.record_domain_activity("economics")
        engine.record_domain_activity("physics")
        stats = engine.get_stats()
        assert stats["domain_growth"]["economics"] == 2

    def test_suggest_reallocation(self):
        engine = LongTermAdaptationEngine()
        for _ in range(10):
            engine.record_domain_activity("cryptography")
        suggestions = engine.suggest_reallocation()
        assert len(suggestions) > 0
        assert "cryptography" in suggestions[0]
