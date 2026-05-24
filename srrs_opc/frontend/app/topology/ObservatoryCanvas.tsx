"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useTopologyStore, ObserverNode, ObserverEdge } from "../stores/topologyStore";

interface LayoutNode extends ObserverNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

export default function ObservatoryCanvas() {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [nodes, setNodes] = useState<LayoutNode[]>([]);
  const [edges, setEdges] = useState<ObserverEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const animationRef = useRef<number | null>(null);

  const { setNodes: storeSetNodes, setEdges: storeSetEdges, selectObserver, viewMode } = useTopologyStore();

  // Initialize nodes with random positions
  useEffect(() => {
    const initialNodes: LayoutNode[] = [
      { id: "trading_observer", label: "Trading", type: "observer", status: "active", entropy: 0.2, syncScore: 0.9, repairState: "idle", x: 400, y: 300, vx: 0, vy: 0 },
      { id: "repair_observer", label: "Repair", type: "observer", status: "synced", entropy: 0.1, syncScore: 0.95, repairState: "idle", x: 300, y: 200, vx: 0, vy: 0 },
      { id: "planner_observer", label: "Planner", type: "observer", status: "active", entropy: 0.3, syncScore: 0.85, repairState: "idle", x: 500, y: 250, vx: 0, vy: 0 },
      { id: "memory_observer", label: "Memory", type: "observer", status: "synced", entropy: 0.15, syncScore: 0.92, repairState: "idle", x: 350, y: 400, vx: 0, vy: 0 },
      { id: "entropy_observer", label: "Entropy", type: "observer", status: "active", entropy: 0.5, syncScore: 0.7, repairState: "idle", x: 550, y: 350, vx: 0, vy: 0 },
      { id: "gateway_observer", label: "Gateway", type: "observer", status: "dormant", entropy: 0.1, syncScore: 0.8, repairState: "idle", x: 200, y: 300, vx: 0, vy: 0 },
      { id: "security_observer", label: "Security", type: "observer", status: "synced", entropy: 0.25, syncScore: 0.88, repairState: "idle", x: 450, y: 150, vx: 0, vy: 0 },
      { id: "health_observer", label: "Health", type: "observer", status: "active", entropy: 0.35, syncScore: 0.75, repairState: "idle", x: 600, y: 200, vx: 0, vy: 0 },
    ];

    const initialEdges: ObserverEdge[] = [
      { source: "trading_observer", target: "repair_observer", strength: 0.8, type: "sync", syncFlow: 0.7 },
      { source: "trading_observer", target: "planner_observer", strength: 0.6, type: "routing", entropyFlow: 0.2 },
      { source: "repair_observer", target: "memory_observer", strength: 0.7, type: "repair", repairFlow: 0.5 },
      { source: "planner_observer", target: "entropy_observer", strength: 0.5, type: "entropy", entropyFlow: 0.4 },
      { source: "memory_observer", target: "gateway_observer", strength: 0.4, type: "memory" },
      { source: "security_observer", target: "trading_observer", strength: 0.6, type: "sync", syncFlow: 0.6 },
      { source: "health_observer", target: "repair_observer", strength: 0.5, type: "field" },
      { source: "entropy_observer", target: "health_observer", strength: 0.3, type: "entropy", entropyFlow: 0.6 },
    ];

    setNodes(initialNodes);
    setEdges(initialEdges);
    storeSetNodes(initialNodes);
    storeSetEdges(initialEdges);
  }, []);

  // Simple force-directed layout
  useEffect(() => {
    if (nodes.length === 0) return;

    const tick = () => {
      setNodes((prev) => {
        const updated = prev.map((node) => ({ ...node }));

        // Repulsion between all nodes
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
          const force = (dist - 100) * 0.01 * edge.strength;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          source.vx += fx;
          source.vy += fy;
          target.vx -= fx;
          target.vy -= fy;
        });

        // Center gravity
        updated.forEach((node) => {
          node.vx += (dimensions.width / 2 - node.x) * 0.001;
          node.vy += (dimensions.height / 2 - node.y) * 0.001;
          // Damping
          node.vx *= 0.9;
          node.vy *= 0.9;
          node.x += node.vx;
          node.y += node.vy;
          // Bounds
          node.x = Math.max(50, Math.min(dimensions.width - 50, node.x));
          node.y = Math.max(50, Math.min(dimensions.height - 50, node.y));
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

  // Handle resize
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

  const handleNodeClick = useCallback((nodeId: string) => {
    setSelectedNode(nodeId);
    selectObserver(nodeId);
  }, [selectObserver]);

  const getNodeColor = (node: LayoutNode) => {
    if (viewMode === "entropy") {
      return node.entropy > 0.7 ? "#dc2626" : node.entropy > 0.4 ? "#d97706" : "#10b981";
    }
    switch (node.status) {
      case "active": return "#22d3ee";
      case "synced": return "#10b981";
      case "repairing": return "#06b6d4";
      case "entropic": return "#dc2626";
      case "dormant": return "#4b5563";
      case "failed": return "#6b7280";
      default: return "#22d3ee";
    }
  };

  const getEdgeColor = (edge: ObserverEdge) => {
    switch (edge.type) {
      case "sync": return "#10b981";
      case "repair": return "#06b6d4";
      case "entropy": return "#dc2626";
      case "routing": return "#6366f1";
      case "memory": return "#8b5cf6";
      case "field": return "#059669";
      default: return "#4b5563";
    }
  };

  return (
    <svg
      ref={svgRef}
      width="100%"
      height="100%"
      className="bg-[var(--bg-primary)]"
      viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
    >
      {/* Grid background */}
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

      {/* Edges */}
      {edges.map((edge, i) => {
        const source = nodes.find((n) => n.id === edge.source);
        const target = nodes.find((n) => n.id === edge.target);
        if (!source || !target) return null;
        return (
          <line
            key={i}
            x1={source.x}
            y1={source.y}
            x2={target.x}
            y2={target.y}
            stroke={getEdgeColor(edge)}
            strokeWidth={edge.strength * 2}
            opacity={0.4}
          />
        );
      })}

      {/* Nodes */}
      {nodes.map((node) => (
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
            opacity={selectedNode === node.id ? 1 : 0.8}
            stroke={selectedNode === node.id ? "#ffffff" : "none"}
            strokeWidth={selectedNode === node.id ? 2 : 0}
          />
          <text
            x={node.x}
            y={node.y + 18}
            textAnchor="middle"
            className="fill-gray-400"
            style={{ fontSize: "9px", fontFamily: "IBM Plex Mono, monospace" }}
          >
            {node.label}
          </text>
        </g>
      ))}
    </svg>
  );
}
