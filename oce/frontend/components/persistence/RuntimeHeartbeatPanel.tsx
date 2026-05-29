"use client";

import { useEffect } from "react";
import { usePersistenceStore } from "../../stores/persistenceStore";

export default function RuntimeHeartbeatPanel() {
  const { heartbeat, fetchHeartbeat, pulseHeartbeat } = usePersistenceStore();

  useEffect(() => {
    fetchHeartbeat();
    const interval = setInterval(fetchHeartbeat, 15000);
    return () => clearInterval(interval);
  }, [fetchHeartbeat]);

  const healthColor = (val: number) => {
    if (val > 0.7) return "bg-green-500";
    if (val > 0.4) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div className="bg-gray-900/50 rounded p-3 border border-gray-800">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs text-gray-500 font-mono">Runtime Heartbeat</div>
        <button
          onClick={pulseHeartbeat}
          className="text-xs px-2 py-1 bg-gray-800 hover:bg-gray-700 rounded text-gray-400 font-mono"
        >
          Pulse
        </button>
      </div>

      {heartbeat && (
        <div className="space-y-2">
          {/* Health bar */}
          <div className="flex items-center gap-2">
            <div className="text-xs text-gray-500 w-16">Health</div>
            <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={`h-full ${healthColor(heartbeat.observer_health)} transition-all`}
                style={{ width: `${heartbeat.observer_health * 100}%` }}
              />
            </div>
            <div className="text-xs text-gray-400 font-mono w-10 text-right">
              {(heartbeat.observer_health * 100).toFixed(0)}%
            </div>
          </div>

          {/* Entropy bar */}
          <div className="flex items-center gap-2">
            <div className="text-xs text-gray-500 w-16">Entropy</div>
            <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={`h-full ${healthColor(1 - heartbeat.entropy_level)} transition-all`}
                style={{ width: `${heartbeat.entropy_level * 100}%` }}
              />
            </div>
            <div className="text-xs text-gray-400 font-mono w-10 text-right">
              {(heartbeat.entropy_level * 100).toFixed(0)}%
            </div>
          </div>

          {/* Continuity bar */}
          <div className="flex items-center gap-2">
            <div className="text-xs text-gray-500 w-16">Continuity</div>
            <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={`h-full ${healthColor(heartbeat.continuity_score)} transition-all`}
                style={{ width: `${heartbeat.continuity_score * 100}%` }}
              />
            </div>
            <div className="text-xs text-gray-400 font-mono w-10 text-right">
              {(heartbeat.continuity_score * 100).toFixed(0)}%
            </div>
          </div>

          <div className="text-xs text-gray-600 font-mono pt-1">
            {heartbeat.timestamp ? new Date(heartbeat.timestamp).toLocaleTimeString() : "—"}
          </div>
        </div>
      )}
    </div>
  );
}
