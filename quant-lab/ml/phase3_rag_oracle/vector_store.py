"""
RAG Oracle — Vector Store (ChromaDB)
=====================================
Ingests chunks into ChromaDB with metadata tags.
Supports querying by asset + session + state for fast retrieval.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings

from .chunker import Chunk, chunk_pdf_text


class RAGVectorStore:
    """ChromaDB-backed vector store for CEREBUS manual chunks."""

    def __init__(self, persist_dir: str = "quant-lab/ml/data/rag_chroma",
                 collection_name: str = "cerebus_manual"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
        )

    def ingest_chunks(self, chunks: list[Chunk]) -> int:
        """Ingest a list of chunks into ChromaDB."""
        if not chunks:
            return 0

        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{chunk.source}_p{chunk.page}_{i}"
            ids.append(chunk_id)
            documents.append(chunk.text)
            metadatas.append({
                "source": chunk.source,
                "page": chunk.page,
                "chunk_type": chunk.chunk_type,
                "asset": chunk.asset,
                "session": chunk.session,
                "state": chunk.state,
                "pattern": chunk.pattern,
                "timeframe": chunk.timeframe,
            })

        # Batch add (ChromaDB handles embedding automatically)
        batch_size = 500
        for start in range(0, len(ids), batch_size):
            end = min(start + batch_size, len(ids))
            self.collection.add(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )

        return len(chunks)

    def ingest_pdf_directory(self, pdf_dir: str) -> int:
        """Ingest all text files from a directory (extracted PDFs)."""
        pdf_path = Path(pdf_dir)
        if not pdf_path.exists():
            print(f"  WARNING: directory not found: {pdf_dir}")
            return 0

        total = 0
        for txt_file in sorted(pdf_path.glob("*.txt")):
            text = txt_file.read_text(encoding="utf-8", errors="replace")
            chunks = chunk_pdf_text(text, filename=txt_file.name)
            count = self.ingest_chunks(chunks)
            total += count
            print(f"  {txt_file.name}: {count} chunks")

        return total

    def ingest_json_knowledge(self, json_path: str) -> int:
        """Ingest structured knowledge from JSON files."""
        path = Path(json_path)
        if not path.exists():
            return 0

        data = json.loads(path.read_text())
        chunks = []

        # Handle decision trees
        if isinstance(data, dict):
            for key, value in data.items():
                text = f"{key}\n\n{json.dumps(value, indent=2)[:2000]}"
                chunk_type = "structural" if any(kw in key.lower() for kw in ["rekey", "fib", "regime", "kill"]) else "general"
                asset = "GENERAL"
                for a in ["EURUSD", "GBPUSD", "USDJPY", "OILUSD", "XAUUSD", "BTCUSD"]:
                    if a.lower() in key.lower() or a.lower() in text.lower():
                        asset = a
                        break
                chunks.append(Chunk(
                    text=text,
                    source=path.name,
                    page=0,
                    chunk_type=chunk_type,
                    asset=asset,
                ))

        return self.ingest_chunks(chunks)

    def query(self, query_text: str, n_results: int = 5,
              asset_filter: Optional[str] = None,
              chunk_type_filter: Optional[str] = None) -> list[dict]:
        """
        Query the vector store for matching manual rules.
        Optional filters for asset and chunk type.
        """
        kwargs = {
            "query_texts": [query_text],
            "n_results": n_results,
        }
        # Build where filter for ChromaDB
        where_clauses = []
        if asset_filter and asset_filter != "GENERAL":
            where_clauses.append({"asset": {"$eq": asset_filter}})
        if chunk_type_filter:
            where_clauses.append({"chunk_type": {"$eq": chunk_type_filter}})
        if where_clauses:
            if len(where_clauses) == 1:
                kwargs["where"] = where_clauses[0]
            else:
                kwargs["where"] = {"$and": where_clauses}

        results = self.collection.query(**kwargs)

        output = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                output.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                })

        return output

    def count(self) -> int:
        """Return total number of chunks in the store."""
        return self.collection.count()

    def build_index(self, pdf_dir: str, json_dir: Optional[str] = None):
        """Build the full index from PDF extracts and JSON knowledge."""
        print("\n=== Building RAG Index ===")

        # Ingest PDF text files
        if pdf_dir:
            count = self.ingest_pdf_directory(pdf_dir)
            print(f"PDF chunks ingested: {count}")

        # Ingest JSON knowledge bases
        if json_dir:
            json_path = Path(json_dir)
            if json_path.exists():
                for json_file in json_path.glob("*.json"):
                    count = self.ingest_json_knowledge(str(json_file))
                    print(f"  {json_file.name}: {count} chunks")

        print(f"Total chunks in store: {self.count()}")
