-- REAL: one row per client, renamed by statement month. The file's repayment-status columns skip PAY_1: PAY_0 is
-- September, PAY_2 August ... PAY_6 April. Status: -2 no balance, -1 paid in full, 0 paid the minimum (revolving),
-- 1-8 months past due. Undocumented codes are kept and flagged, not guessed.
select
    ID                                   as client_id,
    LIMIT_BAL                            as credit_limit,
    SEX                                  as sex_code,
    EDUCATION                            as education_code,
    MARRIAGE                             as marriage_code,
    AGE                                  as age,
    PAY_0 as status_sep, PAY_2 as status_aug, PAY_3 as status_jul, PAY_4 as status_jun, PAY_5 as status_may, PAY_6 as status_apr,
    BILL_AMT1 as bill_sep, BILL_AMT2 as bill_aug, BILL_AMT3 as bill_jul, BILL_AMT4 as bill_jun, BILL_AMT5 as bill_may, BILL_AMT6 as bill_apr,
    PAY_AMT1 as paid_sep, PAY_AMT2 as paid_aug, PAY_AMT3 as paid_jul, PAY_AMT4 as paid_jun, PAY_AMT5 as paid_may, PAY_AMT6 as paid_apr,
    DEFAULT_NEXT_MONTH = 1               as defaulted,
    EDUCATION not in (1, 2, 3, 4)        as dq_education_code_undocumented,
    MARRIAGE not in (1, 2, 3)            as dq_marriage_code_undocumented
from {{ source('bronze', 'uci_credit_clients') }}
