"""
Tufte Renderer — Visual 3: Entropy Heatmap
Shows unstable regions, recurring failures, topology stress.
"""
import json
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def render_entropy_heatmap(entropy_data: dict) -> str:
    """Generate entropy heatmap from temporal graph data."""
    lines = []
    lines.append("=" * 70)
    lines.append("ENTROPY HEATMAP")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("=" * 70)
    lines.append("")
    
    # Heat levels
    levels = {
        "CRITICAL": ("█", 0.8, 1.0),
        "HIGH":     ("▓", 0.6, 0.8),
        "MODERATE": ("▒", 0.4, 0.6),
        "LOW":      ("░", 0.2, 0.4),
        "STABLE":   (" ", 0.0, 0.2),
    }
    
    regions = entropy_data.get("regions", {})
    if not regions:
        lines.append("No entropy data available")
        return "\n".join(lines)
    
    lines.append(f"{'Region':30} | {'Level':10} | {'Score':6} | Map")
    lines.append("-" * 70)
    
    for region, score in sorted(regions.items(), key=lambda x: x[1], reverse=True):
        for level, (char, lo, hi) in levels.items():
            if lo <= score < hi:
                bar = char * int(score * 40)
                lines.append(f"{region[:30]:30} | {level:10} | {score:.4f} | {bar}")
                break
    
    output = "\n".join(lines)
    
    out_file = OUTPUT_DIR / f"entropy_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    out_file.write_text(output, encoding="utf-8")
    
    return output

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.observability.temporal_graph import get_temporal_graph
    tg = get_temporal_graph()
    data = tg.get_entropy_profile() if hasattr(tg, 'get_entropy_profile') else {}
    result = render_entropy_heatmap(data)
    print(result)
