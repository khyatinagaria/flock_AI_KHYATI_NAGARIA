"""Section 3: estimate washing-machine power from the household aggregate.

Run from the repo root (after src/wm_eda.py, which builds the 1-minute cache):
    python src/model.py

Split by HOUSE so the test home is never seen in training:
    train: houses 2, 5, 7, 9    validation (early stopping): house 15    test: house 17
Every feature is computed inside one house's own time series, so no information
crosses between houses. Windows look up to 60 min back and forward (offline,
Seq2Point-style context), which is fine for after-the-fact disaggregation of
smart-meter history but would need a delay in a real-time setting.

Models
    always_off   predicts 0 W (what you get by doing nothing; strong on MAE because
                 the machine is off ~98% of the time)
    profile      mean training-house washing-machine power for that weekday x hour
    lightgbm     gradient-boosted trees on aggregate-window features

Outputs
    outputs/model_metrics.md, outputs/model_predictions_test.parquet
    figures/model_actual_vs_pred.png, figures/model_failures.png, figures/model_metrics.png
"""
import sys
from pathlib import Path

import lightgbm as lgb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import OUT_DIR, FIG_DIR, LOCAL_TZ, C_RAW, C_CLEAN, C_FLAG, C_ALT
from clean_data import load_house

TRAIN, VAL, TEST = [2, 5, 7, 9], [15], [17]
ON_W = 20            # same "running" threshold as the EDA
WM_MAX_W = 3000      # clip target to a physically sensible range
SEED = 0


