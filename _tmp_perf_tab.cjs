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
    // Click the Overview/Performance Summary tab
    console.log('Clicking Overview tab...');
    const r1 = await mcpCall('ui_click_element', { 
      selector: '[class*="overview"], [class*="Overview"], [data-name="Overview"], button:has-text("Overview")',
      method: 'dom'
    });
    console.log(r1);
    await new Promise(r => setTimeout(r, 2000));

    // Try alternative: Metrics tab
    console.log('Clicking Metrics tab...');
    const r2 = await mcpCall('ui_click_element', {
      selector: '[class*="metrics"], [class*="Metrics"], [class*="summary"], [class*="Summary"]',
      method: 'dom'
    });
    console.log(r2);
    await new Promise(r => setTimeout(r, 2000));

    // Screenshot
    console.log('\nScreenshot...');
    const ss = await mcpCall('capture_screenshot', { region: 'full', format: 'path' });
    console.log(ss);

  } catch(e) {
    console.error('ERROR:', e.message);
  }
})();
