"""Stage: raw X posts -> processed posts (flags, no deletions)."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from config.settings import ROOT, load_settings  # noqa: E402
from preprocessing.text_cleaner import clean_posts  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("clean_posts")


def main() -> None:
    a = load_settings().asset
    src = ROOT / "data" / "raw" / "x_posts" / f"stock_tweets_{a.history.ticker_in_dataset}.parquet"
    df = pd.read_parquet(src)
    log.info("loaded %d raw posts", len(df))
    out = clean_posts(df)
    dst = ROOT / "data" / "processed" / f"posts_{a.symbol}.parquet"
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(dst, index=False)
    flags = ["is_duplicate", "flag_promo", "flag_many_cashtags", "flag_url_only", "flag_spam", "flag_bot_like"]
    log.info("flag shares:\n%s", out[flags].mean().round(4).to_string())
    log.info("english_score>=0.5: %.4f", (out["english_score"] >= 0.5).mean())
    log.info("wrote %s", dst)


if __name__ == "__main__":
    main()
