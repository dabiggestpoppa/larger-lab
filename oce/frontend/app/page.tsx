"use client";

import { useState, useEffect, useRef, useCallback } from "react";

// ─── Types ───────────────────────────────────────────────────────────────────

interface ObserverStatus {
  observer_id: string;
  state: "active" | "idle" | "monitoring";
  entropy: number;
  task: string;
}

interface AttractorState {
  goal: string;
  confidence: number;
  entropy_pressure: number;
  convergence: number;
}

interface MemoryView {
  trajectory_memory: unknown[];
  structural_memory: unknown;
  repair_memory: unknown[];
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

// ─── API Client ──────────────────────────────────────────────────────────────

const API_BASE = "http://localhost:8000";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ─── Components ──────────────────────────────────────────────────────────────

function ObserverPanel({ observers }: { observers: ObserverStatus[] }) {
  const stateColor = (s: string) =>
    s === "active" ? "text-green-400" : s === "monitoring" ? "text-yellow-400" : "text-gray-500";

  return (
    <div className="bg-[#111118] border border-[#27272a] rounded-lg p-4">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Observers</h2>
      <div className="space-y-2">
        {observers.map((o) => (
          <div key={o.observer_id} className="flex items-center justify-between py-2 px-3 bg-[#1a1a24] rounded">
            <div className="flex items-center gap-3">
              <span className={`text-xs font-mono font-bold ${stateColor(o.state)}`}>
                {o.state.toUpperCase()}
              </span>
              <span className="text-sm text-gray-200">{o.observer_id}</span>
            </div>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span>H: {o.entropy.toFixed(3)}</span>
              <span className="text-gray-400">{o.task}</span>
            </div>
          </div>
        ))}
        {observers.length === 0 && (
          <p className="text-sm text-gray-600 italic">No observers connected</p>
        )}
      </div>
    </div>
  );
}

function AttractorPanel({ attractor }: { attractor: AttractorState | null }) {
  if (!attractor) return null;
  return (
    <div className="bg-[#111118] border border-[#27272a] rounded-lg p-4">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Attractor</h2>
      <p className="text-sm text-gray-200 mb-3">{attractor.goal}</p>
      <div className="grid grid-cols-3 gap-3">
        <Metric label="Confidence" value={attractor.confidence} color="text-indigo-400" />
        <Metric label="Entropy Pressure" value={attractor.entropy_pressure} color="text-amber-400" />
        <Metric label="Convergence" value={attractor.convergence} color="text-green-400" />
      </div>
    </div>
  );
}

function Metric({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-[#1a1a24] rounded p-3 text-center">
      <div className={`text-lg font-bold ${color}`}>{(value * 100).toFixed(0)}%</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </div>
  );
}

function MemoryPanel({ memory }: { memory: MemoryView | null }) {
  if (!memory) return null;
  return (
    <div className="bg-[#111118] border border-[#27272a] rounded-lg p-4">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Memory</h2>
      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="bg-[#1a1a24] rounded p-3">
          <div className="text-lg font-bold text-gray-200">{memory.trajectory_memory.length}</div>
          <div className="text-xs text-gray-500 mt-1">Trajectory</div>
        </div>
        <div className="bg-[#1a1a24] rounded p-3">
          <div className="text-lg font-bold text-gray-200">
            {Array.isArray(memory.structural_memory) ? memory.structural_memory.length : "—"}
          </div>
          <div className="text-xs text-gray-500 mt-1">Structural</div>
        </div>
        <div className="bg-[#1a1a24] rounded p-3">
          <div className="text-lg font-bold text-gray-200">{memory.repair_memory.length}</div>
          <div className="text-xs text-gray-500 mt-1">Repair</div>
        </div>
      </div>
    </div>
  );
}

function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || loading) return;
    const userMsg: ChatMessage = { role: "user", content: input, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = await res.json();
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: data.response || "No response",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error: Could not reach OCE backend", timestamp: new Date().toISOString() },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="bg-[#111118] border border-[#27272a] rounded-lg p-4 flex flex-col h-[500px]">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Continuity Chat</h2>
      <div className="flex-1 overflow-y-auto space-y-3 mb-3">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                m.role === "user" ? "bg-indigo-600 text-white" : "bg-[#1a1a24] text-gray-200"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#1a1a24] rounded-lg px-3 py-2 text-sm text-gray-500 italic">Thinking...</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2">
        <input
          className="flex-1 bg-[#1a1a24] border border-[#27272a] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-indigo-500"
          placeholder="Ask OCE..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function Home() {
  const [observers, setObservers] = useState<ObserverStatus[]>([]);
  const [attractor, setAttractor] = useState<AttractorState | null>(null);
  const [memory, setMemory] = useState<MemoryView | null>(null);
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");
  const wsRef = useRef<WebSocket | null>(null);

  // Poll observers, attractor, memory
  useEffect(() => {
    const poll = async () => {
      try {
        const [obs, att, mem] = await Promise.all([
          fetchJSON<ObserverStatus[]>("/observers"),
          fetchJSON<AttractorState>("/attractor"),
          fetchJSON<MemoryView>("/memory"),
        ]);
        setObservers(obs);
        setAttractor(att);
        setMemory(mem);
      } catch {
        // Backend not reachable yet
      }
    };
    poll();
    const interval = setInterval(poll, 5000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket for real-time events
  useEffect(() => {
    const connect = () => {
      setWsStatus("connecting");
      const ws = new WebSocket("ws://localhost:8000/ws/events");
      ws.onopen = () => setWsStatus("connected");
      ws.onclose = () => {
        setWsStatus("disconnected");
        setTimeout(connect, 3000);
      };
      ws.onerror = () => ws.close();
      ws.onmessage = () => {
        // Could update a live event feed here
      };
      wsRef.current = ws;
    };
    connect();
    return () => wsRef.current?.close();
  }, []);

  return (
    <div className="min-h-screen p-6 max-w-7xl mx-auto">
      {/* Header */}
      <header className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">OCE</h1>
          <p className="text-sm text-gray-500">Operator Continuity Engine — Powered by SRRA-OPH</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">WebSocket:</span>
          <span
            className={`text-xs font-mono font-bold ${
              wsStatus === "connected" ? "text-green-400" : wsStatus === "connecting" ? "text-yellow-400" : "text-red-400"
            }`}
          >
            {wsStatus.toUpperCase()}
          </span>
        </div>
      </header>

      {/* Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column */}
        <div className="space-y-6">
          <ObserverPanel observers={observers} />
          <AttractorPanel attractor={attractor} />
          <MemoryPanel memory={memory} />
        </div>

        {/* Right column — Chat */}
        <div className="lg:col-span-2">
          <ChatPanel />
        </div>
      </div>
    </div>
  );
}
