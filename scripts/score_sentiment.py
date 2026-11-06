"""Stage: processed posts -> post-level sentiment (FinBERT). Resumable via chunk checkpoints.

Only unique `dedup_key` texts are scored; scores are mapped back to every post sharing the key.
Usage: python scripts/score_sentiment.py [--limit N] [--validate]
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from config.settings import ROOT, load_settings  # noqa: E402
from sentiment.finbert_analyzer import DEFAULT_MODEL, OUT_COLS, FinBertAnalyzer, model_tag  # noqa: E402
from sentiment.sentiment_validation import evaluate  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("score_sentiment")
CHUNK = 50_000


def run_validation(an: FinBertAnalyzer) -> None:
    v = pd.read_csv(ROOT / "data" / "validation" / "sentiment_validation.csv")
    res = evaluate(v, an.score(v["text"].tolist()))
    print(f"\nVALIDATION accuracy={res['accuracy']:.3f}  n={len(v)}")
    print(pd.DataFrame(res["report"]).T.round(3).to_string())
    print(res["confusion"].to_string())
    print(res["calibration"].round(3).to_string())
    print(res["by_category"].round(3).to_string())
    out = ROOT / "artifacts" / "sentiment_validation_report.txt"
    out.parent.mkdir(exist_ok=True)
    out.write_text(f"accuracy={res['accuracy']:.4f}\n{res['confusion']}\n{res['calibration']}\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    a = load_settings().asset
    an = FinBertAnalyzer(args.model)
    if args.validate:
        run_validation(an)
        return

    posts = pd.read_parquet(ROOT / "data" / "processed" / f"posts_{a.symbol}.parquet",
                            columns=["post_id", "clean_text", "dedup_key", "created_at"])
    uniq = posts.drop_duplicates("dedup_key")[["dedup_key", "clean_text"]].reset_index(drop=True)
    if args.limit:
        uniq = uniq.head(args.limit)
    log.info("%d posts, %d unique texts to score", len(posts), len(uniq))

    ck = ROOT / "artifacts" / "sentiment_chunks" / args.model.replace("/", "_")
    ck.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    for ci, s in enumerate(range(0, len(uniq), CHUNK)):
        f = ck / f"chunk_{ci:05d}.parquet"
        if f.exists():
            continue
        part = uniq.iloc[s:s + CHUNK]
        sc = an.score(part["clean_text"].tolist())
        pd.DataFrame({"dedup_key": part["dedup_key"].to_numpy(), **{c: sc[c] for c in OUT_COLS}}).to_parquet(f, index=False)
        done = min(s + CHUNK, len(uniq))
        log.info("chunk %d done: %d/%d (%.0f texts/s)", ci, done, len(uniq), done / (time.time() - t0 + 1e-9))

    scores = pd.concat([pd.read_parquet(p) for p in sorted(ck.glob("chunk_*.parquet"))], ignore_index=True)
    out = posts[["post_id", "dedup_key"]].merge(scores, on="dedup_key", how="inner").drop(columns="dedup_key")
    out["model_name"] = args.model
    assert out["sentiment_score"].between(-1, 1).all(), "sentiment_score out of range"
    dst = ROOT / "data" / "processed" / f"sentiment_{a.symbol}{model_tag(args.model)}.parquet"
    out.to_parquet(dst, index=False)
    log.info("wrote %d post-level sentiments to %s (%.1f%% of posts)", len(out), dst, 100 * len(out) / len(posts))


if __name__ == "__main__":
    main()
