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
    // Close and reopen strategy tester to get fresh state
    console.log('Closing strategy tester...');
    await mcpCall('ui_open_panel', { panel: 'strategy-tester', action: 'close' });
    await new Promise(r => setTimeout(r, 1000));

    console.log('Opening strategy tester...');
    await mcpCall('ui_open_panel', { panel: 'strategy-tester', action: 'open' });
    await new Promise(r => setTimeout(r, 3000));

    // Click Metrics tab
    console.log('Clicking Metrics tab at x:106 y:834...');
    const c1 = await mcpCall('ui_mouse_click', { x: 106, y: 834 });
    console.log('Click:', c1);
    await new Promise(r => setTimeout(r, 2000));

    // Screenshot
    console.log('Screenshot...');
    const ss = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_clean_metrics.png' });
    console.log(ss);

  } catch (e) {
    console.error('ERR:', e.message);
  }
})();
