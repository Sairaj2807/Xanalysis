# Sentiment Methodology

**Model:** `ProsusAI/finbert` ([finbert_analyzer.py](../../sentiment/finbert_analyzer.py)), fp16 on GPU, max 96 tokens, batch 128. Output per text: `p_positive, p_neutral, p_negative`, `sentiment_score = p_pos − p_neg ∈ [-1, 1]`, `confidence = max probability` (**not calibrated**). Label order is read from the model config (this checkpoint: 0 positive, 1 negative, 2 neutral).

**Scoring run:** unique `dedup_key` texts only (996,456); ≈240 texts/s; resumable chunks (NLP-003, in progress).

**Validation (2026-11-05, `scripts/score_sentiment.py --validate`):** 48 items in [sentiment_validation.csv](../../data/validation/sentiment_validation.csv), **labelled by the AI agent, not human-reviewed** (some items are genuinely ambiguous).
- Accuracy 0.604. Positive P/R/F1 = 0.667/0.471/0.552; neutral 0.438/0.583/0.500; negative 0.700/0.737/0.718.
- Confusion (rows true → pred pos/neu/neg): pos 8/6/3, neu 2/7/3, neg 2/3/14.
- By category: slang 3/8, mixed 0/4, ambiguous 2/4, earnings 6/8, guidance 3/4, sarcasm 2/3.
- Calibration: highest bin (conf ≥0.87, n=27) mean conf 0.92 vs accuracy 0.70 → **overconfident**; lowest bins accuracy 0.0–0.4.
Interpretation: with n=48 the accuracy interval is wide; the direction of the findings (slang/mixed weakness, overconfidence) is more reliable than the exact number. Do not use confidence as a correctness probability. Sarcasm is not detected as such.

**Aggregation ([sentiment_aggregation.py](../../sentiment/sentiment_aggregation.py)):** A simple mean; B engagement-weighted `w = 1+log(1+likes+reposts+replies)` (**leaky**, DEC-007); C author-weighted `w = 1+log(1+prior posts by author)` (point-in-time; follower counts do not exist in this dataset); D confidence-weighted. Counts use thresholds ±0.05 (DEC-012). Weighting comparison (STAT-003) not yet run — nothing may be claimed about which method is better.

**Not done:** alternative model comparison (NLP-005), human-reviewed validation set, author influence from historical consistency.

## Model comparison (2026-11-05, same 48 AI-labelled items)
| Model | Accuracy | Slang | Mixed | Sarcasm |
|---|---:|---:|---:|---:|
| ProsusAI/finbert (default) | 0.604 | 3/8 | 0/4 | 2/3 |
| mrm8488/distilroberta-finetuned-financial-news | 0.625 | 2/8 | 1/4 | 2/3 |
| cardiffnlp/twitter-roberta-base-sentiment-latest | 0.646 | 5/8 | 3/4 | 1/3 |
| StephanAkkerman/FinTwitBERT-sentiment | 0.708 | 6/8 | 1/4 | 1/3 |
n=48 and labels by the AI agent: differences of up to 5 items are within noise. FinTwitBERT (trained on finance tweets, labels bullish/bearish) was scored on the whole corpus as a measurement-robustness check (EXP-012, [EXPERIMENT_LOG](../history/EXPERIMENT_LOG.md)). Label aliasing (positive≡bullish, negative≡bearish) is in `finbert_analyzer.resolve_label_indices`.
