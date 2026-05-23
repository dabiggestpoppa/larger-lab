"""
Tufte Renderer — Visual 4: Temporal Continuity Ribbon
Shows continuity persistence through time, observer drift, sync coherence.
"""
import json
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def render_continuity_ribbon(continuity_data: list) -> str:
    """Generate temporal continuity ribbon visualization."""
    if not continuity_data:
        return "No continuity data available"
    
    lines = []
    lines.append("=" * 70)
    lines.append("TEMPORAL CONTINUITY RIBBON")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append(f"Data points: {len(continuity_data)}")
    lines.append("=" * 70)
    lines.append("")
    
    # Ribbon characters for continuity levels
    ribbon_chars = {
        "high":   "█",   # Strong continuity
        "medium": "▓",   # Moderate
        "low":    "▒",   # Weak
        "broken": "░",   # Disrupted
    }
    
    lines.append("Continuity over time (each char = time slice):")
    lines.append("")
    
    ribbon = ""
    for point in continuity_data:
        score = point.get("continuity_score", 0)
        if score >= 0.8:
            ribbon += ribbon_chars["high"]
        elif score >= 0.5:
            ribbon += ribbon_chars["medium"]
        elif score >= 0.2:
            ribbon += ribbon_chars["low"]
        else:
            ribbon += ribbon_chars["broken"]
    
    # Print ribbon in chunks
    chunk_size = 60
    for i in range(0, len(ribbon), chunk_size):
        lines.append(f"  {ribbon[i:i+chunk_size]}")
    
    lines.append("")
    lines.append("LEGEND: █=strong ▓=moderate ▒=weak ░=broken")
    
    # Summary
    high = sum(1 for c in continuity_data if c.get("continuity_score", 0) >= 0.8)
    med = sum(1 for c in continuity_data if 0.5 <= c.get("continuity_score", 0) < 0.8)
    low = sum(1 for c in continuity_data if 0.2 <= c.get("continuity_score", 0) < 0.5)
    broken = sum(1 for c in continuity_data if c.get("continuity_score", 0) < 0.2)
    
    lines.append("")
    lines.append(f"Strong:   {high:4d} ({100*high/len(continuity_data):.1f}%)")
    lines.append(f"Moderate: {med:4d} ({100*med/len(continuity_data):.1f}%)")
    lines.append(f"Weak:     {low:4d} ({100*low/len(continuity_data):.1f}%)")
    lines.append(f"Broken:   {broken:4d} ({100*broken/len(continuity_data):.1f}%)")
    
    output = "\n".join(lines)
    
    out_file = OUTPUT_DIR / f"continuity_ribbon_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    out_file.write_text(output, encoding="utf-8")
    
    return output

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.observability.temporal_graph import get_temporal_graph
    tg = get_temporal_graph()
    data = tg.get_continuity_series() if hasattr(tg, 'get_continuity_series') else []
    result = render_continuity_ribbon(data)
    print(result)
