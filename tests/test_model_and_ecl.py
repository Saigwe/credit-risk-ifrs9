"""Checks on a finished run (CREDIT_DB): the scorecard scaling, the ECL maths recomputed independently in Python,
model stability, and that protected characteristics are never model inputs."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import duckdb
import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "model"))
import train  # noqa: E402

DB = os.environ.get("CREDIT_DB", str(ROOT / "warehouse" / "credit.duckdb"))
RESULTS = Path(os.environ.get("CREDIT_RESULTS", ROOT / "results"))
VARS = yaml.safe_load((ROOT / "dbt" / "dbt_project.yml").read_text())["vars"]


def test_protected_characteristics_are_not_model_inputs():
    assert not {"sex_code", "marriage_code", "age", "education_code"} & set(train.FEATURES)


def test_score_and_pd_follow_the_points_scale():
    """600 points at 50:1 good:bad odds, and every 20 points doubles the odds."""
    con = duckdb.connect(DB, read_only=True)
    score, pd_ = np.array(con.execute("select score, pd_12m from ml.client_pd").fetchall()).T
    odds = train.BASE_ODDS * 2 ** ((score - train.BASE_SCORE) / train.PDO)
    assert np.max(np.abs(1 / (1 + odds) - pd_)) < 0.01   # scores are rounded to whole points


def lifetime_factor(pd, years, eir):
    return sum(((1 - pd) ** (t - 1) - (1 - pd) ** t) / (1 + eir) ** t for t in range(1, years + 1))


@pytest.mark.parametrize("stage", [1, 2, 3])
def test_ecl_matches_an_independent_calculation(stage):
    con = duckdb.connect(DB, read_only=True)
    rows = con.execute("select ead, pd_12m, ecl from gold.rpt_ecl_by_client where stage = ? order by client_id limit 50",
                       [stage]).fetchall()
    assert rows
    lgd, eir, life = VARS["lgd"], VARS["eir"], VARS["behavioural_life_years"]
    for ead, pd_, ecl in rows:
        expected = 0.0
        for s in VARS["scenarios"].values():
            p = min(pd_ * s["pd_multiplier"], 0.9999)
            factor = {1: p / (1 + eir), 2: lifetime_factor(p, life, eir), 3: 1.0}[stage]
            expected += s["weight"] * float(ead) * lgd * factor
        assert ecl == pytest.approx(expected, abs=0.02)


def test_scenario_weights_sum_to_one():
    assert sum(s["weight"] for s in VARS["scenarios"].values()) == pytest.approx(1.0)


def test_model_is_stable_and_discriminates_on_the_hold_out():
    r = json.loads((RESULTS / "model_validation.json").read_text())
    assert r["scorecard"]["gini"] > 0.4 and r["scorecard"]["psi_score_dev_vs_validation"] < 0.1
    assert abs(r["scorecard"]["mean_pd"] - r["scorecard"]["observed_default_rate"]) < 0.02
