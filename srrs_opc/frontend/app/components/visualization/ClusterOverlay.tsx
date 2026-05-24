"use client";

import { useMemo } from "react";
import { useTopologyStore } from "../../stores/topologyStore";
import { computeClusters } from "../../lib/clustering/sync-clusters";

export default function ClusterOverlay() {
  const { nodes, edges } = useTopologyStore();

  const clusters = useMemo(() => computeClusters(nodes, edges), [nodes, edges]);

  if (clusters.length === 0) return null;

  return (
    <g className="cluster-overlay">
      {clusters.map((cluster) => {
        // Compute convex hull-ish boundary
        const clusterNodes = cluster.nodes
          .map((id) => nodes.find((n) => n.id === id))
          .filter(Boolean);

        if (clusterNodes.length < 2) return null;

        const minX = Math.min(...clusterNodes.map((n) => n!.x)) - 30;
        const maxX = Math.max(...clusterNodes.map((n) => n!.x)) + 30;
        const minY = Math.min(...clusterNodes.map((n) => n!.y)) - 30;
        const maxY = Math.max(...clusterNodes.map((n) => n!.y)) + 30;

        return (
          <g key={cluster.id}>
            <rect
              x={minX}
              y={minY}
              width={maxX - minX}
              height={maxY - minY}
              rx={8}
              fill="none"
              stroke="#8b5cf6"
              strokeWidth={1}
              strokeDasharray="4 4"
              opacity={0.4}
            />
            <text
              x={minX + 4}
              y={minY - 4}
              className="fill-[#8b5cf6]"
              style={{ fontSize: "8px", fontFamily: "IBM Plex Mono, monospace" }}
            >
              {cluster.id} (sync: {(cluster.syncDensity * 100).toFixed(0)}%)
            </text>
          </g>
        );
      })}
    </g>
  );
}
