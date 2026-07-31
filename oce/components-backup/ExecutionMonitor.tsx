"use client";

import { useEffect, useState } from "react";
import { Activity, Cpu, Clock, CheckCircle, XCircle, Loader2, AlertTriangle, List } from "lucide-react";
import { api, ExecutionTask, ExecutionStats } from "../lib/api";

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { color: string; icon: React.ComponentType<{ className?: string }> }> = {
    pending: { color: "bg-gray-500/10 text-gray-400 border-gray-500/20", icon: Clock },
    queued: { color: "bg-blue-500/10 text-blue-400 border-blue-500/20", icon: List },
    running: { color: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20", icon: Loader2 },
    completed: { color: "bg-green-500/10 text-green-400 border-green-500/20", icon: CheckCircle },
    failed: { color: "bg-red-500/10 text-red-400 border-red-500/20", icon: XCircle },
    cancelled: { color: "bg-gray-500/10 text-gray-500 border-gray-500/20", icon: AlertTriangle },
    timed_out: { color: "bg-orange-500/10 text-orange-400 border-orange-500/20", icon: Clock },
    retrying: { color: "bg-purple-500/10 text-purple-400 border-purple-500/20", icon: Loader2 },
  };
  const c = config[status] || config.pending;
  const Icon = c.icon;
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border font-medium ${c.color}`}>
      <Icon className="w-3 h-3" />
      {status}
    </span>
  );
}

function WorkerBar({ worker }: { worker: { worker_id: string; is_busy: boolean; tasks_processed: number; tasks_failed: number; current_task_id: string | null } }) {
  return (
    <div className={`rounded-lg border p-3 ${worker.is_busy ? "border-yellow-500/20 bg-yellow-500/5" : "border-[#27272a] bg-[#111118]"}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Cpu className={`w-4 h-4 ${worker.is_busy ? "text-yellow-400" : "text-gray-500"}`} />
          <span className="text-xs font-mono text-gray-300">{worker.worker_id}</span>
        </div>
        <span className={`text-xs px-1.5 py-0.5 rounded ${worker.is_busy ? "bg-yellow-500/20 text-yellow-400" : "bg-green-500/20 text-green-400"}`}>
          {worker.is_busy ? "BUSY" : "IDLE"}
        </span>
      </div>
      {worker.is_busy && worker.current_task_id && (
        <p className="text-xs text-gray-500 truncate">Processing: <span className="text-gray-400 font-mono">{worker.current_task_id}</span></p>
      )}
      <div className="flex items-center gap-3 mt-2 text-xs text-gray-600">
        <span>Processed: <span className="text-gray-400">{worker.tasks_processed}</span></span>
        <span>Failed: <span className="text-red-400">{worker.tasks_failed}</span></span>
      </div>
    </div>
  );
}

export function ExecutionMonitor() {
  const [tasks, setTasks] = useState<ExecutionTask[]>([]);
  const [stats, setStats] = useState<ExecutionStats | null>(null);
  const [filter, setFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [tasksData, statsData] = await Promise.all([
        api.getExecutionTasks({ limit: 50 }),
        api.getExecutionStats(),
      ]);
      setTasks(tasksData);
      setStats(statsData);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load execution data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, []);

  const filtered = tasks.filter((t) => {
    if (!filter) return true;
    return t.task_id.toLowerCase().includes(filter.toLowerCase()) ||
           t.task_type.toLowerCase().includes(filter.toLowerCase()) ||
           t.status.toLowerCase().includes(filter.toLowerCase());
  });

  const statusCounts = tasks.reduce((acc, t) => {
    acc[t.status] = (acc[t.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  if (loading) {
    return (
      <div className="bg-[#111118] border border-[#27272a] rounded-lg p-6 text-center">
        <p className="text-sm text-gray-500 animate-pulse">Loading execution monitor...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-gray-500" />
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Execution Monitor</h2>
        </div>
        <span className="text-xs text-gray-600">{tasks.length} tasks</span>
      </div>

      {error && (
        <div className="bg-[#111118] border border-red-900/30 rounded-lg p-3">
          <p className="text-xs text-red-400">{error}</p>
        </div>
      )}

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="bg-[#111118] border border-[#27272a] rounded-lg p-3 text-center">
            <div className="text-lg font-bold text-blue-400">{stats.total_submitted}</div>
            <div className="text-xs text-gray-600">Submitted</div>
          </div>
          <div className="bg-[#111118] border border-[#27272a] rounded-lg p-3 text-center">
            <div className="text-lg font-bold text-green-400">{stats.total_completed}</div>
            <div className="text-xs text-gray-600">Completed</div>
          </div>
          <div className="bg-[#111118] border border-[#27272a] rounded-lg p-3 text-center">
            <div className="text-lg font-bold text-red-400">{stats.total_failed}</div>
            <div className="text-xs text-gray-600">Failed</div>
          </div>
          <div className="bg-[#111118] border border-[#27272a] rounded-lg p-3 text-center">
            <div className="text-lg font-bold text-yellow-400">{stats.queue_size}</div>
            <div className="text-xs text-gray-600">Queued</div>
          </div>
        </div>
      )}

      {/* Status Filter Tabs */}
      <div className="flex gap-1 flex-wrap">
        <button
          onClick={() => setFilter("")}
          className={`text-xs px-2 py-1 rounded ${!filter ? "bg-indigo-600/10 text-indigo-400 border border-indigo-500/20" : "bg-[#111118] text-gray-500 border border-[#27272a]"}`}
        >
          All ({tasks.length})
        </button>
        {Object.entries(statusCounts).map(([status, count]) => (
          <button
            key={status}
            onClick={() => setFilter(filter === status ? "" : status)}
            className={`text-xs px-2 py-1 rounded ${filter === status ? "bg-indigo-600/10 text-indigo-400 border border-indigo-500/20" : "bg-[#111118] text-gray-500 border border-[#27272a]"}`}
          >
            {status} ({count})
          </button>
        ))}
      </div>

      {/* Task List */}
      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {filtered.slice(0, 20).map((task) => (
          <div key={task.task_id} className="bg-[#111118] border border-[#27272a] rounded-lg p-3 hover:border-[#3a3a4a] transition-colors">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-gray-300">{task.task_id.slice(0, 12)}</span>
                <span className="text-xs text-gray-600">{task.task_type}</span>
              </div>
              <StatusBadge status={task.status} />
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-600">
              <span>Priority: <span className="text-gray-400">{task.priority}</span></span>
              <span>Attempts: <span className="text-gray-400">{task.attempts}/{task.max_retries}</span></span>
              {task.created_at && <span>{new Date(task.created_at).toLocaleTimeString()}</span>}
            </div>
            {task.error && (
              <p className="text-xs text-red-400 mt-1 truncate">{task.error}</p>
            )}
          </div>
        ))}
        {filtered.length === 0 && (
          <p className="text-sm text-gray-600 text-center py-4">No tasks found</p>
        )}
      </div>

      {/* Worker Pool */}
      {stats?.workers && stats.workers.length > 0 && (
        <div>
          <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Worker Pool ({stats.workers.length})</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
            {stats.workers.map((w) => (
              <WorkerBar key={w.worker_id} worker={w} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
