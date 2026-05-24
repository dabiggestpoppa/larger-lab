"use client";

import { useAgentStore, type AgentStatus } from "@/stores/agentStore";
import { useUIStore } from "@/stores/uiStore";

const statusColors: Record<AgentStatus, string> = {
  alive: "badge-success",
  degraded: "badge-warning",
  dead: "badge-danger",
  standby: "badge-neutral",
};

export default function AgentsPage() {
  const agents = useAgentStore((s) => s.agents);
  const setSelectedAgent = useUIStore((s) => s.setSelectedAgent);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-lg font-bold text-text-primary">Agents</h1>
        <p className="text-xs text-text-secondary mt-1">Agent network status and management</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="card p-4 cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => setSelectedAgent(agent.id)}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-full ${agent.status === "alive" ? "bg-accent-success" : agent.status === "degraded" ? "bg-accent-warning" : "bg-text-muted"}`} />
                <span className="text-sm font-semibold text-text-primary">{agent.name}</span>
              </div>
              <span className={`badge ${statusColors[agent.status]}`}>{agent.status}</span>
            </div>
            <div className="text-xs text-text-secondary mb-3">{agent.role}</div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-text-muted">Current Task</span>
                <span className="text-text-primary truncate ml-2 max-w-[140px]">{agent.currentTask}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Tasks Done</span>
                <span className="text-text-primary">{agent.tasksCompleted}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Uptime</span>
                <span className="text-text-primary">{agent.uptimeHours}h</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Errors</span>
                <span className={agent.errors > 0 ? "text-accent-danger" : "text-text-primary"}>{agent.errors}</span>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-border-light">
              <div className="flex items-center justify-between text-xs">
                <span className="text-text-muted">Tag</span>
                <span className="badge badge-neutral">{agent.tag}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
