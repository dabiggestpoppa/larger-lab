"use client";

import { useEffect, useRef, useState } from "react";
import { useTopologyStore, ObserverNode } from "../stores/topologyStore";
import { computeClusters } from "../lib/clustering/sync-clusters";
import { getObserverStyle } from "../lib/observer/state-machine";
import EdgeFlow from "../components/visualization/EdgeFlow";
import EntropyHeatmap from "../components/visualization/EntropyHeatmap";
import RepairWave from "../components/visualization/RepairWave";
import ClusterOverlay from "../components/visualization/ClusterOverlay";

interface LayoutNode extends ObserverNode {
  vx: number;
  vy: number;
}

export default function ObservatoryCanvas() {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [nodes, setNodes] = useState<LayoutNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const animationRef = useRef<number | null>(null);

  const { nodes: storeNodes, edges, selectObserver, viewMode, setClusters } = useTopologyStore();

  // Sync store nodes to local layout nodes
  useEffect(() => {
    setNodes((prev) => {
      return storeNodes.map((sn) => {
        const existing = prev.find((n) => n.id === sn.id);
        if (existing) {
          return { ...existing, ...sn };
        }
        return { ...sn, vx: 0, vy: 0 };
      });
    });
  }, [storeNodes]);

  // Compute clusters when nodes/edges change
  useEffect(() => {
    const clusters = computeClusters(nodes, edges);
    setClusters(clusters);
  }, [nodes, edges, setClusters]);

  // Force-directed layout
  useEffect(() => {
    if (nodes.length === 0) return;

    const tick = () => {
      setNodes((prev) => {
        const updated = prev.map((node) => ({ ...node }));

        // Repulsion
        for (let i = 0; i < updated.length; i++) {
          for (let j = i + 1; j < updated.length; j++) {
            const dx = updated[j].x - updated[i].x;
            const dy = updated[j].y - updated[i].y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = 500 / (dist * dist);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            updated[i].vx -= fx;
            updated[i].vy -= fy;
            updated[j].vx += fx;
            updated[j].vy += fy;
          }
        }

        // Attraction along edges
        edges.forEach((edge) => {
          const source = updated.find((n) => n.id === edge.source);
          const target = updated.find((n) => n.id === edge.target);
          if (!source || !target) return;
          const dx = target.x - source.x;
          const dy = target.y - source.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (dist - 120) * 0.008 * edge.strength;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          source.vx += fx;
          source.vy += fy;
          target.vx -= fx;
          target.vy -= fy;
        });

        // Center gravity + damping + bounds
        updated.forEach((node) => {
          node.vx += (dimensions.width / 2 - node.x) * 0.001;
          node.vy += (dimensions.height / 2 - node.y) * 0.001;
          node.vx *= 0.85;
          node.vy *= 0.85;
          node.x += node.vx;
          node.y += node.vy;
          node.x = Math.max(60, Math.min(dimensions.width - 60, node.x));
          node.y = Math.max(60, Math.min(dimensions.height - 60, node.y));
        });

        return updated;
      });

      animationRef.current = requestAnimationFrame(tick);
    };

    animationRef.current = requestAnimationFrame(tick);
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [nodes.length, edges, dimensions]);

  // Resize handler
  useEffect(() => {
    const handleResize = () => {
      if (svgRef.current) {
        const rect = svgRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width, height: rect.height });
      }
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const handleNodeClick = (nodeId: string) => {
    setSelectedNode(selectedNode === nodeId ? null : nodeId);
    selectObserver(nodeId);
  };

  const getNodeColor = (node: LayoutNode) => {
    const style = getObserverStyle(node.status);
    if (viewMode === "entropy") {
      return node.entropy > 0.7 ? "#dc2626" : node.entropy > 0.4 ? "#d97706" : "#10b981";
    }
    return style.color;
  };

  return (
    <svg
      ref={svgRef}
      width="100%"
      height="100%"
      className="bg-[var(--bg-primary)]"
      viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
    >
      {/* Grid */}
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e1e2e" strokeWidth="0.5" />
        </pattern>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid)" />

      {/* Cluster overlays */}
      <ClusterOverlay />

      {/* Entropy heatmap */}
      {viewMode === "entropy" && <EntropyHeatmap />}

      {/* Edge flow */}
      <EdgeFlow />

      {/* Repair waves */}
      {viewMode === "repair" && <RepairWave />}

      {/* Nodes */}
      {nodes.map((node) => {
        const style = getObserverStyle(node.status);
        return (
          <g
            key={node.id}
            onClick={() => handleNodeClick(node.id)}
            className="cursor-pointer"
            filter={selectedNode === node.id ? "url(#glow)" : undefined}
          >
            <circle
              cx={node.x}
              cy={node.y}
              r={node.status === "active" ? 8 : 6}
              fill={getNodeColor(node)}
              opacity={style.dim ? 0.4 : 0.85}
              stroke={selectedNode === node.id ? "#ffffff" : "none"}
              strokeWidth={selectedNode === node.id ? 2 : 0}
              className={style.pulse ? "node-pulse" : ""}
            />
            <text
              x={node.x}
              y={node.y + 18}
              textAnchor="middle"
              style={{ fontSize: "9px", fontFamily: "IBM Plex Mono, monospace", fill: "#9ca3af" }}
            >
              {node.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
