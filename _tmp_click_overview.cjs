const http = require('http');
const WebSocket = require('ws');

function httpGet(url) {
  return new Promise((resolve, reject) => {
    http.get(url, res => { let d=''; res.on('data',c=>d+=c); res.on('end',()=>resolve(JSON.parse(d))); }).on('error', reject);
  });
}

async function cdpEval(ws, expr, timeout=10000) {
  return new Promise((resolve, reject) => {
    const id = Date.now() + Math.floor(Math.random()*10000);
    const handler = (msg) => {
      try {
        const data = JSON.parse(msg);
        if (data.id === id) {
          ws.off('message', handler);
          if (data.error) reject(new Error(JSON.stringify(data.error)));
          else resolve(data.result);
        }
      } catch(e) {}
    };
    ws.on('message', handler);
    ws.send(JSON.stringify({ id, method: 'Runtime.evaluate', params: { expression: expr, returnByValue: true } }));
    setTimeout(() => { ws.off('message', handler); reject(new Error('CDP eval timeout')); }, timeout);
  });
}

(async () => {
  try {
    const targets = await httpGet('http://localhost:9222/json');
    const tvTarget = targets.find(t => t.url && t.url.includes('tradingview.com'));
    if (!tvTarget) { console.error('No TV tab'); process.exit(1); }
    
    const ws = new WebSocket(tvTarget.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => { ws.on('open', resolve); ws.on('error', reject); });

    // First, let's find what tabs exist in the strategy tester
    const tabResult = await cdpEval(ws, `
      (function() {
        var tabs = document.querySelectorAll('[class*="tab"], [role="tab"], button');
        var found = [];
        tabs.forEach(t => {
          var txt = t.textContent.trim();
          if (txt && txt.length < 30 && t.offsetParent !== null) {
            found.push({text: txt, class: t.className.substring(0,50)});
          }
        });
        return JSON.stringify(found.slice(0, 30));
      })()
    `);
    console.log('Tabs found:', tabResult.value);

    // Click on the "Overview" or "Performance Summary" or "Metrics" tab
    const clickResult = await cdpEval(ws, `
      (function() {
        var tabs = document.querySelectorAll('[class*="tab"], [role="tab"], button, a');
        for (var t of tabs) {
          var txt = t.textContent.trim();
          if ((txt.includes('Overview') || txt.includes('Performance') || txt.includes('Summary') || txt === 'Metrics') && t.offsetParent !== null) {
            t.click();
            return 'Clicked: ' + txt;
          }
        }
        return 'No matching tab found';
      })()
    `);
    console.log('Click result:', clickResult.value);

    await new Promise(r => setTimeout(r, 2000));

    // Now get all text in the strategy tester panel
    const textResult = await cdpEval(ws, `
      (function() {
        var results = [];
        // Find the strategy tester/report panel
        var allEls = document.querySelectorAll('span, td, th, div, p, label, button');
        for (var el of allEls) {
          var t = el.textContent.trim();
          if (t.length > 0 && t.length < 100 && el.offsetParent !== null) {
            // Only include elements that look like they're in the bottom panel
            var rect = el.getBoundingClientRect();
            if (rect.y > 400 && rect.width > 0) {
              results.push({text: t, y: Math.round(rect.y), x: Math.round(rect.x)});
            }
          }
        }
        return JSON.stringify(results.slice(0, 100));
      })()
    `);
    console.log('\nBottom panel text:', textResult.value);

    ws.close();
  } catch(e) {
    console.error('ERROR:', e.message);
  }
})();
