"""
Prop Firm Sniper Engine - Capital Allocation Optimization System
Layer: OC2 Intelligence (above the venue)
Does NOT trade. Outputs deployment config only.

Phase 1 Build: Ontology Mapper + Scraper Engine + F&F Matrix + Deployment Router
Phase 2 Build: Structural Decay Monitor + Self-Healing Telemetry + Risk Litigator
"""

__version__ = "1.2.0-phase2"

# Core math
from .pes_calculator import PESCalculator, FirmProfile, EngineEdge, PESResult

# Database
from .database import (
    init_database, list_firms, upsert_firm, get_firm, get_firm_by_name,
    insert_pes_snapshot, get_latest_snapshots, get_optimal_deployments,
    insert_deployment, list_deployments,
)

# F&F Protocol
from .ff_protocol import FFProtocol, FFStatus, PromoDetails, PatchSignal, PatchSeverity

# Config Generator
from .config_generator import ConfigGenerator

# Phase 1 New Modules
from .ontology_mapper import (
    PropFirmOntology, OntologyMapper, TrailingType, DDType, normalize_raw_scrape
)
from .scraper_engine import PropFirmMatchScraper, PayoutJunctionScraper
from .ff_matrix import FFScalingMatrix, CapitalDeploymentRouter, DeploymentDirective

# OC2Scope is intentionally NOT imported here to avoid circular imports.
# Import directly: from sniper.scope import OC2Scope
