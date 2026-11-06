"""Model/diagnostic charts and the HTML dashboard assembler."""
from __future__ import annotations

import html
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def fig_forecast_vs_actual(preds: pd.DataFrame, model: str, feature_set: str, horizon: int) -> go.Figure:
    g = preds[(preds.model == model) & (preds.feature_set == feature_set) & (preds.horizon == horizon)].sort_values("ts")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g["ts"], y=g["actual_price"], name="actual P(t+h)"))
    fig.add_trace(go.Scatter(x=g["ts"], y=g["pred_price"], name="predicted P(t+h)"))
    fig.update_layout(title=f"Forecast vs actual price, n+{horizon} ({model}/{feature_set}) - indexed by prediction date", height=380)
    return fig


def fig_residuals(preds: pd.DataFrame, model: str, feature_set: str, horizons: list[int]) -> go.Figure:
    fig = go.Figure()
    for h in horizons:
        g = preds[(preds.model == model) & (preds.feature_set == feature_set) & (preds.horizon == h)]
        fig.add_trace(go.Histogram(x=g["y_true"] - g["y_pred"], name=f"n+{h}", opacity=0.55, nbinsx=60))
    fig.update_layout(barmode="overlay", title=f"Forecast residual distribution ({model}/{feature_set})", height=360)
    return fig


def fig_error_by_horizon(metrics: pd.DataFrame) -> go.Figure:
    z = metrics[metrics.model == "zero_return"].set_index("horizon")["RMSE"]
    d = metrics[metrics.feature_set.isin(["A_price", "B_sentiment", "C_combined"])].copy()
    d["ratio"] = d["RMSE"] / d["horizon"].map(z)
    g = d.groupby(["feature_set", "horizon"])["ratio"].mean().reset_index()
    fig = go.Figure()
    for fs, s in g.groupby("feature_set"):
        fig.add_trace(go.Bar(x=[f"n+{h}" for h in s["horizon"]], y=s["ratio"], name=fs))
    fig.add_hline(y=1.0, line_dash="dot", annotation_text="persistence = 1.0")
    fig.update_layout(barmode="group", yaxis_range=[0.98, max(1.04, g["ratio"].max() + 0.01)], height=380,
                      title="RMSE relative to persistence by horizon (mean over models; <1 would beat persistence)")
    return fig


def fig_incremental(inc: pd.DataFrame) -> go.Figure:
    p = inc.pivot_table(index="model", columns="horizon", values="improvement_rmse_pct")
    fig = go.Figure(go.Heatmap(z=p.to_numpy(), x=[f"n+{c}" for c in p.columns], y=list(p.index), colorscale="RdBu", zmid=0,
                               text=np.round(p.to_numpy(), 2), texttemplate="%{text}"))
    fig.update_layout(title="RMSE improvement % from adding sentiment (C vs A); positive = sentiment helps", height=420)
    return fig


def fig_walk_forward(preds: pd.DataFrame, model: str, horizon: int) -> go.Figure:
    g = preds[(preds.model == model) & (preds.horizon == horizon)]
    r = g.assign(se=(g.y_true - g.y_pred) ** 2).groupby(["feature_set", "fold"])["se"].mean().pow(0.5).reset_index()
    fig = go.Figure()
    for fs, s in r.groupby("feature_set"):
        fig.add_trace(go.Scatter(x=s["fold"], y=s["se"], mode="lines+markers", name=fs))
    fig.update_layout(title=f"Walk-forward RMSE by fold ({model}, n+{horizon})", xaxis_title="fold", height=360)
    return fig


def fig_importance(summary: pd.DataFrame, title: str, top: int = 20) -> go.Figure:
    s = summary.sort_values("mean_importance", ascending=True).tail(top)
    return go.Figure(go.Bar(x=s["mean_importance"], y=s.index, orientation="h")).update_layout(title=title, height=520)


def fig_bar(df: pd.DataFrame, x: str, y: str, title: str, color: str | None = None) -> go.Figure:
    fig = go.Figure()
    if color:
        for k, s in df.groupby(color):
            fig.add_trace(go.Bar(x=s[x], y=s[y], name=str(k)))
    else:
        fig.add_trace(go.Bar(x=df[x], y=df[y]))
    return fig.update_layout(title=title, barmode="group", height=360)


def build_dashboard(sections: list[tuple[str, str, go.Figure]], title: str, notes: list[str] | None = None) -> str:
    """sections = [(heading, description, figure)]. Plotly.js is embedded once so the file works offline."""
    parts = [f"<html><head><meta charset='utf-8'><title>{html.escape(title)}</title>"
             "<style>body{font-family:Segoe UI,Arial,sans-serif;max-width:1300px;margin:auto;padding:12px}"
             "h2{border-bottom:1px solid #ccc;padding-top:18px}.note{background:#fff8e1;border-left:4px solid #f0ad00;padding:8px 12px}"
             "p.d{color:#444}</style></head><body>",
             f"<h1>{html.escape(title)}</h1><p>Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} from saved experiment artifacts.</p>"]
    for n in notes or []:
        parts.append(f"<div class='note'>{html.escape(n)}</div>")
    first = True
    for head, desc, fig in sections:
        parts.append(f"<h2>{html.escape(head)}</h2><p class='d'>{html.escape(desc)}</p>")
        parts.append(fig.to_html(full_html=False, include_plotlyjs=True if first else False))
        first = False
    parts.append("</body></html>")
    return "\n".join(parts)
