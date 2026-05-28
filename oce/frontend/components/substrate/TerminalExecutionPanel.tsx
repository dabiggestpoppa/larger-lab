"use client";

import { useState } from "react";
import { useSubstrateStore } from "@/stores/substrateStore";

export default function TerminalExecutionPanel() {
  const { processes, addProcess } = useSubstrateStore();
  const [command, setCommand] = useState("");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);

  const executeCommand = async () => {
    if (!command.trim()) return;
    
    setLoading(true);
    setOutput("");
    
    try {
      const res = await fetch("/api/substrate/terminal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command }),
      });
      const data = await res.json();
      setOutput(data.output || data.error || "No output");
    } catch (e) {
      setOutput(`Error: ${e}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold text-gray-200">Terminal Execution</h2>
      
      <div className="space-y-2">
        <div className="flex gap-2">
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="Enter command..."
            className="flex-1 bg-gray-900/50 border border-gray-800 rounded px-2 py-1 font-mono text-xs text-gray-300"
            onKeyDown={(e) => e.key === "Enter" && executeCommand()}
          />
          <button
            onClick={executeCommand}
            disabled={loading || !command.trim()}
            className="px-3 py-1 bg-cyan-900/50 hover:bg-cyan-900/70 disabled:opacity-50 rounded text-xs"
          >
            {loading ? "Running..." : "Execute"}
          </button>
        </div>
        
        {output && (
          <pre className="bg-gray-950/50 border border-gray-800 rounded p-2 font-mono text-xs text-gray-400 max-h-48 overflow-y-auto">
            {output}
          </pre>
        )}
      </div>
      
      <div className="border-t border-gray-800 pt-2">
        <div className="text-xs text-gray-500 mb-1">Active Processes ({processes.length})</div>
        <div className="space-y-1 max-h-32 overflow-y-auto">
          {processes.slice(0, 5).map((p) => (
            <div key={p.id} className="text-xs font-mono text-gray-400">
              {p.name} — {p.status}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}