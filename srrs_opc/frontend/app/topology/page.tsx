"use client";

import { useEffect, useState } from "react";
import { srraApi, TopologyResponse, TopologyNode, TopologyEdge } from "../lib/api";

function NodeDot({ node, x, y }: { node: TopologyNode; x: number; y: number }) {
  const color =
    node.status === "active"
      ? "#4ade80"
      : node.status === "repairing"
      ? "#facc15"
      : node.type === "patch"
      ? "#6366f1"
      : "#22d3ee";

  return (
    <g>
      <circle cx={x} cy={y} r={node.type === "patch" ? 8 : 5} fill={color} opacity={0.9}>
        <title>{node.label} ({node.status})</title>
      </circle>
      <text
        x={x}
        y={y + 18}
        textAnchor="middle"
        className="fill-gray-400"
        style={{ fontSize: "9px" }}
      >
        {node.label.length > 16 ? node.label.slice(0, 14) + "…" : node.label}
      </text>
    </g>
  );
}

export default function TopologyPage() {
  const [topology, setTopology] = useState<TopologyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTopology = async () => {
    try {
      const data = await srraApi.topology();
      setTopology(data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to fetch topology");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTopology();
    const interval = setInterval(fetchTopology, 30000);
    return () => clearInterval(interval);
  }, []);

  // Simple layout: arrange nodes in a circle
  const layoutNodes = (nodes: TopologyNode[], w: number, h: number) => {
    const cx = w / 2;
    const cy = h / 2;
    const r = Math.min(w, h) * 0.35;
    return nodes.map((node, i) => {
      const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
      return {
        node,
        x: cx + r * Math.cos(angle),
        y: cy + r * Math.sin(angle),
      };
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-10 h-10 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card text-center max-w-md mx-auto mt-20">
        <p className="text-accent-red font-semibold">Error</p>
        <p className="text-gray-400 text-sm mt-2">{error}</p>
      </div>
    );
  }

  const W = 800;
  const H = 500;
  const positioned = topology ? layoutNodes(topology.nodes, W, H) : [];
  const nodeMap = new Map(positioned.map((p) => [p.node.id, p]));

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Topology</h1>
          <p className="text-sm text-gray-500 mt-1">
            {topology?.stats.total_nodes ?? 0} nodes • {topology?.stats.total_edges ?? 0} edges
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-green-400" /> Active
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-yellow-400" /> Repairing
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-400" /> Patch
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" /> Module
          </span>
        </div>
      </div>

      <div className="card topology-container" style={{ height: H }}>
        <svg width="100%" height="100%" viewBox={`0 0 ${W} ${H}`}>
          {/* Edges */}
          {topology?.edges.map((edge: TopologyEdge, i: number) => {
            const src = nodeMap.get(edge.source);
            const tgt = nodeMap.get(edge.target);
            if (!src || !tgt) return null;
            return (
              <line
                key={`edge-${i}`}
                x1={src.x}
                y1={src.y}
                x2={tgt.x}
                y2={tgt.y}
                stroke="#27272a"
                strokeWidth={edge.weight * 2}
                opacity={0.6}
              />
            );
          })}

          {/* Nodes */}
          {positioned.map((p) => (
            <NodeDot key={p.node.id} node={p.node} x={p.x} y={p.y} />
          ))}
        </svg>
      </div>

      {/* Stats */}
      {topology?.stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
          <div className="card text-center">
            <p className="text-xs text-gray-500">Nodes</p>
            <p className="text-xl font-bold text-white">{topology.stats.total_nodes}</p>
          </div>
          <div className="card text-center">
            <p className="text-xs text-gray-500">Edges</p>
            <p className="text-xl font-bold text-white">{topology.stats.total_edges}</p>
          </div>
          <div className="card text-center">
            <p className="text-xs text-gray-500">Patches</p>
            <p className="text-xl font-bold text-accent-blue">{topology.stats.patch_count}</p>
          </div>
          <div className="card text-center">
            <p className="text-xs text-gray-500">Phases</p>
            <p className="text-xl font-bold text-accent-cyan">{topology.stats.phases}</p>
          </div>
        </div>
      )}
    </div>
  );
}
