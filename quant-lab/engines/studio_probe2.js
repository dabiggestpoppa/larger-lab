// Deeper probe of TradeLocker Studio - find editor, backtest, and API calls
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
  await cdpSendRecv(ws, 'Page.enable');
  await cdpSendRecv(ws, 'DOM.enable');

  // 1. Find ALL iframes
  console.log('\n=== IFRAMES ===');
  const iframes = await cdpEval(ws, `
    Array.from(document.querySelectorAll('iframe')).map(f => f.src).join('\\n')
  `);
  console.log(iframes || 'none');

  // 2. Find the code editor (try multiple selectors)
  console.log('\n=== EDITOR SEARCH ===');
  const editorInfo = await cdpEval(ws, `
    (() => {
      // Try Monaco
      const monacoEditors = document.querySelectorAll('.monaco-editor');
      // Try CodeMirror
      const cm = document.querySelector('.CodeMirror');
      // Try Ace
      const ace = document.querySelector('.ace_editor');
      // Try any contenteditable or textarea
      const textarea = document.querySelector('textarea');
      // Try any code-like element
      const codeBlocks = document.querySelectorAll('[class*="editor"], [class*="Editor"], [class*="code"], [class*="Code"]');
      
      return {
        monacoCount: monacoEditors.length,
        hasCodeMirror: !!cm,
        hasAce: !!ace,
        hasTextarea: !!textarea,
        codeBlocks: Array.from(codeBlocks).slice(0, 10).map(e => e.className).join(', '),
        bodyElements: document.body.innerHTML.substring(0, 500)
      };
    })()
  `);
  console.log(JSON.stringify(editorInfo, null, 2));

  // 3. Get the full page HTML structure (key sections)
  console.log('\n=== PAGE STRUCTURE ===');
  const structure = await cdpEval(ws, `
    (() => {
      const body = document.body;
      function getStructure(el, depth) {
        if (depth > 4) return '';
        let result = '';
        const children = el.children;
        for (let i = 0; i < Math.min(children.length, 20); i++) {
          const c = children[i];
          const cls = c.className && typeof c.className === 'string' ? c.className.substring(0, 80) : '';
          const id = c.id ? '#' + c.id : '';
          const tag = c.tagName.toLowerCase();
          if (cls.includes('editor') || cls.includes('Editor') || cls.includes('code') || cls.includes('Code') || 
              cls.includes('backtest') || cls.includes('Backtest') || cls.includes('panel') || cls.includes('Panel') ||
              tag === 'textarea' || tag === 'iframe') {
            result += '  '.repeat(depth) + tag + id + '.' + cls + '\\n';
          }
          if (depth < 4) {
            result += getStructure(c, depth + 1);
          }
        }
        return result;
      }
      return getStructure(body, 0);
    })()
  `);
  console.log(structure);

  // 4. Check for XHR/fetch calls the page makes (intercept)
  console.log('\n=== NETWORK REQUESTS ===');
  await cdpSendRecv(ws, 'Network.enable');
  const requests = [];
  const reqHandler = (msg) => {
    const j = JSON.parse(msg.toString());
    if (j.method === 'Network.requestWillBeSent') {
      const url = j.params.request.url;
      if (url.includes('studio') || url.includes('api') || url.includes('file') || url.includes('process')) {
        requests.push(url);
      }
    }
  };
  ws.on('message', reqHandler);
  
  // Trigger a click to capture network requests - click on the editor area
  await cdpEval(ws, `
    (() => {
      // Click on the main content area to trigger any lazy loading
      const main = document.querySelector('main') || document.querySelector('[role="main"]');
      if (main) main.click();
      return 'clicked';
    })()
  `);
  
  await new Promise(r => setTimeout(r, 3000));
  ws.removeListener('message', reqHandler);
  
  console.log('Network requests captured:');
  requests.forEach(r => console.log('  ', r));

  // 5. Try to get the file content via the Studio engine API using the page's fetch context
  console.log('\n=== FILE CONTENT VIA FETCH ===');
  const fileContent = await cdpEval(ws, `
    (async () => {
      try {
        // The page should have access to the studio engine
        const resp = await fetch('http://localhost:53163/file/244fb7b9-a858-43d0-a25f-9941d88338fe/content');
        const data = await resp.json();
        return data.data ? data.data.substring(0, 500) : JSON.stringify(data).substring(0, 500);
      } catch(e) {
        return 'Error: ' + e.message;
      }
    })()
  `);
  console.log('File content:', fileContent);

  // 6. Get all visible text content in the main area
  console.log('\n=== MAIN CONTENT TEXT ===');
  const mainText = await cdpEval(ws, `
    (() => {
      const main = document.querySelector('[data-panel-group]') || document.querySelector('main');
      if (main) return main.textContent.substring(0, 1000);
      return document.body.textContent.substring(0, 1000);
    })()
  `);
  console.log(mainText);

  ws.close();
}

main().catch(e => { console.error(e); process.exit(1); });
