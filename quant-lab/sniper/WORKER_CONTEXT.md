# PROP_SNIPER_WORKER_CONTEXT.md
# Shared context for all Phase 2-4 workers

## CEREBUS EDGE METRICS (for PES calculations)
- Composite WR: 85.7% (Symmetry Trap primary)
- Monthly return: ~15% of account
- Sharpe ratio: 8.5
- Profit Factor: 8.0
- Avg trades/day: 2.0
- Max DD: 0.04% (1-3% in practice per account)
- Instrument focus: Futures (ES, NQ, CL, Gold)
- Payout cycle assumption: 14-day standard, 7-day best case

## KEY PATHS
- Sniper package: C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\sniper\
- Ontology: quant_lab/sniper/ontology_mapper.py
- Scraper: quant_lab/sniper/scraper_engine.py
- FF Matrix: quant_lab/sniper/ff_matrix.py
- PES Calculator: quant_lab/sniper/pes_calculator.py
- Database: quant_lab/sniper/database.py
- Scope (CLI): quant_lab/sniper/scope.py
- Config output: quant_lab/sniper/configs/
- Snapshots: quant_lab/sniper/snapshots/

## IMPORTANT: Python imports
Always use: `from quant_lab.sniper.X import Y`
Run from project root: C:\Users\wifik\Desktop\projects\larger-lab\

## EXISTING v1.0 MODULES (already working)
- pes_calculator.py: PESCalculator, FirmProfile, EngineEdge, PESResult with full meta equation
- scope.py: CLI orchestrator (seed, scope-calc, scope-run, scope-report)
- config_generator.py: YAML/JSON output generator
- ff_protocol.py: FFProtocol, FFStatus, PromoDetails

## NEW PHASE 1 MODULES (just built)
- ontology_mapper.py: PropFirmOntology dataclass (30+ fields), OntologyMapper.from_propfirm_match()
- scraper_engine.py: PropFirmMatchScraper (2-pass: table + detail pages), PayoutJunctionScraper
- ff_matrix.py: FFScalingMatrix (exponential CoC decay), CapitalDeploymentRouter (ranked directives)

## ARCHITECTURE RULES
1. Physics (trading) NEVER touches venue (prop firm rules)
2. OC2/Sniper = config generator ONLY, not a trading system
3. All outputs are YAML/JSON configs read by execution engine
4. Separation: CEREBUS edge → Sniper PES → Deployment Config → Execution Engine

## DATABASE SCHEMA (3 tables)
- prop_firms: firm_id, name, website, account_sizes, cost_per_size, promo_active, max_daily_loss_pct, max_trailing_dd_pct, consistency_rule, min_trading_days, payout_cycle_days, payout_buffer_days, payout_method, scaling_rules, allowed_instruments, news_restrictions, ff_status, patch_signals, last_updated, status
- capital_deployments: deployment_id, firm_id, account_size, quantity, total_cost, total_risk_capital, pes_score, effective_exposure, capital_velocity, crossover_threshold, equivalent_live_leverage, deployed_at, status, config_version, notes
- pes_snapshots: snapshot_id, snapshot_date, firm_id, account_size, pes_score, effective_leverage, consistency_drag, velocity_factor, opportunity_cost_live, is_optimal, notes
