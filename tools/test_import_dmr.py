"""Test that the DMR module loads with correct thresholds"""
import sys, os
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5")

# Read the file and exec just the threshold part
with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_v2.py", 'r', encoding='utf-8') as f:
    code = f.read()

# Check if the threshold dict is in the file
if '_P90_THRESH' in code:
    print("OK: _P90_THRESH found in file")
    # Extract and eval the dict
    import re
    match = re.search(r'_P90_THRESH\s*=\s*\{([^}]+)\}', code)
    if match:
        dict_str = '{' + match.group(1) + '}'
        thresholds = eval(dict_str)
        print("Thresholds:", thresholds)
        chf = thresholds.get('CHFJPY.PRO', 'NOT FOUND')
        print("CHFJPY:", chf)
        if chf == [5.2, 8.6, 8.6, 7.2, 9.2]:
            print("CHFJPY thresholds CORRECT")
        else:
            print("CHFJPY thresholds WRONG:", chf)
else:
    print("ERROR: _P90_THRESH NOT found in file")

# Check the p90_threshold function signature
if 'def p90_threshold(est_h, symbol' in code:
    print("OK: p90_threshold has symbol parameter")
else:
    print("ERROR: p90_threshold missing symbol parameter")

# Check the call site
if 'thresh = p90_threshold(eh, symbol)' in code:
    print("OK: call site passes symbol")
else:
    print("ERROR: call site doesn't pass symbol")
