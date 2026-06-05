"""
Line-by-line diff: CSV engine vs Nautilus strategy
Focus: state machine logic that determines trade count
"""
import sys
from pathlib import Path

# Read both files
csv_path = Path('symmetry_trap.py')
nautilus_path = Path('../strategies/symmetry_trap_strategy.py')

csv_lines = csv_path.read_text().splitlines()
nautilus_lines = nautilus_path.read_text().splitlines()

print("=" * 80)
print("CSV ENGINE: process_bar() state machine")
print("=" * 80)

# Extract CSV process_bar method
in_process_bar = False
csv_state_machine = []
for i, line in enumerate(csv_lines):
    if 'def process_bar' in line:
        in_process_bar = True
    if in_process_bar:
        csv_state_machine.append(f"{i+1:4d}: {line}")
        if line.strip() and not line.startswith(' ') and not line.startswith('\t') and 'def process_bar' not in line:
            break

# Print key sections
print("\n--- SEARCH state (impulse detection) ---")
in_search = False
for line in csv_state_machine:
    if 'STATE: SEARCH' in line:
        in_search = True
    if in_search:
        print(line)
        if 'STATE: WAIT_RETRACE' in line:
            break

print("\n--- WAIT_RETRACE state (DZ pullback) ---")
in_retrace = False
for line in csv_state_machine:
    if 'STATE: WAIT_RETRACE' in line:
        in_retrace = True
    if in_retrace:
        print(line)
        if 'STATE: WAIT_OCC' in line:
            break

print("\n--- WAIT_OCC state ---")
in_occ = False
for line in csv_state_machine:
    if 'STATE: WAIT_OCC' in line:
        in_occ = True
    if in_occ:
        print(line)
        if 'STATE: IN_TRADE' in line:
            break

print("\n--- IN_TRADE state (TP/SL) ---")
in_trade = False
for line in csv_state_machine:
    if 'STATE: IN_TRADE' in line:
        in_trade = True
    if in_trade:
        print(line)
        if 'return None' in line and in_trade:
            break

print("\n--- _reset_state_keep_loop ---")
in_reset = False
for i, line in enumerate(csv_lines):
    if '_reset_state_keep_loop' in line and 'def ' in line:
        in_reset = True
    if in_reset:
        print(f"{i+1:4d}: {line}")
        if line.strip() and not line.startswith(' ') and not line.startswith('\t') and 'def ' not in line:
            break

print("\n" + "=" * 80)
print("NAUTILUS: _process_state_machine()")
print("=" * 80)

# Extract Nautilus state machine
nautilus_state_machine = []
in_sm = False
for i, line in enumerate(nautilus_lines):
    if '_process_state_machine' in line and 'def ' in line:
        in_sm = True
    if in_sm:
        nautilus_state_machine.append(f"{i+1:4d}: {line}")
        if line.strip() and not line.startswith(' ') and not line.startswith('\t') and 'def _process_state_machine' not in line:
            break

print("\n--- SEARCH state ---")
in_search = False
for line in nautilus_state_machine:
    if 'STATE: SEARCH' in line or '_state_search' in line:
        in_search = True
    if in_search:
        print(line)
        if 'STATE: WAIT_RETRACE' in line or '_state_wait_retrace' in line:
            break

print("\n--- WAIT_RETRACE state ---")
in_retrace = False
for line in nautilus_state_machine:
    if 'STATE: WAIT_RETRACE' in line or '_state_wait_retrace' in line:
        in_retrace = True
    if in_retrace:
        print(line)
        if 'STATE: WAIT_OCC' in line or '_state_wait_occ' in line:
            break

print("\n--- WAIT_OCC state ---")
in_occ = False
for line in nautilus_state_machine:
    if 'STATE: WAIT_OCC' in line or '_state_wait_occ' in line:
        in_occ = True
    if in_occ:
        print(line)
        if 'STATE: IN_TRADE' in line or '_state_in_trade' in line:
            break

print("\n--- IN_TRADE state ---")
in_trade = False
for line in nautilus_state_machine:
    if 'STATE: IN_TRADE' in line or '_state_in_trade' in line:
        in_trade = True
    if in_trade:
        print(line)
        if 'def _' in line and '_state_in_trade' not in line:
            break

print("\n--- _reset_state_keep_loop_fixed ---")
in_reset = False
for i, line in enumerate(nautilus_lines):
    if '_reset_state_keep_loop_fixed' in line and 'def ' in line:
        in_reset = True
    if in_reset:
        print(f"{i+1:4d}: {line}")
        if line.strip() and not line.startswith(' ') and not line.startswith('\t') and 'def ' not in line:
            break

print("\n--- _advance_loop ---")
in_adv = False
for i, line in enumerate(nautilus_lines):
    if 'def _advance_loop' in line:
        in_adv = True
    if in_adv:
        print(f"{i+1:4d}: {line}")
        if line.strip() and not line.startswith(' ') and not line.startswith('\t') and 'def _advance_loop' not in line:
            break

print("\n--- _handle_kill_switch ---")
in_ks = False
for i, line in enumerate(nautilus_lines):
    if 'def _handle_kill_switch' in line:
        in_ks = True
    if in_ks:
        print(f"{i+1:4d}: {line}")
        if line.strip() and not line.startswith(' ') and not line.startswith('\t') and 'def _handle_kill_switch' not in line:
            break
