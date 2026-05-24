"use client";

import { useTaskStore } from "@/stores/taskStore";
import { useAgentStore } from "@/stores/agentStore";
import { useSessionStore } from "@/stores/sessionStore";
import { useUIStore } from "@/stores/uiStore";

function StatCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div className="card p-4">
      <div className="text-xs text-text-muted uppercase tracking-wider mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color || "text-text-primary"}`}>{value}</div>
      {sub && <div className="text-xs text-text-secondary mt-1">{sub}</div>}
    </div>
  );
}

export default function DashboardPage() {
  const tasks = useTaskStore((s) => s.tasks);
  const agents = useAgentStore((s) => s.agents);
  const sessions = useSessionStore((s) => s.sessions);
  const setSelectedTask = useUIStore((s) => s.setSelectedTask);
  const setSelectedAgent = useUIStore((s) => s.setSelectedAgent);

  const activeTasks = tasks.filter((t) => t.status === "active");
  const aliveAgents = agents.filter((a) => a.status === "alive");
  const runningSessions = sessions.filter((s) => s.status === "running");

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-lg font-bold text-text-primary">Dashboard</h1>
        <p className="text-xs text-text-secondary mt-1">Operator Continuity Engine — Operational Overview</p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Active Tasks" value={activeTasks.length} sub={`${tasks.filter((t) => t.status === "completed").length} completed`} color="text-accent-primary" />
        <StatCard label="Agents Alive" value={aliveAgents.length} sub={`${agents.length} total`} color="text-accent-success" />
        <StatCard label="Running Sessions" value={runningSessions.length} sub={`${sessions.length} total`} color="text-accent-warning" />
        <StatCard label="System Health" value="Good" sub="All core systems operational" color="text-accent-success" />
      </div>

      {/* Active Tasks */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-text-primary mb-3">Active Tasks</h2>
        {activeTasks.length === 0 ? (
          <p className="text-xs text-text-muted">No active tasks</p>
        ) : (
          <div className="space-y-2">
            {activeTasks.map((task) => (
              <div
                key={task.id}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-bg-tertiary cursor-pointer transition-colors"
                onClick={() => setSelectedTask(task.id)}
              >
                <div className="w-2 h-2 rounded-full bg-accent-primary shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-text-primary truncate">{task.title}</div>
                  <div className="text-xs text-text-muted">{task.agent} · {task.priority}</div>
                </div>
                <div className="w-20">
                  <div className="w-full bg-bg-tertiary rounded-full h-1">
                    <div className="bg-accent-primary h-1 rounded-full" style={{ width: `${task.progress}%` }} />
                  </div>
                  <div className="text-xs text-text-muted text-right mt-0.5">{task.progress}%</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Agent Status */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-text-primary mb-3">Agent Status</h2>
        <div className="grid grid-cols-2 gap-2">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="flex items-center gap-2 p-2 rounded-lg hover:bg-bg-tertiary cursor-pointer transition-colors"
              onClick={() => setSelectedAgent(agent.id)}
            >
              <div className={`w-2 h-2 rounded-full shrink-0 ${agent.status === "alive" ? "bg-accent-success" : agent.status === "degraded" ? "bg-accent-warning" : "bg-text-muted"}`} />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-text-primary truncate">{agent.name}</div>
                <div className="text-xs text-text-muted truncate">{agent.currentTask}</div>
              </div>
              <span className="badge badge-neutral text-xs">{agent.tag}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Sessions */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-text-primary mb-3">Experiment Sessions</h2>
        <div className="space-y-2">
          {sessions.slice(0, 5).map((session) => (
            <div key={session.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-bg-tertiary transition-colors">
              <span className={`badge badge-${session.status === "running" ? "info" : session.status === "completed" ? "success" : "danger"}`}>
                {session.status}
              </span>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-text-primary">{session.name}</div>
                <div className="text-xs text-text-muted">{session.type} · {session.cycles} cycles</div>
              </div>
              <div className="text-xs text-text-secondary">{session.passRate}% pass</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
