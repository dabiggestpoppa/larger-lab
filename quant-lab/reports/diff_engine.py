import difflib
bak = open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py.bak', encoding='utf-8').readlines()
curr = open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py', encoding='utf-8').readlines()
diff = list(difflib.unified_diff(bak, curr, n=5, lineterm=''))
for line in diff:
    print(line.rstrip())
