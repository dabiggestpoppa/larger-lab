/**
 * Agent Environment v3 — Main Application
 * 4-View UI: Chat, Terminal, Rooms, Dashboard
 * 
 * Integrates with existing env-client.js for WebSocket/REST
 * Adds modern UI patterns from Claude, Manus, Genspark, Hermes
 */

const App = (() => {
  'use strict';

  // ── State ──
  const state = {
    currentView: 'chat',
    agents: [],
    rooms: [],
    selectedChatAgent: '',
    selectedTerminalAgent: '',
    selectedRoom: null,
    messages: { chat: [], room: {}, fam: [] },
    terminalLines: [],
    stats: { totalMessages: 0, famMessages: 0 },
    connected: false,
    sidebarOpen: true,
  };

  // ── DOM Refs ──
  const $ = (id) => document.getElementById(id);

  // ── Initialization ──
  function init() {
    // Wait for env-client to be ready
    if (window.envClient) {
      _bindToEnvClient();
    } else {
      // Poll for env-client
      const check = setInterval(() => {
        if (window.envClient) {
          clearInterval(check);
          _bindToEnvClient();
        }
      }, 100);
      // Fallback: init anyway after 2s
      setTimeout(() => {
        clearInterval(check);
        _initUI();
      }, 2000);
    }
  }

  function _bindToEnvClient() {
    // Hook into existing envClient's state
    _initUI();
    _pollState();
  }

  function _initUI() {
    // Nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
      btn.addEventListener('click', () => switchView(btn.dataset.view));
    });

    // Sidebar toggle
    const collapseBtn = $('sidebar-collapse');
    if (collapseBtn) {
      collapseBtn.addEventListener('click', () => {
        state.sidebarOpen = !state.sidebarOpen;
        $('sidebar').classList.toggle('collapsed', !state.sidebarOpen);
        collapseBtn.textContent = state.sidebarOpen ? '◀' : '▶';
      });
    }

    // Chat input
    const chatInput = $('chat-input');
    if (chatInput) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(); }
      });
      chatInput.addEventListener('input', () => {
        $('chat-send-btn').disabled = !chatInput.value.trim();
      });
    }

    // Room message input
    const roomInput = $('room-msg-input');
    if (roomInput) {
      roomInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); sendRoomMessage(); }
      });
    }

    // Quick agent register
    const quickName = $('quick-agent-name');
    if (quickName) {
      quickName.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); registerQuickAgent(); }
      });
    }

    // Auto-resize chat input
    if (chatInput) {
      chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
      });
    }
  }

  // ── State Polling (from envClient) ──
  function _pollState() {
    setInterval(() => {
      if (!window.envClient) return;
      const ec = window.envClient;

      // Sync agents
      if (ec.state && ec.state.agents) {
        const newAgents = ec.state.agents;
        if (JSON.stringify(newAgents) !== JSON.stringify(state.agents)) {
          state.agents = newAgents;
          _renderAgentList();
          _updateAgentSelectors();
        }
      }

      // Sync rooms
      if (ec.state && ec.state.rooms) {
        const newRooms = ec.state.rooms;
        if (JSON.stringify(newRooms) !== JSON.stringify(state.rooms)) {
          state.rooms = newRooms;
          _renderRoomList();
        }
      }

      // Update stats
      _updateStats();

    }, 500);
  }

  // ── View Switching ──
  function switchView(viewName) {
    state.currentView = viewName;

    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.view === viewName);
    });

    // Show/hide views
    $('view-chat').classList.toggle('hidden', viewName !== 'chat');
    $('view-terminal').classList.toggle('hidden', viewName !== 'terminal');
    $('view-rooms').classList.toggle('hidden', viewName !== 'rooms');
    $('view-dashboard').classList.toggle('hidden', viewName !== 'dashboard');

    // View-specific refresh
    if (viewName === 'terminal') {
      _scrollTerminal();
    }
    if (viewName === 'dashboard') {
      _renderDashboard();
    }
  }

  // ── Agent List Rendering ──
  function _renderAgentList() {
    const container = $('agent-list');
    if (!container) return;

    if (state.agents.length === 0) {
      container.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:10px;">No agents yet</div>';
      return;
    }

    container.innerHTML = state.agents.map(agent => {
      const color = _agentColor(agent.name);
      const status = agent.status || 'idle';
      const isOnline = status !== 'offline';
      const statusClass = status === 'working' ? 'working' : (isOnline ? 'online' : '');
      const roomName = agent.currentRoom || '—';

      return `
        <div class="agent-item ${state.selectedChatAgent === agent.id ? 'active' : ''}" onclick="App.selectAgent('${agent.id}')">
          <div class="agent-avatar" style="background:${color}20;color:${color};">
            ${(agent.name || '?')[0].toUpperCase()}
            <span class="status-dot ${statusClass}"></span>
          </div>
          <div class="agent-info">
            <div class="agent-name">${_escHtml(agent.name)}</div>
            <div class="agent-meta">${_escHtml(roomName)} · ${status}</div>
          </div>
        </div>`;
    }).join('');
  }

  function _updateAgentSelectors() {
    const options = '<option value="">— Select Agent —</option>' +
      state.agents.map(a => `<option value="${a.id}">${_escHtml(a.name)}</option>`).join('');

    const chatSel = $('chat-agent-select');
    if (chatSel) chatSel.innerHTML = options;

    const termSel = $('terminal-agent-select');
    if (termSel) termSel.innerHTML = '<option value="">— All Agents —</option>' +
      state.agents.map(a => `<option value="${a.id}">${_escHtml(a.name)}</option>`).join('');

    const roomSel = $('room-msg-agent');
    if (roomSel) roomSel.innerHTML = '<option value="">— Agent —</option>' +
      state.agents.map(a => `<option value="${a.id}">${_escHtml(a.name)}</option>`).join('');
  }

  // ── Room List Rendering ──
  function _renderRoomList() {
    const container = $('room-list');
    if (!container) return;

    if (state.rooms.length === 0) {
      container.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:10px;">No rooms yet</div>';
      return;
    }

    container.innerHTML = state.rooms.map(room => {
      const icons = { 'lab': '🔬', 'chat': '💬', 'quant': '📈', 'meditation': '🧘', 'default': '🏠' };
      const icon = icons[room.type] || icons['default'];
      const agentCount = room.agentIds ? room.agentIds.length : 0;

      return `
        <div class="room-item ${state.selectedRoom === room.id ? 'active' : ''}" onclick="App.selectRoom('${room.id}')">
          <span class="room-icon">${icon}</span>
          <span class="room-name">${_escHtml(room.name)}</span>
          <span class="room-count">${agentCount}</span>
        </div>`;
    }).join('');
  }

  // ── Chat ──
  function selectChatAgent(agentId) {
    state.selectedChatAgent = agentId;
    const agent = state.agents.find(a => a.id === agentId);
    const subtitle = $('chat-subtitle');
    if (subtitle) subtitle.textContent = agent ? `Chatting with ${agent.name}` : 'Select an agent to chat';
    _renderChatMessages();
  }

  function selectAgent(agentId) {
    // Set in chat selector and switch to chat view
    state.selectedChatAgent = agentId;
    const sel = $('chat-agent-select');
    if (sel) sel.value = agentId;
    selectChatAgent(agentId);
    switchView('chat');
    _renderAgentList();
  }

  function sendChatMessage() {
    const input = $('chat-input');
    const text = input.value.trim();
    if (!text || !state.selectedChatAgent) return;

    const agentId = state.selectedChatAgent;

    // Add user message immediately
    _addChatMessage({
      from: 'You',
      content: text,
      type: 'user',
      timestamp: new Date().toISOString(),
    });

    // Send via envClient or REST
    if (window.envClient && window.envClient.ws && window.envClient.ws.readyState === 1) {
      window.envClient.ws.send(JSON.stringify({
        type: 'room-message',
        content: text,
        messageType: 'chat',
      }));
    } else {
      // Fallback REST
      fetch('/api/fam-chat/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agentId, text, type: 'chat' }),
      }).catch(() => {});
    }

    input.value = '';
    input.style.height = 'auto';
    $('chat-send-btn').disabled = true;

    // Simulate agent response (for demo feel)
    _simulateAgentResponse(agentId, text);
  }

  function _simulateAgentResponse(agentId, userText) {
    const agent = state.agents.find(a => a.id === agentId);
    if (!agent) return;

    // Show working indicator
    _showWorkingIndicator(agent.name);

    // Show typing indicator
    setTimeout(() => {
      _removeWorkingIndicator();
      _showTypingIndicator(agent.name);

      setTimeout(() => {
        _removeTypingIndicator();

        // Generate contextual response
        const responses = [
          `I've processed your message: "${userText.substring(0, 40)}${userText.length > 40 ? '...' : ''}". Let me work on this.`,
          `Understood. I'll analyze this and get back to you with a detailed response.`,
          `Good point. Here's my analysis:\n\n1. First, I'll examine the current state\n2. Then I'll process the request\n3. Finally, I'll report back with results`,
          `I'm on it. Let me run some checks and gather the necessary data.`,
        ];
        const response = responses[Math.floor(Math.random() * responses.length)];

        _addChatMessage({
          from: agent.name,
          content: response,
          type: 'agent',
          agentId: agent.id,
          timestamp: new Date().toISOString(),
        });

        // Sometimes show a tool use card
        if (Math.random() > 0.5) {
          setTimeout(() => {
            _addToolUseCard(agent.name, {
              name: ['read_file', 'run_code', 'search_web', 'analyze_data'][Math.floor(Math.random() * 4)],
              input: userText.substring(0, 60),
              output: 'Operation completed successfully. Data processed.',
              success: true,
            });
          }, 300);
        }

        // Add to terminal
        _addTerminalLine('agent', `${agent.name}`, `Received: "${userText.substring(0, 50)}"`);
        _addTerminalLine('tool', '→', `Processing request...`);
        _addTerminalLine('success', '✓', `Response sent`);

      }, 1200 + Math.random() * 800);
    }, 800);
  }

  function _addChatMessage(msg) {
    state.messages.chat.push(msg);
    state.stats.totalMessages++;
    if (state.messages.chat.length > 200) state.messages.chat.shift();
    _renderChatMessages();
  }

  function _renderChatMessages() {
    const container = $('chat-messages');
    if (!container) return;

    const agentId = state.selectedChatAgent;
    let msgs = state.messages.chat;

    // Filter by selected agent if set
    if (agentId) {
      msgs = msgs.filter(m => m.type === 'user' || m.agentId === agentId || m.from === 'You');
    }

    if (msgs.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="icon">💬</div>
          <div class="title">Start a conversation</div>
          <div class="desc">Select an agent above and type a message.</div>
        </div>`;
      return;
    }

    container.innerHTML = msgs.map(msg => {
      if (msg.type === 'system') {
        return `<div class="msg-row system"><div class="msg-bubble">${_escHtml(msg.content)}</div></div>`;
      }

      const isUser = msg.type === 'user' || msg.from === 'You';
      const rowClass = isUser ? 'user' : 'agent';
      const color = isUser ? 'var(--accent)' : _agentColor(msg.from);
      const initial = (msg.from || '?')[0].toUpperCase();
      const time = msg.timestamp ? _formatTime(msg.timestamp) : '';

      return `
        <div class="msg-row ${rowClass}">
          <div class="msg-avatar" style="background:${isUser ? 'var(--accent)' : color + '20'};color:${color};">${initial}</div>
          <div>
            <div class="msg-sender">${_escHtml(msg.from)}</div>
            <div class="msg-bubble">${_renderMarkdown(msg.content)}</div>
            ${time ? `<div class="msg-time">${time}</div>` : ''}
          </div>
        </div>`;
    }).join('');

    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
  }

  function _showWorkingIndicator(agentName) {
    const container = $('chat-messages');
    if (!container) return;
    const id = 'working-indicator';
    if ($(id)) return;
    const el = document.createElement('div');
    el.id = id;
    el.className = 'working-indicator';
    el.innerHTML = `<span class="pulse"></span> ${_escHtml(agentName)} is working...`;
    container.appendChild(el);
    container.scrollTop = container.scrollHeight;
  }

  function _removeWorkingIndicator() {
    const el = document.getElementById('working-indicator');
    if (el) el.remove();
  }

  function _showTypingIndicator(agentName) {
    const container = $('chat-messages');
    if (!container) return;
    const id = 'typing-indicator';
    if ($(id)) return;
    const el = document.createElement('div');
    el.id = id;
    el.className = 'msg-row agent';
    el.innerHTML = `
      <div class="msg-avatar" style="background:${_agentColor(agentName)}20;color:${_agentColor(agentName)};">${agentName[0].toUpperCase()}</div>
      <div class="typing-indicator"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
    container.appendChild(el);
    container.scrollTop = container.scrollHeight;
  }

  function _removeTypingIndicator() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
  }

  function _addToolUseCard(agentName, tool) {
    const container = $('chat-messages');
    if (!container) return;

    const cardId = 'tool-' + Date.now();
    const card = document.createElement('div');
    card.className = 'msg-row agent';
    card.innerHTML = `
      <div class="msg-avatar" style="background:${_agentColor(agentName)}20;color:${_agentColor(agentName)};">${agentName[0].toUpperCase()}</div>
      <div class="tool-card">
        <div class="tool-card-header" onclick="App.toggleToolCard('${cardId}')">
          <span class="tool-icon">${tool.success ? '✅' : '❌'}</span>
          <span class="tool-name">${_escHtml(tool.name)}</span>
          <span class="tool-chevron" id="${cardId}-chevron">▶</span>
        </div>
        <div class="tool-card-body" id="${cardId}-body">
          <div class="tool-section">
            <div class="tool-label">Input</div>
            <div class="tool-content">${_escHtml(tool.input)}</div>
          </div>
          <div class="tool-section">
            <div class="tool-label">Output</div>
            <div class="tool-content ${tool.success ? 'success' : 'error'}">${_escHtml(tool.output)}</div>
          </div>
        </div>
      </div>`;
    container.appendChild(card);
    container.scrollTop = container.scrollHeight;
  }

  function toggleToolCard(id) {
    const body = document.getElementById(id + '-body');
    const chevron = document.getElementById(id + '-chevron');
    if (body && chevron) {
      const isOpen = body.classList.toggle('open');
      chevron.classList.toggle('open', isOpen);
    }
  }

  // ── Terminal ──
  function selectTerminalAgent(agentId) {
    state.selectedTerminalAgent = agentId;
    _addTerminalLine('info', 'System', `Filter: ${agentId ? state.agents.find(a => a.id === agentId)?.name || agentId : 'All Agents'}`);
  }

  function _addTerminalLine(type, source, text) {
    const line = {
      type,
      source,
      text,
      timestamp: new Date().toISOString(),
      agentId: state.selectedTerminalAgent,
    };
    state.terminalLines.push(line);
    if (state.terminalLines.length > 500) state.terminalLines.shift();
    _renderTerminalLine(line);
  }

  function _renderTerminalLine(line) {
    const container = $('terminal-body');
    if (!container) return;

    // Filter by selected agent
    if (state.selectedTerminalAgent && line.agentId && line.agentId !== state.selectedTerminalAgent) {
      return;
    }

    const time = _formatTime(line.timestamp);
    const promptClass = {
      'cmd': 'term-cmd',
      'output': 'term-output',
      'success': 'term-success',
      'error': 'term-error',
      'info': 'term-info',
      'warn': 'term-warn',
      'tool': 'term-tool',
      'file': 'term-file',
      'agent': 'term-prompt',
    }[line.type] || 'term-output';

    const div = document.createElement('div');
    div.className = 'term-line';
    div.innerHTML = `
      <span class="term-time">[${time}]</span>
      <span class="${promptClass}">${_escHtml(source)}: ${_escHtml(line.text)}</span>`;
    container.appendChild(div);
    _scrollTerminal();
  }

  function _scrollTerminal() {
    const container = $('terminal-body');
    if (container) container.scrollTop = container.scrollHeight;
  }

  function clearTerminal() {
    state.terminalLines = [];
    const container = $('terminal-body');
    if (container) {
      container.innerHTML = '<div class="term-line"><span class="term-time">[--:--:--]</span><span class="term-info">Terminal cleared.</span></div>';
    }
  }

  function exportTerminal() {
    const text = state.terminalLines.map(l => {
      const t = _formatTime(l.timestamp);
      return `[${t}] ${l.source}: ${l.text}`;
    }).join('\n');

    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `terminal-${new Date().toISOString().slice(0, 10)}.log`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ── Rooms ──
  function selectRoom(roomId) {
    state.selectedRoom = roomId;
    const room = state.rooms.find(r => r.id === roomId);
    if (!room) return;

    const icons = { 'lab': '🔬', 'chat': '💬', 'quant': '📈', 'meditation': '🧘', 'default': '🏠' };
    const icon = icons[room.type] || icons['default'];

    const title = $('room-title');
    if (title) title.textContent = `${icon} ${room.name}`;

    const subtitle = $('room-subtitle');
    if (subtitle) subtitle.textContent = room.description || `${room.agentIds ? room.agentIds.length : 0} agents`;

    // Join room via WS
    if (window.envClient && window.envClient.ws && window.envClient.ws.readyState === 1) {
      window.envClient.ws.send(JSON.stringify({ type: 'join-room', roomId }));
    }

    _renderRoomList();
    _renderRoomMessages(roomId);
    _renderRoomAgents(room);
  }

  function _renderRoomMessages(roomId) {
    const container = $('room-messages');
    if (!container) return;

    const msgs = state.messages.room[roomId] || [];

    if (msgs.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="icon">💬</div>
          <div class="title">No messages yet</div>
          <div class="desc">Be the first to send a message in this room.</div>
        </div>`;
      return;
    }

    container.innerHTML = msgs.map(msg => {
      const color = _agentColor(msg.from);
      const initial = (msg.from || '?')[0].toUpperCase();
      const time = msg.timestamp ? _formatTime(msg.timestamp) : '';

      return `
        <div class="msg-row agent">
          <div class="msg-avatar" style="background:${color}20;color:${color};">${initial}</div>
          <div>
            <div class="msg-sender">${_escHtml(msg.from)}</div>
            <div class="msg-bubble">${_escHtml(msg.content)}</div>
            ${time ? `<div class="msg-time">${time}</div>` : ''}
          </div>
        </div>`;
    }).join('');

    container.scrollTop = container.scrollHeight;
  }

  function _renderRoomAgents(room) {
    const container = $('room-agent-list');
    if (!container || !room) return;

    const agentIds = room.agentIds || [];
    if (agentIds.length === 0) {
      container.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:10px;">No agents in room</div>';
      return;
    }

    container.innerHTML = agentIds.map(id => {
      const agent = state.agents.find(a => a.id === id);
      if (!agent) return '';
      const color = _agentColor(agent.name);
      return `
        <div class="agent-item">
          <div class="agent-avatar" style="background:${color}20;color:${color};width:26px;height:26px;font-size:12px;">${agent.name[0].toUpperCase()}</div>
          <div class="agent-info">
            <div class="agent-name" style="font-size:12px;">${_escHtml(agent.name)}</div>
            <div class="agent-meta">${agent.status || 'idle'}</div>
          </div>
        </div>`;
    }).join('');
  }

  function sendRoomMessage() {
    const agentSel = $('room-msg-agent');
    const input = $('room-msg-input');
    const agentId = agentSel ? agentSel.value : '';
    const text = input ? input.value.trim() : '';

    if (!text || !state.selectedRoom) return;

    const roomId = state.selectedRoom;

    // Store message locally
    if (!state.messages.room[roomId]) state.messages.room[roomId] = [];
    state.messages.room[roomId].push({
      from: agentId || 'Anonymous',
      content: text,
      timestamp: new Date().toISOString(),
    });

    // Send via WS
    if (window.envClient && window.envClient.ws && window.envClient.ws.readyState === 1) {
      window.envClient.ws.send(JSON.stringify({
        type: 'room-message',
        content: text,
        messageType: 'chat',
      }));
    } else {
      fetch(`/api/rooms/${roomId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agentId: agentId || 'anonymous', text, type: 'chat' }),
      }).catch(() => {});
    }

    if (input) input.value = '';
    _renderRoomMessages(roomId);
    _addTerminalLine('agent', 'Room', `[${roomId}] ${agentId || 'Anonymous'}: ${text.substring(0, 60)}`);
  }

  function showCreateRoom() {
    const name = prompt('Room name:');
    if (!name) return;
    fetch('/api/rooms', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description: '', type: 'chat' }),
    })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          showToast('Room created: ' + name, 'success');
          _fetchRooms();
        } else {
          showToast('Error: ' + (data.error || 'Failed'), 'error');
        }
      })
      .catch(() => showToast('Failed to create room', 'error'));
  }

  function _fetchRooms() {
    fetch('/api/rooms')
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          state.rooms = data.rooms;
          _renderRoomList();
        }
      })
      .catch(() => {});
  }

  // ── Dashboard ──
  function _updateStats() {
    const el = (id, val) => { const e = $(id); if (e) e.textContent = val; };
    el('stat-rooms', state.rooms.length);
    el('stat-agents', state.agents.length);

    const online = state.agents.filter(a => a.status !== 'offline').length;
    el('stat-online', online);

    // WS indicator
    const ws = $('ws-indicator');
    if (ws) {
      ws.classList.toggle('connected', state.connected);
      ws.title = state.connected ? 'Connected' : 'Disconnected';
    }
  }

  function _renderDashboard() {
    _updateStats();
    const el = (id, val) => { const e = $(id); if (e) e.textContent = val; };

    el('dash-rooms', state.rooms.length);
    el('dash-agents', state.agents.length);
    el('dash-online', state.agents.filter(a => a.status !== 'offline').length);
    el('dash-messages', state.stats.totalMessages);
    el('dash-fam-messages', state.stats.famMessages);

    // Uptime
    if (window.envClient && window.envClient._startTime) {
      const uptime = Math.floor((Date.now() - window.envClient._startTime) / 1000);
      el('dash-uptime', _formatDuration(uptime));
    }

    el('dash-ws-status', state.connected ? '🟢 Connected' : '🔴 Disconnected');

    // Activity feed
    _renderActivityFeed();
  }

  function _renderActivityFeed() {
    const container = $('dash-activity-feed');
    if (!container) return;

    // Build activity from recent messages
    const activities = [];

    state.messages.chat.slice(-20).reverse().forEach(msg => {
      activities.push({
        icon: msg.type === 'user' ? '👤' : '🤖',
        text: `${msg.from}: ${msg.content.substring(0, 80)}${msg.content.length > 80 ? '...' : ''}`,
        time: msg.timestamp,
      });
    });

    if (activities.length === 0) {
      container.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:10px;">No activity yet</div>';
      return;
    }

    container.innerHTML = activities.map(a => `
      <div class="activity-item">
        <span class="activity-icon">${a.icon}</span>
        <div class="activity-content">
          <div class="activity-text">${_escHtml(a.text)}</div>
          <div class="activity-time">${a.time ? _formatTime(a.time) : ''}</div>
        </div>
      </div>`).join('');
  }

  // ── Quick Agent Registration ──
  function registerQuickAgent() {
    const input = $('quick-agent-name');
    if (!input) return;
    const name = input.value.trim();
    if (!name) return;

    const id = 'agent-' + Date.now().toString(36);
    const roles = ['worker', 'researcher', 'analyst', 'builder', 'coordinator'];
    const role = roles[Math.floor(Math.random() * roles.length)];

    fetch('/api/agents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id,
        name,
        role,
        capabilities: ['communicate', 'read_files'],
        metadata: { registeredBy: 'dashboard' },
      }),
    })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          showToast(`Agent "${name}" registered!`, 'success');
          input.value = '';
          _addTerminalLine('success', 'System', `Agent registered: ${name} (${role})`);
          _fetchAgents();
        } else {
          showToast('Error: ' + (data.error || 'Failed'), 'error');
        }
      })
      .catch(() => showToast('Failed to register agent', 'error'));
  }

  function _fetchAgents() {
    fetch('/api/agents')
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          state.agents = data.agents;
          _renderAgentList();
          _updateAgentSelectors();
        }
      })
      .catch(() => {});
  }

  // ── Demo Mode ──
  function runDemo() {
    showToast('Demo mode activated!', 'info');
    _addTerminalLine('info', 'System', 'Demo mode started');

    // Register demo agents
    const demoAgents = [
      { name: 'Manager', role: 'coordinator' },
      { name: 'Optimizer', role: 'optimizer' },
      { name: 'Researcher', role: 'researcher' },
    ];

    demoAgents.forEach((a, i) => {
      setTimeout(() => {
        const id = 'demo-' + Date.now().toString(36) + i;
        fetch('/api/agents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id, name: a.name, role: a.role, capabilities: ['communicate'] }),
        })
          .then(r => r.json())
          .then(data => {
            if (data.success) {
              _addTerminalLine('success', 'Demo', `Registered: ${a.name}`);
              _fetchAgents();
            }
          })
          .catch(() => {});
      }, i * 500);
    });

    // Create demo room
    setTimeout(() => {
      fetch('/api/rooms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Demo Lab', description: 'Demo room', type: 'lab' }),
      })
        .then(r => r.json())
        .then(data => {
          if (data.success) {
            _addTerminalLine('success', 'Demo', 'Created room: Demo Lab');
            _fetchRooms();
          }
        })
        .catch(() => {});
    }, 2000);

    // Add demo messages
    setTimeout(() => {
      _addChatMessage({ from: 'System', content: '🎬 Demo mode! Agents are now active.', type: 'system', timestamp: new Date().toISOString() });
      _addChatMessage({ from: 'Manager', content: 'Hello team! I\'ve initialized the demo environment. Let\'s get to work.', type: 'agent', agentId: 'demo', timestamp: new Date().toISOString() });
      _addToolUseCard('Manager', { name: 'initialize_workspace', input: '{"mode": "demo", "agents": 3}', output: 'Workspace initialized successfully. 3 agents registered.', success: true });
    }, 3000);
  }

  // ── Toast Notifications ──
  function showToast(message, type = 'info') {
    const container = $('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${_escHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 3000);
  }

  // ── WebSocket Event Hooks ──
  function handleWSMessage(msg) {
    switch (msg.event) {
      case 'world.state':
        if (msg.agents) {
          state.agents = msg.agents;
          _renderAgentList();
          _updateAgentSelectors();
        }
        if (msg.rooms) {
          state.rooms = msg.rooms;
          _renderRoomList();
        }
        state.connected = true;
        _updateStats();
        break;

      case 'agent.moved':
        _addTerminalLine('info', 'Move', `Agent ${msg.agentId} → ${msg.roomId}`);
        _fetchAgents();
        _fetchRooms();
        break;

      case 'room.history':
        if (msg.messages && msg.roomId) {
          state.messages.room[msg.roomId] = msg.messages;
          if (state.selectedRoom === msg.roomId) {
            _renderRoomMessages(msg.roomId);
          }
        }
        break;

      case 'fam-message':
        state.stats.famMessages++;
        _addTerminalLine('agent', 'FAM', `${msg.data?.from || '?'}: ${(msg.data?.content || '').substring(0, 60)}`);
        break;

      case 'code-result':
        _addTerminalLine(
          msg.success ? 'success' : 'error',
          'Code',
          `[${msg.language}] ${msg.success ? 'OK' : msg.error || 'Failed'}`
        );
        break;

      case 'server.shutdown':
        showToast('Server is shutting down...', 'warn');
        state.connected = false;
        _updateStats();
        break;
    }
  }

  // ── Helpers ──
  function _agentColor(name) {
    const colors = ['#7c6ff7', '#00d4c8', '#f06292', '#42a5f5', '#ff8a65', '#ffd54f', '#00c896', '#a29bfe'];
    let hash = 0;
    for (let i = 0; i < (name || '').length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
    return colors[Math.abs(hash) % colors.length];
  }

  function _escHtml(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
  }

  function _formatTime(iso) {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch { return ''; }
  }

  function _formatDuration(seconds) {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  }

  function _renderMarkdown(text) {
    if (!text) return '';
    // Basic markdown: bold, italic, code, links
    let html = _escHtml(text);
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/`(.+?)`/g, '<code style="background:var(--bg);padding:1px 4px;border-radius:3px;font-size:12px;font-family:var(--mono);">$1</code>');
    html = html.replace(/\n/g, '<br>');
    return html;
  }

  // ── Public API ──
  return {
    init,
    switchView,
    selectChatAgent,
    selectAgent,
    sendChatMessage,
    selectTerminalAgent,
    clearTerminal,
    exportTerminal,
    selectRoom,
    sendRoomMessage,
    showCreateRoom,
    registerQuickAgent,
    runDemo,
    showToast,
    toggleToolCard,
    handleWSMessage,
  };
})();

// ── Auto-init ──
document.addEventListener('DOMContentLoaded', () => {
  App.init();

  // Hook into env-client's WS message handler
  const origOnLoad = window.onload;
  window.onload = () => {
    if (origOnLoad) origOnLoad();
    // Patch envClient's WS handler to also feed our app
    if (window.envClient) {
      const origHandler = window.envClient._handleWSMessage;
      window.envClient._handleWSMessage = (msg) => {
        if (origHandler) origHandler(msg);
        App.handleWSMessage(msg);
      };
    }
  };
});
