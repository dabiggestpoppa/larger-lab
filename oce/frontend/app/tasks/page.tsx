"use client";

import { useTaskStore, type TaskStatus } from "@/stores/taskStore";
import { useUIStore } from "@/stores/uiStore";

const statusColors: Record<TaskStatus, string> = {
  pending: "badge-neutral",
  active: "badge-info",
  completed: "badge-success",
  failed: "badge-danger",
};

export default function TasksPage() {
  const tasks = useTaskStore((s) => s.tasks);
  const setSelectedTask = useUIStore((s) => s.setSelectedTask);

  const pending = tasks.filter((t) => t.status === "pending");
  const active = tasks.filter((t) => t.status === "active");
  const completed = tasks.filter((t) => t.status === "completed");
  const failed = tasks.filter((t) => t.status === "failed");

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-lg font-bold text-text-primary">Tasks</h1>
        <p className="text-xs text-text-secondary mt-1">Task queue and delegation</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="card p-3 text-center">
          <div className="text-2xl font-bold text-text-muted">{pending.length}</div>
          <div className="text-xs text-text-secondary">Pending</div>
        </div>
        <div className="card p-3 text-center">
          <div className="text-2xl font-bold text-accent-primary">{active.length}</div>
          <div className="text-xs text-text-secondary">Active</div>
        </div>
        <div className="card p-3 text-center">
          <div className="text-2xl font-bold text-accent-success">{completed.length}</div>
          <div className="text-xs text-text-secondary">Completed</div>
        </div>
        <div className="card p-3 text-center">
          <div className="text-2xl font-bold text-accent-danger">{failed.length}</div>
          <div className="text-xs text-text-secondary">Failed</div>
        </div>
      </div>

      {/* Active Tasks */}
      {active.length > 0 && (
        <div className="card p-4">
          <h2 className="text-sm font-semibold text-text-primary mb-3">Active</h2>
          <div className="space-y-2">
            {active.map((task) => (
              <div
                key={task.id}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-bg-tertiary cursor-pointer transition-colors border border-border-light"
                onClick={() => setSelectedTask(task.id)}
              >
                <div className="w-2.5 h-2.5 rounded-full bg-accent-primary animate-pulse shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-text-primary">{task.title}</div>
                  <div className="text-xs text-text-muted mt-0.5">{task.agent} · {task.priority}</div>
                </div>
                <div className="w-24">
                  <div className="w-full bg-bg-tertiary rounded-full h-1.5">
                    <div className="bg-accent-primary h-1.5 rounded-full transition-all" style={{ width: `${task.progress}%` }} />
                  </div>
                  <div className="text-xs text-text-muted text-right mt-0.5">{task.progress}%</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Completed Tasks */}
      {completed.length > 0 && (
        <div className="card p-4">
          <h2 className="text-sm font-semibold text-text-primary mb-3">Completed</h2>
          <div className="space-y-1">
            {completed.map((task) => (
              <div
                key={task.id}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-bg-tertiary cursor-pointer transition-colors"
                onClick={() => setSelectedTask(task.id)}
              >
                <div className="w-2 h-2 rounded-full bg-accent-success shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-text-primary truncate">{task.title}</div>
                </div>
                <span className="badge badge-success text-xs">done</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Tasks Table */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-text-primary mb-3">All Tasks</h2>
        <table className="w-full text-xs">
          <thead>
            <tr className="text-text-muted border-b border-border-light">
              <th className="text-left py-2 font-medium">Task</th>
              <th className="text-left py-2 font-medium">Agent</th>
              <th className="text-left py-2 font-medium">Status</th>
              <th className="text-left py-2 font-medium">Priority</th>
              <th className="text-right py-2 font-medium">Progress</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr
                key={task.id}
                className="border-b border-border-light/50 hover:bg-bg-tertiary cursor-pointer transition-colors"
                onClick={() => setSelectedTask(task.id)}
              >
                <td className="py-2 text-text-primary font-medium">{task.title}</td>
                <td className="py-2 text-text-secondary">{task.agent}</td>
                <td className="py-2"><span className={`badge ${statusColors[task.status]}`}>{task.status}</span></td>
                <td className="py-2 text-text-secondary">{task.priority}</td>
                <td className="py-2 text-right text-text-secondary">{task.progress}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
