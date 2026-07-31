"""Fix all None-unsafe f-string format specifiers in p90_engine.py"""
path = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\p90_engine.py"

with open(path, "r") as f:
    content = f.read()

# Only fix the ones where the variable could be None
mappings = [
    (
        'f"TP2 HIT (-50% AR): exit={self.tp2_price:.5f}"',
        '"TP2 HIT (-50% AR): exit={}".format(self.tp2_price if self.tp2_price is not None else "N/A")'
    ),
    (
        'f"TP1 HIT (-25% AR): exit={self.tp1_price:.5f}"',
        '"TP1 HIT (-25% AR): exit={}".format(self.tp1_price if self.tp1_price is not None else "N/A")'
    ),
    (
        'f"SL HIT: exit={self.sl_price:.5f}"',
        '"SL HIT: exit={}".format(self.sl_price if self.sl_price is not None else "N/A")'
    ),
]

fixes = 0
for old, new in mappings:
    count = content.count(old)
    if count:
        content = content.replace(old, new)
        fixes += count
        print(f"  Replaced {count}x: {old[:70]}")
    else:
        print(f"  Not found: {old[:70]}")

with open(path, "w") as f:
    f.write(content)

print(f"\nFixed {fixes} occurrences total")

import ast
with open(path) as f:
    ast.parse(f.read())
print("Syntax OK")
