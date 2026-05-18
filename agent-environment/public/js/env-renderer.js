/**
 * Env Renderer — Canvas-based world map renderer.
 * Draws rooms, agents, connections, and animations.
 */

class EnvRenderer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.worldState = { rooms: [], agents: [], connections: [], recentActivity: [] };
    this.hoveredAgent = null;
    this.hoveredRoom = null;
    this.selectedAgentId = null;
    this.selectedRoomId = null;
    this.time = 0;
    this.agentPositions = new Map(); // agentId -> { x, y } (interpolated)
    this.demoMode = false;
    this.demoAgents = [];

    // Delay resize to ensure DOM layout is complete
    // Use multiple strategies: immediate attempt, rAF, and timeout
    this._tryResize();
    window.addEventListener('resize', () => this.resize());
    // Also try resizing when the page fully loads
    if (document.readyState !== 'complete') {
      window.addEventListener('load', () => this.resize());
    }
  }

  _tryResize() {
    // Try immediate resize
    if (this.resize()) return;
    // Try after one rAF (browser may not have laid out yet)
    requestAnimationFrame(() => {
      if (this.resize()) return;
      // Try after a short delay as fallback
      setTimeout(() => this.resize(), 100);
    });
  }

  resize() {
    const container = this.canvas.parentElement;
    if (!container) return false;
    const w = container.clientWidth;
    const h = container.clientHeight;
    // Only resize if we have valid dimensions (avoid 0x0 canvas)
    if (w > 0 && h > 0) {
      // Only actually resize if dimensions changed (avoids unnecessary clears)
      if (this.canvas.width !== w || this.canvas.height !== h) {
        this.canvas.width = w;
        this.canvas.height = h;
      }
      return true;
    }
    return false;
  }

  updateWorldState(state) {
    this.worldState = state;
    // Initialize positions for new agents
    if (state.rooms) {
      for (const room of state.rooms) {
        if (room.agents) {
          const positions = this._computeAgentPositionsInRoom(room);
          room.agents.forEach((agent, i) => {
            const pos = positions[i] || { x: room.position.x + 50, y: room.position.y + 50 };
            if (!this.agentPositions.has(agent.id)) {
              this.agentPositions.set(agent.id, { x: pos.x, y: pos.y });
            }
          });
        }
      }
    }
  }

  _computeAgentPositionsInRoom(room) {
    const positions = [];
    const count = room.agents ? room.agents.length : 0;
    const cols = Math.min(count, 3);
    const rows = Math.ceil(count / cols);
    const cellW = (room.size.w - 24) / Math.max(cols, 1);
    const cellH = (room.size.h - 40) / Math.max(rows, 1);
    for (let i = 0; i < count; i++) {
      const col = i % cols;
      const row = Math.floor(i / cols);
      positions.push({
        x: room.position.x + 12 + col * cellW + cellW / 2,
        y: room.position.y + 30 + 12 + row * cellH + cellH / 2,
      });
    }
    return positions;
  }

  render(dt) {
    this.time += dt;
    const ctx = this.ctx;
    const state = this.worldState;

    // Clear
    ctx.fillStyle = '#0a0a0f';
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Draw grid
    this._drawGrid();

    // Show loading state if no rooms and no demo mode
    if (this.worldState.rooms.length === 0 && !this.demoMode) {
      this._drawLoadingState();
      return;
    }

    // Draw connections first (under rooms)
    if (state.connections) {
      this._drawConnections(state.connections, state.agents);
    }

    // Draw rooms
    if (state.rooms) {
      for (const room of state.rooms) {
        this._drawRoom(room);
      }
    }

    // Draw agents
    if (state.rooms) {
      for (const room of state.rooms) {
        if (room.agents) {
          const positions = this._computeAgentPositionsInRoom(room);
          room.agents.forEach((agent, i) => {
            const targetPos = positions[i] || { x: room.position.x + 50, y: room.position.y + 50 };
            // Interpolate position
            const currentPos = this.agentPositions.get(agent.id) || targetPos;
            const lerpFactor = 1 - Math.pow(0.001, dt); // Smooth lerp
            const newPos = {
              x: currentPos.x + (targetPos.x - currentPos.x) * lerpFactor,
              y: currentPos.y + (targetPos.y - currentPos.y) * lerpFactor,
            };
            this.agentPositions.set(agent.id, newPos);
            this._drawAgent(agent, newPos, agent.id === this.selectedAgentId);
          });
        }
      }
    }

    // Draw demo agents if in demo mode
    if (this.demoMode) {
      this._updateDemoAgents(dt);
      for (const demo of this.demoAgents) {
        this._drawAgent(demo, { x: demo.x, y: demo.y }, false);
      }
    }
  }

  _drawLoadingState() {
    const ctx = this.ctx;
    ctx.fillStyle = 'rgba(108, 92, 231, 0.15)';
    ctx.font = '16px "Segoe UI", system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('⏳ Waiting for world state...', this.canvas.width / 2, this.canvas.height / 2 - 10);
    ctx.font = '12px "Segoe UI", system-ui, sans-serif';
    ctx.fillStyle = 'rgba(136, 136, 170, 0.6)';
    ctx.fillText('Connect to the server or click ▶ Demo to begin', this.canvas.width / 2, this.canvas.height / 2 + 16);
    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
  }

  _drawGrid() {
    const ctx = this.ctx;
    ctx.strokeStyle = 'rgba(42, 42, 58, 0.3)';
    ctx.lineWidth = 1;
    const gridSize = 40;
    for (let x = 0; x < this.canvas.width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, this.canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < this.canvas.height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(this.canvas.width, y);
      ctx.stroke();
    }
  }

  _drawRoom(room) {
    const ctx = this.ctx;
    const { x, y } = room.position;
    const { w, h } = room.size;
    const isHovered = room.id === this.hoveredRoom;
    const isSelected = room.id === this.selectedRoomId;
    const agentCount = room.agentCount || 0;

    // Room background
    ctx.fillStyle = room.bgColor || 'rgba(99,110,114,0.08)';
    this._roundRect(x, y, w, h, 10);
    ctx.fill();

    // Room border
    ctx.strokeStyle = isSelected ? (room.color || '#6c5ce7') : (room.borderColor || 'rgba(99,110,114,0.3)');
    ctx.lineWidth = isSelected ? 2.5 : 1.5;
    this._roundRect(x, y, w, h, 10);
    ctx.stroke();

    // Header bar
    ctx.fillStyle = (room.color || '#6c5ce7') + '22';
    this._roundRectTop(x, y, w, 28, 10);
    ctx.fill();

    // Room icon + name
    ctx.font = '12px "Segoe UI", system-ui, sans-serif';
    ctx.fillStyle = room.color || '#888';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${room.icon || '🏠'} ${room.name}`, x + 8, y + 14);

    // Agent count badge
    if (agentCount > 0) {
      const badgeX = x + w - 24;
      const badgeY = y + 8;
      ctx.fillStyle = (room.color || '#6c5ce7') + '44';
      ctx.beginPath();
      ctx.arc(badgeX, badgeY, 9, 0, Math.PI * 2);
      ctx.fill();
      ctx.font = 'bold 10px "Segoe UI", system-ui, sans-serif';
      ctx.fillStyle = room.color || '#888';
      ctx.textAlign = 'center';
      ctx.fillText(String(agentCount), badgeX, badgeY + 1);
      ctx.textAlign = 'left';
    }
  }

  _drawAgent(agent, pos, isSelected) {
    const ctx = this.ctx;
    const radius = agent.avatar ? agent.avatar.radius : 18;
    const color = agent.color || '#888';
    const activity = agent.activity || { level: 0, lastAction: '' };
    const isOnline = agent.online;

    // Activity pulse ring
    if (activity.level > 0.1) {
      const pulseRadius = radius + 4 + Math.sin(this.time * 3) * 3 * activity.level;
      const alpha = activity.level * 0.5;
      ctx.strokeStyle = this._hexToRgba(color, alpha);
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, pulseRadius, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Selection ring
    if (isSelected) {
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius + 6, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Avatar circle
    const gradient = ctx.createRadialGradient(pos.x - 3, pos.y - 3, 0, pos.x, pos.y, radius);
    gradient.addColorStop(0, this._lightenColor(color, 30));
    gradient.addColorStop(1, color);
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
    ctx.fill();

    // Online indicator dot
    ctx.fillStyle = isOnline ? '#00b894' : '#636e72';
    ctx.beginPath();
    ctx.arc(pos.x + radius * 0.6, pos.y - radius * 0.6, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#0a0a0f';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Agent emoji
    const emoji = agent.avatar ? agent.avatar.emoji : '🤖';
    ctx.font = `${radius * 0.8}px "Segoe UI Emoji", "Apple Color Emoji", sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(emoji, pos.x, pos.y + 1);

    // Agent name label
    ctx.font = 'bold 10px "Segoe UI", system-ui, sans-serif';
    ctx.fillStyle = '#e0e0f0';
    ctx.textAlign = 'center';
    const label = agent.avatar ? agent.avatar.label : agent.name;
    const labelY = pos.y + radius + 12;

    // Label background
    const labelWidth = ctx.measureText(label).width + 8;
    ctx.fillStyle = 'rgba(10, 10, 15, 0.8)';
    this._roundRect(pos.x - labelWidth / 2, labelY - 7, labelWidth, 14, 3);
    ctx.fill();
    ctx.fillText(label, pos.x, labelY);

    // Activity bar (small, under label)
    if (activity.level > 0.05) {
      const barWidth = radius * 2;
      const barY = labelY + 10;
      ctx.fillStyle = 'rgba(42, 42, 58, 0.8)';
      this._roundRect(pos.x - barWidth / 2, barY, barWidth, 3, 1.5);
      ctx.fill();
      ctx.fillStyle = color;
      this._roundRect(pos.x - barWidth / 2, barY, barWidth * activity.level, 3, 1.5);
      ctx.fill();
    }

    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
  }

  _drawConnections(connections, agents) {
    const ctx = this.ctx;
    if (!agents || !connections) return;

    for (const conn of connections) {
      const fromAgent = agents.find(a => a.id === conn.from);
      const toAgent = agents.find(a => a.id === conn.to);
      if (!fromAgent || !toAgent) continue;

      const fromPos = this.agentPositions.get(conn.from);
      const toPos = this.agentPositions.get(conn.to);
      if (!fromPos || !toPos) continue;

      const alpha = conn.active ? 0.4 : 0.1;
      const color = fromAgent.color || '#888';

      ctx.strokeStyle = this._hexToRgba(color, alpha);
      ctx.lineWidth = conn.active ? 2 : 1;
      ctx.setLineDash(conn.active ? [] : [4, 4]);

      // Curved line
      ctx.beginPath();
      ctx.moveTo(fromPos.x, fromPos.y);
      const midX = (fromPos.x + toPos.x) / 2;
      const midY = (fromPos.y + toPos.y) / 2 - 20;
      ctx.quadraticCurveTo(midX, midY, toPos.x, toPos.y);
      ctx.stroke();
      ctx.setLineDash([]);

      // Animated dot along the line (if active)
      if (conn.active) {
        const t = (this.time * 0.5) % 1;
        const dotX = (1 - t) * (1 - t) * fromPos.x + 2 * (1 - t) * t * midX + t * t * toPos.x;
        const dotY = (1 - t) * (1 - t) * fromPos.y + 2 * (1 - t) * t * midY + t * t * toPos.y;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(dotX, dotY, 3, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  // ── Demo Mode ──
  enableDemo(demoAgents) {
    this.demoMode = true;
    this.demoAgents = demoAgents.map((d, i) => ({
      ...d,
      x: 100 + i * 120,
      y: 300,
      vx: (Math.random() - 0.5) * 40,
      vy: (Math.random() - 0.5) * 40,
      activity: { level: Math.random() * 0.5 + 0.3, lastAction: 'Demo mode' },
      avatar: { label: d.name, emoji: d.emoji || '🤖', radius: 18 },
      online: true,
    }));
  }

  _updateDemoAgents(dt) {
    for (const agent of this.demoAgents) {
      agent.x += agent.vx * dt;
      agent.y += agent.vy * dt;
      // Bounce off canvas edges
      if (agent.x < 50 || agent.x > this.canvas.width - 50) agent.vx *= -1;
      if (agent.y < 50 || agent.y > this.canvas.height - 50) agent.vy *= -1;
      // Pulse activity
      agent.activity.level = 0.3 + Math.sin(this.time + agent.id.charCodeAt(0)) * 0.3;
    }
  }

  // ── Helpers ──
  _roundRect(x, y, w, h, r) {
    const ctx = this.ctx;
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  _roundRectTop(x, y, w, h, r) {
    const ctx = this.ctx;
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h);
    ctx.lineTo(x, y + h);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  _hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16) || 128;
    const g = parseInt(hex.slice(3, 5), 16) || 128;
    const b = parseInt(hex.slice(5, 7), 16) || 128;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  _lightenColor(hex, amount) {
    const r = Math.min(255, (parseInt(hex.slice(1, 3), 16) || 128) + amount);
    const g = Math.min(255, (parseInt(hex.slice(3, 5), 16) || 128) + amount);
    const b = Math.min(255, (parseInt(hex.slice(5, 7), 16) || 128) + amount);
    return `rgb(${r}, ${g}, ${b})`;
  }

  // ── Drag State ──
  startDrag(agentId, x, y) {
    this.dragState = { agentId, offsetX: 0, offsetY: 0, active: true };
    const pos = this.agentPositions.get(agentId);
    if (pos) {
      this.dragState.offsetX = pos.x - x;
      this.dragState.offsetY = pos.y - y;
    }
  }

  updateDrag(x, y) {
    if (!this.dragState || !this.dragState.active) return;
    const newX = x + this.dragState.offsetX;
    const newY = y + this.dragState.offsetY;
    this.agentPositions.set(this.dragState.agentId, { x: newX, y: newY });
  }

  endDrag() {
    if (this.dragState) this.dragState.active = false;
    return this.dragState ? { ...this.dragState } : null;
  }

  isDragging() {
    return !!(this.dragState && this.dragState.active);
  }

  getDragAgentId() {
    return this.isDragging() ? this.dragState.agentId : null;
  }

  // Hit testing
  getAgentAt(x, y) {
    // Check in reverse order so top-drawn agents are picked first
    const entries = Array.from(this.agentPositions.entries());
    for (let i = entries.length - 1; i >= 0; i--) {
      const [agentId, pos] = entries[i];
      const dx = x - pos.x;
      const dy = y - pos.y;
      if (dx * dx + dy * dy < 18 * 18) {
        const agent = this.worldState.agents.find(a => a.id === agentId);
        return agent || null;
      }
    }
    return null;
  }

  getRoomAt(x, y) {
    if (!this.worldState.rooms) return null;
    for (const room of this.worldState.rooms) {
      if (x >= room.position.x && x <= room.position.x + room.size.w &&
          y >= room.position.y && y <= room.position.y + room.size.h) {
        return room;
      }
    }
    return null;
  }
}

// Export for use in env-client.js
window.EnvRenderer = EnvRenderer;
