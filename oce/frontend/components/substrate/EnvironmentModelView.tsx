"use client";

import { useEffect, useState } from "react";

interface EnvironmentData {
  workspace?: string;
  projects?: Array<{ name: string; path: string; active: boolean }>;
  active_projects?: string[];
  active_workflows?: string[];
  running_environments?: string[];
  system?: { cpu: number; memory: number; disk: number };
  timestamp?: string;
}

export default function EnvironmentModelView() {
  const [environment, setEnvironment] = useState<EnvironmentData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchEnvironment = async () => {
      setLoading(true);
      try {
        const res = await fetch("/api/substrate/environment");
        if (res.ok) {
          const data = await res.json();
          setEnvironment(data);
        }
      } catch (e) {
        console.error("Failed to fetch environment:", e);
      } finally {
        setLoading(false);
      }
    };

    fetchEnvironment();
    const interval = setInterval(fetchEnvironment, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold text-gray-200">Environment Model</h2>
      
      {environment ? (
        <div className="space-y-3 font-mono text-xs">
          <div>
            <span className="text-gray-500">Workspace:</span>
            <span className="ml-2 text-cyan-400">{environment.workspace || "N/A"}</span>
          </div>
          
          <div>
            <span className="text-gray-500">Projects:</span>
            <span className="ml-2 text-green-400">{environment.projects?.length || 0}</span>
          </div>

          <div>
            <span className="text-gray-500">Active Projects:</span>
            <span className="ml-2 text-green-400">{environment.active_projects?.length || 0}</span>
          </div>
          
          <div>
            <span className="text-gray-500">Active Workflows:</span>
            <span className="ml-2 text-purple-400">{environment.active_workflows?.length || 0}</span>
          </div>
          
          <div>
            <span className="text-gray-500">Running Environments:</span>
            <span className="ml-2 text-yellow-400">{environment.running_environments?.length || 0}</span>
          </div>

          {environment.system && (
            <div>
              <span className="text-gray-500">System:</span>
              <span className="ml-2 text-cyan-400">
                CPU {environment.system.cpu?.toFixed(1)}% | MEM {environment.system.memory?.toFixed(1)}% | DISK {environment.system.disk?.toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      ) : (
        <div className="text-gray-500">Loading environment...</div>
      )}
      
      {loading && (
        <div className="text-xs text-gray-500">Updating...</div>
      )}
    </div>
  );
}
