"""
Autonomous research cycle: Riemann-Roch Theorem and AI.
Run: python tools/run_riemann_roch_cycle.py
"""
import asyncio, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.research.ingestion.openalex_client import OpenAlexClient
from core.research.ingestion.cache import Cache
from core.research.distillation.distiller import Distiller
from core.research.distillation.vault_writer import VaultWriter
from core.research.ingestion.models import Paper

async def main():
    print("=" * 70)
    print("AUTONOMOUS RESEARCH CYCLE: RIEMANN-ROCH THEOREM AND AI")
    print("=" * 70)
    
    client = OpenAlexClient()
    
    # Step 1: Search
    print("\n[1/4] Searching OpenAlex...")
    queries = [
        "riemann roch theorem",
        "riemann roch theorem machine learning",
        "riemann roch theorem neural networks",
        "riemann roch theorem artificial intelligence",
        "riemann roch algebraic geometry AI",
    ]
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
    
    # Filter for Riemann-Roch relevance
    rr = [p for p in papers if "riemann" in p.title.lower() or "riemann" in (p.abstract or "").lower() or "roch" in p.title.lower()]
    print(f"  Riemann-Roch relevant: {len(rr)}")
    if len(rr) < 3:
        rr = papers[:10]
    
    # Step 2: Cache
    print("\n[2/4] Caching...")
    cache = Cache()
    new = 0
    for p in rr:
        try:
            cache.write(p)
            new += 1
        except Exception:
            pass
    print(f"  Cached {new} new papers")
    
    # Step 3: Distill + Write
    print("\n[3/4] Distilling + writing to vault...")
    distiller = Distiller()
    writer = VaultWriter()
    distilled = 0
    for paper in rr[:5]:
        note = distiller.distill(paper)
        if note:
            try:
                ok, path = writer.write(paper, note)
                if ok:
                    distilled += 1
                    print(f"  OK: {paper.title[:60]}")
            except Exception as e:
                print(f"  FAIL: {paper.title[:40]}... ({e})")
    print(f"  Distilled {distilled} papers")
    
    # Step 4: Results
    print("\n[4/4] Research Results:")
    print("=" * 70)
    for i, p in enumerate(rr[:5], 1):
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
    for vf in vault_files:
        print(f"  {vf.relative_to(vault_dir.parent)}")
    
    # Summary
    print("\n" + "=" * 70)
    print("CYCLE COMPLETE")
    print(f"  Papers found: {len(papers)}")
    print(f"  Riemann-Roch relevant: {len(rr)}")
    print(f"  Distilled to vault: {distilled}")
    print(f"  Search queries: {len(queries)}")
    print(f"  Data source: OpenAlex API (live)")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())