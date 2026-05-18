/**
 * Agent Client SDK — Node.js client for the Agent Virtual Environment server.
 *
 * Provides a simple API for sub-agents to:
 *   - Register themselves with the environment
 *   - Move between rooms
 *   - Send messages to room chat
 *   - Update their status and activity
 *   - Disconnect cleanly
 *
 * Uses only built-in Node.js modules (no external dependencies).
 *
 * @example
 *   const client = require('./src/agent-client');
 *   const agent = await client.connect({ name: 'Manager', role: 'coordinator' });
 *   await client.moveTo('lab-room');
 *   await client.say('Starting backtest...');
 *   await client.setStatus('working');
 *   await client.disconnect();
 */

const http = require('http');
const { EventEmitter } = require('events');

const DEFAULT_HOST = 'localhost';
const DEFAULT_PORT = 9000;
const HEARTBEAT_INTERVAL_MS = 30_000; // 30 seconds
const REQUEST_TIMEOUT_MS = 10_000;    // 10 seconds

// Valid status values (must match server expectations)
const VALID_STATUSES = ['idle', 'working', 'meditating', 'active', 'error', 'offline'];

// ── Internal State ───────────────────────────────────────────────
let _agentId = null;
let _agentName = null;
let _agentRole = null;
let _currentRoom = null;
let _status = 'idle';
let _host = DEFAULT_HOST;
let _port = DEFAULT_PORT;
let _heartbeatTimer = null;
let _emitter = new EventEmitter();
let _connected = false;
let _offlineQueue = []; // Operations queued when server is unreachable

// ── HTTP Helper ──────────────────────────────────────────────────

/**
 * Make an HTTP request to the environment server.
 * @param {string} method - HTTP method (GET, POST, etc.)
 * @param {string} path - API path (e.g., '/api/agents')
 * @param {object|null} body - Request body (will be JSON-stringified)
 * @returns {Promise<object>} Parsed JSON response
 * @throws {Error} On network failure or non-2xx status
 */
function _request(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const options = {
      hostname: _host,
      port: _port,
      path,
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(data ? { 'Content-Length': Buffer.byteLength(data) } : {}),
      },
      timeout: REQUEST_TIMEOUT_MS,
    };

    const req = http.request(options, (res) => {
      let chunks = '';
      res.on('data', (d) => { chunks += d; });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(chunks);
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(parsed);
          } else {
            const err = new Error(parsed.error || `HTTP ${res.statusCode}`);
            err.code = parsed.code || 'HTTP_ERROR';
            err.statusCode = res.statusCode;
            reject(err);
          }
        } catch {
          resolve({ raw: chunks, statusCode: res.statusCode });
        }
      });
    });

    req.on('timeout', () => {
      req.destroy();
      const err = new Error('Request timeout');
      err.code = 'TIMEOUT';
      reject(err);
    });

    req.on('error', (err) => {
      err.code = err.code || 'NETWORK_ERROR';
      reject(err);
    });

    if (data) req.write(data);
    req.end();
  });
}

// ── Offline Queue ────────────────────────────────────────────────

/**
 * Try to execute an operation. If server is unreachable, queue it.
 * @param {string} label - Operation label for logging
 * @param {Function} fn - Async function to execute
 * @returns {Promise<any>}
 */
function _tryOrQueue(label, fn) {
  return fn().catch((err) => {
    if (err.code === 'ECONNREFUSED' || err.code === 'TIMEOUT' || err.code === 'NETWORK_ERROR') {
      _offlineQueue.push({ label, fn });
      _emitter.emit('queued', { label, error: err.message });
      return { queued: true, error: err.message };
    }
    throw err;
  });
}

/**
 * Flush the offline queue. Called when connection is restored.
 */
async function _flushQueue() {
  if (_offlineQueue.length === 0) return;
  const queued = [..._offlineQueue];
  _offlineQueue = [];
  for (const item of queued) {
    try {
      await item.fn();
      _emitter.emit('dequeued', { label: item.label });
    } catch {
      _offlineQueue.push(item); // Re-queue if still failing
    }
  }
}

// ── Heartbeat ────────────────────────────────────────────────────

/**
 * Start the heartbeat interval. Pings server every 30s.
 */
function _startHeartbeat() {
  _stopHeartbeat();
  _heartbeatTimer = setInterval(async () => {
    try {
      // Use the heartbeat endpoint if available, otherwise use status update
      await _request('POST', `/api/agents/${_agentId}/heartbeat`);
      _emitter.emit('heartbeat', { ok: true });
    } catch {
      // Heartbeat failed — server may be down, queue will retry later
      _emitter.emit('heartbeat', { ok: false });
    }
  }, HEARTBEAT_INTERVAL_MS);
}

/**
 * Stop the heartbeat interval.
 */
function _stopHeartbeat() {
  if (_heartbeatTimer) {
    clearInterval(_heartbeatTimer);
    _heartbeatTimer = null;
  }
}

// ── Public API ───────────────────────────────────────────────────

