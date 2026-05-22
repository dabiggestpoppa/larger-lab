const { spawn } = require('child_process');
const path = require('path');
const TV_DIR = 'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\tools\\tradingview-mcp';

async function mcpCall(toolName, argsObj) {
  return new Promise((resolve, reject) => {
    const mcp = spawn('node', [path.join(TV_DIR, 'src', 'server.js')], { stdio: ['pipe','pipe','pipe'] });
    let buffer = ''; let done = false;
    mcp.stdout.on('data', data => {
      buffer += data.toString();
      const lines = buffer.split('\n'); buffer = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        let p; try { p = JSON.parse(line); } catch(e) { continue; }
        if (p.id === 1 && p.result && !done) { done = true; mcp.stdin.write(JSON.stringify({jsonrpc:'2.0',id:2,method:'tools/call',params:{name:toolName,arguments:argsObj}}) + '\n'); }
        if (p.id === 2) { mcp.kill(); p.error ? reject(new Error(JSON.stringify(p.error))) : resolve(p.result.content ? p.result.content.filter(c=>c.type==='text').map(c=>c.text).join('\n') : JSON.stringify(p.result)); }
      }
    });
    mcp.stderr.on('data', () => {});
    mcp.stdin.write(JSON.stringify({jsonrpc:'2.0',id:1,method:'initialize',params:{protocolVersion:'2025-03-26',capabilities:{},clientInfo:{name:'x',version:'1'}}}) + '\n');
    setTimeout(() => { mcp.kill(); reject(new Error('Timeout')); }, 30000);
  });
}

(async () => {
  try {
    // Try clicking Overview tab using keyboard shortcut or specific selectors
    // TradingView Strategy Tester tabs: Overview | List of trades
    // Let's try various selectors
    
    const selectors = [
      'button:contains("Overview")',
      '[class*="tab-overview"]',
      '[class*="tabOverview"]', 
      '[data-tab="overview"]',
      'button[data-name="overview"]',
      // TradingView specific
      '.report-tabs button:first-child',
      '.strategy-report-tabs button:first-child',
      '[class*="report"] button:first-child',
      '[class*="Report"] button:first-child',
    ];

    for (const sel of selectors) {
      try {
        console.log('Trying selector:', sel);
        const r = await mcpCall('ui_click_element', { selector: sel, method: 'dom' });
        console.log('  Result:', r);
      } catch(e) {
        console.log('  Failed:', e.message);
      }
      await new Promise(r => setTimeout(r, 500));
    }

    // Also try pressing keyboard shortcut
    console.log('\nTrying keyboard: Alt+1');
    const k1 = await mcpCall('ui_press_key', { key: 'Alt+1' });
    console.log('Alt+1:', k1);
    await new Promise(r => setTimeout(r, 1000));

    // Screenshot
    console.log('\nScreenshot...');
    const ss = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_overview_attempt.png' });
    console.log(ss);

  } catch(e) {
    console.error('ERROR:', e.message);
  }
})();
