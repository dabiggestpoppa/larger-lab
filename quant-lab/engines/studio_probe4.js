// Get auth token from the Studio page and understand the WebSocket/Socket.IO connection
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

  // 1. Get cookies for the engine API
  console.log('\n=== COOKIES ===');
  const cookies = await cdpEval(ws, `document.cookie`);
  console.log(cookies);

  // 2. Check for auth token in sessionStorage
  console.log('\n=== SESSIONSTORAGE ===');
  const sessionKeys = await cdpEval(ws, `
    (() => {
      const keys = Object.keys(sessionStorage);
      return keys.map(k => k + '=' + sessionStorage.getItem(k).substring(0, 100));
    })()
  `);
  console.log(JSON.stringify(sessionKeys, null, 2));

  // 3. Check for OIDC tokens
  console.log('\n=== OIDC TOKENS ===');
  const oidcTokens = await cdpEval(ws, `
    (() => {
      const keys = Object.keys(localStorage).filter(k => k.startsWith('oidc.'));
      return keys.map(k => {
        try {
          const val = JSON.parse(localStorage.getItem(k));
          return { key: k, token: val?.access_token?.substring(0, 50) + '...', hasToken: !!val?.access_token };
        } catch(e) {
          return { key: k, raw: localStorage.getItem(k)?.substring(0, 100) };
        }
      });
    })()
  `);
  console.log(JSON.stringify(oidcTokens, null, 2));

  // 4. Try to get the token from the page's own API client
  console.log('\n=== PAGE API CLIENT ===');
  const pageApi = await cdpEval(ws, `
    (async () => {
      // The page must have an internal API client that auths to the engine
      // Let's check for common patterns
      const result = {};
      
      // Check for axios instances
      if (window.axios) result.hasAxios = true;
      
      // Check for fetch wrapper
      if (window.__api) result.hasApi = true;
      
      // Check React fiber for API client
      const app = document.querySelector('#__next');
      if (app && app._reactRootContainer) {
        result.hasReactRoot = true;
      }
      
      // Look for the engine URL in the page source
      const html = document.documentElement.innerHTML;
      result.hasEngine53163 = html.includes('53163');
      result.hasStudioApi = html.includes('studio');
      
      return result;
    })()
  `);
  console.log(JSON.stringify(pageApi));

  // 5. Intercept WebSocket connections to understand how the page talks to the engine
  console.log('\n=== WEBSOCKET CONNECTIONS ===');
  await cdpSendRecv(ws, 'Network.enable');
  
  // Check if there are any WS connections
  const wsInfo = await cdpEval(ws, `
    (() => {
      // Check for Socket.IO
      if (window.io) return { hasIo: true, version: window.io.version };
      // Check for WebSocket
      return { hasIo: false, hasWebSocket: typeof WebSocket !== 'undefined' };
    })()
  `);
  console.log('WS Info:', JSON.stringify(wsInfo));

  // 6. Try to use the page's own Socket.IO connection to the engine
  console.log('\n=== SOCKET.IO TO ENGINE ===');
  const socketInfo = await cdpEval(ws, `
    (async () => {
      try {
        // The page connects to the engine via Socket.IO
        // Let's try to get the socket instance
        const keys = Object.keys(window).filter(k => k.toLowerCase().includes('socket') || k.toLowerCase().includes('io'));
        return { socketKeys: keys };
      } catch(e) {
        return { error: e.message };
      }
    })()
  `);
  console.log(JSON.stringify(socketInfo));

  // 7. Try to get auth from the page's fetch interceptor
  console.log('\n=== FETCH WITH CREDENTIALS ===');
  const fetchResult = await cdpEval(ws, `
    (async () => {
      try {
        // The page uses credentials: 'include' for same-origin requests
        // Let's try with the cookie we have
        const resp = await fetch('http://localhost:53163/all_projects', {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        const text = await resp.text();
        return { status: resp.status, body: text.substring(0, 500) };
      } catch(e) {
        return { error: e.message };
      }
    })()
  `);
  console.log(JSON.stringify(fetchResult));

  // 8. Check if the page has a token for the engine in its headers
  console.log('\n=== ENGINE REQUEST HEADERS ===');
  const headers = await cdpEval(ws, `
    (async () => {
      try {
        // Intercept what headers the page sends to the engine
        const origFetch = window.fetch;
        let capturedHeaders = null;
        window.fetch = function(...args) {
          const url = typeof args[0] === 'string' ? args[0] : args[0]?.url;
          if (url?.includes('53163')) {
            capturedHeaders = args[1]?.headers;
          }
          return origFetch.apply(this, args);
        };
        
        // Make a request to trigger header capture
        await fetch('http://localhost:53163/health/liveness', { credentials: 'include' });
        
        // Restore
        window.fetch = origFetch;
        
        return { capturedHeaders };
      } catch(e) {
        return { error: e.message };
      }
    })()
  `);
  console.log(JSON.stringify(headers));

  ws.close();
}

main().catch(e => { console.error(e); process.exit(1); });
