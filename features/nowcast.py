"""n+0 nowcast: estimate day D's close-to-close return using ONLY information available at 09:30 exchange time on D.

Definition (kept distinct from the n+1..n+5 forecasts and never a trivial identity):
  target   y_0(D) = ln(P_D / P_{D-1})                       (known at D's close)
  features price features through D-1's close  (computed on the series, then shifted one row)
           sentiment from posts in the window (D-1 09:30, D 09:30]   (cutoff = pre-open)
  `price`  column = P_{D-1}, so predicted P_D = price * exp(y0_hat).
Interpretation caveat: the overnight gap is part of y_0 and is not a feature, so pre-open sentiment may partly
reflect overnight news that already moved the open; this measures nowcasting skill, not market-timing ability.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from features.interaction_features import interaction_features
from features.price_features import price_features
from features.sentiment_features import sentiment_features

PREOPEN = (9, 30)


def build_nowcast_table(px: pd.DataFrame, agg_preopen: pd.DataFrame,
                        target: str = "close_to_close") -> tuple[pd.DataFrame, dict[str, list[str]]]:
    pf = price_features(px).shift(1)                       # row D: information through D-1 close
    sf = sentiment_features(agg_preopen).reindex(px.index)  # row D: posts up to D 09:30
    inter = interaction_features(pf, sf)
    lc = np.log(px["close"])
    pxf = pf.add_prefix("px_")
    if target == "intraday":
        # Actionable variant: at the open, predict open->close. The opening gap is KNOWN at that moment and is
        # therefore allowed as a price feature (it uses open_D only, never high/low/close of D).
        y0 = (lc - np.log(px["open"])).rename("y_0")
        pxf["px_gap"] = np.log(px["open"] / px["close"].shift(1))
        price = px["open"].rename("price")
    elif target == "close_to_close":
        y0 = (lc - lc.shift(1)).rename("y_0")
        price = px["close"].shift(1).rename("price")
    else:
        raise ValueError(target)
    table = pd.concat([price, pxf, sf.add_prefix("sn_"), inter.add_prefix("ix_"), y0], axis=1)
    sets = {
        "A_price": [c for c in table if c.startswith("px_")],
        "B_sentiment": [c for c in table if c.startswith("sn_")],
        "C_combined": [c for c in table if c.startswith(("px_", "sn_", "ix_"))],
    }
    return table, sets
