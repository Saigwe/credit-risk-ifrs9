"""README charts from the committed hold-out results (results/*.csv). Usage: python charts/make_charts.py"""
import csv
import sys
from pathlib import Path

import style as st

ROOT = Path(__file__).resolve().parents[1]
RES = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results"
OUT = ROOT / "docs" / "charts"


def read(name):
    with open(RES / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


cal = read("calibration_scorecard.csv")
d = [int(r["decile"]) for r in cal]
f, ax = st.fig()
ax.plot(d, [float(r["observed_default_rate"]) for r in cal], color=st.S[0], marker="o", ms=5, label="Observed default rate")
ax.plot(d, [float(r["predicted_pd"]) for r in cal], color=st.S[1], marker="o", ms=5, ls="--", label="Predicted PD")
ax.set_xticks(d, [f"D{i}" for i in d])
ax.set_xlabel("Score decile, lowest risk to highest (900 hold-out accounts each)")
st.fmt(ax, "y", "pct")
ax.set_ylim(0, None)
st.head(ax, "Predicted PD tracks the observed default rate in every decile", "Scorecard on the 9,000-account hold-out", legend=True)
st.save(f, OUT / "calibration.png")

iv = sorted(read("information_value.csv"), key=lambda r: -float(r["iv"]))
f, ax = st.fig(8, 3.8)
vals = [float(r["iv"]) for r in iv]
st.hbar(ax, [r["feature"].replace("_", " ") for r in iv], vals,
        colors=[st.S[0] if v >= 0.1 else st.MUTED for v in vals], label_fmt=lambda v: f"{v:.2f}")
st.head(ax, "Repayment behaviour carries the signal", "Information value per scorecard feature; grey bars are below 0.1 (weak)", flush=True)
st.save(f, OUT / "information_value.png")

fa = read("fairness.csv")
order = [("sex", "female", "Female"), ("sex", "male", "Male"), ("age_band", "under 30", "Under 30"),
         ("age_band", "30-44", "30 to 44"), ("age_band", "45+", "45+")]
rows = [next(r for r in fa if r["attribute"] == a and r["group"] == g) for a, g, _ in order]
f, ax = st.fig(8, 3.4)
x = range(len(rows))
w = 0.38
b1 = ax.bar([i - w / 2 for i in x], [float(r["observed_default_rate"]) for r in rows], w * 0.92, color=st.S[0], label="Observed default rate")
b2 = ax.bar([i + w / 2 for i in x], [float(r["mean_predicted_pd"]) for r in rows], w * 0.92, color=st.S[1], label="Mean predicted PD")
st.vbar_labels(ax, b1, lambda v: f"{v:.0%}")
st.vbar_labels(ax, b2, lambda v: f"{v:.0%}")
ax.set_xticks(list(x), [lab for _, _, lab in order])
st.fmt(ax, "y", "pct")
st.head(ax, "Predicted risk matches observed risk across sex and age", "Hold-out accounts by group", legend=True)
st.save(f, OUT / "fairness.png")
print(f"wrote charts to {OUT}")
