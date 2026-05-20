/**
 * FAM CHAT — Cross-room agent communication system.
 * Allows agents to send messages across room boundaries.
 * Flood-controlled via rate limiting and subscription model.
 */

const fs = require('fs');
const path = require('path');
const config = require('../utils/config');
const logger = require('../utils/logger');
const agentRegistry = require('../agents/agent-registry');

const FAM_MESSAGES_FILE = path.join(config.dataDir, 'fam-messages.json');

// ── Rate Limiting ──────────────────────────────────────────────
// Track FAM message counts per agent: agentId -> { windowStart, count }
const famRateBuckets = new Map();
const famBroadcastBuckets = new Map();

function checkFamRateLimit(agentId) {
  const cfg = config.famChat || {};
  const now = Date.now();
  const windowMs = 10000; // 10-second window
  const maxMsgs = cfg.maxMessagesPer10s || 5;

  const bucket = famRateBuckets.get(agentId);
  if (!bucket || now - bucket.windowStart > windowMs) {
    famRateBuckets.set(agentId, { windowStart: now, count: 1 });
    return true;
  }
  bucket.count++;
  return bucket.count <= maxMsgs;
}

function checkFamBroadcastLimit(agentId) {
  const cfg = config.famChat || {};
  const now = Date.now();
  const windowMs = 60000; // 60-second window
  const maxBroadcasts = cfg.maxBroadcastsPer60s || 2;

  const bucket = famBroadcastBuckets.get(agentId);
  if (!bucket || now - bucket.windowStart > windowMs) {
    famBroadcastBuckets.set(agentId, { windowStart: now, count: 1 });
    return true;
  }
  bucket.count++;
  return bucket.count <= maxBroadcasts;
}

// Clean up rate limit buckets every 5 minutes
setInterval(() => {
  const now = Date.now();
  for (const [key, bucket] of famRateBuckets) {
    if (now - bucket.windowStart > 600000) famRateBuckets.delete(key);
  }
  for (const [key, bucket] of famBroadcastBuckets) {
    if (now - bucket.windowStart > 600000) famBroadcastBuckets.delete(key);
  }
}, 300000);

// ── Subscriptions ──────────────────────────────────────────────
// agentId -> Set of subscription strings
const subscriptions = new Map();
// channel name -> Set of agent IDs
const channelMembers = new Map();
// agentId -> Set of blocked agent IDs
const blockedAgents = new Map();

// ── Message Store ──────────────────────────────────────────────
let famMessages = [];

function loadFamMessages() {
  try {
    if (fs.existsSync(FAM_MESSAGES_FILE)) {
      famMessages = JSON.parse(fs.readFileSync(FAM_MESSAGES_FILE, 'utf8'));
      logger.info(`Loaded ${famMessages.length} FAM messages from disk`);
    }
  } catch (err) {
    logger.error('Failed to load FAM messages', { error: err.message });
    famMessages = [];
  }
}

function saveFamMessages() {
  try {
    fs.mkdirSync(config.dataDir, { recursive: true });
    // Keep only last 500 FAM messages
    const toSave = famMessages.slice(-500);
    fs.writeFileSync(FAM_MESSAGES_FILE, JSON.stringify(toSave, null, 2), 'utf8');
  } catch (err) {
    logger.error('Failed to save FAM messages', { error: err.message });
  }
}

// ── Core Functions ─────────────────────────────────────────────

/**
 * Send a FAM CHAT message.
 */
