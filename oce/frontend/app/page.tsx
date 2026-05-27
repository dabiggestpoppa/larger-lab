"use client";

import { useState, useRef, useEffect, useCallback } from "react";

/* ─── Types ──────────────────────────────────────────────────────────────── */

interface ObserverMeta {
  task_domain?: string;
  complexity?: string;
  routing_path?: string[];
  model?: string;
  agreement?: number;
  spawn_status?: string;
}

interface SystemMeta {
  health?: string;
  continuity_score?: number;
  active_agents?: number;
  total_spawns?: number;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  observer?: ObserverMeta;
  system?: SystemMeta;
  confidence?: number;
}

interface ChatResponse {
  response: string;
  session_id: string;
  continuity_preserved: boolean;
  observer?: ObserverMeta;
  system?: SystemMeta;
  confidence?: number;
}

/* ─── API ─────────────────────────────────────────────────────────────────── */

async function sendChatMessage(message: string): Promise<ChatResponse> {
  try {
    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (response.ok) {
      const data = await response.json();
      return {
        response: data.response || "No response",
        session_id: data.session_id || "new_session",
        continuity_preserved: data.continuity_preserved ?? true,
        observer: data.observer,
        system: data.system,
        confidence: data.confidence,
      };
    }
  } catch (err) {
    console.error("Chat API error:", err);
  }
  return {
    response: "⚠️ Connection error — backend unavailable",
    session_id: "error",
    continuity_preserved: false,
  };
}

async function fetchObserverHealth(): Promise<Record<string, unknown>> {
  try {
    const res = await fetch("http://localhost:8000/observer/health");
    if (res.ok) return await res.json();
  } catch { /* ignore */ }
  return {};
}

/* ─── Markdown-lite renderer ──────────────────────────────────────────────── */

function renderMarkdown(text: string): React.ReactNode[] {
  const lines = text.split("\n");
  const nodes: React.ReactNode[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Bold **text**
    if (line.startsWith("**") && line.endsWith("**")) {
      nodes.push(
        <div key={i} className="font-bold text-[13px] mt-3 mb-0.5 text-text-primary">
          {line.replace(/\*\*/g, "")}
        </div>
      );
      continue;
    }

    // Bold inline **text**
    if (line.includes("**")) {
      const parts = line.split(/(\*\*[^*]+\*\*)/g);
      nodes.push(
        <div key={i} className="leading-relaxed">
          {parts.map((part, j) =>
            part.startsWith("**") && part.endsWith("**") ? (
              <span key={j} className="font-semibold text-text-primary">
                {part.replace(/\*\*/g, "")}
              </span>
            ) : (
              <span key={j}>{part}</span>
            )
          )}
        </div>
      );
      continue;
    }

    // Bullet points
    if (line.match(/^-\s/) || line.match(/^\d+\.\s/)) {
      const content = line.replace(/^[-\d.]+\s/, "");
      nodes.push(
        <div key={i} className="flex gap-2 leading-relaxed pl-2">
          <span className="text-accent-primary shrink-0">•</span>
          <span>{content}</span>
        </div>
      );
      continue;
    }

    // Empty line
    if (line.trim() === "") {
      nodes.push(<div key={i} className="h-2" />);
      continue;
    }

    // Regular text
    nodes.push(
      <div key={i} className="leading-relaxed">
        {line}
      </div>
    );
  }

  return nodes;
}

/* ─── Icons ───────────────────────────────────────────────────────────────── */

function ChatIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function FolderIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  );
}

function PaperclipIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
    </svg>
  );
}

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className={`transition-transform duration-200 ${open ? "rotate-90" : ""}`}>
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

function ActivityIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  );
}

/* ─── Sidebar ─────────────────────────────────────────────────────────────── */

function Sidebar() {
  return (
    <div className="w-[64px] bg-white/70 backdrop-blur-md flex flex-col items-center py-5 shrink-0 border-r border-border-light/60">
      <div className="w-10 h-10 bg-gradient-to-br from-accent-primary to-accent-secondary rounded-xl flex items-center justify-center mb-10 shadow-lg shadow-blue-500/25">
        <span className="text-white text-lg font-bold">O</span>
      </div>
      <nav className="flex-1 flex flex-col items-center gap-2">
        <NavButton icon={<ChatIcon />} label="Chat" active />
        <NavButton icon={<FolderIcon />} label="Projects" />
        <NavButton icon={<SettingsIcon />} label="Settings" />
      </nav>
      <div className="w-9 h-9 rounded-full bg-gradient-to-br from-gray-600 to-gray-800 flex items-center justify-center shadow-md">
        <span className="text-white text-xs font-bold">M</span>
      </div>
    </div>
  );
}

