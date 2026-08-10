"""
Acceptance Criteria for CEREBUS Morphic Volatility Engine

This module implements the acceptance criteria used in the MVE research
to determine when sigma states become "accepted" territory for trading.

Acceptance is a key concept in the MVE framework, distinguishing between
sigma touches and sigma state occupation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

class AcceptanceCriteria:
    """
    Acceptance criteria for sigma state occupation in MVE research.
    
    This class implements the acceptance criteria used to determine when
sigma states become "accepted" territory, distinguishing between
sigma touches and sigma state occupation.
    """
    
    def __init__(self, step_sizes: List[float] = None):
        """
        Initialize acceptance criteria calculator.
        
        Args:
            step_sizes: List of sigma state step sizes to test
        """
        if step_sizes is None:
            step_sizes = [0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0]
        self.step_sizes = step_sizes
        self.acceptance_criteria = {}
        
    def calculate_occupancy(self, morphic_coordinates: pd.Series,
                           step: float = 1.0, n: int = 1,
                           n_bars: int = 3) -> pd.Series:
        """
        Calculate occupancy beyond sigma state.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step: Sigma state step size
            n: Sigma state level
            n_bars: Number of bars for occupancy calculation
            
        Returns:
            Occupancy series
        """
        # Calculate sigma state boundary
        boundary = n * step
        
        # Initialize occupancy series
        occupancy = pd.Series(0.0, index=morphic_coordinates.index)
        
        # Calculate occupancy for each bar
        for i in range(len(morphic_coordinates)):
            if i >= n_bars - 1:
                # Get the window of bars
                window_coords = morphic_coordinates.iloc[max(0, i - n_bars + 1):i + 1]
                
                # Count bars above boundary
                above_boundary_count = sum(abs(window_coords) > boundary)
                
                # Calculate occupancy ratio
                occupancy.iloc[i] = above_boundary_count / n_bars
                
        return occupancy
        
    def calculate_all_occupancy(self, morphic_coordinates: pd.Series,
                               step_sizes: List[float] = None,
                               n_values: List[int] = None,
                               n_bars_values: List[int] = None) -> Dict:
        """
        Calculate occupancy for all step sizes and n values.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step_sizes: List of sigma state step sizes
            n_values: List of sigma state levels
            n_bars_values: List of bar window sizes
            
        Returns:
            Dictionary with occupancy calculations
        """
        if step_sizes is None:
            step_sizes = self.step_sizes
        if n_values is None:
            n_values = [1]
        if n_bars_values is None:
            n_bars_values = [3, 5, 8, 12]
            
        all_occupancy = {}
        
        for step in step_sizes:
            for n in n_values:
                for n_bars in n_bars_values:
                    key = f'step_{step}_n_{n}_bars_{n_bars}'
                    occupancy = self.calculate_occupancy(morphic_coordinates, step, n, n_bars)
                    all_occupancy[key] = occupancy
                    
        self.acceptance_criteria = all_occupancy
        return all_occupancy
        
    def classify_acceptance(self, occupancy: pd.Series,
                           acceptance_thresholds: List[float] = None) -> pd.Series:
        """
        Classify acceptance based on occupancy thresholds.
        
        Args:
            occupancy: Occupancy series
            acceptance_thresholds: List of acceptance thresholds
            
        Returns:
            Acceptance classification series
        """
        if acceptance_thresholds is None:
            acceptance_thresholds = [0.5, 0.6, 0.66, 0.75, 0.8]
            
        # Initialize acceptance series
        acceptance = pd.Series(0, index=occupancy.index)
        
        # Classify acceptance based on thresholds
        for i in range(len(occupancy)):
            occ = occupancy.iloc[i]
            
            if occ >= 0.8:
                acceptance.iloc[i] = 5  # 80%+
            elif occ >= 0.75:
                acceptance.iloc[i] = 4  # 75-79%
            elif occ >= 0.66:
                acceptance.iloc[i] = 3  # 66-74%
            elif occ >= 0.6:
                acceptance.iloc[i] = 2  # 60-65%
            elif occ >= 0.5:
                acceptance.iloc[i] = 1  # 50-59%
            else:
                acceptance.iloc[i] = 0  # <50%
                
        return acceptance
        
    def analyze_acceptance_statistics(self, occupancy: pd.Series,
                                    acceptance: pd.Series) -> Dict:
        """
        Analyze acceptance statistics.
        
        Args:
            occupancy: Occupancy series
            acceptance: Acceptance classification series
            
        Returns:
            Dictionary with acceptance statistics
        """
        # Calculate basic statistics
        stats_dict = {
            'occupancy_mean': occupancy.mean(),
            'occupancy_std': occupancy.std(),
            'occupancy_min': occupancy.min(),
            'occupancy_max': occupancy.max(),
            'occupancy_median': occupancy.median(),
            'acceptance_levels': {},
            'acceptance_counts': {},
            'acceptance_percentages': {}
        }
        
        # Calculate acceptance level statistics
        for level in range(6):  # 0-5
            level_occupancy = occupancy[acceptance == level]
            
            if len(level_occupancy) > 0:
                stats_dict['acceptance_levels'][level] = {
                    'mean_occupancy': level_occupancy.mean(),
                    'std_occupancy': level_occupancy.std(),
                    'min_occupancy': level_occupancy.min(),
                    'max_occupancy': level_occupancy.max(),
                    'median_occupancy': level_occupancy.median(),
                    'count': len(level_occupancy)
                }
            else:
                stats_dict['acceptance_levels'][level] = {
                    'mean_occupancy': np.nan,
                    'std_occupancy': np.nan,
                    'min_occupancy': np.nan,
                    'max_occupancy': np.nan,
                    'median_occupancy': np.nan,
                    'count': 0
                }
                
        # Calculate acceptance counts and percentages
        total_bars = len(acceptance)
        for level in range(6):
            level_count = (acceptance == level).sum()
            stats_dict['acceptance_counts'][level] = level_count
            stats_dict['acceptance_percentages'][level] = level_count / total_bars * 100
            
        return stats_dict
        
    def analyze_acceptance_forward_returns(self, occupancy: pd.Series,
                                         acceptance: pd.Series,
                                         prices: pd.Series,
                                         horizons: List[int] = None) -> Dict:
        """
        Analyze forward returns for different acceptance levels.
        
        Args:
            occupancy: Occupancy series
            acceptance: Acceptance classification series
            prices: Price series
            horizons: List of forward horizons to analyze
            
        Returns:
            Dictionary with forward return analysis
        """
        if horizons is None:
            horizons = [1, 3, 6, 12, 24, 48]  # Default horizons
            
        forward_return_analysis = {}
        
        for level in range(6):  # 0-5
            level_indices = acceptance[acceptance == level].index
            
            if len(level_indices) == 0:
                forward_return_analysis[level] = {
                    'horizons': {},
                    'mean_return': {},
                    'std_return': {},
                    'median_return': {},
                    'count': 0
                }
                continue
                
            # Calculate forward returns for each horizon
            horizon_returns = {}
            horizon_means = {}
            horizon_stds = {}
            horizon_medians = {}
            
            for horizon in horizons:
                # Calculate returns for this horizon
                returns = []
                for idx in level_indices:
                    if idx + horizon < len(prices):
                        ret = np.log(prices.iloc[idx + horizon] / prices.iloc[idx])
                        returns.append(ret)
                        
                if len(returns) > 0:
                    horizon_returns[str(horizon)] = returns
                    horizon_means[str(horizon)] = np.mean(returns)
                    horizon_stds[str(horizon)] = np.std(returns)
                    horizon_medians[str(horizon)] = np.median(returns)
                else:
                    horizon_returns[str(horizon)] = []
                    horizon_means[str(horizon)] = np.nan
                    horizon_stds[str(horizon)] = np.nan
                    horizon_medians[str(horizon)] = np.nan
                    
            forward_return_analysis[level] = {
                'horizons': horizon_returns,
                'mean_return': horizon_means,
                'std_return': horizon_stds,
                'median_return': horizon_medians,
                'count': len(level_indices)
            }
            
        return forward_return_analysis
        
    def analyze_acceptance_regime_effects(self, occupancy: pd.Series,
                                        acceptance: pd.Series,
                                        regimes: pd.Series) -> Dict:
        """
        Analyze regime effects on acceptance.
        
        Args:
            occupancy: Occupancy series
            acceptance: Acceptance classification series
            regimes: Volatility regime classifications
            
        Returns:
            Dictionary with regime effects analysis
        """
        regime_analysis = {}
        
        for level in range(6):  # 0-5
            level_indices = acceptance[acceptance == level].index
            
            if len(level_indices) == 0:
                regime_analysis[level] = {
                    'regime_effects': {},
                    'count': 0
                }
                continue
                
            # Calculate regime effects
            regime_effects = {}
            
            for regime in ['CONTRACTION', 'NORMAL', 'EXPANSION']:
                regime_level_indices = [idx for idx in level_indices 
                                      if regimes.loc[idx] == regime]
                
                if len(regime_level_indices) > 0:
                    regime_effects[regime] = {
                        'count': len(regime_level_indices),
                        'percentage': len(regime_level_indices) / len(level_indices) * 100
                    }
                else:
                    regime_effects[regime] = {
                        'count': 0,
                        'percentage': 0
                    }
                    
            regime_analysis[level] = {
                'regime_effects': regime_effects,
                'count': len(level_indices)
            }
            
        return regime_analysis
        
    def calculate_rebalancing_fraction(self, prices: pd.Series,
                                      acceptance: pd.Series) -> pd.Series:
        """
        Calculate rebalancing fraction for accepted sigma states.
        
        Args:
            prices: Price series
            acceptance: Acceptance classification series
            
        Returns:
            Rebalancing fraction series
        """
        # Initialize rebalancing fraction series
        rebalancing = pd.Series(0.0, index=prices.index)
        
        # Calculate rebalancing fraction for each bar
        for i in range(len(prices)):
            if acceptance.iloc[i] > 0:  # If accepted
                # Calculate impulse
                if i > 0:
                    impulse = np.log(prices.iloc[i] / prices.iloc[i - 1])
                else:
                    impulse = 0
                    
                # Calculate rebalancing fraction
                # For simplicity, we'll use a fixed formula
                # In a real implementation, this would be more sophisticated
                rebalancing.iloc[i] = min(abs(impulse) / 10.0, 1.0)  # Cap at 1.0
                
        return rebalancing
        
    def analyze_rebalancing_effects(self, rebalancing: pd.Series,
                                  acceptance: pd.Series,
                                  prices: pd.Series) -> Dict:
        """
        Analyze effects of rebalancing on forward returns.
        
        Args:
            rebalancing: Rebalancing fraction series
            acceptance: Acceptance classification series
            prices: Price series
            
        Returns:
            Dictionary with rebalancing effects analysis
        """
        # Calculate forward returns for different rebalancing levels
        rebalancing_levels = {}
        
        for level in range(6):  # 0-5
            level_indices = acceptance[acceptance == level].index
            
            if len(level_indices) == 0:
                rebalancing_levels[level] = {
                    'mean_rebalancing': np.nan,
                    'mean_return': np.nan,
                    'std_return': np.nan,
                    'count': 0
                }
                continue
                
            # Calculate average rebalancing for this level
            level_rebalancing = rebalancing.loc[level_indices]
            avg_rebalancing = level_rebalancing.mean()
            
            # Calculate forward returns
            forward_returns = []
            for idx in level_indices:
                if idx + 1 < len(prices):
                    ret = np.log(prices.iloc[idx + 1] / prices.iloc[idx])
                    forward_returns.append(ret)
                    
            if len(forward_returns) > 0:
                rebalancing_levels[level] = {
                    'mean_rebalancing': avg_rebalancing,
                    'mean_return': np.mean(forward_returns),
                    'std_return': np.std(forward_returns),
                    'count': len(forward_returns)
                }
            else:
                rebalancing_levels[level] = {
                    'mean_rebalancing': np.nan,
                    'mean_return': np.nan,
                    'std_return': np.nan,
                    'count': 0
                }
                
        return rebalancing_levels
        
    def analyze_acceptance_buckets(self, acceptance: pd.Series,
                                 prices: pd.Series) -> Dict:
        """
        Analyze CEREBUS-inspired acceptance buckets.
        
        Args:
            acceptance: Acceptance classification series
            prices: Price series
            
        Returns:
            Dictionary with bucket analysis
        """
        # Define CEREBUS-inspired buckets
        buckets = {
            'shallow': (0, 0.382),
            'normal': (0.382, 0.5),
            'moderate': (0.5, 0.618),
            'deep': (0.618, 0.786),
            'extreme': (0.786, 1.0)
        }
        
        bucket_analysis = {}
        
        for bucket_name, (lower, upper) in buckets.items():
            # Find bars in this bucket
            bucket_indices = acceptance[
                (acceptance >= lower) & (acceptance <= upper)
            ].index
            
            if len(bucket_indices) > 0:
                # Calculate forward returns
                forward_returns = []
                for idx in bucket_indices:
                    if idx + 1 < len(prices):
                        ret = np.log(prices.iloc[idx + 1] / prices.iloc[idx])
                        forward_returns.append(ret)
                        
                if len(forward_returns) > 0:
                    bucket_analysis[bucket_name] = {
                        'mean_return': np.mean(forward_returns),
                        'std_return': np.std(forward_returns),
                        'median_return': np.median(forward_returns),
                        'count': len(forward_returns),
                        'percentage': len(bucket_indices) / len(acceptance) * 100
                    }
                else:
                    bucket_analysis[bucket_name] = {
                        'mean_return': np.nan,
                        'std_return': np.nan,
                        'median_return': np.nan,
                        'count': 0,
                        'percentage': 0
                    }
            else:
                bucket_analysis[bucket_name] = {
                    'mean_return': np.nan,
                    'std_return': np.nan,
                    'median_return': np.nan,
                    'count': 0,
                    'percentage': 0
                }
                
        return bucket_analysis
        
    def analyze_acceptance_quality(self, acceptance: pd.Series) -> Dict:
        """
        Analyze quality of acceptance criteria.
        
        Args:
            acceptance: Acceptance classification series
            
        Returns:
            Dictionary with acceptance quality metrics
        """
        # Calculate basic statistics
        stats_dict = {
            'mean': acceptance.mean(),
            'std': acceptance.std(),
            'min': acceptance.min(),
            'max': acceptance.max(),
            'median': acceptance.median(),
            'skewness': acceptance.skew(),
            'kurtosis': acceptance.kurtosis()
        }
        
        return stats_dict
        
    def get_best_acceptance_levels(self, acceptance: pd.Series,
                                  min_count: int = 10) -> List[int]:
        """
        Get the best acceptance levels based on data count.
        
        Args:
            acceptance: Acceptance classification series
            min_count: Minimum number of bars required
            
        Returns:
            List of best acceptance levels
        """
        # Get acceptance levels with sufficient data
        level_counts = acceptance.value_counts()
        
        # Filter by minimum count
        valid_levels = level_counts[level_counts >= min_count].index.tolist()
        
        # Sort by level (higher levels are better)
        valid_levels.sort(reverse=True)
        
        return valid_levels