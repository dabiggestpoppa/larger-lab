"use client";

import { useEffect, useState, useCallback } from "react";
import { srraApi, HealthResponse, ModuleInfo, PhaseInfo, EventItem } from "./lib/api";
import { ErrorBanner } from "./components/ErrorBanner";
import { SkeletonStatCard, SkeletonPhaseBar, SkeletonEventRow } from "./components/SkeletonLoader";

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "healthy" || status === "active"
      ? "bg-green-500"
      : status === "degraded" || status === "repairing"
      ? "bg-yellow-500"
      : "bg-red-500";
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium text-white ${color}`}>
      <span className="status-dot active" />
      {status}
    </span>
  );
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="card">
      <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold text-white mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [modules, setModules] = useState<ModuleInfo[]>([]);
  const [phases, setPhases] = useState<PhaseInfo[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<string>("");
  const [expandedPhase, setExpandedPhase] = useState<number | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      const [h, m, p, e] = await Promise.all([
        srraApi.health(),
        srraApi.modules(),
        srraApi.phases(),
        srraApi.events(5),
      ]);
      setHealth(h);
      setModules(m);
      setPhases(p);
      setEvents(e);
      setError(null);
      setLastRefresh(new Date().toLocaleTimeString());
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to fetch data";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 15000); // Faster polling (15s vs 30s)
    return () => clearInterval(interval);
  }, [fetchAll]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Dashboard</h1>
            <p className="text-sm text-gray-500 mt-1">SRRA-OPH System Overview</p>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <SkeletonStatCard /><SkeletonStatCard /><SkeletonStatCard /><SkeletonStatCard />
        </div>
        <div className="card mb-8">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">Phase Progress</h2>
          <div className="space-y-3">
            <SkeletonPhaseBar /><SkeletonPhaseBar /><SkeletonPhaseBar />
          </div>
        </div>
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">Recent Events</h2>
          <div className="space-y-2">
            <SkeletonEventRow /><SkeletonEventRow /><SkeletonEventRow />
          </div>
        </div>
      </div>
    );
  }

  if (error && !health) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Dashboard</h1>
            <p className="text-sm text-gray-500 mt-1">SRRA-OPH System Overview</p>
          </div>
        </div>
        <ErrorBanner
          title="Connection Error"
          message={error}
          severity="error"
          onRetry={fetchAll}
          details="Ensure API is running on localhost:8001. Check that the OCE backend is started."
        />
      </div>
    );
  }

  const activePhases = phases.filter((p) => p.status === "active").length;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            SRRA-OPH System Overview {lastRefresh && `• Updated ${lastRefresh}`}
          </p>
        </div>
        {health && <StatusBadge status={health.status} />}
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Patches"
          value={health?.total_patches ?? 0}
          sub={`${health?.stable_count ?? 0} stable`}
        />
        <StatCard
          label="Modules"
          value={modules.length}
          sub={`${modules.filter((m) => m.is_stable).length} stable`}
        />
        <StatCard
          label="Phases"
          value={activePhases}
          sub={`of ${phases.length} active`}
        />
        <StatCard
          label="Coherence"
          value={health ? `${(health.coherence_yield * 100).toFixed(0)}%` : "—"}
          sub={`Entropy: ${health?.entropy_remaining.toFixed(0) ?? "—"}`}
        />
      </div>

      {/* Phase Progress */}
      <div className="card mb-8">
        <h2 className="text-sm font-semibold text-gray-300 mb-4">Phase Progress</h2>
        <div className="space-y-2">
          {phases.map((phase) => {
            const maxModules = Math.max(...phases.map((p) => p.modules.length));
            const pct = maxModules > 0 ? (phase.modules.length / maxModules) * 100 : 0;
            const isExpanded = expandedPhase === phase.phase;
            return (
              <div key={phase.phase}>
                <div
                  className="flex items-center gap-4 cursor-pointer hover:bg-bg-tertiary/50 rounded-md px-2 py-1.5 -mx-2 transition-colors group"
                  onClick={() => setExpandedPhase(isExpanded ? null : phase.phase)}
                  title={`${phase.modules.length} modules — click to ${isExpanded ? "collapse" : "expand"}`}
                >
                  <span className="text-xs text-gray-500 w-6">P{phase.phase}</span>
                  <div className="flex-1 bg-bg-tertiary rounded-full h-2 overflow-hidden relative">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        phase.status === "active" ? "bg-accent-blue" : "bg-yellow-500"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                    <span className="absolute right-1 top-1/2 -translate-y-1/2 text-[9px] text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity">
                      {phase.modules.length} modules
                    </span>
                  </div>
                  <span className="text-xs text-gray-400 w-24 truncate">{phase.name}</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded ${
                      phase.status === "active"
                        ? "bg-green-500/20 text-green-400"
                        : "bg-yellow-500/20 text-yellow-400"
                    }`}
                  >
                    {phase.status}
                  </span>
                </div>
                {isExpanded && (
                  <div className="ml-10 mt-1 mb-2 p-2 bg-bg-tertiary/30 rounded-md">
                    <div className="flex flex-wrap gap-1">
                      {phase.modules.map((modName) => (
                        <span key={modName} className="text-[10px] bg-bg-tertiary px-1.5 py-0.5 rounded text-gray-400 font-mono">
                          {modName}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Events */}
      <div className="card">
        <h2 className="text-sm font-semibold text-gray-300 mb-4">Recent Events</h2>
        {events.length === 0 ? (
          <p className="text-gray-500 text-sm">No events yet</p>
        ) : (
          <div className="space-y-2">
            {events.map((evt) => (
              <div
                key={evt.event_id}
                className="flex items-center gap-3 py-2 border-b border-default last:border-0"
              >
                <span
                  className={`status-dot ${
                    evt.priority > 0 ? "repairing" : "active"
                  }`}
                />
                <span className="text-xs text-gray-500 font-mono w-32 shrink-0">
                  {evt.event_type}
                </span>
                <span className="text-xs text-gray-300 flex-1 truncate">
                  {evt.source}
                </span>
                <span className="text-xs text-gray-600">
                  {new Date(evt.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
