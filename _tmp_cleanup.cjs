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
        if (p.id === 1 && p.result && !done) { done = true; mcp.stdin.write(JSON.stringify({jsonrpc:'2.0',id:2,method:'tools/call',params:{name:toolName,arguments:argsObj}}) + '\n'); }
        if (p.id === 2) { mcp.kill(); p.error ? reject(new Error(JSON.stringify(p.error))) : resolve(p.result.content ? p.result.content.filter(c=>c.type==='text').map(c=>c.text).join('\n') : JSON.stringify(p.result)); }
      }
    });
    mcp.stderr.on('data', () => {});
    mcp.stdin.write(JSON.stringify({jsonrpc:'2.0',id:1,method:'initialize',params:{protocolVersion:'2025-03-26',capabilities:{},clientInfo:{name:'x',version:'1'}}}) + '\n');
    setTimeout(() => { mcp.kill(); reject(new Error('Timeout')); }, 30000);
  });
}

(async () => {
  try {
    // Get current state
    const state = JSON.parse(await mcpCall('chart_get_state', {}));
    console.log('Current studies:');
    for (const s of state.studies) {
      console.log('  ' + s.id + ' = ' + s.name);
    }

    // Remove duplicate DMR v2 (keep first, remove second)
    const dmr2Studies = state.studies.filter(s => s.name === 'CEREBUS DMR v2');
    if (dmr2Studies.length > 1) {
      console.log('\nRemoving duplicate DMR v2:', dmr2Studies[1].id);
      console.log(await mcpCall('chart_manage_indicator', { action: 'remove', name: dmr2Studies[1].id }));
      await new Promise(r => setTimeout(r, 1000));
    }

    // Remove DMR HYBRID v1
    const hybrid = state.studies.find(s => s.name === 'CEREBUS DMR HYBRID v1');
    if (hybrid) {
      console.log('Removing HYBRID v1:', hybrid.id);
      console.log(await mcpCall('chart_manage_indicator', { action: 'remove', name: hybrid.id }));
      await new Promise(r => setTimeout(r, 1000));
    }

    // Remove duplicate V5 LIVE
    const v5 = state.studies.filter(s => s.name.includes('V5 LIVE'));
    if (v5.length > 1) {
      console.log('Removing duplicate V5:', v5[1].id);
      console.log(await mcpCall('chart_manage_indicator', { action: 'remove', name: v5[1].id }));
    }

    // Now verify clean state
    await new Promise(r => setTimeout(r, 2000));
    const state2 = JSON.parse(await mcpCall('chart_get_state', {}));
    console.log('\nClean studies:');
    for (const s of state2.studies) {
      console.log('  ' + s.id + ' = ' + s.name);
    }

    // Open Strategy Tester
    console.log('\nOpening Strategy Tester...');
    console.log(await mcpCall('ui_open_panel', { panel: 'strategy-tester', action: 'open' }));
    await new Promise(r => setTimeout(r, 3000));

    // Screenshot
    console.log('\nTaking screenshot...');
    const ss = await mcpCall('capture_screenshot', { region: 'full', format: 'path' });
    console.log('Screenshot:', ss);

  } catch(e) {
    console.error('ERROR:', e.message);
  }
})();
