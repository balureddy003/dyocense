"""
Advanced Seasonality Detection (Phase 3)

Optional module for micro-seasonality pattern detection using statsmodels.
Enabled via ENABLE_MICRO_SEASONALITY flag.

Provides:
- Day-of-week patterns (e.g., weekend vs weekday sales)
- Hour-of-day patterns (e.g., lunch rush, evening peak)
- Sub-weekly cycles that standard Holt-Winters might miss
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Feature flag for micro-seasonality
ENABLE_MICRO_SEASONALITY = os.getenv("ENABLE_MICRO_SEASONALITY", "").lower() in ("1", "true", "yes")

# Check for optional dependencies
try:
    import numpy as np
    import pandas as pd
    from statsmodels.tsa.seasonal import seasonal_decompose
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    np = None
    pd = None
    seasonal_decompose = None


def detect_micro_seasonality(
    values: List[float],
    freq_hint: Optional[str] = None,
    min_periods: int = 14,
) -> Dict[str, Any]:
    """Detect micro-seasonal patterns in time series data (Phase 3).
    
    Args:
        values: Time series values (most recent last)
        freq_hint: Frequency hint ('H' for hourly, 'D' for daily, 'W' for weekly)
        min_periods: Minimum data points required (default 14 for 2 weeks)
    
    Returns:
        Dict with keys:
        - has_micro_seasonality: bool
        - patterns: Dict[str, float] (e.g., {'day_of_week': 0.15, 'hour_of_day': 0.22})
        - recommended_periods: List[int] (suggested seasonal periods)
        - strength: float (0.0-1.0, overall seasonality strength)
        - reason: str (explanation or error message)
    """
    if not ENABLE_MICRO_SEASONALITY:
        return {
            "has_micro_seasonality": False,
            "patterns": {},
            "recommended_periods": [],
            "strength": 0.0,
            "reason": "Micro-seasonality detection disabled (ENABLE_MICRO_SEASONALITY not set)"
        }
    
    if not HAS_STATSMODELS:
        return {
            "has_micro_seasonality": False,
            "patterns": {},
            "recommended_periods": [],
            "strength": 0.0,
            "reason": "statsmodels not installed; install with: pip install statsmodels"
        }
    
    if len(values) < min_periods:
        return {
            "has_micro_seasonality": False,
            "patterns": {},
            "recommended_periods": [],
            "strength": 0.0,
            "reason": f"Insufficient data: {len(values)} points (need {min_periods}+)"
        }
    
    try:
        # Type guard for optional dependencies
        if pd is None or np is None or seasonal_decompose is None:
            raise ImportError("statsmodels dependencies not available")
        
        # Convert to pandas Series
        series = pd.Series(values)
        
        # Try multiple potential micro-seasonal periods
        candidate_periods = _get_candidate_periods(len(values), freq_hint)
        
        detected_patterns = {}
        max_strength = 0.0
        best_periods = []
        
        for period in candidate_periods:
            try:
                # Decompose with this period
                decomp = seasonal_decompose(
                    series,
                    model='additive',
                    period=period,
                    extrapolate_trend=period  # Use period as extrapolation points
                )
                
                # Measure seasonality strength
                seasonal_var = np.var(decomp.seasonal.dropna())
                residual_var = np.var(decomp.resid.dropna())
                
                if residual_var > 0:
                    strength = seasonal_var / (seasonal_var + residual_var)
                    strength = min(1.0, max(0.0, strength))
                    
                    if strength > 0.1:  # Threshold for meaningful seasonality
                        pattern_name = _period_to_pattern_name(period, freq_hint)
                        detected_patterns[pattern_name] = round(strength, 3)
                        
                        if strength > max_strength:
                            max_strength = strength
                            best_periods = [period]
                        elif abs(strength - max_strength) < 0.05:
                            best_periods.append(period)
            
            except Exception as e:
                logger.debug(f"[detect_micro_seasonality] Period {period} failed: {e}")
                continue
        
        has_seasonality = max_strength > 0.1
        
        return {
            "has_micro_seasonality": has_seasonality,
            "patterns": detected_patterns,
            "recommended_periods": sorted(best_periods),
            "strength": round(max_strength, 3),
            "reason": f"Detected {len(detected_patterns)} pattern(s)" if has_seasonality else "No significant patterns found"
        }
    
    except Exception as e:
        logger.warning(f"[detect_micro_seasonality] Analysis failed: {e}")
        return {
            "has_micro_seasonality": False,
            "patterns": {},
            "recommended_periods": [],
            "strength": 0.0,
            "reason": f"Analysis error: {str(e)}"
        }


def _get_candidate_periods(data_length: int, freq_hint: Optional[str]) -> List[int]:
    """Generate candidate seasonal periods based on data characteristics."""
    candidates = []
    
    # Hourly data (24 hours/day, 168 hours/week)
    if freq_hint == 'H':
        if data_length >= 48:
            candidates.append(24)  # Daily pattern
        if data_length >= 336:
            candidates.append(168)  # Weekly pattern
    
    # Daily data (7 days/week)
    elif freq_hint == 'D':
        if data_length >= 14:
            candidates.append(7)  # Weekly pattern
        if data_length >= 60:
            candidates.append(30)  # Monthly pattern (approx)
    
    # Weekly data
    elif freq_hint == 'W':
        if data_length >= 8:
            candidates.append(4)  # Monthly pattern (4 weeks)
        if data_length >= 26:
            candidates.append(13)  # Quarterly pattern (13 weeks)
    
    # Auto-detect if no hint
    else:
        # Try common patterns based on data length
        if data_length >= 14:
            candidates.append(7)
        if data_length >= 30:
            candidates.append(30)
        if data_length >= 48:
            candidates.append(24)
    
    # Filter to valid periods (at least 2 full cycles)
    candidates = [p for p in candidates if data_length >= (p * 2)]
    
    return candidates if candidates else [min(7, data_length // 2)]


def _period_to_pattern_name(period: int, freq_hint: Optional[str]) -> str:
    """Convert period to human-readable pattern name."""
    if period == 7:
        return "day_of_week"
    elif period == 24:
        return "hour_of_day"
    elif period == 30:
        return "day_of_month"
    elif period == 168:
        return "hour_of_week"
    elif period == 4:
        return "week_of_month"
    elif period == 13:
        return "week_of_quarter"
    else:
        return f"period_{period}"


def enhance_forecast_with_micro_seasonality(
    base_forecast: List[float],
    historical_values: List[float],
    detected_patterns: Dict[str, float],
) -> List[float]:
    """Adjust base forecast using detected micro-seasonal patterns (Phase 3).
    
    Args:
        base_forecast: Base forecast values from Holt-Winters or other method
        historical_values: Historical time series
        detected_patterns: Patterns from detect_micro_seasonality()
    
    Returns:
        Adjusted forecast values incorporating micro-seasonal effects
    """
    if not detected_patterns or not ENABLE_MICRO_SEASONALITY or not HAS_STATSMODELS:
        return base_forecast
    
    # Type guard
    if np is None:
        return base_forecast
    
    try:
        import math
        
        # For simplicity in Phase 3, apply a weighted adjustment based on pattern strength
        # More sophisticated implementations could use the actual seasonal component
        
        adjusted = []
        for i, base_val in enumerate(base_forecast):
            # Apply multiplicative adjustment based on dominant pattern strength
            max_strength = max(detected_patterns.values()) if detected_patterns else 0.0
            
            # Conservative adjustment: ±10% max based on seasonality strength
            adjustment_factor = 1.0 + (0.1 * max_strength * math.sin(2 * math.pi * i / 7))
            
            adjusted_val = base_val * adjustment_factor
            adjusted.append(adjusted_val)
        
        return adjusted
    
    except Exception as e:
        logger.warning(f"[enhance_forecast] Adjustment failed: {e}")
        return base_forecast
