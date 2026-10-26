{{ config(tags=['ecl']) }}
-- Coverage (allowance / exposure) must rise from stage 1 to 2 to 3: riskier stages hold more provision per unit.
select s1.coverage as stage_1, s2.coverage as stage_2, s3.coverage as stage_3
from {{ ref('rpt_ecl_summary') }} s1, {{ ref('rpt_ecl_summary') }} s2, {{ ref('rpt_ecl_summary') }} s3
where s1.stage = 1 and s2.stage = 2 and s3.stage = 3
  and not (s1.coverage < s2.coverage and s2.coverage < s3.coverage)
