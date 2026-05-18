"use client";

import { useState, useEffect } from "react";
import { MetricsPanel } from "./components/MetricsPanel";
import { TraceView } from "./components/TraceView";
import { AlertPanel } from "./components/AlertPanel";
import { SystemMap } from "./components/SystemMap";
import { api, DashboardData } from "./lib/api";
import {
  Activity, GitBranch, Bell, Network, Shield, Cpu, Database, Zap,
  Radio, AlertTriangle, XCircle, MessageSquare,
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

function QuickStat({ label, value, icon: Icon, color, trend }: {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  trend?: "up" | "down" | "stable";
}) {
  return (
    <div className="bg-[#111118] border border-[#27272a] rounded-lg p-4 hover:border-[#3a3a4a] transition-colors">
      <div className="flex items-center justify-between mb-2">
        <Icon className={`w-4 h-4 ${color}`} />
        {trend && (
          <span className={`text-xs ${
            trend === "up" ? "text-green-400" : trend === "down" ? "text-red-400" : "text-gray-500"
          }`}>
            {trend === "up" ? "â†‘" : trend === "down" ? "â†“" : "â†’"}
          </span>
        )}
      </div>
      <div className="text-xl font-bold text-white">{value}</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </div>
  );
}

function NavItem({ icon: Icon, label, active, badge }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  active?: boolean;
  badge?: number;
}) {
  return (
    <button className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors ${
      active
        ? "bg-indigo-600/10 text-indigo-400"
        : "text-gray-400 hover:text-gray-200 hover:bg-[#1a1a24]"
    }`}>
      <Icon className="w-4 h-4" />
      <span>{label}</span>
      {badge !== undefined && badge > 0 && (
        <span className="bg-red-500/20 text-red-400 text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
          {badge}
        </span>
      )}
    </button>
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

  useEffect(() => {
    let ws: WebSocket | null = null;
    let pollInterval: ReturnType<typeof setInterval>;

    const loadDashboard = async () => {
      try {
        const d = await api.getDashboard();
        setDashboard(d);
      } catch { /* backend may not be up */ }
    };

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
  }, []);

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
      <header className="border-b border-[#27272a] bg-[#0a0a0f] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-white tracking-wide">OCE</h1>
              <p className="text-[10px] text-gray-600 -mt-0.5">Operator Continuity Engine</p>
            </div>
          </div>
          <nav className="flex items-center gap-1">
            <NavItem icon={Activity} label="Overview" active />
            <NavItem icon={GitBranch} label="Traces" />
            <NavItem icon={Bell} label="Alerts" badge={dashboard?.alerts.stats.active_firing} />
            <NavItem icon={Network} label="Topology" />
            <a href="/execution" className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors text-gray-400 hover:text-gray-200 hover:bg-[#1a1a24]">
              <Zap className="w-4 h-4" />
              <span>Execution</span>
            </a>
            <a href="/command-center" className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors text-gray-400 hover:text-gray-200 hover:bg-[#1a1a24]">
              <MessageSquare className="w-4 h-4" />
              <span>Command Center</span>
            </a>
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
        {systemHealth !== "healthy" && (
          <div className={`rounded-lg border p-4 flex items-center gap-3 ${
            systemHealth === "critical"
              ? "bg-red-900/10 border-red-900/30"
              : "bg-yellow-900/10 border-yellow-900/30"
          }`}>
            {systemHealth === "critical" ? (
              <XCircle className="w-5 h-5 text-red-400 shrink-0" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0" />
            )}
            <div>
              <p className={`text-sm font-medium ${systemHealth === "critical" ? "text-red-400" : "text-yellow-400"}`}>
                {systemHealth === "critical"
                  ? "System health critical â€” immediate attention required"
                  : "System health degraded â€” review active alerts"}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">
                {dashboard?.alerts.active.filter((a) => a.state === "firing").length} active alerts
                {dashboard && ` Â· ${(dashboard.metrics.observers.avg_health * 100).toFixed(0)}% avg observer health`}
              </p>
            </div>
          </div>
        )}

        {dashboard && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <QuickStat label="Event Rate" value={`${dashboard.metrics.events.rate_per_sec.toFixed(1)}/s`} icon={Activity} color="text-blue-400" />
            <QuickStat label="Observers" value={String(dashboard.metrics.observers.count)} icon={Cpu} color="text-purple-400" trend={dashboard.metrics.observers.avg_health > 0.7 ? "stable" : "down"} />
            <QuickStat label="Memory" value={formatBytes(dashboard.metrics.memory.total_size_bytes)} icon={Database} color="text-cyan-400" />
            <QuickStat label="Entropy" value={`${dashboard.metrics.entropy.usage_pct.toFixed(1)}%`} icon={Zap} color={dashboard.metrics.entropy.usage_pct > 80 ? "text-red-400" : "text-amber-400"} trend={dashboard.metrics.entropy.usage_pct > 80 ? "up" : "stable"} />
          </div>
        )}

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

        <footer className="border-t border-[#27272a] pt-4 pb-6">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <div className="flex items-center gap-4">
              <span>OCE v2.0.0</span>
              <span>Â·</span>
              <span>Powered by SRRA-OPH</span>
            </div>
            <div className="flex items-center gap-2">
              <Radio className="w-3 h-3" />
              <span>Observability Phase 5</span>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );

}
