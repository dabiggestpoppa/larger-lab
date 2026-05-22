const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const TV_DIR = 'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\tools\\tradingview-mcp';

// Use the capture_screenshot with a specific element target
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
    // Take a clean full screenshot and then we'll view it
    console.log('Taking full screenshot...');
    const ss = await mcpCall('capture_screenshot', {
      region: 'full',
      format: 'path'
    });
    console.log('Screenshot saved to:', ss);
    
    // Now let's try to use data_get_study_values
    console.log('\n=== Study values ===');
    const sv = await mcpCall('data_get_study_values', {
      study_name: 'CEREBUS DMR HYBRID v1'
    });
    console.log(sv);
    
    // Try to read pine labels
    console.log('\n=== Pine labels ===');
    const labels = await mcpCall('data_get_pine_labels', {
      study_filter: 'CEREBUS DMR HYBRID v1'
    });
    console.log(labels);

    // Try to read pine tables  
    console.log('\n=== Pine tables ===');
    const tables = await mcpCall('data_get_pine_tables', {
      study_filter: 'CEREBUS DMR HYBRID v1'
    });
    console.log(tables);

  } catch(e) {
    console.error('ERROR:', e.message);
  }
})();
