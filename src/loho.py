"""Leave-one-house-out evaluation of the frozen model design (src/model.py).

Run from the repo root (after src/wm_eda.py has built the 1-minute cache):
    python src/loho.py

For each of the six houses in turn: that house is the TEST house; the next house in
the list (wrapping around) is the VALIDATION house, used only for early stopping and
the detection threshold; the remaining four houses are TRAINING houses. Features,
models, threshold search and post-processing are exactly those in src/model.py, so
nothing is tuned on any test house. This gives six independent test results instead
of one, i.e. a spread of performance across homes.

Outputs
    outputs/loho_metrics.csv   one row per (test house, model)
    outputs/loho_summary.md    per-house table and median / range across houses
    figures/loho_results.png   per-house results for each model
"""
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import OUT_DIR, FIG_DIR, WM_CHANNELS, C_RAW, C_CLEAN, C_ALT
from model import build, fit_models, metrics

HOUSES = list(WM_CHANNELS)
MODELS = ["always_off", "profile", "lgbm_direct", "lgbm_2stage"]
SHOW = ["MAE while running (W)", "total energy error (%)", "daily energy MAE (kWh/day)",
        "on/off precision", "on/off recall", "on/off F1"]


def main():
    print("building features for each house ...")
    data = {h: build([h]) for h in HOUSES}

    rows = []
    for i, test in enumerate(HOUSES):
        val = HOUSES[(i + 1) % len(HOUSES)]
        train = [h for h in HOUSES if h not in (test, val)]
        t0 = time.time()
        print(f"\n=== fold {i + 1}/6: test {test}, validation {val}, train {train} ===")
        Xtr = pd.concat([data[h][0] for h in train])
        ytr = pd.concat([data[h][1] for h in train])
        Xva, yva, _ = data[val]
        Xte, yte, _ = data[test]
        predict_all, info = fit_models(Xtr, ytr, Xva, yva, verbose=0)
        for name, p in predict_all(Xte).items():
            rows.append({"test_house": test, "val_house": val, "model": name,
                         "threshold": info["thr"], **metrics(yte, p, yte.index)})
        print(f"fold done in {(time.time() - t0) / 60:.1f} min")

    res = pd.DataFrame(rows)
    res.to_csv(OUT_DIR / "loho_metrics.csv", index=False)

    lines = ["# Leave-one-house-out results", "",
             "Each row: model trained on 4 houses, validation house for early stopping and "
             "threshold, evaluated on the held-out test house.", ""]
    for col in SHOW:
        t = res.pivot(index="model", columns="test_house", values=col).loc[MODELS]
        t["median"] = t.median(axis=1)
        t["min"] = t[HOUSES].min(axis=1)
        t["max"] = t[HOUSES].max(axis=1)
        lines += [f"## {col}", "", t.round(3).to_string(), ""]
    folds = res.drop_duplicates("test_house")[["test_house", "val_house", "threshold"]]
    lines += ["## Folds", "", folds.to_string(index=False)]
    (OUT_DIR / "loho_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    plot(res)


def plot(res):
    cols = [("on/off F1", "On/off F1 (higher is better)"),
            ("MAE while running (W)", "MAE while running, W (lower is better)"),
            ("total energy error (%)", "Total energy error, % (0 is best)")]
    styles = {"always_off": (C_RAW, "o"), "lgbm_direct": (C_ALT, "s"), "lgbm_2stage": (C_CLEAN, "D")}
    x = np.arange(len(HOUSES))
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    for ax, (col, title) in zip(axes, cols):
        for k, (name, (c, mk)) in enumerate(styles.items()):
            if col == "total energy error (%)" and name == "always_off":
                continue  # always -100%, would squash the axis
            v = res[res.model == name].set_index("test_house").loc[HOUSES, col]
            ax.scatter(x + (k - 1) * 0.18, v, color=c, marker=mk, s=40, label=name, zorder=3)
            ax.axhline(v.median(), color=c, lw=1, ls="--", alpha=0.7)
        if col == "total energy error (%)":
            ax.axhline(0, color="#52514e", lw=0.8)
        ax.set_xticks(x, [f"H{h}" for h in HOUSES], fontsize=8)
        ax.set_xlabel("held-out test house", fontsize=8)
        ax.set_title(title, fontsize=10, loc="left")
        ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(labelsize=8)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=8, frameon=False, loc="lower center", ncol=3)
    fig.suptitle("Leave-one-house-out: each point is a house the model never saw (dashed = median)",
                 fontsize=11, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(FIG_DIR / "loho_results.png", dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    main()
