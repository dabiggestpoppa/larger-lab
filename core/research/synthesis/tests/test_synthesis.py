"""
Tests for Phase 1.5 — Sisyphus Synthesis Engine
"""

import pytest

from core.research.synthesis.sisyphus import (
    Claim,
    SisyphusEngine,
    SourceDocument,
    SynthesisResult,
)
from core.research.synthesis.argument import ArgumentStructurer, Evidence
from core.research.synthesis.citation import Citation, CitationMapper
from core.research.synthesis.contradiction import ContradictionDetector


class TestSisyphusEngine:
    """Test Sisyphus synthesis engine."""

    def test_synthesize_empty_sources(self):
        engine = SisyphusEngine()
        result = engine.synthesize("test query", [])
        assert result.source_count == 0
        assert result.confidence == 0.0

    def test_synthesize_with_sources(self):
        engine = SisyphusEngine()
        sources = [
            SourceDocument(
                doc_id="doc1",
                title="Paper on Semantic Memory",
                text="This paper shows that semantic memory improves agent reasoning. "
                     "The results demonstrate significant improvements. "
                     "We find that agents with semantic memory perform better.",
            ),
            SourceDocument(
                doc_id="doc2",
                title="Memory in AI Systems",
                text="Our findings indicate that memory systems enhance performance. "
                     "The evidence suggests that semantic approaches are superior. "
                     "We observe consistent improvements across all benchmarks.",
            ),
        ]

        result = engine.synthesize("How does semantic memory help agents?", sources)

        assert result.source_count == 2
        assert result.query == "How does semantic memory help agents?"
        assert len(result.key_findings) > 0
        assert len(result.citations) == 2

    def test_extract_claims(self):
        engine = SisyphusEngine()
        source = SourceDocument(
            doc_id="doc1",
            title="Test",
            text="This study shows that X improves Y. "
                 "We find significant results. "
                 "The evidence demonstrates clear improvements.",
        )

        claims = engine._extract_claims(source, "test query")
        assert len(claims) > 0
        # Claims should contain assertion-like sentences
        assert any("shows" in c.text.lower() or "find" in c.text.lower() for c in claims)

    def test_is_claim(self):
        engine = SisyphusEngine()
        assert engine._is_claim("This study shows that X improves Y")
        assert engine._is_claim("We find significant results")
        assert not engine._is_claim("The weather is nice today")

    def test_detect_contradictions(self):
        engine = SisyphusEngine()
        # Use nearly identical text so Jaccard similarity is high
        base = "machine learning improves prediction accuracy in all tested scenarios"
        claims = [
            Claim(text=base, supporting_sources=["doc1"]),
            Claim(text="machine learning does not improve prediction accuracy in all tested scenarios", supporting_sources=["doc2"]),
        ]

        contradictions = engine._detect_contradictions(claims)
        assert len(contradictions) > 0

    def test_merge_claims(self):
        engine = SisyphusEngine()
        group = [
            Claim(text="X improves Y", confidence=0.5, supporting_sources=["doc1"]),
            Claim(text="X significantly improves Y in all cases", confidence=0.6, supporting_sources=["doc2"]),
        ]

        merged = engine._merge_claims(group)
        # Should use longest text
        assert "significantly" in merged.text
        # Should have both sources
        assert "doc1" in merged.supporting_sources
        assert "doc2" in merged.supporting_sources
        # Confidence should be higher with multiple sources
        assert merged.confidence > 0.5

    def test_identify_gaps(self):
        engine = SisyphusEngine()
        result = SynthesisResult(
            query="test",
            confidence=0.3,
            source_count=1,
            contradictions=[{"severity": "high"}],
        )

        gaps = engine._identify_gaps(result)
        assert any("Low overall" in g for g in gaps)
        assert any("Only 1 sources" in g for g in gaps)
        assert any("contradictions" in g for g in gaps)

    def test_synthesis_result_to_dict(self):
        result = SynthesisResult(
            query="test query",
            executive_summary="Test summary",
            key_findings=[
                Claim(text="Finding 1", confidence=0.8, supporting_sources=["doc1"]),
            ],
            source_count=2,
            confidence=0.75,
        )

        d = result.to_dict()
        assert d["query"] == "test query"
        assert d["confidence"] == 0.75
        assert len(d["key_findings"]) == 1
        assert d["key_findings"][0]["text"] == "Finding 1"


