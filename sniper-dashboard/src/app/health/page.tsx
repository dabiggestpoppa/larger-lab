'use client';

import { useEffect, useState } from 'react';
import { getHealth, type HealthData } from '@/lib/api';

export default function HealthPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [countdown, setCountdown] = useState(30);

  async function loadHealth() {
    const data = await getHealth();
    if (data) setHealth(data);
  }

  useEffect(() => {
    loadHealth();
    const dataInterval = setInterval(loadHealth, 30000);
    const countdownInterval = setInterval(() => {
      setCountdown(prev => prev <= 1 ? 30 : prev - 1);
    }, 1000);
    return () => {
      clearInterval(dataInterval);
      clearInterval(countdownInterval);
    };
  }, []);

  if (!health) {
    return <div className="text-dark-muted text-sm py-12 text-center">Checking system health...</div>;
  }

  const overallHealthy = health.overall === 'healthy';

  return (
    <div className="space-y-6">
      {/* Status Banner */}
      <div className={`px-4 py-3 rounded-lg border ${
        overallHealthy
          ? 'bg-dark-success/10 border-dark-success/30'
          : 'bg-dark-warning/10 border-dark-warning/30'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${overallHealthy ? 'bg-dark-success animate-pulse' : 'bg-dark-warning'}`} />
            <span className={`text-sm font-medium ${overallHealthy ? 'text-dark-success' : 'text-dark-warning'}`}>
              {overallHealthy ? 'All Systems Operational' : 'Degraded — Check Components'}
            </span>
          </div>
          <div className="text-xs text-dark-muted">
            Auto-refresh in {countdown}s
          </div>
        </div>
      </div>

      {/* Executor Status */}
      <div className="bg-dark-card border border-dark-border rounded-lg">
        <div className="px-4 py-3 border-b border-dark-border">
          <h3 className="text-sm font-medium">Executor Status</h3>
        </div>
        <div className="p-4 space-y-3">
          {health.executors.map((ex, i) => (
            <div key={i} className="flex items-center justify-between py-3 px-4 rounded-lg bg-dark-bg/50 border border-dark-border/50">
              <div className="flex items-center gap-3">
                <span className={`w-2.5 h-2.5 rounded-full ${
                  ex.status === 'online' ? 'bg-dark-success' : ex.status === 'stale' ? 'bg-dark-warning' : 'bg-dark-danger'
                }`} />
                <div>
                  <div className="text-sm font-medium">{ex.name}</div>
                  <div className="text-[10px] text-dark-muted">{ex.symbol} | {ex.file}</div>
                </div>
              </div>
              <div className="text-right">
                <span className={`text-xs px-2 py-0.5 rounded ${
                  ex.status === 'online'
                    ? 'bg-dark-success/20 text-dark-success'
                    : 'bg-dark-danger/20 text-dark-danger'
                }`}>
                  {ex.status.toUpperCase()}
                </span>
                <div className="text-[10px] text-dark-muted mt-1">
                  {new Date(ex.last_check).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* MT5 Connection */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-dark-card border border-dark-border rounded-lg">
          <div className="px-4 py-3 border-b border-dark-border">
            <h3 className="text-sm font-medium">MT5 Connection</h3>
          </div>
          <div className="p-4">
            <div className="flex items-center gap-3 mb-4">
              <span className={`w-3 h-3 rounded-full ${
                health.mt5_connection === 'connected' ? 'bg-dark-success' : 'bg-dark-warning'
              }`} />
              <span className={`text-sm font-medium ${
                health.mt5_connection === 'connected' ? 'text-dark-success' : 'text-dark-warning'
              }`}>
                {health.mt5_connection === 'connected' ? 'Connected' : health.mt5_connection}
              </span>
            </div>
            <div className="space-y-2 text-xs text-dark-muted">
              <div className="flex justify-between">
                <span>Terminal</span>
                <span className="text-dark-primary">MetaTrader 5</span>
              </div>
              <div className="flex justify-between">
                <span>Broker</span>
                <span className="text-dark-primary">Pepperstone</span>
              </div>
              <div className="flex justify-between">
                <span>Account</span>
                <span className="text-dark-primary">***001</span>
              </div>
              <div className="flex justify-between">
                <span>Leverage</span>
                <span className="text-dark-primary">1:30</span>
              </div>
            </div>
          </div>
        </div>

        {/* API Server */}
        <div className="bg-dark-card border border-dark-border rounded-lg">
          <div className="px-4 py-3 border-b border-dark-border">
            <h3 className="text-sm font-medium">API Server</h3>
          </div>
          <div className="p-4">
            <div className="flex items-center gap-3 mb-4">
              <span className="w-3 h-3 rounded-full bg-dark-success" />
              <span className="text-sm font-medium text-dark-success">Running</span>
            </div>
            <div className="space-y-2 text-xs text-dark-muted">
              <div className="flex justify-between">
                <span>Port</span>
                <span className="text-dark-primary">8090</span>
              </div>
              <div className="flex justify-between">
                <span>Version</span>
                <span className="text-dark-primary">v2.0</span>
              </div>
              <div className="flex justify-between">
                <span>Last Log</span>
                <span className="text-dark-primary">
                  {health.last_log ? health.last_log.file : 'No logs'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Log Freshness</span>
                <span className={health.last_log?.fresh ? 'text-dark-success' : 'text-dark-warning'}>
                  {health.last_log ? `${health.last_log.age_seconds}s ago` : 'Unknown'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Live Logs Preview */}
      <div className="bg-dark-card border border-dark-border rounded-lg">
        <div className="px-4 py-3 border-b border-dark-border">
          <h3 className="text-sm font-medium">Live Log Activity</h3>
        </div>
        <div className="p-4">
          {health.last_log ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${health.last_log.fresh ? 'bg-dark-success' : 'bg-dark-warning'}`} />
                <span className="text-sm text-dark-primary">{health.last_log.file}</span>
              </div>
              <span className={`text-xs ${health.last_log.fresh ? 'text-dark-success' : 'text-dark-warning'}`}>
                {health.last_log.fresh ? 'Fresh' : 'Stale'} — {health.last_log.age_seconds}s ago
              </span>
            </div>
          ) : (
            <p className="text-dark-muted text-sm">No live log data</p>
          )}
        </div>
      </div>
    </div>
  );
}
