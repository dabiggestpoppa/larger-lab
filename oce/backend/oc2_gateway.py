"""
OC2 Gateway — Orchestrator Process
===================================
Persistent process that:
1. Connects to OCE backend via WebSocket
2. Monitors all registered agents
3. Streams observer/event data to connected clients
4. Reports system health

Run: python -m oce.backend.oc2_gateway
"""

from __future__ import annotations

import asyncio
import json
import logging
import signal
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import websockets
import websockets.exceptions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [OC2-GW] %(levelname)s %(message)s",
)
logger = logging.getLogger("oc2_gateway")

OCE_BACKEND_WS = "ws://localhost:8000/ws/observers"
OCE_BACKEND_HTTP = "http://localhost:8000"
HEARTBEAT_INTERVAL = 30  # seconds
RECONNECT_DELAY = 5  # seconds


class OCGateway:
    """OC2 Orchestrator Gateway — monitors agents and streams updates."""

    def __init__(self):
        self.gateway_id = f"oc2-gw-{uuid.uuid4().hex[:8]}"
        self.connected = False
        self.ws: websockets.WebSocketClientProtocol | None = None
        self._running = True
        self._stats = {
            "start_time": datetime.now(timezone.utc).isoformat(),
            "messages_received": 0,
            "messages_sent": 0,
            "reconnects": 0,
            "last_heartbeat": None,
        }

    async def start(self):
        """Start the gateway main loop."""
        logger.info(f"OC2 Gateway starting (id={self.gateway_id})")
        logger.info(f"Connecting to OCE backend at {OCE_BACKEND_WS}")

        # Register self as agent
        await self._register_agent()

        # Main loop: connect, process, reconnect
        while self._running:
            try:
                async with websockets.connect(OCE_BACKEND_WS) as ws:
                    self.ws = ws
                    self.connected = True
                    logger.info("Connected to OCE backend WebSocket")

                    # Start heartbeat and message processing
                    await asyncio.gather(
                        self._heartbeat_loop(),
                        self._receive_loop(),
                    )

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
            except ConnectionRefusedError:
                logger.warning(f"OCE backend not reachable at {OCE_BACKEND_WS}")
            except Exception as e:
                logger.error(f"Gateway error: {e}")

            self.connected = False
            self._stats["reconnects"] += 1

            if self._running:
                logger.info(f"Reconnecting in {RECONNECT_DELAY}s...")
                await asyncio.sleep(RECONNECT_DELAY)

    async def _register_agent(self):
        """Register OC2 gateway as an agent in the command center."""
        try:
            import requests
            r = requests.post(
                f"{OCE_BACKEND_HTTP}/command-center/agents/register",
                json={
                    "session_key": "oc2-gateway",
                    "label": "OC2 Gateway",
                    "role": "Orchestrator. Monitors all agents, streams updates, reports health.",
                    "capabilities": [
                        "orchestration",
                        "monitoring",
                        "health_reporting",
                        "agent_management",
                    ],
                },
                timeout=5,
            )
            if r.status_code == 200:
                logger.info("OC2 Gateway registered in command center")
            else:
                logger.warning(f"Agent registration failed: {r.status_code}")
        except Exception as e:
            logger.warning(f"Could not register agent: {e}")

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to OCE backend."""
        while self._running and self.connected:
            try:
                heartbeat = {
                    "type": "gateway_heartbeat",
                    "gateway_id": self.gateway_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "stats": self._stats,
                }
                if self.ws:
                    await self.ws.send(json.dumps(heartbeat))
                    self._stats["messages_sent"] += 1
                    self._stats["last_heartbeat"] = datetime.now(timezone.utc).isoformat()

                # Also update agent heartbeat via HTTP
                try:
                    import requests
                    requests.post(
                        f"{OCE_BACKEND_HTTP}/command-center/agents/oc2-gateway/heartbeat",
                        timeout=3,
                    )
                except Exception:
                    pass

            except Exception as e:
                logger.debug(f"Heartbeat error: {e}")

            await asyncio.sleep(HEARTBEAT_INTERVAL)

    async def _receive_loop(self):
        """Receive and process messages from OCE backend."""
        while self._running and self.connected and self.ws:
            try:
                raw = await self.ws.recv()
                self._stats["messages_received"] += 1

                try:
                    msg = json.loads(raw)
                    await self._process_message(msg)
                except json.JSONDecodeError:
                    pass

            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                logger.error(f"Receive error: {e}")
                break

    async def _process_message(self, msg: dict[str, Any]):
        """Process incoming messages from OCE backend."""
        msg_type = msg.get("type", "unknown")

        if msg_type == "observer_update":
            logger.debug(f"Observer update: {msg.get('observer_id', 'unknown')}")
        elif msg_type == "event":
            event_type = msg.get("event", {}).get("event_type", "unknown")
            logger.debug(f"Event: {event_type}")
        elif msg_type == "system_status":
            logger.info(f"System status: {msg.get('status', 'unknown')}")

    def stop(self):
        """Stop the gateway."""
        self._running = False
        logger.info("OC2 Gateway stopping")


async def main():
    gateway = OCGateway()

    # Handle graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, gateway.stop)
        except NotImplementedError:
            pass  # Windows

    try:
        await gateway.start()
    except KeyboardInterrupt:
        gateway.stop()
        logger.info("OC2 Gateway stopped")


if __name__ == "__main__":
    asyncio.run(main())
