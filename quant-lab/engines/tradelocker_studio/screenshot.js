const http = require('http');
const WebSocket = require('ws');
const fs = require('fs');

http.get('http://localhost:9222/json/list', (res) => {
  let d=''; res.on('data',c=>d+=c);
  res.on('end',()=>{
    const targets = JSON.parse(d);
    const studio = targets.find(t => t.url.includes('studio'));
    if (!studio) { console.log('no studio'); process.exit(1); }
    console.log('Studio:', studio.title, studio.url);
    const ws = new WebSocket(studio.webSocketDebuggerUrl);
    ws.on('open', () => {
      ws.send(JSON.stringify({id:1, method:'Page.captureScreenshot', params:{format:'png'}}));
    });
    ws.on('message', (msg) => {
      const j = JSON.parse(msg);
      if (j.id === 1 && j.result && j.result.data) {
        fs.writeFileSync('studio_screenshot.png', Buffer.from(j.result.data, 'base64'));
        console.log('Screenshot saved: studio_screenshot.png (' + j.result.data.length + ' bytes)');
        ws.close();
        process.exit(0);
      }
    });
  });
}).on('error',e=>console.error(e.message));
