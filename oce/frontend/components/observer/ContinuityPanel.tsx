"""
O-1-F7: ContinuityPanel
========================
Continuity state display.
"""

"use client";

import { useObserverStore } from "@/stores/observerStore";

export default function ContinuityPanel() {
  const observer = useObserverStore((s) => s.observer);
  const score = observer.continuityScore;

  const getContinuityLabel = (s: number) => {
    if (s >= 0.9) return { label: "Strong", color: "text-green-400" };
    if (s >= 0.7) return { label: "Good", color: "text-blue-400" };
    if (s >= 0.4) return { label: "Weak", color: "text-yellow-400" };
    return { label: "Broken", color: "text-red-400" };
  };

  const { label, color } = getContinuityLabel(score);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-200 mb-3">
        Continuity State
      </h3>

      {/* Continuity bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>0%</span>
          <span className={`font-medium ${color}`}>{label}</span>
          <span>100%</span>
        </div>
        <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${score * 100}%`,
              background: `linear-gradient(90deg, #ef4444 0%, #eab308 50%, #22c55e 100%)`,
            }}
          />
        </div>
      </div>

      {/* Active task */}
      <div className="flex justify-between items-center bg-gray-800/50 rounded px-3 py-2 mb-2">
        <span className="text-xs text-gray-500">Active Task</span>
        <span className="text-xs font-mono text-gray-300">
          {observer.activeTask || "None"}
        </span>
      </div>

      {/* Active agents */}
      <div className="bg-gray-800/50 rounded px-3 py-2">
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-gray-500">Active Agents</span>
          <span className="text-xs font-mono text-gray-300">
            {observer.activeAgents.length}
          </span>
        </div>
        {observer.activeAgents.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {observer.activeAgents.map((agent) => (
              <span
                key={agent}
                className="text-xs bg-purple-900/50 text-purple-300 px-2 py-0.5 rounded"
              >
                {agent}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
