"""
L3.2 — Research task generator.

Converts knowledge gaps into structured research tasks.
Input: knowledge gap (concept missing, edge density low)
Output: structured research task (query, domains, depth limit)

Usage:
    gen = TaskGenerator()
    task = gen.from_gap(gap)
    # Returns ResearchTask ready for queue
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .queue import ResearchTask

logger = logging.getLogger(__name__)


class TaskGenerator:
    """
    Generates research tasks from knowledge gaps.
    
    Maps gap types to specific search queries and domains.
    """

    # Gap type → query template mapping
    QUERY_TEMPLATES: Dict[str, str] = {
        "low_citation_density": "recent advances in {domain} with high impact",
        "missing_concept_links": "{domain} methods and applications",
        "undistilled_papers": "latest research in {domain}",
    }

    # Gap type → priority mapping
    PRIORITY_MAP: Dict[str, int] = {
        "low_citation_density": 4,  # High priority — structural gap
        "missing_concept_links": 3,  # Medium priority
        "undistilled_papers": 2,  # Lower priority — hygiene task
    }

    def from_gap(self, gap: Dict[str, Any]) -> ResearchTask:
        """
        Create a research task from a knowledge gap.
        
        Args:
            gap: Gap dict from GapDetector with type, domain, confidence, etc.
            
        Returns:
            ResearchTask ready to enqueue
        """
        gap_type = gap.get("type", "unknown")
        domain = gap.get("domain", "general")
        confidence = gap.get("confidence", 0.5)
        
        # Build query from template
        template = self.QUERY_TEMPLATES.get(gap_type, "research in {domain}")
        query = template.format(domain=domain.replace("_", " "))
        
        # Determine priority
        priority = self.PRIORITY_MAP.get(gap_type, 3)
        
        # Boost priority for high-confidence gaps
        if confidence > 0.7:
            priority = min(5, priority + 1)
        
        task = ResearchTask(
            query=query,
            domains=[domain],
            priority=priority,
        )
        
        logger.debug(f"Generated task for gap: {gap_type}/{domain} (priority={priority})")
        return task

    def from_gaps(self, gaps: List[Dict[str, Any]], max_tasks: int = 10) -> List[ResearchTask]:
        """
        Create research tasks from multiple gaps.
        
        Args:
            gaps: List of gap dicts from GapDetector
            max_tasks: Maximum number of tasks to generate
            
        Returns:
            List of ResearchTask objects
        """
        tasks = []
        for gap in gaps[:max_tasks]:
            try:
                task = self.from_gap(gap)
                tasks.append(task)
            except Exception as e:
                logger.error(f"Failed to generate task for gap: {e}")
        
        logger.info(f"Generated {len(tasks)} research tasks from {len(gaps)} gaps")
        return tasks

    def from_query(self, query: str, domains: Optional[List[str]] = None, priority: int = 3) -> ResearchTask:
        """
        Create a research task from a manual query.
        
        Args:
            query: Search query string
            domains: Optional list of domains
            priority: Task priority (1-5)
            
        Returns:
            ResearchTask ready to enqueue
        """
        return ResearchTask(
            query=query,
            domains=domains or [],
            priority=priority,
        )