#!/usr/bin/env python3
"""Simple test script"""
import sys
import os

# Write to file
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results\simple_output.txt', 'w') as f:
    f.write("Starting test...\n")
    f.write(f"Python version: {sys.version}\n")
    f.write(f"Working directory: {os.getcwd()}\n")
    
    # Test data loading
    try:
        sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
        from pathlib import Path
        from nautilus.data_loader import _parse_csv
        
        filepath = Path(r'C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv')
        f.write(f"File exists: {filepath.exists()}\n")
        
        if filepath.exists():
            df = _parse_csv(filepath)
            f.write(f"Loaded {len(df)} rows\n")
            f.write(f"Columns: {list(df.columns)}\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
        import traceback
        f.write(traceback.format_exc())
    
    f.write("Test complete!\n")

print("Done - check results/simple_output.txt")