/**
 * Connect to the environment server and register as a new agent.
 *
 * @param {object} opts
 * @param {string} opts.name - Agent display name (e.g., 'Manager')
 * @param {string} [opts.role='agent'] - Agent role (e.g., 'coordinator', 'researcher')
 * @param {string[]} [opts.capabilities=['communicate']] - Agent capabilities
 * @param {string} [opts.room] - Initial room to join (defaults to 'lobby')
 * @param {string} [opts.host='localhost'] - Server hostname
 * @param {number} [opts.port=9000] - Server port
 * @returns {Promise<object>} The registered agent object
 *
 * @example
 *   const agent = await client.connect({ name: 'Manager', role: 'coordinator' });
 *   console.log(`Registered as ${agent.name} (${agent.id})`);
 */
async function connect({
  name,
  role = 'agent',
  capabilities = ['communicate'],
  room = 'lobby',
  host = DEFAULT_HOST,
  port = DEFAULT_PORT,
} = {}) {
  if (_connected) {
    throw new Error('Already connected. Call disconnect() first.');
  }

  if (!name || typeof name !== 'string' || name.trim().length === 0) {
    throw new Error('Agent name is required and must be a non-empty string.');
  }

  _host = host;
  _port = port;

  // Verify server is reachable
  try {
    await _request('GET', '/health');
  } catch (err) {
    throw new Error(`Cannot connect to environment server at ${host}:${port} — ${err.message}`);
  }

  // Register agent
  const result = await _request('POST', '/api/agents', {
    name: name.trim(),
    role,
    capabilities,
  });

  if (!result.success) {
    throw new Error(`Registration failed: ${result.error}`);
  }

  _agentId = result.agent.id;
  _agentName = result.agent.name;
  _agentRole = result.agent.role;
  _currentRoom = result.agent.currentRoom || 'meditation-room';
  _status = result.agent.status || 'idle';
  _connected = true;

  // Move to requested room if different from default
  if (room && room !== _currentRoom) {
    await moveTo(room);
  }

  // Start heartbeat
  _startHeartbeat();

  _emitter.emit('connected', { agent: result.agent });
  return result.agent;
}

/**
 * Move the agent to a different room.
 * Triggers a WebSocket event so the Canvas dashboard updates in real-time.
 *
 * @param {string} roomId - Target room ID (e.g., 'lab-room', 'meditation-room')
 * @returns {Promise<object>} Updated agent object
 *
 * @example
 *   await client.moveTo('lab-room');
 */
async function moveTo(roomId) {
  if (!_connected) throw new Error('Not connected. Call connect() first.');
  if (!roomId || typeof roomId !== 'string') {
    throw new Error('roomId is required and must be a non-empty string.');
  }

  const doMove = () => _request('POST', `/api/agents/${_agentId}/move`, { roomId });

  const result = await _tryOrQueue('moveTo', doMove);
  if (result.queued) return { queued: true, roomId };

  if (result.success) {
    const previousRoom = _currentRoom;
    _currentRoom = roomId;
    _emitter.emit('moved', { from: previousRoom, to: roomId });
    return result.agent;
  }

  const err = new Error(result.error || 'Move failed');
  err.code = 'MOVE_FAILED';
  _emitter.emit('error', err);
  throw err;
}

/**
 * Send a message to the agent's current room.
 *
 * @param {string} text - Message text
 * @param {string} [type='chat'] - Message type ('chat', 'system', 'task')
 * @returns {Promise<object>} The posted message
 *
 * @example
 *   await client.say('Starting backtest on EUR/USD M5...');
 *   await client.say('Backtest complete: +8746 pips', 'task');
 */
async function say(text, type = 'chat') {
  if (!_connected) throw new Error('Not connected. Call connect() first.');
  if (!text || typeof text !== 'string' || text.trim().length === 0) {
    throw new Error('Message text is required and must be a non-empty string.');
  }
  if (!_currentRoom) {
    throw new Error('Not in any room. Call moveTo() first.');
  }

  const doSay = () => _request('POST', `/api/rooms/${_currentRoom}/messages`, {
    agentId: _agentId,
    text: text.trim(),
    type,
  });

  const result = await _tryOrQueue('say', doSay);
  if (result.queued) return { queued: true, text };

  if (result.success) {
    _emitter.emit('message-sent', { room: _currentRoom, text, type });
    return result;
  }

  const err = new Error(result.error || 'Send failed');
  err.code = 'SEND_FAILED';
  _emitter.emit('error', err);
  throw err;
}

/**
 * Update the agent's status. Visible on the Canvas dashboard.
 *
 * @param {string} status - One of: 'idle', 'working', 'meditating', 'active', 'error'
 * @returns {Promise<object>} Updated agent object
 *
 * @example
 *   await client.setStatus('working');
 *   // ... do work ...
 *   await client.setStatus('idle');
 */
