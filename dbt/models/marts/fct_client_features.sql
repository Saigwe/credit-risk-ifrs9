-- One row per client: behavioural features at the September 2005 reporting date, built only from the six statement
-- months. Protected characteristics (sex, marital status, age) are kept for the fairness check but never used as
-- model features (see model/train.py).
with m as (select * from {{ ref('int_client_months') }})

select
    c.client_id,
    c.credit_limit,
    c.bill_sep                                                              as balance,
    greatest(c.credit_limit - greatest(c.bill_sep, 0), 0)                   as undrawn,
    c.status_sep                                                            as status_current,
    max(m.months_past_due)                                                  as max_months_past_due_6m,
    count(*) filter (where m.months_past_due >= 1)                          as months_delinquent_6m,
    count(*) filter (where m.status = -1)                                   as months_paid_in_full_6m,
    max(case when m.month_no = 9 then m.utilisation end)                    as utilisation_current,
    avg(m.utilisation)                                                      as utilisation_avg_6m,
    max(case when m.month_no = 9 then m.utilisation end)
      - max(case when m.month_no = 4 then m.utilisation end)                as utilisation_trend_6m,
    avg(m.payment_ratio)                                                    as payment_ratio_avg_5m,
    min(m.payment_ratio)                                                    as payment_ratio_min_5m,
    c.education_code,
    c.sex_code,
    c.marriage_code,
    c.age,
    c.defaulted
from {{ ref('stg_uci__clients') }} c
join m using (client_id)
group by all
