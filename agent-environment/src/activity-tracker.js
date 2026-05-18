/**
 * Activity Tracker — Tracks agent activity, manages communication connections,
 * and broadcasts state changes to connected WebSocket clients.
 */

const logger = require('./utils/logger');
const agentVisual = require('./agent-visual');

// Active connections: { fromAgentId -> { toAgentId, type, lastMessage, active } }
const connections = new Map();

// Recent activity log (for dashboard)
const activityLog = [];
const MAX_LOG = 100;

// WebSocket broadcast function (set by server.js)
let broadcastFn = null;
let broadcastToAllFn = null;

/**
 * Set the broadcast functions (called from server.js).
 */
function setBroadcastFunctions({ broadcast, broadcastAll }) {
  broadcastFn = broadcast;
  broadcastToAllFn = broadcastAll;
}

/**
 * Record agent activity.
 */
function recordActivity(agentId, action, level = 0.5) {
  agentVisual.updateAgentActivity(agentId, { level, lastAction: action });

  const entry = {
    agentId,
    action,
    level,
    timestamp: new Date().toISOString(),
  };
  activityLog.push(entry);
  if (activityLog.length > MAX_LOG) activityLog.shift();

  // Broadcast to all clients
  if (broadcastToAllFn) {
    broadcastToAllFn({
      event: 'agent.activity',
      agentId,
      level,
      lastAction: action,
      timestamp: entry.timestamp,
    });
  }

  logger.debug('Activity recorded', { agentId, action, level });
  return entry;
}

/**
 * Record a message between agents (creates/updates a connection).
 */
function recordMessage(fromId, toId, roomId, type = 'chat') {
  const connectionKey = `${fromId}->${toId}`;
  const isDirect = !roomId; // Direct messages have no room

  connections.set(connectionKey, {
    from: fromId,
    to: toId,
    type,
    roomId,
    lastMessage: new Date().toISOString(),
    active: true,
    messageCount: (connections.get(connectionKey)?.messageCount || 0) + 1,
  });

  // Also record activity for both agents
  recordActivity(fromId, `Sent ${type} message`, 0.6);
  if (toId) {
    recordActivity(toId, `Received ${type} message`, 0.3);
  }

  // Broadcast connection event
  if (broadcastToAllFn) {
    broadcastToAllFn({
      event: 'message.sent',
      from: fromId,
      to: toId,
      roomId,
      type,
      timestamp: new Date().toISOString(),
    });
    broadcastToAllFn({
      event: 'connection.active',
      from: fromId,
      to: toId,
      type,
    });
  }

  return { connectionKey, from: fromId, to: toId, type };
}

/**
 * Get all active connections.
 */
function getConnections() {
  return Array.from(connections.values());
}

/**
 * Get recent activity log.
 */
function getActivityLog(limit = 20) {
  return activityLog.slice(-limit);
}

/**
 * Idle out old connections (no messages in last 30 seconds).
 */
function idleOldConnections() {
  const now = Date.now();
  const IDLE_TIMEOUT = 30000; // 30 seconds
  for (const [key, conn] of connections) {
    const lastMsg = new Date(conn.lastMessage).getTime();
    if (now - lastMsg > IDLE_TIMEOUT && conn.active) {
      conn.active = false;
      if (broadcastToAllFn) {
        broadcastToAllFn({
          event: 'connection.idle',
          from: conn.from,
          to: conn.to,
        });
      }
    }
  }
}

/**
 * Tick — called each frame to update activity decay.
 */
function tick(deltaTime) {
  agentVisual.tickActivityDecay(deltaTime);
  idleOldConnections();
}

/**
 * Get full activity state for world sync.
 */
function getActivityState() {
  return {
    connections: getConnections(),
    recentActivity: getActivityLog(10),
    timestamp: new Date().toISOString(),
  };
}

module.exports = {
  setBroadcastFunctions,
  recordActivity,
  recordMessage,
  getConnections,
  getActivityLog,
  idleOldConnections,
  tick,
  getActivityState,
};
