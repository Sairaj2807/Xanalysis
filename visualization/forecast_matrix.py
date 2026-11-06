"""Forecast matrix: predicted price at every horizon vs actual, per prediction timestamp."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def forecast_matrix(preds: pd.DataFrame, model: str, feature_set: str, horizons: list[int] | None = None) -> pd.DataFrame:
    """One row per prediction timestamp T (information cutoff = close of T):
    actual_price = P_T (the n+0 column is the observed price at T: a forecast model does not 'predict' it),
    pred_n+h / actual_n+h prices and predicted/actual log returns. Only out-of-sample rows."""
    g = preds[(preds.model == model) & (preds.feature_set == feature_set)]
    hs = horizons or sorted(g.horizon.unique())
    out = g.pivot_table(index="ts", columns="horizon", values=["pred_price", "actual_price", "y_pred", "y_true"], aggfunc="first")
    res = pd.DataFrame(index=out.index)
    res["actual_price_T (n+0)"] = g.drop_duplicates("ts").set_index("ts")["price"]
    for h in hs:
        res[f"pred_n+{h}"] = out[("pred_price", h)]
    for h in hs:
        res[f"actual_n+{h}"] = out[("actual_price", h)]
    for h in hs:
        res[f"pred_ret_n+{h}"] = out[("y_pred", h)]
        res[f"actual_ret_n+{h}"] = out[("y_true", h)]
    return res


def fig_forecast_matrix(mat: pd.DataFrame, last_n: int = 25) -> go.Figure:
    m = mat.tail(last_n)
    cols = ["actual_price_T (n+0)"] + [c for c in m.columns if c.startswith("pred_n+")]
    header = ["Timestamp"] + ["Actual price (n+0)"] + [c.replace("pred_", "Pred ") for c in cols[1:]]
    cells = [[str(i.date()) for i in m.index]] + [np.round(m[c].to_numpy(float), 2) for c in cols]
    return go.Figure(go.Table(header=dict(values=header), cells=dict(values=cells))).update_layout(
        title=f"Forecast matrix (last {last_n} out-of-sample timestamps)", height=60 + 24 * (last_n + 2))
