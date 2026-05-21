/**
 * Room Manager — Creates, manages, and tracks rooms and agent membership.
 * Persists to data/rooms.json.
 *
 * UPDATED: 2026-05-20 — Post-meditation soul alignment
 * - Each room now has: purpose, rules, spawnPrompt, manager
 * - Managers are responsible for room governance and worker spawning
 * - Max 5 concurrent workers per room (system-wide max: 5)
 * - All room operations logged with agent soul alignment
 */

const fs = require('fs');
const path = require('path');
const config = require('../utils/config');
const logger = require('../utils/logger');

const ROOMS_FILE = path.join(config.dataDir, 'rooms.json');

// In-memory: roomId -> { id, name, description, agents: Set, createdAt, ... }
let rooms = new Map();

// Room governance definitions — updated from meditation insights
const ROOM_GOVERNANCE = {
  'meditation-room': {
    purpose: 'IACER thinking space. All agents meditate before joining the field. Meditations must be actionable.',
    manager: 'OWL',
    rules: [
      'All meditations must include: insight, evidence, recommendation, deadline',
      'CEO/SAGE meditations must include revenue impact assessment',
      'Manager meditations must include room governance updates',
      'Reference MEDITATION_INDEX.md for cross-agent synthesis',
      'No philosophical navel-gazing — every meditation must change a decision',
    ],
    spawnPrompt: 'Read your SOUL file in agent-souls/ and MEDITATION_INDEX.md. Meditate on your assigned topic. Use the IACER framework. Complete with actionable insight + recommendation.',
  },
  'quant-room': {
    purpose: 'Quant Lab — strategy validation, backtesting, forward testing. Only validated strategies ship.',
    manager: 'Quant Lab Manager',
    rules: [
      'No strategy deployment without passing all 5 validation gates (PF>1.5, MaxDD<5%, WR>50%, 100+ trades, MC 0% ruin)',
      'Real costs mandatory — no zero-cost backtests',
      'Reporting artifacts are the #1 enemy — every number verified independently',
      'Only DMR is approved for forward test. All other strategies on hold.',
      'Abandoned strategies: Two_Plays, Constraint_Anchor, Stall_Harvest, Dual_Engine, Failure_Repair',
      'Forward test protocol: 20+ demo trades → small live (0.01L) → scale',
    ],
    spawnPrompt: 'Read QUANT_LAB_SOUL.md. Your task is strategy validation. Use the 5-gate validation framework. All results must include real costs. Report honestly — no inflated numbers.',
  },
  'chat-room': {
    purpose: 'General team chat and coordination. Decision Queue hub.',
    manager: 'OWL',
    rules: [
      'All messages must tag priority: P0 (critical) | P1 (important) | P2 (normal) | P3 (low)',
      'MAD decisions are batched here for weekly review — not streamed',
      'Manager messages must include: status, blockers, next action, deadline',
      'No passive monitoring messages — only actionable updates',
    ],
    spawnPrompt: 'Post updates with priority tags. Include blockers and next actions. Batch decisions for MAD review.',
  },
  'war-room': {
    purpose: 'Mission command — active operations and debugging. No passive monitoring.',
    manager: 'PM (Polymorph)',
    rules: [
      'Active operations only — if nothing is broken, this room is empty',
      'All ops must have: objective, success criteria, timeout, rollback plan',
      'Max 2 concurrent ops to avoid resource contention',
      'Post-op report required within 1 hour of completion',
    ],
    spawnPrompt: 'Read your SOUL file. You are debugging or executing an active operation. Define objective, success criteria, timeout. Report results.',
  },
  'farm-room': {
    purpose: 'Content Farm — production, marketing, revenue. Get content published.',
    manager: 'Farm Manager',
    rules: [
      'No more planning documents until first post is published',
      'Every task must have a specific deliverable and deadline',
      'Escalate MAD-dependent blockers within 24 hours',
      'Daily posting cadence once accounts are live',
      'All content must include monetization path (affiliate, product, or funnel)',
      'Primary niche: AI Tools for Creators. Content mix: 40% edu, 30% ent, 20% promo, 10% community',
    ],
    spawnPrompt: 'Read FARM_SOUL.md. Your task is content production and monetization. Every deliverable must have a deadline. Include monetization path. Escalate blockers immediately.',
  },
  'sw-dev-room': {
    purpose: 'Software Development — build, test, ship. Testing > Building until MAD says otherwise.',
    manager: 'SW Dev Manager',
    rules: [
      'No new features until v3 UI is connected to real data',
      'No simulated/fake data in any production view',
      'All views must handle API failures gracefully',
      'Testing > Building until MAD says otherwise',
      'Frontend fixes must not break backend (27/27 tests must stay green)',
      'Priority: app-v3.js self-contained → dashboard live → terminal real → chat real',
    ],
    spawnPrompt: 'Read SW_DEV_SOUL.md. Your priority is making v3 UI a live command center. Remove v2 dependency. Connect to real data. Test everything. No simulated data.',
  },
  'validation-room': {
    purpose: 'Quality gate. Nothing ships without PASS.',
    manager: 'AS (Assistant Manager)',
    rules: [
      'All deliverables must pass validation before shipping',
      'Validation criteria defined per-room in ROOM_GOVERNANCE',
      'Failed validation → return to origin room with specific fix list',
      'Max 3 validation rounds per deliverable — then escalate to OWL',
    ],
    spawnPrompt: 'Read the validation criteria for the source room. Test the deliverable against all criteria. Report PASS or FAIL with specific findings.',
  },
  'archive-room': {
    purpose: 'Compressed history, completed work, decision records.',
    manager: 'OWL',
    rules: [
      'Only completed work gets archived',
      'Include: what was done, why, result, lessons learned',
      'Compress aggressively — preserve trajectory, not noise',
      'MEDITATION_INDEX.md is the index for all archived meditations',
    ],
    spawnPrompt: 'Archive completed work with compression. Include result and lessons learned. Update MEDITATION_INDEX.md if archiving meditations.',
  },
};