# ---- features ------------------------------------------------------------------
def features(m):
    """Features for every minute, using only that house's aggregate and the clock."""
    a = m["aggregate"].astype("float32")
    f = pd.DataFrame(index=m.index)
    f["agg"] = a
    for k in [1, 2, 3, 5, 10, 15, 30]:
        f[f"lag_{k}"] = a.shift(k)
        f[f"lead_{k}"] = a.shift(-k)
    f["diff_1"] = a.diff()
    f["diff_-1"] = a.shift(-1) - a
    for w in [5, 15, 30, 60, 120]:
        r = a.rolling(w, center=True, min_periods=max(1, w // 2))
        f[f"mean_{w}"] = r.mean()
        f[f"std_{w}"] = r.std()
        f[f"max_{w}"] = r.max()
        f[f"min_{w}"] = r.min()
    # power above the local baseload: highlights appliance activity
    f["above_min60"] = a - f["min_60"]
    # count of large step changes nearby: heaters and motors switch often
    big_step = (a.diff().abs() > 500).astype("float32")
    f["steps_30"] = big_step.rolling(30, center=True, min_periods=1).sum()
    f["steps_60"] = big_step.rolling(60, center=True, min_periods=1).sum()
    local = m.index.tz_convert(LOCAL_TZ)
    f["hour"] = local.hour
    f["dow"] = local.day_of_week
    return f.astype("float32")


def build(houses):
    X, y, meta = [], [], []
    for h in houses:
        m = load_house(h)
        f = features(m)
        ok = (~m["gap"]) & m["aggregate"].notna() & m["wm"].notna()
        X.append(f[ok])
        y.append(m.loc[ok, "wm"].clip(0, WM_MAX_W))
        meta.append(m.loc[ok, ["aggregate", "issues"]].assign(house=h))
    return pd.concat(X), pd.concat(y), pd.concat(meta)


# ---- baselines ---------------------------------------------------------------
def profile_baseline(train_y, train_X, X):
    prof = train_y.groupby([train_X["dow"], train_X["hour"]]).mean()
    idx = pd.MultiIndex.from_arrays([X["dow"], X["hour"]])
    return prof.reindex(idx).to_numpy()


# ---- metrics -----------------------------------------------------------------
def metrics(y, p, index):
    y, p = np.asarray(y, float), np.clip(np.asarray(p, float), 0, None)
    on_t, on_p = y > ON_W, p > ON_W
    tp = (on_t & on_p).sum()
    prec = tp / max(on_p.sum(), 1)
    rec = tp / max(on_t.sum(), 1)
    day = pd.Series(index.tz_convert(LOCAL_TZ).normalize(), index=index)
    de = pd.DataFrame({"y": y, "p": p, "d": day.values}).groupby("d").sum() / 60 / 1000
    return {
        "MAE all minutes (W)": np.mean(np.abs(y - p)),
        "MAE while running (W)": np.mean(np.abs(y[on_t] - p[on_t])) if on_t.any() else np.nan,
        "total energy error (%)": 100 * (p.sum() - y.sum()) / y.sum(),
        "daily energy MAE (kWh/day)": (de.p - de.y).abs().mean(),
        "on/off precision": prec,
        "on/off recall": rec,
        "on/off F1": 2 * prec * rec / max(prec + rec, 1e-9),
    }


# ---- plots -------------------------------------------------------------------
def style(ax):
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=8)


def trace(ax, d, title):
    t = d.index.tz_convert(LOCAL_TZ)
    ax.plot(t, d["aggregate"], color=C_RAW, lw=0.8, label="Household aggregate (input)")
    ax.plot(t, d["actual"], color=C_CLEAN, lw=1.5, label="Washing machine, actual")
    ax.plot(t, d["lightgbm"], color=C_FLAG, lw=1.3, label="Washing machine, predicted")
    ax.set_title(title, fontsize=10, loc="left")
    ax.set_ylabel("Power (W)", fontsize=8)
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b %H:%M", tz=t.tz))
    style(ax)


def plot_actual_vs_pred(res, h):
    # the 48 h window with the most actual washing-machine energy in the test house
    e = res["actual"].rolling("48h").sum()
    end = e.idxmax()
    d = res[(res.index > end - pd.Timedelta("48h")) & (res.index <= end)]
    fig, ax = plt.subplots(figsize=(12, 3.8))
    trace(ax, d, f"Test house {h} (never seen in training): actual vs predicted washing machine")
    ax.legend(fontsize=8, frameon=False, loc="upper left", ncol=3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "model_actual_vs_pred.png", dpi=120)
    plt.close(fig)


def plot_failures(res, h):
    """Worst false-positive and worst missed 3-hour window in the test house."""
    err = (res["lightgbm"] - res["actual"])
    fp = err.clip(lower=0).rolling("3h").sum()
    fn = (-err).clip(lower=0).rolling("3h").sum()
    fig, axes = plt.subplots(2, 1, figsize=(12, 6))
    for ax, s, name in [(axes[0], fp, "False alarm: predicted running, machine actually off"),
                        (axes[1], fn, "Missed / underestimated: machine running, prediction low")]:
        end = s.idxmax()
        d = res[(res.index > end - pd.Timedelta("3h")) & (res.index <= end)]
        trace(ax, d, f"House {h}, {name}")
    axes[0].legend(fontsize=8, frameon=False, loc="upper left", ncol=3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "model_failures.png", dpi=120)
    plt.close(fig)


def plot_metrics(table):
    cols = ["MAE while running (W)", "daily energy MAE (kWh/day)", "on/off F1"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3))
    for ax, c in zip(axes, cols):
        v = table[c]
        ax.barh(v.index, v.values, color=[C_RAW, C_ALT, C_CLEAN][: len(v)], height=0.55)
        for i, x in enumerate(v.values):
            ax.text(x, i, f" {x:.2f}", va="center", fontsize=8)
        ax.set_title(c, fontsize=10, loc="left")
        ax.invert_yaxis()
        ax.grid(axis="x", color="#e6e5e0", linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(labelsize=8)
    fig.suptitle(f"Test house {TEST[0]}: model vs baselines (lower is better, except F1)",
                 fontsize=11, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "model_metrics.png", dpi=120)
    plt.close(fig)


def main():
    Xtr, ytr, _ = build(TRAIN)
    Xva, yva, _ = build(VAL)
    Xte, yte, mte = build(TEST)
    print(f"train {len(Xtr):,} min | val {len(Xva):,} | test {len(Xte):,}")

    model = lgb.LGBMRegressor(n_estimators=1500, learning_rate=0.1, num_leaves=63,
                              min_child_samples=200, subsample=0.8, subsample_freq=1,
                              colsample_bytree=0.8, random_state=SEED, verbose=-1)
    model.fit(Xtr, ytr, eval_set=[(Xva, yva)], eval_metric="l1",  # early stopping on house 15
              callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)])

    preds = {
        "always_off": np.zeros(len(yte)),
        "profile": profile_baseline(ytr, Xtr, Xte),
        "lightgbm": np.clip(model.predict(Xte), 0, WM_MAX_W),
    }
    table = pd.DataFrame({k: metrics(yte, p, yte.index) for k, p in preds.items()}).T
    # validation-house numbers too, to show the result is not specific to one home
    pva = {"always_off": np.zeros(len(yva)), "profile": profile_baseline(ytr, Xtr, Xva),
           "lightgbm": np.clip(model.predict(Xva), 0, WM_MAX_W)}
    vtable = pd.DataFrame({k: metrics(yva, p, yva.index) for k, p in pva.items()}).T

    res = pd.DataFrame({"aggregate": mte["aggregate"], "actual": yte, **preds}, index=yte.index)
    res.to_parquet(OUT_DIR / "model_predictions_test.parquet")
    plot_actual_vs_pred(res, TEST[0])
    plot_failures(res, TEST[0])
    plot_metrics(table)

    imp = pd.Series(model.feature_importances_, index=Xtr.columns).sort_values(ascending=False)
    lines = ["# Model results", "",
             f"Train houses {TRAIN}, validation house {VAL}, test house {TEST}. "
             f"Best iteration: {model.best_iteration_}.", "",
             f"## Test house {TEST[0]}", "", table.round(3).to_string(), "",
             f"## Validation house {VAL[0]}", "", vtable.round(3).to_string(), "",
             "## Top 10 features (split count)", "", imp.head(10).to_string()]
    (OUT_DIR / "model_metrics.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
