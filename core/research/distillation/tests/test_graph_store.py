"""
Tests for L2.5 — SQLite knowledge graph store.

5 tests covering:
1. Add node and retrieve
2. Add edge and retrieve
3. Add paper with relations
4. Query nodes by kind
5. Node/edge count
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from core.research.distillation.graph_store import GraphStore
from core.research.ingestion.models import Author, Concept, Paper


@pytest.fixture
def temp_graph():
    """Create a graph store with a temporary database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_graph.db"
        graph = GraphStore(db_path)
        yield graph


@pytest.fixture
def sample_paper():
    return Paper(
        id="W123456789",
        doi="10.1234/test.2024.001",
        title="Test Paper",
        abstract="Test abstract.",
        year=2024,
        source="openalex",
        authors=[
            Author(id="A1", name="Smith, John"),
        ],
        concepts=[
            Concept(id="C1", name="agent_orchestration", score=0.95, level=0),
        ],
        referenced_works=["W999888777"],
    )


class TestGraphNode:
    """Test 1: Add node and retrieve."""

    def test_add_node(self, temp_graph):
        assert temp_graph.add_node("test:1", "paper", "Test Paper") is True

    def test_add_duplicate_node_ignored(self, temp_graph):
        temp_graph.add_node("test:1", "paper", "Test Paper")
        assert temp_graph.add_node("test:1", "paper", "Test Paper") is False

    def test_get_node_count(self, temp_graph):
        temp_graph.add_node("test:1", "paper", "Paper 1")
        temp_graph.add_node("test:2", "paper", "Paper 2")
        assert temp_graph.get_node_count() == 2


class TestGraphEdge:
    """Test 2: Add edge and retrieve."""

    def test_add_edge(self, temp_graph):
        temp_graph.add_node("src:1", "paper", "Source")
        temp_graph.add_node("dst:1", "paper", "Destination")
        assert temp_graph.add_edge("src:1", "dst:1", "cites") is True

    def test_add_duplicate_edge_ignored(self, temp_graph):
        temp_graph.add_node("src:1", "paper", "Source")
        temp_graph.add_node("dst:1", "paper", "Destination")
        temp_graph.add_edge("src:1", "dst:1", "cites")
        assert temp_graph.add_edge("src:1", "dst:1", "cites") is False

    def test_get_edge_count(self, temp_graph):
        temp_graph.add_node("src:1", "paper", "Source")
        temp_graph.add_node("dst:1", "paper", "Dest 1")
        temp_graph.add_node("dst:2", "paper", "Dest 2")
        temp_graph.add_edge("src:1", "dst:1", "cites")
        temp_graph.add_edge("src:1", "dst:2", "cites")
        assert temp_graph.get_edge_count() == 2


class TestGraphPaper:
    """Test 3: Add paper with relations."""

    def test_add_paper_creates_nodes_and_edges(self, temp_graph, sample_paper):
        count = temp_graph.add_paper(sample_paper)
        # Should create: 1 paper + 1 author + 1 concept + 1 citation edge = 4
        assert count >= 3

    def test_paper_node_exists(self, temp_graph, sample_paper):
        temp_graph.add_paper(sample_paper)
        nodes = temp_graph.query_nodes(kind="paper")
        assert len(nodes) >= 1
        assert any(n["label"] == "Test Paper" for n in nodes)


class TestGraphQuery:
    """Test 4: Query nodes by kind."""

    def test_query_by_kind(self, temp_graph):
        temp_graph.add_node("p:1", "paper", "Paper 1")
        temp_graph.add_node("p:2", "paper", "Paper 2")
        temp_graph.add_node("a:1", "author", "Author 1")
        
        papers = temp_graph.query_nodes(kind="paper")
        assert len(papers) == 2
        
        authors = temp_graph.query_nodes(kind="author")
        assert len(authors) == 1

    def test_query_with_limit(self, temp_graph):
        for i in range(10):
            temp_graph.add_node(f"p:{i}", "paper", f"Paper {i}")
        
        nodes = temp_graph.query_nodes(kind="paper", limit=5)
        assert len(nodes) == 5


class TestGraphStats:
    """Test 5: Node/edge count."""

    def test_empty_graph(self, temp_graph):
        assert temp_graph.get_node_count() == 0
        assert temp_graph.get_edge_count() == 0

    def test_counts_after_adding(self, temp_graph, sample_paper):
        temp_graph.add_paper(sample_paper)
        assert temp_graph.get_node_count() >= 3
        assert temp_graph.get_edge_count() >= 1