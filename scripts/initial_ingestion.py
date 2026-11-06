"""Phase 2 entry point: extract historical tweets for the configured asset + download prices."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings  # noqa: E402
from ingestion.legacy_loaders import extract_stock_tweets  # noqa: E402
from ingestion.price_ingestion import fetch_prices, save_prices  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def main() -> None:
    s = load_settings()
    a = s.asset
    h = a.history
    if h is None:
        raise SystemExit("asset_config.yaml needs a `history` block for historical ingestion")
    tweets = extract_stock_tweets(h.ticker_in_dataset, h.start, h.end)
    # pad the price window so lag features / h-step targets exist at the edges
    prices = fetch_prices(a.symbol, "2014-10-01", "2020-02-01", a.bar_interval)
    p = save_prices(prices, a.symbol, a.bar_interval)
    print("tweets:", tweets)
    print("prices:", p, len(prices), prices["bar_start_utc"].min(), prices["bar_start_utc"].max())


if __name__ == "__main__":
    main()
