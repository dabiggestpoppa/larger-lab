// Intercept the WebSocket/Socket.IO connection to get the auth token
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
  await cdpSendRecv(ws, 'Network.enable');

  // 1. Intercept all network requests to capture auth headers
  console.log('\n=== INTERCEPTING ENGINE REQUESTS ===');
  const engineRequests = [];
  const netHandler = (msg) => {
    const j = JSON.parse(msg.toString());
    if (j.method === 'Network.requestWillBeSent') {
      const url = j.params.request.url;
      if (url.includes('53163') && !url.includes('sentry') && !url.includes('analytics') && !url.includes('log')) {
        engineRequests.push({
          method: j.params.request.method,
          url: url.substring(0, 300),
          headers: j.params.request.headers,
          postData: j.params.request.postData ? j.params.request.postData.substring(0, 500) : null
        });
      }
    }
    // Also capture WebSocket upgrade
    if (j.method === 'Network.webSocketCreated') {
      console.log('WebSocket created:', j.params.request.url);
    }
    if (j.method === 'Network.webSocketWillSendHandshakeRequest') {
      console.log('WS handshake headers:', JSON.stringify(j.params.request.headers));
    }
  };
  ws.on('message', netHandler);

  // 2. Try to get the auth token from the page's React state
  console.log('\n=== REACT STATE SEARCH ===');
  const reactState = await cdpEval(ws, `
    (() => {
      // Search through React fiber tree for API client or auth state
      const app = document.querySelector('#__next');
      if (!app) return { error: 'no __next' };
      
      // Get the React fiber
      const fiberKey = Object.keys(app).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
      if (!fiberKey) return { error: 'no fiber', keys: Object.keys(app).slice(0, 10) };
      
      const fiber = app[fiberKey];
      
      // Walk the fiber tree to find components with auth/API state
      const found = [];
      const queue = [fiber];
      let count = 0;
      while (queue.length > 0 && count < 200) {
        const f = queue.shift();
        count++;
        
        if (f.memoizedState) {
          // Check for auth-related state
          let state = f.memoizedState;
          let depth = 0;
          while (state && depth < 10) {
            if (state.memoizedState && state.memoizedState.auth) {
              found.push({ type: 'auth', depth });
            }
            if (state.queue && state.queue.lastRenderedState) {
              const lrs = state.queue.lastRenderedState;
              if (lrs && typeof lrs === 'object') {
                const lrsKeys = Object.keys(lrs).slice(0, 5);
                if (lrsKeys.some(k => k.includes('token') || k.includes('auth') || key.includes('session'))) {
                  found.push({ type: 'lrs', keys: lrsKeys, depth });
                }
              }
            }
            state = state.next;
            depth++;
          }
        }
        
        if (f.stateNode && f.stateNode.state) {
          const stateKeys = Object.keys(f.stateNode.state).slice(0, 5);
          if (stateKeys.some(k => k.includes('token') || k.includes('auth'))) {
            found.push({ type: 'componentState', keys: stateKeys });
          }
        }
        
        if (f.child) queue.push(f.child);
        if (f.sibling) queue.push(f.sibling);
      }
      
      return { found, fiberKey, count };
    })()
  `);
  console.log(JSON.stringify(reactState, null, 2));

  // 3. Try to find the token by intercepting the page's own API calls
  console.log('\n=== TOKEN FROM PAGE CONTEXT ===');
  const tokenInfo = await cdpEval(ws, `
    (async () => {
      // The page must store the engine token somewhere accessible
      // Let's check common patterns
      
      // 1. Check if there's a cookie for the engine
      const allCookies = document.cookie;
      
      // 2. Check if the page has a global API client
      const globals = [];
      for (const key of Object.keys(window)) {
        try {
          const val = window[key];
          if (val && typeof val === 'object' && val !== window && val !== document && val !== localStorage) {
            const str = JSON.stringify(val);
            if (str.includes('token') || str.includes('auth') || str.includes('bearer')) {
              globals.push(key);
            }
          }
        } catch(e) {}
      }
      
      // 3. Check if the page's HTML contains any tokens
      const html = document.documentElement.innerHTML;
      const tokenMatch = html.match(/token["\\s:=]+["']?([a-zA-Z0-9_\\-\\.]{20,})/);
      
      return { globals, tokenMatch: tokenMatch ? tokenMatch[1] : null, cookieLen: allCookies.length };
    })()
  `);
  console.log(JSON.stringify(tokenInfo));

  // 4. Try to use the page's own API by monkey-patching fetch
  console.log('\n=== MONKEY-PATCH FETCH ===');
  const monkeyResult = await cdpEval(ws, `
    (async () => {
      // Intercept the page's fetch to capture the auth header
      const origFetch = window.fetch;
      let capturedAuth = null;
      
      window._testFetch = async (url, opts) => {
        const resp = await origFetch(url, { ...opts, credentials: 'include' });
        const clone = resp.clone();
        try {
          const text = await clone.text();
          return { status: resp.status, body: text.substring(0, 500), url };
        } catch(e) {
          return { status: resp.status, error: e.message };
        }
      };
      
      // Also try to get the token from the page's XHR
      const origXHR = XMLHttpRequest.prototype.open;
      window._origXHR = origXHR;
      
      return 'patched';
    })()
  `);
  console.log('Monkey-patch result:', monkeyResult);

  // 5. Try to get the file content using the page's own fetch
  const fileResult = await cdpEval(ws, `
    (async () => {
      try {
        const resp = await window._testFetch('http://localhost:53163/file/244fb7b9-a858-43d0-a25f-9941d88338fe/content');
        return resp;
      } catch(e) {
        return { error: e.message };
      }
    })()
  `);
  console.log('\nFile via monkey-patch:', JSON.stringify(fileResult));

  // 6. Try to get the project info
  const projectResult = await cdpEval(ws, `
    (async () => {
      try {
        const resp = await window._testFetch('http://localhost:53163/project/244fb7b9-a858-43d0-a25f-9941d88338fe');
        return resp;
      } catch(e) {
        return { error: e.message };
      }
    })()
  `);
  console.log('\nProject via monkey-patch:', JSON.stringify(projectResult));

  // 7. Try to get all projects
  const allResult = await cdpEval(ws, `
    (async () => {
      try {
        const resp = await window._testFetch('http://localhost:53163/all_projects');
        return resp;
      } catch(e) {
        return { error: e.message };
      }
    })()
  `);
  console.log('\nAll projects via monkey-patch:', JSON.stringify(allResult));

  // Print captured engine requests
  console.log('\n=== CAPTURED ENGINE REQUESTS ===');
  engineRequests.forEach(r => {
    console.log(`  ${r.method} ${r.url}`);
    if (r.headers) console.log('    Headers:', JSON.stringify(r.headers));
    if (r.postData) console.log('    Body:', r.postData);
  });

  ws.removeListener('message', netHandler);
  ws.close();
}

main().catch(e => { console.error(e); process.exit(1); });
