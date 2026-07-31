/**
 * Phase 4 — Shockwave Visualization
 * Renders perturbation shockwave propagation.
 */
"use client";

import { useEffect, useState } from "react";

interface Shockwave {
  id: string;
  x: number;
  y: number;
  type: string;
  startTime: number;
  duration: number;
}

interface Props {
  shockwaves: Shockwave[];
}

export default function Shockwave({ shockwaves }: Props) {
  const [time, setTime] = useState(Date.now());

  useEffect(() => {
    const interval = setInterval(() => setTime(Date.now()), 50);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="absolute inset-0 pointer-events-none">
      {shockwaves.map((sw) => {
        const elapsed = time - sw.startTime;
        const progress = Math.min(1, elapsed / sw.duration);
        const radius = progress * 150;
        const opacity = Math.max(0, 1 - progress);

        return (
          <div
            key={sw.id}
            className="absolute rounded-full border-2"
            style={{
              left: `${sw.x}%`,
              top: `${sw.y}%`,
              width: radius * 2,
              height: radius * 2,
              transform: "translate(-50%, -50%)",
              borderColor: sw.type === "CASCADE_STRESS" ? `rgba(239, 68, 68, ${opacity})` : `rgba(251, 191, 36, ${opacity})`,
              boxShadow: `0 0 ${20 * opacity}px ${sw.type === "CASCADE_STRESS" ? "rgba(239, 68, 68, 0.3)" : "rgba(251, 191, 36, 0.3)"}`,
            }}
          />
        );
      })}
    </div>
  );
}
