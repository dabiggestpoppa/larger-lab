"use client";

import Link from "next/link";
import { MetricsPanel } from "../components/MetricsPanel";
import { TraceView } from "../components/TraceView";
import { AlertPanel } from "../components/AlertPanel";
import { SystemMap } from "../components/SystemMap";
import { Activity, GitBranch, Bell, Network, LayoutDashboard, ChevronRight } from "lucide-react";

export default function ObservabilityPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Observability</h1>
          <p className="text-sm text-gray-500 mt-1">Real-time system monitoring, event tracing, and alerting</p>
        </div>
        <Link href="/" className="text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1">
          <ChevronRight className="w-3 h-3 rotate-180" /> Back to Overview
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <MetricsPanel />
          <TraceView />
        </div>
        <div className="space-y-6">
          <AlertPanel />
          <SystemMap />
        </div>
      </div>
    </div>
  );
}
