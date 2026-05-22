const { spawn } = require('child_process');
const path = require('path');
const TV_DIR = 'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\tools\\tradingview-mcp';

async function mcpCall(toolName, argsObj) {
  return new Promise((resolve, reject) => {
    const mcp = spawn('node', [path.join(TV_DIR, 'src', 'server.js')], { stdio: ['pipe','pipe','pipe'] });
    let buffer = ''; let done = false;
    mcp.stdout.on('data', data => {
      buffer += data.toString();
      const lines = buffer.split('\n'); buffer = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        let p; try { p = JSON.parse(line); } catch(e) { continue; }
        if (p.id === 1 && p.result && !done) { done = true; mcp.stdin.write(JSON.stringify({ jsonrpc:'2.0', id:2, method:'tools/call', params:{name:toolName,arguments:argsObj} }) + '\n'); }
        if (p.id === 2) { mcp.kill(); p.error ? reject(new Error(JSON.stringify(p.error))) : resolve(p.result.content ? p.result.content.filter(c=>c.type==='text').map(c=>c.text).join('\n') : JSON.stringify(p.result)); }
      }
    });
    mcp.stderr.on('data', () => {});
    mcp.stdin.write(JSON.stringify({ jsonrpc:'2.0', id:1, method:'initialize', params:{protocolVersion:'2025-03-26',capabilities:{},clientInfo:{name:'OWL',version:'1.0'}} }) + '\n');
    setTimeout(() => { mcp.kill(); reject(new Error('Timeout')); }, 30000);
  });
}

(async () => {
  try {
    // Check chart state
    const state = JSON.parse(await mcpCall('chart_get_state', {}));
    console.log('Studies:', state.studies.map(s => s.name + ' [' + s.id + ']').join('\n  '));
  } catch(e) { console.error(e.message); }
})();
