"""
Tests for Note Standard — Phase 0I
"""

import pytest
from core.obsidian.note_standard import NoteValidator, format_note


class TestValidate:
    def test_valid_full_note(self):
        content = """# Test Note

CAUSE:
Something broke

FIX:
Applied fix

RESULT:
Working now

LINKS:
[[Related]]
"""
        v = NoteValidator(strict=False)
        result = v.validate(content)
        assert result["valid"] is True
        assert result["score"] >= 0.6
        assert result["has_cause"] is True
        assert result["has_fix"] is True
        assert result["has_result"] is True
        assert result["has_links"] is True
        assert result["has_title"] is True

    def test_missing_title(self):
        content = """CAUSE:
Something broke

FIX:
Fix applied

RESULT:
Done
"""
        v = NoteValidator()
        result = v.validate(content)
        assert result["has_title"] is False
        assert result["valid"] is False

    def test_missing_cause(self):
        content = """# No Cause Note

FIX:
Some fix

RESULT:
Done
"""
        v = NoteValidator()
        result = v.validate(content)
        assert result["has_cause"] is False
        assert result["valid"] is False

    def test_ai_sludge_detected(self):
        content = """# Sludge Note

CAUSE:
I apologize for the confusion. As an AI, I need to explain...

FIX:
Great question! Let me explain...

RESULT:

LINKS:
"""
        v = NoteValidator()
        result = v.validate(content)
        sludge_issues = [i for i in result["issues"] if "sludge" in i.lower()]
        assert len(sludge_issues) > 0

    def test_strict_mode_requires_fix_and_result(self):
        content = """# Strict Note

CAUSE:
Something broke

RESULT:
Done
"""
        v_strict = NoteValidator(strict=True)
        v_loose = NoteValidator(strict=False)
        strict_result = v_strict.validate(content)
        loose_result = v_loose.validate(content)
        # Strict should have more issues
        assert len(strict_result["issues"]) >= len(loose_result["issues"])

    def test_empty_note(self):
        content = ""
        v = NoteValidator()
        result = v.validate(content)
        assert result["valid"] is False
        assert result["score"] == 0.0

    def test_score_range(self):
        content = """# Good Note

CAUSE:
Clear cause

FIX:
Clear fix

RESULT:

LINKS:
[[Link1]]
"""
        v = NoteValidator()
        result = v.validate(content)
        assert 0.0 <= result["score"] <= 1.0


class TestFormatNote:
    def test_format_basic(self):
        result = format_note(
            title="Test Bug",
            cause="Something broke",
            fix="Applied patch",
            result="Working",
            links=["Bug Pattern"],
        )
        assert "# Test Bug" in result
        assert "CAUSE:" in result
        assert "Something broke" in result
        assert "FIX:" in result
        assert "Applied patch" in result
        assert "RESULT:" in result
        assert "Working" in result
        assert "[[Bug Pattern]]" in result

    def test_format_no_links(self):
        result = format_note(
            title="No Links",
            cause="Cause",
            fix="Fix",
            result="Result",
        )
        assert "LINKS:" not in result


class TestValidateFile:
    def test_validate_existing_file(self, tmp_path):
        note_file = tmp_path / "test.md"
        note_file.write_text("""# File Note

CAUSE:
File cause

FIX:
File fix

RESULT:
File result

LINKS:
[[FileLink]]
""", encoding="utf-8")
        v = NoteValidator()
        result = v.validate_file(note_file)
        assert result["valid"] is True
        assert "file" in result

    def test_validate_nonexistent_file(self, tmp_path):
        v = NoteValidator()
        result = v.validate_file(tmp_path / "nonexistent.md")
        assert result["valid"] is False
        assert "not found" in result["issues"][0].lower()
