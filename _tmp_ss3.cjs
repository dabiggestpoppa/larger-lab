const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');

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

function httpGet(url) {
  return new Promise((resolve, reject) => {
    http.get(url, res => { let d=''; res.on('data',c=>d+=c); res.on('end',()=>resolve(JSON.parse(d))); }).on('error', reject);
  });
}

(async () => {
  try {
    // Use CDP directly to get strategy tester DOM text
    const targets = await httpGet('http://localhost:9222/json');
    const tvTarget = targets.find(t => t.url && t.url.includes('tradingview.com'));
    
    // Get a screenshot with specific clip region (bottom panel only)
    console.log('=== Screenshot with clip: bottom panel ===');
    const ss1 = await mcpCall('capture_screenshot', { 
      region: 'chart',
      format: 'path'
    });
    console.log(ss1);

    // Try to get the strategy report HTML via CDP evaluate
    console.log('\n=== CDP: Extract strategy report text ===');
    
    // Read the saved screenshot and analyze
    const ss2 = await mcpCall('capture_screenshot', {
      region: 'full',
      format: 'path' 
    });
    console.log(ss2);
    
    // Also try to use the data tools to read strategy values
    console.log('\n=== Try data_get_study_values for strategy ===');
    const studyResult = await mcpCall('data_get_study_values', {
      study_name: 'CEREBUS DMR HYBRID v1',
      summary: true
    });
    console.log(studyResult);

  } catch(e) {
    console.error('ERROR:', e.message);
  }
})();
