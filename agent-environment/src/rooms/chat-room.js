/**
 * Chat Room — General team chat room.
 * Wraps the message bus with chat-specific features.
 *
 * UPDATED: 2026-05-20 — Post-meditation soul alignment
 * - Decision Queue: MAD decisions are batched here, not streamed
 * - All messages must tag priority: P0 (critical) | P1 (important) | P2 (normal) | P3 (low)
 * - Manager messages must include: status, blockers, next action, deadline
 * - No passive monitoring messages — only actionable updates
 */

const messageBus = require('../communication/message-bus');
const logger = require('../utils/logger');

const ROOM_ID = 'chat-room';

/**
 * Post a chat message with priority tagging.
 */
function postChat({ from, content, metadata = {}, priority = 'P2' }) {
  return messageBus.postMessage(ROOM_ID, {
    from,
    type: 'chat',
    content,
    metadata: { ...metadata, priority },
    priority,
  });
}

/**
 * Post a task assignment.
 */
function postTask({ from, content, assignee = null, deadline = null }) {
  return messageBus.postMessage(ROOM_ID, {
    from,
    type: 'task',
    content,
    metadata: { assignee, deadline },
    priority: 'P1',
  });
}

/**
 * Post a result/report.
 */
function postResult({ from, content, taskId = null }) {
  return messageBus.postMessage(ROOM_ID, {
    from,
    type: 'result',
    content,
    metadata: { taskId },
    priority: 'P1',
  });
}

/**
 * Post a MAD decision (batched for weekly review).
 */
function postDecision({ from, decision, rationale, impact = '', deadline = null }) {
  return messageBus.postMessage(ROOM_ID, {
    from,
    type: 'decision',
    content: decision,
    metadata: { rationale, impact, deadline, status: 'pending' },
    priority: 'P0',
  });
}

/**
 * Post a manager status update.
 * Must include: status, blockers, next action, deadline.
 */
function postManagerUpdate({ from, room, status, blockers = [], nextAction = '', deadline = '' }) {
  return messageBus.postMessage(ROOM_ID, {
    from,
    type: 'manager-update',
    content: `[${room}] ${status}`,
    metadata: { room, status, blockers, nextAction, deadline },
    priority: blockers.length > 0 ? 'P0' : 'P1',
  });
}

/**
 * Get chat history.
 */
function getHistory(opts = {}) {
  return messageBus.getMessages(ROOM_ID, opts);
}

module.exports = {
  postChat,
  postTask,
  postResult,
  postDecision,
  postManagerUpdate,
  getHistory,
  ROOM_ID,
};
