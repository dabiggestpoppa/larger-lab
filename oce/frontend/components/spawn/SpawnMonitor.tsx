
"use client";

import { useSpawnStore, AgentLifecycleState } from "@/stores/spawnStore";

const stateColors: Record<AgentLifecycleState, string> = {
  pending: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  running: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  complete: "bg-green-500/20 text-green-400 border-green-500/30",
  failed: "bg-red-500/20 text-red-400 border-red-500/30",
  timeout: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  cancelled: "bg-gray-500/20 text-gray-400 border-gray-500/30",
};

const stateDots: Record<AgentLifecycleState, string> = {
  pending: "bg-yellow-400",
  running: "bg-blue-400 animate-pulse",
  complete: "bg-green-400",
  failed: "bg-red-400",
  timeout: "bg-orange-400",
  cancelled: "bg-gray-400",
};

export default function SpawnMonitor() {
  const agents = useSpawnStore((s) => s.agents);
  const filterState = useSpawnStore((s) => s.filterState);
  const setFilter = useSpawnStore((s) => s.setFilter);
  const setSelectedAgent = useSpawnStore((s) => s.setSelectedAgent);
  const selectedAgentId = useSpawnStore((s) => s.selectedAgentId);

  const filteredAgents = filterState === "all" ? agents : agents.filter((a) => a.state === filterState);

  const counts = {
    all: agents.length,
    pending: agents.filter((a) => a.state === "pending").length,
    running: agents.filter((a) => a.state === "running").length,
    complete: agents.filter((a) => a.state === "complete").length,
    failed: agents.filter((a) => a.state === "failed").length,
    timeout: agents.filter((a) => a.state === "timeout").length,
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-200">Spawn Monitor</h3>
        <span className="text-xs text-gray-500">{agents.length} agents</span>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 px-3 py-2 border-b border-gray-700/50 overflow-x-auto">
        {(["all", "running", "pending", "complete", "failed", "timeout"] as const).map((state) => (
          <button
            key={state}
            onClick={() => setFilter(state)}
            className={`px-2 py-0.5 text-xs rounded-full border transition-colors ${
              filterState === state
                ? "bg-blue-500/20 text-blue-400 border-blue-500/30"
                : "text-gray-500 border-gray-700 hover:text-gray-300"
            }`}
          >
            {state} ({counts[state]})
          </button>
        ))}
      </div>

      {/* Agent list */}
      <div className="flex-1 overflow-y-auto">
        {filteredAgents.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-xs text-gray-600">
            No agents {filterState !== "all" ? `with state: ${filterState}` : ""}
          </div>
        ) : (
          <div className="divide-y divide-gray-700/30">
            {filteredAgents.map((agent) => (
              <button
                key={agent.agentId}
                onClick={() => setSelectedAgent(agent.agentId === selectedAgentId ? null : agent.agentId)}
                className={`w-full text-left px-3 py-2 hover:bg-gray-800/50 transition-colors ${
                  agent.agentId === selectedAgentId ? "bg-gray-800/70" : ""
                }`}
              >
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${stateDots[agent.state]}`} />
                  <span className="text-xs font-mono text-gray-300 truncate flex-1">
                    {agent.agentId}
                  </span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border ${stateColors[agent.state]}`}>
                    {agent.state}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-1 ml-4">
                  <span className="text-[10px] text-gray-500">{agent.taskType}</span>
                  <span className="text-[10px] text-gray-600">•</span>
                  <span className="text-[10px] text-gray-500 truncate">{agent.model.split("/").pop()}</span>
                </div>
                {agent.agentId === selectedAgentId && (
                  <div className="mt-2 ml-4 p-2 rounded bg-gray-900/50 text-[10px] text-gray-400 space-y-1">
                    <div>Plan: {agent.planId}</div>
                    <div>Turns: {agent.turnsUsed} | Tokens: {agent.tokensUsed}</div>
                    <div>Created: {new Date(agent.createdAt).toLocaleTimeString()}</div>
                    {agent.error && <div className="text-red-400">Error: {agent.error}</div>}
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
