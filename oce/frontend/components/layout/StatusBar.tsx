"use client";

import { useTaskStore } from "@/stores/taskStore";
import { useAgentStore } from "@/stores/agentStore";
import { useUIStore } from "@/stores/uiStore";

const statusColors: Record<string, string> = {
  connected: "text-accent-success",
  connecting: "text-accent-warning",
  disconnected: "text-text-muted",
  error: "text-accent-danger",
};

const statusLabels: Record<string, string> = {
  connected: "● Live",
  connecting: "● Connecting...",
  disconnected: "○ Offline",
  error: "✕ Error",
};

export default function StatusBar() {
  const activeTasks = useTaskStore((s) => s.getActiveTasks());
  const agents = useAgentStore((s) => s.agents);
  const aliveCount = agents.filter((a) => a.status === "alive").length;
  const degradedCount = agents.filter((a) => a.status === "degraded").length;
  const connectionStatus = useUIStore((s) => s.connectionStatus);

  return (
    <div className="h-7 bg-bg-tertiary border-t border-border-light flex items-center px-4 gap-4 text-xs text-text-muted shrink-0">
      <span className={statusColors[connectionStatus]}>
        {statusLabels[connectionStatus]}
      </span>
      <span>
        <span className="text-accent-success">●</span> {aliveCount} agents alive
      </span>
      {degradedCount > 0 && (
        <span>
          <span className="text-accent-warning">●</span> {degradedCount} degraded
        </span>
      )}
      <span>
        <span className="text-accent-primary">▶</span> {activeTasks.length} active tasks
      </span>
      <div className="flex-1" />
      <span>OCE v2.0 — Operator Continuity Engine</span>
    </div>
  );
}
