/**
 * Phase 4 — Stability Gradient
 * Stability field overlay showing coherent and fragile regions.
 */
"use client";

import { useMemo } from "react";
import { StabilityIndex, CoherenceRegion, ResilienceZone } from "../../lib/stability/StabilityIndex";

interface Props {
  observers: { id: string; zone: string; x: number; y: number; status: string; entropy: number }[];
}

export default function StabilityGradient({ observers }: Props) {
  const stability = useMemo(() => new StabilityIndex(), []);
  const regions = useMemo(() => stability.mapCoherenceRegions(observers), [observers, stability]);
  const resilience = useMemo(() => stability.detectResilienceZones(observers), [observers, stability]);

  return (
    <div className="absolute inset-0 pointer-events-none">
      {/* Coherence regions */}
      {regions.map((r) => (
        <div
          key={`region_${r.zone}`}
          className="absolute rounded-full border-2 border-dashed"
          style={{
            left: `${r.centerX}%`,
            top: `${r.centerY}%`,
            width: r.radius * 2,
            height: r.radius * 2,
            transform: "translate(-50%, -50%)",
            borderColor: `rgba(${r.coherence > 0.6 ? "34, 211, 238" : r.coherence > 0.3 ? "251, 191, 36" : "239, 68, 68"}, ${r.coherence * 0.4})`,
            background: `radial-gradient(circle, rgba(${r.coherence > 0.6 ? "34, 211, 238" : r.coherence > 0.3 ? "251, 191, 36" : "239, 68, 68"}, ${r.coherence * 0.1}) 0%, transparent 70%)`,
          }}
        />
      ))}

      {/* Resilience zone labels */}
      {resilience
        .filter((r) => r.type !== "stable")
        .map((r) => {
          const region = regions.find((reg) => reg.zone === r.zone);
          if (!region) return null;
          return (
            <div
              key={`label_${r.zone}`}
              className="absolute text-xs font-bold px-1.5 py-0.5 rounded"
              style={{
                left: `${region.centerX}%`,
                top: `${region.centerY - 8}%`,
                transform: "translate(-50%, -50%)",
                background: r.type === "critical" ? "rgba(239, 68, 68, 0.8)" : "rgba(251, 191, 36, 0.8)",
                color: "white",
              }}
            >
              {r.type === "critical" ? "⚠ CRITICAL" : "⚡ FRAGILE"}
            </div>
          );
        })}
    </div>
  );
}
