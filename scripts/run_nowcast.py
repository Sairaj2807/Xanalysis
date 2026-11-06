"""EXP-009: n+0 nowcast of the same-day close-to-close return from information available at 09:30 exchange time.

Usage: python scripts/run_nowcast.py [sentiment_model_name] [--intraday]
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from config.settings import ROOT, load_settings  # noqa: E402
from features.nowcast import PREOPEN, build_nowcast_table  # noqa: E402
from scripts.build_features import FILTERS  # noqa: E402
from sentiment.finbert_analyzer import model_tag  # noqa: E402
from sentiment.sentiment_aggregation import aggregate_daily, attach_trading_day, author_prior_activity  # noqa: E402
from validation.model_comparison import (add_global_correction, incremental_value, metrics_table,  # noqa: E402
                                         run_walk_forward)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("run_nowcast")
MODELS = ["zero_return", "hist_mean", "ridge", "lasso", "extra_trees", "lightgbm"]


def main(sent_model: str | None = None, filter_name: str = "primary", target: str = "close_to_close") -> None:
    a = load_settings().asset
    tag = model_tag(sent_model) if sent_model else ""
    px = pd.read_parquet(ROOT / "data" / "raw" / "prices" / f"{a.symbol}_{a.bar_interval}.parquet")
    px["trading_day"] = px["bar_start_utc"].dt.tz_localize(None).dt.normalize()
    px = px.set_index("trading_day").sort_index()
    posts = pd.read_parquet(ROOT / "data" / "processed" / f"posts_{a.symbol}.parquet")
    sent = pd.read_parquet(ROOT / "data" / "processed" / f"sentiment_{a.symbol}{tag}.parquet")
    d = posts.merge(sent[["post_id", "sentiment_score", "confidence"]], on="post_id")
    d = d[FILTERS[filter_name](d)].copy()
    d["author_prior_posts"] = author_prior_activity(d)
    d = attach_trading_day(d, px.index, a.exchange_timezone, *PREOPEN)
    agg = aggregate_daily(d, px.index)
    table, sets = build_nowcast_table(px[["open", "high", "low", "close"]], agg, target)
    last = d["created_at"].max().normalize()
    table = table.loc["2015-02-02":last].dropna(subset=["y_0", "price"])
    log.info("nowcast table %s, first/last %s %s", table.shape, table.index.min().date(), table.index.max().date())

    preds = run_walk_forward(table, sets, MODELS, [0], train_min=500, test_len=60, embargo=1, val_len=120)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"_nowcast{'_intraday' if target == 'intraday' else ''}{tag}"
    rd = ROOT / "artifacts" / "runs" / run_id
    rd.mkdir(parents=True, exist_ok=True)
    preds.to_parquet(rd / "oos_predictions.parquet", index=False)
    metrics_table(preds).to_csv(rd / "metrics_by_model_horizon.csv", index=False)
    inc = pd.concat([incremental_value(preds, m) for m in MODELS if m not in ("zero_return", "hist_mean")], ignore_index=True)
    inc.to_csv(rd / "incremental_value_price_vs_combined.csv", index=False)
    add_global_correction(inc).to_csv(rd / "incremental_value_global_correction.csv", index=False)
    pd.set_option("display.width", 200)
    print(run_id)
    print(metrics_table(preds)[["model", "feature_set", "MAE", "RMSE", "R2_oos", "directional_accuracy", "IC", "rank_IC"]]
          .round(5).to_string(index=False))
    print(inc[["model", "n", "improvement_rmse_pct", "dm_p", "folds_combined_better", "folds"]].round(4).to_string(index=False))


if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    main(args[0] if args else None, target="intraday" if "--intraday" in sys.argv else "close_to_close")
