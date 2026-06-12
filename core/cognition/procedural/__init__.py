"""
Phase 1.6 — Procedural Cognition

Reusable cognition workflows, operational patterns, execution memory.
Turns documents/skills into executable agent procedures.

Components:
- skill_loader: loads SKILL.md files from skills directory
- workflow_engine: executes cognition chains
- context_injection: injects relevant context into agent sessions
- router: routes tasks to appropriate skills (SkillTree pattern)
"""

from .skill_loader import SkillLoader
from .workflow_engine import WorkflowEngine
from .router import CognitionRouter

__all__ = ["SkillLoader", "WorkflowEngine", "CognitionRouter"]
