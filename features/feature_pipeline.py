"""Build the model-ready table: features for the three controlled experiments + targets."""
from __future__ import annotations

import pandas as pd

from features.interaction_features import interaction_features
from features.price_features import forward_targets, price_features
from features.sentiment_features import sentiment_features


def build_model_table(px: pd.DataFrame, agg: pd.DataFrame, horizons: list[int],
                      include_leaky: bool = False) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """px: indexed by trading_day (open/high/low/close). agg: output of aggregate_daily.
    Returns (table, feature_sets) with sets A=price only, B=sentiment only, C=price+sentiment(+interactions)."""
    pf = price_features(px)
    sf = sentiment_features(agg, include_leaky).reindex(px.index)
    inter = interaction_features(pf, sf)
    y = forward_targets(px, horizons)
    table = pd.concat([px[["close"]].rename(columns={"close": "price"}),
                       pf.add_prefix("px_"), sf.add_prefix("sn_"), inter.add_prefix("ix_"), y], axis=1)
    sets = {
        "A_price": [c for c in table if c.startswith("px_")],
        "B_sentiment": [c for c in table if c.startswith("sn_")],
        "C_combined": [c for c in table if c.startswith(("px_", "sn_", "ix_"))],
    }
    return table, sets
