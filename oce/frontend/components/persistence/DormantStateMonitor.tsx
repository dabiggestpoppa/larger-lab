"use client";

import { useEffect } from "react";
import { usePersistenceStore } from "../../stores/persistenceStore";

export default function DormantStateMonitor() {
  const { dormantState, fetchDormantState, transitionState } = usePersistenceStore();

  useEffect(() => {
    fetchDormantState();
    const interval = setInterval(fetchDormantState, 30000);
    return () => clearInterval(interval);
  }, [fetchDormantState]);

  const stateColors: Record<string, string> = {
    dormant: "text-gray-400",
    observational: "text-blue-400",
    active: "text-green-400",
    recovery: "text-yellow-400",
    critical: "text-red-400",
  };

  const states = ["dormant", "observational", "active", "recovery", "critical"];

  return (
    <div className="bg-gray-900/50 rounded p-3 border border-gray-800">
      <div className="text-xs text-gray-500 font-mono mb-3">Dormant State Monitor</div>

      {dormantState && (
        <div className="space-y-3">
          {/* State indicator */}
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              dormantState.current_state === "active" ? "bg-green-500" :
              dormantState.current_state === "critical" ? "bg-red-500" :
              dormantState.current_state === "dormant" ? "bg-gray-500" : "bg-blue-500"
            }`} />
            <span className={`text-sm font-mono ${stateColors[dormantState.current_state] || "text-gray-400"}`}>
              {dormantState.current_state}
            </span>
            <span className="text-xs text-gray-600 font-mono">
              ({Math.round(dormantState.time_in_state_seconds)}s)
            </span>
          </div>

          {/* State buttons */}
          <div className="flex flex-wrap gap-1">
            {states.map((s) => (
              <button
                key={s}
                onClick={() => transitionState(s, "manual")}
                disabled={dormantState.current_state === s}
                className={`text-xs px-2 py-1 rounded font-mono ${
                  dormantState.current_state === s
                    ? "bg-gray-700 text-gray-500 cursor-not-allowed"
                    : "bg-gray-800 hover:bg-gray-700 text-gray-400"
                }`}
              >
                {s}
              </button>
            ))}
          </div>

          <div className="text-xs text-gray-600 font-mono">
            Transitions: {dormantState.total_transitions}
          </div>
        </div>
      )}
    </div>
  );
}
