"""
Phase 1.5.1 — Entity Extraction

Converts documents, reports, code, vault notes into graph entities.
Each entity is a semantic object (concept, system, person, framework, etc.)
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class Entity:
    """A node in the knowledge graph."""
    entity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str = ""  # concept, system, person, framework, tool, protocol, domain
    canonical_name: str = ""
    aliases: list[str] = field(default_factory=list)
    description: str = ""
    source_refs: list[str] = field(default_factory=list)  # CognitionObject IDs
    confidence: float = 1.0
    
    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "canonical_name": self.canonical_name,
            "aliases": self.aliases,
            "description": self.description,
            "source_refs": self.source_refs,
        }


class EntityExtractor:
    """
    Extracts entities from parsed content.
    
    Entity types:
    - concept: abstract idea (e.g., "semantic memory", "vector cognition")
    - system: software system (e.g., "OCE", "SRRA", "OpenAlex")
    - framework: methodology (e.g., "Phase 1.2", "Parser Router")
    - tool: specific tool (e.g., "markitdown", "codegraph")
    - protocol: standard/protocol (e.g., "MCP", "REST")
    - domain: knowledge domain (e.g., "AI", "Quant Finance")
    - person: author, researcher
    """
    
    # Known entity patterns for OCE/SRRA domain
    KNOWN_ENTITIES = {
        "OCE": ("system", "Observer Core Environment"),
        "SRRA": ("system", "Sovereign Recursive Research Architecture"),
        "OPH": ("system", "Observatory"),
        "PO": ("system", "Primary Observer"),
        "OpenAlex": ("tool", "OpenAlex Research API"),
        "markitdown": ("tool", "Microsoft MarkItDown Document Converter"),
        "codegraph": ("tool", "CodeGraph Semantic Code Intelligence"),
        "turbovec": ("tool", "TurboQuant Vector Search Index"),
        "liteparse": ("tool", "LiteParse Document Parser"),
        "dograh": ("system", "Dograh Voice AI Platform"),
        "notebooklm": ("tool", "Google NotebookLM"),
        "semantic memory": ("concept", "Meaning-linked persistent memory"),
        "vector cognition": ("concept", "High-dimensional semantic reasoning"),
        "knowledge graph": ("concept", "Entity-relationship topology"),
        "procedural cognition": ("concept", "Reusable cognition workflows"),
        "cognition substrate": ("concept", "Foundational cognition infrastructure"),
    }
    
    def extract(self, text: str, source_ref: str = "") -> list[Entity]:
        """
        Extract entities from text.
        
        Strategy:
        1. Match against known entity dictionary
        2. Extract capitalized phrases as potential concepts
        3. Extract wiki-links [[Like This]]
        4. Deduplicate by canonical name
        """
        entities = []
        found_names = set()
        
        # Match known entities
        for name, (etype, description) in self.KNOWN_ENTITIES.items():
            if name.lower() in text.lower() and name not in found_names:
                entity = Entity(
                    entity_type=etype,
                    canonical_name=name,
                    description=description,
                    source_refs=[source_ref] if source_ref else [],
                    confidence=0.95,
                )
                entities.append(entity)
                found_names.add(name)
        
        # Extract wiki-links [[Entity Name]]
        import re
        wiki_links = re.findall(r'\[\[([^\]]+)\]\]', text)
        for link in wiki_links:
            if link not in found_names:
                entity = Entity(
                    entity_type="concept",
                    canonical_name=link,
                    source_refs=[source_ref] if source_ref else [],
                    confidence=0.8,
                )
                entities.append(entity)
                found_names.add(link)
        
        return entities
    
    def canonicalize(self, name: str) -> str:
        """Normalize entity name to canonical form."""
        # Check known aliases
        for canonical, (etype, desc) in self.KNOWN_ENTITIES.items():
            if name.lower() == canonical.lower():
                return canonical
            # Check if name is an alias
            if name.lower() in [a.lower() for a in self.KNOWN_ENTITIES.get(canonical, ("", ""))[0].split()]:
                return canonical
        return name.strip()
