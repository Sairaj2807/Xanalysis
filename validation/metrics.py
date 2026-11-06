"""Per-horizon forecast metrics. Everything is computed on out-of-sample return forecasts."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import balanced_accuracy_score, matthews_corrcoef


def regression_metrics(y: np.ndarray, p: np.ndarray, benchmark: np.ndarray | None = None) -> dict:
    """OOS R^2 = 1 - SSE(model)/SSE(benchmark). Benchmark defaults to the zero-return (persistence) forecast,
    so a positive value means the model beats 'price does not change'."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    err = y - p
    b = np.zeros_like(y) if benchmark is None else np.asarray(benchmark, float)
    sse_b = np.sum((y - b) ** 2)
    return {
        "n": int(len(y)), "MAE": float(np.mean(np.abs(err))), "RMSE": float(np.sqrt(np.mean(err ** 2))),
        "MedAE": float(np.median(np.abs(err))), "mean_error": float(np.mean(p - y)),
        "R2_oos": float(1 - np.sum(err ** 2) / sse_b) if sse_b > 0 else np.nan,
    }


def price_mape(actual_price: np.ndarray, pred_price: np.ndarray) -> float:
    a = np.asarray(actual_price, float)
    return float(np.mean(np.abs((a - pred_price) / a))) * 100


def directional_metrics(y: np.ndarray, p: np.ndarray) -> dict:
    y, p = np.asarray(y, float), np.asarray(p, float)
    up_t, up_p = y > 0, p > 0
    tp, fp = np.sum(up_p & up_t), np.sum(up_p & ~up_t)
    tn, fn = np.sum(~up_p & ~up_t), np.sum(~up_p & up_t)
    out = {
        "directional_accuracy": float(np.mean(up_t == up_p)),
        "up_precision": float(tp / (tp + fp)) if tp + fp else np.nan,
        "down_precision": float(tn / (tn + fn)) if tn + fn else np.nan,
        "balanced_accuracy": float(balanced_accuracy_score(up_t, up_p)) if len(set(up_t)) > 1 else np.nan,
        "MCC": float(matthews_corrcoef(up_t, up_p)) if len(set(up_t)) > 1 and len(set(up_p)) > 1 else 0.0,
    }
    return out


def correlation_metrics(y: np.ndarray, p: np.ndarray) -> dict:
    if len(y) < 3 or np.std(p) == 0 or np.std(y) == 0:
        return {"IC": np.nan, "rank_IC": np.nan}
    return {"IC": float(stats.pearsonr(p, y)[0]), "rank_IC": float(stats.spearmanr(p, y)[0])}


def strategy_metrics(pred_signal: pd.Series, daily_ret: pd.Series, cost_bps: float = 5.0,
                     periods_per_year: int = 252) -> dict:
    """Rule: at the close of day t take position sign(pred_t) (long/short, size 1) and hold it over day t+1
    (earns daily_ret[t+1]); positions are re-evaluated every day. Cost = cost_bps per unit of |position change|,
    charged on the day the position changes. `daily_ret` is the simple 1-day close-to-close return series."""
    pos = np.sign(pred_signal).shift(1)               # position held during day t decided at t-1 close
    r = (pos * daily_ret).dropna()
    turnover = pos.diff().abs().reindex(r.index).fillna(0.0)
    net = r - turnover * cost_bps / 1e4
    eq = (1 + net).cumprod()
    dd = (eq / eq.cummax() - 1).min() if len(eq) else np.nan
    gains, losses = net[net > 0].sum(), -net[net < 0].sum()
    return {
        "gross_pnl": float(r.sum()), "net_pnl": float(net.sum()),
        "sharpe_net": float(net.mean() / net.std(ddof=1) * np.sqrt(periods_per_year)) if net.std(ddof=1) > 0 else np.nan,
        "max_drawdown": float(dd), "profit_factor": float(gains / losses) if losses > 0 else np.nan,
        "turnover": float(turnover.mean()), "n_days": int(len(net)), "cost_bps": cost_bps,
    }


def all_metrics(y: np.ndarray, p: np.ndarray, benchmark: np.ndarray | None = None) -> dict:
    return {**regression_metrics(y, p, benchmark), **directional_metrics(y, p), **correlation_metrics(y, p)}
