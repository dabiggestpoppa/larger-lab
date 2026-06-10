"""
Phase 3: RAG Oracle — Retrieval-Augmented Generation for CEREBUS
===================================================================
Ingests 55 PDFs + v4 Manual into a Vector Database (ChromaDB).
Smart chunking by CEREBUS Decision Nodes (not naive 500-word blocks).
Query engine retrieves matching manual rules for live market states.

Components:
- chunker.py — Smart chunking by decision nodes (Temporal/Structural/Asset)
- vector_store.py — ChromaDB ingestion + query
- query_engine.py — Live state → manual rule retrieval
- rag_api.py — FastAPI endpoints
"""
