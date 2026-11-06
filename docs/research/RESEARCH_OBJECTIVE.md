# Research Objective

Primary question: **does X sentiment, combined with historical prices, improve out-of-sample forecasts of future AAPL prices compared with prices alone?**

Design: for each horizon h ∈ {1..5} and each model family, compare feature sets A (price), B (sentiment), C (price + sentiment + interactions) on identical purged walk-forward folds. Metric: reduction in forecast error of C vs A (`Improvement_h = (Err_A − Err_C)/Err_A × 100`), with Diebold-Mariano p-values (Holm-corrected across horizons), block-bootstrap CI and per-fold consistency.

Twelve final research questions and their current answer status: [RESEARCH_FINDINGS](../research/RESEARCH_FINDINGS.md). Hypotheses: [RESEARCH_HYPOTHESES](../research/RESEARCH_HYPOTHESES.md). Success = a defensible answer, positive or negative.
