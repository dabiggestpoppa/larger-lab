"use client";

import { useEffect, useState } from "react";
import { GitBranch, CheckCircle, XCircle, Clock, ArrowRight, Search } from "lucide-react";
import { api, Trace } from "../lib/api";

function TraceTimeline({ trace }: { trace: Trace }) {
  const totalLatency = trace.total_latency_ms || 1;

  return (
    <div className="space-y-2">
      {/* Source */}
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span className="bg-[#1a1a24] px-2 py-1 rounded font-mono">{trace.source}</span>
        <span>emitted</span>
        <span className="text-gray-400 font-mono">{trace.event_type}</span>
      </div>

      {/* Hops */}
      {trace.hops.map((hop, i) => {
        const widthPct = Math.max(5, (hop.latency_ms / totalLatency) * 100);
        return (
          <div key={i} className="flex items-center gap-2">
            <ArrowRight className="w-3 h-3 text-gray-600 shrink-0" />
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono text-purple-400">{hop.observer_id}</span>
                <span className="text-xs text-gray-500">{hop.action}</span>
                <span className="text-xs text-gray-600 ml-auto">{hop.latency_ms.toFixed(1)}ms</span>
              </div>
              <div className="h-1.5 bg-[#1a1a24] rounded-full overflow-hidden">
                <div
                  className="h-full bg-purple-500/60 rounded-full"
                  style={{ width: `${widthPct}%` }}
                />
              </div>
            </div>
          </div>
        );
      })}

      {/* Outcome */}
      <div className="flex items-center gap-2 text-xs">
        <ArrowRight className="w-3 h-3 text-gray-600" />
        <span className={`font-mono ${
          trace.outcome === "success" ? "text-green-400" :
          trace.outcome === "error" ? "text-red-400" :
          trace.outcome === "timeout" ? "text-yellow-400" :
          "text-gray-400"
        }`}>
          {trace.outcome.toUpperCase()}
        </span>
        <span className="text-gray-600">· {trace.total_latency_ms.toFixed(1)}ms total</span>
      </div>
    </div>
  );
}

function TraceCard({ trace, onClick }: { trace: Trace; onClick: () => void }) {
  const outcomeIcon = {
    success: <CheckCircle className="w-3.5 h-3.5 text-green-400" />,
    error: <XCircle className="w-3.5 h-3.5 text-red-400" />,
    dropped: <XCircle className="w-3.5 h-3.5 text-gray-500" />,
    timeout: <Clock className="w-3.5 h-3.5 text-yellow-400" />,
    in_progress: <Clock className="w-3.5 h-3.5 text-blue-400 animate-pulse" />,
  }[trace.outcome] || <Clock className="w-3.5 h-3.5 text-gray-500" />;

  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-[#111118] border border-[#27272a] rounded-lg p-3 hover:border-[#3a3a4a] transition-colors"
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {outcomeIcon}
          <span className="text-xs font-mono text-gray-300">{trace.event_type}</span>
        </div>
        <span className="text-xs text-gray-600">{trace.total_latency_ms.toFixed(1)}ms</span>
      </div>
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <GitBranch className="w-3 h-3" />
        <span>{trace.hops.length} hops</span>
        <span>·</span>
        <span>{trace.source}</span>
        <span>·</span>
        <span>{new Date(trace.started_at).toLocaleTimeString()}</span>
      </div>
    </button>
  );
}

export function TraceView() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [selected, setSelected] = useState<Trace | null>(null);
  const [filter, setFilter] = useState<string>("");
  const [outcomeFilter, setOutcomeFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTraces = async () => {
    try {
      const data = await api.getTraces({
        limit: 50,
        outcome: outcomeFilter || undefined,
      });
      setTraces(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load traces");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTraces();
    const interval = setInterval(loadTraces, 10000);
    return () => clearInterval(interval);
  }, [outcomeFilter]);

  const filtered = traces.filter((t) => {
    if (filter && !t.event_type.toLowerCase().includes(filter.toLowerCase()) &&
        !t.source.toLowerCase().includes(filter.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Event Traces</h2>
        <span className="text-xs text-gray-600">{filtered.length} traces</span>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="w-3.5 h-3.5 text-gray-600 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            className="w-full bg-[#111118] border border-[#27272a] rounded-lg pl-9 pr-3 py-2 text-xs text-gray-300 placeholder-gray-600 focus:outline-none focus:border-purple-500"
            placeholder="Filter by type or source..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>
        <select
          className="bg-[#111118] border border-[#27272a] rounded-lg px-3 py-2 text-xs text-gray-400 focus:outline-none"
          value={outcomeFilter}
          onChange={(e) => setOutcomeFilter(e.target.value)}
        >
          <option value="">All outcomes</option>
          <option value="success">Success</option>
          <option value="error">Error</option>
          <option value="timeout">Timeout</option>
          <option value="dropped">Dropped</option>
        </select>
      </div>

      {error && (
        <div className="bg-[#111118] border border-red-900/30 rounded-lg p-3">
          <p className="text-xs text-red-400">{error}</p>
        </div>
      )}

      {loading && (
        <div className="text-center py-8">
          <p className="text-sm text-gray-500 animate-pulse">Loading traces...</p>
        </div>
      )}

      {/* Selected trace detail */}
      {selected && (
        <div className="bg-[#111118] border border-purple-500/30 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-purple-400" />
              <span className="text-sm font-mono text-gray-200">{selected.trace_id.slice(0, 8)}</span>
              <span className="text-xs text-gray-500">{selected.event_type}</span>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              Close
            </button>
          </div>
          <TraceTimeline trace={selected} />
          {selected.error_message && (
            <div className="mt-3 bg-red-900/10 border border-red-900/30 rounded p-2">
              <p className="text-xs text-red-400">{selected.error_message}</p>
            </div>
          )}
        </div>
      )}

      {/* Trace list */}
      <div className="space-y-2 max-h-[500px] overflow-y-auto">
        {filtered.map((trace) => (
          <TraceCard
            key={trace.trace_id}
            trace={trace}
            onClick={() => setSelected(trace)}
          />
        ))}
        {filtered.length === 0 && !loading && (
          <p className="text-sm text-gray-600 text-center py-8">No traces found</p>
        )}
      </div>
    </div>
  );
}
