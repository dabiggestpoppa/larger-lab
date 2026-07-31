"use client";

import { useEffect } from "react";
import { usePersistenceStore } from "../../stores/persistenceStore";

export default function DriftAnalysisPanel() {
  const { driftReport, fetchDriftReport } = usePersistenceStore();

  useEffect(() => {
    fetchDriftReport();
    const interval = setInterval(fetchDriftReport, 60000);
    return () => clearInterval(interval);
  }, [fetchDriftReport]);

  const statusColor = (status: string) => {
    if (status === "critical") return "text-red-400";
    if (status === "warning") return "text-yellow-400";
    return "text-green-400";
  };

  return (
    <div className="bg-gray-900/50 rounded p-3 border border-gray-800">
      <div className="text-xs text-gray-500 font-mono mb-3">Drift Analysis</div>

      {driftReport ? (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-mono">
            <span className="text-gray-500">Status:</span>
            <span className={statusColor(driftReport.overall_status)}>
              {driftReport.overall_status}
            </span>
          </div>

          {Object.entries(driftReport.metrics).map(([name, data]) => {
            const m = data as { current_value: number; baseline: number; avg_deviation: number; status: string };
            return (
              <div key={name} className="text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-gray-500">{name}</span>
                  <span className={statusColor(m.status)}>{m.status}</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>current: {m.current_value.toFixed(3)}</span>
                  <span>deviation: {(m.avg_deviation * 100).toFixed(1)}%</span>
                </div>
              </div>
            );
          })}

          {driftReport.alerts.length > 0 && (
            <div className="mt-2 space-y-1">
              {driftReport.alerts.map((alert, i) => (
                <div key={i} className={`text-xs font-mono ${statusColor(alert.status)}`}>
                  ⚠ {alert.metric}: {(alert.deviation * 100).toFixed(1)}% deviation
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="text-xs text-gray-600 font-mono">No drift data</div>
      )}
    </div>
  );
}
