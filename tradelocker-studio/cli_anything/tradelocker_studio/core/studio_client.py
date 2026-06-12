"""
TradeLocker Studio Engine API Client.

Wraps the Studio engine running on localhost:53163 (Python FastAPI + Uvicorn).
The engine is spawned by TradeLocker Desktop and manages:
- Bot projects (CRUD)
- File content (read/write bot code)
- Backtest processes (start/stop/monitor)
- AI chat conversations
"""

import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

STUDIO_ENGINE_HOST = os.environ.get("TRADELOCKER_STUDIO_HOST", "http://127.0.0.1:53163")
STUDIO_API_KEY = os.environ.get("TRADELOCKER_STUDIO_API_KEY", "")
REQUEST_TIMEOUT = (10, 60)  # (connect, read) seconds


def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if STUDIO_API_KEY:
        h["Authorization"] = f"Bearer {STUDIO_API_KEY}"
    return h


# ---------------------------------------------------------------------------
# Project operations
# ---------------------------------------------------------------------------

def list_projects(create_if_empty: bool = False) -> Dict[str, Any]:
    """List all Studio bot projects."""
    r = requests.get(
        urljoin(STUDIO_ENGINE_HOST, f"/all_projects?create_if_empty={str(create_if_empty).lower()}"),
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def get_project(project_id: str) -> Dict[str, Any]:
    """Get a single project by ID."""
    r = requests.get(
        urljoin(STUDIO_ENGINE_HOST, f"/project/{project_id}"),
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def create_project(name: str = "New Bot") -> Dict[str, Any]:
    """Create a new bot project."""
    r = requests.post(
        urljoin(STUDIO_ENGINE_HOST, "/project"),
        headers=_headers(),
        json={"name": name},
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def rename_project(project_id: str, name: str) -> Dict[str, Any]:
    """Rename a project."""
    r = requests.put(
        urljoin(STUDIO_ENGINE_HOST, f"/project/{project_id}/name"),
        headers=_headers(),
        json={"name": name},
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def clone_project(project_id: str) -> Dict[str, Any]:
    """Clone an existing project."""
    r = requests.post(
        urljoin(STUDIO_ENGINE_HOST, f"/project/{project_id}/clone"),
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def delete_project(project_id: str, should_stop: bool = False) -> Dict[str, Any]:
    """Delete a project."""
    r = requests.delete(
        urljoin(STUDIO_ENGINE_HOST, f"/project/{project_id}?should_stop={str(should_stop).lower()}"),
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# File operations (bot code)
# ---------------------------------------------------------------------------

def get_file_content(file_id: str) -> str:
    """Read the content of a strategy file."""
    r = requests.get(
        urljoin(STUDIO_ENGINE_HOST, f"/file/{file_id}/content"),
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("data", "")


def update_file_content(file_id: str, content: str) -> Dict[str, Any]:
    """Write content to a strategy file. This is how we inject bot code."""
    r = requests.put(
        urljoin(STUDIO_ENGINE_HOST, f"/file/{file_id}/content"),
        headers=_headers(),
        json={"data": content},
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Backtest process operations
# ---------------------------------------------------------------------------

def start_process(
    project_id: str,
    refresh_token: str,
    account_id: int,
    acc_num: int,
    strategy_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Start a backtest process.

    Args:
        project_id: The bot project ID
        refresh_token: TradeLocker JWT refresh token (from /auth/jwt/refresh)
        account_id: TradeLocker account ID
        acc_num: TradeLocker account number
        strategy_config: Optional backtest parameters:
            - symbolName: str (e.g., "AUDCAD")
            - resolution: str (e.g., "1m", "5m", "1h", "1D")
            - startDate: ISO datetime string
            - endDate: ISO datetime string
            - margin: float
            - leverage: float
            - commission: float
    """
    payload = {
        "refreshToken": refresh_token,
        "accountId": account_id,
        "accNum": acc_num,
    }
    if strategy_config:
        payload["strategyConfig"] = strategy_config

    r = requests.post(
        urljoin(STUDIO_ENGINE_HOST, f"/project/{project_id}/process"),
        headers=_headers(),
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def get_process(project_id: str, process_id: str) -> Dict[str, Any]:
    """Get process status and results."""
    r = requests.get(
        urljoin(STUDIO_ENGINE_HOST, f"/process/{process_id}"),
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def stop_process(project_id: str, process_id: str) -> Dict[str, Any]:
    """Stop a running backtest process."""
    r = requests.post(
        urljoin(STUDIO_ENGINE_HOST, f"/process/{process_id}/stop"),
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def get_process_issue(project_id: str, process_id: str) -> Dict[str, Any]:
    """Get process issue/diagnostic info."""
    r = requests.get(
        urljoin(STUDIO_ENGINE_HOST, f"/process/{process_id}/issue"),
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Strategy config
# ---------------------------------------------------------------------------

def get_strategy_config(project_id: str) -> Dict[str, Any]:
    """Get the current strategy configuration for a project."""
    r = requests.get(
        urljoin(STUDIO_ENGINE_HOST, f"/project/{project_id}/strategy-config"),
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def update_strategy_config(project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Update strategy configuration (symbol, resolution, dates, margin, etc.)."""
    r = requests.put(
        urljoin(STUDIO_ENGINE_HOST, f"/project/{project_id}/strategy-config"),
        headers=_headers(),
        json=config,
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Conversation (AI chat)
# ---------------------------------------------------------------------------

def get_conversation_messages(conversation_id: str) -> List[Dict[str, Any]]:
    """Get all messages in a conversation."""
    r = requests.get(
        urljoin(STUDIO_ENGINE_HOST, f"/conversation/{conversation_id}/message-list"),
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def send_conversation_message(conversation_id: str, message: str) -> Dict[str, Any]:
    """Send a message to the AI chatbot in Studio."""
    r = requests.post(
        urljoin(STUDIO_ENGINE_HOST, f"/conversation/{conversation_id}/message"),
        headers=_headers(),
        json={"message": message},
        timeout=(10, 120),  # LLM responses can be slow
    )
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Limits & status
# ---------------------------------------------------------------------------

def get_limits() -> Dict[str, Any]:
    """Get Studio engine rate limits."""
    r = requests.get(
        urljoin(STUDIO_ENGINE_HOST, "/limits"),
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def health_check() -> Dict[str, Any]:
    """Check if the Studio engine is alive."""
    r = requests.get(
        urljoin(STUDIO_ENGINE_HOST, "/health/liveness"),
        headers=_headers(),
        timeout=(5, 10),
    )
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Polling helper
# ---------------------------------------------------------------------------

def poll_process_until_complete(
    project_id: str,
    process_id: str,
    poll_interval: float = 2.0,
    max_wait: float = 300.0,
    callback=None,
) -> Dict[str, Any]:
    """
    Poll a process until it completes or times out.

    Args:
        project_id: The bot project ID
        process_id: The process ID
        poll_interval: Seconds between polls
        max_wait: Maximum seconds to wait
        callback: Optional callable(process_data) called on each poll
    """
    start = time.time()
    while time.time() - start < max_wait:
        process = get_process(project_id, process_id)
        status = process.get("status", "unknown")

        if callback:
            callback(process)

        if status in ("completed", "failed", "stopped"):
            return process

        time.sleep(poll_interval)

    # Timed out — return last known state
    return get_process(project_id, process_id)
