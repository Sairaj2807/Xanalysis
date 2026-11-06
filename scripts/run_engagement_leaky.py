"""EXP-011 (LEAKY, exploratory): engagement-weighted sentiment vs simple sentiment.

The datasets only contain LIFETIME like/retweet/reply counts (collected long after posting), so these features are NOT
point-in-time and may contain post-event attention. Results here must NOT be read as predictive evidence; they only show
whether the leaky variants would even look better. Question 5 of the project cannot be answered cleanly with this data.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from config.settings import ROOT, load_settings  # noqa: E402
from validation.model_comparison import add_global_correction, incremental_value, run_walk_forward  # noqa: E402

MODELS = ["ridge", "extra_trees", "lightgbm"]


def main() -> None:
    a = load_settings().asset
    table = pd.read_parquet(ROOT / "data" / "model_ready" / f"model_table_{a.symbol}_primary.parquet")
    agg = pd.read_parquet(ROOT / "data" / "aggregated" / f"sentiment_daily_{a.symbol}_primary.parquet").set_index("trading_day")
    sets = json.loads((ROOT / "data" / "model_ready" / "feature_sets.json").read_text())
    table = table.copy()
    table["lk_sent_engagement_w"] = agg["sent_engagement_w"].reindex(table.index)
    table["lk_engagement_log"] = np.log1p(agg["engagement_total"].reindex(table.index))
    px = sets["A_price"]
    variants = {"A_price": px, "A+simple": px + ["sn_sent_mean"], "A+engagement_w_LEAKY": px + ["lk_sent_engagement_w"],
                "A+engagement_volume_LEAKY": px + ["lk_engagement_log"],
                "A+simple+engagement_w_LEAKY": px + ["sn_sent_mean", "lk_sent_engagement_w"]}
    preds = run_walk_forward(table, variants, MODELS, a.horizons, train_min=500, test_len=60, embargo=1, val_len=120)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_engagement_leaky"
    out = ROOT / "artifacts" / "runs" / run_id
    out.mkdir(parents=True, exist_ok=True)
    preds.to_parquet(out / "oos_predictions.parquet", index=False)
    parts = []
    for m in MODELS:
        for v in variants:
            if v == "A_price":
                continue
            i = incremental_value(preds, m, "A_price", v)
            i.insert(1, "variant", v)
            parts.append(i)
    inc = add_global_correction(pd.concat(parts, ignore_index=True))
    inc.to_csv(out / "ablation_incremental_value.csv", index=False)
    print(run_id, "tests:", int(inc.n_tests_global.iloc[0]))
    print(inc.pivot_table(index="variant", columns="horizon", values="improvement_rmse_pct", aggfunc="mean").round(2))
    print("raw p<.05:", int((inc.dm_p < .05).sum()), "positive among them:", int(((inc.dm_p < .05) & (inc.improvement_rmse_pct > 0)).sum()),
          "| global-Holm<.05:", int((inc.dm_p_holm_global < .05).sum()))
    print(inc.sort_values("improvement_rmse_pct", ascending=False).head(5)[
        ["model", "variant", "horizon", "improvement_rmse_pct", "dm_p", "dm_p_holm_global"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
