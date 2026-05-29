"use client";

import { useEffect } from "react";
import { usePersistenceStore } from "../../stores/persistenceStore";

export default function PersistentFieldView() {
  const {
    runtimeStatus,
    heartbeat,
    dormantState,
    environment,
    loading,
    fetchStatus,
    fetchHeartbeat,
    fetchDormantState,
    fetchEnvironment,
  } = usePersistenceStore();

  useEffect(() => {
    fetchStatus();
    fetchHeartbeat();
    fetchDormantState();
    fetchEnvironment();
    const interval = setInterval(() => {
      fetchStatus();
      fetchHeartbeat();
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus, fetchHeartbeat, fetchDormantState, fetchEnvironment]);

  const stateColor = (state: string) => {
    switch (state) {
      case "active": return "text-green-400";
      case "observational": return "text-blue-400";
      case "dormant": return "text-gray-400";
      case "recovery": return "text-yellow-400";
      case "critical": return "text-red-400";
      default: return "text-gray-400";
    }
  };

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-mono text-gray-200 border-b border-gray-800 pb-2">
        Persistent Field
      </h2>

      {loading && <div className="text-gray-500 text-sm">Loading...</div>}

      {/* Runtime Status */}
      {runtimeStatus && (
        <div className="bg-gray-900/50 rounded p-3 border border-gray-800">
          <div className="text-xs text-gray-500 mb-2">Runtime</div>
          <div className="grid grid-cols-2 gap-2 text-sm font-mono">
            <div>
              <span className="text-gray-500">State: </span>
              <span className={stateColor(runtimeStatus.state)}>{runtimeStatus.state}</span>
            </div>
            <div>
              <span className="text-gray-500">Uptime: </span>
              <span className="text-gray-300">{Math.round(runtimeStatus.uptime_seconds)}s</span>
            </div>
            <div>
              <span className="text-gray-500">Observers: </span>
              <span className="text-gray-300">{runtimeStatus.active_observers}</span>
            </div>
            <div>
              <span className="text-gray-500">Restarts: </span>
              <span className="text-gray-300">{runtimeStatus.total_restarts}</span>
            </div>
            <div>
              <span className="text-gray-500">Entropy: </span>
              <span className={runtimeStatus.entropy_level > 0.7 ? "text-red-400" : "text-gray-300"}>
                {runtimeStatus.entropy_level.toFixed(2)}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Continuity: </span>
              <span className={runtimeStatus.continuity_score < 0.5 ? "text-yellow-400" : "text-green-400"}>
                {runtimeStatus.continuity_score.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Heartbeat */}
      {heartbeat && (
        <div className="bg-gray-900/50 rounded p-3 border border-gray-800">
          <div className="text-xs text-gray-500 mb-2">Heartbeat</div>
          <div className="grid grid-cols-2 gap-2 text-sm font-mono">
            <div>
              <span className="text-gray-500">Field: </span>
              <span className={stateColor(heartbeat.field_state)}>{heartbeat.field_state}</span>
            </div>
            <div>
              <span className="text-gray-500">Health: </span>
              <span className={heartbeat.observer_health > 0.7 ? "text-green-400" : "text-yellow-400"}>
                {(heartbeat.observer_health * 100).toFixed(0)}%
              </span>
            </div>
            <div>
              <span className="text-gray-500">Load: </span>
              <span className="text-gray-300">{(heartbeat.runtime_load * 100).toFixed(0)}%</span>
            </div>
            <div>
              <span className="text-gray-500">Agents: </span>
              <span className="text-gray-300">{heartbeat.active_agents}</span>
            </div>
          </div>
        </div>
      )}

      {/* Dormant State */}
      {dormantState && (
        <div className="bg-gray-900/50 rounded p-3 border border-gray-800">
          <div className="text-xs text-gray-500 mb-2">Dormant State</div>
          <div className="grid grid-cols-2 gap-2 text-sm font-mono">
            <div>
              <span className="text-gray-500">State: </span>
              <span className={stateColor(dormantState.current_state)}>{dormantState.current_state}</span>
            </div>
            <div>
              <span className="text-gray-500">Time: </span>
              <span className="text-gray-300">{Math.round(dormantState.time_in_state_seconds)}s</span>
            </div>
            <div>
              <span className="text-gray-500">Transitions: </span>
              <span className="text-gray-300">{dormantState.total_transitions}</span>
            </div>
          </div>
        </div>
      )}

      {/* Environment */}
      {environment && (
        <div className="bg-gray-900/50 rounded p-3 border border-gray-800">
          <div className="text-xs text-gray-500 mb-2">Environment</div>
          <div className="grid grid-cols-2 gap-2 text-sm font-mono">
            <div>
              <span className="text-gray-500">Status: </span>
              <span className={
                environment.overall_status === "critical" ? "text-red-400" :
                environment.overall_status === "warning" ? "text-yellow-400" : "text-green-400"
              }>{environment.overall_status}</span>
            </div>
            {Object.entries(environment.metrics).map(([key, val]) => (
              <div key={key}>
                <span className="text-gray-500">{key}: </span>
                <span className={(val as number) > 0.75 ? "text-red-400" : "text-gray-300"}>
                  {(val as number).toFixed(2)}
                </span>
              </div>
            ))}
          </div>
          {environment.alerts.length > 0 && (
            <div className="mt-2 space-y-1">
              {environment.alerts.map((alert, i) => (
                <div key={i} className={`text-xs font-mono ${alert.status === "critical" ? "text-red-400" : "text-yellow-400"}`}>
                  ⚠ {alert.metric}: {alert.value.toFixed(2)}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
