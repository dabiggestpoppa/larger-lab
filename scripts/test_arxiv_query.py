"""Quick test for arXiv category-filtered search."""
import asyncio
import sys
sys.path.insert(0, '.')

from core.research.ingestion.arxiv_client import ArxivClient

async def test():
    async with ArxivClient(timeout=30) as client:
        # Test 1: Finance category + systemic risk
        q1 = '(cat:q-fin.TR+OR+cat:q-fin.ST+OR+cat:q-fin.RM)+AND+(abs:"systemic risk"+AND+abs:"contagion"+AND+abs:"entropy")'
        print(f'Query 1: {q1[:80]}...')
        papers1 = await client.search(q1, max_results=5)
        print(f'Results: {len(papers1)}')
        for p in papers1:
            print(f'  {p.title[:80]}')
        
        # Test 2: Economics + geopolitical
        q2 = '(cat:econ.GN+OR+cat:q-fin.EC)+AND+(abs:"geopolitical risk"+AND+abs:"emerging market"+AND+abs:"capital flow")'
        print(f'\nQuery 2: {q2[:80]}...')
        papers2 = await client.search(q2, max_results=5)
        print(f'Results: {len(papers2)}')
        for p in papers2:
            print(f'  {p.title[:80]}')

asyncio.run(test())
