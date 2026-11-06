"""DATA-004: authoritative row count of a ';'-delimited crypto CSV using the stdlib csv parser (streaming)."""
import csv
import sys
from collections import Counter

csv.field_size_limit(2 ** 30)
path = sys.argv[1]
n = bad = 0
widths = Counter()
physical = 0
with open(path, newline="", encoding="utf-8", errors="replace") as f:
    rd = csv.reader(f, delimiter=";", quotechar='"')
    header = next(rd)
    for row in rd:
        n += 1
        widths[len(row)] += 1
    physical = rd.line_num
print({"file": path, "header_cols": len(header), "csv_rows": n, "physical_lines": physical,
       "width_distribution_top": widths.most_common(4)})
