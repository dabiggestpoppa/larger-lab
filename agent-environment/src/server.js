/**
 * Server — Main entry point for the Agent Virtual Environment.
 * Express + HTTP API + WebSocket real-time communication.
 * Wires up all modules: rooms, agents, sandbox, communication.
 */

const express = require('express');
const http = require('http');
const path = require('path');
const { WebSocketServer } = require('ws');

const config = require('./utils/config');
const logger = require('./utils/logger');

// Rooms
const roomManager = require('./rooms/room-manager');
const quantRoom = require('./rooms/quant-room');
const chatRoom = require('./rooms/chat-room');
const meditationRoom = require('./rooms/meditation-room');

// Communication
const messageBus = require('./communication/message-bus');
const broadcast = require('./communication/broadcast');
const directMessage = require('./communication/direct-message');

// Agents
const agentRegistry = require('./agents/agent-registry');
const agentSession = require('./agents/agent-session');
const agentTools = require('./agents/agent-tools');

// Sandbox
const { runPython } = require('./sandbox/python-runner');
const { runNode } = require('./sandbox/node-runner');
const { readFile, writeFile, listFiles } = require('./sandbox/file-system');

// World Engine (v2)
const worldEngine = require('./world-engine');

// ── Express App ──────────────────────────────────────────────────
const app = express();
app.use(express.json({ limit: '1mb' }));

// ── CORS Middleware ──────────────────────────────────────────────
// Allow cross-origin requests from any origin (agents may run on different ports)
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }
  next();
});

// ── Rate Limiting ────────────────────────────────────────────────
// Simple in-memory rate limiter: max 30 requests/second per agent ID (or IP)
const rateBuckets = new Map();
const RATE_LIMIT = 30;       // max requests
const RATE_WINDOW_MS = 1000; // per 1 second

function rateLimitCheck(identifier) {
  const now = Date.now();
  const bucket = rateBuckets.get(identifier);
  if (!bucket || now - bucket.windowStart > RATE_WINDOW_MS) {
    rateBuckets.set(identifier, { windowStart: now, count: 1 });
    return true;
  }
  bucket.count++;
  return bucket.count <= RATE_LIMIT;
}

// Clean up old rate limit entries every 60s
setInterval(() => {
  const now = Date.now();
  for (const [key, bucket] of rateBuckets) {
    if (now - bucket.windowStart > RATE_WINDOW_MS * 10) {
      rateBuckets.delete(key);
    }
  }
}, 60000);

app.use((req, res, next) => {
  // Use agent ID from body/params if available, otherwise IP
  const identifier = (req.body && req.body.agentId) || req.params.id || req.socket.remoteAddress;
  if (!rateLimitCheck(identifier)) {
    return res.status(429).json({
      success: false,
      error: 'Rate limit exceeded. Max 30 requests/second.',
      code: 'RATE_LIMIT_EXCEEDED',
    });
  }
  next();
});

// ── Input Validation Helpers ─────────────────────────────────────
const VALID_STATUSES = ['idle', 'working', 'meditating', 'active', 'error', 'offline'];
const VALID_MESSAGE_TYPES = ['chat', 'system', 'task', 'dm'];
const MAX_MESSAGE_LENGTH = 4096;
const MAX_NAME_LENGTH = 64;

function validateStatus(status) {
  if (!status || typeof status !== 'string') return { valid: false, error: 'Status is required' };
  const normalized = status.toLowerCase().trim();
  if (!VALID_STATUSES.includes(normalized)) {
    return { valid: false, error: `Invalid status. Valid: ${VALID_STATUSES.join(', ')}` };
  }
  return { valid: true, value: normalized };
}

function validateRoomId(roomId) {
  if (!roomId || typeof roomId !== 'string' || roomId.trim().length === 0) {
    return { valid: false, error: 'roomId is required and must be a non-empty string' };
  }
  return { valid: true, value: roomId.trim() };
}

