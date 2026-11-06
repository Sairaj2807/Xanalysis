# Model Limitations

- **Sample:** ~1.2k daily rows; 720 out-of-sample observations per cell, overlapping targets for h>1. Effects below roughly 1–2% in RMSE cannot be reliably detected.
- **Persistence is the benchmark to beat and nothing beats it significantly.** 230 model/feature-set/horizon tests against the no-change forecast: 1 raw-significant improvement, 4 significantly worse after global correction (all with sentiment features).
- **Hyperparameters:** tiny grids; walk-forward configuration provisional (train_min 500, test_len 60, embargo 1). Results were not tuned to produce a conclusion.
- **Architectures:** deep models are deliberately small (CPU, ~800 training rows); larger networks are not justified by this sample size.
- **Sentiment measurement:** 4 transformer models scored 0.60–0.71 on 48 AI-labelled items; no human-reviewed ground truth. Sarcasm and mixed statements are poorly handled by all.
- **Intervals:** empirical-quantile intervals under-cover (80% nominal → 70.5% measured out-of-sample at n+1).
- **No uncertainty-aware nowcast, no regime-switching model, no news model.**
- **Strategy metrics** use a daily long/short rule with 5 bps costs and assume close fills; forecast quality does not establish profitability.
- **Multiple comparisons:** many models × horizons × variants were examined; only globally corrected statements are reported as findings; uncorrected near-misses (e.g. LightGBM + polarity at n+5, +2.4%, raw p=0.052) are exploratory.
- **Single asset and period (AAPL 2015–2019):** no claim about other assets, intraday horizons or later years.