class TestArgumentStructurer:
    """Test argument structurer."""

    def test_structure_argument(self):
        structurer = ArgumentStructurer()
        evidence = [
            Evidence(text="Study A shows X improves Y", source="doc1", strength=0.8),
            Evidence(text="Study B confirms the effect", source="doc2", strength=0.7),
        ]

        argument = structurer.structure(
            claim="X improves Y",
            evidence_list=evidence,
            reasoning="Multiple studies confirm the effect",
        )

        assert argument.root is not None
        assert argument.root.text == "X improves Y"
        assert len(argument.root.children) == 3  # 2 evidence + 1 reasoning
        assert argument.overall_strength > 0.5

    def test_detect_gaps(self):
        structurer = ArgumentStructurer()
        from core.research.synthesis.argument import ArgumentNode
        root = ArgumentNode(text="test", node_type="claim")
        gaps = structurer._detect_gaps(root, [])  # no evidence
        assert any("No evidence" in g for g in gaps)

    def test_mermaid_output(self):
        structurer = ArgumentStructurer()
        evidence = [Evidence(text="Evidence 1", source="doc1", strength=0.8)]

        argument = structurer.structure(claim="Test claim", evidence_list=evidence)
        mermaid = argument.to_mermaid()

        assert "graph TD" in mermaid
        assert "Test claim" in mermaid


class TestCitationMapper:
    """Test citation mapper."""

    def test_extract_dois(self):
        mapper = CitationMapper()
        text = "This paper (doi: 10.1038/s41586-021-03819-2) shows important results."

        citations = mapper.extract_citations(text)
        assert len(citations) == 1
        assert citations[0].doi == "10.1038/s41586-021-03819-2"

    def test_extract_arxiv(self):
        mapper = CitationMapper()
        text = "See arXiv:2401.00001 for details."

        citations = mapper.extract_citations(text)
        assert len(citations) == 1
        assert citations[0].arxiv_id == "2401.00001"

    def test_apa_format(self):
        citation = Citation(
            citation_id="test",
            title="Test Paper",
            authors=["John Doe", "Jane Smith"],
            year="2024",
            doi="10.1000/test",
        )

        apa = citation.to_apa()
        assert "John Doe" in apa
        assert "2024" in apa
        assert "Test Paper" in apa
        assert "10.1000/test" in apa

    def test_bibtex_format(self):
        citation = Citation(
            citation_id="test",
            title="Test Paper",
            authors=["John Doe"],
            year="2024",
            doi="10.1000/test",
        )

        bibtex = citation.to_bibtex()
        assert "@misc" in bibtex
        assert "Test Paper" in bibtex
        assert "2024" in bibtex

    def test_generate_bibliography(self):
        mapper = CitationMapper()
        citations = [
            Citation(citation_id="c1", title="Paper A", authors=["A"], year="2024"),
            Citation(citation_id="c2", title="Paper B", authors=["B"], year="2023"),
        ]

        bib = mapper.generate_bibliography(citations, format="apa")
        assert "Paper A" in bib
        assert "Paper B" in bib

    def test_validate_citation(self):
        mapper = CitationMapper()
        valid = Citation(citation_id="c1", title="Test", authors=["A"], year="2024", doi="10.1000/test")
        result = mapper.validate_citation(valid)
        assert result["valid"] is True

        invalid = Citation(citation_id="c2")
        result = mapper.validate_citation(invalid)
        assert result["valid"] is False


class TestContradictionDetector:
    """Test contradiction detector."""

    def test_detect_negation_contradiction(self):
        detector = ContradictionDetector()
        claims = [
            {"text": "X improves performance significantly", "source": "doc1"},
            {"text": "X does not improve performance", "source": "doc2"},
        ]

        contradictions = detector.detect(claims)
        assert len(contradictions) > 0
        assert contradictions[0].severity in ("low", "medium", "high")

    def test_no_contradiction_for_consistent_claims(self):
        detector = ContradictionDetector()
        claims = [
            {"text": "X improves performance", "source": "doc1"},
            {"text": "X also improves performance", "source": "doc2"},
        ]

        contradictions = detector.detect(claims)
        assert len(contradictions) == 0

    def test_severity_scoring(self):
        detector = ContradictionDetector()
        # High similarity + negation = high severity
        severity = detector._score_severity(0.8, "X is good", "X is not good")
        assert severity == "high"

        severity = detector._score_severity(0.3, "X is good", "Y is not good")
        assert severity == "low"

    def test_resolution_suggestions(self):
        detector = ContradictionDetector()
        hint = detector._suggest_resolution(
            "X was true in 2020",
            "X is not true in 2024",
        )
        assert "time periods" in hint
