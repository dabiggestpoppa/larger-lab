/**
 * Phase 4 — Entropy Field Visualization
 * Renders entropy heatmap overlay on the topology canvas.
 */
"use client";

import { useMemo } from "react";
import { useEntropyStore } from "../../stores/entropyStore";

export default function EntropyField() {
  const { fieldStress, globalEntropy } = useEntropyStore();

  const heatGradient = useMemo(() => {
    const level = globalEntropy;
    if (level < 0.3) return "from-cyan-500/10 to-transparent";
    if (level < 0.6) return "from-amber-500/20 to-transparent";
    return "from-red-500/30 to-transparent";
  }, [globalEntropy]);

  return (
    <div className="absolute inset-0 pointer-events-none">
      {/* Global entropy overlay */}
      <div className={`absolute inset-0 bg-gradient-radial ${heatGradient}`} />

      {/* Zone stress indicators */}
      {fieldStress.map((zone) => (
        <div
          key={zone.zone}
          className="absolute"
          style={{
            left: `${zone.x}%`,
            top: `${zone.y}%`,
            width: 40,
            height: 40,
            transform: "translate(-50%, -50%)",
          }}
        >
          <div
            className="w-full h-full rounded-full animate-pulse"
            style={{
              background: `radial-gradient(circle, ${stressColor(zone.pressure)} 0%, transparent 70%)`,
              opacity: zone.pressure,
            }}
          />
        </div>
      ))}

      {/* Global entropy readout */}
      <div className="absolute top-2 right-2 bg-gray-900/80 rounded px-2 py-1 text-xs">
        <span className="text-gray-400">Entropy: </span>
        <span className={entropyColor(globalEntropy)}>
          {(globalEntropy * 100).toFixed(1)}%
        </span>
      </div>
    </div>
  );
}

function stressColor(pressure: number): string {
  if (pressure < 0.3) return "rgba(34, 211, 238, 0.3)";
  if (pressure < 0.6) return "rgba(251, 191, 36, 0.4)";
  return "rgba(239, 68, 68, 0.5)";
}

function entropyColor(level: number): string {
  if (level < 0.3) return "text-cyan-400";
  if (level < 0.6) return "text-amber-400";
  return "text-red-400";
}
