"""
Tufte Renderer — Visual 1: Observer Density Map
High-density scientific operational visualization.
Shows interaction concentration, synchronization hubs, continuity pressure.
"""
import json
from pathlib import Path
from datetime import datetime

EXPORTS_DIR = Path(__file__).parent.parent / "exports" / "topology"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def render_observer_density(registry_data: dict) -> str:
    """Generate observer density map from registry data."""
    nodes = registry_data.get("nodes", {})
    edges = registry_data.get("edges", [])
    
    if not nodes:
        return "No observer data available"
    
    # Calculate density scores
    density = {}
    for nid, node in nodes.items():
        incoming = sum(1 for e in edges if e.get("target") == nid)
        outgoing = sum(1 for e in edges if e.get("source") == nid)
        density[nid] = {
            "total_interactions": incoming + outgoing,
            "incoming": incoming,
            "outgoing": outgoing,
            "type": node.get("observer_type", "unknown"),
            "state": node.get("runtime_state", "unknown"),
            "entropy": node.get("entropy_score", 0),
        }
    
    # Sort by interaction concentration
    sorted_obs = sorted(density.items(), key=lambda x: x[1]["total_interactions"], reverse=True)
    
    # Generate text-based density map (Tufte-style: high data-ink ratio)
    lines = []
    lines.append("=" * 70)
    lines.append("OBSERVER DENSITY MAP")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append(f"Total observers: {len(nodes)} | Total edges: {len(edges)}")
    lines.append("=" * 70)
    lines.append("")
    
    # Density bars
    max_interactions = max((d["total_interactions"] for d in density.values()), default=1)
    for nid, d in sorted_obs[:20]:  # Top 20
        bar_len = int((d["total_interactions"] / max_interactions) * 40) if max_interactions > 0 else 0
        bar = "█" * bar_len + "░" * (40 - bar_len)
        lines.append(f"{nid[:30]:30} |{bar}| {d['total_interactions']:3d} [{d['type']}]")
    
    lines.append("")
    lines.append("SYNCHRONIZATION HUBS (top 5 by interaction count):")
    for nid, d in sorted_obs[:5]:
        lines.append(f"  {nid}: {d['total_interactions']} interactions, entropy={d['entropy']:.3f}")
    
    lines.append("")
    lines.append("CONTINUITY PRESSURE (entropy > 0.5):")
    high_entropy = [(nid, d) for nid, d in density.items() if d.get("entropy", 0) > 0.5]
    if high_entropy:
        for nid, d in sorted(high_entropy, key=lambda x: x[1]["entropy"], reverse=True)[:10]:
            lines.append(f"  {nid}: entropy={d['entropy']:.3f}")
    else:
        lines.append("  No high-entropy observers")
    
    output = "\n".join(lines)
    
    # Save
    out_file = OUTPUT_DIR / f"observer_density_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    out_file.write_text(output, encoding="utf-8")
    
    # Also save JSON
    json_file = OUTPUT_DIR / f"observer_density_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    json_file.write_text(json.dumps({"nodes": density, "edges": len(edges)}, indent=2), encoding="utf-8")
    
    return output

if __name__ == "__main__":
    # Load from registry
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.observability.observer_registry import get_registry
    reg = get_registry()
    data = reg.get_observer_graph()
    result = render_observer_density(data)
    print(result)
