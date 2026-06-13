"""Full RCE pipeline test with LLM-powered reasoning."""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.research.cognition import MultiSourceFetcher
from core.research.cognition.llm_reasoning import LLMReasoning

TOPICS = [
    "transfer entropy financial markets systemic risk contagion",
    "geopolitical risk emerging markets capital flows financial crisis",
]

Papers_PER_SOURCE = 5  # Reduced for speed
YEAR_FROM = 2016


async def main():
    print("=" * 70)
    print("RCE FULL PIPELINE TEST — LLM-Powered Reasoning")
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)
    
    # Fetch papers from all 3 sources
    fetcher = MultiSourceFetcher()
    llm = LLMReasoning()
    
    all_papers = {}
    for topic in TOPICS:
        print(f"\n{'='*70}")
        print(f"FETCHING: {topic}")
        print(f"{'='*70}")
        
        papers = await fetcher.fetch_papers(
            query=topic,
            per_source=Papers_PER_SOURCE,
            year_from=YEAR_FROM,
        )
        
        all_papers[topic] = papers
        
        sources = {}
        for p in papers:
            src = p.source
            sources[src] = sources.get(src, 0) + 1
        
        print(f"  Total unique papers: {len(papers)}")
        for src, count in sorted(sources.items()):
            print(f"    {src}: {count}")
        for p in papers[:5]:
            print(f"  [{p.source}] {p.title[:70]}")
    
    # Run LLM-powered RCE pipeline on each topic
    for topic in TOPICS:
        papers = all_papers[topic]
        if len(papers) < 2:
            print(f"\n  ⚠️  Only {len(papers)} papers for '{topic}' — skipping")
            continue
        
        print(f"\n{'='*70}")
        print(f"RCE PIPELINE (LLM): {topic}")
        print(f"{'='*70}")
        
        # Convert papers to dicts for the LLM
        paper_dicts = []
        for p in papers:
            text = p.abstract or p.title
            if p.concepts:
                concept_text = ", ".join(c.name for c in p.concepts[:5])
                text = f"{text}. Key concepts: {concept_text}"
            paper_dicts.append({
                "text": text,
                "title": p.title,
                "id": p.id,
                "source": p.source,
                "year": str(p.year),
                "doi": p.doi,
            })
        
        # Run full pipeline
        results = await llm.run_full_pipeline(topic, paper_dicts)
        
        # Print results
        r1 = results["r1"]
        r3 = results["r3"]
        r4 = results["r4"]
        r5 = results["r5"]
        
        print(f"\n  R1: {len(r1)} knowledge objects extracted")
        if isinstance(r1, list) and r1:
            first = r1[0]
            claims = first.get("main_claims", [])
            mechanisms = first.get("mechanisms", [])
            print(f"    First paper: {len(claims)} claims, {len(mechanisms)} mechanisms")
            for c in claims[:2]:
                print(f"      Claim: {c.get('claim', '')[:80]}...")
        
        print(f"\n  R3: {len(r3.get('contradictions', []))} contradictions, "
              f"{len(r3.get('consensus', []))} consensus areas")
        print(f"    Landscape: {r3.get('unified_reasoning', {}).get('landscape', '?')}")
        
        print(f"\n  R4: Confidence: {r4.get('confidence', 0):.3f}")
        report = r4.get("research_report", {})
        print(f"    Report: {report.get('title', '?')}")
        print(f"    Word count: {report.get('word_count', 0)}")
        
        theory = r4.get("unified_theory", {})
        print(f"    Theory: {theory.get('statement', '')[:120]}...")
        
        print(f"\n  R5: Passed: {r5.get('passed', False)}")
        metrics = r5.get("metrics", {})
        for k, v in metrics.items():
            if isinstance(v, float):
                print(f"    {k}: {v:.3f}")
        
        # Save report
        output_dir = PROJECT_ROOT / "data" / "rce_llm_results"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        
        report_text = report.get("full_report", "")
        report_file = output_dir / f"report_{topic[:40].replace(' ', '_')}_{timestamp}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"# {report.get('title', 'Research Report')}\n\n")
            f.write(f"**Topic:** {topic}\n")
            f.write(f"**Papers analyzed:** {len(papers)}\n")
            f.write(f"**Sources:** OpenAlex + arXiv + S2\n\n")
            f.write(report_text)
        print(f"\n  Report saved: {report_file}")
    
    print(f"\n{'='*70}")
    print("DONE")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
