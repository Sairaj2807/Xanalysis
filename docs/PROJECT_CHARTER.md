# Project Charter

**Mission:** determine, with defensible out-of-sample statistics, whether aggregated X (Twitter) sentiment contains incremental information about future asset prices beyond historical prices.

**Scope (in):** one configurable asset (currently AAPL, daily); ingestion of X posts (historical CSV now, Apify live later), prices, news (separate layer); financial sentiment scoring; leakage-safe features; purged walk-forward validation of price-only / sentiment-only / combined models for horizons n+1…n+5; significance testing; dashboard and reports.

**Scope (out, for now):** live trading, order execution, portfolio construction, multi-asset models, the BTC datasets, production deployment.

**Success criterion:** a controlled A-vs-C comparison per horizon with honest reporting of incremental improvement, including the possibility of none. It is **not** to produce a model that predicts well.

**Principles:** temporal correctness > data integrity > reproducibility > out-of-sample performance. Null results are results.

**Constraints:** see [PROJECT_MASTER_CONTEXT](PROJECT_MASTER_CONTEXT.md) (critical constraints). **Stakeholder:** project owner (user). **Governance:** decisions in [DECISION_LOG](decisions/DECISION_LOG.md).
