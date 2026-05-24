"use client";

import { useEffect, useRef } from "react";
import { useTaskStore } from "@/stores/taskStore";
import { useAgentStore } from "@/stores/agentStore";
import { useSessionStore } from "@/stores/sessionStore";
import { useUIStore } from "@/stores/uiStore";

type WSMessage = {
  type: string;
  data: unknown;
  timestamp?: string;
};

export default function LiveDataProvider() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const setAgents = useAgentStore((s) => s.setAgents);
  const setTasks = useTaskStore((s) => s.setTasks);
  const setSessions = useSessionStore((s) => s.setSessions);
  const setConnectionStatus = useUIStore((s) => s.setConnectionStatus);
  const addNotification = useUIStore((s) => s.addNotification);

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket("ws://localhost:8000/ws");

      ws.onopen = () => {
        reconnectCount.current = 0;
        setConnectionStatus("connected");
        addNotification({ type: "success", message: "Connected to OCE backend" });
      };

      ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data);
          handleMessage(msg);
        } catch {
          // ignore non-JSON
        }
      };

      ws.onclose = () => {
        setConnectionStatus("disconnected");
        if (reconnectCount.current < 10) {
          reconnectTimer.current = setTimeout(() => {
            reconnectCount.current++;
            connect();
          }, 3000 * Math.min(reconnectCount.current + 1, 5));
        }
      };

      ws.onerror = () => {
        setConnectionStatus("error");
      };

      wsRef.current = ws;
    };

    const handleMessage = (msg: WSMessage) => {
      switch (msg.type) {
        case "agents":
          setAgents(msg.data as ReturnType<typeof useAgentStore.getState>["agents"]);
          break;
        case "tasks":
          setTasks(msg.data as ReturnType<typeof useTaskStore.getState>["tasks"]);
          break;
        case "sessions":
          setSessions(msg.data as ReturnType<typeof useSessionStore.getState>["sessions"]);
          break;
        case "chaos_update":
          // Handle chaos test live updates
          break;
        case "notification":
          addNotification(msg.data as { type: string; message: string });
          break;
      }
    };

    connect();

    // Poll for data every 10s as fallback
    const pollInterval = setInterval(async () => {
      if (wsRef.current?.readyState !== WebSocket.OPEN) {
        try {
          const [agentsRes, tasksRes] = await Promise.all([
            fetch("http://localhost:8000/api/agents"),
            fetch("http://localhost:8000/api/tasks"),
          ]);
          if (agentsRes.ok) setAgents(await agentsRes.json());
          if (tasksRes.ok) setTasks(await tasksRes.json());
        } catch {
          // backend not available
        }
      }
    }, 10000);

    return () => {
      clearInterval(pollInterval);
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [setAgents, setTasks, setSessions, setConnectionStatus, addNotification]);

  return null;
}
