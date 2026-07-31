"""
Run exactly 2 LLM-distilled papers to vault.
"""
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.research.ingestion.openalex_client import OpenAlexClient
from core.research.ingestion.cache import Cache
from core.research.distillation.llm_distill import LLMDistiller
from core.research.distillation.vault_writer import VaultWriter

async def main():
    print("=" * 70)
    print("LLM DISTILLATION - 2 PAPERS")
    print("=" * 70)
    
    client = OpenAlexClient()
    
    # Get 2 papers on causal inference
    print("\n[1/3] Searching for causal inference papers...")
    papers = await client.search(query="causal inference multi-agent systems", per_page=2)
    print(f"  Found {len(papers)} papers")
    
    # Cache
    print("\n[2/3] Caching...")
    cache = Cache()
    for p in papers:
        cache.write(p)
    print(f"  Cached")
    
    # LLM Distill + Write
    print("\n[3/3] LLM Distilling + writing...")
    distiller = LLMDistiller()
    writer = VaultWriter()
    
    for paper in papers:
        print(f"\n  Paper: {paper.title[:60]}")
        note = await distiller.distill(paper)
        if note:
            ok, path = writer.write(paper, note)
            print(f"  Vault write: {'OK' if ok else 'FAIL'}")
            print(f"\n  LLM OUTPUT PREVIEW:\n  {note[:300]}...")
        else:
            print("  LLM returned None")
    
    print(f"\n  Status: {distiller.get_status()}")
    
    # Final count
    vault_dir = Path(r"C:\Users\wifik\Downloads\o2c\research\papers")
    total = len(list(vault_dir.rglob("*.md")))
    print(f"\n  Total papers in vault: {total}")

if __name__ == "__main__":
    asyncio.run(main())