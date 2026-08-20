# Deep-read synthesis: 19 papers, every word, verified

Corpus: 19 papers downloaded to `analysis/literature/pdfs/` (2.19 MB of
extracted text in `md/`), each read end-to-end by a dedicated agent and
independently audited (file-on-disk, coverage-ledger, section spot-checks,
verbatim-quote grep). **19/19 audits returned VERIFIED.** Per-paper deep
reports (24–34 KB each) live beside this file. Machine-readable summaries:
`_fleet_summaries.json`.

## 1. The scale question, answered by the field

| Benchmark | Independent items | Note |
|---|---|---|
| HealthBench | 5,000 convs / 48,562 rubric criteria | 262 physicians authored rubrics |
| SWE-bench | 2,294 | mined + execution-validated (~2.5% yield) |
| HLE | 2,500 + private held-out | 1,000 contributors, $500K pool |
| LAB-Bench | 2,457 | programmatic + manual hybrid |
| LiveBench | 1,000 | monthly refresh |
| CURIE | 580 | 429 source papers |
| GPQA | 448 main / 198 diamond | admits it resolves only ~10-point effects |
| SciCode | 338 subproblems / 80 mains | ~18 scientist authors |
| CORE-Bench | 270 | 90 papers × 3 levels |
| ScienceAgentBench | 102 | 9 annotators, 44 pubs |
| MLE-bench | 75 competitions | many seeds per comp |
| PaperBench | 20 papers | but 8,316 binary leaves + author sign-off |
| RE-Bench | 7 environments | compensates with 71 expert human runs |
| **CRUCIBLE-CHAIN today** | **8 templates** | **below every entry above** |

Anchors from the methodology papers:
- **Miller (error-bars):** "new evals should contain at least 1,000 questions";
  n≈969 independent items to detect a 3-point difference (α=.05, power .8).
  Clustered SEs run up to **3.05×** naive (DROP) — matching our measured
  ICC ≈ 0.26 / DEFF ≈ 2.3–5.5.
- **GPQA** explicitly concedes 448 items detect only ~50%→60% effects at 80%
  power — and it does not cluster by its 61 writers, which our audit flags as
  an undercount of its uncertainty.
- **BetterBench:** 14 of 24 assessed benchmarks report no significance or
  uncertainty at all; statistical-significance criterion scores 5.62/15 across
  the field. Reporting clustered CIs + power analysis puts us above nearly
  every incumbent on their weakest axis.

**Verdict of record: the current 8-template scale cannot support any public
claim.** (Quantified in `analysis/statistical_power.md`: effective n ≈ 21;
a "5%" is indistinguishable from 0% and 20%.) The two tiny-n exceptions
(RE-Bench n=7, PaperBench n=20) buy credibility with what we ruled out
(large human-expert baselining) or with 8,316-leaf author-signed rubrics.
The expansion must be **100–200 independent templates × 2–3 instances**
(300–400 instances), which lands us mid-table on items and top-of-table on
label reliability — no incumbent has constructed truth.

## 2. What every credible benchmark does that we now do (or must)

1. **Answer-only / ablation probes as release gates** (GPQA's answer-only
   classifiers; SWE-bench's temporal check; LiveBench's post-cutoff rule).
   Ours: B0 prior-only floor + new B10 artifact-ablation + B12 seed-transfer.
2. **Tiering by measured difficulty** (GPQA extended→main→diamond; HLE's
   frozen-frontier-panel filter; HealthBench Hard where "many models score 0").
   Ours: template admission requires measured frontier failure under the
   final harness — mirrors HLE stumping its panel before acceptance.
3. **Pass@k inflation control** (FrontierMath o1-preview ~2%→~6% pass@8;
   MLE-bench 16.9%→34.1% pass@8). Ours: pass^3 headline is the
   anti-inflation statistic; pass@k reported but never headlined.
4. **Contamination defenses beyond honor-system canaries** (survey:
   n-gram/embedding detection is weak against paraphrase; LiveBench's refresh
   is the strongest pattern). Ours: generator mints fresh sealed instances
   per release — a defense no static benchmark can copy.
5. **Prompt-format sensitivity** (lessons-trenches: format alone moves scores
   14–46pp and flips rankings). Ours: byte-identical prompts across
   conditions; the standing preamble is a frozen module constant; report the
   harness version with every number.
6. **Judge validity is earned, not assumed** (HealthBench meta-eval on 60,896
   physician-annotated pairs; MMLU-Redux shows 6.5% label error in the
   field's most-cited benchmark, Virology 57%). Ours: judges never touch VCC;
   cross-family adjudication only extends aliases post-hoc; constructed truth
   keeps label error structurally near zero.

## 3. What the field cannot do that we can (the moat, evidence-grounded)

- **Label error ~0 by construction.** MMLU-Redux: 6.5% of MMLU erroneous.
  GPQA: 5-stage, ~$95/hr pipeline reached only ~74% objectivity. PaperBench:
  tens of author-hours per rubric. Our generator computes truth from data it
  generated; the reference answer scores 1.00 by gate (B8).
- **Contamination-proof refresh at near-zero marginal cost.** LiveBench pays
  monthly authoring costs; HLE's held-out set is finite. New seeds are free.
- **Process verification without agent infrastructure.** CORE/MLE/RE/Paper
  benches need containers, GPUs, hours-long runs ($66–123 per PaperBench
  paper just to grade). A CRUCIBLE chain is one prompt + deterministic
  scoring: frontier-hard, but runnable by anyone in minutes.
- **Condition-controlled counterfactuals.** No incumbent ships byte-identical
  clean/defect pairs (C0/H1) with a false-alarm penalty; RE-Bench and
  PaperBench measure only the happy path.

## 4. Design corrections the corpus forces on us

- **Report the full ladder every time** (GPQA subset-selection warning):
  selection by frontier failure skews estimates → re-estimate on fresh
  instances of selected templates and report both.
- **Pre-register abstention policy** (GPQA: abstention handling moved
  headlines >10 points). F2's refusal-correct scoring is pre-registered;
  backoff/retry policies are forbidden.
- **Per-stage diagnostics are the product** (GPQA domain heatmaps, HLE
  calibration table, hazard profiles): a lab that scores 4% must still learn
  *which* judgment failed — that is why they run it again.
- **Never ship without uncertainty** (BetterBench's weakest criterion
  field-wide): clustered bootstrap CIs by template on every scorecard line.

## 5. Bottom line

The current benchmark is the right *design* at an indefensible *scale*, and
until yesterday it had a fatal prompt-leak defect the field would have caught
in review (it is GPQA's answer-only failure and CORE-Bench's shipped-values
failure in a new costume — both papers document the same disease). The
hardening spec closes the defect mechanically; the literature sets the scale
bar at ≥100 independent templates / 300–400 instances with clustered CIs and
a ≥1,000-instance trajectory; and the moat — constructed truth + free refresh
+ condition-controlled counterfactuals — is real, documented, and unmatched
by any of the 19 benchmarks read.
