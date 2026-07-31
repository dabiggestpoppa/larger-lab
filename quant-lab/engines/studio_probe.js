// Probe TradeLocker Studio page via CDP
// Run: node studio_probe.js

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

async function cdpEval(ws, expression) {
  return new Promise((resolve, reject) => {
    const id = Math.floor(Math.random() * 1000000);
    const handler = (msg) => {
      const j = JSON.parse(msg.toString());
      if (j.id === id) {
        ws.removeListener('message', handler);
        if (j.result && j.result.result) {
          resolve(j.result.result.value);
        } else {
          resolve(j.result);
        }
      }
    };
    ws.on('message', handler);
    ws.send(JSON.stringify({
      id,
      method: 'Runtime.evaluate',
      params: { expression, returnByValue: true, awaitPromise: true }
    }));
    setTimeout(() => reject('timeout'), 10000);
  });
}

async function main() {
  const studio = await getStudioTarget();
  console.log('Studio target:', studio.title, studio.url);
  
  const ws = new WebSocket(studio.webSocketDebuggerUrl);
  await new Promise(r => ws.on('open', r));
  
  // Enable Runtime
  ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
  await new Promise(r => ws.on('message', r));
  
  // 1. Check for auth tokens in localStorage
  console.log('\n=== LOCALSTORAGE AUTH ===');
  const authKeys = await cdpEval(ws, `
    (() => {
      const keys = Object.keys(localStorage);
      return keys.filter(k => k.toLowerCase().includes('token') || k.toLowerCase().includes('auth') || k.toLowerCase().includes('session'));
    })()
  `);
  console.log('Auth-related keys:', JSON.stringify(authKeys));
  
  // 2. Get all localStorage keys
  console.log('\n=== ALL LOCALSTORAGE KEYS ===');
  const allKeys = await cdpEval(ws, `
    (() => {
      const keys = Object.keys(localStorage);
      return keys.slice(0, 30);
    })()
  `);
  console.log('Keys:', JSON.stringify(allKeys));
  
  // 3. Check for cookies
  console.log('\n=== COOKIES ===');
  const cookies = await cdpEval(ws, `
    document.cookie.substring(0, 200)
  `);
  console.log('Cookies:', cookies);
  
  // 4. Check for Monaco editor
  console.log('\n=== MONACO EDITOR ===');
  const monaco = await cdpEval(ws, `
    (() => {
      const editors = window.monaco && window.monaco.editor.getModels();
      if (editors) {
        return editors.map((e, i) => ({
          index: i,
          language: e.getLanguage(),
          valueLength: e.getValue().length,
          valuePreview: e.getValue().substring(0, 200)
        }));
      }
      // Check for CodeMirror
      const cm = document.querySelector('.CodeMirror');
      if (cm && cm.CodeMirror) {
        return [{ type: 'CodeMirror', value: cm.CodeMirror.getValue().substring(0, 200) }];
      }
      return { type: 'none', editors: 0 };
    })()
  `);
  console.log('Editor:', JSON.stringify(monaco, null, 2));
  
  // 5. Check for React/Next.js
  console.log('\n=== FRAMEWORK ===');
  const framework = await cdpEval(ws, `
    (() => {
      const hasReact = !!document.querySelector('[data-reactroot]') || !!document.querySelector('#__next');
      const hasNext = !!window.__NEXT_DATA__;
      const hasChakra = document.body.innerHTML.includes('chakra');
      return { hasReact, hasNext, hasChakra, title: document.title };
    })()
  `);
  console.log('Framework:', JSON.stringify(framework));
  
  // 6. Check for Studio globals
  console.log('\n=== STUDIO GLOBALS ===');
  const globals = await cdpEval(ws, `
    (() => {
      const result = {};
      if (window.isTradeLockerStudioEnabled !== undefined) result.isTradeLockerStudioEnabled = window.isTradeLockerStudioEnabled;
      if (window.studioPort !== undefined) result.studioPort = window.studioPort;
      if (window.__TRADELOCKER__ !== undefined) result.hasTradeLockerGlobal = true;
      if (window.__NEXT_DATA__ !== undefined) result.hasNextData = true;
      return result;
    })()
  `);
  console.log('Globals:', JSON.stringify(globals));
  
  // 7. Check for buttons
  console.log('\n=== BUTTONS ===');
  const buttons = await cdpEval(ws, `
    (() => {
      const btns = document.querySelectorAll('button');
      return Array.from(btns).slice(0, 20).map(b => b.textContent.trim()).filter(t => t.length > 0);
    })()
  `);
  console.log('Buttons:', JSON.stringify(buttons));
  
  // 8. Check for any existing bot code via the Studio engine API (from the page context)
  console.log('\n=== PROJECT INFO ===');
  const projectInfo = await cdpEval(ws, `
    (() => {
      // Check URL for project ID
      const url = window.location.href;
      const match = url.match(/bots\\/([a-f0-9-]+)/);
      return { url, projectId: match ? match[1] : null };
    })()
  `);
  console.log('Project:', JSON.stringify(projectInfo));
  
  ws.close();
}

main().catch(e => { console.error(e); process.exit(1); });
