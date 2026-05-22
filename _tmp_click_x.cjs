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
    // Alert popup is at approximately x:126-450, y:880-970
    // The X close button should be at top-right of the card
    // Try multiple positions for the X
    const positions = [
      { x: 430, y: 890 },
      { x: 450, y: 885 },
      { x: 420, y: 895 },
      { x: 440, y: 880 },
      { x: 460, y: 890 },
    ];

    for (const pos of positions) {
      console.log(`Clicking at (${pos.x}, ${pos.y})...`);
      const r = await mcpCall('ui_mouse_click', pos);
      console.log('Result:', r);
      await new Promise(r => setTimeout(r, 500));
    }

    // Also try class-based close button
    console.log('Trying to find X button by class...');
    const found = await mcpCall('ui_find_element', { query: 'class*=close', strategy: 'css' });
    console.log('Find:', found);

    // Screenshot
    const ss = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_x_click.png' });
    console.log('Screenshot:', ss);

  } catch (e) {
    console.error('ERR:', e.message);
  }
})();
