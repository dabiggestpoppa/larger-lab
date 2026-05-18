/**
 * World Engine — Main game loop / update cycle for the virtual agent environment.
 * Ties together agent visuals, room layout, activity tracking, and broadcasts.
 */

const logger = require('./utils/logger');
const agentRegistry = require('./agents/agent-registry');
const agentSession = require('./agents/agent-session');
const roomManager = require('./rooms/room-manager');
const messageBus = require('./communication/message-bus');
const agentVisual = require('./agent-visual');
const roomVisual = require('./room-visual');
const activityTracker = require('./activity-tracker');

// World state
let worldState = {
  rooms: [],
  agents: [],
  connections: [],
  recentActivity: [],
  timestamp: null,
};

// Timing
let lastTick = Date.now();
let tickCount = 0;
const TICK_INTERVAL = 1000 / 30; // 30 FPS target
const BROADCAST_INTERVAL = 500; // Broadcast state every 500ms
let lastBroadcast = 0;

// Broadcast function (set by server.js)
let broadcastToAllFn = null;

/**
 * Set broadcast function.
 */
function setBroadcastFunction(fn) {
  broadcastToAllFn = fn;
}

/**
 * Initialize the world engine — set up visuals for existing rooms and agents.
 */
function initialize() {
  // Compute room layout with responsive width
  const rooms = roomManager.listRooms();
  roomVisual.computeRoomLayout(rooms, 1200);

  // Initialize visuals for existing agents
  const agents = agentRegistry.listAgents();
  for (const agent of agents) {
    agentVisual.initAgentVisual(agent);
  }

  // Set up activity tracker broadcast
  const self = {
    broadcast: (event, data) => {
      if (broadcastToAllFn) broadcastToAllFn({ event, ...data });
    },
    broadcastAll: (data) => {
      if (broadcastToAllFn) broadcastToAllFn(data);
    },
  };
  activityTracker.setBroadcastFunctions(self);

  updateWorldState();
  logger.info('World engine initialized', {
    rooms: rooms.length,
    agents: agents.length,
  });
}

/**
 * Main tick — called as frequently as possible, throttled internally.
 */
function tick() {
  const now = Date.now();
  const deltaTime = (now - lastTick) / 1000; // in seconds
  lastTick = now;
  tickCount++;

  // Tick activity tracker (decay, idle connections)
  activityTracker.tick(deltaTime);

  // Periodic broadcast
  if (now - lastBroadcast > BROADCAST_INTERVAL) {
    updateWorldState();
    if (broadcastToAllFn) {
      broadcastToAllFn({
        event: 'world.state',
        ...worldState,
      });
    }
    lastBroadcast = now;
  }
}

/**
 * Update the consolidated world state.
 */
