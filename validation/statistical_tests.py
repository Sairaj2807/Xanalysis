"""Significance tests for forecast comparison."""
from __future__ import annotations

import numpy as np
from scipy import stats


def diebold_mariano(e1: np.ndarray, e2: np.ndarray, h: int = 1, loss: str = "se") -> dict:
    """H0: equal predictive accuracy. d_t = L(e1_t) - L(e2_t). Negative statistic => model 1 has lower loss.
    HAC (Newey-West) variance with lag h-1 (forecast errors at horizon h overlap), Harvey-Leybourne-Newbold
    small-sample correction and a t(n-1) reference distribution."""
    e1, e2 = np.asarray(e1, float), np.asarray(e2, float)
    d = (e1 ** 2 - e2 ** 2) if loss == "se" else (np.abs(e1) - np.abs(e2))
    n = len(d)
    if n < 10 or np.allclose(d, d[0]):
        return {"dm": np.nan, "p_value": np.nan, "n": n, "mean_loss_diff": float(d.mean()) if n else np.nan}
    dbar = d.mean()
    lag = max(h - 1, 0)
    gamma0 = np.mean((d - dbar) ** 2)
    var = gamma0 + 2 * sum((1 - k / (lag + 1)) * np.mean((d[k:] - dbar) * (d[:-k] - dbar)) for k in range(1, lag + 1))
    var = max(var, 1e-18) / n
    dm = dbar / np.sqrt(var)
    hln = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    dm_c = dm * hln
    p = 2 * (1 - stats.t.cdf(abs(dm_c), df=n - 1))
    return {"dm": float(dm_c), "p_value": float(p), "n": n, "mean_loss_diff": float(dbar)}


def block_bootstrap_ci(x: np.ndarray, stat=np.mean, block: int = 5, n_boot: int = 2000, alpha: float = 0.05,
                       seed: int = 0) -> tuple[float, float, float]:
    """Moving-block bootstrap CI (preserves serial dependence from overlapping targets)."""
    x = np.asarray(x, float)
    n = len(x)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block))
    starts_max = max(n - block, 0)
    out = np.empty(n_boot)
    for i in range(n_boot):
        s = rng.integers(0, starts_max + 1, nb)
        out[i] = stat(np.concatenate([x[j:j + block] for j in s])[:n])
    return float(stat(x)), float(np.quantile(out, alpha / 2)), float(np.quantile(out, 1 - alpha / 2))


def directional_accuracy_test(y: np.ndarray, p: np.ndarray) -> dict:
    """One-sided binomial test of hit rate against the base rate of the more frequent class
    (so a model cannot 'win' merely by predicting the majority direction)."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    hits = int(np.sum((y > 0) == (p > 0)))
    n = len(y)
    base = max(np.mean(y > 0), 1 - np.mean(y > 0))
    res = stats.binomtest(hits, n, base, alternative="greater")
    return {"hit_rate": hits / n, "base_rate": float(base), "p_value": float(res.pvalue), "n": n}


def holm_bonferroni(p_values: list[float]) -> list[float]:
    """Holm step-down adjusted p-values (controls family-wise error across models/horizons)."""
    p = np.asarray(p_values, float)
    m = int(np.sum(~np.isnan(p)))   # NaN p-values are not tests and must not inflate the family size
    order = np.argsort(np.where(np.isnan(p), np.inf, p))
    adj = np.full(len(p), np.nan)
    running = 0.0
    for rank, i in enumerate(order):
        if np.isnan(p[i]):
            continue
        running = max(running, (m - rank) * p[i])
        adj[i] = min(running, 1.0)
    return adj.tolist()