function validateAgentName(name) {
  if (!name || typeof name !== 'string' || name.trim().length === 0) {
    return { valid: false, error: 'Agent name is required and must be a non-empty string' };
  }
  if (name.trim().length > MAX_NAME_LENGTH) {
    return { valid: false, error: `Agent name must be <= ${MAX_NAME_LENGTH} characters` };
  }
  return { valid: true, value: name.trim() };
}

function validateMessageText(text) {
  if (!text || typeof text !== 'string' || text.trim().length === 0) {
    return { valid: false, error: 'Message text is required and must be a non-empty string' };
  }
  if (text.length > MAX_MESSAGE_LENGTH) {
    return { valid: false, error: `Message text must be <= ${MAX_MESSAGE_LENGTH} characters` };
  }
  return { valid: true, value: text.trim() };
}

function validateMessageType(type) {
  if (!type) return { valid: true, value: 'chat' };
  const normalized = type.toLowerCase().trim();
  if (!VALID_MESSAGE_TYPES.includes(normalized)) {
    return { valid: false, error: `Invalid message type. Valid: ${VALID_MESSAGE_TYPES.join(', ')}` };
  }
  return { valid: true, value: normalized };
}

// Root — serve new env dashboard (before static middleware)
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'public', 'index.html'));
});

// Serve dashboard static files
app.use(express.static(path.join(__dirname, '..', 'public', 'dashboard')));
// Serve new env static assets (CSS, JS)
app.use(express.static(path.join(__dirname, '..', 'public')));

// Request logging
app.use((req, res, next) => {
  logger.debug(`${req.method} ${req.url}`);
  next();
});

// ── Health ───────────────────────────────────────────────────────
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    rooms: roomManager.listRooms().length,
    agents: agentRegistry.listAgents().length,
    online: agentSession.getOnlineAgents().length,
  });
});

// ── Agent Heartbeat Endpoint ─────────────────────────────────────
// Keeps agent session alive. Called by agent-client.js every 30s.
app.post('/api/agents/:id/heartbeat', (req, res) => {
  const agent = agentRegistry.getAgent(req.params.id);
  if (!agent) return res.status(404).json({ success: false, error: 'Agent not found', code: 'AGENT_NOT_FOUND' });
  agentRegistry.updateAgent(req.params.id, { lastActive: new Date().toISOString() });
  res.json({ success: true, agent: agentRegistry.getAgent(req.params.id) });
});

// ── Agent Disconnect Endpoint ────────────────────────────────────
// Clean session teardown. Called by agent-client.js on disconnect.
app.post('/api/agents/:id/disconnect', (req, res) => {
  const agent = agentRegistry.getAgent(req.params.id);
  if (!agent) return res.status(404).json({ success: false, error: 'Agent not found', code: 'AGENT_NOT_FOUND' });
  agentRegistry.updateAgent(req.params.id, { status: 'offline' });
  agentSession.endSession(req.params.id);
  worldEngine.setAgentStatus(req.params.id, 'offline');
  res.json({ success: true });
});

// ── Room Endpoints ───────────────────────────────────────────────
app.get('/api/rooms', (req, res) => {
  res.json({ success: true, rooms: roomManager.listRooms() });
});

app.post('/api/rooms', (req, res) => {
  const { name, type, description } = req.body;
  if (!name) return res.status(400).json({ success: false, error: 'Room name required' });
  const result = roomManager.createRoom({ name, description: description || '', persistent: false });
  if (!result.success) return res.status(409).json(result);
  res.status(201).json(result);
});

app.get('/api/rooms/:id', (req, res) => {
  const room = roomManager.getRoom(req.params.id);
  if (!room) return res.status(404).json({ success: false, error: 'Room not found' });
  const messagesResult = messageBus.getMessages(req.params.id, { limit: 20 });
  res.json({ success: true, room, messages: messagesResult.messages });
});

