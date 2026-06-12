"""Check what buttons are visible in Studio."""
import json, http.client, websocket

conn = http.client.HTTPConnection('localhost', 9222)
conn.request('GET', '/json/list')
resp = conn.getresponse()
targets = json.loads(resp.read())
conn.close()

studio = [t for t in targets if 'studio' in t.get('url','')][0]
ws = websocket.create_connection(studio['webSocketDebuggerUrl'], timeout=30, origin='')

# Enable runtime
ws.send(json.dumps({'id':1, 'method':'Runtime.enable'}))
ws.recv()

# Get all buttons with their text
ws.send(json.dumps({'id':2, 'method':'Runtime.evaluate', 'params':{'expression':'''
(() => {
    const buttons = document.querySelectorAll('button');
    const result = [];
    for (const btn of buttons) {
        const text = btn.textContent.trim();
        if (text.length > 0 && text.length < 80) {
            const cls = btn.className;
            const style = window.getComputedStyle(btn);
            const visible = style.display !== 'none' && style.visibility !== 'hidden';
            result.push({
                text: text,
                class: (cls || '').substring(0, 60),
                visible: visible
            });
        }
    }
    return result;
})()
''', 'returnByValue':True}}))
r = json.loads(ws.recv())
buttons = r.get('result',{}).get('result',{}).get('value', [])

print(f'Found {len(buttons)} buttons:')
for b in buttons:
    vis = 'V' if b['visible'] else 'H'
    print(f'  [{vis}] "{b["text"]}" class={b["class"][:40]}')

ws.close()
