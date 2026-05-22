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
    // Find element "Alert on USDCHF" and look for siblings/parents with close buttons
    // Try to find and click the X using CSS for the alert close button
    const strategies = [
      // TradingView alert close button classes
      { by: 'class-contains', value: 'close' },
      { by: 'class-contains', value: 'Close' },
      { by: 'aria-label', value: 'Close' },
      { by: 'aria-label', value: 'close' },
      { by: 'data-name', value: 'close' },
      { by: 'text', value: '✕' },
      { by: 'text', value: '×' },
    ];

    for (const s of strategies) {
      try {
        console.log('Trying:', JSON.stringify(s));
        const r = await mcpCall('ui_click', s);
        console.log('  Result:', r);
      } catch (e) {
        console.log('  Error:', e.message);
      }
      await new Promise(r => setTimeout(r, 300));
    }

    // Close alerts panel
    console.log('\\nClosing alerts panel...');
    const r = await mcpCall('ui_open_panel', { panel: 'alerts', action: 'close' });
    console.log(r);
    await new Promise(r => setTimeout(r, 2000));

    // Screenshot
    const ss = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_after_close_alerts.png' });
    console.log('Screenshot:', ss);

  } catch (e) {
    console.error('ERR:', e.message);
  }
})();
