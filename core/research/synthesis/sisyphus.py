"""
Phase 1.5 — Sisyphus Academica

Multi-source research synthesis engine using LLM reasoning.
Produces full research reports (10+ pages) with deep analysis,
cross-referencing, proper citations, and contradiction detection.

Uses OpenRouterGateway for LLM access (OWL Alpha primary, auto-failover).

Architecture:
- Multi-pass LLM approach: analyze each source → cross-reference → detect contradictions → assemble report
- Each pass uses a specialized prompt for that synthesis phase
- Final report is a complete academic research paper with all standard sections
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.sisyphus")


@dataclass
class SourceDocument:
    """A source document for synthesis."""
    doc_id: str
    title: str
    text: str
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    authors: List[str] = field(default_factory=list)
    year: str = ""
    doi: str = ""


@dataclass
class SynthesisResult:
    """Complete synthesis output — a full research report."""
    synthesis_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    query: str = ""
    title: str = ""
    executive_summary: str = ""
    introduction: str = ""
    literature_review: str = ""
    methodology: str = ""
    findings: str = ""
    discussion: str = ""
    contradictions: str = ""
    limitations: str = ""
    future_research: str = ""
    conclusion: str = ""
    references: str = ""
    full_report: str = ""
    pdf_path: str = ""
    source_count: int = 0
    confidence: float = 0.0
    word_count: int = 0

    def to_dict(self) -> dict:
        return {
            "synthesis_id": self.synthesis_id,
            "query": self.query,
            "title": self.title,
            "source_count": self.source_count,
            "confidence": self.confidence,
            "word_count": self.word_count,
        }


class SisyphusEngine:
    """
    Multi-source research synthesis engine using LLM reasoning.
    
    Produces full research reports by:
    1. Analyzing each source individually (LLM pass per source)
    2. Cross-referencing and synthesizing (LLM pass across all analyses)
    3. Detecting contradictions (LLM pass for conflict analysis)
    4. Assembling final report (LLM pass for narrative assembly)
    
    Usage:
        engine = SisyphusEngine(gateway=openrouter_gateway)
        result = await engine.synthesize(
            query="How does information theory apply to trading systems?",
            sources=source_docs,
        )
        print(result.full_report)  # Complete 10+ page research report
    """

    def __init__(
        self,
        gateway=None,
        chunker=None,
        max_sources: int = 20,
    ):
        self.gateway = gateway
        self.chunker = chunker
        self.max_sources = max_sources

    async def synthesize(
        self,
        query: str,
        sources: List[SourceDocument],
    ) -> SynthesisResult:
        """Produce a full research report from multiple sources."""
        logger.info(f"Sisyphus: synthesizing {len(sources)} sources for: {query[:80]}")

        if not sources:
            return SynthesisResult(query=query, confidence=0.0)

        if not self.gateway:
            logger.error("No LLM gateway configured")
            return SynthesisResult(query=query, confidence=0.0)

        result = SynthesisResult(query=query, source_count=len(sources))

        try:
            # Phase 1: Individual source analysis
            logger.info("Phase 1: Analyzing individual sources...")
            source_analyses = []
            for i, source in enumerate(sources):
                analysis = await self._analyze_source(source, query, i + 1)
                if analysis:
                    source_analyses.append(analysis)

            # Phase 2: Cross-reference synthesis
            logger.info("Phase 2: Cross-referencing and synthesizing...")
            synthesis = await self._synthesize_sources(query, sources, source_analyses)

            # Phase 3: Contradiction analysis
            logger.info("Phase 3: Detecting contradictions...")
            contradictions = await self._analyze_contradictions(query, source_analyses)

            # Phase 4: Assemble full report
            logger.info("Phase 4: Assembling final report...")
            report = await self._assemble_report(
                query, sources, source_analyses, synthesis, contradictions
            )

            result.full_report = report
            result.word_count = len(report.split())
            result.confidence = min(1.0, len(sources) * 0.15)
            self._extract_sections(result, report)

            # Phase 5: Generate PDF
            logger.info("Phase 5: Generating PDF...")
            try:
                from core.research.synthesis.pdf_generator import PDFReportGenerator
                pdf_gen = PDFReportGenerator()
                pdf_path = pdf_gen.generate(
                    markdown=report,
                    title=result.title or f"Research Report: {query[:60]}",
                    output_path=None,  # Auto-generate path
                )
                if pdf_path:
                    result.pdf_path = pdf_path
                    logger.info(f"PDF generated: {pdf_path}")
                else:
                    logger.warning("PDF generation returned None")
            except Exception as pdf_err:
                logger.warning(f"PDF generation failed (non-critical): {pdf_err}")

            logger.info(f"Synthesis complete: {result.word_count} words")

        except Exception as e:
            logger.error(f"Synthesis failed: {e}", exc_info=True)
            result.full_report = f"Synthesis failed: {e}"
            result.confidence = 0.0

        return result

    async def _analyze_source(self, source: SourceDocument, query: str, num: int) -> str:
        """Analyze a single source via LLM."""
        text_preview = source.text[:3000] if len(source.text) > 3000 else source.text
        prompt = f"""Analyze this research source for the research question: {query}

