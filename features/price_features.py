"""Price features. Row t uses only data up to and including bar t's close (the prediction cutoff)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def price_features(px: pd.DataFrame, close_col: str = "close") -> pd.DataFrame:
    """px indexed by trading_day with open/high/low/close. All features are causal."""
    c = px[close_col]
    lr = np.log(c).diff()
    f = pd.DataFrame(index=px.index)
    f["ret_1"] = c.pct_change(1)
    f["logret_1"] = lr
    for k in (2, 3, 5, 10):
        f[f"ret_{k}"] = c.pct_change(k)
    for w in (5, 10, 20):
        f[f"vol_{w}"] = lr.rolling(w).std()
        f[f"mean_ret_{w}"] = lr.rolling(w).mean()
        f[f"dev_ma_{w}"] = c / c.rolling(w).mean() - 1
    f["momentum_10"] = c / c.shift(10) - 1
    f["hl_range"] = (px["high"] - px["low"]) / c
    f["range_10"] = (px["high"].rolling(10).max() - px["low"].rolling(10).min()) / c
    f["ret_accel"] = lr.diff()
    ma5, ma20 = c.rolling(5).mean(), c.rolling(20).mean()
    f["trend_strength"] = (ma5 - ma20) / c.rolling(20).std()
    f["direction_1"] = np.sign(lr)
    return f


def forward_targets(px: pd.DataFrame, horizons: list[int], close_col: str = "close") -> pd.DataFrame:
    """y_h = ln(P_{t+h} / P_t). Uses FUTURE prices by design - never a feature."""
    lc = np.log(px[close_col])
    return pd.DataFrame({f"y_{h}": lc.shift(-h) - lc for h in horizons}, index=px.index)
