"""
RCE Fresh Test — Multi-source ingestion + full pipeline.

Fetches papers from ALL 3 sources (OpenAlex, arXiv, S2) for:
  1. Information Theory × Trading Systems
  2. Geopolitical Risk × Emerging Markets

Then runs the full RCE pipeline (R1→R5) on each topic separately
and on the combined set. Outputs quality comparison metrics.

Usage:
    python scripts/rce_fresh_test.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows encoding fix
os.environ["PYTHONIOENCODING"] = "utf-8"

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.research.cognition import (
    KnowledgeDecomposer,
    MultiSourceFetcher,
    RelationshipBuilder,
    CrossDocumentReasoner,
    TheorySynthesizer,
    RCEValidator,
)


TOPICS = [
    "transfer entropy financial markets systemic risk contagion",
    "geopolitical risk emerging markets capital flows financial crisis",
]

PAPERS_PER_SOURCE = 10
YEAR_FROM = 2016


async def fetch_all_topics():
    """Fetch papers from all 3 sources for all topics."""
    fetcher = MultiSourceFetcher()
    
    all_papers = {}
    for topic in TOPICS:
        print(f"\n{'='*70}")
        print(f"FETCHING: {topic}")
        print(f"{'='*70}")
        
        papers = await fetcher.fetch_papers(
            query=topic,
            per_source=PAPERS_PER_SOURCE,
            year_from=YEAR_FROM,
        )
        
        all_papers[topic] = papers
        
        # Print source breakdown
        sources = {}
        for p in papers:
            src = p.source
            sources[src] = sources.get(src, 0) + 1
        
        print(f"\n  Total unique papers: {len(papers)}")
        for src, count in sorted(sources.items()):
            print(f"    {src}: {count}")
        
        # Print top papers
        print(f"\n  Top papers:")
        for p in papers[:5]:
            print(f"    [{p.source}] {p.title[:70]} ({p.year}, {p.citation_count} citations)")
    
    return all_papers


def run_rce_pipeline(topic_name: str, papers):
    """Run the full RCE pipeline on a set of papers."""
    print(f"\n{'='*70}")
    print(f"RCE PIPELINE: {topic_name}")
    print(f"{'='*70}")
    
    # Convert Paper objects to text for decomposition
    paper_dicts = []
    for p in papers:
        text = p.abstract or p.title
        # Enhance with concepts if available
        if p.concepts:
            concept_text = ", ".join(c.name for c in p.concepts[:5])
            text = f"{text}. Key concepts: {concept_text}"
        
        paper_dicts.append({
            "text": text,
            "title": p.title,
            "authors": [a.name for a in p.authors],
            "year": str(p.year),
            "doi": p.doi,
            "source_url": p.url,
            "source": p.source,
        })
    
    # R1 — Decompose
    print(f"\n  R1: Decomposing {len(paper_dicts)} papers...")
    decomposer = KnowledgeDecomposer()
    knowledge_objects = decomposer.decompose_batch(paper_dicts)
    
    total_claims = sum(len(obj.main_claims) for obj in knowledge_objects)
    total_mechanisms = sum(len(obj.mechanisms) for obj in knowledge_objects)
    total_assumptions = sum(len(obj.assumptions) for obj in knowledge_objects)
    total_equations = sum(len(obj.equations) for obj in knowledge_objects)
    total_limitations = sum(len(obj.limitations) for obj in knowledge_objects)
    total_novelty = sum(1 for obj in knowledge_objects if obj.novel_contribution)
    avg_completeness = sum(obj.extraction_completeness for obj in knowledge_objects) / max(len(knowledge_objects), 1)
    
    print(f"    Knowledge objects: {len(knowledge_objects)}")
    print(f"    Claims: {total_claims}, Mechanisms: {total_mechanisms}")
    print(f"    Assumptions: {total_assumptions}, Equations: {total_equations}")
    print(f"    Limitations: {total_limitations}, Novelty: {total_novelty}")
    print(f"    Avg completeness: {avg_completeness:.2f}")
    
    # R2 — Relationships
    print(f"\n  R2: Building relationship graph...")
    builder = RelationshipBuilder()
    graph = builder.build_graph(knowledge_objects)
    
    print(f"    Concepts: {graph['stats']['num_concepts']}")
    print(f"    Relationships: {graph['stats']['num_relationships']}")
    print(f"    Causal chains: {graph['stats']['num_causal_chains']}")
    print(f"    Clusters: {graph['stats']['num_clusters']}")
    
    # R3 — Reasoning
    print(f"\n  R3: Cross-document reasoning...")
    reasoner = CrossDocumentReasoner()
    reasoning = reasoner.reason(knowledge_objects)
    
    print(f"    Contradictions: {reasoning['stats']['num_contradictions']}")
    print(f"    Consensus areas: {reasoning['stats']['num_consensus']}")
    print(f"    Assumption conflicts: {reasoning['stats']['num_assumption_conflicts']}")
    print(f"    Reasoning chains: {reasoning['stats']['num_reasoning_chains']}")
    
    landscape = reasoning.get("unified_reasoning", {}).get("landscape", "?")
    print(f"    Research landscape: {landscape}")
    
    # R4 — Synthesis
    print(f"\n  R4: Theory synthesis...")
    synthesizer = TheorySynthesizer()
    synthesis = synthesizer.synthesize(knowledge_objects, reasoning)
    
    report = synthesis["research_report"]
    print(f"    Confidence: {synthesis['confidence']:.3f}")
    print(f"    Report: {report['title']}")
    print(f"    Report length: {report['word_count']} words")
    print(f"    Domains: {synthesis['domains_covered']}")
    
    # R5 — Validation
    print(f"\n  R5: Validation...")
    validator = RCEValidator()
    validation = validator.validate(knowledge_objects)
    
    print(f"    Overall pass: {validation['passed']}")
    for benchmark in validation["benchmarks"]:
        status = "✅" if benchmark["passed"] else "❌"
        print(f"    {status} {benchmark['name']}: {benchmark['details']}")
    
    metrics = validation["metrics"]
    print(f"    Extraction completeness: {metrics['extraction_completeness']:.3f}")
    print(f"    Mechanism coverage: {metrics['mechanism_coverage']:.3f}")
    print(f"    Synthesis confidence: {metrics['synthesis_confidence']:.3f}")
    
    return {
        "topic": topic_name,
        "num_papers": len(papers),
        "num_knowledge_objects": len(knowledge_objects),
        "r1": {
            "claims": total_claims,
            "mechanisms": total_mechanisms,
            "assumptions": total_assumptions,
            "equations": total_equations,
            "limitations": total_limitations,
            "novelty": total_novelty,
            "avg_completeness": round(avg_completeness, 3),
        },
        "r2": graph["stats"],
        "r3": {
            **reasoning["stats"],
            "landscape": landscape,
        },
        "r4": {
            "confidence": round(synthesis["confidence"], 3),
            "report_word_count": report["word_count"],
            "report_title": report["title"],
            "domains_covered": synthesis["domains_covered"],
        },
        "r5": {
            "passed": validation["passed"],
            "completeness": metrics["extraction_completeness"],
            "mechanism_coverage": metrics["mechanism_coverage"],
            "synthesis_confidence": metrics["synthesis_confidence"],
            "benchmarks": [{"name": b["name"], "passed": b["passed"]} for b in validation["benchmarks"]],
        },
        "report_full": report["full_report"],
    }


async def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║  RCE FRESH TEST — Multi-Source Ingestion + Full Pipeline           ║")
    print(f"║  Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}                              ║")
    print("║  Sources: OpenAlex + arXiv + S2 (all 3)                            ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    
    # Fetch papers from all 3 sources
    all_papers = await fetch_all_topics()
    
    # Run RCE pipeline on each topic
    results = []
    for i, topic in enumerate(TOPICS):
        papers = all_papers[topic]
        if len(papers) < 2:
            print(f"\n  ⚠️  Only {len(papers)} papers for '{topic}' — need at least 2 for cross-document reasoning")
            continue
        
        result = run_rce_pipeline(topic, papers)
        results.append(result)
    
    # Run combined pipeline (all papers together)
    all_papers_flat = []
    for papers in all_papers.values():
        all_papers_flat.extend(papers)
    
    if len(all_papers_flat) >= 4:
        combined_result = run_rce_pipeline("COMBINED (All Topics)", all_papers_flat)
        results.append(combined_result)
    
    # Summary comparison
    print(f"\n{'='*70}")
    print("QUALITY COMPARISON SUMMARY")
    print(f"{'='*70}")
    
    print(f"\n{'Topic':<45} {'Papers':>6} {'Claims':>6} {'Mech':>5} {'Comp':>5} {'Contra':>6} {'Conse':>5} {'Synth':>5} {'Pass':>5}")
    print("-" * 100)
    
    for r in results:
        topic_short = r["topic"][:44]
        print(
            f"{topic_short:<45} "
            f"{r['num_papers']:>6} "
            f"{r['r1']['claims']:>6} "
            f"{r['r1']['mechanisms']:>5} "
            f"{r['r1']['avg_completeness']:>5.2f} "
            f"{r['r3']['num_contradictions']:>6} "
            f"{r['r3']['num_consensus']:>5} "
            f"{r['r4']['confidence']:>5.3f} "
            f"{'✅' if r['r5']['passed'] else '❌':>5}"
        )
    
    # Save results
    output_dir = PROJECT_ROOT / "data" / "rce_test_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_file = output_dir / f"rce_fresh_test_{timestamp}.json"
    
    # Save JSON (without full report text for readability)
    json_results = []
    for r in results:
        jr = {k: v for k, v in r.items() if k != "report_full"}
        jr["report_excerpt"] = r["report_full"][:500] + "..."
        json_results.append(jr)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "test": "rce_fresh_test",
            "timestamp": timestamp,
            "sources": ["openalex", "arxiv", "s2"],
            "topics": TOPICS,
            "papers_per_source": PAPERS_PER_SOURCE,
            "year_from": YEAR_FROM,
            "results": json_results,
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n  Results saved to: {output_file}")
    
    # Save full reports
    for r in results:
        safe_name = r["topic"].replace(" ", "_").replace("/", "_")[:40]
        report_file = output_dir / f"report_{safe_name}_{timestamp}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"# {r['r4']['report_title']}\n\n")
            f.write(f"**Topic:** {r['topic']}\n")
            f.write(f"**Papers analyzed:** {r['num_papers']}\n")
            f.write(f"**Sources:** OpenAlex + arXiv + S2\n\n")
            f.write(r["report_full"])
        print(f"  Report saved: {report_file}")
    
    print(f"\n{'='*70}")
    print("DONE")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
