with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_executor.py", "rb") as f:
    lines = f.readlines()
for i in range(93, 120):
    line = lines[i]
    has_tab = b'\t' in line
    prefix = ""
    for b in line[:20]:
        if b == 9:
            prefix += "<TAB>"
        elif b == 32:
            prefix += "<SP>"
        else:
            break
    print(f"Line {i+1}: tab={has_tab} prefix={prefix!r}")
