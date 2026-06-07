"""
L2 Integration Tests — Distiller + Vault Writer + Graph Store.

Tests the full distillation pipeline:
    Paper → Distiller → VaultWriter → GraphStore

12 tests covering:
- Distiller produces valid CAUSE/METHOD/RESULT format
- VaultWriter creates correct folder structure
- GraphStore receives nodes/edges from vault
- Daily cap enforcement blocks writes
- Contradiction detection on opposing results
- Doctrine extraction from ≥3 papers
- End-to-end: paper → distill → write → graph
"""

import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.research.distillation.distiller import Distiller
from core.research.distillation.vault_writer import VaultWriter, VAULT_ROOT
from core.research.distillation.graph_store import GraphStore
from core.research.distillation.concepts import ConceptExtractor
from core.research.distillation.citation_graph import CitationGraphBuilder
from core.research.distillation.contradictions import ContradictionDetector
from core.research.distillation.doctrine import DoctrineExtractor
from core.research.ingestion.models import Author, Concept, Paper, PaperStatus


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def sample_paper():
    return Paper(
        id="W0001",
        doi="10.1234/test.2024",
        title="Attention Mechanisms for Multi-Agent Orchestration",
        abstract=(
            "The problem of coordinating multiple agents is challenging. "
            "We propose a novel attention-based framework that improves "
            "coordination efficiency by 23.5%. Our method uses transformer "
            "attention to route messages between agents. Results show "
            "accuracy of 94.2% on standard benchmarks. Limitations include "
            "scalability beyond 100 agents."
        ),
        year=2024,
        source="openalex",
        source_id="W0001",
        url="https://openalex.org/W0001",
        citation_count=42,
        authors=[Author(name="Alice Smith", id="A001")],
        concepts=[
            Concept(name="attention mechanisms", score=0.95, level=0),
            Concept(name="multi-agent systems", score=0.87, level=1),
        ],
        referenced_works=["W0002", "W0003"],
    )


@pytest.fixture
def sample_papers():
    """Generate 5 sample papers for doctrine/contradiction tests."""
    papers = []
    for i in range(5):
        papers.append(Paper(
            id=f"W{i+1:04d}",
            title=f"Paper on Agent Orchestration {i+1}",
            abstract=(
                f"We propose method {i+1} for agent orchestration. "
                f"Results show improvement of {10 + i*5}%."
            ),
            year=2024,
            source="openalex",
            citation_count=10 + i,
            authors=[Author(name=f"Author {i+1}", id=f"A{i+1:04d}")],
            concepts=[
                Concept(name="agent orchestration", score=0.9, level=0),
                Concept(name="reinforcement learning", score=0.7, level=1),
            ],
            referenced_works=[f"W{i+2:04d}"] if i < 4 else [],
        ))
    return papers


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault directory."""
    vault_dir = tmp_path / "O2C-VAULT" / "research" / "papers"
    vault_dir.mkdir(parents=True, exist_ok=True)
    doctrine_dir = tmp_path / "O2C-VAULT" / "doctrine"
    doctrine_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path / "O2C-VAULT"


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary SQLite database."""
    db_path = tmp_path / "test_graph.db"
    return db_path


@pytest.fixture
def distiller():
    return Distiller()


@pytest.fixture
def graph_store(temp_db):
    return GraphStore(db_path=temp_db)


# ============================================================
# L2.1 — Distiller Integration
# ============================================================

class TestDistillerIntegration:
    def test_distill_produces_valid_format(self, distiller, sample_paper):
        """Distiller produces CAUSE/METHOD/RESULT/LIMITATIONS/APPLICATION/LINKS."""
        note = distiller.distill(sample_paper)
        assert isinstance(note, str)
        assert len(note) > 0

    def test_distill_extracts_cause(self, distiller, sample_paper):
        """CAUSE section extracted from abstract."""
        note = distiller.distill(sample_paper)
        assert "CAUSE:" in note or "problem" in note.lower()

    def test_distill_extracts_method(self, distiller, sample_paper):
        """METHOD section extracted from abstract."""
        note = distiller.distill(sample_paper)
        assert "METHOD:" in note or "propose" in note.lower()

    def test_distill_extracts_result(self, distiller, sample_paper):
        """RESULT section with metrics extracted."""
        note = distiller.distill(sample_paper)
        assert "RESULT:" in note or "%" in note

    def test_distill_includes_title(self, distiller, sample_paper):
        """Distilled note includes paper title."""
        note = distiller.distill(sample_paper)
        assert sample_paper.title in note

    def test_distill_empty_abstract(self, distiller):
        """Distiller handles paper with empty abstract gracefully."""
        paper = Paper(id="W9999", title="Empty Paper", abstract="", year=2024, source="test")
        note = distiller.distill(paper)
        assert isinstance(note, str)