app.post('/api/rooms/:id/join', (req, res) => {
  const { agentId } = req.body;
  if (!agentId) return res.status(400).json({ success: false, error: 'agentId required' });
  const result = roomManager.joinRoom(req.params.id, agentId);
  if (!result.success) return res.status(404).json(result);
  agentRegistry.moveAgent(agentId, req.params.id);
  res.json(result);
});

app.post('/api/rooms/:id/leave', (req, res) => {
  const { agentId } = req.body;
  if (!agentId) return res.status(400).json({ success: false, error: 'agentId required' });
  const result = roomManager.leaveRoom(req.params.id, agentId);
  if (!result.success) return res.status(404).json(result);
  res.json(result);
});

app.get('/api/rooms/:id/messages', (req, res) => {
  const limit = parseInt(req.query.limit) || 50;
  const result = messageBus.getMessages(req.params.id, { limit });
  res.json(result);
});

app.post('/api/rooms/:id/messages', (req, res) => {
  const { agentId, text, type = 'chat' } = req.body;
  if (!agentId || typeof agentId !== 'string') return res.status(400).json({ success: false, error: 'agentId is required', code: 'INVALID_AGENT_ID' });
  const textCheck = validateMessageText(text);
  if (!textCheck.valid) return res.status(400).json({ success: false, error: textCheck.error, code: 'INVALID_TEXT' });
  const typeCheck = validateMessageType(type);
  if (!typeCheck.valid) return res.status(400).json({ success: false, error: typeCheck.error, code: 'INVALID_TYPE' });
  const result = messageBus.postMessage(req.params.id, {
    from: agentId,
    type: typeCheck.value,
    content: textCheck.value,
  });
  if (!result.success) return res.status(400).json({ ...result, code: 'MESSAGE_FAILED' });

  // Broadcast to WebSocket clients in the room
  broadcast.broadcastToRoom(wsRoomSockets, req.params.id, result.message);

  // Record in world engine
  worldEngine.recordMessage(agentId, null, req.params.id, type);

  res.status(201).json(result);
});

// ── Agent Endpoints ──────────────────────────────────────────────
app.get('/api/agents', (req, res) => {
  const filter = {};
  if (req.query.room) filter.room = req.query.room;
  if (req.query.status) filter.status = req.query.status;
  res.json({ success: true, agents: agentRegistry.listAgents(filter) });
});

app.post('/api/agents', (req, res) => {
  const { id, name, role, capabilities, metadata } = req.body;
  const nameCheck = validateAgentName(name);
  if (!nameCheck.valid) return res.status(400).json({ success: false, error: nameCheck.error, code: 'INVALID_NAME' });
  const result = agentRegistry.registerAgent({ name: nameCheck.value, role, capabilities, metadata });
  if (!result.success) return res.status(400).json({ ...result, code: 'REGISTRATION_FAILED' });
  // Register in world engine
  worldEngine.registerAgent(result.agent);
  res.status(201).json(result);
});

app.get('/api/agents/:id', (req, res) => {
  const agent = agentRegistry.getAgent(req.params.id);
  if (!agent) return res.status(404).json({ success: false, error: 'Agent not found' });
  const online = agentSession.isOnline(req.params.id);
  res.json({ success: true, agent: { ...agent, online } });
});

app.post('/api/agents/:id/move', (req, res) => {
  const roomCheck = validateRoomId(req.body.roomId);
  if (!roomCheck.valid) return res.status(400).json({ success: false, error: roomCheck.error, code: 'INVALID_ROOM_ID' });
  const roomId = roomCheck.value;
  const agent = agentRegistry.getAgent(req.params.id);
  if (!agent) return res.status(404).json({ success: false, error: 'Agent not found', code: 'AGENT_NOT_FOUND' });

  // Leave current room
  if (agent.currentRoom) {
    roomManager.leaveRoom(agent.currentRoom, req.params.id);
  }
  // Join new room
  const joinResult = roomManager.joinRoom(roomId, req.params.id);
  if (!joinResult.success) return res.status(404).json(joinResult);
  agentRegistry.moveAgent(req.params.id, roomId);

  // Update WebSocket room tracking
  updateWsAgentRoom(req.params.id, roomId);

  // Update world engine
  worldEngine.moveAgent(req.params.id, roomId);

  res.json({ success: true, agent: agentRegistry.getAgent(req.params.id) });
});

