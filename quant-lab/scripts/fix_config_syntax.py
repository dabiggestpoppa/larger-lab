"""Fix the corrupted asset_configs.py by removing orphaned blocks left by regex replacement."""
from pathlib import Path

CFG_FILE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs\asset_configs.py")

with open(CFG_FILE) as f:
    lines = f.readlines()

# Find and remove orphaned blocks: lines that start with "gear_shifts" or "p90_threshold" or "fixed_tp"
# that appear right after a closing "},"
# Pattern: after a line with just "}," the next non-empty line should NOT be "gear_shifts" etc.
# Those are orphaned from the old config that wasn't fully replaced.

new_lines = []
i = 0
removed = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    
    # Check if this line is an orphaned block
    # An orphaned block starts with one of these after a closing }, at wrong indent level
    is_orphan = False
    if stripped.startswith('"gear_shifts"') or stripped.startswith('"p90_threshold"') or stripped.startswith('"fixed_tp"'):
        # Check if previous non-empty line ends with },
        j = i - 1
        while j >= 0 and lines[j].strip() == '':
            j -= 1
        if j >= 0 and lines[j].strip().endswith('},'):
            # This is orphaned — skip it and its continuation lines
            is_orphan = True
            # Skip until we hit the next } or end of block
            indent = len(line) - len(line.lstrip())
            new_lines.append(line)  # Keep the line but we'll deduplicate
            i += 1
            # Skip continuation lines of this orphaned block
            while i < len(lines):
                next_stripped = lines[i].strip()
                if next_stripped == '' or next_stripped.startswith('#'):
                    i += 1
                    continue
                next_indent = len(lines[i]) - len(lines[i].lstrip())
                if next_indent <= indent and (next_stripped.startswith('},') or next_stripped.startswith('"')):
                    break
                i += 1
            removed += 1
            continue
    
    if not is_orphan:
        new_lines.append(line)
    i += 1

print(f"Processed {len(lines)} lines, removed {removed} orphaned blocks")

# Write fixed config
with open(CFG_FILE, 'w') as f:
    f.writelines(new_lines)

print(f"Wrote {len(new_lines)} lines to {CFG_FILE}")
