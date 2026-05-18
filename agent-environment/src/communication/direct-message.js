/**
 * Direct Message — Agent-to-agent private messaging.
 * Uses the session layer for real-time delivery.
 */

const session = require('../agents/agent-session');
const logger = require('../utils/logger');

/**
 * Send a direct message from one agent to another.
 */
function sendDirectMessage(fromAgentId, toAgentId, { type = 'dm', content, metadata = {} }) {
  if (!content) return { success: false, error: 'Content required' };

  const message = {
    event: 'direct-message',
    from: fromAgentId,
    to: toAgentId,
    type,
    content,
    metadata,
    timestamp: new Date().toISOString(),
  };

  const delivered = session.sendToAgent(toAgentId, message);
  logger.info('Direct message', { from: fromAgentId, to: toAgentId, delivered });

  return {
    success: true,
    delivered,
    message: delivered ? message : null,
    queued: !delivered, // If not delivered, agent is offline
  };
}

module.exports = { sendDirectMessage };
