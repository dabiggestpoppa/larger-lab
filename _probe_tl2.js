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
      // Probe __TRADELOCKER__ global and the iframe
      const expr = `
        (function() {
          const result = {};
          
          // Explore __TRADELOCKER__
          const tl = window.__TRADELOCKER__;
          result.hasTlGlobal = !!tl;
          result.tlKeys = tl ? Object.keys(tl).slice(0, 30) : [];
          result.tlProto = tl ? Object.getOwnPropertyNames(Object.getPrototypeOf(tl)).slice(0, 50) : [];
          
          // Check if TradingView has chart API
          try {
            const tv = window.TradingView;
            result.tvKeys = tv ? Object.keys(tv).slice(0, 20) : [];
          } catch(e) {
            result.tvError = e.message;
          }
          
          // Check the iframe - is it Studio?
          const iframes = document.querySelectorAll('iframe');
          result.iframeCount = iframes.length;
          result.iframeSrcs = Array.from(iframes).map(f => f.src);
          
          // Try to access iframe content
          try {
            const iframeDoc = iframes[0]?.contentDocument || iframes[0]?.contentWindow?.document;
            if (iframeDoc) {
              result.iframeTitle = iframeDoc.title;
              result.iframeUrl = iframeDoc.location.href;
              result.iframeStudioElements = iframeDoc.querySelectorAll('[class*="studio"]').length;
              result.iframeEditorElements = iframeDoc.querySelectorAll('[class*="editor"], [class*="code"], .monaco-editor, .CodeMirror').length;
              result.iframeBacktestBtns = iframeDoc.querySelectorAll('[class*="backtest"], [class*="test"]').length;
              result.iframeButtons = Array.from(iframeDoc.querySelectorAll('button')).map(b => b.textContent.trim()).filter(t => t.length > 0 && t.length < 50).slice(0, 20);
            }
          } catch(e) {
            result.iframeError = e.message;
          }
          
          // Check for React/Vue in the main page
          const app = document.querySelector('#app, #root, [data-reactroot], [data-v-app]');
          result.appRoot = app ? { tag: app.tagName, id: app.id, classes: app.className } : null;
          
          // Get all buttons on the page
          result.mainPageButtons = Array.from(document.querySelectorAll('button, [role="button"]')).map(b => b.textContent.trim()).filter(t => t.length > 0 && t.length < 50).slice(0, 30);
          
          // Check for sidebar/navigation
          result.sidebarItems = Array.from(document.querySelectorAll('nav a, [class*="nav"] a, [class*="sidebar"] a, [class*="menu"] a, [class*="panel"] a')).map(a => a.textContent.trim()).filter(t => t.length > 0 && t.length < 50).slice(0, 20);
          
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
