"""
Triangular Basis Shadow Guard
=============================

Non-bypassable shadow flag for Triangular Basis strategy.

When --mode shadow is enabled, ALL paths to mt5.order_send() must be disabled.
This is a HARD guard - no exceptions.

Required artifact: shadow_order_guard.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class ShadowOrderGuard:
    """
    Non-bypassable shadow guard for Triangular Basis strategy.
    
    When shadow mode is active:
    - All mt5.order_send() calls are blocked
    - Shadow mode status is logged
    - Guard status can be checked
    """
    
    def __init__(self, shadow_mode: bool = False):
        self.shadow_mode = shadow_mode
        self.shadow_start_time = datetime.utcnow() if shadow_mode else None
        self.blocked_calls = []
        self.original_order_send = None
        self.shadow_guard_active = False
        
    def enable_shadow_mode(self):
        """Enable shadow mode - blocks all order sends."""
        self.shadow_mode = True
        self.shadow_start_time = datetime.utcnow()
        self.shadow_guard_active = True
        logger.info(f"[SHADOW_GUARD] Shadow mode ENABLED at {self.shadow_start_time}")
        
    def disable_shadow_mode(self):
        """Disable shadow mode."""
        self.shadow_mode = False
        self.shadow_guard_active = False
        logger.info(f"[SHADOW_GUARD] Shadow mode DISABLED")
        
    def is_shadow_mode(self) -> bool:
        """Check if shadow mode is active."""
        return self.shadow_mode
        
    def block_order_send(self, *args, **kwargs) -> None:
        """
        BLOCKS all order_send calls when in shadow mode.
        
        This is the HARD guard - no exceptions.
        """
        if self.shadow_mode:
            # Log the blocked call
            call_info = {
                "timestamp": datetime.utcnow().isoformat(),
                "args": str(args),
                "kwargs": str(kwargs),
                "blocked": True
            }
            self.blocked_calls.append(call_info)
            
            logger.warning(
                f"[SHADOW_GUARD] BLOCKED mt5.order_send() call at {call_info['timestamp']}"
            )
            
            # Return a mock result to prevent crashes
            # This simulates a successful but non-executing call
            class MockResult:
                ticket = 0
                order = 0
                deal = 0
                position = 0
                
            return MockResult()
            
    def get_shadow_stats(self) -> Dict[str, Any]:
        """Get shadow mode statistics."""
        return {
            "shadow_mode": self.shadow_mode,
            "shadow_guard_active": self.shadow_guard_active,
            "shadow_start_time": self.shadow_start_time.isoformat() if self.shadow_start_time else None,
            "blocked_calls_count": len(self.blocked_calls),
            "blocked_calls": self.blocked_calls[-10:] if self.blocked_calls else [],  # Last 10
        }
        
    def save_shadow_guard_state(self, path: str | Path):
        """Save shadow guard state to JSON file."""
        path = Path(path)
        state = {
            "timestamp": datetime.utcnow().isoformat(),
            "shadow_mode": self.shadow_mode,
            "shadow_guard_active": self.shadow_guard_active,
            "shadow_start_time": self.shadow_start_time.isoformat() if self.shadow_start_time else None,
            "blocked_calls_count": len(self.blocked_calls),
            "blocked_calls": self.blocked_calls,
        }
        
        with open(path, "w") as f:
            json.dump(state, f, indent=2)
            
        logger.info(f"[SHADOW_GUARD] Shadow guard state saved to {path}")
        
    def load_shadow_guard_state(self, path: str | Path):
        """Load shadow guard state from JSON file."""
        path = Path(path)
        if not path.exists():
            logger.warning(f"[SHADOW_GUARD] Shadow guard state file not found: {path}")
            return
            
        with open(path, "r") as f:
            state = json.load(f)
            
        self.shadow_mode = state.get("shadow_mode", False)
        self.shadow_guard_active = state.get("shadow_guard_active", False)
        self.shadow_start_time = datetime.fromisoformat(state.get("shadow_start_time", "")) \
            if state.get("shadow_start_time") else None
        self.blocked_calls = state.get("blocked_calls", [])
        
        logger.info(f"[SHADOW_GUARD] Shadow guard state loaded from {path}")
        
    def monkeypatch_mt5_order_send(self):
        """
        Monkeypatch mt5.order_send to use our shadow guard.
        
        This ensures ALL order_send calls go through our guard.
        """
        try:
            import MetaTrader5 as mt5
            
            # Save original
            self.original_order_send = mt5.order_send
            
            # Replace with guarded version
            def guarded_order_send(*args, **kwargs):
                return self.block_order_send(*args, **kwargs)
                
            mt5.order_send = guarded_order_send
            logger.info("[SHADOW_GUARD] Monkeypatched mt5.order_send with shadow guard")
            
        except ImportError:
            logger.warning("[SHADOW_GUARD] MetaTrader5 not available - cannot monkeypatch")
            
    def restore_original_order_send(self):
        """Restore original mt5.order_send."""
        if self.original_order_send and hasattr(sys.modules.get('MetaTrader5'), 'order_send'):
            import MetaTrader5 as mt5
            mt5.order_send = self.original_order_send
            logger.info("[SHADOW_GUARD] Restored original mt5.order_send")


# Global shadow guard instance
_shadow_guard = ShadowOrderGuard()


def get_shadow_guard() -> ShadowOrderGuard:
    """Get the global shadow guard instance."""
    return _shadow_guard


def enable_shadow_mode():
    """Enable shadow mode globally."""
    _shadow_guard.enable_shadow_mode()
    _shadow_guard.monkeypatch_mt5_order_send()


def disable_shadow_mode():
    """Disable shadow mode globally."""
    _shadow_guard.disable_shadow_mode()
    _shadow_guard.restore_original_order_send()


def is_shadow_mode() -> bool:
    """Check if shadow mode is active globally."""
    return _shadow_guard.is_shadow_mode()


def save_shadow_guard_state(path: str | Path):
    """Save shadow guard state globally."""
    _shadow_guard.save_shadow_guard_state(path)


def load_shadow_guard_state(path: str | Path):
    """Load shadow guard state globally."""
    _shadow_guard.load_shadow_guard_state(path)


def test_shadow_guard():
    """
    Test that shadow guard is working.
    
    This function monkeypatches mt5.order_send and asserts that
    call count = 0 when in shadow mode.
    """
    import MetaTrader5 as mt5
    
    # Enable shadow mode
    enable_shadow_mode()
    
    # Mock mt5.order_send to track calls
    call_count = 0
    original_order_send = mt5.order_send
    
    def mock_order_send(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return original_order_send(*args, **kwargs)
        
    mt5.order_send = mock_order_send
    
    # Try to send an order (should be blocked)
    try:
        # This should be blocked by shadow guard
        result = mt5.order_send(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    except:
        pass
        
    # Restore original
    mt5.order_send = original_order_send
    disable_shadow_mode()
    
    # Assert call count = 0
    assert call_count == 0, f"Shadow guard failed - order_send was called {call_count} times"
    
    logger.info("[SHADOW_GUARD] Shadow guard test PASSED - order_send calls = 0")
    
    return True