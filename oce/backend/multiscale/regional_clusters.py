"""V3 Phase 7 — Regional Cognitive Clusters

Self-organizing clusters by interaction density.
Observers that frequently interact form regional clusters with shared context.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import uuid


@dataclass
class RegionalCluster:
    """A self-organizing cluster of observers with shared context."""
    
    cluster_id: str
    members: Set[str] = field(default_factory=set)
    shared_context: Dict[str, Any] = field(default_factory=dict)
    interaction_density: float = 0.0
    formation_time: datetime = field(default_factory=datetime.utcnow)
    last_activity: Optional[datetime] = None
    
    def add_member(self, observer_id: str) -> None:
        """Add an observer to the cluster."""
        self.members.add(observer_id)
        self.last_activity = datetime.utcnow()
    
    def remove_member(self, observer_id: str) -> bool:
        """Remove an observer from the cluster."""
        if observer_id in self.members:
            self.members.remove(observer_id)
            self.last_activity = datetime.utcnow()
            return True
        return False
    
    def update_interaction_density(self, density: float) -> None:
        """Update the interaction density metric."""
        self.interaction_density = density
        self.last_activity = datetime.utcnow()
    
    def get_member_count(self) -> int:
        """Get the number of members in the cluster."""
        return len(self.members)
    
    def is_active(self, threshold: float = 0.1) -> bool:
        """Check if cluster is active based on interaction density."""
        return self.interaction_density >= threshold


class ClusterRegistry:
    """Registry for managing regional clusters."""
    
    def __init__(self, density_threshold: float = 0.5):
        self._clusters: Dict[str, RegionalCluster] = {}
        self._observer_to_cluster: Dict[str, str] = {}
        self.density_threshold = density_threshold
    
    def create_cluster(self, observer_ids: List[str], **kwargs) -> RegionalCluster:
        """Create a new cluster with initial members."""
        cluster_id = f"cluster_{uuid.uuid4().hex[:8]}"
        cluster = RegionalCluster(cluster_id=cluster_id, **kwargs)
        
        for oid in observer_ids:
            cluster.add_member(oid)
            self._observer_to_cluster[oid] = cluster_id
        
        self._clusters[cluster_id] = cluster
        return cluster
    
    def get_cluster(self, cluster_id: str) -> Optional[RegionalCluster]:
        """Get a cluster by ID."""
        return self._clusters.get(cluster_id)
    
    def get_cluster_for_observer(self, observer_id: str) -> Optional[RegionalCluster]:
        """Get the cluster an observer belongs to."""
        cluster_id = self._observer_to_cluster.get(observer_id)
        return self._clusters.get(cluster_id) if cluster_id else None
    
    def get_all_clusters(self) -> List[RegionalCluster]:
        """Get all clusters."""
        return list(self._clusters.values())
    
    def get_active_clusters(self) -> List[RegionalCluster]:
        """Get clusters that meet the density threshold."""
        return [c for c in self._clusters.values() if c.is_active(self.density_threshold)]
    
    def calculate_interaction_density(self, observer_id: str, interaction_count: int, time_window: float) -> float:
        """Calculate interaction density for an observer."""
        if time_window <= 0:
            return 0.0
        return interaction_count / time_window
    
    def merge_clusters(self, cluster_id1: str, cluster_id2: str) -> Optional[RegionalCluster]:
        """Merge two clusters into one."""
        c1 = self._clusters.get(cluster_id1)
        c2 = self._clusters.get(cluster_id2)
        
        if not c1 or not c2:
            return None
        
        # Merge members
        for member in c2.members:
            c1.add_member(member)
            self._observer_to_cluster[member] = cluster_id1
        
        # Remove old cluster
        del self._clusters[cluster_id2]
        
        return c1