"""Build the research dashboard and reports from saved artifacts (never recomputes models).

Outputs: artifacts/reports/dashboard.html, artifacts/reports/outlook.html,
         docs/reports/{research_reports,model_validation,data_quality}/<date>_*.md
Usage: python scripts/generate_report.py [YYYY-MM-DD label]
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from config.settings import ROOT, load_settings  # noqa: E402
from prediction.forecasting import latest_forecast  # noqa: E402
from prediction.uncertainty import coverage_by_fold  # noqa: E402
from reporting.run_index import latest_run  # noqa: E402
from reporting.research_report import (importance_report, md_table, performance_report,  # noqa: E402
                                       walk_forward_report)
from reporting.sentiment_report import build_outlook, render_html, render_markdown  # noqa: E402
from validation.model_comparison import add_global_correction  # noqa: E402
from validation.regime_analysis import spike_regime, vol_regime  # noqa: E402
from visualization.forecast_matrix import fig_forecast_matrix, forecast_matrix  # noqa: E402
from visualization.performance_dashboard import (build_dashboard, fig_bar, fig_error_by_horizon,  # noqa: E402
                                                  fig_forecast_vs_actual, fig_importance, fig_incremental,
                                                  fig_residuals, fig_walk_forward)
from visualization.price_sentiment import (divergence_events, fig_divergence, fig_price_sentiment,  # noqa: E402
                                           fig_rolling_correlation, fig_scatter_future, fig_volume_spikes)
from visualization.sentiment_heatmap import fig_heatmaps  # noqa: E402

latest = latest_run   # exact-kind lookup (see reporting/run_index.py)


def main(label: str | None = None) -> None:
    label = label or date.today().isoformat()
    a = load_settings().asset
    table = pd.read_parquet(ROOT / "data" / "model_ready" / f"model_table_{a.symbol}_primary.parquet")
    sets = json.loads((ROOT / "data" / "model_ready" / "feature_sets.json").read_text())
    agg = pd.read_parquet(ROOT / "data" / "aggregated" / f"sentiment_daily_{a.symbol}_primary.parquet")
    px = pd.read_parquet(ROOT / "data" / "raw" / "prices" / f"{a.symbol}_{a.bar_interval}.parquet")
    px["trading_day"] = px["bar_start_utc"].dt.tz_localize(None).dt.normalize()
    px = px.set_index("trading_day").sort_index()
    prim = latest("primary")
    preds = pd.read_parquet(prim / "oos_predictions.parquet")
    metrics = pd.read_csv(prim / "metrics_by_model_horizon.csv")
    inc = add_global_correction(pd.read_csv(prim / "incremental_value_price_vs_combined.csv"))
    strat = pd.read_csv(prim / "strategy_metrics.csv") if (prim / "strategy_metrics.csv").exists() else None
    out_html = ROOT / "artifacts" / "reports"
    out_html.mkdir(parents=True, exist_ok=True)

    # ---- sections --------------------------------------------------------------------------------------
    mat = forecast_matrix(preds, "ridge", "C_combined")
    secs = [
        ("Price vs sentiment", "OHLC, FinBERT mean sentiment and volume on one time axis, with the 1-day-ahead ridge forecast overlaid.",
         fig_price_sentiment(px.loc[table.index[0]:table.index[-1]], agg, preds, "ridge", "C_combined", 1)),
        ("Sentiment-price divergence", "D = Z(S) - Z(R). Descriptive only - not a reversal signal.", fig_divergence(table)),
        ("Rolling correlation", "Sentiment moves with same-day returns (reaction) but not with next-day returns (prediction).",
         fig_rolling_correlation(table)),
        ("Sentiment vs future return", "Scatter of daily mean sentiment against the next-day log return.", fig_scatter_future(table, 1)),
        ("Sentiment calendar heatmaps", "Net sentiment, positive/negative ratio, volume, acceleration on comparable scales.", fig_heatmaps(agg)),
        ("Volume spikes", "Days with abnormally high post volume (a proxy for events; no news data).", fig_volume_spikes(table)),
        ("Forecast matrix", "Predicted price at every horizon vs the observed price at T (out-of-sample; ridge, price+sentiment).",
         fig_forecast_matrix(mat)),
        ("Forecast vs actual", "Out-of-sample n+1 forecast tracks the price level only because the level is persistent.",
         fig_forecast_vs_actual(preds, "ridge", "C_combined", 1)),
        ("Residuals", "Forecast residual distribution by horizon.", fig_residuals(preds, "ridge", "C_combined", [1, 3, 5])),
        ("Error by horizon", "RMSE relative to the no-change forecast. Values above 1 are worse than persistence.",
         fig_error_by_horizon(metrics)),
        ("Value of sentiment", "RMSE improvement from adding sentiment, per model and horizon.", fig_incremental(inc)),
        ("Walk-forward performance", "Per-fold RMSE for price-only vs price+sentiment (ridge, n+1).", fig_walk_forward(preds, "ridge", 1)),
    ]
    extras: dict[str, str] = {}
    # ablation
    ab = latest("ablation_primary")
    if ab is not None:
        abl = pd.read_csv(ab / "ablation_incremental_value.csv")
        piv = abl.pivot_table(index="variant", columns="horizon", values="improvement_rmse_pct", aggfunc="mean").reset_index()
        secs.append(("Feature-group ablation", "Mean RMSE improvement (%) vs price-only for price + one sentiment group.",
                     fig_incremental(abl.assign(model=abl.variant))))
        extras["6. Ablation (feature groups)"] = md_table(piv, ".2f") + (
            f"\n\n{int(abl.n_tests_global.iloc[0])} tests; raw p<0.05: {(abl.dm_p < 0.05).sum()} "
            f"(positive: {((abl.dm_p < 0.05) & (abl.improvement_rmse_pct > 0)).sum()}); global-Holm p<0.05: {(abl.dm_p_holm_global < 0.05).sum()}.")
    # robustness
    rob = []
    for suf, name in (("primary", "primary filter (FinBERT)"), ("all_posts", "all posts (FinBERT)"), ("no_bots", "no bot-like authors (FinBERT)"),
                      ("primary_fintwitbert-sentiment", "primary filter, FinTwitBERT sentiment")):
        r = latest(suf)
        if r is not None and (r / "incremental_value_price_vs_combined.csv").exists():
            i2 = add_global_correction(pd.read_csv(r / "incremental_value_price_vs_combined.csv"))
            rob.append({"post filter": name, **{f"n+{h}": v for h, v in i2.groupby("horizon").improvement_rmse_pct.mean().items()},
                        "positive cells": f"{(i2.improvement_rmse_pct > 0).sum()}/{len(i2)}",
                        "global-Holm sig.": int((i2.dm_p_holm_global < 0.05).sum())})
    if rob:
        extras["7. Robustness to post filtering (mean RMSE improvement %)"] = md_table(pd.DataFrame(rob), ".2f")
    # multi-horizon / deep
    mh = latest("multihorizon")
    if mh is not None:
        mi = pd.read_csv(mh / "incremental_value_price_vs_combined.csv")
        mm = pd.read_csv(mh / "metrics_by_model_horizon.csv")
        z = mm[mm.model == "zero_return"].set_index("horizon").RMSE
        mm["ratio_to_persistence"] = mm.apply(lambda r: r.RMSE / z[r.horizon], axis=1)
        tbl = mm[mm.feature_set.isin(["A_price", "C_combined"])].pivot_table(
            index=["model", "feature_set"], columns="horizon", values="ratio_to_persistence").reset_index()
        extras["8. Multi-output / shared-head / deep models (RMSE ratio to persistence)"] = md_table(tbl, ".4f") + (
            "\n\n" + md_table(mi.pivot_table(index="model", columns="horizon", values="improvement_rmse_pct").reset_index(), ".2f") +
            "\n\n(second table: sentiment improvement % per model/horizon)")
        secs.append(("Deep / multi-output: value of sentiment", "Same comparison for architecture B (multi-output) and C (shared heads, GRU, LSTM, TCN, Transformer).",
                     fig_incremental(mi)))
    # models versus persistence (global correction over every model / feature set / horizon)
    vp_path = ROOT / "artifacts" / "versus_persistence_all_models.csv"
    if vp_path.exists():
        vp = pd.read_csv(vp_path)
        worse = vp[(vp.dm_p_holm_global < 0.05) & (vp.improvement_rmse_pct_vs_persistence < 0)]
        better = vp[(vp.dm_p_holm_global < 0.05) & (vp.improvement_rmse_pct_vs_persistence > 0)]
        extras["Models versus persistence"] = (
            f"Diebold-Mariano test of every model x feature set x horizon against the no-change forecast ({len(vp)} tests, Holm-corrected globally). "
            f"Significantly BETTER than persistence: {len(better)}; significantly WORSE: {len(worse)} "
            f"(feature sets of the worse ones: {dict(worse.feature_set.value_counts())}). Raw p<0.05 and better: "
            f"{int(((vp.dm_p < 0.05) & (vp.improvement_rmse_pct_vs_persistence > 0)).sum())}.\n\n" +
            md_table(vp.sort_values("dm_p").head(10)[["model", "feature_set", "horizon", "improvement_rmse_pct_vs_persistence",
                                                       "dm_p", "dm_p_holm_global"]], ".4f"))
    # nowcast
    for suf, title in (("nowcast", "close-to-close nowcast (gap echo)"), ("nowcast_intraday", "intraday nowcast (open to close)")):
        nr = latest(suf)
        if nr is not None:
            ni = pd.read_csv(nr / "incremental_value_price_vs_combined.csv")
            extras[f"9. n+0 {title}"] = md_table(ni[["model", "n", "improvement_rmse_pct", "dm_p", "folds_combined_better", "folds"]], ".4f")
    # importance / regimes
    an_dirs = sorted((ROOT / "artifacts" / "analysis").glob("*")) if (ROOT / "artifacts" / "analysis").exists() else []
    imp_report = None
    for an in reversed(an_dirs):
        if (an / "permutation_importance.csv").exists():
            imp = pd.read_csv(an / "permutation_importance.csv")
            shap_t = {h: pd.read_csv(an / f"shap_h{h}.csv") for h in (1, 5) if (an / f"shap_h{h}.csv").exists()}
            imp_report = importance_report(an.name, imp, shap_t)
            s1 = imp[(imp.model == "extra_trees") & (imp.horizon == 1)].set_index("feature")
            secs.append(("Feature importance", "Out-of-sample permutation importance (extra_trees, n+1).", fig_importance(s1, "Permutation importance (extra_trees, n+1)")))
            if shap_t:
                s = shap_t[min(shap_t)].set_index("feature").rename(columns={"mean_abs_shap": "mean_importance"})
                secs.append(("SHAP summary", "Mean |SHAP| of LightGBM on the final walk-forward block.", fig_importance(s, "Mean |SHAP|")))
            break
    for an in reversed(an_dirs):
        if (an / "feature_target_correlations.csv").exists():
            cc = pd.read_csv(an / "feature_target_correlations.csv")
            by_group = cc.groupby("group").agg(tests=("p", "size"), max_abs_rho=("spearman", lambda s: s.abs().max()),
                                               holm_sig=("p_holm_global", lambda s: int((s < 0.05).sum()))).reset_index()
            extras["11. Feature-target Spearman correlations"] = (
                f"{len(cc)} tests (features x horizons); significant after global Holm: {int((cc.p_holm_global < 0.05).sum())}.\n\n" +
                md_table(by_group, ".3f") + "\n\nStrongest raw correlations (sign stability = blocks with the same sign, of 6):\n\n" +
                md_table(cc.head(8)[["feature", "horizon", "spearman", "p", "p_holm_global", "blocks_same_sign"]], ".4f"))
            break
    for an in reversed(an_dirs):
        if (an / "regime_improvement.csv").exists():
            rg = pd.read_csv(an / "regime_improvement.csv")
            gg = rg.groupby(["regime_type", "regime"])["improvement_rmse_pct"].mean().reset_index()
            secs.append(("Accuracy by regime", "Mean RMSE improvement from sentiment by volatility / volume regime.",
                         fig_bar(gg, "regime", "improvement_rmse_pct", "Sentiment improvement by regime (mean over models/horizons)", "regime_type")))
            extras["10. Regimes (mean RMSE improvement %)"] = md_table(gg, ".3f")
            break

    notes = ["Headline: no evidence that X sentiment improves out-of-sample price forecasts; models do not beat the no-change forecast.",
             "Out-of-sample window 2017-01-26..2019-12-04; AAPL daily; see docs/research/RESEARCH_FINDINGS.md for full caveats."]
    (out_html / "dashboard.html").write_text(build_dashboard(secs, f"{a.symbol} X-sentiment research dashboard", notes), encoding="utf-8")

    # ---- reports ---------------------------------------------------------------------------------------
    rr = ROOT / "docs" / "reports"
    for d in ("research_reports", "model_validation", "data_quality"):
        (rr / d).mkdir(parents=True, exist_ok=True)
    (rr / "model_validation" / f"{label}_model_performance_report.md").write_text(
        performance_report(prim.name, metrics, inc, strat, extras), encoding="utf-8")
    (rr / "model_validation" / f"{label}_walk_forward_report.md").write_text(walk_forward_report(prim.name, preds, inc), encoding="utf-8")
    if imp_report:
        (rr / "research_reports" / f"{label}_feature_importance_report.md").write_text(imp_report, encoding="utf-8")

    # one-page outlook
    posts = pd.read_parquet(ROOT / "data" / "processed" / f"posts_{a.symbol}.parquet", columns=["username", "is_duplicate", "flag_spam", "english_score"])
    used = posts[(~posts.is_duplicate) & (~posts.flag_spam) & (posts.english_score >= 0.5)]
    fc = latest_forecast(table, sets["A_price"], "ridge", a.horizons, preds, "A_price")
    cov = coverage_by_fold(preds, "ridge", "A_price", 1)
    evidence = ("No validated predictive relationship: across 8 classical learners and 7 deep/multi-output architectures, 5 horizons, 3 post filters, 7 feature groups and 2 nowcast definitions, sentiment did not "
                "improve out-of-sample forecasts; sentiment correlates with same-day returns (it reacts to price) but not with next-day returns.")
    o = build_outlook({"company_name": a.company_name, "symbol": a.symbol}, px, agg, table, fc, len(used), used.username.nunique(), evidence)
    md = render_markdown(o).replace("80% empirical interval", f"80% nominal interval (measured out-of-sample coverage {cov['empirical']:.0%})")
    md += f"\n*Interval calibration check (n+1, ridge, out-of-sample): nominal 80% -> empirical {cov['empirical']:.1%} over {cov['n']} points; intervals are too narrow.*\n"
    (rr / "research_reports" / f"{label}_one_page_outlook.md").write_text(md, encoding="utf-8")
    (out_html / "outlook.html").write_text(render_html(o), encoding="utf-8")

    # data-quality report
    allp = pd.read_parquet(ROOT / "data" / "processed" / f"posts_{a.symbol}.parquet")
    flags = allp[["is_duplicate", "flag_promo", "flag_many_cashtags", "flag_url_only", "flag_spam", "flag_bot_like"]].mean().rename("share").reset_index()
    flags.columns = ["flag", "share"]
    yearly = allp.assign(year=pd.to_datetime(allp.created_at).dt.year).groupby("year").size().rename("posts").reset_index()
    dq = ["# Data Quality Report", "", f"> AUTO-GENERATED by scripts/generate_report.py ({label}).", "",
          f"- Raw posts: {len(allp):,}; unique ids {allp.post_id.nunique():,}; distinct authors {allp.username.nunique():,}.",
          f"- Primary filter keeps {len(used):,} ({len(used) / len(allp):.1%}).", f"- Price bars: {len(px):,} ({px.index.min().date()} .. {px.index.max().date()}), NaN cells {int(px[['open','high','low','close']].isna().sum().sum())}.",
          f"- Model table: {table.shape[0]} trading days x {table.shape[1]} columns; days with sentiment {int(table['sn_had_posts'].sum())}.", "",
          "## Cleaning flags (heuristic, uncalibrated)", "", md_table(flags, ".4f"), "", "## Posts per year", "", md_table(yearly, ".0f"), "",
          "## Daily post counts (primary filter)", "", md_table(agg["post_count"].describe().rename("posts_per_day").reset_index(), ".1f"), "",
          "Known issues: 532 linked IDs absent from the extract; engagement counts are lifetime values (excluded); timezone of `post_date` presumed UTC.", ""]
    (rr / "data_quality" / f"{label}_data_quality_report.md").write_text("\n".join(dq), encoding="utf-8")
    print("dashboard:", out_html / "dashboard.html")
    print("reports written under", rr)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
