"""
Structural Anchors for the CEREBUS Morphic Volatility Engine (MVE)

This module implements 6 different structural anchor calculations with quality metrics,
providing multiple perspectives on market structure for sigma state analysis.
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks
from typing import Dict, List, Tuple, Optional, Union
import warnings
warnings.filterwarnings('ignore')

class StructuralAnchors:
    """
    Collection of structural anchor calculations for MVE research.
    
    This class implements 6 different structural anchor calculations:
    1. Pivot High/Low (local maxima/minima)
    2. Support/Resistance Levels (statistical levels)
    3. Trend Line Anchors (linear regression)
    4. Volume Profile Anchors (volume-based levels)
    5. Time-based Anchors (time-based levels)
    6. Volatility-based Anchors (volatility-based levels)
    
    Each anchor is evaluated for quality and can be used for sigma state analysis.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize structural anchors.
        
        Args:
            config: Configuration dictionary with anchor parameters
        """
        self.config = config or self._get_default_config()
        self.anchor_weights = self.config.get('anchor_weights', {})
        self.quality_metrics = {}
        
    def _get_default_config(self) -> Dict:
        """
        Get default configuration for structural anchors.
        
        Returns:
            Default configuration dictionary
        """
        return {
            'pivot_high_low': {
                'window': 5,
                'min_pivot_height': 0.01,
                'min_pivot_width': 3
            },
            'support_resistance': {
                'window': 20,
                'num_levels': 5,
                'percentile': 95
            },
            'trend_line': {
                'window': 20,
                'min_points': 3
            },
            'volume_profile': {
                'window': 20,
                'num_bins': 10,
                'volume_threshold': 0.1
            },
            'time_based': {
                'window': 20,
                'num_levels': 5
            },
            'volatility_based': {
                'window': 20,
                'num_levels': 5,
                'volatility_threshold': 0.5
            }
        }
        
    def calculate_all_anchors(self, prices: pd.Series, highs: pd.Series = None,
                             lows: pd.Series = None, volumes: pd.Series = None,
                             timestamps: pd.Series = None) -> Dict[str, pd.Series]:
        """
        Calculate all structural anchors.
        
        Args:
            prices: Price series (typically close prices)
            highs: High price series (optional)
            lows: Low price series (optional)
            volumes: Volume series (optional)
            timestamps: Timestamp series (optional)
            
        Returns:
            Dictionary with anchor names as keys and series as values
        """
        anchors = {}
        
        # Calculate each anchor
        anchors['pivot_high'] = self._calculate_pivot_high(prices)
        anchors['pivot_low'] = self._calculate_pivot_low(prices)
        anchors['support_levels'] = self._calculate_support_levels(prices)
        anchors['resistance_levels'] = self._calculate_resistance_levels(prices)
        anchors['trend_line'] = self._calculate_trend_line(prices)
        anchors['volume_profile'] = self._calculate_volume_profile(prices, volumes)
        anchors['time_based'] = self._calculate_time_based_anchors(prices, timestamps)
        anchors['volatility_based'] = self._calculate_volatility_based_anchors(prices)
        
        return anchors
        
    def _calculate_pivot_high(self, prices: pd.Series) -> pd.Series:
        """
        Calculate pivot high levels.
        
        Args:
            prices: Price series
            
        Returns:
            Pivot high levels series
        """
        window = self.config['pivot_high_low']['window']
        min_pivot_height = self.config['pivot_high_low']['min_pivot_height']
        min_pivot_width = self.config['pivot_high_low']['min_pivot_width']
        
        # Find pivot highs
        pivot_highs = pd.Series(index=prices.index, dtype=float)
        
        for i in range(window, len(prices) - window):
            # Check if current price is higher than surrounding prices
            if (prices.iloc[i] > prices.iloc[i-window:i] and 
                prices.iloc[i] > prices.iloc[i+1:i+window+1]):
                # Check pivot height
                pivot_height = (prices.iloc[i] - min(prices.iloc[i-window:i])) / prices.iloc[i]
                if pivot_height >= min_pivot_height:
                    pivot_highs.iloc[i] = prices.iloc[i]
                    
        return pivot_highs
        
    def _calculate_pivot_low(self, prices: pd.Series) -> pd.Series:
        """
        Calculate pivot low levels.
        
        Args:
            prices: Price series
            
        Returns:
            Pivot low levels series
        """
        window = self.config['pivot_high_low']['window']
        min_pivot_height = self.config['pivot_high_low']['min_pivot_height']
        min_pivot_width = self.config['pivot_high_low']['min_pivot_width']
        
        # Find pivot lows
        pivot_lows = pd.Series(index=prices.index, dtype=float)
        
        for i in range(window, len(prices) - window):
            # Check if current price is lower than surrounding prices
            if (prices.iloc[i] < prices.iloc[i-window:i] and 
                prices.iloc[i] < prices.iloc[i+1:i+window+1]):
                # Check pivot height
                pivot_height = (max(prices.iloc[i-window:i]) - prices.iloc[i]) / prices.iloc[i]
                if pivot_height >= min_pivot_height:
                    pivot_lows.iloc[i] = prices.iloc[i]
                    
        return pivot_lows
        
    def _calculate_support_levels(self, prices: pd.Series) -> pd.Series:
        """
        Calculate support levels.
        
        Args:
            prices: Price series
            
        Returns:
            Support levels series
        """
        window = self.config['support_resistance']['window']
        num_levels = self.config['support_resistance']['num_levels']
        percentile = self.config['support_resistance']['percentile']
        
        # Calculate rolling minimum
        rolling_min = prices.rolling(window=window, min_periods=window).min()
        
        # Calculate support levels as percentiles of rolling minimum
        support_levels = pd.Series(index=prices.index, dtype=float)
        
        for i in range(window, len(prices)):
            # Get recent prices
            recent_prices = prices.iloc[max(0, i-window):i+1]
            
            # Calculate support levels
            support_values = np.percentile(recent_prices, [100 - percentile] * num_levels)
            support_levels.iloc[i] = support_values[-1] if len(support_values) > 0 else np.nan
            
        return support_levels
        
    def _calculate_resistance_levels(self, prices: pd.Series) -> pd.Series:
        """
        Calculate resistance levels.
        
        Args:
            prices: Price series
            
        Returns:
            Resistance levels series
        """
        window = self.config['support_resistance']['window']
        num_levels = self.config['support_resistance']['num_levels']
        percentile = self.config['support_resistance']['percentile']
        
        # Calculate rolling maximum
        rolling_max = prices.rolling(window=window, min_periods=window).max()
        
        # Calculate resistance levels as percentiles of rolling maximum
        resistance_levels = pd.Series(index=prices.index, dtype=float)
        
        for i in range(window, len(prices)):
            # Get recent prices
            recent_prices = prices.iloc[max(0, i-window):i+1]
            
            # Calculate resistance levels
            resistance_values = np.percentile(recent_prices, [percentile] * num_levels)
            resistance_levels.iloc[i] = resistance_values[-1] if len(resistance_values) > 0 else np.nan
            
        return resistance_levels
        
    def _calculate_trend_line(self, prices: pd.Series) -> pd.Series:
        """
        Calculate trend line anchors.
        
        Args:
            prices: Price series
            
        Returns:
            Trend line anchors series
        """
        window = self.config['trend_line']['window']
        min_points = self.config['trend_line']['min_points']
        
        # Calculate linear regression trend line
        trend_line = pd.Series(index=prices.index, dtype=float)
        
        for i in range(window, len(prices)):
            # Get recent prices
            recent_prices = prices.iloc[i-window:i+1]
            recent_indices = np.arange(len(recent_prices))
            
            # Calculate linear regression
            if len(recent_prices) >= min_points:
                slope, intercept = np.polyfit(recent_indices, recent_prices, 1)
                trend_line.iloc[i] = slope * recent_indices[-1] + intercept
            else:
                trend_line.iloc[i] = np.nan
                
        return trend_line
        
    def _calculate_volume_profile(self, prices: pd.Series, volumes: pd.Series = None) -> pd.Series:
        """
        Calculate volume profile anchors.
        
        Args:
            prices: Price series
            volumes: Volume series (optional)
            
        Returns:
            Volume profile anchors series
        """
        if volumes is None:
            raise ValueError("Volume series is required for volume profile calculation")
            
        window = self.config['volume_profile']['window']
        num_bins = self.config['volume_profile']['num_bins']
        volume_threshold = self.config['volume_profile']['volume_threshold']
        
        # Calculate volume profile
        volume_profile = pd.Series(index=prices.index, dtype=float)
        
        for i in range(window, len(prices)):
            # Get recent prices and volumes
            recent_prices = prices.iloc[i-window:i+1]
            recent_volumes = volumes.iloc[i-window:i+1]
            
            # Calculate volume-weighted average price
            if recent_volumes.sum() > 0:
                vw_price = (recent_prices * recent_volumes).sum() / recent_volumes.sum()
                volume_profile.iloc[i] = vw_price
            else:
                volume_profile.iloc[i] = np.nan
                
        return volume_profile
        
    def _calculate_time_based_anchors(self, prices: pd.Series, timestamps: pd.Series = None) -> pd.Series:
        """
        Calculate time-based anchors.
        
        Args:
            prices: Price series
            timestamps: Timestamp series (optional)
            
        Returns:
            Time-based anchors series
        """
        window = self.config['time_based']['window']
        num_levels = self.config['time_based']['num_levels']
        
        # Calculate time-based anchors
        time_anchors = pd.Series(index=prices.index, dtype=float)
        
        for i in range(window, len(prices)):
            # Get recent prices
            recent_prices = prices.iloc[i-window:i+1]
            
            # Calculate time-based anchors as percentiles
            anchor_values = np.percentile(recent_prices, [100/num_levels * j for j in range(1, num_levels+1)])
            time_anchors.iloc[i] = anchor_values[-1] if len(anchor_values) > 0 else np.nan
            
        return time_anchors
        
    def _calculate_volatility_based_anchors(self, prices: pd.Series) -> pd.Series:
        """
        Calculate volatility-based anchors.
        
        Args:
            prices: Price series
            
        Returns:
            Volatility-based anchors series
        """
        window = self.config['volatility_based']['window']
        num_levels = self.config['volatility_based']['num_levels']
        volatility_threshold = self.config['volatility_based']['volatility_threshold']
        
        # Calculate rolling volatility
        returns = np.log(prices / prices.shift(1))
        rolling_volatility = returns.rolling(window=window, min_periods=window).std()
        
        # Calculate volatility-based anchors
        volatility_anchors = pd.Series(index=prices.index, dtype=float)
        
        for i in range(window, len(prices)):
            # Get recent volatility
            recent_volatility = rolling_volatility.iloc[i-window:i+1]
            
            # Calculate volatility-based anchors as percentiles
            anchor_values = np.percentile(recent_volatility, [100/num_levels * j for j in range(1, num_levels+1)])
            volatility_anchors.iloc[i] = anchor_values[-1] if len(anchor_values) > 0 else np.nan
            
        return volatility_anchors
        
    def evaluate_anchor_quality(self, anchors: Dict[str, pd.Series],
                               prices: pd.Series) -> Dict[str, Dict]:
        """
        Evaluate quality of structural anchors.
        
        Args:
            anchors: Dictionary of structural anchors
            prices: Price series
            
        Returns:
            Dictionary with quality metrics for each anchor
        """
        quality_metrics = {}
        
        for name, anchor in anchors.items():
            metrics = self._calculate_anchor_quality(anchor, prices)
            quality_metrics[name] = metrics
            
        return quality_metrics
        
    def _calculate_anchor_quality(self, anchor: pd.Series, prices: pd.Series) -> Dict:
        """
        Calculate quality metrics for a single structural anchor.
        
        Args:
            anchor: Anchor series
            prices: Price series
            
        Returns:
            Dictionary with quality metrics
        """
        # Remove NaN values
        valid_data = anchor.dropna()
        
        if len(valid_data) == 0:
            return {
                'mean': np.nan,
                'std': np.nan,
                'skewness': np.nan,
                'kurtosis': np.nan,
                'autocorrelation': np.nan,
                'information_ratio': np.nan,
                'tracking_error': np.nan,
                'r_squared': np.nan
            }
            
        # Calculate basic statistics
        mean = valid_data.mean()
        std = valid_data.std()
        skewness = stats.skew(valid_data)
        kurtosis = stats.kurtosis(valid_data)
        
        # Calculate autocorrelation
        autocorr = valid_data.autocorr(lag=1)
        
        # Calculate information ratio (simplified)
        returns = np.log(prices / prices.shift(1)).dropna()
        information_ratio = (returns * anchor).mean() / (returns.std() * anchor.std())
        
        # Calculate tracking error
        tracking_error = np.sqrt(((returns - anchor) ** 2).mean())
        
        # Calculate R-squared
        r_squared = 1 - (returns.var() / anchor.var())
        
        return {
            'mean': mean,
            'std': std,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'autocorrelation': autocorr,
            'information_ratio': information_ratio,
            'tracking_error': tracking_error,
            'r_squared': r_squared
        }
        
    def get_weighted_anchors(self, anchors: Dict[str, pd.Series]) -> pd.Series:
        """
        Calculate weighted anchors from multiple anchor types.
        
        Args:
            anchors: Dictionary of structural anchors
            
        Returns:
            Weighted anchors series
        """
        # Get weights from config
        weights = self.anchor_weights
        
        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
        
        # Calculate weighted anchors
        weighted_anchors = pd.Series(0, index=anchors[list(anchors.keys())[0]].index)
        
        for name, anchor in anchors.items():
            if name in weights:
                weighted_anchors += weights[name] * anchor
                
        return weighted_anchors
        
    def get_best_anchors(self, quality_metrics: Dict[str, Dict],
                        top_n: int = 3) -> List[str]:
        """
        Get the best structural anchors based on quality metrics.
        
        Args:
            quality_metrics: Dictionary with quality metrics for each anchor
            top_n: Number of best anchors to return
            
        Returns:
            List of best anchor names
        """
        # Calculate composite quality score
        scores = {}
        
        for name, metrics in quality_metrics.items():
            # Calculate composite score (higher is better)
            score = (
                metrics['information_ratio'] * 0.3 +
                metrics['r_squared'] * 0.25 +
                (1 - metrics['tracking_error']) * 0.25 +
                (1 - abs(metrics['autocorrelation'])) * 0.2
            )
            scores[name] = score
            
        # Get top N anchors
        best_anchors = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return [name for name, score in best_anchors]
                        
                        comparison[f'{anchor1}_vs_{anchor2}'] = {
                            'correlation': correlation,
                            'anchor1_mean': anchor1_aligned.mean(),
                            'anchor2_mean': anchor2_aligned.mean(),
                            'anchor1_std': anchor1_aligned.std(),
                            'anchor2_std': anchor2_aligned.std()
                        }
                        
        return comparison