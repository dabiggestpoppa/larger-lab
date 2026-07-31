"use client";

import { useEffect } from "react";
import { useSubstrateStore } from "@/stores/substrateStore";

export default function ProcessGraph() {
  const { processes, loading, setLoading, setProcesses } = useSubstrateStore();

  useEffect(() => {
    const fetchProcesses = async () => {
      setLoading(true);
      try {
        const res = await fetch("/api/substrate/processes");
        const data = await res.json();
        setProcesses(data.processes || []);
      } catch (e) {
        console.error("Failed to fetch processes:", e);
      } finally {
        setLoading(false);
      }
    };

    fetchProcesses();
    const interval = setInterval(fetchProcesses, 3000);
    return () => clearInterval(interval);
  }, [setLoading, setProcesses]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running": return "text-green-400";
      case "hung": return "text-red-400";
      case "idle": return "text-yellow-400";
      default: return "text-gray-400";
    }
  };

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold text-gray-200">Process Graph</h2>
      
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {processes.map((p) => (
          <div key={p.id} className="flex items-center justify-between bg-gray-900/50 rounded-lg p-2">
            <div className="flex items-center gap-2">
              <span className={`text-xs ${getStatusColor(p.status)}`}>●</span>
              <span className="text-sm font-mono text-gray-300">{p.name}</span>
            </div>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span>CPU: {p.cpu.toFixed(1)}%</span>
              <span>MEM: {p.memory.toFixed(1)}%</span>
            </div>
          </div>
        ))}
        
        {processes.length === 0 && !loading && (
          <div className="text-xs text-gray-500">No active processes</div>
        )}
      </div>
    </div>
  );
}