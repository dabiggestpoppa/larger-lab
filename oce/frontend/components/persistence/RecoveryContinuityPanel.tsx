"use client";

import { useEffect } from "react";
import { usePersistenceStore } from "../../stores/persistenceStore";

export default function RecoveryContinuityPanel() {
  const { continuitySummary, fetchContinuity, createSnapshot } = usePersistenceStore();

  useEffect(() => {
    fetchContinuity();
  }, [fetchContinuity]);

  return (
    <div className="bg-gray-900/50 rounded p-3 border border-gray-800">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs text-gray-500 font-mono">Recovery Continuity</div>
        <button
          onClick={() => createSnapshot(["runtime", "observers", "topology"])}
          className="text-xs px-2 py-1 bg-gray-800 hover:bg-gray-700 rounded text-gray-400 font-mono"
        >
          Snapshot
        </button>
      </div>

      {continuitySummary ? (
        <div className="space-y-2">
          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div>
              <span className="text-gray-500">Records: </span>
              <span className="text-gray-300">{continuitySummary.total_records}</span>
            </div>
            <div>
              <span className="text-gray-500">Score: </span>
              <span className={continuitySummary.continuity_score > 0.7 ? "text-green-400" : "text-yellow-400"}>
                {continuitySummary.continuity_score.toFixed(2)}
              </span>
            </div>
          </div>

          {Object.entries(continuitySummary.by_type).map(([type, count]) => (
            <div key={type} className="flex justify-between text-xs font-mono">
              <span className="text-gray-500">{type}</span>
              <span className="text-gray-300">{count as number}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-xs text-gray-600 font-mono">No continuity data</div>
      )}
    </div>
  );
}
