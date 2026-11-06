"""Stage: walk-forward experiment A (price) vs B (sentiment) vs C (combined) on the real table.

Prediction rows are written to a NEW timestamped file each run (history is never overwritten).
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from config.settings import ROOT, load_settings  # noqa: E402
from sentiment.finbert_analyzer import model_tag  # noqa: E402
from validation.model_comparison import incremental_value, metrics_table, run_walk_forward  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("run_validation")

DEFAULT_MODELS = ["zero_return", "hist_mean", "ridge", "lasso", "elasticnet", "random_forest", "extra_trees",
                  "lightgbm", "xgboost", "catboost"]


def main(filter_name: str = "primary", models: list[str] | None = None, sent_model: str | None = None) -> None:
    a = load_settings().asset
    tag = model_tag(sent_model) if sent_model else ""
    table = pd.read_parquet(ROOT / "data" / "model_ready" / f"model_table_{a.symbol}_{filter_name}{tag}.parquet")
    sets = json.loads((ROOT / "data" / "model_ready" / "feature_sets.json").read_text())
    models = models or DEFAULT_MODELS
    preds = run_walk_forward(table, sets, models, a.horizons, train_min=500, test_len=60, embargo=1, val_len=120)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"_{filter_name}{tag}"
    out_dir = ROOT / "artifacts" / "runs" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    preds.to_parquet(out_dir / "oos_predictions.parquet", index=False)
    mt = metrics_table(preds)
    mt.to_csv(out_dir / "metrics_by_model_horizon.csv", index=False)
    inc = pd.concat([incremental_value(preds, m) for m in models if m not in ("zero_return", "hist_mean")])
    inc.to_csv(out_dir / "incremental_value_price_vs_combined.csv", index=False)
    pd.set_option("display.width", 220, "display.max_columns", 40)
    log.info("run %s: %d OOS predictions", run_id, len(preds))
    print(mt[["model", "feature_set", "horizon", "MAE", "RMSE", "R2_oos", "directional_accuracy", "IC"]]
          .sort_values(["horizon", "model", "feature_set"]).round(5).to_string(index=False))
    print("\nIncremental value: Price+Sentiment (C) vs Price-only (A)")
    print(inc[["model", "horizon", "n", "improvement_rmse_pct", "dm_p", "dm_p_holm", "folds_combined_better", "folds"]]
          .round(4).to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "primary", sent_model=sys.argv[2] if len(sys.argv) > 2 else None)
