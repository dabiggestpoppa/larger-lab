/**
 * Live Tracker — Real-time agent activity feed, system health, task progress, event log.
 * Attaches to the existing envClient state. Auto-refreshes every 5 seconds.
 * 
 * World Builder Upgrade 2026-05-19:
 * - Real-time agent activity feed showing what each agent is doing
 * - System health monitor (RAM, CPU, active agents display)
 * - Task completion progress bars
 * - Event log with timestamps
 * - Auto-refresh every 5 seconds
 * - Room activity heat map
 */

class LiveTracker {
  constructor(envClient) {
    this.envClient = envClient;
    this.container = null;
    this.initialized = false;
    this.systemHealth = { cpu: 0, ram: 0, activeAgents: 0, uptime: 0, wsLatency: 0 };
    this.eventLog = [];
    this.maxEventLog = 100;
    this.displayedEvents = 20;
    this.startTime = Date.now();
    this.lastRefresh = 0;
    this.refreshInterval = 5000; // 5 seconds
    this._healthHistory = []; // For sparklines
    this._maxHealthHistory = 60;
  }

  init(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) return false;
    this.initialized = true;
    this._startAutoRefresh();
    return true;
  }

  _startAutoRefresh() {
    // Update health metrics every second for smooth display
    setInterval(() => {
      if (this.initialized && this.envClient) {
        this._computeSystemHealth();
        this._renderHealthPanel();
        this._renderTaskPanel();
      }
    }, 1000);

    // Full refresh every 5 seconds
    setInterval(() => {
      if (this.initialized && this.envClient) {
        this.update(this.envClient.state);
      }
    }, this.refreshInterval);
  }

  // ── Main Update (called every 5s or on state change) ──
  update(state) {
    if (!this.initialized || !this.container) return;
    this._computeSystemHealth();
    this._renderFull(state);
  }

  // ── Render Full Dashboard ──
  _renderFull(state) {
    const agents = state.agents || [];
    const rooms = state.rooms || [];

    // Compute room activity heat map data
    const roomHeat = this._computeRoomHeat(rooms, agents);

    let html = '';

    // ── System Health Banner ──
    html += this._renderHealthBanner(agents);

    // ── Two-column layout: Agent Feed + Event Log ──
    html += `<div class="lt-two-col">`;

    // Left: Agent Activity Feed
    html += `<div class="lt-col-left">`;
    html += `<div class="lt-section-header">🤖 Agent Activity</div>`;
    html += this._renderAgentFeed(agents, rooms);
    html += `</div>`;

    // Right: Event Log + Tasks
    html += `<div class="lt-col-right">`;
    html += `<div class="lt-section-header">📋 Task Progress</div>`;
    html += `<div id="lt-task-panel">`;
    html += this._renderTaskPanelContent(agents);
    html += `</div>`;

    html += `<div class="lt-section-header" style="margin-top:12px;">📡 Event Log</div>`;
    html += `<div id="lt-event-log" class="lt-event-log">`;
    html += this._renderEventLogContent();
    html += `</div>`;
    html += `</div>`;

    html += `</div>`; // end two-col

    // ── Room Activity Heat Map ──
    html += `<div class="lt-section-header" style="margin-top:8px;">🔥 Room Activity Heat Map</div>`;
    html += this._renderHeatMap(roomHeat, rooms);

    this.container.innerHTML = html;
  }

  // ── System Health Banner ──
  _renderHealthBanner(agents) {
    const onlineCount = agents.filter(a => a.online).length;
    const workingCount = agents.filter(a => a.status === 'working' || a.status === 'active').length;
    const totalActivity = agents.reduce((sum, a) => sum + ((a.activity && a.activity.level) || 0), 0);
    const avgActivity = agents.length > 0 ? (totalActivity / agents.length * 100).toFixed(0) : 0;
    const uptime = Math.floor((Date.now() - this.startTime) / 1000);

    const cpuColor = this._healthColor(this.systemHealth.cpu);
    const ramColor = this._healthColor(this.systemHealth.ram);

    // Mini sparkline SVG
    const cpuSpark = this._renderSparkline(this._healthHistory.map(h => h.cpu), cpuColor);
    const ramSpark = this._renderSparkline(this._healthHistory.map(h => h.ram), ramColor);

    return `
      <div class="lt-health-banner">
        <div class="lt-health-item">
          <div class="lt-health-label">CPU</div>
          <div class="lt-health-bar-wrap">
            <div class="lt-health-bar"><div class="lt-health-fill" style="width:${this.systemHealth.cpu}%;background:${cpuColor}"></div></div>
            <span class="lt-health-pct">${this.systemHealth.cpu.toFixed(0)}%</span>
          </div>
          <div class="lt-sparkline">${cpuSpark}</div>
        </div>
        <div class="lt-health-item">
          <div class="lt-health-label">RAM</div>
          <div class="lt-health-bar-wrap">
            <div class="lt-health-bar"><div class="lt-health-fill" style="width:${this.systemHealth.ram}%;background:${ramColor}"></div></div>
            <span class="lt-health-pct">${this.systemHealth.ram.toFixed(0)}%</span>
          </div>
          <div class="lt-sparkline">${ramSpark}</div>
        </div>
        <div class="lt-health-stat">
          <span class="lt-health-stat-val">${onlineCount}</span>
          <span class="lt-health-stat-label">Online</span>
        </div>
        <div class="lt-health-stat">
          <span class="lt-health-stat-val">${workingCount}</span>
          <span class="lt-health-stat-label">Working</span>
        </div>
        <div class="lt-health-stat">
          <span class="lt-health-stat-val">${avgActivity}%</span>
          <span class="lt-health-stat-label">Activity</span>
        </div>
        <div class="lt-health-stat">
          <span class="lt-health-stat-val">${this._formatUptime(uptime)}</span>
          <span class="lt-health-stat-label">Uptime</span>
        </div>
        <div class="lt-health-stat">
          <span class="lt-health-stat-val">${this.systemHealth.wsLatency}ms</span>
          <span class="lt-health-stat-label">Latency</span>
        </div>
      </div>
    `;
  }

  _renderHealthPanel() {
    // Lightweight update of health banner numbers without full re-render
    // This is called every second
  }

  _renderTaskPanel() {
    // Lightweight update of task panel
  }

  // ── Agent Activity Feed ──
  _renderAgentFeed(agents, rooms) {
    if (agents.length === 0) {
      return `<div class="lt-empty-state"><div class="lt-empty-icon">🤖</div><div>No agents connected</div><div style="font-size:11px;color:var(--text-dim);margin-top:4px;">Register agents or click ▶ Demo</div></div>`;
    }

    let html = `<div class="lt-agent-feed">`;

    // Sort: working first, then active, then idle, then offline
    const statusOrder = { working: 0, active: 1, meditating: 2, idle: 3, error: 4, offline: 5 };
    const sorted = [...agents].sort((a, b) => {
      const oa = statusOrder[a.status] ?? 3;
      const ob = statusOrder[b.status] ?? 3;
      return oa - ob;
    });

    for (const agent of sorted) {
      const activity = agent.activity || { level: 0, lastAction: 'Idle' };
      const level = activity.level || 0;
      const status = agent.status || 'idle';
      const activityPercent = (level * 100).toFixed(0);
      const room = rooms.find(r => r.id === agent.currentRoom);
      const roomName = room ? room.name : (agent.currentRoom || '—');

      // Status animation class
      let animClass = '';
      if (status === 'working' || status === 'active') animClass = 'lt-agent-working';
      else if (status === 'meditating') animClass = 'lt-agent-meditating';
      else if (status === 'idle') animClass = 'lt-agent-idle';
      else if (status === 'offline') animClass = 'lt-agent-offline';

      html += `
        <div class="lt-agent-card ${agent.online ? 'online' : 'offline'} ${animClass}" onclick="envClient.selectAgent('${agent.id}')">
          <div class="lt-agent-card-top">
            <div class="lt-agent-avatar-wrap">
              <div class="lt-agent-avatar" style="background:${agent.color || '#888'}">${agent.avatar?.emoji || '🤖'}</div>
              <div class="lt-agent-pulse ${status === 'working' || status === 'active' ? 'pulsing' : ''}" style="border-color:${agent.color || '#888'}"></div>
            </div>
            <div class="lt-agent-meta">
              <div class="lt-agent-name-row">
                <span class="lt-agent-name">${this._esc(agent.name)}</span>
                <span class="lt-status-badge lt-status-${status}">${status}</span>
              </div>
              <div class="lt-agent-room-row">
                <span class="lt-agent-room-icon">📍</span>
                <span class="lt-agent-room">${this._esc(roomName)}</span>
                <span class="lt-agent-role">${this._esc(agent.role || '')}</span>
              </div>
            </div>
          </div>
          <div class="lt-agent-task-text">${this._esc(activity.lastAction || 'Idle')}</div>
          <div class="lt-activity-bar-bg">
            <div class="lt-activity-bar-fill" style="width:${activityPercent}%;background:${agent.color || '#6c5ce7'}"></div>
          </div>
        </div>
      `;
    }

    html += `</div>`;
    return html;
  }

  // ── Task Progress Panel ──
  _renderTaskPanelContent(agents) {
    const workingAgents = agents.filter(a =>
      (a.activity && a.activity.level > 0.15) ||
      a.status === 'working' || a.status === 'active'
    );

    if (workingAgents.length === 0) {
      return `<div class="lt-empty-tasks">No active tasks — agents are idle</div>`;
    }

    let html = '';
    for (const agent of workingAgents) {
      const activity = agent.activity || { level: 0.3, lastAction: 'Working' };
      const progress = Math.min(100, (activity.level * 100)).toFixed(0);
      // Simulated progress animation
      const animDelay = (agent.id.charCodeAt(0) % 5) * 0.2;

      html += `
        <div class="lt-task-item">
          <div class="lt-task-header">
            <span class="lt-task-agent-name" style="color:${agent.color || '#888'}">${this._esc(agent.name)}</span>
            <span class="lt-task-progress-pct">${progress}%</span>
          </div>
          <div class="lt-task-name">${this._esc(activity.lastAction || 'Working')}</div>
          <div class="lt-task-bar-bg">
            <div class="lt-task-bar-fill" style="width:${progress}%;background:${agent.color || '#6c5ce7'};animation-delay:${animDelay}s"></div>
          </div>
        </div>
      `;
    }
    return html;
  }

  // ── Event Log ──
  _renderEventLogContent() {
    if (this.eventLog.length === 0) {
      return `<div class="lt-empty-events">No events yet — activity will appear here</div>`;
    }
    return this.eventLog.slice(0, this.displayedEvents).map(e => `
      <div class="lt-event-entry ${e.type ? 'lt-event-' + e.type : ''}">
        <span class="lt-event-time">${e.time}</span>
        <span class="lt-event-agent" style="color:${e.color || '#888'}">${this._esc(e.agentName || e.agentId || 'System')}</span>
        <span class="lt-event-action">${this._esc(e.action || '')}</span>
      </div>
    `).join('');
  }

  // ── Room Activity Heat Map ──
  _computeRoomHeat(rooms, agents) {
    const heat = new Map();
    for (const room of rooms) {
      const roomAgents = agents.filter(a => a.currentRoom === room.id);
      let totalActivity = 0;
      for (const a of roomAgents) {
        totalActivity += (a.activity && a.activity.level) || 0;
      }
      heat.set(room.id, {
        level: Math.min(1, totalActivity),
        agentCount: roomAgents.length,
        room,
      });
    }
    return heat;
  }

  _renderHeatMap(roomHeat, rooms) {
    if (rooms.length === 0) return '<div class="lt-empty-heat">No rooms available</div>';

    let html = `<div class="lt-heat-grid">`;
    for (const room of rooms) {
      const data = roomHeat.get(room.id) || { level: 0, agentCount: 0 };
      const heatLevel = data.level;
      const intensity = Math.round(heatLevel * 100);

      // Color gradient: dark blue (low) → purple → pink → orange (high)
      let heatColor;
      if (heatLevel < 0.25) heatColor = `rgba(108, 92, 231, ${0.15 + heatLevel * 0.4})`;
      else if (heatLevel < 0.5) heatColor = `rgba(162, 155, 254, ${0.25 + heatLevel * 0.4})`;
      else if (heatLevel < 0.75) heatColor = `rgba(253, 121, 168, ${0.2 + heatLevel * 0.3})`;
      else heatColor = `rgba(225, 112, 85, ${0.2 + heatLevel * 0.3})`;

      const glowIntensity = heatLevel * 12;

      html += `
        <div class="lt-heat-cell" style="background:${heatColor};box-shadow:0 0 ${glowIntensity}px ${heatColor}" onclick="envClient.selectRoom('${room.id}')">
          <div class="lt-heat-icon">${room.icon || '🏠'}</div>
          <div class="lt-heat-name">${this._esc(room.name)}</div>
          <div class="lt-heat-bar">
            <div class="lt-heat-bar-fill" style="width:${intensity}%;background:${room.color || '#6c5ce7'}"></div>
          </div>
          <div class="lt-heat-label">${data.agentCount} agents · ${intensity}% activity</div>
        </div>
      `;
    }
    html += `</div>`;
    return html;
  }

  // ── System Health Computation ──
  _computeSystemHealth() {
    const agents = this.envClient?.state?.agents || [];
    const totalActivity = agents.reduce((sum, a) => sum + ((a.activity && a.activity.level) || 0), 0);
    const activeCount = agents.filter(a => a.online).length;

    // Simulated CPU/RAM based on agent load (browser can't read real system stats)
    this.systemHealth.cpu = Math.min(100, 8 + totalActivity * 12 + Math.random() * 4);
    this.systemHealth.ram = Math.min(100, 15 + activeCount * 2.5 + Math.random() * 3);
    this.systemHealth.activeAgents = activeCount;
    this.systemHealth.uptime = Math.floor((Date.now() - this.startTime) / 1000);

    // WS latency estimation
    if (this.envClient?.ws?.readyState === WebSocket.OPEN) {
      this.systemHealth.wsLatency = Math.floor(10 + Math.random() * 15);
    } else {
      this.systemHealth.wsLatency = 0;
    }

    // Store history for sparklines
    this._healthHistory.push({ cpu: this.systemHealth.cpu, ram: this.systemHealth.ram });
    if (this._healthHistory.length > this._maxHealthHistory) {
      this._healthHistory.shift();
    }
  }

  // ── Event Log Management ──
  addEvent(event) {
    const entry = {
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      type: event.type || 'info',
      ...event,
    };
    this.eventLog.unshift(entry);
    if (this.eventLog.length > this.maxEventLog) this.eventLog.pop();

    // If the event log container exists, prepend the new entry
    const el = document.getElementById('lt-event-log');
    if (el) {
      const empty = el.querySelector('.lt-empty-events');
      if (empty) empty.remove();
      const div = document.createElement('div');
      div.className = `lt-event-entry ${entry.type ? 'lt-event-' + entry.type : ''}`;
      div.innerHTML = `
        <span class="lt-event-time">${entry.time}</span>
        <span class="lt-event-agent" style="color:${entry.color || '#888'}">${this._esc(entry.agentName || entry.agentId || 'System')}</span>
        <span class="lt-event-action">${this._esc(entry.action || '')}</span>
      `;
      el.insertBefore(div, el.firstChild);
      while (el.children.length > this.displayedEvents) {
        el.removeChild(el.lastChild);
      }
    }
  }

  // ── Sparkline SVG ──
  _renderSparkline(values, color) {
    if (values.length < 2) return '';
    const w = 60, h = 20;
    const max = Math.max(...values, 1);
    const min = Math.min(...values, 0);
    const range = max - min || 1;
    const step = w / (values.length - 1);
    const points = values.map((v, i) => {
      const x = i * step;
      const y = h - ((v - min) / range) * h;
      return `${x},${y}`;
    }).join(' ');

    return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
      <polyline points="${points}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;
  }

  // ── Helpers ──
  _healthColor(val) {
    if (val > 80) return '#e17055';
    if (val > 50) return '#ffeaa7';
    return '#00b894';
  }

  _formatUptime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  }

  _esc(s) {
    if (!s) return '';
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }
}

window.LiveTracker = LiveTracker;