function NavButton({ icon, label, active = false }: { icon: React.ReactNode; label: string; active?: boolean }) {
  const base = "w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200";
  const activeCls = "bg-accent-primary/10 text-accent-primary shadow-sm";
  const inactiveCls = "text-text-muted hover:text-text-secondary hover:bg-gray-100/80";
  return (
    <button title={label} className={`${base} ${active ? activeCls : inactiveCls}`}>
      {icon}
    </button>
  );
}

/* ─── Message Bubble ───────────────────────────────────────────────────────── */

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const [showMeta, setShowMeta] = useState(false);
  const hasObserver = message.observer && !isUser;

  const complexityColor: Record<string, string> = {
    low: "bg-emerald-50 text-emerald-700 border-emerald-200",
    medium: "bg-amber-50 text-amber-700 border-amber-200",
    high: "bg-orange-50 text-orange-700 border-orange-200",
    critical: "bg-red-50 text-red-700 border-red-200",
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4 group`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center mr-3 shrink-0 mt-0.5 shadow-sm">
          <span className="text-white text-[10px] font-bold">O</span>
        </div>
      )}

      <div className={`max-w-[78%] ${isUser ? "" : "flex-1"}`}>
        <div
          className={`px-4 py-3 text-[13.5px] ${
            isUser
              ? "bg-accent-primary text-white rounded-2xl rounded-br-md shadow-sm shadow-blue-500/15"
              : "bg-white text-text-primary rounded-2xl rounded-tl-md border border-border-light/60 shadow-sm"
          }`}
        >
          {isUser ? (
            <div className="leading-relaxed">{message.content}</div>
          ) : (
            <div className="text-[13px]">{renderMarkdown(message.content)}</div>
          )}
        </div>

        {hasObserver && (
          <div className="mt-1.5 ml-1">
            <button
              onClick={() => setShowMeta(!showMeta)}
              className="flex items-center gap-1.5 text-[10px] text-text-muted hover:text-text-secondary transition-colors"
            >
              <ChevronIcon open={showMeta} />
              <ActivityIcon />
              <span>Observer analysis</span>
            </button>

            {showMeta && (
              <div className="mt-2 p-3 bg-bg-tertiary/80 rounded-xl border border-border-light/50 text-[11px] space-y-2">
                <div className="flex flex-wrap gap-1.5">
                  {message.observer?.task_domain && (
                    <span className="px-2 py-0.5 bg-accent-primary/10 text-accent-primary rounded-md font-medium border border-accent-primary/20">
                      {message.observer.task_domain.replace(/_/g, " ")}
                    </span>
                  )}
                  {message.observer?.complexity && (
                    <span className={`px-2 py-0.5 rounded-md font-medium border ${complexityColor[message.observer.complexity] || "bg-gray-50 text-gray-600 border-gray-200"}`}>
                      {message.observer.complexity}
                    </span>
                  )}
                  {message.observer?.model && (
                    <span className="px-2 py-0.5 bg-violet-50 text-violet-700 rounded-md border border-violet-200">
                      {message.observer.model}
                    </span>
                  )}
                  {message.observer?.spawn_status && (
                    <span className="px-2 py-0.5 bg-sky-50 text-sky-700 rounded-md border border-sky-200">
                      {message.observer.spawn_status}
                    </span>
                  )}
                </div>

                {message.observer?.routing_path && message.observer.routing_path.length > 0 && (
                  <div className="flex items-center gap-1 text-text-muted flex-wrap">
                    <span className="font-medium text-text-secondary">Route:</span>
                    <span className="flex items-center gap-0.5 flex-wrap">
                      {message.observer.routing_path.map((obs, idx) => (
                        <span key={idx} className="flex items-center gap-0.5">
                          <span className="px-1.5 py-0.5 bg-white rounded border border-border-light text-text-primary font-mono text-[10px]">
                            {obs}
                          </span>
                          {idx < (message.observer?.routing_path?.length ?? 0) - 1 && (
                            <span className="text-text-muted">→</span>
                          )}
                        </span>
                      ))}
                    </span>
                  </div>
                )}

                <div className="flex items-center gap-3 text-text-muted flex-wrap">
                  {message.observer?.agreement !== undefined && (
                    <span>Agreement: <span className="font-medium text-text-secondary">{(message.observer.agreement * 100).toFixed(0)}%</span></span>
                  )}
                  {message.confidence !== undefined && (
                    <span>Confidence: <span className="font-medium text-text-secondary">{(message.confidence * 100).toFixed(0)}%</span></span>
                  )}
                  {message.system?.continuity_score !== undefined && (
                    <span>Continuity: <span className="font-medium text-text-secondary">{(message.system.continuity_score * 100).toFixed(0)}%</span></span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gray-500 to-gray-700 flex items-center justify-center ml-3 shrink-0 mt-0.5 shadow-sm">
          <span className="text-white text-[10px] font-bold">M</span>
        </div>
      )}
    </div>
  );
}

/* ─── Typing Indicator ─────────────────────────────────────────────────────── */

function TypingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center mr-3 shrink-0 shadow-sm">
        <span className="text-white text-[10px] font-bold">O</span>
      </div>
      <div className="bg-white rounded-2xl rounded-tl-md px-5 py-3.5 flex items-center gap-2 border border-border-light/60 shadow-sm">
        <span className="w-2 h-2 bg-accent-primary/60 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
        <span className="w-2 h-2 bg-accent-primary/60 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
        <span className="w-2 h-2 bg-accent-primary/60 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
        <span className="text-[11px] text-text-muted ml-1">Observer analyzing…</span>
      </div>
    </div>
  );
}

/* ─── Welcome Screen ───────────────────────────────────────────────────────── */

function WelcomeScreen({ onSuggestion }: { onSuggestion: (text: string) => void }) {
  const suggestions = [
    { text: "What can you help me with?", icon: "?", desc: "Overview of capabilities" },
    { text: "Show system status", icon: "◉", desc: "Observer field health" },
    { text: "Run diagnostics", icon: "⚡", desc: "Full system check" },
    { text: "Plan next phase", icon: "▸", desc: "Architecture planning" },
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-8">
      <div className="w-16 h-16 bg-gradient-to-br from-accent-primary to-accent-secondary rounded-2xl flex items-center justify-center mb-6 shadow-xl shadow-blue-500/20">
        <span className="text-white text-2xl font-bold">O</span>
      </div>
      <h1 className="text-xl font-bold text-text-primary mb-2">Observer Online</h1>
      <p className="text-text-secondary text-sm mb-8 text-center max-w-sm leading-relaxed">
        O-1/O-2/O-3 pipeline active. Ask me anything — I classify, route, and respond through the observer field.
      </p>
      <div className="grid grid-cols-2 gap-2.5 w-full max-w-md">
        {suggestions.map((s) => (
          <button
            key={s.text}
            onClick={() => onSuggestion(s.text)}
            className="flex items-start gap-3 px-4 py-3.5 bg-white border border-border-light rounded-xl text-left hover:border-accent-primary/30 hover:shadow-md transition-all group"
          >
            <span className="w-7 h-7 rounded-lg bg-accent-primary/10 text-accent-primary flex items-center justify-center text-xs font-bold shrink-0 group-hover:bg-accent-primary/20 transition-colors">
              {s.icon}
            </span>
            <div>
              <div className="text-sm font-medium text-text-primary">{s.text}</div>
              <div className="text-[11px] text-text-muted mt-0.5">{s.desc}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ─── Right Panel: Observer Status ─────────────────────────────────────────── */

function ObserverPanel() {
  const [health, setHealth] = useState<Record<string, unknown>>({});
  const [expanded, setExpanded] = useState(true);

  const refresh = useCallback(async () => {
    const data = await fetchObserverHealth();
    setHealth(data);
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  const status = (health.status as string) || "unknown";
  const statusColor: Record<string, string> = {
    healthy: "bg-emerald-500",
    degraded: "bg-amber-500",
    recovering: "bg-blue-500",
    failed: "bg-red-500",
  };

  const continuity = (health.continuity_score as number) ?? 1.0;
  const requestCount = (health.request_count as number) ?? 0;

  return (
    <div className="w-[260px] bg-white/50 backdrop-blur-sm border-l border-border-light/60 flex flex-col shrink-0">
      <div className="px-4 py-3 border-b border-border-light/60 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${statusColor[status] || "bg-gray-400"} animate-pulse`} />
          <span className="text-xs font-semibold text-text-primary">Observer Field</span>
        </div>
        <button onClick={() => setExpanded(!expanded)} className="text-text-muted hover:text-text-secondary transition-colors">
          <ChevronIcon open={expanded} />
        </button>
      </div>

      {expanded && (
        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {/* Health */}
          <div className="bg-white rounded-xl border border-border-light/60 p-3">
            <div className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">Health</div>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs text-text-secondary">Status</span>
                <span className="text-xs font-medium text-text-primary capitalize">{status}</span>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-text-muted">Continuity</span>
                  <span className="text-text-secondary font-medium">{(continuity * 100).toFixed(0)}%</span>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-accent-primary to-accent-secondary rounded-full transition-all duration-700"
                    style={{ width: `${continuity * 100}%` }}
                  />
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-text-muted">Requests</span>
                <span className="text-xs font-medium text-text-primary">{requestCount}</span>
              </div>
            </div>
          </div>

          {/* Active Observers */}
          <div className="bg-white rounded-xl border border-border-light/60 p-3">
            <div className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">Active Observers</div>
            <div className="space-y-1.5">
              {["planner", "execution", "memory", "repair"].map((obs) => (
                <div key={obs} className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  <span className="text-xs text-text-secondary font-mono">{obs}</span>
                  <span className="text-[10px] text-text-muted ml-auto">active</span>
                </div>
              ))}
            </div>
          </div>

          {/* O-2 Consensus */}
          <div className="bg-white rounded-xl border border-border-light/60 p-3">
            <div className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">O-2 Consensus</div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-text-muted">Task Types</span>
                <span className="text-text-secondary font-medium">9 categories</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Complexity</span>
                <span className="text-text-secondary font-medium">4 levels</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Routing</span>
                <span className="text-text-secondary font-medium">Dynamic</span>
              </div>
            </div>
          </div>

          {/* O-3 Spawn */}
          <div className="bg-white rounded-xl border border-border-light/60 p-3">
            <div className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">O-3 Spawn Engine</div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-text-muted">Lifecycle</span>
                <span className="text-text-secondary font-medium">6 states</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Boundaries</span>
                <span className="text-text-secondary font-medium">Enforced</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Trace Feedback</span>
                <span className="text-emerald-600 font-medium">Active</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Main Page ────────────────────────────────────────────────────────────── */

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isTyping) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: trimmed,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const chatResponse = await sendChatMessage(trimmed);
      const response: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: chatResponse.response,
        timestamp: new Date(),
        observer: chatResponse.observer,
        system: chatResponse.system,
        confidence: chatResponse.confidence,
      };
      setMessages((prev) => [...prev, response]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "⚠️ Error connecting to OCE backend",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestion = (text: string) => {
    setInput(text);
    inputRef.current?.focus();
  };

  const sendBtnBase = "w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200";
  const sendBtnActive = "bg-accent-primary text-white hover:bg-accent-secondary shadow-sm shadow-blue-500/20";
  const sendBtnDisabled = "bg-bg-tertiary text-text-muted cursor-not-allowed";

  return (
    <div className="h-screen max-h-[100dvh] overflow-hidden flex flex-row bg-bg-primary">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="border-b border-border-light/60 px-6 py-3 flex items-center justify-between shrink-0 bg-white/40 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <h1 className="text-sm font-semibold text-text-primary">OCE Operator Chat</h1>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-accent-primary/10 text-accent-primary font-medium">
              v2.0
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-text-muted">
              O-1 · O-2 · O-3 Active
            </span>
            <button className="w-7 h-7 rounded-lg flex items-center justify-center text-text-muted hover:text-text-secondary hover:bg-bg-tertiary transition-colors">
              <PlusIcon />
            </button>
          </div>
        </header>

        {/* Messages area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Chat */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {messages.length === 0 ? (
              <WelcomeScreen onSuggestion={handleSuggestion} />
            ) : (
              <div className="flex-1 overflow-y-auto px-6 py-5">
                {messages.map((msg) => (
                  <MessageBubble key={msg.id} message={msg} />
                ))}
                {isTyping && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </div>
            )}

            {/* Input */}
            <div className="px-6 pb-4 pt-2 shrink-0">
              <div className="bg-white rounded-2xl p-3 border border-border-light/60 shadow-sm">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Message the observer…"
                  rows={1}
                  className="w-full bg-transparent text-sm text-text-primary placeholder-text-muted resize-none outline-none max-h-28 leading-relaxed"
                  style={{ minHeight: "22px" }}
                />
                <div className="flex items-center justify-between mt-2 pt-2 border-t border-border-light/40">
                  <div className="flex items-center gap-1">
                    <button className="w-7 h-7 rounded-lg flex items-center justify-center text-text-muted hover:text-text-secondary hover:bg-gray-100/60 transition-colors" title="Attach file">
                      <PaperclipIcon />
                    </button>
                  </div>
                  <button
                    onClick={handleSend}
                    disabled={!input.trim() || isTyping}
                    className={`${sendBtnBase} ${input.trim() && !isTyping ? sendBtnActive : sendBtnDisabled}`}
                  >
                    <SendIcon />
                  </button>
                </div>
              </div>
              <p className="text-[10px] text-text-muted text-center mt-2">
                Observer pipeline: O-1 Primary → O-2 Consensus → O-3 Spawn
              </p>
            </div>
          </div>

          {/* Right panel */}
          <ObserverPanel />
        </div>
      </div>
    </div>
  );
}
