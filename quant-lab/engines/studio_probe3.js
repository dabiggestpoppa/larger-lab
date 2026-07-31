// Get the full bot code from the Monaco editor and understand the Studio API
const http = require('http');
const WebSocket = require('ws');

async function getStudioTarget() {
  return new Promise((resolve, reject) => {
    http.get('http://localhost:9222/json/list', (res) => {
      let d = ''; res.on('data', c => d += c);
      res.on('end', () => {
        const targets = JSON.parse(d);
        const studio = targets.find(t => t.url.includes('studio'));
        if (studio) resolve(studio);
        else reject('No studio target found');
      });
    }).on('error', reject);
  });
}

let msgId = 0;
async function cdpSendRecv(ws, method, params) {
  return new Promise((resolve, reject) => {
    const id = ++msgId;
    const handler = (msg) => {
      const j = JSON.parse(msg.toString());
      if (j.id === id) {
        ws.removeListener('message', handler);
        resolve(j.result);
      }
    };
    ws.on('message', handler);
    ws.send(JSON.stringify({ id, method, params: params || {} }));
    setTimeout(() => { ws.removeListener('message', handler); reject('timeout'); }, 15000);
  });
}

async function cdpEval(ws, expression) {
  const r = await cdpSendRecv(ws, 'Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (r && r.result) return r.result.value;
  return r;
}

async function main() {
  const studio = await getStudioTarget();
  const ws = new WebSocket(studio.webSocketDebuggerUrl);
  await new Promise(r => ws.on('open', r));
  await cdpSendRecv(ws, 'Runtime.enable');

  // 1. Get the full Monaco editor content
  console.log('\n=== FULL BOT CODE ===');
  const botCode = await cdpEval(ws, `
    (() => {
      const editors = window.monaco && window.monaco.editor.getModels();
      if (editors && editors.length > 0) {
        return editors[0].getValue();
      }
      return 'No editor content found';
    })()
  `);
  console.log(botCode);

  // 2. Get all editor models (there might be multiple tabs)
  console.log('\n=== ALL EDITOR MODELS ===');
  const allModels = await cdpEval(ws, `
    (() => {
      const editors = window.monaco && window.monaco.editor.getModels();
      if (editors) {
        return editors.map((e, i) => ({
          index: i,
          language: e.getLanguage(),
          uri: e.uri.toString(),
          valueLength: e.getValue().length,
          value: e.getValue()
        }));
      }
      return [];
    })()
  `);
  console.log(JSON.stringify(allModels, null, 2));

  // 3. Check the page's JavaScript context for Studio API
  console.log('\n=== STUDIO API GLOBALS ===');
  const apiGlobals = await cdpEval(ws, `
    (() => {
      const result = {};
      // Check for common Studio API patterns
      for (const key of Object.keys(window)) {
        if (key.startsWith('__') || key.includes('studio') || key.includes('Studio') || 
            key.includes('tradelocker') || key.includes('TradeLocker') ||
            key.includes('api') || key.includes('API') || key.includes('engine')) {
          const val = window[key];
          result[key] = typeof val === 'function' ? 'function' : 
                        typeof val === 'object' ? JSON.stringify(val).substring(0, 200) : val;
        }
      }
      return result;
    })()
  `);
  console.log(JSON.stringify(apiGlobals, null, 2));

  // 4. Intercept the page's fetch calls to understand the API
  console.log('\n=== INTERCEPTED API CALLS ===');
  await cdpSendRecv(ws, 'Network.enable');
  const apiCalls = [];
  const reqHandler = (msg) => {
    const j = JSON.parse(msg.toString());
    if (j.method === 'Network.requestWillBeSent') {
      const url = j.params.request.url;
      const method = j.params.request.method;
      const body = j.params.request.postData;
      if (url.includes('localhost:53163') || url.includes('studio') || url.includes('api.tradelocker')) {
        apiCalls.push({ method, url: url.substring(0, 200), body: body ? body.substring(0, 200) : null });
      }
    }
  };
  ws.on('message', reqHandler);

  // Try to get the file content via the page's own fetch (which has auth)
  const fileData = await cdpEval(ws, `
    (async () => {
      try {
        const resp = await fetch('http://localhost:53163/file/244fb7b9-a858-43d0-a25f-9941d88338fe/content', {
          credentials: 'include'
        });
        const data = await resp.json();
        return JSON.stringify(data).substring(0, 1000);
      } catch(e) {
        return 'Error: ' + e.message;
      }
    })()
  `);
  console.log('File data via page fetch:', fileData);

  // 5. Try to get project info
  const projectData = await cdpEval(ws, `
    (async () => {
      try {
        const resp = await fetch('http://localhost:53163/project/244fb7b9-a858-43d0-a25f-9941d88338fe', {
          credentials: 'include'
        });
        const data = await resp.json();
        return JSON.stringify(data, null, 2).substring(0, 1000);
      } catch(e) {
        return 'Error: ' + e.message;
      }
    })()
  `);
  console.log('\nProject data:', projectData);

  // 6. Try to get all projects
  const allProjects = await cdpEval(ws, `
    (async () => {
      try {
        const resp = await fetch('http://localhost:53163/all_projects', {
          credentials: 'include'
        });
        const data = await resp.json();
        return JSON.stringify(data, null, 2).substring(0, 1000);
      } catch(e) {
        return 'Error: ' + e.message;
      }
    })()
  `);
  console.log('\nAll projects:', allProjects);

  ws.removeListener('message', reqHandler);

  // 7. Print captured API calls
  console.log('\n=== CAPTURED API CALLS ===');
  apiCalls.forEach(c => console.log(`  ${c.method} ${c.url}`));

  ws.close();
}

main().catch(e => { console.error(e); process.exit(1); });
