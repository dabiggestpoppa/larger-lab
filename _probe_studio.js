const http = require('http');
const WebSocket = require('ws');

http.get('http://localhost:9222/json/list', (res) => {
  let data = '';
  res.on('data', (chunk) => data += chunk);
  res.on('end', () => {
    const targets = JSON.parse(data);
    const page = targets.find(t => t.url.includes('tradelocker.com'));
    if (!page) { console.log('No TL page'); process.exit(1); }
    
    const ws = new WebSocket(page.webSocketDebuggerUrl);
    let id = 1;
    
    ws.on('open', () => {
      // Navigate to Studio
      ws.send(JSON.stringify({
        id: id++,
        method: 'Page.navigate',
        params: { url: 'https://demo.tradelocker.com/en/studio/bots/new' }
      }));
    });
    
    ws.on('message', (msg) => {
      const resp = JSON.parse(msg);
      if (resp.id === 1) {
        console.log('Navigating to Studio... waiting 5s for load');
        // Wait for page to load then probe
        setTimeout(() => {
          const expr = `
            (function() {
              const result = {};
              result.title = document.title;
              result.url = window.location.href;
              
              // Check for Next.js
              result.hasNextJs = !!window.__NEXT_DATA__;
              result.nextData = window.__NEXT_DATA__ ? JSON.stringify(window.__NEXT_DATA__).substring(0, 500) : null;
              
              // Check for React root
              const root = document.querySelector('#__next, #root, [data-reactroot]');
              result.reactRoot = root ? { tag: root.tagName, id: root.id } : null;
              
              // Get all visible text elements
              const body = document.body.innerText;
              result.bodyPreview = body.substring(0, 2000);
              
              // Check for editor
              result.hasMonaco = !!window.monaco;
              result.hasCodeMirror = !!window.CodeMirror;
              result.hasAce = !!window.ace;
              result.hasPrism = !!window.Prism;
              
              // Check for editor DOM elements
              result.monacoEditors = document.querySelectorAll('.monaco-editor').length;
              result.codeMirrorEditors = document.querySelectorAll('.CodeMirror').length;
              result.aceEditors = document.querySelectorAll('.ace_editor').length;
              result.textareas = document.querySelectorAll('textarea').length;
              
              // Check for buttons
              result.buttons = Array.from(document.querySelectorAll('button, [role="button"]')).map(b => b.textContent.trim()).filter(t => t.length > 0 && t.length < 80).slice(0, 30);
              
              // Check for forms/inputs
              result.inputs = document.querySelectorAll('input, textarea, select').length;
              
              // Check for any API calls being made
              result.hasFetch = typeof window.fetch;
              
              // Check for global state
              result.globalKeys = Object.keys(window).filter(k => k.startsWith('__'));
              
              // Check for Studio-specific globals
              result.studioKeys = Object.keys(window).filter(k => 
                k.toLowerCase().includes('studio') || 
                k.toLowerCase().includes('bot') || 
                k.toLowerCase().includes('engine') ||
                k.toLowerCase().includes('project')
              );
              
              return JSON.stringify(result, null, 2);
            })()
          `;
          
          ws.send(JSON.stringify({
            id: id++,
            method: 'Runtime.evaluate',
            params: { expression: expr, returnByValue: true }
          }));
        }, 5000);
      }
      if (resp.id === 2) {
        const val = resp.result && resp.result.result ? resp.result.result.value : JSON.stringify(resp);
        console.log(val);
        ws.close();
      }
    });
  });
}).on('error', (e) => console.error(e.message));
