"""
Tests for Pattern Crystallization Engine — Phase 01 Component 2
"""

import pytest
from core.obsidian.pattern_crystallizer import PatternCrystallizer


@pytest.fixture
def tmp_pc(tmp_path):
    return PatternCrystallizer(vault_path=tmp_path / "vault")


class TestExtractPatterns:
    def test_no_patterns_empty_vault(self, tmp_pc):
        patterns = tmp_pc.extract_patterns(min_occurrences=2)
        assert patterns == []

    def test_detects_recurring_tags(self, tmp_pc, tmp_path):
        vault = tmp_path / "vault"
        writer = tmp_pc.writer
        content = {"cause": "a", "fix": "b", "result": "c", "links": []}
        writer.write_note("failures", "Bug A", content, tags=["state", "reset"])
        writer.write_note("failures", "Bug B", content, tags=["state", "keyerror"])
        patterns = tmp_pc.extract_patterns(min_occurrences=2)
        tag_patterns = [p for p in patterns if p["type"] == "recurring_tag"]
        assert len(tag_patterns) >= 1
        assert any(p["name"] == "state" for p in tag_patterns)


class TestCrystallizePattern:
    def test_crystallize(self, tmp_pc, tmp_path):
        result = tmp_pc.crystallize_pattern(
            name="Test Pattern",
            conditions=["Condition A", "Condition B"],
            result="Achieves X",
            links=["Related"],
        )
        assert result is not None
        assert result["name"] == "Test Pattern"
        assert len(result["conditions"]) == 2


class TestGetCognitivePrimitives:
    def test_get_primitives(self, tmp_pc):
        tmp_pc.crystallize_pattern(
            name="Primitive A",
            conditions=["C1"],
            result="R1",
        )
        primitives = tmp_pc.get_cognitive_primitives()
        assert len(primitives) >= 1


class TestAnalyzeCoOccurrence:
    def test_co_occurrence(self, tmp_pc):
        content = {"cause": "a", "fix": "b", "result": "c", "links": ["LinkA", "LinkB"]}
        tmp_pc.writer.write_note("doctrine", "Note A", content)
        co = tmp_pc.analyze_co_occurrence()
        assert isinstance(co, dict)
