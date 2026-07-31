"""
Phase 1.5 — Knowledge Graph Engine

Transforms semantic retrieval into conceptual cognition.
Builds entity-relationship topology from parsed content.

Components:
- entity_extractor: identifies concepts, systems, people, frameworks
- relationship_mapper: connects entities with typed edges
- ontology_engine: builds concept hierarchies
- graph_store: persistent graph storage (NetworkX → Neo4j)
- traversal: graph navigation and pathfinding
- inference: relational reasoning over the graph
- abstraction: compresses concepts into higher-order structures
- gap_detector: identifies missing knowledge regions
"""

from .entity_extractor import EntityExtractor
from .relationship_mapper import RelationshipMapper
from .ontology_engine import OntologyEngine
from .graph_store import GraphStore

__all__ = [
    "EntityExtractor",
    "RelationshipMapper", 
    "OntologyEngine",
    "GraphStore",
]
