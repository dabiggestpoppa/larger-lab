# Skill Loader - Phase 0E
# Inject relevant doctrine into agent runtime at spawn time
# Loads skills from the skills/ directory and makes them available to agents

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.obsidian.vault_writer import VaultWriter, DEFAULT_VAULT_PATH


# Skill directory structure
SKILL_DIR = Path(__file__).parent.parent.parent / "skills"

# Required files in a skill directory
SKILL_REQUIRED_FILES = ["SKILL.md"]
SKILL_OPTIONAL_FILES = ["heuristics.md", "failures.md", "patterns.md", "examples.md"]


class SkillLoader:
    """Load and inject skills into agent runtime."""
    
    def __init__(self, skills_dir: Optional[str] = None):
        self.skills_dir = Path(skills_dir) if skills_dir else SKILL_DIR
        self.loaded_skills: Dict[str, dict] = {}
        self._scan_skills()
    
    def _scan_skills(self):
        """Scan skills directory and load all valid skills."""
        if not self.skills_dir.exists():
            return
        
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            
            skill = self._load_skill(skill_dir)
            if skill:
                self.loaded_skills[skill["name"]] = skill
    
    def _load_skill(self, skill_dir: Path) -> Optional[dict]:
        """Load a single skill from its directory."""
        try:
            skill_md = skill_dir / "SKILL.md"
            content = skill_md.read_text(encoding="utf-8")
            
            skill = {
                "name": skill_dir.name,
                "path": str(skill_dir),
                "content": content,
                "heuristics": "",
                "failures": "",
                "patterns": "",
                "examples": "",
            }
            
            # Load optional files
            for fname, key in [
                ("heuristics.md", "heuristics"),
                ("failures.md", "failures"),
                ("patterns.md", "patterns"),
                ("examples.md", "examples"),
            ]:
                fpath = skill_dir / fname
                if fpath.exists():
                    skill[key] = fpath.read_text(encoding="utf-8")
            
            return skill
        except Exception as e:
            print(f"Failed to load skill {skill_dir.name}: {e}")
            return None
    
    def get_skill(self, skill_name: str) -> Optional[dict]:
        """Get a loaded skill by name."""
        return self.loaded_skills.get(skill_name)
    
    def list_skills(self) -> List[str]:
        """List all loaded skill names."""
        return list(self.loaded_skills.keys())
    
    def get_skill_context(self, skill_names: List[str]) -> str:
        """Get combined context for multiple skills (for injection into agent prompt)."""
        contexts = []
        for name in skill_names:
            skill = self.loaded_skills.get(name)
            if skill:
                ctx = f"## Skill: {name}\n\n{skill['content']}"
                if skill.get("heuristics"):
                    ctx += f"\n\n### Heuristics\n\n{skill['heuristics']}"
                if skill.get("failures"):
                    ctx += f"\n\n### Known Failures\n\n{skill['failures']}"
                contexts.append(ctx)
        return "\n\n---\n\n".join(contexts)
    
    def reload(self):
        """Reload all skills from disk."""
        self.loaded_skills.clear()
        self._scan_skills()


# Example usage
if __name__ == "__main__":
    loader = SkillLoader()
    skills = loader.list_skills()
    print(f"Loaded {len(skills)} skills: {skills}")

    def classify_task(self, task: str) -> list:
        '''Classify a task and return relevant skill names.'''
        task_lower = task.lower()
        relevant = []
        keyword_map = {
            'chat': ['chat_response'], 'response': ['chat_response'],
            'reply': ['chat_response'], 'fix': ['chat_response'],
            'debug': ['chat_response'], 'test': ['chat_response'],
            'build': ['chat_response'], 'vault': ['chat_response'],
        }
        for keyword, skill_names in keyword_map.items():
            if keyword in task_lower:
                relevant.extend(skill_names)
        for skill_name in self.loaded_skills:
            if skill_name.lower() in task_lower and skill_name not in relevant:
                relevant.append(skill_name)
        return relevant

    def load_for_task(self, task: str) -> str:
        '''Load all relevant skills for a task and generate context injection.'''
        relevant_names = self.classify_task(task)
        if not relevant_names:
            return ''
        return self.get_skill_context(relevant_names)
