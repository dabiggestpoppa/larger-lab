#!/usr/bin/env python3
"""
PM V3 Phase Monitor - Watches for CC resonance module builds
Runs continuously until V3 Phase 2/3 complete
"""
import time
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
TEAM_CHAT = WORKSPACE / "shared-conversations" / "team-chat.md"
RESONANCE_DIR = WORKSPACE / "oce" / "backend" / "resonance"
CHECK_INTERVAL = 30  # seconds

def get_last_cc_entry():
    """Get the last CC entry from team chat"""
    try:
        content = TEAM_CHAT.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')
        for i, line in enumerate(reversed(lines)):
            if '[CC]' in line or '## 🔵' in line:
                idx = len(lines) - 1 - i
                entry_lines = []
                for j in range(idx, min(idx + 50, len(lines))):
                    if j > idx and lines[j].startswith('##') and '[CC]' not in lines[j] and '🔵' not in lines[j]:
                        break
                    entry_lines.append(lines[j])
                return '\n'.join(entry_lines)
        return None
    except Exception as e:
        print(f"Error reading team chat: {e}")
        return None

def check_resonance_modules():
    """Check which resonance modules exist"""
    modules = [
        'signal_packet.py',
        'field_state.py', 
        'boundary_mapper.py',
        'resonance_engine.py',
        'coherence_metrics.py',
        'pressure_tracker.py'
    ]
    existing = []
    for m in modules:
        if (RESONANCE_DIR / m).exists():
            existing.append(m)
    return existing

def main():
    print("=" * 60)
    print("PM V3 PHASE MONITOR - Starting")
    print("Watching for CC resonance module builds...")
    print("=" * 60)
    print()
    
    check_count = 0
    last_cc_entry = None
    last_modules = []
    
    while True:
        check_count += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cc_entry = get_last_cc_entry()
        modules = check_resonance_modules()
        
        # Check for new CC entry
        if cc_entry and cc_entry != last_cc_entry:
            print(f"\n[{timestamp}] NEW CC ENTRY DETECTED!")
            print("-" * 40)
            print(cc_entry[:300])
            print("-" * 40)
            last_cc_entry = cc_entry
        
        # Check for new modules
        if modules and modules != last_modules:
            new_modules = [m for m in modules if m not in last_modules]
            if new_modules:
                print(f"\n[{timestamp}] NEW MODULES DETECTED: {new_modules}")
                print("PM READY TO DEBUG!")
            last_modules = modules
        
        # Status update
        print(f"[{timestamp}] Check #{check_count} | Modules: {len(modules)}/6 | CC: {'active' if cc_entry else 'none'}")
        
        # Check for completion
        if len(modules) >= 6:
            print("\n" + "=" * 60)
            print("ALL RESONANCE MODULES BUILT - PHASE 1 COMPLETE")
            print("=" * 60)
            break
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()