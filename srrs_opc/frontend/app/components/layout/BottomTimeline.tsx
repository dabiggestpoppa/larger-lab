"use client";

import { useEffect, useRef, useCallback } from "react";
import { useTimelineStore } from "../../stores/timelineStore";

export default function BottomTimeline() {
  const { frames, playback, setPlayback, setCurrentFrame } = useTimelineStore();
  const { isPlaying, isReversed, speed, loop, currentFrame } = playback;
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const totalFrames = frames.length;
  const progress = totalFrames > 1 ? (currentFrame / (totalFrames - 1)) * 100 : 0;

  const advance = useCallback(() => {
    const { currentFrame: cf, totalFrames: tf, loop: lp } = useTimelineStore.getState().playback;
    if (isReversed) {
      if (cf > 0) setCurrentFrame(cf - 1);
      else if (lp) setCurrentFrame(tf - 1);
      else setPlayback({ isPlaying: false });
    } else {
      if (cf < tf - 1) setCurrentFrame(cf + 1);
      else if (lp) setCurrentFrame(0);
      else setPlayback({ isPlaying: false });
    }
  }, [isReversed, setCurrentFrame, setPlayback]);

  // Auto-advance when playing
  useEffect(() => {
    if (isPlaying) {
      const ms = Math.max(100, 1000 / speed);
      intervalRef.current = setInterval(advance, ms);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isPlaying, speed, advance]);

  const eventMarkers = frames
    .map((f, i) => ({ frame: i, hasEvent: f.events.length > 0 }))
    .filter((m) => m.hasEvent);

  return (
    <div
      className="flex items-center gap-3 px-3 border-t border-[var(--border-subtle)] bg-[var(--bg-secondary)] overflow-hidden"
      style={{ height: "var(--bottom-timeline-height)", gridColumn: "1 / -1" }}
    >
      {/* Playback Controls */}
      <div className="flex items-center gap-1 shrink-0">
        <button
          onClick={() => setCurrentFrame(0)}
          className="w-7 h-7 flex items-center justify-center rounded bg-[var(--bg-tertiary)] text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors text-[10px]"
        >⏮</button>
        <button
          onClick={() => setPlayback({ isReversed: !isReversed })}
          className="w-7 h-7 flex items-center justify-center rounded bg-[var(--bg-tertiary)] text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors text-[10px]"
        >{isReversed ? "←" : "→"}</button>
        <button
          onClick={() => setPlayback({ isPlaying: !isPlaying })}
          className={`w-8 h-8 flex items-center justify-center rounded text-[var(--bg-primary)] transition-colors text-xs ${
            isPlaying ? "bg-[var(--field-warning)]" : "bg-[var(--field-active)]"
          }`}
        >{isPlaying ? "⏸" : "▶"}</button>
        <button
          onClick={() => setCurrentFrame(totalFrames - 1)}
          className="w-7 h-7 flex items-center justify-center rounded bg-[var(--bg-tertiary)] text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors text-[10px]"
        >⏭</button>
      </div>

      {/* Speed */}
      <div className="flex items-center gap-1 shrink-0">
        <span className="text-[9px] font-mono text-[var(--text-muted)]">SPD</span>
        {[0.25, 0.5, 1, 2, 5].map((s) => (
          <button
            key={s}
            onClick={() => setPlayback({ speed: s })}
            className={`px-1.5 py-0.5 text-[9px] font-mono rounded transition-colors ${
              speed === s ? "bg-[var(--bg-elevated)] text-[var(--field-active)]" : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >{s}x</button>
        ))}
      </div>

      {/* Scrubber */}
      <div className="flex-1 flex items-center gap-2 min-w-0">
        <span className="text-[9px] font-mono text-[var(--text-muted)] w-6 text-right shrink-0">{currentFrame}</span>
        <div
          className="flex-1 relative h-6 bg-[var(--bg-tertiary)] rounded-full overflow-hidden cursor-pointer"
          onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const pct = (e.clientX - rect.left) / rect.width;
            setCurrentFrame(Math.round(pct * (totalFrames - 1)));
          }}
        >
          <div className="absolute top-0 left-0 h-full bg-[var(--field-active)] opacity-20" style={{ width: `${progress}%` }} />
          {eventMarkers.map((m) => (
            <div key={m.frame} className="absolute top-0 bottom-0 w-0.5 bg-[var(--field-warning)]" style={{ left: `${(m.frame / (totalFrames - 1)) * 100}%` }} />
          ))}
          <div className="absolute top-0 bottom-0 w-0.5 bg-[var(--field-active)]" style={{ left: `${progress}%` }} />
        </div>
        <span className="text-[9px] font-mono text-[var(--text-muted)] w-6 shrink-0">{totalFrames}</span>
      </div>

      {/* Loop */}
      <button
        onClick={() => setPlayback({ loop: !loop })}
        className={`w-6 h-6 flex items-center justify-center rounded text-[9px] transition-colors shrink-0 ${
          loop ? "bg-[var(--field-active)] text-[var(--bg-primary)]" : "bg-[var(--bg-tertiary)] text-[var(--text-muted)]"
        }`}
      >🔁</button>

      {/* Status */}
      <div className="text-[9px] font-mono text-[var(--text-muted)] w-16 text-right shrink-0">
        {isPlaying ? "PLAYING" : "PAUSED"}
      </div>
    </div>
  );
}
