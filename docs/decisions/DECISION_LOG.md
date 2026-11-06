# Decision Log

All significant architecture and research decisions. Never silently change methodology: add a new entry that supersedes the old one. Topical views: [ARCHITECTURE_DECISIONS](ARCHITECTURE_DECISIONS.md), [RESEARCH_DECISIONS](RESEARCH_DECISIONS.md).

## DEC-001: Primary asset and timeframe — AAPL, daily bars
Date: 2026-11-05 · Status: Accepted (user choice)
### Context
Repository had two unrelated tweet datasets (6 stocks 2015–2019; BTC 2013–2023) and no price data.
### Alternatives
BTC hourly (VADER scores already present, more samples); another stock ticker.
### Decision
AAPL, daily bars, America/New_York.
### Rationale
Matches the specification's example asset; free daily history covers 2015–2019; user selected it.
### Consequences
~1.2k usable daily observations → low statistical power; 5 years of tweets only; BTC data unused.
### Revisit Conditions
If power proves insufficient, or intraday prices become available for the tweet period.

## DEC-002: Python 3.12 virtual environment
Date: 2026-11-05 · Status: Accepted (user approved)
### Context
System Python 3.14 may lack wheels for torch/catboost/lightgbm.
### Alternatives
Stay on 3.14; use 3.10.
### Decision
Install 3.12.10 (winget, user scope) and use `.venv`.
### Rationale
Wheel availability; confirmed all packages installed.
### Consequences
Must run everything with `.venv/Scripts/python.exe`.
### Revisit Conditions
When 3.14 wheels are confirmed for the full stack.

## DEC-003: FinBERT (ProsusAI/finbert) as the sentiment model
Date: 2026-11-05 · Status: Accepted (as benchmark)
### Context
Spec requires a financial-domain model, full probabilities, and comparison with alternatives.
### Alternatives
VADER (exists only for crypto set), generic sentiment models, other financial transformers.
### Decision
FinBERT, fp16 on GPU, max_length 96, batch 128.
### Rationale
Standard financial benchmark; runs at ~240 texts/s on the available GPU.
### Consequences
Measured accuracy 0.604 on 48 self-labelled items: weak on slang (3/8) and mixed statements (0/4), overconfident. Alternatives not yet compared (NLP-005).
### Revisit Conditions
Human-reviewed validation shows another model is better; or sentiment features show no signal and model quality is suspected.

## DEC-004: Storage — Parquet + DuckDB for bulk data, SQLite via SQLAlchemy for state
Date: 2026-11-05 · Status: Accepted
### Context
Multi-GB CSVs and 1.4M-row working sets.
### Alternatives
PostgreSQL/Timescale for everything.
### Decision
Bulk research data in Parquet processed with DuckDB/pandas; relational schema defined for ingestion state, predictions, model runs.
### Rationale
Fast, no server needed.
### Consequences
The DB schema exists but is unused by the pipeline (DB-003); Postgres upsert not implemented (DB-004).
### Revisit Conditions
Live incremental ingestion is implemented.

## DEC-005: Targets are future log returns; prices reconstructed
Date: 2026-11-05 · Status: Accepted (per specification)
### Context
Price levels are non-stationary.
### Decision
`y_h = ln(P_{t+h}/P_t)`, `P_hat = P_t·exp(y_hat)`; metrics per horizon; persistence = zero return.
### Rationale / Consequences
Comparable across time; n+0 is not part of this and needs its own definition (ML-006).
### Revisit Conditions
If a different target (e.g. direction classification) is justified by results.

## DEC-006: Information cutoff = exchange close (16:00 America/New_York)
Date: 2026-11-05 · Status: Accepted
### Context
Daily bars; posts must not inform a prediction made before they exist.
### Decision
A post is assigned to the first trading day whose close is ≥ the post time. Weekend/holiday/after-close posts roll to the next trading day. Row `t` features use data through `t`'s close; targets use closes after `t`.
### Rationale
Strict no-look-ahead; unit-tested including DST.
### Consequences
Closing price is assumed to be actionable at the close; trading-rule realism is a separate question (VAL-002 rule).
### Revisit Conditions
Intraday data or a different execution assumption.

## DEC-007: Engagement features excluded from primary feature sets
Date: 2026-11-05 · Status: Accepted
### Context
Likes/retweets/replies are lifetime counts scraped later, not point-in-time.
### Decision
`sent_engagement_w` and `engagement_*` computed but flagged leaky; `include_leaky=False` by default.
### Consequences
Question 5 (does engagement weighting help?) cannot be answered cleanly with this dataset; any engagement result must be labelled leaky.
### Revisit Conditions
Live Apify collection with repeated snapshots.

## DEC-008: Primary post filter
Date: 2026-11-05 · Status: Accepted (revisitable)
### Decision
Primary = canonical (non-duplicate) AND not spam-flagged AND `english_score ≥ 0.5`. Alternatives `all_posts` and `no_bots` are available as robustness checks in `scripts/build_features.py`.
### Rationale / Consequences
Reduces promotional/duplicate noise but the flags are uncalibrated heuristics; conclusions should be checked under all filters.
### Revisit Conditions
Flag precision measured; or results sensitive to the filter.

