{{ config(tags=['ecl']) }}
-- One row per client at the reporting date: IFRS 9 stage, exposure at default, PD under each macro scenario, and the
-- probability-weighted expected credit loss. Assumptions (LGD, CCF, EIR, life, SICR threshold, scenarios) are dbt vars.
with base as (
    select
        f.client_id,
        f.balance,
        f.undrawn,
        greatest(f.status_current, 0)                                          as months_past_due,
        p.pd_12m,
        p.score,
        greatest(f.balance, 0) + {{ var('ccf') }} * f.undrawn                  as ead
    from {{ ref('fct_client_features') }} f
    join {{ source('ml', 'client_pd') }} p using (client_id)
),

staged as (
    select *, {{ ifrs9_stage('months_past_due', 'pd_12m') }} as stage from base
)

select
    client_id,
    stage,
    score,
    round(balance, 2)                                                           as balance,
    round(ead, 2)                                                               as ead,
    pd_12m,
    {% for name, s in var('scenarios').items() %}
    least(pd_12m * {{ s.pd_multiplier }}, 0.9999)                              as pd_12m_{{ name }},
    round(ead * {{ var('lgd') }} * {{ ecl_factor('least(pd_12m * ' ~ s.pd_multiplier ~ ', 0.9999)', 'stage') }}, 2) as ecl_{{ name }},
    {% endfor %}
    round(
        {% for name, s in var('scenarios').items() %}
        {{ s.weight }} * ead * {{ var('lgd') }} * {{ ecl_factor('least(pd_12m * ' ~ s.pd_multiplier ~ ', 0.9999)', 'stage') }}{{ " +" if not loop.last }}
        {% endfor %}, 2)                                                        as ecl
from staged
