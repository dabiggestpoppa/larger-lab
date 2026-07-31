"""Compare process_bar between .bak and current — find logic differences"""
import re

bak = open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py.bak', 'r', encoding='latin-1').read()
curr = open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py', 'r', encoding='utf-8').read()

# They should be identical since git checkout restored from same commit
# But let me check if the .bak was modified after the git checkout

# Check file sizes
import os
bak_size = os.path.getsize(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py.bak')
curr_size = os.path.getsize(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py')
print('BAK size: %d' % bak_size)
print('CUR size: %d' % curr_size)
print('Same size: %s' % (bak_size == curr_size))

# Check if they're byte-identical
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py.bak', 'rb') as f:
    bak_bytes = f.read()
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py', 'rb') as f:
    curr_bytes = f.read()

# Normalize encoding differences
bak_str = bak_bytes.decode('latin-1')
curr_str = curr_bytes.decode('utf-8')

# Compare line by line
bak_lines = bak_str.split('\n')
curr_lines = curr_str.split('\n')

print('BAK lines: %d' % len(bak_lines))
print('CUR lines: %d' % len(curr_lines))

diffs = []
for i, (b, c) in enumerate(zip(bak_lines, curr_lines)):
    if b != c:
        diffs.append((i+1, b[:100], c[:100]))

print('Differences: %d' % len(diffs))
for line_num, b, c in diffs[:20]:
    print('  Line %d:' % line_num)
    print('    BAK: %s' % b)
    print('    CUR: %s' % c)
