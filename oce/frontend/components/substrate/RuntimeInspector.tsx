"use client";

import { useEffect, useState } from "react";

interface RuntimeMetrics {
  timestamp: string;
  system_load?: {
    cpu: number;
    memory: number;
    disk: number;
    load_avg?: number[];
  };
  bottlenecks?: string[];
  orchestration_pressure?: number;
}

export default function RuntimeInspector() {
  const [metrics, setMetrics] = useState<RuntimeMetrics | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchMetrics = async () => {
      setLoading(true);
      try {
        const res = await fetch("/api/substrate/inspector");
        if (res.ok) {
          const data = await res.json();
          setMetrics(data);
        }
      } catch (e) {
        console.error("Failed to fetch runtime metrics:", e);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const cpu = metrics?.system_load?.cpu ?? 0;
  const memory = metrics?.system_load?.memory ?? 0;
  const disk = metrics?.system_load?.disk ?? 0;
  const bottlenecks = metrics?.bottlenecks ?? [];

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold text-gray-200">Runtime Inspector</h2>
      
      <div className="space-y-3">
        <div>
          <div className="text-xs text-gray-500 mb-1">System Load</div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <span>CPU: <span className="text-cyan-400">{cpu.toFixed(1)}%</span></span>
            <span>MEM: <span className="text-purple-400">{memory.toFixed(1)}%</span></span>
            <span>DISK: <span className="text-green-400">{disk.toFixed(1)}%</span></span>
          </div>
        </div>
        
        <div>
          <div className="text-xs text-gray-500 mb-1">Bottlenecks</div>
          {bottlenecks.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {bottlenecks.map((b) => (
                <span key={b} className="px-2 py-1 bg-red-900/30 text-red-400 rounded text-xs">
                  {b}
                </span>
              ))}
            </div>
          ) : (
            <span className="text-xs text-green-400">None detected</span>
          )}
        </div>

        {metrics?.orchestration_pressure !== undefined && (
          <div>
            <div className="text-xs text-gray-500 mb-1">Orchestration Pressure</div>
            <span className="text-xs text-yellow-400">{metrics.orchestration_pressure.toFixed(2)}</span>
          </div>
        )}
        
        {loading && (
          <div className="text-xs text-gray-500">Inspecting...</div>
        )}
      </div>
    </div>
  );
}
