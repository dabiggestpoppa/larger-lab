const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const TV_DIR = 'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\tools\\tradingview-mcp';

async function mcpCall(toolName, argsObj) {
  return new Promise((resolve, reject) => {
    const mcp = spawn('node', [path.join(TV_DIR, 'src', 'server.js')], { stdio: ['pipe','pipe','pipe'] });
    let buffer = '';
    let done = false;
    mcp.stdout.on('data', (data) => {
      buffer += data.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        let parsed;
        try { parsed = JSON.parse(line); } catch(e) { continue; }
        if (parsed.id === 1 && parsed.result && !done) {
          done = true;
          mcp.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 2, method: 'tools/call', params: { name: toolName, arguments: argsObj } }) + '\n');
        }
        if (parsed.id === 2) {
          mcp.kill();
          if (parsed.error) reject(new Error(JSON.stringify(parsed.error)));
          else if (parsed.result && parsed.result.content) {
            resolve(parsed.result.content.filter(c => c.type === 'text').map(c => c.text).join('\n'));
          } else resolve(JSON.stringify(parsed.result));
        }
      }
    });
    mcp.stderr.on('data', () => {});
    mcp.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2025-03-26', capabilities: {}, clientInfo: { name: 'OWL', version: '1.0' } } }) + '\n');
    setTimeout(() => { mcp.kill(); reject(new Error('Timeout: ' + toolName)); }, 30000);
  });
}

(async () => {
  try {
    // Remove duplicate CEREBUS V5 studies
    console.log('=== Remove duplicate studies ===');
    
    // List all studies
    const state = JSON.parse(await mcpCall('chart_get_state', {}));
    console.log('Current studies:', state.studies.map(s => s.name + ' (' + s.id + ')').join(', '));
    
    // The CEREBUS V5 LIVE appears twice - remove one instance
    const v5Studies = state.studies.filter(s => s.name.includes('V5 LIVE'));
    if (v5Studies.length > 1) {
      console.log('Removing duplicate:', v5Studies[1].id);
      const remResult = await mcpCall('chart_manage_indicator', { 
        action: 'remove', 
        name: v5Studies[1].id 
      });
      console.log(remResult);
      await new Promise(r => setTimeout(r, 1000));
    }

    // Now let's open the Strategy Tester and get a clean screenshot
    console.log('\n=== Open Strategy Tester ===');
    console.log(await mcpCall('ui_open_panel', { panel: 'strategy-tester', action: 'open' }));
    await new Promise(r => setTimeout(r, 3000));

    // Screenshot
    console.log('\n=== Screenshot ===');
    const ss = await mcpCall('capture_screenshot', { region: 'full', format: 'path' });
    console.log(ss);

  } catch(e) {
    console.error('ERROR:', e.message);
  }
})();
