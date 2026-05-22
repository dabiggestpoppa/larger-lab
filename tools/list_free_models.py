import urllib.request, json, datetime

url = 'https://openrouter.ai/api/v1/models'
req = urllib.request.Request(url)
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())

free = []
for m in data['data']:
    mid = m['id']
    if ':free' in mid:
        ctx = m.get('context_length', 0)
        created = m.get('created', 0)
        free.append({
            'id': mid,
            'name': m['name'],
            'ctx': ctx,
            'created': created,
        })

free.sort(key=lambda x: x['created'], reverse=True)

print(f'Found {len(free)} free models\n')
print('=== TOP 25 NEWEST FREE MODELS ===')
for m in free[:25]:
    dt = datetime.datetime.fromtimestamp(m['created']).strftime('%Y-%m-%d') if m['created'] else '?'
    ctx_k = m['ctx'] // 1000 if m['ctx'] else 0
    mid = m['id'][:48]
    print(f"{mid:50s} {dt:12s} {ctx_k:6d}K  {m['name']}")
