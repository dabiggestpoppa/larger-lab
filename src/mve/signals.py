"""
Signal Generation for CEREBUS Morphic Volatility Engine

This module implements signal generation for the MVE research project.
Signals are generated based on sigma state occupation, acceptance criteria,
and rekey logic to identify potential trading opportunities.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

class SignalGenerator:
    """
    Signal generation for MVE research.
    
    This class implements signal generation based on sigma state occupation,
acceptance criteria, and rekey logic to identify potential trading opportunities.
    """
    
    def __init__(self, step_sizes: List[float] = None):
        """
        Initialize signal generator.
        
        Args:
            step_sizes: List of sigma state step sizes to test
        """
        if step_sizes is None:
            step_sizes = [0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0]
        self.step_sizes = step_sizes
        self.signals = {}
        
    def generate_sigma_escape_signals(self, morphic_coordinates: pd.Series,
                                    step: float = 1.0,
                                    n: int = 1) -> pd.Series:
        """
        Generate Sigma Escape signals.
        
        Model A: SIGMA ESCAPE
        
        LONG:
        1. M_frozen crosses +1 sigma.
        2. H4/D1 close beyond +1 sigma.
        3. volatility ratio C >= threshold.
        4. no immediate close back below boundary.
        
        Entry:
        next bar open or breakout close.
        
        Invalidation:
        0 sigma anchor OR prior structural state.
        
        Targets:
        +2 sigma
        +3 sigma
        
        SHORT = mirror.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step: Sigma state step size
            n: Sigma state level
            
        Returns:
            Signal series (1 for long, -1 for short, 0 for no signal)

        CAUSAL (R0.5.1 repair): the signal is KNOWN at the confirmation bar
        i+1 ("no immediate close back below boundary"), never backdated to the
        crossing bar i. The short mirror (documented "SHORT = mirror") is now
        implemented: the prior elif carried an identical condition (dead code),
        so shorts could never fire.
        """
        # Calculate sigma state boundary
        boundary = n * step

        # Initialize signal series
        signals = pd.Series(0, index=morphic_coordinates.index)
        coords = morphic_coordinates.to_numpy(dtype=float)

        # Generate signals (signal at i+1 is known only after bar i+1 closes)
        for i in range(len(coords) - 1):
            current_coord = coords[i]
            prev_coord = coords[i - 1] if i > 0 else 0.0

            # Check for long signal: crossing +boundary from below, confirmed
            # by bar i+1 (no immediate close back below boundary).
            if (current_coord > boundary and
                    (i == 0 or prev_coord <= boundary)):
                if abs(coords[i + 1]) > boundary:
                    signals.iloc[i + 1] = 1  # known at the confirmation bar

            # Check for short signal (mirror): crossing -boundary from above,
            # confirmed by bar i+1 (no immediate close back above boundary).
            elif (current_coord < -boundary and
                  (i == 0 or prev_coord >= -boundary)):
                if abs(coords[i + 1]) > boundary:
                    signals.iloc[i + 1] = -1  # known at the confirmation bar

        return signals
        
    def generate_accepted_sigma_breakout_signals(self, morphic_coordinates: pd.Series,
                                                step: float = 1.0,
                                                n: int = 1,
                                                acceptance_threshold: float = 0.8) -> pd.Series:
        """
        Generate Accepted Sigma Breakout signals.
        
        Model B: ACCEPTED SIGMA BREAKOUT
        
        LONG:
        1. +1 sigma breached.
        2. acceptance Occ >= threshold.
        3. shallow or normal rebalancing.
        4. prior sigma boundary remains intact.
        
        Entry:
        retest rejection or next close higher.
        
        Initial invalidation:
        accepted boundary - buffer.
        
        Runner:
        until accepted state is lost.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step: Sigma state step size
            n: Sigma state level
            acceptance_threshold: Acceptance threshold
            
        Returns:
            Signal series (1 for long, -1 for short, 0 for no signal)

        CAUSAL (R0.5.1 repair): realtime state signal, known at bar i. The
        prior implementation read bar i+1 into next_coord but BOTH branches
        emitted 1, so the read was cosmetic (no future dependency) and the
        last-bar suppression was an off-by-one artifact. The docstring's
        'retest rejection / next close higher' ENTRY was never implemented in
        code -> BLOCKED_LOGIC_SPEC (excluded from future scientific execution).
        """
        # Calculate sigma state boundary
        boundary = n * step

        # Initialize signal series
        signals = pd.Series(0, index=morphic_coordinates.index)

        # Calculate occupancy
        occupancy = self._calculate_occupancy(morphic_coordinates, step, n)

        # Generate signals (realtime: bar i uses only bars <= i)
        for i in range(len(morphic_coordinates)):
            current_coord = morphic_coordinates.iloc[i]
            current_occupancy = occupancy.iloc[i]

            # Accepted-breakout state signal
            if (abs(current_coord) > boundary and
                    current_occupancy >= acceptance_threshold):
                signals.iloc[i] = 1

        return signals
        
    def generate_recursive_morphic_trend_signals(self, morphic_coordinates: pd.Series,
                                               step: float = 1.0,
                                               n: int = 1) -> pd.Series:
        """
        Generate Recursive Morphic Trend signals.
        
        Model C: RECURSIVE MORPHIC TREND
        
        1. Enter after +1 sigma acceptance.
        2. When +2 sigma accepts:
           rekey origin.
        3. Continue while sigma progression remains positive.
        4. Exit only when active rekey field fails.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step: Sigma state step size
            n: Sigma state level
            
        Returns:
            Signal series (1 for entry, -1 for exit, 0 for no signal)

        CAUSAL (R0.5.1 repair): entry is KNOWN at the +2-sigma CONFIRMATION bar
        i+1, never backdated to the crossing bar i. The exit check uses a
        trailing 3-bar window (already causal).
        """
        # Calculate sigma state boundary
        boundary = n * step

        # Initialize signal series
        signals = pd.Series(0, index=morphic_coordinates.index)
        coords = morphic_coordinates.to_numpy(dtype=float)

        # Generate signals
        for i in range(len(coords)):
            current_coord = coords[i]
            prev_coord = coords[i - 1] if i > 0 else 0.0
            prev_prev = coords[i - 2] if i > 1 else 0.0

            # Check for entry signal: crossing at bar i-1 (from inside the
            # boundary to beyond it) confirmed by +2-sigma acceptance at bar i.
            # The signal is KNOWN at the confirmation bar i, never backdated
            # to the crossing bar i-1. A confirmed entry takes priority over a
            # same-bar exit (no overwrite).
            crossed_prev = (abs(prev_coord) > boundary and
                            (i == 1 or abs(prev_prev) <= boundary))
            if crossed_prev and abs(current_coord) > 2 * boundary:
                signals.iloc[i] = 1
                continue

            # Check for exit signal: active rekey field fails (trailing 3-bar
            # window, already causal).
            exit_path = (abs(current_coord) > boundary and
                         (i == 0 or abs(prev_coord) > boundary))
            if exit_path and i >= 5:
                above_count = sum(abs(coords[max(0, i - 2):i + 1]) > boundary)
                if above_count < 3:  # Less than 3 consecutive bars above boundary
                    signals.iloc[i] = -1

        return signals
        
    def generate_multi_timeframe_morphic_alignment_signals(self, morphic_coordinates_h1: pd.Series,
                                                          morphic_coordinates_d1: pd.Series,
                                                          step_h1: float = 1.0,
                                                          step_d1: float = 1.0,
                                                          n_h1: int = 1,
                                                          n_d1: int = 1) -> pd.Series:
        """
        Generate Multi-Timeframe Morphic Alignment signals.
        
        Model D: MULTI-TIMEFRAME MORPHIC ALIGNMENT
        
        Compute:
        M_D
        M_W
        M_M
        
        Test combinations:
        M_M > 0
        M_W > +1
        M_D < 0
        
        as candidate pullback-long regime.
        
        Also:
        M_M > 0
        M_W > 0
        M_D > 0
        
        as full alignment.
        
        Do NOT assume full alignment is superior.
        
        Test whether lower-timeframe opposition inside higher-timeframe positive state provides better entries.
        
        Args:
            morphic_coordinates_h1: H1 morphic coordinates
            morphic_coordinates_d1: D1 morphic coordinates
            step_h1: H1 sigma state step size
            step_d1: D1 sigma state step size
            n_h1: H1 sigma state level
            n_d1: D1 sigma state level
            
        Returns:
            Signal series (1 for long, -1 for short, 0 for no signal)
        """
        # Initialize signal series
        signals = pd.Series(0, index=morphic_coordinates_h1.index)
        
        # Generate signals
        for i in range(len(morphic_coordinates_h1)):
            # Get coordinates for this time
            h1_coord = morphic_coordinates_h1.iloc[i]
            d1_coord = morphic_coordinates_d1.iloc[i]

            # ROBUST (R0.5.1): NaN guard on int() conversions - warm-up NaN
            # coordinates previously crashed with int(NaN). Logic conditions
            # are UNTOUCHED (contradictions classified BLOCKED_LOGIC_SPEC in
            # MVE_R05_1_MODEL_D_AUDIT.md).
            h1_state = int(abs(h1_coord) // step_h1) if (not np.isnan(h1_coord) and h1_coord != 0) else 0
            d1_state = int(abs(d1_coord) // step_d1) if (not np.isnan(d1_coord) and d1_coord != 0) else 0
            
            # Test candidate pullback-long regime
            # M_M > 0, M_W > +1, M_D < 0
            if (d1_coord > 0 and h1_coord > n_h1 and d1_coord < 0):
                signals.iloc[i] = 1
                
            # Test full alignment
            # M_M > 0, M_W > 0, M_D > 0
            elif (d1_coord > 0 and h1_coord > 0 and d1_coord > 0):
                signals.iloc[i] = 1
                
            # Test lower-timeframe opposition inside higher-timeframe positive state
            elif (d1_coord > 0 and h1_coord < 0):
                signals.iloc[i] = 1
                
        return signals
        
    def generate_morphic_trend_score_signals(self, morphic_coordinates: pd.Series,
                                           step: float = 1.0,
                                           weights: Dict[str, float] = None) -> pd.Series:
        """
        Generate Morphic Trend Score signals.
        
        Model E: MORPHIC TREND SCORE
        
        TrendScore =
        w1 * D
        + w2 * V
        + w3 * A
        + w4 * P
        + w5 * Q
        
        where:
        D = directional normalized displacement
        V = volatility expansion ratio
        A = acceptance / occupancy
        P = persistence / retracement efficiency
        Q = state progression quality
        
        Possible definitions:
        D =
        signed M normalized / clipped
        
        V =
        sigma_fast / sigma_slow
        
        A =
        occupancy beyond active boundary
        
        P =
        1 - retracement_fraction
        
        Q =
        number of accepted same-direction sigma transitions
        minus
        number of reclaimed states
        
        DO NOT optimize continuous weights initially.
        
        First use:
        equal weights
        
        Then:
        rank transforms
        
        Then:
        simple logistic regression
        
        Then:
        regularized logistic regression
        
        Only after that consider:
        gradient boosting
        random forests
        hidden Markov models
        
        Avoid deep learning unless simple models demonstrably fail and there is sufficient data.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step: Sigma state step size
            weights: Dictionary of weights for each component
            
        Returns:
            Signal series (1 for long, -1 for short, 0 for no signal)
        """
        if weights is None:
            # Equal weights
            weights = {
                'D': 0.2,
                'V': 0.2,
                'A': 0.2,
                'P': 0.2,
                'Q': 0.2
            }
            
        # Initialize signal series
        signals = pd.Series(0, index=morphic_coordinates.index)
        
        # Calculate components
        D = self._calculate_directional_displacement(morphic_coordinates, step)
        V = self._calculate_volatility_expansion_ratio(morphic_coordinates)
        A = self._calculate_acceptance(morphic_coordinates, step)
        P = self._calculate_persistence(morphic_coordinates, step)
        Q = self._calculate_state_progression_quality(morphic_coordinates, step)
        
        # Calculate trend score
        trend_score = (
            weights['D'] * D +
            weights['V'] * V +
            weights['A'] * A +
            weights['P'] * P +
            weights['Q'] * Q
        )
        
        # Generate signals based on trend score
        for i in range(len(trend_score)):
            if trend_score.iloc[i] > 0.5:  # Threshold for long signal
                signals.iloc[i] = 1
            elif trend_score.iloc[i] < -0.5:  # Threshold for short signal
                signals.iloc[i] = -1
                
        return signals
        
    def _calculate_occupancy(self, morphic_coordinates: pd.Series,
                           step: float, n: int) -> pd.Series:
        """
        Calculate occupancy beyond sigma state.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step: Sigma state step size
            n: Sigma state level
            
        Returns:
            Occupancy series
        """
        # Calculate sigma state boundary
        boundary = n * step
        
        # Initialize occupancy series
        occupancy = pd.Series(0.0, index=morphic_coordinates.index)
        
        # Calculate occupancy for each bar
        for i in range(len(morphic_coordinates)):
            if i >= 3:  # Need at least 3 bars for occupancy calculation
                # Get the window of bars
                window_coords = morphic_coordinates.iloc[max(0, i - 2):i + 1]
                
                # Count bars above boundary
                above_boundary_count = sum(abs(window_coords) > boundary)
                
                # Calculate occupancy ratio
                occupancy.iloc[i] = above_boundary_count / 3
                
        return occupancy
        
    def _calculate_directional_displacement(self, morphic_coordinates: pd.Series,
                                           step: float) -> pd.Series:
        """
        Calculate directional displacement component.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step: Sigma state step size
            
        Returns:
            Directional displacement series
        """
        # Calculate directional displacement
        # D = signed M normalized / clipped
        displacement = morphic_coordinates / step
        
        # Clip to reasonable range
        displacement = displacement.clip(-5, 5)
        
        return displacement
        
    def _calculate_volatility_expansion_ratio(self, morphic_coordinates: pd.Series) -> pd.Series:
        """
        Calculate volatility expansion ratio component.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            
        Returns:
            Volatility expansion ratio series
        """
        # Calculate volatility expansion ratio
        # V = sigma_fast / sigma_slow
        # For simplicity, we'll use a basic approximation
        # In a real implementation, this would use actual volatility estimates
        
        # Calculate rolling standard deviation
        vol_fast = morphic_coordinates.rolling(window=5).std()
        vol_slow = morphic_coordinates.rolling(window=20).std()
        
        # Calculate ratio
        expansion_ratio = vol_fast / vol_slow
        
        return expansion_ratio
        
    def _calculate_acceptance(self, morphic_coordinates: pd.Series,
                            step: float) -> pd.Series:
        """
        Calculate acceptance component.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step: Sigma state step size
            
        Returns:
            Acceptance series
        """
        # Calculate acceptance
        # A = occupancy beyond active boundary
        # For simplicity, we'll use a basic approximation
        # In a real implementation, this would use actual occupancy calculations
        
        # Calculate occupancy
        occupancy = self._calculate_occupancy(morphic_coordinates, step, 1)
        
        return occupancy
        
    def _calculate_persistence(self, morphic_coordinates: pd.Series,
                             step: float) -> pd.Series:
        """
        Calculate persistence component.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step: Sigma state step size
            
        Returns:
            Persistence series
        """
        # Calculate persistence
        # P = 1 - retracement_fraction
        # For simplicity, we'll use a basic approximation
        # In a real implementation, this would use actual persistence calculations
        
        # Calculate retracement fraction
        # For simplicity, we'll use a fixed value
        retracement_fraction = 0.5  # Placeholder
        
        persistence = 1 - retracement_fraction
        
        return pd.Series(persistence, index=morphic_coordinates.index)
        
    def _calculate_state_progression_quality(self, morphic_coordinates: pd.Series,
                                           step: float) -> pd.Series:
        """
        Calculate state progression quality component.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step: Sigma state step size
            
        Returns:
            State progression quality series
        """
        # Calculate state progression quality
        # Q = number of accepted same-direction sigma transitions
        # minus number of reclaimed states
        # For simplicity, we'll use a basic approximation
        # In a real implementation, this would use actual state progression calculations
        
        # Calculate state transitions
        state_transitions = morphic_coordinates.diff().abs() > step
        
        # Calculate quality
        quality = state_transitions.sum() / len(morphic_coordinates)
        
        return pd.Series(quality, index=morphic_coordinates.index)
        
    def generate_all_signals(self, morphic_coordinates: pd.Series,
                           step: float = 1.0,
                           n: int = 1,
                           weights: Dict[str, float] = None) -> Dict[str, pd.Series]:
        """
        Generate all signal types for a given set of parameters.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step: Sigma state step size
            n: Sigma state level
            weights: Dictionary of weights for trend score
            
        Returns:
            Dictionary with signal types as keys and signal series as values
        """
        signals = {}
        
        # Generate sigma escape signals
        signals['sigma_escape'] = self.generate_sigma_escape_signals(
            morphic_coordinates, step, n
        )
        
        # Generate accepted sigma breakout signals
        signals['accepted_sigma_breakout'] = self.generate_accepted_sigma_breakout_signals(
            morphic_coordinates, step, n
        )
        
        # Generate recursive morphic trend signals
        signals['recursive_morphic_trend'] = self.generate_recursive_morphic_trend_signals(
            morphic_coordinates, step, n
        )
        
        # Generate morphic trend score signals
        signals['morphic_trend_score'] = self.generate_morphic_trend_score_signals(
            morphic_coordinates, step, weights
        )
        
        return signals
        
    def combine_signals(self, signals: Dict[str, pd.Series],
                       weights: Dict[str, float] = None) -> pd.Series:
        """
        Combine multiple signals into a single signal.
        
        Args:
            signals: Dictionary with signal types as keys and signal series as values
            weights: Dictionary of weights for each signal type
            
        Returns:
            Combined signal series
        """
        if weights is None:
            # Equal weights
            weights = {name: 1.0 / len(signals) for name in signals.keys()}
            
        # Initialize combined signal series
        combined_signal = pd.Series(0, index=signals[list(signals.keys())[0]].index)
        
        # Combine signals
        for name, signal in signals.items():
            combined_signal += weights[name] * signal
            
        # Generate final signal based on combined signal
        final_signal = pd.Series(0, index=combined_signal.index)
        
        for i in range(len(combined_signal)):
            if combined_signal.iloc[i] > 0.5:  # Threshold for long signal
                final_signal.iloc[i] = 1
            elif combined_signal.iloc[i] < -0.5:  # Threshold for short signal
                final_signal.iloc[i] = -1
                
        return final_signal