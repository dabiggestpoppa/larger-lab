"""Quick test for arXiv category-only search."""
import asyncio
import sys
sys.path.insert(0, '.')

from core.research.ingestion.arxiv_client import ArxivClient

async def test():
    async with ArxivClient(timeout=30) as client:
        # Test: just finance categories, no text filter
        cats = ["q-fin.TR", "q-fin.ST", "q-fin.RM"]
        all_papers = []
        seen_ids = set()
        
        for cat in cats:
            papers = await client.search_by_category(cat, max_results=5)
            for p in papers:
                if p.id not in seen_ids:
                    seen_ids.add(p.id)
                    all_papers.append(p)
        
        print(f"Total from {len(cats)} categories: {len(all_papers)} papers")
        for p in all_papers[:10]:
            print(f"  {p.title[:80]}")

asyncio.run(test())
