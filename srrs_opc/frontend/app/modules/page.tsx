"use client";

import { useEffect, useState, useCallback } from "react";
import { srraApi, ModuleInfo } from "../lib/api";
import { ErrorBanner } from "../components/ErrorBanner";
import { SkeletonCard } from "../components/SkeletonLoader";
import { Search, ChevronDown, ChevronUp, Wrench, Hash } from "lucide-react";

function ModuleCard({ module }: { module: ModuleInfo }) {
  const [expanded, setExpanded] = useState(false);

  const statusColor = module.is_stable
    ? "border-green-500/30"
    : module.status === "repairing"
    ? "border-yellow-500/30"
    : "border-red-500/30";

  const dotColor = module.is_stable
    ? "active"
    : module.status === "repairing"
    ? "repairing"
    : "error";

  return (
    <div className={`card border ${statusColor} hover:border-accent-blue/40 transition-all cursor-pointer`} onClick={() => setExpanded(!expanded)}>
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-white truncate">
            {module.name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
          </h3>
          <p className="text-xs text-gray-500 mt-1">{module.module_type}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-2">
          <span className={`status-dot ${dotColor}`} />
          {expanded ? <ChevronUp className="w-3 h-3 text-gray-500" /> : <ChevronDown className="w-3 h-3 text-gray-500" />}
        </div>
      </div>
      <div className="flex items-center gap-3 mt-3 flex-wrap">
        <span className="text-xs bg-bg-tertiary px-2 py-0.5 rounded text-gray-400">
          Phase {module.phase}
        </span>
        <span
          className={`text-xs px-2 py-0.5 rounded ${
            module.is_stable
              ? "bg-green-500/10 text-green-400"
              : "bg-yellow-500/10 text-yellow-400"
          }`}
        >
          {module.status}
        </span>
        {module.repair_count > 0 && (
          <span className="text-xs text-gray-500 flex items-center gap-1">
            <Wrench className="w-3 h-3" />
            {module.repair_count} repairs
          </span>
        )}
      </div>
      {expanded && (
        <div className="mt-3 pt-3 border-t border-default space-y-2">
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <Hash className="w-3 h-3" />
            <span className="font-mono text-gray-500">{module.name}</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="text-gray-500">State Keys:</span>
            <span className="text-gray-300 font-mono">{module.local_state_keys.length}</span>
          </div>
          {module.local_state_keys.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {module.local_state_keys.slice(0, 6).map((key) => (
                <span key={key} className="text-[10px] bg-bg-tertiary px-1.5 py-0.5 rounded text-gray-500 font-mono">
                  {key}
                </span>
              ))}
              {module.local_state_keys.length > 6 && (
                <span className="text-[10px] text-gray-600">+{module.local_state_keys.length - 6} more</span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ModulesPage() {
  const [modules, setModules] = useState<ModuleInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<number | null>(null);
  const [search, setSearch] = useState("");

  const fetchModules = useCallback(async () => {
    try {
      const data = await srraApi.modules();
      setModules(data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to fetch modules");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModules();
    const interval = setInterval(fetchModules, 15000);
    return () => clearInterval(interval);
  }, [fetchModules]);

  const phases = [...new Set(modules.map((m) => m.phase))].sort();
  const filtered = modules.filter((m) => {
    const matchesPhase = filter ? m.phase === filter : true;
    const matchesSearch = search
      ? m.name.toLowerCase().includes(search.toLowerCase()) ||
        m.module_type.toLowerCase().includes(search.toLowerCase())
      : true;
    return matchesPhase && matchesSearch;
  });

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Modules</h1>
            <p className="text-sm text-gray-500 mt-1">Loading...</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  if (error && modules.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Modules</h1>
        <ErrorBanner title="Error" message={error} severity="error" onRetry={fetchModules} />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Modules</h1>
          <p className="text-sm text-gray-500 mt-1">
            {filtered.length} of {modules.length} modules across {phases.length} phases
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="status-dot active" />
          <span className="text-xs text-gray-400">
            {modules.filter((m) => m.is_stable).length} stable
          </span>
        </div>
      </div>

      {/* Search + Filter */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search modules..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm bg-bg-secondary border border-default rounded-md text-gray-200 placeholder-gray-600 focus:outline-none focus:border-accent-blue/50"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setFilter(null)}
            className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
              filter === null
                ? "bg-accent-blue text-white"
                : "bg-bg-tertiary text-gray-400 hover:text-white"
            }`}
          >
            All
          </button>
          {phases.map((p) => (
            <button
              key={p}
              onClick={() => setFilter(filter === p ? null : p)}
              className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                filter === p
                  ? "bg-accent-blue text-white"
                  : "bg-bg-tertiary text-gray-400 hover:text-white"
              }`}
            >
              Phase {p}
            </button>
          ))}
        </div>
      </div>

      {/* Module Grid */}
      {filtered.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 text-sm">No modules match your search</p>
          <button onClick={() => { setSearch(""); setFilter(null); }} className="text-xs text-accent-blue mt-2 hover:underline">
            Clear filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((mod) => (
            <ModuleCard key={mod.name} module={mod} />
          ))}
        </div>
      )}
    </div>
  );
}
