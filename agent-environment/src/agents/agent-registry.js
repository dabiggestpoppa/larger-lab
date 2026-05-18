/**
 * Agent Registry — Manages agent identities, capabilities, and presence.
 * Persists to data/agents.json.
 */

const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const config = require('../utils/config');
const logger = require('../utils/logger');

const AGENTS_FILE = path.join(config.dataDir, 'agents.json');

// In-memory store
let agents = new Map();

// Load persisted agents
function loadAgents() {
  try {
    if (fs.existsSync(AGENTS_FILE)) {
      const data = JSON.parse(fs.readFileSync(AGENTS_FILE, 'utf8'));
      agents = new Map(Object.entries(data));
      logger.info(`Loaded ${agents.size} agents from disk`);
    }
  } catch (err) {
    logger.error('Failed to load agents', { error: err.message });
  }
}

// Persist agents to disk
function saveAgents() {
  try {
    fs.mkdirSync(config.dataDir, { recursive: true });
    const data = Object.fromEntries(agents);
    fs.writeFileSync(AGENTS_FILE, JSON.stringify(data, null, 2), 'utf8');
  } catch (err) {
    logger.error('Failed to save agents', { error: err.message });
  }
}

/**
 * Register a new agent.
 * @param {object} params - { name, role, capabilities }
 * @returns {object} The created agent
 */
function registerAgent({ name, role = 'general', capabilities = [], metadata = {} }) {
  if (agents.size >= config.maxAgents) {
    return { success: false, error: 'Maximum agent limit reached' };
  }
  const id = uuidv4().slice(0, 8); // Short readable ID
  const agent = {
    id,
    name,
    role,
    capabilities: [...config.defaultCapabilities, ...capabilities],
    currentRoom: 'meditation-room', // All agents start in meditation
    status: 'meditating',
    createdAt: new Date().toISOString(),
    lastActive: new Date().toISOString(),
    metadata,
  };
  agents.set(id, agent);
  saveAgents();
  logger.info('Agent registered', { id, name, role });
  return { success: true, agent };
}

/**
 * Get agent by ID.
 */
function getAgent(id) {
  const agent = agents.get(id);
  if (!agent) return null;
  agent.lastActive = new Date().toISOString();
  return agent;
}

/**
 * Update agent fields.
 */
function updateAgent(id, updates) {
  const agent = agents.get(id);
  if (!agent) return { success: false, error: 'Agent not found' };
  Object.assign(agent, updates, { lastActive: new Date().toISOString() });
  agents.set(id, agent);
  saveAgents();
  return { success: true, agent };
}

/**
 * Move agent to a room.
 */
function moveAgent(id, roomId) {
  return updateAgent(id, { currentRoom: roomId, status: 'active' });
}

/**
 * List all agents, optionally filtered by room.
 */
function listAgents(filter = {}) {
  let result = Array.from(agents.values());
  if (filter.room) result = result.filter(a => a.currentRoom === filter.room);
  if (filter.status) result = result.filter(a => a.status === filter.status);
  if (filter.role) result = result.filter(a => a.role === filter.role);
  return result;
}

/**
 * Deregister an agent.
 */
function deregisterAgent(id) {
  const deleted = agents.delete(id);
  if (deleted) saveAgents();
  return { success: deleted };
}

// Load on module init
loadAgents();

module.exports = {
  registerAgent,
  getAgent,
  updateAgent,
  moveAgent,
  listAgents,
  deregisterAgent,
  saveAgents,
};
