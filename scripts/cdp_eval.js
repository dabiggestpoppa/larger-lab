const WebSocket = require('ws');
const pageId = process.argv[2] || '69CD17E04C3F788E1DF56008A1B93F33';
const expr = process.argv[3] || 'document.title';
const wsUrl = `ws://localhost:9222/devtools/page/${pageId}`;
const ws = new WebSocket(wsUrl);
ws.on('open', () => {
  ws.send(JSON.stringify({id:1, method:'Runtime.evaluate', params:{expression: expr, returnByValue: true}}));
});
ws.on('message', (d) => {
  const m = JSON.parse(d);
  if(m.id===1) {
    console.log(JSON.stringify(m.result));
    ws.close();
    process.exit(0);
  }
});
ws.on('error', (e) => { console.error('WS Error:', e.message); process.exit(1); });
setTimeout(() => { console.error('Timeout'); process.exit(1); }, 5000);
