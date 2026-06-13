"""
Phase 1 — Integration Test Harness

Tests the full cognition pipeline with real OpenAlex API calls
and interdisciplinary synthesis.

Test Strategy:
- Use niche, interdisciplinary topics that force cross-domain retrieval
- Test OpenAlex ingestion → chunking → embedding → retrieval → synthesis
- Verify Sisyphus can synthesize across disparate fields

Run:
    python -m pytest core/tests/test_phase1_integration.py -v --tb=long -s
    
Or directly:
    python core/tests/test_phase1_integration.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("phase1_test")

# ─── Test Configuration ─────────────────────────────────────────────────────

# Interdisciplinary test topics designed to stress the system
TEST_TOPICS = [
    {
        "name": "Emerging Markets × Geopolitics",
        "query": "emerging markets geopolitical risk institutional quality",
        "description": "Tests cross-domain synthesis between political science, economics, and international relations",
        "expected_domains": ["economics", "political science", "international relations"],
        "min_sources": 5,
    },
    {
        "name": "Information Theory × Trading Systems",
        "query": "information theory entropy trading systems market microstructure",
        "description": "Tests synthesis across physics, computer science, and quantitative finance",
        "expected_domains": ["information theory", "finance", "computer science"],
        "min_sources": 5,
    },
    {
        "name": "Thermodynamics × Economic Systems",
        "query": "thermodynamics entropy economic systems complexity",
        "description": "Tests synthesis between physics and economics — far-field interdisciplinary",
        "expected_domains": ["physics", "economics", "complexity science"],
        "min_sources": 3,
    },
    {
        "name": "Cognitive Science × Machine Learning",
        "query": "cognitive architectures attention mechanisms working memory neural networks",
        "description": "Tests synthesis between neuroscience and AI — closely related but distinct vocabularies",
        "expected_domains": ["cognitive science", "machine learning", "neuroscience"],
        "min_sources": 5,
    },
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

class TestResult:
    """Tracks test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors: List[str] = []
        self.details: List[Dict] = []

    def record(self, name: str, passed: bool, detail: Any = None):
        if passed:
            self.passed += 1
            logger.info(f"  ✅ {name}")
        else:
            self.failed += 1
            self.errors.append(name)
            logger.error(f"  ❌ {name}")
        self.details.append({"name": name, "passed": passed, "detail": detail})

    @property
    def total(self):
        return self.passed + self.failed

    def summary(self):
        lines = [
            f"\n{'='*60}",
            f"RESULTS: {self.passed}/{self.total} passed",
            f"{'='*60}",
        ]
        if self.errors:
            lines.append("FAILURES:")
            for e in self.errors:
                lines.append(f"  ❌ {e}")
        return "\n".join(lines)


# ─── Test 1: OpenAlex API Integration ────────────────────────────────────────

async def test_openalex_api_integration(result: TestResult):
    """Test OpenAlex API with real calls."""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: OpenAlex API Integration")
    logger.info("="*60)

    try:
        from core.research.ingestion.openalex import OpenAlexClient, OpenAlexNormalizer
    except ImportError as e:
        result.record("OpenAlex import", False, str(e))
        return

    client = OpenAlexClient()

    try:
        # Test 1a: Basic search
        logger.info("\n1a: Basic search...")
        raw_results = await client.search_works("emerging markets geopolitics", limit=5)
        result.record(
            "OpenAlex search returns results",
            len(raw_results) > 0,
            f"Got {len(raw_results)} results",
        )

        if raw_results:
            # Test 1b: Result structure
            first = raw_results[0]
            result.record(
                "Result has required fields",
                all(k in first for k in ["id", "title"]),
                f"Keys: {list(first.keys())[:10]}",
            )

            # Test 1c: Normalization
            logger.info("\n1c: Normalization...")
            work = OpenAlexNormalizer.normalize_work(first)
            result.record(
                "Normalization produces valid work",
                work.work_id != "" and work.title != "",
                f"ID={work.work_id}, Title={work.title[:60]}",
            )

            # Test 1d: Semantic tags
            result.record(
                "Semantic tags extracted",
                isinstance(work.semantic_tags, list),
                f"Tags: {work.semantic_tags[:5]}",
            )

            # Test 1e: DOI handling
            if work.doi:
                result.record(
                    "DOI properly extracted",
                    "/" in work.doi and "http" not in work.doi,
                    f"DOI: {work.doi}",
                )

        # Test 1f: DOI lookup
        logger.info("\n1f: DOI lookup...")
        doi_work = await client.get_work_by_doi("10.1038/s41586-021-03819-2")
        result.record(
            "DOI lookup works",
            doi_work is not None,
            f"Title: {doi_work.get('title', 'N/A')[:60] if doi_work else 'None'}",
        )

        # Test 1g: Pagination (OpenAlex uses page numbers, not offsets)
        logger.info("\n1g: Pagination...")
        page1 = await client.search_works("machine learning", limit=3)
        page2 = await client.search_works("machine learning", limit=3, page=2)
        result.record(
            "Pagination returns different results",
            len(page1) > 0 and len(page2) > 0 and page1[0].get("id") != page2[0].get("id"),
            f"Page1[0]={page1[0].get('id', '')[:20]}, Page2[0]={page2[0].get('id', '')[:20]}",
        )

        # Test 1h: Rate limiting (should not error)
        logger.info("\n1h: Rate limiting...")
        start = time.time()
        await asyncio.gather(*[
            client.search_works(f"test query {i}", limit=1)
            for i in range(5)
        ])
        elapsed = time.time() - start
        result.record(
            "Rate limiting works (5 calls in < 2s)",
            elapsed < 2.0,
            f"5 calls in {elapsed:.2f}s",
        )

    finally:
        await client.close()


