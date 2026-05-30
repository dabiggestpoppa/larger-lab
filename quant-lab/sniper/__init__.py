"""
Prop Firm Sniper Engine - Capital Allocation Optimization System
Layer: OC2 Intelligence (above the venue)
Does NOT trade. Outputs deployment config only.
"""

__version__ = "1.0.0"

from .pes_calculator import PESCalculator, FirmProfile, EngineEdge, PESResult
from .database import init_database, list_firms, upsert_firm, insert_pes_snapshot, get_latest_snapshots, get_optimal_deployments
from .ff_protocol import FFProtocol, FFStatus, PromoDetails, PatchSignal, PatchSeverity
from .config_generator import ConfigGenerator
from .firm_scanner import FirmScanner

# OC2Scope is intentionally NOT imported here to avoid circular imports.
# Import directly: from sniper.scope import OC2Scope
