const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const tvDir = 'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\tools\\tradingview-mcp';
const tvCall = path.join(tvDir, 'tv-call.cjs');

function callTV(tool) {
  const argsFile = path.join(tvDir, '_args_' + process.pid + '.json');
  fs.writeFileSync(argsFile, '{}');
  return new Promise((resolve, reject) => {
    const proc = spawn('node', [tvCall, tool, '@' + argsFile], { stdio: 'pipe' });
    let out = '';
    proc.stdout.on('data', d => out += d);
    proc.stderr.on('data', () => {});
    proc.on('close', code => {
      try { fs.unlinkSync(argsFile); } catch(e) {}
      code === 0 ? resolve(out.trim()) : reject(new Error('Exit ' + code + ': ' + out));
    });
  });
}

(async () => {
  // First list available tools
  const mcp = spawn('node', [path.join(tvDir, 'src', 'server.js')], { stdio: 'pipe' });
  let buffer = '';

  mcp.stdout.on('data', async (data) => {
    buffer += data.toString();
    const lines = buffer.split('\n');
    buffer = lines.pop();
    
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const parsed = JSON.parse(line);
        
        if (parsed.id === 1 && parsed.result) {
          // Got init, request tools list
          mcp.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 2, method: 'tools/list', params: {} }) + '\n');
        }
        
        if (parsed.id === 2 && parsed.result && parsed.result.tools) {
          console.log('AVAILABLE TOOLS (' + parsed.result.tools.length + '):');
          for (const t of parsed.result.tools) {
            console.log('  ' + t.name + ': ' + (t.description || '').substring(0, 80));
          }
          mcp.kill();
          
          // Now inject the hybrid
          console.log('\n--- INJECTING CEREBUS DMR HYBRID ---');
          const pineCode = fs.readFileSync('C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\quant-lab\\conversions\\pinescript\\CEREBUS_DMR_HYBRID.pine', 'utf8');
          console.log('Pine code: ' + pineCode.length + ' chars');
          
          // Step 1: open pine editor
          console.log('\n1. Open Pine Editor');
          console.log(await callTV('ui_open_panel', {}));
          
          process.exit(0);
        }
      } catch(e) {}
    }
  });
  
  mcp.stderr.on('data', () => {});
  mcp.stdin.write(JSON.stringify({
    jsonrpc: '2.0', id: 1, method: 'initialize',
    params: { protocolVersion: '2025-03-26', capabilities: {}, clientInfo: { name: 'list', version: '1.0' } }
  }) + '\n');
  
  setTimeout(() => { mcp.kill(); process.exit(1); }, 10000);
})();
