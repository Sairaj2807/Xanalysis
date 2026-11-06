"""EXP-003/004: which part of the sentiment signal (if any) adds value over price-only?

Each variant = price features + ONE sentiment feature group, compared with price-only on identical folds.
Groups: polarity, volume, dynamics, three single-series weightings (simple / author / confidence), interactions.
Headline claims must use `dm_p_holm_global` (Holm across every row of the ablation).
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
from validation.model_comparison import add_global_correction, incremental_value, run_walk_forward  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("run_ablation")

GROUPS = {
    "polarity": ["sn_sent_mean", "sn_sent_median", "sn_pos_ratio", "sn_neg_ratio", "sn_pos_neg_imbalance",
                 "sn_sent_lag1", "sn_sent_lag2", "sn_sent_ma_3", "sn_sent_ma_5", "sn_sent_ma_10", "sn_sent_z"],
    "volume": ["sn_post_count", "sn_log_post_count", "sn_unique_authors", "sn_post_vol_change",
               "sn_post_vol_accel", "sn_post_count_z"],
    "dynamics": ["sn_sent_mom_1", "sn_sent_accel", "sn_sent_vol_10", "sn_sent_std"],
    "w_simple": ["sn_sent_mean"],
    "w_author": ["sn_sent_author_w"],
    "w_confidence": ["sn_sent_conf_w"],
    "interactions": [],  # filled from ix_ columns
}
MODELS = ["ridge", "extra_trees", "lightgbm"]


def main(filter_name: str = "primary") -> None:
    a = load_settings().asset
    table = pd.read_parquet(ROOT / "data" / "model_ready" / f"model_table_{a.symbol}_{filter_name}.parquet")
    sets = json.loads((ROOT / "data" / "model_ready" / "feature_sets.json").read_text())
    px_cols = sets["A_price"]
    GROUPS["interactions"] = [c for c in table if c.startswith("ix_")]
    variants = {"A_price": px_cols}
    for g, cols in GROUPS.items():
        missing = [c for c in cols if c not in table]
        assert not missing, f"unknown columns in group {g}: {missing}"
        variants[f"A+{g}"] = px_cols + cols
    preds = run_walk_forward(table, variants, MODELS, a.horizons, train_min=500, test_len=60, embargo=1, val_len=120)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"_ablation_{filter_name}"
    out = ROOT / "artifacts" / "runs" / run_id
    out.mkdir(parents=True, exist_ok=True)
    preds.to_parquet(out / "oos_predictions.parquet", index=False)
    parts = []
    for m in MODELS:
        for v in variants:
            if v == "A_price":
                continue
            inc = incremental_value(preds, m, base_set="A_price", new_set=v)
            inc.insert(1, "variant", v)
            parts.append(inc)
    inc = add_global_correction(pd.concat(parts, ignore_index=True))
    inc.to_csv(out / "ablation_incremental_value.csv", index=False)
    pd.set_option("display.width", 220)
    print(f"run {run_id}; tests in family: {int(inc.n_tests_global.iloc[0])}")
    print("\nMean RMSE improvement % vs price-only (positive = helps), by variant x horizon (mean over models):")
    print(inc.pivot_table(index="variant", columns="horizon", values="improvement_rmse_pct", aggfunc="mean").round(2))
    print("\nBest 8 cells by improvement:")
    print(inc.sort_values("improvement_rmse_pct", ascending=False).head(8)[
        ["model", "variant", "horizon", "improvement_rmse_pct", "dm_p", "dm_p_holm_global"]].round(4).to_string(index=False))
    print("\nCells with raw p<0.05:", int((inc.dm_p < 0.05).sum()), "| positive-effect among them:",
          int(((inc.dm_p < 0.05) & (inc.improvement_rmse_pct > 0)).sum()), "| global-Holm p<0.05:",
          int((inc.dm_p_holm_global < 0.05).sum()))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "primary")
