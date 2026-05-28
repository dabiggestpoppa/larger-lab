"use client";

import { useEffect } from "react";
import { useSubstrateStore } from "@/stores/substrateStore";

export default function SandboxMonitor() {
  const { sandboxes, loading, setLoading, setSandboxes } = useSubstrateStore();

  useEffect(() => {
    const fetchSandboxes = async () => {
      setLoading(true);
      try {
        const res = await fetch("/api/substrate/sandbox");
        const data = await res.json();
        setSandboxes(data.sandboxes || []);
      } catch (e) {
        console.error("Failed to fetch sandboxes:", e);
      } finally {
        setLoading(false);
      }
    };

    fetchSandboxes();
    const interval = setInterval(fetchSandboxes, 5000);
    return () => clearInterval(interval);
  }, [setLoading, setSandboxes]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "text-green-400";
      case "inactive": return "text-gray-400";
      case "error": return "text-red-400";
      case "restricted": return "text-yellow-400";
      default: return "text-gray-400";
    }
  };

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold text-gray-200">Sandbox Monitor</h2>
      
      <div className="space-y-2">
        {sandboxes.map((s) => (
          <div key={s.id} className="bg-gray-900/50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-mono text-gray-300">{s.name}</span>
              <span className={`text-xs ${getStatusColor(s.status)}`}>
                ● {s.status}
              </span>
            </div>
            
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span>Tasks: {s.activeTasks}/{s.maxTasks}</span>
              <span>CPU: {s.resourceUsage.cpu.toFixed(1)}%</span>
              <span>MEM: {s.resourceUsage.memory.toFixed(1)}%</span>
            </div>
            
            <div className="w-full bg-gray-800 rounded-full h-1 mt-2">
              <div 
                className="bg-cyan-400 h-1 rounded-full transition-all"
                style={{ width: `${(s.activeTasks / s.maxTasks) * 100}%` }}
              />
            </div>
          </div>
        ))}
        
        {sandboxes.length === 0 && !loading && (
          <div className="text-xs text-gray-500">No active sandboxes</div>
        )}
      </div>
    </div>
  );
}