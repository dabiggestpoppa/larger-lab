
"use client";

import { useSpawnStore } from "@/stores/spawnStore";

export default function RuntimeLoadPanel() {
  const runtimeLoad = useSpawnStore((s) => s.runtimeLoad);
  const agents = useSpawnStore((s) => s.agents);

  const activeCount = agents.filter((a) => a.state === "running" || a.state === "pending").length;
  const loadPct = Math.min((activeCount / runtimeLoad.maxAgents) * 100, 100);
  const loadColor = loadPct > 80 ? "bg-red-500" : loadPct > 50 ? "bg-yellow-500" : "bg-green-500";

  return (
    <div className="p-4 space-y-4">
      <h3 className="text-sm font-semibold text-gray-200">Runtime Load</h3>

      {/* Active agents gauge */}
      <div>
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-400">Active Agents</span>
          <span className="text-gray-300">{activeCount}/{runtimeLoad.maxAgents}</span>
        </div>
        <div className="w-full h-2 rounded bg-gray-700 overflow-hidden">
          <div className={`h-full ${loadColor} transition-all`} style={{ width: `${loadPct}%` }} />
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-2">
        <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700/50">
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Total Tokens</div>
          <div className="text-lg font-semibold text-gray-200 mt-1">
            {runtimeLoad.totalTokens.toLocaleString()}
          </div>
        </div>
        <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700/50">
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Avg Duration</div>
          <div className="text-lg font-semibold text-gray-200 mt-1">
            {runtimeLoad.avgDuration.toFixed(1)}s
          </div>
        </div>
        <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700/50">
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Success Rate</div>
          <div className={`text-lg font-semibold mt-1 ${runtimeLoad.successRate >= 80 ? "text-green-400" : runtimeLoad.successRate >= 50 ? "text-yellow-400" : "text-red-400"}`}>
            {runtimeLoad.successRate}%
          </div>
        </div>
        <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700/50">
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Total Spawns</div>
          <div className="text-lg font-semibold text-gray-200 mt-1">{agents.length}</div>
        </div>
      </div>

      {/* State breakdown */}
      <div>
        <span className="text-[10px] uppercase tracking-wider text-gray-500">State Breakdown</span>
        <div className="mt-2 space-y-1">
          {(["pending", "running", "complete", "failed", "timeout"] as const).map((state) => {
            const count = agents.filter((a) => a.state === state).length;
            if (count === 0) return null;
            return (
              <div key={state} className="flex items-center justify-between text-xs">
                <span className="text-gray-400">{state}</span>
                <span className="text-gray-300">{count}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
