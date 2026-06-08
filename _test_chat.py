import requests, json

print('Testing /api/chat/stream...')
try:
    r = requests.post('http://localhost:8000/api/chat/stream',
        json={'message': 'hello', 'stream': True},
        stream=True, timeout=60)
    print('Status:', r.status_code)

    count = 0
    final_received = False
    for line in r.iter_lines():
        if line:
            line_str = line.decode('utf-8') if isinstance(line, bytes) else line
            if line_str.startswith('data: '):
                data = json.loads(line_str[6:])
                etype = data.get('type', '?')
                edata = data.get('data', {})
                if etype == 'round':
                    print(f'  ROUND {edata.get("round", "?")}/{edata.get("max", "?")}')
                elif etype == 'tool_call':
                    print(f'  TOOL: {edata.get("tool")}')
                elif etype == 'tool_result':
                    result = (edata.get('result') or '')[:60]
                    print(f'  RESULT: {edata.get("tool")}: {result}')
                elif etype == 'complete':
                    print(f'  COMPLETE')
                elif etype == 'final':
                    resp = (edata.get('response') or '')[:200]
                    print(f'  FINAL: {resp}')
                    final_received = True
                elif etype == 'error':
                    print(f'  ERROR: {edata.get("message", "")[:200]}')
                elif etype == 'max_rounds':
                    print(f'  MAX ROUNDS')
            count += 1
            if final_received:
                break

    if not final_received:
        print('NO FINAL RESPONSE RECEIVED')
except requests.exceptions.Timeout:
    print('TIMEOUT after 60s')
except Exception as e:
    print('Error:', type(e).__name__, e)
