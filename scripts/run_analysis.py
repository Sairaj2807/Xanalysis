"""EXP-005..008: importance, SHAP, regimes, multi-output / shared-head / deep models on the primary table.

Writes: artifacts/analysis/<ts>/ (importance, shap, regimes CSVs) and artifacts/runs/<ts>_multihorizon/ (standard run layout).
Usage: python scripts/run_analysis.py [importance regimes multihorizon]   (default: all)
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from config.settings import ROOT, load_settings  # noqa: E402
from models.multi_horizon import run_multi_horizon  # noqa: E402
from reporting.run_index import latest_run  # noqa: E402
from validation.importance import (feature_target_correlations, group_importance,  # noqa: E402
                                   permutation_importance_wf, shap_values_last_fold, summarise_importance)
from validation.model_comparison import (add_global_correction, incremental_value, metrics_table,  # noqa: E402
                                         run_walk_forward)
from validation.regime_analysis import improvement_by_regime, spike_regime, vol_regime  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("run_analysis")


def main(parts: list[str]) -> None:
    a = load_settings().asset
    table = pd.read_parquet(ROOT / "data" / "model_ready" / f"model_table_{a.symbol}_primary.parquet")
    sets = json.loads((ROOT / "data" / "model_ready" / "feature_sets.json").read_text())
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "artifacts" / "analysis" / ts
    out.mkdir(parents=True, exist_ok=True)

    if "importance" in parts:
        allimp = []
        for model in ("extra_trees", "lightgbm"):
            for h in (1, 3, 5):
                df = permutation_importance_wf(table, sets["C_combined"], model, h)
                s = summarise_importance(df)
                s.insert(0, "horizon", h)
                s.insert(0, "model", model)
                allimp.append(s.reset_index())
                log.info("importance %s h=%d top: %s | groups: %s", model, h, list(s.index[:3]),
                         group_importance(s).round(8).to_dict())
        imp = pd.concat(allimp)
        imp.to_csv(out / "permutation_importance.csv", index=False)
        for h in (1, 5):
            X, sv = shap_values_last_fold(table, sets["C_combined"], h)
            ms = pd.DataFrame({"feature": X.columns, "mean_abs_shap": np.abs(sv).mean(axis=0)}).sort_values(
                "mean_abs_shap", ascending=False)
            ms.insert(0, "horizon", h)
            ms.to_csv(out / f"shap_h{h}.csv", index=False)
            np.save(out / f"shap_values_h{h}.npy", sv)
            X.to_parquet(out / f"shap_features_h{h}.parquet")

    if "correlations" in parts:
        cor = feature_target_correlations(table, sets["C_combined"], a.horizons)
        cor.to_csv(out / "feature_target_correlations.csv", index=False)
        log.info("correlations: %d tests; global-Holm p<0.05: %d; top:\n%s", len(cor), int((cor.p_holm_global < 0.05).sum()),
                 cor.head(8)[["feature", "horizon", "spearman", "p", "p_holm_global", "blocks_same_sign"]].round(4).to_string(index=False))

    if "regimes" in parts:
        preds = pd.read_parquet(latest_run("primary") / "oos_predictions.parquet")
        rows = []
        for name, reg in (("volatility", vol_regime(table)), ("volume_spike_proxy", spike_regime(table))):
            for m in ("ridge", "extra_trees", "lightgbm"):
                for h in range(1, 6):
                    r = improvement_by_regime(preds, reg, m, h)
                    r.insert(0, "regime_type", name)
                    rows.append(r)
        reg = pd.concat(rows, ignore_index=True)
        reg.to_csv(out / "regime_improvement.csv", index=False)
        log.info("regime mean improvement:\n%s", reg.groupby(["regime_type", "regime"])["improvement_rmse_pct"].mean().round(3))

    if "multihorizon" in parts:
        models = ["mo_ridge", "mo_extra_trees", "shared_mlp", "gru", "lstm", "tcn", "transformer"]
        preds = run_multi_horizon(table, sets, models, a.horizons, train_min=500, test_len=60, embargo=1)
        base = run_walk_forward(table, {"A_price": sets["A_price"]}, ["zero_return", "hist_mean"], a.horizons,
                                train_min=500, test_len=60, embargo=1)
        allp = pd.concat([preds, base], ignore_index=True)
        rd = ROOT / "artifacts" / "runs" / f"{ts}_multihorizon"
        rd.mkdir(parents=True, exist_ok=True)
        allp.to_parquet(rd / "oos_predictions.parquet", index=False)
        metrics_table(allp).to_csv(rd / "metrics_by_model_horizon.csv", index=False)
        inc = pd.concat([incremental_value(allp, m) for m in models], ignore_index=True)
        inc.to_csv(rd / "incremental_value_price_vs_combined.csv", index=False)
        add_global_correction(inc).to_csv(rd / "incremental_value_global_correction.csv", index=False)
        log.info("multihorizon run: %s", rd.name)


if __name__ == "__main__":
    main(sys.argv[1:] or ["importance", "regimes", "multihorizon"])
