text = open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py.bak', 'r', encoding='latin-1').read()

# Find the process_bar method
import re
m = re.search(r'def process_bar\(self.*?\n(?:.*?\n)*?(?=\n    def |\nclass )', text, re.DOTALL)
if m:
    with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\old_process_bar.txt', 'w', encoding='utf-8') as f:
        f.write(m.group(0))
    print("OLD process_bar: %d chars" % len(m.group(0)))
else:
    print("process_bar not found")
