"""Find the Backtest button in TradeLocker Studio."""
import json, http.client, websocket

conn = http.client.HTTPConnection('localhost', 9222)
conn.request('GET', '/json/list')
resp = conn.getresponse()
targets = json.loads(resp.read())
conn.close()

studio = [t for t in targets if 'studio' in t.get('url','')][0]
ws = websocket.create_connection(studio['webSocketDebuggerUrl'], timeout=30, origin='')
ws.send(json.dumps({'id':1, 'method':'Runtime.enable'}))
ws.recv()

# 1. Get ALL clickable elements and their text
ws.send(json.dumps({'id':2, 'method':'Runtime.evaluate', 'params':{'expression':'''
(() => {
    // Get all elements that might be clickable
    const result = [];
    
    // Check all buttons
    document.querySelectorAll('button').forEach(el => {
        const text = el.textContent.trim();
        if (text.length > 0 && text.length < 100) {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0) {
                result.push({type: 'button', text: text, x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height)});
            }
        }
    });
    
    // Check tabs
    document.querySelectorAll('[role="tab"], [class*="tab"]').forEach(el => {
        const text = el.textContent.trim();
        if (text.length > 0 && text.length < 50) {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0) {
                result.push({type: 'tab', text: text, x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height)});
            }
        }
    });
    
    // Check all elements with "backtest" or "run" or "test" in text
    document.querySelectorAll('*').forEach(el => {
        if (el.children.length === 0) {
            const text = el.textContent.trim();
            if (text.length > 0 && text.length < 50 && (text.toLowerCase().includes('backtest') || text.toLowerCase().includes('run') || text.toLowerCase().includes('test') || text.toLowerCase().includes('launch'))) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0) {
                    result.push({type: 'match', text: text, tag: el.tagName, x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height)});
                }
            }
        }
    });
    
    return result;
})()
''', 'returnByValue':True}}))
r = json.loads(ws.recv())
elements = r.get('result',{}).get('result',{}).get('value', [])

print(f'Found {len(elements)} elements:')
for e in elements:
    print(f'  [{e["type"]:6s}] "{e["text"]}" pos=({e["x"]},{e["y"]} {e["w"]}x{e["h"]})')

# 2. Get the page structure (what panels are visible)
ws.send(json.dumps({'id':3, 'method':'Runtime.evaluate', 'params':{'expression':'''
(() => {
    // Get the main content area structure
    const body = document.body;
    function getStructure(el, depth) {
        if (depth > 3) return '';
        let result = '';
        const children = el.children;
        for (let i = 0; i < Math.min(children.length, 15); i++) {
            const c = children[i];
            const cls = c.className && typeof c.className === 'string' ? c.className.substring(0, 60) : '';
            const id = c.id ? '#' + c.id : '';
            const tag = c.tagName.toLowerCase();
            if (cls || id) {
                result += '  '.repeat(depth) + tag + id + ' .' + cls + '\\n';
            }
            if (depth < 3 && (cls.includes('panel') || cls.includes('Panel') || cls.includes('editor') || cls.includes('code') || cls.includes('backtest') || cls.includes('result'))) {
                result += getStructure(c, depth + 1);
            }
        }
        return result;
    }
    return getStructure(body, 0);
})()
''', 'returnByValue':True}}))
r = json.loads(ws.recv())
structure = r.get('result',{}).get('result',{}).get('value', '')
print(f'\nPage structure:\n{structure}')

ws.close()
