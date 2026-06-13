"""Test S2 rate limit behavior."""
import asyncio
import sys
import os
import time

sys.path.insert(0, '.')

async def test_s2_wait_and_retry():
    """Test if S2 recovers after waiting."""
    from core.research.ingestion.s2_client import S2Client
    
    print('=== S2 Wait-and-Retry Test ===')
    
    # Try 1: immediate
    async with S2Client(timeout=30) as client:
        try:
            papers = await client.search_by_query('geopolitical risk', limit=2)
            print(f'  Attempt 1 (immediate): OK - {len(papers)} papers')
            return
        except Exception as e:
            print(f'  Attempt 1 (immediate): FAILED - {str(e)[:100]}')
    
    # Wait 10 seconds
    print('  Waiting 10s...')
    await asyncio.sleep(10)
    
    # Try 2: after 10s
    async with S2Client(timeout=30) as client:
        try:
            papers = await client.search_by_query('geopolitical risk', limit=2)
            print(f'  Attempt 2 (after 10s): OK - {len(papers)} papers')
            return
        except Exception as e:
            print(f'  Attempt 2 (after 10s): FAILED - {str(e)[:100]}')
    
    # Wait 30 seconds
    print('  Waiting 30s...')
    await asyncio.sleep(30)
    
    # Try 3: after 40s total
    async with S2Client(timeout=30) as client:
        try:
            papers = await client.search_by_query('geopolitical risk', limit=2)
            print(f'  Attempt 3 (after 40s): OK - {len(papers)} papers')
            return
        except Exception as e:
            print(f'  Attempt 3 (after 40s): FAILED - {str(e)[:100]}')

asyncio.run(test_s2_wait_and_retry())
