# CORR-003 - 31 runs voided for infrastructure failures (billing + harness kills)

- Date: 2026-08-16 (UTC). Scope: campaign release-1.0.0 only.
- What happened: near the end of the campaign the OpenRouter account ran out
  of credits; every subsequent call returned HTTP 402 "Insufficient credits".
  26 runs recorded failure outcomes whose only cause was the 402:
  kimi-k3 12 (all sealed), qwen3.8-max 14 (11 sealed + 3 hidden).
  Because the slowest systems process the sealed block last, the void
  concentrates in exactly the cells the memorization probe needs - the
  hidden-vs-sealed "gaps" for kimi (+42%) and qwen (+45%) in the initial
  finalize output are artifacts of this billing failure, NOT memorization
  evidence. No other system had any 402.
- Decision rule (content-blind, same class as CORR-002): any outcome whose
  integrity_problems include "Error code: 402" is voided and re-run once
  credits exist; nothing else is touched. The model never produced work for
  these runs, so no outcome-dependent selection is possible.
- Quarantined: 26 outcome files under runs/corrections/CORR-003/outcomes/.
- Addendum (same day): 5 marigold outcomes (4 sealed, 1 hidden) recorded
  "run failed: ssh ..." because the evaluation host's interactive session
  restarts terminated the worker's SSH child processes mid-run (exit
  0xC000013A). Same content-blind class - the product never finished
  receiving/serving the work order. These 5 do NOT depend on OpenRouter and
  were re-run immediately on the same host; the scorecard uses the re-runs.
- Resolution (sponsor decision, 2026-08-16): the 26 runs are DROPPED, not
  re-run. Every affected table reports the reduced denominator (e.g. kimi
  sealed 7/10, qwen hidden x/63) and this correction is cited wherever those
  cells appear. This is a preregistration deviation (the plan promised every
  instance once per system); it is content-blind - the 402 depended only on
  account balance, never on task content or model output - so it cannot bias
  the surviving results, but it does weaken the kimi/qwen sealed comparisons
  to 10 and 11 instances respectively.
- Prevention: pre-campaign credit check added to the runbook; the finalize
  step now cross-checks for 402 markers before publishing a scorecard.
