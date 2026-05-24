/**
 * Phase 5 — Reintegration Tracker
 * Observer reintegration status after repair.
 */
"use client";

import { useMemo } from "react";
import { useTopologyStore } from "../../stores/topologyStore";

export default function ReintegrationTracker() {
  const { nodes } = useTopologyStore();

  const reintegrating = useMemo(
    () => nodes.filter((n) => n.status === "repairing" || n.status === "synced"),
    [nodes]
  );

  const failed = useMemo(
    () => nodes.filter((n) => n.status === "failed" || n.status === "dormant"),
    [nodes]
  );

  return (
    <div className="bg-gray-900/80 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-bold text-gray-300 mb-3">Reintegration</h3>

      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-gray-800 rounded p-2 text-center">
          <div className="text-lg font-bold text-cyan-400">{reintegrating.length}</div>
          <div className="text-xs text-gray-500">Reintegrating</div>
        </div>
        <div className="bg-gray-800 rounded p-2 text-center">
          <div className="text-lg font-bold text-red-400">{failed.length}</div>
          <div className="text-xs text-gray-500">Failed</div>
        </div>
      </div>

      {reintegrating.length > 0 && (
        <div className="space-y-1">
          <div className="text-xs text-gray-500 font-bold">In Progress</div>
          {reintegrating.slice(0, 5).map((n) => (
            <div key={n.id} className="flex items-center gap-2 text-xs">
              <div className={`w-2 h-2 rounded-full ${
                n.status === "repairing" ? "bg-amber-400 animate-pulse" : "bg-cyan-400"
              }`} />
              <span className="text-gray-300">{n.label}</span>
              <span className="text-gray-500 ml-auto">{n.status}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
