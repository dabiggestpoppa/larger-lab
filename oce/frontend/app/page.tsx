"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { MetricsPanel } from "./components/MetricsPanel";
import { TraceView } from "./components/TraceView";
import { AlertPanel } from "./components/AlertPanel";
import { SystemMap } from "./components/SystemMap";
import { QuickStat } from "./components/QuickStat";
import { api, DashboardData } from "./lib/api";
import { SkeletonCard } from "./components/SkeletonLoader";
import { ErrorBanner } from "./components/ErrorBanner";
import { useToast } from "./components/Toast";
import {
  Activity, GitBranch, Bell, Network, Shield, Cpu, Database, Zap,
  Radio, AlertTriangle, XCircle, MessageSquare, ChevronRight,
} from "lucide-react";

function StatusBadge({ status }: { status: "healthy" | "degraded" | "critical" }) {
  const config = {
    healthy: { color: "bg-green-500/10 text-green-400 border-green-500/20", label: "Healthy" },
    degraded: { color: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20", label: "Degraded" },
    critical: { color: "bg-red-500/10 text-red-400 border-red-500/20", label: "Critical" },
  }[status];
  return (
    <span className={`text-xs px-2 py-1 rounded-full border font-medium ${config.color}`}>
      {config.label}
    </span>
  );
}

function NavItem({ icon: Icon, label, href, badge }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  href: string;
  badge?: number;
}) {
  const [isActive, setIsActive] = useState(false);
  useEffect(() => {
    const path = window.location.pathname;
    setIsActive(path === href || (href === "/" && path === "/"));
  }, [href]);

  return (
    <Link
      href={href}
      className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors ${
        isActive
          ? "bg-indigo-600/10 text-indigo-400"
          : "text-gray-400 hover:text-gray-200 hover:bg-[#1a1a24]"
      }`}
    >
      <Icon className="w-4 h-4" />
      <span>{label}</span>
      {badge !== undefined && badge > 0 && (
        <span className="bg-red-500/20 text-red-400 text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
          {badge}
        </span>
      )}
    </Link>
  );
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export default function Home() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedStat, setSelectedStat] = useState<string | null>(null);
  const { addToast } = useToast();

  const loadDashboard = useCallback(async () => {
    try {
      const d = await api.getDashboard();
      setDashboard(d);
      setLoadError(null);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to load dashboard";
      setLoadError(msg);
    }
  }, []);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let pollInterval: ReturnType<typeof setInterval>;

    try {
      ws = new WebSocket("ws://localhost:8000/ws/metrics");
      ws.onopen = () => setWsStatus("connected");
      ws.onclose = () => {
        setWsStatus("disconnected");
        loadDashboard();
        pollInterval = setInterval(loadDashboard, 5000);
      };
      ws.onerror = () => ws?.close();
    } catch {
      setWsStatus("disconnected");
      loadDashboard();
      pollInterval = setInterval(loadDashboard, 5000);
    }

    return () => {
      ws?.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [loadDashboard]);

  const systemHealth: "healthy" | "degraded" | "critical" = (() => {
    if (!dashboard) return "healthy";
    const criticalAlerts = dashboard.alerts.active.filter(
      (a) => a.severity === "critical" && a.state === "firing"
    ).length;
    const avgHealth = dashboard.metrics.observers.avg_health;
    if (criticalAlerts > 0 || avgHealth < 0.3) return "critical";
    if (avgHealth < 0.7 || dashboard.alerts.stats.active_firing > 2) return "degraded";
    return "healthy";
  })();

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-[#27272a] bg-[#0a0a0f] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-white tracking-wide">OCE</h1>
              <p className="text-[10px] text-gray-600 -mt-0.5">Operator Continuity Engine</p>
            </div>
          </Link>
          <nav className="flex items-center gap-1">
            <NavItem icon={Activity} label="Overview" href="/" />
            <NavItem icon={GitBranch} label="Traces" href="/observability" />
            <NavItem icon={Bell} label="Alerts" href="/observability" badge={dashboard?.alerts.stats.active_firing} />
            <NavItem icon={Network} label="Topology" href="/observability" />
            <NavItem icon={Zap} label="Execution" href="/execution" />
            <NavItem icon={MessageSquare} label="Command" href="/command-center" />
          </nav>
          <div className="flex items-center gap-3">
            <StatusBadge status={systemHealth} />
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${
                wsStatus === "connected" ? "bg-green-500 animate-pulse" :
                wsStatus === "connecting" ? "bg-yellow-500 animate-pulse" : "bg-red-500"
              }`} />
              <span className="text-xs text-gray-500">
                {wsStatus === "connected" ? "Live" : wsStatus === "connecting" ? "Connecting" : "Offline"}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {loadError && !dashboard && (
          <ErrorBanner title="Dashboard Unavailable" message={loadError} severity="error" onRetry={loadDashboard} />
        )}

        {systemHealth !== "healthy" && dashboard && (
          <div className={`rounded-lg border p-4 flex items-center gap-3 ${
            systemHealth === "critical" ? "bg-red-900/10 border-red-900/30" : "bg-yellow-900/10 border-yellow-900/30"
          }`}>
            {systemHealth === "critical" ? (
              <XCircle className="w-5 h-5 text-red-400 shrink-0" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0" />
            )}
            <div className="flex-1">
              <p className={`text-sm font-medium ${systemHealth === "critical" ? "text-red-400" : "text-yellow-400"}`}>
                {systemHealth === "critical" ? "System health critical — immediate attention required" : "System health degraded — review active alerts"}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">
                {dashboard.alerts.active.filter((a) => a.state === "firing").length} active alerts
                {` · ${(dashboard.metrics.observers.avg_health * 100).toFixed(0)}% avg observer health`}
              </p>
            </div>
            <Link href="/observability" className="text-xs px-3 py-1.5 rounded-md bg-white/5 hover:bg-white/10 text-gray-400 hover:text-gray-200 transition-colors flex items-center gap-1">
              View Alerts <ChevronRight className="w-3 h-3" />
            </Link>
            <button onClick={loadDashboard} className="text-xs px-3 py-1.5 rounded-md bg-white/5 hover:bg-white/10 text-gray-400 hover:text-gray-200 transition-colors">
              Refresh
            </button>
          </div>
        )}

        {/* Quick Stats — Clickable */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">System Overview</h2>
            <span className="text-xs text-gray-600">Click any card for details</span>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {dashboard ? (
              <>
                <QuickStat label="Event Rate" value={`${dashboard.metrics.events.rate_per_sec.toFixed(1)}/s`} subtitle={`${dashboard.metrics.events.total_count.toLocaleString()} total`} icon={Activity} color="text-blue-400" onClick={() => setSelectedStat(selectedStat === "events" ? null : "events")} />
                <QuickStat label="Observers" value={String(dashboard.metrics.observers.count)} subtitle={`Avg health: ${(dashboard.metrics.observers.avg_health * 100).toFixed(0)}%`} icon={Cpu} color="text-purple-400" trend={dashboard.metrics.observers.avg_health > 0.7 ? "stable" : "down"} onClick={() => setSelectedStat(selectedStat === "observers" ? null : "observers")} />
                <QuickStat label="Memory" value={formatBytes(dashboard.metrics.memory.total_size_bytes)} subtitle={`${dashboard.metrics.memory.total_entries} entries`} icon={Database} color="text-cyan-400" onClick={() => setSelectedStat(selectedStat === "memory" ? null : "memory")} />
                <QuickStat label="Entropy" value={`${dashboard.metrics.entropy.usage_pct.toFixed(1)}%`} subtitle={`${formatBytes(dashboard.metrics.entropy.remaining)} remaining`} icon={Zap} color={dashboard.metrics.entropy.usage_pct > 80 ? "text-red-400" : "text-amber-400"} trend={dashboard.metrics.entropy.usage_pct > 80 ? "up" : "stable"} onClick={() => setSelectedStat(selectedStat === "entropy" ? null : "entropy")} />
              </>
            ) : (
              <><SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard /></>
            )}
          </div>
        </div>

        {/* Drill-down detail panel */}
        {selectedStat && dashboard && (
          <div className="bg-[#111118] border border-indigo-500/20 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-indigo-400 capitalize">{selectedStat} Details</h3>
              <button onClick={() => setSelectedStat(null)} className="text-xs text-gray-500 hover:text-gray-300">✕ Close</button>
            </div>
            {selectedStat === "events" && (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="bg-[#1a1a24] rounded p-3"><div className="text-xs text-gray-500">Avg Latency</div><div className="text-lg font-bold text-white">{dashboard.metrics.events.latency.avg_ms.toFixed(1)}ms</div></div>
                <div className="bg-[#1a1a24] rounded p-3"><div className="text-xs text-gray-500">P95</div><div className="text-lg font-bold text-yellow-400">{dashboard.metrics.events.latency.p95_ms.toFixed(1)}ms</div></div>
                <div className="bg-[#1a1a24] rounded p-3"><div className="text-xs text-gray-500">P99</div><div className="text-lg font-bold text-red-400">{dashboard.metrics.events.latency.p99_ms.toFixed(1)}ms</div></div>
                <div className="bg-[#1a1a24] rounded p-3"><div className="text-xs text-gray-500">Samples</div><div className="text-lg font-bold text-gray-300">{dashboard.metrics.events.latency.count}</div></div>
                {Object.entries(dashboard.metrics.events.by_type).slice(0, 8).map(([type, count]) => (
                  <div key={type} className="bg-[#1a1a24] rounded p-2 flex items-center justify-between">
                    <span className="text-xs text-gray-400 font-mono">{type}</span>
                    <span className="text-xs text-white font-medium">{count}</span>
                  </div>
                ))}
              </div>
            )}
            {selectedStat === "observers" && (
              <div className="space-y-2">
                {Object.entries(dashboard.metrics.observers.by_id).map(([id, obs]) => {
                  const pct = Math.round(obs.health * 100);
                  const color = pct > 70 ? "bg-green-500" : pct > 40 ? "bg-yellow-500" : "bg-red-500";
                  return (
                    <div key={id} className="flex items-center gap-3">
                      <span className="text-xs text-gray-400 w-32 truncate font-mono">{id}</span>
                      <div className="flex-1 h-2 bg-[#1a1a24] rounded-full overflow-hidden">
                        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
                      </div>
                      <span className="text-xs text-gray-500 w-10 text-right">{pct}%</span>
                      <span className="text-xs text-gray-600 w-16 text-right">{obs.entropy.toFixed(2)} ent</span>
                    </div>
                  );
                })}
                {Object.keys(dashboard.metrics.observers.by_id).length === 0 && <p className="text-xs text-gray-500 text-center py-4">No observer data</p>}
              </div>
            )}
            {selectedStat === "memory" && (
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                {Object.entries(dashboard.metrics.memory.layers).map(([layer, info]) => (
                  <div key={layer} className="bg-[#1a1a24] rounded p-3">
                    <div className="text-sm font-bold text-white capitalize">{layer}</div>
                    <div className="text-xs text-gray-500 mt-1">{info.entries} entries · {formatBytes(info.size_bytes)}</div>
                    {info.compression_ratio < 1.0 && <div className="text-xs text-cyan-400 mt-1">{(info.compression_ratio * 100).toFixed(0)}% compressed</div>}
                  </div>
                ))}
                {Object.keys(dashboard.metrics.memory.layers).length === 0 && <p className="text-xs text-gray-500 text-center py-4 col-span-3">No memory layer data</p>}
              </div>
            )}
            {selectedStat === "entropy" && (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="bg-[#1a1a24] rounded p-3"><div className="text-xs text-gray-500">Usage</div><div className={`text-lg font-bold ${dashboard.metrics.entropy.usage_pct > 80 ? "text-red-400" : "text-amber-400"}`}>{dashboard.metrics.entropy.usage_pct.toFixed(1)}%</div></div>
                <div className="bg-[#1a1a24] rounded p-3"><div className="text-xs text-gray-500">Remaining</div><div className="text-lg font-bold text-white">{formatBytes(dashboard.metrics.entropy.remaining)}</div></div>
                <div className="bg-[#1a1a24] rounded p-3"><div className="text-xs text-gray-500">Status</div><div className={`text-lg font-bold ${dashboard.metrics.entropy.usage_pct > 80 ? "text-red-400" : dashboard.metrics.entropy.usage_pct > 60 ? "text-yellow-400" : "text-green-400"}`}>{dashboard.metrics.entropy.usage_pct > 80 ? "Critical" : dashboard.metrics.entropy.usage_pct > 60 ? "Elevated" : "Normal"}</div></div>
                <div className="bg-[#1a1a24] rounded p-3"><div className="text-xs text-gray-500">Total</div><div className="text-lg font-bold text-gray-300">{formatBytes(dashboard.metrics.entropy.total)}</div></div>
              </div>
            )}
          </div>
        )}

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <MetricsPanel />
            <TraceView />
          </div>
          <div className="space-y-6">
            <AlertPanel />
            <SystemMap />
          </div>
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link href="/execution" className="bg-[#111118] border border-[#27272a] rounded-lg p-4 hover:border-indigo-500/30 transition-all group">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-indigo-600/10 rounded-lg flex items-center justify-center"><Zap className="w-4 h-4 text-indigo-400" /></div>
                <div><div className="text-sm font-medium text-white">Execution Engine</div><div className="text-xs text-gray-500">Submit & monitor tasks</div></div>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-indigo-400 transition-colors" />
            </div>
          </Link>
          <Link href="/observability" className="bg-[#111118] border border-[#27272a] rounded-lg p-4 hover:border-indigo-500/30 transition-all group">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-purple-600/10 rounded-lg flex items-center justify-center"><Activity className="w-4 h-4 text-purple-400" /></div>
                <div><div className="text-sm font-medium text-white">Observability</div><div className="text-xs text-gray-500">Metrics, traces & alerts</div></div>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-indigo-400 transition-colors" />
            </div>
          </Link>
          <Link href="/command-center" className="bg-[#111118] border border-[#27272a] rounded-lg p-4 hover:border-indigo-500/30 transition-all group">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-cyan-600/10 rounded-lg flex items-center justify-center"><MessageSquare className="w-4 h-4 text-cyan-400" /></div>
                <div><div className="text-sm font-medium text-white">Command Center</div><div className="text-xs text-gray-500">Agent coordination hub</div></div>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-indigo-400 transition-colors" />
            </div>
          </Link>
        </div>

        <footer className="border-t border-[#27272a] pt-4 pb-6">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <div className="flex items-center gap-4"><span>OCE v2.0.0</span><span>·</span><span>Powered by SRRA-OPH</span></div>
            <div className="flex items-center gap-2"><Radio className="w-3 h-3" /><span>Observability Phase 5</span></div>
          </div>
        </footer>
      </main>
    </div>
  );
}
