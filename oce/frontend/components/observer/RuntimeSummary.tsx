"""
O-1-F8: RuntimeSummary
=======================
Current runtime awareness display.
"""

"use client";

import { useObserverStore } from "@/stores/observerStore";

export default function RuntimeSummary() {
  const observer = useObserverStore((s) => s.observer);
  const runtime = observer.runtimeState;

  const entries = Object.entries(runtime);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-200 mb-3">
        Runtime Awareness
      </h3>

      {/* Entropy section */}
      <div className="mb-3">
        <div className="text-xs text-gray-500 mb-2">Entropy</div>
        <div className="flex items-center gap-3">
          <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${observer.entropyState.level * 100}%`,
                backgroundColor:
                  observer.entropyState.level > 0.7
                    ? "#ef4444"
                    : observer.entropyState.level > 0.4
                    ? "#eab308"
                    : "#22c55e",
              }}
            />
          </div>
          <span className="text-xs font-mono text-gray-400">
            {observer.entropyState.level.toFixed(3)}
          </span>
          <span
            className={`text-xs ${
              observer.entropyState.trend === "rising"
                ? "text-red-400"
                : observer.entropyState.trend === "falling"
                ? "text-green-400"
                : "text-gray-500"
            }`}
          >
            {observer.entropyState.trend === "rising"
              ? "↑"
              : observer.entropyState.trend === "falling"
              ? "↓"
              : "→"}
          </span>
        </div>
      </div>

      {/* Repair section */}
      <div className="mb-3">
        <div className="text-xs text-gray-500 mb-2">Repair State</div>
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              observer.repairState.active ? "bg-yellow-500 animate-pulse" : "bg-gray-600"
            }`}
          />
          <span className="text-xs text-gray-300">
            {observer.repairState.active ? "Active" : "Idle"}
          </span>
          {observer.repairState.targets.length > 0 && (
            <span className="text-xs text-gray-500">
              ({observer.repairState.targets.join(", ")})
            </span>
          )}
        </div>
      </div>

      {/* Runtime entries */}
      {entries.length > 0 && (
        <div>
          <div className="text-xs text-gray-500 mb-2">Runtime State</div>
          <div className="space-y-1">
            {entries.map(([key, value]) => (
              <div
                key={key}
                className="flex justify-between items-center bg-gray-800/50 rounded px-2 py-1"
              >
                <span className="text-xs text-gray-500">{key}</span>
                <span className="text-xs font-mono text-gray-300 truncate max-w-[150px]">
                  {String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {entries.length === 0 && (
        <div className="text-xs text-gray-600 italic">
          No runtime state data
        </div>
      )}
    </div>
  );
}