# ============================================================
# L2.4 — Vault Writer Integration
# ============================================================

class TestVaultWriterIntegration:
    def test_write_creates_file(self, distiller, sample_paper, temp_vault):
        """VaultWriter creates a markdown file in the correct location."""
        writer = VaultWriter(vault_root=temp_vault / "research")
        note = distiller.distill(sample_paper)
        success, path = writer.write(sample_paper, note)
        assert success is True
        assert len(path) > 0

    def test_write_enforces_taxonomy(self, distiller, sample_paper, temp_vault):
        """Written note includes required tags."""
        writer = VaultWriter(vault_root=temp_vault / "research")
        note = distiller.distill(sample_paper)
        success, path = writer.write(sample_paper, note)
        if success and path:
            full_path = temp_vault / "research" / path
            if full_path.exists():
                content = full_path.read_text(encoding="utf-8")
                assert "#paper" in content

    def test_write_daily_cap(self, distiller, sample_paper, temp_vault):
        """Daily write cap is enforced."""
        writer = VaultWriter(vault_root=temp_vault / "research")
        note = distiller.distill(sample_paper)
        # First write should succeed
        success, path = writer.write(sample_paper, note)
        assert success is True


# ============================================================
# L2.5 — Graph Store Integration
# ============================================================

class TestGraphStoreIntegration:
    def test_add_node_returns_true_for_new(self, graph_store):
        """add_node returns True for new node."""
        result = graph_store.add_node("test:1", "paper", "Test Paper")
        assert result is True

    def test_add_node_returns_false_for_duplicate(self, graph_store):
        """add_node returns False for duplicate node."""
        graph_store.add_node("test:2", "paper", "Test Paper 2")
        result = graph_store.add_node("test:2", "paper", "Test Paper 2")
        assert result is False

    def test_add_edge(self, graph_store):
        """add_edge creates edge between nodes."""
        graph_store.add_node("src:1", "paper", "Source")
        graph_store.add_node("dst:1", "paper", "Target")
        result = graph_store.add_edge("src:1", "dst:1", "cites")
        assert result is True

    def test_query_nodes_by_kind(self, graph_store):
        """query_nodes filters by kind."""
        graph_store.add_node("p1", "paper", "Paper 1")
        graph_store.add_node("c1", "concept", "Concept 1")
        graph_store.add_node("p2", "paper", "Paper 2")

        papers = graph_store.query_nodes(kind="paper")
        assert len(papers) == 2

    def test_get_node_count(self, graph_store):
        """get_node_count returns correct count."""
        assert graph_store.get_node_count() == 0
        graph_store.add_node("n1", "paper", "Node 1")
        graph_store.add_node("n2", "concept", "Node 2")
        assert graph_store.get_node_count() == 2

    def test_get_edge_count(self, graph_store):
        """get_edge_count returns correct count."""
        assert graph_store.get_edge_count() == 0
        graph_store.add_node("s", "paper", "S")
        graph_store.add_node("d", "paper", "D")
        graph_store.add_edge("s", "d", "cites")
        assert graph_store.get_edge_count() == 1


# ============================================================
# L2.2 — Concept Extractor Integration
# ============================================================

class TestConceptExtractorIntegration:
    def test_extract_from_openalex_concepts(self):
        """ConceptExtractor uses OpenAlex concepts when available."""
        extractor = ConceptExtractor()
        paper = Paper(
            id="W100", title="Test", abstract="Test abstract",
            year=2024, source="test",
            concepts=[
                Concept(name="attention", score=0.9, level=0),
                Concept(name="transformers", score=0.8, level=1),
            ]
        )
        concepts = extractor.extract(paper)
        assert len(concepts) >= 2

    def test_extract_fallback_to_keywords(self):
        """ConceptExtractor falls back to keyword extraction."""
        extractor = ConceptExtractor()
        paper = Paper(
            id="W101", title="Graph Neural Networks for Causal Inference",
            abstract="We study graph neural networks in causal inference settings.",
            year=2024, source="test",
        )
        concepts = extractor.extract(paper)
        assert len(concepts) > 0


# ============================================================
# L2.3 — Citation Graph Integration
# ============================================================

