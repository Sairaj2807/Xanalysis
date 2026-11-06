"""Regime analysis of the sentiment effect (research questions 7 and 8).

Regimes use only information available at the prediction time:
- volatility regime: trailing 20-day volatility vs its expanding median up to the previous day;
- event-proxy regime: sentiment-volume spike (log post-count z-score > 2). NOTE this is a PROXY for news events,
  not news: no news data exist yet (Tavily not run).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from validation.statistical_tests import diebold_mariano


def vol_regime(table: pd.DataFrame, col: str = "px_vol_20", min_periods: int = 60) -> pd.Series:
    med = table[col].expanding(min_periods=min_periods).median().shift(1)   # strictly past information
    reg = pd.Series(np.where(table[col] > med, "high_vol", "low_vol"), index=table.index)
    reg[med.isna() | table[col].isna()] = np.nan
    return reg


def spike_regime(table: pd.DataFrame, col: str = "sn_post_count_z", thr: float = 2.0) -> pd.Series:
    reg = pd.Series(np.where(table[col] > thr, "volume_spike", "normal"), index=table.index)
    reg[table[col].isna()] = np.nan
    return reg


def improvement_by_regime(preds: pd.DataFrame, regimes: pd.Series, model: str, h: int, base: str = "A_price",
                          new: str = "C_combined") -> pd.DataFrame:
    g = preds[(preds.model == model) & (preds.horizon == h)]
    a = g[g.feature_set == base].set_index("ts")
    c = g[g.feature_set == new].set_index("ts")
    idx = a.index.intersection(c.index)
    rows = []
    for name, sub in regimes.reindex(idx).dropna().groupby(regimes.reindex(idx).dropna()):
        ii = sub.index
        ea, ec = (a.loc[ii].y_true - a.loc[ii].y_pred).to_numpy(), (c.loc[ii].y_true - c.loc[ii].y_pred).to_numpy()
        if len(ii) < 15:
            continue
        dm = diebold_mariano(ec, ea, h=h)
        rows.append({"model": model, "horizon": h, "regime": name, "n": len(ii),
                     "rmse_price": float(np.sqrt(np.mean(ea ** 2))), "rmse_combined": float(np.sqrt(np.mean(ec ** 2))),
                     "improvement_rmse_pct": 100 * (1 - np.sqrt(np.mean(ec ** 2)) / np.sqrt(np.mean(ea ** 2))),
                     "dm_p": dm["p_value"]})
    return pd.DataFrame(rows)
