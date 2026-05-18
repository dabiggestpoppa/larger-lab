/**
 * Quant Room — Specialized room for quantitative strategy work.
 * Provides shared state for backtests, strategies, and market data.
 */

const fs = require('fs');
const path = require('path');
const config = require('../utils/config');
const logger = require('../utils/logger');

const QUANT_STATE_FILE = path.join(config.dataDir, 'quant-state.json');

// Quant room shared state
let quantState = {
  strategies: [],       // { id, name, code, author, createdAt }
  backtests: [],        // { id, strategyId, results, status, createdAt }
  marketData: {},       // Cached market data snapshots
  lastUpdated: null,
};

function loadState() {
  try {
    if (fs.existsSync(QUANT_STATE_FILE)) {
      quantState = JSON.parse(fs.readFileSync(QUANT_STATE_FILE, 'utf8'));
    }
  } catch (err) {
    logger.error('Failed to load quant state', { error: err.message });
  }
}

function saveState() {
  try {
    quantState.lastUpdated = new Date().toISOString();
    fs.mkdirSync(config.dataDir, { recursive: true });
    fs.writeFileSync(QUANT_STATE_FILE, JSON.stringify(quantState, null, 2), 'utf8');
  } catch (err) {
    logger.error('Failed to save quant state', { error: err.message });
  }
}

/**
 * Register a new strategy.
 */
function addStrategy({ name, code, author }) {
  const strategy = {
    id: `strat_${Date.now()}`,
    name,
    code,
    author,
    createdAt: new Date().toISOString(),
  };
  quantState.strategies.push(strategy);
  saveState();
  logger.info('Strategy added', { name, author });
  return { success: true, strategy };
}

/**
 * Record a backtest result.
 */
function addBacktest({ strategyId, results, status = 'completed' }) {
  const backtest = {
    id: `bt_${Date.now()}`,
    strategyId,
    results,
    status,
    createdAt: new Date().toISOString(),
  };
  quantState.backtests.push(backtest);
  saveState();
  return { success: true, backtest };
}

/**
 * Get all strategies.
 */
function getStrategies() {
  return quantState.strategies;
}

/**
 * Get all backtests.
 */
function getBacktests() {
  return quantState.backtests;
}

/**
 * Get full quant state.
 */
function getState() {
  return { ...quantState };
}

// Load on init
loadState();

module.exports = {
  addStrategy,
  addBacktest,
  getStrategies,
  getBacktests,
  getState,
};
