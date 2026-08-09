"""
CEREBUS FX v4.0 -- Strategy Registry & Magic Number Allocation
================================================================

Central registry of ALL active strategies on a single demo/live account.

CRITICAL: Every strategy MUST register its magic number here. NO hardcoding
across multiple files. At startup, verify uniqueness across all entries.

Usage from other engines:
    from configs.strategy_registry import STRATEGY_REGISTRY, verify_unique_magnetics

DEPLOYED ON SAME ACCOUNT AS SYMMETRY TRAP (magic=20260531)
"""

from typing import Dict

STRATEGY_REGISTRY: Dict[str, dict] = {
    "SYMMETRY_TRAP": {
        "magic": 20260531,
        "description": "Symmetry Trap - Directional breakout/reversion",
        "symbols_overlap_with_triangular": False,
    },
    "TRIANGULAR_BASIS_GBP_AUD_NZD": {
        "magic": 31082026,
        "description": "Triangular Basis Mean Reversion - Market-neutral statistical arbitrage",
        "symbols_overlap_with_triangular": True,
        "leg_symbols": ["GBPAUD", "GBPNZD", "AUDNZD"],
    },
}


def verify_unique_magnetics(registry: dict = None) -> bool:
    """Assert that all registered strategies have unique magic numbers."""
    if registry is None:
        registry = STRATEGY_REGISTRY
    
    magnetics_per_id = {}
    for sid, info in registry.items():
        m = info["magic"]
        magnetics_per_id.setdefault(m, []).append(sid)
    
    collisions = {m: sids for m, sids in magnetics_per_id.items() if len(sids) > 1}
    if collisions:
        parts = [f"  Magic {m}: {', '.join(sids)}" for m, sids in collisions.items()]
        raise ValueError("FATAL: Magic number collision detected!\n" + "\n".join(parts))
    
    return True


def get_magic(strategy_id: str) -> int:
    """Lookup magic number by strategy ID."""
    try:
        return STRATEGY_REGISTRY[strategy_id]["magic"]
    except KeyError:
        raise ValueError(f"Strategy '{strategy_id}' not found in registry")


# Startup verification - fail immediately if collision detected
try:
    verify_unique_magnetics()
except ValueError:
    raise
