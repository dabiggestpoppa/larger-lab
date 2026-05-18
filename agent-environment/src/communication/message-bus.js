/**
 * Message Bus — Inter-agent messaging system.
 * Handles room messages, direct messages, and broadcasts.
 * Persists room messages to data/room-messages.json.
 */

const fs = require('fs');
const path = require('path');
const config = require('../utils/config');
const logger = require('../utils/logger');

const MESSAGES_FILE = path.join(config.dataDir, 'room-messages.json');

// In-memory message store: roomId -> [messages]
let roomMessages = new Map();

// Load persisted messages
function loadMessages() {
  try {
    if (fs.existsSync(MESSAGES_FILE)) {
      const data = JSON.parse(fs.readFileSync(MESSAGES_FILE, 'utf8'));
      roomMessages = new Map(Object.entries(data));
      logger.info('Room messages loaded from disk');
    }
  } catch (err) {
    logger.error('Failed to load room messages', { error: err.message });
  }
}

// Persist messages
function saveMessages() {
  try {
    fs.mkdirSync(config.dataDir, { recursive: true });
    const data = Object.fromEntries(roomMessages);
    fs.writeFileSync(MESSAGES_FILE, JSON.stringify(data, null, 2), 'utf8');
  } catch (err) {
    logger.error('Failed to save room messages', { error: err.message });
  }
}

/**
 * Post a message to a room.
 */
function postMessage(roomId, { from, type = 'chat', content, metadata = {} }) {
  if (!content || typeof content !== 'string') {
    return { success: false, error: 'Message content required' };
  }
  if (content.length > config.maxMessageLength) {
    content = content.slice(0, config.maxMessageLength) + '…[TRUNCATED]';
  }

  const message = {
    id: `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    from,
    type, // chat, task, result, question, ping, broadcast, iacer
    content,
    metadata,
    timestamp: new Date().toISOString(),
  };

  if (!roomMessages.has(roomId)) {
    roomMessages.set(roomId, []);
  }
  const messages = roomMessages.get(roomId);
  messages.push(message);

  // Enforce max history
  if (messages.length > config.maxHistoryPerRoom) {
    roomMessages.set(roomId, messages.slice(-config.maxHistoryPerRoom));
  }

  saveMessages();
  logger.debug('Message posted', { roomId, from, type });
  return { success: true, message };
}

/**
 * Get messages for a room.
 */
function getMessages(roomId, { limit = 50, before } = {}) {
  const messages = roomMessages.get(roomId) || [];
  let result = messages;
  if (before) {
    const idx = result.findIndex(m => m.id === before);
    if (idx >= 0) result = result.slice(0, idx);
  }
  if (limit) result = result.slice(-limit);
  return { success: true, messages: result, total: messages.length };
}

/**
 * Get all room IDs that have messages.
 */
function getActiveRooms() {
  return Array.from(roomMessages.keys());
}

// Load on init
loadMessages();

module.exports = {
  postMessage,
  getMessages,
  getActiveRooms,
  saveMessages,
};
