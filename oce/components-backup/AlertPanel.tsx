"use client";

import { useEffect, useState } from "react";
import { Bell, BellOff, CheckCircle, AlertTriangle, Info, XCircle, Shield } from "lucide-react";
import { api, Alert } from "../lib/api";
import { useWebSocket } from "../lib/useWebSocket";

function AlertCard({ alert, onAcknowledge }: { alert: Alert; onAcknowledge: (id: string) => void }) {
  const severityConfig = {
    critical: { icon: XCircle, color: "text-red-400", bg: "bg-red-900/10", border: "border-red-900/30" },
    warning: { icon: AlertTriangle, color: "text-yellow-400", bg: "bg-yellow-900/10", border: "border-yellow-900/30" },
    info: { icon: Info, color: "text-blue-400", bg: "bg-blue-900/10", border: "border-blue-900/30" },
  }[alert.severity] || { icon: Info, color: "text-gray-400", bg: "bg-gray-900/10", border: "border-gray-800" };

  const Icon = severityConfig.icon;

  return (
    <div className={`${severityConfig.bg} border ${severityConfig.border} rounded-lg p-3`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2">
          <Icon className={`w-4 h-4 ${severityConfig.color} mt-0.5 shrink-0`} />
          <div>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-semibold ${severityConfig.color}`}>
                {alert.rule_name}
              </span>
              <span className={`text-xs px-1.5 py-0.5 rounded ${
                alert.state === "firing" ? "bg-red-900/30 text-red-400" :
                alert.state === "acknowledged" ? "bg-yellow-900/30 text-yellow-400" :
                "bg-gray-800 text-gray-500"
              }`}>
                {alert.state}
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-1">{alert.message}</p>
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-600">
              <span>Actual: <span className="text-gray-400">{alert.actual_value.toFixed(3)}</span></span>
              <span>Threshold: <span className="text-gray-400">{alert.threshold}</span></span>
              <span>{new Date(alert.fired_at).toLocaleTimeString()}</span>
            </div>
          </div>
        </div>
        {alert.state === "firing" && (
          <button
            onClick={() => onAcknowledge(alert.alert_id)}
            className="shrink-0 bg-[#1a1a24] border border-[#27272a] rounded px-2 py-1 text-xs text-gray-400 hover:text-gray-200 hover:border-gray-600 transition-colors"
          >
            Ack
          </button>
        )}
      </div>
    </div>
  );
}

export function AlertPanel() {
  const wsData = useWebSocket<{ alerts: Alert[]; stats: Record<string, number> }>("/ws/alerts");
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [history, setHistory] = useState<Alert[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [loading, setLoading] = useState(true);

  // Sync from WebSocket or poll
  useEffect(() => {
    if (wsData.data?.alerts) {
      setAlerts(wsData.data.alerts);
      return;
    }
    const poll = async () => {
      try {
        const data = await api.getAlerts();
        setAlerts(data);
      } catch { /* backend may not be up */ }
      setLoading(false);
    };
    poll();
    const interval = setInterval(poll, 10000);
    return () => clearInterval(interval);
  }, [wsData.data]);

  const loadHistory = async () => {
    if (history.length > 0) return;
    try {
      const h = await api.getAlertHistory(20);
      setHistory(h);
    } catch { /* ignore */ }
  };

  const handleAcknowledge = async (alertId: string) => {
    try {
      await api.acknowledgeAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) =>
          a.alert_id === alertId ? { ...a, state: "acknowledged" as const } : a
        )
      );
    } catch { /* ignore */ }
  };

  const criticalCount = alerts.filter((a) => a.severity === "critical" && a.state === "firing").length;
  const warningCount = alerts.filter((a) => a.severity === "warning" && a.state === "firing").length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-gray-500" />
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Alerts</h2>
        </div>
        <div className="flex items-center gap-2">
          {criticalCount > 0 && (
            <span className="bg-red-900/30 text-red-400 text-xs px-2 py-0.5 rounded-full font-medium">
              {criticalCount} critical
            </span>
          )}
          {warningCount > 0 && (
            <span className="bg-yellow-900/30 text-yellow-400 text-xs px-2 py-0.5 rounded-full font-medium">
              {warningCount} warning
            </span>
          )}
          <button
            onClick={() => { setShowHistory(!showHistory); loadHistory(); }}
            className="text-xs text-gray-500 hover:text-gray-300"
          >
            {showHistory ? "Hide" : "Show"} history
          </button>
        </div>
      </div>

      {loading && alerts.length === 0 && (
        <div className="text-center py-8">
          <p className="text-sm text-gray-500 animate-pulse">Loading alerts...</p>
        </div>
      )}

      {!loading && alerts.length === 0 && (
        <div className="bg-[#111118] border border-[#27272a] rounded-lg p-6 text-center">
          <Shield className="w-8 h-8 text-green-500/30 mx-auto mb-2" />
          <p className="text-sm text-gray-500">All systems nominal</p>
          <p className="text-xs text-gray-600 mt-1">No active alerts</p>
        </div>
      )}

      {/* Active alerts */}
      <div className="space-y-2">
        {alerts.map((alert) => (
          <AlertCard key={alert.alert_id} alert={alert} onAcknowledge={handleAcknowledge} />
        ))}
      </div>

      {/* History */}
      {showHistory && history.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs text-gray-600 uppercase tracking-wider">Recent History</h3>
          {history.slice(0, 10).map((alert) => (
            <div key={alert.alert_id} className="bg-[#111118] border border-[#27272a] rounded-lg p-2 opacity-60">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">{alert.rule_name}</span>
                <span className="text-xs text-gray-600">{alert.state} · {new Date(alert.fired_at).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
