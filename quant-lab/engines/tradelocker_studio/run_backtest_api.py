"""
Run TradeLocker Studio backtest via the Studio engine REST API.
Uses the same auth token the page uses (extracted from network traffic).
"""
import json, http.client, websocket

# ── Step 1: Get auth token from the page ──
conn = http.client.HTTPConnection('localhost', 9222)
conn.request('GET', '/json/list')
resp = conn.getresponse()
targets = json.loads(resp.read())
conn.close()

studio = [t for t in targets if 'studio' in t.get('url','')][0]
ws = websocket.create_connection(studio['webSocketDebuggerUrl'], timeout=30, origin='')
ws.send(json.dumps({'id':1, 'method':'Runtime.enable'}))
ws.recv()

# Get the auth token from the page's own API client
# The page stores the token in its React state or we can get it from the cookie
ws.send(json.dumps({'id':2, 'method':'Runtime.evaluate', 'params':{'expression':'''
(() => {
    // The page's API client uses a token — let's check localStorage and sessionStorage
    const allStorage = {};
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.toLowerCase().includes('token') || key.toLowerCase().includes('auth') || key.toLowerCase().includes('session')) {
            allStorage[key] = localStorage.getItem(key);
        }
    }
    for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key.toLowerCase().includes('token') || key.toLowerCase().includes('auth')) {
            allStorage[key] = sessionStorage.getItem(key);
        }
    }
    return allStorage;
})()
''', 'returnByValue':True}}))
r = json.loads(ws.recv())
tokens = r.get('result',{}).get('result',{}).get('value', {})
print('Storage tokens:', json.dumps(tokens, indent=2, default=str)[:500])

# Get cookies
ws.send(json.dumps({'id':3, 'method':'Runtime.evaluate', 'params':{'expression':'''
(async () => {
    // The page uses cookies for auth to the engine
    // Let's check what headers the page sends to the engine
    const resp = await fetch('http://localhost:60370/health/liveness', {credentials: 'include'});
    const text = await resp.text();
    return {status: resp.status, body: text};
})()
''', 'returnByValue':True, 'awaitPromise':True}}))
r = json.loads(ws.recv())
health = r.get('result',{}).get('result',{}).get('value', {})
print('Engine health:', health)

# Try to get project info via the page's own fetch context
ws.send(json.dumps({'id':4, 'method':'Runtime.evaluate', 'params':{'expression':'''
(async () => {
    try {
        const resp = await fetch('http://localhost:60370/project/244fb7b9-a858-43d0-a25f-9941d88338fe', {
            credentials: 'include',
            headers: {'Content-Type': 'application/json'}
        });
        const data = await resp.json();
        return data;
    } catch(e) {
        return {error: e.message};
    }
})()
''', 'returnByValue':True, 'awaitPromise':True}}))
r = json.loads(ws.recv())
project = r.get('result',{}).get('result',{}).get('value', {})
print('Project info:', json.dumps(project, indent=2, default=str)[:500])

# Try to get file content
ws.send(json.dumps({'id':5, 'method':'Runtime.evaluate', 'params':{'expression':'''
(async () => {
    try {
        const resp = await fetch('http://localhost:60370/file/6446491b-f0ac-4b05-abb0-b2389e4a0daf/content', {
            credentials: 'include'
        });
        const data = await resp.json();
        return data;
    } catch(e) {
        return {error: e.message};
    }
})()
''', 'returnByValue':True, 'awaitPromise':True}}))
r = json.loads(ws.recv())
file_data = r.get('result',{}).get('result',{}).get('value', {})
print('File content:', json.dumps(file_data, indent=2, default=str)[:500])

# Try to get all projects
ws.send(json.dumps({'id':6, 'method':'Runtime.evaluate', 'params':{'expression':'''
(async () => {
    try {
        const resp = await fetch('http://localhost:60370/all_projects?create_if_empty=false', {
            credentials: 'include'
        });
        const data = await resp.json();
        return data;
    } catch(e) {
        return {error: e.message};
    }
})()
''', 'returnByValue':True, 'awaitPromise':True}}))
r = json.loads(ws.recv())
projects = r.get('result',{}).get('result',{}).get('value', {})
print('All projects:', json.dumps(projects, indent=2, default=str)[:500])

ws.close()