// ── Agent Status Endpoint ────────────────────────────────────────
app.post('/api/agents/:id/status', (req, res) => {
  const statusCheck = validateStatus(req.body.status);
  if (!statusCheck.valid) return res.status(400).json({ success: false, error: statusCheck.error, code: 'INVALID_STATUS' });
  const agent = agentRegistry.getAgent(req.params.id);
  if (!agent) return res.status(404).json({ success: false, error: 'Agent not found', code: 'AGENT_NOT_FOUND' });
  worldEngine.setAgentStatus(req.params.id, statusCheck.value);
  res.json({ success: true, agent: agentRegistry.getAgent(req.params.id) });
});

// ── Agent Activity Endpoint ──────────────────────────────────────
app.post('/api/agents/:id/activity', (req, res) => {
  const agent = agentRegistry.getAgent(req.params.id);
  if (!agent) return res.status(404).json({ success: false, error: 'Agent not found', code: 'AGENT_NOT_FOUND' });
  const action = (req.body.action && typeof req.body.action === 'string') ? req.body.action.trim() : 'Working';
  const level = Math.max(0, Math.min(1, Number(req.body.level) || 0.5));
  if (action.length === 0) return res.status(400).json({ success: false, error: 'Activity action cannot be empty', code: 'INVALID_ACTIVITY' });
  worldEngine.recordActivity(req.params.id, action, level);
  res.json({ success: true });
});

// ── World State Endpoint ─────────────────────────────────────────
app.get('/api/world', (req, res) => {
  worldEngine.updateWorldState();
  res.json({ success: true, ...worldEngine.getWorldState() });
});

// ── Connections Endpoint ─────────────────────────────────────────
app.get('/api/connections', (req, res) => {
  const activityTracker = require('./activity-tracker');
  res.json({ success: true, connections: activityTracker.getConnections() });
});

// ── Sandbox Endpoints ────────────────────────────────────────────
app.post('/api/sandbox/python', async (req, res) => {
  const { code, agentId, timeout } = req.body;
  if (!code) return res.status(400).json({ success: false, error: 'Code required' });
  logger.info('Python sandbox request', { agentId, codeLength: code.length });
  const result = await runPython(code, { timeoutMs: timeout || config.sandbox.pythonTimeoutMs });
  res.json({ success: true, ...result });
});

app.post('/api/sandbox/node', async (req, res) => {
  const { code, agentId, timeout } = req.body;
  if (!code) return res.status(400).json({ success: false, error: 'Code required' });
  logger.info('Node sandbox request', { agentId, codeLength: code.length });
  const result = await runNode(code, { timeoutMs: timeout || config.sandbox.nodeTimeoutMs });
  res.json({ success: true, ...result });
});

// ── File Endpoints ───────────────────────────────────────────────
app.post('/api/files/read', (req, res) => {
  const { path: filePath } = req.body;
  if (!filePath) return res.status(400).json({ success: false, error: 'path required' });
  res.json(readFile(filePath));
});

app.post('/api/files/write', (req, res) => {
  const { path: filePath, content } = req.body;
  if (!filePath) return res.status(400).json({ success: false, error: 'path required' });
  const result = writeFile(filePath, content);
  res.json(result);
});

app.post('/api/files/list', (req, res) => {
  const { path: dirPath = '.' } = req.body;
  res.json(listFiles(dirPath));
});

