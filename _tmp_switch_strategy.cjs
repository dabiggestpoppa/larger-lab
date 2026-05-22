const { spawn } = require('child_process');
const path = require('path');
const TV_DIR = 'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\tools\\tradingview-mcp';

function mcpCall(name, args) {
  return new Promise((ok, fail) => {
    const m = spawn('node', [path.join(TV_DIR, 'src', 'server.js')], { stdio: ['pipe','pipe','pipe'] });
    let buf = ''; let sent = false;
    m.stdout.on('data', d => {
      buf += d.toString();
      const lines = buf.split('\n'); buf = lines.pop();
      for (const l of lines) {
        if (!l.trim()) continue;
        let p; try { p = JSON.parse(l); } catch(e) { continue; }
        if (p.id === 1 && p.result && !sent) { sent = true; m.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 2, method: 'tools/call', params: { name, arguments: args } }) + '\n'); }
        if (p.id === 2) { m.kill(); p.error ? fail(new Error(JSON.stringify(p.error))) : ok(p.result.content ? p.result.content.filter(c => c.type === 'text').map(c => c.text).join('\n') : JSON.stringify(p.result)); }
      }
    });
    m.stderr.on('data', () => { });
    m.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2025-03-26', capabilities: {}, clientInfo: { name: 'x', version: '1' } } }) + '\n');
    setTimeout(() => { m.kill(); fail(new Error('timeout')); }, 30000);
  });
}

(async () => {
  try {
    // Find the strategy selector in the Strategy Tester panel
    // It's usually a dropdown at the top of the panel showing the current strategy name
    // Let me find it by looking for the strategy name text
    
    console.log('Looking for strategy selector...');
    
    // The strategy name "CEREBUS V5 LIVE PERFECT FORM FIXED v5" should be clickable
    // Let's find it and click it to open the dropdown
    const found = await mcpCall('ui_find_element', { 
      query: 'CEREBUS V5 LIVE PERFECT FORM FIXED v5', 
      strategy: 'text' 
    });
    console.log('Found:', found);
    
    // Also look for "CEREBUS DMR v5" in the page
    const dmrFound = await mcpCall('ui_find_element', { 
      query: 'CEREBUS DMR v5', 
      strategy: 'text' 
    });
    console.log('DMR v5 found:', dmrFound);
    
    // The strategy selector dropdown is usually near the top of the Strategy Tester panel
    // Let me try clicking at the strategy name area to open the dropdown
    // From the screenshot, the strategy name appears at the top of the panel area
    // Panel starts around y:850, so the strategy selector might be at y:860-880
    
    // Let me try clicking at approximately where the strategy name is displayed
    // Based on the earlier screenshot, it's at the top-left of the panel
    console.log('\\nClicking strategy selector area...');
    const c1 = await mcpCall('ui_mouse_click', { x: 200, y: 860 });
    console.log('Click:', c1);
    await new Promise(r => setTimeout(r, 1000));
    
    // Screenshot to see if dropdown opened
    const ss = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_strategy_dropdown.png' });
    console.log('Screenshot:', ss);

  } catch (e) {
    console.error('ERR:', e.message);
  }
})();
