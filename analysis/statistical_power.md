# Is the current scale statistically adequate? No — and here is exactly why.

Computed by `analysis/power_analysis.py` from the real release-3.0.0 outcomes
(2026-08-16). Method: template-level intraclass correlation (ICC) estimated by
one-way ANOVA on binary VCC outcomes; effective sample size via the design
effect DEFF = 1 + (m−1)·ICC; Wilson intervals; two-arm minimum detectable
difference at α=.05, power .80.

## The measured fact that drives everything

Runs within a template are strongly correlated. Measured ICC of chain success
within template: 0.10–0.55 across the four estimable systems (working value
0.26). Nemotron-super is the clearest case: its per-template pass rates are
`1.00, 0.75, 0.40, 0.33, 0.00, 0.00, 0.00, 0.00` — whole templates pass or
whole templates fail. **The template, not the run, is the unit of evidence.**

## What that does to the current design

| Design | runs | effective n | 95% CI width at a "5%" score | smallest detectable gap vs 5% |
|---|---|---|---|---|
| **Current: 8 templates × 6 runs** | 48 | **~21** | **±11 pp** (spans ~0–22%) | **33 pp** |
| 8 templates × 18 runs (more repeats) | 144 | ~26 | ±10 pp | 28 pp |
| 100 templates × 3 | 300 | ~197 | ±3.2 pp | 8.0 pp |
| 120 templates × 3 | 360 | ~236 | ±2.9 pp | 7.2 pp |
| 135 templates × 3 | 405 | ~266 | ±2.7 pp | 6.7 pp |
| 200 templates × 2 | 400 | ~317 | ±2.5 pp | 6.0 pp |

Two conclusions are forced:

1. **The current 8-template benchmark cannot support any public claim.** A
   reported "5%" is statistically indistinguishable from 0% and from 20%, and
   two frontier models cannot be separated unless they differ by ~33 points.
   At single-digit target difficulty, every interesting comparison is smaller
   than that.
2. **Adding repeats or instances to existing templates is nearly worthless**
   (48→144 runs moves effective n from 21 to 26). Only new independent
   templates buy information. The 300–400 expansion must therefore be
   **100+ new templates × 2–3 evaluated instances**, not more instances of
   few templates. Wide-and-shallow (200×2) is the best value per run.

## Adopted requirements for the 300–400 expansion

- ≥100 independent templates (target 120–135); ≤3 evaluated instances each.
- Templates must vary generator family, science area, and defect mechanism —
  correlated templates re-inflate ICC and silently shrink effective n.
- Report clustered (template-level bootstrap) intervals everywhere; Wilson on
  raw runs is an undercount of uncertainty and may only appear as a diagnostic.
- Between-model claims use paired-by-instance comparisons with template-level
  resampling; anything else overstates significance.
- Repeats (pass^3) are kept for the reliability headline, not for precision:
  they measure stability, they do not add independent evidence.

## Corroboration (19-paper deep-read fleet, all audits VERIFIED)

- Miller 2024 (error-bars): "new evals should contain at least 1,000
  questions"; n≈969 independent items to detect a 3-point gap; clustered SEs
  up to 3.05x naive on DROP - independently matching our DEFF estimate.
- GPQA (n=448) concedes it resolves only ~10-point effects at 80% power, and
  does not even cluster by its 61 question writers.
- Scale of credible frontier benchmarks: HealthBench 5,000; HLE 2,500;
  LAB-Bench 2,457; SWE-bench 2,294; LiveBench 1,000; CURIE 580. The only
  small-n exceptions (RE-Bench n=7, PaperBench n=20) compensate with 71
  expert human baseline runs or 8,316-leaf author-signed rubrics - both
  out of scope for us.
- BetterBench: 14/24 benchmarks report no uncertainty at all; the
  statistical-significance criterion is the field's weakest (5.62/15).
  Clustered CIs + power analysis on every scorecard puts us above nearly
  every incumbent on that axis.

Full synthesis: `analysis/literature/deep/SYNTHESIS.md`.
