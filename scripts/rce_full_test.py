"""
RCE Full Pipeline Test — All 3 Sources × 2 Topics

Queries OpenAlex, arXiv, and Semantic Scholar for:
  1. Information Theory × Trading Systems
  2. Geopolitical Risk × Emerging Markets

Then runs the full RCE pipeline (R1→R5) on all papers and outputs
a comprehensive quality comparison report.

Usage:
    python scripts/rce_full_test.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Windows encoding fix
os.environ["PYTHONIOENCODING"] = "utf-8"

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("rce.test")

# ─── Configuration ───

TOPICS = [
    {
        "name": "Information Theory × Trading Systems",
        "openalex_query": "information theory trading systems financial markets entropy",
        "arxiv_query": "cat:cs.IR+AND+(abs:information+theory+AND+abs:trading)",
        "s2_query": "information theory trading systems financial markets",
        "max_per_source": 10,
    },
    {
        "name": "Geopolitical Risk × Emerging Markets",
        "openalex_query": "geopolitical risk emerging markets financial contagion",
        "arxiv_query": "cat:cs.IR+AND+(abs:geopolitical+AND+abs:emerging+AND+abs:markets)",
        "s2_query": "geopolitical risk emerging markets financial contagion",
        "max_per_source": 10,
    },
]

# ─── Source Clients ───


async def fetch_openalex(query: str, max_results: int) -> list:
    """Fetch papers from OpenAlex."""
    from core.research.ingestion.openalex_client import OpenAlexClient

    logger.info(f"  OpenAlex: querying '{query[:60]}...'")
    try:
        async with OpenAlexClient() as client:
            papers = await client.search(query, per_page=max_results)
            logger.info(f"  OpenAlex: found {len(papers)} papers")
            return papers
    except Exception as e:
        logger.error(f"  OpenAlex failed: {e}")
        return []


async def fetch_arxiv(query: str, max_results: int) -> list:
    """Fetch papers from arXiv."""
    from core.research.ingestion.arxiv_client import ArxivClient

    logger.info(f"  arXiv: querying '{query[:60]}...'")
    try:
        client = ArxivClient()
        papers = await client.search(query, max_results=max_results)
        logger.info(f"  arXiv: found {len(papers)} papers")
        return papers
    except Exception as e:
        logger.error(f"  arXiv failed: {e}")
        return []


async def fetch_s2(query: str, max_results: int) -> list:
    """Fetch papers from Semantic Scholar."""
    from core.research.ingestion.s2_client import S2Client

    logger.info(f"  S2: querying '{query[:60]}...'")
    try:
        async with S2Client() as client:
            papers = await client.search(query, limit=max_results)
            logger.info(f"  S2: found {len(papers)} papers")
            return papers
    except Exception as e:
        logger.error(f"  S2 failed: {e}")
        return []


# ─── RCE Pipeline ───


def run_rce_pipeline(papers: list, topic_name: str) -> dict:
    """
    Run the full RCE pipeline on a set of papers.
    
    Args:
        papers: List of Paper objects from any source
        topic_name: Name of the topic for labeling
        
    Returns:
        Complete pipeline results
    """
    from core.research.cognition.decomposition import KnowledgeDecomposer
    from core.research.cognition.relationships import RelationshipBuilder
    from core.research.cognition.reasoning import CrossDocumentReasoner
    from core.research.cognition.synthesis import TheorySynthesizer
    from core.research.cognition.validation import RCEValidator

    logger.info(f"\n{'='*60}")
    logger.info(f"RCE Pipeline: {topic_name}")
    logger.info(f"  Papers: {len(papers)}")
    logger.info(f"{'='*60}")

    if len(papers) < 2:
        logger.warning(f"  Not enough papers ({len(papers)}), need at least 2")
        return {"error": f"Only {len(papers)} papers", "topic": topic_name}

    # Convert Paper objects to text for decomposition
    paper_dicts = []
    for p in papers:
        text = p.abstract or p.title or ""
        # Include abstract + title for better extraction
        full_text = f"{p.title}. {text}" if text != p.title else text
        paper_dicts.append({
            "text": full_text,
            "title": p.title or "Untitled",
            "authors": [a.name for a in p.authors] if p.authors else [],
            "year": str(p.year) if p.year else "",
            "doi": p.doi or "",
            "source_url": p.url or "",
        })

    # R1 — Decompose
    logger.info("  R1: Knowledge Decomposition...")
    decomposer = KnowledgeDecomposer()
    knowledge_objects = decomposer.decompose_batch(paper_dicts)
    logger.info(f"  R1: {len(knowledge_objects)} knowledge objects created")

    if not knowledge_objects:
        return {"error": "Decomposition produced no results", "topic": topic_name}

    # R2 — Relationships
    logger.info("  R2: Semantic Relationships...")
    builder = RelationshipBuilder()
    graph = builder.build_graph(knowledge_objects)
    logger.info(f"  R2: {graph['stats']['num_concepts']} concepts, "
                f"{graph['stats']['num_relationships']} relationships, "
                f"{graph['stats']['num_causal_chains']} causal chains")

    # R3 — Reasoning
    logger.info("  R3: Cross-Document Reasoning...")
    reasoner = CrossDocumentReasoner()
    reasoning = reasoner.reason(knowledge_objects)
    logger.info(f"  R3: {reasoning['stats']['num_contradictions']} contradictions, "
                f"{reasoning['stats']['num_consensus']} consensus areas, "
                f"{reasoning['stats']['num_reasoning_chains']} reasoning chains")

    # R4 — Synthesis
    logger.info("  R4: Theory Synthesis...")
    synthesizer = TheorySynthesizer()
    synthesis = synthesizer.synthesize(knowledge_objects, reasoning)
    logger.info(f"  R4: confidence={synthesis['confidence']:.3f}, "
                f"report_words={synthesis['research_report']['word_count']}")

    # R5 — Validation
    logger.info("  R5: Validation...")
    validator = RCEValidator()
    validation = validator.validate(knowledge_objects)
    logger.info(f"  R5: passed={validation['passed']}, "
                f"completeness={validation['metrics'].get('extraction_completeness', 0):.3f}")

    return {
        "topic": topic_name,
        "num_papers": len(papers),
        "num_knowledge_objects": len(knowledge_objects),
        "graph_stats": graph["stats"],
        "reasoning_stats": reasoning["stats"],
        "reasoning_unified": reasoning["unified_reasoning"],
        "synthesis_confidence": synthesis["confidence"],
        "synthesis_report": synthesis["research_report"],
        "validation_passed": validation["passed"],
        "validation_metrics": validation["metrics"],
        "validation_benchmarks": validation["benchmarks"],
        "validation_recommendations": validation["recommendations"],
    }


# ─── Main ───


async def main():
    start_time = time.time()
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    logger.info("=" * 70)
    logger.info("RCE FULL PIPELINE TEST — All 3 Sources × 2 Topics")
    logger.info(f"Timestamp: {timestamp_str}")
    logger.info("=" * 70)

    all_results = {}

    for topic in TOPICS:
        topic_name = topic["name"]
        logger.info(f"\n{'#'*70}")
        logger.info(f"# TOPIC: {topic_name}")
        logger.info(f"{'#'*70}")

        # Fetch from ALL 3 sources in parallel
        logger.info("\n--- Fetching from all 3 sources ---")
        openalex_papers, arxiv_papers, s2_papers = await asyncio.gather(
            fetch_openalex(topic["openalex_query"], topic["max_per_source"]),
            fetch_arxiv(topic["arxiv_query"], topic["max_per_source"]),
            fetch_s2(topic["s2_query"], topic["max_per_source"]),
        )

        # Deduplicate by DOI/title
        seen_dois = set()
        seen_titles = set()
        all_papers = []
        source_counts = {"openalex": 0, "arxiv": 0, "s2": 0}

        for source, papers in [
            ("openalex", openalex_papers),
            ("arxiv", arxiv_papers),
            ("s2", s2_papers),
        ]:
            for paper in papers:
                doi = paper.doi or ""
                title_key = (paper.title or "").lower().strip()[:60]

                if doi and doi in seen_dois:
                    continue
                if title_key in seen_titles:
                    continue

                if doi:
                    seen_dois.add(doi)
                seen_titles.add(title_key)
                all_papers.append(paper)
                source_counts[source] += 1

        logger.info(f"\n--- Deduplicated totals ---")
        logger.info(f"  OpenAlex: {source_counts['openalex']} unique")
        logger.info(f"  arXiv:    {source_counts['arxiv']} unique")
        logger.info(f"  S2:       {source_counts['s2']} unique")
        logger.info(f"  Total:    {len(all_papers)} unique papers")

        if len(all_papers) < 2:
            logger.warning(f"  Not enough unique papers for {topic_name}, skipping")
            all_results[topic_name] = {"error": "Not enough papers", "total": len(all_papers)}
            continue

        # Run RCE pipeline
        result = run_rce_pipeline(all_papers, topic_name)
        result["source_counts"] = source_counts
        all_results[topic_name] = result

    # ─── Output Report ───

    duration = time.time() - start_time
    logger.info(f"\n{'='*70}")
    logger.info("PIPELINE TEST COMPLETE")
    logger.info(f"Duration: {duration:.1f}s")
    logger.info(f"{'='*70}")

    # Print summary comparison
    for topic_name, result in all_results.items():
        logger.info(f"\n--- {topic_name} ---")
        if "error" in result:
            logger.info(f"  ERROR: {result['error']}")
            continue

        logger.info(f"  Papers: {result['num_papers']} (OA: {result['source_counts']['openalex']}, "
                     f"arXiv: {result['source_counts']['arxiv']}, S2: {result['source_counts']['s2']})")
        logger.info(f"  Knowledge Objects: {result['num_knowledge_objects']}")
        logger.info(f"  Concepts: {result['graph_stats']['num_concepts']}")
        logger.info(f"  Relationships: {result['graph_stats']['num_relationships']}")
        logger.info(f"  Causal Chains: {result['graph_stats']['num_causal_chains']}")
        logger.info(f"  Contradictions: {result['reasoning_stats']['num_contradictions']}")
        logger.info(f"  Consensus Areas: {result['reasoning_stats']['num_consensus']}")
        logger.info(f"  Reasoning Chains: {result['reasoning_stats']['num_reasoning_chains']}")
        logger.info(f"  Synthesis Confidence: {result['synthesis_confidence']:.3f}")
        logger.info(f"  Report Words: {result['synthesis_report']['word_count']}")
        logger.info(f"  Validation Passed: {result['validation_passed']}")
        logger.info(f"  Extraction Completeness: {result['validation_metrics'].get('extraction_completeness', 0):.3f}")
        logger.info(f"  Mechanism Coverage: {result['validation_metrics'].get('mechanism_coverage', 0):.3f}")

        # Landscape
        landscape = result['reasoning_unified'].get('landscape', 'unknown')
        logger.info(f"  Research Landscape: {landscape}")

    # Save full results to JSON
    output_dir = PROJECT_ROOT / "data" / "rce_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"rce_test_{timestamp_str}.json"

    # Serialize results (convert non-serializable objects)
    def serialize(obj):
        if hasattr(obj, '__dict__'):
            return {k: serialize(v) for k, v in obj.__dict__.items()}
        if isinstance(obj, (list, tuple)):
            return [serialize(v) for v in obj]
        if isinstance(obj, dict):
            return {k: serialize(v) for k, v in obj.items()}
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        return str(obj)

    serializable = {}
    for topic, result in all_results.items():
        serializable[topic] = serialize(result)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)

    logger.info(f"\nFull results saved to: {output_file}")

    # Also save the synthesis reports as markdown
    for topic_name, result in all_results.items():
        if "synthesis_report" in result:
            safe_name = topic_name.replace(" ", "_").replace("×", "x").lower()
            report_file = output_dir / f"report_{safe_name}_{timestamp_str}.md"
            report_text = result["synthesis_report"].get("full_report", "No report generated.")
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(f"# {topic_name}\n\n")
                f.write(f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n")
                f.write(f"**Papers analyzed:** {result.get('num_papers', 0)}\n")
                f.write(f"**Sources:** OpenAlex ({result.get('source_counts', {}).get('openalex', 0)}), "
                        f"arXiv ({result.get('source_counts', {}).get('arxiv', 0)}), "
                        f"S2 ({result.get('source_counts', {}).get('s2', 0)})\n")
                f.write(f"**Synthesis confidence:** {result.get('synthesis_confidence', 0):.3f}\n")
                f.write(f"**Validation passed:** {result.get('validation_passed', False)}\n\n")
                f.write("---\n\n")
                f.write(report_text)
            logger.info(f"Report saved to: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
