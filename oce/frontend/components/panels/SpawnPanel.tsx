"use client";

import { useState } from "react";

interface SpawnEntry {
  id: string;
  agentType: string;
  status: "pending" | "running" | "complete" | "failed" | "timeout";
  blueprint: string;
  contextSize: number;
  tokenBudget: number;
  createdAt: string;
}

const mockSpawns: SpawnEntry[] = [
  { id: "spawn-001", agentType: "Worker", status: "complete", blueprint: "data-analysis-v2", contextSize: 4096, tokenBudget: 8000, createdAt: "2026-05-28T07:00:00Z" },
  { id: "spawn-002", agentType: "Monitor", status: "running", blueprint: "health-check-v1", contextSize: 2048, tokenBudget: 4000, createdAt: "2026-05-28T08:30:00Z" },
  { id: "spawn-003", agentType: "Debugger", status: "pending", blueprint: "error-trace-v3", contextSize: 8192, tokenBudget: 16000, createdAt: "2026-05-28T09:00:00Z" },
  { id: "spawn-004", agentType: "Researcher", status: "failed", blueprint: "pattern-search-v1", contextSize: 16384, tokenBudget: 32000, createdAt: "2026-05-28T06:00:00Z" },
];

export default function SpawnPanel() {
  const [spawns] = useState<SpawnEntry[]>(mockSpawns);
  const [selectedSpawn, setSelectedSpawn] = useState<string | null>(null);

  const statusColor = (status: string) => {
    switch (status) {
      case "complete": return "text-[var(--accent-success)]";
      case "running": return "text-[var(--accent-primary)]";
      case "pending": return "text-[var(--accent-warning)]";
      case "failed": return "text-[var(--accent-danger)]";
      case "timeout": return "text-[var(--accent-warning)]";
      default: return "text-[var(--text-muted)]";
    }
  };

  const statusDot = (status: string) => {
    switch (status) {
      case "complete": return "bg-[var(--accent-success)]";
      case "running": return "bg-[var(--accent-primary)] animate-pulse";
      case "pending": return "bg-[var(--accent-warning)]";
      case "failed": return "bg-[var(--accent-danger)]";
      default: return "bg-[var(--text-muted)]";
    }
  };

  const runningCount = spawns.filter(s => s.status === "running").length;
  const completeCount = spawns.filter(s => s.status === "complete").length;
  const failedCount = spawns.filter(s => s.status === "failed" || s.status === "timeout").length;

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-[var(--border-subtle)]">
        <h3 className="text-xs font-mono font-bold text-[var(--text-primary)]">SPAWN ENGINE</h3>
        <p className="text-[10px] text-[var(--text-muted)] mt-1">O-3 Agent Spawn — {spawns.length} entries</p>
      </div>

      <div className="flex-1 p-3 overflow-y-auto space-y-2">
        {spawns.map((spawn) => (
          <div
            key={spawn.id}
            onClick={() => setSelectedSpawn(selectedSpawn === spawn.id ? null : spawn.id)}
            className={`p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedSpawn === spawn.id
                ? "bg-[var(--bg-tertiary)] border-[var(--accent-primary)]"
                : "bg-[var(--bg-secondary)] border-[var(--border-subtle)] hover:border-[var(--border-default)]"
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${statusDot(spawn.status)}`} />
                <span className="text-xs font-mono text-[var(--text-primary)]">{spawn.agentType}</span>
              </div>
              <span className={`text-[10px] font-mono uppercase ${statusColor(spawn.status)}`}>{spawn.status}</span>
            </div>

            {selectedSpawn === spawn.id && (
              <div className="mt-3 space-y-2 text-[10px] font-mono">
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Blueprint</span>
                  <span className="text-[var(--text-primary)]">{spawn.blueprint}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Context</span>
                  <span className="text-[var(--text-primary)]">{spawn.contextSize.toLocaleString()} tokens</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Budget</span>
                  <span className="text-[var(--text-primary)]">{spawn.tokenBudget.toLocaleString()} tokens</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Created</span>
                  <span className="text-[var(--text-primary)]">{new Date(spawn.createdAt).toLocaleTimeString()}</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="px-4 py-3 border-t border-[var(--border-subtle)]">
        <div className="grid grid-cols-3 gap-2 text-center">
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)]">Running</span>
            <p className="text-sm font-mono text-[var(--accent-primary)]">{runningCount}</p>
          </div>
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)]">Complete</span>
            <p className="text-sm font-mono text-[var(--accent-success)]">{completeCount}</p>
          </div>
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)]">Failed</span>
            <p className="text-sm font-mono text-[var(--accent-danger)]">{failedCount}</p>
          </div>
        </div>
      </div>
    </div>
  );
}