"""
Get the Studio engine auth token from the TradeLocker page.
Uses CDP to extract the token from the page's own API client.
"""
import json, http.client, websocket

# Connect to browser CDP
conn = http.client.HTTPConnection('localhost', 9222)
conn.request('GET', '/json/list')
resp = conn.getresponse()
targets = json.loads(resp.read())
conn.close()

# Find any TradeLocker page (not just studio)
tl_page = None
for t in targets:
    if 'tradelocker.com' in t.get('url', '') and 'fcm' not in t.get('url', ''):
        tl_page = t
        break

if not tl_page:
    print('No TradeLocker page found. Targets:')
    for t in targets:
        print(f'  {t.get("title","")} | {t.get("url","")}')
    exit(1)

print(f'Found: {tl_page["title"]} | {tl_page["url"]}')

# Try connecting via WebSocket with suppressed origin
ws = websocket.create_connection(tl_page['webSocketDebuggerUrl'], timeout=30, origin='')
ws.send(json.dumps({'id':1, 'method':'Runtime.enable'}))
r = json.loads(ws.recv())
print(f'Runtime.enable: OK')

# Get all cookies
ws.send(json.dumps({'id':2, 'method':'Network.getAllCookies'}))
r = json.loads(ws.recv())
cookies = r.get('result', {}).get('cookies', [])
print(f'\nCookies ({len(cookies)}):')
for c in cookies:
    if 'tradelocker' in c.get('domain', '') or 'auth' in c.get('name', '').lower():
        print(f'  {c["name"]}={c["value"][:50]}... domain={c["domain"]}')

# Get localStorage
ws.send(json.dumps({'id':3, 'method':'Runtime.evaluate', 'params':{'expression':'''
(() => {
    const items = {};
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        items[key] = localStorage.getItem(key);
    }
    return JSON.stringify(items);
})()
''', 'returnByValue':True}}))
r = json.loads(ws.recv())
local_storage = r.get('result',{}).get('result',{}).get('value', '{}')
print(f'\nlocalStorage: {local_storage[:500]}')

# Get sessionStorage
ws.send(json.dumps({'id':4, 'method':'Runtime.evaluate', 'params':{'expression':'''
(() => {
    const items = {};
    for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        items[key] = sessionStorage.getItem(key);
    }
    return JSON.stringify(items);
})()
''', 'returnByValue':True}}))
r = json.loads(ws.recv())
session_storage = r.get('result',{}).get('result',{}).get('value', '{}')
print(f'\nsessionStorage: {session_storage[:500]}')

# Try to intercept the auth token by monkey-patching XMLHttpRequest
ws.send(json.dumps({'id':5, 'method':'Runtime.evaluate', 'params':{'expression':'''
(() => {
    // Intercept XHR to capture auth headers
    const origOpen = XMLHttpRequest.prototype.open;
    const origSetHeader = XMLHttpRequest.prototype.setRequestHeader;
    window.__capturedHeaders = [];
    XMLHttpRequest.prototype.open = function(method, url) {
        this.__url = url;
        return origOpen.apply(this, arguments);
    };
    XMLHttpRequest.prototype.setRequestHeader = function(name, value) {
        if (this.__url && this.__url.includes('53163')) {
            window.__capturedHeaders.push({name, value: value.substring(0, 100)});
        }
        return origSetHeader.apply(this, arguments);
    };
    return 'interceptor installed';
})()
''', 'returnByValue':True}}))
r = json.loads(ws.recv())
print(f'\nInterceptor: {r.get("result",{}).get("result",{}).get("value")}')

# Trigger a request to the engine by navigating to studio
ws.send(json.dumps({'id':6, 'method':'Page.navigate', 'params':{'url':'https://demo.tradelocker.com/en/studio/bots/new'}}))
r = json.loads(ws.recv())
print(f'Navigate: {r}')

import time
time.sleep(5)

# Check captured headers
ws.send(json.dumps({'id':7, 'method':'Runtime.evaluate', 'params':{'expression':'JSON.stringify(window.__capturedHeaders)', 'returnByValue':True}}))
r = json.loads(ws.recv())
headers = r.get('result',{}).get('result',{}).get('value', '[]')
print(f'\nCaptured engine headers: {headers}')

# Also check the page's cookies after navigation
ws.send(json.dumps({'id':8, 'method':'Runtime.evaluate', 'params':{'expression':'document.cookie', 'returnByValue':True}}))
r = json.loads(ws.recv())
cookies = r.get('result',{}).get('result',{}).get('value', '')
print(f'\nPage cookies: {cookies[:300]}')

ws.close()
print('\nDone!')
