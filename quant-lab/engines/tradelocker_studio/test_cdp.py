"""Quick test: connect to Studio via CDP and check if automation works."""
import json, http.client, websocket

# 1. Get studio target
conn = http.client.HTTPConnection('localhost', 9222)
conn.request('GET', '/json/list')
resp = conn.getresponse()
targets = json.loads(resp.read())
conn.close()

studio = [t for t in targets if 'studio' in t.get('url','')][0]
print('Studio:', studio['title'], studio['url'])

# 2. Connect via WebSocket (suppress Origin header)
ws = websocket.create_connection(studio['webSocketDebuggerUrl'], timeout=30, origin='')

# 3. Enable Runtime
ws.send(json.dumps({'id':1, 'method':'Runtime.enable'}))
r = json.loads(ws.recv())
print('Runtime.enable:', r.get('result', r))

# 4. Check isTradeLockerStudioEnabled
ws.send(json.dumps({'id':2, 'method':'Runtime.evaluate', 'params':{'expression':'window.isTradeLockerStudioEnabled', 'returnByValue':True}}))
r = json.loads(ws.recv())
val = r.get('result',{}).get('result',{}).get('value')
print('isTradeLockerStudioEnabled:', val)

# 5. Check monaco
ws.send(json.dumps({'id':3, 'method':'Runtime.evaluate', 'params':{'expression':'window.monaco ? "monaco found" : "no monaco"', 'returnByValue':True}}))
r = json.loads(ws.recv())
val = r.get('result',{}).get('result',{}).get('value')
print('monaco:', val)

# 6. Get current editor code length
ws.send(json.dumps({'id':4, 'method':'Runtime.evaluate', 'params':{'expression':'''
(() => {
    const editors = window.monaco && window.monaco.editor.getEditors();
    if (editors && editors.length > 0) {
        const val = editors[0].getValue();
        return val.length + ' chars: ' + val.substring(0, 100);
    }
    return 'no editor content';
})()
''', 'returnByValue':True}}))
r = json.loads(ws.recv())
val = r.get('result',{}).get('result',{}).get('value')
print('editor content:', val)

# 7. Test writing code
test_code = '# Test write\nimport backtrader as bt\nprint("CDP write works!")'
escaped = json.dumps(test_code)
ws.send(json.dumps({'id':5, 'method':'Runtime.evaluate', 'params':{'expression':f'''
(() => {{
    const editors = window.monaco && window.monaco.editor.getEditors();
    if (!editors || editors.length === 0) return 'no editor';
    editors[0].getModel().setValue({escaped});
    return 'written: ' + editors[0].getValue().length;
}})()
''', 'returnByValue':True}}))
r = json.loads(ws.recv())
val = r.get('result',{}).get('result',{}).get('value')
print('write test:', val)

# 8. Check buttons
ws.send(json.dumps({'id':6, 'method':'Runtime.evaluate', 'params':{'expression':'''
(() => {
    const buttons = document.querySelectorAll('button');
    return Array.from(buttons).map(b => b.textContent.trim()).filter(t => t.length > 0 && t.length < 50);
})()
''', 'returnByValue':True}}))
r = json.loads(ws.recv())
val = r.get('result',{}).get('result',{}).get('value')
print('buttons:', val)

ws.close()
print('\nDone!')
