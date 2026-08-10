"""
Sigma State Classification for the CEREBUS Morphic Volatility Engine (MVE)

This module implements sigma state classification and event detection,
providing the foundation for analyzing sigma state occupation and trend
continuation in financial markets.
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks
from typing import Dict, List, Tuple, Optional, Union
import warnings
warnings.filterwarnings('ignore')

class SigmaStates:
    """
    Collection of sigma state classification and event detection for MVE research.
    
    This class implements sigma state classification and event detection,
    including:
    1. Sigma state classification based on morphic coordinates
    2. Sigma event detection (occupation and acceptance)
    3. State transition analysis
    4. Event statistics and analysis
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize sigma states.
        
        Args:
            config: Configuration dictionary with sigma state parameters
        """
        self.config = config or self._get_default_config()
        self.quality_metrics = {}
        
    def _get_default_config(self) -> Dict:
        """
        Get default configuration for sigma states.
        
        Returns:
            Default configuration dictionary
        """
        return {
            'classification': {
                'num_states': 5,
                'step_size': 1.0,
                'min_occupancy': 0.1,
                'acceptance_threshold': 0.5
            },
            'event_detection': {
                'window': 20,
                'min_periods': 1,
                'acceptance_threshold': 0.5,
                'continuation_window': 5
            },
            'transition': {
                'window': 20,
                'min_periods': 1,
                'transition_threshold': 0.1
            }
        }
        
    def classify_sigma_states(self, morphic_coordinates: pd.Series,
                            step_size: float = 1.0) -> pd.Series:
        """
        Classify sigma states based on morphic coordinates.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step_size: Sigma state step size
            
        Returns:
            Sigma state classifications
        """
        # Calculate sigma states
        # S_t = sign(M_t) * floor(|M_t| / step_size)
        sigma_states = np.sign(morphic_coordinates) * np.floor(np.abs(morphic_coordinates) / step_size)
        
        return pd.Series(sigma_states, index=morphic_coordinates.index)
        
    def detect_sigma_events(self, morphic_coordinates: pd.Series,
                           sigma_states: pd.Series,
                           acceptance_threshold: float = 0.5) -> Dict[str, pd.Series]:
        """
        Detect sigma events (occupation and acceptance).
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            sigma_states: Sigma state classifications
            acceptance_threshold: Acceptance threshold
            
        Returns:
            Dictionary with sigma event series
        """
        events = {}
        
        # Detect occupation events
        events['occupation'] = self._detect_occupation_events(morphic_coordinates, sigma_states)
        
        # Detect acceptance events
        events['acceptance'] = self._detect_acceptance_events(morphic_coordinates, sigma_states, acceptance_threshold)
        
        # Detect continuation events
        events['continuation'] = self._detect_continuation_events(morphic_coordinates, sigma_states)
        
        return events
        
    def _detect_occupation_events(self, morphic_coordinates: pd.Series,
                                 sigma_states: pd.Series) -> pd.Series:
        """
        Detect occupation events.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            sigma_states: Sigma state classifications
            
        Returns:
            Occupation events series
        """
        # Occupation occurs when sigma state is non-zero
        occupation = sigma_states != 0
        
        return pd.Series(occupation, index=morphic_coordinates.index)
        
    def _detect_acceptance_events(self, morphic_coordinates: pd.Series,
                                 sigma_states: pd.Series,
                                 acceptance_threshold: float) -> pd.Series:
        """
        Detect acceptance events.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            sigma_states: Sigma state classifications
            acceptance_threshold: Acceptance threshold
            
        Returns:
            Acceptance events series
        """
        # Acceptance occurs when sigma state is above threshold
        acceptance = np.abs(sigma_states) >= acceptance_threshold
        
        return pd.Series(acceptance, index=morphic_coordinates.index)
        
    def _detect_continuation_events(self, morphic_coordinates: pd.Series,
                                   sigma_states: pd.Series) -> pd.Series:
        """
        Detect continuation events.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            sigma_states: Sigma state classifications
            
        Returns:
            Continuation events series
        """
        # Continuation occurs when sigma state persists
        # For simplicity, we'll use a rolling window approach
        window = self.config['event_detection']['continuation_window']
        
        # Calculate rolling persistence
        rolling_persistence = sigma_states.rolling(window=window, min_periods=window).apply(
            lambda x: len(x) - len(np.unique(x)) > 0
        )
        
        return rolling_persistence
        
    def analyze_event_statistics(self, events: Dict[str, pd.Series]) -> Dict[str, Dict]:
        """
        Analyze statistics of sigma events.
        
        Args:
            events: Dictionary with sigma event series
            
        Returns:
            Dictionary with event statistics
        """
        statistics = {}
        
        for event_name, event_series in events.items():
            # Remove NaN values
            valid_events = event_series.dropna()
            
            if len(valid_events) == 0:
                statistics[event_name] = {
                    'total_events': 0,
                    'event_rate': 0,
                    'mean_duration': np.nan,
                    'median_duration': np.nan,
                    'mean_magnitude': np.nan,
                    'median_magnitude': np.nan
                }
                continue
                
            # Calculate basic statistics
            total_events = valid_events.sum()
            event_rate = total_events / len(valid_events)
            
            # Calculate duration statistics
            event_groups = (valid_events != valid_events.shift()).cumsum()
            durations = valid_events.groupby(event_groups).sum()
            
            # Calculate magnitude statistics
            magnitudes = np.abs(valid_events)
            
            statistics[event_name] = {
                'total_events': total_events,
                'event_rate': event_rate,
                'mean_duration': durations.mean(),
                'median_duration': durations.median(),
                'mean_magnitude': magnitudes.mean(),
                'median_magnitude': magnitudes.median()
            }
            
        return statistics
        
    def analyze_event_regimes(self, events: Dict[str, pd.Series],
                            sigma_states: pd.Series) -> Dict[str, Dict]:
        """
        Analyze sigma events by regime.
        
        Args:
            events: Dictionary with sigma event series
            sigma_states: Sigma state classifications
            
        Returns:
            Dictionary with regime analysis results
        """
        regime_analysis = {}
        
        # Get unique sigma states
        unique_states = sigma_states.dropna().unique()
        
        for event_name, event_series in events.items():
            event_regime_analysis = {}
            
            for state in unique_states:
                # Get events for this state
                state_events = event_series[sigma_states == state]
                
                if len(state_events) > 0:
                    event_regime_analysis[str(state)] = {
                        'event_rate': state_events.mean(),
                        'total_events': state_events.sum(),
                        'mean_magnitude': np.abs(state_events).mean()
                    }
                else:
                    event_regime_analysis[str(state)] = {
                        'event_rate': 0,
                        'total_events': 0,
                        'mean_magnitude': np.nan
                    }
                    
            regime_analysis[event_name] = event_regime_analysis
            
        return regime_analysis
        
    def calculate_event_transitions(self, events: Dict[str, pd.Series]) -> Dict[str, Dict]:
        """
        Calculate transitions between sigma events.
        
        Args:
            events: Dictionary with sigma event series
            
        Returns:
            Dictionary with event transition probabilities
        """
        transition_probs = {}
        
        for event_name, event_series in events.items():
            # Calculate transitions
            transitions = {}
            
            for i in range(len(event_series) - 1):
                current_event = event_series.iloc[i]
                next_event = event_series.iloc[i + 1]
                
                if current_event not in transitions:
                    transitions[current_event] = {}
                    
                if next_event not in transitions[current_event]:
                    transitions[current_event][next_event] = 0
                    
                transitions[current_event][next_event] += 1
                
            # Convert to probabilities
            event_transition_probs = {}
            for current_event, next_counts in transitions.items():
                total = sum(next_counts.values())
                event_transition_probs[current_event] = {
                    next_event: count / total
                    for next_event, count in next_counts.items()
                }
                
            transition_probs[event_name] = event_transition_probs
            
        return transition_probs
        
    def analyze_event_trends(self, events: Dict[str, pd.Series],
                           prices: pd.Series) -> Dict[str, Dict]:
        """
        Analyze trends in sigma events.
        
        Args:
            events: Dictionary with sigma event series
            prices: Price series
            
        Returns:
            Dictionary with event trend analysis
        """
        trend_analysis = {}
        
        for event_name, event_series in events.items():
            # Calculate forward returns
            forward_returns = np.log(prices.shift(-1) / prices)
            
            # Group by event presence
            event_present = event_series == True
            event_absent = event_series == False
            
            event_trend_analysis = {}
            
            # Analyze when event is present
            if event_present.any():
                present_returns = forward_returns[event_present]
                event_trend_analysis['event_present'] = {
                    'mean_return': present_returns.mean(),
                    'std_return': present_returns.std(),
                    'median_return': present_returns.median(),
                    'count': len(present_returns)
                }
            else:
                event_trend_analysis['event_present'] = {
                    'mean_return': np.nan,
                    'std_return': np.nan,
                    'median_return': np.nan,
                    'count': 0
                }
                
            # Analyze when event is absent
            if event_absent.any():
                absent_returns = forward_returns[event_absent]
                event_trend_analysis['event_absent'] = {
                    'mean_return': absent_returns.mean(),
                    'std_return': absent_returns.std(),
                    'median_return': absent_returns.median(),
                    'count': len(absent_returns)
                }
            else:
                event_trend_analysis['event_absent'] = {
                    'mean_return': np.nan,
                    'std_return': np.nan,
                    'median_return': np.nan,
                    'count': 0
                }
                
            trend_analysis[event_name] = event_trend_analysis
            
        return trend_analysis
        
    def evaluate_state_quality(self, sigma_states: pd.Series,
                              events: Dict[str, pd.Series]) -> Dict[str, Dict]:
        """
        Evaluate quality of sigma state classification.
        
        Args:
            sigma_states: Sigma state classifications
            events: Dictionary with sigma event series
            
        Returns:
            Dictionary with state quality metrics
        """
        quality_metrics = {}
        
        # Evaluate sigma state quality
        sigma_state_quality = self._calculate_sigma_state_quality(sigma_states)
        quality_metrics['sigma_state'] = sigma_state_quality
        
        # Evaluate event quality
        event_quality = self._calculate_event_quality(events)
        quality_metrics.update(event_quality)
        
        return quality_metrics
        
    def _calculate_sigma_state_quality(self, sigma_states: pd.Series) -> Dict:
        """
        Calculate quality metrics for sigma state classification.
        
        Args:
            sigma_states: Sigma state classifications
            
        Returns:
            Dictionary with quality metrics
        """
        # Remove NaN values
        valid_states = sigma_states.dropna()
        
        if len(valid_states) == 0:
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
        mean = valid_states.mean()
        std = valid_states.std()
        skewness = stats.skew(valid_states)
        kurtosis = stats.kurtosis(valid_states)
        
        # Calculate autocorrelation
        autocorr = valid_states.autocorr(lag=1)
        
        # Calculate information ratio (simplified)
        returns = np.log(sigma_states / sigma_states.shift(1)).dropna()
        information_ratio = (returns * sigma_states).mean() / (returns.std() * sigma_states.std())
        
        # Calculate tracking error
        tracking_error = np.sqrt(((returns - sigma_states) ** 2).mean())
        
        # Calculate R-squared
        r_squared = 1 - (returns.var() / sigma_states.var())
        
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
        
    def _calculate_event_quality(self, events: Dict[str, pd.Series]) -> Dict:
        """
        Calculate quality metrics for sigma events.
        
        Args:
            events: Dictionary with sigma event series
            
        Returns:
            Dictionary with quality metrics
        """
        quality_metrics = {}
        
        for event_name, event_series in events.items():
            # Remove NaN values
            valid_events = event_series.dropna()
            
            if len(valid_events) == 0:
                quality_metrics[event_name] = {
                    'mean': np.nan,
                    'std': np.nan,
                    'skewness': np.nan,
                    'kurtosis': np.nan,
                    'autocorrelation': np.nan,
                    'information_ratio': np.nan,
                    'tracking_error': np.nan,
                    'r_squared': np.nan
                }
                continue
                
            # Calculate basic statistics
            mean = valid_events.mean()
            std = valid_events.std()
            skewness = stats.skew(valid_events)
            kurtosis = stats.kurtosis(valid_events)
            
            # Calculate autocorrelation
            autocorr = valid_events.autocorr(lag=1)
            
            # Calculate information ratio (simplified)
            returns = np.log(event_series / event_series.shift(1)).dropna()
            information_ratio = (returns * event_series).mean() / (returns.std() * event_series.std())
            
            # Calculate tracking error
            tracking_error = np.sqrt(((returns - event_series) ** 2).mean())
            
            # Calculate R-squared
            r_squared = 1 - (returns.var() / event_series.var())
            
            quality_metrics[event_name] = {
                'mean': mean,
                'std': std,
                'skewness': skewness,
                'kurtosis': kurtosis,
                'autocorrelation': autocorr,
                'information_ratio': information_ratio,
                'tracking_error': tracking_error,
                'r_squared': r_squared
            }
            
        return quality_metrics
        
    def get_best_states(self, quality_metrics: Dict[str, Dict],
                       top_n: int = 3) -> List[str]:
        """
        Get the best sigma states based on quality metrics.
        
        Args:
            quality_metrics: Dictionary with quality metrics for each state
            top_n: Number of best states to return
            
        Returns:
            List of best state names
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
            
        # Get top N states
        best_states = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return [name for name, score in best_states]
            
        return forward_return_analysis
        
    def analyze_event_state_transitions(self, events: Dict[str, pd.Series],
                                      states: pd.Series) -> Dict[str, Dict]:
        """
        Analyze state transitions for each event type.
        
        Args:
            events: Dictionary with event types as keys and boolean series as values
            states: Sigma states
            
        Returns:
            Dictionary with state transition analysis
        """
        event_transition_analysis = {}
        
        for event_name, event_series in events.items():
            event_indices = event_series[event_series].index
            
            if len(event_indices) == 0:
                event_transition_analysis[event_name] = {
                    'next_state_probs': {},
                    'continuation_probs': {},
                    'reversal_probs': {},
                    'count': 0
                }
                continue
                
            # Calculate state transitions
            next_state_probs = {}
            continuation_probs = {}
            reversal_probs = {}
            
            for idx in event_indices:
                if idx < len(states) - 1:
                    current_state = states.iloc[idx]
                    next_state = states.iloc[idx + 1]
                    
                    # Calculate next state probability
                    if current_state not in next_state_probs:
                        next_state_probs[current_state] = {}
                    if next_state not in next_state_probs[current_state]:
                        next_state_probs[current_state][next_state] = 0
                    next_state_probs[current_state][next_state] += 1
                    
                    # Calculate continuation probability
                    if current_state == next_state:
                        if 'continuation' not in continuation_probs:
                            continuation_probs['continuation'] = 0
                        continuation_probs['continuation'] += 1
                    else:
                        if 'reversal' not in reversal_probs:
                            reversal_probs['reversal'] = 0
                        reversal_probs['reversal'] += 1
                        
            # Convert counts to probabilities
            for current_state, next_counts in next_state_probs.items():
                total = sum(next_counts.values())
                next_state_probs[current_state] = {
                    next_state: count / total
                    for next_state, count in next_counts.items()
                }
                
            # Convert continuation/reversal counts to probabilities
            total_events = len(event_indices)
            if total_events > 0:
                if 'continuation' in continuation_probs:
                    continuation_probs['continuation'] /= total_events
                if 'reversal' in reversal_probs:
                    reversal_probs['reversal'] /= total_events
                    
            event_transition_analysis[event_name] = {
                'next_state_probs': next_state_probs,
                'continuation_probs': continuation_probs,
                'reversal_probs': reversal_probs,
                'count': total_events
            }
            
        return event_transition_analysis
        
    def analyze_event_time_metrics(self, events: Dict[str, pd.Series],
                                  prices: pd.Series) -> Dict[str, Dict]:
        """
        Analyze time metrics for each event type.
        
        Args:
            events: Dictionary with event types as keys and boolean series as values
            prices: Price series
            
        Returns:
            Dictionary with time metrics analysis
        """
        event_time_analysis = {}
        
        for event_name, event_series in events.items():
            event_indices = event_series[event_series].index
            
            if len(event_indices) == 0:
                event_time_analysis[event_name] = {
                    'time_to_next_state': {},
                    'time_to_failure': {},
                    'median_time_to_next_state': {},
                    'median_time_to_failure': {},
                    'count': 0
                }
                continue
                
            # Calculate time to next state
            time_to_next_state = {}
            time_to_failure = {}
            
            for idx in event_indices:
                # Find next state
                next_state_idx = None
                for j in range(idx + 1, len(prices)):
                    if not np.isnan(prices.iloc[j]):
                        next_state_idx = j
                        break
                        
                if next_state_idx is not None:
                    time_to_next_state[idx] = next_state_idx - idx
                    
                # Find time to failure (simplified)
                # For simplicity, we'll use a fixed failure horizon
                failure_horizon = 24  # 24 bars
                if idx + failure_horizon < len(prices):
                    time_to_failure[idx] = failure_horizon
                    
            # Calculate medians
            median_time_to_next_state = {}
            median_time_to_failure = {}
            
            if time_to_next_state:
                median_time_to_next_state['median'] = np.median(list(time_to_next_state.values()))
                median_time_to_next_state['mean'] = np.mean(list(time_to_next_state.values()))
                
            if time_to_failure:
                median_time_to_failure['median'] = np.median(list(time_to_failure.values()))
                median_time_to_failure['mean'] = np.mean(list(time_to_failure.values()))
                
            event_time_analysis[event_name] = {
                'time_to_next_state': time_to_next_state,
                'time_to_failure': time_to_failure,
                'median_time_to_next_state': median_time_to_next_state,
                'median_time_to_failure': median_time_to_failure,
                'count': len(event_indices)
            }
            
        return event_time_analysis
        
    def analyze_event_regime_effects(self, events: Dict[str, pd.Series],
                                   regimes: pd.Series) -> Dict[str, Dict]:
        """
        Analyze regime effects on events.
        
        Args:
            events: Dictionary with event types as keys and boolean series as values
            regimes: Volatility regime classifications
            
        Returns:
            Dictionary with regime effects analysis
        """
        event_regime_analysis = {}
        
        for event_name, event_series in events.items():
            event_indices = event_series[event_series].index
            
            if len(event_indices) == 0:
                event_regime_analysis[event_name] = {
                    'regime_effects': {},
                    'count': 0
                }
                continue
                
            # Calculate regime effects
            regime_effects = {}
            
            for regime in ['CONTRACTION', 'NORMAL', 'EXPANSION']:
                regime_event_indices = [idx for idx in event_indices 
                                      if regimes.loc[idx] == regime]
                
                if len(regime_event_indices) > 0:
                    regime_effects[regime] = {
                        'count': len(regime_event_indices),
                        'percentage': len(regime_event_indices) / len(event_indices) * 100
                    }
                else:
                    regime_effects[regime] = {
                        'count': 0,
                        'percentage': 0
                    }
                    
            event_regime_analysis[event_name] = {
                'regime_effects': regime_effects,
                'count': len(event_indices)
            }
            
        return event_regime_analysis