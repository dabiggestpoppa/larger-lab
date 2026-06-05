path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\scripts\group_combinatorics.py'
with open(path, 'r') as f:
    lines = f.readlines()

# Find and fix the greedy_top3 function's internal loop
# The issue: inside the loop, `for csym, d in pairs_list` unpacks the tuple,
# but key_func and filter_func expect (csym, data) tuples.
# Fix: pass the full tuple p to key_func and filter_func.

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Fix the unpacking line to keep as tuple
    if 'for csym, d in pairs_list:' in line and i > 0 and 'greedy_top3' in ''.join(lines[max(0,i-10):i]):
        new_lines.append(line.replace('for csym, d in pairs_list:', 'for p in pairs_list:'))
        # Next line: if csym in used
        i += 1
        if i < len(lines):
            new_lines.append(lines[i].replace('if csym in used:', 'if p[0] in used:'))
            i += 1
        # Skip filter_func check for now (will handle below)
        if i < len(lines) and 'if filter_func and not filter_func(d):' in lines[i]:
            new_lines.append(lines[i].replace('if filter_func and not filter_func(d):', 'if filter_func and not filter_func(p):'))
            i += 1
        # Fix key_func(d) -> key_func(p)
        if i < len(lines) and 'score = key_func(d)' in lines[i]:
            new_lines.append(lines[i].replace('score = key_func(d)', 'score = key_func(p)'))
            i += 1
        # Fix best_next assignment
        if i < len(lines) and 'best_next = (csym, d)' in lines[i]:
            new_lines.append(lines[i].replace('best_next = (csym, d)', 'best_next = p'))
            i += 1
        continue
    new_lines.append(line)
    i += 1

with open(path, 'w') as f:
    f.writelines(new_lines)
print('Fixed internal loop')
