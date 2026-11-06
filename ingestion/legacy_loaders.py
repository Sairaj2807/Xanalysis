"""Adapters turning the pre-existing CSV datasets into the project's raw schema (Parquet).

Raw CSVs are never modified; outputs are new files under data/raw/x_posts.
"""
from __future__ import annotations

import logging
from pathlib import Path

import duckdb

from config.settings import ROOT

log = logging.getLogger(__name__)
DATA = ROOT / "data"


def extract_stock_tweets(ticker: str, start: str, end: str, out_dir: Path | None = None) -> Path:
    """Join Tweet.csv with Company_Tweet.csv for one ticker and write UTC-normalised Parquet.

    Output columns follow the raw X schema where the source has the field; the stock
    dataset has no follower/view/language/verified data, so those are absent, not invented.
    post_date is epoch seconds and is treated as UTC (presumed; documented in DATA_AUDIT).
    """
    out_dir = out_dir or DATA / "raw" / "x_posts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"stock_tweets_{ticker}.parquet"
    tweet = (DATA / "Tweet.csv").as_posix()
    link = (DATA / "Company_Tweet.csv").as_posix()
    con = duckdb.connect()
    sql = f"""
    COPY (
      SELECT CAST(t.tweet_id AS VARCHAR)                       AS post_id,
             epoch_ms(CAST(t.post_date AS BIGINT) * 1000)      AS created_at,       -- UTC instant stored as naive TIMESTAMP
             t.writer                                          AS username,
             t.body                                            AS text,
             CAST(t.comment_num AS BIGINT)                     AS replies,
             CAST(t.retweet_num AS BIGINT)                     AS reposts,
             CAST(t.like_num AS BIGINT)                        AS likes,
             '{ticker}'                                        AS asset_symbol,
             'stock_tweets_csv'                                AS query_source
      FROM read_csv('{tweet}', max_line_size=10000000, ignore_errors=true, strict_mode=false,
                    columns={{'tweet_id':'BIGINT','writer':'VARCHAR','post_date':'BIGINT',
                              'body':'VARCHAR','comment_num':'BIGINT','retweet_num':'BIGINT',
                              'like_num':'BIGINT'}}, header=true) t
      JOIN (SELECT DISTINCT tweet_id FROM read_csv('{link}', header=true,
              columns={{'tweet_id':'BIGINT','ticker_symbol':'VARCHAR'}})
            WHERE ticker_symbol = '{ticker}') c USING (tweet_id)
      WHERE t.post_date BETWEEN epoch(TIMESTAMP '{start} 00:00:00') AND epoch(TIMESTAMP '{end} 23:59:59')
    ) TO '{out.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """
    con.execute(sql)
    n = con.execute(f"SELECT count(*) FROM read_parquet('{out.as_posix()}')").fetchone()[0]
    log.info("wrote %s rows to %s", n, out)
    return out


def recover_missing_posts(ticker: str, out_dir: Path | None = None, raw_csv: Path | None = None) -> Path:
    """Recover linked tweet ids that the bulk CSV parser dropped (BUG-004 / DATA-003).

    Root cause: in the large file a malformed record upstream makes the parser lose a few following rows. Each missing
    record is located by its id at a record start and parsed on its own with the csv module. Written to a SEPARATE
    supplementary Parquet; the main extract is not modified.
    """
    import csv
    import io
    import re

    import pandas as pd

    out_dir = out_dir or DATA / "raw" / "x_posts"
    main = out_dir / f"stock_tweets_{ticker}.parquet"
    raw_csv = raw_csv or DATA / "Tweet.csv"
    con = duckdb.connect()
    link = (DATA / "Company_Tweet.csv").as_posix()
    missing = {str(r[0]) for r in con.execute(
        f"SELECT DISTINCT CAST(tweet_id AS VARCHAR) FROM read_csv('{link}', header=true, "
        f"columns={{'tweet_id':'BIGINT','ticker_symbol':'VARCHAR'}}) WHERE ticker_symbol='{ticker}' AND "
        f"CAST(tweet_id AS VARCHAR) NOT IN (SELECT post_id FROM read_parquet('{main.as_posix()}'))").fetchall()}
    raw = raw_csv.read_bytes()
    starts = [(m.start() + (1 if raw[m.start():m.start() + 1] == b"\n" else 0), m.group(1).decode())
              for m in re.finditer(rb"(?:^|\n)(\d{15,19}),", raw)]
    rows = []
    for k, (pos, rid) in enumerate(starts):
        if rid not in missing:
            continue
        end = starts[k + 1][0] if k + 1 < len(starts) else len(raw)
        rec = next(csv.reader(io.StringIO(raw[pos:end].decode("utf-8", "replace").rstrip("\r\n"))), None)
        if rec and len(rec) == 7 and rec[2].isdigit():
            rows.append({"post_id": rec[0], "created_at": pd.to_datetime(int(rec[2]), unit="s"), "username": rec[1],
                         "text": rec[3], "replies": int(rec[4]), "reposts": int(rec[5]), "likes": int(rec[6]),
                         "asset_symbol": ticker, "query_source": "stock_tweets_csv_recovered"})
    out = out_dir / f"stock_tweets_{ticker}_recovered.parquet"
    pd.DataFrame(rows).to_parquet(out, index=False)
    log.info("recovered %d of %d missing posts -> %s", len(rows), len(missing), out)
    return out
