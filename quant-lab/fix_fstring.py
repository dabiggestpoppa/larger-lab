"""Fix f-string format specifier bugs in p90_engine.py"""
path = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\p90_engine.py"

with open(path, "r") as f:
    content = f.read()

# The bug: f'{tp1:.5f if tp1 else "N/A"}' -- can't use :.5f with inline if on None
# Fix: use separate f-string that handles None before formatting
old_line_a = '                    f"SL={sl:.5f}, TP1={tp1:.5f if tp1 is not None else \'N/A\'}, "\n                    f"TP2={tp2:.5f if tp2 is not None else \'N/A\'}"'
new_line_a = '                    f"SL={sl:.5f}, TP1={(f\'{tp1:.5f}\' if tp1 is not None else \'N/A\')}, "\n                    f"TP2={(f\'{tp2:.5f}\' if tp2 is not None else \'N/A\')}"'

if old_line_a in content:
    content = content.replace(old_line_a, new_line_a)
    print("Fixed TP1/TP2 f-string")
else:
    # Try the original bad pattern
    old_orig = "TP1={tp1:.5f if tp1 else 'N/A'}"
    if old_orig in content:
        content = content.replace(old_orig, "TP1={(f'{tp1:.5f}' if tp1 is not None else 'N/A')}")
        content = content.replace("TP2={tp2:.5f if tp2 else 'N/A'}", "TP2={(f'{tp2:.5f}' if tp2 is not None else 'N/A')}")
        print("Fixed original bad f-string")
    else:
        print("Pattern not found, checking...")
        for i, line in enumerate(content.split("\n"), 1):
            if "TP1" in line and "f'" in line or "TP1" in line and 'f"' in line:
                print(f"  Line {i}: {line.rstrip()}")

with open(path, "w") as f:
    f.write(content)

# Verify syntax
import ast
with open(path) as f:
    ast.parse(f.read())
print("Syntax OK")
