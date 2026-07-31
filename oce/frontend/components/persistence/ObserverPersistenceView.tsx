"use client";

import { useEffect } from "react";
import { usePersistenceStore } from "../../stores/persistenceStore";

export default function ObserverPersistenceView() {
  const { runtimeStatus, fetchStatus } = usePersistenceStore();

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const coreObservers = ["continuity", "entropy", "topology", "repair", "routing"];

  return (
    <div className="bg-gray-900/50 rounded p-3 border border-gray-800">
      <div className="text-xs text-gray-500 font-mono mb-3">Observer Persistence</div>

      <div className="space-y-2">
        {coreObservers.map((obs) => (
          <div key={obs} className="flex items-center justify-between text-sm font-mono">
            <span className="text-gray-400">{obs}</span>
            <div className="flex items-center gap-2">
              <div className="w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full bg-green-500 w-full" />
              </div>
              <span className="text-green-400 text-xs">active</span>
            </div>
          </div>
        ))}
      </div>

      {runtimeStatus && (
        <div className="mt-3 pt-2 border-t border-gray-800 text-xs text-gray-600 font-mono">
          Active: {runtimeStatus.active_observers} | Restarts: {runtimeStatus.total_restarts}
        </div>
      )}
    </div>
  );
}
