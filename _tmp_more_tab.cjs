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
    // The "More" tab button is at approximately x:290, y:834 (based on Metrics at x:72, List of trades at x:198)
    // Actually from the element data, the tab bar is at y:820
    // Metrics tab is at x:72, List of trades at x:198, More should be around x:290+
    // Let me find the exact position
    
    // Click "More" tab
    console.log('Clicking More tab...');
    
    // From the round-tabs-buttons div at x:68, y:816, width:1759
    // The tabs are: Metrics (x:72), List of trades (x:198), More (need to find)
    // Let me try clicking at the "More" text position
    const moreFound = await mcpCall('ui_find_element', { query: 'More', strategy: 'text' });
    const moreObj = JSON.parse(moreFound);
    
    // Find the "More" button that's a direct tab (not the "Show more" buttons)
    // The tab buttons are in the round-tabs-buttons div
    // Metrics is at ~x:72, List of trades at ~x:198
    // "More" tab should be the third tab
    
    // Let me click at the approximate position of the More tab
    // Based on the tab bar layout, More should be around x:290-320, y:834
    console.log('Clicking More tab at ~x:310, y:834...');
    const c1 = await mcpCall('ui_mouse_click', { x: 310, y: 834 });
    console.log('Click result:', c1);
    await new Promise(r => setTimeout(r, 2000));
    
    // Screenshot
    const ss = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_v5_more.png' });
    console.log('Screenshot:', ss);
    
    // Also try clicking directly on the "More" text in the tab
    // The tab text "More" should be visible in the tab bar
    console.log('\\nTrying to click More tab by finding its position...');
    // The round-tabs-buttons contains "MetricsList of tradesMore"
    // So the order is: Metrics, List of trades, More
    // Metrics starts at x:72, width ~69 (from earlier data)
    // List of trades starts at x:198
    // More should start around x:290+
    
    // Let me try x:310, y:820 (tab bar area)
    const c2 = await mcpCall('ui_mouse_click', { x: 310, y: 820 });
    console.log('Click 2:', c2);
    await new Promise(r => setTimeout(r, 2000));
    
    const ss2 = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_v5_more2.png' });
    console.log('Screenshot 2:', ss2);

  } catch (e) {
    console.error('ERR:', e.message);
  }
})();
