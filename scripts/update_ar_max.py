"""Update all asset configs to use optimized ar_max=60 for all tiers."""
import re

fpath = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs\asset_configs.py'
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all ar_max values with 60.0
# Pattern: "ar_max": <number> -> "ar_max": 60.0
updated = re.sub(r'"ar_max":\s*[\d.]+', '"ar_max": 60.0', content)

with open(fpath, 'w', encoding='utf-8') as f:
    f.write(updated)

# Count replacements
count = len(re.findall(r'"ar_max":\s*[\d.]+', content))
print(f'Updated {count} ar_max values to 60.0')

# Verify
with open(fpath, 'r', encoding='utf-8') as f:
    new_content = f.read()
remaining = re.findall(r'"ar_max":\s*([\d.]+)', new_content)
unique_vals = set(remaining)
print(f'Unique ar_max values after update: {unique_vals}')
