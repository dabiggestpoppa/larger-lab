"use client";

import { useEffect, useState } from "react";
import { BarChart3, Zap, AlertTriangle, CheckCircle, Clock, TrendingUp, Settings } from "lucide-react";
import { api, ExecutionAnalytics as ExecutionAnalyticsType, ExecutionBottlenecks } from "../lib/api";

function BottleneckCard({ bottleneck }: { bottleneck: { type: string; severity: string; message: string; recommendation: string } }) {
  const severityConfig: Record<string, { color: string; bg: string; border: string }> = {
    critical: { color: "text-red-400", bg: "bg-red-500/5", border: "border-red-500/20" },
    warning: { color: "text-yellow-400", bg: "bg-yellow-500/5", border: "border-yellow-500/20" },
    info: { color: "text-blue-400", bg: "bg-blue-500/5", border: "border-blue-500/20" },
  };
  const c = severityConfig[bottleneck.severity] || severityConfig.info;

  return (
    <div className={`${c.bg} border ${c.border} rounded-lg p-3`}>
      <div className="flex items-center gap-2 mb-1">
        <AlertTriangle className={`w-3.5 h-3.5 ${c.color}`} />
        <span className={`text-xs font-semibold ${c.color}`}>{bottleneck.type.replace(/_/g, " ").toUpperCase()}</span>
        <span className={`text-[10px] px-1.5 py-0.5 rounded ${c.bg} ${c.color} border ${c.border}`}>{bottleneck.severity}</span>
      </div>
      <p className="text-xs text-gray-300 mt-1">{bottleneck.message}</p>
      <p className="text-xs text-gray-500 mt-1 italic">→ {bottleneck.recommendation}</p>
    </div>
  );
}

function TypeAnalyticsRow({ taskType, data }: { taskType: string; data: { total: number; completed: number; failed: number; success_rate: number; avg_latency_ms: number } }) {
  const successPct = (data.success_rate * 100).toFixed(1);
  const barWidth = Math.min(100, data.success_rate * 100);
  const barColor = data.success_rate > 0.8 ? "bg-green-500" : data.success_rate > 0.5 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div className="bg-[#111118] border border-[#27272a] rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-mono text-gray-300">{taskType}</span>
        <span className="text-xs text-gray-500">{data.total} tasks</span>
      </div>
      <div className="h-2 bg-[#1a1a24] rounded-full overflow-hidden mb-2">
        <div className={`h-full ${barColor} rounded-full transition-all`} style={{ width: `${barWidth}%` }} />
      </div>
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-sm font-bold text-green-400">{data.completed}</div>
          <div className="text-[10px] text-gray-600">Success</div>
        </div>
        <div>
          <div className="text-sm font-bold text-red-400">{data.failed}</div>
          <div className="text-[10px] text-gray-600">Failed</div>
        </div>
        <div>
          <div className="text-sm font-bold text-gray-300">{data.avg_latency_ms.toFixed(0)}ms</div>
          <div className="text-[10px] text-gray-600">Avg Latency</div>
        </div>
      </div>
    </div>
  );
}

export function ExecutionAnalytics() {
  const [analytics, setAnalytics] = useState<ExecutionAnalyticsType | null>(null);
  const [bottlenecks, setBottlenecks] = useState<ExecutionBottlenecks | null>(null);
  const [tuning, setTuning] = useState(false);
  const [tuneResult, setTuneResult] = useState<{ previous: number; recommended: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [analyticsData, bottlenecksData] = await Promise.all([
        api.getExecutionAnalytics(),
        api.getExecutionBottlenecks(),
      ]);
      setAnalytics(analyticsData);
      setBottlenecks(bottlenecksData);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleTune = async () => {
    setTuning(true);
    try {
      const result = await api.tuneExecution();
      setTuneResult({ previous: result.previous_workers, recommended: result.recommended_workers });
      await loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Tune failed");
    } finally {
      setTuning(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-[#111118] border border-[#27272a] rounded-lg p-6 text-center">
        <p className="text-sm text-gray-500 animate-pulse">Loading analytics...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-gray-500" />
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Execution Analytics</h2>
        </div>
        <button
          onClick={handleTune}
          disabled={tuning}
          className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-xs font-medium px-3 py-1.5 rounded-lg"
        >
          <Settings className="w-3 h-3" />
          {tuning ? "Tuning..." : "Auto-Tune"}
        </button>
      </div>

      {error && (
        <div className="bg-[#111118] border border-red-900/30 rounded-lg p-3">
          <p className="text-xs text-red-400">{error}</p>
        </div>
      )}

      {tuneResult && (
        <div className="bg-indigo-500/5 border border-indigo-500/20 rounded-lg p-3 flex items-center gap-2">
          <Zap className="w-4 h-4 text-indigo-400" />
          <span className="text-xs text-gray-300">
            Worker pool tuned: <span className="text-indigo-400 font-bold">{tuneResult.previous}</span> → <span className="text-indigo-400 font-bold">{tuneResult.recommended}</span> workers
          </span>
        </div>
      )}

      {/* Summary Stats */}
      {analytics?.engine_stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="bg-[#111118] border border-[#27272a] rounded-lg p-3 text-center">
            <TrendingUp className="w-4 h-4 text-blue-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-gray-200">{analytics.engine_stats.total_submitted}</div>
            <div className="text-xs text-gray-600">Total Submitted</div>
          </div>
          <div className="bg-[#111118] border border-[#27272a] rounded-lg p-3 text-center">
            <CheckCircle className="w-4 h-4 text-green-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-green-400">{analytics.engine_stats.total_completed}</div>
            <div className="text-xs text-gray-600">Completed</div>
          </div>
          <div className="bg-[#111118] border border-[#27272a] rounded-lg p-3 text-center">
            <AlertTriangle className="w-4 h-4 text-red-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-red-400">{analytics.engine_stats.total_failed}</div>
            <div className="text-xs text-gray-600">Failed</div>
          </div>
          <div className="bg-[#111118] border border-[#27272a] rounded-lg p-3 text-center">
            <Clock className="w-4 h-4 text-yellow-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-yellow-400">{analytics.engine_stats.queue_size}</div>
            <div className="text-xs text-gray-600">Queue Depth</div>
          </div>
        </div>
      )}

      {/* Per-Type Analytics */}
      {analytics?.by_type && Object.keys(analytics.by_type).length > 0 && (
        <div>
          <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-2">By Task Type</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {Object.entries(analytics.by_type).map(([type, data]) => (
              <TypeAnalyticsRow key={type} taskType={type} data={data} />
            ))}
          </div>
        </div>
      )}

      {/* Bottlenecks */}
      <div>
        <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-2">
          Bottlenecks {bottlenecks && !bottlenecks.healthy && <span className="text-red-400">({bottlenecks.bottleneck_count} detected)</span>}
        </h3>
        {bottlenecks?.healthy ? (
          <div className="bg-green-500/5 border border-green-500/20 rounded-lg p-4 text-center">
            <CheckCircle className="w-6 h-6 text-green-400 mx-auto mb-2" />
            <p className="text-sm text-green-400">All systems healthy</p>
            <p className="text-xs text-gray-500 mt-1">No execution bottlenecks detected</p>
          </div>
        ) : (
          <div className="space-y-2">
            {bottlenecks?.bottlenecks.map((b, i) => (
              <BottleneckCard key={i} bottleneck={b} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
