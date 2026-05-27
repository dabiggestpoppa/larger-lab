"use client";

import { useState, useRef, useEffect } from "react";
import { useUIStore } from "@/stores/uiStore";
import { useConsensusStore } from "@/stores/consensusStore";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  observer?: {
    task_type: string;
    complexity: string;
    confidence: number;
    routing_path: string[];
    agreement?: number;
    model?: string;
    spawn_required?: boolean;
  };
}

export default function ChatPanel() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const setConnectionStatus = useUIStore((s) => s.setConnectionStatus);
  const setCurrentConsensus = useConsensusStore((s) => s.setCurrentConsensus);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async () => {
    if (!input.trim() || isProcessing) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsProcessing(true);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      if (res.ok) {
        const data = await res.json();
        const assistantMsg: ChatMessage = {
          id: `msg-${Date.now()}-resp`,
          role: "assistant",
          content: data.response || data.message || "No response",
          timestamp: new Date().toISOString(),
          observer: data.observer,
        };
        setMessages((prev) => [...prev, assistantMsg]);
        if (data.observer) {
          setCurrentConsensus({
            task_type: data.observer.task_type || "unknown",
            complexity: data.observer.complexity || "low",
            confidence: data.observer.confidence || 0,
            routing_path: data.observer.routing_path || [],
            required_capabilities: data.observer.required_capabilities || [],
            recommended_model: data.observer.model || "default",
            spawn_required: data.observer.spawn_required || false,
            timestamp: new Date().toISOString(),
            voter_count: data.observer.voter_count || 1,
            agreement_score: data.observer.agreement || 1.0,
          });
        }
        setConnectionStatus("connected");
      } else {
        setConnectionStatus("error");
      }
    } catch {
      setConnectionStatus("error");
      const errMsg: ChatMessage = {
        id: `msg-${Date.now()}-err`,
        role: "assistant",
        content: "Error: Could not connect to OCE backend.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center px-4 py-2 border-b border-border-light bg-bg-secondary">
        <h2 className="text-xs font-mono font-bold text-text-primary">PRIMARY OBSERVER CHAT</h2>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-lg p-3 ${
              msg.role === "user" ? "bg-accent-primary/10" : "bg-bg-tertiary"
            }`}>
              <p className="text-sm text-text-primary whitespace-pre-wrap">{msg.content}</p>

              {msg.observer && (
                <div className="mt-2 pt-2 border-t border-border-light space-y-1">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="px-1.5 py-0.5 rounded bg-accent-primary/10 text-accent-primary font-mono">
                      {msg.observer.task_type}
                    </span>
                    <span className="text-text-muted">{msg.observer.complexity}</span>
                    <span className="text-accent-success">{(msg.observer.confidence * 100).toFixed(0)}%</span>
                  </div>
                  {msg.observer.routing_path && msg.observer.routing_path.length > 0 && (
                    <div className="flex items-center gap-1 text-xs text-text-muted flex-wrap">
                      <span>Route:</span>
                      {msg.observer.routing_path.map((step, idx) => (
                        <span key={idx} className="flex items-center gap-1">
                          <span className="px-1.5 py-0.5 bg-white rounded border border-border-light text-text-primary font-mono text-[10px]">
                            {step}
                          </span>
                          {idx < (msg.observer?.routing_path?.length ?? 0) - 1 && (
                            <span className="text-text-muted">→</span>
                          )}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="text-[10px] text-text-muted mt-1">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-bg-tertiary rounded-lg p-3">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent-primary animate-pulse" />
                <span className="text-xs text-text-muted">Observer analyzing...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-border-light">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            placeholder="Send message to Primary Observer..."
            className="flex-1 px-3 py-2 rounded-lg bg-bg-tertiary border border-border-light text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-primary"
          />
          <button
            onClick={handleSubmit}
            disabled={isProcessing || !input.trim()}
            className="px-4 py-2 rounded-lg bg-accent-primary text-white text-sm font-medium disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
