"""
L4.7 — Vault Sync Engine.

Bidirectional sync between O2C-VAULT/research/ and the SQLite knowledge graph.
- Vault → Graph: Scans vault paper notes, adds nodes/edges to graph_store
- Graph → Vault: (future) Updates vault notes when graph topology changes

Usage:
    from .vault_sync import VaultSync
    sync = VaultSync()
    result = await sync.sync_vault_to_graph()
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Vault paths
VAULT_ROOT = Path(__file__).resolve().parents[2] / "O2C-VAULT"
RESEARCH_PAPERS_DIR = VAULT_ROOT / "research" / "papers"
DOCTRINE_DIR = VAULT_ROOT / "doctrine"

# Regex for parsing vault note links
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]]")
TAG_RE = re.compile(r"#(\w+)(/\w+)?")


class VaultSync:
    """
    Syncs vault markdown notes to the SQLite knowledge graph.
    
    Scans O2C-VAULT/research/papers/ and O2C-VAULT/doctrine/,
    extracts nodes (papers, concepts, doctrine) and edges (links, citations),
    and upserts them into graph_store.
    """

    def __init__(self, vault_root: Optional[Path] = None):
        self.vault_root = vault_root or VAULT_ROOT
        self._graph_store = None

    def _get_graph_store(self):
        """Lazy-import graph_store to avoid circular deps."""
        if self._graph_store is None:
            try:
                from core.research.distillation.graph_store import GraphStore
                self._graph_store = GraphStore()
            except ImportError:
                logger.warning("graph_store not available — vault sync will be no-op")
                self._graph_store = False
        return self._graph_store if self._graph_store is not None else None

    async def sync_vault_to_graph(self) -> Dict[str, Any]:
        """
        Full sync: scan all vault notes and update the knowledge graph.
        
        Returns summary of changes.
        """
        gs = self._get_graph_store()
        if not gs:
            return {"status": "unavailable", "nodes_added": 0, "edges_added": 0}

        result = {
            "status": "ok",
            "nodes_added": 0,
            "edges_added": 0,
            "papers_synced": 0,
            "doctrine_synced": 0,
            "errors": [],
        }

        try:
            # Sync paper notes
            paper_result = await self._sync_paper_notes(gs)
            result["nodes_added"] += paper_result["nodes"]
            result["edges_added"] += paper_result["edges"]
            result["papers_synced"] = paper_result["count"]

            # Sync doctrine notes
            doctrine_result = await self._sync_doctrine_notes(gs)
            result["nodes_added"] += doctrine_result["nodes"]
            result["edges_added"] += doctrine_result["edges"]
            result["doctrine_synced"] = doctrine_result["count"]

        except Exception as exc:
            logger.error("vault_sync: error during sync: %s", exc)
            result["status"] = "error"
            result["errors"].append(str(exc))

        logger.info(
            "vault_sync: %d nodes, %d edges added (%d papers, %d doctrine)",
            result["nodes_added"], result["edges_added"],
            result["papers_synced"], result["doctrine_synced"],
        )
        return result

    async def _sync_paper_notes(self, gs) -> Dict[str, int]:
        """Sync paper notes from O2C-VAULT/research/papers/."""
        nodes = 0
        edges = 0
        count = 0

        if not RESEARCH_PAPERS_DIR.exists():
            return {"nodes": 0, "edges": 0, "count": 0}

        for md_file in RESEARCH_PAPERS_DIR.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                rel_path = str(md_file.relative_to(self.vault_root))

                # Extract title from first # heading
                title = md_file.stem.replace("_", " ")
                for line in content.split("\n"):
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

                # Extract tags
                tags = TAG_RE.findall(content)
                tag_list = [f"{t[0]}{t[1]}" for t in tags if t[0]]

                # Extract domain from path
                parts = rel_path.split("/")
                domain = parts[2] if len(parts) > 2 else "unknown"

                # Extract year from path
                year = 0
                if len(parts) > 3:
                    try:
                        year = int(parts[3])
                    except ValueError:
                        pass

                # Add paper node
                node_id = f"paper:{md_file.stem}"
                gs.add_node(
                    node_id=node_id,
                    kind="paper",
                    label=title,
                    metadata={
                        "path": rel_path,
                        "domain": domain,
                        "year": year,
                        "tags": tag_list,
                    },
                )
                nodes += 1

                # Add concept nodes from tags
                for tag in tag_list:
                    if tag.startswith("domain/"):
                        continue
                    concept_id = f"concept:{tag}"
                    gs.add_node(
                        node_id=concept_id,
                        kind="concept",
                        label=tag,
                        metadata={"source": "vault_tag"},
                    )
                    nodes += 1
                    # Edge: paper → concept
                    gs.add_edge(node_id, concept_id, "tagged")
                    edges += 1

                # Add wikilink edges
                for link in WIKILINK_RE.findall(content):
                    link_id = f"concept:{link.lower().replace(' ', '_')}"
                    gs.add_edge(node_id, link_id, "links_to")
                    edges += 1

                count += 1

            except Exception as exc:
                logger.warning("vault_sync: failed to sync %s: %s", md_file, exc)

        return {"nodes": nodes, "edges": edges, "count": count}

    async def _sync_doctrine_notes(self, gs) -> Dict[str, int]:
        """Sync doctrine notes from O2C-VAULT/doctrine/."""
        nodes = 0
        edges = 0
        count = 0

        if not DOCTRINE_DIR.exists():
            return {"nodes": 0, "edges": 0, "count": 0}

        for md_file in DOCTRINE_DIR.rglob("*.md"):
            try:
                # Skip meta files
                if md_file.parent.name == "meta":
                    continue

                content = md_file.read_text(encoding="utf-8")
                rel_path = str(md_file.relative_to(self.vault_root))

                title = md_file.stem.replace("_", " ")
                for line in content.split("\n"):
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

                parts = rel_path.split("/")
                domain = parts[1] if len(parts) > 1 else "general"

                node_id = f"doctrine:{md_file.stem}"
                gs.add_node(
                    node_id=node_id,
                    kind="doctrine",
                    label=title,
                    metadata={
                        "path": rel_path,
                        "domain": domain,
                        "tier": self._extract_tier(content),
                    },
                )
                nodes += 1

                # Link doctrine to domain concept
                domain_concept = f"concept:{domain}"
                gs.add_node(node_id=domain_concept, kind="concept", label=domain)
                gs.add_edge(node_id, domain_concept, "in_domain")
                edges += 1

                # Add wikilink edges
                for link in WIKILINK_RE.findall(content):
                    link_id = f"concept:{link.lower().replace(' ', '_')}"
                    gs.add_edge(node_id, link_id, "extends")
                    edges += 1

                count += 1

            except Exception as exc:
                logger.warning("vault_sync: failed to sync doctrine %s: %s", md_file, exc)

        return {"nodes": nodes, "edges": edges, "count": count}

    def _extract_tier(self, content: str) -> int:
        """Extract doctrine tier from content (tier/1, tier/2, tier/3)."""
        match = re.search(r"tier/(\d)", content)
        return int(match.group(1)) if match else 1

    def get_vault_stats(self) -> Dict[str, Any]:
        """Get statistics about vault contents."""
        stats = {
            "paper_notes": 0,
            "doctrine_notes": 0,
            "total_notes": 0,
            "domains": [],
        }

        if RESEARCH_PAPERS_DIR.exists():
            stats["paper_notes"] = len(list(RESEARCH_PAPERS_DIR.rglob("*.md")))

        if DOCTRINE_DIR.exists():
            stats["doctrine_notes"] = sum(
                1 for f in DOCTRINE_DIR.rglob("*.md") if f.parent.name != "meta"
            )

        stats["total_notes"] = stats["paper_notes"] + stats["doctrine_notes"]

        # Count domains
        if RESEARCH_PAPERS_DIR.exists():
            stats["domains"] = [
                d.name for d in RESEARCH_PAPERS_DIR.iterdir() if d.is_dir()
            ]

        return stats
