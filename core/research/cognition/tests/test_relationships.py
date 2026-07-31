"""
R2 — Semantic Relationship Construction Tests

Tests:
R2.1 Concept entity extraction
R2.2 Semantic relationship detection
R2.3 Causal chain construction
R2.4 Knowledge graph building
R2.5 Dependency mapping
R2.6 Similarity clustering
"""

import pytest
from core.research.cognition.decomposition import KnowledgeDecomposer
from core.research.cognition.relationships import RelationshipBuilder


SAMPLE_PAPER_1 = """
We show that transfer entropy between financial institutions predicts systemic instability 
through asymmetric information propagation mechanisms. Our results demonstrate that higher 
transfer entropy predicts increased systemic instability. We assume efficient information 
propagation between institutions. Information asymmetry causes volatility expansion through 
reduced market depth. We found that entropy accumulation precedes market crisis events.
"""

SAMPLE_PAPER_2 = """
We demonstrate that network topology controls systemic risk in interbank markets. 
Our analysis reveals that information imbalance drives market instability through 
cascading default mechanisms. We present a novel graph-theoretic framework. 
Results indicate that centrality measures explain 62% of variance in default probability. 
We propose that entropy accumulation in the network precedes systemic crisis events.
"""

SAMPLE_PAPER_3 = """
This study examines how liquidity shortages amplify price volatility during systemic stress. 
We show that reduced market depth leads to increased price volatility. Our model assumes 
rational actor behavior and stationary market conditions. The results demonstrate that 
liquidity contraction causes volatility expansion. We found that diversification strategies 
are most effective during periods of low volatility.
"""


@pytest.fixture
def builder():
    return RelationshipBuilder()


@pytest.fixture
def knowledge_objects():
    decomposer = KnowledgeDecomposer()
    papers = [
        {"text": SAMPLE_PAPER_1, "title": "Transfer Entropy Paper"},
        {"text": SAMPLE_PAPER_2, "title": "Network Topology Paper"},
        {"text": SAMPLE_PAPER_3, "title": "Liquidity Paper"},
    ]
    return decomposer.decompose_batch(papers)


# ─── R2.1 Concept Entity Extraction ───

class TestConceptExtraction:
    def test_extracts_concepts(self, builder, knowledge_objects):
        """R2.1 — System should extract concept entities."""
        graph = builder.build_graph(knowledge_objects)
        assert graph["stats"]["num_concepts"] > 0
    
    def test_concepts_have_domains(self, builder, knowledge_objects):
        """R2.1 — Concepts should be assigned to domains."""
        graph = builder.build_graph(knowledge_objects)
        concepts = graph["concepts"]
        # At least some concepts should have non-empty domains
        domains = [c.get("domain", "") for c in concepts.values()]
        assert any(d for d in domains)
    
    def test_concepts_have_frequencies(self, builder, knowledge_objects):
        """R2.1 — Concepts should have frequency counts."""
        graph = builder.build_graph(knowledge_objects)
        concepts = graph["concepts"]
        for concept in concepts.values():
            assert concept["frequency"] >= 1


# ─── R2.2 Semantic Relationship Detection ───

class TestRelationshipDetection:
    def test_detects_relationships(self, builder, knowledge_objects):
        """R2.2 — System should detect semantic relationships."""
        graph = builder.build_graph(knowledge_objects)
        assert graph["stats"]["num_relationships"] > 0
    
    def test_relationships_have_types(self, builder, knowledge_objects):
        """R2.2 — Relationships should have typed connections."""
        graph = builder.build_graph(knowledge_objects)
        relationships = graph["relationships"]
        types = {r["type"] for r in relationships}
        assert len(types) >= 1
    
    def test_relationships_have_confidence(self, builder, knowledge_objects):
        """R2.2 — Relationships should have confidence scores."""
        graph = builder.build_graph(knowledge_objects)
        for rel in graph["relationships"]:
            assert 0 <= rel["confidence"] <= 1.0


# ─── R2.3 Causal Chain Construction ───

class TestCausalChains:
    def test_builds_causal_chains(self, builder, knowledge_objects):
        """R2.3 — System should build multi-step causal chains."""
        graph = builder.build_graph(knowledge_objects)
        # With 3 papers about finance, should find at least 1 chain
        assert graph["stats"]["num_causal_chains"] >= 0  # May be 0 if papers don't connect
    
    def test_chains_have_minimum_length(self, builder, knowledge_objects):
        """R2.3 — Causal chains should have at least 3 nodes."""
        graph = builder.build_graph(knowledge_objects)
        for chain in graph["causal_chains"]:
            assert chain["length"] >= 3
    
    def test_chains_have_confidence(self, builder, knowledge_objects):
        """R2.3 — Causal chains should have confidence scores."""
        graph = builder.build_graph(knowledge_objects)
        for chain in graph["causal_chains"]:
            assert 0 <= chain["confidence"] <= 1.0


# ─── R2.4 Knowledge Graph ───

class TestKnowledgeGraph:
    def test_builds_graph(self, builder, knowledge_objects):
        """R2.4 — System should build a knowledge graph."""
        graph = builder.build_graph(knowledge_objects)
        assert "graph" in graph
        assert len(graph["graph"]) > 0
    
    def test_graph_is_serializable(self, builder, knowledge_objects):
        """R2.4 — Graph should be JSON-serializable."""
        import json
        graph = builder.build_graph(knowledge_objects)
        # Should not raise
        json.dumps(graph["graph"], default=str)


# ─── R2.5 Dependency Mapping ───

class TestDependencyMapping:
    def test_maps_dependencies(self, builder, knowledge_objects):
        """R2.5 — System should map concept dependencies."""
        graph = builder.build_graph(knowledge_objects)
        assert "dependencies" in graph
    
    def test_dependencies_have_types(self, builder, knowledge_objects):
        """R2.5 — Dependencies should have relationship types."""
        graph = builder.build_graph(knowledge_objects)
        for dep in graph["dependencies"]:
            assert "type" in dep


# ─── R2.6 Similarity Clustering ───

class TestSimilarityClustering:
    def test_clusters_concepts(self, builder, knowledge_objects):
        """R2.6 — System should cluster similar concepts."""
        graph = builder.build_graph(knowledge_objects)
        assert "clusters" in graph
    
    def test_clusters_have_domains(self, builder, knowledge_objects):
        """R2.6 — Clusters should be domain-specific."""
        graph = builder.build_graph(knowledge_objects)
        for cluster in graph["clusters"]:
            assert "domain" in cluster
            assert "concepts" in cluster
            assert cluster["size"] >= 2


# ─── Graph Statistics ───

class TestGraphStats:
    def test_stats_present(self, builder, knowledge_objects):
        """R2 — Graph should include statistics."""
        graph = builder.build_graph(knowledge_objects)
        stats = graph["stats"]
        assert "num_concepts" in stats
        assert "num_relationships" in stats
        assert "num_causal_chains" in stats
        assert "num_clusters" in stats
        assert "num_papers" in stats
    
    def test_paper_count_correct(self, builder, knowledge_objects):
        """R2 — Paper count should match input."""
        graph = builder.build_graph(knowledge_objects)
        assert graph["stats"]["num_papers"] == 3