# ─── Test 2: Full Ingestion Pipeline ────────────────────────────────────────

async def test_full_ingestion_pipeline(result: TestResult):
    """Test the full ingestion pipeline for multiple topics."""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Full Ingestion Pipeline")
    logger.info("="*60)

    try:
        from core.research.ingestion.openalex import OpenAlexIngester, OpenAlexClient
    except ImportError as e:
        result.record("Ingester import", False, str(e))
        return

    client = OpenAlexClient()
    ingester = OpenAlexIngester(client=client)

    try:
        for topic in TEST_TOPICS:
            logger.info(f"\nTopic: {topic['name']}")
            logger.info(f"Query: {topic['query']}")

            start = time.time()
            works = await ingester.ingest_query(topic["query"], limit=topic["min_sources"])
            elapsed = time.time() - start

            result.record(
                f"[{topic['name']}] Ingestion returns works",
                len(works) >= topic["min_sources"],
                f"Got {len(works)} works in {elapsed:.1f}s",
            )

            if works:
                # Check quality
                with_abstracts = sum(1 for w in works if w.abstract)
                with_concepts = sum(1 for w in works if w.concepts)
                with_authors = sum(1 for w in works if w.authors)

                result.record(
                    f"[{topic['name']}] Works have abstracts",
                    with_abstracts > 0,
                    f"{with_abstracts}/{len(works)} have abstracts",
                )

                result.record(
                    f"[{topic['name']}] Works have concepts",
                    with_concepts > 0,
                    f"{with_concepts}/{len(works)} have concepts",
                )

                result.record(
                    f"[{topic['name']}] Works have authors",
                    with_authors > 0,
                    f"{with_authors}/{len(works)} have authors",
                )

                # Check domain diversity
                all_concepts = set()
                for w in works:
                    for c in w.concepts:
                        all_concepts.add(c.display_name.lower())

                result.record(
                    f"[{topic['name']}] Domain diversity",
                    len(all_concepts) >= 3,
                    f"{len(all_concepts)} unique concepts: {list(all_concepts)[:10]}",
                )

                # Check deduplication
                unique_ids = set(w.canonical_id for w in works)
                result.record(
                    f"[{topic['name']}] No duplicates",
                    len(unique_ids) == len(works),
                    f"{len(unique_ids)} unique / {len(works)} total",
                )

    finally:
        await ingester.close()


# ─── Test 3: Sisyphus Synthesis ──────────────────────────────────────────────

