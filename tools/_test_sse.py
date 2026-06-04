import requests, json

# Test exactly what the frontend receives through Next.js proxy
r = requests.post('http://localhost:3000/api/chat/stream',
    json={'message': 'run git log --oneline -3 and tell me the latest commits'},
    timeout=120, stream=True)
print('Status:', r.status_code)
print('Content-Type:', r.headers.get('content-type', ''))
print()

count = 0
for line in r.iter_lines():
    if line:
        d = line.decode('utf-8') if isinstance(line, bytes) else line
        print(f'RAW LINE [{count}]: {repr(d)[:200]}')
        if d.startswith('data: '):
            data = d[6:].strip()
            try:
                evt = json.loads(data)
                etype = evt.get('type', '?')
                edata = evt.get('data', {})
                if etype == 'round':
                    print(f'  [ROUND] {edata}')
                elif etype == 'tool_call':
                    print(f'  [TOOL_CALL] tool={edata.get("tool")} args={str(edata.get("args", {}))[:100]}')
                elif etype == 'tool_result':
                    print(f'  [TOOL_RESULT] tool={edata.get("tool")} result_len={len(str(edata.get("result", "")))}')
                elif etype == 'final':
                    print(f'  [FINAL] response_len={len(str(edata.get("response", "")))}')
                elif etype == 'error':
                    print(f'  [ERROR] {edata}')
                count += 1
            except Exception as e:
                print(f'  [PARSE_ERR] {e}')
        elif d.startswith(': '):
            print(f'  [KEEPALIVE]')

print(f'\nTotal data events: {count}')
