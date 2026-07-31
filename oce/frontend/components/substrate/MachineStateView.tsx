"use client";

import { useEffect } from "react";
import { useSubstrateStore } from "@/stores/substrateStore";

export default function MachineStateView() {
  const { systemLoad, loading, setLoading, setSystemLoad } = useSubstrateStore();

  useEffect(() => {
    const fetchState = async () => {
      setLoading(true);
      try {
        const res = await fetch("/api/substrate/state");
        const data = await res.json();
        setSystemLoad({
          cpu: data.cpu_percent || 0,
          memory: data.memory_percent || 0,
          disk: data.disk_percent || 0,
        });
      } catch (e) {
        console.error("Failed to fetch machine state:", e);
      } finally {
        setLoading(false);
      }
    };

    fetchState();
    const interval = setInterval(fetchState, 5000);
    return () => clearInterval(interval);
  }, [setLoading, setSystemLoad]);

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold text-gray-200">Machine State</h2>
      
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-900/50 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">CPU</div>
          <div className="text-2xl font-mono text-cyan-400">{systemLoad.cpu.toFixed(1)}%</div>
          <div className="w-full bg-gray-800 rounded-full h-1 mt-2">
            <div 
              className="bg-cyan-400 h-1 rounded-full transition-all"
              style={{ width: `${systemLoad.cpu}%` }}
            />
          </div>
        </div>
        
        <div className="bg-gray-900/50 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">Memory</div>
          <div className="text-2xl font-mono text-purple-400">{systemLoad.memory.toFixed(1)}%</div>
          <div className="w-full bg-gray-800 rounded-full h-1 mt-2">
            <div 
              className="bg-purple-400 h-1 rounded-full transition-all"
              style={{ width: `${systemLoad.memory}%` }}
            />
          </div>
        </div>
        
        <div className="bg-gray-900/50 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">Disk</div>
          <div className="text-2xl font-mono text-green-400">{systemLoad.disk.toFixed(1)}%</div>
          <div className="w-full bg-gray-800 rounded-full h-1 mt-2">
            <div 
              className="bg-green-400 h-1 rounded-full transition-all"
              style={{ width: `${systemLoad.disk}%` }}
            />
          </div>
        </div>
      </div>
      
      {loading && (
        <div className="text-xs text-gray-500">Updating...</div>
      )}
    </div>
  );
}