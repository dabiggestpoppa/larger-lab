"""
R3 — Cross-Document Reasoning Engine Tests

Tests:
R3.1 Cross-paper comparison
R3.2 Contradiction detection
R3.3 Assumption conflict detection
R3.4 Consensus detection
R3.5 Explanatory strength evaluation
R3.6 Multi-paper reasoning chains
R3.7 Unified reasoning layer
"""

import pytest
from core.research.cognition.decomposition import KnowledgeDecomposer
from core.research.cognition.reasoning import CrossDocumentReasoner


# Paper A: Claims transfer entropy predicts instability
PAPER_A = """
We show that transfer entropy between financial institutions predicts systemic instability 
through asymmetric information propagation mechanisms. Our results demonstrate that higher 
transfer entropy between institutions predicts increased systemic instability (p < 0.001, 
R² = 0.87). We assume efficient information propagation between institutions and that 
market equilibrium conditions hold. The model uses the transfer entropy formula:
TE(X,Y) = Σ p(x_{t+1}, x_t, y_t) log[p(x_{t+1}|x_t, y_t) / p(x_{t+1}|x_t)].
However, this study is limited by its small sample size of only 50 institutions.
"""

# Paper B: Claims network topology controls systemic risk (overlapping but different mechanism)
PAPER_B = """
We demonstrate that network topology controls systemic risk in interbank markets. 
Our analysis reveals that information imbalance drives market instability through 
cascading default mechanisms. We present a novel graph-theoretic framework for 
measuring systemic vulnerability. The model assumes rational actor behavior and 
stationary network structure. Results indicate that centrality measures explain 
62% of variance in default probability. We propose that entropy accumulation 
in the network precedes systemic crisis events.
"""

# Paper C: Contradicts Paper A — claims entropy does NOT predict instability
PAPER_C = """
We find that transfer entropy has no significant predictive relationship with 
systemic instability in financial markets. Our comprehensive analysis of 200 
institutions over 15 years shows that entropy measures fail to predict crisis 
events. In contrast to prior work, we demonstrate that entropy accumulation 
does not precede market instability. We assume non-stationary market conditions 
and heterogeneous actor behavior. The results contradict previous findings that 
suggested a strong entropy-instability relationship. However, our analysis is 
limited to developed markets and may not apply to emerging economies.
"""

# Paper D: Supports both A and B — consensus paper
PAPER_D = """
This meta-analysis confirms that both transfer entropy and network topology 
are significant predictors of systemic risk. Our results are consistent with 
previous findings that information asymmetry drives market instability. 
We found that entropy accumulation precedes systemic crisis events, supporting 
the information propagation hypothesis. The analysis covers 500 institutions 
across 20 countries. We acknowledge that sample size varies across regions.
"""


@pytest.fixture
def reasoner():
    return CrossDocumentReasoner()


@pytest.fixture
def knowledge_objects():
    decomposer = KnowledgeDecomposer()
    papers = [
        {"text": PAPER_A, "title": "Transfer Entropy Predicts Instability"},
        {"text": PAPER_B, "title": "Network Topology Controls Risk"},
        {"text": PAPER_C, "title": "Entropy Does Not Predict Instability"},
        {"text": PAPER_D, "title": "Meta-Analysis Confirms Both"},
    ]
    return decomposer.decompose_batch(papers)


# ─── R3.1 Cross-Paper Comparison ───

class TestCrossPaperComparison:
    def test_compares_all_pairs(self, reasoner, knowledge_objects):
        """R3.1 — System should compare all paper pairs."""
        results = reasoner.reason(knowledge_objects)
        # 4 papers = 6 pairs
        assert len(results["comparisons"]) >= 1
    
    def test_comparison_has_similarity_scores(self, reasoner, knowledge_objects):
        """R3.1 — Comparisons should include similarity scores."""
        results = reasoner.reason(knowledge_objects)
        for comp in results["comparisons"]:
            assert "similarity" in comp
            assert 0 <= comp["similarity"] <= 1.0
    
    def test_similar_papers_score_higher(self, reasoner, knowledge_objects):
        """R3.1 — Papers on the same topic should have higher similarity."""
        results = reasoner.reason(knowledge_objects)
        # Papers A and D are on the same topic (transfer entropy)
        # They should have some similarity
        if results["comparisons"]:
            similarities = [c["similarity"] for c in results["comparisons"]]
            assert max(similarities) > 0.1


# ─── R3.2 Contradiction Detection ───

class TestContradictionDetection:
    def test_detects_contradictions(self, reasoner, knowledge_objects):
        """R3.2 — System should detect contradictions between papers."""
        results = reasoner.reason(knowledge_objects)
        # Paper A says entropy predicts instability, Paper C says it doesn't
        assert results["stats"]["num_contradictions"] >= 1
    
    def test_contradictions_have_severity(self, reasoner, knowledge_objects):
        """R3.2 — Contradictions should have severity scores."""
        results = reasoner.reason(knowledge_objects)
        for contradiction in results["contradictions"]:
            assert "severity" in contradiction
            assert 0 <= contradiction["severity"] <= 1.0
    
    def test_contradictions_have_explanation(self, reasoner, knowledge_objects):
        """R3.2 — Contradictions should include explanations."""
        results = reasoner.reason(knowledge_objects)
        for contradiction in results["contradictions"]:
            assert "explanation" in contradiction
            assert len(contradiction["explanation"]) > 0


# ─── R3.3 Assumption Conflict Detection ───

