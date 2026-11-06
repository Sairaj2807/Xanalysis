"""DATA-003 / DATA-007 diagnostics.

DATA-003: why are some AAPL tweet ids linked in Company_Tweet.csv absent from the extract?
          Scans the raw Tweet.csv for each missing id as a record start.
DATA-007: agreement between the ASCII/stopword English heuristic and a real language identifier (py3langid) on a sample.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from config.settings import ROOT  # noqa: E402


def data003() -> dict:
    con = duckdb.connect()
    ext = (ROOT / "data" / "raw" / "x_posts" / "stock_tweets_AAPL.parquet").as_posix()
    link = (ROOT / "data" / "Company_Tweet.csv").as_posix()
    missing = [r[0] for r in con.execute(
        f"SELECT DISTINCT CAST(tweet_id AS VARCHAR) FROM read_csv('{link}', header=true, columns={{'tweet_id':'BIGINT','ticker_symbol':'VARCHAR'}}) "
        f"WHERE ticker_symbol='AAPL' AND CAST(tweet_id AS VARCHAR) NOT IN (SELECT post_id FROM read_parquet('{ext}'))").fetchall()]
    want = set(missing)
    raw = (ROOT / "data" / "Tweet.csv").read_bytes()
    found_rows = {}
    for m in re.finditer(rb"(?:^|\n)(\d{15,19}),", raw):
        i = m.group(1).decode()
        if i in want:
            found_rows.setdefault(i, m.start())
    in_file = len(found_rows)
    # of the ids present in the raw file, were they dropped by the CSV parser (e.g. malformed quoting)?
    sample = list(found_rows.items())[:3]
    snippets = [raw[p + 1:p + 160].decode("utf-8", "replace").replace("\n", "\\n") for _, p in sample]
    return {"missing_ids": len(missing), "present_in_raw_tweet_csv": in_file, "absent_from_raw_tweet_csv": len(missing) - in_file,
            "snippets_of_present_but_dropped": snippets}


def data007(n: int = 20000, seed: int = 0) -> dict:
    import py3langid as langid

    posts = pd.read_parquet(ROOT / "data" / "processed" / "posts_AAPL.parquet", columns=["clean_text", "english_score"])
    s = posts.sample(n, random_state=seed).reset_index(drop=True)
    lang = s["clean_text"].map(lambda t: langid.classify(t)[0])
    is_en = lang == "en"
    heur = s["english_score"] >= 0.5
    tab = pd.crosstab(heur.rename("heuristic_english"), is_en.rename("langid_english"))
    agree = float((heur == is_en).mean())
    return {"n": n, "agreement": agree, "langid_english_share": float(is_en.mean()), "heuristic_english_share": float(heur.mean()),
            "crosstab": tab.to_dict(), "top_langs": lang.value_counts().head(6).to_dict()}


if __name__ == "__main__":
    which = sys.argv[1:] or ["data003", "data007"]
    if "data003" in which:
        print("DATA-003", data003())
    if "data007" in which:
        print("DATA-007", data007())
