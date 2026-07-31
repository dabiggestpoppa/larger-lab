"""Check what's in the .bak file vs current"""
import re

# Read .bak file
bak = open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py.bak', 'r', encoding='latin-1').read()
curr = open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py', 'r', encoding='utf-8').read()

# Find classify_tier in both
for label, text in [('BAK', bak), ('CURRENT', curr)]:
    m = re.search(r'def classify_tier\([^)]*\).*?(?=\n    def |\nclass )', text, re.DOTALL)
    if m:
        print('=== %s classify_tier ===' % label)
        print(m.group(0)[:600])
        print()

# Find initialize_session in both
for label, text in [('BAK', bak), ('CURRENT', curr)]:
    m = re.search(r'def initialize_session\([^)]*\).*?(?=\n    def |\nclass )', text, re.DOTALL)
    if m:
        print('=== %s initialize_session ===' % label)
        print(m.group(0)[:600])
        print()

# Find DEFAULT_TIER_CONFIG in both
for label, text in [('BAK', bak), ('CURRENT', curr)]:
    m = re.search(r'DEFAULT_TIER_CONFIG\s*=\s*\{[^}]+\}', text, re.DOTALL)
    if m:
        print('=== %s DEFAULT_TIER_CONFIG ===' % label)
        print(m.group(0)[:300])
        print()
