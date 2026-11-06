# Data Limitations

1. **Lifetime engagement counts** (likes/reposts/replies) are scraped after the fact → not point-in-time → leaky; excluded from primary features. Engagement-weighting research is therefore limited.
2. No follower counts, language, verification or views in the stock dataset → author influence limited to prior post count.
3. Historical window 2015–2019 only; live Apify data would be a different sample (180-day lookback from today).
4. Daily bars: few independent observations (~1.2k) for five horizons and many models.
5. `close` is split-adjusted but not dividend-adjusted → ex-dividend drops appear as returns.
6. Duplicate-heavy (30%) and spam/bot-heavy corpus; flags are heuristics.
7. `post_date` timezone presumed UTC.
8. 532 ids dropped by the bulk parser (root cause known, recovered into a supplementary file but not merged downstream, BUG-004); post volume falls ~45% after 2016 and sentiment dispersion/volume drift strongly (PSI up to 1.76) so the sentiment signal's statistics are not stationary.
9. News: none. Database unused.
10. Crypto files: no parse loss (verified for the vader file); mixed/unknown timestamp timezones; no 2020 (out of current scope, DEC-013).
