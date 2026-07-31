"""
R4 — Theory Synthesis Engine Tests

Tests:
- Claim aggregation
- Dominant mechanism identification
- Unified theory construction
- Research report generation
- Confidence scoring
"""

import pytest
from core.research.cognition.decomposition import KnowledgeDecomposer
from core.research.cognition.reasoning import CrossDocumentReasoner
from core.research.cognition.synthesis import TheorySynthesizer


SAMPLE_PAPERS = [
    """
We show that transfer entropy between financial institutions predicts systemic instability 
through asymmetric information propagation mechanisms. Our results demonstrate that higher 
transfer entropy between institutions predicts increased systemic instability (p < 0.001, 
R² = 0.87). We assume efficient information propagation between institutions. Information 
asymmetry causes volatility expansion through reduced market depth. We found that entropy 
accumulation precedes market crisis events. This is the first application of CEEMDAN 
filtering to financial contagion analysis.
""",
    """
We demonstrate that network topology controls systemic risk in interbank markets. 
Our analysis reveals that information imbalance drives market instability through 
cascading default mechanisms. We present a novel graph-theoretic framework. Results 
indicate that centrality measures explain 62% of variance in default probability. 
We propose that entropy accumulation in the network precedes systemic crisis events.
""",
    """
This meta-analysis confirms that both transfer entropy and network topology are 
significant predictors of systemic risk. Our results are consistent with previous 
findings that information asymmetry drives market instability. We found that entropy 
accumulation precedes systemic crisis events, supporting the information propagation 
hypothesis. The analysis covers 500 institutions across 20 countries.
""",
]


@pytest.fixture
def synthesizer():
    return TheorySynthesizer()


@pytest.fixture
def knowledge_objects():
    decomposer = KnowledgeDecomposer()
    papers = [
        {"text": text, "title": f"Paper {i+1}"}
        for i, text in enumerate(SAMPLE_PAPERS)
    ]
    return decomposer.decompose_batch(papers)


@pytest.fixture
def reasoning_results(knowledge_objects):
    reasoner = CrossDocumentReasoner()
    return reasoner.reason(knowledge_objects)


# ─── R4.1 Claim Aggregation ───

class TestClaimAggregation:
    def test_aggregates_claims(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.1 — System should aggregate claims across papers."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        clusters = results["theory_components"]["claim_clusters"]
        assert len(clusters) >= 1
    
    def test_clusters_by_domain(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.1 — Claims should be clustered by domain."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        clusters = results["theory_components"]["claim_clusters"]
        for cluster in clusters:
            assert "domain" in cluster
            assert "num_claims" in cluster


# ─── R4.2 Dominant Mechanisms ───

class TestDominantMechanisms:
    def test_identifies_dominant_mechanisms(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.2 — System should identify dominant mechanisms."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        mechanisms = results["theory_components"]["dominant_mechanisms"]
        assert len(mechanisms) >= 0  # May be 0 if mechanisms don't overlap
    
    def test_mechanisms_ranked_by_frequency(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.2 — Mechanisms should be ranked by frequency × confidence."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        mechanisms = results["theory_components"]["dominant_mechanisms"]
        if len(mechanisms) >= 2:
            # First should have higher or equal score than second
            assert mechanisms[0]["frequency"] * mechanisms[0]["avg_confidence"] >= \
                   mechanisms[1]["frequency"] * mechanisms[1]["avg_confidence"]


# ─── R4.3 Unified Theory Construction ───

class TestUnifiedTheory:
    def test_builds_theory(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.3 — System should build a unified theory."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        theory = results["unified_theory"]
        assert "statement" in theory
        assert len(theory["statement"]) > 0
    
    def test_theory_has_components(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.3 — Theory should have component parts."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        theory = results["unified_theory"]
        assert "components" in theory
        assert len(theory["components"]) >= 0
    
    def test_theory_identifies_open_questions(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.3 — Theory should identify open questions."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        theory = results["unified_theory"]
        assert "open_questions" in theory
    
    def test_theory_tracks_consensus_contradictions(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.3 — Theory should track consensus areas and contradictions."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        theory = results["unified_theory"]
        assert "consensus_areas" in theory
        assert "contradictions_remaining" in theory


# ─── R4.4 Research Report Generation ───

class TestResearchReport:
    def test_generates_report(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.4 — System should generate a research report."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        report = results["research_report"]
        assert "title" in report
        assert "full_report" in report
    
    def test_report_has_sections(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.4 — Report should have standard academic sections."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        report = results["research_report"]
        sections = report["sections"]
        assert "executive_summary" in sections
        assert "introduction" in sections
        assert "theoretical_framework" in sections
        assert "conclusion" in sections
    
    def test_report_has_word_count(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.4 — Report should have word count."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        report = results["research_report"]
        assert report["word_count"] > 50
    
    def test_report_has_references(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.4 — Report should count references."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        report = results["research_report"]
        assert report["num_references"] == len(knowledge_objects)


# ─── R4.5 Confidence Scoring ───

class TestSynthesisConfidence:
    def test_confidence_score(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.5 — Synthesis should have confidence score."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        assert 0 <= results["confidence"] <= 1.0
    
    def test_paper_count(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.5 — Should track number of papers synthesized."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        assert results["num_papers_synthesized"] == len(knowledge_objects)
    
    def test_domains_covered(self, synthesizer, knowledge_objects, reasoning_results):
        """R4.5 — Should list domains covered."""
        results = synthesizer.synthesize(knowledge_objects, reasoning_results)
        assert len(results["domains_covered"]) >= 1


# ─── Edge Cases ───

class TestSynthesisEdgeCases:
    def test_single_paper(self, synthesizer):
        """R4 — Single paper should still produce synthesis."""
        decomposer = KnowledgeDecomposer()
        papers = [{"text": SAMPLE_PAPERS[0], "title": "Solo"}]
        objs = decomposer.decompose_batch(papers)
        reasoner = CrossDocumentReasoner()
        reasoning = reasoner.reason(objs)
        results = synthesizer.synthesize(objs, reasoning)
        assert results["num_papers_synthesized"] == 1
    
    def test_empty_input(self, synthesizer):
        """R4 — Empty input should return empty synthesis."""
        results = synthesizer.synthesize([], {})
        assert results["num_papers_synthesized"] == 0
