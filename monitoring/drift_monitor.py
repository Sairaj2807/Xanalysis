"""Distribution-drift monitoring: PSI and Kolmogorov-Smirnov between a reference (training) window and a recent window."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

PSI_WARN, PSI_ALERT = 0.10, 0.25          # conventional thresholds


def psi(reference: np.ndarray, recent: np.ndarray, bins: int = 10) -> float:
    """Population stability index with reference-quantile bins; NaNs ignored."""
    ref, rec = np.asarray(reference, float), np.asarray(recent, float)
    ref, rec = ref[~np.isnan(ref)], rec[~np.isnan(rec)]
    if len(ref) < bins or len(rec) < 5:
        return float("nan")
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    p = np.histogram(ref, edges)[0] / len(ref)
    q = np.histogram(rec, edges)[0] / len(rec)
    p, q = np.clip(p, 1e-6, None), np.clip(q, 1e-6, None)
    return float(np.sum((q - p) * np.log(q / p)))


def drift_report(reference: pd.DataFrame, recent: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    for c in cols:
        a, b = reference[c].to_numpy(float), recent[c].to_numpy(float)
        a2, b2 = a[~np.isnan(a)], b[~np.isnan(b)]
        ks = stats.ks_2samp(a2, b2) if len(a2) > 5 and len(b2) > 5 else None
        v = psi(a, b)
        rows.append({"feature": c, "psi": v, "ks_stat": ks.statistic if ks else np.nan, "ks_p": ks.pvalue if ks else np.nan,
                     "status": "n/a" if np.isnan(v) else "alert" if v >= PSI_ALERT else "warn" if v >= PSI_WARN else "ok"})
    return pd.DataFrame(rows).sort_values("psi", ascending=False, na_position="last")
