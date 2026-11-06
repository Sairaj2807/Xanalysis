"""Calendar heatmaps (week x weekday) of sentiment metrics with consistent, comparable colour scales."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def calendar_matrix(s: pd.Series) -> pd.DataFrame:
    """Rows = ISO (year, week) labels, columns = Mon..Fri."""
    d = s.dropna()
    iso = d.index.isocalendar()
    m = pd.DataFrame({"year": iso.year.to_numpy(), "week": iso.week.to_numpy(), "dow": d.index.day_of_week, "v": d.to_numpy()})
    m = m[m.dow < 5]
    piv = m.pivot_table(index=["year", "week"], columns="dow", values="v", aggfunc="mean")
    piv.columns = ["Mon", "Tue", "Wed", "Thu", "Fri"][: len(piv.columns)]
    piv.index = [f"{y}-W{w:02d}" for y, w in piv.index]
    return piv


def fig_heatmaps(agg: pd.DataFrame) -> go.Figure:
    a = agg.set_index("trading_day") if "trading_day" in agg.columns else agg
    metrics = {
        "Net sentiment (pos% - neg%)": (a["positive_ratio"] - a["negative_ratio"], True),
        "Positive ratio": (a["positive_ratio"], False),
        "Negative ratio": (a["negative_ratio"], False),
        "Post volume (log)": (np.log1p(a["post_count"]), False),
        "Sentiment acceleration": (a["mean_sentiment"].diff().diff(), True),
    }
    fig = make_subplots(rows=1, cols=len(metrics), subplot_titles=list(metrics), shared_yaxes=True, horizontal_spacing=0.02)
    for i, (name, (s, diverging)) in enumerate(metrics.items(), start=1):
        mat = calendar_matrix(s)
        lim = float(np.nanpercentile(np.abs(mat.to_numpy()), 98)) if diverging else None
        fig.add_trace(go.Heatmap(z=mat.to_numpy(), x=list(mat.columns), y=list(mat.index), colorscale="RdBu" if diverging else "Viridis",
                                 zmid=0 if diverging else None, zmin=-lim if diverging else None, zmax=lim if diverging else None,
                                 showscale=False, name=name), row=1, col=i)
    fig.update_yaxes(autorange="reversed", showticklabels=False)
    fig.update_yaxes(showticklabels=True, row=1, col=1)
    fig.update_layout(height=1500, margin=dict(t=60), title="Sentiment calendar heatmaps (rows = ISO weeks; diverging scales centred on 0)")
    return fig
