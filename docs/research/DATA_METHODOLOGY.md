# Data Methodology

**Timestamps:** stored UTC. Stock-tweet `post_date` is epoch seconds, *presumed* UTC (unverified). Naive timestamps require an explicit timezone ([timestamp_alignment.py](../../preprocessing/timestamp_alignment.py)). Exchange-time logic uses zoneinfo (DST-aware).

**Cleaning ([text_cleaner.py](../../preprocessing/text_cleaner.py)):** HTML-unescape, NFKC, URLs → `URL`, whitespace collapse; `dedup_key` = lower-cased, mentions removed, digits → 0, non-alphanumerics stripped (near-duplicate approximation, not MinHash); cashtag/hashtag extraction; flags `flag_promo`, `flag_many_cashtags` (≥4), `flag_url_only`, `flag_spam`, `is_duplicate` (later copies of a key), `flag_bot_like` (author ≥200 posts and ≥50% duplicates), `english_score` (ASCII share × English-function-word presence). **Nothing is deleted;** low engagement is never a reason to drop.

**Selection filters** for aggregation: `primary`, `all_posts`, `no_bots` ([build_features.py](../../scripts/build_features.py)); DEC-008.

**Cutoff / alignment:** DEC-006. Empty days: `post_count = 0`, sentiment NaN, `had_posts = False`; never forward-filled.

**Prices:** yfinance, `auto_adjust=False`; `close` split-adjusted, `adj_close` also dividend-adjusted. Features use `close`.

**Not done:** proper language ID, calibrated spam/bot detection, intraday intervals, news alignment.
