# Experiment Log

Append-only. Template per experiment:

```
## EXP-NNN — title
Question / hypothesis · Dataset version (files, filter) · Date range · Asset · Timeframe · Feature sets · Model(s) + hyperparameters · Training and validation method (mode, train_min, test_len, embargo) · Test period · Metrics · Statistical tests · Results · Interpretation · Limitations · Reproduce (exact commands, run id)
```

## Entries
*None.* No real-data experiment has been run (2026-11-05). EXP-001 is queued ([MODEL_EXPERIMENTS](../models/MODEL_EXPERIMENTS.md)).

### Non-experiment check — FinBERT validation (2026-11-05)
`scripts/score_sentiment.py --validate`: n=48 AI-labelled items, accuracy 0.604; details in [SENTIMENT_METHODOLOGY](../research/SENTIMENT_METHODOLOGY.md).

## EXP-001 — A vs B vs C, all horizons (COMPLETED 2026-11-05)
Question: does adding X sentiment features improve OOS forecasts of AAPL n+1..n+5 log returns vs price-only? · Data: `data/model_ready/model_table_AAPL_primary.parquet` (filter `primary`, 663,144 posts; 1,238 days 2015-02-02..2019-12-31) · Models: zero_return, hist_mean, ridge, lasso, elasticnet, random_forest, extra_trees, lightgbm, xgboost, catboost · Validation: expanding walk-forward, train_min 500, test_len 60, embargo 1, val_len 120, tiny grids · Command: `.venv/Scripts/python.exe scripts/run_validation.py primary` (log `logs/run_validation_primary.log`) · Started ~19:37 IST, finished ~19:45 IST (about 8 minutes). Run id `20261105T141541Z_primary` (`artifacts/runs/20261105T141541Z_primary/`: oos_predictions.parquet, metrics_by_model_horizon.csv, incremental_value_price_vs_combined.csv). Code state: 51 tests passing; no code changes between build and run.

**Setup actually used:** 12 expanding walk-forward folds, 60-day test blocks, first test day 2017-01-26, last 2019-12-04; 720 OOS observations per horizon/model/feature set; features A=price, B=sentiment, C=price+sentiment+interactions; engagement features excluded.

**Results.**
- Persistence is essentially unbeatable. h=1: only 4 of 25 model/feature-set configurations beat zero-return RMSE (best extra_trees/A: 0.01583 vs 0.01588, -0.3%). h=2..5: only `hist_mean` beats it (<=0.3% lower RMSE), reflecting AAPL's upward drift in the test period (up-day base rate 54-62%).
- Mean RMSE ratio to persistence by feature set (all 8 models), h=1..5: A 1.003/1.009/1.017/1.027/1.032; B 1.017/1.017/1.017/1.022/1.021; C 1.016/1.014/1.019/1.027/1.032. All >1 (worse than persistence).
- Sentiment-only (B) is worse than `hist_mean` at every horizon (best-B RMSE ratio 1.006-1.013).
- C vs A (improvement in RMSE %, positive = sentiment helps), mean across 8 models: h1 -1.34, h2 -0.48, h3 -0.16, h4 +0.01, h5 +0.01. 11 of 40 model x horizon cells positive (max +1.90%, lightgbm h5, raw p=0.165); 29 negative (worst -2.08%, elasticnet h1).
- Significance: 4 of 40 raw DM p-values <0.05 (ridge h2, ridge h4, random_forest h1, extra_trees h1) - **all four are cases where sentiment made forecasts worse**. Zero positive-improvement cells reach p<0.05. Only ridge h4 survives Holm across horizons within the model (p_holm 0.024, sentiment hurts); with a Bonferroni-style correction across all 40 tests its adjusted p is about 0.19 (0.0047 x 40), i.e. not significant.
- Per-fold: C beat A in about half of the folds for most cells (e.g. ridge 2-5 of 12).
- Directional accuracy: `hist_mean` 0.59-0.62 equals the always-up base rate (no skill). `zero_return` directional accuracy (0.38-0.46) is an artefact of predicting exactly 0 and must not be interpreted.

