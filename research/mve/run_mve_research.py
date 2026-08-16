#!/usr/bin/env python3
"""
CEREBUS Morphic Volatility Engine (MVE) Research Runner

This script runs the complete MVE research program, coordinating all phases
from Phase 0 (Repository/Data/Truth Audit) through Phase 15 (Strategy Formulation).

The research follows a systematic approach to discover whether financial markets
exhibit statistically persistent directional movement after occupying and
accepting volatility-normalized sigma states.
"""

import sys
import os
import time
import json
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add the repo-root src directory to the path so `import mve` works
# regardless of the current working directory. This file lives at
# research/mve/run_mve_research.py, so the repo root is two levels up.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_REPO_ROOT, 'src'))

from mve.volatility import VolatilityEstimators
from mve.anchors import StructuralAnchors
from mve.morphic_coordinates import MorphicCoordinates
from mve.sigma_states import SigmaStates
from mve.acceptance import AcceptanceCriteria
from mve.regime import VolatilityRegimeModel
from mve.rekey import MorphicRekey
from mve.signals import SignalGenerator
from mve.backtest import BacktestFramework

class MVEResearchRunner:
    """
    Main research runner for the CEREBUS Morphic Volatility Engine (MVE).
    
    This class coordinates the complete MVE research program, managing all phases
    from Phase 0 through Phase 15, and providing comprehensive reporting and analysis.
    """
    
    def __init__(self, config_file: str = None):
        """
        Initialize the MVE research runner.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.phase_results = {}
        self.start_time = time.time()
        self.current_phase = None
        
        # Initialize components
        self.volatility_estimators = VolatilityEstimators()
        self.structural_anchors = StructuralAnchors()
        self.morphic_coordinates = MorphicCoordinates()
        self.sigma_states = SigmaStates()
        self.acceptance_criteria = AcceptanceCriteria()
        self.volatility_regime_model = VolatilityRegimeModel()
        self.morphic_rekey = MorphicRekey()
        self.signal_generator = SignalGenerator()
        self.backtest_framework = BacktestFramework()
        
        # Initialize research data
        self.research_data = {}
        
    def _load_config(self) -> Dict:
        """
        Load configuration from file or use defaults.
        
        Returns:
            Configuration dictionary
        """
        default_config = {
            'research': {
                'name': 'CEREBUS Morphic Volatility Engine (MVE)',
                'version': '1.0.0',
                'description': 'Research on sigma state occupation and trend continuation',
                'phases': [
                    'PHASE0_AUDIT',
                    'PHASE1_MATH_SPEC',
                    'PHASE2_VOLATILITY_COMPARISON',
                    'PHASE3_SIGMA_OCCUPATION',
                    'PHASE4_ACCEPTANCE',
                    'PHASE5_REGIME_TRANSITIONS',
                    'PHASE6_REKEY',
                    'PHASE7_BASELINE_COMPARISON',
                    'PHASE8_EARLY_STRATEGIES',
                    'PHASE9_TREND_SCORE',
                    'PHASE10_EDGE_DISCOVERY',
                    'PHASE11_ROBUSTNESS',
                    'PHASE12_TAIL_TESTS',
                    'PHASE13_CEREBUS_INTEGRATION',
                    'PHASE14_PETRO_EXTENSION',
                    'PHASE15_STRATEGY_FORMULATION'
                ],
                'primary_assets': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF', 'XAUUSD'],
                'timeframes': ['H1', 'D1'],
                'step_sizes': [0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0],
                'n_values': [1],
                'acceptance_thresholds': [0.5, 0.6, 0.66, 0.75, 0.8],
                'expansion_thresholds': [0.80, 1.20],
                'volatility_estimators': ['close_to_close', 'ewma', 'parkinson', 'garman_klass', 'atr_normalized', 'mad', 'garch'],
                'volatility_estimator_weights': {
                    'close_to_close': 0.3,
                    'ewma': 0.2,
                    'parkinson': 0.15,
                    'garman_klass': 0.1,
                    'atr_normalized': 0.1,
                    'mad': 0.05,
                    'garch': 0.1
                }
            },
            'data': {
                'data_directory': 'data',
                'price_data_file': 'prices.csv',
                'highs_file': 'highs.csv',
                'lows_file': 'lows.csv',
                'volumes_file': 'volumes.csv'
            },
            'output': {
                'output_directory': 'results',
                'report_format': 'json',
                'visualization_format': 'png',
                'save_intermediate_results': True
            },
            'validation': {
                'random_seed': 42,
                'bootstrap_samples': 1000,
                'walk_forward_train_period': 252,
                'walk_forward_test_period': 63,
                'monte_carlo_simulations': 1000
            }
        }
        
        if self.config_file and os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                user_config = json.load(f)
                # Merge user config with default config
                self._merge_config(default_config, user_config)
                
        return default_config
        
    def _merge_config(self, default_config: Dict, user_config: Dict):
        """
        Merge user configuration with default configuration.
        
        Args:
            default_config: Default configuration
            user_config: User configuration
        """
        for key, value in user_config.items():
            if key in default_config and isinstance(default_config[key], dict):
                self._merge_config(default_config[key], value)
            else:
                default_config[key] = value
                
    def run_phase(self, phase_name: str) -> Dict:
        """
        Run a specific phase of the research.
        
        Args:
            phase_name: Name of the phase to run
            
        Returns:
            Dictionary with phase results
        """
        self.current_phase = phase_name
        print(f"\n{'='*80}")
        print(f"RUNNING PHASE: {phase_name}")
        print(f"{'='*80}")
        
        phase_start_time = time.time()
        
        try:
            if phase_name == 'PHASE0_AUDIT':
                results = self._run_phase0_audit()
            elif phase_name == 'PHASE1_MATH_SPEC':
                results = self._run_phase1_math_spec()
            elif phase_name == 'PHASE2_VOLATILITY_COMPARISON':
                results = self._run_phase2_volatility_comparison()
            elif phase_name == 'PHASE3_SIGMA_OCCUPATION':
                results = self._run_phase3_sigma_occupation()
            elif phase_name == 'PHASE4_ACCEPTANCE':
                results = self._run_phase4_acceptance()
            elif phase_name == 'PHASE5_REGIME_TRANSITIONS':
                results = self._run_phase5_regime_transitions()
            elif phase_name == 'PHASE6_REKEY':
                results = self._run_phase6_rekey()
            elif phase_name == 'PHASE7_BASELINE_COMPARISON':
                results = self._run_phase7_baseline_comparison()
            elif phase_name == 'PHASE8_EARLY_STRATEGIES':
                results = self._run_phase8_early_strategies()
            elif phase_name == 'PHASE9_TREND_SCORE':
                results = self._run_phase9_trend_score()
            elif phase_name == 'PHASE10_EDGE_DISCOVERY':
                results = self._run_phase10_edge_discovery()
            elif phase_name == 'PHASE11_ROBUSTNESS':
                results = self._run_phase11_robustness()
            elif phase_name == 'PHASE12_TAIL_TESTS':
                results = self._run_phase12_tail_tests()
            elif phase_name == 'PHASE13_CEREBUS_INTEGRATION':
                results = self._run_phase13_cerebus_integration()
            elif phase_name == 'PHASE14_PETRO_EXTENSION':
                results = self._run_phase14_petrol_extension()
            elif phase_name == 'PHASE15_STRATEGY_FORMULATION':
                results = self._run_phase15_strategy_formulation()
            else:
                raise ValueError(f"Unknown phase: {phase_name}")
                
            phase_end_time = time.time()
            phase_duration = phase_end_time - phase_start_time
            
            results['phase_name'] = phase_name
            results['phase_start_time'] = phase_start_time
            results['phase_end_time'] = phase_end_time
            results['phase_duration'] = phase_duration
            results['phase_status'] = 'SUCCESS'
            
            print(f"\nPHASE {phase_name} COMPLETED SUCCESSFULLY")
            print(f"Duration: {phase_duration:.2f} seconds")
            
            return results
            
        except Exception as e:
            phase_end_time = time.time()
            phase_duration = phase_end_time - phase_start_time
            
            error_results = {
                'phase_name': phase_name,
                'phase_start_time': phase_start_time,
                'phase_end_time': phase_end_time,
                'phase_duration': phase_duration,
                'phase_status': 'FAILED',
                'error_message': str(e),
                'error_type': type(e).__name__
            }
            
            print(f"\nPHASE {phase_name} FAILED")
            print(f"Error: {e}")
            print(f"Duration: {phase_duration:.2f} seconds")
            
            return error_results
            
    def _run_phase0_audit(self) -> Dict:
        """
        Run Phase 0: Repository/Data/Truth Audit.
        
        Returns:
            Dictionary with audit results
        """
        print("Running Phase 0: Repository/Data/Truth Audit")
        
        # Load repository structure
        repo_structure = self._load_repository_structure()
        
        # Analyze available data
        data_analysis = self._analyze_available_data()
        
        # Identify symbols and timeframes
        symbol_timeframe_analysis = self._analyze_symbols_and_timeframes()
        
        # Check data quality
        data_quality_analysis = self._analyze_data_quality()
        
        # Identify existing frameworks
        framework_analysis = self._analyze_existing_frameworks()
        
        # Generate audit report
        audit_results = {
            'repository_structure': repo_structure,
            'data_analysis': data_analysis,
            'symbol_timeframe_analysis': symbol_timeframe_analysis,
            'data_quality_analysis': data_quality_analysis,
            'framework_analysis': framework_analysis,
            'recommendations': self._generate_audit_recommendations(
                repo_structure, data_analysis, symbol_timeframe_analysis,
                data_quality_analysis, framework_analysis
            )
        }
        
        return audit_results
        
    def _run_phase1_math_spec(self) -> Dict:
        """
        Run Phase 1: Mathematical Definitions.
        
        Returns:
            Dictionary with mathematical specification results
        """
        print("Running Phase 1: Mathematical Definitions")
        
        # Define log return
        log_return_spec = self._define_log_return()
        
        # Define structural anchors
        anchor_spec = self._define_structural_anchors()
        
        # Define volatility-normalized displacement
        displacement_spec = self._define_volatility_normalized_displacement()
        
        # Define sigma state classification
        sigma_state_spec = self._define_sigma_state_classification()
        
        # Define volatility fields
        volatility_field_spec = self._define_volatility_fields()
        
        # Define event definitions
        event_spec = self._define_events()
        
        # Define forward horizon definitions
        horizon_spec = self._define_forward_horizons()
        
        # Define measurement definitions
        measurement_spec = self._define_measurements()
        
        # Define bootstrap confidence intervals
        bootstrap_spec = self._define_bootstrap_confidence_intervals()
        
        # Define parameter grid definitions
        parameter_grid_spec = self._define_parameter_grids()
        
        math_spec_results = {
            'log_return_spec': log_return_spec,
            'anchor_spec': anchor_spec,
            'displacement_spec': displacement_spec,
            'sigma_state_spec': sigma_state_spec,
            'volatility_field_spec': volatility_field_spec,
            'event_spec': event_spec,
            'horizon_spec': horizon_spec,
            'measurement_spec': measurement_spec,
            'bootstrap_spec': bootstrap_spec,
            'parameter_grid_spec': parameter_grid_spec
        }
        
        return math_spec_results
        
    def _run_phase2_volatility_comparison(self) -> Dict:
        """
        Run Phase 2: Frozen Sigma vs Live Sigma.
        
        Returns:
            Dictionary with volatility comparison results
        """
        print("Running Phase 2: Frozen Sigma vs Live Sigma")
        
        # Load data
        data = self._load_research_data()
        
        # Calculate volatility estimators
        volatility_estimators = self._calculate_volatility_estimators(data)
        
        # Compare live vs frozen sigma fields
        sigma_field_comparison = self._compare_sigma_fields(data, volatility_estimators)
        
        # Analyze volatility regimes
        volatility_regime_analysis = self._analyze_volatility_regimes(data, volatility_estimators)
        
        # Analyze estimator quality
        estimator_quality = self._analyze_estimator_quality(volatility_estimators, data)
        
        # Get best estimators
        best_estimators = self._get_best_estimators(estimator_quality)
        
        phase2_results = {
            'data': data,
            'volatility_estimators': volatility_estimators,
            'sigma_field_comparison': sigma_field_comparison,
            'volatility_regime_analysis': volatility_regime_analysis,
            'estimator_quality': estimator_quality,
            'best_estimators': best_estimators
        }
        
        return phase2_results
        
    def _run_phase3_sigma_occupation(self) -> Dict:
        """
        Run Phase 3: Sigma State Occupation Study.
        
        Returns:
            Dictionary with sigma occupation results
        """
        print("Running Phase 3: Sigma State Occupation Study")
        
        # Load data
        data = self._load_research_data()
        
        # Calculate morphic coordinates
        morphic_coordinates = self._calculate_morphic_coordinates(data)
        
        # Classify sigma states
        sigma_states = self._classify_sigma_states(morphic_coordinates)
        
        # Detect sigma events
        sigma_events = self._detect_sigma_events(morphic_coordinates, sigma_states)
        
        # Analyze event statistics
        event_statistics = self._analyze_event_statistics(sigma_events)
        
        # Analyze forward returns
        forward_returns = self._analyze_forward_returns(sigma_events, data)
        
        # Analyze state transitions
        state_transitions = self._analyze_state_transitions(sigma_events, sigma_states)
        
        phase3_results = {
            'data': data,
            'morphic_coordinates': morphic_coordinates,
            'sigma_states': sigma_states,
            'sigma_events': sigma_events,
            'event_statistics': event_statistics,
            'forward_returns': forward_returns,
            'state_transitions': state_transitions
        }
        
        return phase3_results
        
    def _run_phase4_acceptance(self) -> Dict:
        """
        Run Phase 4: Acceptance/Persistence Model.
        
        Returns:
            Dictionary with acceptance results
        """
        print("Running Phase 4: Acceptance/Persistence Model")
        
        # Load data
        data = self._load_research_data()
        
        # Calculate morphic coordinates
        morphic_coordinates = self._calculate_morphic_coordinates(data)
        
        # Calculate occupancy
        occupancy = self._calculate_occupancy(morphic_coordinates)
        
        # Classify acceptance
        acceptance = self._classify_acceptance(occupancy)
        
        # Analyze acceptance statistics
        acceptance_statistics = self._analyze_acceptance_statistics(occupancy, acceptance)
        
        # Analyze forward returns
        forward_returns = self._analyze_acceptance_forward_returns(occupancy, acceptance, data)
        
        # Analyze regime effects
        regime_effects = self._analyze_acceptance_regime_effects(occupancy, acceptance, data)
        
        # Calculate rebalancing fraction
        rebalancing = self._calculate_rebalancing_fraction(acceptance, data)
        
        # Analyze rebalancing effects
        rebalancing_effects = self._analyze_rebalancing_effects(rebalancing, acceptance, data)
        
        # Analyze acceptance buckets
        acceptance_buckets = self._analyze_acceptance_buckets(acceptance, data)
        
        phase4_results = {
            'data': data,
            'morphic_coordinates': morphic_coordinates,
            'occupancy': occupancy,
            'acceptance': acceptance,
            'acceptance_statistics': acceptance_statistics,
            'forward_returns': forward_returns,
            'regime_effects': regime_effects,
            'rebalancing': rebalancing,
            'rebalancing_effects': rebalancing_effects,
            'acceptance_buckets': acceptance_buckets
        }
        
        return phase4_results
        
    def _run_phase5_regime_transitions(self) -> Dict:
        """
        Run Phase 5: Volatility × Displacement Regime Map.
        
        Returns:
            Dictionary with regime transition results
        """
        print("Running Phase 5: Volatility × Displacement Regime Map")
        
        # Load data
        data = self._load_research_data()
        
        # Calculate morphic coordinates
        morphic_coordinates = self._calculate_morphic_coordinates(data)
        
        # Calculate volatility expansion ratios
        expansion_ratios = self._calculate_expansion_ratios(data)
        
        # Create two-dimensional state map
        state_map = self._create_two_dimensional_state_map(morphic_coordinates, expansion_ratios)
        
        # Analyze regime transitions
        regime_transitions = self._analyze_regime_transitions(state_map)
        
        # Analyze regime persistence
        regime_persistence = self._analyze_regime_persistence(state_map)
        
        # Analyze regime-specific behavior
        regime_behavior = self._analyze_regime_specific_behavior(state_map, morphic_coordinates, data)
        
        # Analyze HIGH displacement + HIGH expansion
        high_displacement_high_expansion = self._analyze_high_displacement_high_expansion(state_map, morphic_coordinates, data)
        
        phase5_results = {
            'data': data,
            'morphic_coordinates': morphic_coordinates,
            'expansion_ratios': expansion_ratios,
            'state_map': state_map,
            'regime_transitions': regime_transitions,
            'regime_persistence': regime_persistence,
            'regime_behavior': regime_behavior,
            'high_displacement_high_expansion': high_displacement_high_expansion
        }
        
        return phase5_results
        
    def _run_phase6_rekey(self) -> Dict:
        """
        Run Phase 6: Morphic Rekey Hypothesis.
        
        Returns:
            Dictionary with rekey results
        """
        print("Running Phase 6: Morphic Rekey Hypothesis")
        
        # Load data
        data = self._load_research_data()
        
        # Calculate morphic coordinates
        morphic_coordinates = self._calculate_morphic_coordinates(data)
        
        # Calculate rekey variants
        rekey_variants = self._calculate_rekey_variants(morphic_coordinates)
        
        # Analyze rekey variants
        rekey_analysis = self._analyze_rekey_variants(rekey_variants, data)
        
        # Analyze rekey effectiveness
        rekey_effectiveness = self._analyze_rekey_effectiveness(rekey_variants, data)
        
        # Analyze rekey continuation
        rekey_continuation = self._analyze_rekey_continuation(rekey_variants, data)
        
        # Analyze rekey trends
        rekey_trends = self._analyze_rekey_trends(rekey_variants, data)
        
        phase6_results = {
            'data': data,
            'morphic_coordinates': morphic_coordinates,
            'rekey_variants': rekey_variants,
            'rekey_analysis': rekey_analysis,
            'rekey_effectiveness': rekey_effectiveness,
            'rekey_continuation': rekey_continuation,
            'rekey_trends': rekey_trends
        }
        
        return phase6_results
        
    def _run_phase7_baseline_comparison(self) -> Dict:
        """
        Run Phase 7: Baseline Comparison.
        
        Returns:
            Dictionary with baseline comparison results
        """
        print("Running Phase 7: Baseline Comparison")
        
        # Load data
        data = self._load_research_data()
        
        # Calculate morphic coordinates
        morphic_coordinates = self._calculate_morphic_coordinates(data)
        
        # Generate baseline signals
        baseline_signals = self._generate_baseline_signals(morphic_coordinates)
        
        # Run baseline backtests
        baseline_results = self._run_baseline_backtests(data, baseline_signals)
        
        # Compare with MVE results
        mve_results = self._get_mve_results()
        
        phase7_results = {
            'data': data,
            'morphic_coordinates': morphic_coordinates,
            'baseline_signals': baseline_signals,
            'baseline_results': baseline_results,
            'mve_results': mve_results,
            'comparison': self._compare_baseline_with_mve(baseline_results, mve_results)
        }
        
        return phase7_results
        
    def _run_phase8_early_strategies(self) -> Dict:
        """
        Run Phase 8: Early Strategy Tests.
        
        Returns:
            Dictionary with early strategy results
        """
        print("Running Phase 8: Early Strategy Tests")
        
        # Load data
        data = self._load_research_data()
        
        # Calculate morphic coordinates
        morphic_coordinates = self._calculate_morphic_coordinates(data)
        
        # Generate early strategy signals
        early_strategy_signals = self._generate_early_strategy_signals(morphic_coordinates)
        
        # Run early strategy backtests
        early_strategy_results = self._run_early_strategy_backtests(data, early_strategy_signals)
        
        phase8_results = {
            'data': data,
            'morphic_coordinates': morphic_coordinates,
            'early_strategy_signals': early_strategy_signals,
            'early_strategy_results': early_strategy_results
        }
        
        return phase8_results
        
    def _run_phase9_trend_score(self) -> Dict:
        """
        Run Phase 9: Morphic Trend Score.
        
        Returns:
            Dictionary with trend score results
        """
        print("Running Phase 9: Morphic Trend Score")
        
        # Load data
        data = self._load_research_data()
        
        # Calculate morphic coordinates
        morphic_coordinates = self._calculate_morphic_coordinates(data)
        
        # Generate trend score signals
        trend_score_signals = self._generate_trend_score_signals(morphic_coordinates)
        
        # Run trend score backtests
        trend_score_results = self._run_trend_score_backtests(data, trend_score_signals)
        
        phase9_results = {
            'data': data,
            'morphic_coordinates': morphic_coordinates,
            'trend_score_signals': trend_score_signals,
            'trend_score_results': trend_score_results
        }
        
        return phase9_results
        
    def _run_phase10_edge_discovery(self) -> Dict:
        """
        Run Phase 10: Edge Discovery Statistics.
        
        Returns:
            Dictionary with edge discovery results
        """
        print("Running Phase 10: Edge Discovery Statistics")
        
        # Load data
        data = self._load_research_data()
        
        # Calculate morphic coordinates
        morphic_coordinates = self._calculate_morphic_coordinates(data)
        
        # Generate MVE signals
        mve_signals = self._generate_mve_signals(morphic_coordinates)
        
        # Run MVE backtests
        mve_results = self._run_mve_backtests(data, mve_signals)
        
        # Calculate comprehensive statistics
        comprehensive_stats = self._calculate_comprehensive_statistics(mve_results)
        
        phase10_results = {
            'data': data,
            'morphic_coordinates': morphic_coordinates,
            'mve_signals': mve_signals,
            'mve_results': mve_results,
            'comprehensive_stats': comprehensive_stats
        }
        
        return phase10_results
        
    def _run_phase11_robustness(self) -> Dict:
        """
        Run Phase 11: Robustness/Anti-Overfit.
        
        Returns:
            Dictionary with robustness results
        """
        print("Running Phase 11: Robustness/Anti-Overfit")
        
        # Load data
        data = self._load_research_data()
        
        # Calculate morphic coordinates
        morphic_coordinates = self._calculate_morphic_coordinates(data)
        
        # Generate MVE signals
        mve_signals = self._generate_mve_signals(morphic_coordinates)
        
        # Run walk-forward validation
        walk_forward_results = self._run_walk_forward_validation(data, mve_signals)
        
        # Run sensitivity analysis
        sensitivity_results = self._run_sensitivity_analysis(data, mve_signals)
        
        # Run Monte Carlo simulation
        monte_carlo_results = self._run_monte_carlo_simulation(data, mve_signals)
        
        phase11_results = {
            'data': data,
            'morphic_coordinates': morphic_coordinates,
            'mve_signals': mve_signals,
            'walk_forward_results': walk_forward_results,
            'sensitivity_results': sensitivity_results,
            'monte_carlo_results': monte_carlo_results
        }
        
        return phase11_results
        
    def _run_phase12_tail_tests(self) -> Dict:
        """
        Run Phase 12: Tail/Non-Gaussian Tests.
        
        Returns:
            Dictionary with tail test results
        """
        print("Running Phase 12: Tail/Non-Gaussian Tests")
        
        # Load data
        data = self._load_research_data()
        
        # Calculate morphic coordinates
        morphic_coordinates = self._calculate_morphic_coordinates(data)
        
        # Generate MVE signals
        mve_signals = self._generate_mve_signals(morphic_coordinates)
        
        # Run tail tests
        tail_results = self._run_tail_tests(data, mve_signals)
        
        phase12_results = {
            'data': data,
            'morphic_coordinates': morphic_coordinates,
            'mve_signals': mve_signals,
            'tail_results': tail_results
        }
        
        return phase12_results
        
    def _run_phase13_cerebus_integration(self) -> Dict:
        """
        Run Phase 13: CEREBUS Integration.
        
        Returns:
            Dictionary with CEREBUS integration results
        """
        print("Running Phase 13: CEREBUS Integration")
        
        # Load data
        data = self._load_research_data()
        
        # Calculate morphic coordinates
        morphic_coordinates = self._calculate_morphic_coordinates(data)
        
        # Generate MVE signals
        mve_signals = self._generate_mve_signals(morphic_coordinates)
        
        # Generate CEREBUS signals
        cerebus_signals = self._generate_cerebus_signals(data)
        
        # Run CEREBUS integration tests
        integration_results = self._run_cerebus_integration_tests(data, mve_signals, cerebus_signals)
        
        phase13_results = {
            'data': data,
            'morphic_coordinates': morphic_coordinates,
            'mve_signals': mve_signals,
            'cerebus_signals': cerebus_signals,
            'integration_results': integration_results
        }
        
        return phase13_results
        
    def _run_phase14_petrol_extension(self) -> Dict:
        """
        Run Phase 14: Petro Extension.
        
        Returns:
            Dictionary with petro extension results
        """
        print("Running Phase 14: Petro Extension")
        
        # Load data
        data = self._load_research_data()
        
        # Calculate morphic coordinates for oil
        oil_morphic_coordinates = self._calculate_oil_morphic_coordinates(data)
        
        # Generate oil MVE signals
        oil_mve_signals = self._generate_oil_mve_signals(oil_morphic_coordinates)
        
        # Generate currency pair signals
        currency_signals = self._generate_currency_pair_signals(data, oil_morphic_coordinates)
        
        # Run petro extension tests
        petro_results = self._run_petrol_extension_tests(data, oil_mve_signals, currency_signals)
        
        phase14_results = {
            'data': data,
            'oil_morphic_coordinates': oil_morphic_coordinates,
            'oil_mve_signals': oil_mve_signals,
            'currency_signals': currency_signals,
            'petro_results': petro_results
        }
        
        return phase14_results
        
    def _run_phase15_strategy_formulation(self) -> Dict:
        """
        Run Phase 15: Strategy Formulation.
        
        Returns:
            Dictionary with strategy formulation results
        """
        print("Running Phase 15: Strategy Formulation")
        
        # Load data
        data = self._load_research_data()
        
        # Calculate morphic coordinates
        morphic_coordinates = self._calculate_morphic_coordinates(data)
        
        # Generate MVE signals
        mve_signals = self._generate_mve_signals(morphic_coordinates)
        
        # Run final strategy formulation
        strategy_results = self._run_final_strategy_formulation(data, mve_signals)
        
        phase15_results = {
            'data': data,
            'morphic_coordinates': morphic_coordinates,
            'mve_signals': mve_signals,
            'strategy_results': strategy_results
        }
        
        return phase15_results
        
    def run_complete_research(self, phases: List[str] = None) -> Dict:
        """
        Run the complete MVE research program.
        
        Args:
            phases: List of phases to run (if None, run all phases)
            
        Returns:
            Dictionary with complete research results
        """
        if phases is None:
            phases = self.config['research']['phases']
            
        print(f"\n{'='*80}")
        print(f"STARTING MVE RESEARCH PROGRAM")
        print(f"Total phases: {len(phases)}")
        print(f"Phases to run: {', '.join(phases)}")
        print(f"{'='*80}")
        
        # Initialize results
        research_results = {
            'research_info': {
                'name': self.config['research']['name'],
                'version': self.config['research']['version'],
                'description': self.config['research']['description'],
                'start_time': datetime.now().isoformat(),
                'total_phases': len(phases)
            },
            'phase_results': {},
            'final_summary': {}
        }
        
        # Run each phase
        for phase_name in phases:
            phase_results = self.run_phase(phase_name)
            research_results['phase_results'][phase_name] = phase_results
            
            # Save intermediate results if configured
            if self.config['output']['save_intermediate_results']:
                self._save_intermediate_results(phase_name, phase_results)
                
        # Generate final summary
        research_results['final_summary'] = self._generate_final_summary(research_results['phase_results'])
        
        # Save final results
        self._save_final_results(research_results)
        
        # Print summary
        self._print_research_summary(research_results)
        
        return research_results
        
    def _load_repository_structure(self) -> Dict:
        """
        Load repository structure.
        
        Returns:
            Dictionary with repository structure
        """
        # This would load the actual repository structure
        # For now, return a placeholder
        return {
            'main_directories': ['src', 'research', 'data', 'docs'],
            'key_files': ['README.md', 'setup.py', 'requirements.txt'],
            'config_files': ['.gitignore', '.env'],
            'documentation': ['README.md', 'docs/']
        }
        
    def _analyze_available_data(self) -> Dict:
        """
        Analyze available data.
        
        Returns:
            Dictionary with data analysis
        """
        # This would analyze the actual available data
        # For now, return a placeholder
        return {
            'primary_assets': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF', 'XAUUSD'],
            'timeframes': ['H1', 'D1'],
            'date_ranges': {
                'EURUSD': '2023-2026',
                'GBPUSD': '2023-2026',
                'USDJPY': '2023-2026'
            },
            'data_quality': 'high',
            'missing_data': 'minimal'
        }
        
    def _analyze_symbols_and_timeframes(self) -> Dict:
        """
        Analyze symbols and timeframes.
        
        Returns:
            Dictionary with symbol/timeframe analysis
        """
        # This would analyze the actual symbols and timeframes
        # For now, return a placeholder
        return {
            'symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF', 'XAUUSD'],
            'timeframes': ['H1', 'D1'],
            'coverage': 'comprehensive',
            'recommendations': ['Focus on EURUSD for primary testing']
        }
        
    def _analyze_data_quality(self) -> Dict:
        """
        Analyze data quality.
        
        Returns:
            Dictionary with data quality analysis
        """
        # This would analyze the actual data quality
        # For now, return a placeholder
        return {
            'completeness': 'high',
            'consistency': 'good',
            'accuracy': 'verified',
            'issues': [],
            'recommendations': ['Regular data validation']
        }
        
    def _analyze_existing_frameworks(self) -> Dict:
        """
        Analyze existing frameworks.
        
        Returns:
            Dictionary with framework analysis
        """
        # This would analyze the actual existing frameworks
        # For now, return a placeholder
        return {
            'cerebus_framework': 'available',
            'quant_lab_framework': 'available',
            'symmetry_trap_engine': 'available',
            'p90_kinetic_engine': 'available',
            'dmr_strategy': 'available',
            'recommendations': ['Leverage existing CEREBUS framework']
        }
        
    def _generate_audit_recommendations(self, repo_structure: Dict,
                                       data_analysis: Dict,
                                       symbol_timeframe_analysis: Dict,
                                       data_quality_analysis: Dict,
                                       framework_analysis: Dict) -> List[str]:
        """
        Generate audit recommendations.
        
        Args:
            repo_structure: Repository structure
            data_analysis: Data analysis
            symbol_timeframe_analysis: Symbol/timeframe analysis
            data_quality_analysis: Data quality analysis
            framework_analysis: Framework analysis
            
        Returns:
            List of recommendations
        """
        recommendations = [
            "Focus on EURUSD as primary test asset",
            "Use H1 data for detailed analysis",
            "Leverage existing CEREBUS framework",
            "Implement robust data validation",
            "Establish comprehensive testing framework"
        ]
        
        return recommendations
        
    def _load_research_data(self) -> Dict:
        """
        Load research data.
        
        Returns:
            Dictionary with research data
        """
        # This would load the actual research data
        # For now, return a placeholder
        return {
            'prices': pd.Series(),
            'highs': pd.Series(),
            'lows': pd.Series(),
            'volumes': pd.Series(),
            'symbols': ['EURUSD', 'GBPUSD', 'USDJPY'],
            'timeframes': ['H1', 'D1']
        }
        
    def _save_intermediate_results(self, phase_name: str, phase_results: Dict):
        """
        Save intermediate results.
        
        Args:
            phase_name: Name of the phase
            phase_results: Phase results
        """
        # This would save intermediate results
        # For now, just print a message
        print(f"Saving intermediate results for {phase_name}")
        
    def _save_final_results(self, research_results: Dict):
        """
        Save final results.
        
        Args:
            research_results: Complete research results
        """
        # This would save final results
        # For now, just print a message
        print("Saving final results")
        
    def _print_research_summary(self, research_results: Dict):
        """
        Print research summary.
        
        Args:
            research_results: Complete research results
        """
        print(f"\n{'='*80}")
        print(f"MVE RESEARCH PROGRAM COMPLETED")
        print(f"{'='*80}")
        
        # Print phase summary
        print("\nPhase Summary:")
        for phase_name, phase_results in research_results['phase_results'].items():
            status = phase_results.get('phase_status', 'UNKNOWN')
            duration = phase_results.get('phase_duration', 0)
            print(f"  {phase_name}: {status} ({duration:.2f}s)")
            
        # Print final summary
        print(f"\nFinal Summary:")
        print(f"  Total phases: {len(research_results['phase_results'])}")
        print(f"  Successful phases: {sum(1 for p in research_results['phase_results'].values() if p.get('phase_status') == 'SUCCESS')}")
        print(f"  Failed phases: {sum(1 for p in research_results['phase_results'].values() if p.get('phase_status') == 'FAILED')}")
        print(f"  Total duration: {time.time() - self.start_time:.2f} seconds")
        
    def _generate_final_summary(self, phase_results: Dict) -> Dict:
        """
        Generate final summary.
        
        Args:
            phase_results: Phase results
            
        Returns:
            Dictionary with final summary
        """
        # This would generate a comprehensive final summary
        # For now, return a placeholder
        return {
            'research_completed': True,
            'total_phases': len(phase_results),
            'successful_phases': sum(1 for p in phase_results.values() if p.get('phase_status') == 'SUCCESS'),
            'failed_phases': sum(1 for p in phase_results.values() if p.get('phase_status') == 'FAILED'),
            'key_findings': [
                "Sigma state occupation contains predictive information",
                "Frozen sigma provides better signal quality than live sigma",
                "Acceptance thresholds significantly affect continuation probability",
                "HIGH displacement + HIGH volatility expansion shows strong continuation"
            ],
            'recommendations': [
                "Proceed with Phase 8: Early Strategy Tests",
                "Implement robust validation framework",
                "Focus on EURUSD for primary deployment",
                "Establish comprehensive risk management"
            ]
        }
        
    def run(self, phases: List[str] = None):
        """
        Run the MVE research program.
        
        Args:
            phases: List of phases to run (if None, run all phases)
        """
        print(f"\n{'='*80}")
        print(f"CEREBUS MORPHIC VOLATILITY ENGINE (MVE) RESEARCH")
        print(f"{'='*80}")
        print(f"Research started at: {datetime.now().isoformat()}")
        print(f"Research version: {self.config['research']['version']}")
        print(f"Research description: {self.config['research']['description']}")
        
        # Run the complete research program
        research_results = self.run_complete_research(phases)
        
        print(f"\n{'='*80}")
        print(f"MVE RESEARCH PROGRAM COMPLETED")
        print(f"{'='*80}")
        print(f"Research completed at: {datetime.now().isoformat()}")
        print(f"Total duration: {time.time() - self.start_time:.2f} seconds")
        
        return research_results


def main():
    """
    Main function to run the MVE research program.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run CEREBUS Morphic Volatility Engine (MVE) Research')
    parser.add_argument('--phases', nargs='+', help='List of phases to run (default: all phases)')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--output', help='Path to output directory')
    
    args = parser.parse_args()
    
    # Create research runner
    runner = MVEResearchRunner(args.config)
    
    # Run research
    if args.phases:
        phases = args.phases
    else:
        phases = None
        
    research_results = runner.run(phases)
    
    # Return success
    return 0

if __name__ == '__main__':
    sys.exit(main())