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
  const [renderNodes, setRenderNodes] = useState<LayoutNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
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
        node.x = Math.max(60, Math.min(dimensions.width - 60, node.x || 0));
        node.y = Math.max(60, Math.min(dimensions.height - 60, node.y || 0));
      });

      // Only trigger re-render every 3 frames (throttle)
      frameCount++;
      if (frameCount % 3 === 0) {
        setRenderNodes([...nodes]);
      }

      animationRef.current = requestAnimationFrame(tick);
    };

    animationRef.current = requestAnimationFrame(tick);
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [edges, dimensions]);

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

      <ClusterOverlay />
      {viewMode === "entropy" && <EntropyHeatmap />}
      <EdgeFlow />
      {viewMode === "repair" && <RepairWave />}

      {renderNodes.map((node) => {
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
