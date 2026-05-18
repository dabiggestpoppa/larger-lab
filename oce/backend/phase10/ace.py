"""
Attractor Compute Engine (ACE)

Solutions emerge through field convergence.
Computation happens through attractor dynamics in the field.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import math


class AttractorType(Enum):
    """Types of attractors in the field."""
    POINT = "point"       # Single stable state
    CYCLE = "cycle"       # Cyclical attractor
    CHAOTIC = "chaotic"   # Chaotic attractor
    TORUS = "torus"       # Toroidal attractor


@dataclass
class AttractorSolution:
    """A solution that has emerged from attractor convergence."""
    solution_id: str
    attractor_type: AttractorType
    state: Dict[str, Any]
    convergence_path: List[Dict[str, Any]]
    stability_score: float
    energy: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "solution_id": self.solution_id,
            "attractor_type": self.attractor_type.value,
            "state": self.state,
            "convergence_path": self.convergence_path,
            "stability_score": self.stability_score,
            "energy": self.energy
        }


class AttractorComputeEngine:
    """
    Computes solutions through attractor dynamics.
    
    Instead of executing instructions, the field evolves toward
    attractor states. Solutions emerge when the field converges.
    """
    
    def __init__(self, name: str = "ace"):
        self.name = name
        self.field_state: Dict[str, Any] = {}
        self.attractors: List[Dict[str, Any]] = []
        self.convergence_history: List[Dict[str, Any]] = []
        self.energy: float = 0.0
    
    def set_field_state(self, state: Dict[str, Any]) -> None:
        """Set the current field state."""
        self.field_state = state.copy()
    
    def add_attractor(self, attractor: Dict[str, Any]) -> None:
        """Add an attractor to the field."""
        self.attractors.append(attractor)
    
    def compute_energy(self, state: Optional[Dict[str, Any]] = None) -> float:
        """
        Compute the energy of a state.
        Lower energy = more stable/attractive.
        """
        state = state or self.field_state
        if not state:
            return 0.0
        
        # Energy based on variance from attractor centers
        energy = 0.0
        for attractor in self.attractors:
            center = attractor.get("center", {})
            weight = attractor.get("weight", 1.0)
            
            for key, value in state.items():
                if key in center:
                    diff = value - center[key]
                    energy += weight * diff * diff
        
        return energy
    
    def compute_gradient(self, state: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Compute the gradient toward attractors.
        Returns the direction of steepest descent.
        """
        state = state or self.field_state
        if not state:
            return {}
        
        gradient = {}
        for key in state:
            gradient[key] = 0.0
            
            for attractor in self.attractors:
                center = attractor.get("center", {})
                weight = attractor.get("weight", 1.0)
                
                if key in center:
                    gradient[key] += 2 * weight * (state[key] - center[key])
        
        return gradient
    
    def evolve(
        self,
        steps: int = 10,
        learning_rate: float = 0.1,
        momentum: float = 0.9
    ) -> List[Dict[str, Any]]:
        """
        Evolve the field state toward attractors.
        
        Uses gradient descent with momentum.
        """
        path = []
        velocity = {k: 0.0 for k in self.field_state}
        
        for step in range(steps):
            gradient = self.compute_gradient()
            
            # Update with momentum
            for key in self.field_state:
                velocity[key] = momentum * velocity[key] - learning_rate * gradient.get(key, 0)
                self.field_state[key] += velocity[key]
            
            # Record state
            path.append({
                "step": step,
                "state": self.field_state.copy(),
                "energy": self.compute_energy(),
                "gradient_norm": sum(g*g for g in gradient.values()) ** 0.5
            })
            
            self.convergence_history.append(path[-1])
        
        return path
    
    def find_attractor(self, state: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Find the nearest attractor to a state.
        """
        state = state or self.field_state
        if not state or not self.attractors:
            return None
        
        best_attractor = None
        best_distance = float('inf')
        
        for attractor in self.attractors:
            center = attractor.get("center", {})
            distance = sum(
                (state.get(k, 0) - center.get(k, 0)) ** 2
                for k in set(state.keys()) | set(center.keys())
            ) ** 0.5
            
            if distance < best_distance:
                best_distance = distance
                best_attractor = attractor
        
        return best_attractor
    
    def compute(
        self,
        initial_state: Optional[Dict[str, Any]] = None,
        max_steps: int = 100,
        convergence_threshold: float = 0.001
    ) -> AttractorSolution:
        """
        Compute a solution through attractor convergence.
        
        Evolves the field until it converges to an attractor.
        """
        if initial_state:
            self.set_field_state(initial_state)
        
        # Evolve until convergence
        prev_energy = self.compute_energy()
        path = []
        
        for step in range(max_steps):
            gradient = self.compute_gradient()
            gradient_norm = sum(g*g for g in gradient.values()) ** 0.5
            
            if gradient_norm < convergence_threshold:
                break
            
            # Simple gradient step
            for key in self.field_state:
                self.field_state[key] -= 0.1 * gradient.get(key, 0)
            
            new_energy = self.compute_energy()
            path.append({
                "step": step,
                "state": self.field_state.copy(),
                "energy": new_energy
            })
            
            if abs(prev_energy - new_energy) < convergence_threshold:
                break
            
            prev_energy = new_energy
        
        # Determine attractor type
        attractor = self.find_attractor()
        attractor_type = AttractorType.POINT
        if attractor:
            attractor_type = AttractorType(attractor.get("type", "point"))
        
        return AttractorSolution(
            solution_id=f"sol_{len(self.convergence_history)}",
            attractor_type=attractor_type,
            state=self.field_state.copy(),
            convergence_path=path,
            stability_score=1.0 / (1.0 + self.compute_energy()),
            energy=self.compute_energy()
        )
    
    def get_field_coherence(self) -> float:
        """Get coherence of the current field state."""
        if not self.attractors:
            return 1.0
        
        attractor = self.find_attractor()
        if not attractor:
            return 0.0
        
        center = attractor.get("center", {})
        if not center:
            return 1.0
        
        matches = sum(
            1 for k in center
            if k in self.field_state and self.field_state[k] == center[k]
        )
        return matches / len(center) if center else 1.0