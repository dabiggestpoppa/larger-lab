"""
DMR MT5 Strategy Tester Automation
Writes tester config, launches Strategy Tester via terminal CLI, parses results.
"""
import sys, os, time, subprocess, glob, json
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# ── Paths ──────────────────────────────────────────────────────────
MT5_DIR     = r"C:\Program Files\Ox Securities MetaTrader 5"
TERMINAL    = os.path.join(MT5_DIR, "terminal64.exe")
EXPERTS_DIR = r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\MQL5\Experts"
PROFILES_DIR = r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\MQL5\Profiles\Tester"
LOGS_DIR     = r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\Tester\logs"
WORKSPACE    = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5"

EA_NAME      = "DMR_FULL_BACKTEST"
SYMBOL       = "EURUSD.PRO"
PERIOD       = "M5"
TIMEFRAME    = 5  # MQL PERIOD_M5

# ── Test Configuration ─────────────────────────────────────────────
# Format: (label, from_date, to_date)
TESTS = [
    ("1M_Jan2024",  "2024.01.01", "2024.01.31"),
    ("1M_Feb2024",  "2024.02.01", "2024.02.29"),
    ("1M_Mar2024",  "2024.03.01", "2024.03.31"),
    ("1M_Apr2024",  "2024.04.01", "2024.04.30"),
    ("1M_May2024",  "2024.05.01", "2024.05.31"),
    ("1M_Jun2024",  "2024.06.01", "2024.06.30"),
    ("3M_Q1Q2_2024","2024.01.01", "2024.06.30"),
    ("1Y_2024",     "2024.01.01", "2024.12.31"),
]

