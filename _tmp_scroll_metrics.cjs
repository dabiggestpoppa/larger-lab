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
    // Try scrolling the strategy tester panel to see more metrics
    // First, click in the strategy tester area to focus it
    await mcpCall('ui_mouse_click', { x: 500, y: 900 });
    await new Promise(r => setTimeout(r, 500));
    
    // Scroll down within the panel
    console.log('Scrolling down in strategy tester...');
    await mcpCall('ui_scroll', { x: 500, y: 900, deltaY: 300 });
    await new Promise(r => setTimeout(r, 1000));
    
    // Screenshot
    const ss1 = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_v5_scroll1.png' });
    console.log('Screenshot 1:', ss1);
    
    // Scroll more
    await mcpCall('ui_scroll', { x: 500, y: 900, deltaY: 300 });
    await new Promise(r => setTimeout(r, 1000));
    
    const ss2 = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_v5_scroll2.png' });
    console.log('Screenshot 2:', ss2);

    // Also try the "More" button if it exists
    const moreBtn = await mcpCall('ui_find_element', { query: 'More', strategy: 'text' });
    console.log('More button:', moreBtn);

  } catch (e) {
    console.error('ERR:', e.message);
  }
})();
