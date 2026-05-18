/**
 * Env Client — WebSocket client and UI controller for the Virtual Agent Environment v2.
 * Handles real-time updates, user interactions, and coordinates the renderer.
 */

class EnvClient {
  constructor() {
    this.ws = null;
    this.renderer = null;
    this.state = {
      rooms: [],
      agents: [],
      connections: [],
      recentActivity: [],
      selectedRoom: null,
      selectedAgent: null,
    };
    this.lastFrameTime = performance.now();
    this.connected = false;
    this.reconnectAttempts = 0;

    this._initRenderer();
    this._connect();
    this._startRenderLoop();
    this._bindUI();
  }

  _initRenderer() {
    this.renderer = new EnvRenderer('world-canvas');
  }

  _connect() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${proto}//${location.host}/ws`);
    this.ws = ws;

    ws.onopen = () => {
      this.connected = true;
      this.reconnectAttempts = 0;
      document.getElementById('ws-dot').classList.add('connected');
      document.getElementById('ws-status').textContent = 'Connected';
      ws.send(JSON.stringify({ type: 'auth', agentId: 'dashboard' }));
      ws.send(JSON.stringify({ type: 'request-world' }));
    };

    ws.onclose = () => {
      this.connected = false;
      document.getElementById('ws-dot').classList.remove('connected');
      document.getElementById('ws-status').textContent = 'Disconnected';
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
      this.reconnectAttempts++;
      setTimeout(() => this._connect(), delay);
    };

    ws.onerror = () => {};

