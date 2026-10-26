# 3-minute walkthrough: Credit Risk PD Scorecard and IFRS 9 ECL

A timed script for a Loom recording of about 3 minutes (screen plus camera bubble, 1080p). Say it in your own words; the lines are a guide, not a teleprompter.

**Open these tabs before you press record:** README, the architecture diagram, `results/scorecard.csv`, the IFRS 9 table in the README, `dbt/models/marts/rpt_ecl_by_client.sql`, `tests/` (the independent ECL recalculation), `docs/design_doc.md`.

| Time | On screen | What to say |
|---|---|---|
| 0:00–0:20 | Portfolio card, then the README title | Under IFRS 9 a lender sets aside a loss allowance: 12 months of expected loss for performing accounts, lifetime for those whose risk has risen, full loss for defaults. It must be forward-looking and explainable to auditors. This goes from a raw account file to that number. |
| 0:20–0:40 | README intro and the Data section | At a Big Four firm I built risk-indicator datasets for tier-1 banks with audit-ready validation. This uses the real UCI file: 30,000 credit card accounts with six months of statements. The outcome is next month's default, and I say wherever I use it as a 12-month flag. |
| 0:40–1:05 | Architecture, then `scorecard.csv` | dbt turns the statements into behavioural features. Sex, age, marital status and education are never inputs, and a test enforces it. The scorecard is weight of evidence and logistic regression, scaled to points, so every bin can be explained. |
| 1:05–1:30 | Numbers: PD model table | On a 9,000-account hold-out: Gini 0.51, KS 0.40, mean PD 22.0% against 22.1% observed, PSI 0.001. A gradient-boosting challenger gets 0.55. I keep the scorecard as champion and state the 0.04 Gini as the price of explainability. |
| 1:30–1:50 | Numbers: fairness table | The fairness check uses characteristics the model never sees. Approval ratios are 0.93 by age and 0.97 by sex. The finding to act on: the model under-predicts risk for customers 45 and over by about 3 points. |
| 1:50–2:20 | IFRS 9 rules table, then the ECL by stage | Stage 3 at 90 days past due, stage 2 at 30 days or a PD of 30%, three weighted scenarios. Allowance NT$503.6M on NT$3.29B of exposure. Coverage rises from 7.8% to 46% to 75%, and stage 2 holds 18% of exposure but over half the allowance. |
| 2:20–2:40 | Sensitivity table, then the test that recomputes ECL | Every assumption is a dbt variable with its value shown. The credit conversion factor moves the allowance ±18%, more than LGD's ±13%, so it's the first to evidence. The tests recompute ECL independently in Python for 50 accounts in each stage. |
| 2:40–3:00 | `docs/design_doc.md` options table, then the README top | The decision I'd defend: an explainable scorecard over the more accurate model, with the cost measured. For a lender, that's an allowance every account can be traced to. Links are under the video. |

## Recording checklist
- Close email, chat and notifications. Zoom the browser to 125% so code is readable.
- Run `make all` once before recording so the results files are fresh.
- Keep to one take per section; Loom lets you trim. Aim for 2:45 to 3:10.
- Show real numbers on screen as you say them; never estimate on camera.
- Say "NT dollars" for amounts: the data is from Taiwan, 2005.

## After recording
1. Copy the Loom share link.
2. In `README.md`, replace the roadmap line with `- [x] [3-minute Loom walkthrough](<your Loom link>)` and add the link under the title.
3. Add the link to this project's card on saigwe.github.io.
