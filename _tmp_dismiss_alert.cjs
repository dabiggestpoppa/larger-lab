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
    // Find the close/dismiss button for the alert
    const found = await mcpCall('ui_find_element', { query: 'Edit alert', strategy: 'text' });
    console.log('Edit alert:', found);

    // Try pressing Escape to dismiss the alert
    console.log('Pressing Escape...');
    const esc = await mcpCall('ui_keyboard', { key: 'Escape' });
    console.log('Escape:', esc);
    await new Promise(r => setTimeout(r, 1000));

    // Also try clicking somewhere outside the alert to dismiss it
    // The alert is probably in the bottom-left area, click top-right of strategy tester
    console.log('Clicking outside alert area...');
    const c1 = await mcpCall('ui_mouse_click', { x: 500, y: 700 });
    console.log('Click:', c1);
    await new Promise(r => setTimeout(r, 1000));

    // Now click Metrics tab
    console.log('Clicking Metrics tab...');
    const c2 = await mcpCall('ui_mouse_click', { x: 106, y: 834 });
    console.log('Click Metrics:', c2);
    await new Promise(r => setTimeout(r, 2000));

    // Screenshot
    const ss = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_no_alert.png' });
    console.log('Screenshot:', ss);

  } catch (e) {
    console.error('ERR:', e.message);
  }
})();
