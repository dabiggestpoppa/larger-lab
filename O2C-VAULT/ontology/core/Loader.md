# Loader

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
# Skill Loader - Phase 0E
# Inject relevant doctrine into agent runtime at spawn time
# Loads skills from the skills/ directory and makes them available to agents

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.obsidian.vault_writer import VaultWriter, DEFAULT_VAULT_PATH


# Skill directory structure: skills/<category>/<skill_name>/SKILL.md
SKILL_DIR = Path(__file__).parent.parent.parent / "skills"

# Required files in a skill directory
SKILL_REQUIRED_FILES = ["SKILL.md"]
SKILL_OPTIONAL_FILES = ["heuristics.md", "failures.md", "patterns.md", "examples.md"]

# Keyword map for task classification
KEYWORD_MAP = {
    'chat': ['observer/chat_response'],
    'response': ['observer/chat_response'],
    'reply': ['observer/chat_response'],
    'fix': ['observer/chat_response'],
    'debug': ['observer/chat_response'],
    'test': ['observer/chat_response'],
    'build': ['observer/chat_response'],
    'vault': ['observer/chat_response'],
    'conversation': ['observer/chat_response'],
    'message': ['observer/chat_response'],
    'answer': ['observer/chat_response'],
    'question': ['observer/chat_response'],
}


class SkillLoader:
    """Load and inject skills into agent runtime."""

    def __init__(self, skills_dir: Optional[str] = None):
        self.skills_dir = Path(skills_dir) if skills_dir else SKILL_DIR
        # Skills stored as {category: {name: skill_dict}}
        self._skills: Dict[str, Dict[str, dict]] = {}
        self._scan_skills()

    def _scan_skills(self):
        """Scan skills directory and load all valid skills."""
        self._skills.clear()
        if not self.skills_dir.exists():
            return

        # Structure: skills/<category>/<skill_name>/SKILL.md
        for category_dir in self.skills_dir.iterdir():
            if not category_dir.is_dir():
                continue
            category = category_dir.name
            self._skills[category] = {}

            for skill_dir in category_dir.iterdir():
                if not skill_dir.is_dir():
                    continue

                skill_md = skill_dir / "SKILL.md"
                if not skill_md.exists():
                    continue

                skill = self._load_skill(skill_dir, category)
                if skill:
                    self._skills[category][skill["name"]] = skill

    def _load_skill(self, skill_dir: Path, category: str) -> Optional[dict]:
        """Load a single skill from its directory."""
        try:
            skill_md = skill_dir / "SKILL.md"
            content = skill_md.read_text(encoding="utf-8")

            skill = {
                "name": skill_dir.name,
                "category": category,
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

    def get_skill(self, category: str, skill_name: str) -> Optional[dict]:
        """Get a loaded skill by category and name."""
        return self._skills.get(category, {}).get(skill_name)

    def list_skills(self) -> List[str]:
        """List all loaded skill names (category/name format)."""
        result = []
        for category, skills in self._skills.items():
            for name in skills:
                result.append(f"{category}/{name}")
        return result

    def get_skill_context(self, skill_paths: List[str]) -> str:
        """Get combined context for multiple skills (for injection into agent prompt).

        Args:
            skill_paths: List of 'category/name' strings
        """
        contexts = []
        for path in skill_paths:
            parts = path.split("/", 1)
            if len(parts) == 2:
                category, name = parts
            else:
                category, name = parts[0], parts[0]
            skill = self.get_skill(category, name)
            if skill:
                ctx = f"## Skill: {name}\n\n{skill['content']}"
                if skill.get("heuristics"):
                    ctx += f"\n\n### Heuristics\n\n{skill['heuristics']}"
                if skill.get("failures"):
                    ctx += f"\n\n### Known Failures\n\n{skill['failures']}"
                contexts.append(ctx)
        return "\n\n---\n\n".join(contexts)

    def classify_task(self, task: str) -> list:
        """Classify a task and return relevant skill paths."""
        task_lower = task.lower()
        relevant = []
        for keyword, skill_paths in KEYWORD_MAP.items():
            if keyword in task_lower:
                for sp in skill_paths:
                    if sp not in relevant:
                        relevant.append(sp)
        # Also check skill names directly
        for path in self.list_skills():
            name = path.split("/")[-1]
            if name.lower() in task_lower and path not in relevant:
                relevant.append(path)
        return relevant

    def load_for_task(self, task: str) -> str:
        """Load all relevant skills for a task and generate context injection."""
        relevant_names = self.classify_task(task)
        if not relevant_names:
            return ""
        return self.get_skill_context(relevant_names)

    def get_skill_count(self) -> int:
        """Get total number of loaded skills."""
        return sum(len(skills) for skills in self._skills.values())

    def get_categories(self) -> List[str]:
        """Get list of category names."""
        return list(self._skills.keys())

    def reload(self):
        """Reload all skills from disk."""
        self._skills.clear()
        self._scan_skills()


# Example usage
if __name__ == "__main__":
    loader = SkillLoader()
    print(f"Loaded {loader.get_skill_count()} skills in categories: {loader.get_categories()}")
    for path in loader.list_skills():
        print(f"  - {path}")

```

LINKS:
[[Agents]]
[[Ontology Core Summary]]
[[Citation Workflow]]
[[Examples]]
[[Failures]]
[[Heuristics]]
[[Patterns]]
[[Server]]
[[Skill]]
[[Usage]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