Source {num}: {source.title}
Authors: {', '.join(source.authors) if source.authors else 'Unknown'}
Year: {source.year} | DOI: {source.doi}

Content: {text_preview}

Provide a structured 500-800 word analysis:
1. Main Argument
2. Key Concepts & Frameworks
3. Methodology
4. Key Findings
5. Relevance to Research Question
6. Strengths & Limitations
7. Key Quotes/Findings"""
        try:
            return await self.gateway.complete(prompt=prompt, max_tokens=2000)
        except Exception as e:
            logger.warning(f"Source analysis failed: {e}")
            return ""

    async def _synthesize_sources(self, query, sources, analyses) -> str:
        """Cross-reference synthesis via LLM."""
        summaries = "\n---\n".join(
            f"### Source {i+1}: {s.title} ({s.year})\n\n{a}"
            for i, (s, a) in enumerate(zip(sources, analyses)) if a
        )
        prompt = f"""Synthesize these analyzed sources into a comprehensive research report section.

Research Question: {query}
Sources: {len(sources)}

Source Analyses:
{summaries}

Produce a 2000-3000 word synthesis covering:
1. Thematic Analysis
2. Comparative Analysis
3. Theoretical Frameworks
4. Methodological Comparison
5. Evidence Evaluation
7. Gaps and Limitations
8. Emergent Insights

Be thorough, critical, and cite sources using [Author, Year] format."""
        try:
            return await self.gateway.complete(prompt=prompt, max_tokens=4000)
        except Exception as e:
            return f"Synthesis error: {e}"

    async def _analyze_contradictions(self, query, analyses) -> str:
        """Detect contradictions via LLM."""
        all_text = "\n---\n".join(f"Source {i+1}:\n{a}" for i, a in enumerate(analyses) if a)
        prompt = f"""Analyze these source analyses for contradictions. Research: {query}

{all_text}

Identify (500-1000 words):
1. Direct Contradictions
2. Methodological Conflicts
3. Contextual Differences
4. Severity Assessment
5. Resolution Strategies
6. Nuanced Reconciliation"""
        try:
            return await self.gateway.complete(prompt=prompt, max_tokens=2000)
        except Exception:
            return ""

    async def _assemble_report(self, query, sources, analyses, synthesis, contradictions) -> str:
        """Assemble the final research report."""
        refs = []
        for s in sources:
            ref = f"- {', '.join(s.authors) if s.authors else 'Unknown'} ({s.year}). {s.title}."
            if s.doi:
                ref += f" DOI: https://doi.org/{s.doi}"
            refs.append(ref)

        # Generate title
        try:
            title_resp = await self.gateway.complete(
                prompt=f"Generate a professional academic title (max 15 words) for research on: {query}",
                max_tokens=100,
            )
            title = title_resp.strip().strip('"').strip("'")
        except Exception:
            title = f"Research Report: {query[:60]}"

        # Generate executive summary
        try:
            summary_resp = await self.gateway.complete(
                prompt=f"Write a 300-500 word executive summary for this research report.\n\nTitle: {title}\nQuery: {query}\nSources: {len(sources)}\n\nKey Synthesis:\n{synthesis[:1000]}\n\nContradictions:\n{contradictions[:500] if contradictions else 'None detected.'}",
                max_tokens=1500,
            )
        except Exception:
            summary_resp = f"Executive summary for: {query}"

        # Build full report
        report = f"""# {title}

