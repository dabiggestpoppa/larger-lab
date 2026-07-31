"""
R2 — Semantic Relationship Construction

Builds connections between knowledge objects:
- Concept entity extraction
- Semantic relationship detection
- Causal chain construction
- Knowledge graph building
- Similarity clustering
- Dependency mapping
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple

from .schema import KnowledgeObject, Claim, Mechanism

logger = logging.getLogger("oce.rce.relationships")


# ─── R2.1 Concept Entity Extraction ───

# Scientific stop words to filter out
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "this", "that",
    "these", "those", "it", "its", "we", "our", "they", "their", "which",
    "what", "who", "whom", "how", "when", "where", "why", "not", "no",
    "nor", "so", "if", "then", "than", "too", "very", "just", "about",
    "also", "more", "most", "some", "any", "each", "every", "all", "both",
    "few", "many", "much", "several", "other", "such", "only", "own",
    "same", "new", "old", "first", "last", "long", "great", "little",
    "right", "big", "high", "different", "small", "large", "next",
    "early", "young", "important", "public", "bad", "good", "make",
    "like", "use", "using", "used", "based", "show", "shown", "study",
    "paper", "propose", "proposed", "method", "methods", "approach",
    "result", "results", "performance", "model", "models", "data",
    "set", "sets", "one", "two", "three", "four", "five", "six",
    "seven", "eight", "nine", "ten", "et", "al", "fig", "figure",
    "table", "eq", "equation", "sec", "section", "ref", "reference",
    "however", "therefore", "thus", "hence", "although", "while",
    "because", "since", "given", "despite", "yet", "still", "well",
}


class ConceptEntity:
    """R2.1 — Extracted concept entity."""
    
    def __init__(self, name: str, domain: str = "", frequency: int = 1):
        self.name = name.lower().strip()
        self.domain = domain
        self.frequency = frequency
        self.related_concepts: List[str] = []
        self.source_papers: List[str] = []
    
    def __repr__(self):
        return f"Concept({self.name}, freq={self.frequency})"


class RelationshipBuilder:
    """
    R2 — Semantic Relationship Construction.
    
    Takes KnowledgeObjects from R1 and builds:
    1. Concept entities
    2. Semantic relationships (causes, influences, depends_on, etc.)
    3. Causal chains
    4. Knowledge graph
    5. Similarity clusters
    6. Dependency maps
    
    Usage:
        builder = RelationshipBuilder()
        graph = builder.build_graph(knowledge_objects)
    """
    
    def __init__(self, similarity_threshold: float = 0.35):
        self.similarity_threshold = similarity_threshold
        self._concepts: Dict[str, ConceptEntity] = {}
        self._relationships: List[Dict[str, Any]] = []
        self._graph: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    def build_graph(
        self, knowledge_objects: List[KnowledgeObject]
    ) -> Dict[str, Any]:
        """
        Build complete relationship graph from knowledge objects.
        
        Returns:
            Dict with keys: concepts, relationships, causal_chains, clusters, graph
        """
        # R2.1 — Extract concept entities
        concepts = self._extract_concepts(knowledge_objects)
        
        # R2.2 — Detect semantic relationships
        relationships = self._detect_relationships(knowledge_objects, concepts)
        
        # R2.3 — Build causal chains
        causal_chains = self._build_causal_chains(knowledge_objects)
        
        # R2.4 — Build knowledge graph
        graph = self._build_knowledge_graph(concepts, relationships, causal_chains)
        
        # R2.6 — Similarity clustering
        clusters = self._cluster_similar_concepts(concepts)
        
        # R2.5 — Dependency mapping
        dependencies = self._map_dependencies(knowledge_objects)
        
        return {
            "concepts": {k: self._concept_to_dict(v) for k, v in concepts.items()},
            "relationships": relationships,
            "causal_chains": causal_chains,
            "clusters": clusters,
            "dependencies": dependencies,
            "graph": dict(graph),
            "stats": {
                "num_concepts": len(concepts),
                "num_relationships": len(relationships),
                "num_causal_chains": len(causal_chains),
                "num_clusters": len(clusters),
                "num_papers": len(knowledge_objects),
            },
        }
    
    # ─── R2.1 Concept Entity Extraction ───
    
    def _extract_concepts(
        self, knowledge_objects: List[KnowledgeObject]
    ) -> Dict[str, ConceptEntity]:
        """Extract concept entities from knowledge objects."""
        concepts: Dict[str, ConceptEntity] = {}
        
        for obj in knowledge_objects:
            # Extract from claims
            for claim in obj.main_claims:
                self._extract_phrases_from_text(
                    claim.claim, concepts, obj.domain, obj.paper_id
                )
            
            # Extract from mechanisms
            for mech in obj.mechanisms:
                self._extract_phrases_from_text(
                    mech.cause + " " + mech.effect, concepts, obj.domain, obj.paper_id
                )
            
            # Extract from equations
            for eq in obj.equations:
                for var in eq.variables:
                    name = var.lower().strip()
                    if name not in concepts:
                        concepts[name] = ConceptEntity(name, eq.mathematical_framework)
                    concepts[name].frequency += 1
                    concepts[name].source_papers.append(obj.paper_id)
        
        # Filter low-frequency concepts
        return {
            k: v for k, v in concepts.items()
            if v.frequency >= 1 and len(k) > 2
        }
    
    def _extract_phrases_from_text(
        self,
        text: str,
        concepts: Dict[str, ConceptEntity],
        domain: str,
        paper_id: str,
    ) -> None:
        """Extract noun phrases and technical terms from text."""
        # Extract bigrams and trigrams
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Single important words (not stop words)
        for word in words:
            if word not in STOP_WORDS and len(word) > 3:
                if word not in concepts:
                    concepts[word] = ConceptEntity(word, domain)
                concepts[word].frequency += 1
                if paper_id not in concepts[word].source_papers:
                    concepts[word].source_papers.append(paper_id)
        
        # Bigrams
        for i in range(len(words) - 1):
            if words[i] not in STOP_WORDS and words[i + 1] not in STOP_WORDS:
                bigram = f"{words[i]} {words[i + 1]}"
                if bigram not in concepts:
                    concepts[bigram] = ConceptEntity(bigram, domain)
                concepts[bigram].frequency += 0.5
                if paper_id not in concepts[bigram].source_papers:
                    concepts[bigram].source_papers.append(paper_id)
    
    # ─── R2.2 Semantic Relationship Detection ───
    
    def _detect_relationships(
        self,
        knowledge_objects: List[KnowledgeObject],
        concepts: Dict[str, ConceptEntity],
    ) -> List[Dict[str, Any]]:
        """Detect semantic relationships between concepts."""
        relationships = []
        
        for obj in knowledge_objects:
            # From mechanisms: cause → effect
            for mech in obj.mechanisms:
                cause_key = mech.cause.lower().strip()[:40]
                effect_key = mech.effect.lower().strip()[:40]
                
                if cause_key and effect_key:
                    relationships.append({
                        "source": cause_key,
                        "target": effect_key,
                        "type": "causes",
                        "confidence": mech.confidence,
                        "source_paper": obj.paper_id,
                    })
            
            # From causal relationships
            for rel in obj.causal_relationships:
                cause_key = rel.get("cause", "").lower().strip()[:40]
                effect_key = rel.get("effect", "").lower().strip()[:40]
                
                if cause_key and effect_key:
                    relationships.append({
                        "source": cause_key,
                        "target": effect_key,
                        "type": rel.get("relationship", "relates_to"),
                        "confidence": 0.5,
                        "source_paper": obj.paper_id,
                    })
            
            # From claims: co-occurrence relationships
            claim_concepts = []
            for claim in obj.main_claims:
                claim_concepts.extend(
                    w for w in re.findall(r'\b[a-zA-Z]{4,}\b', claim.claim.lower())
                    if w not in STOP_WORDS
                )
            
            # Co-occurring concepts in claims are related
            for i, c1 in enumerate(claim_concepts):
                for c2 in claim_concepts[i + 1:]:
                    if c1 != c2:
                        relationships.append({
                            "source": c1,
                            "target": c2,
                            "type": "co_occurs",
                            "confidence": 0.3,
                            "source_paper": obj.paper_id,
                        })
        
        return relationships
    
    # ─── R2.3 Causal Chain Construction ───
    
    def _build_causal_chains(
        self, knowledge_objects: List[KnowledgeObject]
    ) -> List[Dict[str, Any]]:
        """Build multi-step causal chains from mechanisms."""
        # Collect all cause→effect edges
        edges: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        
        for obj in knowledge_objects:
            for mech in obj.mechanisms:
                cause = mech.cause.lower().strip()[:40]
                effect = mech.effect.lower().strip()[:40]
                if cause and effect:
                    edges[cause].append((effect, mech.confidence))
        
        # Find chains: A → B → C
        chains = []
        visited = set()
        
        for start_node in edges:
            if start_node in visited:
                continue
            
            chain = [start_node]
            current = start_node
            chain_confidence = 1.0
            
            for _ in range(5):  # Max chain length
                if current not in edges or not edges[current]:
                    break
                
                # Pick highest-confidence next node
                next_node, conf = max(edges[current], key=lambda x: x[1])
                
                if next_node in chain:  # Avoid cycles
                    break
                
                chain.append(next_node)
                chain_confidence *= conf
                current = next_node
            
            if len(chain) >= 3:  # Only keep chains with 3+ nodes
                chains.append({
                    "chain": chain,
                    "length": len(chain),
                    "confidence": chain_confidence ** (1 / len(chain)),  # Geometric mean
                    "type": "causal_chain",
                })
                visited.update(chain)
        
        return chains
    
    # ─── R2.4 Knowledge Graph ───
    
    def _build_knowledge_graph(
        self,
        concepts: Dict[str, ConceptEntity],
        relationships: List[Dict[str, Any]],
        causal_chains: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Build the central knowledge graph."""
        graph: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        for rel in relationships:
            source = rel["source"]
            target = rel["target"]
            graph[source].append({
                "target": target,
                "type": rel["type"],
                "confidence": rel["confidence"],
            })
        
        # Add causal chains as hyper-edges
        for chain in causal_chains:
            chain_key = " → ".join(chain["chain"])
            graph[chain["chain"][0]].append({
                "target": chain["chain"][-1],
                "type": "causal_chain",
                "confidence": chain["confidence"],
                "chain": chain["chain"],
            })
        
        return dict(graph)
    
    # ─── R2.5 Dependency Mapping ───
    
    def _map_dependencies(
        self, knowledge_objects: List[KnowledgeObject]
    ) -> List[Dict[str, Any]]:
        """Map which concepts depend on which assumptions."""
        dependencies = []
        
        for obj in knowledge_objects:
            # Claims depend on assumptions
            claim_texts = " ".join(c.claim for c in obj.main_claims).lower()
            for assumption in obj.assumptions:
                # Check if claim text relates to assumption
                assumption_words = set(assumption.assumption.lower().split())
                claim_words = set(claim_texts.split())
                overlap = assumption_words & claim_words
                
                if len(overlap) >= 2:
                    dependencies.append({
                        "dependent": "claim",
                        "depends_on": assumption.assumption[:80],
                        "type": "assumption_dependency",
                        "strength": len(overlap) / max(len(assumption_words), 1),
                        "source_paper": obj.paper_id,
                    })
        
        return dependencies
    
    # ─── R2.6 Similarity Clustering ───
    
    def _cluster_similar_concepts(
        self, concepts: Dict[str, ConceptEntity]
    ) -> List[Dict[str, Any]]:
        """Cluster related concepts by domain and co-occurrence."""
        # Group by domain
        domain_groups: Dict[str, List[str]] = defaultdict(list)
        for name, concept in concepts.items():
            domain = concept.domain or "general"
            domain_groups[domain].append(name)
        
        # Within each domain, cluster by string similarity
        clusters = []
        for domain, concept_names in domain_groups.items():
            if len(concept_names) < 2:
                continue
            
            # Simple agglomerative clustering
            used: Set[str] = set()
            for i, name1 in enumerate(concept_names):
                if name1 in used:
                    continue
                
                cluster = [name1]
                used.add(name1)
                
                for name2 in concept_names[i + 1:]:
                    if name2 in used:
                        continue
                    similarity = SequenceMatcher(None, name1, name2).ratio()
                    if similarity >= self.similarity_threshold:
                        cluster.append(name2)
                        used.add(name2)
                
                if len(cluster) >= 2:
                    clusters.append({
                        "domain": domain,
                        "concepts": cluster,
                        "size": len(cluster),
                        "representative": cluster[0],
                    })
        
        return clusters
    
    # ─── Serialization ───
    
    def _concept_to_dict(self, concept: ConceptEntity) -> Dict[str, Any]:
        return {
            "name": concept.name,
            "domain": concept.domain,
            "frequency": concept.frequency,
            "related_concepts": concept.related_concepts,
            "source_papers": concept.source_papers,
        }
