"use client";

import { useEffect, useState, useCallback } from "react";
import { Activity, Cpu, Database, Zap, TrendingUp, Clock } from "lucide-react";
import { api, MetricsSummary } from "../lib/api";
import { useWebSocket } from "../lib/useWebSocket";
import { SkeletonPanel } from "./SkeletonLoader";
import { ErrorBanner } from "./ErrorBanner";
import { useToast } from "./Toast";

function StatCard({ label, value, icon: Icon, color, sub }: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  sub?: string;
}) {
  return (
    <div className="bg-[#111118] border border-[#27272a] rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
      </div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      {sub && <div className="text-xs text-gray-600 mt-1">{sub}</div>}
    </div>
  );
}

function HealthBar({ value, label }: { value: number; label: string }) {
  const pct = Math.round(value * 100);
  const color = pct > 70 ? "bg-green-500" : pct > 40 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-gray-400 w-24 truncate">{label}</span>
      <div className="flex-1 h-2 bg-[#1a1a24] rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-500 w-10 text-right">{pct}%</span>
    </div>
  );
}

export function MetricsPanel() {
  const wsData = useWebSocket<MetricsSummary>("/ws/metrics");
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { addToast } = useToast();

  const fetchMetrics = useCallback(async () => {
    try {
      const m = await api.getMetrics();
      setMetrics(m);
      setError(null);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Backend unreachable";
      setError(msg);
      addToast({ type: "error", title: "Metrics Error", message: msg });
    }
  }, [addToast]);

  // Fallback polling if WebSocket not available
  useEffect(() => {
    if (wsData.data) {
      setMetrics(wsData.data);
      return;
    }
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, [wsData.data, fetchMetrics]);

  // Notify on reconnect
  useEffect(() => {
    if (wsData.status === "connected" && wsData.reconnectCount > 0) {
      addToast({ type: "success", title: "Reconnected", message: "Live metrics restored" });
    }
  }, [wsData.status, wsData.reconnectCount, addToast]);

  if (error && !metrics) {
    return (
      <ErrorBanner
        title="Metrics Unavailable"
        message={error}
        severity="error"
        onRetry={fetchMetrics}
        details={wsData.lastError ?? undefined}
      />
    );
  }

  if (!metrics) {
    return <SkeletonPanel />;
  }

  const m = metrics;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">System Metrics</h2>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${
            wsData.status === "connected" ? "bg-green-500 animate-pulse" :
            wsData.status === "connecting" ? "bg-yellow-500 animate-pulse" : "bg-red-500"
          }`} />
          <span className="text-xs text-gray-600">
            {wsData.status === "connected" ? "Live" :
             wsData.status === "connecting" ? "Connecting..." :
             wsData.reconnectCount > 0 ? `Reconnecting (${wsData.reconnectCount})` : "Offline"}
          </span>
          {wsData.lastMessageAt && wsData.status === "connected" && (
            <span className="text-xs text-gray-700">
              {wsData.lastMessageAt.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Top Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          label="Event Rate"
          value={`${m.events.rate_per_sec.toFixed(1)}/s`}
          icon={Activity}
          color="text-blue-400"
          sub={`${m.events.total_count.toLocaleString()} total`}
        />
        <StatCard
          label="Observers"
          value={m.observers.count}
          icon={Cpu}
          color="text-purple-400"
          sub={`Avg health: ${(m.observers.avg_health * 100).toFixed(0)}%`}
        />
        <StatCard
          label="Memory"
          value={formatBytes(m.memory.total_size_bytes)}
          icon={Database}
          color="text-cyan-400"
          sub={`${m.memory.total_entries} entries`}
        />
        <StatCard
          label="Entropy"
          value={`${m.entropy.usage_pct.toFixed(1)}%`}
          icon={Zap}
          color={m.entropy.usage_pct > 80 ? "text-red-400" : "text-amber-400"}
          sub={`${formatBytes(m.entropy.remaining)} remaining`}
        />
      </div>

      {/* Latency */}
      <div className="bg-[#111118] border border-[#27272a] rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <Clock className="w-4 h-4 text-gray-500" />
          <span className="text-xs text-gray-500 uppercase tracking-wider">Event Latency</span>
        </div>
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-lg font-bold text-gray-200">{m.events.latency.avg_ms.toFixed(1)}</div>
            <div className="text-xs text-gray-600">Avg (ms)</div>
          </div>
          <div>
            <div className="text-lg font-bold text-yellow-400">{m.events.latency.p95_ms.toFixed(1)}</div>
            <div className="text-xs text-gray-600">P95 (ms)</div>
          </div>
          <div>
            <div className="text-lg font-bold text-red-400">{m.events.latency.p99_ms.toFixed(1)}</div>
            <div className="text-xs text-gray-600">P99 (ms)</div>
          </div>
          <div>
            <div className="text-lg font-bold text-gray-400">{m.events.latency.count}</div>
            <div className="text-xs text-gray-600">Samples</div>
          </div>
        </div>
      </div>

      {/* Observer Health */}
      {Object.keys(m.observers.by_id).length > 0 && (
        <div className="bg-[#111118] border border-[#27272a] rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-gray-500" />
            <span className="text-xs text-gray-500 uppercase tracking-wider">Observer Health</span>
          </div>
          <div className="space-y-2">
            {Object.entries(m.observers.by_id).map(([id, obs]) => (
              <HealthBar key={id} value={obs.health} label={id} />
            ))}
          </div>
        </div>
      )}

      {/* Memory Layers */}
      {Object.keys(m.memory.layers).length > 0 && (
        <div className="bg-[#111118] border border-[#27272a] rounded-lg p-4">
          <span className="text-xs text-gray-500 uppercase tracking-wider">Memory Layers</span>
          <div className="grid grid-cols-3 gap-3 mt-3">
            {Object.entries(m.memory.layers).map(([layer, info]) => (
              <div key={layer} className="bg-[#1a1a24] rounded p-3 text-center">
                <div className="text-sm font-bold text-gray-200">{layer}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {info.entries} entries · {formatBytes(info.size_bytes)}
                </div>
                {info.compression_ratio < 1.0 && (
                  <div className="text-xs text-cyan-400 mt-1">
                    {(info.compression_ratio * 100).toFixed(0)}% compressed
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Event Types */}
      {Object.keys(m.events.by_type).length > 0 && (
        <div className="bg-[#111118] border border-[#27272a] rounded-lg p-4">
          <span className="text-xs text-gray-500 uppercase tracking-wider">Events by Type</span>
          <div className="flex flex-wrap gap-2 mt-3">
            {Object.entries(m.events.by_type).slice(0, 12).map(([type, count]) => (
              <span key={type} className="bg-[#1a1a24] text-xs text-gray-400 px-2 py-1 rounded">
                {type}: <span className="text-gray-200 font-medium">{count}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}
