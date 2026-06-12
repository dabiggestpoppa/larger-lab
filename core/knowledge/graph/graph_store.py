"""
Phase 1.5.4 — Knowledge Graph Store

Persistent semantic topology storage.
Starts with NetworkX (local), scales to Neo4j (production).
"""

from typing import Optional
import os
import json


class GraphStore:
    """
    Persistent knowledge graph storage.
    
    Backend: NetworkX (default) → Neo4j (production)
    
    Contents:
    - nodes: entities
    - edges: relationships
    - weights: confidence scores
    - labels: semantic roles
    - clusters: concept ecosystems
    """
    
    def __init__(self, backend: str = "networkx", db_path: str = ""):
        self.backend = backend
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "data", "knowledge_graph"
        )
        self._graph = None
        self._ensure_dir()
    
    def _ensure_dir(self):
        """Ensure data directory exists."""
        os.makedirs(self.db_path, exist_ok=True)
    
    def _get_graph(self):
        """Lazy-load graph backend."""
        if self._graph is None:
            if self.backend == "networkx":
                self._graph = self._init_networkx()
            elif self.backend == "neo4j":
                self._graph = self._init_neo4j()
        return self._graph
    
    def _init_networkx(self):
        """Initialize NetworkX graph."""
        try:
            import networkx as nx
            return nx.DiGraph()
        except ImportError:
            raise ImportError("networkx not installed. Run: pip install networkx")
    
    def _init_neo4j(self):
        """Initialize Neo4j connection (production)."""
        # TODO: Neo4j integration for production scaling
        raise NotImplementedError("Neo4j backend not yet implemented")
    
    def add_entity(self, entity):
        """Add an entity node to the graph."""
        graph = self._get_graph()
        graph.add_node(
            entity.canonical_name,
            entity_type=entity.entity_type,
            description=entity.description,
            aliases=entity.aliases,
            confidence=entity.confidence,
        )
    
    def add_relationship(self, relationship):
        """Add a relationship edge to the graph."""
        graph = self._get_graph()
        graph.add_edge(
            relationship.source,
            relationship.target,
            relation=relationship.relation,
            confidence=relationship.confidence,
        )
    
    def get_entity(self, name: str) -> Optional[dict]:
        """Get entity by canonical name."""
        graph = self._get_graph()
        if name in graph.nodes:
            return dict(graph.nodes[name])
        return None
    
    def get_neighbors(self, name: str) -> list[str]:
        """Get neighboring entities."""
        graph = self._get_graph()
        if name in graph.nodes:
            return list(graph.successors(name)) + list(graph.predecessors(name))
        return []
    
    def find_path(self, source: str, target: str) -> list[str]:
        """Find shortest path between two entities."""
        graph = self._get_graph()
        try:
            import networkx as nx
            return nx.shortest_path(graph, source, target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    def get_all_entities(self) -> list[dict]:
        """Get all entities in the graph."""
        graph = self._get_graph()
        return [
            {"name": name, **dict(data)}
            for name, data in graph.nodes(data=True)
        ]
    
    def get_all_relationships(self) -> list[dict]:
        """Get all relationships in the graph."""
        graph = self._get_graph()
        return [
            {"source": u, "target": v, **dict(data)}
            for u, v, data in graph.edges(data=True)
        ]
    
    def save(self, filename: str = "graph.json"):
        """Save graph to JSON."""
        path = os.path.join(self.db_path, filename)
        data = {
            "entities": self.get_all_entities(),
            "relationships": self.get_all_relationships(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self, filename: str = "graph.json"):
        """Load graph from JSON."""
        path = os.path.join(self.db_path, filename)
        if not os.path.exists(path):
            return
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for entity_data in data.get("entities", []):
            name = entity_data.pop("name", "")
            if name:
                self._get_graph().add_node(name, **entity_data)
        
        for rel_data in data.get("relationships", []):
            source = rel_data.pop("source", "")
            target = rel_data.pop("target", "")
            if source and target:
                self._get_graph().add_edge(source, target, **rel_data)
