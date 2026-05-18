/**
 * Chat Room — General team chat room.
 * Wraps the message bus with chat-specific features.
 */

const messageBus = require('../communication/message-bus');
const logger = require('../utils/logger');

const ROOM_ID = 'chat-room';

/**
 * Post a chat message.
 */
function postChat({ from, content, metadata = {} }) {
  return messageBus.postMessage(ROOM_ID, {
    from,
    type: 'chat',
    content,
    metadata,
  });
}

/**
 * Post a task assignment.
 */
function postTask({ from, content, assignee = null }) {
  return messageBus.postMessage(ROOM_ID, {
    from,
    type: 'task',
    content,
    metadata: { assignee },
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
  getHistory,
  ROOM_ID,
};
