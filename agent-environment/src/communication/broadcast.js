/**
 * Broadcast — Room-wide message broadcasting via WebSocket.
 */

const logger = require('../utils/logger');

/**
 * Broadcast a message to all WebSocket clients in a room.
 * @param {Map<string, Set<ws>>} roomSockets - Map of roomId -> Set of WebSocket connections
 * @param {string} roomId - Target room
 * @param {object} message - Message to broadcast
 * @param {string|null} excludeAgentId - Optional agent ID to exclude
 */
function broadcastToRoom(roomSockets, roomId, message, excludeAgentId = null) {
  const sockets = roomSockets.get(roomId);
  if (!sockets) return 0;

  const payload = JSON.stringify({
    event: 'room-message',
    roomId,
    data: message,
    timestamp: new Date().toISOString(),
  });

  let sent = 0;
  sockets.forEach((client) => {
    if (client.agentId === excludeAgentId) return;
    if (client.ws && client.ws.readyState === 1) {
      try {
        client.ws.send(payload);
        sent++;
      } catch (err) {
        logger.warn('Broadcast send failed', { error: err.message });
      }
    }
  });

  logger.debug('Broadcast complete', { roomId, sent, total: sockets.size });
  return sent;
}

/**
 * Broadcast to ALL connected clients regardless of room.
 */
function broadcastGlobal(roomSockets, message) {
  const payload = JSON.stringify({
    event: 'global-broadcast',
    data: message,
    timestamp: new Date().toISOString(),
  });

  let sent = 0;
  roomSockets.forEach((sockets) => {
    sockets.forEach((client) => {
      if (client.ws && client.ws.readyState === 1) {
        try {
          client.ws.send(payload);
          sent++;
        } catch {}
      }
    });
  });

  return sent;
}

module.exports = { broadcastToRoom, broadcastGlobal };
