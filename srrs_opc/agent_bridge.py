"""
Agent Bridge
============
Connects SRRA-OPH patches to OpenClaw and Hermes agents.
"""

import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime


class AgentBridge:
    """Bridge between observer patches and external agents."""
    
    def __init__(self, openclaw_url: str = "ws://127.0.0.1:18789",
                 hermes_url: Optional[str] = None):
        self.openclaw_url = openclaw_url
        self.hermes_url = hermes_url
        self.last_sync: Dict[str, Any] = {}
    
    def send_to_openclaw(self, message: Dict[str, Any]) -> bool:
        """Send message to OpenClaw via CLI gateway."""
        try:
            # In production, this would use the actual OpenClaw protocol
            # For now, we log the message
            self.last_sync["openclaw"] = {
                "timestamp": datetime.now().isoformat(),
                "message": message
            }
            return True
        except Exception as e:
            print(f"OpenClaw send error: {e}")
            return False
    
    def send_to_hermes(self, message: Dict[str, Any]) -> bool:
        """Send message to Hermes via Telegram."""
        try:
            # In production, this would use Telegram bot API
            self.last_sync["hermes"] = {
                "timestamp": datetime.now().isoformat(),
                "message": message
            }
            return True
        except Exception as e:
            print(f"Hermes send error: {e}")
            return False
    
    def sync_from_patches(self, collar_results: Dict) -> Dict[str, Any]:
        """Sync collar results to agents."""
        sync_data = {
            "timestamp": datetime.now().isoformat(),
            "patches": {}
        }
        
        for patch_id, state in collar_results.items():
            sync_data["patches"][patch_id] = {
                "objective": state.objective,
                "confidence": state.confidence,
                "repair_flags": state.repair_flags
            }
        
        # Send to both agents
        self.send_to_openclaw(sync_data)
        self.send_to_hermes(sync_data)
        
        return sync_data
    
    def get_last_sync(self) -> Dict[str, Any]:
        """Get last synchronization data."""
        return self.last_sync