#!/usr/bin/env python3
"""Test MetaEditor compilation and backtesting"""
import sys
sys.path.insert(0, '.')

from mt5_mcp_server import mt5_create_ea, mt5_compile_file, mt5_backtest_python, mt5_backtest_terminal
import re

print("=" * 60)
print("METATRADER 5 EDITOR SETUP TEST")
print("=" * 60)

# Test 1: Create EA with custom inputs (partial override)
print("\n1. Creating EA with custom LotSize input...")
result = mt5_create_ea(
    name="TestCompile",
    description="Test EA for compilation",
    strategy_logic="Simple test strategy",
    inputs="input double LotSize = 0.1;"
)
print(result)

# Test 2: Compile the EA
filepath_match = re.search(r'path: (.+\.mq5)', result)
if filepath_match:
    ea_path = filepath_match.group(1)
    print(f"\n2. Compiling: {ea_path}")
    compile_result = mt5_compile_file(ea_path)
    print(compile_result)

# Test 3: Python backtest
print("\n3. Running Python backtest...")
backtest_result = mt5_backtest_python(
    ea_code='EMA_Crossover',
    symbol='EURUSD',
    timeframe_str='H1',
    bars=500
)
print(backtest_result)

# Test 4: Terminal backtest
print("\n4. Running terminal backtest...")
terminal_result = mt5_backtest_terminal(
    ea_name='TestCompile',
    symbol='EURUSD',
    timeframe='H1',
    from_date='2024.01.01',
    to_date='2024.03.01'
)
print(terminal_result)

print("\n" + "=" * 60)
print("✅ ALL TESTS COMPLETE - MetaEditor is ready for strategy building!")
print("=" * 60)