"""Debug ChromaDB query issue."""
import tempfile, shutil
from pathlib import Path
import chromadb
from chromadb.config import Settings

temp_dir = tempfile.mkdtemp()
print(f"Temp dir: {temp_dir}")

client = chromadb.PersistentClient(path=temp_dir)
col = client.get_or_create_collection("test")

# Add some test documents with metadata
col.add(
    ids=["doc1", "doc2", "doc3"],
    documents=[
        "Wednesday PM bifurcation rules",
        "132% kill switch invalidation",
        "EURUSD Monday London Range"
    ],
    metadatas=[
        {"chunk_type": "temporal", "asset": "GENERAL"},
        {"chunk_type": "structural", "asset": "GENERAL"},
        {"chunk_type": "asset", "asset": "EURUSD"},
    ]
)

print(f"Count: {col.count()}")

# Query without filter
print("\n--- Query without filter ---")
r = col.query(query_texts=["Wednesday PM"], n_results=3)
for i, doc in enumerate(r["documents"][0]):
    print(f"  {i+1}. {doc[:50]}... | meta: {r['metadatas'][0][i]}")

# Query with $eq filter
print("\n--- Query with $eq filter (asset=EURUSD) ---")
r = col.query(query_texts=["Monday London"], n_results=3, where={"asset": {"$eq": "EURUSD"}})
print(f"  Results: {len(r['documents'][0])}")
for i, doc in enumerate(r["documents"][0]):
    print(f"  {i+1}. {doc[:50]}... | meta: {r['metadatas'][0][i]}")

# Query with simple equality (newer ChromaDB syntax)
print("\n--- Query with simple equality (asset=EURUSD) ---")
r = col.query(query_texts=["Monday London"], n_results=3, where={"asset": "EURUSD"})
print(f"  Results: {len(r['documents'][0])}")
for i, doc in enumerate(r["documents"][0]):
    print(f"  {i+1}. {doc[:50]}... | meta: {r['metadatas'][0][i]}")

# Query with $and
print("\n--- Query with $and filter ---")
r = col.query(query_texts=["Monday London"], n_results=3, where={"$and": [{"asset": {"$eq": "EURUSD"}}]})
print(f"  Results: {len(r['documents'][0])}")
for i, doc in enumerate(r["documents"][0]):
    print(f"  {i+1}. {doc[:50]}... | meta: {r['metadatas'][0][i]}")

# Peek at raw data
print("\n--- Raw data ---")
peek = col.peek(3)
for i, doc in enumerate(peek["documents"]):
    print(f"  {i+1}. {doc[:50]}... | meta: {peek['metadatas'][i]}")

shutil.rmtree(temp_dir, ignore_errors=True)
