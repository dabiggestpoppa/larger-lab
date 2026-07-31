"""
Tests for Skill Loader — Phase 0E
"""

import pytest
from pathlib import Path
from core.skills.loader import SkillLoader


@pytest.fixture
def tmp_skills(tmp_path):
    """Create a temp skills directory with a sample skill."""
    skill_dir = tmp_path / "skills" / "observer" / "chat_response"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# Chat Response Skill\n\nGenerate dynamic responses.", encoding="utf-8"
    )
    (skill_dir / "heuristics.md").write_text(
        "# Heuristics\n\nVary phrasing.", encoding="utf-8"
    )
    (skill_dir / "failures.md").write_text(
        "# Failures\n\nStatic template response.", encoding="utf-8"
    )
    return tmp_path / "skills"


class TestSkillLoader:
    def test_loads_skills(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        skills = loader.list_skills()
        assert len(skills) >= 1

    def test_get_skill(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        skill = loader.get_skill("observer", "chat_response")
        assert skill is not None
        assert skill["name"] == "chat_response"

    def test_get_skill_context(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        context = loader.get_skill_context(["observer/chat_response"])
        assert "Chat Response Skill" in context
        assert "Heuristics" in context
        assert "Known Failures" in context

    def test_classify_task(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        relevant = loader.classify_task("Fix the chat response bug")
        assert len(relevant) >= 1

    def test_load_for_task(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        context = loader.load_for_task("Fix the chat response")
        assert "Chat Response" in context or "chat_response" in context

    def test_load_for_irrelevant_task(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        context = loader.load_for_task("Something completely unrelated xyz123")
        # Should return empty or minimal context
        assert isinstance(context, str)

    def test_skill_count(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        assert loader.get_skill_count() >= 1

    def test_categories(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        cats = loader.get_categories()
        assert "observer" in cats
