"""
Tests for L3.4 — Finding evaluator.

5 tests covering:
1. Basic evaluation returns score 0-1
2. Source quality scoring
3. Citation count scoring
4. Recency scoring
5. Acceptable threshold
"""

import pytest

from core.research.agents.evaluator import FindingEvaluator


@pytest.fixture
def evaluator():
    return FindingEvaluator(threshold=0.6)


class TestEvaluatorBasic:
    """Test 1: Basic evaluation."""

    def test_evaluate_returns_score(self, evaluator):
        finding = {
            "paper_id": "W123",
            "source": "openalex",
            "citation_count": 10,
            "year": 2024,
        }
        score = evaluator.evaluate(finding)
        assert 0.0 <= score <= 1.0

    def test_evaluate_high_quality(self, evaluator):
        finding = {
            "paper_id": "W123",
            "source": "openalex",
            "citation_count": 100,
            "year": 2024,
            "llm_confidence": 0.9,
        }
        score = evaluator.evaluate(finding)
        assert score > 0.7

    def test_evaluate_low_quality(self, evaluator):
        finding = {
            "paper_id": "W456",
            "source": "s2",
            "citation_count": 0,
            "year": 2015,
            "llm_confidence": 0.2,
        }
        score = evaluator.evaluate(finding)
        assert score < 0.5


class TestEvaluatorSource:
    """Test 2: Source quality scoring."""

    def test_openalex_highest(self, evaluator):
        finding = {"source": "openalex", "citation_count": 0, "year": 2020}
        score_oa = evaluator.evaluate(finding)
        
        finding["source"] = "arxiv"
        score_arxiv = evaluator.evaluate(finding)
        
        assert score_oa > score_arxiv


class TestEvaluatorCitations:
    """Test 3: Citation count scoring."""

    def test_more_citations_higher_score(self, evaluator):
        low = evaluator.evaluate({"source": "openalex", "citation_count": 1, "year": 2024})
        high = evaluator.evaluate({"source": "openalex", "citation_count": 50, "year": 2024})
        assert high > low


class TestEvaluatorRecency:
    """Test 4: Recency scoring."""

    def test_newer_paper_higher_score(self, evaluator):
        old = evaluator.evaluate({"source": "openalex", "citation_count": 10, "year": 2015})
        new = evaluator.evaluate({"source": "openalex", "citation_count": 10, "year": 2024})
        assert new > old


class TestEvaluatorThreshold:
    """Test 5: Acceptable threshold."""

    def test_acceptable_above_threshold(self, evaluator):
        finding = {
            "source": "openalex",
            "citation_count": 20,
            "year": 2024,
            "llm_confidence": 0.8,
        }
        assert evaluator.is_acceptable(finding) is True

    def test_not_acceptable_below_threshold(self, evaluator):
        finding = {
            "source": "s2",
            "citation_count": 0,
            "year": 2010,
            "llm_confidence": 0.1,
        }
        assert evaluator.is_acceptable(finding) is False

    def test_evaluation_report(self, evaluator):
        finding = {
            "paper_id": "W123",
            "source": "openalex",
            "citation_count": 10,
            "year": 2024,
        }
        report = evaluator.get_evaluation_report(finding)
        assert "total_confidence" in report
        assert "breakdown" in report
        assert "acceptable" in report