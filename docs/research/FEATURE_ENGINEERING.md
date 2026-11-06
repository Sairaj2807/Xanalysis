# Feature Engineering

Code: [features/](../../features/). Row `t` uses information available at `t`'s close.

- **Price (`px_`):** 1/2/3/5/10-day returns, log return, rolling vol/mean (5/10/20), deviation from MA, 10-day momentum, high-low range, 10-day range, return acceleration, trend strength `(MA5−MA20)/std20`, direction.
- **Sentiment (`sn_`):** mean/median, author-weighted, confidence-weighted, std, positive/negative ratios, imbalance, confidence, post count (+log), unique authors, `had_posts`, lags 1–2, momentum, acceleration, MAs (3/5/10), rolling vol (10), post-volume change/acceleration, rolling z (60-day window, min 20) of sentiment and log volume. Leaky engagement columns only with `include_leaky=True`.
- **Interactions (`ix_`):** sentiment×momentum, ×volatility, ×post volume, acceleration×return, divergence `Z(S)−Z(R)` (causal rolling z).
- **Sets:** A_price = `px_*`; B_sentiment = `sn_*`; C_combined = all three prefixes.
- **Normalisation:** rolling z-scores are causal; model pipelines fit imputer/scaler on the training window only.
- **Missing sentiment:** NaN on empty days, median-imputed inside the pipeline (train-only); `sn_had_posts` and `sn_post_count` preserve the missingness signal.
- **Leakage controls:** [leakage_checks.py](../../features/leakage_checks.py); tests in `tests/test_features.py`. Real-data table not yet built (FEAT-005). Feature versioning: not implemented — the model-table filename encodes only the post filter; record code state in the experiment log until a version tag exists (TECHNICAL_DEBT).