// ── Quant Room Endpoints ─────────────────────────────────────────
app.get('/api/quant/strategies', (req, res) => {
  res.json({ success: true, strategies: quantRoom.getStrategies() });
});

app.post('/api/quant/strategies', (req, res) => {
  const { name, code, author } = req.body;
  if (!name || !code) return res.status(400).json({ success: false, error: 'name and code required' });
  res.status(201).json(quantRoom.addStrategy({ name, code, author }));
});

app.get('/api/quant/backtests', (req, res) => {
  res.json({ success: true, backtests: quantRoom.getBacktests() });
});

app.post('/api/quant/backtests', (req, res) => {
  const { strategyId, results, status } = req.body;
  res.status(201).json(quantRoom.addBacktest({ strategyId, results, status }));
});

// ── Meditation Room Endpoints ────────────────────────────────────
app.post('/api/meditation/begin', (req, res) => {
  const { agentId, task, idea } = req.body;
  if (!agentId) return res.status(400).json({ success: false, error: 'agentId required' });
  res.status(201).json(meditationRoom.beginMeditation(agentId, { task, idea }));
});

app.post('/api/meditation/iacer', (req, res) => {
  const { agentId, intent, abstraction, context, expectations, results } = req.body;
  if (!agentId) return res.status(400).json({ success: false, error: 'agentId required' });
  res.json(meditationRoom.updateIacer(agentId, { intent, abstraction, context, expectations, results }));
});

app.post('/api/meditation/sketch', (req, res) => {
  const { agentId, sketch } = req.body;
  if (!agentId) return res.status(400).json({ success: false, error: 'agentId required' });
  res.json(meditationRoom.setPrototypeSketch(agentId, sketch));
});

app.post('/api/meditation/complete', (req, res) => {
  const { agentId } = req.body;
  if (!agentId) return res.status(400).json({ success: false, error: 'agentId required' });
  res.json(meditationRoom.completeMeditation(agentId));
});

app.get('/api/meditation/sessions', (req, res) => {
  res.json({ success: true, sessions: meditationRoom.listSessions() });
});

app.get('/api/meditation/sessions/:agentId', (req, res) => {
  const session = meditationRoom.getSession(req.params.agentId);
  if (!session) return res.status(404).json({ success: false, error: 'Session not found' });
  res.json({ success: true, session });
});

// ── Direct Message Endpoint ──────────────────────────────────────
app.post('/api/messages/direct', (req, res) => {
  const { from, to, content, type } = req.body;
  if (!from || !to || !content) return res.status(400).json({ success: false, error: 'from, to, and content required' });
  res.json(directMessage.sendDirectMessage(from, to, { type, content }));
});

// ── Agent Tools Endpoint ─────────────────────────────────────────
app.get('/api/tools', (req, res) => {
  res.json({ success: true, tools: agentTools.listTools() });
});

// ── HTTP Server ──────────────────────────────────────────────────
const server = http.createServer(app);
const PORT = config.port;

// ── WebSocket Server ─────────────────────────────────────────────
const wss = new WebSocketServer({ server, path: '/ws' });

// Track which room each WebSocket client is in: ws -> { agentId, roomId }
const wsClients = new WeakMap();
// Track room sockets: roomId -> Set of { ws, agentId }
const wsRoomSockets = new Map();

function updateWsAgentRoom(agentId, roomId) {
  // Remove from all rooms, add to new
  for (const [rid, sockets] of wsRoomSockets) {
    for (const client of sockets) {
      if (client.agentId === agentId) {
        sockets.delete(client);
        break;
      }
    }
  }
  // Client will need to reconnect or we find their ws
  // For now, broadcast the move event
  broadcastGlobal({ event: 'agent-moved', agentId, roomId });
}

function broadcastGlobal(message) {
  const payload = JSON.stringify({ ...message, timestamp: new Date().toISOString() });
  wss.clients.forEach((client) => {
    if (client.readyState === 1) {
      try { client.send(payload); } catch {}
    }
  });
}

