"""
O-1-F1: ChatPanel
==================
Enhanced Primary Observer chat interface.

Replaces basic chat with observer-aware chat that shows
task analysis, routing, and execution context.
*/

"use client";

import { useState, useRef, useEffect } from "react";
import { useObserverStore } from "@/stores/observerStore";

interface ChatMessage {
  id: string;
  role: "user" | "observer" | "system";
  content: string;
  timestamp: string;
  metadata?: {
    domain?: string;
    complexity?: string;
    nextAction?: string;
  };
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const observer = useObserverStore((s) => s.observer);
  const setObserverState = useObserverStore((s) => s.setObserverState);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userMsg: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsProcessing(true);

    // Simulate observer processing (will be replaced with real API call)
    try {
      const response = await fetch("/api/observer/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      if (response.ok) {
        const data = await response.json();
        const observerMsg: ChatMessage = {
          id: `msg_${Date.now()}_resp`,
          role: "observer",
          content: data.message || "Task received and analyzed.",
          timestamp: new Date().toISOString(),
          metadata: {
            domain: data.task_domain,
            complexity: data.complexity,
            nextAction: data.next_action,
          },
        };
        setMessages((prev) => [...prev, observerMsg]);
        setObserverState({ requestCount: observer.requestCount + 1 });
      } else {
        // Fallback: show that observer received the message
        const observerMsg: ChatMessage = {
          id: `msg_${Date.now()}_resp`,
          role: "observer",
          content: `Received: "${input}" — Observer API not yet connected.`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, observerMsg]);
      }
    } catch {
      const observerMsg: ChatMessage = {
        id: `msg_${Date.now()}_resp`,
        role: "observer",
        content: `Received: "${input}" — Observer API not yet connected.`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, observerMsg]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-950 border border-gray-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-800 bg-gray-900/50">
        <h2 className="text-sm font-semibold text-gray-200">
          Primary Observer Chat
        </h2>
        <p className="text-xs text-gray-500">
          Continuity-aware orchestration interface
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-gray-600 text-sm py-8">
            <p>Start a conversation with the Primary Observer.</p>
            <p className="text-xs mt-1">
              Try: &quot;Build a REST API&quot;, &quot;Analyze the topology&quot;,
              &quot;Debug the spawn engine&quot;
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-3 py-2 ${
                msg.role === "user"
                  ? "bg-blue-900/50 text-blue-100"
                  : msg.role === "system"
                  ? "bg-gray-800 text-gray-400 text-xs"
                  : "bg-gray-800 text-gray-200"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              {msg.metadata && (
                <div className="flex gap-2 mt-2 text-xs">
                  {msg.metadata.domain && (
                    <span className="bg-purple-900/50 text-purple-300 px-1.5 py-0.5 rounded">
                      {msg.metadata.domain}
                    </span>
                  )}
                  {msg.metadata.complexity && (
                    <span className="bg-gray-700 text-gray-300 px-1.5 py-0.5 rounded">
                      {msg.metadata.complexity}
                    </span>
                  )}
                  {msg.metadata.nextAction && (
                    <span className="bg-green-900/50 text-green-300 px-1.5 py-0.5 rounded">
                      → {msg.metadata.nextAction}
                    </span>
                  )}
                </div>
              )}
              <div className="text-xs text-gray-600 mt-1">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-lg px-3 py-2">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-gray-800">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a task or question..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-600"
            disabled={isProcessing}
          />
          <button
            type="submit"
            disabled={isProcessing || !input.trim()}
            className="px-4 py-2 bg-blue-700 hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm font-medium rounded-lg transition-colors"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
