"""Tavily news retrieval. News is kept in a separate layer and never enters the primary model."""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

from tenacity import retry, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)


def parse_result(r: dict, asset: str, query: str, retrieved_at: datetime | None = None) -> dict | None:
    if not r.get("url") or not r.get("title"):
        return None
    return {
        "article_id": hashlib.sha256(r["url"].encode()).hexdigest()[:32],
        "headline": r["title"],
        "url": r["url"],
        "source": urlparse(r["url"]).netloc.removeprefix("www."),
        "published_at": r.get("published_date"),  # None when Tavily does not provide it
        "retrieved_at": (retrieved_at or datetime.now(timezone.utc)).isoformat(),
        "content": r.get("content"),
        "asset": asset,
        "query": query,
        "relevance_score": r.get("score"),
    }


class TavilyNews:
    def __init__(self, api_key: str):
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY must be set (see .env.example)")
        from tavily import TavilyClient

        self._c = TavilyClient(api_key=api_key)

    @retry(reraise=True, stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=2, max=30))
    def search(self, query: str, asset: str, days: int = 7, max_results: int = 20) -> list[dict]:
        resp = self._c.search(query=query, topic="news", days=days, max_results=max_results)
        now = datetime.now(timezone.utc)
        rows = [parse_result(r, asset, query, now) for r in resp.get("results", [])]
        return dedupe_articles([r for r in rows if r])


def dedupe_articles(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out = []
    for r in rows:
        if r["article_id"] not in seen:
            seen.add(r["article_id"])
            out.append(r)
    return out
