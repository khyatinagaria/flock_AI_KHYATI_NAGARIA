"""Diagnostic: how do RAW House 1 Part1 and Part2 fit together?"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import RAW_DIR

p1 = pd.read_csv(RAW_DIR / "RAW_House1_Part1.csv")
p2 = pd.read_csv(RAW_DIR / "RAW_House1_Part2.csv")
for name, p in [("Part1", p1), ("Part2", p2)]:
    print(f"\n== {name}: {len(p):,} rows, Time {p.Time.iloc[0]} -> {p.Time.iloc[-1]}")
    print("Unix min/max:", pd.to_datetime(p.Unix.min(), unit="s"), pd.to_datetime(p.Unix.max(), unit="s"))
    print("NaN per column:", p.isna().sum().to_dict())
    d = p.Unix.diff()
    print("backward jumps:", p.loc[d < -60, "Time"].head(5).tolist(), "sizes(s):", d[d < -60].head(5).tolist())

print("\n== Part2 rows that have a NaN (first 5):")
print(p2[p2.isna().any(axis=1)].head(5).to_string())

lo, hi = p2.Unix.min(), p1.Unix.max()
print(f"\n== overlap window: {pd.to_datetime(lo, unit='s')} -> {pd.to_datetime(hi, unit='s')}")
if lo < hi:
    o1 = p1[p1.Unix >= lo].set_index("Unix")
    o2 = p2[p2.Unix <= hi].set_index("Unix")
    print("Part1 rows in overlap:", len(o1), " Part2 rows in overlap:", len(o2))
    common = o1.index.intersection(o2.index)
    print("shared Unix values:", len(common))
    m1 = pd.to_datetime(o1.index, unit="s").floor("1min")
    m2 = pd.to_datetime(o2.index, unit="s").floor("1min")
    a1 = o1["Aggregate"].groupby(m1).mean()
    a2 = o2["Aggregate"].groupby(m2).mean()
    j = pd.concat([a1, a2], axis=1, keys=["p1", "p2"]).dropna()
    print("minutes with both:", len(j), " mean |p1-p2| aggregate (W):", round((j.p1 - j.p2).abs().mean(), 1))
    print(j.head(5).to_string())

print("\n== around autumn clock change 2014-10-26 (Part2):")
t = pd.to_datetime(p2.Unix, unit="s")
w = p2[(t > "2014-10-26 00:50") & (t < "2014-10-26 02:10")]
print(len(w), "rows;", w.Time.iloc[[0, -1]].tolist() if len(w) else "none")
print("backward steps there:", int((w.Unix.diff() < 0).sum()))
