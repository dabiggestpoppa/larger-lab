"""
Tests for Error Intelligence System — Phase 01 Component 1
"""

import pytest
from core.obsidian.error_intelligence import ErrorIntelligence, ERROR_CATEGORIES, ERROR_PATTERNS


@pytest.fixture
def tmp_ei(tmp_path):
    return ErrorIntelligence(vault_path=tmp_path / "vault")


SAMPLE_KEYERROR = """
Traceback (most recent call last):
  File "trading.py", line 42, in execute_trade
    entry_price = state['price']
KeyError: 'price'
"""

SAMPLE_IMPORTERROR = """
Traceback (most recent call last):
  File "main.py", line 1, in <module>
    from core.semantic.interpret import interpret
ModuleNotFoundError: No module named 'core.semantic.interpret'
"""


class TestClassifyError:
    def test_classify_keyerror(self, tmp_ei):
        category, cause = tmp_ei.classify_error(SAMPLE_KEYERROR)
        assert category == "data_validation"
        assert "key" in cause.lower() or "dictionary" in cause.lower()

    def test_classify_importerror(self, tmp_ei):
        category, cause = tmp_ei.classify_error(SAMPLE_IMPORTERROR)
        assert category == "import_error"

    def test_classify_unknown(self, tmp_ei):
        category, cause = tmp_ei.classify_error("Some random error text")
        assert category == "unknown"

    def test_classify_routing(self, tmp_ei):
        category, cause = tmp_ei.classify_error("routing consensus failed")
        assert category == "routing"


class TestIndexError:
    def test_index_creates_note(self, tmp_ei, tmp_path):
        result = tmp_ei.index_error(
            traceback=SAMPLE_KEYERROR,
            context="Trade execution failed",
            fix_applied="Added key validation",
            result="Trade executes correctly",
        )
        assert result is not None
        assert "error_type" in result
        assert result["error_type"] == "KeyError"
        assert result["category"] == "data_validation"

    def test_index_auto_classifies(self, tmp_ei):
        result = tmp_ei.index_error(traceback=SAMPLE_KEYERROR)
        assert result["category"] == "data_validation"

    def test_index_with_custom_category(self, tmp_ei):
        result = tmp_ei.index_error(
            traceback=SAMPLE_KEYERROR,
            category="execution",
        )
        assert result["category"] == "execution"


class TestFindSimilarErrors:
    def test_find_similar(self, tmp_ei):
        tmp_ei.index_error(SAMPLE_KEYERROR, context="test")
        results = tmp_ei.find_similar_errors("KeyError")
        assert len(results) >= 1

    def test_find_by_tag(self, tmp_ei):
        tmp_ei.index_error(SAMPLE_KEYERROR, context="test")
        results = tmp_ei.find_similar_errors("data_validation")
        assert len(results) >= 1


class TestGetErrorPatterns:
    def test_patterns(self, tmp_ei):
        tmp_ei.index_error(SAMPLE_KEYERROR, context="test")
        tmp_ei.index_error(SAMPLE_IMPORTERROR, context="test")
        patterns = tmp_ei.get_error_patterns()
        assert patterns["total_errors"] >= 2
        assert "by_category" in patterns
        assert "by_type" in patterns


class TestGetPreventionRules:
    def test_prevention_rules(self, tmp_ei):
        tmp_ei.index_error(SAMPLE_KEYERROR, context="test", fix_applied="Validate keys")
        rules = tmp_ei.get_prevention_rules()
        assert len(rules) >= 1


class TestErrorCategories:
    def test_all_categories_valid(self):
        assert "routing" in ERROR_CATEGORIES
        assert "memory" in ERROR_CATEGORIES
        assert "execution" in ERROR_CATEGORIES
        assert "import_error" in ERROR_CATEGORIES

    def test_error_patterns_complete(self):
        assert "KeyError" in ERROR_PATTERNS
        assert "ImportError" in ERROR_PATTERNS
        assert "ModuleNotFoundError" in ERROR_PATTERNS
