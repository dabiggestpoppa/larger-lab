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
      const expr = `
        (function() {
          const result = {};
          
          // Check for TradingView-like API
          result.hasTradingViewApi = !!window.TradingViewApi;
          result.hasTradingView = !!window.TradingView;
          
          // Check for Studio-related globals
          result.hasStudio = !!window.__studio;
          result.hasEngine = !!window.__engine;
          result.hasApp = !!window.__app;
          result.hasStore = !!window.__store;
          result.hasVue = !!window.__vue_app__;
          result.hasReact = !!window.__reactRoot;
          
          // Check for common state management
          result.keys = Object.keys(window).filter(k => k.startsWith('__'));
          
          // Check document for Studio elements
          result.studioElements = document.querySelectorAll('[class*="studio"]').length;
          result.editorElements = document.querySelectorAll('[class*="editor"], [class*="code"], .monaco-editor, .CodeMirror').length;
          result.backtestButtons = document.querySelectorAll('[class*="backtest"], [class*="test"]').length;
          
          // Check for Electron
          result.isElectron = !!window.process;
          result.electronVersion = window.process && window.process.versions ? window.process.versions.electron : 'N/A';
          
          // Get page title and URL
          result.title = document.title;
          result.url = window.location.href;
          
          // Check for iframes
          result.iframes = Array.from(document.querySelectorAll('iframe')).map(f => f.src);
          
          return JSON.stringify(result, null, 2);
        })()
      `;
      
      ws.send(JSON.stringify({
        id: id++,
        method: 'Runtime.evaluate',
        params: { expression: expr, returnByValue: true }
      }));
    });
    
    ws.on('message', (msg) => {
      const resp = JSON.parse(msg);
      if (resp.id) {
        console.log(resp.result && resp.result.result ? resp.result.result.value : JSON.stringify(resp));
        ws.close();
      }
    });
  });
}).on('error', (e) => console.error(e.message));