**Interpretation.** In this configuration there is no evidence that X sentiment improves out-of-sample AAPL forecasts; if anything it slightly worsens short-horizon forecasts, consistent with added noise. Price-only models also fail to beat persistence, so the whole feature set has no demonstrated skill.

**Limitations.** One asset, one sentiment model (FinBERT, weak on slang), one post filter, daily bars, provisional walk-forward config, overlapping targets, 720 observations per cell (low power: effects below roughly 1-2% RMSE would be hard to detect); economic (PnL) evaluation not computed by the runner; cross-model multiple-comparison correction not built into the runner; engagement weighting not testable. Absence of evidence here is not proof of no effect.

## EXP-002 - Robustness to post filtering (COMPLETED 2026-11-05)
Question: does the EXP-001 conclusion depend on which posts enter the sentiment features? · Same setup as EXP-001 (12 folds, 720 OOS days, 10 models, 3 sets, 5 horizons) · Runs `20261105T143517Z_all_posts` (all 1,424,481 posts, incl. duplicates/spam/bots), `20261105T144552Z_no_bots` (579,972 posts), primary = EXP-001 (663,144) · Command: `build_features.py <filter>` then `run_validation.py <filter>` · Summary: `scripts/summarize_run.py <run>`.
Results (mean C-vs-A RMSE improvement %, n+1..n+5): all_posts -0.57/-0.43/-0.04/-0.62/-0.94 (8/40 positive cells, raw p<.05: 3, none positive, global Holm 0, max +0.49%); no_bots -1.37/-0.30/+0.15/+0.06/+0.14 (17/40 positive, raw p<.05: 6, none positive, global Holm 0, max +2.05%); primary -1.34/-0.48/-0.16/+0.01/+0.01. In all three, persistence is beaten by at most 0.3% (best of ~25 configs, ex post).
Interpretation: filtering matters little; unfiltered data (spam/duplicates included) makes sentiment slightly worse. Limitations: same as EXP-001.

## EXP-003/004 - Weighting and feature-group ablation (COMPLETED 2026-11-05)
Question: does any part of the sentiment signal (polarity, volume, dynamics, weighting, interactions) add value over price? · Run `20261105T143130Z_ablation_primary` · price features + ONE group vs price only; ridge/extra_trees/lightgbm; 5 horizons → 105 tests · Command: `scripts/run_ablation.py primary`.
Results (mean RMSE improvement %, n+1..n+5): polarity -0.68/-0.16/+0.44/+0.41/+0.41; volume -0.51/-0.30/+0.24/-0.04/-0.10; dynamics -0.31/-0.11/-0.01/+0.15/+0.20; simple mean -0.01/+0.22/+0.38/+0.52/+0.40; author-weighted -0.17/+0.15/+0.29/+0.37/+0.26; confidence-weighted -0.09/+0.17/+0.52/+0.41/+0.32; interactions -0.42/+0.32/+0.45/+0.18/+0.06. Raw p<0.05 in 12 of 105 cells (7 positive; ~5 expected by chance); global Holm: 0. Largest: LightGBM + polarity n+5 +2.40% (raw p 0.052).
Interpretation: a consistent but tiny (<0.6%) positive drift at n+3..n+5 for simple/author/confidence weightings and polarity; not distinguishable from zero after correction; no weighting is clearly better than the simple mean (research question 5 for point-in-time weights). Volume carries no more than polarity (question 4).

## EXP-005 - Importance, SHAP, correlations (COMPLETED 2026-11-05)
Question: where does any predictive information come from? · Out-of-sample permutation importance (extra_trees, lightgbm at n+1/3/5), SHAP (LightGBM, final fold), 250 Spearman feature-target correlations · Dirs `artifacts/analysis/20261105T144723Z` (importance, SHAP), `.../20261105T151220Z` (correlations) · Command: `scripts/run_analysis.py importance|correlations`.
Results: importances ~1e-6 in squared-error units (MSE ~2.5e-4 → well under 1%); sentiment group sum negative/≈0 at n+1, positive at n+5 (extra_trees +9e-6, lightgbm +1.6e-5) while price group is negative there. Top SHAP at n+1: sn_post_count_z, px_hl_range, px_ret_accel. Correlations: strongest = price momentum at n+5 (rho +0.087, 3/6 blocks same sign); 0 of 250 significant after global Holm.
Interpretation: no feature carries stable information; the n+5 sentiment drift matches the small non-significant ablation gains.

