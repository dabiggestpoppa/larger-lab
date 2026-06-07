text = open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py.bak', 'r', encoding='latin-1').read()

import re

# Find initialize_session
m = re.search(r'def initialize_session\(.*?\n(?:.*?\n)*?(?=\n    def |\nclass )', text, re.DOTALL)
if m:
    with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\old_init.txt', 'w', encoding='utf-8') as f:
        f.write(m.group(0))
    print("OLD initialize_session: %d chars" % len(m.group(0)))

# Find classify_tier
m2 = re.search(r'def classify_tier\(.*?\n(?:.*?\n)*?(?=\n    def |\nclass )', text, re.DOTALL)
if m2:
    with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\old_classify.txt', 'w', encoding='utf-8') as f:
        f.write(m2.group(0))
    print("OLD classify_tier: %d chars" % len(m2.group(0)))

# Find SEARCH state
m3 = re.search(r'if self\.state == EngineState\.SEARCH:.*?(?=\n        # ---\n        elif self\.state)', text, re.DOTALL)
if m3:
    with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\old_search.txt', 'w', encoding='utf-8') as f:
        f.write(m3.group(0))
    print("OLD SEARCH state: %d chars" % len(m3.group(0)))

# Find WAIT_RETRACE state
m4 = re.search(r'elif self\.state == EngineState\.WAIT_RETRACE:.*?(?=\n        # ---\n        elif self\.state)', text, re.DOTALL)
if m4:
    with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\old_wait_retrace.txt', 'w', encoding='utf-8') as f:
        f.write(m4.group(0))
    print("OLD WAIT_RETRACE: %d chars" % len(m4.group(0)))

# Find WAIT_OCC state
m5 = re.search(r'elif self\.state == EngineState\.WAIT_OCC:.*?(?=\n        # ---\n        elif self\.state)', text, re.DOTALL)
if m5:
    with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\old_wait_occ.txt', 'w', encoding='utf-8') as f:
        f.write(m5.group(0))
    print("OLD WAIT_OCC: %d chars" % len(m5.group(0)))
