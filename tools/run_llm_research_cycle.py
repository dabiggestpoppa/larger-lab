"""
LLM-powered research cycle: Uses Nemotron for paper distillation.
Run: python tools/run_llm_research_cycle.py
"""
import asyncio, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.research.ingestion.openalex_client import OpenAlexClient
from core.research.ingestion.cache import Cache
from core.research.distillation.llm_distill import LLMDistiller
from core.research.distillation.vault_writer import VaultWriter
from core.research.ingestion.models import Paper

async def run_llm_cycle(topic: str, queries: list[str]):
    print("=" * 70)
    print(f"LLM RESEARCH CYCLE: {topic}")
    print("=" * 70)
    
    client = OpenAlexClient()
    
    # Step 1: Search
    print("\n[1/4] Searching OpenAlex...")
    all_papers = []
    for q in queries:
        papers = await client.search(query=q, per_page=10)
        print(f"  '{q}': {len(papers)} papers")
        all_papers += papers
    
    seen = set()
    unique = []
    for p in all_papers:
        key = p.doi or p.id
        if key not in seen:
            seen.add(key)
            unique.append(p)
    papers = unique
    print(f"  Total unique: {len(papers)}")
    
    # Step 2: Cache
    print("\n[2/4] Caching...")
    cache = Cache()
    new = 0
    for p in papers:
        try:
            cache.write(p)
            new += 1
        except Exception:
            pass
    print(f"  Cached {new} new papers")
    
    # Step 3: LLM Distill + Write
    print("\n[3/4] LLM Distilling + writing to vault...")
    distiller = LLMDistiller()
    writer = VaultWriter()
    distilled = 0
    for paper in papers[:5]:
        note = await distiller.distill(paper)
        if note:
            try:
                ok, path = writer.write(paper, note)
                if ok:
                    distilled += 1
                    print(f"  OK: {paper.title[:60]}")
            except Exception as e:
                print(f"  FAIL: {paper.title[:40]}... ({e})")
        else:
            print(f"  SKIP: {paper.title[:40]}... (LLM unavailable)")
    print(f"  Distilled {distilled} papers")
    
    # Step 4: Results
    print("\n[4/4] Research Results:")
    print("=" * 70)
    for i, p in enumerate(papers[:5], 1):
        print(f"\n{i}. {p.title}")
        if p.authors:
            print(f"   Authors: {p.first_author}")
        print(f"   Year: {p.year} | Citations: {p.citation_count}")
        if p.concepts:
            print(f"   Concepts: {[c.name for c in p.concepts[:5]]}")
        if p.abstract:
            print(f"   Abstract: {p.abstract[:200]}...")
    
    # Check vault
    vault_dir = Path(r"C:\Users\wifik\Downloads\o2c\research\papers")
    vault_files = list(vault_dir.rglob("*.md")) if vault_dir.exists() else []
    print(f"\n--- Vault: {len(vault_files)} paper notes written ---")
    
    # Summary
    print("\n" + "=" * 70)
    print("CYCLE COMPLETE")
    print(f"  Papers found: {len(papers)}")
    print(f"  Distilled to vault: {distilled}")
    print(f"  Search queries: {len(queries)}")
    print(f"  Data source: OpenAlex API (live)")
    print(f"  LLM model: nvidia/nemotron-3-ultra-550b-a55b:free")


async def main():
    # Run 2 cycles - topics can be customized
    topics = [
        ("Neural-Symbolic Integration", [
            "neural symbolic integration",
            "neural symbolic reasoning",
            "symbolic neural networks",
            "neural symbolic AI",
            "symbolic reasoning neural networks",
        ]),
        ("Causal Inference for Agents", [
            "causal inference multi-agent",
            "causal discovery agents",
            "causal reasoning AI systems",
            "causal inference reinforcement learning",
            "agent causal models",
        ]),
    ]
    
    for topic, queries in topics:
        await run_llm_cycle(topic, queries)
        print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())