## EXP-006 - Regimes (COMPLETED 2026-11-05)
Question: does sentiment help more in high-volatility or event periods? · Run uses EXP-001 predictions · Mean RMSE improvement: high-vol +0.14%, low-vol -0.83%; volume-spike days (proxy, not news) -3.84%, normal days -0.03% · File `artifacts/analysis/20261105T145545Z/regime_improvement.csv`. No evidence of concentration around events; spike days are worse. Limitation: no news data.

## EXP-007 - Multi-output, shared-head and deep models (COMPLETED 2026-11-05)
Question: does a different architecture extract value from sentiment? · Run `20261105T145545Z_multihorizon`: mo_ridge, mo_extra_trees (B), shared_mlp, GRU, LSTM, TCN, Transformer (C) × A/B/C sets × 5 horizons · Command `scripts/run_analysis.py multihorizon`.
Results: mean C-vs-A improvement -0.55/-0.54/-0.37/-0.59/-0.81%; 9/35 positive cells; raw p<0.05 in 5 (none positive); global Holm 0; max +1.20% (LSTM n+2). Price-only TCN at n+5 reaches 0.980 of persistence RMSE but is not significant (EXP-008).

## EXP-008 - All models versus persistence; economics (COMPLETED 2026-11-05)
Question: does anything beat 'no change', and does it pay? · `versus_persistence` over EXP-001 + EXP-007 (230 tests) → `artifacts/versus_persistence_all_models.csv`; `evaluate_run.py` on EXP-001 → `strategy_metrics.csv`.
Results: 1 configuration beats persistence at raw p<0.05; after global Holm 0 beat it and 4 are significantly WORSE (sentiment-only/combined models: random_forest B n+2 -2.1%, lightgbm B n+2 -3.7%, ridge C n+4 -2.7%, lightgbm B n+1 -2.7%). Economics (5 bps): buy-and-hold net 0.854 (Sharpe 1.19, max DD -38.7%); mean net PnL price-only +0.167, sentiment-only -0.323, combined -0.241; the best 'strategies' are always-long (hist_mean). Q12: no.

## EXP-009 - n+0 nowcast, close-to-close (COMPLETED 2026-11-05)
Question: can pre-open sentiment estimate the same-day return? · Run `20261105T144813Z_nowcast` · features: prices through D-1, posts in (D-1 09:30, D 09:30] · Command `scripts/run_nowcast.py`.
Results: sentiment-only models reach OOS R² +4.0-5.8% vs persistence and IC ≈ 0.24; price-only ≈ 0. Combined vs price-only: ridge +2.2% (p 0.49), lasso +0.4%, extra_trees +3.4% (p 0.046, 11/12 folds), lightgbm +4.4% (p 0.040, 10/12) - raw, 4 tests.
Interpretation: a statistically visible edge - but see EXP-010 for why it is not new information.

## EXP-010 - Nowcast diagnosis and intraday nowcast (COMPLETED 2026-11-05)
Question: is the EXP-009 edge real information? · `scripts/diagnose_nowcast.py` (Spearman, n=1,218): pre-open sentiment vs overnight gap rho 0.234 (z 8.2), vs intraday (open→close) 0.024 (z 0.8); session sentiment vs gap 0.328, intraday 0.448, total 0.562; LAGGED session sentiment vs total return -0.012, lagged pre-open vs total +0.005. Intraday nowcast (`run_nowcast.py --intraday`, run `20261105T144958Z_nowcast_intraday`, the gap is a known feature): sentiment improvement ridge -0.55% (p 0.012, worse), lasso 0.00, extra_trees -0.29%, lightgbm -0.28%; no model beats hist_mean.
Interpretation: pre-open sentiment echoes the overnight gap that has already happened; it adds nothing for the rest of the day, and sentiment overall *follows* price (strong contemporaneous correlation, none at a lag).

