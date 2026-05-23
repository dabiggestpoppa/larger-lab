"""Quick analysis of topology snapshot — fragility zones + orphan nodes."""
import json
from collections import Counter
from pathlib import Path

SNAPSHOT = Path(__file__).parent / "snapshots" / "topology_snapshot_001.json"
with open(SNAPSHOT) as f:
    data = json.load(f)

print("=== METRICS ===")
for k, v in data["metrics"].items():
    if k not in ("top_entropy_sensitive", "cycles", "orphan_list", "over_connected_list"):
        print(f"  {k}: {v}")

print("\n=== OVER-CONNECTED NODES (12) ===")
for nid in data["metrics"].get("over_connected_list", []):
    node = data["nodes"].get(nid, {})
    print(f"  {nid} | coupling={node.get('coupling_strength',0)} | type={node.get('node_type','?')}")

print("\n=== FRAGILITY ZONES BY TYPE ===")
zone_types = Counter(z.get("type","?") for z in data.get("fragility_zones", []))
for ztype, count in zone_types.most_common():
    print(f"  {ztype}: {count}")

print("\n=== SAMPLE FRAGILITY ZONES (first 15) ===")
for z in data.get("fragility_zones", [])[:15]:
    print(f"  {z.get('node','?')} | type={z.get('type','?')} | risk={z.get('risk','?')} | coupling={z.get('coupling',0)} | entropy={z.get('entropy',0)}")

print("\n=== ORPHAN ANALYSIS ===")
orphan_types = Counter(
    data["nodes"][nid].get("node_type","?") for nid in data["nodes"]
    if not data["nodes"][nid].get("dependencies") and not data["nodes"][nid].get("dependents")
)
print("Orphan count by type:")
for ntype, count in orphan_types.most_common():
    print(f"  {ntype}: {count}")

connected_types = Counter(
    data["nodes"][nid].get("node_type","?") for nid in data["nodes"]
    if data["nodes"][nid].get("dependencies") or data["nodes"][nid].get("dependents")
)
print("\nConnected count by type:")
for ntype, count in connected_types.most_common():
    print(f"  {ntype}: {count}")

# Check: are there orphan OBSERVERS specifically?
orphan_observers = [
    nid for nid in data["nodes"]
    if data["nodes"][nid].get("node_type") == "observer"
    and not data["nodes"][nid].get("dependencies")
    and not data["nodes"][nid].get("dependents")
]
print(f"\n=== OBSERVER CONNECTEDNESS ===")
print(f"Total observers: {sum(1 for n in data['nodes'].values() if n.get('node_type')=='observer')}")
print(f"Orphan observers: {len(orphan_observers)}")
print(f"Connected observers: {sum(1 for n in data['nodes'].values() if n.get('node_type')=='observer' and (n.get('dependencies') or n.get('dependents')))}")

if orphan_observers:
    print("\nOrphan observers (no connections):")
    for nid in orphan_observers[:10]:
        print(f"  {nid}")

# Check: what are the 9 edges?
print(f"\n=== EDGES (9 total) ===")
for edge in data.get("edges", []):
    print(f"  {edge['source']} --[{edge['type']}]--> {edge['target']}")
