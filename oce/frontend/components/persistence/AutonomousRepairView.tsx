"use client";

import { useEffect } from "react";
import { usePersistenceStore } from "../../stores/persistenceStore";

export default function AutonomousRepairView() {
  const { repairStatus, fetchRepairStatus, triggerRepair } = usePersistenceStore();

  useEffect(() => {
    fetchRepairStatus();
    const interval = setInterval(fetchRepairStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchRepairStatus]);

  const actions = [
    { action: "restart_observer", label: "Restart Observer" },
    { action: "terminate_hung", label: "Terminate Hung" },
    { action: "restore_state", label: "Restore State" },
    { action: "reduce_entropy", label: "Reduce Entropy" },
  ];

  return (
    <div className="bg-gray-900/50 rounded p-3 border border-gray-800">
      <div className="text-xs text-gray-500 font-mono mb-3">Autonomous Repair</div>

      {repairStatus && (
        <div className="space-y-2 mb-3">
          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div>
              <span className="text-gray-500">Total: </span>
              <span className="text-gray-300">{repairStatus.total_repairs}</span>
            </div>
            <div>
              <span className="text-gray-500">Active: </span>
              <span className="text-gray-300">{repairStatus.active_repairs}</span>
            </div>
            <div>
              <span className="text-gray-500">Success: </span>
              <span className={repairStatus.recent_success_rate > 0.7 ? "text-green-400" : "text-yellow-400"}>
                {(repairStatus.recent_success_rate * 100).toFixed(0)}%
              </span>
            </div>
            <div>
              <span className="text-gray-500">Failed: </span>
              <span className="text-gray-300">{repairStatus.active_repairs}</span>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-1">
        {actions.map((a) => (
          <button
            key={a.action}
            onClick={() => triggerRepair(a.action, "all")}
            className="w-full text-left text-xs px-2 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-gray-400 font-mono"
          >
            {a.label}
          </button>
        ))}
      </div>
    </div>
  );
}
