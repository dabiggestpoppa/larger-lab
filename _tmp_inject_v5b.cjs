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
    const code = fs.readFileSync('C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\quant-lab\\conversions\\pinescript\\CEREBUS_DMR_V5.pine', 'utf8');
    console.log('Loaded:', code.length, 'chars');

    // Click the Pine Editor button at top of screen
    console.log('1. Click Pine Editor button at (1206, 24)...');
    console.log(await mcpCall('ui_mouse_click', { x: 1206, y: 24 }));
    await new Promise(r => setTimeout(r, 3000));

    // Screenshot to confirm editor opened
    const ss1 = await mcpCall('capture_screenshot', { region: 'full', format: 'path', filename: 'tv_pe_open.png' });
    console.log('Screenshot:', ss1);

    // Now try set_source
    console.log('2. Set source...');
    const setResult = await mcpCall('pine_set_source', { source: code });
    console.log(setResult);
    
    const setObj = JSON.parse(setResult);
    if (!setObj.success) {
      console.log('Set source failed. Trying alternative: write to temp file and use keyboard...');
      
      // Write code to a temp file that can be loaded
      // Actually, let's try using the "Open" dialog in Pine Editor
      // First, try Ctrl+O to open file dialog
      // But that won't help since we need to load from our path
      
      // Alternative: use the clipboard approach
      // Write a small script that sets clipboard and pastes
      const tmpFile = 'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\_tmp_clipboard.js';
      fs.writeFileSync(tmpFile, `
        const { execSync } = require('child_process');
        const fs = require('fs');
        const code = fs.readFileSync('C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\quant-lab\\conversions\\pinescript\\CEREBUS_DMR_V5.pine', 'utf8');
        // Use PowerShell to set clipboard
        const escaped = code.replace(/\\$/g, '\\$').replace(/"/g, '\\"').replace(/\\n/g, '\\n');
        execSync('powershell -command "$text = \\"' + escaped + '\\"; [System.Windows.Forms.Clipboard]::SetText($text)"');
        console.log('Clipboard set with ' + code.length + ' chars');
      `);
      
      // Actually, let's try a simpler approach: use the existing working method from v4
      // The v4 injection worked when the editor was already open
      // Let's close and reopen properly
      console.log('Closing editor...');
      await mcpCall('ui_open_panel', { panel: 'pine-editor', action: 'close' });
      await new Promise(r => setTimeout(r, 2000));
      
      console.log('Opening editor fresh...');
      await mcpCall('ui_open_panel', { panel: 'pine-editor', action: 'open' });
      await new Promise(r => setTimeout(r, 3000));
      
      console.log('Trying set_source again...');
      const setResult2 = await mcpCall('pine_set_source', { source: code });
      console.log(setResult2);
    }

    await new Promise(r => setTimeout(r, 1000));

    // Compile
    console.log('3. Compile...');
    console.log(await mcpCall('pine_compile', {}));
    await new Promise(r => setTimeout(r, 3000));

    // Errors
    console.log('4. Errors:', await mcpCall('pine_get_errors', {}));

    // Chart state
    const state = JSON.parse(await mcpCall('chart_get_state', {}));
    console.log('5. Studies:', state.studies.map(s => s.name).join(', '));

  } catch (e) {
    console.error('ERR:', e.message);
  }
})();
