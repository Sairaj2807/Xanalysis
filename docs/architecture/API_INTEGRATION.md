# API Integration

| Service | Client | Auth | Status |
|---|---|---|---|
| Apify (X posts) | [ingestion/apify_client.py](../../ingestion/apify_client.py) | `APIFY_API_TOKEN`, `APIFY_ACTOR_ID` | BLOCKED: never run. Parsing/validation tested on fixtures; actor input keys assumed (BUG-005) |
| Tavily (news) | [ingestion/tavily_client.py](../../ingestion/tavily_client.py) | `TAVILY_API_KEY` | BLOCKED: never run. `published_at` is None when Tavily omits it |
| yfinance (prices) | [ingestion/price_ingestion.py](../../ingestion/price_ingestion.py) | none | VERIFIED for AAPL 1d |
| HuggingFace Hub | transformers | none | FinBERT weights downloaded (cached in `~/.cache/huggingface`) |

Implemented: env-var auth, tenacity exponential backoff (Apify 5 attempts, Tavily 4), response validation (drop items lacking id/text), null-preserving mapping, field-availability report. **Missing:** pagination across date windows, incremental state, rate-limit-specific handling, request timeouts beyond client defaults for Tavily, ingestion log writes (ING-004).

## Update 2026-11-05
`ingestion/x_scraper.py::XCollector` adds per-(query, window) collection, exclusion keywords, unparseable-timestamp rejection, idempotent inserts, `ingestion_logs` state and incremental windows. `ingestion/news_processing.py` adds relevance, time validation, clustering, event categorisation, sentiment and social-vs-news flags. Both are tested only with fakes/fixtures; **no live call to Apify or Tavily has ever been made** (no credentials).
