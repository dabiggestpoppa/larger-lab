const { spawn } = require('child_process');
const fs = require('fs');
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
    const code = fs.readFileSync('C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\quant-lab\\conversions\\pinescript\\CEREBUS_DMR_V4.pine', 'utf8');
    console.log('Loaded:', code.length, 'chars,', code.split('\n').length, 'lines');

    // Close editor
    console.log('1. Close editor...');
    console.log(await mcpCall('ui_open_panel', { panel: 'pine-editor', action: 'close' }));
    await new Promise(r => setTimeout(r, 2000));

    // Open editor fresh
    console.log('2. Open editor...');
    console.log(await mcpCall('ui_open_panel', { panel: 'pine-editor', action: 'open' }));
    await new Promise(r => setTimeout(r, 3000));

    // Set source
    console.log('3. Set source...');
    const setResult = await mcpCall('pine_set_source', { source: code });
    console.log(setResult);

    // If set_source failed, try using keyboard shortcut to select all and paste
    const setObj = JSON.parse(setResult);
    if (!setObj.success) {
      console.log('Set source failed, trying keyboard approach...');
      // Ctrl+A to select all
      await mcpCall('ui_keyboard', { key: 'a', modifiers: ['ctrl'] });
      await new Promise(r => setTimeout(r, 500));
      // Type the code (won't work for large code)
      console.log('Cannot use keyboard approach for large code. Will try DOM manipulation.');
    }

    await new Promise(r => setTimeout(r, 1000));

    // Compile
    console.log('4. Compile...');
    console.log(await mcpCall('pine_compile', {}));
    await new Promise(r => setTimeout(r, 3000));

    // Errors
    console.log('5. Errors:', await mcpCall('pine_get_errors', {}));

    // Console
    const con = await mcpCall('pine_get_console', {});
    console.log('6. Console:', con.substring(con.length - 300));

    // Chart state
    const state = JSON.parse(await mcpCall('chart_get_state', {}));
    console.log('7. Studies:', state.studies.map(s => s.name).join(', '));

  } catch (e) {
    console.error('ERR:', e.message);
  }
})();
