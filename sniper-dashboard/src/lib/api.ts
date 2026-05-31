/**
 * CEREBUS Dashboard API Client
 * Connects to FastAPI server at localhost:8090
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8090';

async function fetchApi(path: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
    return res.json();
  } catch (error) {
    console.error(`API fetch error: ${path}`, error);
    return null;
  }
}

// ── TYPES ──────────────────────────────────────────────────

export interface OverviewData {
  generated_at: string;
  summary: {
    total_firms_tracked: number;
    active_deployments: number;
    total_capital_deployed: number;
    avg_pes_score: number;
    crossover_proximity_pct: number;
    account_balance: number;
    equity: number;
    daily_pnl: number;
    weekly_pnl: number;
    monthly_pnl: number;
    drawdown_pct: number;
    active_trades: number;
    rolling_wr_20: number;
    rolling_wr_50: number;
  };
  strategy_live: {
    symmetry_trap: { wr: number; trades: number; status: string };
    p90_cascade: { wr: number; trades: number; status: string };
  };
  alerts: { level: string; message: string }[];
  alerts_count: number;
  tickers: Record<string, { bid: number; ask: number; spread: number; change_pct: number }>;
}

export interface StrategyData {
  generated_at: string;
  symmetry_trap: StrategyRecord[];
  p90_cascade: StrategyRecord[];
  all: StrategyRecord[];
}

export interface StrategyRecord {
  strategy: string;
  symbol: string;
  trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  pnl_pips: number;
  report_file: string;
  timestamp: string;
}

export interface TradeData {
  trades: TradeRecord[];
  count: number;
  stats: {
    total_pnl: number;
    win_rate: number;
    wins: number;
    losses: number;
    avg_win: number;
    avg_loss: number;
  };
}

export interface TradeRecord {
  id: string;
  symbol: string;
  strategy: string;
  entry_time: string;
  exit_time: string;
  pnl: number;
  pips: number;
  duration: string;
  type: string;
}

export interface AssetResult {
  symbol: string;
  trades: number;
  win_rate: number | null;
  pf: number;
  sharpe: number | null;
  max_dd: number;
  max_dd_pct: number;
  ruin_prob: number;
  median_pnl: number;
  has_report: boolean;
  report_file: string;
}

export interface BacktestData {
  generated_at: string;
  assets: AssetResult[];
  count: number;
}

export interface EquityCurve {
  symbol: string;
  curve: { trade: number; p5: number; p25: number; p50: number; p75: number; p95: number }[];
  stats: {
    median_pnl: number;
    mean_pnl: number;
    max_dd: number;
    ruin_prob: number;
    pf: number;
  };
}

export interface HealthData {
  generated_at: string;
  executors: { name: string; file: string; symbol: string; status: string; last_check: string }[];
  mt5_connection: string;
  last_log: { file: string; age_seconds: number; fresh: boolean } | null;
  overall: string;
}

// ── API FUNCTIONS ──────────────────────────────────────────

export async function getOverview(): Promise<OverviewData | null> {
  return fetchApi('/api/overview');
}

export async function getStrategies(): Promise<StrategyData | null> {
  return fetchApi('/api/strategies');
}

export async function getEquityCurve(strategy: string, symbol: string): Promise<EquityCurve | null> {
  return fetchApi(`/api/strategies/${strategy}/equity?symbol=${symbol}`);
}

export async function getTrades(strategy?: string, symbol?: string, limit?: number): Promise<TradeData | null> {
  let path = `/api/trades?limit=${limit || 50}`;
  if (strategy) path += `&strategy=${encodeURIComponent(strategy)}`;
  if (symbol) path += `&symbol=${encodeURIComponent(symbol)}`;
  return fetchApi(path);
}

export async function getBacktests(): Promise<BacktestData | null> {
  return fetchApi('/api/backtests');
}

export async function getBacktestReport(symbol: string): Promise<{ symbol: string; content: string } | null> {
  return fetchApi(`/api/backtests/report/${symbol}`);
}

export async function getHealth(): Promise<HealthData | null> {
  return fetchApi('/api/health/live');
}

// Legacy sniper endpoints
export async function getDeploymentMatrix() {
  return fetchApi('/api/matrix');
}

export async function getActiveDeployments() {
  const data = await fetchApi('/api/deployments/active-full');
  return data?.deployments || [];
}

export async function getLatestPES() {
  const data = await fetchApi('/api/pes/latest');
  return data?.snapshots || [];
}
