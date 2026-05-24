"use client";

import { useState } from "react";

export default function BottomTimeline() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const totalFrames = 100;

  return (
    <div
      className="flex items-center gap-4 px-4 border-t border-[var(--border-subtle)] bg-[var(--bg-secondary)]"
      style={{ height: "var(--bottom-timeline-height)", gridColumn: "1 / -1" }}
    >
      {/* Playback Controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="w-8 h-8 flex items-center justify-center rounded bg-[var(--bg-tertiary)] text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors text-xs"
        >
          {isPlaying ? "⏸" : "▶"}
        </button>
        <button
          onClick={() => setCurrentFrame(0)}
          className="w-8 h-8 flex items-center justify-center rounded bg-[var(--bg-tertiary)] text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors text-xs"
        >
          ⏮
        </button>
      </div>

      {/* Timeline Scrubber */}
      <div className="flex-1 flex items-center gap-2">
        <span className="text-[10px] font-mono text-[var(--text-muted)] w-8">
          {currentFrame}
        </span>
        <input
          type="range"
          min={0}
          max={totalFrames}
          value={currentFrame}
          onChange={(e) => setCurrentFrame(Number(e.target.value))}
          className="flex-1 h-1 bg-[var(--bg-tertiary)] rounded-full appearance-none cursor-pointer accent-[var(--field-active)]"
        />
        <span className="text-[10px] font-mono text-[var(--text-muted)] w-8">
          {totalFrames}
        </span>
      </div>

      {/* Speed Control */}
      <div className="flex items-center gap-1">
        {[0.25, 0.5, 1, 2, 5].map((speed) => (
          <button
            key={speed}
            className="px-2 py-1 text-[10px] font-mono rounded bg-[var(--bg-tertiary)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
          >
            {speed}x
          </button>
        ))}
      </div>

      {/* Time Display */}
      <div className="text-[10px] font-mono text-[var(--text-muted)] w-24 text-right">
        {new Date().toISOString().slice(11, 19)} UTC
      </div>
    </div>
  );
}
