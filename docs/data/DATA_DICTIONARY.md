# Data Dictionary

**stock_tweets_AAPL.parquet (raw):** post_id (str), created_at (UTC instant, naive dtype), username, text, replies, reposts, likes (lifetime counts, **not point-in-time**), asset_symbol, query_source. Absent in source (not invented): author_id, followers, following, views, quotes, language, verified, is_reply/is_repost, url, collected_at.

**posts_AAPL.parquet (processed)** adds: clean_text, dedup_key, cashtags, hashtags, dup_count, is_duplicate, english_score, flag_promo, flag_many_cashtags, flag_url_only, flag_duplicate_text, flag_spam, author_post_count, author_dup_share (computed over the full history — descriptive only, not for features), flag_bot_like.

**sentiment_AAPL.parquet (pending):** post_id, p_positive, p_neutral, p_negative, sentiment_score, confidence, model_name.

**AAPL_1d.parquet:** bar_start_utc (date label at 00:00 UTC, *not* the close time), symbol, open, high, low, close (split-adjusted), adj_close, volume, interval.

**sentiment_daily (aggregate, pending):** trading_day, post_count, positive/negative/neutral_count, mean/median_sentiment, sentiment_std, sent_engagement_w (leaky), sent_author_w, sent_confidence_w, engagement_total (leaky), unique_authors, sentiment_confidence, had_posts, positive/negative_ratio, sentiment_change.

**model_table (pending):** index trading_day; `price`; features prefixed `px_`, `sn_`, `ix_`; targets `y_1..y_5` (future log returns; never features). Feature meaning: [FEATURE_ENGINEERING](../research/FEATURE_ENGINEERING.md).
