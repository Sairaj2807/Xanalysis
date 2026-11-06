# Apple (AAPL) - Sentiment Outlook (data as of 2019-12-31)

*Report generated 2026-11-05 21:38. Research output - not investment advice; sentiment is not a validated trading signal.*

## 1. Observed facts

- Latest observable close: **73.41**; data coverage 2015-02-02 to 2019-12-31.
- X posts analysed: 663,144 (46,846 unique authors); last 20 trading days: 5,662.
- Last-20-day mix: positive 44.5% / neutral 33.7% / negative 21.8%; net sentiment +0.057; momentum (5d vs 20d) +0.024; volatility 0.053; post-volume trend +10%.
- Price: 5-day +3.4%, 20-day +11.2%; daily vol 1.01%; short-term trend up; sentiment-price divergence z = -0.06.
- News: No news data available (Tavily has not been run).

## 2. Model predictions (research forecast)

| Horizon | Predicted price | Predicted return | 80% nominal interval (measured out-of-sample coverage 70%) |
|---|---:|---:|---|
| n+0 | 73.41 (observed close; not a prediction) | - | - |
| n+1 | 73.54 | +0.170% | 72.32 - 74.82 |
| n+2 | 73.65 | +0.318% | 71.92 - 75.57 |
| n+3 | 73.78 | +0.499% | 71.65 - 76.14 |
| n+4 | 73.97 | +0.763% | 71.46 - 76.68 |
| n+5 | 74.06 | +0.877% | 71.00 - 76.92 |

Model: `ridge`. Out-of-sample evidence shows such models do not beat 'no change'; treat as indicative only.

## 3. Research interpretation

- Current sentiment: **Positive**; momentum: **Improving**.
- Price-sentiment relationship: No validated predictive relationship: across 8 classical learners and 7 deep/multi-output architectures, 5 horizons, 3 post filters, 7 feature groups and 2 nowcast definitions, sentiment did not improve out-of-sample forecasts; sentiment correlates with same-day returns (it reacts to price) but not with next-day returns.
- Bullish observations: 20-day net FinBERT sentiment +0.057 (positive); 5-day return +3.4%; Short-term trend above 20-day average
- Bearish observations: None identified
- Limitations: Forecast models did not beat the no-change forecast out of sample. Sentiment model accuracy ~0.60-0.71 on a small hand-labelled set. Single asset, 2015-2019 history; no live data or news layer. Intervals are empirical from past errors and not guaranteed calibrated.

*Interval calibration check (n+1, ridge, out-of-sample): nominal 80% -> empirical 70.5% over 600 points; intervals are too narrow.*