## DEC-009: Score unique texts only
Date: 2026-11-05 · Status: Accepted
### Decision
Score one text per `dedup_key` (996,456 of 1,424,481) and map scores back to all posts sharing the key.
### Consequences
~30% compute saved; near-duplicates share identical sentiment by construction.

## DEC-010: Walk-forward configuration
Date: 2026-11-05 · Status: Accepted (provisional)
### Decision
`train_min=500`, `test_len=60`, `embargo=1`, expanding window, inner validation `val_len=120`, tiny hyperparameter grids.
### Rationale
~1.2k observations cannot support large grids or many folds.
### Revisit Conditions
After the first real run, if folds are too few/noisy.

## DEC-011: AI agent makes no commits or pushes
Date: 2026-11-05 · Status: Accepted (user instruction)
### Context
User supplied the GitHub repo URL and asked that the AI not commit/push so its involvement is not displayed.
### Decision
`git init` + `origin` remote only. No commits, pushes, merges or attribution lines unless explicitly requested later.
### Consequences
"Related Git commit" in the task register is `—`; no version history exists.
### Revisit Conditions
User asks for commits.

## DEC-012: Sentiment class thresholds for counts
Date: 2026-11-05 · Status: Accepted (provisional)
### Decision
For daily positive/negative/neutral counts use score thresholds ±0.05 on `S = P(pos) − P(neg)`.
### Consequences
Arbitrary; sensitivity untested. Revisit if count-based features matter.

## DEC-013: Crypto/BTC datasets are out of scope for the AAPL study
Date: 2026-11-05 · Status: Accepted
### Context
Eleven pre-existing CSVs hold a BTC tweet corpus (up to 11 GB) with VADER scores.
### Alternatives
Run a second BTC study; profile everything.
### Decision
Not used. Only one check was made (row-count reconciliation, which showed no parse loss, DATA-004).
### Consequences
No cross-asset evidence; the VADER-scored BTC corpus remains an available second study.
### Revisit Conditions
If the owner wants a replication on BTC with hourly prices.

## DEC-014: Headline claims require Holm correction over the whole family of tests
Date: 2026-11-05 · Status: Accepted
### Context
EXP-001 alone has 40 model×horizon comparisons; the ablation 105; versus-persistence 230.
### Decision
A result is called significant only if its Holm-adjusted p over ALL rows of the relevant table is < 0.05 (`dm_p_holm_global`). Raw p-values and per-model Holm are reported but are exploratory.
### Consequences
Few if any findings survive; this is intended. Near-misses are reported as exploratory.
### Revisit Conditions
A pre-registered, narrower hypothesis family (e.g. a single model and horizon fixed in advance).

## DEC-015: Two definitions of the n+0 nowcast
Date: 2026-11-05 · Status: Accepted
### Context
A current-period estimate must not be a trivial identity or use post-cutoff data.
### Decision
(a) close-to-close: target ln(P_D/P_{D-1}) from prices through D-1 and posts up to 09:30 on D; (b) intraday: target ln(close_D/open_D) from the same plus the opening gap (known at 09:30).
### Rationale
(a) exposed that pre-open sentiment merely echoes the overnight gap; (b) is the actionable form.
### Consequences
Only (b) is a fair test of "does sentiment add information at the open".
### Revisit Conditions
Intraday price data become available.

## DEC-016: Repeat the experiment with a second sentiment model
Date: 2026-11-05 · Status: Accepted
### Context
FinBERT scored 0.604 on the small validation set, so a null result might reflect poor measurement.
### Decision
Score the full corpus with FinTwitBERT (0.708 on the same set) and repeat EXP-001, nowcasts and diagnostics; report both.
### Consequences
~85 minutes of GPU time; if both agree the measurement-quality objection is weakened (not removed: both validated on 48 AI-labelled items).
### Revisit Conditions
Human-reviewed validation labels.

## DEC-017: Forecast immutability enforced in the database and by run folders
Date: 2026-11-05 · Status: Accepted
### Decision
`model_predictions` forbids DELETE and any change to forecast fields (SQLite triggers; Alembic migration includes them); `actual_*` may be filled later. Experiment runs are written to new timestamped folders and never overwritten.
### Consequences
PostgreSQL needs an equivalent trigger (not implemented, BUG-006).

## DEC-018: Engagement features only in a labelled leaky experiment
Date: 2026-11-05 · Status: Accepted (supersedes nothing; extends DEC-007)
### Decision
Lifetime engagement counts are used only in EXP-011, clearly labelled leaky, to answer whether engagement weighting would even look better. They never enter the primary or any reported-as-predictive model.

## DEC-019: Prediction intervals are empirical residual quantiles with measured coverage
Date: 2026-11-05 · Status: Accepted
### Decision
Intervals = point forecast + quantiles of past out-of-sample errors; calibration is checked by fold-wise coverage and reported (measured 70.5% vs nominal 80% at n+1).
### Revisit Conditions
Conformal or volatility-scaled intervals if intervals are needed for decisions.
