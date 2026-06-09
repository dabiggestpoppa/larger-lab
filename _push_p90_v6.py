"""
Push P90 V6 Pine Script to TradingView via CDP.
Reads the .pine file and uses the MCP to set source, save, and compile.
"""
import json
import sys
import os

# Read the pine file
pine_path = r'C:\Users\wifik\Desktop\projects\larger-lab\_p90_v6_per_asset.pine'
with open(pine_path, 'r', encoding='utf-8') as f:
    source = f.read()

print(f"Pine Script: {len(source)} chars, {len(source.splitlines())} lines")
print("Ready to push to TradingView")
print(f"First 200 chars: {source[:200]}")
