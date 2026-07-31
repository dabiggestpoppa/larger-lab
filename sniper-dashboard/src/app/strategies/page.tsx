'use client';

import { useEffect, useState } from 'react';
import { getStrategies, getEquityCurve, type StrategyRecord, type EquityCurve } from '@/lib/api';

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<{
    symmetry_trap: StrategyRecord[];
    p90_cascade: StrategyRecord[];
    all: StrategyRecord[];
  } | null>(null);
  const [equityCurves, setEquityCurves] = useState<Record<string, EquityCurve | null>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const s = await getStrategies();
      if (s) {
        setStrategies(s);
        // Load equity curves for primary pairs
        const stCurve = await getEquityCurve('symmetry_trap', 'EURUSD.PRO');
        const p90Curve = await getEquityCurve('p90_cascade', 'USDCHF.PRO');
        setEquityCurves({
          'symmetry_trap_EURUSD': stCurve,
          'p90_cascade_USDCHF': p90Curve,
        });
      }
      setLoading(false);
    }
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="text-dark-muted text-sm py-12 text-center">Loading strategy data...</div>;
  }

  if (!strategies) {
    return <div className="text-dark-muted text-sm py-12 text-center">No strategy data available. Start the API server.</div>;
  }

  const allStrat = strategies.all || [];
  const totalTrades = allStrat.reduce((s, r) => s + r.trades, 0);
  const totalWins = allStrat.reduce((s, r) => s + r.wins, 0);
  const combinedWR = totalTrades > 0 ? ((totalWins / totalTrades) * 100).toFixed(1) : '0.0';

  return (
    <div className="space-y-6">
      {/* Combined Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Trades" value={totalTrades.toString()} accent="blue" />
        <StatCard label="Combined WR" value={`${combinedWR}%`} accent="green" />
        <StatCard label="Strategies" value={(strategies.symmetry_trap.length + strategies.p90_cascade.length).toString()} accent="blue" />
        <StatCard label="Total Pips" value={allStrat.reduce((s, r) => s + r.pnl_pips, 0).toFixed(1)} accent="green" />
      </div>

      {/* Equity Curve Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <EquityChartCard title="Symmetry Trap — EURUSD" data={equityCurves['symmetry_trap_EURUSD']} />
        <EquityChartCard title="P90 CASCADE — USDCHF" data={equityCurves['p90_cascade_USDCHF']} />
      </div>

      {/* Strategy Breakdown Table */}
      <div className="bg-dark-card border border-dark-border rounded-lg">
        <div className="px-4 py-3 border-b border-dark-border">
          <h3 className="text-sm font-medium">Strategy Performance</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-dark-muted text-xs border-b border-dark-border">
                <th className="text-left px-4 py-2.5 font-medium">Strategy</th>
                <th className="text-left px-4 py-2.5 font-medium">Symbol</th>
                <th className="text-right px-4 py-2.5 font-medium">Trades</th>
                <th className="text-right px-4 py-2.5 font-medium">Wins</th>
                <th className="text-right px-4 py-2.5 font-medium">Losses</th>
                <th className="text-right px-4 py-2.5 font-medium">Win Rate</th>
                <th className="text-right px-4 py-2.5 font-medium">Pips</th>
                <th className="text-center px-4 py-2.5 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {allStrat.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-dark-muted">No strategy data available</td>
                </tr>
              ) : (
                allStrat.map((s, i) => (
                  <tr key={i} className="border-b border-dark-border/50 hover:bg-dark-border/30">
                    <td className="px-4 py-3 font-medium">{s.strategy.replace('_', ' ').toUpperCase()}</td>
                    <td className="px-4 py-3 text-dark-muted">{s.symbol}</td>
                    <td className="px-4 py-3 text-right font-mono">{s.trades}</td>
                    <td className="px-4 py-3 text-right font-mono text-dark-success">{s.wins}</td>
                    <td className="px-4 py-3 text-right font-mono text-dark-danger">{s.losses}</td>
                    <td className="px-4 py-3 text-right font-mono">
                      <span className={s.win_rate >= 80 ? 'text-dark-success' : s.win_rate >= 70 ? 'text-dark-warning' : 'text-dark-danger'}>
                        {s.win_rate.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono">
                      <span className={s.pnl_pips >= 0 ? 'text-dark-success' : 'text-dark-danger'}>
                        {s.pnl_pips.toFixed(1)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-xs px-2 py-0.5 rounded bg-dark-success/20 text-dark-success">LIVE</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: string; accent: 'blue' | 'green' | 'red' }) {
  const colors: Record<string, string> = { blue: 'text-dark-accent', green: 'text-dark-success', red: 'text-dark-danger' };
  return (
    <div className="bg-dark-card border border-dark-border rounded-lg p-4">
      <div className="text-[11px] text-dark-muted uppercase tracking-wider">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${colors[accent]}`}>{value}</div>
    </div>
  );
}

function EquityChartCard({ title, data }: { title: string; data: EquityCurve | null | undefined }) {
  if (!data || !data.curve || data.curve.length === 0) {
    return (
      <div className="bg-dark-card border border-dark-border rounded-lg">
        <div className="px-4 py-3 border-b border-dark-border">
          <h3 className="text-sm font-medium">{title}</h3>
        </div>
        <div className="p-8 flex items-center justify-center h-64">
          <p className="text-sm text-dark-muted">No equity curve data</p>
        </div>
      </div>
    );
  }

  const curve = data.curve;
  const maxVal = Math.max(...curve.map(d => d.p95));
  const minVal = Math.min(...curve.map(d => d.p5));
  const range = maxVal - minVal || 1;
  const w = 400;
  const h = 160;
  const pad = 10;

  const toY = (val: number) => h - pad - ((val - minVal) / range) * (h - pad * 2);
  const toX = (i: number) => pad + (i / Math.max(curve.length - 1, 1)) * (w - pad * 2);

  const makePath = (key: 'p5' | 'p25' | 'p50' | 'p75' | 'p95') =>
    curve.map((d, i) => `${i === 0 ? 'M' : 'L'} ${toX(i)} ${toY(d[key])}`).join(' ');

  const bandPath = (lo: 'p25' | 'p5', hi: 'p75' | 'p95') => {
    const loPoints = curve.map((d, i) => `${toX(i)} ${toY(d[lo])}`).join(' L ');
    const hiPoints = [...curve].reverse().map((d, i) => `${toX(curve.length - 1 - i)} ${toY(d[hi])}`).join(' L ');
    return `M ${loPoints} L ${hiPoints} Z`;
  };

  return (
    <div className="bg-dark-card border border-dark-border rounded-lg">
      <div className="px-4 py-3 border-b border-dark-border flex items-center justify-between">
        <h3 className="text-sm font-medium">{title}</h3>
        <div className="flex items-center gap-4 text-[10px] text-dark-muted">
          {data.stats && (
            <>
              <span>Med PnL: <span className="text-dark-success font-medium">${data.stats.median_pnl.toFixed(0)}</span></span>
              <span>MaxDD: <span className="text-dark-danger font-medium">${data.stats.max_dd.toFixed(0)}</span></span>
              <span>PF: <span className="text-dark-accent font-medium">{data.stats.pf.toFixed(1)}</span></span>
            </>
          )}
        </div>
      </div>
      <div className="p-4">
        <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-52">
          {/* Bands */}
          <path d={bandPath('p5', 'p95')} fill="rgba(59,130,246,0.08)" />
          <path d={bandPath('p25', 'p75')} fill="rgba(59,130,246,0.15)" />
          {/* Median line */}
          <path d={makePath('p50')} fill="none" stroke="#3b82f6" strokeWidth={2} />
          {/* Grid lines */}
          {[0, 0.5, 1].map(f => (
            <line key={f} x1={pad} y1={pad + f * (h - pad * 2)} x2={w - pad} y2={pad + f * (h - pad * 2)}
              stroke="#1e1e2e" strokeWidth={0.5} />
          ))}
        </svg>
      </div>
    </div>
  );
}
