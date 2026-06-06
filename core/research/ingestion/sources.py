"""
Source registry + domain filter for the research mesh.

Defines which sources are available, which domains to ingest, and
provides the canonical domain→query mapping for each source.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ============================================================
# INITIAL DOMAINS — curated aggressively per BUILD-NOTES
# ============================================================

INITIAL_DOMAINS: List[str] = [
    "agent_orchestration",
    "memory_systems",
    "distributed_cognition",
    "knowledge_graphs",
    "vector_retrieval",
    "reinforcement_learning",
    "attention_mechanisms",
    "inference_optimization",
    "llm_systems",
    "market_microstructure",
    "topology_network_theory",
    "entropy_systems",
    "causal_inference",
    "graph_neural_networks",
    "self_supervised_learning",
]

# Domain → OpenAlex search query mapping
DOMAIN_OPENALEX_QUERIES: Dict[str, str] = {
    "agent_orchestration": "agent orchestration multi-agent",
    "memory_systems": "memory systems long-term memory neural",
    "distributed_cognition": "distributed cognition swarm intelligence",
    "knowledge_graphs": "knowledge graph embedding reasoning",
    "vector_retrieval": "vector search approximate nearest neighbor retrieval",
    "reinforcement_learning": "reinforcement learning policy optimization",
    "attention_mechanisms": "attention mechanism transformer",
    "inference_optimization": "inference optimization quantization pruning",
    "llm_systems": "large language model LLM systems",
    "market_microstructure": "market microstructure liquidity",
    "topology_network_theory": "network topology graph theory",
    "entropy_systems": "entropy information theory complex systems",
    "causal_inference": "causal inference causal discovery",
    "graph_neural_networks": "graph neural network GNN",
    "self_supervised_learning": "self-supervised learning contrastive",
}

# Domain → arXiv category mapping
DOMAIN_ARXIV_CATEGORIES: Dict[str, List[str]] = {
    "agent_orchestration": ["cs.AI", "cs.MA"],
    "memory_systems": ["cs.AI", "cs.LG", "cs.CL"],
    "distributed_cognition": ["cs.AI", "cs.MA", "cs.NE"],
    "knowledge_graphs": ["cs.AI", "cs.CL", "cs.IR"],
    "vector_retrieval": ["cs.IR", "cs.LG", "cs.DB"],
    "reinforcement_learning": ["cs.LG", "cs.AI", "stat.ML"],
    "attention_mechanisms": ["cs.LG", "cs.CL", "cs.AI"],
    "inference_optimization": ["cs.LG", "cs.DC", "cs.PF"],
    "llm_systems": ["cs.CL", "cs.AI", "cs.LG"],
    "market_microstructure": ["q-fin.TR", "q-fin.ST"],
    "topology_network_theory": ["cs.SI", "math.CO", "cs.NI"],
    "entropy_systems": ["cs.IT", "math.IT", "nlin.CD"],
    "causal_inference": ["cs.LG", "stat.ME", "cs.AI"],
    "graph_neural_networks": ["cs.LG", "cs.AI"],
    "self_supervised_learning": ["cs.LG", "cs.CV", "cs.CL"],
}


@dataclass
class SourceConfig:
    """Configuration for a single ingestion source."""
    name: str
    base_url: str
    api_key: str = ""
    mailto: str = "ops@larger-lab.local"   # For OpenAlex polite pool
    rate_limit_per_second: float = 10.0
    max_retries: int = 3
    timeout_seconds: int = 30
    enabled: bool = True


# ============================================================
# SOURCE REGISTRY
# ============================================================

class SourceRegistry:
    """
    Central registry for all ingestion sources.
    Each source client registers here on import.
    """

    def __init__(self):
        self._sources: Dict[str, SourceConfig] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(SourceConfig(
            name="openalex",
            base_url="https://api.openalex.org",
            rate_limit_per_second=10.0,     # Polite pool with mailto
            max_retries=3,
        ))
        self.register(SourceConfig(
            name="arxiv",
            base_url="http://export.arxiv.org/api/query",
            rate_limit_per_second=3.0,      # arXiv asks for ≤3 req/s
            max_retries=3,
        ))
        self.register(SourceConfig(
            name="semantic_scholar",
            base_url="https://api.semanticscholar.org/graph/v1",
            rate_limit_per_second=1.0,      # S2 free tier: 1 req/s
            max_retries=3,
        ))

    def register(self, config: SourceConfig):
        self._sources[config.name] = config

    def get(self, name: str) -> Optional[SourceConfig]:
        return self._sources.get(name)

    def list_enabled(self) -> List[SourceConfig]:
        return [s for s in self._sources.values() if s.enabled]

    @property
    def domains(self) -> List[str]:
        return list(INITIAL_DOMAINS)

    def openalex_query_for_domain(self, domain: str) -> str:
        return DOMAIN_OPENALEX_QUERIES.get(domain, domain.replace("_", " "))

    def arxiv_categories_for_domain(self, domain: str) -> List[str]:
        return DOMAIN_ARXIV_CATEGORIES.get(domain, ["cs.AI"])


# Singleton
_registry = SourceRegistry()


def get_registry() -> SourceConfig:
    return _registry
