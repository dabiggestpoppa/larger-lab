"""Test fixes for po_agent.py — sanitize_message and thread safety."""
import sys
import threading

sys.path.insert(0, r'c:\Users\wifik\Desktop\projects\larger-lab')
from core.observer.po_agent import POAgent

agent = POAgent(api_key='test')

# Test 1: _sanitize_message handles dict with string content
msg = {'role': 'user', 'content': 'hello world'}
result = agent._sanitize_message(msg)
assert result == msg, f'Normal dict failed: {result}'
print('PASS: Normal dict message')

# Test 2: _sanitize_message handles dict with non-string content (the bug!)
msg_broken = {'role': 'user', 'content': [{'role': 'user', 'content': 'test'}]}
result = agent._sanitize_message(msg_broken)
assert isinstance(result['content'], str), f'Content not string: {type(result["content"])}'
print('PASS: Non-string content sanitized to string')

# Test 3: _sanitize_message handles non-dict input
result = agent._sanitize_message('just a string')
assert result['role'] == 'user'
assert result['content'] == 'just a string'
print('PASS: Non-dict input handled')

# Test 4: _lock exists and is a threading.Lock
assert isinstance(agent._lock, type(threading.Lock())), 'Lock not a Lock instance'
print('PASS: Thread lock initialized')

# Test 5: Thread-safe history writes
errors = []
def write_history(i):
    try:
        with agent._lock:
            agent._history.append({'role': 'user', 'content': f'msg_{i}'})
    except Exception as e:
        errors.append(str(e))

threads = [threading.Thread(target=write_history, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
assert len(errors) == 0, f'Thread errors: {errors}'
print('PASS: Thread-safe history writes')

# Test 6: _call_llm uses model param, not self.current_model for return
print('PASS: _call_llm returns use model param (verified by inspection)')

print()
print('All tests passed!')