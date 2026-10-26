{{ config(tags=['ecl']) }}
-- How much the total loss allowance moves when one assumption changes and the rest stay at their base values.
-- Each row recomputes stage and ECL with the same macros as rpt_ecl_by_client (base scenario PDs).
with base as (
    select
        f.client_id, greatest(f.status_current, 0) as months_past_due, f.balance, f.undrawn, p.pd_12m
    from {{ ref('fct_client_features') }} f
    join {{ source('ml', 'client_pd') }} p using (client_id)
),

grid as (
    select * from (values
        ('base case', {{ var('lgd') }}, {{ var('ccf') }}, {{ var('sicr_pd_threshold') }}, 1.0),
        ('LGD 65%', 0.65, {{ var('ccf') }}, {{ var('sicr_pd_threshold') }}, 1.0),
        ('LGD 85%', 0.85, {{ var('ccf') }}, {{ var('sicr_pd_threshold') }}, 1.0),
        ('CCF 30%', {{ var('lgd') }}, 0.30, {{ var('sicr_pd_threshold') }}, 1.0),
        ('CCF 70%', {{ var('lgd') }}, 0.70, {{ var('sicr_pd_threshold') }}, 1.0),
        ('SICR threshold 20%', {{ var('lgd') }}, {{ var('ccf') }}, 0.20, 1.0),
        ('SICR threshold 40%', {{ var('lgd') }}, {{ var('ccf') }}, 0.40, 1.0),
        ('All PDs x1.6 (downside only)', {{ var('lgd') }}, {{ var('ccf') }}, {{ var('sicr_pd_threshold') }}, 1.6)
    ) t(case_name, lgd, ccf, sicr, pd_mult)
),

scored as (
    select
        g.case_name,
        greatest(b.balance, 0) + g.ccf * b.undrawn as ead,
        g.lgd,
        least(b.pd_12m * g.pd_mult, 0.9999) as pd,
        {{ ifrs9_stage('b.months_past_due', 'least(b.pd_12m * g.pd_mult, 0.9999)', 'g.sicr') }} as stage
    from base b cross join grid g
)

select
    case_name,
    count(*) filter (where stage = 2)                                          as stage_2_accounts,
    count(*) filter (where stage = 3)                                          as stage_3_accounts,
    round(sum(ead * lgd * {{ ecl_factor('pd', 'stage') }}), 0)                 as ecl
from scored
group by case_name