    ws.onmessage = (e) => {
      let msg;
      try { msg = JSON.parse(e.data); } catch { return; }
      this._handleWSMessage(msg);
    };
  }

  _handleWSMessage(msg) {
    switch (msg.event) {
      case 'world.state':
        this._updateWorldState(msg);
        break;
      case 'agent.moved':
        this._handleAgentMoved(msg);
        break;
      case 'agent.status':
        this._handleAgentStatus(msg);
        break;
      case 'agent.activity':
        this._handleAgentActivity(msg);
        break;
      case 'agent.joined':
        this._handleAgentJoined(msg);
        break;
      case 'agent.left':
        this._handleAgentLeft(msg);
        break;
      case 'message.sent':
        this._handleMessageSent(msg);
        break;
      case 'connection.active':
        this._handleConnectionActive(msg);
        break;
      case 'connection.idle':
        this._handleConnectionIdle(msg);
        break;
      case 'room-message':
        this._handleRoomMessage(msg);
        break;
    }
  }

  _updateWorldState(state) {
    this.state.rooms = state.rooms || [];
    this.state.agents = state.agents || [];
    this.state.connections = state.connections || [];
    this.state.recentActivity = state.recentActivity || [];
    this.renderer.updateWorldState(state);
    this._updateSidebar();
    this._updateStatusBar();
    this._updateActivityLog();
    if (this.state.selectedAgent) {
      this._updateAgentDetail(this.state.selectedAgent.id);
    }
  }

  _handleAgentMoved(msg) {
    const agent = this.state.agents.find(a => a.id === msg.agentId);
    if (agent) {
      agent.currentRoom = msg.toRoom;
      this._addActivityEntry({
        agentId: msg.agentId,
        agentName: agent.name,
        action: `Moved to ${msg.toRoom}`,
        color: agent.color,
      });
    }
    this._updateSidebar();
  }

  _handleAgentStatus(msg) {
    const agent = this.state.agents.find(a => a.id === msg.agentId);
    if (agent) {
      agent.status = msg.status;
      this._updateAgentDetail(msg.agentId);
    }
  }

  _handleAgentActivity(msg) {
    const agent = this.state.agents.find(a => a.id === msg.agentId);
    if (agent) {
      agent.activity = agent.activity || {};
      agent.activity.level = msg.level;
      agent.activity.lastAction = msg.lastAction;
      this._addActivityEntry({
        agentId: msg.agentId,
        agentName: agent?.name || msg.agentId,
        action: msg.lastAction,
        color: agent?.color || '#888',
      });
      if (this.state.selectedAgent?.id === msg.agentId) {
        this._updateAgentDetail(msg.agentId);
      }
    }
  }

  _handleAgentJoined(msg) {
    if (msg.agent) {
      const exists = this.state.agents.find(a => a.id === msg.agent.id);
      if (!exists) {
        this.state.agents.push(msg.agent);
      }
      this._addActivityEntry({
        agentId: msg.agent.id,
        agentName: msg.agent.name,
        action: 'Joined the world',
        color: msg.agent.color,
      });
    }
    this._updateSidebar();
  }

  _handleAgentLeft(msg) {
    this.state.agents = this.state.agents.filter(a => a.id !== msg.agentId);
    if (this.state.selectedAgent?.id === msg.agentId) {
      this.state.selectedAgent = null;
      this._clearAgentDetail();
    }
    this._updateSidebar();
  }

  _handleMessageSent(msg) {
    const fromAgent = this.state.agents.find(a => a.id === msg.from);
    this._addActivityEntry({
      agentId: msg.from,
      agentName: fromAgent?.name || msg.from,
      action: `Sent ${msg.type} message${msg.roomId ? ' in ' + msg.roomId : ''}`,
      color: fromAgent?.color || '#888',
    });
  }

  _handleConnectionActive(msg) {
    // Connection visualization is handled by world state updates
  }

  _handleConnectionIdle(msg) {
    // Connection visualization is handled by world state updates
  }

  _handleRoomMessage(msg) {
    if (msg.data && msg.roomId === this.state.selectedRoom?.id) {
      this._appendMessage(msg.data);
    }
  }

  // ── UI Updates ──
  _updateSidebar() {
    // Rooms
    const roomList = document.getElementById('room-list');
    roomList.innerHTML = this.state.rooms.map(r => `
      <div class="sidebar-item ${r.id === this.state.selectedRoom?.id ? 'active' : ''}" 
           onclick="envClient.selectRoom('${r.id}')">
        <span>${r.icon || '🏠'} ${r.name}</span>
        <span class="badge">${r.agentCount || 0}</span>
      </div>
    `).join('');

    // Agents
    const agentList = document.getElementById('agent-list');
    agentList.innerHTML = this.state.agents.map(a => `
      <div class="sidebar-item ${a.id === this.state.selectedAgent?.id ? 'active' : ''}" 
           onclick="envClient.selectAgent('${a.id}')">
        <span><span class="agent-dot ${a.online ? 'online' : ''}"></span>${a.name}</span>
      </div>
    `).join('');

    // Agent select dropdown
    const sel = document.getElementById('msg-agent-select');
    if (sel) {
      sel.innerHTML = '<option value="">— Select Agent —</option>' +
        this.state.agents.map(a => `<option value="${a.id}">${a.name}</option>`).join('');
    }
  }

  _updateStatusBar() {
    document.getElementById('room-count').textContent = this.state.rooms.length;
    document.getElementById('agent-count').textContent = this.state.agents.length;
    const online = this.state.agents.filter(a => a.online).length;
    document.getElementById('online-count').textContent = online;
  }

  _updateActivityLog() {
    const container = document.getElementById('activity-log');
    if (!container) return;
    const entries = this.state.recentActivity || [];
    if (entries.length === 0) {
      container.innerHTML = '<div style="color:var(--text-dim);font-size:11px;">No recent activity</div>';
      return;
    }
    container.innerHTML = entries.slice(-8).reverse().map(e => {
      const agent = this.state.agents.find(a => a.id === e.agentId);
      const color = agent?.color || '#888';
      const time = e.timestamp ? new Date(e.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';
      return `
        <div class="activity-entry">
          <span class="time">${time}</span>
          <span class="agent-name" style="color:${color}">${agent?.name || e.agentId}</span>
          <span class="action">${this._escapeHtml(e.action)}</span>
        </div>
      `;
    }).join('');
  }

  _addActivityEntry({ agentId, agentName, action, color }) {
    const container = document.getElementById('activity-log');
    if (!container) return;
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const entry = document.createElement('div');
    entry.className = 'activity-entry';
    entry.innerHTML = `
      <span class="time">${time}</span>
      <span class="agent-name" style="color:${color || '#888'}">${this._escapeHtml(agentName)}</span>
      <span class="action">${this._escapeHtml(action)}</span>
    `;
    const empty = container.querySelector('.empty-state, [style*="No recent"]');
    if (empty) empty.remove();
    container.insertBefore(entry, container.firstChild);
    // Keep only last 20 entries
    while (container.children.length > 20) {
      container.removeChild(container.lastChild);
    }
  }

  _updateAgentDetail(agentId) {
    const agent = this.state.agents.find(a => a.id === agentId);
    if (!agent) return;
    this.state.selectedAgent = agent;

    document.getElementById('sel-agent-name').textContent = agent.name;
    document.getElementById('sel-agent-role').textContent = agent.role || '—';
    document.getElementById('sel-agent-room').textContent = agent.currentRoom || '—';
    document.getElementById('sel-agent-status').textContent = agent.status || '—';
    document.getElementById('sel-agent-online').textContent = agent.online ? '🟢 Online' : '⚫ Offline';

    const capsEl = document.getElementById('sel-agent-caps');
    if (capsEl) {
      capsEl.innerHTML = (agent.capabilities || []).map(c => `<span class="capability-tag">${c}</span>`).join('') || '—';
    }

    // Activity
    const activity = agent.activity || { level: 0, lastAction: '' };
    const activityFill = document.getElementById('sel-agent-activity-fill');
    if (activityFill) {
      activityFill.style.width = `${(activity.level || 0) * 100}%`;
      activityFill.style.background = agent.color || '#6c5ce7';
    }
    const activityText = document.getElementById('sel-agent-activity-text');
    if (activityText) {
      activityText.textContent = activity.lastAction || 'Idle';
    }

    // Avatar
    const avatarEl = document.getElementById('sel-agent-avatar');
    if (avatarEl) {
      avatarEl.style.background = agent.color || '#6c5ce7';
      avatarEl.textContent = agent.avatar?.emoji || '🤖';
    }

    this._updateSidebar();
  }

  _clearAgentDetail() {
    document.getElementById('sel-agent-name').textContent = '—';
    document.getElementById('sel-agent-role').textContent = '—';
    document.getElementById('sel-agent-room').textContent = '—';
    document.getElementById('sel-agent-status').textContent = '—';
    document.getElementById('sel-agent-online').textContent = '—';
  }

  _appendMessage(msg) {
    const container = document.getElementById('messages-container');
    if (!container) return;
    const empty = container.querySelector('.empty-state');
    if (empty) empty.remove();

    const div = document.createElement('div');
    div.className = `message ${msg.type || 'chat'}`;
    const time = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
    div.innerHTML = `
      <div class="meta">
        <span class="from">${this._escapeHtml(msg.from)}</span>
        <span class="type">${msg.type}</span>
        <span>${time}</span>
      </div>
      <div class="content">${this._escapeHtml(msg.content)}</div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  // ── User Actions ──
  selectRoom(roomId) {
    this.state.selectedRoom = this.state.rooms.find(r => r.id === roomId) || null;
    this.renderer.selectedRoomId = roomId;
    this._updateSidebar();

    if (this.state.selectedRoom) {
      document.getElementById('sel-room-name').textContent = this.state.selectedRoom.name;
      document.getElementById('sel-room-agents').textContent = this.state.selectedRoom.agentCount || 0;
      document.getElementById('sel-room-desc').textContent = this.state.selectedRoom.description || '—';

      // Load messages
      fetch(`/api/rooms/${roomId}/messages?limit=50`)
        .then(r => r.json())
        .then(data => {
          const container = document.getElementById('messages-container');
          const msgs = data.messages || [];
          if (msgs.length === 0) {
            container.innerHTML = '<div class="empty-state"><div class="icon">💬</div><div>No messages yet in this room</div></div>';
          } else {
            container.innerHTML = msgs.map(m => `
              <div class="message ${m.type || 'chat'}">
                <div class="meta">
                  <span class="from">${this._escapeHtml(m.from)}</span>
                  <span class="type">${m.type}</span>
                  <span>${m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</span>
                </div>
                <div class="content">${this._escapeHtml(m.content)}</div>
              </div>
            `).join('');
            container.scrollTop = container.scrollHeight;
          }
        });

      // Join room via WS
      if (this.ws && this.ws.readyState === 1) {
        this.ws.send(JSON.stringify({ type: 'join-room', roomId }));
      }
    }
  }

  selectAgent(agentId) {
    this.renderer.selectedAgentId = agentId;
    this._updateAgentDetail(agentId);
  }

  sendMessage() {
    const agentId = document.getElementById('msg-agent-select').value;
    const type = document.getElementById('msg-type-select').value;
    const text = document.getElementById('msg-input').value.trim();
    if (!agentId || !text || !this.state.selectedRoom) return;

    fetch(`/api/rooms/${this.state.selectedRoom.id}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agentId, text, type }),
    }).then(() => {
      document.getElementById('msg-input').value = '';
    });
  }

  registerAgent() {
    const name = document.getElementById('new-agent-name').value.trim();
    const role = document.getElementById('new-agent-role').value.trim() || 'general';
    if (!name) return;

    fetch('/api/agents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, role, capabilities: ['communicate'] }),
    }).then(r => r.json()).then(() => {
      document.getElementById('new-agent-name').value = '';
      document.getElementById('new-agent-role').value = '';
    });
  }

  moveAgentToRoom(agentId, roomId) {
    if (this.ws && this.ws.readyState === 1) {
      this.ws.send(JSON.stringify({ type: 'move-agent', agentId, roomId }));
    }
  }

  simulateActivity(agentId) {
    if (this.ws && this.ws.readyState === 1) {
      this.ws.send(JSON.stringify({ type: 'simulate-activity', agentId }));
    }
  }

  // ── Render Loop ──
  _startRenderLoop() {
    const loop = (now) => {
      const dt = Math.min((now - this.lastFrameTime) / 1000, 0.1); // Cap at 100ms
      this.lastFrameTime = now;
      this.renderer.render(dt);
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  // ── UI Bindings ──
  _bindUI() {
    // Tabs
    document.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
        if (tab.dataset.tab === 'world') {
          // Resize canvas when switching to world tab
          setTimeout(() => this.renderer.resize(), 50);
        }
      });
    });

    // Enter key for message input
    const msgInput = document.getElementById('msg-input');
    if (msgInput) {
      msgInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') this.sendMessage();
      });
    }

    // Canvas click handling
    this.canvas = document.getElementById('world-canvas');
    this.canvas.addEventListener('click', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const agent = this.renderer.getAgentAt(x, y);
      if (agent) {
        this.selectAgent(agent.id);
        return;
      }

      const room = this.renderer.getRoomAt(x, y);
      if (room) {
        this.selectRoom(room.id);
      }
    });

    // Map control buttons
    document.getElementById('btn-demo')?.addEventListener('click', () => {
      this._startDemo();
    });
    document.getElementById('btn-reset-view')?.addEventListener('click', () => {
      this.renderer.selectedAgentId = null;
      this.renderer.selectedRoomId = null;
      this.state.selectedAgent = null;
      this.state.selectedRoom = null;
      this._updateSidebar();
      this._clearAgentDetail();
    });
  }

  _startDemo() {
    // Create demo agents if none exist
    if (this.state.agents.length === 0) {
      const demoData = [
        { name: 'OWL', role: 'operator', emoji: '🦉', color: '#6c5ce7' },
        { name: 'CC', role: 'overseer', emoji: '🔵', color: '#e17055' },
        { name: 'AS', role: 'assistant', emoji: '🟡', color: '#00cec9' },
        { name: 'PM', role: 'debugger', emoji: '🔴', color: '#fd79a8' },
        { name: 'RL', role: 'researcher', emoji: '🟢', color: '#74b9ff' },
      ];
      for (const d of demoData) {
        fetch('/api/agents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: d.name, role: d.role, capabilities: ['communicate'] }),
        });
      }
    }

    // Enable renderer demo mode
    const demoAgents = [
      { id: 'demo-1', name: 'OWL', color: '#6c5ce7', emoji: '🦉' },
      { id: 'demo-2', name: 'CC', color: '#e17055', emoji: '🔵' },
      { id: 'demo-3', name: 'AS', color: '#00cec9', emoji: '🟡' },
      { id: 'demo-4', name: 'PM', color: '#fd79a8', emoji: '🔴' },
      { id: 'demo-5', name: 'RL', color: '#74b9ff', emoji: '🟢' },
    ];
    this.renderer.enableDemo(demoAgents);
  }

  _escapeHtml(s) {
    if (!s) return '';
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }
}

// ── Initialize ──
let envClient;
document.addEventListener('DOMContentLoaded', () => {
  envClient = new EnvClient();
});
