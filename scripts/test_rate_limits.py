"""Test rate limits for S2 and OpenRouter."""
import asyncio
import sys
import os

sys.path.insert(0, '.')

async def test_s2():
    from core.research.ingestion.s2_client import S2Client
    async with S2Client(timeout=30) as client:
        try:
            papers = await client.search_by_query('geopolitical risk emerging markets', limit=3)
            print(f'S2: OK - {len(papers)} papers returned')
            for p in papers[:2]:
                print(f'  {p.title[:60]}')
        except Exception as e:
            print(f'S2: FAILED - {e}')

async def test_openrouter():
    from core.spawn.openrouter_gateway import OpenRouterGateway
    gw = OpenRouterGateway()
    
    # Test nemotron
    try:
        r = await gw.complete('Say hello in one word.', max_tokens=10, model='nvidia/nemotron-3-ultra-550b-a55b:free')
        print(f'OpenRouter nemotron: OK - "{r}"')
    except Exception as e:
        print(f'OpenRouter nemotron: FAILED - {str(e)[:200]}')
    
    # Test nex-n2-pro
    try:
        r2 = await gw.complete('Say hello in one word.', max_tokens=10, model='nex-agi/nex-n2-pro:free')
        print(f'OpenRouter nex-n2-pro: OK - "{r2}"')
    except Exception as e:
        print(f'OpenRouter nex-n2-pro: FAILED - {str(e)[:200]}')

    # Test owl-alpha
    try:
        r3 = await gw.complete('Say hello in one word.', max_tokens=10, model='openrouter/owl-alpha')
        print(f'OpenRouter owl-alpha: OK - "{r3}"')
    except Exception as e:
        print(f'OpenRouter owl-alpha: FAILED - {str(e)[:200]}')

async def test_openrouter_concurrent():
    """Test if concurrent calls cause rate limiting."""
    from core.spawn.openrouter_gateway import OpenRouterGateway
    gw = OpenRouterGateway()
    
    print('\n--- Concurrent test (3 parallel calls) ---')
    tasks = [
        gw.complete(f'Count to {i}.', max_tokens=20, model='nvidia/nemotron-3-ultra-550b-a55b:free')
        for i in range(1, 4)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            print(f'  Call {i+1}: FAILED - {str(r)[:150]}')
        else:
            print(f'  Call {i+1}: OK - "{r[:50]}"')

async def main():
    print('=== S2 Rate Limit Test ===')
    await test_s2()
    
    print('\n=== OpenRouter Single Call Tests ===')
    await test_openrouter()
    
    await test_openrouter_concurrent()

asyncio.run(main())