async def test_sisyphus_synthesis(result: TestResult):
    """Test Sisyphus synthesis with real ingested data."""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Sisyphus Synthesis Engine")
    logger.info("="*60)

    try:
        from core.research.synthesis.sisyphus import SisyphusEngine, SourceDocument
        from core.research.ingestion.openalex import OpenAlexIngester, OpenAlexClient
        from core.spawn.openrouter_gateway import OpenRouterGateway
    except ImportError as e:
        result.record("Synthesis import", False, str(e))
        return

    client = OpenAlexClient()
    ingester = OpenAlexIngester(client=client)
    gateway = OpenRouterGateway()
    sisyphus = SisyphusEngine(gateway=gateway)

    try:
        for topic in TEST_TOPICS[:2]:  # Test with 2 topics to save time
            logger.info(f"\nSynthesizing: {topic['name']}")

            # Ingest sources
            works = await ingester.ingest_query(topic["query"], limit=8)

            if len(works) < 3:
                result.record(
                    f"[{topic['name']}] Enough sources for synthesis",
                    False,
                    f"Only {len(works)} sources",
                )
                continue

            # Convert to SourceDocuments
            sources = [
                SourceDocument(
                    doc_id=w.canonical_id,
                    title=w.title,
                    text=f"{w.title}. {w.abstract}" if w.abstract else w.title,
                    source="openalex",
                    metadata=w.to_dict(),
                )
                for w in works
            ]

            # Synthesize
            start = time.time()
            synthesis = sisyphus.synthesize(
                query=f"How does {topic['name'].split(' × ')[0].lower()} relate to {topic['name'].split(' × ')[1].lower()}?",
                sources=sources,
            )
            elapsed = time.time() - start

            result.record(
                f"[{topic['name']}] Synthesis completes",
                synthesis is not None,
                f"Completed in {elapsed:.1f}s",
            )

            if synthesis:
                result.record(
                    f"[{topic['name']}] Has findings",
                    len(synthesis.key_findings) > 0,
                    f"{len(synthesis.key_findings)} findings",
                )

                result.record(
                    f"[{topic['name']}] Has summary",
                    len(synthesis.executive_summary) > 50,
                    f"Summary length: {len(synthesis.executive_summary)}",
                )

                result.record(
                    f"[{topic['name']}] Has citations",
                    len(synthesis.citations) > 0,
                    f"{len(synthesis.citations)} citations",
                )

                result.record(
                    f"[{topic['name']}] Confidence > 0",
                    synthesis.confidence > 0,
                    f"Confidence: {synthesis.confidence:.2f}",
                )

                # Check finding quality
                if synthesis.key_findings:
                    top_finding = synthesis.key_findings[0]
                    result.record(
                        f"[{topic['name']}] Top finding has sources",
                        len(top_finding.supporting_sources) > 0,
                        f"Sources: {top_finding.supporting_sources[:3]}",
                    )

                    result.record(
                        f"[{topic['name']}] Top finding has evidence",
                        len(top_finding.evidence) > 0,
                        f"Evidence items: {len(top_finding.evidence)}",
                    )

                # Log the actual output
                logger.info(f"\n  Executive Summary:\n  {synthesis.executive_summary[:300]}")
                logger.info(f"\n  Top Findings:")
                for i, f in enumerate(synthesis.key_findings[:3], 1):
                    logger.info(f"    {i}. [{f.confidence:.0%}] {f.text[:120]}")

    finally:
        await ingester.close()


# ─── Test 4: Argument Structure ──────────────────────────────────────────────

async def test_argument_structure(result: TestResult):
    """Test argument structuring with synthesis results."""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Argument Structure")
    logger.info("="*60)

    try:
        from core.research.synthesis.argument import ArgumentStructurer, Evidence
        from core.research.synthesis.sisyphus import SisyphusEngine, SourceDocument
        from core.research.ingestion.openalex import OpenAlexIngester, OpenAlexClient
    except ImportError as e:
        result.record("Argument import", False, str(e))
        return

    client = OpenAlexClient()
    ingester = OpenAlexIngester(client=client)
    sisyphus = SisyphusEngine()
    structurer = ArgumentStructurer()

    try:
        # Use the information theory × trading topic
        topic = TEST_TOPICS[1]
        logger.info(f"\nTopic: {topic['name']}")

        works = await ingester.ingest_query(topic["query"], limit=5)
        if len(works) < 3:
            result.record("Enough sources", False, f"Only {len(works)}")
            return

        sources = [
            SourceDocument(
                doc_id=w.canonical_id,
                title=w.title,
                text=f"{w.title}. {w.abstract}" if w.abstract else w.title,
                source="openalex",
                metadata=w.to_dict(),
            )
            for w in works
        ]

        synthesis = sisyphus.synthesize(
            query=f"How does information theory apply to trading systems?",
            sources=sources,
        )

        if synthesis and synthesis.key_findings:
            # Structure the top finding as an argument
            top_finding = synthesis.key_findings[0]
            evidence_list = [
                Evidence(
                    text=e[:200],
                    source=src,
                    strength=top_finding.confidence,
                )
                for e, src in zip(top_finding.evidence[:3], top_finding.supporting_sources[:3])
            ]

            argument = structurer.structure(
                claim=top_finding.text[:200],
                evidence_list=evidence_list,
                reasoning="Synthesized from multiple interdisciplinary sources",
            )

            result.record(
                "Argument structure created",
                argument.root is not None,
                f"Root: {argument.root.text[:80]}",
            )

            result.record(
                "Argument has evidence nodes",
                len(argument.root.children) > 0,
                f"Children: {len(argument.root.children)}",
            )

            result.record(
                "Argument strength > 0",
                argument.overall_strength > 0,
                f"Strength: {argument.overall_strength:.2f}",
            )

            result.record(
                "Gap detection works",
                isinstance(argument.gaps, list),
                f"Gaps: {argument.gaps}",
            )

            # Test Mermaid output
            mermaid = argument.to_mermaid()
            result.record(
                "Mermaid diagram generated",
                "graph TD" in mermaid,
                f"Length: {len(mermaid)}",
            )

    finally:
        await ingester.close()