## EXP-011 - Engagement-weighted sentiment (LEAKY, exploratory; COMPLETED 2026-11-05)
Question 5. Run `20261105T150522Z_engagement_leaky` (60 tests). Engagement-weighted mean improvement -0.15/+0.18/+0.41/+0.54/+0.34% vs simple +/-: -0.01/+0.22/+0.38/+0.52/+0.40%; engagement volume ≈ -0.2..+0.1%. Raw p<0.05: 11 (9 positive); global Holm 0. Interpretation: even with leaky data, engagement weighting is not better than the simple mean. Counts are lifetime values, so this is not evidence about point-in-time engagement.

## EXP-013 - Power analysis (COMPLETED 2026-11-05)
Question: what true effect could this design have detected? · `scripts/power_analysis.py 20` · real price table, synthetic feature f = sqrt(r2)·z(y_1) + sqrt(1-r2)·noise planted into the 'sentiment' slot; ridge A vs C, n+1, same walk-forward and DM test, 20 seeds per level · output `artifacts/analysis/power_analysis_summary.csv`.
Results (planted R² of next-day return → mean RMSE improvement, detection rate at raw p<0.05 / p<0.001): 0% → -0.03%, 5% / 0%; 0.25% → +0.03%, 0% / 0%; 0.5% → +0.08%, 0% / 0%; 1% → +0.22%, 5% / 0%; 2% → +0.61%, 25% / 0%; 4% → +1.44%, 80% / 10%.
Interpretation: the null results exclude effects of roughly corr ≥ 0.2 (R² ≥ 4%) at n+1; effects up to ~1-2% R² (which could still matter economically) cannot be excluded. Limitations: ridge only, h=1, linear planted signal, Gaussian noise; real-world signals may be non-linear or time-varying.

## EXP-012 - Replication with a second sentiment model, FinTwitBERT (COMPLETED 2026-11-05)
Question: is the null result an artefact of FinBERT's measurement quality? · Model `StephanAkkerman/FinTwitBERT-sentiment` (0.708 on the validation items vs 0.604) scored on all 996,456 unique texts (~84 min) · Agreement with FinBERT: post-level Spearman 0.555, argmax-label agreement 55.8%, but DAILY mean-sentiment correlation 0.873 (n=1,259 days) · Runs `20261105T160603Z_primary_fintwitbert-sentiment` (EXP-001 repeat), `20261105T160643Z_nowcast_intraday_fintwitbert-sentiment`, `20261105T160721Z_nowcast_fintwitbert-sentiment`, diagnostics in `logs/diagnose_fintwit.log` · Chain: `build_features.py primary <model>` → `run_validation.py primary <model>` → `run_nowcast.py` ×2 → `diagnose_nowcast.py`.
Results:
- A vs C: mean RMSE improvement -0.67 / +0.25 / +0.17 / -0.13 / +0.15% (n+1..n+5); 20/40 positive cells; raw p<0.05 in 1 cell (random_forest n+3, +1.04%, raw p 0.021, global Holm 0.83); global Holm significant: 0; max +1.54% (LightGBM n+5, p 0.175). Versus persistence (125 tests): 0 better, 0 worse after correction.
- Economics (5 bps): mean net PnL price-only +0.167, sentiment-only -0.194, combined -0.050 (buy-and-hold +0.854).
- Intraday nowcast (gap known): mean -0.04%, 0 significant. Close-to-close nowcast: +3.8% (extra_trees +3.9% p 0.014, LightGBM +4.5% p 0.014; sentiment-only OOS R² 5.2-6.9%, IC 0.23-0.27) - the gap-echo effect again.
- Diagnostics (Spearman, n=1,218): pre-open sentiment vs gap 0.258 (z 9.0), vs intraday 0.038 (z 1.3); session sentiment vs total return 0.569; lagged session sentiment vs total return +0.014, lagged pre-open -0.005.
Interpretation: every substantive conclusion is reproduced with an independent, better-validated, finance-tweet-specific sentiment model: no significant incremental value, sentiment follows price, the nowcast edge is the overnight gap. Point estimates are slightly less negative than with FinBERT (c. +0.5pp at n+1..n+5) but not significant, consistent with measurement noise being a small part of the story. Limitations: the two models' daily series correlate 0.87, so the replication is only partly independent; both are validated on the same 48 AI-labelled items.
