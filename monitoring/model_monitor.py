"""Model monitoring, retraining triggers and promotion rule.

A newly trained model is NOT promoted merely because it is newer: it must beat the incumbent on a common
out-of-sample window with a one-sided Diebold-Mariano test (and not be worse in point estimate).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from validation.statistical_tests import diebold_mariano


@dataclass(frozen=True)
class RetrainPolicy:
    max_age_days: int = 90
    degradation_ratio: float = 1.25      # recent RMSE / historical RMSE
    psi_alert: float = 0.25
    min_recent: int = 40


def rolling_degradation(errors: pd.Series, recent: int = 60) -> dict:
    """errors: forecast errors indexed by time. Compares RMSE of the latest `recent` points with all earlier ones."""
    e = errors.dropna()
    if len(e) < 2 * recent:
        return {"ratio": np.nan, "recent_rmse": np.nan, "history_rmse": np.nan}
    r, h = e.iloc[-recent:], e.iloc[:-recent]
    rr, hh = float(np.sqrt((r ** 2).mean())), float(np.sqrt((h ** 2).mean()))
    return {"ratio": rr / hh, "recent_rmse": rr, "history_rmse": hh}


def should_retrain(policy: RetrainPolicy, model_age_days: float, degradation_ratio: float | None,
                   max_feature_psi: float | None) -> tuple[bool, list[str]]:
    reasons = []
    if model_age_days >= policy.max_age_days:
        reasons.append(f"model age {model_age_days:.0f}d >= {policy.max_age_days}d")
    if degradation_ratio is not None and not np.isnan(degradation_ratio) and degradation_ratio >= policy.degradation_ratio:
        reasons.append(f"error ratio {degradation_ratio:.2f} >= {policy.degradation_ratio}")
    if max_feature_psi is not None and not np.isnan(max_feature_psi) and max_feature_psi >= policy.psi_alert:
        reasons.append(f"feature PSI {max_feature_psi:.2f} >= {policy.psi_alert}")
    return bool(reasons), reasons


def promote_candidate(incumbent_errors: np.ndarray, candidate_errors: np.ndarray, h: int = 1, alpha: float = 0.05) -> dict:
    """Promote only if the candidate has lower squared error AND the one-sided DM test is significant at alpha."""
    inc, cand = np.asarray(incumbent_errors, float), np.asarray(candidate_errors, float)
    dm = diebold_mariano(cand, inc, h=h)                       # negative => candidate better
    better = np.mean(cand ** 2) < np.mean(inc ** 2)
    one_sided_p = dm["p_value"] / 2 if dm["dm"] < 0 else 1 - dm["p_value"] / 2
    promote = bool(better and not np.isnan(one_sided_p) and one_sided_p < alpha)
    return {"promote": promote, "one_sided_p": float(one_sided_p), "mse_incumbent": float(np.mean(inc ** 2)),
            "mse_candidate": float(np.mean(cand ** 2)), "n": int(len(inc))}
