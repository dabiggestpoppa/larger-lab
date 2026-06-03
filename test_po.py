"""Quick test of PO chat agent."""
import os, sys, time
sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
from core.observer.chat_agent import ChatAgent
from core.observer.sovereign_field import SovereignField

agent = ChatAgent(); sov = SovereignField()
msg = 'AYE YOU BACK UP? Short answer.'
ctx = sov.get_sovereign_context()
print(f'Context: {len(ctx)} chars')
print(f'API key: {agent.api_key[:8]}...')
print(f'Model: {agent.current_model}')
print('Calling...')
start = time.time()
resp = agent.chat(msg, sovereign_context=ctx)
elapsed = time.time() - start
print(f'Done in {elapsed:.1f}s')
print(f'Response:\n{resp[:500] if resp else "NONE"}')
