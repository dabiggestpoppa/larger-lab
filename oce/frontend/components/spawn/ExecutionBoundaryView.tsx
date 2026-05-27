
"use client";

interface BoundaryConfig {
  allowed_tools: string[];
  max_file_writes: number;
  max_terminal_commands: number;
  max_network_requests: number;
  allow_network: boolean;
  allow_file_system: boolean;
  sandbox_enabled: boolean;
}

interface BoundaryUsage {
  file_writes: number;
  terminal_commands: number;
  network_requests: number;
}

export default function ExecutionBoundaryView() {
  // Placeholder — would be connected to real data via props or store
  const boundary: BoundaryConfig | null = null;
  const usage: BoundaryUsage = { file_writes: 0, terminal_commands: 0, network_requests: 0 };

  if (!boundary) {
    return (
      <div className="flex items-center justify-center h-full text-xs text-gray-600">
        Select an agent to view execution boundaries
      </div>
    );
  }

  const usageBar = (used: number, max: number) => {
    const pct = Math.min((used / max) * 100, 100);
    const color = pct > 80 ? "bg-red-500" : pct > 50 ? "bg-yellow-500" : "bg-green-500";
    return (
      <div className="w-full h-1.5 rounded bg-gray-700 overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    );
  };

  return (
    <div className="p-4 space-y-4">
      <h3 className="text-sm font-semibold text-gray-200">Execution Boundaries</h3>

      {/* Usage meters */}
      <div className="space-y-3">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">File Writes</span>
            <span className="text-gray-500">{usage.file_writes}/{boundary.max_file_writes}</span>
          </div>
          {usageBar(usage.file_writes, boundary.max_file_writes)}
        </div>
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">Terminal Commands</span>
            <span className="text-gray-500">{usage.terminal_commands}/{boundary.max_terminal_commands}</span>
          </div>
          {usageBar(usage.terminal_commands, boundary.max_terminal_commands)}
        </div>
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">Network Requests</span>
            <span className="text-gray-500">{usage.network_requests}/{boundary.max_network_requests}</span>
          </div>
          {usageBar(usage.network_requests, boundary.max_network_requests)}
        </div>
      </div>

      {/* Tool scope */}
      <div>
        <span className="text-[10px] uppercase tracking-wider text-gray-500">Allowed Tools</span>
        <div className="flex flex-wrap gap-1 mt-2">
          {boundary.allowed_tools.map((tool) => (
            <span key={tool} className="text-[10px] px-1.5 py-0.5 rounded bg-green-500/10 text-green-400 border border-green-500/20">
              {tool}
            </span>
          ))}
        </div>
      </div>

      {/* Flags */}
      <div className="grid grid-cols-2 gap-2">
        <div className={`p-2 rounded text-xs ${boundary.allow_network ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"}`}>
          Network: {boundary.allow_network ? "Allowed" : "Blocked"}
        </div>
        <div className={`p-2 rounded text-xs ${boundary.allow_file_system ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"}`}>
          Filesystem: {boundary.allow_file_system ? "Allowed" : "Blocked"}
        </div>
        <div className={`p-2 rounded text-xs col-span-2 ${boundary.sandbox_enabled ? "bg-yellow-500/10 text-yellow-400" : "bg-gray-700/50 text-gray-500"}`}>
          Sandbox: {boundary.sandbox_enabled ? "Enabled" : "Disabled"}
        </div>
      </div>
    </div>
  );
}
