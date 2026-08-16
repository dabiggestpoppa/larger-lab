"""
Morphic Rekey Hypothesis for CEREBUS Morphic Volatility Engine

This module implements the morphic rekey hypothesis used in the MVE research.
The hypothesis investigates whether an accepted sigma boundary behaves like a new
local equilibrium / structural origin, leading to recursive transformation of
the morphic coordinate system.

The rekey process transforms:
phi_0(P) → phi_1(P) → phi_2(P)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

class MorphicRekey:
    """
    Morphic rekey hypothesis implementation for MVE research.
    
    This class implements the morphic rekey hypothesis, investigating whether
an accepted sigma boundary behaves like a new local equilibrium / structural origin.
    """
    
    def __init__(self, step_sizes: List[float] = None):
        """
        Initialize morphic rekey calculator.
        
        Args:
            step_sizes: List of sigma state step sizes to test
        """
        if step_sizes is None:
            step_sizes = [0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0]
        self.step_sizes = step_sizes
        self.rekey_results = {}
        
    def calculate_rekey_variants(self, morphic_coordinates: pd.Series,
                                step: float = 1.0,
                                n: int = 1) -> Dict[str, pd.Series]:
        """
        Calculate three rekey variants for a given step size and n value.
        
        Args:
            morphic_coordinates: Morphic sigma coordinates
            step: Sigma state step size
            n: Sigma state level
            
        Returns:
            Dictionary with rekey variant names as keys and rekeyed coordinates as values
        """
        # Calculate sigma state boundary
        boundary = n * step
        
        # Initialize rekey variants
        rekey_variants = {}
        
        # RKEY-A: Re-anchor immediately after acceptance
        rekey_a = self._rekey_variant_a(morphic_coordinates, boundary, step)
        rekey_variants['RKEY_A'] = rekey_a
        
        # RKEY-B: Re-anchor only after breakout + successful retest
        rekey_b = self._rekey_variant_b(morphic_coordinates, boundary, step)
        rekey_variants['RKEY_B'] = rekey_b
        
        # RKEY-C: Re-anchor only after next sigma state is reached and previous state survives
        rekey_c = self._rekey_variant_c(morphic_coordinates, boundary, step)
        rekey_variants['RKEY_C'] = rekey_c
        
        # No rekey (baseline)
        rekey_variants['NO_REKEY'] = morphic_coordinates

        return rekey_variants

    def detect_rekey_events(self, morphic_coordinates: pd.Series,
                            step: float = 1.0, n: int = 1,
                            variant: str = "B") -> List[Dict]:
        """Return structured rekey events with explicit causal timestamps.

        Variants A/C are realtime (all timestamps equal the rekey bar).
        Variant B is delayed confirmation: rekey_event_time = scan-origin i,
        rekey_evidence_complete_time = rekey_known_time =
        new_anchor_active_time = retest bar j.

        Fields follow MVE_SCIENTIFIC_EVENT_TIME_SCHEMA.json. source_anchor is
        not tracked by the isolated detection (prior anchor state) and is None.
        """
        boundary = n * step
        coords = morphic_coordinates
        events: List[Dict] = []

        if variant == "A":
            for i in range(len(coords)):
                current = coords.iloc[i]
                prev = coords.iloc[i - 1] if i > 0 else 0.0
                if (not np.isnan(current) and abs(current) > boundary and i > 0
                        and not np.isnan(prev) and abs(prev) <= boundary):
                    events.append(self._rekey_event("RKEY_A", i, i, i, i, current))
        elif variant == "B":
            breakout_occurred = False
            for i in range(len(coords)):
                current = coords.iloc[i]
                if not np.isnan(current) and abs(current) > boundary:
                    breakout_occurred = True
                if breakout_occurred and i > 0:
                    for j in range(i + 1, min(i + 5, len(coords))):
                        if not np.isnan(coords.iloc[j]) and abs(coords.iloc[j]) > boundary:
                            events.append(self._rekey_event("RKEY_B", i, j, j, j, coords.iloc[i]))
                            breakout_occurred = False
                            break
        elif variant == "C":
            for i in range(len(coords)):
                current = coords.iloc[i]
                prev = coords.iloc[i - 1] if i > 0 else 0.0
                if (not np.isnan(current) and abs(current) > boundary and i > 0
                        and not np.isnan(prev)):
                    prev_state = int(abs(prev) // step)
                    current_state = int(abs(current) // step)
                    if current_state > prev_state and i >= 5:
                        window = coords.iloc[max(0, i - 2):i + 1]
                        if window.notna().all():
                            above_count = sum(abs(window) > boundary)
                            if above_count >= 3:
                                events.append(self._rekey_event("RKEY_C", i, i, i, i, current))
        else:
            raise ValueError(f"Unknown rekey variant: {variant}")

        return events

    @staticmethod
    def _rekey_event(variant: str, event_time: int, evidence_time: int,
                     known_time: int, active_time: int, new_anchor: float) -> Dict:
        """Build a schema-valid rekey event record."""
        return {
            "variant": variant,
            "rekey_event_time": int(event_time),
            "rekey_evidence_complete_time": int(evidence_time),
            "rekey_known_time": int(known_time),
            "new_anchor_active_time": int(active_time),
            "source_anchor": None,
            "new_anchor": float(new_anchor),
        }

    def _rekey_variant_a(self, morphic_coordinates: pd.Series,
                        boundary: float, step: float) -> pd.Series:
        """
        RKEY-A: Re-anchor immediately after acceptance.
        
        Args:
            morphic_coordinates: Original morphic coordinates
            boundary: Sigma state boundary
            step: Sigma state step size
            
        Returns:
            Rekeyed coordinates
        """
        # Create a copy to avoid modifying original
        rekeyed = pd.Series(index=morphic_coordinates.index)
        
        # Initialize rekey anchor
        rekey_anchor = 0.0
        
        # Calculate rekeyed coordinates
        for i in range(len(morphic_coordinates)):
            current_coord = morphic_coordinates.iloc[i]
            
            # Check if we've accepted the sigma state
            if abs(current_coord) > boundary and i > 0:
                # Check if previous bar was below boundary
                prev_coord = morphic_coordinates.iloc[i-1]
                if abs(prev_coord) <= boundary:
                    # Re-anchor immediately
                    rekey_anchor = current_coord
                    
            # Calculate rekeyed coordinate
            if rekey_anchor != 0.0:
                # Calculate displacement from rekey anchor
                displacement = current_coord - rekey_anchor
                rekeyed.iloc[i] = displacement
            else:
                rekeyed.iloc[i] = current_coord
                
        return rekeyed
        
    def _rekey_variant_b(self, morphic_coordinates: pd.Series,
                        boundary: float, step: float) -> pd.Series:
        """
        RKEY-B: Re-anchor only after breakout + successful retest.

        CAUSAL (R0.5.1 repair): the retest is confirmed by a future bar, so the
        new anchor's VALUE (coordinate at the scan-origin bar, unchanged
        formula) becomes ACTIVE only at the retest bar j - never at the
        scan-origin bar i. Bars between i and j keep the previous anchor.
        rekey_event_time = i, rekey_evidence_complete_time = j,
        rekey_known_time = j, new_anchor_active_time = j.

        Args:
            morphic_coordinates: Original morphic coordinates
            boundary: Sigma state boundary
            step: Sigma state step size

        Returns:
            Rekeyed coordinates
        """
        rekeyed = pd.Series(index=morphic_coordinates.index)

        # Initialize rekey anchor
        rekey_anchor = 0.0
        breakout_occurred = False
        pending_anchor = None  # (value, activation_bar) scheduled by retest scan

        # Calculate rekeyed coordinates
        for i in range(len(morphic_coordinates)):
            current_coord = morphic_coordinates.iloc[i]

            # Activate a scheduled rekey once its confirmation bar is reached.
            if pending_anchor is not None and i >= pending_anchor[1]:
                rekey_anchor = pending_anchor[0]
                pending_anchor = None

            # Check if we've had a breakout
            if abs(current_coord) > boundary:
                breakout_occurred = True

            # Check if we've had a successful retest (evidence in i+1..i+4)
            if breakout_occurred and i > 0:
                for j in range(i + 1, min(i + 5, len(morphic_coordinates))):
                    if abs(morphic_coordinates.iloc[j]) > boundary:
                        # Schedule the re-anchor at the retest bar j; the
                        # earliest confirmed activation wins.
                        if pending_anchor is None or j < pending_anchor[1]:
                            pending_anchor = (current_coord, j)
                        breakout_occurred = False
                        break

            # Calculate rekeyed coordinate
            if rekey_anchor != 0.0:
                displacement = current_coord - rekey_anchor
                rekeyed.iloc[i] = displacement
            else:
                rekeyed.iloc[i] = current_coord

        return rekeyed
        
    def _rekey_variant_c(self, morphic_coordinates: pd.Series,
                        boundary: float, step: float) -> pd.Series:
        """
        RKEY-C: Re-anchor only after next sigma state is reached and previous state survives.

        ROBUST (R0.5.1 repair): NaN inputs (warm-up) emit NO rekey decision at
        that bar (ready-guard). NaN is never coerced and no default values are
        invented; int() conversions are guarded so int(NaN) cannot crash.

        Args:
            morphic_coordinates: Original morphic coordinates
            boundary: Sigma state boundary
            step: Sigma state step size

        Returns:
            Rekeyed coordinates
        """
        rekeyed = pd.Series(index=morphic_coordinates.index)

        # Initialize rekey anchor
        rekey_anchor = 0.0

        # Calculate rekeyed coordinates
        for i in range(len(morphic_coordinates)):
            current_coord = morphic_coordinates.iloc[i]

            # Ready-guard: a rekey decision requires the current coordinate to
            # be finite. Not-ready bars emit no new rekey (no synthetic
            # rekeys) and keep the current anchor state.
            if not np.isnan(current_coord) and abs(current_coord) > boundary:
                prev_coord = morphic_coordinates.iloc[i - 1] if i > 0 else 0.0
                if np.isnan(prev_coord):
                    prev_state = 0  # not ready: no prior state (guarded below)
                else:
                    prev_state = int(abs(prev_coord) // step)
                current_state = int(abs(current_coord) // step)

                if current_state > prev_state:
                    if i >= 5:  # Need at least 5 bars
                        # Check if previous state survives (3 consecutive bars
                        # above boundary); a NaN in the window = not ready.
                        window = morphic_coordinates.iloc[max(0, i - 2):i + 1]
                        if window.notna().all():
                            above_count = sum(abs(window) > boundary)
                            if above_count >= 3:
                                # Re-anchor after next sigma state is reached and previous state survives
                                rekey_anchor = current_coord

            # Calculate rekeyed coordinate
            if rekey_anchor != 0.0:
                displacement = current_coord - rekey_anchor
                rekeyed.iloc[i] = displacement
            else:
                rekeyed.iloc[i] = current_coord

        return rekeyed
        
    def analyze_rekey_variants(self, rekey_variants: Dict[str, pd.Series],
                              prices: pd.Series) -> Dict[str, Dict]:
        """
        Analyze all rekey variants.
        
        Args:
            rekey_variants: Dictionary with rekey variant names as keys
            prices: Price series
            
        Returns:
            Dictionary with analysis results for each rekey variant
        """
        analysis = {}
        
        for variant_name, rekeyed_coords in rekey_variants.items():
            # Calculate forward returns
            forward_returns = []
            for i in range(len(rekeyed_coords)):
                if i + 1 < len(prices):
                    ret = np.log(prices.iloc[i + 1] / prices.iloc[i])
                    forward_returns.append(ret)
                    
            if len(forward_returns) > 0:
                analysis[variant_name] = {
                    'mean_return': np.mean(forward_returns),
                    'std_return': np.std(forward_returns),
                    'median_return': np.median(forward_returns),
                    'count': len(forward_returns),
                    'sharpe_ratio': np.mean(forward_returns) / np.std(forward_returns) if np.std(forward_returns) > 0 else np.nan
                }
            else:
                analysis[variant_name] = {
                    'mean_return': np.nan,
                    'std_return': np.nan,
                    'median_return': np.nan,
                    'sharpe_ratio': np.nan,
                    'count': 0
                }
                
        return analysis
        
    def analyze_rekey_effectiveness(self, rekey_variants: Dict[str, pd.Series],
                                   prices: pd.Series) -> Dict:
        """
        Analyze effectiveness of rekey variants compared to no rekey.
        
        Args:
            rekey_variants: Dictionary with rekey variant names as keys
            prices: Price series
            
        Returns:
            Dictionary with effectiveness analysis
        """
        # Get no rekey variant
        no_rekey = rekey_variants.get('NO_REKEY')
        if no_rekey is None:
            return {}
            
        effectiveness = {}
        
        for variant_name, rekeyed_coords in rekey_variants.items():
            if variant_name == 'NO_REKEY':
                continue
                
            # Calculate forward returns for both variants
            no_rekey_returns = []
            rekey_returns = []
            
            for i in range(len(rekeyed_coords)):
                if i + 1 < len(prices):
                    no_rekey_ret = np.log(prices.iloc[i + 1] / prices.iloc[i])
                    rekey_ret = np.log(prices.iloc[i + 1] / prices.iloc[i])  # Same returns, different coordinates
                    
                    no_rekey_returns.append(no_rekey_ret)
                    rekey_returns.append(rekey_ret)
                    
            if len(no_rekey_returns) > 0 and len(rekey_returns) > 0:
                # Calculate effectiveness metrics
                mean_diff = np.mean(rekey_returns) - np.mean(no_rekey_returns)
                std_diff = np.std(rekey_returns - no_rekey_returns)
                
                effectiveness[variant_name] = {
                    'mean_difference': mean_diff,
                    'std_difference': std_diff,
                    't_statistic': mean_diff / std_diff if std_diff > 0 else np.nan,
                    'p_value': 2 * (1 - stats.t.cdf(abs(mean_diff / std_diff), len(no_rekey_returns) - 1)) if std_diff > 0 else np.nan,
                    'effect_size': mean_diff / std_diff if std_diff > 0 else np.nan,
                    'no_rekey_mean': np.mean(no_rekey_returns),
                    'rekey_mean': np.mean(rekey_returns),
                    'no_rekey_std': np.std(no_rekey_returns),
                    'rekey_std': np.std(rekey_returns)
                }
            else:
                effectiveness[variant_name] = {
                    'mean_difference': np.nan,
                    'std_difference': np.nan,
                    't_statistic': np.nan,
                    'p_value': np.nan,
                    'effect_size': np.nan,
                    'no_rekey_mean': np.nan,
                    'rekey_mean': np.nan,
                    'no_rekey_std': np.nan,
                    'rekey_std': np.nan
                }
                
        return effectiveness
        
    def analyze_rekey_continuation(self, rekey_variants: Dict[str, pd.Series],
                                  prices: pd.Series) -> Dict:
        """
        Analyze continuation after rekey events.
        
        Args:
            rekey_variants: Dictionary with rekey variant names as keys
            prices: Price series
            
        Returns:
            Dictionary with continuation analysis
        """
        continuation_analysis = {}
        
        for variant_name, rekeyed_coords in rekey_variants.items():
            if variant_name == 'NO_REKEY':
                continue
                
            # Calculate continuation metrics
            # For simplicity, we'll use a basic approach
            # In a real implementation, this would be more sophisticated
            
            # Calculate average rekey coordinate
            avg_rekey_coord = rekeyed_coords.mean()
            
            # Calculate forward returns after rekey events
            forward_returns = []
            for i in range(len(rekeyed_coords)):
                if i + 1 < len(prices):
                    ret = np.log(prices.iloc[i + 1] / prices.iloc[i])
                    forward_returns.append(ret)
                    
            if len(forward_returns) > 0:
                continuation_analysis[variant_name] = {
                    'avg_rekey_coordinate': avg_rekey_coord,
                    'mean_forward_return': np.mean(forward_returns),
                    'std_forward_return': np.std(forward_returns),
                    'median_forward_return': np.median(forward_returns),
                    'count': len(forward_returns),
                    'positive_return_rate': sum(1 for r in forward_returns if r > 0) / len(forward_returns)
                }
            else:
                continuation_analysis[variant_name] = {
                    'avg_rekey_coordinate': np.nan,
                    'mean_forward_return': np.nan,
                    'std_forward_return': np.nan,
                    'median_forward_return': np.nan,
                    'count': 0,
                    'positive_return_rate': np.nan
                }
                
        return continuation_analysis
        
    def analyze_rekey_trends(self, rekey_variants: Dict[str, pd.Series],
                           prices: pd.Series) -> Dict:
        """
        Analyze trends after rekey events.
        
        Args:
            rekey_variants: Dictionary with rekey variant names as keys
            prices: Price series
            
        Returns:
            Dictionary with trend analysis
        """
        trend_analysis = {}
        
        for variant_name, rekeyed_coords in rekey_variants.items():
            if variant_name == 'NO_REKEY':
                continue
                
            # Calculate trend metrics
            # For simplicity, we'll use a basic approach
            # In a real implementation, this would be more sophisticated
            
            # Calculate average rekey coordinate
            avg_rekey_coord = rekeyed_coords.mean()
            
            # Calculate trend direction
            # For simplicity, we'll use the sign of the average rekey coordinate
            trend_direction = np.sign(avg_rekey_coord)
            
            # Calculate trend strength
            trend_strength = abs(avg_rekey_coord) / rekeyed_coords.std() if rekeyed_coords.std() > 0 else 0
            
            trend_analysis[variant_name] = {
                'avg_rekey_coordinate': avg_rekey_coord,
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'trend_persistence': trend_strength * 0.5,  # Placeholder
                'trend_capture_ratio': trend_strength * 0.8,  # Placeholder
                'trend_false_breakout_rate': 1.0 - trend_strength * 0.2  # Placeholder
            }
            
        return trend_analysis