function updateWorldState() {
  const rooms = roomManager.listRooms();
  const agents = agentRegistry.listAgents();
  const onlineAgents = agentSession.getOnlineAgents();

  // Ensure all agents have visual states
  for (const agent of agents) {
    if (!agentVisual.getAgentVisual(agent.id)) {
      agentVisual.initAgentVisual(agent);
    }
    // Update online status
    agentVisual.updateAgentOnline(agent.id, onlineAgents.includes(agent.id));
  }

  // Recompute layout if room count changed (new rooms added)
  const currentRoomCount = roomVisual.getAllRoomVisuals().length;
  if (rooms.length !== currentRoomCount) {
    roomVisual.computeRoomLayout(rooms, 1200);
  }

  // Build room states with agents
  const roomStates = rooms.map(room => {
    const roomAgents = agents
      .filter(a => a.currentRoom === room.id)
      .map(a => {
        const visual = agentVisual.getAgentVisual(a.id);
        const isOnline = onlineAgents.includes(a.id) || ['active', 'working', 'meditating', 'idle'].includes(a.status);
        return {
          id: a.id,
          name: a.name,
          role: a.role,
          color: visual?.color || '#888',
          status: a.status,
          online: isOnline,
          activity: visual?.activity || { level: 0, lastAction: '' },
          avatar: visual?.avatar || { label: a.name, emoji: '🤖', radius: 18 },
        };
      });

    const visual = roomVisual.getRoomVisual(room.id);
    return {
      id: room.id,
      name: room.name,
      description: room.description || '',
      icon: visual?.icon || '🏠',
      color: visual?.color || '#636e72',
      bgColor: visual?.bgColor || 'rgba(99,110,114,0.08)',
      borderColor: visual?.borderColor || 'rgba(99,110,114,0.3)',
      position: visual?.position || { x: 0, y: 0 },
      size: visual?.size || { w: 220, h: 160 },
      agentCount: roomAgents.length,
      agents: roomAgents,
    };
  });

  // Build agent states
  const agentStates = agents.map(a => {
    const visual = agentVisual.getAgentVisual(a.id);
    const isOnline = onlineAgents.includes(a.id) || ['active', 'working', 'meditating', 'idle'].includes(a.status);
    return {
      id: a.id,
      name: a.name,
      role: a.role,
      color: visual?.color || '#888',
      currentRoom: a.currentRoom,
      status: a.status,
      online: isOnline,
      activity: visual?.activity || { level: 0, lastAction: '' },
      avatar: visual?.avatar || { label: a.name, emoji: '🤖', radius: 18 },
      capabilities: a.capabilities || [],
    };
  });

  worldState = {
    rooms: roomStates,
    agents: agentStates,
    connections: activityTracker.getConnections(),
    recentActivity: activityTracker.getActivityLog(10),
    timestamp: new Date().toISOString(),
  };

  return worldState;
}

/**
 * Get current world state (without forcing an update).
 */
function getWorldState() {
  return worldState;
}

/**
 * Register a new agent in the world.
 */
function registerAgent(agent) {
  agentVisual.initAgentVisual(agent);
  activityTracker.recordActivity(agent.id, 'Registered in world', 0.4);
  updateWorldState();
  if (broadcastToAllFn) {
    broadcastToAllFn({
      event: 'agent.joined',
      agentId: agent.id,
      agent: worldState.agents.find(a => a.id === agent.id),
    });
  }
}

/**
 * Move agent to a room.
 */
function moveAgent(agentId, roomId) {
  const agent = agentRegistry.getAgent(agentId);
  if (!agent) return null;

  agentVisual.updateAgentRoom(agentId, roomId);
  activityTracker.recordActivity(agentId, `Moved to ${roomId}`, 0.5);
  updateWorldState();

  if (broadcastToAllFn) {
    broadcastToAllFn({
      event: 'agent.moved',
      agentId,
      fromRoom: agent.currentRoom,
      toRoom: roomId,
    });
  }

  return worldState;
}

/**
 * Update agent status.
 */
function setAgentStatus(agentId, status) {
  agentVisual.updateAgentStatus(agentId, status);
  agentRegistry.updateAgent(agentId, { status });
  activityTracker.recordActivity(agentId, `Status: ${status}`, 0.3);
  updateWorldState();

  if (broadcastToAllFn) {
    broadcastToAllFn({
      event: 'agent.status',
      agentId,
      status,
    });
  }
}

/**
 * Record a message in the world.
 */
function recordMessage(from, to, roomId, type) {
  activityTracker.recordMessage(from, to, roomId, type);
}

/**
 * Record agent activity.
 */
function recordActivity(agentId, action, level) {
  activityTracker.recordActivity(agentId, action, level);
}

/**
 * Remove agent from world.
 */
function removeAgent(agentId) {
  agentVisual.removeAgentVisual(agentId);
  updateWorldState();
  if (broadcastToAllFn) {
    broadcastToAllFn({
      event: 'agent.left',
      agentId,
    });
  }
}

module.exports = {
  initialize,
  tick,
  getWorldState,
  updateWorldState,
  registerAgent,
  moveAgent,
  setAgentStatus,
  recordMessage,
  recordActivity,
  removeAgent,
  setBroadcastFunction,
};
