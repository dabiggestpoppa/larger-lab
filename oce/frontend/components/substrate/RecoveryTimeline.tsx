"use client";

import { useEffect } from "react";
import { useSubstrateStore } from "@/stores/substrateStore";

export default function RecoveryTimeline() {
  const { recoveryEvents, addRecoveryEvent } = useSubstrateStore();

  const triggerRecovery = async (action: string, target: string) => {
    try {
      const res = await fetch("/api/substrate/recovery", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, target }),
      });
      const data = await res.json();
      addRecoveryEvent({
        id: data.id,
        timestamp: data.timestamp,
        type: action as any,
        target,
        status: data.status as any,
        duration: data.duration_seconds,
      });
    } catch (e) {
      console.error("Recovery failed:", e);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "stable": return "text-green-400";
      case "recovering": return "text-yellow-400";
      case "failed": return "text-red-400";
      case "restarting": return "text-blue-400";
      default: return "text-gray-400";
    }
  };

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold text-gray-200">Recovery Timeline</h2>
      
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => triggerRecovery("terminate_hung", "all")}
          className="px-2 py-1 bg-red-900/30 hover:bg-red-900/50 rounded text-xs"
        >
          Terminate Hung
        </button>
        <button
          onClick={() => triggerRecovery("restart_observer", "default")}
          className="px-2 py-1 bg-blue-900/30 hover:bg-blue-900/50 rounded text-xs"
        >
          Restart Observer
        </button>
        <button
          onClick={() => triggerRecovery("restore_state", "continuity")}
          className="px-2 py-1 bg-purple-900/30 hover:bg-purple-900/50 rounded text-xs"
        >
          Restore State
        </button>
      </div>
      
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {recoveryEvents.map((e) => (
          <div key={e.id} className="bg-gray-900/50 rounded-lg p-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-gray-300">{e.type}</span>
              <span className={`text-xs ${getStatusColor(e.status)}`}>
                ● {e.status}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Target: {e.target} • {e.duration.toFixed(2)}s
            </div>
          </div>
        ))}
        
        {recoveryEvents.length === 0 && (
          <div className="text-xs text-gray-500">No recovery events</div>
        )}
      </div>
    </div>
  );
}