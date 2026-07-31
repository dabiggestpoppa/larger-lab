const http = require('http');
const WebSocket = require('ws');

http.get('http://localhost:9222/json/list', (res) => {
  let data = '';
  res.on('data', (chunk) => data += chunk);
  res.on('end', () => {
    const targets = JSON.parse(data);
    
    // Show ALL targets
    console.log('=== ALL CDP TARGETS ===');
    targets.forEach(t => {
      console.log(t.type, '|', t.title, '|', t.url);
    });
    
    const page = targets.find(t => t.url.includes('tradelocker.com'));
    if (!page) { console.log('No TL page'); process.exit(1); }
    
    const ws = new WebSocket(page.webSocketDebuggerUrl);
    let id = 1;
    
    ws.on('open', () => {
      // Deep probe into __TRADELOCKER__.runtimeConfig and look for Studio window
      const expr = `
        (function() {
          const result = {};
          
          // Explore runtimeConfig
          try {
            const rc = window.__TRADELOCKER__.runtimeConfig;
            result.runtimeConfig = rc ? JSON.parse(JSON.stringify(rc, (k, v) => {
              if (typeof v === 'function') return '[Function]';
              if (v instanceof Promise) return '[Promise]';
              return v;
            })).slice(0, 2000) : null;
          } catch(e) {
            result.rcError = e.message;
          }
          
          // Look for Studio-related items in localStorage
          try {
            const keys = Object.keys(localStorage).filter(k => 
              k.toLowerCase().includes('studio') || 
              k.toLowerCase().includes('bot') || 
              k.toLowerCase().includes('backtest') ||
              k.toLowerCase().includes('project')
            );
            result.localStorageKeys = keys.slice(0, 20);
          } catch(e) {
            result.lsError = e.message;
          }
          
          // Look for Studio in sessionStorage
          try {
            const keys = Object.keys(sessionStorage).filter(k => 
              k.toLowerCase().includes('studio') || 
              k.toLowerCase().includes('bot')
            );
            result.sessionStorageKeys = keys.slice(0, 20);
          } catch(e) {
            result.ssError = e.message;
          }
          
          // Check for any global functions related to Studio
          result.globalFns = Object.keys(window).filter(k => {
            try {
              return typeof window[k] === 'function' && 
                (k.toLowerCase().includes('studio') || 
                 k.toLowerCase().includes('bot') || 
                 k.toLowerCase().includes('backtest') ||
                 k.toLowerCase().includes('engine'));
            } catch(e) { return false; }
          }).slice(0, 20);
          
          // Check if there's a way to open Studio from this page
          result.hasOpenStudio = typeof window.openStudio;
          result.hasStudioApi = typeof window.studioApi;
          result.hasEngineApi = typeof window.engineApi;
          
          // Check for TradingView chart widget
          try {
            const charts = document.querySelectorAll('[class*="chart"], [class*="trading"]');
            result.chartElements = charts.length;
          } catch(e) {}
          
          // Check for any links/buttons to open Studio
          const allLinks = document.querySelectorAll('a[href*="studio"], [onclick*="studio"], [data-action*="studio"]');
          result.studioLinks = allLinks.length;
          
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
        const val = resp.result && resp.result.result ? resp.result.result.value : JSON.stringify(resp);
        console.log(val);
        ws.close();
      }
    });
  });
}).on('error', (e) => console.error(e.message));
