"""Section 2: washing-machine exploratory analysis on the CLEAN REFIT data.

Run from the repo root:
    python src/wm_eda.py

Cycle rule (plain language): the machine is "running" in any minute where its
average power is above 20 W. Washing machines pause for several minutes between
wash, rinse and spin, so running stretches separated by 10 minutes or less of
low power are joined into one cycle. A cycle is kept if it lasts at least
10 minutes, reaches at least 200 W at some point (the heater or spin motor), and
uses at least 0.05 kWh. Cycles touching a data gap are dropped as incomplete.

Outputs
    outputs/wm_summary.md     availability, data quality and cycle statistics per house
    outputs/wm_cycles.csv     one row per detected cycle
    figures/wm_*.png          day trace, example cycles, cross-house comparison, usage patterns
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import OUT_DIR, FIG_DIR, LOCAL_TZ, WM_CHANNELS, C_RAW, C_CLEAN, C_FLAG
from clean_data import load_house

ON_W = 20          # minute is "running" above this
BRIDGE_MIN = 10    # join running stretches separated by <= this many low minutes
MIN_DUR_MIN = 10   # shortest cycle kept
MIN_PEAK_W = 200   # cycle must reach this at least once
MIN_KWH = 0.05     # and use at least this much energy
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def runs(mask):
    """(start_pos, end_pos_exclusive) of True runs in a boolean array."""
    m = np.r_[False, np.asarray(mask, bool), False]
    d = np.diff(m.astype(int))
    return np.flatnonzero(d == 1), np.flatnonzero(d == -1)


def detect_cycles(m):
    on = (m["wm"] > ON_W).to_numpy().copy()
    # bridge short low stretches that sit between two running stretches
    s, e = runs(~on)
    for a, b in zip(s, e):
        if 0 < a and b < len(on) and b - a <= BRIDGE_MIN:
            on[a:b] = True
    s, e = runs(on)
    gap = m["gap"].to_numpy()
    wm = m["wm"].to_numpy()
    rows = []
    for a, b in zip(s, e):
        lo, hi = max(a - 1, 0), min(b + 1, len(m))
        if gap[lo:hi].any():
            continue
        seg = wm[a:b]
        rows.append({"start_utc": m.index[a], "end_utc": m.index[b - 1] + pd.Timedelta("1min"),
                     "duration_min": b - a, "peak_w": float(np.nanmax(seg)),
                     "energy_kwh": float(np.nansum(seg) / 60 / 1000)})
    c = pd.DataFrame(rows)
    if c.empty:
        return c
    keep = (c.duration_min >= MIN_DUR_MIN) & (c.peak_w >= MIN_PEAK_W) & (c.energy_kwh >= MIN_KWH)
    c = c[keep].reset_index(drop=True)
    c["start_local"] = c["start_utc"].dt.tz_convert(LOCAL_TZ)
    return c


def summarise(h, m, c):
    valid = ~m["gap"]
    wm_v = m.loc[valid, "wm"]
    days = (m.index.max() - m.index.min()).total_seconds() / 86400
    valid_weeks = valid.sum() / (7 * 1440)
    gap_runs = runs(m["gap"].to_numpy())
    return {
        "house": h, "channel": WM_CHANNELS[h],
        "first day": f"{m.index.min():%Y-%m-%d}", "last day": f"{m.index.max():%Y-%m-%d}",
        "span (days)": round(days),
        "missing minutes (%)": round(100 * m["gap"].mean(), 1),
        "gaps > 5 min": len(gap_runs[0]),
        "longest gap (days)": round(max((b - a for a, b in zip(*gap_runs)), default=0) / 1440, 1),
        "minutes with REFIT issue flag (%)": round(100 * (m.loc[valid, "issues"] > 0).mean(), 1),
        "WM exactly 0 W (%)": round(100 * (wm_v == 0).mean(), 1),
        f"WM off, <= {ON_W} W (%)": round(100 * (wm_v <= ON_W).mean(), 1),
        "cycles detected": len(c),
        "cycles per week": round(len(c) / valid_weeks, 1),
        "median duration (min)": c.duration_min.median(),
        "median peak (W)": round(c.peak_w.median()),
        "median energy (kWh)": round(c.energy_kwh.median(), 2),
        "WM share of household energy (%)": round(float(100 * wm_v.sum() / m.loc[valid, "aggregate"].sum()), 1),
    }


# ---- plots -------------------------------------------------------------------
def style(ax, grid="y"):
    ax.grid(axis=grid, color="#e6e5e0", linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=8)


def median_cycle(c):
    return c.iloc[(c.energy_kwh - c.energy_kwh.median()).abs().argmin()]


def plot_day(h, m, c):
    """(i) one representative day: aggregate and washing machine on one axis."""
    local = m.tz_convert(LOCAL_TZ)
    gap_days = set(local.index[local["gap"]].normalize())
    c = c[~c.start_local.dt.normalize().isin(gap_days)]
    per_day = c.groupby(c.start_local.dt.normalize()).size()
    one = c[c.start_local.dt.normalize().isin(per_day[per_day == 1].index)]
    cyc = median_cycle(one if len(one) else c)
    day = cyc.start_local.normalize()
    d = local[(local.index >= day) & (local.index < day + pd.Timedelta("1D"))]
    fig, ax = plt.subplots(figsize=(12, 3.6))
    ax.plot(d.index, d["aggregate"], color=C_RAW, lw=1, label="Household aggregate")
    ax.plot(d.index, d["wm"], color=C_CLEAN, lw=1.4, label="Washing machine")
    ax.axvspan(cyc.start_local, cyc.end_utc.tz_convert(LOCAL_TZ), color=C_FLAG, alpha=0.15,
               label=f"Detected cycle ({cyc.duration_min} min, {cyc.energy_kwh:.2f} kWh)")
    ax.set_ylabel("Power (W)", fontsize=9)
    ax.set_title(f"House {h}, {day:%A %d %b %Y}: aggregate and washing machine (1-minute)",
                 fontsize=10, loc="left")
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M", tz=d.index.tz))
    style(ax)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "wm_day_trace.png", dpi=120)
    plt.close(fig)


def plot_cycles(data, cycles):
    """(ii) the median-energy cycle of each house, with the threshold and window."""
    houses = list(data)
    ncol = 3
    nrow = int(np.ceil(len(houses) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(12, 3 * nrow), squeeze=False)
    for ax, h in zip(axes.flat, houses):
        c = cycles[h]
        if c.empty:
            ax.set_visible(False)
            continue
        cyc = median_cycle(c)
        pad = pd.Timedelta("20min")
        m = data[h]
        w = m[(m.index >= cyc.start_utc - pad) & (m.index < cyc.end_utc + pad)]
        t = (w.index - cyc.start_utc).total_seconds() / 60
        ax.plot(t, w["wm"], color=C_CLEAN, lw=1.3)
        ax.axvspan(0, cyc.duration_min, color=C_FLAG, alpha=0.15)
        ax.axhline(ON_W, color=C_FLAG, lw=0.8, ls="--")
        ax.set_title(f"House {h}: {cyc.duration_min} min, peak {cyc.peak_w:.0f} W, "
                     f"{cyc.energy_kwh:.2f} kWh", fontsize=9, loc="left")
        ax.set_xlabel("minutes from cycle start", fontsize=8)
        style(ax)
    for ax in axes.flat[len(houses):]:
        ax.set_visible(False)
    axes[0, 0].set_ylabel("Washing machine (W)", fontsize=8)
    fig.suptitle(f"A typical detected cycle per house (shaded = detected; dashed = {ON_W} W threshold)",
                 fontsize=11, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "wm_cycle_examples.png", dpi=120)
    plt.close(fig)


def plot_cross_house(cycles):
    """(iii) cycle characteristics compared across houses."""
    houses = [h for h in cycles if not cycles[h].empty]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    for ax, (col, label) in zip(axes, [("energy_kwh", "Energy per cycle (kWh)"),
                                       ("duration_min", "Duration (min)"),
                                       ("peak_w", "Peak power (W)")]):
        ax.boxplot([cycles[h][col] for h in houses], tick_labels=[f"H{h}" for h in houses],
                   showfliers=False, widths=0.55, patch_artist=True,
                   boxprops=dict(facecolor="#cde2fb", edgecolor=C_CLEAN),
                   medianprops=dict(color="#0d366b", lw=2),
                   whiskerprops=dict(color=C_CLEAN), capprops=dict(color=C_CLEAN))
        ax.set_title(label, fontsize=10, loc="left")
        style(ax)
    fig.suptitle("Washing-machine cycles compared across houses (box = middle 50%, line = median)",
                 fontsize=11, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "wm_cross_house.png", dpi=120)
    plt.close(fig)


def plot_patterns(cycles):
    """When cycles start: share of each house's cycles by hour and by weekday."""
    houses = [h for h in cycles if not cycles[h].empty]
    hour = pd.DataFrame({h: cycles[h].start_local.dt.hour.value_counts(normalize=True)
                         .reindex(range(24), fill_value=0) for h in houses}).T * 100
    dow = pd.DataFrame({h: cycles[h].start_local.dt.day_of_week.value_counts(normalize=True)
                        .reindex(range(7), fill_value=0) for h in houses}).T * 100
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.4), gridspec_kw={"width_ratios": [24, 9]})
    for ax, tab, xl in [(axes[0], hour, list(range(24))), (axes[1], dow, DOW)]:
        im = ax.imshow(tab.values, cmap="Blues", aspect="auto", vmin=0)
        ax.set_yticks(range(len(houses)), [f"House {h}" for h in houses], fontsize=8)
        ax.set_xticks(range(len(xl)), xl, fontsize=8)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02).ax.tick_params(labelsize=7)
    for (i, j), v in np.ndenumerate(dow.values):
        axes[1].text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7,
                     color="white" if v > dow.values.max() * 0.6 else "#0b0b0b")
    axes[0].set_title("Cycle starts by hour of day (% of house's cycles, UK local time)",
                      fontsize=10, loc="left")
    axes[1].set_title("By day of week (%)", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "wm_usage_patterns.png", dpi=120)
    plt.close(fig)
    return hour, dow


