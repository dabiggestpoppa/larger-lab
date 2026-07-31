"use client";

import { useState } from "react";
import { FileText, RotateCcw, XCircle, Clock, Hash, Tag, AlertTriangle, CheckCircle } from "lucide-react";
import { api, ExecutionTask } from "../lib/api";

function DetailRow({ label, value, mono }: { label: string; value: string | number | null; mono?: boolean }) {
  return (
    <div className="flex items-start gap-3 py-2 border-b border-[#27272a] last:border-0">
      <span className="text-xs text-gray-500 w-28 shrink-0">{label}</span>
      <span className={`text-xs text-gray-300 break-all ${mono ? "font-mono" : ""}`}>{value ?? "—"}</span>
    </div>
  );
}

export function TaskDetail({ task, onClose }: { task: ExecutionTask; onClose: () => void }) {
  const [replaying, setReplaying] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleReplay = async () => {
    setReplaying(true);
    setError(null);
    try {
      await api.replayExecutionTask(task.task_id);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Replay failed");
    } finally {
      setReplaying(false);
    }
  };

  const handleCancel = async () => {
    setCancelling(true);
    setError(null);
    try {
      await api.cancelExecutionTask(task.task_id);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Cancel failed");
    } finally {
      setCancelling(false);
    }
  };

  const canCancel = ["pending", "queued", "running", "retrying"].includes(task.status);
  const canReplay = ["completed", "failed", "cancelled", "timed_out"].includes(task.status);

  return (
    <div className="bg-[#111118] border border-indigo-500/20 rounded-lg p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-indigo-400" />
          <span className="text-sm font-mono text-gray-200">{task.task_id}</span>
        </div>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-300">
          <XCircle className="w-4 h-4" />
        </button>
      </div>

      {error && (
        <div className="bg-red-900/10 border border-red-900/30 rounded p-2">
          <p className="text-xs text-red-400">{error}</p>
        </div>
      )}

      {/* Status Banner */}
      <div className={`rounded-lg p-3 flex items-center gap-2 ${
        task.status === "completed" ? "bg-green-500/5 border border-green-500/20" :
        task.status === "failed" ? "bg-red-500/5 border border-red-500/20" :
        task.status === "running" ? "bg-yellow-500/5 border border-yellow-500/20" :
        "bg-[#1a1a24] border border-[#27272a]"
      }`}>
        {task.status === "completed" && <CheckCircle className="w-4 h-4 text-green-400" />}
        {task.status === "failed" && <AlertTriangle className="w-4 h-4 text-red-400" />}
        {task.status === "running" && <Clock className="w-4 h-4 text-yellow-400 animate-pulse" />}
        <span className="text-sm font-medium text-gray-200">{task.status.toUpperCase()}</span>
        <span className="text-xs text-gray-500 ml-auto">{task.task_type}</span>
      </div>

      {/* Details */}
      <div className="bg-[#1a1a24] rounded-lg p-3">
        <DetailRow label="Task ID" value={task.task_id} mono />
        <DetailRow label="Type" value={task.task_type} />
        <DetailRow label="Status" value={task.status} />
        <DetailRow label="Priority" value={task.priority} />
        <DetailRow label="Source" value={task.source} />
        <DetailRow label="Attempts" value={`${task.attempts} / ${task.max_retries}`} />
        <DetailRow label="Timeout" value={`${task.timeout_sec}s`} />
        <DetailRow label="Policy" value={task.policy_id} />
        <DetailRow label="Created" value={task.created_at ? new Date(task.created_at).toLocaleString() : null} />
        <DetailRow label="Started" value={task.started_at ? new Date(task.started_at).toLocaleString() : null} />
        <DetailRow label="Completed" value={task.completed_at ? new Date(task.completed_at).toLocaleString() : null} />
        {task.parent_task_id && <DetailRow label="Parent Task" value={task.parent_task_id} mono />}
      </div>

      {/* Tags */}
      {task.tags && task.tags.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <Tag className="w-3 h-3 text-gray-600" />
          {task.tags.map((tag) => (
            <span key={tag} className="bg-[#1a1a24] text-xs text-gray-400 px-2 py-0.5 rounded">{tag}</span>
          ))}
        </div>
      )}

      {/* Payload */}
      {task.payload && Object.keys(task.payload).length > 0 && (
        <div>
          <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Payload</h4>
          <pre className="bg-[#1a1a24] rounded-lg p-3 text-xs text-gray-400 font-mono overflow-x-auto max-h-40 overflow-y-auto">
            {JSON.stringify(task.payload, null, 2)}
          </pre>
        </div>
      )}

      {/* Result */}
      {task.result && Object.keys(task.result).length > 0 && (
        <div>
          <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Result</h4>
          <pre className="bg-[#1a1a24] rounded-lg p-3 text-xs text-green-400 font-mono overflow-x-auto max-h-40 overflow-y-auto">
            {JSON.stringify(task.result, null, 2)}
          </pre>
        </div>
      )}

      {/* Error */}
      {task.error && (
        <div>
          <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Error</h4>
          <pre className="bg-red-900/10 border border-red-900/30 rounded-lg p-3 text-xs text-red-400 font-mono overflow-x-auto">
            {task.error}
          </pre>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        {canReplay && (
          <button
            onClick={handleReplay}
            disabled={replaying}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-xs font-medium px-3 py-2 rounded-lg"
          >
            <RotateCcw className="w-3 h-3" />
            {replaying ? "Replaying..." : "Replay Task"}
          </button>
        )}
        {canCancel && (
          <button
            onClick={handleCancel}
            disabled={cancelling}
            className="flex items-center gap-2 bg-red-600/20 hover:bg-red-600/30 border border-red-500/20 text-red-400 disabled:opacity-40 text-xs font-medium px-3 py-2 rounded-lg"
          >
            <XCircle className="w-3 h-3" />
            {cancelling ? "Cancelling..." : "Cancel Task"}
          </button>
        )}
      </div>
    </div>
  );
}
