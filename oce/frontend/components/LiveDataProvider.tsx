"use client";

import { useEffect, useRef, useCallback } from "react";
import { useTopologyStore } from "@/stores/topologyStore";
import { useEntropyStore } from "@/stores/entropyStore";
import { useRepairStore } from "@/stores/repairStore";
import { useContinuityStore } from "@/stores/continuityStore";
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
  const isMounted = useRef(true);
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const setNodes = useTopologyStore((s) => s.setNodes);
  const setEdges = useTopologyStore((s) => s.setEdges);
  const updateEntropy = useEntropyStore((s) => s.updateFromFrame);
  const addRepair = useRepairStore((s) => s.addRepair);
  const addCheckpoint = useContinuityStore((s) => s.addCheckpoint);
  const setConnectionStatus = useUIStore((s) => s.setConnectionStatus);

  const fetchTopology = useCallback(async () => {
    if (!isMounted.current) return;
    try {
      const res = await fetch("/api/topology");
      const data = await res.json();
      if (data.nodes && data.edges) {
        setNodes(data.nodes);
        setEdges(data.edges);
      }
    } catch (err) {
      // API not available, will retry
    }
  }, [setNodes, setEdges]);

  const handleMessage = useCallback(
    (msg: WSMessage) => {
      if (!isMounted.current) return;
      switch (msg.type) {
        case "topology_update":
          setNodes((msg.data as any).nodes);
          setEdges((msg.data as any).edges);
          break;
        case "entropy_update":
          updateEntropy((msg.data as any).observerStates);
          break;
        case "repair_event":
          addRepair({
            id: (msg.data as any).id || `repair-${Date.now()}`,
            source: (msg.data as any).source,
            target: (msg.data as any).target,
            type: "trigger",
            timestamp: Date.now(),
            strength: (msg.data as any).strength || 0.5,
          });
          break;
        case "checkpoint":
          addCheckpoint({
            id: (msg.data as any).id || `cp-${Date.now()}`,
            timestamp: (msg.data as any).timestamp || new Date().toISOString(),
            status: (msg.data as any).status || "PASS",
            drift_score: (msg.data as any).drift_score || 0,
            observer_health: (msg.data as any).observer_health || { alive: 0, degraded: 0, dead: 0 },
            elapsed_hours: (msg.data as any).elapsed_hours || 0,
          });
          break;
      }
    },
    [setNodes, setEdges, updateEntropy, addRepair, addCheckpoint]
  );

  useEffect(() => {
    isMounted.current = true;
    setConnectionStatus("connecting");

    // Initial fetch
    fetchTopology();

    // Try WebSocket first
    const connect = () => {
      if (!isMounted.current) return;
      try {
        const ws = new WebSocket("ws://localhost:8001/ws");

        ws.onopen = () => {
          reconnectCount.current = 0;
          setConnectionStatus("connected");
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
          if (isMounted.current && reconnectCount.current < 10) {
            reconnectTimer.current = setTimeout(() => {
              reconnectCount.current++;
              connect();
            }, 3000 * Math.min(reconnectCount.current + 1, 5));
          }
        };

        ws.onerror = () => {
          setConnectionStatus("error");
          if (pollTimer.current === null) {
            pollTimer.current = setInterval(fetchTopology, 5000);
          }
        };

        wsRef.current = ws;
      } catch {
        setConnectionStatus("error");
        if (pollTimer.current === null) {
          pollTimer.current = setInterval(fetchTopology, 5000);
        }
      }
    };

    connect();

    return () => {
      isMounted.current = false;
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (pollTimer.current) clearInterval(pollTimer.current);
    };
  }, [fetchTopology, handleMessage, setConnectionStatus]);

  return null;
}