# ── Write .ini config file ─────────────────────────────────────────
def write_ini(label, from_date, to_date):
    ini_name = f"{EA_NAME}.{SYMBOL}.{PERIOD}.{from_date.replace('.','')}_{to_date.replace('.','')}.000.ini"
    ini_path = os.path.join(PROFILES_DIR, ini_name)
    
    content = f""";Expert Advisor single test: {EA_NAME}, {SYMBOL} {PERIOD}, every tick, {from_date} - {to_date}
[Tester]
Expert={EA_NAME}.ex5
Symbol={SYMBOL}
Period={PERIOD}
Optimization=0
Model=0
FromDate={from_date}
ToDate={to_date}
ForwardMode=0
Deposit=10000
Currency=USD
ProfitInPips=0
Leverage=100
ExecutionMode=0
OptimizationCriterion=0
Visual=0
[TesterInputs]
LotSize=0.01||0.01||0.001000||0.100000||N
MagicNumber=20260528||20260528||1||202605280||N
MaxDailyTrades=1||1||1||10||N
HardExitHour=17||17||1||170||N
DeepMult=2.00||2.00||0.100000||5.000000||N
KillMult=2.20||2.20||0.100000||5.000000||N
MaxAR=45||45||1||450||N
MinAR=3||3||1||45||N
ESTOffset=-5||-5||-12||12||N
EnableLogging=true||false||0||true||N
"""
    with open(ini_path, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    print(f"  Config: {ini_name}")
    return ini_name

# ── Write .set file (EA parameters) ────────────────────────────────
def write_set():
    set_path = os.path.join(PROFILES_DIR, f"{EA_NAME}.set")
    content = """LotSize=0.01||0.01||0.001000||0.100000||N
MagicNumber=20260528||20260528||1||202605280||N
MaxDailyTrades=1||1||1||10||N
HardExitHour=17||17||1||170||N
DeepMult=2.00||2.00||0.100000||5.000000||N
KillMult=2.20||2.20||0.100000||5.000000||N
MaxAR=45||45||1||450||N
MinAR=3||3||1||45||N
ESTOffset=-5||-5||-12||12||N
EnableLogging=true||false||0||true||N
"""
    with open(set_path, 'w') as f:
        f.write(content)

# ── Launch backtest via terminal CLI ───────────────────────────────
def run_test(ini_name):
    """Launch MT5 terminal with /test flag for Strategy Tester"""
    # MT5 terminal supports: terminal64.exe /test:<ini_file>
    ini_path = os.path.join(PROFILES_DIR, ini_name)
    
    # Kill any existing tester instance first
    subprocess.run(['taskkill', '/IM', 'terminal64.exe', '/F'], 
                   capture_output=True, text=True)
    time.sleep(3)
    
    print(f"  Launching backtest: {ini_name}")
    proc = subprocess.Popen(
        [TERMINAL, f"/test:{ini_path}"],
        cwd=MT5_DIR
    )
    print(f"  Terminal PID: {proc.pid}")
    return proc

# ── Parse backtest results ─────────────────────────────────────────
def parse_results_xml(label):
    """Parse the Strategy Tester XML report"""
    # MT5 writes results to Tester/logs or creates .htm report
    # Look for the most recent report
    patterns = [
        os.path.join(LOGS_DIR, "*.htm"),
        os.path.join(LOGS_DIR, "*.xml"),
        os.path.join(WORKSPACE, "reports", "*.htm"),
    ]
    
    results = {}
    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            latest = max(files, key=os.path.getmtime)
            results['report_file'] = latest
            results['mtime'] = os.path.getmtime(latest)
            break
    
    return results

def parse_log_results(label):
    """Parse the tester log for results summary"""
    log_files = glob.glob(os.path.join(LOGS_DIR, "*.log"))
    if not log_files:
        return None
    
    latest_log = max(log_files, key=os.path.getmtime)
    
    try:
        with open(latest_log, 'r', errors='replace') as f:
            lines = f.readlines()
        
        results = {}
        for line in lines[-100:]:  # Last 100 lines
            line = line.strip()
            if 'Testing pass' in line or 'Testing complete' in line:
                results['status'] = 'complete'
            if 'total' in line.lower() and 'deal' in line.lower():
                results['deals'] = line
            if 'profit' in line.lower() and 'gross' not in line.lower():
                results['profit_line'] = line
        
        results['log_file'] = latest_log
        return results
    except Exception as e:
        return {'error': str(e)}

def parse_tester_log_for_stats():
    """Parse the most recent tester log for key statistics"""
    log_files = glob.glob(os.path.join(LOGS_DIR, "Serial*"))
    if not log_files:
        # Try all log files
        log_files = glob.glob(os.path.join(LOGS_DIR, "*"))
        log_files = [f for f in log_files if os.path.isfile(f)]
    
    if not log_files:
        return None
    
    latest = max(log_files, key=os.path.getmtime)
    
    try:
        with open(latest, 'r', errors='replace') as f:
            content = f.read()
        
        stats = {}
        lines = content.split('\n')
        
        # Look for summary lines at end of log
        for line in reversed(lines[-200:]):
            line = line.strip()
            if not line:
                continue
            lower = line.lower()
            if 'total trades' in lower or ' trades' in lower:
                stats['trades'] = line
            elif 'profit' in lower and ('total' in lower or 'net' in lower):
                stats['profit'] = line
            elif 'winning' in lower or 'win rate' in lower or '%' in line:
                stats['winrate'] = line
            elif 'drawdown' in lower and ('max' in lower or '%' in lower):
                stats['drawdown'] = line
            elif 'profit factor' in lower or ' Sharpe' in lower:
                stats['pf_sharpe'] = line
        
        return stats
    except Exception as e:
        return {'error': str(e)}

# ── Main ───────────────────────────────────────────────────────────
def main():
    overall_start = datetime.now()
    
    print("="*60)
    print(f"DMT MT5 BACKTEST PIPELINE")
    print(f"EA:     {EA_NAME}")
    print(f"Symbol: {SYMBOL}")
    print(f"Period: {PERIOD}")
    print(f"Model:  Every tick (real ticks)")
    print(f"Tests:  {len(TESTS)} configurations")
    print(f"Started: {overall_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Verify EA is compiled
    ex5_path = os.path.join(EXPERTS_DIR, f"{EA_NAME}.ex5")
    if not os.path.exists(ex5_path):
        print(f"\nERROR: {EA_NAME}.ex5 not found in Experts folder!")
        print("Compile the .mq5 first in MetaEditor.")
        sys.exit(1)
    print(f"\nEA found: {ex5_path} ({os.path.getsize(ex5_path)} bytes)")
    
    # Write .set file
    write_set()
    print("Set file updated.")
    
    # Run single quick test for now (full suite can take hours)
    print(f"\n{'─'*60}")
    print("Running quick validation test (1M Jan 2024)...")
    print(f"{'─'*60}")
    
    label, from_d, to_d = TESTS[0]
    ini_name = write_ini(label, from_d, to_d)
    write_set()
    
    # Check if terminal is already running and kill it
    r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal64.exe'], 
                       capture_output=True, text=True)
    
    if 'terminal64' in r.stdout:
        print("\nMT5 already running. Closing for clean start...")
        subprocess.run(['taskkill', '/IM', 'terminal64.exe', '/F'], 
                       capture_output=True)
        time.sleep(3)
    
    print(f"\nLaunching Strategy Tester...")
    print(f"  Config: {ini_name}")
    print(f"  Date range: {from_d} → {to_d}")
    
    proc = run_test(ini_name)
    
    print(f"\nStrategy Tester launched.")
    print("Waiting for test completion...")
    print("(MT5 must have enough historical data for the date range)")
    print("\nNOTE: This will take several minutes for 1M M5 every-tick.")
    print("Monitor progress in the MT5 Strategy Tester window.")
    
    # Wait and monitor
    report_line = f"Reporter={EA_NAME}.{SYMBOL}.{PERIOD}.{from_d.replace('.','')}_{to_d.replace('.','')}.000.htm"
    report_path = os.path.join(LOGS_DIR, os.path.basename(report_line.replace('Reporter=', '')))
    
    max_wait = 600  # 10 minutes max
    check_interval = 15
    elapsed = 0
    
    while elapsed < max_wait:
        time.sleep(check_interval)
        elapsed += check_interval
        
        # Check if terminal still running
        r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal64.exe'],
                           capture_output=True, text=True)
        
        if 'terminal64' not in r.stdout:
            print(f"\nMT5 terminal closed after {elapsed}s. Test likely complete.")
            break
        
        print(f"  [{elapsed}s] Still running...")
    
    # Parse results
    print(f"\n{'─'*60}")
    print("Parsing results...")
    print(f"{'─'*60}")
    
    stats = parse_tester_log_for_stats()
    if stats:
        print("\nTest Results:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    else:
        print("Could not parse tester log. Check MT5 Strategy Tester for results.")
    
    # Check for HTML report
    htm_files = glob.glob(os.path.join(LOGS_DIR, "*.htm"))
    xml_files = glob.glob(os.path.join(LOGS_DIR, "*.xml"))
    
    if htm_files:
        latest_htm = max(htm_files, key=os.path.getmtime)
        print(f"\nHTML Report: {latest_htm}")
        # Copy to workspace
        import shutil
        dst = os.path.join(WORKSPACE, "reports")
        os.makedirs(dst, exist_ok=True)
        shutil.copy2(latest_htm, os.path.join(dst, os.path.basename(latest_htm)))
        print(f"  Copied to: {dst}")
    
    elapsed_total = datetime.now() - overall_start
    print(f"\nTotal pipeline time: {elapsed_total}")
    print("Backtest complete.")

if __name__ == '__main__':
    main()
