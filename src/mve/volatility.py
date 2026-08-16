"""
Volatility Estimators for the CEREBUS Morphic Volatility Engine (MVE)

This module implements 7 different volatility estimators with quality analysis,
providing multiple perspectives on market volatility for sigma state analysis.
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks
from typing import Dict, List, Tuple, Optional, Union
import warnings
warnings.filterwarnings('ignore')

class VolatilityEstimators:
    """
    Collection of volatility estimators for MVE research.
    
    This class implements 7 different volatility estimation methods:
    1. Close-to-Close (standard deviation of log returns)
    2. EWMA (Exponentially Weighted Moving Average)
    3. Parkinson (range-based estimator)
    4. Garman-Klass (OHLC-based estimator)
    5. ATR Normalized (Average True Range normalized)
    6. MAD (Median Absolute Deviation)
    7. GARCH (Generalized Autoregressive Conditional Heteroskedasticity)
    
    Each estimator is evaluated for quality and can be weighted according to
    research requirements.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize volatility estimators.
        
        Args:
            config: Configuration dictionary with estimator parameters
        """
        self.config = config or self._get_default_config()
        self.estimator_weights = self.config.get('volatility_estimator_weights', {})
        self.quality_metrics = {}
        
    def _get_default_config(self) -> Dict:
        """
        Get default configuration for volatility estimators.
        
        Returns:
            Default configuration dictionary
        """
        return {
            'close_to_close': {
                'window': 20,
                'min_periods': 1,
                'ddof': 1
            },
            'ewma': {
                'lambda': 0.94,
                'min_periods': 1
            },
            'parkinson': {
                'window': 20,
                'min_periods': 1
            },
            'garman_klass': {
                'window': 20,
                'min_periods': 1
            },
            'atr_normalized': {
                'window': 20,
                'min_periods': 1,
                'atr_period': 14
            },
            'mad': {
                'window': 20,
                'min_periods': 1,
                'constant': 1.4826
            },
            'garch': {
                'window': 252,
                'min_periods': 1,
                'order': (1, 1)
            }
        }
        
    def calculate_all_estimators(self, prices: pd.Series, highs: pd.Series = None,
                                lows: pd.Series = None, volumes: pd.Series = None) -> Dict[str, pd.Series]:
        """
        Calculate all volatility estimators.
        
        Args:
            prices: Price series (typically close prices)
            highs: High price series (optional)
            lows: Low price series (optional)
            volumes: Volume series (optional)
            
        Returns:
            Dictionary with volatility estimator names as keys and series as values
        """
        estimators = {}
        
        # Calculate each estimator
        returns = np.log(prices / prices.shift(1))
        estimators['close_to_close'] = self._close_to_close_volatility(returns)
        estimators['ewma'] = self._ewma_volatility(prices)
        estimators['parkinson'] = self._parkinson_volatility(highs, lows)
        estimators['garman_klass'] = self._garman_klass_volatility(highs, lows)
        estimators['atr_normalized'] = self._atr_normalized_volatility(prices, highs, lows)
        estimators['mad'] = self._mad_volatility(prices)
        estimators['garch'] = self._garch_volatility(prices)
        
        return estimators

    def _close_to_close_volatility(self, returns: pd.Series) -> pd.Series:
        """Calculate close-to-close rolling standard deviation."""
        return returns.rolling(window=self.config['close_to_close']['window']).std()
        
    def _ewma_volatility(self, prices: pd.Series) -> pd.Series:
        """
        Calculate EWMA volatility (Exponentially Weighted Moving Average).
        
        Args:
            prices: Price series
            
        Returns:
            EWMA volatility series
        """
        returns = np.log(prices / prices.shift(1))
        lambda_ = self.config['ewma']['lambda']
        min_periods = self.config['ewma']['min_periods']
        
        # Calculate EWMA of squared returns
        ewma_variance = returns.ewm(alpha=1-lambda_, min_periods=min_periods).mean()
        volatility = np.sqrt(ewma_variance)
        
        # Annualize
        volatility = volatility * np.sqrt(252)
        
        return volatility
        
    def _parkinson_volatility(self, highs: pd.Series, lows: pd.Series) -> pd.Series:
        """
        Calculate Parkinson volatility (range-based estimator).
        
        Args:
            highs: High price series
            lows: Low price series
            
        Returns:
            Parkinson volatility series
        """
        if highs is None or lows is None:
            raise ValueError("High and low prices are required for Parkinson volatility")
            
        window = self.config['parkinson']['window']
        min_periods = self.config['parkinson']['min_periods']
        
        # Calculate Parkinson estimator
        log_ratio = np.log(highs / lows)
        parkinson_variance = (log_ratio ** 2) / (4 * np.log(2))
        volatility = np.sqrt(parkinson_variance.rolling(window=window, min_periods=min_periods).mean())
        
        # Annualize
        volatility = volatility * np.sqrt(252)
        
        return volatility
        
    def _garman_klass_volatility(self, highs: pd.Series, lows: pd.Series) -> pd.Series:
        """
        Calculate Garman-Klass volatility (OHLC-based estimator).
        
        Args:
            highs: High price series
            lows: Low price series
            
        Returns:
            Garman-Klass volatility series
        """
        if highs is None or lows is None:
            raise ValueError("High and low prices are required for Garman-Klass volatility")
            
        window = self.config['garman_klass']['window']
        min_periods = self.config['garman_klass']['min_periods']
        
        # Calculate Garman-Klass estimator
        log_ratio = np.log(highs / lows)
        garman_klass_variance = (0.5 * log_ratio ** 2) - (np.log(highs / highs.shift(1)) ** 2)
        volatility = np.sqrt(garman_klass_variance.rolling(window=window, min_periods=min_periods).mean())
        
        # Annualize
        volatility = volatility * np.sqrt(252)
        
        return volatility
        
    def _atr_normalized_volatility(self, prices: pd.Series, highs: pd.Series = None,
                                  lows: pd.Series = None) -> pd.Series:
        """
        Calculate ATR normalized volatility.
        
        Args:
            prices: Price series
            highs: High price series (optional)
            lows: Low price series (optional)
            
        Returns:
            ATR normalized volatility series
        """
        if highs is None or lows is None:
            raise ValueError("High and low prices are required for ATR normalized volatility")
            
        window = self.config['atr_normalized']['window']
        min_periods = self.config['atr_normalized']['min_periods']
        atr_period = self.config['atr_normalized']['atr_period']
        
        # Calculate True Range
        tr1 = highs - lows
        tr2 = abs(highs - prices.shift(1))
        tr3 = abs(lows - prices.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR
        atr = true_range.rolling(window=atr_period, min_periods=atr_period).mean()
        
        # Calculate volatility as percentage of ATR
        volatility = (prices.rolling(window=window, min_periods=min_periods).std() / atr) * 100
        
        return volatility
        
    def _mad_volatility(self, prices: pd.Series) -> pd.Series:
        """
        Calculate MAD volatility (Median Absolute Deviation).
        
        Args:
            prices: Price series
            
        Returns:
            MAD volatility series
        """
        returns = np.log(prices / prices.shift(1))
        window = self.config['mad']['window']
        min_periods = self.config['mad']['min_periods']
        constant = self.config['mad']['constant']
        
        # Calculate MAD
        mad = returns.rolling(window=window, min_periods=min_periods).apply(
            lambda x: np.median(np.abs(x - np.median(x))) * constant
        )
        
        # Annualize
        mad = mad * np.sqrt(252)
        
        return mad
        
    def _garch_volatility(self, prices: pd.Series) -> pd.Series:
        """
        Calculate GARCH volatility (Generalized Autoregressive Conditional Heteroskedasticity).
        
        Args:
            prices: Price series
            
        Returns:
            GARCH volatility series
        """
        returns = np.log(prices / prices.shift(1))
        window = self.config['garch']['window']
        min_periods = self.config['garch']['min_periods']
        order = self.config['garch']['order']
        
        # Simplified GARCH(1,1) estimation
        # In practice, this would use a proper GARCH library
        volatility = returns.rolling(window=window, min_periods=min_periods).std()
        
        # Annualize
        volatility = volatility * np.sqrt(252)
        
        return volatility
        
    def analyze_estimator_quality(self, estimators: Dict[str, pd.Series], 
                                 realized_vol: pd.Series) -> Dict[str, Dict]:
        """
        Analyze quality of each volatility estimator.
        
        Args:
            estimators: Dictionary of volatility estimators
            realized_vol: Realized volatility for comparison
            
        Returns:
            Dictionary with quality metrics for each estimator
        """
        quality_metrics = {}
        
        for name, estimator in estimators.items():
            # Remove NaN values
            valid_data = estimator.dropna()
            realized_valid = realized_vol.loc[valid_data.index]
            
            if len(valid_data) == 0:
                quality_metrics[name] = {
                    'stability': np.nan,
                    'responsiveness': np.nan,
                    'realized_coverage': np.nan,
                    'outlier_sensitivity': np.nan,
                    'state_persistence': np.nan
                }
                continue
            
            # Calculate correlation with realized volatility
            correlation = valid_data.corr(realized_valid)
            
            # Calculate stability (inverse of variance)
            stability = 1 / valid_data.var()
            
            # Calculate responsiveness (autocorrelation)
            responsiveness = valid_data.autocorr(lag=1)
            
            # Calculate realized coverage (percentage of realized vol within estimator range)
            estimator_range = valid_data.max() - valid_data.min()
            coverage = ((realized_valid >= valid_data.min()) & 
                       (realized_valid <= valid_data.max())).mean()
            
            # Calculate outlier sensitivity (percentage of outliers)
            z_scores = np.abs((valid_data - valid_data.mean()) / valid_data.std())
            outlier_sensitivity = (z_scores > 3).mean()
            
            # Calculate state persistence (autocorrelation at lag 5)
            state_persistence = valid_data.autocorr(lag=5)
            
            quality_metrics[name] = {
                'correlation': correlation,
                'stability': stability,
                'responsiveness': responsiveness,
                'realized_coverage': coverage,
                'outlier_sensitivity': outlier_sensitivity,
                'state_persistence': state_persistence
            }
            
        return quality_metrics
        
    def evaluate_estimator_quality(self, estimators: Dict[str, pd.Series],
                                  prices: pd.Series) -> Dict[str, Dict]:
        """
        Evaluate quality of volatility estimators.
        
        Args:
            estimators: Dictionary of volatility estimators
            prices: Price series
            
        Returns:
            Dictionary with quality metrics for each estimator
        """
        quality_metrics = {}
        
        for name, estimator in estimators.items():
            metrics = self._calculate_estimator_quality(estimator, prices)
            quality_metrics[name] = metrics
            
        return quality_metrics
        
    def _calculate_estimator_quality(self, estimator: pd.Series, prices: pd.Series) -> Dict:
        """
        Calculate quality metrics for a single volatility estimator.
        
        Args:
            estimator: Volatility estimator series
            prices: Price series
            
        Returns:
            Dictionary with quality metrics
        """
        # Remove NaN values
        valid_data = estimator.dropna()
        
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
        information_ratio = (returns * estimator).mean() / (returns.std() * estimator.std())
        
        # Calculate tracking error
        tracking_error = np.sqrt(((returns - estimator) ** 2).mean())
        
        # Calculate R-squared
        r_squared = 1 - (returns.var() / estimator.var())
        
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
        
    def get_best_estimators(self, quality_metrics: Dict[str, Dict], 
                           top_n: int = 3) -> List[str]:
        """
        Get the best volatility estimators based on quality metrics.
        
        Args:
            quality_metrics: Dictionary with quality metrics for each estimator
            top_n: Number of best estimators to return
            
        Returns:
            List of best estimator names
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
            
        # Get top N estimators
        best_estimators = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return [name for name, score in best_estimators]
        
    def compare_volatility_fields(self, prices: pd.Series, anchors: pd.Series,
                                 volatility_estimators: Dict[str, pd.Series],
                                 step: float = 1.0) -> Dict[str, pd.Series]:
        """
        Compare live vs frozen sigma fields for each volatility estimator.
        
        Args:
            prices: Price series
            anchors: Anchor values
            volatility_estimators: Dictionary of volatility estimators
            step: Sigma state step size
            
        Returns:
            Dictionary with sigma fields for each estimator
        """
        sigma_fields = {}
        
        for name, volatility in volatility_estimators.items():
            # Calculate live sigma field
            live_sigma = (np.log(prices / anchors) / 
                         (volatility * np.sqrt(1.0)))  # tau = 1 for daily
            
            # Calculate frozen sigma field (using first non-NaN volatility as sigma*)
            valid_vol = volatility.dropna()
            if len(valid_vol) > 0:
                sigma_star = valid_vol.iloc[0]
                frozen_sigma = (np.log(prices / anchors) / 
                               (sigma_star * np.sqrt(1.0)))
            else:
                frozen_sigma = pd.Series(np.nan, index=prices.index)
            
            sigma_fields[f'{name}_live'] = live_sigma
            sigma_fields[f'{name}_frozen'] = frozen_sigma
            
        return sigma_fields
        
    def analyze_volatility_regimes(self, expansion_ratios: pd.Series) -> Dict:
        """
        Analyze volatility regime characteristics.
        
        Args:
            expansion_ratios: Volatility expansion ratios
            
        Returns:
            Dictionary with regime analysis results
        """
        # Classify regimes
        regimes = pd.Series(index=expansion_ratios.index)
        regimes[expansion_ratios < 0.80] = 'CONTRACTION'
        regimes[(expansion_ratios >= 0.80) & (expansion_ratios <= 1.20)] = 'NORMAL'
        regimes[expansion_ratios > 1.20] = 'EXPANSION'
        
        # Calculate regime statistics
        regime_stats = {}
        for regime in ['CONTRACTION', 'NORMAL', 'EXPANSION']:
            regime_data = expansion_ratios[regimes == regime]
            
            if len(regime_data) > 0:
                regime_stats[regime] = {
                    'mean': regime_data.mean(),
                    'std': regime_data.std(),
                    'min': regime_data.min(),
                    'max': regime_data.max(),
                    'count': len(regime_data),
                    'duration_mean': len(regime_data) / len(expansion_ratios) * 100
                }
            else:
                regime_stats[regime] = {
                    'mean': np.nan,
                    'std': np.nan,
                    'min': np.nan,
                    'max': np.nan,
                    'count': 0,
                    'duration_mean': 0
                }
                
        return {
            'regimes': regimes,
            'statistics': regime_stats,
            'transitions': self._calculate_regime_transitions(regimes)
        }
        
    def _calculate_regime_transitions(self, regimes: pd.Series) -> Dict:
        """Calculate regime transition probabilities."""
        transitions = {}
        
        # Count transitions
        for i in range(len(regimes) - 1):
            current = regimes.iloc[i]
            next_regime = regimes.iloc[i + 1]
            
            if current not in transitions:
                transitions[current] = {}
                
            if next_regime not in transitions[current]:
                transitions[current][next_regime] = 0
                
            transitions[current][next_regime] += 1
            
        # Convert to probabilities
        transition_probs = {}
        for current, next_counts in transitions.items():
            total = sum(next_counts.values())
            transition_probs[current] = {
                next_regime: count / total
                for next_regime, count in next_counts.items()
            }
            
        return transition_probs