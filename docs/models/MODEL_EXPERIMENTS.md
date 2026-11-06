# Model Experiments

Index of experiments. Detailed chronological records: [EXPERIMENT_LOG](../history/EXPERIMENT_LOG.md). Each entry must follow the template there. Never overwrite.

| Exp ID | Question | Status | Result |
|---|---|---|---|
| EXP-001 | A vs B vs C, all horizons, primary filter, expanding walk-forward | **Completed** (run `20261105T141541Z_primary`) | No evidence sentiment helps; no model beats persistence; see [EXPERIMENT_LOG](../history/EXPERIMENT_LOG.md) |
| EXP-002 | Robustness: filters `all_posts`, `no_bots` | Planned | — |
| EXP-003 | Sentiment weighting comparison (simple / author / confidence; engagement flagged leaky) | Planned (STAT-003) | — |
| EXP-004 | Feature-group ablation (volume vs polarity vs dynamics) | Planned | — |
| EXP-005 | News-inclusive exploratory model D | Planned; requires news layer | — |
Synthetic-data tooling checks (planted-signal / noise) are tests, not experiments.

## Experiments EXP-002 … EXP-013 (all completed 2026-11-05)
| Exp ID | Question | Result (see [EXPERIMENT_LOG](../history/EXPERIMENT_LOG.md)) |
|---|---|---|
| EXP-002 | Robustness to post filters (all_posts, no_bots) | Same conclusion; unfiltered data slightly worse |
| EXP-003/004 | Weighting + feature-group ablation (105 tests) | 0 significant after global Holm; tiny positive drift at n+3..5 |
| EXP-005 | Importance, SHAP, 250 correlations | Noise-level importances; 0 correlations significant |
| EXP-006 | Volatility / volume-spike regimes | No regime shows a significant effect |
| EXP-007 | Multi-output, shared-head, GRU/LSTM/TCN/Transformer | 0/35 significant |
| EXP-008 | All models vs persistence (230 tests); economics | 0 better, 4 worse after correction; buy-and-hold wins |
| EXP-009 | n+0 nowcast, close-to-close | Apparent edge (+2..4%) |
| EXP-010 | Nowcast diagnosis + intraday nowcast | Edge = overnight-gap echo; intraday nowcast shows none |
| EXP-011 | Engagement-weighted sentiment (LEAKY) | Not better than simple mean |
| EXP-012 | Replication with FinTwitBERT | Reproduces all conclusions |
| EXP-013 | Power analysis | 1% R² → 5% detection; 4% → 80% |
| EXP-005 (news model D) | News-inclusive exploratory model | Not run: no news data (Tavily blocked) |
