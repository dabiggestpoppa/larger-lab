"use client";

import { useState } from "react";
import { AlertTriangle, XCircle, ChevronDown, ChevronUp, RefreshCw } from "lucide-react";

interface ErrorBannerProps {
  title: string;
  message: string;
  severity?: "warning" | "error";
  onRetry?: () => void;
  details?: string;
}

export function ErrorBanner({ title, message, severity = "error", onRetry, details }: ErrorBannerProps) {
  const [expanded, setExpanded] = useState(false);
  const [retrying, setRetrying] = useState(false);

  const bgColor = severity === "error" ? "bg-red-900/10 border-red-900/30" : "bg-yellow-900/10 border-yellow-900/30";
  const textColor = severity === "error" ? "text-red-400" : "text-yellow-400";
  const Icon = severity === "error" ? XCircle : AlertTriangle;

  const handleRetry = async () => {
    if (!onRetry) return;
    setRetrying(true);
    try {
      await onRetry();
    } finally {
      setRetrying(false);
    }
  };

  return (
    <div className={`rounded-lg border p-4 ${bgColor}`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 ${textColor} shrink-0 mt-0.5`} />
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-medium ${textColor}`}>{title}</p>
          <p className="text-xs text-gray-500 mt-0.5">{message}</p>
          {details && expanded && (
            <pre className="text-xs text-gray-400 mt-2 bg-[#0a0a0f] rounded p-2 overflow-x-auto whitespace-pre-wrap">
              {details}
            </pre>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {details && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1 rounded hover:bg-white/5 text-gray-500 hover:text-gray-300 transition-colors"
              title={expanded ? "Hide details" : "Show details"}
            >
              {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          )}
          {onRetry && (
            <button
              onClick={handleRetry}
              disabled={retrying}
              className="p-1 rounded hover:bg-white/5 text-gray-500 hover:text-gray-300 transition-colors disabled:opacity-50"
              title="Retry"
            >
              <RefreshCw className={`w-4 h-4 ${retrying ? "animate-spin" : ""}`} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
