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
    // Find all button elements on the page
    console.log('=== Finding all buttons ===');
    
    // Use a broader approach - find the alert and all its children
    const found = await mcpCall('ui_find_element', { query: 'button', strategy: 'css' });
    console.log('Buttons:', found);

    // Find SVG elements (X buttons are often SVG)
    const svgFound = await mcpCall('ui_find_element', { query: 'svg', strategy: 'css' });
    console.log('SVGs:', svgFound);

    // Try pressing Delete key
    console.log('\\nPressing Delete key...');
    const del1 = await mcpCall('ui_keyboard', { key: 'Delete' });
    console.log('Delete:', del1);
    await new Promise(r => setTimeout(r, 500));

    // Try pressing 'x' key
    console.log('Pressing x key...');
    const xkey = await mcpCall('ui_keyboard', { key: 'x' });
    console.log('x:', xkey);
    await new Promise(r => setTimeout(r, 500));

    // Screenshot
    const ss = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_after_keys.png' });
    console.log('\\nScreenshot:', ss);

  } catch (e) {
    console.error('ERR:', e.message);
  }
})();
