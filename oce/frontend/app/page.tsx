"use client";

import { useState, useRef, useEffect } from "react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

function Sidebar() {
  return (
    <div className="w-[70px] bg-white/60 backdrop-blur-sm flex flex-col items-center py-5 shrink-0 border-r border-gray-200/50">
      <div className="w-11 h-11 bg-[#133EBF] rounded-xl flex items-center justify-center mb-10 shadow-lg shadow-blue-500/20">
        <span className="text-white text-xl font-bold">O</span>
      </div>
      <nav className="flex-1 flex flex-col items-center gap-3">
        <NavButton icon={<ChatIcon />} label="Chat" active />
        <NavButton icon={<FolderIcon />} label="Projects" />
        <NavButton icon={<SettingsIcon />} label="Settings" />
      </nav>
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#133EBF] to-[#4F46E5] flex items-center justify-center shadow-md">
        <span className="text-white text-sm font-bold">M</span>
      </div>
    </div>
  );
}

function NavButton({ icon, label, active = false }: { icon: React.ReactNode; label: string; active?: boolean }) {
  const base = "w-11 h-11 rounded-xl flex items-center justify-center transition-all duration-200";
  const activeCls = "bg-[#133EBF]/10 text-[#133EBF]";
  const inactiveCls = "text-gray-400 hover:text-gray-600 hover:bg-gray-100/80";
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
  const bubbleBase = "max-w-[70%] px-4 py-3 text-sm leading-relaxed";
  const userBubble = "bg-[#133EBF] text-white rounded-tl-2xl rounded-tr-2xl rounded-bl-2xl rounded-br-md";
  const assistantBubble = "bg-[#F2F2F2] text-gray-800 rounded-tl-md rounded-tr-2xl rounded-bl-2xl rounded-br-2xl";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-5`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-[#133EBF] flex items-center justify-center mr-3 shrink-0 mt-1">
          <span className="text-white text-xs font-bold">O</span>
        </div>
      )}
      <div className={`${bubbleBase} ${isUser ? userBubble : assistantBubble}`}>
        {message.content}
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-600 to-gray-800 flex items-center justify-center ml-3 shrink-0 mt-1">
          <span className="text-white text-xs font-bold">M</span>
        </div>
      )}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start mb-5">
      <div className="w-8 h-8 rounded-full bg-[#133EBF] flex items-center justify-center mr-3 shrink-0">
        <span className="text-white text-xs font-bold">O</span>
      </div>
      <div className="bg-[#F2F2F2] rounded-tl-md rounded-tr-2xl rounded-bl-2xl rounded-br-2xl px-5 py-3 flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
        <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
        <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
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
      <div className="w-20 h-20 bg-gradient-to-br from-[#133EBF] to-[#4F46E5] rounded-2xl flex items-center justify-center mb-8 shadow-xl shadow-blue-500/25">
        <span className="text-white text-3xl font-bold">O</span>
      </div>
      <h1 className="text-2xl font-bold text-gray-900 mb-3">Good to see you, MAD</h1>
      <p className="text-gray-500 text-sm mb-10 text-center max-w-sm leading-relaxed">
        I am your Operator Continuity Engine. Manage tasks, run diagnostics, and coordinate your team.
      </p>
      <div className="grid grid-cols-2 gap-3 w-full max-w-md">
        {suggestions.map((s) => (
          <button
            key={s.text}
            onClick={() => onSuggestion(s.text)}
            className="flex items-center gap-3 px-4 py-3.5 bg-white border border-gray-200/80 rounded-xl text-sm text-gray-700 hover:border-[#133EBF]/30 hover:bg-[#133EBF]/5 hover:shadow-sm transition-all text-left group"
          >
            <span className="w-6 h-6 rounded-lg bg-[#133EBF]/10 text-[#133EBF] flex items-center justify-center text-xs font-bold group-hover:bg-[#133EBF]/20 transition-colors">
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

  const handleSend = () => {
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

    setTimeout(() => {
      const response: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Received: \"" + trimmed + "\". This is a placeholder — real OCE backend integration goes here.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, response]);
      setIsTyping(false);
    }, 1000);
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
  const sendBtnActive = "bg-[#133EBF] text-white hover:bg-[#1030a0] shadow-sm";
  const sendBtnDisabled = "bg-gray-200 text-gray-400 cursor-not-allowed";

  return (
    <div className="h-screen max-h-[100dvh] overflow-hidden flex flex-row">
      <Sidebar />

      <div className="flex-1 bg-white rounded-tl-[16px] rounded-bl-[16px] overflow-hidden flex flex-col shadow-sm">
        {/* Header */}
        <header className="border-b border-gray-100 px-6 py-3.5 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <h1 className="text-sm font-semibold text-gray-900">OCE Operator</h1>
            <span className="flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200/80 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Online
            </span>
          </div>
          <button className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-colors">
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
          <div className="bg-[#F9F9F9] rounded-2xl p-3.5 border border-gray-200/50">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              rows={1}
              className="w-full bg-transparent text-sm text-gray-800 placeholder-gray-400 resize-none outline-none max-h-32 leading-relaxed"
              style={{ minHeight: "24px" }}
            />
            <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-gray-200/50">
              <button className="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-200/60 transition-colors" title="Attach file">
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
          <p className="text-[10px] text-gray-400 text-center mt-2.5">
            OCE v2.0 — Operator Continuity Engine
          </p>
        </div>
      </div>
    </div>
  );
}
