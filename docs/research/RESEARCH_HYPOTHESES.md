# Research Hypotheses

Status of all hypotheses: **untested** (no real-data experiment has run, 2026-11-05).

| ID | Hypothesis | Test | Status |
|---|---|---|---|
| H0 | Sentiment does not improve OOS forecasting vs price-only | DM test C vs A per horizon | Untested |
| H1 | Sentiment improves OOS forecasting | same | Untested |
| H2 | Post volume carries information beyond polarity | Feature-group ablation (volume vs polarity) | Untested |
| H3 | Engagement-weighted sentiment improves predictions | Weighting comparison — **only possible with leaky lifetime counts** (DEC-007) | Untested; limited |
| H4 | Sentiment momentum/acceleration has predictive value | Ablation | Untested |
| H5 | Information decays with horizon | Improvement_h across h=1..5 | Untested |
| H6 | Value differs across horizons | Same | Untested |
| H7 | Value differs in high vs low volatility regimes | Regime split (VAL-005) | Not started |
| H8 | Value concentrates around news events | Needs news layer (ING-006) | Not started |

Multiple-comparison control: Holm across horizons per model; many model families inflate the family — treat any single significant model with caution and report all.

## Status update (2026-11-05, after EXP-001..012)
| ID | Result |
|---|---|
| H0/H1 | H0 (no incremental value) not rejected in any experiment; sentiment-using models are significantly worse than persistence in 4 of 230 corrected tests |
| H2 volume vs polarity | Neither helps; volume features -0.5%/-0.3% at n+1/2, polarity +0.4% at n+3..5, all non-significant |
| H3 engagement weighting | Cannot be tested cleanly (lifetime counts); leaky version is not better than the simple mean |
| H4 momentum/acceleration | Dynamics group: -0.31..+0.20%, non-significant |
| H5/H6 decay and horizon dependence | Point estimates drift from negative (n+1) to ≈0/slightly positive (n+4/5); nothing significant |
| H7 volatility regimes | High-vol +0.14%, low-vol -0.83% (non-significant) |
| H8 news events | Tested only with a volume-spike proxy: sentiment is *worse* on spike days (-3.8%); real news not available |