def main():
    data, cycles, rows = {}, {}, []
    for h in WM_CHANNELS:
        m = load_house(h)
        c = detect_cycles(m)
        data[h], cycles[h] = m, c
        rows.append(summarise(h, m, c))
        print(f"house {h}: {len(c)} cycles")

    summary = pd.DataFrame(rows)
    allc = pd.concat([c.assign(house=h) for h, c in cycles.items()], ignore_index=True)
    allc.to_csv(OUT_DIR / "wm_cycles.csv", index=False)

    plot_day(list(WM_CHANNELS)[0], data[list(WM_CHANNELS)[0]], cycles[list(WM_CHANNELS)[0]])
    plot_cycles(data, cycles)
    plot_cross_house(cycles)
    hour, dow = plot_patterns(cycles)

    t = summary.set_index("house").T
    lines = ["# Washing-machine EDA summary (CLEAN REFIT, 1-minute)", "",
             f"Cycle rule: running when > {ON_W} W; pauses <= {BRIDGE_MIN} min joined; "
             f"kept if >= {MIN_DUR_MIN} min, peak >= {MIN_PEAK_W} W, >= {MIN_KWH} kWh; "
             "cycles touching a data gap dropped.", "",
             "| | " + " | ".join(f"House {h}" for h in t.columns) + " |",
             "|---" * (len(t.columns) + 1) + "|"]
    lines += [f"| {k} | " + " | ".join(str(v) for v in r) + " |" for k, r in t.iterrows()]
    peak_hours = hour.idxmax(axis=1)
    lines += ["", "Most common start hour per house: " +
              ", ".join(f"H{h}: {v:02d}:00" for h, v in peak_hours.items()),
              "Share of cycles at weekends (%): " +
              ", ".join(f"H{h}: {dow.loc[h, [5, 6]].sum():.0f}" for h in dow.index)]
    (OUT_DIR / "wm_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
