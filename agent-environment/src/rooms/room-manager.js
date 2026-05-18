/**
 * Room Manager — Creates, manages, and tracks rooms and agent membership.
 * Persists to data/rooms.json.
 */

const fs = require('fs');
const path = require('path');
const config = require('../utils/config');
const logger = require('../utils/logger');

const ROOMS_FILE = path.join(config.dataDir, 'rooms.json');

// In-memory: roomId -> { id, name, description, agents: Set, createdAt, ... }
let rooms = new Map();

// Load persisted rooms
function loadRooms() {
  try {
    if (fs.existsSync(ROOMS_FILE)) {
      const data = JSON.parse(fs.readFileSync(ROOMS_FILE, 'utf8'));
      for (const [id, room] of Object.entries(data)) {
        room.agents = new Set(room.agents || []);
        rooms.set(id, room);
      }
      logger.info(`Loaded ${rooms.size} rooms from disk`);
    }
  } catch (err) {
    logger.error('Failed to load rooms', { error: err.message });
  }

  // Ensure default rooms exist
  for (const defaultRoom of config.defaultRooms) {
    if (!rooms.has(defaultRoom.id)) {
      rooms.set(defaultRoom.id, {
        id: defaultRoom.id,
        name: defaultRoom.name,
        description: defaultRoom.description,
        agents: new Set(),
        persistent: defaultRoom.persistent,
        createdAt: new Date().toISOString(),
      });
    }
  }
  saveRooms();
}

// Persist rooms
function saveRooms() {
  try {
    fs.mkdirSync(config.dataDir, { recursive: true });
    const data = {};
    for (const [id, room] of rooms) {
      data[id] = { ...room, agents: Array.from(room.agents) };
    }
    fs.writeFileSync(ROOMS_FILE, JSON.stringify(data, null, 2), 'utf8');
  } catch (err) {
    logger.error('Failed to save rooms', { error: err.message });
  }
}

/**
 * Create a new room.
 */
function createRoom({ name, description = '', persistent = false }) {
  const id = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-_]/g, '');
  if (rooms.has(id)) return { success: false, error: 'Room already exists' };

  const room = {
    id,
    name,
    description,
    agents: new Set(),
    persistent,
    createdAt: new Date().toISOString(),
  };
  rooms.set(id, room);
  saveRooms();
  logger.info('Room created', { id, name });
  return { success: true, room: { ...room, agents: [] } };
}

/**
 * Get room by ID.
 */
function getRoom(id) {
  const room = rooms.get(id);
  if (!room) return null;
  return { ...room, agents: Array.from(room.agents) };
}

/**
 * List all rooms.
 */
function listRooms() {
  return Array.from(rooms.values()).map(r => ({
    ...r,
    agents: Array.from(r.agents),
    agentCount: r.agents.size,
  }));
}

/**
 * Agent joins a room.
 */
function joinRoom(roomId, agentId) {
  const room = rooms.get(roomId);
  if (!room) return { success: false, error: 'Room not found' };
  room.agents.add(agentId);
  saveRooms();
  logger.info('Agent joined room', { agentId, roomId });
  return { success: true, room: { ...room, agents: Array.from(room.agents) } };
}

/**
 * Agent leaves a room.
 */
function leaveRoom(roomId, agentId) {
  const room = rooms.get(roomId);
  if (!room) return { success: false, error: 'Room not found' };
  room.agents.delete(agentId);
  saveRooms();
  logger.info('Agent left room', { agentId, roomId });
  return { success: true };
}

/**
 * Get agents in a room.
 */
function getRoomAgents(roomId) {
  const room = rooms.get(roomId);
  if (!room) return [];
  return Array.from(room.agents);
}

/**
 * Delete a room (only non-persistent).
 */
function deleteRoom(roomId) {
  const room = rooms.get(roomId);
  if (!room) return { success: false, error: 'Room not found' };
  if (room.persistent) return { success: false, error: 'Cannot delete persistent room' };
  rooms.delete(roomId);
  saveRooms();
  return { success: true };
}

// Load on init
loadRooms();

module.exports = {
  createRoom,
  getRoom,
  listRooms,
  joinRoom,
  leaveRoom,
  getRoomAgents,
  deleteRoom,
  saveRooms,
};
