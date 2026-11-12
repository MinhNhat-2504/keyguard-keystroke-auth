import csv
src, dst = "docs/attempts.csv", "docs/attempts_fixed.csv"
rows = list(csv.DictReader(open(src, encoding="utf-8", newline="")))
for r in rows:
    if r["event"] == "verify":
        r["confidence"] = f"{int(r['confidence'].replace('.', '')) / 10000:.4f}"
w = csv.DictWriter(open(dst, "w", encoding="utf-8", newline=""), fieldnames=rows[0].keys())
w.writeheader()
w.writerows(rows)