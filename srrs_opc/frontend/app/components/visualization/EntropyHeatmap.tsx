"use client";

import { useMemo } from "react";
import { useTopologyStore } from "../../stores/topologyStore";

export default function EntropyHeatmap() {
  const { nodes } = useTopologyStore();

  const entropyRegions = useMemo(() => {
    const regions: { id: string; x: number; y: number; entropy: number; label: string }[] = [];
    nodes.forEach((node) => {
      if (node.entropy > 0.3) {
        regions.push({
          id: node.id,
          x: node.x,
          y: node.y,
          entropy: node.entropy,
          label: node.label,
        });
      }
    });
    return regions;
  }, [nodes]);

  if (entropyRegions.length === 0) return null;

  return (
    <g className="entropy-overlay">
      <defs>
        <radialGradient id="entropy-glow">
          <stop offset="0%" stopColor="#dc2626" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#dc2626" stopOpacity="0" />
        </radialGradient>
      </defs>
      {entropyRegions.map((region) => (
        <g key={region.id}>
          <circle
            cx={region.x}
            cy={region.y}
            r={30 + region.entropy * 40}
            fill="url(#entropy-glow)"
            className="entropy-flicker"
          />
          <circle
            cx={region.x}
            cy={region.y}
            r={4}
            fill="#dc2626"
            opacity={region.entropy}
          />
        </g>
      ))}
    </g>
  );
}
