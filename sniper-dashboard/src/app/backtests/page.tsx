'use client';

import { useEffect, useState } from 'react';
import { getBacktests, type BacktestData, type AssetResult } from '@/lib/api';

export default function BacktestsPage() {
  const [data, setData] = useState<BacktestData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function load() {
      const d = await getBacktests();
      if (mounted) { setData(d); setLoading(false); }
    }
    load();
    const interval = setInterval(load, 60000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-dark-muted text-sm">Loading backtest data...</div>
      </div>
    );
  }

  if (!data || !data.assets || data.assets.length === 0) {
    return (
      <div className="text-dark-muted text-sm py-12 text-center">
        No backtest data available. Start the API server.
      </div>
    );
  }

  const { assets } = data;
  const sorted = [...assets].sort((a, b) => a.symbol.localeCompare(b.symbol));
  const avgWR = assets.filter(a => a.win_rate).reduce((s, a) => s + (a.win_rate || 0), 0) / Math.max(assets.filter(a => a.win_rate).length, 1);
  const avgPF = assets.reduce((s, a) => s + a.pf, 0) / assets.length;
  const avgRuin = assets.reduce((s, a) => s + a.ruin_prob, 0) / assets.length;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Assets Tested" value={assets.length.toString()} accent="blue" />
        <StatCard label="Avg Win Rate" value={`${avgWR.toFixed(1)}%`} accent="green" />
        <StatCard label="Avg Profit Factor" value={avgPF.toFixed(2)} accent="green" />
        <StatCard label="Avg Ruin Prob" value={`${avgRuin.toFixed(2)}%`} accent={avgRuin < 1 ? 'green' : 'red'} />
      </div>

      <div className="bg-dark-card border border-dark-border rounded-lg">
        <div className="px-4 py-3 border-b border-dark-border flex items-center justify-between">
          <h3 className="text-sm font-medium">Per-Asset Backtest Results</h3>
          <span className="text-xs text-dark-muted">{assets.length} assets</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-dark-muted text-xs border-b border-dark-border">
                <th className="text-left px-4 py-2.5 font-medium">Asset</th>
                <th className="text-right px-4 py-2.5 font-medium">Trades</th>
                <th className="text-right px-4 py-2.5 font-medium">Win Rate</th>
                <th className="text-right px-4 py-2.5 font-medium">PF</th>
                <th className="text-right px-4 py-2.5 font-medium">Sharpe</th>
                <th className="text-right px-4 py-2.5 font-medium">Max DD</th>
                <th className="text-right px-4 py-2.5 font-medium">Max DD %</th>
                <th className="text-right px-4 py-2.5 font-medium">Ruin %</th>
                <th className="text-right px-4 py-2.5 font-medium">Med PnL</th>
                <th className="text-center px-4 py-2.5 font-medium">Report</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((asset) => (
                <tr key={asset.symbol} className="border-b border-dark-border/50 hover:bg-dark-border/30">
                  <td className="px-4 py-3 font-medium">{asset.symbol}</td>
                  <td className="px-4 py-3 text-right font-mono">{asset.trades}</td>
                  <td className="px-4 py-3 text-right font-mono">
                    {asset.win_rate !== null ? (
                      <span className={asset.win_rate >= 85 ? 'text-dark-success' : asset.win_rate >= 75 ? 'text-dark-warning' : 'text-dark-danger'}>
                        {asset.win_rate.toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-dark-muted">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    <span className={asset.pf >= 10 ? 'text-dark-success' : asset.pf >= 5 ? 'text-dark-warning' : 'text-dark-danger'}>
                      {asset.pf.toFixed(2)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {asset.sharpe !== null ? asset.sharpe.toFixed(2) : <span className="text-dark-muted">—</span>}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-dark-danger">${asset.max_dd.toFixed(0)}</td>
                  <td className="px-4 py-3 text-right font-mono text-dark-danger">{(asset.max_dd_pct * 100).toFixed(2)}%</td>
                  <td className="px-4 py-3 text-right font-mono">
                    <span className={asset.ruin_prob === 0 ? 'text-dark-success' : 'text-dark-warning'}>
                      {asset.ruin_prob.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-dark-success">${asset.median_pnl.toFixed(0)}</td>
                  <td className="px-4 py-3 text-center">
                    {asset.has_report ? (
                      <a
                        href={`/backtests/report/${asset.symbol}`}
                        className="text-xs px-2 py-0.5 rounded bg-dark-accent/15 text-dark-accent hover:bg-dark-accent/25 transition-colors"
                      >
                        View
                      </a>
                    ) : (
                      <span className="text-dark-muted text-xs">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: string; accent: 'blue' | 'green' | 'red' }) {
  const colors: Record<string, string> = {
    blue: 'text-dark-accent',
    green: 'text-dark-success',
    red: 'text-dark-danger',
  };
  return (
    <div className="bg-dark-card border border-dark-border rounded-lg p-4">
      <div className="text-[11px] text-dark-muted uppercase tracking-wider">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${colors[accent]}`}>{value}</div>
    </div>
  );
}
