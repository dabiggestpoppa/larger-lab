/**
 * Phase 4 — Pressure Field Renderer
 * Renders pressure field overlay on the topology canvas.
 */
"use client";

import { useMemo } from "react";
import { useEntropyStore } from "../../stores/entropyStore";

export type PressureMode = "THERMAL" | "VECTOR" | "GRADIENT" | "PRESSURE_WAVES";

interface Props {
  mode?: PressureMode;
}

export default function PressureField({ mode = "THERMAL" }: Props) {
  const { fieldStress } = useEntropyStore();

  const gradients = useMemo(() => {
    return fieldStress.map((zone) => {
      const intensity = zone.pressure;
      switch (mode) {
        case "THERMAL":
          return {
            ...zone,
            color: intensity < 0.3 ? "cyan" : intensity < 0.6 ? "amber" : "red",
            radius: 30 + intensity * 40,
            opacity: 0.1 + intensity * 0.3,
          };
        case "GRADIENT":
          return {
            ...zone,
            color: `rgba(${Math.round(intensity * 255)}, ${Math.round((1 - intensity) * 200)}, 50, ${0.1 + intensity * 0.2})`,
            radius: 25 + intensity * 35,
            opacity: 0.15 + intensity * 0.25,
          };
        case "PRESSURE_WAVES":
          return {
            ...zone,
            color: intensity > 0.5 ? "red" : "cyan",
            radius: 20 + intensity * 50,
            opacity: 0.05 + intensity * 0.15,
            animated: intensity > 0.4,
          };
        default:
          return { ...zone, color: "cyan", radius: 30, opacity: 0.2 };
      }
    });
  }, [fieldStress, mode]);

  return (
    <div className="absolute inset-0 pointer-events-none">
      {gradients.map((g) => (
        <div
          key={g.zone}
          className={`absolute rounded-full ${g.animated ? "animate-pulse" : ""}`}
          style={{
            left: `${g.x}%`,
            top: `${g.y}%`,
            width: g.radius * 2,
            height: g.radius * 2,
            transform: "translate(-50%, -50%)",
            background: `radial-gradient(circle, ${g.color} 0%, transparent 70%)`,
            opacity: g.opacity,
          }}
        />
      ))}
    </div>
  );
}
