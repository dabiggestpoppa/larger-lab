/**
 * Agent Session — Manages agent runtime sessions (WebSocket connections, activity).
 */

const logger = require('../utils/logger');

// Map of agentId -> { ws, connectedAt, lastPing }
const sessions = new Map();

/**
 * Start a session for an agent.
 */
function startSession(agentId, ws) {
  sessions.set(agentId, {
    ws,
    connectedAt: new Date().toISOString(),
    lastPing: Date.now(),
  });
  logger.info('Session started', { agentId });
}

/**
 * End a session.
 */
function endSession(agentId) {
  sessions.delete(agentId);
  logger.info('Session ended', { agentId });
}

/**
 * Get session info.
 */
function getSession(agentId) {
  return sessions.get(agentId) || null;
}

/**
 * Check if agent is online.
 */
function isOnline(agentId) {
  return sessions.has(agentId);
}

/**
 * Get all online agent IDs.
 */
function getOnlineAgents() {
  return Array.from(sessions.keys());
}

/**
 * Send a message to a specific agent via WebSocket.
 */
function sendToAgent(agentId, message) {
  const session = sessions.get(agentId);
  if (!session || !session.ws || session.ws.readyState !== 1) return false;
  try {
    session.ws.send(JSON.stringify(message));
    return true;
  } catch {
    return false;
  }
}

/**
 * Get session stats.
 */
function getStats() {
  return {
    totalSessions: sessions.size,
    onlineAgents: Array.from(sessions.keys()),
  };
}

module.exports = {
  startSession,
  endSession,
  getSession,
  isOnline,
  getOnlineAgents,
  sendToAgent,
  getStats,
};