async function setStatus(status) {
  if (!_connected) throw new Error('Not connected. Call connect() first.');
  if (!status || typeof status !== 'string') {
    throw new Error(`Status is required. Valid: ${VALID_STATUSES.join(', ')}`);
  }
  const normalized = status.toLowerCase().trim();
  if (!VALID_STATUSES.includes(normalized)) {
    throw new Error(`Invalid status "${status}". Valid: ${VALID_STATUSES.join(', ')}`);
  }

  const doUpdate = () => _request('POST', `/api/agents/${_agentId}/status`, { status: normalized });

  const result = await _tryOrQueue('setStatus', doUpdate);
  if (result.queued) return { queued: true, status: normalized };

  if (result.success) {
    _status = normalized;
    _emitter.emit('status-changed', { status: normalized });
    return result.agent;
  }

  const err = new Error(result.error || 'Status update failed');
  err.code = 'STATUS_FAILED';
  _emitter.emit('error', err);
  throw err;
}

/**
 * Update the agent's current activity. Shown in the activity log on the dashboard.
 *
 * @param {string} action - Description of current activity (e.g., 'Running backtest...')
 * @param {number} [level=0.5] - Activity intensity 0.0-1.0
 * @returns {Promise<object>}
 *
 * @example
 *   await client.setActivity('Running optimizer v4 backtest...', 0.8);
 */
async function setActivity(action, level = 0.5) {
  if (!_connected) throw new Error('Not connected. Call connect() first.');
  if (!action || typeof action !== 'string' || action.trim().length === 0) {
    throw new Error('Activity action is required and must be a non-empty string.');
  }
  const normalizedLevel = Math.max(0, Math.min(1, Number(level) || 0.5));

  const doUpdate = () => _request('POST', `/api/agents/${_agentId}/activity`, {
    action: action.trim(),
    level: normalizedLevel,
  });

  const result = await _tryOrQueue('setActivity', doUpdate);
  if (result.queued) return { queued: true, action };

  if (result.success) {
    _emitter.emit('activity-updated', { action, level: normalizedLevel });
    return result;
  }

  const err = new Error(result.error || 'Activity update failed');
  err.code = 'ACTIVITY_FAILED';
  _emitter.emit('error', err);
  throw err;
}

/**
 * Get the current world state from the server.
 * Useful for discovering other agents and rooms.
 *
 * @returns {Promise<object>} Full world state (rooms, agents, connections, activity)
 *
 * @example
 *   const world = await client.getWorld();
 *   console.log(`${world.agents.length} agents online`);
 */
async function getWorld() {
  if (!_connected) throw new Error('Not connected. Call connect() first.');
  return _request('GET', '/api/world');
}

/**
 * Get the agent's own current state.
 *
 * @returns {object} Local agent state (id, name, room, status, role)
 */
function whoami() {
  return {
    id: _agentId,
    name: _agentName,
    role: _agentRole,
    room: _currentRoom,
    status: _status,
    connected: _connected,
  };
}

/**
 * Disconnect from the environment server.
 * Stops heartbeat, cleans up resources. The agent remains in the registry
 * but is marked as offline.
 *
 * @returns {Promise<void>}
 *
 * @example
 *   await client.disconnect();
 */
async function disconnect() {
  if (!_connected) return;

  _stopHeartbeat();

  // Try to update status to offline
  try {
    await _request('POST', `/api/agents/${_agentId}/status`, { status: 'offline' });
  } catch {
    // Best effort — server may be down
  }

  _emitter.emit('disconnected', { agentId: _agentId });

  _agentId = null;
  _agentName = null;
  _agentRole = null;
  _currentRoom = null;
  _status = 'offline';
  _connected = false;
  _offlineQueue = [];
}

/**
 * Register an event listener.
 *
 * Events:
 *   'connected'     - Agent registered successfully
 *   'moved'         - Agent moved to a new room { from, to }
 *   'message-sent'  - Message posted to room { room, text, type }
 *   'status-changed'- Status updated { status }
 *   'activity-updated' - Activity updated { action, level }
 *   'heartbeat'     - Heartbeat ping { ok: boolean }
 *   'queued'        - Operation queued (server unreachable) { label, error }
 *   'dequeued'      - Queued operation flushed { label }
 *   'error'         - An error occurred { message, code }
 *   'disconnected'  - Agent disconnected { agentId }
 *
 * @param {string} event - Event name
 * @param {Function} fn - Callback function
 */
function on(event, fn) {
  _emitter.on(event, fn);
}

/**
 * Remove an event listener.
 *
 * @param {string} event - Event name
 * @param {Function} fn - Callback function to remove
 */
function off(event, fn) {
  _emitter.off(event, fn);
}

// ── Module Exports ───────────────────────────────────────────────

module.exports = {
  connect,
  moveTo,
  say,
  setStatus,
  setActivity,
  getWorld,
  whoami,
  disconnect,
  on,
  off,

  // Expose for testing
  _request,
  _tryOrQueue,
  _flushQueue,
  _startHeartbeat,
  _stopHeartbeat,
  VALID_STATUSES,
};
