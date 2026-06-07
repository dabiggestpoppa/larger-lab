"""
Tests for L2.1 — Rule-based paper distiller.

8 tests covering:
1. Basic distillation produces all 6 fields
2. CAUSE extraction from abstract
3. METHOD extraction from abstract
4. RESULT extraction with numbers
5. LIMITATIONS extraction
6. APPLICATION generation
7. LINKS generation from concepts
8. Fallback when abstract is empty
"""

import pytest

from core.research.distillation.distiller import Distiller
from core.research.ingestion.models import Author, Concept, Paper


@pytest.fixture
def distiller():
    return Distiller()


@pytest.fixture
def sample_paper():
    return Paper(
        id="W123456789",
        doi="10.1234/test.2024.001",
        title="Deep Learning for Agent Orchestration",
        abstract=(
            "The problem of coordinating multiple AI agents is challenging. "
            "We propose a novel attention-based framework for agent orchestration. "
            "Our method achieves 95% accuracy on the AgentBench benchmark, "
            "a 15% improvement over prior work. "
            "Limitations include high computational cost and reliance on synthetic training data. "
            "This work enables more efficient multi-agent systems."
        ),
        year=2024,
        source="openalex",
        source_id="W123456789",
        citation_count=42,
        authors=[
            Author(id="A1", name="Smith, John", orcid="0000-0000-0000-0001"),
            Author(id="A2", name="Doe, Jane", orcid=""),
        ],
        concepts=[
            Concept(id="C1", name="agent_orchestration", score=0.95, level=0),
            Concept(id="C2", name="attention_mechanisms", score=0.87, level=1),
            Concept(id="C3", name="multi_agent_systems", score=0.72, level=1),
        ],
        referenced_works=["W999888777", "W666555444"],
    )


class TestDistillerBasic:
    """Test 1: Basic distillation produces all required fields."""

    def test_distill_produces_note(self, distiller, sample_paper):
        note = distiller.distill(sample_paper)
        assert isinstance(note, str)
        assert len(note) > 0

    def test_note_contains_all_fields(self, distiller, sample_paper):
        note = distiller.distill(sample_paper)
        assert "CAUSE:" in note
        assert "METHOD:" in note
        assert "RESULT:" in note
        assert "LIMITATIONS:" in note
        assert "APPLICATION:" in note
        assert "LINKS:" in note

    def test_note_contains_title(self, distiller, sample_paper):
        note = distiller.distill(sample_paper)
        assert sample_paper.title in note


class TestDistillerCause:
    """Test 2: CAUSE extraction."""

    def test_cause_extracted(self, distiller, sample_paper):
        note = distiller.distill(sample_paper)
        cause_section = note.split("CAUSE:")[1].split("METHOD:")[0].strip()
        assert len(cause_section) > 0
        assert cause_section != "Problem not explicitly stated"


class TestDistillerMethod:
    """Test 3: METHOD extraction."""

    def test_method_extracted(self, distiller, sample_paper):
        note = distiller.distill(sample_paper)
        method_section = note.split("METHOD:")[1].split("RESULT:")[0].strip()
        assert len(method_section) > 0
        assert "propose" in method_section.lower() or "framework" in method_section.lower()


class TestDistillerResult:
    """Test 4: RESULT extraction with numbers."""

    def test_result_contains_numbers(self, distiller, sample_paper):
        note = distiller.distill(sample_paper)
        result_section = note.split("RESULT:")[1].split("LIMITATIONS:")[0].strip()
        assert len(result_section) > 0
        # Should contain at least one digit (from "95%" or "15%")
        assert any(c.isdigit() for c in result_section)


class TestDistillerLimitations:
    """Test 5: LIMITATIONS extraction."""

    def test_limitations_extracted(self, distiller, sample_paper):
        note = distiller.distill(sample_paper)
        lim_section = note.split("LIMITATIONS:")[1].split("APPLICATION:")[0].strip()
        assert len(lim_section) > 0


class TestDistillerApplication:
    """Test 6: APPLICATION generation."""

    def test_application_generated(self, distiller, sample_paper):
        note = distiller.distill(sample_paper)
        app_section = note.split("APPLICATION:")[1].split("LINKS:")[0].strip()
        assert len(app_section) > 0


class TestDistillerLinks:
    """Test 7: LINKS generation from concepts."""

    def test_links_contain_concepts(self, distiller, sample_paper):
        note = distiller.distill(sample_paper)
        links_section = note.split("LINKS:")[1].strip()
        # Should contain at least one concept link
        assert "[[" in links_section or "No links" in links_section


class TestDistillerFallback:
    """Test 8: Fallback when abstract is empty."""

    def test_empty_abstract_fallback(self, distiller):
        paper = Paper(
            id="W000",
            title="Test Paper",
            abstract="",
            year=2024,
            source="openalex",
        )
        note = distiller.distill(paper)
        assert "CAUSE:" in note
        assert "METHOD:" in note
        # Should not crash, should produce fallback text
        assert len(note) > 50