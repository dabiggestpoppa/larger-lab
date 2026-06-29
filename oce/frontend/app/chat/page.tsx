"use client";

import { useEffect, useRef, useState } from "react";
import { useChatStore, loadMessagesFromStorage, type ChatMessage } from "@/stores/chatStore";

function formatTime(ts: string): string {
  try { return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); } catch { return ""; }
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  if (msg.role === "system") {
    return (
      <div className="flex justify-center my-2">
        <span className="text-[10px] font-mono text-gray-500 bg-gray-800 px-3 py-1 rounded-full">{msg.content}</span>
      </div>
    );
  }
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div className={`max-w-[75%] rounded-lg px-4 py-2.5 ${isUser ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-100 border border-gray-700"}`}>
        <div className="text-xs leading-relaxed whitespace-pre-wrap">{msg.content}</div>
        <div className={`text-[9px] font-mono mt-1 ${isUser ? "text-white/60" : "text-gray-500"}`}>{formatTime(msg.timestamp)}</div>
      </div>
    </div>
  );
}

function StreamStatus() {
  const { streamStatus } = useChatStore();
  if (!streamStatus.active && !streamStatus.detail) return null;

  const colors: Record<string, string> = {
    thinking: "text-yellow-400",
    tool_call: "text-blue-400",
    tool_result: "text-cyan-400",
    responding: "text-green-400",
    error: "text-red-400",
  };
  const c = colors[streamStatus.stage] || "text-gray-400";

  return (
    <div className="flex justify-start mb-3">
      <div className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 max-w-[85%]">
        <div className="flex items-center gap-2">
          {streamStatus.active && <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse shrink-0" />}
          <span className={`text-[11px] font-mono ${c} truncate`}>{streamStatus.detail}</span>
        </div>
        {streamStatus.round && streamStatus.maxRounds && (
          <div className="mt-1.5 h-1 bg-gray-700 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 rounded-full transition-all duration-300" style={{ width: `${(streamStatus.round / streamStatus.maxRounds) * 100}%` }} />
          </div>
        )}
      </div>
    </div>
  );
}

function SessionList() {
  const { sessions, activeSessionId, loadSessions, loadHistory, createSession, deleteSession, isLoading } = useChatStore();
  const [showNew, setShowNew] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  useEffect(() => { loadSessions(); }, [loadSessions]);

  return (
    <div className="w-64 bg-gray-900 border-r border-gray-700 flex flex-col shrink-0">
      <div className="p-3 border-b border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xs font-mono font-bold text-gray-100">SESSIONS</h2>
          <button onClick={() => setShowNew(true)} className="text-[10px] font-mono text-blue-400 hover:underline">+ NEW</button>
        </div>
        {showNew && (
          <div className="flex gap-1 mt-1">
            <input type="text" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} placeholder="Title..."
              className="flex-1 text-[10px] font-mono bg-gray-800 border border-gray-700 rounded px-2 py-1 text-gray-100 outline-none focus:border-blue-500"
              onKeyDown={(e) => e.key === "Enter" && createSession(newTitle || undefined).then(() => { setShowNew(false); setNewTitle(""); })} autoFocus />
            <button onClick={() => { createSession(newTitle || undefined).then(() => { setShowNew(false); setNewTitle(""); }); }}
              className="text-[10px] font-mono bg-blue-600 text-white px-2 py-1 rounded">OK</button>
          </div>
        )}
      </div>
      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="p-3 text-[10px] font-mono text-gray-500">No sessions yet.</div>
        ) : sessions.map((s) => (
          <div key={s.session_id} className={`px-3 py-2.5 cursor-pointer border-b border-gray-700 ${activeSessionId === s.session_id ? "bg-gray-800" : "hover:bg-gray-800"}`}
            onClick={() => loadHistory(s.session_id)}>
            <div className="text-[11px] font-mono text-gray-100 truncate">{s.title}</div>
            <div className="text-[9px] font-mono text-gray-500 mt-0.5">{s.entry_count} msgs</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ChatArea() {
  const { messages, isSending, error, sendMessage, streamStatus } = useChatStore();
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, streamStatus]);

  // Reset isSending on mount in case it was stuck from a previous session
  useEffect(() => {
    useChatStore.setState({ isSending: false, error: null });
  }, []);

  const send = async () => {
    const t = input.trim();
    if (!t || isSending) return;
    setInput("");
    await sendMessage(t);
  };

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && !isSending ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="text-2xl mb-3">PO</div>
            <h2 className="text-sm font-mono font-bold text-gray-100 mb-1">Primary Observer</h2>
            <p className="text-[10px] font-mono text-gray-500 max-w-xs">Chat with PO. Real-time streaming shows live activity.</p>
          </div>
        ) : (
          messages.map((m) => <MessageBubble key={m.message_id} msg={m} />)
        )}
        <StreamStatus />
        {error && <div className="flex justify-center my-2"><span className="text-[10px] font-mono text-red-400 bg-red-400/10 px-3 py-1 rounded-full">{error}</span></div>}
        <div ref={endRef} />
      </div>
      <div className="p-3 border-t border-gray-700">
        <form onSubmit={(e) => { e.preventDefault(); send(); }} className="flex gap-2">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message... (Enter to send)"
            className="flex-1 text-xs font-mono bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 outline-none focus:border-blue-500"
            disabled={isSending} />
          <button type="submit" disabled={!input.trim() || isSending}
            className="px-4 py-2 text-xs font-mono bg-blue-600 text-white rounded-lg hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed">
            {isSending ? "..." : "SEND"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function ChatPage() {
  // Load persisted sessions and messages on mount
  useEffect(() => {
    const store = useChatStore.getState();
    store.loadFromStorage();
    // If there's an active session, load its history
    if (store.activeSessionId) {
      const msgs = loadMessagesFromStorage(store.activeSessionId);
      if (msgs.length > 0) store.setMessages(msgs);
    }
  }, []);

  return (
    <div className="flex h-full bg-gray-950">
      <SessionList />
      <ChatArea />
    </div>
  );
}
