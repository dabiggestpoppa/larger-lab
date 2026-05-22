const http = require('http');
const WebSocket = require('ws');
const fs = require('fs');

function httpGet(url) {
  return new Promise((resolve, reject) => {
    http.get(url, res => { let d=''; res.on('data',c=>d+=c); res.on('end',()=>resolve(JSON.parse(d))); }).on('error', reject);
  });
}

async function cdpEval(ws, expr) {
  return new Promise((resolve, reject) => {
    const id = Date.now();
    const handler = (msg) => {
      const data = JSON.parse(msg);
      if (data.id === id) {
        ws.off('message', handler);
        if (data.error) reject(new Error(JSON.stringify(data.error)));
        else resolve(data.result);
      }
    };
    ws.on('message', handler);
    ws.send(JSON.stringify({ id, method: 'Runtime.evaluate', params: { expression: expr, returnByValue: true } }));
    setTimeout(() => { ws.off('message', handler); reject(new Error('CDP eval timeout')); }, 10000);
  });
}

(async () => {
  try {
    const targets = await httpGet('http://localhost:9222/json');
    const tvTarget = targets.find(t => t.url && t.url.includes('tradingview.com'));
    if (!tvTarget) { console.error('No TV tab'); process.exit(1); }
    
    const ws = new WebSocket(tvTarget.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => { ws.on('open', resolve); ws.on('error', reject); });

    // Extract strategy tester metrics from DOM
    const result = await cdpEval(ws, `
      (function() {
        // Find all text content in the strategy tester panel
        var texts = [];
        
        // Look for the strategy report panel
        var panels = document.querySelectorAll('[class*="strategy-report"], [class*="strategyReport"], [class*="report-panel"]');
        if (panels.length === 0) {
          // Try broader search
          panels = document.querySelectorAll('[class*="report"]');
        }
        
        // Try to find metric rows
        var metricRows = document.querySelectorAll('[class*="metrics"], [class*="performance"]');
        
        // Get all visible text elements in the bottom panel
        var allText = [];
        document.querySelectorAll('span, td, th, div, p, label').forEach(el => {
          var t = el.textContent.trim();
          if (t.length > 0 && t.length < 200 && el.offsetParent !== null) {
            // Filter to strategy-tester-like content
            if (t.match(/Profit|Trades|Factor|Drawdown|Sharpe|Win|Loss|P&L|Net|Total/i)) {
              allText.push(t);
            }
          }
        });
        
        return JSON.stringify({
          panels: panels.length,
          metricRows: metricRows.length,
          texts: allText.slice(0, 50)
        });
      })()
    `);
    
    console.log('Strategy Tester DOM:');
    console.log(result.value);
    
    ws.close();
  } catch(e) {
    console.error('ERROR:', e.message);
  }
  
  // ws.close()
})();
