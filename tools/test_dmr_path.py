import os, json
# Simulate what DMR sees
script_file = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_v2.py"
dir_path = os.path.dirname(os.path.abspath(script_file))
cfg_path = os.path.join(dir_path, 'dmr_config.json')
print(f"Script dir: {dir_path}")
print(f"Config path: {cfg_path}")
print(f"Config exists: {os.path.exists(cfg_path)}")
