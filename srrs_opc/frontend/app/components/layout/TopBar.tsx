"use client";

export default function TopBar() {
  return (
    <header
      className="flex items-center justify-between px-4 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]"
      style={{ height: "var(--top-bar-height)", gridColumn: "1 / -1" }}
    >
      <div className="flex items-center gap-4">
        <span className="text-xs font-mono font-bold text-[var(--text-primary)]">
          SRRA-OPH
        </span>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          v0.1.0
        </span>
      </div>

      <div className="flex items-center gap-4">
        {/* System Status */}
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[var(--field-stable)] node-pulse" />
          <span className="text-[10px] font-mono text-[var(--text-muted)]">STABLE</span>
        </div>

        {/* Observer Count */}
        <div className="flex items-center gap-1">
          <span className="text-[10px] font-mono text-[var(--text-muted)]">OBS:</span>
          <span className="text-[10px] font-mono text-[var(--observer-active)]">8</span>
        </div>

        {/* Entropy Level */}
        <div className="flex items-center gap-1">
          <span className="text-[10px] font-mono text-[var(--text-muted)]">ENT:</span>
          <span className="text-[10px] font-mono text-[var(--field-stable)]">LOW</span>
        </div>

        {/* Connection Status */}
        <div className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--field-stable)]" />
          <span className="text-[10px] font-mono text-[var(--text-muted)]">CONNECTED</span>
        </div>
      </div>
    </header>
  );
}
