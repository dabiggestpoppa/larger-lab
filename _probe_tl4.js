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
          
          // Fix runtimeConfig probe
          try {
            const rc = window.__TRADELOCKER__.runtimeConfig;
            if (rc && typeof rc === 'object') {
              result.rcKeys = Object.keys(rc);
              result.rcType = typeof rc;
              // Try to serialize it
              try {
                const str = JSON.stringify(rc);
                result.rcPreview = str.substring(0, 2000);
              } catch(e) {
                result.rcStringifyError = e.message;
              }
            }
          } catch(e) {
            result.rcError = e.message;
          }
          
          // Find the 2 studio links
          const allEls = document.querySelectorAll('a[href*="studio"], [onclick*="studio"], [data-action*="studio"]');
          result.studioLinkDetails = Array.from(allEls).map(el => ({
            tag: el.tagName,
            href: el.href || '',
            text: el.textContent.trim().substring(0, 100),
            className: el.className.substring(0, 100),
            id: el.id,
            onclick: el.getAttribute('onclick') || '',
            dataAction: el.getAttribute('data-action') || '',
            outerHTML: el.outerHTML.substring(0, 300)
          }));
          
          // Also search for "Bot Studio" or "Studio" text in all clickable elements
          const allClickable = document.querySelectorAll('a, button, [role="button"], [class*="studio"], [class*="bot"]');
          result.studioClickables = Array.from(allClickable).filter(el => {
            const text = el.textContent.trim();
            return text.toLowerCase().includes('studio') || text.toLowerCase().includes('bot');
          }).map(el => ({
            tag: el.tagName,
            text: el.textContent.trim().substring(0, 100),
            className: el.className.substring(0, 100),
            href: el.href || '',
            outerHTML: el.outerHTML.substring(0, 300)
          }));
          
          // Check for the sidebar - look for "Bot Studio" navigation
          const sidebar = document.querySelectorAll('[class*="sidebar"], [class*="side"], [class*="nav"], [class*="panel"]');
          result.sidebarInfo = Array.from(sidebar).map(el => ({
            tag: el.tagName,
            className: el.className.substring(0, 100),
            textPreview: el.textContent.trim().substring(0, 200)
          })).slice(0, 10);
          
          // Check for the iframe more carefully
          const iframes = document.querySelectorAll('iframe');
          result.iframeDetails = Array.from(iframes).map(f => ({
            src: f.src,
            id: f.id,
            className: f.className,
            width: f.offsetWidth,
            height: f.offsetHeight
          }));
          
          // Check for TradingView widget access
          try {
            // TradingView embeds usually have a widget reference
            const tvWidgets = document.querySelectorAll('[id*="tradingview"], [class*="tradingview"]');
            result.tvWidgets = tvWidgets.length;
          } catch(e) {}
          
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
