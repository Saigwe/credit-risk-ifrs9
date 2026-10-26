-- One row per client and statement month (Apr-Sep 2005): status, bill, and the payment made in that month.
-- A payment in month m settles the bill of month m-1, so the payment ratio pairs them.
with long as (
    {% set months = [('apr', 4), ('may', 5), ('jun', 6), ('jul', 7), ('aug', 8), ('sep', 9)] %}
    {% for m, n in months %}
    select client_id, credit_limit, make_date(2005, {{ n }}, 1) as statement_month, {{ n }} as month_no,
           status_{{ m }} as status, bill_{{ m }} as bill, paid_{{ m }} as paid
    from {{ ref('stg_uci__clients') }}
    {{ "union all" if not loop.last }}
    {% endfor %}
)

select
    *,
    greatest(status, 0)                                                         as months_past_due,
    bill / nullif(credit_limit, 0)                                              as utilisation,
    lag(bill) over (partition by client_id order by statement_month)            as prior_bill,
    case when lag(bill) over (partition by client_id order by statement_month) > 0
         then least(paid / lag(bill) over (partition by client_id order by statement_month), 1.5) end as payment_ratio
from long
