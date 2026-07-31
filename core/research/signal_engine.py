"""
Phase 3 — Research Signal Engine

Detects knowledge gaps, emerging domains, and research opportunities.
Integrates with Horizon (news radar) and OpenAlex (research API).

This is where the system becomes autonomous:
- Monitors news/trends for relevant signals
- Detects knowledge gaps in the vault
- Spawns research tasks automatically
- Identifies emerging domains before they peak
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import uuid


@dataclass
class ResearchSignal:
    """A detected research signal."""
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    source: str = ""  # horizon, openalex, manual
    domain: str = ""
    relevance_score: float = 0.0  # 0-1
    novelty_score: float = 0.0   # 0-1
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "new"  # new, researching, completed, archived
    
    # Gap analysis
    is_knowledge_gap: bool = False
    related_concepts: list[str] = field(default_factory=list)
    missing_concepts: list[str] = field(default_factory=list)


@dataclass
class KnowledgeGap:
    """A detected gap in the knowledge graph."""
    gap_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    domain: str = ""
    description: str = ""
    severity: float = 0.0  # 0-1 (how critical is this gap)
    related_entities: list[str] = field(default_factory=list)
    suggested_research: list[str] = field(default_factory=list)
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ResearchSignalEngine:
    """
    Detects and routes research signals.
    
    Sources:
    - Horizon: news/trend monitoring
    - OpenAlex: research paper monitoring
    - Knowledge Graph: gap detection
    - Manual: user-flagged topics
    """
    
    def __init__(self, graph_store=None, ontology_engine=None):
        self.graph_store = graph_store
        self.ontology_engine = ontology_engine
        self._signals: list[ResearchSignal] = []
        self._gaps: list[KnowledgeGap] = []
    
    def detect_gaps(self) -> list[KnowledgeGap]:
        """
        Detect knowledge gaps by analyzing the knowledge graph.
        
        Gap detection strategies:
        1. Topology voids: regions with few connections
        2. Missing parents: concepts without hierarchy
        3. Contradictions: conflicting claims
        4. Low-coverage domains: domains with few entities
        """
        gaps = []
        
        if self.graph_store:
            entities = self.graph_store.get_all_entities()
            relationships = self.graph_store.get_all_relationships()
            
            # Find entities with few connections
            for entity in entities:
                neighbors = self.graph_store.get_neighbors(entity.get("name", ""))
                if len(neighbors) <= 1:
                    gaps.append(KnowledgeGap(
                        domain=entity.get("entity_type", "unknown"),
                        description=f"Low connectivity: {entity.get('name', '')} has only {len(neighbors)} connections",
                        severity=0.5,
                        related_entities=[entity.get("name", "")],
                    ))
        
        if self.ontology_engine:
            # Check for missing domains
            ontology = self.ontology_engine.build_ontology()
            # Compare ontology against graph coverage
            # TODO: implement ontology-graph comparison
        
        self._gaps.extend(gaps)
        return gaps
    
    def add_signal(self, signal: ResearchSignal):
        """Add a research signal."""
        self._signals.append(signal)
    
    def get_signals(self, domain: str = None, min_relevance: float = 0.0) -> list[ResearchSignal]:
        """Get research signals, optionally filtered."""
        signals = self._signals
        if domain:
            signals = [s for s in signals if s.domain == domain]
        if min_relevance > 0:
            signals = [s for s in signals if s.relevance_score >= min_relevance]
        return sorted(signals, key=lambda s: s.relevance_score, reverse=True)
    
    def get_gaps(self, min_severity: float = 0.0) -> list[KnowledgeGap]:
        """Get knowledge gaps, optionally filtered by severity."""
        gaps = self._gaps
        if min_severity > 0:
            gaps = [g for g in gaps if g.severity >= min_severity]
        return sorted(gaps, key=lambda g: g.severity, reverse=True)
    
    def generate_research_tasks(self, max_tasks: int = 5) -> list[dict]:
        """
        Generate research tasks from detected gaps and signals.
        This is the autonomous research spawning point.
        """
        tasks = []
        
        # From gaps
        for gap in self.get_gaps(min_severity=0.3)[:max_tasks]:
            tasks.append({
                "type": "gap_research",
                "gap_id": gap.gap_id,
                "domain": gap.domain,
                "description": f"Research gap: {gap.description}",
                "suggested_queries": gap.suggested_research,
                "priority": gap.severity,
            })
        
        # From high-relevance signals
        for signal in self.get_signals(min_relevance=0.7)[:max_tasks]:
            tasks.append({
                "type": "signal_research",
                "signal_id": signal.signal_id,
                "domain": signal.domain,
                "description": f"Follow up: {signal.title}",
                "suggested_queries": [signal.title],
                "priority": signal.relevance_score,
            })
        
        return tasks[:max_tasks]
