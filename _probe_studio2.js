const http = require('http');
const WebSocket = require('ws');

http.get('http://localhost:9222/json/list', (res) => {
  let data = '';
  res.on('data', (chunk) => data += chunk);
  res.on('end', () => {
    const targets = JSON.parse(data);
    const page = targets.find(t => t.url.includes('tradelocker.com'));
    if (!page) { console.log('No TL page'); process.exit(1); }
    
    const ws = new WebSocket(page.webSocketDebuggerUrl);
    let id = 1;
    
    ws.on('open', () => {
      // Probe Monaco editor and Studio engine API
      const expr = `
        (function() {
          const result = {};
          
          // === MONACO EDITOR ===
          try {
            const editors = window.monaco?.editor?.getEditors?.();
            result.monacoEditorCount = editors ? editors.length : 0;
            if (editors && editors.length > 0) {
              const ed = editors[0];
              result.monacoModel = ed.getModel() ? 'has model' : 'no model';
              result.monacoValue = ed.getValue() ? ed.getValue().substring(0, 500) : 'empty';
              result.monacoLanguage = ed.getModel() ? ed.getModel().getLanguageId() : 'N/A';
            }
          } catch(e) {
            result.monacoError = e.message;
          }
          
          // === STUDIO ENGINE API ===
          // The engine runs on localhost:53163
          // Let's check what endpoints it has
          result.studioPort = window.studioPort;
          result.isStudioEnabled = window.isTradeLockerStudioEnabled;
          
          // === REACT STATE ===
          // Try to find React fiber root
          const root = document.getElementById('__next');
          if (root) {
            const keys = Object.keys(root);
            const reactKeys = keys.filter(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
            result.reactFiberCount = reactKeys.length;
            result.hasReactRoot = true;
          }
          
          // === DOM STRUCTURE ===
          // Get the three-panel layout mentioned in the guide
          const panels = document.querySelectorAll('[class*="panel"], [class*="pane"], [class*="section"]');
          result.panelCount = panels.length;
          
          // Get all tabs
          const tabs = document.querySelectorAll('[class*="tab"], [role="tab"]');
          result.tabs = Array.from(tabs).map(t => t.textContent.trim()).filter(t => t.length > 0 && t.length < 50).slice(0, 20);
          
          // Get the code editor area
          const editorArea = document.querySelector('.monaco-editor');
          result.editorArea = editorArea ? {
            width: editorArea.offsetWidth,
            height: editorArea.offsetHeight,
            className: editorArea.className.substring(0, 100)
          } : null;
          
          // Get backtest panel
          const backtestPanel = document.querySelector('[class*="backtest"]');
          result.backtestPanel = backtestPanel ? {
            text: backtestPanel.textContent.trim().substring(0, 200),
            className: backtestPanel.className.substring(0, 100)
          } : null;
          
          // Check for the AI chat input
          const chatInput = document.querySelector('textarea, [contenteditable="true"], [class*="chat"]');
          result.chatInput = chatInput ? {
            tag: chatInput.tagName,
            className: chatInput.className.substring(0, 100),
            placeholder: chatInput.placeholder || chatInput.getAttribute('placeholder') || ''
          } : null;
          
          // Get all select/dropdown elements
          const selects = document.querySelectorAll('select, [class*="select"], [class*="dropdown"]');
          result.selectCount = selects.length;
          
          // Check for date range pickers, instrument selectors
          const datePickers = document.querySelectorAll('[class*="date"], [class*="range"], [class*="picker"]');
          result.datePickerCount = datePickers.length;
          
          const instrumentSelectors = document.querySelectorAll('[class*="instrument"], [class*="symbol"]');
          result.instrumentSelectorCount = instrumentSelectors.length;
          
          return JSON.stringify(result, null, 2);
        })()
      `;
      
      ws.send(JSON.stringify({
        id: id++,
        method: 'Runtime.evaluate',
        params: { expression: expr, returnByValue: true }
      }));
    });
    
    ws.on('message', (msg) => {
      const resp = JSON.parse(msg);
      if (resp.id) {
        const val = resp.result && resp.result.result ? resp.result.result.value : JSON.stringify(resp);
        console.log(val);
        ws.close();
      }
    });
  });
}).on('error', (e) => console.error(e.message));
