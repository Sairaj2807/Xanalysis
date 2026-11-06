# Research Findings

Evidence base: experiments EXP-001..013 in [EXPERIMENT_LOG](../history/EXPERIMENT_LOG.md) (AAPL, daily bars, 1,238 trading days 2015-02-02..2019-12-31, out-of-sample 2017-01-26..2019-12-04, 720 days per cell). Findings are append-only: a later entry supersedes an earlier one explicitly. "Significant" always means Holm-adjusted p < 0.05 over the whole family of tests ([DEC-014](../decisions/DECISION_LOG.md)).

## Headline
1. **No evidence that X sentiment improves out-of-sample AAPL price forecasts at n+1..n+5.** Not for 8 classical learners (plus 2 baselines), 7 deep/multi-output architectures, 3 post filters, 7 feature groups, 2 nowcast definitions, or leaky engagement weights. 0 positive effects are significant after correction.
2. **Nothing beats "no change".** Across 230 model/feature-set/horizon tests against persistence, 0 are significantly better after correction and 4 (all using sentiment features) are significantly worse. The best model beats persistence by at most ~0.3% RMSE (ex-post best of ~25; not significant).
3. **Sentiment is a coincident indicator, not a leading one.** It correlates with the same day's return (Spearman 0.56 for session sentiment with the day's return) but not with the next day's (-0.01 lagged). A same-day "nowcast" from pre-open sentiment looks skilful (OOS R² +4-6%) only because pre-open sentiment echoes the overnight gap that is already known; for the part of the day still unknown at the open it adds nothing.
4. **Power caveat (important):** with this design a true effect explaining 1% of next-day return variance is detected only ~5% of the time, 2% → 25%, 4% (corr 0.2) → 80% (ridge, n+1, raw p<0.05). The study therefore rules out *large* effects, not small ones. "No evidence" ≠ "no effect".
5. **Economics:** buy-and-hold (net +0.854, Sharpe 1.19) beat every strategy; mean net PnL after 5 bps: price-only +0.167, sentiment-only -0.323, combined -0.241.

## Tables of evidence
| Exp | What | Mean sentiment effect on RMSE (n+1..n+5, % ; + = helps) | Significant after global Holm |
|---|---|---|---|
| 001 | 10 models A vs C | -1.34 / -0.48 / -0.16 / +0.01 / +0.01 | 0 of 40 (4 raw-significant, all negative) |
| 002 | all_posts / no_bots filters | -0.57..-0.94 / -1.37..+0.15 | 0 / 0 |
| 003-004 | 7 feature groups × 3 models | -0.7..+0.5 (see log) | 0 of 105 |
| 007 | multi-output, shared heads, GRU/LSTM/TCN/Transformer | -0.55 / -0.54 / -0.37 / -0.59 / -0.81 | 0 of 35 |
| 008 | vs persistence | — | 0 better, 4 worse (of 230) |
| 010 | intraday nowcast (gap known) | -0.55 .. 0.00 | 0 |
| 011 | engagement weighting (LEAKY) | -0.15 / +0.18 / +0.41 / +0.54 / +0.34 (simple mean: -0.01 / +0.22 / +0.38 / +0.52 / +0.40) | 0 of 60 |
| 012 | repeat of EXP-001 with FinTwitBERT sentiment | -0.67 / +0.25 / +0.17 / -0.13 / +0.15 | 0 of 40 (1 raw-significant, positive: random_forest n+3 +1.04%, global p 0.83) |

