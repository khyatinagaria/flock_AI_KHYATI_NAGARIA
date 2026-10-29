"""Load the official CLEAN REFIT data for one house at 1-minute resolution.

The clean files are already DST-corrected (Unix is UTC), forward-filled between
sensor updates, and have IAM spikes > 4 kW set to 0 (see docs/CLEAN_READ_ME_081116.txt).
What is left for us: resample ~8 s readings to 1-minute means and mark gaps.

Result columns: aggregate, wm (washing-machine W), issues (share of samples in the
minute flagged by REFIT), n (samples), gap (True = no data, longer than MAX_FILL_MIN).
The index is UTC; use .tz_convert(LOCAL_TZ) for hour-of-day analysis.
Results are cached in outputs/clean_1min/ so later steps load in seconds.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import CLEAN_DIR, OUT_DIR, WM_CHANNELS

CACHE_DIR = OUT_DIR / "clean_1min"
MAX_FILL_MIN = 5  # same short-gap rule as the raw House 1 pipeline


def _short_gap_mask(isna, max_len):
    run_id = (isna != isna.shift()).cumsum()
    run_len = isna.groupby(run_id).transform("size")
    return isna & (run_len <= max_len)


def load_house(house, refresh=False):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = CACHE_DIR / f"house{house}.parquet"
    if cache.exists() and not refresh:
        return pd.read_parquet(cache)

    col = WM_CHANNELS[house]
    f = CLEAN_DIR / f"CLEAN_House{house}.csv"
    print(f"reading {f.name} (washing machine = {col}) ...")
    df = pd.read_csv(f, usecols=["Unix", "Aggregate", col, "Issues"],
                     dtype={"Aggregate": "float32", col: "float32", "Issues": "float32"})
    df = df.rename(columns={"Aggregate": "aggregate", col: "wm", "Issues": "issues"})
    df.index = pd.to_datetime(df.pop("Unix"), unit="s", utc=True)
    df = df[~df.index.duplicated(keep="last")].sort_index()

    m = df.resample("1min").mean()
    m["n"] = df["aggregate"].resample("1min").size()
    nodata = m["n"] == 0
    short = _short_gap_mask(nodata, MAX_FILL_MIN)
    for c in ["aggregate", "wm"]:
        m[c] = m[c].where(~short, m[c].interpolate(limit_area="inside"))
    m["gap"] = nodata & ~short
    m.to_parquet(cache)
    return m


if __name__ == "__main__":
    for h in WM_CHANNELS:
        m = load_house(h, refresh="--refresh" in sys.argv)
        print(f"house {h}: {m.index.min():%Y-%m-%d} -> {m.index.max():%Y-%m-%d}, "
              f"{len(m):,} minutes, {100 * m['gap'].mean():.1f}% gap")
