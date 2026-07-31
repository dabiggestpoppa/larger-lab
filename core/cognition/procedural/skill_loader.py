"""
Phase 1.6 — Skill Loader

Loads SKILL.md files from the skills directory.
Follows the open Agent Skills standard.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class Skill:
    """A loaded skill definition."""
    name: str
    description: str
    file_path: str
    content: str
    triggers: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    apply_to: list[str] = field(default_factory=list)  # glob patterns
    
    @property
    def token_count(self) -> int:
        """Approximate token count."""
        return len(self.content) // 4


class SkillLoader:
    """
    Loads and manages skills from the skills directory.
    
    Skills can come from:
    - Local skills/ directory
    - mattpocock/skills (engineering best practices)
    - book-to-skill generated skills (from documents)
    - Custom agent skills
    """
    
    def __init__(self, skills_dirs: list[str] = None):
        self.skills_dirs = skills_dirs or [
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "skills"),
            os.path.join(os.path.dirname(__file__), "book-to-skill"),
        ]
        self._skills: dict[str, Skill] = {}
    
    def load_all(self) -> dict[str, Skill]:
        """Load all skills from all skill directories."""
        for skills_dir in self.skills_dirs:
            if os.path.isdir(skills_dir):
                self._load_directory(skills_dir)
        return self._skills
    
    def _load_directory(self, directory: str):
        """Load all SKILL.md files from a directory."""
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename == "SKILL.md":
                    file_path = os.path.join(root, filename)
                    skill = self._parse_skill(file_path)
                    if skill:
                        self._skills[skill.name] = skill
    
    def _parse_skill(self, file_path: str) -> Optional[Skill]:
        """Parse a SKILL.md file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (IOError, UnicodeDecodeError):
            return None
        
        # Extract YAML frontmatter
        name = os.path.basename(os.path.dirname(file_path))
        description = ""
        triggers = []
        tools = []
        apply_to = []
        
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                frontmatter = content[3:end]
                content_body = content[end + 3:].strip()
                
                # Parse frontmatter fields
                for line in frontmatter.split("\n"):
                    line = line.strip()
                    if line.startswith("name:"):
                        name = line.split(":", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("description:"):
                        description = line.split(":", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("triggers:"):
                        triggers_str = line.split(":", 1)[1].strip()
                        triggers = [t.strip() for t in triggers_str.split(",") if t.strip()]
                    elif line.startswith("tools:"):
                        tools_str = line.split(":", 1)[1].strip()
                        tools = [t.strip() for t in tools_str.split(",") if t.strip()]
                    elif line.startswith("applyTo:"):
                        apply_str = line.split(":", 1)[1].strip()
                        apply_to = [a.strip() for a in apply_str.split(",") if a.strip()]
            else:
                content_body = content
        else:
            content_body = content
        
        # Extract description from first paragraph if not in frontmatter
        if not description:
            for line in content_body.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    description = line[:200]
                    break
        
        return Skill(
            name=name,
            description=description,
            file_path=file_path,
            content=content,
            triggers=triggers,
            tools=tools,
            apply_to=apply_to,
        )
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self._skills.get(name)
    
    def find_skills_for_task(self, task_description: str) -> list[Skill]:
        """Find relevant skills for a task description."""
        task_lower = task_description.lower()
        matches = []
        
        for skill in self._skills.values():
            # Check triggers
            for trigger in skill.triggers:
                if trigger.lower() in task_lower:
                    matches.append(skill)
                    break
            else:
                # Check name/description
                if skill.name.lower() in task_lower:
                    matches.append(skill)
                elif skill.description and skill.description.lower()[:50] in task_lower:
                    matches.append(skill)
        
        return matches
    
    def list_skills(self) -> list[dict]:
        """List all loaded skills."""
        return [
            {
                "name": s.name,
                "description": s.description[:100],
                "file_path": s.file_path,
                "token_count": s.token_count,
            }
            for s in self._skills.values()
        ]
