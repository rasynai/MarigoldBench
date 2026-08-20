# Saturation and retirement policy

Preregistered numeric triggers, adopted 2026-08-16 after CORR-010. The point
of writing them down with numbers and dates is that "we'll refresh when it
saturates" is self-attestation; a trigger that binds is one the maintainer
cannot argue with after the fact.

## Definitions

- **Epoch**: one minted population of sealed + hidden instances, committed to
  cryptographically before any candidate runs (`crucible/commitment.py`).
- **Strongest system**: the highest pass@1 VCC among evaluated frontier
  systems in a campaign, on the hidden split.

## Triggers

| # | Condition (hidden split) | Action | Deadline |
|---|---|---|---|
| T1 | Strongest system pass@1 > 40% in one campaign | Mint the next epoch from fresh seeds; investigate which templates carry the inflation (per-template solve table) | before the next campaign |
| T2 | Strongest system pass@1 > 40% in two consecutive campaigns | Retire the template generation: new templates required, not just new seeds | within one quarter |
| T3 | Strongest system pass@1 > 70% in any campaign | The epoch is dead on arrival: withhold the headline, publish the number only inside a correction, root-cause before anything ships | immediately |
| T4 | Any single template solved at 100% by two frontier families (>= 3 runs each) | That template is removed from the headline population and audited | before the scorecard ships |
| T5 | Released-split vs freshly-minted-split gap > 10 pp for any system | Treat as contamination evidence: publish the gap, retire the released split | immediately |

CORR-010 is the precedent for T3: the 3.0.0 campaign measured 94-100%, the
headline was withheld, and the numbers were published only inside the
correction with the defect named.

## Why this is cheap for us and expensive for everyone else

Static benchmarks pay authorship costs per refresh, so their real policy is
to hope. Constructed truth regenerates an epoch from new seeds for CPU cost,
and gates (B8/B1/B5b/B0, leak scan, giveaway scan, wrong-path margins) re-run
mechanically. The policy above is only credible because refresh costs
approximately nothing.

## Reporting requirement

Every scorecard states the epoch id, the commitment digest, and which
triggers (if any) fired. "No triggers fired" is itself a required line.
