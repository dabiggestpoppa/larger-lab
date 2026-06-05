path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\scripts\group_combinatorics.py'
with open(path, 'r') as f:
    content = f.read()

# Fix remaining d[" references that should be p[1]["
content = content.replace('and d["cost_pct"] < 20', 'and p[1]["cost_pct"] < 20')

with open(path, 'w') as f:
    f.write(content)
print('Fixed remaining d references')
