"""12-month PD model: a points scorecard (weight-of-evidence logistic regression) as champion, gradient boosting as
challenger, validated on a 30% hold-out. Writes ml.client_pd for the IFRS 9 models and results/ for the README.

Features are behavioural only (limit, delinquency, utilisation, payments). Sex, marital status, age and education are
never model inputs; they are used afterwards to check that the scores treat groups consistently.

Validation: AUC / Gini, KS, Brier score, calibration by decile, population stability (PSI) between development and
hold-out, information value per feature. The data is one snapshot, so the split is random (stratified); an
out-of-time test isn't possible and the README says so.

Usage: python model/train.py --db warehouse/credit.duckdb --out results
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split

SEED = 42
FEATURES = ["credit_limit", "status_current", "max_months_past_due_6m", "months_delinquent_6m",
            "months_paid_in_full_6m", "utilisation_current", "utilisation_avg_6m", "utilisation_trend_6m",
            "payment_ratio_avg_5m", "payment_ratio_min_5m"]
PDO, BASE_SCORE, BASE_ODDS = 20, 600, 50  # 600 points at 50:1 good:bad odds; 20 points double the odds


def bin_edges(x: pd.Series, bins: int = 6) -> np.ndarray:
    edges = np.unique(np.nanquantile(x.dropna(), np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    return edges


def assign(x: pd.Series, edges: np.ndarray) -> pd.Series:
    b = pd.cut(x, edges, include_lowest=True, duplicates="drop").astype(str)
    return b.where(x.notna(), "missing")


def woe_table(bins: pd.Series, y: pd.Series) -> pd.DataFrame:
    t = pd.crosstab(bins, y).reindex(columns=[0, 1], fill_value=0).rename(columns={0: "good", 1: "bad"})
    g, b = (t.good + 0.5) / (t.good.sum() + 0.5), (t.bad + 0.5) / (t.bad.sum() + 0.5)
    t["woe"] = np.log(g / b)
    t["iv"] = (g - b) * t.woe
    t["bad_rate"] = t.bad / (t.good + t.bad)
    return t


def ks(y: np.ndarray, p: np.ndarray) -> float:
    fpr, tpr, _ = roc_curve(y, p)
    return float(np.max(tpr - fpr))


def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    e = np.histogram(expected, edges)[0] / len(expected) + 1e-6
    a = np.histogram(actual, edges)[0] / len(actual) + 1e-6
    return float(np.sum((a - e) * np.log(a / e)))


def calibration(y: np.ndarray, p: np.ndarray) -> pd.DataFrame:
    d = pd.DataFrame({"y": y, "p": p})
    d["decile"] = pd.qcut(d.p.rank(method="first"), 10, labels=range(1, 11))
    return d.groupby("decile", observed=True).agg(accounts=("y", "size"), predicted_pd=("p", "mean"),
                                                  observed_default_rate=("y", "mean")).reset_index()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="warehouse/credit.duckdb")
    ap.add_argument("--out", type=Path, default=Path("results"))
    args = ap.parse_args()
    con = duckdb.connect(args.db)
    df = con.execute("select * from gold.fct_client_features order by client_id").df()
    y = df.defaulted.astype(int)
    dev, val = train_test_split(df.index, test_size=0.3, stratify=y, random_state=SEED)

    # scorecard: bins and WoE learnt on development data only
    tables, woe = {}, pd.DataFrame(index=df.index)
    for f in FEATURES:
        edges = bin_edges(df.loc[dev, f])
        bins = assign(df[f], edges)
        t = woe_table(bins[dev], y[dev])
        tables[f] = (edges, t)
        woe[f] = bins.map(t.woe).fillna(0.0)
    lr = LogisticRegression(C=1.0, max_iter=2000).fit(woe.loc[dev], y[dev])
    pd_sc = lr.predict_proba(woe)[:, 1]
    factor = PDO / np.log(2)
    offset = BASE_SCORE - factor * np.log(BASE_ODDS)
    n = len(FEATURES)
    score = offset - factor * (lr.intercept_[0] + woe.values @ lr.coef_[0])
    rows = []
    for f, beta in zip(FEATURES, lr.coef_[0]):
        for b, r in tables[f][1].iterrows():
            rows.append({"feature": f, "bin": b, "accounts": int(r.good + r.bad), "bad_rate": round(r.bad_rate, 4),
                         "woe": round(r.woe, 4), "points": round(offset / n - factor * (beta * r.woe + lr.intercept_[0] / n), 1)})
    scorecard = pd.DataFrame(rows)
    iv = pd.DataFrame([{"feature": f, "iv": round(float(t.iv.sum()), 4)} for f, (_, t) in tables.items()]
                      ).sort_values("iv", ascending=False)

    # challenger
    gbm = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=300, random_state=SEED)
    gbm.fit(df.loc[dev, FEATURES], y[dev])
    pd_gbm = gbm.predict_proba(df[FEATURES])[:, 1]

    yv = y[val].to_numpy()
    def metrics(p):
        auc = roc_auc_score(yv, p[val])
        return {"auc": round(auc, 4), "gini": round(2 * auc - 1, 4), "ks": round(ks(yv, p[val]), 4),
                "brier": round(brier_score_loss(yv, p[val]), 4), "mean_pd": round(float(p[val].mean()), 4),
                "observed_default_rate": round(float(yv.mean()), 4)}
    results = {"accounts": len(df), "development": len(dev), "validation": len(val),
               "default_rate": round(float(y.mean()), 4),
               "scorecard": {**metrics(pd_sc), "psi_score_dev_vs_validation": round(psi(score[dev], score[val]), 4)},
               "gradient_boosting": {**metrics(pd_gbm), "psi_pd_dev_vs_validation": round(psi(pd_gbm[dev], pd_gbm[val]), 4)}}

    # fairness check on the hold-out: groups are never model inputs
    v = df.loc[val].assign(pd=pd_sc[val], approved=pd_sc[val] < 0.30)
    v["sex"] = v.sex_code.map({1: "male", 2: "female"})
    v["age_band"] = pd.cut(v.age, [0, 29, 44, 200], labels=["under 30", "30-44", "45+"]).astype(str)
    fair = []
    for col in ("sex", "age_band"):
        for g, d in v.groupby(col):
            fair.append({"attribute": col, "group": g, "accounts": len(d), "observed_default_rate": round(d.defaulted.mean(), 4),
                         "mean_predicted_pd": round(d.pd.mean(), 4), "approval_rate_at_pd_30": round(d.approved.mean(), 4)})
    fair = pd.DataFrame(fair)
    for col in ("sex", "age_band"):
        rates = fair[fair.attribute == col].approval_rate_at_pd_30
        results[f"approval_rate_ratio_{col}"] = round(float(rates.min() / rates.max()), 4)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "model_validation.json").write_text(json.dumps(results, indent=2))
    scorecard.to_csv(args.out / "scorecard.csv", index=False)
    iv.to_csv(args.out / "information_value.csv", index=False)
    calibration(yv, pd_sc[val]).round(4).to_csv(args.out / "calibration_scorecard.csv", index=False)
    fair.to_csv(args.out / "fairness.csv", index=False)

    out = pd.DataFrame({"client_id": df.client_id, "pd_12m": pd_sc, "pd_12m_challenger": pd_gbm,
                        "score": np.round(score).astype(int), "sample": np.where(df.index.isin(val), "validation", "development")})
    con.execute("create schema if not exists ml")
    con.register("pd_df", out)
    con.execute("create or replace table ml.client_pd as select * from pd_df")
    print(json.dumps(results, indent=2))
    print(iv.to_string(index=False))
    print(fair.to_string(index=False))


if __name__ == "__main__":
    main()
