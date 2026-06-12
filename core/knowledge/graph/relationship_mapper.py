"""
Phase 1.5.2 — Relationship Mapping

Connects entities with typed semantic edges.
Creates the semantic topology (knowledge graph edges).
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class Relationship:
    """An edge in the knowledge graph."""
    relationship_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""  # entity canonical name
    target: str = ""  # entity canonical name
    relation: str = ""  # relation type
    confidence: float = 1.0
    source_refs: list[str] = field(default_factory=list)
    
    # Relation types
    DEPENDS_ON = "depends_on"
    POWERS = "powers"
    EXTENDS = "extends"
    RELATED_TO = "related_to"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    FEEDS = "feeds"
    ABSTRACTS = "abstracts"
    USES = "uses"
    PART_OF = "part_of"
    
    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "confidence": self.confidence,
        }


class RelationshipMapper:
    """
    Maps relationships between entities.
    
    Strategy:
    1. Co-occurrence analysis (entities appearing together)
    2. Semantic reasoning (determine relation meaning)
    3. Confidence scoring (reject weak links)
    """
    
    # Known relationships for OCE/SRRA domain
    KNOWN_RELATIONSHIPS = [
        ("OpenAlex", "FEEDS", "research ingestion"),
        ("markitdown", "POWERS", "Parser Router"),
        ("odl-pdf", "POWERS", "research PDF extraction"),
        ("liteparse", "POWERS", "multimodal parsing"),
        ("chandra", "POWERS", "OCR cognition"),
        ("Parser Router", "FEEDS", "Cognition Objects"),
        ("Cognition Objects", "FEEDS", "Semantic Memory"),
        ("Semantic Memory", "FEEDS", "Knowledge Graph"),
        ("Knowledge Graph", "FEEDS", "OCE"),
        ("turbovec", "POWERS", "vector cognition"),
        ("codegraph", "POWERS", "architecture topology"),
        ("OCE", "EXTENDS", "SRRA"),
        ("PO", "USES", "OCE"),
        ("VTuber", "USES", "dograh"),
        ("notebooklm-py", "POWERS", "content distillation"),
    ]
    
    def map_relationships(self, entities: list, text: str = "") -> list[Relationship]:
        """
        Map relationships between a set of entities.
        
        Strategy:
        1. Check known relationships
        2. Co-occurrence analysis
        3. Return deduplicated edges
        """
        relationships = []
        entity_names = {e.canonical_name for e in entities}
        
        # Apply known relationships
        for source, relation, target in self.KNOWN_RELATIONSHIPS:
            if source in entity_names and target in entity_names:
                rel = Relationship(
                    source=source,
                    target=target,
                    relation=relation,
                    confidence=0.95,
                )
                relationships.append(rel)
        
        # Co-occurrence: entities in same paragraph
        if text:
            paragraphs = text.split("\n\n")
            for para in paragraphs:
                para_entities = [e for e in entities if e.canonical_name in para]
                for i, e1 in enumerate(para_entities):
                    for e2 in para_entities[i+1:]:
                        # Check if relationship already exists
                        exists = any(
                            (r.source == e1.canonical_name and r.target == e2.canonical_name) or
                            (r.source == e2.canonical_name and r.target == e1.canonical_name)
                            for r in relationships
                        )
                        if not exists:
                            relationships.append(Relationship(
                                source=e1.canonical_name,
                                target=e2.canonical_name,
                                relation=Relationship.RELATED_TO,
                                confidence=0.6,
                            ))
        
        return relationships
    
    def validate_edge(self, relationship: Relationship) -> bool:
        """Validate a relationship edge. Reject weak links."""
        if relationship.confidence < 0.3:
            return False
        if relationship.source == relationship.target:
            return False
        return True
