/**
 * Env Renderer — Canvas-based world map renderer.
 * Draws rooms, agents, connections, and animations.
 * 
 * PM Visual Overhaul 2026-05-19:
 * - Grid layout (responsive, not stacked)
 * - Zoom (mouse wheel) + pan (drag)
 * - Live activity indicators (room glow/pulse)
 * - Message flow particles between rooms
 * - Inter-room connection lines (thickness = traffic)
 * - Room detail overlay on click
 * - Agent selection in chat
 * - Observer overlap visualization
 * - FAM CHAT toggle
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
    this.agentPositions = new Map();
    this.demoMode = false;
    this.demoAgents = [];

    // ── Camera (zoom + pan) ──
    this.camera = { x: 0, y: 0, zoom: 1 };
    this.isPanning = false;
    this.panStart = { x: 0, y: 0 };
    this.panCameraStart = { x: 0, y: 0 };

    // ── Message flow particles ──
    this.flowParticles = []; // { fromRoomId, toRoomId, t, speed, color }

    // ── Observer overlap data ──
    this.overlaps = []; // { agentId1, agentId2, strength, color1, color2 }
    this.knowledgeTransferParticles = []; // burst particles on transfer

    // ── Room detail overlay ──
    this.showRoomDetail = false;
    this.roomDetailData = null;

    // ── FAM CHAT toggle ──
    this.famChatMode = false; // false = room chat, true = global/fam chat

    // ── Agent selection in chat ──
    this.chatSelectedAgentId = null;

    // ── Inter-room connection traffic ──
    this.roomTraffic = new Map(); // "roomA->roomB" -> count

    // ── Layout config ──
    this.layoutConfig = {
      roomWidth: 260,
      roomHeight: 180,
      roomMargin: 28,
      headerHeight: 30,
      minCols: 2,
      maxCols: 4,
    };

    this._tryResize();
    window.addEventListener('resize', () => this.resize());
    if (document.readyState !== 'complete') {
      window.addEventListener('load', () => this.resize());
    }
  }

  // ── Coordinate Transforms ──
  _worldToScreen(wx, wy) {
    return {
      x: (wx - this.camera.x) * this.camera.zoom,
      y: (wy - this.camera.y) * this.camera.zoom,
    };
  }

  _screenToWorld(sx, sy) {
    return {
      x: sx / this.camera.zoom + this.camera.x,
      y: sy / this.camera.zoom + this.camera.y,
    };
  }

  _tryResize() {
    if (this.resize()) return;
    requestAnimationFrame(() => {
      if (this.resize()) return;
      setTimeout(() => this.resize(), 100);
    });
  }

  resize() {
    const container = this.canvas.parentElement;
    if (!container) return false;
    const w = container.clientWidth;
    const h = container.clientHeight;
    if (w > 0 && h > 0) {
      if (this.canvas.width !== w || this.canvas.height !== h) {
        this.canvas.width = w;
        this.canvas.height = h;
      }
      return true;
    }
    return false;
  }

  // ── Layout Computation ──
  _computeRoomLayout() {
    const { roomWidth, roomHeight, roomMargin, minCols, maxCols } = this.layoutConfig;
    const rooms = this.worldState.rooms || [];
    const count = rooms.length;
    if (count === 0) return;

    // Determine columns based on canvas width
    const canvasW = this.canvas.width;
    const availableWidth = canvasW - 40; // 20px padding each side
    let cols = Math.floor((availableWidth + roomMargin) / (roomWidth + roomMargin));
    cols = Math.max(minCols, Math.min(maxCols, cols));
    // For 8 rooms: aim for 4x2 or 3x3
    if (count <= 4) cols = Math.min(count, 2);
    else if (count <= 6) cols = 3;
    else cols = 4;

    const rows = Math.ceil(count / cols);
    const startX = 20;
    const startY = 20;

    // Assign grid positions
    for (let i = 0; i < count; i++) {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const room = rooms[i];
      if (!room._gridPos) room._gridPos = {};
      room._gridPos.x = startX + col * (roomWidth + roomMargin);
      room._gridPos.y = startY + row * (roomHeight + roomMargin);
      room._gridPos.w = roomWidth;
      room._gridPos.h = roomHeight;
      // Update position/size for backward compat
      room.position = { x: room._gridPos.x, y: room._gridPos.y };
      room.size = { w: roomWidth, h: roomHeight };
    }

    // Store grid info for canvas sizing
    this._gridInfo = { cols, rows, totalW: startX + cols * (roomWidth + roomMargin) + 20, totalH: startY + rows * (roomHeight + roomMargin) + 20 };
  }

  _computeAgentPositionsInRoom(room) {
    const positions = [];
    const count = room.agents ? room.agents.length : 0;
    if (count === 0) return positions;
    const { roomWidth, roomHeight, headerHeight } = this.layoutConfig;
    const cols = Math.min(count, 3);
    const rows = Math.ceil(count / cols);
    const cellW = (roomWidth - 24) / Math.max(cols, 1);
    const cellH = (roomHeight - headerHeight - 24) / Math.max(rows, 1);
    for (let i = 0; i < count; i++) {
      const col = i % cols;
      const row = Math.floor(i / cols);
      positions.push({
        x: room.position.x + 12 + col * cellW + cellW / 2,
        y: room.position.y + headerHeight + 12 + row * cellH + cellH / 2,
      });
    }
    return positions;
  }

  // ── State Updates ──
  updateWorldState(state) {
    this.worldState = state;
    this._computeRoomLayout();

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

    // Track room-to-room traffic from connections
    if (state.connections) {
      this.roomTraffic.clear();
      for (const conn of state.connections) {
        const fromRoom = this._findAgentRoom(conn.from);
        const toRoom = this._findAgentRoom(conn.to);
        if (fromRoom && toRoom && fromRoom !== toRoom) {
          const key = `${fromRoom}->${toRoom}`;
          this.roomTraffic.set(key, (this.roomTraffic.get(key) || 0) + 1);
        }
      }
    }
  }

  _findAgentRoom(agentId) {
    for (const room of (this.worldState.rooms || [])) {
      if (room.agents && room.agents.find(a => a.id === agentId)) return room.id;
    }
    return null;
  }

  // ── Flow Particles ──
  spawnFlowParticle(fromRoomId, toRoomId, color) {
    this.flowParticles.push({
      fromRoomId,
      toRoomId,
      t: 0,
      speed: 0.4 + Math.random() * 0.3,
      color: color || '#6c5ce7',
      size: 3 + Math.random() * 2,
    });
  }

  _updateFlowParticles(dt) {
    for (let i = this.flowParticles.length - 1; i >= 0; i--) {
      const p = this.flowParticles[i];
      p.t += p.speed * dt;
      if (p.t >= 1) this.flowParticles.splice(i, 1);
    }
  }

  _drawFlowParticles() {
    const rooms = this.worldState.rooms || [];
    for (const p of this.flowParticles) {
      const fromRoom = rooms.find(r => r.id === p.fromRoomId);
      const toRoom = rooms.find(r => r.id === p.toRoomId);
      if (!fromRoom || !toRoom) continue;

      const from = { x: fromRoom.position.x + fromRoom.size.w / 2, y: fromRoom.position.y + fromRoom.size.h / 2 };
      const to = { x: toRoom.position.x + toRoom.size.w / 2, y: toRoom.position.y + toRoom.size.h / 2 };

      // Bezier curve
      const midX = (from.x + to.x) / 2;
      const midY = (from.y + to.y) / 2 - 40;
      const px = (1 - p.t) * (1 - p.t) * from.x + 2 * (1 - p.t) * p.t * midX + p.t * p.t * to.x;
      const py = (1 - p.t) * (1 - p.t) * from.y + 2 * (1 - p.t) * p.t * midY + p.t * p.t * to.y;

      const screenPos = this._worldToScreen(px, py);
      const alpha = Math.sin(p.t * Math.PI) * 0.8;

      // Glow
      const ctx = this.ctx;
      ctx.save();
      ctx.globalAlpha = alpha * 0.4;
      ctx.fillStyle = p.color;
      ctx.shadowColor = p.color;
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.arc(screenPos.x, screenPos.y, p.size * this.camera.zoom, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();

      // Core
      ctx.fillStyle = p.color;
      ctx.globalAlpha = alpha;
      ctx.beginPath();
      ctx.arc(screenPos.x, screenPos.y, p.size * 0.6 * this.camera.zoom, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
    }
  }

  // ── Observer Overlaps ──
  setOverlaps(overlaps) {
    this.overlaps = overlaps || [];
  }

  spawnKnowledgeTransfer(agentId1, agentId2, color) {
    const pos1 = this.agentPositions.get(agentId1);
    const pos2 = this.agentPositions.get(agentId2);
    if (!pos1 || !pos2) return;
    const mx = (pos1.x + pos2.x) / 2;
    const my = (pos1.y + pos2.y) / 2;
    for (let i = 0; i < 12; i++) {
      const angle = (Math.PI * 2 * i) / 12;
      this.knowledgeTransferParticles.push({
        x: mx, y: my,
        vx: Math.cos(angle) * (40 + Math.random() * 30),
        vy: Math.sin(angle) * (40 + Math.random() * 30),
        life: 1,
        color: color || '#a29bfe',
        size: 2 + Math.random() * 2,
      });
    }
  }

  _updateKnowledgeParticles(dt) {
    for (let i = this.knowledgeTransferParticles.length - 1; i >= 0; i--) {
      const p = this.knowledgeTransferParticles[i];
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.life -= dt * 1.5;
      p.vx *= 0.98;
      p.vy *= 0.98;
      if (p.life <= 0) this.knowledgeTransferParticles.splice(i, 1);
    }
  }

  _drawObserverOverlaps() {
    const ctx = this.ctx;
    for (const overlap of this.overlaps) {
      const pos1 = this.agentPositions.get(overlap.agentId1);
      const pos2 = this.agentPositions.get(overlap.agentId2);
      if (!pos1 || !pos2) continue;

      const s1 = this._worldToScreen(pos1.x, pos1.y);
      const s2 = this._worldToScreen(pos2.x, pos2.y);
      const z = this.camera.zoom;
      const r = 28 * z;

      // Shared gradient connection
      const grad = ctx.createLinearGradient(s1.x, s1.y, s2.x, s2.y);
      grad.addColorStop(0, this._hexToRgba(overlap.color1 || '#6c5ce7', overlap.strength * 0.5));
      grad.addColorStop(1, this._hexToRgba(overlap.color2 || '#a29bfe', overlap.strength * 0.5));

      ctx.strokeStyle = grad;
      ctx.lineWidth = 1 + overlap.strength * 3;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(s1.x, s1.y);
      ctx.lineTo(s2.x, s2.y);
      ctx.stroke();
      ctx.setLineDash([]);

      // Overlap zone (intersection circles)
      const dist = Math.sqrt((s2.x - s1.x) ** 2 + (s2.y - s1.y) ** 2);
      if (dist < r * 2 && dist > 0) {
        const overlapAlpha = overlap.strength * 0.15;
        const midX = (s1.x + s2.x) / 2;
        const midY = (s1.y + s2.y) / 2;
        const grad2 = ctx.createRadialGradient(midX, midY, 0, midX, midY, r * 0.8);
        grad2.addColorStop(0, this._hexToRgba(overlap.color1 || '#6c5ce7', overlapAlpha));
        grad2.addColorStop(0.5, this._hexToRgba('#a29bfe', overlapAlpha * 0.6));
        grad2.addColorStop(1, 'rgba(162,155,254,0)');
        ctx.fillStyle = grad2;
        ctx.beginPath();
        ctx.arc(midX, midY, r * 0.8, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Knowledge transfer particles
    for (const p of this.knowledgeTransferParticles) {
      const sp = this._worldToScreen(p.x, p.y);
      ctx.globalAlpha = p.life;
      ctx.fillStyle = p.color;
      ctx.shadowColor = p.color;
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.arc(sp.x, sp.y, p.size * this.camera.zoom, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    ctx.shadowBlur = 0;
  }

  // ── Main Render ──
  render(dt) {
    this.time += dt;
    const ctx = this.ctx;
    const state = this.worldState;

    // Clear
    ctx.fillStyle = '#0a0a0f';
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    if (!state.rooms || state.rooms.length === 0) {
      if (!this.demoMode) {
        this._drawLoadingState();
        return;
      }
    }

    // Apply camera transform
    ctx.save();
    ctx.translate(this.canvas.width / 2, this.canvas.height / 2);
    ctx.scale(this.camera.zoom, this.camera.zoom);
    ctx.translate(-this.camera.x, -this.camera.y);

    // Draw grid
    this._drawGrid();

    // Update particles
    this._updateFlowParticles(dt);
    this._updateKnowledgeParticles(dt);

    // Draw inter-room connections
    this._drawRoomConnections();

    // Draw flow particles
    this._drawFlowParticles();

    // Draw observer overlaps
    this._drawObserverOverlaps();

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
            const currentPos = this.agentPositions.get(agent.id) || targetPos;
            const lerpFactor = 1 - Math.pow(0.001, dt);
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

    // Demo agents
    if (this.demoMode) {
      this._updateDemoAgents(dt);
      for (const demo of this.demoAgents) {
        this._drawAgent(demo, { x: demo.x, y: demo.y }, false);
      }
    }

    ctx.restore();

    // Draw HUD elements (not affected by camera)
    this._drawZoomIndicator();
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
    ctx.strokeStyle = 'rgba(42, 42, 58, 0.2)';
    ctx.lineWidth = 1;
    const gridSize = 40;
    // Calculate visible area
    const visW = this.canvas.width / this.camera.zoom;
    const visH = this.canvas.height / this.camera.zoom;
    const startX = this.camera.x - visW / 2;
    const startY = this.camera.y - visH / 2;
    const endX = startX + visW;
    const endY = startY + visH;

    const gx0 = Math.floor(startX / gridSize) * gridSize;
    const gy0 = Math.floor(startY / gridSize) * gridSize;
    for (let x = gx0; x <= endX; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, startY);
      ctx.lineTo(x, endY);
      ctx.stroke();
    }
    for (let y = gy0; y <= endY; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(startX, y);
      ctx.lineTo(endX, y);
      ctx.stroke();
    }
  }

  _drawZoomIndicator() {
    const ctx = this.ctx;
    ctx.fillStyle = 'rgba(136, 136, 170, 0.5)';
    ctx.font = '10px "Segoe UI", system-ui, sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'bottom';
    ctx.fillText(`${Math.round(this.camera.zoom * 100)}%`, this.canvas.width - 10, this.canvas.height - 10);
    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
  }

  // ── Room Rendering ──
  _drawRoom(room) {
    const ctx = this.ctx;
    const { x, y } = room.position;
    const { w, h } = room.size;
    const isHovered = room.id === this.hoveredRoom;
    const isSelected = room.id === this.selectedRoomId;
    const agentCount = room.agentCount || 0;

    // Compute aggregate activity for this room
    let roomActivity = 0;
    if (room.agents) {
      for (const a of room.agents) {
        roomActivity += (a.activity && a.activity.level) ? a.activity.level : 0;
      }
      roomActivity = Math.min(1, roomActivity);
    }

    // Activity glow (pulsing border when agents are active)
    if (roomActivity > 0.1) {
      const glowAlpha = roomActivity * 0.3 * (0.7 + Math.sin(this.time * 2) * 0.3);
      const glowRadius = 8 + roomActivity * 4;
      ctx.shadowColor = room.color || '#6c5ce7';
      ctx.shadowBlur = glowRadius;
      ctx.strokeStyle = this._hexToRgba(room.color || '#6c5ce7', glowAlpha);
      ctx.lineWidth = 2;
      this._roundRect(x - 2, y - 2, w + 4, h + 4, 12);
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    // Room background
    const bgGrad = ctx.createLinearGradient(x, y, x, y + h);
    bgGrad.addColorStop(0, room.bgColor || 'rgba(30,30,40,0.9)');
    bgGrad.addColorStop(1, 'rgba(20,20,28,0.95)');
    ctx.fillStyle = bgGrad;
    this._roundRect(x, y, w, h, 10);
    ctx.fill();

    // Room border
    ctx.strokeStyle = isSelected ? (room.color || '#6c5ce7') : (room.borderColor || 'rgba(99,110,114,0.3)');
    ctx.lineWidth = isSelected ? 2.5 : 1.5;
    this._roundRect(x, y, w, h, 10);
    ctx.stroke();

    // Header bar
    const headGrad = ctx.createLinearGradient(x, y, x, y + 30);
    headGrad.addColorStop(0, (room.color || '#6c5ce7') + '33');
    headGrad.addColorStop(1, (room.color || '#6c5ce7') + '11');
    ctx.fillStyle = headGrad;
    this._roundRectTop(x, y, w, 30, 10);
    ctx.fill();

    // Room icon + name
    ctx.font = '13px "Segoe UI", system-ui, sans-serif';
    ctx.fillStyle = room.color || '#888';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${room.icon || '🏠'} ${room.name}`, x + 10, y + 15);

    // Agent count badge
    if (agentCount > 0) {
      const badgeX = x + w - 28;
      const badgeY = y + 10;
      ctx.fillStyle = (room.color || '#6c5ce7') + '44';
      ctx.beginPath();
      ctx.arc(badgeX, badgeY, 10, 0, Math.PI * 2);
      ctx.fill();
      ctx.font = 'bold 11px "Segoe UI", system-ui, sans-serif';
      ctx.fillStyle = '#e0e0f0';
      ctx.textAlign = 'center';
      ctx.fillText(String(agentCount), badgeX, badgeY + 1);
      ctx.textAlign = 'left';
    }

    // Activity sparkline at bottom of room
    if (roomActivity > 0.05) {
      const barY = y + h - 8;
      const barW = w - 20;
      const barH = 3;
      ctx.fillStyle = 'rgba(42, 42, 58, 0.6)';
      this._roundRect(x + 10, barY, barW, barH, 1.5);
      ctx.fill();
      const activeW = barW * roomActivity;
      const actGrad = ctx.createLinearGradient(x + 10, barY, x + 10 + activeW, barY);
      actGrad.addColorStop(0, room.color || '#6c5ce7');
      actGrad.addColorStop(1, this._lightenColor(room.color || '#6c5ce7', 20));
      ctx.fillStyle = actGrad;
      this._roundRect(x + 10, barY, activeW, barH, 1.5);
      ctx.fill();
    }
  }

  // ── Agent Rendering ──
  _drawAgent(agent, pos, isSelected) {
    const ctx = this.ctx;
    const radius = agent.avatar ? agent.avatar.radius : 18;
    const color = agent.color || '#888';
    const activity = agent.activity || { level: 0, lastAction: '' };
    const isOnline = agent.online;
    const status = agent.status || 'idle';

    // Status-based color for the pulse ring
    const statusColors = {
      active: '#00b894',
      working: '#74b9ff',
      meditating: '#a29bfe',
      idle: '#636e72',
      error: '#e17055',
      offline: '#636e72',
    };
    const pulseColor = statusColors[status] || color;

    // Activity pulse ring
    if (activity.level > 0.1) {
      const pulseRadius = radius + 4 + Math.sin(this.time * 3) * 3 * activity.level;
      const alpha = activity.level * 0.5;
      ctx.strokeStyle = this._hexToRgba(pulseColor, alpha);
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

      // Selection glow
      ctx.shadowColor = '#ffffff';
      ctx.shadowBlur = 10;
      ctx.strokeStyle = 'rgba(255,255,255,0.3)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius + 10, 0, Math.PI * 2);
      ctx.stroke();
      ctx.shadowBlur = 0;
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
      ctx.fillStyle = pulseColor;
      this._roundRect(pos.x - barWidth / 2, barY, barWidth * activity.level, 3, 1.5);
      ctx.fill();
    }

    // Status-specific animation
    if (status === 'working' && isOnline) {
      // Progress bar animation
      const progressW = radius * 2;
      const progressY = (pos.y + radius + 12) + 16;
      const progressH = 2;
      ctx.fillStyle = 'rgba(42, 42, 58, 0.6)';
      this._roundRect(pos.x - progressW / 2, progressY, progressW, progressH, 1);
      ctx.fill();
      const fillW = progressW * ((this.time * 0.3 + (agent.id.charCodeAt(0) % 10) * 0.1) % 1);
      ctx.fillStyle = pulseColor;
      this._roundRect(pos.x - progressW / 2, progressY, fillW, progressH, 1);
      ctx.fill();
    } else if (status === 'meditating') {
      // Pulsing dot
      const dotY = pos.y + radius + 28;
      const dotAlpha = 0.4 + Math.sin(this.time * 2) * 0.3;
      ctx.fillStyle = this._hexToRgba(pulseColor, dotAlpha);
      ctx.beginPath();
      ctx.arc(pos.x, dotY, 3, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
  }

  // ── Inter-Room Connections ──
  _drawRoomConnections() {
    const ctx = this.ctx;
    const rooms = this.worldState.rooms || [];
    if (this.roomTraffic.size === 0) return;

    // Find max traffic for normalization
    let maxTraffic = 1;
    for (const count of this.roomTraffic.values()) {
      maxTraffic = Math.max(maxTraffic, count);
    }

    for (const [key, count] of this.roomTraffic) {
      const [fromId, toId] = key.split('->');
      const fromRoom = rooms.find(r => r.id === fromId);
      const toRoom = rooms.find(r => r.id === toId);
      if (!fromRoom || !toRoom) continue;

      const from = { x: fromRoom.position.x + fromRoom.size.w / 2, y: fromRoom.position.y + fromRoom.size.h / 2 };
      const to = { x: toRoom.position.x + toRoom.size.w / 2, y: toRoom.position.y + toRoom.size.h / 2 };

      const strength = count / maxTraffic;
      const alpha = 0.08 + strength * 0.2;
      const width = 1 + strength * 3;

      ctx.strokeStyle = `rgba(136,136,170,${alpha})`;
      ctx.lineWidth = width;
      ctx.setLineDash([6, 4]);

      // Curved line
      const midX = (from.x + to.x) / 2;
      const midY = (from.y + to.y) / 2 - 30;
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.quadraticCurveTo(midX, midY, to.x, to.y);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }

  // ── Legacy Connection Drawing (agent-to-agent) ──
  _drawConnections(connections, agents) {
    const ctx = this.ctx;
    if (!agents || !connections) return;

    for (const conn of connections) {
      const fromPos = this.agentPositions.get(conn.from);
      const toPos = this.agentPositions.get(conn.to);
      if (!fromPos || !toPos) continue;

      const alpha = conn.active ? 0.4 : 0.1;
      const fromAgent = agents.find(a => a.id === conn.from);
      const color = fromAgent?.color || '#888';

      ctx.strokeStyle = this._hexToRgba(color, alpha);
      ctx.lineWidth = conn.active ? 2 : 1;
      ctx.setLineDash(conn.active ? [] : [4, 4]);

      ctx.beginPath();
      ctx.moveTo(fromPos.x, fromPos.y);
      const midX = (fromPos.x + toPos.x) / 2;
      const midY = (fromPos.y + toPos.y) / 2 - 20;
      ctx.quadraticCurveTo(midX, midY, toPos.x, toPos.y);
      ctx.stroke();
      ctx.setLineDash([]);

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
      if (agent.x < 50 || agent.x > (this._gridInfo?.totalW || 1200) - 50) agent.vx *= -1;
      if (agent.y < 50 || agent.y > (this._gridInfo?.totalH || 800) - 50) agent.vy *= -1;
      agent.activity.level = 0.3 + Math.sin(this.time + agent.id.charCodeAt(0)) * 0.3;
    }
  }

  // ── Room Detail Overlay ──
  showRoomDetail(room) {
    this.showRoomDetail = true;
    this.roomDetailData = room;
  }

  hideRoomDetail() {
    this.showRoomDetail = false;
    this.roomDetailData = null;
  }

  // ── FAM CHAT Toggle ──
  setFamChatMode(enabled) {
    this.famChatMode = enabled;
  }

  // ── Agent Selection in Chat ──
  selectChatAgent(agentId) {
    this.chatSelectedAgentId = agentId;
  }

  // ── Drag State ──
  startDrag(agentId, x, y) {
    this.dragState = { agentId, offsetX: 0, offsetY: 0, active: true };
    const pos = this.agentPositions.get(agentId);
    if (pos) {
      const world = this._screenToWorld(x, y);
      this.dragState.offsetX = pos.x - world.x;
      this.dragState.offsetY = pos.y - world.y;
    }
  }

  updateDrag(x, y) {
    if (!this.dragState || !this.dragState.active) return;
    const world = this._screenToWorld(x, y);
    const newX = world.x + this.dragState.offsetX;
    const newY = world.y + this.dragState.offsetY;
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

  // ── Pan & Zoom ──
  startPan(x, y) {
    this.isPanning = true;
    this.panStart = { x, y };
    this.panCameraStart = { x: this.camera.x, y: this.camera.y };
  }

  updatePan(x, y) {
    if (!this.isPanning) return;
    const dx = (x - this.panStart.x) / this.camera.zoom;
    const dy = (y - this.panStart.y) / this.camera.zoom;
    this.camera.x = this.panCameraStart.x - dx;
    this.camera.y = this.panCameraStart.y - dy;
  }

  endPan() {
    this.isPanning = false;
  }

  zoomAt(screenX, screenY, factor) {
    // Zoom toward a specific screen point
    const worldBefore = this._screenToWorld(screenX, screenY);
    this.camera.zoom = Math.max(0.3, Math.min(3, this.camera.zoom * factor));
    const worldAfter = this._screenToWorld(screenX, screenY);
    this.camera.x += (worldAfter.x - worldBefore.x);
    this.camera.y += (worldAfter.y - worldBefore.y);
  }

  resetView() {
    this.camera = { x: (this._gridInfo?.totalW || 600) / 2, y: (this._gridInfo?.totalH || 400) / 2, zoom: 1 };
  }

  // Hit testing (screen coordinates)
  getAgentAt(screenX, screenY) {
    const world = this._screenToWorld(screenX, screenY);
    const entries = Array.from(this.agentPositions.entries());
    for (let i = entries.length - 1; i >= 0; i--) {
      const [agentId, pos] = entries[i];
      const dx = world.x - pos.x;
      const dy = world.y - pos.y;
      if (dx * dx + dy * dy < 18 * 18) {
        const agent = this.worldState.agents?.find(a => a.id === agentId);
        return agent || null;
      }
    }
    return null;
  }

  getRoomAt(screenX, screenY) {
    const world = this._screenToWorld(screenX, screenY);
    if (!this.worldState.rooms) return null;
    for (const room of this.worldState.rooms) {
      if (world.x >= room.position.x && world.x <= room.position.x + room.size.w &&
          world.y >= room.position.y && world.y <= room.position.y + room.size.h) {
        return room;
      }
    }
    return null;
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
}

window.EnvRenderer = EnvRenderer;