# ─── Test 5: Citation Mapping ───────────────────────────────────────────────

async def test_citation_mapping(result: TestResult):
    """Test citation extraction and bibliography generation."""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: Citation Mapping")
    logger.info("="*60)

    try:
        from core.research.synthesis.citation import CitationMapper, Citation
    except ImportError as e:
        result.record("Citation import", False, str(e))
        return

    mapper = CitationMapper()

    # Test with real paper text
    sample_text = """
    This builds on the work of Shannon (10.1002/j.1538-7305.1948.tb01338.x) 
    who established information theory. Recent work by arXiv:2401.00001 and 
    https://doi.org/10.1038/s41586-021-03819-2 extends these ideas.
    See also https://arxiv.org/abs/2305.12345 for related work.
    """

    citations = mapper.extract_citations(sample_text)
    result.record(
        "Citations extracted from text",
        len(citations) >= 2,
        f"Found {len(citations)} citations",
    )

    # Test bibliography generation
    if citations:
        apa_bib = mapper.generate_bibliography(citations, format="apa")
        result.record(
            "APA bibliography generated",
            len(apa_bib) > 0,
            f"Length: {len(apa_bib)}",
        )

        bibtex_bib = mapper.generate_bibliography(citations, format="bibtex")
        result.record(
            "BibTeX bibliography generated",
            "@misc" in bibtex_bib,
            f"Length: {len(bibtex_bib)}",
        )

    # Test validation
    valid_citation = Citation(
        citation_id="test",
        title="Test Paper",
        authors=["Author"],
        year="2024",
        doi="10.1000/test",
    )
    validation = mapper.validate_citation(valid_citation)
    result.record(
        "Valid citation passes validation",
        validation["valid"] is True,
        f"Issues: {validation['issues']}",
    )


# ─── Test 6: Contradiction Detection ────────────────────────────────────────

async def test_contradiction_detection(result: TestResult):
    """Test contradiction detection across sources."""
    logger.info("\n" + "="*60)
    logger.info("TEST 6: Contradiction Detection")
    logger.info("="*60)

    try:
        from core.research.synthesis.contradiction import ContradictionDetector
        from core.research.synthesis.sisyphus import Claim
    except ImportError as e:
        result.record("Contradiction import", False, str(e))
        return

    detector = ContradictionDetector()

    # Test with synthetic claims that should contradict
    claims = [
        {"text": "Market entropy increases with information asymmetry in all tested conditions", "source": "doc1"},
        {"text": "Market entropy does not increase with information asymmetry in tested conditions", "source": "doc2"},
        {"text": "Information theory provides useful frameworks for understanding market microstructure", "source": "doc3"},
        {"text": "Trading systems based on entropy measures show improved risk-adjusted returns", "source": "doc4"},
        {"text": "Entropy-based trading systems do not show improved risk-adjusted returns in live testing", "source": "doc5"},
    ]

    contradictions = detector.detect(claims)
    result.record(
        "Contradictions detected",
        len(contradictions) > 0,
        f"Found {len(contradictions)} contradictions",
    )

    if contradictions:
        result.record(
            "Contradictions have severity",
            all(c.severity in ("low", "medium", "high") for c in contradictions),
            f"Severities: {[c.severity for c in contradictions]}",
        )

        result.record(
            "Contradictions have resolution hints",
            all(len(c.resolution_hint) > 0 for c in contradictions),
            f"Hints: {[c.resolution_hint[:50] for c in contradictions[:2]]}",
        )


