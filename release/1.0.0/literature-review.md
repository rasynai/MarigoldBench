# Literature record for CRUCIBLE-CHAIN

What was read, what it established, and what we did about it. 23 benchmarks and
methodology papers were read in full (not abstracts) by parallel research
agents during design; the two most load-bearing papers (LifeSciBench,
HealthBench) are archived as PDFs in this directory alongside extracted text.

Everything below is here because it changed a design decision. Where a paper
only confirmed something we already did, it is marked *(confirms)*.

---

## 1. The finding that reorganised the whole design

**At single-digit pass rates, the benchmark's own error rate is the binding
constraint, not task difficulty.**

- **Humanity's Last Exam**: adversarial filtering kept questions *because
  models failed them*, which systematically enriches for wrong answer keys.
  FutureHouse's audit of 321 bio/chem items found **29 ± 3.7%** with answers
  contradicted by peer-reviewed literature; HLE's own re-audit put expert
  disagreement at **15.4%** (18% in bio/chem, 25% under a single-reviewer
  criterion). Reviewers had been told not to spend >5 minutes verifying.
- **GPQA**: Epoch estimates **~8%** of Diamond items are invalid; the authors'
  own conservative objectivity estimate for the extended set is **73.6-76.4%**.
- **FrontierMath**: a 35-problem double review found 2 wrong answers →
  posterior error rate **~7-10%**; v2 (June 2026) went on to correct **42%** of
  problems.
- **CORE-Bench**: a post-saturation audit found **15 of 45** hard tasks
  contained errors and **20 of 45** were shortcut-exploitable.
- **SWE-bench**: OpenAI's Verified re-curation flagged **38.3%** of samples as
  underspecified and **61.1%** as having tests that could reject valid
  solutions; **68.3%** were filtered out. Fixing this moved GPT-4o from 16% to
  33.2% — the original benchmark *understated* capability.

**What we did.** Our truth is *constructed*: a deterministic generator computes
every stage answer from data it generated itself, so there is no answer key to
get wrong. This is the single largest structural advantage CRUCIBLE-CHAIN has
over every benchmark above, and it is why we can aim at single-digit scores
without the signal being swamped by label noise. We still publish an audited
error estimate rather than asserting zero (see §7).

---

## 2. Where difficulty must come from

| Source | Evidence | Our decision |
|---|---|---|
| **Constructed multi-stage chains** | GeneBench-Pro: 129 problems built from a fully known causal structure, 3-13 ordered decision points (median 6), best frontier model **28.7%**. Names the "noticing-to-acting gap" — models spot QC flags and fail to propagate them — and concedes binary grading "collapses useful stage-level diagnostic evidence" | Adopted, and we build the instrument GeneBench-Pro says it lacks: per-stage scoring, chain depth, and an explicit notice-vs-act metric |
| **Adversarial filtering against models** | HLE got single-digit launch scores this way — and imported a ~29% error rate doing it | **Rejected as the primary mechanism.** We never select tasks by model failure. Difficulty is constructed via trap separation and chain length |
| **Human expertise gap** | GPQA's two-sided filter (2 experts must agree, 3 skilled non-experts with web access must fail) moved non-expert accuracy 34%→22% while expert accuracy rose 65%→81% | Cannot replicate without humans. Substituted by the baseline ladder (§5) |
| **Long horizons** | PaperBench: agents lead humans in the first hours, humans overtake after ~24h; RE-Bench: agents 4x humans at 2h, humans 2x agents at 32h | Out of scope — we are single-turn. Disclosed as a scope limit |

**Compounding arithmetic.** With per-stage accuracy p over K stages, chain
completion ≈ p^K. p=0.75, K=7 → 13%. p=0.65, K=7 → 5%. Single-digit headline
numbers fall out of the structure rather than out of obscurity.

---

## 3. Grading: what the evidence says works

Every mitigation in `crucible/chain/judge_chain.py` and `judge2.py` is here
because a 2025-26 paper measured it working.

- **Criterion-level decomposition beats holistic scoring**: replacing a holistic
  verdict with per-dimension forced choices reduced self-preference bias by
  **31.5%** on average (69.9% for the worst offender). Plain chain-of-thought
  sometimes *increased* bias.
- **Style bias dwarfs position bias**: markdown formatting shifted judge
  preference by up to **+0.76**, versus **≤0.04** for position in modern judges.
  → we strip formatting before judging.
