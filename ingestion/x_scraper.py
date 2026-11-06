"""Incremental X collection on top of an Apify client (injectable for tests). Idempotent: re-running adds 0 posts.

State is kept in `ingestion_logs` (last successful collection, latest post time, last post id, counters).
Each (query, day-window) is fetched separately so one failure does not lose the others (status 'partial').
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import pandas as pd

from database.connection import insert_ignore_duplicates, session_scope
from database.models import RawXPost
from database.repositories import last_successful_collection, log_ingestion
from preprocessing.timestamp_alignment import to_utc

log = logging.getLogger(__name__)
DB_FIELDS = ["post_id", "created_at", "text", "author_id", "username", "followers_count", "likes", "reposts",
             "replies", "views", "language", "query_source", "collected_at"]


def _to_db_row(r: dict, symbol: str) -> dict | None:
    created = to_utc(pd.Series([r.get("created_at")]), assume_tz="UTC").iloc[0]
    if pd.isna(created):
        return None                      # unparseable time => cannot be point-in-time: dropped, not guessed
    row = {k: r.get(k) for k in DB_FIELDS}
    row["created_at"] = created.tz_convert("UTC").tz_localize(None).to_pydatetime()
    coll = to_utc(pd.Series([r.get("collected_at")]), assume_tz="UTC").iloc[0]
    row["collected_at"] = None if pd.isna(coll) else coll.tz_convert("UTC").tz_localize(None).to_pydatetime()
    row["asset_symbol"] = symbol
    for k in ("author_id", "post_id"):
        row[k] = None if row[k] is None else str(row[k])
    return row


class XCollector:
    def __init__(self, client, engine, symbol: str, queries: list[str], exclude_keywords: list[str] | None = None,
                 window_days: int = 7, source: str = "apify_x"):
        self.client, self.engine, self.symbol = client, engine, symbol
        self.queries, self.exclude = queries, [k.lower() for k in (exclude_keywords or [])]
        self.window_days, self.source = window_days, source

    def _windows(self, since: datetime, until: datetime):
        s = since
        while s < until:
            e = min(s + timedelta(days=self.window_days), until)
            yield s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")
            s = e

    def collect(self, since: datetime, until: datetime) -> dict:
        started = datetime.now(timezone.utc).replace(tzinfo=None)
        n_ret = n_new = 0
        failures: list[str] = []
        latest, last_id = None, None
        for q in self.queries:
            for a, b in self._windows(since, until):
                try:
                    items = self.client.search(q, a, b)
                except Exception as e:                       # record and continue with the other windows
                    failures.append(f"{q} {a}..{b}: {e}")
                    log.warning("collection failed for %s %s..%s: %s", q, a, b, e)
                    continue
                rows = []
                for it in items:
                    if self.exclude and any(k in str(it.get("text", "")).lower() for k in self.exclude):
                        continue
                    r = _to_db_row(it, self.symbol)
                    if r:
                        rows.append(r)
                n_ret += len(rows)
                with session_scope(self.engine) as s:
                    n_new += insert_ignore_duplicates(s, RawXPost, rows)
                for r in rows:
                    if latest is None or r["created_at"] > latest:
                        latest, last_id = r["created_at"], r["post_id"]
        status = "ok" if not failures else ("partial" if n_ret else "failed")
        log_ingestion(self.engine, self.source, started, status, n_ret, n_new, n_ret - n_new, latest, last_id,
                      "; ".join(failures)[:2000] or None)
        return {"status": status, "retrieved": n_ret, "new": n_new, "duplicates": n_ret - n_new,
                "failures": failures, "latest_post_ts": latest}

    def collect_incremental(self, now: datetime, lookback_days: int = 180, overlap_days: int = 1) -> dict:
        """First run: `lookback_days` of history. Later runs: from the last successful latest_post_ts minus overlap."""
        last = last_successful_collection(self.engine, self.source)
        since = (last.latest_post_ts - timedelta(days=overlap_days)) if last and last.latest_post_ts \
            else now - timedelta(days=lookback_days)
        return self.collect(since, now)
