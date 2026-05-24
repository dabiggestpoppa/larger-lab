"use client";

import { useState } from "react";

export default function PlaybackPage() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [speed, setSpeed] = useState(1);
  const totalDuration = 3600; // 1 hour of replay data

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
          TEMPORAL PLAYBACK
        </h2>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {formatTime(currentTime)} / {formatTime(totalDuration)}
        </span>
      </div>

      <div className="flex-1 p-4 overflow-y-auto observatory-scroll">
        {/* Playback Controls */}
        <div className="flex items-center justify-center gap-4 mb-6">
          <button
            onClick={() => setCurrentTime(0)}
            className="w-10 h-10 flex items-center justify-center rounded bg-[var(--bg-tertiary)] text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors"
          >
            ⏮
          </button>
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="w-12 h-12 flex items-center justify-center rounded bg-[var(--field-active)] text-[var(--bg-primary)] hover:opacity-80 transition-opacity text-lg"
          >
            {isPlaying ? "⏸" : "▶"}
          </button>
          <button
            onClick={() => setCurrentTime(totalDuration)}
            className="w-10 h-10 flex items-center justify-center rounded bg-[var(--bg-tertiary)] text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors"
          >
            ⏭
          </button>
        </div>

        {/* Speed Control */}
        <div className="flex items-center justify-center gap-2 mb-6">
          <span className="text-[10px] font-mono text-[var(--text-muted)]">SPEED:</span>
          {[0.25, 0.5, 1, 2, 5, 10].map((s) => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              className={`px-3 py-1 text-[10px] font-mono rounded transition-colors ${
                speed === s
                  ? "bg-[var(--field-active)] text-[var(--bg-primary)]"
                  : "bg-[var(--bg-tertiary)] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              }`}
            >
              {s}x
            </button>
          ))}
        </div>

        {/* Timeline Visualization */}
        <div className="p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono text-[var(--text-muted)]">TIMELINE</span>
            <span className="text-[10px] font-mono text-[var(--text-muted)]">
              {isPlaying ? "PLAYING" : "PAUSED"}
            </span>
          </div>

          {/* Event density bar */}
          <div className="h-8 bg-[var(--bg-tertiary)] rounded-full overflow-hidden relative">
            <div
              className="h-full bg-[var(--field-active)] opacity-30"
              style={{ width: `${(currentTime / totalDuration) * 100}%` }}
            />
            {/* Event markers */}
            {Array.from({ length: 20 }).map((_, i) => (
              <div
                key={i}
                className="absolute top-0 bottom-0 w-0.5 bg-[var(--field-warning)]"
                style={{ left: `${(i / 20) * 100}%` }}
              />
            ))}
            {/* Playhead */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-[var(--field-active)]"
              style={{ left: `${(currentTime / totalDuration) * 100}%` }}
            />
          </div>

          <div className="flex justify-between mt-1">
            <span className="text-[10px] font-mono text-[var(--text-dim)]">00:00:00</span>
            <span className="text-[10px] font-mono text-[var(--text-dim)]">01:00:00</span>
          </div>
        </div>

        {/* Frame Info */}
        <div className="mt-4 p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
          <h3 className="text-[10px] font-mono text-[var(--text-muted)] uppercase mb-2">Current Frame</h3>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <span className="text-[10px] font-mono text-[var(--text-muted)]">Time</span>
              <p className="text-xs font-mono text-[var(--text-primary)]">{formatTime(currentTime)}</p>
            </div>
            <div>
              <span className="text-[10px] font-mono text-[var(--text-muted)]">Frame</span>
              <p className="text-xs font-mono text-[var(--text-primary)]">{Math.floor(currentTime * 30)}</p>
            </div>
            <div>
              <span className="text-[10px] font-mono text-[var(--text-muted)]">Speed</span>
              <p className="text-xs font-mono text-[var(--text-primary)]">{speed}x</p>
            </div>
            <div>
              <span className="text-[10px] font-mono text-[var(--text-muted)]">Status</span>
              <p className={`text-xs font-mono ${isPlaying ? "text-[var(--field-stable)]" : "text-[var(--text-muted)]"}`}>
                {isPlaying ? "PLAYING" : "PAUSED"}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
