"""Empirical prediction intervals from past out-of-sample errors, and a calibration (coverage) check."""
from __future__ import annotations

import numpy as np
import pandas as pd


def empirical_interval(errors: np.ndarray, level: float = 0.8) -> tuple[float, float]:
    """Quantiles of (actual - predicted) errors; add to a point forecast to obtain an interval."""
    e = np.asarray(errors, float)
    e = e[~np.isnan(e)]
    a = (1 - level) / 2
    return float(np.quantile(e, a)), float(np.quantile(e, 1 - a))


def coverage_by_fold(preds: pd.DataFrame, model: str, feature_set: str, horizon: int, level: float = 0.8,
                     min_history: int = 100) -> dict:
    """Honest calibration check: for each fold build the interval ONLY from errors of earlier folds and measure how often
    the realised return falls inside. Returns nominal vs empirical coverage and the number of points tested."""
    g = preds[(preds.model == model) & (preds.feature_set == feature_set) & (preds.horizon == horizon)].sort_values("ts")
    err = (g["y_true"] - g["y_pred"]).to_numpy()
    folds = g["fold"].to_numpy()
    inside, n = 0, 0
    for f in sorted(set(folds)):
        hist = err[folds < f]
        if len(hist) < min_history:
            continue
        lo, hi = empirical_interval(hist, level)
        cur = err[folds == f]
        inside += int(((cur >= lo) & (cur <= hi)).sum())
        n += len(cur)
    return {"nominal": level, "empirical": inside / n if n else np.nan, "n": n}
