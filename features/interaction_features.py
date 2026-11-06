from __future__ import annotations

import pandas as pd

from features.sentiment_features import rolling_z


def interaction_features(price_f: pd.DataFrame, sent_f: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(index=price_f.index)
    s = sent_f["sent_mean"].reindex(price_f.index)
    f["sent_x_momentum"] = s * price_f["momentum_10"]
    f["sent_x_vol"] = s * price_f["vol_10"]
    f["sent_x_postvol"] = s * sent_f["log_post_count"].reindex(price_f.index)
    f["sent_accel_x_ret"] = sent_f["sent_accel"].reindex(price_f.index) * price_f["ret_1"]
    # divergence D_t = Z(S_t) - Z(R_t), both causal rolling z-scores
    f["sent_price_divergence"] = rolling_z(s) - rolling_z(price_f["logret_1"])
    return f
