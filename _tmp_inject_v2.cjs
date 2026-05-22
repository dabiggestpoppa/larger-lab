const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const TV_DIR = 'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\tools\\tradingview-mcp';
const pineFile = 'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\quant-lab\\conversions\\pinescript\\CEREBUS_DMR_V2.pine';

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
    const pineCode = fs.readFileSync(pineFile, 'utf8');
    console.log('Loaded ' + pineCode.length + ' chars');

    console.log('\n1. Open editor');
    console.log(await mcpCall('ui_open_panel', { panel: 'pine-editor', action: 'open' }));
    await new Promise(r => setTimeout(r, 2000));

    console.log('\n2. Set source');
    console.log(await mcpCall('pine_set_source', { source: pineCode }));
    await new Promise(r => setTimeout(r, 1000));

    console.log('\n3. Compile');
    console.log(await mcpCall('pine_compile', {}));
    await new Promise(r => setTimeout(r, 3000));

    console.log('\n4. Errors');
    console.log(await mcpCall('pine_get_errors', {}));

    console.log('\n5. Console');
    console.log(await mcpCall('pine_get_console', {}));

    console.log('\n6. Chart state');
    console.log(await mcpCall('chart_get_state', {}));

    console.log('\n✅ DMR v2 injected! Check Strategy Tester for backtest results.');
  } catch(e) {
    console.error('ERROR:', e.message);
  }
})();
