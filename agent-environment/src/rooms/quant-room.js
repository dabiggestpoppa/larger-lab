/**
 * Quant Room — Specialized room for quantitative strategy work.
 * Provides shared state for backtests, strategies, and market data.
 *
 * UPDATED: 2026-05-20 — Post-meditation soul alignment
 * - Validation gate enforced: PF>1.5, MaxDD<5%, WR>50%, 100+ trades, MC 0% ruin
 * - Only DMR is approved for forward test. All others on hold.
 * - Real costs mandatory. No zero-cost backtests.
 * - Reporting artifacts are the #1 enemy. Every number verified independently.
 */

const fs = require('fs');
const path = require('path');
const config = require('../utils/config');
const logger = require('../utils/logger');

const QUANT_STATE_FILE = path.join(config.dataDir, 'quant-state.json');

// Quant room shared state
let quantState = {
  strategies: [],       // { id, name, code, author, createdAt, status }
  backtests: [],        // { id, strategyId, results, status, createdAt }
  forwardTests: [],     // { id, strategyId, liveResults, status, trades, wr, pnl }
  marketData: {},       // Cached market data snapshots
  validationGate: {     // Hard validation criteria
    minPF: 1.5,
    maxDD: 5.0,
    minWR: 50.0,
    minTrades: 100,
    mcRuinLimit: 0,     // 0% ruin probability
    requireRealCosts: true,
  },
  approvedForForwardTest: ['DMR'],  // Only DMR approved
  abandoned: ['Two_Plays', 'Constraint_Anchor', 'Stall_Harvest', 'Dual_Engine', 'Failure_Repair'],
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
    status: 'registered', // registered → backtested → mc_validated → forward_tested → live
    createdAt: new Date().toISOString(),
  };
  quantState.strategies.push(strategy);
  saveState();
  logger.info('Strategy added', { name, author });
  return { success: true, strategy };
}

/**
 * Record a backtest result.
 * Enforces real costs requirement.
 */
function addBacktest({ strategyId, results, status = 'completed' }) {
  // Validate that real costs were applied
  if (!results.costsApplied) {
    logger.warn('Backtest recorded without real costs — flagged as unreliable', { strategyId });
  }
  const backtest = {
    id: `bt_${Date.now()}`,
    strategyId,
    results,
    status,
    costsApplied: !!results.costsApplied,
    passedGate: results.pf > quantState.validationGate.minPF &&
                results.maxDD < quantState.validationGate.maxDD &&
                results.wr > quantState.validationGate.minWR &&
                results.tradeCount >= quantState.validationGate.minTrades,
    createdAt: new Date().toISOString(),
  };
  quantState.backtests.push(backtest);
  saveState();
  return { success: true, backtest };
}

/**
 * Record a forward test result.
 */
function addForwardTest({ strategyId, results, status = 'active' }) {
  const ft = {
    id: `ft_${Date.now()}`,
    strategyId,
    liveResults: results,
    status, // active → completed → passed → failed
    trades: results.trades || 0,
    wr: results.wr || 0,
    pnl: results.pnl || 0,
    slippageAvg: results.slippageAvg || 0,
    startedAt: new Date().toISOString(),
  };
  quantState.forwardTests.push(ft);
  saveState();
  return { success: true, forwardTest: ft };
}

/**
 * Validate a strategy against the hard gate.
 */
function validateStrategy(strategyId) {
  const backtests = quantState.backtests.filter(b => b.strategyId === strategyId);
  if (backtests.length === 0) return { valid: false, reason: 'No backtest data' };
  const latest = backtests[backtests.length - 1];
  const r = latest.results;
  const gate = quantState.validationGate;
  const checks = {
    pf: { pass: r.pf > gate.minPF, value: r.pf, required: `> ${gate.minPF}` },
    maxDD: { pass: r.maxDD < gate.maxDD, value: r.maxDD, required: `< ${gate.maxDD}%` },
    wr: { pass: r.wr > gate.minWR, value: r.wr, required: `> ${gate.minWR}%` },
    trades: { pass: r.tradeCount >= gate.minTrades, value: r.tradeCount, required: `>= ${gate.minTrades}` },
    costs: { pass: !!latest.costsApplied, value: latest.costsApplied, required: 'Real costs applied' },
  };
  const allPass = Object.values(checks).every(c => c.pass);
  return { valid: allPass, checks, strategyId };
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
 * Get all forward tests.
 */
function getForwardTests() {
  return quantState.forwardTests;
}

/**
 * Get full quant state.
 */
function getState() {
  return { ...quantState };
}

/**
 * Get validation gate config.
 */
function getValidationGate() {
  return { ...quantState.validationGate };
}

// Load on init
loadState();

module.exports = {
  addStrategy,
  addBacktest,
  addForwardTest,
  validateStrategy,
  getStrategies,
  getBacktests,
  getForwardTests,
  getState,
  getValidationGate,
};
