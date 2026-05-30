"""
Tests for Compressor — Phase 0B
"""

import pytest
from core.obsidian.compressor import compress_trace, extract_signal, is_noise, filter_noise


SAMPLE_TRACEBACK = """
Traceback (most recent call last):
  File "trading.py", line 42, in execute_trade
    entry_price = get_entry()
  File "trading.py", line 15, in get_entry
    return state['price']
KeyError: 'price'
During handling of the above exception, another exception occurred:
Traceback (most recent call last):
  File "main.py", line 10, in <module>
    run_trader()
KeyError: 'price'
"""


class TestCompressTrace:
    def test_basic_compression(self):
        result = compress_trace(
            traceback=SAMPLE_TRACEBACK,
            context="Trade execution failed during entry",
            fix_applied="Added price validation before entry",
            result="Trade executes correctly with validation",
        )
        assert "CAUSE:" in result
        assert "Trade execution failed during entry" in result
        assert "KeyError: 'price'" in result
        assert "FIX:" in result
        assert "Added price validation before entry" in result
        assert "RESULT:" in result
        assert "Trade executes correctly with validation" in result

    def test_extracts_error_links(self):
        result = compress_trace(
            traceback=SAMPLE_TRACEBACK,
            context="Test",
            fix_applied="Fix",
            result="Done",
        )
        assert "[[KeyError]]" in result

    def test_no_fix_provided(self):
        result = compress_trace(
            traceback=SAMPLE_TRACEBACK,
            context="Test",
        )
        assert "Pending verification" in result

    def test_fix_attempts_fallback(self):
        result = compress_trace(
            traceback=SAMPLE_TRACEBACK,
            context="Test",
            fix_attempts=["tried A", "tried B", "tried C"],
        )
        assert "tried C" in result  # Last attempt

    def test_deduplicates_signals(self):
        result = compress_trace(
            traceback="KeyError: 'x'\nKeyError: 'x'\nKeyError: 'x'",
            context="Test",
            fix_applied="Fix",
            result="Done",
        )
        # Should only appear once
        assert result.count("KeyError: 'x'") == 1


class TestExtractSignal:
    def test_extract_labeled_sections(self):
        text = """CAUSE:
Something broke
FIX:
Applied fix
RESULT:
Working now
LINKS:
[[ErrorType]]
"""
        result = extract_signal(text)
        assert result["cause"] == "Something broke"
        assert result["fix"] == "Applied fix"
        assert result["result"] == "Working now"
        assert "ErrorType" in result["links"]

    def test_empty_input(self):
        result = extract_signal("")
        assert result["cause"] == ""
        assert result["links"] == []


class TestIsNoise:
    def test_traceback_header(self):
        assert is_noise("Traceback (most recent call last):") is True

    def test_file_line(self):
        assert is_noise('  File "test.py", line 10, in func') is True

    def test_signal_line(self):
        assert is_noise("KeyError: 'price'") is False

    def test_empty_line(self):
        assert is_noise("   ") is True


class TestFilterNoise:
    def test_removes_noise(self):
        lines = [
            "Traceback (most recent call last):",
            "KeyError: 'price'",
            "",
            "FIX: applied patch",
        ]
        result = filter_noise(lines)
        assert "KeyError: 'price'" in result
        assert "FIX: applied patch" in result
        assert "Traceback" not in "\n".join(result)
