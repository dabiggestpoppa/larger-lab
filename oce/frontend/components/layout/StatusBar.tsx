"use client";

import { useMemo } from "react";
import { useTaskStore } from "@/stores/taskStore";
import { useAgentStore } from "@/stores/agentStore";
import { useUIStore } from "@/stores/uiStore";

const statusColors: Record<string, string> = {
  connected: "text-[var(--accent-success)]",
  connecting: "text-[var(--accent-warning)]",
  disconnected: "text-[var(--text-muted)]",
  error: "text-[var(--accent-danger)]",
};

const statusLabels: Record<string, string> = {
  connected: "● Live",
  connecting: "● Connecting...",
  disconnected: "○ Offline",
  error: "✕ Error",
};

export default function StatusBar() {
  const tasks = useTaskStore((s) => s.tasks);
  const agents = useAgentStore((s) => s.agents);
  const connectionStatus = useUIStore((s) => s.connectionStatus);

  const activeTasks = useMemo(() => tasks.filter((t) => t.status === "active"), [tasks]);
  const aliveCount = useMemo(() => agents.filter((a) => a.status === "alive").length, [agents]);
  const degradedCount = useMemo(() => agents.filter((a) => a.status === "degraded").length, [agents]);

  return (
    <div className="h-7 bg-[var(--bg-tertiary)] border-t border-[var(--border-default)] flex items-center px-4 gap-4 text-xs text-[var(--text-muted)] shrink-0">
      <span className={statusColors[connectionStatus]}>
        {statusLabels[connectionStatus]}
      </span>
      <span>
        <span className="text-[var(--accent-success)]">●</span> {aliveCount} agents alive
      </span>
      {degradedCount > 0 && (
        <span>
          <span className="text-[var(--accent-warning)]">●</span> {degradedCount} degraded
        </span>
      )}
      <span>
        <span className="text-[var(--accent-primary)]">▶</span> {activeTasks.length} active tasks
      </span>
      <div className="flex-1" />
      <span>OCE v2.0 — Operator Continuity Engine</span>
    </div>
  );
}
