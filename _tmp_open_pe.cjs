const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
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
    // First screenshot to see current state
    const ss1 = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_pre_open.png' });
    console.log('Pre-screenshot:', ss1);

    // Try to find and click the Pine Editor button
    // It's usually in the top toolbar
    console.log('Looking for Pine Editor button...');
    
    // Try finding by text
    const found = await mcpCall('ui_find_element', { query: 'Pine Editor', strategy: 'text' });
    console.log('Pine Editor text:', found);

    // Try the keyboard shortcut Ctrl+Alt+P or similar
    // Actually in TV Desktop, Pine Editor is opened via the "Pine" button in the top bar
    // Let's try finding it by looking at the top toolbar area
    
    // Try clicking at common Pine Editor button positions
    // In TV Desktop, it's typically at the top: indicators button -> Pine Editor
    // Or there's a dedicated Pine button
    
    // Let's try the "Indicators" button first, then look for Pine Editor
    const indFound = await mcpCall('ui_find_element', { query: 'Indicators', strategy: 'text' });
    console.log('Indicators:', indFound);

    // Try opening via panel with different approach
    console.log('\\nTrying ui_open_panel with pine-editor...');
    const r1 = await mcpCall('ui_open_panel', { panel: 'pine-editor', action: 'open' });
    console.log('Result:', r1);
    
    await new Promise(r => setTimeout(r, 2000));
    
    // Screenshot to see if it opened
    const ss2 = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_post_open.png' });
    console.log('Post-screenshot:', ss2);

  } catch (e) {
    console.error('ERR:', e.message);
  }
})();
