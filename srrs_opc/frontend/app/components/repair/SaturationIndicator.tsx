/**
 * Phase 5 — Saturation Indicator
 * Repair overload warnings.
 */
"use client";

import { useRepairStore } from "../../stores/repairStore";

export default function SaturationIndicator() {
  const { saturationLevel, activeRepairs } = useRepairStore();

  const level = saturationLevel;
  const isWarning = level > 0.5;
  const isCritical = level > 0.8;

  return (
    <div className={`rounded-lg p-3 border ${
      isCritical ? "bg-red-900/60 border-red-500" :
      isWarning ? "bg-amber-900/60 border-amber-500" :
      "bg-gray-900/60 border-gray-700"
    }`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold text-gray-300">Repair Saturation</span>
        <span className={`text-xs font-bold ${
          isCritical ? "text-red-400" : isWarning ? "text-amber-400" : "text-cyan-400"
        }`}>
          {(level * 100).toFixed(0)}%
        </span>
      </div>

      {/* Saturation bar */}
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${
            isCritical ? "bg-red-500" : isWarning ? "bg-amber-500" : "bg-cyan-500"
          }`}
          style={{ width: `${level * 100}%` }}
        />
      </div>

      {isWarning && (
        <div className="mt-2 text-xs text-amber-400">
          ⚠ {isCritical ? "Critical: Repair overload imminent" : "Warning: High repair load"}
        </div>
      )}

      <div className="mt-1 text-xs text-gray-500">
        {activeRepairs.length} active repairs
      </div>
    </div>
  );
}
