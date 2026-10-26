{{ config(tags=['ecl']) }}
-- Stage movement from August to September 2005 on the days-past-due rules alone (the backstops), since a PD exists
-- only at the reporting date. Rows: August stage; columns: September stage.
with s as (
    select
        client_id,
        case when greatest(status_aug, 0) >= 3 then 3 when greatest(status_aug, 0) >= 1 then 2 else 1 end as stage_aug,
        case when greatest(status_sep, 0) >= 3 then 3 when greatest(status_sep, 0) >= 1 then 2 else 1 end as stage_sep
    from {{ ref('stg_uci__clients') }}
)

select
    stage_aug,
    count(*)                                         as accounts,
    count(*) filter (where stage_sep = 1)            as to_stage_1,
    count(*) filter (where stage_sep = 2)            as to_stage_2,
    count(*) filter (where stage_sep = 3)            as to_stage_3
from s
group by stage_aug
