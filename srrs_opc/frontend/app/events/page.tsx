"use client";

import { useEffect, useState } from "react";
import { srraApi, EventItem } from "../lib/api";

function EventRow({ event }: { event: EventItem }) {
  const priorityColor =
    event.priority > 1
      ? "border-l-red-500"
      : event.priority > 0
      ? "border-l-yellow-500"
      : "border-l-accent-blue";

  return (
    <div className={`border-l-2 ${priorityColor} bg-bg-tertiary/40 rounded-r-lg px-4 py-3 mb-2`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono bg-bg-secondary px-2 py-0.5 rounded text-accent-blue">
            {event.event_type}
          </span>
          <span className="text-sm text-gray-300">{event.source}</span>
        </div>
        <span className="text-xs text-gray-500">
          {new Date(event.timestamp).toLocaleString()}
        </span>
      </div>
      {Object.keys(event.payload).length > 0 && (
        <pre className="text-xs text-gray-500 mt-2 overflow-x-auto whitespace-pre-wrap">
          {JSON.stringify(event.payload, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default function EventsPage() {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>("");

  const fetchEvents = async () => {
    try {
      const data = await srraApi.events(50);
      setEvents(data);
      setError(null);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to fetch events");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-10 h-10 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card text-center max-w-md mx-auto mt-20">
        <p className="text-accent-red font-semibold">Error</p>
        <p className="text-gray-400 text-sm mt-2">{error}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Event Stream</h1>
          <p className="text-sm text-gray-500 mt-1">
            {events.length} events {lastUpdate && `• Updated ${lastUpdate}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="status-dot active animate-pulse-glow" />
          <span className="text-xs text-gray-400">Live (10s)</span>
        </div>
      </div>

      <div className="space-y-0">
        {events.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-gray-500">No events yet</p>
          </div>
        ) : (
          events.map((evt) => <EventRow key={evt.event_id} event={evt} />)
        )}
      </div>
    </div>
  );
}
