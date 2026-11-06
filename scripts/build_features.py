"""Stage: scored posts + prices -> daily sentiment aggregates -> model-ready table (+ leakage gate)."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from config.settings import ROOT, load_settings  # noqa: E402
from features.feature_pipeline import build_model_table  # noqa: E402
from features.leakage_checks import check_feature_sets_exclude_targets, check_targets_are_future_only  # noqa: E402
from sentiment.finbert_analyzer import model_tag  # noqa: E402
from sentiment.sentiment_aggregation import aggregate_daily, attach_trading_day, author_prior_activity  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("build_features")

# Primary post filter: canonical (non-duplicate), non-spam, English. Switchable for robustness checks.
FILTERS = {
    "primary": lambda d: (~d.is_duplicate) & (~d.flag_spam) & (d.english_score >= 0.5),
    "all_posts": lambda d: pd.Series(True, index=d.index),
    "no_bots": lambda d: (~d.is_duplicate) & (~d.flag_spam) & (~d.flag_bot_like) & (d.english_score >= 0.5),
}


def build_table(px: pd.DataFrame, posts: pd.DataFrame, sent: pd.DataFrame, tz: str, horizons: list[int],
                filter_name: str = "primary", start: str | None = "2015-02-02"):
    """Pure function used by main() and tests. px indexed by trading_day (open/high/low/close);
    posts has the processed-post columns; sent has post_id, sentiment_score, confidence."""
    d = posts.merge(sent[["post_id", "sentiment_score", "confidence"]], on="post_id", how="inner")
    d = d[FILTERS[filter_name](d)].copy()
    d["author_prior_posts"] = author_prior_activity(d)
    d = attach_trading_day(d, px.index, tz)
    agg = aggregate_daily(d, px.index)
    last_post_day = d["created_at"].max().normalize()
    if getattr(last_post_day, "tzinfo", None) is not None:
        last_post_day = last_post_day.tz_convert("UTC").tz_localize(None)
    table, sets = build_model_table(px[["open", "high", "low", "close"]], agg, horizons)
    # Gate on the FULL table first: targets near the end of the slice legitimately use later prices,
    # so checking after slicing would raise false alarms (regression: tests/test_build_features.py).
    check_feature_sets_exclude_targets(sets)
    check_targets_are_future_only(table, horizons)
    table = table.loc[start:last_post_day] if start else table.loc[:last_post_day]
    return table, sets, agg, d


def main(filter_name: str = "primary", sent_model: str | None = None) -> Path:
    s = load_settings()
    a = s.asset
    px = pd.read_parquet(ROOT / "data" / "raw" / "prices" / f"{a.symbol}_{a.bar_interval}.parquet")
    px["trading_day"] = px["bar_start_utc"].dt.tz_convert("UTC").dt.tz_localize(None).dt.normalize()
    px = px.set_index("trading_day").sort_index()
    posts = pd.read_parquet(ROOT / "data" / "processed" / f"posts_{a.symbol}.parquet")
    tag = model_tag(sent_model) if sent_model else ""
    sent = pd.read_parquet(ROOT / "data" / "processed" / f"sentiment_{a.symbol}{tag}.parquet")
    log.info("posts=%d scored=%d", len(posts), len(sent))
    table, sets, agg, used = build_table(px, posts, sent, a.exchange_timezone, a.horizons, filter_name)
    log.info("filter %r kept %d scored posts; leakage gate passed; table=%s; days with posts=%.1f%%",
             filter_name, len(used), table.shape, 100 * table["sn_had_posts"].mean())

    out = ROOT / "data" / "model_ready" / f"model_table_{a.symbol}_{filter_name}{tag}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(out)
    (ROOT / "data" / "aggregated").mkdir(parents=True, exist_ok=True)
    agg.to_parquet(ROOT / "data" / "aggregated" / f"sentiment_daily_{a.symbol}_{filter_name}{tag}.parquet", index=False)
    pd.Series(sets).to_json(ROOT / "data" / "model_ready" / "feature_sets.json")
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "primary", sys.argv[2] if len(sys.argv) > 2 else None)
