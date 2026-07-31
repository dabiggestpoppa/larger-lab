"""Phase 2: Semantic Retrieval Layer.

Provides TF-IDF based semantic search over the vault.
Production: replace with embedding-based retrieval (e.g., sentence-transformers + FAISS).
"""
import os
import re
import math
from typing import Dict, Any, List, Tuple
from collections import Counter, defaultdict


class SemanticRetrieval:
    def __init__(self):
        self._docs: Dict[str, str] = {}       # path -> text
        self._tf: Dict[str, Counter] = {}     # path -> term freq
        self._df: Counter = Counter()         # document frequency
        self._idf: Dict[str, float] = {}      # term -> idf
        self._built = False

    def index_vault(self, vault_path: str) -> int:
        """Index all markdown files in vault_path. Returns number of docs indexed."""
        self._docs.clear()
        self._tf.clear()
        self._df.clear()
        self._idf.clear()

        if not os.path.isdir(vault_path):
            return 0

        for root, _, files in os.walk(vault_path):
            for fn in files:
                if not fn.lower().endswith('.md'):
                    continue
                fp = os.path.join(root, fn)
                rel = os.path.relpath(fp, vault_path)
                try:
                    with open(fp, 'r', encoding='utf-8') as f:
                        text = f.read()
                except Exception:
                    continue
                self._docs[rel] = text
                tokens = self._tokenize(text)
                self._tf[rel] = Counter(tokens)
                for term in set(tokens):
                    self._df[term] += 1

        n = len(self._docs)
        if n > 0:
            for term, df in self._df.items():
                self._idf[term] = math.log((n + 1) / (df + 1)) + 1
        self._built = True
        return n

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-z0-9_]+", text.lower())

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """TF-IDF cosine similarity search."""
        if not self._built:
            return []
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        q_tf = Counter(q_tokens)
        q_vec = {t: q_tf[t] * self._idf.get(t, 1.0) for t in q_tf}
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0

        scores: List[Tuple[str, float]] = []
        for doc_path, tf in self._tf.items():
            dot = 0.0
            d_norm_sq = 0.0
            for t in set(q_vec) | set(tf):
                idf = self._idf.get(t, 1.0)
                d_val = tf.get(t, 0) * idf
                d_norm_sq += d_val * d_val
                if t in q_vec:
                    dot += q_vec[t] * d_val
            d_norm = math.sqrt(d_norm_sq) or 1.0
            score = dot / (q_norm * d_norm)
            if score > 0:
                scores.append((doc_path, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for path, score in scores[:top_k]:
            snippet = next(
                (line.strip() for line in self._docs[path].splitlines() if line.strip()),
                ""
            )[:120]
            results.append({"path": path, "score": round(score, 4), "snippet": snippet})
        return results


if __name__ == "__main__":
    sr = SemanticRetrieval()
    n = sr.index_vault(os.path.join(os.getcwd(), "memory"))
    print(f"Indexed {n} docs")
    results = sr.search("observer runtime continuity")
    for r in results[:5]:
        print(f"  {r['score']:.4f} {r['path']}: {r['snippet'][:80]}")