# ─── Test 7: Report Generation ──────────────────────────────────────────────

async def test_report_generation(result: TestResult):
    """Test research report generation."""
    logger.info("\n" + "="*60)
    logger.info("TEST 7: Report Generation")
    logger.info("="*60)

    try:
        from core.research.synthesis.report import ResearchReportGenerator
        from core.research.synthesis.sisyphus import SynthesisResult, Claim
    except ImportError as e:
        result.record("Report import", False, str(e))
        return

    generator = ResearchReportGenerator()

    # Create a mock synthesis result
    synthesis = SynthesisResult(
        query="How does information theory relate to trading systems?",
        executive_summary="Information theory provides fundamental frameworks for understanding market microstructure and trading system design.",
        key_findings=[
            Claim(
                text="Entropy measures from information theory quantify market uncertainty",
                confidence=0.85,
                supporting_sources=["doc1", "doc2"],
                evidence=["Study shows entropy correlates with volatility"],
            ),
            Claim(
                text="Trading systems using information-theoretic features show improved risk-adjusted returns",
                confidence=0.72,
                supporting_sources=["doc3"],
                evidence=["Backtest results show 15% improvement in Sharpe ratio"],
            ),
        ],
        contradictions=[
            {
                "claim_a": "Entropy measures improve trading performance",
                "claim_b": "Entropy measures do not improve trading performance in live tests",
                "severity": "medium",
            },
        ],
        citations=[
            {"id": "doc1", "title": "Information Theory in Markets", "authors": ["Smith, J."], "year": "2023", "doi": "10.1000/test1"},
            {"id": "doc2", "title": "Entropy and Trading", "authors": ["Doe, A."], "year": "2024", "doi": "10.1000/test2"},
        ],
        source_count=5,
        confidence=0.78,
        gaps=["Limited live testing data", "Most studies use backtested results"],
    )

    # Test Markdown
    md_report = generator.generate(synthesis, format="markdown")
    result.record(
        "Markdown report generated",
        len(md_report) > 100 and "# Research Report" in md_report,
        f"Length: {len(md_report)}",
    )

    # Test JSON
    json_report = generator.generate(synthesis, format="json")
    json_data = json.loads(json_report)
    result.record(
        "JSON report valid",
        json_data["query"] == synthesis.query and len(json_data["key_findings"]) > 0,
        f"Keys: {list(json_data.keys())}",
    )

    # Test HTML
    html_report = generator.generate(synthesis, format="html")
    result.record(
        "HTML report generated",
        "<html>" in html_report.lower() or "<!DOCTYPE" in html_report,
        f"Length: {len(html_report)}",
    )

    # Save reports for inspection
    output_dir = REPO_ROOT / "data" / "test_reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "test_report.md").write_text(md_report, encoding="utf-8")
    (output_dir / "test_report.json").write_text(json_report, encoding="utf-8")
    (output_dir / "test_report.html").write_text(html_report, encoding="utf-8")
    logger.info(f"\n  Reports saved to {output_dir}/")


# ─── Main Runner ─────────────────────────────────────────────────────────────

async def run_all_tests():
    """Run all integration tests."""
    result = TestResult()

    logger.info("="*60)
    logger.info("PHASE 1 INTEGRATION TEST HARNESS")
    logger.info("Testing: OpenAlex → Ingestion → Synthesis → Reports")
    logger.info("="*60)

    # Test 1: OpenAlex API
    await test_openalex_api_integration(result)

    # Test 2: Full ingestion pipeline
    await test_full_ingestion_pipeline(result)

    # Test 3: Sisyphus synthesis
    await test_sisyphus_synthesis(result)

    # Test 4: Argument structure
    await test_argument_structure(result)

    # Test 5: Citation mapping
    await test_citation_mapping(result)

    # Test 6: Contradiction detection
    await test_contradiction_detection(result)

    # Test 7: Report generation
    await test_report_generation(result)

    # Summary
    print(result.summary())
    return result


if __name__ == "__main__":
    result = asyncio.run(run_all_tests())
    sys.exit(0 if result.failed == 0 else 1)
