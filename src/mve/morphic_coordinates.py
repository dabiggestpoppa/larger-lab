"""
Morphic Sigma Coordinates for CEREBUS Morphic Volatility Engine

This module implements the core morphic sigma coordinate calculations
used in the MVE research. The morphic sigma coordinate represents
the displacement of price from a structural anchor, normalized by
volatility and time horizon.

The formula is:
M_t = ln(P_t / A_t) / (sigma_t * sqrt(tau))

Where:
- P_t = current price
- A_t = structural anchor value at time t
- sigma_t = volatility estimator at time t
- tau = elapsed normalized horizon
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

class MorphicCoordinates:
    """
    Calculate morphic sigma coordinates for MVE research.
    
    This class implements the core morphic sigma coordinate calculations
    used to analyze sigma state persistence and trend continuation.
    """
    
    def __init__(self, time_horizon: float = 1.0):
        """
        Initialize morphic coordinates calculator.
        
        Args:
            time_horizon: Time horizon normalization factor (tau)
        """
        self.time_horizon = time_horizon
        self.coordinates = {}
        
    def calculate_morphic_coordinates(self, prices: pd.Series, anchors: pd.Series,
                                     volatility_estimators: Dict[str, pd.Series],
                                     estimator_name: str = 'close_to_close') -> pd.Series:
        """
        Calculate morphic sigma coordinates for a given volatility estimator.
        
        Args:
            prices: Price series
            anchors: Anchor values
            volatility_estimators: Dictionary of volatility estimators
            estimator_name: Name of volatility estimator to use
            
        Returns:
            Morphic sigma coordinates
        """
        if estimator_name not in volatility_estimators:
            raise ValueError(f"Volatility estimator '{estimator_name}' not found")
            
        volatility = volatility_estimators[estimator_name]
        
        # Calculate morphic coordinates
        # M_t = ln(P_t / A_t) / (sigma_t * sqrt(tau))
        displacement = np.log(prices / anchors)
        normalized_volatility = volatility * np.sqrt(self.time_horizon)
        
        # Avoid division by zero
        normalized_volatility = normalized_volatility.replace(0, np.nan)
        
        morphic_coords = displacement / normalized_volatility
        
        self.coordinates[estimator_name] = morphic_coords
        return morphic_coords
        
    def calculate_live_frozen_coordinates(self, prices: pd.Series, anchors: pd.Series,
                                         volatility_estimators: Dict[str, pd.Series],
                                         estimator_name: str = 'close_to_close') -> Tuple[pd.Series, pd.Series]:
        """
        Calculate both live and frozen morphic sigma coordinates.
        
        Args:
            prices: Price series
            anchors: Anchor values
            volatility_estimators: Dictionary of volatility estimators
            estimator_name: Name of volatility estimator to use
            
        Returns:
            Tuple of (live_coordinates, frozen_coordinates)
        """
        if estimator_name not in volatility_estimators:
            raise ValueError(f"Volatility estimator '{estimator_name}' not found")
            
        volatility = volatility_estimators[estimator_name]
        
        # Calculate live coordinates
        live_displacement = np.log(prices / anchors)
        live_normalized_vol = volatility * np.sqrt(self.time_horizon)
        live_normalized_vol = live_normalized_vol.replace(0, np.nan)
        live_coordinates = live_displacement / live_normalized_vol
        
        # Calculate frozen coordinates
        # Use first non-NaN volatility as sigma*
        valid_vol = volatility.dropna()
        if len(valid_vol) > 0:
            sigma_star = valid_vol.iloc[0]
            frozen_normalized_vol = sigma_star * np.sqrt(self.time_horizon)
            frozen_coordinates = live_displacement / frozen_normalized_vol
        else:
            frozen_coordinates = pd.Series(np.nan, index=prices.index)
            
        self.coordinates[f'{estimator_name}_live'] = live_coordinates
        self.coordinates[f'{estimator_name}_frozen'] = frozen_coordinates
        
        return live_coordinates, frozen_coordinates
        
    def calculate_volatility_expansion_ratio(self, live_volatility: pd.Series,
                                           frozen_volatility: float) -> pd.Series:
        """
        Calculate volatility expansion ratio.
        
        Args:
            live_volatility: Live volatility series
            frozen_volatility: Frozen volatility value (sigma*)
            
        Returns:
            Volatility expansion ratio
        """
        # C_t = sigma_live(t) / sigma_frozen
        expansion_ratio = live_volatility / frozen_volatility
        return expansion_ratio
        
    def classify_volatility_regimes(self, expansion_ratios: pd.Series,
                                   contraction_threshold: float = 0.80,
                                   expansion_threshold: float = 1.20) -> pd.Series:
        """
        Classify volatility regimes based on expansion ratios.
        
        Args:
            expansion_ratios: Volatility expansion ratios
            contraction_threshold: Threshold for contraction regime
            expansion_threshold: Threshold for expansion regime
            
        Returns:
            Volatility regime classifications
        """
        regimes = pd.Series(index=expansion_ratios.index)
        
        # Classify regimes
        regimes[expansion_ratios < contraction_threshold] = 'CONTRACTION'
        regimes[(expansion_ratios >= contraction_threshold) & 
               (expansion_ratios <= expansion_threshold)] = 'NORMAL'
        regimes[expansion_ratios > expansion_threshold] = 'EXPANSION'
        
        return regimes
        
    def calculate_sigma_states(self, morphic_coordinates: pd.Series,
                             step: float = 1.0) -> pd.Series:
        """
        Calculate sigma states from morphic coordinates.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step: Sigma state step size
            
        Returns:
            Sigma states
        """
        # S_t = sign(M_t) * floor(|M_t| / step)
        states = np.sign(morphic_coordinates) * np.floor(np.abs(morphic_coordinates) / step)
        return pd.Series(states, index=morphic_coordinates.index)
        
    def analyze_coordinate_statistics(self, coordinates: pd.Series) -> Dict:
        """
        Analyze statistics of morphic coordinates.
        
        Args:
            coordinates: Morphic sigma coordinates
            
        Returns:
            Dictionary with coordinate statistics
        """
        # Remove NaN values
        valid_coords = coordinates.dropna()
        
        if len(valid_coords) == 0:
            return {
                'mean': np.nan,
                'std': np.nan,
                'min': np.nan,
                'max': np.nan,
                'median': np.nan,
                'skewness': np.nan,
                'kurtosis': np.nan,
                'percentiles': {}
            }
            
        # Calculate basic statistics
        stats_dict = {
            'mean': valid_coords.mean(),
            'std': valid_coords.std(),
            'min': valid_coords.min(),
            'max': valid_coords.max(),
            'median': valid_coords.median(),
            'skewness': valid_coords.skew(),
            'kurtosis': valid_coords.kurtosis()
        }
        
        # Calculate percentiles
        percentiles = {}
        for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
            percentiles[f'p{p}'] = valid_coords.quantile(p / 100)
            
        stats_dict['percentiles'] = percentiles
        
        return stats_dict
        
    def calculate_coordinate_persistence(self, coordinates: pd.Series,
                                        max_lag: int = 10) -> Dict:
        """
        Calculate persistence of morphic coordinates.
        
        Args:
            coordinates: Morphic sigma coordinates
            max_lag: Maximum lag for autocorrelation calculation
            
        Returns:
            Dictionary with persistence statistics
        """
        persistence = {}
        
        for lag in range(1, max_lag + 1):
            autocorr = coordinates.autocorr(lag=lag)
            persistence[f'lag_{lag}'] = autocorr
            
        return persistence
        
    def analyze_coordinate_regimes(self, coordinates: pd.Series,
                                 regimes: pd.Series) -> Dict:
        """
        Analyze morphic coordinates by regime.
        
        Args:
            coordinates: Morphic sigma coordinates
            regimes: Volatility regime classifications
            
        Returns:
            Dictionary with regime analysis results
        """
        regime_analysis = {}
        
        for regime in ['CONTRACTION', 'NORMAL', 'EXPANSION']:
            regime_coords = coordinates[regimes == regime]
            
            if len(regime_coords) > 0:
                regime_analysis[regime] = {
                    'mean': regime_coords.mean(),
                    'std': regime_coords.std(),
                    'min': regime_coords.min(),
                    'max': regime_coords.max(),
                    'median': regime_coords.median(),
                    'count': len(regime_coords),
                    'percentage': len(regime_coords) / len(coordinates) * 100
                }
            else:
                regime_analysis[regime] = {
                    'mean': np.nan,
                    'std': np.nan,
                    'min': np.nan,
                    'max': np.nan,
                    'median': np.nan,
                    'count': 0,
                    'percentage': 0
                }
                
        return regime_analysis
        
    def calculate_coordinate_transitions(self, coordinates: pd.Series,
                                        step: float = 1.0) -> Dict:
        """
        Calculate transitions between sigma states.
        
        Args:
            coordinates: Morphic sigma coordinates
            step: Sigma state step size
            
        Returns:
            Dictionary with transition probabilities
        """
        # Calculate sigma states
        states = self.calculate_sigma_states(coordinates, step)
        
        # Count transitions
        transitions = {}
        
        for i in range(len(states) - 1):
            current_state = states.iloc[i]
            next_state = states.iloc[i + 1]
            
            if current_state not in transitions:
                transitions[current_state] = {}
                
            if next_state not in transitions[current_state]:
                transitions[current_state][next_state] = 0
                
            transitions[current_state][next_state] += 1
            
        # Convert to probabilities
        transition_probs = {}
        for current_state, next_counts in transitions.items():
            total = sum(next_counts.values())
            transition_probs[current_state] = {
                next_state: count / total
                for next_state, count in next_counts.items()
            }
            
        return transition_probs
        
    def analyze_coordinate_trends(self, coordinates: pd.Series,
                                 prices: pd.Series) -> Dict:
        """
        Analyze trends in morphic coordinates.
        
        Args:
            coordinates: Morphic sigma coordinates
            prices: Price series
            
        Returns:
            Dictionary with trend analysis results
        """
        # Calculate forward returns
        forward_returns = np.log(prices.shift(-1) / prices)
        
        # Group by coordinate sign
        positive_coords = coordinates > 0
        negative_coords = coordinates < 0
        
        trend_analysis = {}
        
        # Analyze positive coordinates
        if positive_coords.any():
            pos_returns = forward_returns[positive_coords]
            trend_analysis['positive'] = {
                'mean_return': pos_returns.mean(),
                'std_return': pos_returns.std(),
                'median_return': pos_returns.median(),
                'count': len(pos_returns)
            }
        else:
            trend_analysis['positive'] = {
                'mean_return': np.nan,
                'std_return': np.nan,
                'median_return': np.nan,
                'count': 0
            }
            
        # Analyze negative coordinates
        if negative_coords.any():
            neg_returns = forward_returns[negative_coords]
            trend_analysis['negative'] = {
                'mean_return': neg_returns.mean(),
                'std_return': neg_returns.std(),
                'median_return': neg_returns.median(),
                'count': len(neg_returns)
            }
        else:
            trend_analysis['negative'] = {
                'mean_return': np.nan,
                'std_return': np.nan,
                'median_return': np.nan,
                'count': 0
            }
            
        return trend_analysis