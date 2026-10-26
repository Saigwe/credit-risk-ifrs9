# Design doc: PD Scorecard and IFRS 9 ECL

| | |
|---|---|
| **Author** | Stanley Igwe |
| **Status** | Built on real UCI data |
| **Last updated** | 26 Oct 2026 |

## 1. Problem and users
- **Users:** credit risk (model owner), finance (impairment and disclosure), internal audit and model validation.
- **Questions:** How risky is each account? Which stage is it in, and why? What allowance do we hold, and how sensitive is it to our assumptions? Does the score treat customer groups consistently?

## 2. Requirements
| Type | Requirement |
|---|---|
| Functional | Behavioural features; a 12-month PD; IFRS 9 stage, EAD and scenario-weighted ECL per account; disclosure summary; transitions; sensitivities |
| Explainability | Points per bin for every feature; every IFRS 9 assumption a named variable |
| Correctness | ECL recomputed independently; reconciliation from account to disclosure; IFRS 9 sanity rules as tests |
| Fairness | Protected characteristics never inputs; outcomes checked by group after scoring |
| Reproducibility | CI downloads the public file and rebuilds everything |

## 3. Design
- **Features in dbt, model in Python, impairment in dbt.** Features and impairment are data products that finance and audit read as SQL; the model step is the only part that needs Python. A tag splits the dbt build around it.
- **Scorecard as champion.** A WoE logistic regression scaled to points is less accurate than gradient boosting (Gini 0.51 vs 0.55) but explainable bin by bin, which matters for adverse-action reasons and model validation.
- **One ECL formula, used twice.** The `ecl_factor` and `ifrs9_stage` macros drive both the per-account allowance and the sensitivity grid, so a sensitivity can't silently use different maths.
- **Assumptions as dbt vars**, overridable on the command line, so finance can run "what if LGD were 80%?" without touching SQL.

## 4. Options considered
| Decision | Options | Chosen | Why |
|---|---|---|---|
| PD model | Logistic on raw / WoE scorecard / gradient boosting | WoE scorecard, boosting as challenger | Explainability, with the accuracy cost measured |
| SICR test | Relative PD change since origination / absolute PD threshold | Absolute 30%, plus the 30-day backstop | No origination PD in the data; stated as a limitation |
| Lifetime PD | Vintage curves / constant hazard from 12-month PD | Constant hazard over a 3-year behavioural life | One snapshot can't support vintage curves |
| Validation split | Out-of-time / stratified random | Stratified random | One snapshot; out-of-time is on the roadmap with richer data |

## 5. Risks
- **Outcome definition:** the file's flag is next-month default, used here as a 12-month proxy.
- **Population:** a high-default period; the PD level wouldn't transfer to a normal book.
- **Fairness:** under-prediction for customers 45+ by about 3 points; recalibrate before use.
- **Assumptions:** CCF moves the allowance most (±18%); it is the first to evidence with drawdown data.
