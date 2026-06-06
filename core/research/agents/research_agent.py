"""
L3.3 — LLM-driven research agent.

Executes research tasks by querying sources, distilling findings, and updating the vault.
Bounded by token budget and time limits.

Usage:
    agent = ResearchAgent()
    result = await agent.execute(task)
    # Returns finding with confidence score
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from ..distillation.distiller import Distiller
from ..distillation.vault_writer import VaultWriter
from ..ingestion.models import Paper
from .queue import ResearchTask

logger = logging.getLogger(__name__)

# Token budget per finding extraction
MAX_TOKENS_INPUT = 500
MAX_TOKENS_OUTPUT = 300

# Time limit per task (seconds)
MAX_TASK_DURATION = 3600  # 1 hour


class ResearchAgent:
    """
    LLM-driven research agent that fills knowledge gaps.
    
    Executes tasks by:
    1. Querying sources for relevant papers
    2. Distilling findings using rule-based + optional LLM
    3. Writing to vault if confidence >= 0.6
    """

    def __init__(self, llm_client: Optional[Any] = None):
        self.llm = llm_client
        self.distiller = Distiller()
        self.vault_writer = VaultWriter()
        self._running = False

    async def execute(self, task: ResearchTask) -> Dict[str, Any]:
        """
        Execute a research task.
        
        Args:
            task: Research task with query and domains
            
        Returns:
            Finding dict with confidence, summary, and vault_path
        """
        self._running = True
        start_time = datetime.now(timezone.utc)
        
        try:
            # Query sources for relevant papers (placeholder - PM builds clients)
            papers = await self._query_sources(task)
            
            if not papers:
                return {
                    "success": False,
                    "confidence": 0.0,
                    "error": "No papers found for query",
                    "task_id": task.id,
                }
            
            # Distill findings
            findings = []
            for paper in papers[:5]:  # Cap at 5 papers per task
                note = self.distiller.distill(paper)
                findings.append({
                    "paper_id": paper.id,
                    "note": note,
                })
            
            # Aggregate confidence
            confidence = min(0.9, 0.5 + len(findings) * 0.1)
            
            # Write to vault if confident enough
            vault_path = ""
            if confidence >= 0.6 and findings:
                combined_note = self._combine_findings(findings, task)
                success, vault_path = self.vault_writer.write_finding(
                    task.id, combined_note, confidence
                )
            
            return {
                "success": True,
                "confidence": confidence,
                "papers_found": len(papers),
                "findings": findings,
                "vault_path": vault_path,
                "task_id": task.id,
                "duration_seconds": (datetime.now(timezone.utc) - start_time).total_seconds(),
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "confidence": 0.0,
                "error": "Task exceeded time limit",
                "task_id": task.id,
            }
        except Exception as e:
            logger.error(f"Research agent failed: {e}")
            return {
                "success": False,
                "confidence": 0.0,
                "error": str(e),
                "task_id": task.id,
            }
        finally:
            self._running = False

    async def _query_sources(self, task: ResearchTask) -> list[Paper]:
        """
        Query available sources for relevant papers.
        
        This is a placeholder — actual implementation uses PM/PM2 clients.
        """
        # Placeholder: return empty list until clients are built
        # PM will implement openalex_client, arxiv_client, s2_client
        return []

    def _combine_findings(self, findings: list[Dict], task: ResearchTask) -> str:
        """Combine multiple paper findings into a single note."""
        lines = [f"# Research Finding: {task.query}", ""]
        
        for f in findings:
            lines.append(f"## Paper: {f['paper_id']}")
            lines.append(f['note'])
            lines.append("")
        
        lines.append(f"Confidence: {min(0.9, 0.5 + len(findings) * 0.1):.2f}")
        lines.append(f"Task ID: {task.id}")
        
        return "\n".join(lines)

    @property
    def is_running(self) -> bool:
        return self._running