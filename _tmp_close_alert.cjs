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
    // Find the X/close button on the alert popup
    // The alert is at approximately x:126-450, y:948 area
    // The X button is likely at the top-right of the alert popup
    const found = await mcpCall('ui_find_element', { query: 'close', strategy: 'text' });
    console.log('Close button:', found);

    // Try clicking at the X position (top-right of alert area)
    // Alert seems to be around x:126-450, y:880-970
    // X button would be around x:430, y:890
    console.log('Clicking X button at ~430,890...');
    const c1 = await mcpCall('ui_mouse_click', { x: 430, y: 890 });
    console.log('Click:', c1);
    await new Promise(r => setTimeout(r, 1000));

    // Also try finding button elements near the alert
    const found2 = await mcpCall('ui_find_element', { query: '[class*="close"]', strategy: 'css' });
    console.log('CSS close:', found2);

    // Try clicking the alert backdrop to dismiss
    console.log('Clicking at edge of screen to dismiss...');
    const c2 = await mcpCall('ui_mouse_click', { x: 50, y: 50 });
    console.log('Edge click:', c2);
    await new Promise(r => setTimeout(r, 1000));

    // Screenshot
    const ss = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_dismissed.png' });
    console.log('Screenshot:', ss);

  } catch (e) {
    console.error('ERR:', e.message);
  }
})();
