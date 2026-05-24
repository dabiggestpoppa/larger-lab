"use client";

import { useUIStore } from "@/stores/uiStore";
import { useTaskStore } from "@/stores/taskStore";
import { useAgentStore } from "@/stores/agentStore";

export default function RightPanel() {
  const { rightPanelOpen, rightPanelContent, toggleRightPanel } = useUIStore();
  const { selectedTaskId, selectedAgentId } = useUIStore();
  const task = useTaskStore((s) => s.tasks.find((t) => t.id === selectedTaskId));
  const agent = useAgentStore((s) => s.agents.find((a) => a.id === selectedAgentId));

  if (!rightPanelOpen) return null;

  return (
    <div className="w-72 bg-bg-secondary border-l border-border-light flex flex-col shrink-0 overflow-y-auto">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border-light">
        <span className="text-xs font-semibold text-text-primary uppercase tracking-wider">
          {rightPanelContent === "task" ? "Task Details" : rightPanelContent === "agent" ? "Agent Details" : "Details"}
        </span>
        <button
          onClick={toggleRightPanel}
          className="text-text-muted hover:text-text-primary text-xs px-2 py-1 rounded hover:bg-bg-tertiary"
        >
          ✕
        </button>
      </div>
      <div className="p-4">
        {rightPanelContent === "task" && task && (
          <div className="space-y-3">
            <div>
              <span className="badge badge-neutral">Task</span>
            </div>
            <h3 className="text-sm font-semibold text-text-primary">{task.title}</h3>
            <p className="text-xs text-text-secondary">{task.description}</p>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-text-muted">Status</span>
                <span className={`badge badge-${task.status === "active" ? "info" : task.status === "completed" ? "success" : task.status === "failed" ? "danger" : "neutral"}`}>
                  {task.status}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Agent</span>
                <span className="text-text-primary">{task.agent}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Progress</span>
                <span className="text-text-primary">{task.progress}%</span>
              </div>
              <div className="w-full bg-bg-tertiary rounded-full h-1.5 mt-1">
                <div
                  className="bg-accent-primary h-1.5 rounded-full transition-all"
                  style={{ width: `${task.progress}%` }}
                />
              </div>
            </div>
          </div>
        )}
        {rightPanelContent === "agent" && agent && (
          <div className="space-y-3">
            <div>
              <span className="badge badge-neutral">{agent.tag}</span>
            </div>
            <h3 className="text-sm font-semibold text-text-primary">{agent.name}</h3>
            <p className="text-xs text-text-secondary">{agent.role}</p>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-text-muted">Status</span>
                <span className={`badge badge-${agent.status === "alive" ? "success" : agent.status === "degraded" ? "warning" : "neutral"}`}>
                  {agent.status}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Current Task</span>
                <span className="text-text-primary truncate ml-2">{agent.currentTask}</span>
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
          </div>
        )}
        {!rightPanelContent && (
          <p className="text-xs text-text-muted">Select a task or agent to view details.</p>
        )}
      </div>
    </div>
  );
}
