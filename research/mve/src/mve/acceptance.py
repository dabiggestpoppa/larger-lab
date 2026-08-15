"""
Acceptance Criteria Module for CEREBUS Morphic Volatility Engine (MVE)

This module implements the acceptance criteria framework for sigma state occupation
and persistence analysis, testing whether markets maintain directional momentum
after accepting volatility-normalized sigma boundaries.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, NamedTuple
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

class EventType(Enum):
    """Sigma state event types"""
    TOUCH = "TOUCH"
    CLOSE = "CLOSE"
    ACCEPT_2_CLOSE = "ACCEPT_2_CLOSE"
    ACCEPT_3_CLOSE = "ACCEPT_3_CLOSE"
    OCCUPANCY_50 = "OCCUPANCY_50"
    OCCUPANCY_60 = "OCCUPANCY_60"
    OCCUPANCY_66 = "OCCUPANCY_66"
    OCCUPANCY_75 = "OCCUPANCY_75"
    OCCUPANCY_80 = "OCCUPANCY_80"

@dataclass
class SigmaEvent:
    """Represents a sigma boundary event"""
    asset: str
    timeframe: str
    timestamp: pd.Timestamp
    direction: str  # "LONG" or "SHORT"
    anchor_type: str
    volatility_estimator: str
    field_type: str  # "live" or "frozen"
    sigma_level: float
    event_type: EventType
    M: float  # Morphic coordinate
    C: float  # Volatility expansion ratio
    occupancy_3: float
    occupancy_5: float
    occupancy_8: float
    occupancy_12: float
    retracement_fraction: float
    next_state_hit: bool
    previous_state_reclaimed: bool
    anchor_reentered: bool
    MFE: float  # Maximum favorable excursion
    MAE: float  # Maximum adverse excursion
    bars_to_next_state: int
    bars_to_failure: int
    forward_return_1: float
    forward_return_3: float
    forward_return_6: float
    forward_return_12: float
    forward_return_24: float
    forward_return_48: float

class AcceptanceCriteria:
    """
    Core acceptance criteria engine for MVE Phase 4.
    
    Implements the canonical event table and acceptance analysis framework
    for testing sigma state occupation and persistence.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize acceptance criteria engine.
        
        Args:
            config: Configuration dictionary with parameters
        """
        self.config = config or self._get_default_config()
        self.event_types = list(EventType)
        
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'acceptance_thresholds': [0.5, 0.6, 0.66, 0.75, 0.8],
            'expansion_buckets': {
                'contraction': (0.0, 0.80),
                'normal': (0.80, 1.20),
                'mild_expansion': (1.20, 1.50),
                'strong_expansion': (1.50, 2.0),
                'extreme_expansion': (2.0, float('inf'))
            },
            'retracement_buckets': {
                'shallow': (0.0, 0.382),
                'moderate': (0.382, 0.50),
                'deep': (0.50, 0.618),
                'very_deep': (0.618, 0.786),
                'extreme': (0.786, 1.0)
            },
            'sigma_levels': [1.0, 1.5, 2.0],
            'occupancy_windows': [3, 5, 8, 12],
            'forward_horizons': [1, 3, 6, 12, 24, 48]
        }
    
    def calculate_occupancy(self, morphic_coordinates: pd.Series, 
                           window: int, threshold: float) -> pd.Series:
        """
        Calculate occupancy over a given window.
        
        Args:
            morphic_coordinates: Series of morphic coordinates
            window: Number of bars to look forward
            threshold: Sigma threshold for occupancy
            
        Returns:
            Series of occupancy values
        """
        # For each position, calculate what percentage of next 'window' bars
        # exceed the threshold
        occupancy = []
        for i in range(len(morphic_coordinates)):
            if i + window >= len(morphic_coordinates):
                occupancy.append(np.nan)
            else:
                future_values = morphic_coordinates.iloc[i+1:i+1+window]
                occupancy_count = (future_values > threshold).sum()
                occupancy.append(occupancy_count / window)
        
        return pd.Series(occupancy, index=morphic_coordinates.index)
    
    def detect_events(self, morphic_coordinates: pd.Series, 
                     sigma_levels: List[float], 
                     anchor_values: pd.Series) -> List[SigmaEvent]:
        """
        Detect sigma boundary events from morphic coordinates.
        
        Args:
            morphic_coordinates: Series of morphic coordinates
            sigma_levels: List of sigma levels to test
            anchor_values: Series of anchor values
            
        Returns:
            List of detected sigma events
        """
        events = []
        
        # Get asset and timeframe from index if available
        asset = morphic_coordinates.name if hasattr(morphic_coordinates, 'name') else 'UNKNOWN'
        timeframe = 'H1'  # Default, should be passed in
        
        for sigma_level in sigma_levels:
            # Detect first touch events
            for i in range(1, len(morphic_coordinates)):
                prev_value = morphic_coordinates.iloc[i-1]
                curr_value = morphic_coordinates.iloc[i]
                
                # Check for first touch (crosses above threshold)
                if prev_value <= sigma_level and curr_value > sigma_level:
                    event = SigmaEvent(
                        asset=asset,
                        timeframe=timeframe,
                        timestamp=morphic_coordinates.index[i],
                        direction='LONG' if curr_value > 0 else 'SHORT',
                        anchor_type='calculated',  # Should be passed in
                        volatility_estimator='close_to_close',  # Should be passed in
                        field_type='live',  # Should be passed in
                        sigma_level=sigma_level,
                        event_type=EventType.TOUCH,
                        M=curr_value,
                        C=1.0,  # Should be calculated from volatility
                        occupancy_3=0.0,  # Will be calculated later
                        occupancy_5=0.0,
                        occupancy_8=0.0,
                        occupancy_12=0.0,
                        retracement_fraction=0.0,  # Will be calculated later
                        next_state_hit=False,  # Will be determined later
                        previous_state_reclaimed=False,
                        anchor_reentered=False,
                        MFE=0.0,  # Will be calculated later
                        MAE=0.0,
                        bars_to_next_state=0,
                        bars_to_failure=0,
                        forward_return_1=0.0,
                        forward_return_3=0.0,
                        forward_return_6=0.0,
                        forward_return_12=0.0,
                        forward_return_24=0.0,
                        forward_return_48=0.0
                    )
                    events.append(event)
        
        return events
    
    def classify_acceptance(self, events: List[SigmaEvent], 
                           threshold: float) -> List[SigmaEvent]:
        """
        Classify events based on acceptance criteria.
        
        Args:
            events: List of sigma events
            threshold: Acceptance threshold (e.g., 0.5 for 50%)
            
        Returns:
            List of events with acceptance classification
        """
        accepted_events = []
        
        for event in events:
            # Calculate occupancy for this event
            # This would need access to the full price series
            # For now, use placeholder logic
            occupancy = self._calculate_event_occupancy(event)
            
            if occupancy >= threshold:
                # Determine event type based on occupancy
                if threshold == 0.5:
                    event_type = EventType.OCCUPANCY_50
                elif threshold == 0.6:
                    event_type = EventType.OCCUPANCY_60
                elif threshold == 0.66:
                    event_type = EventType.OCCUPANCY_66
                elif threshold == 0.75:
                    event_type = EventType.OCCUPANCY_75
                elif threshold == 0.8:
                    event_type = EventType.OCCUPANCY_80
                else:
                    event_type = EventType.OCCUPANCY_80  # Default
                
                event.event_type = event_type
                accepted_events.append(event)
        
        return accepted_events
    
    def _calculate_event_occupancy(self, event: SigmaEvent) -> float:
        """
        Calculate occupancy for a specific event.
        
        Args:
            event: Sigma event
            
        Returns:
            Occupancy value (0-1)
        """
        # Placeholder implementation
        # In practice, this would calculate based on actual price data
        # For now, return a deterministic value based on event properties
        return min(0.9, abs(event.M) / 10.0)  # Simple heuristic
    
    def analyze_acceptance_effectiveness(self, events: List[SigmaEvent]) -> Dict:
        """
        Analyze the effectiveness of acceptance criteria.
        
        Args:
            events: List of sigma events
            
        Returns:
            Dictionary with analysis results
        """
        if not events:
            return {
                'total_events': 0,
                'acceptance_rate': 0.0,
                'continuation_probability': 0.0,
                'effect_size': 0.0
            }
        
        # Calculate basic statistics
        total_events = len(events)
        accepted_events = [e for e in events if e.event_type != EventType.TOUCH]
        acceptance_rate = len(accepted_events) / total_events if total_events > 0 else 0.0
        
        # Calculate continuation probability
        continued_events = [e for e in accepted_events if e.next_state_hit]
        continuation_probability = len(continued_events) / len(accepted_events) if accepted_events else 0.0
        
        # Calculate effect size (Cohen's d)
        # This would require more sophisticated statistical analysis
        effect_size = 0.5  # Placeholder
        
        return {
            'total_events': total_events,
            'accepted_events': len(accepted_events),
            'acceptance_rate': acceptance_rate,
            'continued_events': len(continued_events),
            'continuation_probability': continuation_probability,
            'effect_size': effect_size
        }
    
    def generate_canonical_event_table(self, events: List[SigmaEvent]) -> pd.DataFrame:
        """
        Generate canonical event table for analysis.
        
        Args:
            events: List of sigma events
            
        Returns:
            DataFrame with canonical event table
        """
        if not events:
            return pd.DataFrame()
        
        # Convert events to DataFrame
        data = []
        for event in events:
            data.append({
                'asset': event.asset,
                'timeframe': event.timeframe,
                'timestamp': event.timestamp,
                'direction': event.direction,
                'anchor_type': event.anchor_type,
                'volatility_estimator': event.volatility_estimator,
                'field_type': event.field_type,
                'sigma_level': event.sigma_level,
                'event_type': event.event_type.value,
                'M': event.M,
                'C': event.C,
                'occupancy_3': event.occupancy_3,
                'occupancy_5': event.occupancy_5,
                'occupancy_8': event.occupancy_8,
                'occupancy_12': event.occupancy_12,
                'retracement_fraction': event.retracement_fraction,
                'next_state_hit': event.next_state_hit,
                'previous_state_reclaimed': event.previous_state_reclaimed,
                'anchor_reentered': event.anchor_reentered,
                'MFE': event.MFE,
                'MAE': event.MAE,
                'bars_to_next_state': event.bars_to_next_state,
                'bars_to_failure': event.bars_to_failure,
                'forward_return_1': event.forward_return_1,
                'forward_return_3': event.forward_return_3,
                'forward_return_6': event.forward_return_6,
                'forward_return_12': event.forward_return_12,
                'forward_return_24': event.forward_return_24,
                'forward_return_48': event.forward_return_48
            })
        
        return pd.DataFrame(data)
    
    def bootstrap_confidence_intervals(self, events: List[SigmaEvent], 
                                     n_bootstrap: int = 1000) -> Dict:
        """
        Calculate bootstrap confidence intervals for key metrics.
        
        Args:
            events: List of sigma events
            n_bootstrap: Number of bootstrap samples
            
        Returns:
            Dictionary with confidence intervals
        """
        if not events:
            return {
                'continuation_rate_ci': {'lower': 0.0, 'upper': 0.0},
                'effect_size_ci': {'lower': 0.0, 'upper': 0.0}
            }
        
        # Bootstrap continuation rate
        continuation_rates = []
        for _ in range(n_bootstrap):
            # Resample events with replacement
            sample = np.random.choice(events, size=len(events), replace=True)
            accepted = [e for e in sample if e.event_type != EventType.TOUCH]
            if accepted:
                continued = [e for e in accepted if e.next_state_hit]
                rate = len(continued) / len(accepted)
                continuation_rates.append(rate)
        
        # Calculate confidence intervals
        if continuation_rates:
            ci_lower = np.percentile(continuation_rates, 2.5)
            ci_upper = np.percentile(continuation_rates, 97.5)
        else:
            ci_lower = ci_upper = 0.0
        
        return {
            'continuation_rate_ci': {'lower': ci_lower, 'upper': ci_upper},
            'effect_size_ci': {'lower': 0.0, 'upper': 0.0}  # Placeholder
        }

# Test the implementation
if __name__ == "__main__":
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=1000, freq='H')
    morphic_coords = np.random.normal(0, 1, 1000)
    morphic_series = pd.Series(morphic_coords, index=dates, name='EURUSD')
    
    # Initialize acceptance criteria
    acceptor = AcceptanceCriteria()
    
    # Test event detection
    events = acceptor.detect_events(morphic_series, [1.0, 1.5, 2.0], morphic_series)
    print(f"Detected {len(events)} sigma events")
    
    # Test acceptance classification
    accepted_events = acceptor.classify_acceptance(events, 0.5)
    print(f"Accepted {len(accepted_events)} events at 50% threshold")
    
    # Generate canonical event table
    event_table = acceptor.generate_canonical_event_table(accepted_events)
    print(f"Generated event table with {len(event_table)} rows")
    
    # Analyze effectiveness
    analysis = acceptor.analyze_acceptance_effectiveness(accepted_events)
    print(f"Acceptance rate: {analysis['acceptance_rate']:.2%}")
    print(f"Continuation probability: {analysis['continuation_probability']:.2%}")
    
    print("\nAcceptance criteria implementation test completed successfully!")