import json, os

reports = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

# Check the cost sweep files which have per-pair configs
# Also check sweep_matrix_v2 for the full data
with open(os.path.join(reports, 'SWEEP_MATRIX_V2.md')) as f:
    content = f.read()

# Find our pairs
target_pairs = ['EURJPY', 'EURNZD', 'GBPNZD', 'EURAUD', 'GBPAUD', 'GBPCAD']

for pair in target_pairs:
    # Find the line with this pair
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if pair in line and ('FLOOR' in line or 'floor' in line.lower()):
            # Print surrounding context
            start = max(0, i-1)
            end = min(len(lines), i+3)
            for j in range(start, end):
                print(f'  {lines[j]}')
            print()
            break
    else:
        # Just find any mention
        for i, line in enumerate(lines):
            if pair in line:
                print(f'{pair} line {i}: {line[:120]}')
                break
