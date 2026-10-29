"""Section 1: inspect and clean RAW REFIT House 1, resampled to 1-minute.

Run from the repo root:
    python src/clean_house1.py

Outputs
    outputs/house1_quality_report.md   inspection findings (copied into DATA.md)
    outputs/house1_outages.csv         gaps longer than MAX_FILL_MIN, flagged not filled
    outputs/house1_1min.parquet        cleaned 1-minute data with flag columns
    figures/house1_before_after_*.png  raw vs cleaned plots
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (RAW_DIR, OUT_DIR, FIG_DIR, LOCAL_TZ, HOUSE1_APPLIANCES,
                    C_RAW, C_CLEAN, C_FLAG)

# ---- Cleaning rules (all stated in DATA.md) --------------------------------
MAX_AGG_W = 20_000       # whole-house limit: above a typical UK 80-100 A supply
MAX_APPLIANCE_W = 4_000  # plug monitors on 13 A sockets cannot exceed ~3.1 kW
MAX_FILL_MIN = 5         # fill missing runs of <= 5 min by linear interpolation
POWER_COLS = ["Aggregate"] + list(HOUSE1_APPLIANCES)


def load_raw(files):
    """Read Part1 + Part2 and concatenate them in file order (column `part` = 1, 2)."""
    parts = []
    for i, f in enumerate(files, start=1):
        print(f"reading {f.name} ...")
        p = pd.read_csv(f, dtype={c: "float32" for c in POWER_COLS})
        p["part"] = np.int8(i)
        parts.append(p)
    df = pd.concat(parts, ignore_index=True)
    print(f"{len(df):,} raw rows")
    return df


def inspect(df):
    """Return a dict of raw-data quality findings (before any change)."""
    r = {}
    t_str = pd.to_datetime(df["Time"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    t_unix = pd.to_datetime(df["Unix"], unit="s")
    r["rows"] = len(df)
    r["unparseable Time"] = int(t_str.isna().sum())
    r["Time vs Unix differ by > 2 s"] = int(((t_str - t_unix).abs() > pd.Timedelta("2s")).sum())
    r["first timestamp"] = str(t_unix.min())
    r["last timestamp"] = str(t_unix.max())

    d = df["Unix"].diff()
    r["backward jumps in file order"] = int((d < 0).sum())
    r["rows earlier than a previous row"] = int((df["Unix"] < df["Unix"].cummax().shift()).sum())
    back = df.loc[d < -1800, "Time"].tolist()
    r["large backward jumps at (local time)"] = ", ".join(back) or "none"
    fwd = df.loc[(d > 3500) & (d < 3700), "Time"].tolist()
    r["~1 h forward jumps at (local time)"] = ", ".join(fwd) or "none"

    cols = ["Time", "Unix"] + POWER_COLS
    r["exact duplicate rows"] = int(df.duplicated(cols).sum())
    r["duplicate Unix with different values"] = int(
        (df["Unix"].duplicated(keep=False) & ~df.duplicated(cols, keep=False)).sum())
    for k, g in df.groupby("part"):
        u = pd.to_datetime(g["Unix"], unit="s")
        r[f"part {k} span (local)"] = f"{u.min()} -> {u.max()}, {len(g):,} rows"
        r[f"part {k} NaN power values"] = int(g[POWER_COLS].isna().sum().sum())
    if df["part"].nunique() > 1:
        end1 = df.loc[df["part"] == 1, "Unix"].max()
        r["part 2 rows overlapping part 1"] = int(((df["part"] == 2) & (df["Unix"] <= end1)).sum())

    q = d[d > 0].quantile([0.5, 0.9, 0.99])
    r["sampling interval median / p90 / p99 (s)"] = f"{q[0.5]:.0f} / {q[0.9]:.0f} / {q[0.99]:.0f}"
    r["intervals > 2 min"] = int((d > 120).sum())
    r["intervals > 1 h"] = int((d > 3600).sum())
    r["longest interval (days)"] = round(d.max() / 86400, 1)

    r["negative power values"] = int((df[POWER_COLS] < 0).sum().sum())
    r[f"Aggregate > {MAX_AGG_W} W"] = int((df["Aggregate"] > MAX_AGG_W).sum())
    r[f"appliance values > {MAX_APPLIANCE_W} W"] = int((df[list(HOUSE1_APPLIANCES)] > MAX_APPLIANCE_W).sum().sum())
    r["max value per channel"] = ", ".join(f"{c}={df[c].max():.0f}" for c in POWER_COLS)
    return r


def to_utc(df):
    """Convert wall-clock Unix values to a true UTC index.

    The logger stored UK local time. In the autumn the 01:00-02:00 hour appears
    twice (a backward jump of ~1 h in file order); rows of that hour BEFORE the
    jump are BST, rows after are GMT. In spring the 01:00-02:00 hour is simply absent.
    If a repeated hour has no backward jump (rows already interleaved), its rows
    cannot be assigned to BST or GMT and are returned as NaT (dropped later).
    """
    wall = pd.to_datetime(df["Unix"], unit="s")
    ambiguous = wall.dt.tz_localize(LOCAL_TZ, ambiguous="NaT", nonexistent="shift_forward").isna()
    jumps = np.flatnonzero(df["Unix"].diff().to_numpy() < -1800)
    is_dst = np.zeros(len(df), dtype=bool)
    resolved = np.zeros(len(df), dtype=bool)
    for j in jumps:
        day = (wall.dt.normalize() == wall.iloc[j].normalize()).to_numpy()
        is_dst |= day & (np.arange(len(df)) < j)
        resolved |= day
    local = wall.dt.tz_localize(LOCAL_TZ, ambiguous=is_dst, nonexistent="shift_forward")
    utc = local.dt.tz_convert("UTC")
    return utc.where(~(ambiguous.to_numpy() & ~resolved))


def short_gap_mask(s, max_len):
    """True for NaN positions that belong to a NaN run of length <= max_len."""
    isna = s.isna()
    run_id = (isna != isna.shift()).cumsum()
    run_len = isna.groupby(run_id).transform("size")
    return isna & (run_len <= max_len)


def clean(df):
    log = {}
    # 0. overlapping parts: Part2 starts ~3 months before Part1 ends. Keep Part1
    #    for the overlap (complete rows, no NaN) and Part2 only after Part1's end.
    end_prev = df.groupby("part")["Unix"].max().cummax().shift().fillna(-np.inf)
    keep = df["Unix"] > df["part"].map(end_prev)
    log["overlapping Part2 rows dropped"] = int((~keep).sum())
    df = df[keep].copy()
    n0 = len(df)

    df["ts"] = to_utc(df)
    log["rows in unresolvable repeated DST hour dropped"] = int(df["ts"].isna().sum())
    df = df.dropna(subset=["ts"])
    n0b = len(df)

    # 1. sort by true time (stable, so file order breaks ties)
    df = df.sort_values("ts", kind="stable")
    # 2. duplicates: drop exact copies; then collapse rows sharing a timestamp,
    #    keeping the last non-missing value per channel (Part2 writes one row per
    #    sensor report with the other channels blank, so rows in the same second
    #    complement each other)
    df = df.drop_duplicates(["ts"] + POWER_COLS)
    log["exact duplicate rows dropped"] = n0b - len(df)
    n1 = len(df)
    df = df.groupby("ts", sort=True)[POWER_COLS].last().reset_index()
    log["same-timestamp rows merged"] = n1 - len(df)

    # 3. impossible values -> NaN (counted, not clipped)
    bad_agg = df["Aggregate"] > MAX_AGG_W
    df.loc[bad_agg, "Aggregate"] = np.nan
    apps = list(HOUSE1_APPLIANCES)
    bad_app = df[apps] > MAX_APPLIANCE_W
    df[apps] = df[apps].mask(bad_app)
    log["Aggregate values set to NaN"] = int(bad_agg.sum())
    log["appliance values set to NaN"] = int(bad_app.sum().sum())

    # 4. resample to 1 minute: mean of the samples inside each minute
    df = df.set_index("ts")[POWER_COLS]
    m = df.resample("1min").mean()
    m["n_samples"] = df["Aggregate"].resample("1min").size()
    no_data = m["n_samples"] == 0
    log["minutes in span"] = len(m)
    log["minutes with no samples"] = int(no_data.sum())

    # 5. short gaps (<= MAX_FILL_MIN consecutive missing minutes) -> interpolate;
    #    longer gaps stay NaN and are flagged as outages
    m["filled"] = False
    for c in POWER_COLS:
        fill = short_gap_mask(m[c], MAX_FILL_MIN)
        m[c] = m[c].where(~fill, m[c].interpolate(limit_area="inside"))
        m["filled"] |= fill
    long_gap = no_data & ~short_gap_mask(m["Aggregate"].where(~no_data), MAX_FILL_MIN)
    m["outage"] = long_gap
    log["minutes filled by interpolation"] = int(m["filled"].sum())
    log["minutes flagged as outage"] = int(m["outage"].sum())
    log["outage share of span (%)"] = round(100 * m["outage"].mean(), 2)
    return m, log


def outage_table(m):
    run_id = (m["outage"] != m["outage"].shift()).cumsum()
    g = m[m["outage"]].groupby(run_id[m["outage"]])
    out = pd.DataFrame({"start_utc": g.apply(lambda x: x.index.min()),
                        "end_utc": g.apply(lambda x: x.index.max() + pd.Timedelta("1min"))})
    out["duration_h"] = ((out["end_utc"] - out["start_utc"]).dt.total_seconds() / 3600).round(2)
    return out.sort_values("duration_h", ascending=False).reset_index(drop=True)


# ---- plots -------------------------------------------------------------------
def style(ax):
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=8)


def plot_before_after(raw, m, start, end, cols, fname, title):
    """Raw samples (grey, wall-clock time as logged) vs cleaned 1-min (blue)."""
    wall = pd.to_datetime(raw["Unix"], unit="s")
    sel = (wall >= start) & (wall < end)
    mm = m.copy()
    mm.index = mm.index.tz_convert(LOCAL_TZ).tz_localize(None)
    mm = mm[(mm.index >= start) & (mm.index < end)]
    fig, axes = plt.subplots(len(cols), 2, figsize=(12, 2.4 * len(cols)), sharex=True)
    for i, c in enumerate(cols):
        name = HOUSE1_APPLIANCES.get(c, "Aggregate")
        a0, a1 = axes[i]
        a0.plot(wall[sel], raw.loc[sel, c], color=C_RAW, lw=0.8)
        a1.plot(mm.index, mm[c], color=C_CLEAN, lw=1.2)
        out = mm["outage"]
        if out.any():
            ymax = np.nanmax(mm[c]) if mm[c].notna().any() else 1
            a1.fill_between(mm.index, 0, ymax, where=out, color=C_FLAG, alpha=0.25,
                            step="mid", label="flagged outage")
            a1.legend(fontsize=7, frameon=False, loc="upper right")
        a0.set_ylabel(f"{name}\n(W)", fontsize=8)
        for a in (a0, a1):
            style(a)
    axes[0, 0].set_title("Before: raw samples", fontsize=10, loc="left")
    axes[0, 1].set_title("After: cleaned, 1-minute mean", fontsize=10, loc="left")
    fig.suptitle(title, fontsize=11, x=0.01, ha="left")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIG_DIR / fname, dpi=120)
    plt.close(fig)
    print(f"saved figures/{fname}")


def plot_coverage(m):
    daily = (~m["outage"]).resample("D").mean() * 100
    fig, ax = plt.subplots(figsize=(12, 2.6))
    ax.bar(daily.index, daily.values, width=1, color=C_CLEAN)
    ax.set_ylabel("% of minutes\nwith data", fontsize=8)
    ax.set_ylim(0, 105)
    ax.set_title("House 1 raw data: daily coverage after cleaning (gaps = outages)",
                 fontsize=10, loc="left")
    style(ax)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "house1_coverage.png", dpi=120)
    plt.close(fig)
    print("saved figures/house1_coverage.png")


def main(files):
    raw = load_raw(files)
    report = inspect(raw)
    m, log = clean(raw)
    outages = outage_table(m)

    m.to_parquet(OUT_DIR / "house1_1min.parquet")
    outages.to_csv(OUT_DIR / "house1_outages.csv", index=False)

    lines = ["# House 1 raw data: quality report", "",
             "Files: " + ", ".join(f.name for f in files), "",
             "## Inspection (raw, before cleaning)", "", "| check | result |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in report.items()]
    lines += ["", "## Cleaning log", "", "| step | count |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in log.items()]
    lines += ["", f"## Outages longer than {MAX_FILL_MIN} min: {len(outages)}", "",
              "Ten longest:", "", "| start (UTC) | end (UTC) | hours |", "|---|---|---|"]
    lines += [f"| {r.start_utc:%Y-%m-%d %H:%M} | {r.end_utc:%Y-%m-%d %H:%M} | {r.duration_h} |"
              for r in outages.head(10).itertuples()]
    (OUT_DIR / "house1_quality_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))

    # Plot windows chosen from the data, not by hand:
    # (a) the complete day with the most washing-machine energy
    local = m.copy()
    local.index = local.index.tz_convert(LOCAL_TZ).tz_localize(None)
    daily = local.resample("D").agg({"Appliance5": "sum", "outage": "sum"})
    day = daily[daily["outage"] == 0]["Appliance5"].idxmax()
    plot_before_after(raw, m, day, day + pd.Timedelta("1D"),
                      ["Aggregate", "Appliance5", "Appliance1"],
                      "house1_before_after_day.png",
                      f"House 1, {day:%a %d %b %Y}: aggregate, washing machine, fridge")
    # (b) a window around the first impossible spike, showing its removal
    wall = pd.to_datetime(raw["Unix"], unit="s")
    over = raw[list(HOUSE1_APPLIANCES)] > MAX_APPLIANCE_W
    first = over.any(axis=1).idxmax()
    spike, spike_col = wall[first], over.loc[first].idxmax()
    plot_before_after(raw, m, spike - pd.Timedelta("3h"), spike + pd.Timedelta("3h"),
                      ["Aggregate", spike_col, "Appliance5"],
                      "house1_before_after_spike.png",
                      f"House 1, around a sensor spike on {spike:%d %b %Y %H:%M}")
    # (c) a window around the longest outage shorter than 2 days, showing flagging
    o = outages[outages["duration_h"] < 48].iloc[0]
    s = o["start_utc"].tz_convert(LOCAL_TZ).tz_localize(None)
    e = o["end_utc"].tz_convert(LOCAL_TZ).tz_localize(None)
    pad = max(pd.Timedelta("6h"), (e - s) / 2)
    plot_before_after(raw, m, s - pad, e + pad, ["Aggregate", "Appliance5"],
                      "house1_before_after_gap.png",
                      f"House 1, around a {o['duration_h']:.1f} h outage starting {s:%d %b %Y %H:%M}")
    plot_coverage(m)


if __name__ == "__main__":
    files = [Path(p) for p in sys.argv[1:]] or (sorted(RAW_DIR.glob("RAW_House1_Part*.csv"))
                                                 or sorted(RAW_DIR.glob("RAW_House_1_Part*.csv")))
    if not files:
        sys.exit(f"No RAW_House1_Part*.csv found in {RAW_DIR}")
    main(files)
