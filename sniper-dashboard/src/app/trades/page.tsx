'use client';

import { useEffect, useState } from 'react';
import { getTrades, type TradeRecord, type TradeData } from '@/lib/api';

export default function TradesPage() {
  const [tradeData, setTradeData] = useState<TradeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [strategyFilter, setStrategyFilter] = useState('');
  const [symbolFilter, setSymbolFilter] = useState('');

  async function loadData() {
    const data = await getTrades(
      strategyFilter || undefined,
      symbolFilter || undefined,
      100
    );
    if (data) setTradeData(data);
    setLoading(false);
  }

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [strategyFilter, symbolFilter]);

  if (loading) {
    return <div className="text-dark-muted text-sm py-12 text-center">Loading trade data...</div>;
  }

  if (!tradeData) {
    return <div className="text-dark-muted text-sm py-12 text-center">No trade data available. Start the API server.</div>;
  }

  const { trades, stats } = tradeData;

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard label="Total P&L" value={`${stats.total_pnl >= 0 ? '+' : ''}$${stats.total_pnl.toFixed(2)}`} accent={stats.total_pnl >= 0 ? 'green' : 'red'} />
        <StatCard label="Win Rate" value={`${stats.win_rate}%`} accent={stats.win_rate >= 80 ? 'green' : stats.win_rate >= 60 ? 'amber' : 'red'} />
        <StatCard label="Wins" value={stats.wins.toString()} accent="green" />
        <StatCard label="Losses" value={stats.losses.toString()} accent="red" />
        <StatCard label="Avg Win" value={`+$${stats.avg_win.toFixed(2)}`} accent="green" />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div>
          <label className="text-[10px] text-dark-muted uppercase tracking-wider block mb-1">Strategy</label>
          <select
            value={strategyFilter}
            onChange={e => setStrategyFilter(e.target.value)}
            className="bg-dark-card border border-dark-border rounded px-3 py-1.5 text-sm text-dark-primary focus:outline-none focus:border-dark-accent"
          >
            <option value="">All</option>
            <option value="symmetry">Symmetry Trap</option>
            <option value="p90">P90 CASCADE</option>
            <option value="dmr">DMR</option>
          </select>
        </div>
        <div>
          <label className="text-[10px] text-dark-muted uppercase tracking-wider block mb-1">Symbol</label>
          <select
            value={symbolFilter}
            onChange={e => setSymbolFilter(e.target.value)}
            className="bg-dark-card border border-dark-border rounded px-3 py-1.5 text-sm text-dark-primary focus:outline-none focus:border-dark-accent"
          >
            <option value="">All</option>
            <option value="EURUSD">EURUSD</option>
            <option value="USDCHF">USDCHF</option>
            <option value="GBPUSD">GBPUSD</option>
          </select>
        </div>
        <div className="flex-1" />
        <div className="text-xs text-dark-muted">
          {trades.length} trades shown
        </div>
      </div>

      {/* Trade Table */}
      <div className="bg-dark-card border border-dark-border rounded-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-dark-muted text-xs border-b border-dark-border">
                <th className="text-left px-4 py-2.5 font-medium">Symbol</th>
                <th className="text-left px-4 py-2.5 font-medium">Strategy</th>
                <th className="text-left px-4 py-2.5 font-medium">Entry</th>
                <th className="text-left px-4 py-2.5 font-medium">Exit</th>
                <th className="text-right px-4 py-2.5 font-medium">P&L</th>
                <th className="text-right px-4 py-2.5 font-medium">Pips</th>
                <th className="text-left px-4 py-2.5 font-medium">Type</th>
              </tr>
            </thead>
            <tbody>
              {trades.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-dark-muted">No trades found</td>
                </tr>
              ) : (
                trades.map((t, i) => (
                  <TradeRow key={t.id || i} trade={t} />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: string; accent: 'blue' | 'green' | 'red' | 'amber' }) {
  const colors: Record<string, string> = {
    blue: 'text-dark-accent',
    green: 'text-dark-success',
    red: 'text-dark-danger',
    amber: 'text-dark-warning',
  };
  return (
    <div className="bg-dark-card border border-dark-border rounded-lg p-4">
      <div className="text-[11px] text-dark-muted uppercase tracking-wider">{label}</div>
      <div className={`text-xl font-bold mt-1 ${colors[accent]}`}>{value}</div>
    </div>
  );
}

function TradeRow({ trade }: { trade: TradeRecord }) {
  const pnlColor = trade.pnl > 0 ? 'text-dark-success' : trade.pnl < 0 ? 'text-dark-danger' : 'text-dark-muted';
  return (
    <tr className="border-b border-dark-border/50 hover:bg-dark-border/30">
      <td className="px-4 py-2.5 font-medium">{trade.symbol}</td>
      <td className="px-4 py-2.5">
        <span className="text-xs px-2 py-0.5 rounded bg-dark-accent/15 text-dark-accent">
          {trade.strategy}
        </span>
      </td>
      <td className="px-4 py-2.5 text-dark-muted text-xs font-mono">{trade.entry_time || '—'}</td>
      <td className="px-4 py-2.5 text-dark-muted text-xs font-mono">{trade.exit_time || '—'}</td>
      <td className={`px-4 py-2.5 text-right font-mono font-medium ${pnlColor}`}>
        {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
      </td>
      <td className={`px-4 py-2.5 text-right font-mono ${pnlColor}`}>
        {trade.pips >= 0 ? '+' : ''}{trade.pips.toFixed(1)}
      </td>
      <td className="px-4 py-2.5 text-dark-muted text-xs">{trade.type || '—'}</td>
    </tr>
  );
}