- **Never batch many criteria over long outputs**: verification accuracy fell
  **-1.9 to -20.0** points at 2 criteria/call and **-18.7 to -35.4** at 5, on
  long agentic transcripts. → we cap at 8 and prefer fewer.
- **Reference-guided grading**: giving the judge the gold answer cut math
  grading error from **70% → 15%** (Zheng et al. 2023). → our judge sees truth
  and the reference answer.
- **Self-preference is real and family-shaped**: 17 of 20 models showed
  statistically significant self-preference; some strongly self-*deprecating*
  (Claude Sonnet 4.5, β=-0.229). Capability does not imply objectivity — only
  3 of 20 qualified as objective judges. → cross-family judge of record, and
  judges never touch the primary metric.
- **Ship a judge benchmark with the benchmark**: PaperBench's JudgeEval gave
  human gold labels and reported o3-mini at **F1 0.83** ($66/paper) vs o1 at
  0.84 ($830). HealthBench's meta-eval put GPT-4.1 at **macro-F1 0.709**,
  within the physician range where physician-physician agreement is 55-75%.
  → `meta_eval2.py` gates the campaign on a gold-set run.
- **PaperBench's own admission**: its judge was **never stress-tested against
  adversarial submissions**, and its cheat monitor is a lexical grep. → we test
  judge-injection, fabricated evidence quotes, and empty submissions explicitly.

---

## 4. Anti-gaming: assume the benchmark will be attacked

The 2026 audits are unambiguous: a Berkeley team scored **100% on Terminal-Bench,
SWE-bench Verified, SWE-bench Pro and FieldWorkArena, ~98% on GAIA, ~100% on
WebArena — without solving a single task**. BenchJack found 219 flaws across 10
benchmarks. Concretely:

| Exploit | Where it happened | Our defence |
|---|---|---|
| Answer shipped inside the artifact | CORE-Bench: **20 of 45** hard tasks | `spec.leak_scan()` greps every artifact for every stage answer in ~12 renderings; a hit is a build-time rejection |
| Answer guessable from priors | DiscoveryBench: Llama-3 scored **11.5% with no data and 11.5% with data** — its entire score was prior knowledge | B0 prior-only baseline is mandatory and printed next to the headline |
| Visible scorer → hill-climbing | METR: reward hacking **43x** more common on RE-Bench (visible scorer) than HCAST; **100%** of o3 trajectories hacked one task | Single-turn, no execution environment, no score feedback, truth never shipped |
| Grader trusts agent-written files | SWE-Lancer: agents overwrote test files → **100%** without solving anything | Grading is a pure function of the submission string; nothing the candidate writes is executed |
| Null/empty answers score | τ-bench: a do-nothing agent passed **38%** of airline tasks | Verified: empty, prose-only, shotgun and judge-injection submissions all score 0 |
| Truth recoverable from public data | MLE-bench: private labels recomputable from the public Kaggle split; **74/75** even after patching | Our data is generated; nothing exists publicly to join against |
| Telling the model not to cheat | METR: "do not reward hack" left hacking at **70%**; the model answered "no" 10/10 when asked if its strategy matched intent | Not attempted. Structure, not instruction |

---

## 5. No human baseline: what we do instead

The honest accounting first: a defensible expert baseline costs **$100k-$350k
and 500-2,500 expert-hours** (RE-Bench: $1,855 per 8-hour attempt × 71 attempts;
HCAST: $50-100/h plus bonuses over 1,500+ hours; GPQA: ~$95/h realised over 61
contractors). We have none of that, and the standing scope decision is that we
never will.

The substitute is **bracketing rather than proxying**, following RE-Bench's
two-anchor normalisation with anchors that are artifacts rather than people
(0 = naive method, 1 = reference solution) plus the ladder below. Rungs L0, L1,
L5, L8, L9 are non-negotiable; L2 is non-negotiable for us because our forks are
drawn from real methodological literature.

| Rung | What it proves |
|---|---|
| L0 random | the arithmetic floor |
| L1 degenerate (empty, refusal, constant) | the grader rejects nothing-answers — this is the rung that caught τ-bench's 38% |
| **L2 prior-only (artifacts withheld)** | how much score is parametric recall, not analysis. The frontier's real credit is (score − L2) |
| L5 naive method (all-decoy path) | what a competent-but-hasty analyst scores; our normalised zero |
| L8 reference solution | the task is solvable and the grader accepts a correct answer |
| L9 grader adversary | the ceiling cannot be reached illegitimately |

