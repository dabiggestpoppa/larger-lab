"use client";

import { useEffect, useRef, useState } from "react";
import { useChatStore, type ChatMessage } from "@/stores/chatStore";

function formatTime(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  const isSystem = msg.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center my-2">
        <span className="text-[10px] font-mono text-[var(--text-muted)] bg-[var(--bg-tertiary)] px-3 py-1 rounded-full">
          {msg.content}
        </span>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[75%] rounded-lg px-4 py-2.5 ${
          isUser
            ? "bg-[var(--accent-primary)] text-white"
            : "bg-[var(--bg-secondary)] text-[var(--text-primary)] border border-[var(--border-default)]"
        }`}
      >
        <div className="text-xs leading-relaxed whitespace-pre-wrap">
          {msg.content}
        </div>
        <div className="flex items-center justify-between mt-1.5 gap-3">
          <span
            className={`text-[9px] font-mono ${
              isUser ? "text-white/60" : "text-[var(--text-muted)]"
            }`}
          >
            {formatTime(msg.timestamp)}
          </span>
          {msg.task_domain && !isUser && (
            <span
              className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                isUser
                  ? "bg-white/20 text-white/80"
                  : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"
              }`}
            >
              {msg.task_domain}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function SessionList() {
  const {
    sessions,
    activeSessionId,
    loadSessions,
    loadHistory,
    createSession,
    deleteSession,
    isLoading,
  } = useChatStore();
  const [showNew, setShowNew] = useState(false);
  const [newTitle, setNewTitle] = useState("");

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleCreate = async () => {
    await createSession(newTitle || undefined);
    setShowNew(false);
    setNewTitle("");
  };

  return (
    <div className="w-64 bg-[var(--bg-secondary)] border-r border-[var(--border-default)] flex flex-col shrink-0">
      <div className="p-3 border-b border-[var(--border-default)]">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
            SESSIONS
          </h2>
          <button
            onClick={() => setShowNew(true)}
            className="text-[10px] font-mono text-[var(--accent-primary)] hover:underline"
          >
            + NEW
          </button>
        </div>
        {showNew && (
          <div className="flex gap-1 mt-1">
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Session title..."
              className="flex-1 text-[10px] font-mono bg-[var(--bg-tertiary)] border border-[var(--border-default)] rounded px-2 py-1 text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent-primary)]"
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              autoFocus
            />
            <button
              onClick={handleCreate}
              className="text-[10px] font-mono bg-[var(--accent-primary)] text-white px-2 py-1 rounded"
            >
              ✓
            </button>
            <button
              onClick={() => setShowNew(false)}
              className="text-[10px] font-mono text-[var(--text-muted)] px-1"
            >
              ✕
            </button>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading && sessions.length === 0 ? (
          <div className="p-3 text-[10px] font-mono text-[var(--text-muted)]">
            Loading...
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-3 text-[10px] font-mono text-[var(--text-muted)]">
            No sessions yet. Start a conversation.
          </div>
        ) : (
          sessions.map((s) => (
            <div
              key={s.session_id}
              className={`group flex items-start justify-between px-3 py-2.5 cursor-pointer border-b border-[var(--border-default)] transition-colors ${
                activeSessionId === s.session_id
                  ? "bg-[var(--bg-tertiary)]"
                  : "hover:bg-[var(--bg-tertiary)]"
              }`}
              onClick={() => loadHistory(s.session_id)}
            >
              <div className="flex-1 min-w-0">
                <div className="text-[11px] font-mono text-[var(--text-primary)] truncate">
                  {s.title}
                </div>
                <div className="text-[9px] font-mono text-[var(--text-muted)] mt-0.5">
                  {s.entry_count} msgs · {formatTime(s.updated_at)}
                </div>
                {s.last_preview && (
                  <div className="text-[9px] font-mono text-[var(--text-secondary)] truncate mt-0.5">
                    {s.last_preview}
                  </div>
                )}
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteSession(s.session_id);
                }}
                className="opacity-0 group-hover:opacity-100 text-[9px] text-[var(--text-muted)] hover:text-red-400 ml-2 shrink-0"
              >
                ✕
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function ChatArea() {
  const {
    messages,
    activeSessionId,
    isSending,
    error,
    sendMessage,
  } = useChatStore();
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isSending) return;
    setInput("");
    await sendMessage(trimmed);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="text-2xl mb-3">◉</div>
            <h2 className="text-sm font-mono font-bold text-[var(--text-primary)] mb-1">
              Primary Observer
            </h2>
            <p className="text-[10px] font-mono text-[var(--text-muted)] max-w-xs">
              The continuity interface for SRRA/OCE. Ask questions, discuss
              architecture, debug issues, or just talk.
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.message_id} msg={msg} />
          ))
        )}
        {isSending && (
          <div className="flex justify-start mb-3">
            <div className="bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-lg px-4 py-2.5">
              <div className="flex items-center gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-primary)] animate-pulse" />
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-primary)] animate-pulse delay-75" />
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-primary)] animate-pulse delay-150" />
              </div>
            </div>
          </div>
        )}
        {error && (
          <div className="flex justify-center my-2">
            <span className="text-[10px] font-mono text-red-400 bg-red-400/10 px-3 py-1 rounded-full">
              {error}
            </span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-[var(--border-default)]">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message... (Enter to send, Shift+Enter for newline)"
            rows={1}
            className="flex-1 text-xs font-mono bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-lg px-3 py-2 text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent-primary)] resize-none"
            disabled={isSending}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isSending}
            className="px-4 py-2 text-xs font-mono bg-[var(--accent-primary)] text-white rounded-lg hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
          >
            SEND
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <div className="flex h-full">
      <SessionList />
      <ChatArea />
    </div>
  );
}
