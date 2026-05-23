"""
Tufte Renderer — Visual 2: Repair Cascade Timeline
Shows perturbation, OPH activation, stabilization sequence.
"""
import json
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def render_repair_timeline(events: list) -> str:
    """Generate repair cascade timeline from event data."""
    if not events:
        return "No repair events available"
    
    lines = []
    lines.append("=" * 70)
    lines.append("REPAIR CASCADE TIMELINE")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append(f"Total events: {len(events)}")
    lines.append("=" * 70)
    lines.append("")
    
    # Sort by timestamp
    sorted_events = sorted(events, key=lambda e: e.get("timestamp", ""))
    
    # Timeline
    for i, evt in enumerate(sorted_events):
        ts = evt.get("timestamp", "?")
        etype = evt.get("event_type", "?")
        source = evt.get("source", "?")
        target = evt.get("target", "?")
        entropy = evt.get("entropy_delta", 0)
        repair = evt.get("repair_triggered", False)
        
        # Visual marker
        if repair:
            marker = "🔧"
        elif entropy > 0:
            marker = "⚡"
        elif entropy < 0:
            marker = "✓"
        else:
            marker = "○"
        
        lines.append(f"{marker} {ts[:19]} | {etype:20} | {source[:15]:15} → {target[:15]:15} | Δentropy={entropy:+.3f}")
    
    lines.append("")
    lines.append("SUMMARY:")
    repairs = sum(1 for e in events if e.get("repair_triggered"))
    perturbations = sum(1 for e in events if e.get("entropy_delta", 0) > 0)
    stabilizations = sum(1 for e in events if e.get("entropy_delta", 0) < 0)
    lines.append(f"  Perturbations: {perturbations}")
    lines.append(f"  Repair triggers: {repairs}")
    lines.append(f"  Stabilizations: {stabilizations}")
    
    output = "\n".join(lines)
    
    out_file = OUTPUT_DIR / f"repair_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    out_file.write_text(output, encoding="utf-8")
    
    return output

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.observability.event_schema import get_event_store
    es = get_event_store()
    events = es.get_all_events() if hasattr(es, 'get_all_events') else []
    result = render_repair_timeline(events)
    print(result)
