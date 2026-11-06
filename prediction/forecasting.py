"""Generate the latest multi-horizon forecast from the model table (fit on labelled history only)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from models.model_registry import make_model
from prediction.uncertainty import empirical_interval


def latest_forecast(table: pd.DataFrame, cols: list[str], model: str, horizons: list[int],
                    oos_preds: pd.DataFrame | None = None, feature_set: str | None = None, level: float = 0.8,
                    params: dict | None = None) -> pd.DataFrame:
    """Predict from the LAST row of `table` (information as of that row's close). Each horizon's model is fitted only on
    rows whose h-day target is already realised (so no future data enter training). Intervals come from past
    out-of-sample errors if `oos_preds` is given. This is a research forecast, not a trading recommendation."""
    last = table.index[-1]
    x_last = table[cols].iloc[[-1]].to_numpy(float)
    p0 = float(table["price"].iloc[-1])
    rows = []
    for h in horizons:
        y = table[f"y_{h}"]
        tr = table.index[y.notna() & (table.index < last)]
        m = make_model(model, **(params or {})).fit(table.loc[tr, cols].to_numpy(float), y.loc[tr].to_numpy(float))
        r = float(m.predict(x_last)[0])
        lo = hi = np.nan
        if oos_preds is not None:
            g = oos_preds[(oos_preds.model == model) & (oos_preds.horizon == h)]
            if feature_set:
                g = g[g.feature_set == feature_set]
            if len(g) >= 30:
                elo, ehi = empirical_interval((g["y_true"] - g["y_pred"]).to_numpy(), level)
                lo, hi = r + elo, r + ehi
        rows.append({"asof": last, "horizon": h, "pred_return": r, "pred_price": p0 * np.exp(r),
                     "price_lo": p0 * np.exp(lo) if not np.isnan(lo) else np.nan,
                     "price_hi": p0 * np.exp(hi) if not np.isnan(hi) else np.nan, "level": level, "model": model})
    return pd.DataFrame(rows)
