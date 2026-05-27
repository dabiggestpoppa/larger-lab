
"use client";

import { useSpawnStore } from "@/stores/spawnStore";

export default function MultiAgentFlowGraph() {
  const agents = useSpawnStore((s) => s.agents);
  const groups = new Map<string, typeof agents>();

  // Group agents by groupId
  agents.forEach((a) => {
    if (a.groupId) {
      if (!groups.has(a.groupId)) groups.set(a.groupId, []);
      groups.get(a.groupId)!.push(a);
    }
  });

  if (groups.size === 0) {
    return (
      <div className="flex items-center justify-center h-full text-xs text-gray-600">
        No multi-agent coordination groups active
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4 overflow-y-auto h-full">
      <h3 className="text-sm font-semibold text-gray-200">Multi-Agent Flow</h3>

      {Array.from(groups.entries()).map(([groupId, groupAgents]) => (
        <div key={groupId} className="p-3 rounded-lg bg-gray-800/30 border border-gray-700/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono text-gray-400">Group: {groupId}</span>
            <span className="text-[10px] text-gray-500">{groupAgents.length} agents</span>
          </div>

          {/* Flow visualization */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {groupAgents.map((agent, i) => (
              <div key={agent.agentId} className="flex items-center gap-2 shrink-0">
                <div className="flex flex-col items-center">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold ${
                      agent.state === "complete"
                        ? "bg-green-500/20 text-green-400 border border-green-500/30"
                        : agent.state === "running"
                        ? "bg-blue-500/20 text-blue-400 border border-blue-500/30 animate-pulse"
                        : agent.state === "failed"
                        ? "bg-red-500/20 text-red-400 border border-red-500/30"
                        : "bg-gray-700/50 text-gray-500 border border-gray-600"
                    }`}
                  >
                    {i + 1}
                  </div>
                  <span className="text-[9px] text-gray-500 mt-1 max-w-16 truncate">
                    {agent.taskType}
                  </span>
                </div>
                {i < groupAgents.length - 1 && (
                  <div className="w-4 h-px bg-gray-600" />
                )}
              </div>
            ))}
          </div>

          {/* Status summary */}
          <div className="flex gap-2 mt-2">
            {["running", "complete", "failed"].map((state) => {
              const count = groupAgents.filter((a) => a.state === state).length;
              if (count === 0) return null;
              return (
                <span key={state} className="text-[10px] text-gray-500">
                  {count} {state}
                </span>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
