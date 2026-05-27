
"use client";

import { useSpawnStore } from "@/stores/spawnStore";

export default function SpawnReplayPanel() {
  const agents = useSpawnStore((s) => s.agents);
  const traces = useSpawnStore((s) => s.traces);

  // Combine agents and traces into replay entries
  const entries = agents.map((a) => {
    const trace = traces.find((t) => t.agentId === a.agentId);
    return { agent: a, trace };
  });

  if (entries.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-xs text-gray-600">
        No spawn history to replay
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-200">Spawn Replay</h3>
        <span className="text-[10px] text-gray-500">{entries.length} decisions recorded</span>
      </div>
      <div className="flex-1 overflow-y-auto divide-y divide-gray-700/30">
        {entries.map(({ agent, trace }) => (
          <div key={agent.agentId} className="px-4 py-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-gray-300">{agent.agentId}</span>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded ${
                  agent.state === "complete"
                    ? "bg-green-500/20 text-green-400"
                    : agent.state === "failed"
                    ? "bg-red-500/20 text-red-400"
                    : "bg-blue-500/20 text-blue-400"
                }`}
              >
                {agent.state}
              </span>
            </div>
            <div className="mt-1 text-[10px] text-gray-500">
              <span>{agent.taskType}</span>
              <span className="mx-1">•</span>
              <span>{agent.model.split("/").pop()}</span>
            </div>
            {trace && (
              <div className="mt-2 p-2 rounded bg-gray-900/50 text-[10px] text-gray-400 space-y-1">
                <div>Tokens: {trace.tokensUsed} | Turns: {trace.turnsUsed}</div>
                <div>Duration: {trace.durationSeconds.toFixed(1)}s</div>
                {trace.keyFindings.length > 0 && (
                  <div>Findings: {trace.keyFindings.join(", ")}</div>
                )}
              </div>
            )}
            <div className="mt-1 text-[10px] text-gray-600">
              {new Date(agent.createdAt).toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
