
"use client";

import { useSpawnStore } from "@/stores/spawnStore";

const stateLabels: Record<string, string> = {
  pending: "Pending",
  running: "Running",
  complete: "Complete",
  failed: "Failed",
  timeout: "Timeout",
  cancelled: "Cancelled",
};

const stateIcons: Record<string, string> = {
  pending: "⏳",
  running: "🔄",
  complete: "✅",
  failed: "❌",
  timeout: "⏱️",
  cancelled: "🚫",
};

export default function AgentLifecyclePanel() {
  const selectedAgentId = useSpawnStore((s) => s.selectedAgentId);
  const getAgentById = useSpawnStore((s) => s.getAgentById);
  const agent = selectedAgentId ? getAgentById(selectedAgentId) : null;

  if (!agent) {
    return (
      <div className="flex items-center justify-center h-full text-xs text-gray-600">
        Select an agent to view lifecycle details
      </div>
    );
  }

  const lifecycleSteps = ["pending", "running", "complete"];
  const currentIdx = lifecycleSteps.indexOf(agent.state);

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-2">
        <span className="text-lg">{stateIcons[agent.state]}</span>
        <div>
          <h4 className="text-sm font-semibold text-gray-200">{agent.agentId}</h4>
          <span className="text-xs text-gray-500">{stateLabels[agent.state]}</span>
        </div>
      </div>

      {/* Lifecycle progress */}
      <div className="space-y-2">
        <span className="text-[10px] uppercase tracking-wider text-gray-500">Lifecycle</span>
        <div className="flex items-center gap-1">
          {lifecycleSteps.map((step, i) => (
            <div key={step} className="flex items-center flex-1">
              <div
                className={`w-full h-1.5 rounded ${
                  i <= currentIdx ? "bg-blue-500" : "bg-gray-700"
                } ${agent.state === "failed" && step === "running" ? "bg-red-500" : ""}`}
              />
              {i < lifecycleSteps.length - 1 && <div className="w-1" />}
            </div>
          ))}
        </div>
        <div className="flex justify-between text-[10px] text-gray-600">
          <span>Pending</span>
          <span>Running</span>
          <span>Complete</span>
        </div>
      </div>

      {/* Details */}
      <div className="space-y-2">
        <span className="text-[10px] uppercase tracking-wider text-gray-500">Details</span>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="p-2 rounded bg-gray-800/50">
            <span className="text-gray-500">Task Type</span>
            <div className="text-gray-300">{agent.taskType}</div>
          </div>
          <div className="p-2 rounded bg-gray-800/50">
            <span className="text-gray-500">Model</span>
            <div className="text-gray-300 truncate">{agent.model.split("/").pop()}</div>
          </div>
          <div className="p-2 rounded bg-gray-800/50">
            <span className="text-gray-500">Turns</span>
            <div className="text-gray-300">{agent.turnsUsed}</div>
          </div>
          <div className="p-2 rounded bg-gray-800/50">
            <span className="text-gray-500">Tokens</span>
            <div className="text-gray-300">{agent.tokensUsed}</div>
          </div>
        </div>
      </div>

      {/* Timing */}
      <div className="space-y-2">
        <span className="text-[10px] uppercase tracking-wider text-gray-500">Timing</span>
        <div className="text-xs space-y-1">
          <div className="flex justify-between">
            <span className="text-gray-500">Created</span>
            <span className="text-gray-300">{new Date(agent.createdAt).toLocaleString()}</span>
          </div>
          {agent.startedAt && (
            <div className="flex justify-between">
              <span className="text-gray-500">Started</span>
              <span className="text-gray-300">{new Date(agent.startedAt).toLocaleString()}</span>
            </div>
          )}
          {agent.endedAt && (
            <div className="flex justify-between">
              <span className="text-gray-500">Ended</span>
              <span className="text-gray-300">{new Date(agent.endedAt).toLocaleString()}</span>
            </div>
          )}
        </div>
      </div>

      {agent.error && (
        <div className="p-2 rounded bg-red-500/10 border border-red-500/20">
          <span className="text-[10px] uppercase tracking-wider text-red-400">Error</span>
          <div className="text-xs text-red-300 mt-1">{agent.error}</div>
        </div>
      )}
    </div>
  );
}
