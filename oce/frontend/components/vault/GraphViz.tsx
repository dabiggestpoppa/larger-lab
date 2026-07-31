"use client";

import { useEffect, useState, useRef, useCallback } from "react";

interface GraphNode {
  id: string;
  label: string;
  category: string;
  connections: number;
}

interface GraphEdge {
  source: string;
  target: string;
  label?: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface GraphVizProps {
  onNodeSelect?: (node: GraphNode) => void;
}

export default function GraphViz({ onNodeSelect }: GraphVizProps) {
  const [data, setData] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [zoom, setZoom] = useState(1);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const nodePositions = useRef<Map<string, { x: number; y: number }>>(new Map());

  const fetchGraph = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/vault/graph");
      if (!res.ok) {
        setData({ nodes: [], edges: [] });
        setError("Graph API not yet available. Waiting for Phase 0C (Linker) completion.");
        return;
      }
      const result = await res.json();
      setData(result);
    } catch {
      setData({ nodes: [], edges: [] });
      setError("Graph API not yet available. Waiting for Phase 0C (Linker) completion.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGraph();
    const interval = setInterval(fetchGraph, 60000);
    return () => clearInterval(interval);
  }, [fetchGraph]);

  // Simple force-directed layout
  useEffect(() => {
    if (data.nodes.length === 0 || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    // Initialize positions in a circle if not set
    data.nodes.forEach((node, i) => {
      if (!nodePositions.current.has(node.id)) {
        const angle = (2 * Math.PI * i) / data.nodes.length;
        const radius = Math.min(width, height) * 0.35;
        nodePositions.current.set(node.id, {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
        });
      }
    });

    // Simple force simulation (3 iterations)
    for (let iter = 0; iter < 3; iter++) {
      data.nodes.forEach((node) => {
        const pos = nodePositions.current.get(node.id);
        if (!pos) return;

        let fx = 0;
        let fy = 0;

        // Repulsion from other nodes
        data.nodes.forEach((other) => {
          if (other.id === node.id) return;
          const otherPos = nodePositions.current.get(other.id);
          if (!otherPos) return;
          const dx = pos.x - otherPos.x;
          const dy = pos.y - otherPos.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = 5000 / (dist * dist);
          fx += (dx / dist) * force;
          fy += (dy / dist) * force;
        });

        // Attraction along edges
        data.edges.forEach((edge) => {
          let otherId: string | null = null;
          if (edge.source === node.id) otherId = edge.target;
          else if (edge.target === node.id) otherId = edge.source;
          if (!otherId) return;

          const otherPos = nodePositions.current.get(otherId);
          if (!otherPos) return;
          const dx = otherPos.x - pos.x;
          const dy = otherPos.y - pos.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = dist * 0.01;
          fx += (dx / dist) * force;
          fy += (dy / dist) * force;
        });

        // Center gravity
        fx += (centerX - pos.x) * 0.001;
        fy += (centerY - pos.y) * 0.001;

        nodePositions.current.set(node.id, {
          x: pos.x + fx * 0.1,
          y: pos.y + fy * 0.1,
        });
      });
    }

    // Draw
    ctx.clearRect(0, 0, width, height);
    ctx.save();
    ctx.scale(zoom, zoom);

    // Draw edges
    ctx.strokeStyle = "rgba(100, 100, 120, 0.4)";
    ctx.lineWidth = 1;
    data.edges.forEach((edge) => {
      const source = nodePositions.current.get(edge.source);
      const target = nodePositions.current.get(edge.target);
      if (!source || !target) return;
      ctx.beginPath();
      ctx.moveTo(source.x, source.y);
      ctx.lineTo(target.x, target.y);
      ctx.stroke();
    });

    // Draw nodes
    const categoryColors: Record<string, string> = {
      doctrine: "#3498db",
      failure: "#e74c3c",
      execution: "#2ecc71",
      skill: "#9b59b6",
      default: "#f39c12",
    };

    data.nodes.forEach((node) => {
      const pos = nodePositions.current.get(node.id);
      if (!pos) return;

      const color = categoryColors[node.category] || categoryColors.default;
      const radius = Math.max(4, Math.min(12, node.connections * 2 + 4));

      // Node circle
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();

      // Highlight selected
      if (selectedNode?.id === node.id) {
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Label
      ctx.fillStyle = "rgba(200, 200, 210, 0.9)";
      ctx.font = "9px monospace";
      ctx.textAlign = "center";
      ctx.fillText(node.label.slice(0, 20), pos.x, pos.y + radius + 12);
    });

    ctx.restore();
  }, [data, selectedNode, zoom]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / zoom;
    const y = (e.clientY - rect.top) / zoom;

    // Find clicked node
    for (const node of data.nodes) {
      const pos = nodePositions.current.get(node.id);
      if (!pos) continue;
      const radius = Math.max(4, Math.min(12, node.connections * 2 + 4));
      const dx = x - pos.x;
      const dy = y - pos.y;
      if (dx * dx + dy * dy < radius * radius) {
        setSelectedNode(node);
        onNodeSelect?.(node);
        return;
      }
    }
    setSelectedNode(null);
  };

  if (loading && data.nodes.length === 0) {
    return (
      <div className="p-4 space-y-4">
        <h2 className="text-lg font-semibold text-gray-200">Knowledge Graph</h2>
        <div className="flex items-center gap-2 text-gray-400">
          <div className="w-4 h-4 border-2 border-gray-600 border-t-cyan-400 rounded-full animate-spin" />
          <span className="text-sm">Loading graph...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
          KNOWLEDGE GRAPH
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setZoom((z) => Math.min(z + 0.2, 3))}
            className="text-[10px] font-mono text-[var(--text-secondary)] hover:text-[var(--accent-primary)]"
          >
            +
          </button>
          <span className="text-[10px] font-mono text-[var(--text-muted)]">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoom((z) => Math.max(z - 0.2, 0.3))}
            className="text-[10px] font-mono text-[var(--text-secondary)] hover:text-[var(--accent-primary)]"
          >
            −
          </button>
          <button
            onClick={fetchGraph}
            className="text-[10px] font-mono text-[var(--text-secondary)] hover:text-[var(--accent-primary)] ml-2"
          >
            REFRESH
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div ref={containerRef} className="flex-1 relative overflow-hidden bg-[var(--bg-primary)]">
        {error && data.nodes.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-gray-500 text-2xl mb-2">🕸️</div>
              <p className="text-xs text-gray-400 max-w-48">{error}</p>
            </div>
          </div>
        ) : data.nodes.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-gray-500 text-2xl mb-2">📊</div>
              <p className="text-xs text-gray-400">
                No graph data yet. Phase 0C (Linker) will populate this.
              </p>
            </div>
          </div>
        ) : (
          <canvas
            ref={canvasRef}
            width={800}
            height={600}
            onClick={handleCanvasClick}
            className="w-full h-full cursor-pointer"
          />
        )}
      </div>

      {/* Selected Node Info */}
      {selectedNode && (
        <div className="border-t border-[var(--border-subtle)] bg-[var(--bg-secondary)] p-3">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-xs font-mono font-bold text-[var(--text-primary)]">
              {selectedNode.label}
            </h3>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-[10px] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            >
              ✕
            </button>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-1 py-0 text-[9px] font-mono bg-[var(--bg-tertiary)] text-[var(--text-secondary)] rounded">
              {selectedNode.category}
            </span>
            <span className="text-[10px] font-mono text-[var(--text-muted)]">
              {selectedNode.connections} connection{selectedNode.connections !== 1 ? "s" : ""}
            </span>
          </div>
        </div>
      )}

      {/* Status Bar */}
      <div className="px-4 py-1 border-t border-[var(--border-subtle)] bg-[var(--bg-tertiary)]">
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {data.nodes.length} nodes · {data.edges.length} edges
        </span>
      </div>
    </div>
  );
}
