#!/usr/bin/env python3
"""Quick test of OCE backend + Event Fabric integration."""

import urllib.request
import json
import sys

BASE = 'http://127.0.0.1:8000'

def call(method, path, body=None):
    url = f'{BASE}{path}'
    data = json.dumps(body).encode() if body else None
    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}

print('=== OCE Integration Test ===\n')

# 1. Health
r = call('GET', '/health')
print(f'1. Health: {r}')

# 2. SRRA-OPH health
r = call('GET', '/health/srrs')
print(f'2. SRRA-OPH: status={r.get("status")}, patches={r.get("total_patches")}')

# 3. Event stats (before)
r = call('GET', '/events/stats')
print(f'3. Stats (before): ingested={r.get("total_ingested")}, history={r.get("history_size")}')

# 4. Ingest test event
r = call('POST', '/events/ingest', {
    'event_type': 'operator.command.executed',
    'source': 'pm-integration-test',
    'payload': {'command': 'test-ingest', 'success': True, 'duration_ms': 42}
})
print(f'4. Ingest: {r}')

# 5. Ingest another
r = call('POST', '/events/ingest', {
    'event_type': 'operator.vscode.file_opened',
    'source': 'pm-integration-test',
    'payload': {'file': 'test.py', 'line': 10}
})
print(f'5. Ingest: {r}')

# 6. Event stats (after)
r = call('GET', '/events/stats')
print(f'6. Stats (after): ingested={r.get("total_ingested")}, history={r.get("history_size")}')
print(f'   By type: {r.get("events_by_type")}')
print(f'   By source: {r.get("events_by_source")}')

# 7. Query events
r = call('GET', '/events?limit=5')
print(f'7. Events query: {len(r)} events')
for e in r[:3]:
    print(f'   - [{e["priority"]}] {e["event_type"]} from {e["source"]}')

# 8. Filter by type
r = call('GET', '/events?event_type=operator.command.executed&limit=5')
print(f'8. Filtered (operator.command.executed): {len(r)} events')

# 9. Event types
r = call('GET', '/events/types')
print(f'9. Event types: {len(r)} registered')

# 10. Observer status
r = call('GET', '/observers')
print(f'10. Observers: {len(r)} active')
for o in r[:3]:
    print(f'    - {o["observer_id"]}: {o["state"]} (entropy: {o["entropy"]})')

# 11. Attractor state
r = call('GET', '/attractor')
print(f'11. Attractor: {r}')

# 12. Memory view
r = call('GET', '/memory')
print(f'12. Memory: trajectory={len(r.get("trajectory_memory", []))}, structural={len(r.get("structural_memory", []))}')

print('\n=== All tests complete ===')
