"""Historical OHLCV ingestion (yfinance). Raw files are written once and never overwritten."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from config.settings import ROOT

log = logging.getLogger(__name__)

YF_INTERVAL = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "60m", "1d": "1d"}


def fetch_prices(symbol: str, start: str, end: str, interval: str = "1d", auto_adjust: bool = False) -> pd.DataFrame:
    """Download OHLCV. auto_adjust=False keeps raw prices and returns 'Adj Close' separately,
    so the adjusted/unadjusted question is explicit rather than silent."""
    import yfinance as yf

    df = yf.download(symbol, start=start, end=end, interval=YF_INTERVAL[interval],
                     auto_adjust=auto_adjust, progress=False, multi_level_index=False)
    if df.empty:
        raise RuntimeError(f"no price data returned for {symbol} {start}..{end}")
    return normalise_prices(df, symbol, interval)


def normalise_prices(df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
    out = df.rename(columns=str.lower).rename(columns={"adj close": "adj_close"}).copy()
    idx = pd.DatetimeIndex(out.index)
    out.index = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    out.index.name = "bar_start_utc"
    out = out[~out.index.duplicated(keep="last")].sort_index()
    out.insert(0, "symbol", symbol)
    out["interval"] = interval
    return out.reset_index()


def save_prices(df: pd.DataFrame, symbol: str, interval: str, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or ROOT / "data" / "raw" / "prices"
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{symbol}_{interval}.parquet"
    if p.exists():
        old = pd.read_parquet(p)
        df = pd.concat([old, df]).drop_duplicates(["symbol", "bar_start_utc"], keep="last").sort_values("bar_start_utc")
    df.to_parquet(p, index=False)
    log.info("saved %d price rows to %s", len(df), p)
    return p


def update_prices(symbol: str, interval: str = "1d", end: str | None = None, overlap_days: int = 5,
                  fetch=None, out_dir: Path | None = None) -> dict:
    """Incremental price refresh (ING-002): fetch from (last stored bar - overlap) to `end`, merge idempotently.

    Re-running adds 0 rows. `fetch` is injectable for tests; defaults to `fetch_prices` (network). Overlapping bars are
    replaced by the newer download (provider revisions), never duplicated. Raw history is kept (rows are only added/replaced
    by key)."""
    from datetime import date, timedelta

    fetch = fetch or fetch_prices
    out_dir = out_dir or ROOT / "data" / "raw" / "prices"
    p = out_dir / f"{symbol}_{interval}.parquet"
    old = pd.read_parquet(p) if p.exists() else None
    start = (pd.to_datetime(old["bar_start_utc"]).max().tz_localize(None) - timedelta(days=overlap_days)).strftime("%Y-%m-%d") \
        if old is not None else "2015-01-01"
    end = end or (date.today() + timedelta(days=1)).isoformat()
    new = fetch(symbol, start, end, interval)
    before = 0 if old is None else len(old)
    save_prices(new, symbol, interval, out_dir)
    after = len(pd.read_parquet(p))
    return {"fetched": len(new), "added": after - before, "total": after, "from": start, "to": end}
