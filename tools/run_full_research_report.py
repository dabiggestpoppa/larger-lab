"""
Full Research Report Pipeline - End to end: Search → Distill → Report (PDF)
Run: python tools/run_full_research_report.py
"""
import asyncio, sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.research.ingestion.openalex_client import OpenAlexClient
from core.research.ingestion.cache import Cache
from core.research.distillation.llm_distill import LLMDistiller
from core.research.distillation.report_generator import ReportGenerator


async def main():
    print("=" * 70)
    print("FULL RESEARCH REPORT PIPELINE")
    print("=" * 70)

    topic = "Neural-Symbolic Integration for AI Agents"
    queries = [
        "neural symbolic integration",
        "neural symbolic reasoning",
        "symbolic neural networks",
    ]

    client = OpenAlexClient()
    cache = Cache()
    distiller = LLMDistiller()
    generator = ReportGenerator()

    # Step 1: Search
    print(f"\n[1/4] Searching for: {topic}")
    all_papers = []
    for q in queries:
        papers = await client.search(query=q, per_page=5)
        all_papers.extend(papers)
        print(f"  '{q}': {len(papers)} papers")

    # Deduplicate
    seen = set()
    papers = []
    for p in all_papers:
        key = p.doi or p.id
        if key not in seen:
            seen.add(key)
            papers.append(p)
    print(f"  Unique: {len(papers)}")

    # Step 2: Cache
    print("\n[2/4] Caching papers...")
    for p in papers:
        cache.write(p)
    print(f"  Cached {len(papers)} papers")

    # Step 3: LLM Distill
    print("\n[3/4] LLM Distilling papers...")
    notes = []
    for paper in papers[:5]:
        print(f"  Distilling: {paper.title[:50]}...")
        note = await distiller.distill(paper)
        if note:
            notes.append(note)
    print(f"  Distilled {len(notes)} papers")

    # Step 4: Generate PDF Report
    print("\n[4/4] Generating PDF report...")
    vault_root = Path(r"C:\Users\wifik\Downloads\o2c\research")
    output_path = vault_root / "reports" / f"neural_symbolic_integration_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.pdf"

    report_path = await generator.generate_report(topic, papers, notes, output_path)

    if report_path:
        print(f"\n✅ REPORT GENERATED: {report_path}")
        print(f"   File size: {output_path.stat().st_size} bytes")
    else:
        print("\n❌ Report generation failed")

    print(f"\n  Status: {distiller.get_status()}")


if __name__ == "__main__":
    asyncio.run(main())