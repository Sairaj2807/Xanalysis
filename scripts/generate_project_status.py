"""Refresh the AUTO block in docs/PROJECT_STATUS.md with task-status counts parsed from MASTER_TASK_REGISTER.md.

Only the text between the AUTO markers is rewritten; all other content is left untouched.
No completion percentage is produced: counts are shown per status and workstream, unweighted.
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_documentation import DOCS, STATUSES, parse_register  # noqa: E402

START, END = "<!-- AUTO:STATUS_COUNTS:START -->", "<!-- AUTO:STATUS_COUNTS:END -->"
ORDER = ["VERIFIED", "TESTED", "IMPLEMENTED", "IN_PROGRESS", "BLOCKED", "NOT_STARTED", "DEPRECATED"]


def main() -> None:
    tasks = parse_register()
    by_ws: dict[str, Counter] = defaultdict(Counter)
    for tid, t in tasks.items():
        by_ws[tid.split("-")[0]][t["status"]] += 1
    lines = [START, "", "Task counts by workstream (auto-generated from the task register; unweighted, not a completion %):", "",
             "| Workstream | " + " | ".join(ORDER) + " | Total |", "|---|" + "---:|" * (len(ORDER) + 1)]
    tot = Counter()
    for ws in sorted(by_ws):
        c = by_ws[ws]
        tot.update(c)
        lines.append(f"| {ws} | " + " | ".join(str(c.get(s, 0)) for s in ORDER) + f" | {sum(c.values())} |")
    lines.append("| **All** | " + " | ".join(str(tot.get(s, 0)) for s in ORDER) + f" | {sum(tot.values())} |")
    lines += ["", END]
    p = DOCS / "PROJECT_STATUS.md"
    txt = p.read_text(encoding="utf-8")
    block = "\n".join(lines)
    if START in txt and END in txt:
        txt = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, txt, flags=re.S)
    else:
        txt += "\n" + block + "\n"
    p.write_text(txt, encoding="utf-8")
    assert set(tot) <= STATUSES
    print("updated", p, dict(tot))


if __name__ == "__main__":
    main()
