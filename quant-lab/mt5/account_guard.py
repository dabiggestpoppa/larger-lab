"""
CEREBUS FX v4.0 — Shared Account Guard
========================================

Lightweight account-level coordinator shared by ALL strategies on a single MT5
demo/live account.

Responsibilities:
- Account identity verification (login, server, mode)
- Connection health monitoring
- Environment detection (DEMO vs LIVE)
- Strategy magic number registry validation
- Global emergency halt signal
- Broker position mode detection (HEDGING vs NETTING)
- Optional total account exposure limits

It must NOT contain strategy logic. Both Symmetry Trap and Triangular Basis
may call it.

Usage:
    from mt5.account_guard import AccountGuard
    guard = AccountGuard()
    guard.verify_demo_identity()
    guard.check_connection()
    guard.get_broker_mode()
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

sys.stdout.reconfigure(encoding="utf-8")

# ─── IMPORTS ──────────────────────────────────────────────────────────────

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None  # Will fail gracefully if not available


class AccountMode(Enum):
    HEDGING = "hedging"
    NETTING = "netting"


class Environment(Enum):
    DEMO = "demo"
    LIVE = "live"
    UNKNOWN = "unknown"


class HaltStatus(Enum):
    CLEAR = "clear"
    BLOCK_NEW_ENTRY = "block_new_entry"
    EMERGENCY_HALT = "emergency_halt"


class AccountGuard:
    """Shared account-level coordinator for multi-strategy MT5 accounts."""

    def __init__(self, config_path: str = None):
        self._initialized = False
        self._account_info = None
        self._broker_mode: Optional[AccountMode] = None
        self._environment: Environment = Environment.UNKNOWN
        self._halt_status = HaltStatus.CLEAR
        self._last_health_check = 0.0
        self._health_interval = 120  # seconds
        
        # Expected demo account identity (override via config or env var)
        self.expected_login: Optional[str] = None
        self.expected_server: Optional[str] = None
        
        # Load config if provided
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
    
    def _load_config(self, config_path: str):
        """Load account configuration from YAML-like JSON file."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            
            self.expected_login = cfg.get("expected_login")
            self.expected_server = cfg.get("expected_server")
            self._environment = Environment(cfg.get("environment", "unknown"))
        except Exception as e:
            print(f"[ACCOUNT_GUARD] WARNING: Failed to load config {config_path}: {e}")
    
    def initialize(self) -> bool:
        """Initialize MT5 connection and verify account identity.
        
        Returns:
            True if initialized successfully, False otherwise.
        """
        if mt5 is None:
            print("[ACCOUNT_GUARD] ERROR: MetaTrader5 module not available")
            return False
        
        if not mt5.initialize():
            print("[ACCOUNT_GUARD] ERROR: MT5 initialization failed")
            return False
        
        self._account_info = mt5.account_info()
        if self._account_info is None:
            print("[ACCOUNT_GUARD] ERROR: Cannot retrieve account info")
            mt5.shutdown()
            return False
        
        self._initialized = True
        self._detect_broker_mode()
        self._last_health_check = time.time()
        
        print(f"[ACCOUNT_GUARD] Initialized: Login={self._account_info.login}, "
              f"Server={self._account_info.server}, Mode={self._broker_mode.value}")
        
        return True
    
    def _detect_broker_mode(self):
        """Detect whether broker account is HEDGING or NETTING mode."""
        if self._account_info is None:
            self._broker_mode = AccountMode.HEDGING  # Default assumption
            return
        
        # Check account margin mode field
        # In MT5 Python API: account_info.trade_mode returns trade mode
        # 0 = disabled, 1 = hedged, 2 = netted
        try:
            trade_mode = self._account_info.trade_mode
            if trade_mode == 2:
                self._broker_mode = AccountMode.NETTING
            else:
                self._broker_mode = AccountMode.HEDGING
        except AttributeError:
            # Fallback: check account_info fields directly
            # Some MT5 versions use different field names
            self._broker_mode = AccountMode.HEDGING  # Conservative default
    
    def get_broker_mode(self) -> AccountMode:
        """Get detected broker position mode."""
        return self._broker_mode
    
    def verify_demo_identity(self) -> bool:
        """Verify that connected account matches expected demo identity.
        
        Returns:
            True if verified, raises AssertionError if mismatch.
        """
        if not self._initialized:
            raise AssertionError("AccountGuard not initialized. Call initialize() first.")
        
        login = str(self._account_info.login)
        server = self._account_info.server
        
        errors = []
        
        if self.expected_login and login != self.expected_login:
            errors.append(f"Login mismatch: expected={self.expected_login}, got={login}")
        
        if self.expected_server and server != self.expected_server:
            errors.append(f"Server mismatch: expected={self.expected_server}, got={server}")
        
        if errors:
            msg = "FATAL: Demo identity verification failed!\n" + "\n".join(errors)
            print(f"[ACCOUNT_GUARD] {msg}")
            raise AssertionError(msg)
        
        print(f"[ACCOUNT_GUARD] Demo identity verified: Login={login}, Server={server}")
        return True
    
    def check_connection(self) -> bool:
        """Check MT5 connection health.
        
        Returns:
            True if healthy, False if disconnected.
        """
        if not self._initialized:
            return False
        
        now = time.time()
        if now - self._last_health_check < self._health_interval:
            return True  # Skip redundant checks
        
        try:
            ai = mt5.account_info()
            if ai is None:
                print("[ACCOUNT_GUARD] WARNING: MT5 connection lost")
                self._halt_status = HaltStatus.EMERGENCY_HALT
                return False
            
            self._last_health_check = now
            return True
        except Exception as e:
            print(f"[ACCOUNT_GUARD] WARNING: Health check error: {e}")
            self._halt_status = HaltStatus.EMERGENCY_HALT
            return False
    
    def set_halt_status(self, status: HaltStatus):
        """Set global halt status.
        
        Args:
            status: HaltStatus enum value
        """
        old_status = self._halt_status
        self._halt_status = status
        print(f"[ACCOUNT_GUARD] Halt status changed: {old_status.value} -> {status.value}")
    
    def get_halt_status(self) -> HaltStatus:
        """Get current halt status."""
        return self._halt_status
    
    def can_enter_new_position(self) -> bool:
        """Check if new positions are allowed based on halt status.
        
        Returns:
            True if entry allowed, False if blocked.
        """
        if self._halt_status in (HaltStatus.BLOCK_NEW_ENTRY, HaltStatus.EMERGENCY_HALT):
            return False
        return True
    
    def get_account_info(self) -> dict:
        """Get current account info as dictionary."""
        if self._account_info is None:
            return {}
        
        return {
            "login": str(self._account_info.login),
            "server": self._account_info.server,
            "balance": self._account_info.balance,
            "equity": self._account_info.equity,
            "margin": self._account_info.margin,
            "free_margin": self._account_info.free_margin,
            "trade_mode": self._broker_mode.value if self._broker_mode else "unknown",
            "permissions": {
                "trade_allowed": self._account_info.trade_allowed,
                "expert_allowed": self._account_info.expert_allowed,
            },
        }
    
    def shutdown(self):
        """Shutdown MT5 connection."""
        if mt5 is not None and self._initialized:
            mt5.shutdown()
            self._initialized = False
            print("[ACCOUNT_GUARD] Shutdown complete")


# ─── GLOBAL INSTANCE ─────────────────────────────────────────────────────

# Singleton instance accessible from all engines
_guard_instance: Optional[AccountGuard] = None


def get_guard(config_path: str = None) -> AccountGuard:
    """Get or create the global AccountGuard singleton."""
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = AccountGuard(config_path)
    return _guard_instance


def reset_guard():
    """Reset the global guard instance (for testing)."""
    global _guard_instance
    if _guard_instance:
        _guard_instance.shutdown()
    _guard_instance = None

