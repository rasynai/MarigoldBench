# Statistical and operating plan, extract

Estimand: first adjudicated relapse by day 450. Death before relapse is
a competing event. Withdrawal is censoring in the primary analysis.

Primary calculation: use the cumulative-incidence product-limit
calculation. At each interval, add S(previous) times relapse/risk and
then update S by multiplying by 1 minus
(relapse plus competing death)/risk. Do not use the complement of
ordinary relapse-free Kaplan-Meier survival for this estimand.

Pre-specified withdrawal tipping analysis: withdrawals recorded as
clinical deterioration or adverse-effect refusal are informative.
For this analysis only, reclassify those participants as relapses in
their withdrawal interval. Leave relocation and scheduling/travel as
censored. Preserve the displayed interval risk sets.

Operating rule: NO_GO when the primary cumulative incidence exceeds
the futility boundary. When the primary value does not exceed the
boundary but the pre-specified tipping value does, issue NOT_ROBUST.
Issue GO only when neither value exceeds the boundary.

Futility boundary: specified in decision charter DC-12.
The decision-charter page is not included in this extract.
