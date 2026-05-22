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

        // Init response
        if (parsed.id === 1 && parsed.result && !done) {
          done = true;
          const req = JSON.stringify({
            jsonrpc: '2.0', id: 2, method: 'tools/call',
            params: { name: toolName, arguments: argsObj }
          });
          mcp.stdin.write(req + '\n');
        }

        // Tool response
        if (parsed.id === 2) {
          mcp.kill();
          if (parsed.error) reject(new Error(JSON.stringify(parsed.error)));
          else if (parsed.result && parsed.result.content) {
            const texts = parsed.result.content.filter(c => c.type === 'text').map(c => c.text);
            resolve(texts.join('\n'));
          } else {
            resolve(JSON.stringify(parsed.result));
          }
        }
      }
    });

    mcp.stderr.on('data', () => {});
    mcp.stdin.write(JSON.stringify({
      jsonrpc: '2.0', id: 1, method: 'initialize',
      params: { protocolVersion: '2025-03-26', capabilities: {}, clientInfo: { name: 'OWL', version: '1.0' } }
    }) + '\n');

    setTimeout(() => { mcp.kill(); reject(new Error('Timeout calling ' + toolName)); }, 15000);
  });
}

(async () => {
  try {
    const pineCode = fs.readFileSync(
      'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\quant-lab\\conversions\\pinescript\\CEREBUS_DMR_HYBRID.pine', 'utf8'
    );
    console.log('Loaded ' + pineCode.length + ' chars');

    // Step 1: List available pine tools
    console.log('\n=== STEP 1: List tools ===');
    const mcp = spawn('node', [path.join(TV_DIR, 'src', 'server.js')], { stdio: ['pipe','pipe','pipe'] });
    let buf = '';
    mcp.stdout.on('data', d => {
      buf += d.toString();
      const lines = buf.split('\n');
      buf = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        let p; try { p = JSON.parse(line); } catch(e) { continue; }
        if (p.id === 1 && p.result) {
          mcp.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 3, method: 'tools/list', params: {} }) + '\n');
        }
        if (p.id === 3 && p.result && p.result.tools) {
          const pineTools = p.result.tools.filter(t => t.name.includes('pine') || t.name.includes('Pine'));
          console.log('Pine-related tools:');
          pineTools.forEach(t => console.log('  ' + t.name + ': ' + (t.description||'').substring(0,100)));
          mcp.kill();
          
          // Now inject
          injectHybrid(pineCode);
        }
      }
    });
    mcp.stderr.on('data', () => {});
    mcp.stdin.write(JSON.stringify({
      jsonrpc: '2.0', id: 1, method: 'initialize',
      params: { protocolVersion: '2025-03-26', capabilities: {}, clientInfo: { name: 'x', version: '1' } }
    }) + '\n');

  } catch(e) {
    console.error('FATAL:', e.message);
  }
})();

async function injectHybrid(pineCode) {
  try {
    console.log('\n=== STEP 2: Open Pine Editor ===');
    console.log(await mcpCall('ui_open_panel', { panel: 'pine-editor', action: 'open' }));
    await new Promise(r => setTimeout(r, 3000));

    console.log('\n=== STEP 3: Set Pine Source ===');
    console.log(await mcpCall('pine_set_source', { source: pineCode }));
    await new Promise(r => setTimeout(r, 2000));

    console.log('\n=== STEP 4: Compile ===');
    console.log(await mcpCall('pine_compile', {}));

    console.log('\n=== STEP 5: Get Errors ===');
    console.log(await mcpCall('pine_get_errors', {}));

    console.log('\n=== STEP 6: Chart State ===');
    console.log(await mcpCall('chart_get_state', {}));

    console.log('\n=== COMPLETE: Check TradingView for DMR HYBRID strategy ===');
  } catch(e) {
    console.error('Inject error:', e.message);
  }
}
