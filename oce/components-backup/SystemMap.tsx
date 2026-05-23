"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { Network, Cpu, Activity, Zap } from "lucide-react";
import { api, ObserverStatus } from "../lib/api";

interface NodePosition {
  id: string;
  x: number;
  y: number;
  health: number;
  state: string;
  entropy: number;
}

function getStatusColor(state: string, health: number): string {
  if (state === "destroyed" || state === "suspended") return "#6b7280";
  if (health > 0.7) return "#22c55e";
  if (health > 0.4) return "#eab308";
  return "#ef4444";
}

function getStatusGlow(state: string, health: number): string {
  if (state === "destroyed" || state === "suspended") return "rgba(107,114,128,0.15)";
  if (health > 0.7) return "rgba(34,197,94,0.2)";
  if (health > 0.4) return "rgba(234,179,8,0.2)";
  return "rgba(239,68,68,0.2)";
}

export function SystemMap() {
  const [observers, setObservers] = useState<ObserverStatus[]>([]);
  const [nodes, setNodes] = useState<NodePosition[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const [loading, setLoading] = useState(true);

  const loadObservers = useCallback(async () => {
    try {
      const data = await api.getObservers();
      setObservers(data);
    } catch { /* backend may not be up */ }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadObservers();
    const interval = setInterval(loadObservers, 5000);
    return () => clearInterval(interval);
  }, [loadObservers]);

  // Position nodes in a circle
  useEffect(() => {
    if (observers.length === 0) {
      setNodes([]);
      return;
    }
    const cx = 200;
    const cy = 150;
    const radius = Math.min(120, 40 + observers.length * 15);
    const positioned = observers.map((obs, i) => {
      const angle = (2 * Math.PI * i) / observers.length - Math.PI / 2;
      return {
        id: obs.observer_id,
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
        health: (obs as unknown as Record<string, number>).health_score ?? (1 - obs.entropy),
        state: obs.state,
        entropy: obs.entropy,
      };
    });
    setNodes(positioned);
  }, [observers]);

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw connections between nodes
      if (nodes.length > 1) {
        ctx.strokeStyle = "rgba(99,102,241,0.12)";
        ctx.lineWidth = 1;
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.stroke();
          }
        }
      }

      // Draw center hub
      const cx = 200, cy = 150;
      ctx.beginPath();
      ctx.arc(cx, cy, 12, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(99,102,241,0.15)";
      ctx.fill();
      ctx.strokeStyle = "rgba(99,102,241,0.4)";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.fillStyle = "#818cf8";
      ctx.font = "bold 8px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("OCE", cx, cy);

      // Draw connections to hub
      nodes.forEach((node) => {
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(node.x, node.y);
        const grad = ctx.createLinearGradient(cx, cy, node.x, node.y);
        grad.addColorStop(0, "rgba(99,102,241,0.15)");
        grad.addColorStop(1, `${getStatusColor(node.state, node.health)}22`);
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1;
        ctx.stroke();
      });

      // Draw nodes
      nodes.forEach((node) => {
        const color = getStatusColor(node.state, node.health);
        const glow = getStatusGlow(node.state, node.health);
        const isSelected = selected === node.id;

        // Glow
        if (isSelected) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, 18, 0, Math.PI * 2);
          ctx.fillStyle = glow;
          ctx.fill();
        }

        // Node circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, isSelected ? 10 : 8, 0, Math.PI * 2);
        ctx.fillStyle = "#111118";
        ctx.fill();
        ctx.strokeStyle = color;
        ctx.lineWidth = isSelected ? 2.5 : 1.5;
        ctx.stroke();

        // Health arc
        if (node.health > 0) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, isSelected ? 10 : 8, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * node.health);
          ctx.strokeStyle = color;
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        // Label
        ctx.fillStyle = isSelected ? "#e4e4e7" : "#a1a1aa";
        ctx.font = `${isSelected ? "bold " : ""}9px monospace`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        const label = node.id.length > 12 ? node.id.slice(0, 10) + "…" : node.id;
        ctx.fillText(label, node.x, node.y + (isSelected ? 22 : 18));
      });

      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [nodes, selected]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const clicked = nodes.find((n) => Math.hypot(n.x - x, n.y - y) < 15);
    setSelected(clicked?.id ?? null);
  };

  const selectedNode = nodes.find((n) => n.id === selected);
  const selectedObs = observers.find((o) => o.observer_id === selected);

  if (loading) {
    return (
      <div className="bg-[#111118] border border-[#27272a] rounded-lg p-6 text-center">
        <p className="text-sm text-gray-500 animate-pulse">Loading topology...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-gray-500" />
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">System Topology</h2>
        </div>
        <span className="text-xs text-gray-600">{nodes.length} observers</span>
      </div>

      <div className="bg-[#111118] border border-[#27272a] rounded-lg overflow-hidden">
        <canvas
          ref={canvasRef}
          width={400}
          height={300}
          className="w-full cursor-pointer"
          onClick={handleCanvasClick}
        />
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-gray-500">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-green-500" />
          <span>Healthy (&gt;70%)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-yellow-500" />
          <span>Degraded (40-70%)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-red-500" />
          <span>Critical (&lt;40%)</span>
        </div>
      </div>

      {/* Selected node detail */}
      {selectedNode && selectedObs && (
        <div className="bg-[#111118] border border-indigo-500/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Cpu className="w-4 h-4 text-indigo-400" />
            <span className="text-sm font-mono text-gray-200">{selectedNode.id}</span>
            <span className={`text-xs px-1.5 py-0.5 rounded ${
              selectedNode.state === "active" ? "bg-green-900/30 text-green-400" :
              selectedNode.state === "monitoring" ? "bg-yellow-900/30 text-yellow-400" :
              "bg-gray-800 text-gray-500"
            }`}>
              {selectedNode.state}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-[#1a1a24] rounded p-2 text-center">
              <Activity className="w-3.5 h-3.5 text-blue-400 mx-auto mb-1" />
              <div className="text-sm font-bold text-gray-200">{(selectedNode.health * 100).toFixed(0)}%</div>
              <div className="text-xs text-gray-600">Health</div>
            </div>
            <div className="bg-[#1a1a24] rounded p-2 text-center">
              <Zap className="w-3.5 h-3.5 text-amber-400 mx-auto mb-1" />
              <div className="text-sm font-bold text-gray-200">{selectedNode.entropy.toFixed(3)}</div>
              <div className="text-xs text-gray-600">Entropy</div>
            </div>
            <div className="bg-[#1a1a24] rounded p-2 text-center">
              <Network className="w-3.5 h-3.5 text-purple-400 mx-auto mb-1" />
              <div className="text-sm font-bold text-gray-200">{selectedObs.task || "—"}</div>
              <div className="text-xs text-gray-600">Task</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
