"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useResearchStore } from "@/stores/researchStore";

interface GraphNode {
  id: string;
  label: string;
  category: string;
  x: number;
  y: number;
  connections: number;
}

interface GraphEdge {
  source: string;
  target: string;
  label?: string;
}

const CATEGORY_COLORS: Record<string, string> = {
  paper: "#60a5fa",
  author: "#34d399",
  concept: "#fbbf24",
  method: "#f472b6",
  institution: "#a78bfa",
  default: "#94a3b8",
};

export default function KnowledgeGraphPage() {
  const { graphNodes, graphEdges, fetchGraph } = useResearchStore();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [filter, setFilter] = useState("");
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  // Layout nodes using simple force-directed approach
  useEffect(() => {
    if (graphNodes.length === 0) {
      setNodes([]);
      setEdges([]);
      return;
    }

    const w = 800;
    const h = 600;
    const centerX = w / 2;
    const centerY = h / 2;

    // Simple circular layout with random jitter
    const laidOut: GraphNode[] = graphNodes.map((n, i) => {
      const angle = (2 * Math.PI * i) / graphNodes.length;
      const radius = Math.min(w, h) * 0.35;
      return {
        ...n,
        x: centerX + radius * Math.cos(angle) + (Math.random() - 0.5) * 40,
        y: centerY + radius * Math.sin(angle) + (Math.random() - 0.5) * 40,
      };
    });

    setNodes(laidOut);
    setEdges(graphEdges);
  }, [graphNodes, graphEdges]);

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.offsetWidth * dpr;
    canvas.height = canvas.offsetHeight * dpr;
    ctx.scale(dpr, dpr);

    const w = canvas.offsetWidth;
    const h = canvas.offsetHeight;

    // Clear
    ctx.fillStyle = "var(--bg-primary)";
    ctx.fillRect(0, 0, w, h);

    ctx.save();
    ctx.translate(offset.x, offset.y);
    ctx.scale(zoom, zoom);

    // Draw edges
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    for (const edge of edges) {
      const src = nodeMap.get(edge.source);
      const dst = nodeMap.get(edge.target);
      if (!src || !dst) continue;

      ctx.beginPath();
      ctx.moveTo(src.x, src.y);
      ctx.lineTo(dst.x, dst.y);
      ctx.strokeStyle = "rgba(148, 163, 184, 0.2)";
      ctx.lineWidth = 0.5;
      ctx.stroke();
    }

    // Draw nodes
    for (const node of nodes) {
      const color = CATEGORY_COLORS[node.category] || CATEGORY_COLORS.default;
      const radius = Math.max(3, Math.min(8, node.connections * 0.5 + 2));

      ctx.beginPath();
      ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();

      if (selectedNode?.id === node.id) {
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Label
      if (zoom > 0.6 || selectedNode?.id === node.id) {
        ctx.fillStyle = "var(--text-secondary)";
        ctx.font = "9px monospace";
        ctx.fillText(node.label.slice(0, 30), node.x + radius + 3, node.y + 3);
      }
    }

    ctx.restore();
  }, [nodes, edges, selectedNode, offset, zoom]);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((z) => Math.max(0.2, Math.min(3, z * delta)));
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
  }, [offset]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragging) return;
    setOffset({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  }, [dragging, dragStart]);

  const handleMouseUp = useCallback(() => {
    setDragging(false);
  }, []);

  const filteredNodes = filter
    ? nodes.filter(
        (n) =>
          n.label.toLowerCase().includes(filter.toLowerCase()) ||
          n.category.toLowerCase().includes(filter.toLowerCase())
      )
    : nodes;

  return (
    <div className="p-6 space-y-4 h-full flex flex-col">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-[var(--text-primary)]">Knowledge Graph</h1>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            {nodes.length} nodes · {edges.length} edges
          </p>
        </div>
        <input
          type="text"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter nodes..."
          className="input text-xs w-48"
        />
      </div>

      <div className="flex-1 flex gap-4 min-h-0">
        {/* Canvas */}
        <div className="flex-1 card overflow-hidden relative">
          <canvas
            ref={canvasRef}
            className="w-full h-full cursor-grab active:cursor-grabbing"
            onWheel={handleWheel}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          />
          <div className="absolute bottom-2 right-2 text-[10px] text-[var(--text-muted)]">
            Scroll to zoom · Drag to pan
          </div>
        </div>

        {/* Side panel */}
        <div className="w-64 space-y-3 overflow-y-auto">
          {/* Legend */}
          <div className="card p-3">
            <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider mb-2">Categories</div>
            {Object.entries(CATEGORY_COLORS).map(([cat, color]) => (
              <div key={cat} className="flex items-center gap-2 text-[10px] text-[var(--text-secondary)] mb-1">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                {cat}
              </div>
            ))}
          </div>

          {/* Selected node */}
          {selectedNode && (
            <div className="card p-3">
              <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider mb-1">Selected</div>
              <div className="text-xs font-semibold text-[var(--text-primary)]">{selectedNode.label}</div>
              <div className="text-[10px] text-[var(--text-muted)] mt-1">
                {selectedNode.category} · {selectedNode.connections} connections
              </div>
            </div>
          )}

          {/* Node list */}
          <div className="card p-3">
            <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider mb-2">
              Nodes ({filteredNodes.length})
            </div>
            <div className="space-y-1 max-h-64 overflow-y-auto">
              {filteredNodes.slice(0, 50).map((n) => (
                <button
                  key={n.id}
                  onClick={() => setSelectedNode(n)}
                  className={`w-full text-left text-[10px] px-2 py-1 rounded truncate ${
                    selectedNode?.id === n.id
                      ? "bg-[var(--accent-primary)] text-white"
                      : "text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]"
                  }`}
                >
                  {n.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
