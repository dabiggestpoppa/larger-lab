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
    // Check study values
    const sv = await mcpCall('data_get_study_values', { study_name: 'CEREBUS DMR v5' });
    console.log('Study values:', sv);

    // Check tables
    const tables = await mcpCall('data_get_pine_tables', { study_filter: 'DMR v5' });
    console.log('Tables:', tables);

    // Open strategy tester
    await mcpCall('ui_open_panel', { panel: 'strategy-tester', action: 'close' });
    await new Promise(r => setTimeout(r, 1000));
    await mcpCall('ui_open_panel', { panel: 'strategy-tester', action: 'open' });
    await new Promise(r => setTimeout(r, 5000));

    // Try to dismiss alert by clicking Close button
    try {
      await mcpCall('ui_click', { by: 'aria-label', value: 'Close' });
      console.log('Dismissed alert');
      await new Promise(r => setTimeout(r, 2000));
    } catch(e) {
      console.log('No alert to dismiss');
    }

    // Click Metrics tab
    await mcpCall('ui_mouse_click', { x: 106, y: 834 });
    await new Promise(r => setTimeout(r, 3000));

    // Screenshot
    const ss = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_v5_backtest.png' });
    console.log('Screenshot:', ss);

  } catch (e) {
    console.error('ERR:', e.message);
  }
})();
