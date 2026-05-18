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
      // Ensure canvas is sized correctly after connection
      this.renderer.resize();
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
    // Ensure canvas has valid dimensions after world state arrives
    // This fixes the issue where rooms/agents aren't visible on initial load
    // because the canvas was 0x0 when the renderer was constructed
    const container = this.renderer.canvas.parentElement;
    if (container) {
      const cw = container.clientWidth;
      const ch = container.clientHeight;
      if ((cw > 0 && ch > 0) && (this.renderer.canvas.width !== cw || this.renderer.canvas.height !== ch)) {
        this.renderer.resize();
      }
    }
    this._updateSidebar();
    this._updateStatusBar();
    this._updateActivityLog();
    if (this.state.selectedAgent) {
      this._updateAgentDetail(this.state.selectedAgent.id);
    }
    // Refresh agents tab if it's the active tab
    const agentsTab = document.getElementById('tab-agents');
    if (agentsTab && agentsTab.classList.contains('active')) {
      this._renderAgentsTab();
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
      // Also update online status based on status
      if (msg.status === 'offline') {
        agent.online = false;
      } else if (msg.status === 'active' || msg.status === 'working') {
        agent.online = true;
      }
      this._updateAgentDetail(msg.agentId);
      this._updateSidebar();
      this._updateStatusBar();
      // Refresh agents tab if active
      const agentsTab = document.getElementById('tab-agents');
      if (agentsTab && agentsTab.classList.contains('active')) {
        this._renderAgentsTab();
      }
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
    // If the message is for the currently selected room, append it to the chat view
    if (msg.roomId && this.state.selectedRoom && msg.roomId === this.state.selectedRoom.id) {
      this._appendMessage({
        from: msg.from,
        type: msg.type || 'chat',
        content: msg.content || '',
        timestamp: msg.timestamp || new Date().toISOString(),
      });
    }
  }

  _handleConnectionActive(msg) {
    // Connection visualization is handled by world state updates
  }

  _handleConnectionIdle(msg) {
    // Connection visualization is handled by world state updates
  }

  _handleRoomMessage(msg) {
    // Handle both { data: {...} } and direct message formats
    const messageData = msg.data || msg;
    if (messageData && msg.roomId === this.state.selectedRoom?.id) {
      this._appendMessage(messageData);
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
      container.innerHTML = '<div class="activity-empty-msg" style="color:var(--text-dim);font-size:11px;">No recent activity</div>';
      return;
    }
    // Show ALL agents' activity, not just the selected one
    container.innerHTML = entries.slice(-12).reverse().map(e => {
      const agent = this.state.agents.find(a => a.id === e.agentId);
      const color = agent?.color || '#888';
      const name = agent?.name || e.agentId;
      const time = e.timestamp ? new Date(e.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';
      return `
        <div class="activity-entry">
          <span class="time">${time}</span>
          <span class="agent-name" style="color:${color}">${this._escapeHtml(name)}</span>
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
    // Remove the "No recent activity" empty message if present
    const empty = container.querySelector('.activity-empty-msg') || container.querySelector('[style*="No recent"]') || container.querySelector('.empty-state');
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
        .then(r => {
          if (!r.ok) throw new Error(`Failed to load messages (${r.status})`);
          return r.json();
        })
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
        })
        .catch(err => {
          this._showToast(`Failed to load messages: ${err.message}`, 'error');
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
    if (!agentId || !text || !this.state.selectedRoom) {
      if (!agentId) this._showToast('Please select an agent', 'error');
      else if (!text) this._showToast('Please type a message', 'error');
      return;
    }

    fetch(`/api/rooms/${this.state.selectedRoom.id}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agentId, text, type }),
    })
      .then(r => {
        if (!r.ok) throw new Error(`Failed to send (${r.status})`);
        document.getElementById('msg-input').value = '';
      })
      .catch(err => {
        this._showToast(`Failed to send message: ${err.message}`, 'error');
      });
  }

  registerAgent() {
    const name = document.getElementById('new-agent-name').value.trim();
    const role = document.getElementById('new-agent-role').value.trim() || 'general';
    if (!name) {
      this._showToast('Please enter an agent name', 'error');
      return;
    }

    fetch('/api/agents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, role, capabilities: ['communicate'] }),
    })
      .then(r => {
        if (!r.ok) throw new Error(`Failed to register (${r.status})`);
        return r.json();
      })
      .then(() => {
        document.getElementById('new-agent-name').value = '';
        document.getElementById('new-agent-role').value = '';
        this._showToast(`Agent "${name}" registered!`, 'success');
        // Refresh agents tab
        setTimeout(() => this._renderAgentsTab(), 500);
      })
      .catch(err => {
        this._showToast(`Failed to register agent: ${err.message}`, 'error');
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

  // ── Toast Notifications ──
  _showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.classList.add('toast-out');
      setTimeout(() => toast.remove(), 300);
    }, duration);
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
          // Use double-rAF to ensure layout is complete after tab display change
          requestAnimationFrame(() => {
            requestAnimationFrame(() => {
              this.renderer.resize();
              // Force a re-render with current state
              if (this.renderer.worldState) {
                this.renderer.updateWorldState(this.renderer.worldState);
              }
            });
          });
        }
        if (tab.dataset.tab === 'agents') {
          this._renderAgentsTab();
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

    // Canvas interaction — click, drag, and click-to-move
    this.canvas = document.getElementById('world-canvas');
    this._setupCanvasInteraction();

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

  // ── Canvas Interaction (Click + Drag + Click-to-Move) ──
  _setupCanvasInteraction() {
    const canvas = this.canvas;
    let isDragging = false;
    let dragStarted = false;
    let mouseDownAgent = null;
    let mouseDownPos = null;

    const getCanvasPos = (e) => {
      const rect = canvas.getBoundingClientRect();
      return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    };

    canvas.addEventListener('mousedown', (e) => {
      const pos = getCanvasPos(e);
      const agent = this.renderer.getAgentAt(pos.x, pos.y);

      if (agent) {
        // Start potential drag or select
        mouseDownAgent = agent;
        mouseDownPos = pos;
        isDragging = true;
        dragStarted = false;
        this.selectAgent(agent.id);
      } else {
        const room = this.renderer.getRoomAt(pos.x, pos.y);
        if (room) {
          // Click-to-move: if an agent is selected and we click a different room, move it
          if (this.state.selectedAgent && this.state.selectedAgent.currentRoom !== room.id) {
            this.moveAgentToRoom(this.state.selectedAgent.id, room.id);
          }
          this.selectRoom(room.id);
        }
      }
    });

    canvas.addEventListener('mousemove', (e) => {
      if (!isDragging || !mouseDownAgent) return;
      const pos = getCanvasPos(e);

      // Check if mouse has moved enough to start drag (5px threshold)
      if (!dragStarted && mouseDownPos) {
        const dx = pos.x - mouseDownPos.x;
        const dy = pos.y - mouseDownPos.y;
        if (dx * dx + dy * dy > 25) {
          dragStarted = true;
          this.renderer.startDrag(mouseDownAgent.id, mouseDownPos.x, mouseDownPos.y);
        }
      }

      if (dragStarted) {
        this.renderer.updateDrag(pos.x, pos.y);
        canvas.style.cursor = 'grabbing';
      }
    });

    const endDrag = (e) => {
      if (isDragging) {
        if (dragStarted && mouseDownAgent) {
          // Find which room the agent was dropped in
          const pos = getCanvasPos(e);
          const targetRoom = this.renderer.getRoomAt(pos.x, pos.y);
          if (targetRoom && targetRoom.id !== mouseDownAgent.currentRoom) {
            this.moveAgentToRoom(mouseDownAgent.id, targetRoom.id);
          }
          this.renderer.endDrag();
          canvas.style.cursor = 'default';
        }
        // If drag never started, it was just a click (already handled in mousedown)
      }
      isDragging = false;
      dragStarted = false;
      mouseDownAgent = null;
      mouseDownPos = null;
    };

    canvas.addEventListener('mouseup', endDrag);
    canvas.addEventListener('mouseleave', endDrag);

    // Window resize — keep canvas sized correctly
    window.addEventListener('resize', () => {
      this.renderer.resize();
    });

    // Hover cursor feedback
    canvas.addEventListener('mousemove', (e) => {
      if (isDragging) return;
      const pos = getCanvasPos(e);
      const agent = this.renderer.getAgentAt(pos.x, pos.y);
      canvas.style.cursor = agent ? 'pointer' : 'default';
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

  _renderAgentsTab() {
    const container = document.getElementById('agents-container');
    if (!container) return;
    const agents = this.state.agents || [];
    if (agents.length === 0) {
      container.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><div class="icon">🤖</div><div>No agents registered yet</div><div style="font-size:11px;margin-top:8px;color:var(--text-dim);">Register agents below or click ▶ Demo</div></div>';
      return;
    }
    container.innerHTML = agents.map(a => {
      const room = this.state.rooms.find(r => r.id === a.currentRoom);
      const statusColor = a.online ? '#00b894' : '#636e72';
      const statusLabel = a.online ? 'Online' : 'Offline';
      return `
        <div class="agent-card" onclick="envClient.selectAgent('${a.id}');" style="background:rgba(30,30,40,0.8);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px;cursor:pointer;transition:border-color 0.2s;" onmouseover="this.style.borderColor='${a.color || '#888'}'" onmouseout="this.style.borderColor='rgba(255,255,255,0.08)'">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <div style="width:36px;height:36px;border-radius:50%;background:${a.color || '#888'};display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;">${a.avatar?.emoji || '🤖'}</div>
            <div style="min-width:0;flex:1;">
              <div style="font-weight:600;font-size:13px;color:#e0e0f0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${this._escapeHtml(a.name)}</div>
              <div style="font-size:11px;color:var(--text-dim);">${this._escapeHtml(a.role || '—')}</div>
            </div>
            <div style="width:8px;height:8px;border-radius:50%;background:${statusColor};flex-shrink:0;" title="${statusLabel}"></div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:11px;">
            <div style="color:var(--text-dim);">Room:</div><div style="color:#ccc;">${this._escapeHtml(room ? room.name : (a.currentRoom || '—'))}</div>
            <div style="color:var(--text-dim);">Status:</div><div style="color:${statusColor};">${this._escapeHtml(a.status || '—')}</div>
          </div>
          ${(a.capabilities && a.capabilities.length > 0) ? `<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:4px;">${a.capabilities.slice(0, 4).map(c => `<span style="background:rgba(255,255,255,0.06);border-radius:4px;padding:2px 6px;font-size:10px;color:var(--text-dim);">${this._escapeHtml(c)}</span>`).join('')}</div>` : ''}
        </div>
      `;
    }).join('');
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
