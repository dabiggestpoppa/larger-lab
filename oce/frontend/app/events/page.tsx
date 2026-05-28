"use client";

import { useState } from "react";

interface EventItem {
  id: string;
  event_type: string;
  source: string;
  timestamp: string;
  payload: Record<string, unknown>;
  priority: number;
}

const mockEvents: EventItem[] = [
  { id: "evt-001", event_type: "TOPOLOGY_CHANGE", source: "observer-core", timestamp: "2026-05-28T08:00:00Z", payload: { nodes_added: 2, edges_removed: 1 }, priority: 0 },
  { id: "evt-002", event_type: "ENTROPY_SPIKE", source: "entropy-monitor", timestamp: "2026-05-28T08:15:00Z", payload: { zone: "alpha", level: 0.72 }, priority: 1 },
  { id: "evt-003", event_type: "REPAIR_TRIGGERED", source: "repair-engine", timestamp: "2026-05-28T08:16:00Z", payload: { target: "obs-003", cascade_depth: 2 }, priority: 1 },
  { id: "evt-004", event_type: "CHECKPOINT_PASS", source: "continuity-checker", timestamp: "2026-05-28T08:30:00Z", payload: { checkpoint: 8, drift: 0.02 }, priority: 0 },
  { id: "evt-005", event_type: "CONSENSUS_REACHED", source: "consensus-engine", timestamp: "2026-05-28T08:45:00Z", payload: { proposal: "exp-005", votes: 7 }, priority: 0 },
];

function EventRow({ event }: { event: EventItem }) {
  const priorityColor =
    event.priority > 1
      ? "border-l-[var(--accent-danger)]"
      : event.priority > 0
      ? "border-l-[var(--accent-warning)]"
      : "border-l-[var(--accent-primary)]";

  return (
    <div className={`border-l-2 ${priorityColor} bg-[var(--bg-tertiary)] rounded-r-lg px-4 py-3 mb-2`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono bg-[var(--bg-secondary)] px-2 py-0.5 rounded text-[var(--accent-primary)]">
            {event.event_type}
          </span>
          <span className="text-sm text-[var(--text-primary)]">{event.source}</span>
        </div>
        <span className="text-xs text-[var(--text-muted)]">
          {new Date(event.timestamp).toLocaleString()}
        </span>
      </div>
      {Object.keys(event.payload).length > 0 && (
        <pre className="text-xs text-[var(--text-muted)] mt-2 overflow-x-auto whitespace-pre-wrap">
          {JSON.stringify(event.payload, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default function EventsPage() {
  const [events] = useState<EventItem[]>(mockEvents);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
          EVENT STREAM
        </h2>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {events.length} events
        </span>
      </div>

      <div className="flex-1 p-4 overflow-y-auto">
        {events.map((event) => (
          <EventRow key={event.id} event={event} />
        ))}
        {events.length === 0 && (
          <div className="flex items-center justify-center h-48">
            <p className="text-xs font-mono text-[var(--text-dim)]">No events recorded</p>
          </div>
        )}
      </div>
    </div>
  );
}