"use client";

import { useState } from "react";

interface ModuleInfo {
  name: string;
  module_type: string;
  phase: number;
  status: string;
  is_stable: boolean;
  repair_count: number;
  local_state_keys: string[];
}

const mockModules: ModuleInfo[] = [
  { name: "observer_core", module_type: "core", phase: 1, status: "stable", is_stable: true, repair_count: 0, local_state_keys: ["topology", "entropy", "sync_state"] },
  { name: "consensus_engine", module_type: "consensus", phase: 2, status: "stable", is_stable: true, repair_count: 1, local_state_keys: ["votes", "proposals", "quorum"] },
  { name: "spawn_engine", module_type: "spawn", phase: 3, status: "stable", is_stable: true, repair_count: 0, local_state_keys: ["blueprints", "active_spawns", "registry"] },
  { name: "field_learning", module_type: "learning", phase: 4, status: "stable", is_stable: true, repair_count: 2, local_state_keys: ["traces", "patterns", "scores"] },
  { name: "continuity_checker", module_type: "continuity", phase: 5, status: "repairing", is_stable: false, repair_count: 3, local_state_keys: ["checkpoints", "drift_log", "health"] },
  { name: "chaos_engine", module_type: "testing", phase: 11, status: "stable", is_stable: true, repair_count: 0, local_state_keys: ["scenarios", "results", "recovery_times"] },
];

function ModuleCard({ module }: { module: ModuleInfo }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`p-4 rounded-lg border cursor-pointer transition-all ${
        module.is_stable
          ? "border-[var(--border-subtle)] hover:border-[var(--accent-primary)]"
          : "border-[var(--accent-warning)] hover:border-[var(--accent-danger)]"
      } bg-[var(--bg-secondary)]`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] truncate">
            {module.name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-1">{module.module_type}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-2">
          <span className={`w-2 h-2 rounded-full ${
            module.is_stable ? "bg-[var(--accent-success)]" : "bg-[var(--accent-warning)]"
          }`} />
        </div>
      </div>
      <div className="flex items-center gap-3 mt-3 flex-wrap">
        <span className="text-xs bg-[var(--bg-tertiary)] px-2 py-0.5 rounded text-[var(--text-muted)]">
          Phase {module.phase}
        </span>
        <span className={`text-xs px-2 py-0.5 rounded ${
          module.is_stable
            ? "bg-[var(--accent-success)]/10 text-[var(--accent-success)]"
            : "bg-[var(--accent-warning)]/10 text-[var(--accent-warning)]"
        }`}>
          {module.status}
        </span>
        {module.repair_count > 0 && (
          <span className="text-xs text-[var(--text-muted)]">
            🔧 {module.repair_count} repairs
          </span>
        )}
      </div>
      {expanded && (
        <div className="mt-3 pt-3 border-t border-[var(--border-subtle)] space-y-2">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-[var(--text-muted)]">State Keys:</span>
            <span className="text-[var(--text-primary)] font-mono">{module.local_state_keys.length}</span>
          </div>
          {module.local_state_keys.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {module.local_state_keys.map((key) => (
                <span key={key} className="text-[10px] bg-[var(--bg-tertiary)] px-1.5 py-0.5 rounded text-[var(--text-muted)] font-mono">
                  {key}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ModulesPage() {
  const [modules] = useState<ModuleInfo[]>(mockModules);
  const stableCount = modules.filter((m) => m.is_stable).length;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
          MODULE STATUS DASHBOARD
        </h2>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {stableCount}/{modules.length} stable
        </span>
      </div>

      <div className="flex-1 p-4 overflow-y-auto">
        <div className="space-y-3">
          {modules.map((mod) => (
            <ModuleCard key={mod.name} module={mod} />
          ))}
        </div>
      </div>
    </div>
  );
}