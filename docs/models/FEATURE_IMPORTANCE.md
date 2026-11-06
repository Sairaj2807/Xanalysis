# Feature Importance

Completed (STAT-002, EXP-005): see the [feature importance report](../reports/research_reports/2026-11-05_feature_importance_report.md). Summary: out-of-sample permutation importances are ~1e-6 (squared-error units, i.e. well under 1% of MSE); the sentiment group is ≈0/negative at n+1 and slightly positive at n+5; SHAP top features at n+1 are sn_post_count_z, px_hl_range, px_ret_accel; none of 250 feature-return correlations is significant after global correction.

Original plan: Planned: permutation importance per fold, SHAP for tree models, feature-group ablation, stability across folds, correlation analysis. Purpose: decide whether any information comes from sentiment, price, or their interaction.
