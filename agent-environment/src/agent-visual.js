/**
 * Agent Visual — Manages agent visual state: position, color, activity, avatar rendering data.
 * Each agent gets a unique color, position within a room, and activity visualization.
 */

const logger = require('./utils/logger');

// Color palette for agents
const COLOR_PALETTE = [
  '#6c5ce7', // purple
  '#e17055', // red
  '#00cec9', // teal
  '#fd79a8', // pink
  '#74b9ff', // blue
  '#ffeaa7', // yellow
  '#55efc4', // green
  '#a29bfe', // light purple
  '#fab1a0', // peach
  '#81ecec', // cyan
];

// Agent visual states: agentId -> visual state
const visualStates = new Map();

// Agent color assignments: agentId -> color
const colorAssignments = new Map();
let colorIndex = 0;

/**
 * Assign a unique color to an agent.
 */
function assignColor(agentId) {
  if (colorAssignments.has(agentId)) return colorAssignments.get(agentId);
  const color = COLOR_PALETTE[colorIndex % COLOR_PALETTE.length];
  colorIndex++;
  colorAssignments.set(agentId, color);
  return color;
}

/**
 * Initialize visual state for an agent.
 */
function initAgentVisual(agent) {
  const color = assignColor(agent.id);
  const state = {
    id: agent.id,
    name: agent.name,
    role: agent.role || 'general',
    color,
    currentRoom: agent.currentRoom || 'meditation-room',
    status: agent.status || 'idle',
    online: false,
    position: { x: 0, y: 0 }, // Computed by room-visual
    targetPosition: { x: 0, y: 0 },
    activity: {
      level: 0,        // 0-1 activity intensity
      lastAction: '',
      lastActionTime: null,
      pulsePhase: 0,   // For animation
    },
    // Visual metadata
    avatar: {
      radius: 18,
      label: agent.name.length > 8 ? agent.name.slice(0, 8) + '…' : agent.name,
      emoji: getRoleEmoji(agent.role),
    },
  };
  visualStates.set(agent.id, state);
  logger.debug('Agent visual initialized', { agentId: agent.id, color });
  return state;
}

/**
 * Get an emoji for a role.
 */
function getRoleEmoji(role) {
  const emojis = {
    operator: '🦉',
    overseer: '🔵',
    assistant: '🟡',
    debugger: '🔴',
    researcher: '🟢',
    general: '🤖',
    architect: '🏗️',
    developer: '💻',
    analyst: '📊',
    writer: '✍️',
  };
  return emojis[role] || '🤖';
}

/**
 * Update agent's room and set new target position.
 */
function updateAgentRoom(agentId, roomId) {
  const state = visualStates.get(agentId);
  if (!state) return null;
  const oldRoom = state.currentRoom;
  state.currentRoom = roomId;
  state.activity.level = 0.3; // Brief activity spike on move
  state.activity.lastAction = `Moved to ${roomId}`;
  state.activity.lastActionTime = new Date().toISOString();
  logger.debug('Agent visual room updated', { agentId, oldRoom, newRoom: roomId });
  return state;
}

/**
 * Update agent's online status.
 */
function updateAgentOnline(agentId, online) {
  const state = visualStates.get(agentId);
  if (!state) return null;
  state.online = online;
  if (online) {
    state.status = 'active';
    state.activity.level = 0.5;
    state.activity.lastAction = 'Came online';
    state.activity.lastActionTime = new Date().toISOString();
  } else {
    state.status = 'offline';
    state.activity.level = 0;
  }
  return state;
}

/**
 * Update agent's status.
 */
function updateAgentStatus(agentId, status) {
  const state = visualStates.get(agentId);
  if (!state) return null;
  state.status = status;
  state.activity.lastActionTime = new Date().toISOString();
  return state;
}

/**
 * Update agent's activity.
 */
function updateAgentActivity(agentId, { level, lastAction }) {
  const state = visualStates.get(agentId);
  if (!state) return null;
  if (level !== undefined) state.activity.level = Math.max(0, Math.min(1, level));
  if (lastAction) state.activity.lastAction = lastAction;
  state.activity.lastActionTime = new Date().toISOString();
  return state;
}

/**
 * Tick activity decay — call each frame to decay activity levels.
 */
function tickActivityDecay(deltaTime) {
  for (const [id, state] of visualStates) {
    if (state.activity.level > 0) {
      state.activity.level = Math.max(0, state.activity.level - deltaTime * 0.05);
    }
    state.activity.pulsePhase = (state.activity.pulsePhase + deltaTime * 3) % (Math.PI * 2);
  }
}

/**
 * Get visual state for an agent.
 */
function getAgentVisual(agentId) {
  return visualStates.get(agentId) || null;
}

/**
 * Get all agent visual states.
 */
function getAllAgentVisuals() {
  return Array.from(visualStates.values());
}

/**
 * Get agents in a specific room.
 */
function getAgentsInRoom(roomId) {
  return Array.from(visualStates.values()).filter(s => s.currentRoom === roomId);
}

/**
 * Remove an agent's visual state.
 */
function removeAgentVisual(agentId) {
  visualStates.delete(agentId);
  colorAssignments.delete(agentId);
}

/**
 * Get full visual world state (for sending to clients).
 */
function getWorldVisualState(roomList) {
  const rooms = roomList.map(room => {
    const agents = getAgentsInRoom(room.id);
    return {
      id: room.id,
      name: room.name,
      description: room.description,
      agentCount: agents.length,
      agents: agents.map(a => ({
        id: a.id,
        name: a.name,
        role: a.role,
        color: a.color,
        status: a.status,
        online: a.online,
        activity: { ...a.activity },
        avatar: { ...a.avatar },
      })),
    };
  });

  const agents = Array.from(visualStates.values()).map(a => ({
    id: a.id,
    name: a.name,
    role: a.role,
    color: a.color,
    currentRoom: a.currentRoom,
    status: a.status,
    online: a.online,
    activity: { ...a.activity },
    avatar: { ...a.avatar },
  }));

  return { rooms, agents, timestamp: new Date().toISOString() };
}

module.exports = {
  initAgentVisual,
  updateAgentRoom,
  updateAgentOnline,
  updateAgentStatus,
  updateAgentActivity,
  tickActivityDecay,
  getAgentVisual,
  getAllAgentVisuals,
  getAgentsInRoom,
  removeAgentVisual,
  getWorldVisualState,
};