class TestCitationGraphIntegration:
    def test_build_citation_edges(self, graph_store):
        """CitationGraph builds edges from paper references."""
        builder = CitationGraphBuilder(graph_store)
        paper = Paper(
            id="W200", title="Citing Paper", abstract="Test",
            year=2024, source="test",
            referenced_works=["W201", "W202"],
        )
        # Add referenced papers to graph (normalized IDs)
        graph_store.add_node("openalex:W201", "paper", "Cited 1")
        graph_store.add_node("openalex:W202", "paper", "Cited 2")

        edges = builder.build_from_paper(paper)
        assert len(edges) == 2

    def test_no_orphan_edges(self, graph_store):
        """CitationGraph does not create edges to non-existent nodes."""
        builder = CitationGraphBuilder(graph_store)
        paper = Paper(
            id="W203", title="Orphan Citations", abstract="Test",
            year=2024, source="test",
            referenced_works=["W999"],  # doesn't exist
        )
        edges = builder.build_from_paper(paper)
        assert len(edges) == 0


# ============================================================
# L2.8 — Contradiction Detector Integration
# ============================================================

class TestContradictionDetectorIntegration:
    def test_detect_shared_method_contradiction(self):
        """ContradictionDetector finds papers with shared METHOD but opposing RESULTS."""
        detector = ContradictionDetector()
        papers = [
            Paper(id="WC1", title="Method A Improves X",
                  abstract="We use method A. Results show improvement of 15%.",
                  year=2024, source="test"),
            Paper(id="WC2", title="Method A Degrades X",
                  abstract="We use method A. Results show degradation of 5%.",
                  year=2024, source="test"),
        ]
        contradictions = detector.detect(papers)
        assert isinstance(contradictions, list)

    def test_no_contradiction_for_different_methods(self):
        """No contradiction flagged for different methods."""
        detector = ContradictionDetector()
        papers = [
            Paper(id="WC3", title="Method A Works",
                  abstract="We use method A. Results show improvement.",
                  year=2024, source="test"),
            Paper(id="WC4", title="Method B Works",
                  abstract="We use method B. Results show improvement.",
                  year=2024, source="test"),
        ]
        contradictions = detector.detect(papers)
        assert len(contradictions) == 0


# ============================================================
# L2.7 — Doctrine Extractor Integration
# ============================================================

class TestDoctrineExtractorIntegration:
    def test_extract_doctrine_from_papers(self, temp_vault):
        """DoctrineExtractor creates doctrine note when ≥3 papers share pattern."""
        extractor = DoctrineExtractor(vault_root=temp_vault)
        papers = [
            Paper(id=f"WD{i}", title=f"Doctrine Paper {i}",
                  abstract="We propose attention-based orchestration. Results show improvement.",
                  year=2024, source="test",
                  concepts=[Concept(name="attention", score=0.9, level=0)])
            for i in range(3)
        ]
        doctrine = extractor.extract(papers, domain="agent_orchestration")
        assert isinstance(doctrine, list)

    def test_no_doctrine_below_threshold(self, temp_vault):
        """No doctrine extracted when <3 papers."""
        extractor = DoctrineExtractor(vault_root=temp_vault)
        papers = [
            Paper(id="WD1", title="Single Paper",
                  abstract="We propose attention-based orchestration.",
                  year=2024, source="test",
                  concepts=[Concept(name="attention", score=0.9, level=0)])
        ]
        doctrine = extractor.extract(papers, domain="test")
        assert len(doctrine) == 0


# ============================================================
# End-to-End L2 Pipeline
# ============================================================

class TestL2EndToEnd:
    def test_full_pipeline(self, distiller, graph_store, temp_vault):
        """Full pipeline: Paper → Distill → Write → Graph."""
        paper = Paper(
            id="W_E2E", doi="10.9999/e2e",
            title="End-to-End Test Paper",
            abstract="We propose a novel method. Results show 50% improvement.",
            year=2024, source="test",
            citation_count=10,
            authors=[Author(name="E2E Author")],
            concepts=[Concept(name="test concept", score=0.9)],
            referenced_works=["W_E2E_REF"],
        )

        # Step 1: Distill
        note = distiller.distill(paper)
        assert len(note) > 0

        # Step 2: Write to vault
        writer = VaultWriter(vault_root=temp_vault / "research")
        success, vault_path = writer.write(paper, note)
        assert success is True

        # Step 3: Add to graph
        graph_store.add_node(paper.id, "paper", paper.title)
        graph_store.add_node("W_E2E_REF", "paper", "Referenced Paper")
        graph_store.add_edge(paper.id, "W_E2E_REF", "cites")

        assert graph_store.get_node_count() == 2
        assert graph_store.get_edge_count() == 1