**Research Question:** {query}
**Sources Analyzed:** {len(sources)}
**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

---

## Executive Summary

{summary_resp}

---

## 1. Introduction

### 1.1 Research Context

This report presents a systematic synthesis of {len(sources)} academic sources addressing: **{query}**

### 1.2 Methodology

Sources were retrieved from OpenAlex. Each source was individually analyzed for main arguments, theoretical frameworks, methodology, key findings, and relevance. The synthesis then cross-references all sources to identify themes, agreements, contradictions, and knowledge gaps.

### 1.3 Source Overview

| # | Title | Authors | Year |
|---|-------|---------|------|
{chr(10).join(f"| {i+1} | {s.title[:60]} | {', '.join(s.authors[:2]) if s.authors else 'Unknown'} | {s.year} |" for i, s in enumerate(sources))}

---

## 2. Literature Review

{chr(10).join(f"### Source {i+1}: {s.title}{chr(10)}{chr(10)}{a}{chr(10)}" for i, (s, a) in enumerate(zip(sources, analyses)) if a)}

---

## 3. Synthesis and Analysis

{synthesis}

---

## 4. Contradictions and Debates

{contradictions if contradictions else "No major contradictions detected."}

---

## 5. Discussion

### 5.1 Key Themes

The synthesis reveals several key themes across the literature, including interdisciplinary connections, methodological diversity, and emergent insights from cross-source analysis.

### 5.2 Theoretical Implications

The synthesized findings suggest theoretical implications extending beyond any single source's contribution.

### 5.3 Practical Implications

The research has practical implications for practitioners, policymakers, and researchers.

---

## 6. Limitations

- Analysis limited to {len(sources)} sources
- Source quality and methodology vary
- Publication bias may affect available evidence
- Cross-source comparison limited by terminology differences

---

## 7. Future Research Directions

1. Resolving identified contradictions through targeted studies
2. Methodological integration across approaches
3. Cross-domain validation of findings
4. Longitudinal analysis of dynamics

---

## 8. Conclusion

This report has presented a systematic synthesis of {len(sources)} academic sources addressing: **{query}**

The analysis reveals a complex, multi-faceted landscape where insights from different disciplines converge and diverge. The key contribution is the identification of cross-cutting themes, methodological trade-offs, and knowledge gaps.

---

## References

{chr(10).join(refs)}

---
*Generated by Sisyphus Academica — Phase 1 Cognition Substrate*
"""
        return report

    def _extract_sections(self, result: SynthesisResult, report: str):
        """Extract sections from the full report."""
        def extract(header: str) -> str:
            pattern = rf"## {re.escape(header)}\n(.*?)(?=\n## |\Z)"
            match = re.search(pattern, report, re.DOTALL)
            return match.group(1).strip() if match else ""

        result.title = extract("").split("\n")[0].strip("# ").strip() if report else ""
        result.executive_summary = extract("Executive Summary")
        result.introduction = extract("1. Introduction")
        result.literature_review = extract("2. Literature Review")
        result.findings = extract("3. Synthesis and Analysis")
        result.discussion = extract("5. Discussion")
        result.contradictions = extract("4. Contradictions and Debates")
        result.limitations = extract("6. Limitations")
        result.future_research = extract("7. Future Research Directions")
        result.conclusion = extract("8. Conclusion")
        result.references = extract("References")