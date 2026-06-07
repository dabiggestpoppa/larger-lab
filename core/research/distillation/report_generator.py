"""
L2.7 — Research Report Generator.

Synthesizes distilled papers into comprehensive research reports (PDF output).
Uses LLM to generate full academic-style reports with citations, analysis, and conclusions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..ingestion.models import Paper

logger = logging.getLogger(__name__)


REPORT_PROMPT = """You are a research analyst generating a comprehensive academic report.

Topic: {topic}
Papers analyzed: {paper_count}

Distilled paper notes:
{notes}

Generate a formal research report with:
1. Executive Summary (2-3 paragraphs)
2. Introduction (problem statement, significance, objectives)
3. Literature Review (synthesizing the papers, key themes, gaps)
4. Methodology (how the research was conducted)
5. Findings (key insights from each paper, quantitative results)
6. Discussion (implications, contradictions, future directions)
7. Conclusion (summary, recommendations)
8. References (formatted citations)

Write in academic style, 1500-2000 words. Include specific numbers, methods, and citations.
Use markdown format with proper headers (#, ##, ###)."""


class ReportGenerator:
    """
    Generates comprehensive research reports from distilled papers.
    
    Uses LLM to synthesize multiple paper notes into a single coherent report.
    Outputs PDF via reportlab.
    """

    def __init__(self, llm_client=None, model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"):
        self.llm = llm_client
        self.model = model

    async def generate_report(
        self,
        topic: str,
        papers: list[Paper],
        notes: list[str],
        output_path: Optional[Path] = None,
    ) -> Optional[str]:
        """
        Generate a comprehensive research report.
        
        Args:
            topic: Research topic
            papers: List of Paper objects
            notes: List of distilled notes (markdown strings)
            output_path: Where to write PDF (defaults to vault/reports/)
            
        Returns:
            Path to generated PDF or None on failure
        """
        if not notes:
            logger.warning("No notes provided for report generation")
            return None

        # Build prompt
        notes_text = "\n\n---\n\n".join(notes[:10])  # Limit to 10 papers
        prompt = REPORT_PROMPT.format(
            topic=topic,
            paper_count=len(notes),
            notes=notes_text,
        )

        try:
            # Use OpenRouterGateway if no LLM client
            if not self.llm:
                from core.spawn.openrouter_gateway import OpenRouterGateway
                gateway = OpenRouterGateway()
                report_md = await gateway.complete(prompt, model=self.model)
            else:
                report_md = await self.llm.complete(prompt=prompt, model=self.model)

            if not report_md:
                return None

            # Convert to PDF
            return self._markdown_to_pdf(report_md, topic, output_path)

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return None

    def _markdown_to_pdf(self, markdown: str, topic: str, output_path: Optional[Path] = None) -> str:
        """Convert markdown to PDF using reportlab."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import inch

        # Default output path
        if not output_path:
            vault_root = Path(r"C:\Users\wifik\Downloads\o2c\research")
            output_path = vault_root / "reports" / f"{topic.lower().replace(' ', '_')}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create PDF
        doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        story = []

        # Parse markdown headers
        for line in markdown.split('\n'):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 12))
                continue

            if line.startswith('# '):
                story.append(Paragraph(line[2:], styles['Title']))
            elif line.startswith('## '):
                story.append(Paragraph(line[3:], styles['Heading1']))
            elif line.startswith('### '):
                story.append(Paragraph(line[4:], styles['Heading2']))
            else:
                story.append(Paragraph(line, styles['Normal']))

        doc.build(story)
        logger.info(f"Report generated: {output_path}")
        return str(output_path)


async def generate_research_report(topic: str, paper_ids: list[str]) -> str:
    """
    Convenience function to generate report from paper IDs.
    
    Args:
        topic: Research topic
        paper_ids: List of paper IDs to include
        
    Returns:
        Path to PDF report
    """
    from core.research.ingestion.cache import Cache
    from core.research.distillation.llm_distill import LLMDistiller
    from core.research.distillation.vault_writer import VaultWriter

    cache = Cache()
    distiller = LLMDistiller()
    writer = VaultWriter()
    generator = ReportGenerator()

    # Load papers and distill
    papers = []
    notes = []
    for pid in paper_ids[:10]:
        paper = cache.get_paper(pid)
        if paper:
            papers.append(paper)
            note = await distiller.distill(paper)
            if note:
                notes.append(note)

    # Generate report
    return await generator.generate_report(topic, papers, notes)