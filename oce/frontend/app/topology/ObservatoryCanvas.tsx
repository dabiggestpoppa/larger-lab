"use client";

import { useEffect, useRef, useState } from "react";
import { useTopologyStore, ObserverNode } from "../../stores/topologyStore";
import { computeClusters } from "../../lib/clustering/sync-clusters";

interface LayoutNode extends ObserverNode {
  vx: number;
  vy: number;
}

export default function ObservatoryCanvas() {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [renderNodes, setRenderNodes] = useState<LayoutNode[]>([]);
  const animationRef = useRef<number | null>(null);
  const layoutNodesRef = useRef<LayoutNode[]>([]);

  const { nodes: storeNodes, edges, selectObserver, viewMode, setClusters } = useTopologyStore();

  // Sync store nodes to layout ref (no re-render trigger)
  useEffect(() => {
    const currentIds = layoutNodesRef.current.map(n => n.id).sort().join(',');
    const newIds = storeNodes.map(n => n.id).sort().join(',');

    if (currentIds !== newIds || layoutNodesRef.current.length === 0) {
      layoutNodesRef.current = storeNodes.map((sn) => {
        const existing = layoutNodesRef.current.find((n) => n.id === sn.id);
        if (existing) {
          return { ...existing, ...sn };
        }
        return { ...sn, vx: 0, vy: 0, x: dimensions.width / 2 + (Math.random() - 0.5) * 200, y: dimensions.height / 2 + (Math.random() - 0.5) * 200 };
      });
      setRenderNodes([...layoutNodesRef.current]);
    }
  }, [storeNodes, dimensions.width, dimensions.height]);

  // Compute clusters when nodes change
  useEffect(() => {
    if (layoutNodesRef.current.length > 0) {
      const clusters = computeClusters(layoutNodesRef.current, edges);
      setClusters(clusters);
    }
  }, [renderNodes, edges, setClusters]);

  // Force-directed layout using refs (no setState in animation loop)
  useEffect(() => {
    if (layoutNodesRef.current.length === 0) return;

    let frameCount = 0;
    const tick = () => {
      const nodes = layoutNodesRef.current;
      if (nodes.length === 0) return;

      // Repulsion
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = (nodes[j].x || 0) - (nodes[i].x || 0);
          const dy = (nodes[j].y || 0) - (nodes[i].y || 0);
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = 500 / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          nodes[i].vx = (nodes[i].vx || 0) - fx;
          nodes[i].vy = (nodes[i].vy || 0) - fy;
          nodes[j].vx = (nodes[j].vx || 0) + fx;
          nodes[j].vy = (nodes[j].vy || 0) + fy;
        }
      }

      // Attraction along edges
      edges.forEach((edge) => {
        const source = nodes.find((n) => n.id === edge.source);
        const target = nodes.find((n) => n.id === edge.target);
        if (!source || !target) return;
        const dx = (target.x || 0) - (source.x || 0);
        const dy = (target.y || 0) - (source.y || 0);
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - 120) * 0.008 * edge.strength;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        source.vx = (source.vx || 0) + fx;
        source.vy = (source.vy || 0) + fy;
        target.vx = (target.vx || 0) - fx;
        target.vy = (target.vy || 0) - fy;
      });

      // Center gravity + damping + bounds
      nodes.forEach((node) => {
        node.vx = (node.vx || 0) + (dimensions.width / 2 - (node.x || 0)) * 0.001;
        node.vy = (node.vy || 0) + (dimensions.height / 2 - (node.y || 0)) * 0.001;
        node.vx = (node.vx || 0) * 0.85;
        node.vy = (node.vy || 0) * 0.85;
        node.x = (node.x || 0) + (node.vx || 0);
        node.y = (node.y || 0) + (node.vy || 0);
      });

      // Throttled re-render (every 3 frames)
      frameCount++;
      if (frameCount % 3 === 0) {
        setRenderNodes([...layoutNodesRef.current]);
      }

      animationRef.current = requestAnimationFrame(tick);
    };

    animationRef.current = requestAnimationFrame(tick);
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [dimensions, edges, setClusters]);

  const getNodeColor = (status: string) => {
    switch (status) {
      case "active": return "var(--observer-active)";
      case "synced": return "var(--observer-synced)";
      case "repairing": return "var(--observer-repairing)";
      case "degraded": return "var(--observer-degraded)";
      default: return "var(--observer-dormant)";
    }
  };

  return (
    <div className="w-full h-full relative bg-[var(--bg-primary)]">
      <svg ref={svgRef} width="100%" height="100%" viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}>
        {/* Edges */}
        {edges.map((edge, i) => (
          <line
            key={`edge-${i}`}
            x1={renderNodes.find(n => n.id === edge.source)?.x || 0}
            y1={renderNodes.find(n => n.id === edge.source)?.y || 0}
            x2={renderNodes.find(n => n.id === edge.target)?.x || 0}
            y2={renderNodes.find(n => n.id === edge.target)?.y || 0}
            stroke="var(--border-default)"
            strokeWidth={Math.max(1, edge.strength * 3)}
            opacity={0.6}
          />
        ))}

        {/* Nodes */}
        {renderNodes.map((node) => (
          <g key={node.id} transform={`translate(${(node.x || 0) - 12}, ${(node.y || 0) - 12})`}>
            <circle
              r="12"
              fill={getNodeColor(node.status)}
              stroke="var(--bg-primary)"
              strokeWidth="2"
              className="cursor-pointer"
              onClick={() => selectObserver(node.id)}
            />
            <text
              x="16"
              y="4"
              fontSize="10"
              fill="var(--text-primary)"
              className="pointer-events-none"
            >
              {node.label || node.id.slice(0, 6)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}