"""Refresh the AUTO facts block in docs/ai_context/CURRENT_CONTEXT.md (counts measured from the filesystem/pytest).

Only the text between the AUTO markers is rewritten. Interpretation, priorities and blockers are written by hand.
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START, END = "<!-- AUTO:FACTS:START -->", "<!-- AUTO:FACTS:END -->"


def fmt_size(n: int) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return f"{n:.0f} {u}" if u == "B" else f"{n / 1:.1f} {u}"
        n /= 1024
    return ""


def main() -> None:
    py = sys.executable
    r = subprocess.run([py, "-m", "pytest", "--co", "-q"], cwd=ROOT, capture_output=True, text=True)
    n_tests = sum("::" in ln for ln in r.stdout.splitlines())
    files = []
    for rel in ["data/raw/x_posts", "data/raw/prices", "data/raw/news", "data/processed", "data/aggregated", "data/model_ready"]:
        d = ROOT / rel
        for f in sorted(d.glob("*")) if d.exists() else []:
            if f.is_file():
                files.append(f"- `{f.relative_to(ROOT).as_posix()}` ({fmt_size(f.stat().st_size)})")
    chunks = list((ROOT / "artifacts" / "sentiment_chunks").glob("*/chunk_*.parquet"))
    runs = sorted((ROOT / "artifacts" / "runs").glob("*")) if (ROOT / "artifacts" / "runs").exists() else []
    block = "\n".join([
        START, f"_Measured {datetime.now().strftime('%Y-%m-%d %H:%M')} by `scripts/update_project_context.py`._", "",
        f"- Collected tests: {n_tests}", f"- Sentiment scoring chunks on disk: {len(chunks)} (50,000 unique texts each; 996,456 total expected)",
        f"- Experiment runs on disk: {len(runs)}" + (f" (latest `{runs[-1].name}`)" if runs else ""),
        "- Derived data files present:", *(files or ["  - none"]), END])
    p = ROOT / "docs" / "ai_context" / "CURRENT_CONTEXT.md"
    txt = p.read_text(encoding="utf-8")
    txt = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, txt, flags=re.S) if START in txt else txt + "\n" + block + "\n"
    p.write_text(txt, encoding="utf-8")
    print("updated", p)


if __name__ == "__main__":
    main()
