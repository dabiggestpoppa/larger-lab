"use client";

import { useState, useRef, useEffect, useCallback } from "react";

/* ─── Types ───────────────────────────────────────────────────────────────── */

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  status?: "sending" | "done" | "error";
}

/* ─── API ─────────────────────────────────────────────────────────────────── */

async function sendMessage(msg: string): Promise<string> {
  try {
    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg }),
    });
    if (res.ok) {
      const data = await res.json();
      return data.response || data.message || "No response";
    }
  } catch {
    // fallback — return error message
  }
  return "I'm having trouble connecting to my backend. Please make sure the OCE server is running on port 8000.";
}

/* ─── Markdown-lite renderer ──────────────────────────────────────────────── */

function renderContent(text: string) {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let inCode = false;
  let codeLines: string[] = [];
  let listItems: { ordered: boolean; content: string }[] = [];
  let listKey = 0;

  const flushList = () => {
    if (listItems.length === 0) return;
    const ordered = listItems[0].ordered;
    const Tag = ordered ? "ol" : "ul";
    elements.push(
      <Tag
        key={`list-${listKey++}`}
        className={`my-2 pl-5 space-y-0.5 ${ordered ? "list-decimal" : "list-disc"}`}
      >
        {listItems.map((item, i) => (
          <li key={i} className="text-[14px] leading-relaxed">
            {item.content}
          </li>
        ))}
      </Tag>
    );
    listItems = [];
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code block toggle
    if (line.startsWith("```")) {
      if (inCode) {
        flushList();
        elements.push(
          <pre
            key={`code-${i}`}
            className="bg-[#1e1e2e] text-[#cdd6f4] rounded-lg p-3 my-2 overflow-x-auto text-[13px] leading-relaxed"
          >
            <code>{codeLines.join("\n")}</code>
          </pre>
        );
        codeLines = [];
        inCode = false;
      } else {
        flushList();
        inCode = true;
      }
      continue;
    }

    if (inCode) {
      codeLines.push(line);
      continue;
    }

    // Headers
    if (line.startsWith("### ")) {
      flushList();
      elements.push(
        <h3 key={i} className="text-[15px] font-semibold mt-3 mb-1">
          {line.slice(4)}
        </h3>
      );
      continue;
    }
    if (line.startsWith("## ")) {
      flushList();
      elements.push(
        <h2 key={i} className="text-[16px] font-semibold mt-3 mb-1">
          {line.slice(3)}
        </h2>
      );
      continue;
    }

    // Bold heading **text**
    if (line.startsWith("**") && line.endsWith("**")) {
      flushList();
      elements.push(
        <p key={i} className="font-semibold text-[14px] mt-2 mb-0.5">
          {line.replace(/\*\*/g, "")}
        </p>
      );
      continue;
    }

    // List items
    const ulMatch = line.match(/^[-*]\s+(.+)/);
    const olMatch = line.match(/^\d+\.\s+(.+)/);
    if (ulMatch) {
      listItems.push({ ordered: false, content: ulMatch[1] });
      continue;
    }
    if (olMatch) {
      listItems.push({ ordered: true, content: olMatch[1] });
      continue;
    }

    flushList();

    // Empty line
    if (line.trim() === "") {
      elements.push(<div key={i} className="h-2" />);
      continue;
    }

    // Inline bold
    if (line.includes("**")) {
      const parts = line.split(/(\*\*[^*]+\*\*)/g);
      elements.push(
        <p key={i} className="text-[14px] leading-relaxed">
          {parts.map((part, j) =>
            part.startsWith("**") && part.endsWith("**") ? (
              <strong key={j} className="font-semibold">
                {part.replace(/\*\*/g, "")}
              </strong>
            ) : (
              <span key={j}>{part}</span>
            )
          )}
        </p>
      );
      continue;
    }

    // Regular paragraph
    elements.push(
      <p key={i} className="text-[14px] leading-relaxed">
        {line}
      </p>
    );
  }
  flushList();
  return elements;
}

/* ─── Send Icon ──────────────────────────────────────────────────────────── */

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

/* ─── Logo ────────────────────────────────────────────────────────────────── */

function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-sm">
        <span className="text-white text-sm font-bold">O</span>
      </div>
      <div>
        <h1 className="text-[15px] font-semibold leading-tight">OCE</h1>
        <p className="text-[10px] text-text-muted leading-tight">AI Agent Platform</p>
      </div>
    </div>
  );
}

/* ─── Welcome Screen ─────────────────────────────────────────────────────── */

