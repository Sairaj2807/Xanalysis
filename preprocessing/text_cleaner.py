"""Post cleaning and flagging. Nothing is dropped here: spam/bot/duplicate are flags, and the
raw text is preserved separately from `clean_text` (raw posts live in data/raw)."""
from __future__ import annotations

import html
import re
import unicodedata

import pandas as pd

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
MENTION_RE = re.compile(r"@\w+")
CASHTAG_RE = re.compile(r"\$[A-Za-z][A-Za-z.]{0,9}\b")
HASHTAG_RE = re.compile(r"#\w+")
WS_RE = re.compile(r"\s+")
DIGITS_RE = re.compile(r"\d+")

# Promotional / pump patterns common in stock-tweet spam. Heuristic, not exhaustive.
SPAM_PATTERNS = re.compile(
    r"(?:profit\.ly|made \$[\d,]+|check it out|free (?:trial|alerts?|picks?)|join (?:us|now)|"
    r"click here|sign ?up|penny stock|guaranteed|dm me|giveaway)", re.I)


def normalise_text(s: pd.Series) -> pd.Series:
    """Entity-decode, NFKC-normalise, collapse URLs to the token 'URL', strip whitespace."""
    out = s.fillna("").map(html.unescape).map(lambda x: unicodedata.normalize("NFKC", x))
    out = out.str.replace(URL_RE, " URL ", regex=True)
    return out.str.replace(WS_RE, " ", regex=True).str.strip()


def dedup_key(clean: pd.Series) -> pd.Series:
    """Normalised key for near-duplicate detection: case-folded, URL/mention/digit-insensitive."""
    k = clean.str.lower()
    k = k.str.replace(MENTION_RE, "", regex=True).str.replace(DIGITS_RE, "0", regex=True)
    k = k.str.replace(r"[^a-z0$# ]", "", regex=True).str.replace(WS_RE, " ", regex=True).str.strip()
    return k


def extract_entities(clean: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({
        "cashtags": clean.str.findall(CASHTAG_RE).map(lambda x: sorted({c.upper() for c in x})),
        "hashtags": clean.str.findall(HASHTAG_RE).map(lambda x: sorted({h.lower() for h in x})),
    })


_EN_STOP = frozenset("the a an and or of to in is are was for on with at by this that it be as from have has will "
                     "not but you i we they up down buy sell short long call put".split())


def english_likelihood(clean: pd.Series) -> pd.Series:
    """Cheap language heuristic in [0,1]: share of ASCII letters x presence of English function words.
    A proper identifier (langid) is applied in scripts/clean_posts.py when installed."""
    ascii_ratio = clean.map(lambda t: sum(c < "\x80" for c in t) / max(len(t), 1))
    stop_hit = clean.str.lower().str.findall(r"[a-z]+").map(lambda ws: any(w in _EN_STOP for w in ws))
    return ascii_ratio * stop_hit.astype(float)


def spam_flags(clean: pd.Series, cashtags: pd.Series, dup_count: pd.Series) -> pd.DataFrame:
    n_cash = cashtags.map(len)
    url_only = clean.str.replace("URL", "", regex=False).str.replace(r"[^A-Za-z]", "", regex=True).str.len() < 5
    return pd.DataFrame({
        "flag_promo": clean.str.contains(SPAM_PATTERNS, na=False),
        "flag_many_cashtags": n_cash >= 4,
        "flag_url_only": url_only,
        "flag_duplicate_text": dup_count > 1,
    })


def clean_posts(df: pd.DataFrame) -> pd.DataFrame:
    """df needs post_id, created_at, username, text. Returns df plus derived columns."""
    out = df.copy()
    out["clean_text"] = normalise_text(out["text"])
    out["dedup_key"] = dedup_key(out["clean_text"])
    ent = extract_entities(out["clean_text"])
    out["cashtags"], out["hashtags"] = ent["cashtags"], ent["hashtags"]
    out["dup_count"] = out.groupby("dedup_key")["post_id"].transform("size")
    # canonical = earliest occurrence of the key; later copies are marked, not removed
    out = out.sort_values(["created_at", "post_id"], kind="stable")
    out["is_duplicate"] = out.duplicated("dedup_key", keep="first")
    out["english_score"] = english_likelihood(out["clean_text"])
    flags = spam_flags(out["clean_text"], out["cashtags"], out["dup_count"])
    out = pd.concat([out, flags], axis=1)
    out["flag_spam"] = out[["flag_promo", "flag_many_cashtags", "flag_url_only"]].any(axis=1)
    # bot-like author activity: user volume and share of that user's posts that are duplicates
    g = out.groupby("username")
    out["author_post_count"] = g["post_id"].transform("size")
    out["author_dup_share"] = g["is_duplicate"].transform("mean")
    out["flag_bot_like"] = (out["author_post_count"] >= 200) & (out["author_dup_share"] >= 0.5)
    return out
