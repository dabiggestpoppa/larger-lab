/**
 * Meditation Room — IACER thinking space.
 *
 * Before spawning a new agent, it enters the meditation room.
 * It receives a task/idea and works through the IACER framework:
 *   Intent     — What is the true objective?
 *   Abstraction — What are the layers?
 *   Context    — What's the current state?
 *   Expectations — What does success look like?
 *   Results    — What's the expected outcome?
 *
 * Agent thinks through the problem, creates a prototype sketch.
 * When ready, it pings OWL with its idea for approval to join a working room.
 */

const fs = require('fs');
const path = require('path');
const config = require('../utils/config');
const logger = require('../utils/logger');

const MEDITATION_STATE_FILE = path.join(config.dataDir, 'meditation-state.json');

// Active meditation sessions: agentId -> session
let sessions = new Map();

function loadState() {
  try {
    if (fs.existsSync(MEDITATION_STATE_FILE)) {
      const data = JSON.parse(fs.readFileSync(MEDITATION_STATE_FILE, 'utf8'));
      sessions = new Map(Object.entries(data.sessions || {}));
    }
  } catch (err) {
    logger.error('Failed to load meditation state', { error: err.message });
  }
}

function saveState() {
  try {
    fs.mkdirSync(config.dataDir, { recursive: true });
    fs.writeFileSync(MEDITATION_STATE_FILE, JSON.stringify({
      sessions: Object.fromEntries(sessions),
      lastUpdated: new Date().toISOString(),
    }, null, 2), 'utf8');
  } catch (err) {
    logger.error('Failed to save meditation state', { error: err.message });
  }
}

/**
 * Begin a meditation session for an agent.
 */
function beginMeditation(agentId, { task = '', idea = '' }) {
  const session = {
    agentId,
    task,
    idea,
    startedAt: new Date().toISOString(),
    status: 'meditating',
    iacer: {
      intent: null,
      abstraction: null,
      context: null,
      expectations: null,
      results: null,
    },
    prototypeSketch: null,
    completed: false,
  };
  sessions.set(agentId, session);
  saveState();
  logger.info('Meditation started', { agentId, task: task.slice(0, 60) });
  return { success: true, session };
}

/**
 * Update the IACER framework for a meditating agent.
 */
function updateIacer(agentId, { intent, abstraction, context, expectations, results }) {
  const session = sessions.get(agentId);
  if (!session) return { success: false, error: 'No active meditation session' };

  if (intent !== undefined) session.iacer.intent = intent;
  if (abstraction !== undefined) session.iacer.abstraction = abstraction;
  if (context !== undefined) session.iacer.context = context;
  if (expectations !== undefined) session.iacer.expectations = expectations;
  if (results !== undefined) session.iacer.results = results;

  saveState();
  return { success: true, iacer: session.iacer };
}

/**
 * Set the prototype sketch (agent's plan after meditation).
 */
function setPrototypeSketch(agentId, sketch) {
  const session = sessions.get(agentId);
  if (!session) return { success: false, error: 'No active meditation session' };
  session.prototypeSketch = sketch;
  saveState();
  return { success: true };
}

/**
 * Complete meditation — agent is ready to join a working room.
 */
function completeMeditation(agentId) {
  const session = sessions.get(agentId);
  if (!session) return { success: false, error: 'No active meditation session' };
  session.completed = true;
  session.status = 'ready';
  session.completedAt = new Date().toISOString();
  saveState();
  logger.info('Meditation completed', { agentId, hasSketch: !!session.prototypeSketch });
  return { success: true, session };
}

/**
 * Get meditation session.
 */
function getSession(agentId) {
  return sessions.get(agentId) || null;
}

/**
 * List all active meditation sessions.
 */
function listSessions() {
  return Array.from(sessions.entries()).map(([id, s]) => ({ agentId: id, ...s }));
}

/**
 * Check if agent has completed meditation.
 */
function isReady(agentId) {
  const session = sessions.get(agentId);
  return session ? session.completed : false;
}

// Load on init
loadState();

module.exports = {
  beginMeditation,
  updateIacer,
  setPrototypeSketch,
  completeMeditation,
  getSession,
  listSessions,
  isReady,
};
