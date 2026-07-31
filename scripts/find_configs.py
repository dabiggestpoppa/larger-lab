"""Find the optimized engine config from sweep scripts."""
import os, re

scripts_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\scripts'
for fname in sorted(os.listdir(scripts_dir)):
    if 'sweep' in fname.lower() or 'trigger' in fname.lower():
        fpath = os.path.join(scripts_dir, fname)
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        # Look for ar_max values
        ar_vals = re.findall(r'ar_max[\":\s]+(\d+)', content)
        trigger_vals = re.findall(r'trigger[\":\s]+([\d.]+)', content)
        if ar_vals or trigger_vals:
            print(f'{fname}:')
            print(f'  ar_max values: {ar_vals[:8]}')
            print(f'  trigger values: {trigger_vals[:8]}')
            print()
