# CORR-010 - campaign 3.0.0 saturated: the work orders did the candidate's thinking

Date: 2026-08-16 (UTC). Scope: campaign release-3.0.0 (CRUCIBLE-CHAIN), all 8
templates. Status: defect confirmed, root causes fixed, campaign results
retained as a measurement of the OLD instrument only.

## What happened

The 3.0.0 chain campaign completed 280 runs across five frontier systems. The
design target was single-digit pass rates. The measured result:

| System | pass^3 | pass@1 [95% CI] | E[chain depth] |
|---|---|---|---|
| openai (gpt-5.6-sol) | 100.0% | 100.0% [92.6, 100.0] | 8.0 / 8 |
| anthropic (claude-opus-5) | 93.8% | 93.8% [83.2, 97.9] | 7.5 / 8 |
| deepseek-v4-flash | 31.2% | 62.5% [48.4, 74.8] | 5.74 |
| nemotron-3-super-120b | 6.2% | 27.1% [16.6, 41.0] | 2.24 |
| nemotron-3-ultra-550b | 0.0% | 14.6% [7.2, 27.2] | 1.52 |

Seven of eight templates were solved at 100% by the frontier pair, including
the 8-stage chain. The tasks discriminate between capability tiers, but they
do not challenge the frontier at all, which is what the benchmark exists to do.

## Root cause

Not "the science was easy". The candidate-visible material handed over the
work. A nine-agent audit (one per template plus synthesis; full report at
`analysis/crucible4_hardening_spec.md`) classified all 61 stages and found
six giveaway classes. Ranked by difficulty destroyed:

1. **DEFECT_ANNOUNCED** - the prep log narrated the planted defect, its cause,
   its direction and its consequence in prose ("so this level is over-strength
   relative to its nominal value. Re-prep requested"). Noticing was free, so
   the whole H1 chain collapsed to one announced branch.
2. **RECIPE_IN_PROMPT / IN_ARTIFACT** (39% of stages) - the work order listed
   the method as an ordered checklist ("Apply the stated single-point test,
   identify the error structure, select the permitted calibration treatment,
   calculate the slope..."), converting every judgment into execution.
3. **OPTION_MENU** (25% of stages) - the answer schema printed the allowed
   values (`"<one of: PFAFFL | DELTA_DELTA_CQ>"`), making each categorical
   judgment multiple choice with a 1/2 guess floor.
4. **TOLERANCE_LEAK** (20% of stages) - wrong analysis paths landed *inside*
   tolerance. On the exemplar's H1 seed 12, unweighted OLS scored 1891.65
   against a keyed 1881.5 +/- 18.815 (a pass), and weighting all seven
   standards - i.e. missing the entire planted defect - gave 0.7758 against a
   keyed 0.78 +/- 0.03 (also a pass). Three of four analysis paths reached the
   correct verdict, so the chain was compensatory and p^K never multiplied.
5. **DECOY_HINT** - the prompt warned against the trap ("A good r-squared does
   not by itself answer the work order"), which drove benchmark-wide trap rate
   to ~0 and made the trap-reachability gate vacuous.
6. **Seed-invariant answers** - 5 of 8 templates had stages constant across
   all 18 instances; PHARM-016's six H1 seeds shared an identical answer
   vector, so the sealed split was fully determined by the development split.

Two institutional causes let this ship, and both are fixed:

- **`spec.giveaway_scan()` only inspected `payload["prompt"]`.** Every audited
  recipe lived in an *artifact*. The gate was blind to the file containing the
  answer sheet.
- **`author.REVIEW_TEMPLATE` criterion 2 instructed the reviewer to demand
  spoon-feeding**: "the key is unfair and must be tightened by the prompt
  naming the required method." The repair loop actively rewarded the defect.
  Five of eight templates shipped with `approve: true` **and** a non-empty
  `required_fixes` list documenting these exact problems.

## What was fixed

Code (all changes covered by tests; suite 86 passing):

- `spec.giveaway_scan()` now scans the prompt **and every artifact** for
  option menus, method recipes (>=3 verbs/sentence, >=5 per work order) and
  decoy hints; `check_payload` rejects on any finding.
- `spec.check_stage()` requires `wrong_paths` for every numeric stage: >=2
  enumerated wrong-analysis values, **all** of which must miss the correct
  value by >3x tolerance. Single-decoy checks could not catch a compensatory
  chain.
- Categorical stages now require negation-safe `correct_aliases` /
  `decoy_aliases` with a gate-checked disjointness proof, so answers can be
  free-form: the prompt no longer prints any judgment vocabulary.
- `score.py`: alias matching on word boundaries, set-valued answers, hedge
  detection (matching both sides is not a verdict), `decoy_id` reporting so
  failures can be traced to *which* wrong analysis was taken, and an
  `unmatched` flag feeding a post-hoc cross-family adjudication lane that can
  extend aliases and trigger a rescore but can never grant credit in place.
- `spec.check_payload()` rejects any `rule_constants` (thresholds, critical
  values, limits the key depends on) that appear verbatim in candidate-visible
  text; they must be derivable from shipped data.
- `author.py` rules 17-19 forbid method recipes, answer menus and
  missing/unsafe aliases; review criterion 2 now demands the DATA determine
  the method and requires deleting any stage where it cannot.
- `build.py` refuses to materialize on `approve: true` with a non-empty
  `required_fixes`.
- The gold-standard exemplar was rebuilt: neutral provenance (the prep log
  records lots, a separate stock register makes disqualification a join with a
  benign case-difference near-miss), a data-driven acceptance criterion in
  place of a named method, and **per-seed regime rotation** so the winning
  treatment, the eligible count, the contamination direction and the side of
  the reporting limit all vary. Measured over the 18 shipped instances: the
  weighting answer splits 9/9 between the two treatments, and H1 decisions
  split 3/3 - the condition label is no longer a lookup key.
- New population gates in the test suite: no stage answer may be constant
  across the 18 instances, and no condition may pin the decision to one token.

A test that asserted the old defect was corrected: it required
`c0_decision != h1_decision`, which is precisely the condition-to-decision
bijection that let a model score by pattern-matching the condition. It now
asserts the answer keys differ while decisions remain unpredictable from the
condition.

## Status of the 3.0.0 numbers

The 280 runs are **valid measurements of the 3.0.0 instrument** and are
retained and published as such, with this correction linked from the
scorecard. They are **not** evidence about frontier scientific judgment, and
no claim of that kind may cite them. The five-system comparison, the hazard
profiles and the calibration table remain informative about the systems'
relative behaviour on guided worksheets.

Note also that 8 templates cannot support a public claim at any difficulty:
the template-clustered effective sample size is ~21 (ICC ~0.26), so a "5%"
result is statistically indistinguishable from 0% and from 20%. See
`analysis/statistical_power.md`. The 4.0 expansion is specified at >=100
independent templates.

## Why this is published rather than quietly patched

The identical failure is documented in the two most relevant prior
benchmarks: GPQA required answer-only baselines to stay at chance before
claiming there were no easy tells, and CORE-Bench shipped values that made 20
of 45 hard tasks answerable without doing the analysis - unnoticed until
saturation. A benchmark that claims near-zero label error has to hold itself
to the standard it advertises, in public, including when it fails.

## Related

- `analysis/crucible4_hardening_spec.md` - the full nine-agent audit and spec
- `analysis/statistical_power.md` - why 8 templates cannot support a claim
- `analysis/literature/deep/SYNTHESIS.md` - 19-paper corroboration
- CORR-009 - frontier-only lineup restriction
