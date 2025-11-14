"""
Causal/Evidence Engine for Dyocense v4.0

Provides basic statistical tooling to:
- detect correlations across metrics
- detect Granger causality on time series
- explain changes with simple root-cause analysis
- generate brief natural language explanations

This module intentionally ships with light-weight dependencies and will
use numpy/scipy/statsmodels if available, otherwise gracefully degrade.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    from scipy.stats import pearsonr
    from statsmodels.tsa.stattools import grangercausalitytests
except Exception:  # pragma: no cover - optional deps
    np = None
    pearsonr = None
    grangercausalitytests = None


CorrelationResult = Dict[str, Any]
GrangerResult = Dict[str, Any]


class CausalEngine:
    """Simple causal evidence utilities."""

    def detect_correlations(self, series: Dict[str, List[float]]) -> List[CorrelationResult]:
        """
        Compute pairwise Pearson correlations with p-values when scipy is available.
        Falls back to numpy.corrcoef without p-values.
        """
        try:
            if not series or np is None or pearsonr is None:
                # Fallback using numpy only (no p-values)
                if not series or np is None:
                    return []
                keys = list(series.keys())
                n = len(keys)
                results: List[CorrelationResult] = []
                length_set = {len(v) for v in series.values()}
                if len(length_set) != 1:
                    return []
                for i in range(n):
                    for j in range(i + 1, n):
                        a, b = keys[i], keys[j]
                        x = np.asarray(series[a])
                        y = np.asarray(series[b])
                        if np.isnan(x).any() or np.isnan(y).any():
                            continue
                        coeff = float(np.corrcoef(x, y)[0, 1])
                        results.append({"a": a, "b": b, "corr": coeff, "p_value": None})
                results.sort(key=lambda r: abs(r["corr"]), reverse=True)
                return results
            keys = list(series.keys())
            n = len(keys)
            results: List[CorrelationResult] = []
            length_set = {len(v) for v in series.values()}
            if len(length_set) != 1:
                return []
            for i in range(n):
                for j in range(i + 1, n):
                    a, b = keys[i], keys[j]
                    x = np.asarray(series[a])
                    y = np.asarray(series[b])
                    if np.isnan(x).any() or np.isnan(y).any():
                        continue
                    res = pearsonr(x, y)  # scipy returns an object with statistic/pvalue or a tuple
                    try:
                        corr_val = float(getattr(res, "statistic"))  # type: ignore[attr-defined]
                        p_val = float(getattr(res, "pvalue"))  # type: ignore[attr-defined]
                    except Exception:
                        # Fallback to tuple-style access
                        corr_val = float(res[0])  # type: ignore[index]
                        p_val = float(res[1])  # type: ignore[index]
                    results.append({"a": a, "b": b, "corr": corr_val, "p_value": p_val})
            results.sort(key=lambda r: abs(r["corr"]), reverse=True)
            return results
        except Exception:
            return []

    def granger_causality(self, series_xy: Dict[str, List[float]], max_lag: int = 3, alpha: float = 0.05) -> List[GrangerResult]:
        """Placeholder implementation; returns empty list if optional deps missing or bad input."""
        try:
            if grangercausalitytests is None or np is None:
                return []
            if len(series_xy) != 2:
                return []
            names = list(series_xy.keys())
            a, b = names[0], names[1]
            x = np.asarray(series_xy[a])
            y = np.asarray(series_xy[b])
            if len(x) != len(y):
                return []
            results: List[GrangerResult] = []
            for cause, effect, arr in [(a, b, np.column_stack([y, x])), (b, a, np.column_stack([x, y]))]:
                try:
                    test_res = grangercausalitytests(arr, maxlag=max_lag, verbose=False)
                    best = None
                    for lag, detail in test_res.items():
                        p_val = float(detail[0]["ssr_ftest"][1])
                        if best is None or p_val < best[1]:
                            best = (lag, p_val)
                    if best and best[1] <= alpha:
                        results.append({"cause": cause, "effect": effect, "lag": int(best[0]), "p_value": float(best[1])})
                except Exception:
                    continue
            return results
        except Exception:
            return []

    def fit_linear(self, x: List[float], y: List[float]) -> Optional[Dict[str, float]]:
        """
        Fit simple linear relationship y = m*x + c using numpy.
        Returns slope m, intercept c, and r2. None if invalid.
        """
        try:
            if np is None:
                return None
            x_arr = np.asarray(x, dtype=float)
            y_arr = np.asarray(y, dtype=float)
            if x_arr.size < 2 or y_arr.size < 2 or x_arr.size != y_arr.size:
                return None
            m, c = np.polyfit(x_arr, y_arr, 1)
            y_hat = m * x_arr + c
            ss_res = float(np.sum((y_arr - y_hat) ** 2))
            ss_tot = float(np.sum((y_arr - np.mean(y_arr)) ** 2))
            r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            return {"slope": float(m), "intercept": float(c), "r2": float(r2)}
        except Exception:
            return None

    def what_if(self, cause: List[float], effect: List[float], delta_cause: float) -> Optional[Dict[str, float]]:
        """
        Estimate change in effect for a given change in cause using linear fit.
        Returns predicted_delta and model diagnostics.
        """
        model = self.fit_linear(cause, effect)
        if not model:
            return None
        predicted_delta = model["slope"] * float(delta_cause)
        return {"predicted_delta": predicted_delta, **model}

    def infer_drivers(self, target: List[float], drivers: Dict[str, List[float]]) -> List[Dict[str, float]]:
        """
        Infer driver importance via standardized linear regression (OLS via lstsq).
        Returns list of {name, beta} sorted by |beta| desc.
        """
        try:
            if np is None or not drivers:
                return []
            y = np.asarray(target, dtype=float)
            X_list = []
            names = []
            for name, values in drivers.items():
                v = np.asarray(values, dtype=float)
                if v.size != y.size:
                    continue
                # Standardize to zero mean / unit variance to compare betas
                v_std = (v - v.mean()) / (v.std() if v.std() > 0 else 1.0)
                X_list.append(v_std)
                names.append(name)
            if not X_list:
                return []
            X = np.vstack(X_list).T
            X = np.column_stack([np.ones(X.shape[0]), X])  # intercept
            beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
            # beta[0] is intercept
            betas = beta[1:]
            results = [{"name": n, "beta": float(b)} for n, b in zip(names, betas)]
            results.sort(key=lambda d: abs(d["beta"]), reverse=True)
            return results
        except Exception:
            return []

    def explain_change(self, metric: str, before: float, after: float, drivers: Dict[str, float]) -> str:
        """
        Provide a simple explanation of a change in a metric using a set of driver contributions.

        Args:
            metric: metric name
            before: value before
            after: value after
            drivers: mapping of driver -> contribution (positive/negative)
        """
        delta = after - before
        if not drivers:
            return f"{metric} changed by {delta:.2f}. No driver data provided."
        top = sorted(drivers.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]
        parts = [f"{k} ({v:+.2f})" for k, v in top]
        return f"{metric} changed by {delta:+.2f}. Top drivers: {', '.join(parts)}."

    def generate_explanation(self, correlations: List[CorrelationResult], granger: List[GrangerResult]) -> str:
        """Compose a short human-readable explanation from results."""
        lines: List[str] = []
        if correlations:
            top = correlations[0]
            lines.append(
                f"Strongest correlation: {top['a']} vs {top['b']} (r={top['corr']:.2f}, p={top['p_value']:.3f})."
            )
        if granger:
            g = granger[0]
            lines.append(
                f"Potential causality: {g['cause']} -> {g['effect']} at lag {g['lag']} (p={g['p_value']:.3f})."
            )
        return " ".join(lines) if lines else "No significant relationships detected."
