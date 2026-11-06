"""Timestamp normalisation and bar alignment. Everything is stored in UTC."""
from __future__ import annotations

import pandas as pd

INTERVAL_FREQ = {"1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min", "1h": "1h", "1d": "1D"}


def to_utc(series: pd.Series, assume_tz: str | None = None) -> pd.Series:
    """Parse timestamps to tz-aware UTC.

    Naive values are localised to `assume_tz` and the caller must state it explicitly:
    silently assuming UTC for naive data is how look-ahead/offset bugs are born.
    Unparseable values become NaT (never guessed).
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        tz = getattr(series.dt, "tz", None)
        if tz is None:
            if assume_tz is None:
                raise ValueError("naive timestamps require an explicit assume_tz")
            return series.dt.tz_localize(assume_tz, ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
        return series.dt.tz_convert("UTC")

    text = series.astype("string")
    # Strings carrying an explicit offset / Z are unambiguous; the rest are naive.
    aware_mask = text.str.contains(r"(?:[+-]\d{2}(?::?\d{2})?|Z)\s*$", regex=True, na=False) & text.str.contains(
        r"\d[T ]\d", regex=True, na=False)
    out = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns, UTC]")
    if aware_mask.any():
        out[aware_mask] = pd.to_datetime(text[aware_mask], errors="coerce", utc=True, format="mixed")
    naive_mask = ~aware_mask & text.notna()
    if naive_mask.any():
        naive = pd.to_datetime(text[naive_mask], errors="coerce", format="mixed")
        if naive.notna().any() and assume_tz is None:
            raise ValueError("naive timestamps require an explicit assume_tz")
        if not naive.notna().any():
            return out
        out[naive_mask] = naive.dt.tz_localize(assume_tz, ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
    return out


def session_close_utc(trade_date: pd.Series, tz: str, close_hour: int = 16, close_minute: int = 0) -> pd.Series:
    """UTC instant of the exchange close for each local trade date (DST-safe via zoneinfo)."""
    local = pd.to_datetime(trade_date).dt.tz_localize(None) + pd.Timedelta(hours=close_hour, minutes=close_minute)
    return local.dt.tz_localize(tz, ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")


def assign_daily_bar(created_at_utc: pd.Series, tz: str, close_hour: int = 16, close_minute: int = 0) -> pd.Series:
    """Map each post to the daily bar whose information cutoff it is allowed to inform.

    A bar dated D is observable at D's close. A post made at or before the close of D
    belongs to bar D's feature window; a post made after the close belongs to the NEXT
    calendar day's window (and for weekends is resolved to the next trading day by the
    caller joining against the price calendar). Returns the *local calendar date* of the
    cutoff bucket; posts exactly at the close are inside bucket D.
    """
    local = created_at_utc.dt.tz_convert(tz)
    cutoff = local.dt.normalize() + pd.Timedelta(hours=close_hour, minutes=close_minute)
    after = local > cutoff
    bucket = local.dt.normalize().dt.tz_localize(None)
    return bucket + pd.to_timedelta(after.astype(int), unit="D")


def assign_bar(created_at_utc: pd.Series, interval: str, tz: str | None = None, close_hour: int = 16, close_minute: int = 0) -> pd.Series:
    """Map each post to the bar whose information cutoff may use it, for any supported interval.

    Intraday ('1m','5m','15m','30m','1h'): bars are labelled by their END time (UTC). A post at time t is available to
    the first bar whose end is >= t, i.e. ceil(t); a post exactly on a boundary belongs to the bar ending at that boundary
    (consistent with the daily rule 'posts at or before the close are inside the bar').
    Daily ('1d'): delegates to assign_daily_bar (requires `tz`)."""
    if interval == "1d":
        if tz is None:
            raise ValueError("daily bars need the exchange timezone")
        return assign_daily_bar(created_at_utc, tz, close_hour, close_minute)
    if interval not in INTERVAL_FREQ:
        raise ValueError(f"unsupported interval {interval}")
    t = created_at_utc.dt.tz_convert("UTC") if created_at_utc.dt.tz is not None else created_at_utc.dt.tz_localize("UTC")
    return t.dt.ceil(INTERVAL_FREQ[interval])


def aggregate_prices(df: pd.DataFrame, interval: str) -> pd.DataFrame:
    """Resample finer OHLCV bars to `interval`. df: UTC DatetimeIndex (bar START) with open/high/low/close/volume.
    open=first, high=max, low=min, close=last, volume=sum; bars labelled by their start; empty bars are dropped
    (not forward-filled)."""
    if interval not in INTERVAL_FREQ:
        raise ValueError(f"unsupported interval {interval}")
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    out = df.resample(INTERVAL_FREQ[interval], label="left", closed="left").agg({k: v for k, v in agg.items() if k in df})
    return out.dropna(subset=["close"])