Wei et al.'s systematic review of **115 human baselines** is the governing
citation for how to disclose the absence: median sample size **8**; only
**1.74%** ran a power analysis; **33%** reported uncertainty; **8.7%** ran a
significance test. Their principle — *"all baselines should be transparent even
if not maximally rigorous"* — extends to the null case, so `docs/LIMITATIONS.md`
states plainly that no human-level claim of any kind is supported.

---

## 6. Statistics

From *Adding Error Bars to Evals* (Miller, Anthropic, 2024), all adopted:
CLT-based standard errors rather than bootstrap for simple means; **clustered
standard errors** wherever items come in related groups (real cases show
clustered SEs **>3x** naive ones — for us the cluster is the template);
question-level **paired** differences when comparing two systems; and a power
analysis stating the minimum detectable effect rather than implying a ranking
the n cannot support. `chain/score.py` implements cluster bootstrap over
templates; `pass_hat_k` reports reliability alongside pass@1.

Calibration is reported because HLE showed it carries most of the information
when accuracy is near the floor: every model there exceeded **70% RMS
calibration error** — confidently wrong. We require a per-stage confidence and
report Brier, RMS calibration error, and mean overconfidence.

---

## 7. Governance

The FrontierMath episode is the cautionary case: OpenAI commissioned and funded
the benchmark, held problems *and solutions* for ~250 of 300 items under a
**verbal** no-training agreement, contributors were never told, and disclosure
appeared in arXiv v5 **the same day** OpenAI announced o3 at 25.2% — a number
the benchmark's own lead mathematician said they could not vouch for. Epoch's
retrofit (a sponsor-blind holdout, published sponsorship policy) is now the
community's expected baseline.

Adopted from BetterBench (46 criteria; the field's compliance is poor —
**17 of 24** benchmarks ship no replication script, **14 of 24** report no
uncertainty, only **3 of 24** have CI): a datasheet with the funding question
answered, a benchmark card naming out-of-scope claims, floors and ceilings
reported next to every score, versioned corrections that re-run rather than
retro-fit, and a named maintainer.

Our disclosure obligations, stated up front rather than in an appendix: the
tasks are model-authored and model-reviewed; the judges share families with the
candidates; there is no human baseline; and the same person built the benchmark
and ran every system on it.

---

## 8. Papers read

**Science and agent benchmarks**: LifeSciBench (750 tasks, expert rubrics,
best model 0.576/36.1%) · GeneBench-Pro (129 synthetic-causality problems,
28.7%) · HealthBench (5,000 conversations, 48,562 physician criteria) ·
PaperBench (20 papers, 8,316 rubric leaves, JudgeEval) · MLE-bench (75 Kaggle
competitions, medal thresholds, Dolos plagiarism detection) · SWE-bench and
SWE-bench Verified · ScienceAgentBench (102 tasks, contamination surgery) ·
CORE-Bench (270 tasks, 3-level information ladder) · SciCode · DiscoveryBench
(NoDataGuess control) · BixBench · LAB-Bench and LABBench2 · GAIA · RE-Bench ·
GPQA · Humanity's Last Exam · FrontierMath · Cybench · ARC-AGI-2 · HCAST

**Methodology**: Zheng et al. 2023 (LLM-as-judge) · Play Favorites (2025,
self-bias regression) · Quantifying and Mitigating Self-Preference Bias (2026) ·
Judging the Judges (2026, mitigation ablations) · Can LLMs Write Reliable
Rubrics (2026) · RuVerBench (2026, criterion verification) · BetterBench (2024) ·
Adding Error Bars to Evals (2024) · Wei et al. Human Baselines checklist (2025) ·
Agentic Benchmark Checklist (2025) · BenchJack (2026) · Berkeley RDI benchmark
audits (2026) · Life After Benchmark Saturation (2026) · SWE-Bench Illusion
(2025) · SWE-bench+ (2024) · HAL (2025) · AstaBench (2025) · AI Agents That
Matter (2024) · evaluation-awareness literature (2025-26)

Full per-paper notes, including every quantitative claim and its URL, are in
`analysis/literature/notes/`.
