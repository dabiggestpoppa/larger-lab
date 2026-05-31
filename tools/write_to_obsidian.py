#!/usr/bin/env python3
"""Write the QUANTLAB_BIBLE and all OC2 knowledge notes to the Obsidian vault."""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')

from core.obsidian.vault_writer import VaultWriter
from pathlib import Path

VAULT = r'C:\Users\wifik\Downloads\O2C-VAULT'
w = VaultWriter(vault_path=VAULT)
print(f"Vault: {w.vault_path}")
print(f"Categories: {w.list_categories()}")

# Write the bible as a central note
bible_path = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\QUANTLAB_BIBLE.md')
if bible_path.exists():
    bible_content = bible_path.read_text(encoding='utf-8')
    # Parse into vault content format
    result = w.write_note(
        category='architecture',
        title='QUANTLAB_BIBLE',
        content={
            'cause': 'Central navigation hub for all quant lab knowledge',
            'result': bible_content[:2000],
            'status': 'Living document — update after every test'
        },
        tags=['bible', 'quant-lab', 'reference', 'living-doc'],
        subcategory='bible'
    )
    print(f"Bible written: {result}")

# Write ontology core
ontology_path = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\CEREBUS_ONTOLOGY.md')
if ontology_path.exists():
    ont_content = ontology_path.read_text(encoding='utf-8')
    result = w.write_note(
        category='ontology',
        title='CEREBUS_ONTOLOGY',
        content={
            'cause': 'Single source of truth for CEREBUS trading system',
            'result': ont_content[:3000],
            'status': 'Locked reference'
        },
        tags=['ontology', 'cerebus', 'locked', 'reference'],
        subcategory='cerebus'
    )
    print(f"Ontology written: {result}")

# Write strategy summary
strategy_notes = {
    'cause': 'Active strategy performance summary — what is deployed and working',
    'result': """## Symmetry Trap (Engine B — Structural/Atomic)
- 4-state FSM: SEARCH → WAIT_RETRACE → WAIT_OCC → IN_TRADE
- Entry: Impulse → DZ pullback → OCC
- SL: Zero-Buffer Extreme | TP: 1 AU
- Universal performance: 82-97% WR across 19 assets
- Top: ETHUSD 96.9% | HK50 94.0% | NZDUSD 93.3%

## P90 Kinetic (Engine A — Kinetic)
- 4 variants: INITIAL, CASCADE, STALL_HARVEST, EWS
- CASCADE dominant (85.4% WR standalone)
- Dual entries per signal: SL at 80% and 168% body

## Dual-Engine Convergence
- 94-95% WR when both engines align""",
    'status': 'Active — 2 live executors running'
}
result = w.write_note(
    category='doctrine',
    title='Active_Strategy_Summary',
    content=strategy_notes,
    tags=['strategy', 'active', 'st', 'p90', 'dual-engine'],
    subcategory=None
)
print(f"Strategy summary written: {result}")

print("\n=== DONE ===")
print(f"Notes in vault: {len(w.list_notes())}")
