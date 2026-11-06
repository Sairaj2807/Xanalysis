"""Apify wrapper: auth from env, retries with exponential backoff, response validation.

The actor's output schema is actor-specific. `parse_item` maps common field names and leaves
anything unavailable as None (never fabricated); `field_availability` reports coverage.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Iterable

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

log = logging.getLogger(__name__)

RAW_FIELDS = [
    "post_id", "created_at", "text", "author_id", "username", "followers_count", "following_count",
    "likes", "reposts", "replies", "views", "quotes", "language", "is_reply", "is_repost",
    "is_verified", "post_url", "query_source", "collected_at",
]

# candidate source keys per target field (first present wins)
_ALIASES: dict[str, list[str]] = {
    "post_id": ["id", "id_str", "tweetId", "tweet_id"],
    "created_at": ["createdAt", "created_at", "timestamp", "date"],
    "text": ["fullText", "full_text", "text"],
    "author_id": ["author.id", "user.id", "userId", "author_id"],
    "username": ["author.userName", "author.username", "user.screen_name", "username"],
    "followers_count": ["author.followers", "author.followersCount", "user.followers_count"],
    "following_count": ["author.following", "author.followingCount", "user.friends_count"],
    "likes": ["likeCount", "favorite_count", "likes"],
    "reposts": ["retweetCount", "retweet_count", "reposts"],
    "replies": ["replyCount", "reply_count", "replies"],
    "views": ["viewCount", "views"],
    "quotes": ["quoteCount", "quote_count", "quotes"],
    "language": ["lang", "language"],
    "is_reply": ["isReply", "is_reply"],
    "is_repost": ["isRetweet", "is_retweet", "is_repost"],
    "is_verified": ["author.isVerified", "author.isBlueVerified", "user.verified", "is_verified"],
    "post_url": ["url", "twitterUrl", "post_url"],
}


class ApifyError(RuntimeError):
    pass


def _get(d: dict, dotted: str) -> Any:
    cur: Any = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def parse_item(item: dict, query_source: str, collected_at: datetime | None = None) -> dict | None:
    """Map one actor item to the raw schema. Returns None if it lacks an id or text (invalid)."""
    out: dict[str, Any] = {}
    for field, keys in _ALIASES.items():
        out[field] = next((v for k in keys if (v := _get(item, k)) is not None), None)
    if out["post_id"] is None or out["text"] is None:
        return None
    out["post_id"] = str(out["post_id"])
    out["query_source"] = query_source
    out["collected_at"] = (collected_at or datetime.now(timezone.utc)).isoformat()
    return out


def field_availability(rows: Iterable[dict]) -> dict[str, float]:
    rows = list(rows)
    if not rows:
        return {}
    return {f: sum(r.get(f) is not None for r in rows) / len(rows) for f in RAW_FIELDS}


class ApifyXClient:
    def __init__(self, token: str, actor_id: str, timeout_s: int = 600):
        if not token or not actor_id:
            raise ApifyError("APIFY_API_TOKEN and APIFY_ACTOR_ID must be set (see .env.example)")
        from apify_client import ApifyClient

        self._client = ApifyClient(token, timeout_secs=timeout_s)
        self.actor_id = actor_id

    @retry(reraise=True, stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=60),
           retry=retry_if_exception_type(Exception))
    def _run(self, run_input: dict) -> list[dict]:
        run = self._client.actor(self.actor_id).call(run_input=run_input)
        if not run or "defaultDatasetId" not in run:
            raise ApifyError(f"actor run returned no dataset: {run}")
        return list(self._client.dataset(run["defaultDatasetId"]).iterate_items())

    def search(self, query: str, since: str, until: str, max_items: int = 5000) -> list[dict]:
        """since/until are YYYY-MM-DD. The input keys follow the common tweet-scraper actors;
        adjust `run_input` for the actor configured in APIFY_ACTOR_ID."""
        q = f"{query} since:{since} until:{until}"
        run_input = {"searchTerms": [q], "maxItems": max_items, "sort": "Latest"}
        items = self._run(run_input)
        collected = datetime.now(timezone.utc)
        parsed = [parse_item(i, query, collected) for i in items]
        bad = sum(p is None for p in parsed)
        if bad:
            log.warning("dropped %d/%d invalid items for %r", bad, len(items), query)
        return [p for p in parsed if p]
