{{ config(tags=['ecl']) }}
-- IFRS 9 sanity rules on every client:
--  PDs are probabilities; the weighted ECL sits between the upside and downside ECL; ECL never exceeds LGD x EAD;
--  a stage 3 account carries exactly LGD x EAD.
select client_id, 'pd out of range' as problem from {{ ref('rpt_ecl_by_client') }} where pd_12m < 0 or pd_12m > 1
union all
select client_id, 'weighted ECL outside the scenario range' from {{ ref('rpt_ecl_by_client') }}
where ecl < ecl_upside - 0.01 or ecl > ecl_downside + 0.01
union all
select client_id, 'ECL above LGD x EAD' from {{ ref('rpt_ecl_by_client') }} where ecl > {{ var('lgd') }} * ead + 0.01
union all
select client_id, 'stage 3 not at LGD x EAD' from {{ ref('rpt_ecl_by_client') }}
where stage = 3 and abs(ecl - {{ var('lgd') }} * ead) > 0.01
