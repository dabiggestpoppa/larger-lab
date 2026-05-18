/**
 * Config — Loads environment.yaml and provides accessors.
 */

const fs = require('fs');
const path = require('path');
const yaml = require('yaml');

const configPath = path.join(__dirname, '..', '..', 'config', 'environment.yaml');

let parsed = {};
try {
  const raw = fs.readFileSync(configPath, 'utf8');
  parsed = yaml.parse(raw) || {};
} catch (err) {
  console.warn('[config] Could not load environment.yaml, using defaults:', err.message);
}

const env = parsed.environment || {};
const sandbox = parsed.sandbox || {};
const rooms = parsed.rooms || {};
const agents = parsed.agents || {};
const messages = parsed.messages || {};

module.exports = {
  // Server
  port: env.port || 9000,
  host: env.host || 'localhost',

  // Sandbox
  sandbox: {
    pythonEnabled: sandbox.python?.enabled !== false,
    nodeEnabled: sandbox.node?.enabled !== false,
    pythonTimeoutMs: sandbox.python?.timeout_ms || 30000,
    nodeTimeoutMs: sandbox.node?.timeout_ms || 30000,
    maxOutputBytes: sandbox.python?.max_output_bytes || 65536,
    workspaceRoot: sandbox.filesystem?.workspace_root || 'data/workspace',
    maxFileSizeBytes: sandbox.filesystem?.max_file_size_bytes || 1048576,
  },

  // Rooms
  defaultRooms: (rooms.defaults || []).map(r => ({
    id: r.name.toLowerCase().replace(/\s+/g, '-'),
    name: r.name,
    description: r.description || '',
    persistent: r.persistent !== false,
  })),

  // Agents
  maxAgents: agents.max_concurrent || 20,
  defaultCapabilities: agents.default_capabilities || ['communicate'],
  sessionTimeoutMinutes: agents.session_timeout_minutes || 60,

  // Messages
  maxHistoryPerRoom: messages.max_history_per_room || 500,
  maxMessageLength: messages.max_message_length || 4096,

  // Paths
  dataDir: path.join(__dirname, '..', '..', 'data'),
};
