"""
Volatility Regime Model for CEREBUS Morphic Volatility Engine

This module implements the volatility × displacement regime model used in the MVE research.
The model constructs a two-dimensional state map combining absolute normalized displacement
and volatility expansion ratio to identify meaningful market regimes.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

class VolatilityRegimeModel:
    """
    Volatility × displacement regime model for MVE research.
    
    This class implements the two-dimensional state map combining absolute normalized
    displacement and volatility expansion ratio to identify meaningful market regimes.
    """
    
    def __init__(self, displacement_step: float = 1.0, expansion_thresholds: List[float] = None):
        """
        Initialize volatility regime model.
        
        Args:
            displacement_step: Step size for displacement classification
            expansion_thresholds: List of expansion thresholds for regime classification
        """
        self.displacement_step = displacement_step
        if expansion_thresholds is None:
            expansion_thresholds = [0.80, 1.20]
        self.expansion_thresholds = expansion_thresholds
        self.regime_model = {}
        
    def classify_displacement_regime(self, displacement: pd.Series) -> pd.Series:
        """
        Classify displacement regime based on absolute normalized displacement.
        
        Args:
            displacement: Absolute normalized displacement
            
        Returns:
            Displacement regime classifications
        """
        regimes = pd.Series(index=displacement.index)
        
        # Classify based on displacement magnitude
        regimes[displacement < self.displacement_step] = 'LOW_DISPLACEMENT'
        regimes[displacement >= self.displacement_step] = 'HIGH_DISPLACEMENT'
        
        return regimes
        
    def classify_expansion_regime(self, expansion_ratios: pd.Series) -> pd.Series:
        """
        Classify expansion regime based on volatility expansion ratios.
        
        Args:
            expansion_ratios: Volatility expansion ratios
            
        Returns:
            Expansion regime classifications
        """
        regimes = pd.Series(index=expansion_ratios.index)
        
        # Classify based on expansion ratio
        regimes[expansion_ratios < self.expansion_thresholds[0]] = 'CONTRACTION'
        regimes[(expansion_ratios >= self.expansion_thresholds[0]) & 
               (expansion_ratios <= self.expansion_thresholds[1])] = 'NORMAL'
        regimes[expansion_ratios > self.expansion_thresholds[1]] = 'EXPANSION'
        
        return regimes
        
    def create_two_dimensional_state_map(self, displacement: pd.Series,
                                        expansion_ratios: pd.Series) -> pd.DataFrame:
        """
        Create two-dimensional state map combining displacement and expansion regimes.
        
        Args:
            displacement: Absolute normalized displacement
            expansion_ratios: Volatility expansion ratios
            
        Returns:
            DataFrame with two-dimensional state classifications
        """
        # Classify both dimensions
        displacement_regimes = self.classify_displacement_regime(displacement)
        expansion_regimes = self.classify_expansion_regime(expansion_ratios)
        
        # Create DataFrame
        state_map = pd.DataFrame({
            'displacement_regime': displacement_regimes,
            'expansion_regime': expansion_regimes
        })
        
        # Create combined state
        state_map['combined_state'] = (
            state_map['displacement_regime'] + '_' + state_map['expansion_regime']
        )
        
        return state_map
        
    def analyze_regime_transitions(self, state_map: pd.DataFrame) -> Dict:
        """
        Analyze transitions between regimes in the two-dimensional state map.
        
        Args:
            state_map: DataFrame with two-dimensional state classifications
            
        Returns:
            Dictionary with transition probabilities
        """
        transitions = {}
        
        # Count transitions
        for i in range(len(state_map) - 1):
            current_state = state_map.iloc[i]['combined_state']
            next_state = state_map.iloc[i + 1]['combined_state']
            
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
        
    def analyze_regime_persistence(self, state_map: pd.DataFrame) -> Dict:
        """
        Analyze persistence of regimes in the two-dimensional state map.
        
        Args:
            state_map: DataFrame with two-dimensional state classifications
            
        Returns:
            Dictionary with persistence statistics
        """
        persistence = {}
        
        # Calculate persistence for each combined state
        for state in state_map['combined_state'].unique():
            state_data = state_map[state_map['combined_state'] == state]
            
            if len(state_data) > 0:
                # Calculate persistence (percentage of consecutive same-state transitions)
                same_state_transitions = 0
                total_transitions = 0
                
                for i in range(len(state_data) - 1):
                    current_state = state_data.iloc[i]['combined_state']
                    next_state = state_data.iloc[i + 1]['combined_state']
                    
                    if current_state == next_state:
                        same_state_transitions += 1
                    total_transitions += 1
                    
                persistence_rate = same_state_transitions / total_transitions if total_transitions > 0 else 0
                
                persistence[state] = {
                    'persistence_rate': persistence_rate,
                    'duration_mean': len(state_data) / len(state_map) * 100,
                    'count': len(state_data)
                }
            else:
                persistence[state] = {
                    'persistence_rate': 0,
                    'duration_mean': 0,
                    'count': 0
                }
                
        return persistence
        
    def analyze_regime_specific_behavior(self, state_map: pd.DataFrame,
                                        morphic_coordinates: pd.Series,
                                        prices: pd.Series) -> Dict:
        """
        Analyze behavior specific to each regime.
        
        Args:
            state_map: DataFrame with two-dimensional state classifications
            morphic_coordinates: Morphic sigma coordinates
            prices: Price series
            
        Returns:
            Dictionary with regime-specific behavior analysis
        """
        regime_analysis = {}
        
        for state in state_map['combined_state'].unique():
            state_data = state_map[state_map['combined_state'] == state]
            
            if len(state_data) > 0:
                # Calculate forward returns for this regime
                forward_returns = []
                for idx in state_data.index:
                    if idx + 1 < len(prices):
                        ret = np.log(prices.iloc[idx + 1] / prices.iloc[idx])
                        forward_returns.append(ret)
                        
                if len(forward_returns) > 0:
                    regime_analysis[state] = {
                        'mean_return': np.mean(forward_returns),
                        'std_return': np.std(forward_returns),
                        'median_return': np.median(forward_returns),
                        'count': len(forward_returns),
                        'percentage': len(state_data) / len(state_map) * 100
                    }
                else:
                    regime_analysis[state] = {
                        'mean_return': np.nan,
                        'std_return': np.nan,
                        'median_return': np.nan,
                        'count': 0,
                        'percentage': 0
                    }
            else:
                regime_analysis[state] = {
                    'mean_return': np.nan,
                    'std_return': np.nan,
                    'median_return': np.nan,
                    'count': 0,
                    'percentage': 0
                }
                
        return regime_analysis
        
    def analyze_high_displacement_high_expansion(self, state_map: pd.DataFrame,
                                               morphic_coordinates: pd.Series,
                                               prices: pd.Series) -> Dict:
        """
        Analyze HIGH displacement + HIGH volatility expansion regime specifically.
        
        Args:
            state_map: DataFrame with two-dimensional state classifications
            morphic_coordinates: Morphic sigma coordinates
            prices: Price series
            
        Returns:
            Dictionary with HIGH displacement + HIGH expansion analysis
        """
        # Identify HIGH displacement + HIGH expansion regime
        high_displacement_high_expansion = state_map[
            (state_map['displacement_regime'] == 'HIGH_DISPLACEMENT') &
            (state_map['expansion_regime'] == 'EXPANSION')
        ]
        
        if len(high_displacement_high_expansion) == 0:
            return {
                'mean_return': np.nan,
                'std_return': np.nan,
                'median_return': np.nan,
                'count': 0,
                'percentage': 0,
                'persistence': np.nan
            }
            
        # Calculate forward returns
        forward_returns = []
        for idx in high_displacement_high_expansion.index:
            if idx + 1 < len(prices):
                ret = np.log(prices.iloc[idx + 1] / prices.iloc[idx])
                forward_returns.append(ret)
                
        # Calculate persistence
        persistence = 0
        total_transitions = 0
        
        for i in range(len(high_displacement_high_expansion) - 1):
            current_state = high_displacement_high_expansion.iloc[i]['combined_state']
            next_state = high_displacement_high_expansion.iloc[i + 1]['combined_state']
            
            if current_state == next_state:
                persistence += 1
            total_transitions += 1
            
        persistence_rate = persistence / total_transitions if total_transitions > 0 else 0
        
        return {
            'mean_return': np.mean(forward_returns) if forward_returns else np.nan,
            'std_return': np.std(forward_returns) if forward_returns else np.nan,
            'median_return': np.median(forward_returns) if forward_returns else np.nan,
            'count': len(forward_returns),
            'percentage': len(high_displacement_high_expansion) / len(state_map) * 100,
            'persistence': persistence_rate
        }
        
    def create_regime_heatmap(self, state_map: pd.DataFrame) -> pd.DataFrame:
        """
        Create regime transition heatmap.
        
        Args:
            state_map: DataFrame with two-dimensional state classifications
            
        Returns:
            DataFrame with transition probabilities for heatmap
        """
        # Calculate transition matrix
        transitions = self.analyze_regime_transitions(state_map)
        
        # Create pivot table for heatmap
        heatmap_data = pd.DataFrame(index=state_map['combined_state'].unique(),
                                   columns=state_map['combined_state'].unique(),
                                   dtype=float)
        
        for current_state, next_probs in transitions.items():
            for next_state, prob in next_probs.items():
                heatmap_data.loc[current_state, next_state] = prob
                
        return heatmap_data
        
    def analyze_regime_stability(self, state_map: pd.DataFrame) -> Dict:
        """
        Analyze stability of regimes over time.
        
        Args:
            state_map: DataFrame with two-dimensional state classifications
            
        Returns:
            Dictionary with regime stability analysis
        """
        stability = {}
        
        for state in state_map['combined_state'].unique():
            state_data = state_map[state_map['combined_state'] == state]
            
            if len(state_data) > 0:
                # Calculate stability metrics
                # 1. Duration stability (variance of state durations)
                # 2. Transition stability (variance of transition probabilities)
                # 3. Return stability (variance of forward returns)
                
                # For simplicity, we'll calculate basic stability metrics
                stability[state] = {
                    'duration_stability': 1.0 / (len(state_data) + 1),  # Inverse of duration
                    'transition_stability': 1.0,  # Placeholder
                    'return_stability': 1.0 / (len(state_data) + 1),  # Placeholder
                    'count': len(state_data),
                    'percentage': len(state_data) / len(state_map) * 100
                }
            else:
                stability[state] = {
                    'duration_stability': 0,
                    'transition_stability': 0,
                    'return_stability': 0,
                    'count': 0,
                    'percentage': 0
                }
                
        return stability