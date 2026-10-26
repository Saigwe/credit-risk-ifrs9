{{ config(tags=['ecl']) }}
-- The IFRS 9 disclosure view: accounts, exposure, loss allowance and coverage by stage, and by scenario.
select
    stage,
    count(*)                                        as accounts,
    round(sum(ead), 0)                              as ead,
    round(sum(ecl), 0)                              as ecl,
    round(sum(ecl) / nullif(sum(ead), 0), 4)        as coverage,
    {% for name in var('scenarios').keys() %}
    round(sum(ecl_{{ name }}), 0)                   as ecl_{{ name }},
    {% endfor %}
    round(avg(pd_12m), 4)                           as avg_pd_12m
from {{ ref('rpt_ecl_by_client') }}
group by stage
