"""
Collar Layer
============
Coordinates bounded overlap between observer patches.
"""

from .base_patch import BasePatch, CollarState
from typing import Dict, List, Optional
from datetime import datetime


class CollarLayer:
    """Manages structured overlap between patches."""
    
    def __init__(self):
        self.patches: Dict[str, BasePatch] = {}
        self.sync_log: List[Dict] = []
    
    def register_patch(self, patch: BasePatch):
        """Register a patch with the collar layer."""
        self.patches[patch.patch_id] = patch
    
    def run_cycle(self) -> Dict[str, CollarState]:
        """Run one synchronization cycle."""
        results = {}
        
        # Get initial collar state
        collar = CollarState(
            patch_id="collar_layer",
            timestamp=datetime.now().isoformat(),
            objective="initialize",
            constraints=[],
            confidence=1.0
        )
        
        # Process through each patch
        for patch_id, patch in self.patches.items():
            # Run repair loop first
            patch.run_repair_loop()
            
            # Process collar
            collar = patch.process(collar)
            results[patch_id] = collar
            
            # Log sync
            self.sync_log.append({
                "timestamp": collar.timestamp,
                "patch_id": patch_id,
                "objective": collar.objective
            })
        
        return results
    
    def get_status(self) -> Dict:
        """Get status of all patches."""
        return {
            "patches": {pid: p.get_status() for pid, p in self.patches.items()},
            "sync_count": len(self.sync_log)
        }