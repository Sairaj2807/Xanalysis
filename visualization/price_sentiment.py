"""Price-vs-sentiment charts (research dashboard section 13.1-13.2). All figures are plain Plotly objects."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def fig_price_sentiment(px: pd.DataFrame, agg: pd.DataFrame, preds: pd.DataFrame | None = None, model: str | None = None,
                        feature_set: str = "C_combined", horizon: int = 1) -> go.Figure:
    """Three panels with a shared time axis: price (OHLC + optional predicted/actual future price),
    sentiment (mean, positive/negative ratio, moving average), volume (posts, unique authors)."""
    a = agg.set_index("trading_day") if "trading_day" in agg.columns else agg
    a = a.reindex(px.index)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.5, 0.28, 0.22],
                        subplot_titles=("Price", "X sentiment (FinBERT/selected model)", "Post volume"))
    fig.add_trace(go.Candlestick(x=px.index, open=px["open"], high=px["high"], low=px["low"], close=px["close"],
                                 name="OHLC"), row=1, col=1)
    if preds is not None and model is not None:
        g = preds[(preds.model == model) & (preds.feature_set == feature_set) & (preds.horizon == horizon)].sort_values("ts")
        pos = px.index.get_indexer(pd.DatetimeIndex(g["ts"]))
        tgt = [px.index[p + horizon] if 0 <= p and p + horizon < len(px.index) else pd.NaT for p in pos]
        fig.add_trace(go.Scatter(x=tgt, y=g["pred_price"], name=f"predicted n+{horizon} ({model}/{feature_set})",
                                 mode="lines", line=dict(width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=tgt, y=g["actual_price"], name=f"actual n+{horizon}", mode="lines",
                                 line=dict(width=1, dash="dot")), row=1, col=1)
    m = a["mean_sentiment"]
    fig.add_trace(go.Scatter(x=a.index, y=m, name="mean sentiment", mode="lines", line=dict(width=1)), row=2, col=1)
    fig.add_trace(go.Scatter(x=a.index, y=m.rolling(10, min_periods=5).mean(), name="10-day MA", mode="lines"), row=2, col=1)
    fig.add_trace(go.Scatter(x=a.index, y=a["positive_ratio"], name="positive ratio", mode="lines", line=dict(width=1)), row=2, col=1)
    fig.add_trace(go.Scatter(x=a.index, y=a["negative_ratio"], name="negative ratio", mode="lines", line=dict(width=1)), row=2, col=1)
    fig.add_trace(go.Bar(x=a.index, y=a["post_count"], name="posts"), row=3, col=1)
    fig.add_trace(go.Scatter(x=a.index, y=a["unique_authors"], name="unique authors", mode="lines"), row=3, col=1)
    fig.update_layout(height=900, xaxis_rangeslider_visible=False, legend=dict(orientation="h"), margin=dict(t=50, b=30))
    return fig


def divergence_events(table: pd.DataFrame, thr: float = 2.0) -> pd.DataFrame:
    """D_t = Z(S_t) - Z(R_t) (causal rolling z-scores). Events are flagged descriptively only: divergence is
    NOT treated as a reversal signal (see research rules)."""
    d = table["ix_sent_price_divergence"]
    ev = pd.DataFrame({"divergence": d, "sentiment_z": table["sn_sent_z"], "return_1d": table["px_ret_1"]})
    ev["type"] = np.where(d > thr, "sentiment_above_price", np.where(d < -thr, "sentiment_below_price", ""))
    return ev[ev["type"] != ""]


def fig_divergence(table: pd.DataFrame, thr: float = 2.0) -> go.Figure:
    d = table["ix_sent_price_divergence"]
    colors = np.where(d > thr, "crimson", np.where(d < -thr, "royalblue", "lightgray"))
    fig = go.Figure(go.Bar(x=d.index, y=d, marker_color=colors, name="Z(S) - Z(R)"))
    fig.add_hline(y=thr, line_dash="dot")
    fig.add_hline(y=-thr, line_dash="dot")
    fig.update_layout(title="Sentiment-price divergence D = Z(S) - Z(R)  (descriptive, not a trading signal)", height=350)
    return fig


def fig_rolling_correlation(table: pd.DataFrame, window: int = 60) -> go.Figure:
    s = table["sn_sent_mean"]
    r_now = table["px_logret_1"]
    fut = table["y_1"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=table.index, y=s.rolling(window, min_periods=30).corr(r_now), name="sentiment vs SAME-day return"))
    fig.add_trace(go.Scatter(x=table.index, y=s.rolling(window, min_periods=30).corr(fut), name="sentiment vs NEXT-day return (y_1)"))
    fig.add_hline(y=0, line_dash="dot")
    fig.update_layout(title=f"Rolling {window}-day correlation: sentiment follows price (contemporaneous) but does not lead it",
                      height=380)
    return fig


def fig_scatter_future(table: pd.DataFrame, h: int = 1) -> go.Figure:
    d = table[["sn_sent_mean", f"y_{h}"]].dropna()
    x, y = d["sn_sent_mean"].to_numpy(), d[f"y_{h}"].to_numpy()
    b = np.polyfit(x, y, 1)
    xs = np.linspace(x.min(), x.max(), 50)
    fig = go.Figure(go.Scattergl(x=x, y=y, mode="markers", marker=dict(size=4, opacity=0.5), name="days"))
    fig.add_trace(go.Scatter(x=xs, y=np.polyval(b, xs), name=f"OLS slope {b[0]:.4f}"))
    fig.update_layout(title=f"Daily mean sentiment vs future {h}-day log return (corr {np.corrcoef(x, y)[0, 1]:.3f})",
                      xaxis_title="mean sentiment", yaxis_title=f"y_{h}", height=380)
    return fig


def fig_volume_spikes(table: pd.DataFrame, thr: float = 2.0) -> go.Figure:
    z = table["sn_post_count_z"]
    fig = go.Figure(go.Scatter(x=table.index, y=z, mode="lines", name="log post-count z"))
    sp = z[z > thr]
    fig.add_trace(go.Scatter(x=sp.index, y=sp, mode="markers", name=f"spike (z>{thr})", marker=dict(color="crimson")))
    fig.update_layout(title="Sentiment-volume spikes (proxy for event days; not news)", height=340)
    return fig
