# Naut Asset Config

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
"""
Patch Nautilus strategy configs to use per-asset configs from asset_configs.py.
This is loaded by run_cerebus_backtest.py before creating strategies.

Usage: from naut_asset_config import get_naut_config_for_symbol
"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab/configs')

from quant_lab.configs.asset_configs import ASSET_CONFIGS

# Nautilus default pip divisors for forefx
FOREX_PIP_DIVISOR = 10000.0
JPY_PIP_DIVISOR = 100.0

def get_pip_divisor(symbol: str, pip_value: float) -> float:
    """Convert pip_value to Nautilus pip divisor.
    
    Nautilus works in integer 'price units'. For EURUSD at 1.0500 with pip=0.0001:
      divisor = 1/0.0001 = 10000 → price_in_pips = price * 10000
    
    For BTCUSD at 105000 with pip=1.0:
      divisor = 1/1.0 = 1.0 → price_in_pips = price * 1.0 (= price itself)
    """
    if pip_value <= 0:
        return 10000.0
    return 1.0 / pip_value


def get_naut_config_for_symbol(symbol: str) -> dict:
    """Get Nautilus-compatible configuration for a symbol from asset_configs.py.
    
    Returns dict with:
      - pip_divisor: float (for converting price to pips)
      - tier_config: dict {T1/T2/T3: {ar_max, au, trigger}}
      - k_factor: float
      - pip_value: float
      - scale_factor: float (Nautilus lot_size adjustment)
    """
    cfg = ASSET_CONFIGS.get(symbol)
    if not cfg:
        # Default to EURUSD config
        cfg = ASSET_CONFIGS['EURUSD']
    
    pip_value = cfg['pip_value']
    k_factor = cfg['k_factor']
    tiers = cfg['tiers']
    
    pip_divisor = get_pip_divisor(symbol, pip_value)
    
    # Scale factor: Nautilus default lot_size=1000 works for FX (1000 units = 0.1 lot)
    # For BTCUSD (pip=1.0, price~105000), we want smaller position scaling
    # For XAUUSD (pip=0.1, price~3300), moderate scaling
    if pip_value >= 1.0:
        # Crypto/indices with large pip values — reduce effective lot size in pip calc
        scale_factor = 1.0 / pip_value
    elif pip_value >= 0.1:
        # Gold (pip=0.1)
        scale_factor = 0.1 / pip_value
    else:
        # Standard FX (pip=0.0001 or 0.01 for JPY)
        scale_factor = 0.0001 / pip_value if pip_value < 0.01 else 1.0
    
    return {
        'symbol': symbol,
        'pip_value': pip_value,
        'pip_divisor': pip_divisor,
        'k_factor': k_factor,
        'tier_config': tiers,
        'scale_factor': scale_factor,
        'sl_buffer': cfg.get('sl_buffer', {}),
        'gear_shifts': cfg.get('gear_shifts', {}),
        'p90_threshold': cfg.get('p90_threshold', 0),
        'fixed_tp': cfg.get('fixed_tp', 0),
        'class': cfg.get('class', 'Unknown'),
    }


# Quick reference for key crypto symbols
CRYPTO_CONFIGS = {
    'BTCUSD': lambda: get_naut_config_for_symbol('BTCUSD'),
    'ETHUSD': lambda: get_naut_config_for_symbol('ETHUSD'),
    'XAUUSD': lambda: get_naut_config_for_symbol('XAUUSD'),
    'XAGUSD': lambda: get_naut_config_for_symbol('XAGUSD'),
}


if __name__ == '__main__':
    # Print all crypto configs for verification
    for sym in ['BTCUSD', 'ETHUSD', 'XAUUSD', 'XAGUSD', 'EURUSD']:
        c = get_naut_config_for_symbol(sym)
        print(f"\n=== {sym} ===")
        print(f"  pip_value={c['pip_value']}, divisor={c['pip_divisor']}, k={c['k_factor']}")
        print(f"  scale_factor={c['scale_factor']}")
        print(f"  tiers: T1={c['tier_config']['T1']}")
        print(f"         T2={c['tier_config']['T2']}")
        print(f"         T3={c['tier_config']['T3']}")

```

LINKS:
[[Codemap]]
[[01 System Overview]]
[[02 Agent Workflow]]
[[03 Srra Topology]]
[[04 Data And Storage]]
[[Agents]]
[[Api Reference]]
[[Cg 1 Mermaid Specs]]
[[Cg 1 Revised]]
[[Cg 2 Mermaid Specs]]
[[Cg 2 World Model Activation]]
[[Cg 3 Openclaw Anchor]]
[[Cg 3 Relational Topology]]
[[Cg 4 Execution Intelligence]]
[[Cg 4 Mermaid Specs]]
[[Cg 5 Continuity Intelligence]]
[[Cg 6 Meta Cognition]]
[[Cg 7 Multi Scale Orchestration]]
[[Cg 8 Operator Coevolution]]
[[Cg 9 Autonomous Strategic Field]]
[[Chaos Scenarios]]
[[Chat Response Bug Diagram]]
[[Cleanup Report]]
[[Code Quality]]
[[Contributing]]
[[Debugging]]
[[Domain Micro Doctrines]]
[[Harness Engineering]]
[[Heartbeat]]
[[Identity]]
[[Master Plan 2026 05 18]]
[[Master Plan Observer Core]]
[[Master Prompt]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[Oce Unified Frontend Plan]]
[[O 6 Implementation Plan]]
[[O 7 Persistent Field Doc]]
[[Phase10]]
[[Phase Breakdown]]
[[Principles]]
[[Project Progress Clean]]
[[Quality Review]]
[[Quality Review Feedback]]
[[Readme]]
[[Soul]]
[[Sub Agent Rules]]
[[Team Tasks]]
[[Telegram Bot Setup]]
[[Testing]]
[[Test Manual]]
[[Tools]]
[[Topological Cognition Architecture]]
[[User]]
[[Workspace State]]
[[Cal]]
[[Citation Workflow]]
[[Configuration]]
[[Standard]]
[[Usage]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Memory]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
