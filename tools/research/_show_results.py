"""Show the autonomous research cycle results."""
import sqlite3
from pathlib import Path

db_path = Path("data/research/papers.db")
conn = sqlite3.connect(db_path)

print("=" * 70)
print("AUTONOMOUS RESEARCH CYCLE RESULTS — PINNs × Volatility Trading")
print("=" * 70)

# Total papers
row = conn.execute("SELECT COUNT(*) FROM papers").fetchone()
print(f"\nTotal papers: {row[0]}")

# By source
for src in ["openalex", "arxiv"]:
    row = conn.execute("SELECT COUNT(*) FROM papers WHERE source=?", (src,)).fetchone()
    print(f"  {src}: {row[0]}")

# By status
for status in ["pending", "distilled", "skipped"]:
    row = conn.execute("SELECT COUNT(*) FROM papers WHERE status=?", (status,)).fetchone()
    print(f"  status={status}: {row[0]}")

# Sample papers
print("\n--- Sample Papers ---")
rows = conn.execute(
    "SELECT id, title, source, citation_count, status FROM papers ORDER BY citation_count DESC LIMIT 10"
).fetchall()
for r in rows:
    title = r[1][:70] if r[1] else "N/A"
    print(f"  [{r[3]:3d} cites] ({r[2]:8s}) {title}")

# Cross-domain papers
print("\n--- Cross-Domain Papers (PINNs + Volatility) ---")
rows = conn.execute(
    """SELECT id, title, source, citation_count FROM papers
       WHERE (abstract LIKE '%neural network%' OR abstract LIKE '%PINN%'
              OR abstract LIKE '%physics informed%')
       AND (abstract LIKE '%volatil%' OR abstract LIKE '%financ%'
            OR abstract LIKE '%market%' OR abstract LIKE '%trading%')
       LIMIT 10"""
).fetchall()
for r in rows:
    title = r[1][:70] if r[1] else "N/A"
    print(f"  [{r[3]:3d} cites] ({r[2]:8s}) {title}")

# PINNs papers
print("\n--- PINNs Papers ---")
rows = conn.execute(
    "SELECT id, title, citation_count FROM papers WHERE abstract LIKE '%physics informed%' OR abstract LIKE '%PINN%' LIMIT 5"
).fetchall()
for r in rows:
    title = r[1][:70] if r[1] else "N/A"
    print(f"  [{r[2]:3d} cites] {title}")

# Volatility papers
print("\n--- Volatility Trading Papers ---")
rows = conn.execute(
    "SELECT id, title, citation_count FROM papers WHERE abstract LIKE '%volatil%' OR abstract LIKE '%trading%' LIMIT 5"
).fetchall()
for r in rows:
    title = r[1][:70] if r[1] else "N/A"
    print(f"  [{r[2]:3d} cites] {title}")

# Vault notes
print("\n--- Vault Notes ---")
vault_papers = Path("O2C-VAULT/research/papers")
if vault_papers.exists():
    notes = list(vault_papers.rglob("*.md"))
    print(f"  Paper notes: {len(notes)}")
    for n in notes[:5]:
        print(f"    {n.relative_to(vault_papers)}")

# Graph stats
print("\n--- Knowledge Graph ---")
graph_db = Path("data/research/citations.db")
if graph_db.exists():
    gconn = sqlite3.connect(graph_db)
    nodes = gconn.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
    edges = gconn.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0]
    print(f"  Nodes: {nodes}")
    print(f"  Edges: {edges}")
    kinds = gconn.execute("SELECT kind, COUNT(*) FROM graph_nodes GROUP BY kind ORDER BY COUNT(*) DESC").fetchall()
    for k in kinds:
        print(f"    {k[0]}: {k[1]}")
    gconn.close()

# Telemetry
print("\n--- Telemetry ---")
agents_db = Path("data/research/agents.db")
if agents_db.exists():
    aconn = sqlite3.connect(agents_db)
    logs = aconn.execute("SELECT COUNT(*) FROM agent_log").fetchone()[0]
    print(f"  Agent log entries: {logs}")
    tasks = aconn.execute("SELECT COUNT(*) FROM research_tasks").fetchone()[0]
    print(f"  Research tasks: {tasks}")
    caps = aconn.execute("SELECT * FROM daily_caps ORDER BY date DESC LIMIT 1").fetchall()
    if caps:
        print(f"  Daily caps: {caps[0]}")
    aconn.close()

conn.close()
print("\n" + "=" * 70)