## The 12 research questions
| # | Question | Answer (evidence) |
|---|---|---|
| 1 | Is X sentiment statistically predictive of future returns? | **No evidence.** 250 feature-return Spearman correlations (features × n+1..n+5): none significant (strongest: price momentum at n+5, rho 0.087, same sign in 3/6 blocks). Lagged sentiment vs next-day return: -0.01 / +0.005. Sentiment-only models are worse than the historical mean at every horizon. |
| 2 | Does sentiment improve prediction over price-only? | **No** (EXP-001..011): negative at n+1 (-1.3%), ≈0 at n+4/5. |
| 3 | At which horizon is the incremental value greatest? | None is significant. Point estimates are least negative / slightly positive at n+3..n+5 (simple/author/confidence weights +0.3..+0.5%; best single raw cell LightGBM+polarity n+5 +2.4%, p 0.052, global p 1.0) - exploratory only. |
| 4 | Does sentiment volume carry more than polarity? | No. Volume group -0.51/-0.30/+0.24/-0.04/-0.10; polarity -0.68/-0.16/+0.44/+0.41/+0.41; both non-significant. |
| 5 | Does engagement-weighted beat simple aggregation? | **Not testable cleanly** (lifetime counts, not point-in-time). With the leaky counts it is not better than the simple mean. Author-weighted and confidence-weighted are also indistinguishable from the simple mean. |
| 6 | Does sentiment acceleration predict future moves? | No: the dynamics group (momentum, acceleration, volatility, std) is -0.31..+0.20%, non-significant. |
| 7 | Does sentiment work differently in high vs low volatility? | No detectable difference: high-vol +0.14%, low-vol -0.83% (non-significant). |
| 8 | Is predictive information concentrated around major news events? | Real news not available. Proxy (post-volume spike days): sentiment is *worse* there (-3.8%). Unanswered for real news. |
| 9 | How long does the effect persist? | There is no predictive effect to persist. The only structure is contemporaneous (same-day) and it vanishes at a one-day lag. |
| 10 | Is the relationship stable across walk-forward periods? | There is no stable advantage: price+sentiment beats price-only in about half the folds; sentiment-feature distributions drift strongly (PSI up to 1.76, 19/51 features in alert). |
| 11 | Are improvements statistically significant? | No positive improvement is significant after correction; the only significant results are sentiment-using models doing *worse* than persistence. |
| 12 | Economically meaningful after costs? | No: buy-and-hold dominates; sentiment-based long/short strategies lose money after 5 bps. |

## Measured side findings
| Date | Finding | Evidence |
|---|---|---|
| 2026-11-05 | Sentiment models are weak on slang/mixed statements and over-confident: accuracy FinBERT 0.604, distilroberta-fin 0.625, Cardiff Twitter-RoBERTa 0.646, FinTwitBERT 0.708 (n=48, AI-labelled) | [SENTIMENT_METHODOLOGY](SENTIMENT_METHODOLOGY.md) |
| 2026-11-05 | 30% of AAPL posts are near-duplicates, 24% spam-flagged, 27.5% bot-like (heuristics); using all posts makes sentiment slightly worse than the filtered set | EXP-002, `clean_posts.py` |
| 2026-11-05 | Pre-open sentiment correlates with the overnight gap (0.23) but not with the rest of the day (0.02); session sentiment correlates 0.45 with open→close return | EXP-010 |
| 2026-11-05 | 80% empirical forecast intervals cover only 70.5% out of sample (n+1, ridge) | `uncertainty.coverage_by_fold` |
| 2026-11-05 | Post volume and sentiment dispersion shifted sharply between 2015-17 and 2019 (PSI up to 1.76); volume fell ~45% after 2016 | monitoring report |
| 2026-11-05 | Power analysis (ridge, n+1): detection rate 5% / 25% / 80% for true R² of 1% / 2% / 4% | EXP-013 |

## EXP-012: replication with a second sentiment model (FinTwitBERT) - completed
FinTwitBERT (finance-tweet model, 0.708 vs FinBERT's 0.604 on the validation items) was run through the entire pipeline. Per-post agreement with FinBERT is modest (Spearman 0.56) but daily mean sentiment correlates 0.87. Every headline conclusion above is reproduced: no significant incremental value (mean effect -0.67..+0.25% across horizons, 0/40 after correction; mean net PnL combined -0.05 vs buy-and-hold +0.854), nothing significantly better or worse than persistence (125 tests), the close-to-close nowcast edge (+3.8%, sentiment-only R² 5-7%) is the overnight-gap echo (pre-open sentiment vs gap 0.26, vs intraday 0.04), and lagged sentiment has no relation to returns (+0.014 / -0.005). Details: [EXPERIMENT_LOG](../history/EXPERIMENT_LOG.md).
The measurement-quality objection is therefore weakened but not eliminated (the two series are 0.87 correlated; both validated on the same small AI-labelled set).

## What would change these conclusions
A larger sample or intraday data (power); point-in-time engagement/follower snapshots from live Apify collection; real news timestamps (Tavily); human-validated sentiment labels; other assets (BTC corpus is available). None of these were available or in scope here.
