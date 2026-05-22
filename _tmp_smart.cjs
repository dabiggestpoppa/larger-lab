const { spawn } = require('child_process');
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
          const req = JSON.stringify({
            jsonrpc: '2.0', id: 2, method: 'tools/call',
            params: { name: toolName, arguments: argsObj }
          });
          mcp.stdin.write(req + '\n');
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
    mcp.stdin.write(JSON.stringify({
      jsonrpc: '2.0', id: 1, method: 'initialize',
      params: { protocolVersion: '2025-03-26', capabilities: {}, clientInfo: { name: 'OWL', version: '1.0' } }
    }) + '\n');
    setTimeout(() => { mcp.kill(); reject(new Error('Timeout: ' + toolName)); }, 20000);
  });
}

(async () => {
  try {
    // First, try to save and add to chart using pine_save (Ctrl+S)
    console.log('=== Save (Ctrl+S) ===');
    console.log(await mcpCall('pine_save', {}));
    await new Promise(r => setTimeout(r, 2000));

    // Try smart_compile
    console.log('\n=== Smart Compile ===');
    console.log(await mcpCall('pine_smart_compile', {}));
    await new Promise(r => setTimeout(r, 3000));

    // Check errors
    console.log('\n=== Errors ===');
    console.log(await mcpCall('pine_get_errors', {}));

    // Chart state
    console.log('\n=== Chart State ===');
    console.log(await mcpCall('chart_get_state', {}));

    // Also list saved scripts to confirm
    console.log('\n=== Saved Scripts ===');
    console.log(await mcpCall('pine_list_scripts', {}));

    // Get console output
    console.log('\n=== Console ===');
    console.log(await mcpCall('pine_get_console', {}));

  } catch(e) {
    console.error('ERROR:', e.message);
  }
})();
