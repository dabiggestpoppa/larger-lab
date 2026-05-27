"use client";

import { useState, useRef, useEffect } from "react";

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

// API call to OCE backend
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
    response: "Connection error — backend unavailable",
    session_id: "error",
    continuity_preserved: false,
  };
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

function Sidebar() {
  return (
    <div className="w-[70px] bg-white/60 backdrop-blur-sm flex flex-col items-center py-5 shrink-0 border-r border-border-light">
      <div className="w-11 h-11 bg-accent-primary rounded-xl flex items-center justify-center mb-10 shadow-lg shadow-blue-500/20">
        <span className="text-white text-xl font-bold">O</span>
      </div>
      <nav className="flex-1 flex flex-col items-center gap-3">
        <NavButton icon={<ChatIcon />} label="Chat" active />
        <NavButton icon={<FolderIcon />} label="Projects" />
        <NavButton icon={<SettingsIcon />} label="Settings" />
      </nav>
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center shadow-md">
        <span className="text-white text-sm font-bold">M</span>
      </div>
    </div>
  );
}

function NavButton({ icon, label, active = false }: { icon: React.ReactNode; label: string; active?: boolean }) {
  const base = "w-11 h-11 rounded-xl flex items-center justify-center transition-all duration-200";
  const activeCls = "bg-[#133EBF]/10 text-accent-primary";
  const inactiveCls = "text-text-muted hover:text-text-secondary hover:bg-gray-100/80";
  return (
    <button title={label} className={`${base} ${active ? activeCls : inactiveCls}`}>
      {icon}
    </button>
  );
}

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

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const bubbleBase = "max-w-[75%] px-4 py-3 text-sm leading-relaxed";
  const userBubble = "bg-accent-primary text-white rounded-tl-2xl rounded-tr-2xl rounded-bl-2xl rounded-br-md";
  const assistantBubble = "bg-bg-input text-text-primary rounded-tl-md rounded-tr-2xl rounded-bl-2xl rounded-br-2xl border border-border-light";

  const hasObserver = message.observer && !isUser;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-5`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center mr-3 shrink-0 mt-1">
          <span className="text-white text-xs font-bold">O</span>
        </div>
      )}
      <div className={`${bubbleBase} ${isUser ? userBubble : assistantBubble}`}>
        {/* Render multi-line response with markdown-like formatting */}
        <div className="whitespace-pre-wrap">{message.content}</div>

        {/* Observer metadata badge */}
        {hasObserver && (
          <div className="mt-3 pt-3 border-t border-border-light/50 flex flex-wrap gap-2 text-xs">
            {message.observer?.task_domain && (
              <span className="px-2 py-0.5 bg-accent-primary/10 text-accent-primary rounded-md font-medium">
                {message.observer.task_domain.replace("_", " ")}
              </span>
            )}
            {message.observer?.complexity && (
              <span className="px-2 py-0.5 bg-amber-500/10 text-amber-600 rounded-md font-medium">
                {message.observer.complexity}
              </span>
            )}
            {message.observer?.model && (
              <span className="px-2 py-0.5 bg-purple-500/10 text-purple-600 rounded-md">
                {message.observer.model}
              </span>
            )}
            {message.observer?.agreement !== undefined && (
              <span className="px-2 py-0.5 bg-green-500/10 text-green-600 rounded-md">
                agreement: {(message.observer.agreement * 100).toFixed(0)}%
              </span>
            )}
            {message.system?.health && (
              <span className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded-md">
                system: {message.system.health}
              </span>
            )}
          </div>
        )}
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-text-secondary to-text-primary flex items-center justify-center ml-3 shrink-0 mt-1">
          <span className="text-white text-xs font-bold">M</span>
        </div>
      )}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start mb-5">
      <div className="w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center mr-3 shrink-0">
        <span className="text-white text-xs font-bold">O</span>
      </div>
      <div className="bg-bg-input rounded-tl-md rounded-tr-2xl rounded-bl-2xl rounded-br-2xl px-5 py-3 flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
        <span className="w-1.5 h-1.5 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
        <span className="w-1.5 h-1.5 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
      </div>
    </div>
  );
}

function WelcomeScreen({ onSuggestion }: { onSuggestion: (text: string) => void }) {
  const suggestions = [
    { text: "What can you help me with?", icon: "?" },
    { text: "Show system status", icon: "i" },
    { text: "Run diagnostics", icon: "*" },
    { text: "Plan next phase", icon: ">" },
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-8">
      <div className="w-20 h-20 bg-gradient-to-br from-accent-primary to-accent-secondary rounded-2xl flex items-center justify-center mb-8 shadow-lg shadow-blue-500/25">
        <span className="text-white text-3xl font-bold">O</span>
      </div>
      <h1 className="text-2xl font-bold text-text-primary mb-3">Good to see you, MAD</h1>
      <p className="text-text-secondary text-sm mb-10 text-center max-w-sm leading-relaxed">
        I am your Operator Continuity Engine. Manage tasks, run diagnostics, and coordinate your team.
      </p>
      <div className="grid grid-cols-2 gap-3 w-full max-w-md">
        {suggestions.map((s) => (
          <button
            key={s.text}
            onClick={() => onSuggestion(s.text)}
            className="flex items-center gap-3 px-4 py-3.5 bg-bg-secondary border border-border-light rounded-xl text-sm text-text-primary hover:border-[#133EBF]/30 hover:bg-[#133EBF]/5 hover:shadow-sm transition-all text-left group"
          >
            <span className="w-6 h-6 rounded-lg bg-[#133EBF]/10 text-accent-primary flex items-center justify-center text-xs font-bold transition-colors">
              {s.icon}
            </span>
            <span className="font-medium">{s.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

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
    if (!trimmed) return;

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
    } catch (err) {
      const response: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Error connecting to OCE backend",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, response]);
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
  const sendBtnActive = "bg-accent-primary text-white hover:bg-accent-secondary shadow-sm";
  const sendBtnDisabled = "bg-bg-tertiary text-text-muted cursor-not-allowed";

  return (
    <div className="h-screen max-h-[100dvh] overflow-hidden flex flex-row">
      <Sidebar />

      <div className="flex-1 bg-bg-secondary rounded-tl-[16px] rounded-bl-[16px] overflow-hidden flex flex-col shadow-sm">
        {/* Header */}
        <header className="border-b border-border-light px-6 py-3.5 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <h1 className="text-sm font-semibold text-text-primary">OCE Operator</h1>
            <span className="flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-full bg-green-50 text-accent-success border border-green-200/50 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-success animate-pulse" />
              Online
            </span>
          </div>
          <button className="w-8 h-8 rounded-lg flex items-center justify-center text-text-muted hover:text-text-secondary hover:bg-bg-tertiary transition-colors">
            <PlusIcon />
          </button>
        </header>

        {/* Messages */}
        {messages.length === 0 ? (
          <WelcomeScreen onSuggestion={handleSuggestion} />
        ) : (
          <div className="flex-1 overflow-y-auto px-6 py-6">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isTyping && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Input */}
        <div className="px-6 pb-5 pt-2 shrink-0">
          <div className="bg-bg-input rounded-2xl p-3.5 border border-border-light">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              rows={1}
              className="w-full bg-transparent text-sm text-text-primary placeholder-text-muted resize-none outline-none max-h-32 leading-relaxed"
              style={{ minHeight: "24px" }}
            />
            <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-border-light">
              <button className="w-7 h-7 rounded-lg flex items-center justify-center text-text-muted hover:text-text-secondary hover:bg-gray-100/60 transition-colors" title="Attach file">
                <PaperclipIcon />
              </button>
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className={`${sendBtnBase} ${input.trim() ? sendBtnActive : sendBtnDisabled}`}
              >
                <SendIcon />
              </button>
            </div>
          </div>
          <p className="text-[10px] text-text-muted text-center mt-2.5">
            OCE v2.0 — Operator Continuity Engine
          </p>
        </div>
      </div>
    </div>
  );
}
