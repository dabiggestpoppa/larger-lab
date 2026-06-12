"""
Phase 1.3.2 — Embedding Engine

Converts text chunks to vector representations.
Supports multiple backends:
- OpenAI text-embedding-3-small/large
- Local models (sentence-transformers)
- Custom models
"""

from typing import Optional
import os


class EmbeddingEngine:
    """
    Embedding engine with pluggable backends.
    
    Default: OpenAI text-embedding-3-small (1536 dims)
    Fallback: sentence-transformers all-MiniLM-L6-v2 (384 dims)
    """
    
    def __init__(
        self,
        backend: str = "openai",
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        dim: int = 1536,
    ):
        self.backend = backend
        self.model = model
        self.dim = dim
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._client = None
    
    def embed(self, text: str) -> list[float]:
        """Embed a single text string."""
        if self.backend == "openai":
            return self._embed_openai(text)
        elif self.backend == "local":
            return self._embed_local(text)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
    
    def embed_batch(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        """Embed a batch of texts."""
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            if self.backend == "openai":
                results.extend(self._embed_openai_batch(batch))
            elif self.backend == "local":
                results.extend(self._embed_local_batch(batch))
        return results
    
    def _embed_openai(self, text: str) -> list[float]:
        """Embed using OpenAI API."""
        try:
            from openai import OpenAI
            if self._client is None:
                self._client = OpenAI(api_key=self.api_key)
            response = self._client.embeddings.create(
                input=text,
                model=self.model,
            )
            return response.data[0].embedding
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")
    
    def _embed_openai_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embed using OpenAI API."""
        try:
            from openai import OpenAI
            if self._client is None:
                self._client = OpenAI(api_key=self.api_key)
            response = self._client.embeddings.create(
                input=texts,
                model=self.model,
            )
            return [item.embedding for item in response.data]
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")
    
    def _embed_local(self, text: str) -> list[float]:
        """Embed using local sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer
            if self._client is None:
                self._client = SentenceTransformer("all-MiniLM-L6-v2")
            return self._client.encode(text).tolist()
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
    
    def _embed_local_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embed using local model."""
        try:
            from sentence_transformers import SentenceTransformer
            if self._client is None:
                self._client = SentenceTransformer("all-MiniLM-L6-v2")
            return self._client.encode(texts).tolist()
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
