"use client";

import { useEffect, useState } from "react";
import { useTopologyStore } from "../../stores/topologyStore";

interface RepairWaveData {
  id: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  progress: number;
}

export default function RepairWave() {
  const { nodes, edges } = useTopologyStore();
  const [waves, setWaves] = useState<RepairWaveData[]>([]);

  // Generate repair waves from repair edges
  useEffect(() => {
    const repairEdges = edges.filter((e) => e.type === "repair" && e.repairFlow && e.repairFlow > 0);
    const newWaves: RepairWaveData[] = [];

    repairEdges.forEach((edge, i) => {
      const source = nodes.find((n) => n.id === edge.source);
      const target = nodes.find((n) => n.id === edge.target);
      if (source && target) {
        newWaves.push({
          id: `wave-${i}`,
          sourceX: source.x,
          sourceY: source.y,
          targetX: target.x,
          targetY: target.y,
          progress: 0,
        });
      }
    });

    setWaves(newWaves);

    // Animate waves
    const interval = setInterval(() => {
      setWaves((prev) =>
        prev.map((w) => ({
          ...w,
          progress: Math.min(w.progress + 0.05, 1),
        })).filter((w) => w.progress < 1)
      );
    }, 50);

    return () => clearInterval(interval);
  }, [nodes, edges]);

  return (
    <g className="repair-waves">
      {waves.map((wave) => {
        const x = wave.sourceX + (wave.targetX - wave.sourceX) * wave.progress;
        const y = wave.sourceY + (wave.targetY - wave.sourceY) * wave.progress;
        return (
          <g key={wave.id}>
            {/* Wave trail */}
            <line
              x1={wave.sourceX}
              y1={wave.sourceY}
              x2={x}
              y2={y}
              stroke="#06b6d4"
              strokeWidth={2}
              opacity={0.6}
            />
            {/* Wave head */}
            <circle
              cx={x}
              cy={y}
              r={4}
              fill="#06b6d4"
              opacity={1 - wave.progress * 0.5}
            />
          </g>
        );
      })}
    </g>
  );
}