wss.on('connection', (ws, req) => {
  const ip = req.socket.remoteAddress;
  logger.info('WebSocket connected', { ip });

  ws.isAlive = true;
  ws.on('pong', () => { ws.isAlive = true; });

  ws.on('message', (raw) => {
    let msg;
    try { msg = JSON.parse(raw.toString()); } catch {
      ws.send(JSON.stringify({ event: 'error', error: 'Invalid JSON' }));
      return;
    }

    switch (msg.type) {
      case 'auth': {
        // Agent authenticates with their ID
        wsClients.set(ws, { agentId: msg.agentId, roomId: msg.roomId || null });
        if (msg.roomId) {
          if (!wsRoomSockets.has(msg.roomId)) wsRoomSockets.set(msg.roomId, new Set());
          wsRoomSockets.get(msg.roomId).add({ ws, agentId: msg.agentId });
        }
        agentSession.startSession(msg.agentId, ws);
        ws.send(JSON.stringify({ event: 'auth-ok', agentId: msg.agentId }));
        logger.info('WS agent authenticated', { agentId: msg.agentId });
        break;
      }

      case 'join-room': {
        const client = wsClients.get(ws);
        if (!client) { ws.send(JSON.stringify({ event: 'error', error: 'Not authenticated' })); return; }
        const { agentId } = client;

        // Remove from previous room
        if (client.roomId) {
          const prev = wsRoomSockets.get(client.roomId);
          if (prev) { for (const c of prev) { if (c.agentId === agentId) { prev.delete(c); break; } } }
        }

        // Add to new room
        const roomId = msg.roomId;
        if (!wsRoomSockets.has(roomId)) wsRoomSockets.set(roomId, new Set());
        wsRoomSockets.get(roomId).add({ ws, agentId });
        client.roomId = roomId;

        roomManager.joinRoom(roomId, agentId);
        agentRegistry.moveAgent(agentId, roomId);

        ws.send(JSON.stringify({ event: 'room-joined', roomId }));
        logger.info('WS agent joined room', { agentId, roomId });
        break;
      }

      case 'room-message': {
        const client = wsClients.get(ws);
        if (!client || !client.roomId) { ws.send(JSON.stringify({ event: 'error', error: 'Not in a room' })); return; }
        const result = messageBus.postMessage(client.roomId, {
          from: client.agentId,
          type: msg.messageType || 'chat',
          content: msg.content,
        });
        if (result.success) {
          broadcast.broadcastToRoom(wsRoomSockets, client.roomId, result.message);
        }
        break;
      }

      case 'direct-message': {
        const client = wsClients.get(ws);
        if (!client) return;
        const result = directMessage.sendDirectMessage(client.agentId, msg.to, {
          type: msg.messageType || 'dm',
          content: msg.content,
        });
        ws.send(JSON.stringify({ event: 'dm-result', ...result }));
        break;
      }

      case 'meditation-update': {
        const client = wsClients.get(ws);
        if (!client) return;
        const result = meditationRoom.updateIacer(client.agentId, msg.iacer || {});
        ws.send(JSON.stringify({ event: 'meditation-updated', ...result }));
        break;
      }

      case 'request-world': {
        worldEngine.updateWorldState();
        const wsClient = wsClients.get(ws);
        ws.send(JSON.stringify({ event: 'world.state', ...worldEngine.getWorldState() }));
        break;
      }

      case 'move-agent': {
        const client = wsClients.get(ws);
        if (!client) { ws.send(JSON.stringify({ event: 'error', error: 'Not authenticated' })); return; }
        const { agentId, roomId } = msg;
        if (!agentId || !roomId) { ws.send(JSON.stringify({ event: 'error', error: 'agentId and roomId required' })); return; }
        const agent = agentRegistry.getAgent(agentId);
        if (!agent) { ws.send(JSON.stringify({ event: 'error', error: 'Agent not found' })); return; }
        if (agent.currentRoom) roomManager.leaveRoom(agent.currentRoom, agentId);
        const joinResult = roomManager.joinRoom(roomId, agentId);
        if (!joinResult.success) { ws.send(JSON.stringify({ event: 'error', error: joinResult.error })); return; }
        agentRegistry.moveAgent(agentId, roomId);
        updateWsAgentRoom(agentId, roomId);
        worldEngine.moveAgent(agentId, roomId);
        break;
      }

      case 'set-agent-status': {
        const client = wsClients.get(ws);
        if (!client) return;
        const { agentId, status } = msg;
        if (!agentId || !status) return;
        worldEngine.setAgentStatus(agentId, status);
        break;
      }

      case 'simulate-activity': {
        const client = wsClients.get(ws);
        if (!client) return;
        const { agentId } = msg;
        if (!agentId) return;
        const actions = ['Analyzing data', 'Running strategy', 'Reviewing code', 'Writing report', 'Debugging', 'Researching', 'Building prototype'];
        const action = actions[Math.floor(Math.random() * actions.length)];
        worldEngine.recordActivity(agentId, action, 0.5 + Math.random() * 0.5);
        break;
      }

      case 'run-code': {
        const client = wsClients.get(ws);
        if (!client) return;
        const lang = msg.language || 'python';
        const code = msg.code || '';
        if (lang === 'python') {
          runPython(code, { timeoutMs: msg.timeout || config.sandbox.pythonTimeoutMs }).then((result) => {
            ws.send(JSON.stringify({ event: 'code-result', language: 'python', ...result }));
          });
        } else {
          runNode(code, { timeoutMs: msg.timeout || config.sandbox.nodeTimeoutMs }).then((result) => {
            ws.send(JSON.stringify({ event: 'code-result', language: 'node', ...result }));
          });
        }
        break;
      }

      default:
        ws.send(JSON.stringify({ event: 'error', error: `Unknown message type: ${msg.type}` }));
    }
  });

  ws.on('close', () => {
    const client = wsClients.get(ws);
    if (client) {
      agentSession.endSession(client.agentId);
      if (client.roomId) {
        const room = wsRoomSockets.get(client.roomId);
        if (room) { for (const c of room) { if (c.agentId === client.agentId) { room.delete(c); break; } } }
      }
      logger.info('WS agent disconnected', { agentId: client.agentId });
    }
  });

  ws.on('error', (err) => {
    logger.error('WebSocket error', { error: err.message });
  });
});

