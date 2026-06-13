"""
Phase 1.5 — Research Report Generator

Generates structured research reports from synthesis results.
Outputs: Markdown, JSON, or HTML.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.report")


class ResearchReportGenerator:
    """
    Generates structured research reports from synthesis results.
    
    Usage:
        generator = ResearchReportGenerator()
        report = generator.generate(synthesis_result, format="markdown")
    """

    def generate(
        self,
        synthesis_result: Any,
        format: str = "markdown",
    ) -> str:
        """Generate a report from synthesis results."""
        if format == "markdown":
            return self._generate_markdown(synthesis_result)
        elif format == "json":
            return self._generate_json(synthesis_result)
        elif format == "html":
            return self._generate_html(synthesis_result)
        else:
            return self._generate_markdown(synthesis_result)

    def _generate_markdown(self, result: Any) -> str:
        """Generate Markdown report."""
        lines = []

        # Title
        lines.append(f"# Research Report")
        lines.append(f"")
        lines.append(f"**Query:** {result.query}")
        lines.append(f"**Sources:** {result.source_count}")
        lines.append(f"**Confidence:** {result.confidence:.0%}")
        lines.append(f"")

        # Executive Summary
        lines.append(f"## Executive Summary")
        lines.append(f"")
        lines.append(result.executive_summary)
        lines.append(f"")

        # Key Findings
        lines.append(f"## Key Findings")
        lines.append(f"")
        for i, finding in enumerate(result.key_findings, 1):
            confidence_label = "🟢" if finding.confidence > 0.7 else "🟡" if finding.confidence > 0.5 else "🔴"
            lines.append(f"{i}. {confidence_label} {finding.text}")
            if finding.supporting_sources:
                lines.append(f"   *Sources: {', '.join(finding.supporting_sources[:3])}*")
            lines.append(f"")

        # Contradictions
        if result.contradictions:
            lines.append(f"## Contradictions")
            lines.append(f"")
            for i, contr in enumerate(result.contradictions, 1):
                severity_emoji = "🔴" if contr.get("severity") == "high" else "🟡" if contr.get("severity") == "medium" else "⚪"
                lines.append(f"{i}. {severity_emoji} **{contr.get('severity', 'unknown').upper()}**")
                lines.append(f"   - Claim A: {contr.get('claim_a', '')[:100]}")
                lines.append(f"   - Claim B: {contr.get('claim_b', '')[:100]}")
                lines.append(f"")

        # Knowledge Gaps
        if result.gaps:
            lines.append(f"## Knowledge Gaps")
            lines.append(f"")
            for gap in result.gaps:
                lines.append(f"- ⚠️ {gap}")
            lines.append(f"")

        # Citations
        if result.citations:
            lines.append(f"## References")
            lines.append(f"")
            for i, citation in enumerate(result.citations, 1):
                title = citation.get("title", "Untitled")
                authors = citation.get("authors", "")
                year = citation.get("year", "")
                doi = citation.get("doi", "")
                lines.append(f"{i}. {authors} ({year}). {title}.")
                if doi:
                    lines.append(f"   DOI: https://doi.org/{doi}")
                lines.append(f"")

        return "\n".join(lines)

    def _generate_json(self, result: Any) -> str:
        """Generate JSON report."""
        data = {
            "query": result.query,
            "source_count": result.source_count,
            "confidence": result.confidence,
            "executive_summary": result.executive_summary,
            "key_findings": [
                {
                    "text": f.text,
                    "confidence": f.confidence,
                    "sources": f.supporting_sources,
                }
                for f in result.key_findings
            ],
            "contradictions": result.contradictions,
            "gaps": result.gaps,
            "citations": result.citations,
        }
        return json.dumps(data, indent=2, default=str)

    def _generate_html(self, result: Any) -> str:
        """Generate HTML report."""
        md = self._generate_markdown(result)
        # Simple Markdown → HTML conversion
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Research Report</title>
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #1a1a2e; }}
        h2 {{ color: #333; border-bottom: 1px solid #ddd; }}
        .finding {{ margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 4px; }}
        .contradiction {{ margin: 10px 0; padding: 10px; background: #fff3cd; border-radius: 4px; }}
        .gap {{ color: #856404; }}
        .meta {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>Research Report</h1>
    <p class="meta">Query: {result.query}</p>
    <p class="meta">Sources: {result.source_count} | Confidence: {result.confidence:.0%}</p>
    <h2>Executive Summary</h2>
    <p>{result.executive_summary}</p>
    <h2>Key Findings</h2>
"""
        for i, finding in enumerate(result.key_findings, 1):
            html += f'    <div class="finding">{i}. {finding.text} <span class="meta">({finding.confidence:.0%})</span></div>\n'

        if result.contradictions:
            html += "    <h2>Contradictions</h2>\n"
            for contr in result.contradictions:
                html += f'    <div class="contradiction">{contr.get("severity", "")}: {contr.get("claim_a", "")[:100]}</div>\n'

        html += "</body></html>"
        return html
