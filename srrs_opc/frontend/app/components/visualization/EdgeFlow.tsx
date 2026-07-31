"use client";

import { useTopologyStore } from "../../stores/topologyStore";
import { getEdgeStyle } from "../../lib/edge/edge-types";

export default function EdgeFlow() {
  const { nodes, edges } = useTopologyStore();

  return (
    <g className="edge-flow">
      {edges.map((edge, i) => {
        const source = nodes.find((n) => n.id === edge.source);
        const target = nodes.find((n) => n.id === edge.target);
        if (!source || !target) return null;

        const style = getEdgeStyle(edge.type, edge.strength);
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;

        // Animated dash for flowing edges
        const dashArray = style.animated ? "8 4" : style.dashArray || "none";

        return (
          <g key={i}>
            {/* Base edge */}
            <line
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke={style.color}
              strokeWidth={style.width}
              strokeDasharray={dashArray}
              opacity={style.opacity}
            />
            {/* Flow direction indicator */}
            {style.animated && (
              <circle
                r={2}
                fill={style.color}
                opacity={0.8}
              >
                <animateMotion
                  dur={`${3 / edge.strength}s`}
                  repeatCount="indefinite"
                  path={`M${source.x},${source.y} L${target.x},${target.y}`}
                />
              </circle>
            )}
          </g>
        );
      })}
    </g>
  );
}