// Heartbeat — detect dead connections
const heartbeat = setInterval(() => {
  wss.clients.forEach((ws) => {
    if (!ws.isAlive) return ws.terminate();
    ws.isAlive = false;
    ws.ping();
  });
}, 30000);

wss.on('close', () => clearInterval(heartbeat));

// ── World Engine Initialization ─────────────────────────────────
worldEngine.setBroadcastFunction((data) => broadcastGlobal(data));
worldEngine.initialize();

// Start world tick loop
setInterval(() => worldEngine.tick(), 1000 / 30); // 30 FPS

// ── Start ────────────────────────────────────────────────────────
server.listen(PORT, config.host, () => {
  logger.info(`Agent Virtual Environment running on http://${config.host}:${PORT}`);
  logger.info(`WebSocket available at ws://${config.host}:${PORT}/ws`);
  logger.info(`Dashboard: http://${config.host}:${PORT}/`);
  logger.info(`Health: http://${config.host}:${PORT}/health`);
  logger.info(`Default rooms: ${roomManager.listRooms().map(r => r.name).join(', ')}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received — shutting down');
  clearInterval(heartbeat);
  wss.close();
  server.close(() => process.exit(0));
});

process.on('SIGINT', () => {
  logger.info('SIGINT received — shutting down');
  clearInterval(heartbeat);
  wss.close();
  server.close(() => process.exit(0));
});