function sendFamMessage({ from, to, content, channel }) {
  const cfg = config.famChat;
  if (!cfg || !cfg.enabled) {
    return { success: false, error: 'FAM CHAT is disabled', code: 'FAM_NOT_ENABLED' };
  }

  // Validate sender
  const sender = agentRegistry.getAgent(from);
  if (!sender) return { success: false, error: 'Sender agent not found', code: 'FAM_AGENT_NOT_FOUND' };

  // Validate target
  let target = null;
  if (to !== '*') {
    target = agentRegistry.getAgent(to);
    if (!target) return { success: false, error: 'Target agent not found', code: 'FAM_AGENT_NOT_FOUND' };
  }

  // Check rate limits
  if (to === '*') {
    if (!cfg.allowBroadcast) return { success: false, error: 'Broadcast is disabled', code: 'FAM_BROADCAST_DISABLED' };
    if (!checkFamBroadcastLimit(from)) {
      return { success: false, error: 'Broadcast rate limit exceeded (max 2/min)', code: 'FAM_BROADCAST_LIMITED' };
    }
  } else {
    if (!checkFamRateLimit(from)) {
      return { success: false, error: 'FAM message rate limit exceeded (max 5/10s)', code: 'FAM_RATE_LIMITED' };
    }
  }

  // Check if sender is blocked by target
  if (to !== '*') {
    const targetBlocks = blockedAgents.get(to);
    if (targetBlocks && targetBlocks.has(from)) {
      return { success: false, error: 'You are blocked by this agent', code: 'FAM_AGENT_BLOCKED' };
    }
  }

  // Build message
  const message = {
    id: `fam_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    from,
    to,
    type: channel ? 'fam-channel' : (to === '*' ? 'fam-broadcast' : 'fam-chat'),
    content,
    sourceRoom: sender.currentRoom || null,
    targetRoom: target ? target.currentRoom : null,
    channel: channel || null,
    timestamp: new Date().toISOString(),
  };

  // Store message
  famMessages.push(message);
  if (famMessages.length > 1000) famMessages = famMessages.slice(-500);
  saveFamMessages();

  logger.info('FAM message sent', { from, to, type: message.type, channel });
  return { success: true, message };
}

/**
 * Get FAM messages for an agent (based on subscriptions).
 */
function getFamMessages(agentId, { limit = 50 } = {}) {
  const subs = subscriptions.get(agentId);
  const blocks = blockedAgents.get(agentId) || new Set();

  const filtered = famMessages.filter(msg => {
    // Don't show messages from blocked agents
    if (blocks.has(msg.from)) return false;

    // Messages sent directly to this agent
    if (msg.to === agentId) return true;

    // Messages from this agent
    if (msg.from === agentId) return true;

    // Broadcasts — only if subscribed to 'all'
    if (msg.to === '*') {
      if (!subs) return false;
      return subs.has('all') || subs.has('direct-only');
    }

    // Channel messages — only if subscribed to the channel
    if (msg.channel) {
      if (!subs) return false;
      return subs.has(msg.channel);
    }

    return false;
  });

  return {
    success: true,
    messages: filtered.slice(-limit),
    total: filtered.length,
  };
}

/**
 * Subscribe an agent to a channel or feed.
 */
function subscribe(agentId, channel) {
  const cfg = config.famChat;
  const maxSubs = cfg.maxSubscriptions || 10;

  if (!subscriptions.has(agentId)) {
    subscriptions.set(agentId, new Set());
  }
  const subs = subscriptions.get(agentId);

  if (subs.size >= maxSubs && !subs.has(channel)) {
    return { success: false, error: `Maximum subscriptions reached (${maxSubs})`, code: 'FAM_SUBSCRIPTION_LIMIT' };
  }

  subs.add(channel);

  // Track channel membership
  if (channel.startsWith('#')) {
    if (!channelMembers.has(channel)) {
      channelMembers.set(channel, new Set());
    }
    channelMembers.get(channel).add(agentId);
  }

  logger.info('FAM subscription added', { agentId, channel });
  return { success: true, subscriptions: Array.from(subs) };
}

/**
 * Unsubscribe an agent from a channel or feed.
 */
function unsubscribe(agentId, channel) {
  const subs = subscriptions.get(agentId);
  if (subs) {
    subs.delete(channel);
  }

  // Remove from channel membership
  if (channel.startsWith('#')) {
    const members = channelMembers.get(channel);
    if (members) {
      members.delete(agentId);
      if (members.size === 0) channelMembers.delete(channel);
    }
  }

  logger.info('FAM subscription removed', { agentId, channel });
  return { success: true, subscriptions: subs ? Array.from(subs) : [] };
}

/**
 * Get an agent's subscriptions.
 */
function getSubscriptions(agentId) {
  const subs = subscriptions.get(agentId);
  return { success: true, subscriptions: subs ? Array.from(subs) : [] };
}

/**
 * Get all active channels.
 */
function getChannels() {
  const cfg = config.famChat || {};
  const defaults = cfg.defaultChannels || ['#general'];
  const channels = [];

  // Include default channels even if empty
  for (const name of defaults) {
    const members = channelMembers.get(name);
    channels.push({
      name,
      memberCount: members ? members.size : 0,
      members: members ? Array.from(members) : [],
    });
  }

  // Include non-default channels that have members
  for (const [name, members] of channelMembers) {
    if (!defaults.includes(name) && members.size > 0) {
      channels.push({
        name,
        memberCount: members.size,
        members: Array.from(members),
      });
    }
  }

  return { success: true, channels };
}

/**
 * Block an agent.
 */
function blockAgent(agentId, blockId) {
  if (!blockedAgents.has(agentId)) {
    blockedAgents.set(agentId, new Set());
  }
  blockedAgents.get(agentId).add(blockId);
  logger.info('FAM block', { agentId, blockId });
  return { success: true };
}

/**
 * Unblock an agent.
 */
function unblockAgent(agentId, unblockId) {
  const blocks = blockedAgents.get(agentId);
  if (blocks) blocks.delete(unblockId);
  logger.info('FAM unblock', { agentId, unblockId });
  return { success: true };
}

/**
 * Get blocked agents for an agent.
 */
function getBlocked(agentId) {
  const blocks = blockedAgents.get(agentId);
  return { success: true, blocked: blocks ? Array.from(blocks) : [] };
}

// ── Initialize default subscriptions ───────────────────────────
// On agent registration, auto-subscribe to #general
function onAgentRegistered(agentId) {
  subscribe(agentId, '#general');
}

// Load on init
loadFamMessages();

module.exports = {
  sendFamMessage,
  getFamMessages,
  subscribe,
  unsubscribe,
  getSubscriptions,
  getChannels,
  blockAgent,
  unblockAgent,
  getBlocked,
  onAgentRegistered,
};
