"""
Phase 1.5.3 — Ontology Engine

Builds concept hierarchies from the knowledge graph.
Creates taxonomy trees: parent-child relationships between concepts.
"""

from typing import Optional


class OntologyEngine:
    """
    Builds and manages concept hierarchies (ontology trees).
    
    Example hierarchy:
        AI Systems
         └── Agent Systems
              └── SRRA
                   └── OCE
    """
    
    # Initial ontology seed for OCE/SRRA domain
    ONTOLOGY_SEED = {
        "AI Systems": {
            "Agent Systems": {
                "SRRA": {
                    "OCE": {},
                    "PO": {},
                    "OPH": {},
                },
                "OpenClaw": {},
                "Codex": {},
            },
            "Memory Systems": {
                "Semantic Memory": {},
                "Vector Memory": {},
                "Knowledge Graph": {},
                "Procedural Memory": {},
            },
            "Language Models": {
                "OpenRouter": {},
                "Ollama": {},
            },
        },
        "Infrastructure": {
            "Parser Stack": {
                "markitdown": {},
                "odl-pdf": {},
                "liteparse": {},
                "chandra": {},
            },
            "Vector Search": {
                "turbovec": {},
                "FAISS": {},
            },
            "Knowledge Graph": {
                "codegraph": {},
                "NetworkX": {},
                "Neo4j": {},
            },
            "Storage": {
                "Obsidian Vault": {},
                "SQLite": {},
            },
        },
        "Interfaces": {
            "VTuber": {
                "dograh": {},
                "dotlottie-web": {},
                "Open-LLM-VTuber": {},
            },
            "Telegram": {},
            "Web UI": {
                "OCE Cockpit": {},
                "SRRA-OPH Observatory": {},
            },
        },
        "Research": {
            "Ingestion": {
                "OpenAlex": {},
                "arXiv": {},
                "Web Scraping": {},
            },
            "Distillation": {
                "notebooklm-py": {},
                "book-to-skill": {},
            },
            "Synthesis": {
                "Sisyphus": {},
            },
        },
    }
    
    def __init__(self, graph_store=None):
        self.graph_store = graph_store
    
    def build_ontology(self) -> dict:
        """Build ontology tree from seed + graph data."""
        return self.ONTOLOGY_SEED
    
    def get_parent(self, concept: str) -> Optional[str]:
        """Get parent concept in hierarchy."""
        def search(tree, target, parent=None):
            for key, children in tree.items():
                if key == target:
                    return parent
                result = search(children, target, key)
                if result:
                    return result
            return None
        
        return search(self.ONTOLOGY_SEED, concept)
    
    def get_children(self, concept: str) -> list[str]:
        """Get child concepts in hierarchy."""
        def find_node(tree, target):
            for key, children in tree.items():
                if key == target:
                    return children
                result = find_node(children, target)
                if result is not None:
                    return result
            return None
        
        node = find_node(self.ONTOLOGY_SEED, concept)
        return list(node.keys()) if node else []
    
    def get_depth(self, concept: str) -> int:
        """Get depth of concept in hierarchy (root = 0)."""
        def find_depth(tree, target, depth=0):
            for key, children in tree.items():
                if key == target:
                    return depth
                result = find_depth(children, target, depth + 1)
                if result >= 0:
                    return result
            return -1
        
        return find_depth(self.ONTOLOGY_SEED, concept)
    
    def to_mermaid(self) -> str:
        """Export ontology as Mermaid diagram."""
        lines = ["graph TB"]
        
        def add_nodes(tree, parent=None):
            for key, children in tree.items():
                safe_key = key.replace(" ", "_").replace("-", "_")
                if parent:
                    safe_parent = parent.replace(" ", "_").replace("-", "_")
                    lines.append(f"    {safe_parent} --> {safe_key}")
                add_nodes(children, key)
        
        add_nodes(self.ONTOLOGY_SEED)
        return "\n".join(lines)
