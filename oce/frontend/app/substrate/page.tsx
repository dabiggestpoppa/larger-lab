"use client";

import MachineStateView from "@/components/substrate/MachineStateView";
import ProcessGraph from "@/components/substrate/ProcessGraph";
import RuntimeInspector from "@/components/substrate/RuntimeInspector";
import FilesystemTopology from "@/components/substrate/FilesystemTopology";
import SandboxMonitor from "@/components/substrate/SandboxMonitor";
import EnvironmentModelView from "@/components/substrate/EnvironmentModelView";
import TerminalExecutionPanel from "@/components/substrate/TerminalExecutionPanel";
import RecoveryTimeline from "@/components/substrate/RecoveryTimeline";

export default function SubstratePage() {
  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <div className="flex items-center gap-2">
          <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
            LOCAL EXECUTION SUBSTRATE
          </h2>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="flex-1 p-4 overflow-auto">
        <div className="grid grid-cols-2 gap-4">
          {/* Row 1 */}
          <div className="bg-[var(--bg-secondary)] rounded-lg">
            <MachineStateView />
          </div>
          <div className="bg-[var(--bg-secondary)] rounded-lg">
            <SandboxMonitor />
          </div>
          
          {/* Row 2 */}
          <div className="bg-[var(--bg-secondary)] rounded-lg">
            <ProcessGraph />
          </div>
          <div className="bg-[var(--bg-secondary)] rounded-lg">
            <RuntimeInspector />
          </div>
          
          {/* Row 3 */}
          <div className="bg-[var(--bg-secondary)] rounded-lg">
            <FilesystemTopology />
          </div>
          <div className="bg-[var(--bg-secondary)] rounded-lg">
            <EnvironmentModelView />
          </div>
          
          {/* Full Width */}
          <div className="col-span-2 bg-[var(--bg-secondary)] rounded-lg">
            <TerminalExecutionPanel />
          </div>
          
          {/* Full Width */}
          <div className="col-span-2 bg-[var(--bg-secondary)] rounded-lg">
            <RecoveryTimeline />
          </div>
        </div>
      </div>
    </div>
  );
}