"use client";

import { useEffect, useState } from "react";
import { srraApi, ModuleInfo } from "../lib/api";

function ModuleCard({ module }: { module: ModuleInfo }) {
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
    <div className={`card border ${statusColor} hover:border-accent-blue/40 transition-colors`}>
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white">
            {module.name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
          </h3>
          <p className="text-xs text-gray-500 mt-1">{module.module_type}</p>
        </div>
        <span className={`status-dot ${dotColor}`} />
      </div>
      <div className="flex items-center gap-3 mt-3">
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
          <span className="text-xs text-gray-500">
            {module.repair_count} repairs
          </span>
        )}
      </div>
    </div>
  );
}

export default function ModulesPage() {
  const [modules, setModules] = useState<ModuleInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<number | null>(null);

  const fetchModules = async () => {
    try {
      const data = await srraApi.modules();
      setModules(data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to fetch modules");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModules();
    const interval = setInterval(fetchModules, 30000);
    return () => clearInterval(interval);
  }, []);

  const phases = [...new Set(modules.map((m) => m.phase))].sort();
  const filtered = filter ? modules.filter((m) => m.phase === filter) : modules;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-10 h-10 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card text-center max-w-md mx-auto mt-20">
        <p className="text-accent-red font-semibold">Error</p>
        <p className="text-gray-400 text-sm mt-2">{error}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Modules</h1>
          <p className="text-sm text-gray-500 mt-1">
            {modules.length} modules across {phases.length} phases
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="status-dot active" />
          <span className="text-xs text-gray-400">
            {modules.filter((m) => m.is_stable).length} stable
          </span>
        </div>
      </div>

      {/* Phase Filter */}
      <div className="flex gap-2 mb-6 flex-wrap">
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
            onClick={() => setFilter(p)}
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

      {/* Module Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((mod) => (
          <ModuleCard key={mod.name} module={mod} />
        ))}
      </div>
    </div>
  );
}
