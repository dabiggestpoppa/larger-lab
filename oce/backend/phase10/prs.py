"""
Positional Reference System (PRS)

State transitions via relative relationships.
Positions are defined by relationships to other positions, not absolute coordinates.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import hashlib


@dataclass
class Position:
    """A position defined by relative relationships."""
    position_id: str
    coordinates: Dict[str, float] = field(default_factory=dict)
    relationships: Dict[str, float] = field(default_factory=dict)  # position_id -> distance
    
    def distance_to(self, other: 'Position') -> float:
        """Compute distance to another position."""
        if self.position_id in other.relationships:
            return other.relationships[self.position_id]
        if other.position_id in self.relationships:
            return self.relationships[other.position_id]
        return self._compute_coordinate_distance(other)
    
    def _compute_coordinate_distance(self, other: 'Position') -> float:
        """Compute Euclidean distance from coordinates."""
        common_dims = set(self.coordinates.keys()) & set(other.coordinates.keys())
        if not common_dims:
            return float('inf')
        
        squared_dist = sum(
            (self.coordinates[d] - other.coordinates[d]) ** 2
            for d in common_dims
        )
        return squared_dist ** 0.5
    
    def to_hash(self) -> str:
        """Generate hash for this position."""
        data = f"{self.position_id}:{sorted(self.coordinates.items())}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class ReferenceFrame:
    """
    A reference frame defines how positions relate to each other.
    State transitions are movements within this frame.
    """
    
    def __init__(self, frame_id: str):
        self.frame_id = frame_id
        self.positions: Dict[str, Position] = {}
        self.origin: Optional[str] = None
    
    def add_position(self, position: Position) -> None:
        """Add a position to the frame."""
        self.positions[position.position_id] = position
    
    def set_origin(self, position_id: str) -> None:
        """Set the origin position for this frame."""
        if position_id in self.positions:
            self.origin = position_id
    
    def get_relative_position(self, position_id: str) -> Dict[str, float]:
        """Get position relative to origin."""
        if not self.origin or position_id not in self.positions:
            return {}
        
        pos = self.positions[position_id]
        origin = self.positions[self.origin]
        
        return {
            dim: pos.coordinates.get(dim, 0) - origin.coordinates.get(dim, 0)
            for dim in set(pos.coordinates.keys()) | set(origin.coordinates.keys())
        }
    
    def transition(self, from_id: str, to_id: str) -> Dict[str, Any]:
        """
        Compute state transition from one position to another.
        Returns the transformation needed.
        """
        if from_id not in self.positions or to_id not in self.positions:
            return {"valid": False, "error": "Position not found"}
        
        from_pos = self.positions[from_id]
        to_pos = self.positions[to_id]
        
        # Compute delta
        delta = {}
        all_dims = set(from_pos.coordinates.keys()) | set(to_pos.coordinates.keys())
        for dim in all_dims:
            delta[dim] = to_pos.coordinates.get(dim, 0) - from_pos.coordinates.get(dim, 0)
        
        return {
            "valid": True,
            "from": from_id,
            "to": to_id,
            "delta": delta,
            "distance": from_pos.distance_to(to_pos)
        }


class PositionalReferenceSystem:
    """
    Manages multiple reference frames and position transitions.
    
    State is represented as positions in a field, and transitions
    are movements through the field topology.
    """
    
    def __init__(self, name: str = "prs"):
        self.name = name
        self.frames: Dict[str, ReferenceFrame] = {}
        self.active_frame: Optional[str] = None
    
    def create_frame(self, frame_id: str) -> ReferenceFrame:
        """Create a new reference frame."""
        frame = ReferenceFrame(frame_id)
        self.frames[frame_id] = frame
        if not self.active_frame:
            self.active_frame = frame_id
        return frame
    
    def get_frame(self, frame_id: str) -> Optional[ReferenceFrame]:
        """Get a reference frame by ID."""
        return self.frames.get(frame_id)
    
    def set_active_frame(self, frame_id: str) -> None:
        """Set the active reference frame."""
        if frame_id in self.frames:
            self.active_frame = frame_id
    
    def compute_transition_path(
        self, 
        start_id: str, 
        end_id: str,
        frame_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Compute a path of transitions from start to end position.
        Uses intermediate positions if direct transition is not possible.
        """
        frame = self.frames.get(frame_id or self.active_frame)
        if not frame:
            return []
        
        if start_id not in frame.positions or end_id not in frame.positions:
            return []
        
        # Direct transition
        transition = frame.transition(start_id, end_id)
        if transition["valid"]:
            return [transition]
        
        # Find intermediate positions
        path = []
        current = start_id
        
        # Simple greedy approach: move toward target
        while current != end_id:
            # Find closest position to target
            current_pos = frame.positions[current]
            target_pos = frame.positions[end_id]
            
            # Find neighbor closest to target
            neighbors = [
                (pid, frame.positions[pid].distance_to(target_pos))
                for pid in frame.positions
                if pid != current
            ]
            
            if not neighbors:
                break
            
            next_id = min(neighbors, key=lambda x: x[1])[0]
            transition = frame.transition(current, next_id)
            if transition["valid"]:
                path.append(transition)
            current = next_id
        
        return path
    
    def get_position_hash(self, position_id: str, frame_id: Optional[str] = None) -> str:
        """Get hash of a position for identity tracking."""
        frame = self.frames.get(frame_id or self.active_frame)
        if not frame or position_id not in frame.positions:
            return ""
        return frame.positions[position_id].to_hash()