// Load persisted rooms
function loadRooms() {
  try {
    if (fs.existsSync(ROOMS_FILE)) {
      const data = JSON.parse(fs.readFileSync(ROOMS_FILE, 'utf8'));
      for (const [id, room] of Object.entries(data)) {
        room.agents = new Set(room.agents || []);
        // Merge governance if not present
        if (!room.governance && ROOM_GOVERNANCE[id]) {
          room.governance = ROOM_GOVERNANCE[id];
        }
        rooms.set(id, room);
      }
      logger.info(`Loaded ${rooms.size} rooms from disk`);
    }
  } catch (err) {
    logger.error('Failed to load rooms', { error: err.message });
  }

  // Ensure default rooms exist with governance
  for (const [id, gov] of Object.entries(ROOM_GOVERNANCE)) {
    if (!rooms.has(id)) {
      rooms.set(id, {
        id,
        name: gov.name || id,
        description: gov.purpose,
        agents: new Set(),
        persistent: true,
        governance: gov,
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
    data[id] = {
      ...room,
      agents: Array.from(room.agents),
      governance: room.governance || ROOM_GOVERNANCE[id] || null,
    };
  }
    fs.writeFileSync(ROOMS_FILE, JSON.stringify(data, null, 2), 'utf8');
  } catch (err) {
    logger.error('Failed to save rooms', { error: err.message });
  }
}

/**
 * Create a new room.
 */
function createRoom({ name, description = '', persistent = false, governance = null }) {
  const id = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-_]/g, '');
  if (rooms.has(id)) return { success: false, error: 'Room already exists' };

  const room = {
    id,
    name,
    description,
    agents: new Set(),
    persistent,
    governance,
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

/**
 * Get room governance (rules, spawn prompt, manager).
 */
function getRoomGovernance(roomId) {
  const room = rooms.get(roomId);
  if (!room) return null;
  return room.governance || ROOM_GOVERNANCE[roomId] || null;
}

/**
 * Update room governance.
 */
function updateRoomGovernance(roomId, governance) {
  const room = rooms.get(roomId);
  if (!room) return { success: false, error: 'Room not found' };
  room.governance = { ...room.governance, ...governance };
  saveRooms();
  logger.info('Room governance updated', { roomId });
  return { success: true, governance: room.governance };
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
  getRoomGovernance,
  updateRoomGovernance,
  saveRooms,
  ROOM_GOVERNANCE,
};
