'use client';

import { useEffect, useState } from 'react';
import { getOverview, type OverviewData } from '@/lib/api';

export default function OverviewPage() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function load() {
      const d = await getOverview();
      if (mounted) { setData(d); setLoading(false); }
    }
    load();
    const interval = setInterval(load, 30000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="text-dark-muted text-sm">Loading dashboard...</div>
          <div className="text-dark-muted text-xs mt-2">Connecting to API server on port 8090</div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="text-dark-muted text-sm">Connecting to API server...</div>
          <div className="text-dark-muted text-xs mt-2">Ensure api_server.py is running on port 8090</div>
        </div>
      </div>
    );
  }

  const { summary, strategy_live, alerts, tickers } = data;

  return (
    <div className="space-y-6">
      {/* Alerts Banner */}
      {alerts && alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((alert, i) => (
            <div
              key={i}
              className={`px-4 py-2.5 rounded-lg border text-sm ${
                alert.level === 'danger'
                  ? 'bg-dark-danger/10 border-dark-danger/30 text-dark-danger'
                  : 'bg-dark-warning/10 border-dark-warning/30 text-dark-warning'
              }`}
            >
              ⚠ {alert.message}
            </div>
          ))}
        </div>
      )}

      {/* Top Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Account Balance"
          value={`$${summary.account_balance.toLocaleString()}`}
          accent="blue"
        />
        <StatCard
          label="Equity"
          value={`$${summary.equity.toLocaleString()}`}
          accent="green"
        />
        <StatCard
          label="Daily P&L"
          value={`${summary.daily_pnl >= 0 ? '+' : ''}$${summary.daily_pnl.toFixed(2)}`}
          accent={summary.daily_pnl >= 0 ? 'green' : 'red'}
        />
        <StatCard
          label="Drawdown"
          value={`${summary.drawdown_pct.toFixed(2)}%`}
          accent="red"
        />
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Monthly P&L"
          value={`${summary.monthly_pnl >= 0 ? '+' : ''}$${summary.monthly_pnl.toFixed(2)}`}
          accent={summary.monthly_pnl >= 0 ? 'green' : 'red'}
        />
        <StatCard
          label="Active Trades"
          value={summary.active_trades.toString()}
          accent="blue"
        />
        <StatCard
          label="Win Rate (20)"
          value={`${summary.rolling_wr_20}%`}
          accent="green"
        />
        <StatCard
          label="Avg PES Score"
          value={summary.avg_pes_score.toFixed(2)}
          accent="blue"
        />
      </div>

      {/* Strategy Cards + Tickers */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <StrategyCard
          name="Symmetry Trap"
          symbol="EURUSD.PRO"
          engine="B"
          data={strategy_live.symmetry_trap}
        />
        <StrategyCard
          name="P90 CASCADE"
          symbol="GBPUSD.PRO"
          engine="A"
          data={strategy_live.p90_cascade}
        />

        {/* Live Tickers */}
        <div className="bg-dark-card border border-dark-border rounded-lg">
          <div className="px-4 py-3 border-b border-dark-border">
            <h3 className="text-sm font-medium">Live Tickers</h3>
          </div>
          <div className="p-4 space-y-3">
            {tickers && Object.entries(tickers).map(([sym, tick]) => (
              <TickerRow key={sym} symbol={sym} {...tick} />
            ))}
          </div>
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
      <div className={`text-2xl font-bold mt-1 ${colors[accent]}`}>{value}</div>
    </div>
  );
}

function StrategyCard({
  name,
  symbol,
  engine,
  data,
}: {
  name: string;
  symbol: string;
  engine: string;
  data: { wr: number; trades: number; status: string };
}) {
  return (
    <div className="bg-dark-card border border-dark-border rounded-lg">
      <div className="px-4 py-3 border-b border-dark-border">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium">{name}</h3>
            <div className="text-[10px] text-dark-muted">{symbol} | Engine {engine}</div>
          </div>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-dark-success/15 border border-dark-success/30">
            <span className="w-1.5 h-1.5 rounded-full bg-dark-success animate-pulse" />
            <span className="text-[10px] text-dark-success font-medium">{data.status}</span>
          </div>
        </div>
      </div>
      <div className="p-4">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <div className="text-[10px] text-dark-muted uppercase">Win Rate</div>
            <div className="text-lg font-bold text-dark-success">{data.wr}%</div>
          </div>
          <div>
            <div className="text-[10px] text-dark-muted uppercase">Trades</div>
            <div className="text-lg font-bold text-dark-primary">{data.trades}</div>
          </div>
          <div>
            <div className="text-[10px] text-dark-muted uppercase">Engine</div>
            <div className="text-lg font-bold text-dark-accent">{engine}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TickerRow({
  symbol,
  bid,
  ask,
  spread,
  change_pct,
}: {
  symbol: string;
  bid: number;
  ask: number;
  spread: number;
  change_pct: number;
}) {
  const isUp = change_pct >= 0;
  return (
    <div className="flex items-center justify-between py-2 px-3 rounded bg-dark-bg/50">
      <div>
        <div className="text-sm font-medium text-dark-primary">{symbol}</div>
        <div className="text-[10px] text-dark-muted">{spread} pip spread</div>
      </div>
      <div className="text-right">
        <div className="text-sm font-mono text-dark-primary">{bid.toFixed(5)}</div>
        <div className={`text-[10px] font-medium ${isUp ? 'text-dark-success' : 'text-dark-danger'}`}>
          {isUp ? '▲' : '▼'} {Math.abs(change_pct).toFixed(2)}%
        </div>
      </div>
    </div>
  );
}
