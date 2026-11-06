"""News processing: relevance scoring, publication-time validation, near-duplicate clustering, event
categorisation, sentiment (injected analyzer) and social-vs-news comparison.

News stays a SEPARATE research layer: nothing here feeds the primary price + X-sentiment model.
Tested on fixtures only; Tavily has not been called live (no API key).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from preprocessing.timestamp_alignment import to_utc

EVENT_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("earnings", ("earnings", "eps", "quarterly", "revenue", "profit", "results")),
    ("guidance", ("guidance", "outlook", "forecast", "expects")),
    ("regulatory", ("sec ", "antitrust", "regulator", "fine", "probe", "ban", "tariff")),
    ("legal", ("lawsuit", "court", "patent", "settlement", "sues")),
    ("m&a", ("acquire", "acquisition", "merger", "buyout", "takeover")),
    ("analyst", ("upgrade", "downgrade", "price target", "analyst", "rating")),
    ("product", ("launch", "unveil", "iphone", "new product", "release", "announces")),
    ("management", ("ceo", "executive", "resigns", "appoints", "layoff")),
    ("macro", ("fed ", "inflation", "interest rate", "gdp", "recession")),
]
_TOKEN = re.compile(r"[a-z0-9$]+")


def _tokens(s: str) -> set[str]:
    return set(_TOKEN.findall(s.lower()))


def relevance_score(article: dict, terms: list[str]) -> float:
    """Share of asset terms present in headline (weight 2) or body (weight 1), in [0, 1]."""
    head, body = (article.get("headline") or "").lower(), (article.get("content") or "").lower()
    if not terms:
        return 0.0
    got = sum(min(2 * (t.lower() in head) + (t.lower() in body), 2) for t in terms)
    return got / (2 * len(terms))


def validate_publication_time(article: dict) -> dict:
    """Adds `published_at_utc` and `time_valid`. Invalid = missing/unparseable or later than retrieval
    (an article cannot be published after we retrieved it). Invalid articles must not be used point-in-time."""
    pub = to_utc(pd.Series([article.get("published_at")]), assume_tz="UTC").iloc[0]
    ret = to_utc(pd.Series([article.get("retrieved_at")]), assume_tz="UTC").iloc[0]
    ok = (not pd.isna(pub)) and (pd.isna(ret) or pub <= ret)
    return {**article, "published_at_utc": None if pd.isna(pub) else pub, "time_valid": bool(ok)}


def categorize_event(article: dict) -> str:
    text = f"{article.get('headline', '')} {article.get('content', '') or ''}".lower() + " "
    scores = {name: sum(k in text for k in kws) for name, kws in EVENT_RULES}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "other"


def cluster_articles(articles: list[dict], threshold: float = 0.6) -> list[dict]:
    """Greedy single-pass clustering on headline token Jaccard similarity. Adds `cluster_id`."""
    reps: list[set[str]] = []
    out = []
    for a in articles:
        tk = _tokens(a.get("headline", ""))
        cid = next((i for i, r in enumerate(reps) if tk and len(tk & r) / len(tk | r) >= threshold), None)
        if cid is None:
            reps.append(tk)
            cid = len(reps) - 1
        out.append({**a, "cluster_id": cid})
    return out


def classify_sentiment(articles: list[dict], analyzer) -> list[dict]:
    """analyzer.score(texts) -> dict with sentiment_score/confidence (same interface as FinBertAnalyzer)."""
    if not articles:
        return []
    texts = [f"{a.get('headline', '')}. {(a.get('content') or '')[:300]}" for a in articles]
    s = analyzer.score(texts)
    return [{**a, "sentiment_score": float(s["sentiment_score"][i]), "confidence": float(s["confidence"][i])}
            for i, a in enumerate(articles)]


def process_articles(articles: list[dict], terms: list[str], analyzer=None, min_relevance: float = 0.25) -> pd.DataFrame:
    rows = [validate_publication_time(a) for a in articles]
    rows = [{**a, "relevance": relevance_score(a, terms), "event_type": categorize_event(a)} for a in rows]
    rows = cluster_articles(rows)
    rows = [a for a in rows if a["relevance"] >= min_relevance]
    if analyzer is not None:
        rows = classify_sentiment(rows, analyzer)
    return pd.DataFrame(rows)


def compare_social_news(social: pd.DataFrame, news: pd.DataFrame, thr: float = 0.05, volume_z: float = 2.0) -> pd.DataFrame:
    """social: index trading_day with mean_sentiment, post_count. news: trading_day, sentiment_score (article level).
    Flags days where signs disagree beyond +-thr, plus social volume spikes (log post-count z-score > volume_z)."""
    n = news.groupby("trading_day")["sentiment_score"].agg(news_sentiment="mean", n_articles="size")
    d = social.set_index("trading_day") if "trading_day" in social.columns else social
    d = d[["mean_sentiment", "post_count"]].join(n, how="left")
    lp = np.log1p(d["post_count"])
    d["volume_z"] = (lp - lp.rolling(60, min_periods=20).mean()) / lp.rolling(60, min_periods=20).std()
    d["volume_spike"] = d["volume_z"] > volume_z
    d["social_pos_news_neg"] = (d.mean_sentiment > thr) & (d.news_sentiment < -thr)
    d["social_neg_news_pos"] = (d.mean_sentiment < -thr) & (d.news_sentiment > thr)
    d["divergence"] = d["social_pos_news_neg"] | d["social_neg_news_pos"]
    return d
