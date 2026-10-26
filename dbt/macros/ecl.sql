{#-
  Expected-credit-loss factors, per unit of EAD x LGD, under a constant annual hazard implied by the 12-month PD.
    12-month (stage 1):  PD / (1 + EIR)
    lifetime (stage 2):  sum over years t = 1..L of [S(t-1) - S(t)] / (1 + EIR)^t, with S(t) = (1 - PD)^t
    credit-impaired (stage 3): 1 (default has happened; the loss is LGD x EAD)
-#}
{% macro ecl_factor(pd, stage, life_years=var('behavioural_life_years'), eir=var('eir')) -%}
case
    when {{ stage }} = 3 then 1.0
    when {{ stage }} = 2 then (
        {% for t in range(1, life_years + 1) -%}
        (pow(1 - {{ pd }}, {{ t - 1 }}) - pow(1 - {{ pd }}, {{ t }})) / pow(1 + {{ eir }}, {{ t }}){{ " +" if not loop.last }}
        {% endfor -%}
    )
    else {{ pd }} / (1 + {{ eir }})
end
{%- endmacro %}

{#- IFRS 9 stage at the reporting date: 90+ days past due is credit-impaired (stage 3); 30+ days past due (the
    backstop) or a 12-month PD at or above the SICR threshold is a significant increase in credit risk (stage 2). -#}
{% macro ifrs9_stage(months_past_due, pd, sicr_threshold=var('sicr_pd_threshold')) -%}
case
    when {{ months_past_due }} >= 3 then 3
    when {{ months_past_due }} >= 1 or {{ pd }} >= {{ sicr_threshold }} then 2
    else 1
end
{%- endmacro %}
