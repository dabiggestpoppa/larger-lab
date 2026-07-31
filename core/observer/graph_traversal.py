"""Phase 2: Graph Traversal + Auto-Link Generation.

Builds a knowledge graph from vault markdown files:
- Nodes: notes (files)
- Edges: [[wikilinks]], #hashtags, and co-occurrence

Provides recursive traversal for context injection.
"""
import os
import re
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict


class KnowledgeGraph:
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}   # path -> {title, tags, links}
        self.edges: Dict[str, Set[str]] = defaultdict(set)  # path -> {linked_paths}
        self._built = False

    def build_from_vault(self, vault_path: str) -> int:
        """Parse all markdown files and build the graph. Returns node count."""
        self.nodes.clear()
        self.edges.clear()

        if not os.path.isdir(vault_path):
            return 0

        # First pass: collect all file paths and their titles
        all_files: Dict[str, str] = {}  # relpath -> title
        for root, _, files in os.walk(vault_path):
            for fn in files:
                if not fn.lower().endswith('.md'):
                    continue
                fp = os.path.join(root, fn)
                rel = os.path.relpath(fp, vault_path)
                title = os.path.splitext(fn)[0]
                try:
                    with open(fp, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                    if first_line.startswith('#'):
                        title = first_line.lstrip('#').strip()
                except Exception:
                    pass
                all_files[rel] = title
                self.nodes[rel] = {"title": title, "tags": [], "links": []}

        # Second pass: extract links and tags
        for rel, node in self.nodes.items():
            fp = os.path.join(vault_path, rel)
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    text = f.read()
            except Exception:
                continue

            # [[wikilinks]]
            wikilinks = re.findall(r'\[\[([^\]]+)\]\]', text)
            # #hashtags
            hashtags = re.findall(r'(?<!\w)#([a-zA-Z_][a-zA-Z0-9_]+)', text)

            node["tags"] = hashtags
            node["links"] = wikilinks

            # Resolve wikilinks to file paths (fuzzy match)
            for wl in wikilinks:
                wl_lower = wl.lower().replace(' ', '_')
                for candidate in all_files:
                    if wl_lower in candidate.lower() or wl_lower in all_files[candidate].lower():
                        self.edges[rel].add(candidate)

        self._built = True
        return len(self.nodes)

    def traverse(self, start_node: str, depth: int = 2) -> List[Dict[str, Any]]:
        """BFS traversal from start_node up to `depth` hops."""
        if not self._built or start_node not in self.nodes:
            return []
        visited: Set[str] = set()
        queue: List[Tuple[str, int]] = [(start_node, 0)]
        results = []
        while queue:
            current, d = queue.pop(0)
            if current in visited or d > depth:
                continue
            visited.add(current)
            node = self.nodes[current]
            results.append({
                "path": current,
                "title": node["title"],
                "depth": d,
                "tags": node["tags"],
                "links": list(self.edges.get(current, set()))
            })
            for neighbor in self.edges.get(current, set()):
                if neighbor not in visited:
                    queue.append((neighbor, d + 1))
        return results

    def auto_links(self, text: str) -> List[str]:
        """Suggest [[links]] for a piece of text based on existing node titles."""
        if not self._built:
            return []
        text_lower = text.lower()
        suggestions = []
        for path, node in self.nodes.items():
            title_lower = node["title"].lower()
            # suggest if any word from title appears in text
            title_words = set(re.findall(r'\w+', title_lower))
            text_words = set(re.findall(r'\w+', text_lower))
            if title_words & text_words and len(title_words & text_words) >= 1:
                suggestions.append(node["title"])
        return suggestions[:10]

    def summary(self) -> str:
        total_edges = sum(len(v) for v in self.edges.values())
        return f"Graph: {len(self.nodes)} nodes, {total_edges} edges"


if __name__ == "__main__":
    kg = KnowledgeGraph()
    n = kg.build_from_vault(os.path.join(os.getcwd(), "memory"))
    print(kg.summary())
    # show a few nodes
    for path, node in list(kg.nodes.items())[:5]:
        print(f"  {path}: {node['title']} — tags={node['tags']}, links={node['links']}")
