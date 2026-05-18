/**
 * Room Visual — Manages room layout, positioning, and visual properties.
 * Each room has a position, size, color theme, and agent slot positions.
 */

const logger = require('./utils/logger');

// Room visual configurations
const ROOM_VISUALS = {
  'meditation-room': {
    icon: '🧘',
    color: '#6c5ce7',
    bgColor: 'rgba(108, 92, 231, 0.08)',
    borderColor: 'rgba(108, 92, 231, 0.3)',
  },
  'quant-room': {
    icon: '📊',
    color: '#00b894',
    bgColor: 'rgba(0, 184, 148, 0.08)',
    borderColor: 'rgba(0, 184, 148, 0.3)',
  },
  'chat-room': {
    icon: '💬',
    color: '#00cec9',
    bgColor: 'rgba(0, 206, 201, 0.08)',
    borderColor: 'rgba(0, 206, 201, 0.3)',
  },
  'war-room': {
    icon: '⚔️',
    color: '#e17055',
    bgColor: 'rgba(225, 112, 85, 0.08)',
    borderColor: 'rgba(225, 112, 85, 0.3)',
  },
};

// Default visual for unknown rooms
const DEFAULT_VISUAL = {
  icon: '🏠',
  color: '#636e72',
  bgColor: 'rgba(99, 110, 114, 0.08)',
  borderColor: 'rgba(99, 110, 114, 0.3)',
};

// Room layout positions (computed or preset)
const roomPositions = new Map();

// Room dimensions
const ROOM_WIDTH = 220;
const ROOM_HEIGHT = 160;
const ROOM_MARGIN = 30;
const ROOM_PADDING = 12;

/**
 * Compute room positions in a grid layout.
 * @param {Array} rooms - List of room objects from roomManager
 */
function computeRoomLayout(rooms) {
  const cols = Math.min(rooms.length, 2);
  const rows = Math.ceil(rooms.length / cols);

  // Start position (offset for sidebar)
  const startX = 20;
  const startY = 20;

  rooms.forEach((room, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const x = startX + col * (ROOM_WIDTH + ROOM_MARGIN);
    const y = startY + row * (ROOM_HEIGHT + ROOM_MARGIN);

    const visual = ROOM_VISUALS[room.id] || DEFAULT_VISUAL;

    roomPositions.set(room.id, {
      id: room.id,
      name: room.name,
      description: room.description || '',
      ...visual,
      position: { x, y },
      size: { w: ROOM_WIDTH, h: ROOM_HEIGHT },
    });
  });

  logger.debug('Room layout computed', { rooms: rooms.length, cols, rows });
  return Array.from(roomPositions.values());
}

/**
 * Get the visual config for a room.
 */
function getRoomVisual(roomId) {
  return roomPositions.get(roomId) || null;
}

/**
 * Get all room visuals.
 */
function getAllRoomVisuals() {
  return Array.from(roomPositions.values());
}

/**
 * Compute agent positions within a room.
 * Agents are arranged in a grid inside the room.
 * @param {string} roomId
 * @param {number} agentCount
 * @returns {Array} Array of { x, y } positions
 */
function computeAgentPositions(roomId, agentCount) {
  const room = roomPositions.get(roomId);
  if (!room) return [];

  const positions = [];
  const cols = Math.min(agentCount, 3);
  const rows = Math.ceil(agentCount / cols);

  const cellW = (room.size.w - ROOM_PADDING * 2) / Math.max(cols, 1);
  const cellH = (room.size.h - ROOM_PADDING * 2 - 30) / Math.max(rows, 1); // 30px for header

  for (let i = 0; i < agentCount; i++) {
    const col = i % cols;
    const row = Math.floor(i / cols);
    positions.push({
      x: room.position.x + ROOM_PADDING + col * cellW + cellW / 2,
      y: room.position.y + 30 + ROOM_PADDING + row * cellH + cellH / 2, // 30px header
    });
  }

  return positions;
}

/**
 * Get room dimensions.
 */
function getRoomDimensions() {
  return { width: ROOM_WIDTH, height: ROOM_HEIGHT, margin: ROOM_MARGIN };
}

/**
 * Get the canvas size needed for the current layout.
 */
function getCanvasSize() {
  let maxX = 0;
  let maxY = 0;
  for (const room of roomPositions.values()) {
    maxX = Math.max(maxX, room.position.x + room.size.w);
    maxY = Math.max(maxY, room.position.y + room.size.h);
  }
  return { width: maxX + ROOM_MARGIN, height: maxY + ROOM_MARGIN };
}

module.exports = {
  computeRoomLayout,
  getRoomVisual,
  getAllRoomVisuals,
  computeAgentPositions,
  getRoomDimensions,
  getCanvasSize,
  ROOM_WIDTH,
  ROOM_HEIGHT,
  ROOM_MARGIN,
};