function WelcomeScreen({ onPrompt }: { onPrompt: (text: string) => void }) {
  const prompts = [
    { label: "What can you do?", text: "What can you do?" },
    { label: "Check system status", text: "Check the system status and health" },
    { label: "Run diagnostics", text: "Run a full diagnostics check" },
    { label: "Help me build something", text: "I want to build something new" },
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 animate-fade-in">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mb-6 shadow-lg shadow-indigo-500/20">
        <span className="text-white text-2xl font-bold">O</span>
      </div>
      <h2 className="text-xl font-semibold mb-2 text-text-primary">How can I help?</h2>
      <p className="text-sm text-text-muted mb-8 max-w-md text-center">
        I'm your AI operator. Ask me anything, delegate tasks, or explore what the system can do.
      </p>

      <div className="grid grid-cols-2 gap-3 max-w-lg w-full">
        {prompts.map((p) => (
          <button
            key={p.label}
            onClick={() => onPrompt(p.text)}
            className="text-left px-4 py-3 rounded-xl border border-border-light bg-white hover:bg-gray-50 hover:border-gray-300 transition-all duration-150 shadow-sm group"
          >
            <span className="text-xs font-medium text-text-primary group-hover:text-indigo-600 transition-colors">
              {p.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ─── Message Bubble ──────────────────────────────────────────────────────── */

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4 animate-fade-in`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mr-2.5 shrink-0 mt-0.5 shadow-sm">
          <span className="text-white text-[10px] font-bold">O</span>
        </div>
      )}

      <div className={`max-w-[75%] ${isUser ? "" : ""}`}>
        <div
          className={`px-4 py-3 ${
            isUser
              ? "bg-indigo-600 text-white rounded-2xl rounded-br-md shadow-sm"
              : "bg-white text-text-primary rounded-2xl rounded-tl-md border border-border-light shadow-sm"
          }`}
        >
          {isUser ? (
            <p className="text-[14px] leading-relaxed">{message.content}</p>
          ) : message.status === "sending" ? (
            <div className="flex items-center gap-1.5 py-1 px-1">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 dot-1" />
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 dot-2" />
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 dot-3" />
            </div>
          ) : (
            <div className="msg-content">{renderContent(message.content)}</div>
          )}
        </div>
        <p className={`text-[10px] text-text-muted mt-1 ${isUser ? "text-right" : "text-left"} px-1`}>
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>

      {isUser && (
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-gray-600 to-gray-800 flex items-center justify-center ml-2.5 shrink-0 mt-0.5 shadow-sm">
          <span className="text-white text-[10px] font-bold">M</span>
        </div>
      )}
    </div>
  );
}

/* ─── Main App ────────────────────────────────────────────────────────────── */

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + "px";
    }
  }, [input]);

  const handleSend = async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || isTyping) return;

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: "user",
      content: msg,
      timestamp: new Date(),
      status: "done",
    };

    const thinkingMsg: Message = {
      id: `t-${Date.now()}`,
      role: "assistant",
      content: "",
      timestamp: new Date(),
      status: "sending",
    };

    setMessages((prev) => [...prev, userMsg, thinkingMsg]);
    setInput("");
    setIsTyping(true);

    const response = await sendMessage(msg);

    setMessages((prev) =>
      prev.map((m) =>
        m.id === thinkingMsg.id
          ? { ...m, content: response, status: "done" as const }
          : m
      )
    );
    setIsTyping(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handlePrompt = (text: string) => {
    handleSend(text);
  };

  return (
    <div className="h-screen flex flex-col bg-bg-secondary">
      {/* Header */}
      <header className="shrink-0 px-5 py-3 flex items-center justify-between border-b border-border-light bg-white/80 backdrop-blur-sm">
        <Logo />
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse-slow" />
            <span className="text-[10px] font-medium text-emerald-700">Online</span>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <WelcomeScreen onPrompt={handlePrompt} />
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="shrink-0 border-t border-border-light bg-white/80 backdrop-blur-sm px-4 py-3">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-2 bg-white rounded-2xl border border-border-light shadow-sm px-3 py-2 focus-within:border-indigo-300 focus-within:shadow-md focus-within:shadow-indigo-500/5 transition-all">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Send a message..."
              rows={1}
              className="flex-1 bg-transparent text-[14px] text-text-primary placeholder:text-text-muted resize-none outline-none leading-relaxed py-1"
              style={{ maxHeight: "160px" }}
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || isTyping}
              className="w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-150 shrink-0 mb-0.5
                bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed"
            >
              <SendIcon />
            </button>
          </div>
          <p className="text-[10px] text-text-muted text-center mt-2">
            OCE v2.0 — AI Agent Platform
          </p>
        </div>
      </div>
    </div>
  );
}