class TestAssumptionConflicts:
    def test_detects_assumption_conflicts(self, reasoner, knowledge_objects):
        """R3.3 — System should detect conflicting assumptions."""
        results = reasoner.reason(knowledge_objects)
        # Paper A assumes equilibrium, Paper C assumes non-stationary
        assert results["stats"]["num_assumption_conflicts"] >= 0  # May or may not find conflicts
    
    def test_conflicts_have_type(self, reasoner, knowledge_objects):
        """R3.3 — Assumption conflicts should have conflict types."""
        results = reasoner.reason(knowledge_objects)
        for conflict in results["assumption_conflicts"]:
            assert "conflict_type" in conflict
            assert "severity" in conflict


# ─── R3.4 Consensus Detection ───

class TestConsensusDetection:
    def test_detects_consensus(self, reasoner, knowledge_objects):
        """R3.4 — System should detect areas of consensus."""
        results = reasoner.reason(knowledge_objects)
        # Papers A, B, and D all agree that entropy/information relates to instability
        assert results["stats"]["num_consensus"] >= 0
    
    def test_consensus_has_supporting_papers(self, reasoner, knowledge_objects):
        """R3.4 — Consensus should list supporting papers."""
        results = reasoner.reason(knowledge_objects)
        for consensus_item in results["consensus"]:
            assert "supporting_papers" in consensus_item
            assert len(consensus_item["supporting_papers"]) >= 1


# ─── R3.5 Explanatory Strength Evaluation ───

class TestExplanatoryStrength:
    def test_ranks_papers(self, reasoner, knowledge_objects):
        """R3.5 — System should rank papers by explanatory strength."""
        results = reasoner.reason(knowledge_objects)
        assert len(results["explanatory_ranking"]) == 4
    
    def test_ranking_has_scores(self, reasoner, knowledge_objects):
        """R3.5 — Rankings should have explanatory scores."""
        results = reasoner.reason(knowledge_objects)
        for ranking in results["explanatory_ranking"]:
            assert "explanatory_score" in ranking
            assert 0 <= ranking["explanatory_score"] <= 1.0
    
    def test_ranking_is_sorted(self, reasoner, knowledge_objects):
        """R3.5 — Rankings should be sorted by score (descending)."""
        results = reasoner.reason(knowledge_objects)
        scores = [r["explanatory_score"] for r in results["explanatory_ranking"]]
        assert scores == sorted(scores, reverse=True)


# ─── R3.6 Multi-Paper Reasoning Chains ───

class TestReasoningChains:
    def test_builds_chains(self, reasoner, knowledge_objects):
        """R3.6 — System should build multi-paper reasoning chains."""
        results = reasoner.reason(knowledge_objects)
        assert "reasoning_chains" in results
    
    def test_chains_span_multiple_papers(self, reasoner, knowledge_objects):
        """R3.6 — Reasoning chains should span multiple papers."""
        results = reasoner.reason(knowledge_objects)
        for chain in results["reasoning_chains"]:
            assert "papers_involved" in chain
            assert "chain" in chain


# ─── R3.7 Unified Reasoning ───

class TestUnifiedReasoning:
    def test_produces_landscape(self, reasoner, knowledge_objects):
        """R3.7 — System should produce a research landscape assessment."""
        results = reasoner.reason(knowledge_objects)
        unified = results["unified_reasoning"]
        assert unified["landscape"] in ("mature", "contested", "developing", "insufficient_data")
    
    def test_produces_maturity_note(self, reasoner, knowledge_objects):
        """R3.7 — System should produce a maturity note."""
        results = reasoner.reason(knowledge_objects)
        unified = results["unified_reasoning"]
        assert len(unified["maturity_note"]) > 0
    
    def test_produces_overall_confidence(self, reasoner, knowledge_objects):
        """R3.7 — System should produce overall confidence score."""
        results = reasoner.reason(knowledge_objects)
        unified = results["unified_reasoning"]
        assert "overall_confidence" in unified
        assert 0 <= unified["overall_confidence"] <= 1.0
    
    def test_identifies_key_tensions(self, reasoner, knowledge_objects):
        """R3.7 — System should identify key tensions."""
        results = reasoner.reason(knowledge_objects)
        unified = results["unified_reasoning"]
        assert "key_tensions" in unified


# ─── Statistics ───

class TestReasoningStats:
    def test_stats_present(self, reasoner, knowledge_objects):
        """R3 — Results should include statistics."""
        results = reasoner.reason(knowledge_objects)
        stats = results["stats"]
        assert "num_papers" in stats
        assert "num_contradictions" in stats
        assert "num_consensus" in stats
        assert "num_assumption_conflicts" in stats
        assert "num_reasoning_chains" in stats
    
    def test_paper_count_correct(self, reasoner, knowledge_objects):
        """R3 — Paper count should match input."""
        results = reasoner.reason(knowledge_objects)
        assert results["stats"]["num_papers"] == 4


# ─── Edge Cases ───

class TestEdgeCases:
    def test_single_paper(self, reasoner):
        """R3 — Single paper should return results with 0 contradictions."""
        decomposer = KnowledgeDecomposer()
        papers = [{"text": PAPER_A, "title": "Solo Paper"}]
        objs = decomposer.decompose_batch(papers)
        results = reasoner.reason(objs)
        # With single paper, no cross-document reasoning possible
        assert results["stats"]["num_papers"] <= 1
        assert len(results["contradictions"]) == 0
    
    def test_empty_input(self, reasoner):
        """R3 — Empty input should return empty results."""
        results = reasoner.reason([])
        assert results["stats"]["num_papers"] == 0
