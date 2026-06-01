import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab')
sys.path.insert(0, 'quant-lab/backtests')
print('imports ok')
try:
    from run_cerebus_backtest_fixed import find_csv, run_backtest
    print('runner import ok')
    r = run_backtest('symmetry_trap', 'EURUSD')
    print('RESULT:', r)
except Exception as e:
    import traceback
    traceback.print_exc()
