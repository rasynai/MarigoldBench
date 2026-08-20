# CRUCIBLE 2.0 - gap analysis and design rationale

Date: 2026-08-16. Author: automated release manager for sponsor Ansh Tiwari.
Purpose: recorded basis for rebuilding CRUCIBLE into a public frontier
benchmark for open-ended science tasks (300-400 items, LLM-judged), per the
sponsor's directive. Sources reviewed are listed at the end; the two primary
papers are archived in analysis/papers/.

## 1. What CRUCIBLE v1 actually tested

104 instances, 10 synthetic archetypes of routine analytical-chemistry and
ops micro-tasks. Every task had computed ground truth (GeneBench-style
known-causality) and a deterministic, non-compensatory gate: endpoint value,
reproduction script, claim grounding, planted-hazard detection, and a
report/don't-report decision. Strengths that are RARE elsewhere and must be
kept: condition symmetry (clean vs hazard vs underidentified variants with
byte-identical wording), hidden + sealed splits, repeat runs for run-to-run
reliability, a native-product row (Marigold) separated from model rows, a
corrections protocol that was actually exercised (CORR-001..004).
Weaknesses the sponsor correctly called out: tasks are narrow, closed-form,
and small; the deterministic graders proved brittle to phrasing (CORR-004:
22 grader false-negatives across 7 of 9 systems); nothing is open-ended, so
nothing measures judgment, design, synthesis, or communication.

## 2. What exists at the frontier (June-July 2026 state of the art)

- **LifeSciBench (OpenAI, June 2026; 750 tasks)** - expert-authored
  free-response tasks across 7 workflows x 7 life-science domains with
  expert-written rubrics (19,020 criteria, avg 25/task; normalized score =
  points/total; pass = >=70%). Single-turn; artifacts (sequences,
  structures, figures, tabular, PDFs); model-based rubric grader
  spot-validated against experts. Best frontier model: 0.576 normalized /
  36.1% pass; 22.8% of tasks passed by NO model. Documented bottlenecks:
  artifact use, exact/construct outputs, partial-progress-without-completion.
- **GeneBench-Pro (OpenAI, June 2026; 129 problems)** - research-level
  computational-biology problems over PURELY SYNTHETIC data with a known
  causal structure, so grading is deterministic and there is a unique
  correct analytical path. Headline finding: the "noticing-to-acting gap" -
  models notice QC failures and confounds but fail to propagate them into
  the right downstream decision. Best model ~28.7% pass.
- **HealthBench (OpenAI, 2025)** - physician-written rubrics (48,562
  criteria) applied by a model grader; the template for criterion-level
  rubric judging at scale.
- **PaperBench (OpenAI, 2025)** - hierarchical rubric trees judged by LLM
  judges for paper replication; 20 papers (depth over breadth).
- **LAB-Bench / LABBench2 (FutureHouse, 2024/2026)** - biology research
  assistant tasks; LABBench2 moves to open-response with patents, trials,
  messy data.
- **BixBench, ScienceAgentBench, CORE-Bench, SciCode** - agentic
  computational-science suites; largely code-execution scoped; BixBench
  reported near-saturated.
- **LLM-judge methodology literature (2025-26)** - self-preference bias is
  real and large in pairwise settings (75-84% own-family win rates for some
  families; Claude under-rates itself); mitigations with empirical support:
  criterion-level BINARY rubric judgments with required evidence quotes
  (granularity suppresses holistic style bias), cross-family judge
  assignment, judge panels/juries for audit slices, meta-evaluation against
  gold labels, reporting inter-judge agreement (target alpha ~0.8). Regex
  and string graders are documented to systematically penalize semantically
  correct answers (large judge-flip rates on re-check) - independently
  rediscovered by us as CORR-004.

## 3. The gap CRUCIBLE 2.0 fills

Nobody combines, in one public benchmark:
1. **Open-ended realistic science tasks** (LifeSciBench's strength) WITH
   **synthetic known-truth artifacts** (GeneBench's strength). We generate
   the data behind every task, so every rubric mixes objectively checkable
   anchor criteria with judged criteria - rubric judging that cannot drift
   from the physical truth of the artifact.
2. **Hazard conditions inside open-ended work** - planted defects, flawed
   premises, impossible requests, and clean controls with symmetric wording.
   This measures the noticing-to-ACTING gap by construction: every hazard
   task carries paired rubric criteria (notice the defect; act on it in the
   recommendation) plus penalty criteria for inventing problems in clean
   controls. GeneBench named this gap; no open-ended benchmark scores it
   symmetrically with false-alarm controls.
3. **Reliability as a first-class metric** - repeat runs and flip rates;
   frontier benchmarks report single-shot scores only.
4. **Contamination hygiene** - hidden + sealed splits and condition
   symmetry, absent from all of the above (LifeSciBench is fully public on
   release; GeneBench released 10 of 129).
5. **Judge accountability** - cross-family judging with a preregistered
   gold-set meta-evaluation, a dual-judged audit slice with agreement
   statistics, and per-criterion evidence quotes, following the 2025-26
   bias literature rather than trusting a single grader.

## 4. Design decisions for 2.0 (with reasons)

- **Scale**: ~300 new open-ended tasks (30 templates x ~10 instances) +
  the 104 verifiable-core v1 instances retained as the deterministic
  anchor track -> ~400 total items. Fits the sponsor's 300-400 target.
- **Structure per task**: prompt (realistic work order, single-turn) +
  generated artifacts (CSV/logs/notes/sequences as text artifacts; we skip
  binary images - a disclosed scope limit) + rubric of 12-25 criteria in
  four groups: anchors (deterministically checkable against generation
  truth), reasoning/method, hazard notice->act pairs (or false-alarm
  penalties on clean variants), communication/actionability. Points sum to
  100; penalties negative; pass threshold 70 (LifeSciBench convention).
- **Domains x workflows**: 10 science areas (analytical chem, org synthesis,
  molecular bio, genomics, pharmacology/PK, microbiology, materials,
  environmental, biostat/epidemiology, lab ops/QA) x 6 workflows (evidence
  handling, analysis, design/optimization, troubleshooting/QC, translation/
  decision, communication) - LifeSciBench's taxonomy adapted to what is
  generatable with verifiable text artifacts.
- **Generation**: dual-model authoring (claude-opus-5 authors half,
  gpt-5.6-sol half), then MANDATORY cross-family review (the other family
  checks question-rubric consistency, ambition, factual soundness,
  ambiguity, leakage) with revision; then judge-based selftest: a reference
  strong answer must score >=85, a planted weak answer <=40, else the task
  is rejected. This mirrors LifeSciBench's QA (consistency/ambition/
  fact-check) with models standing in for experts - disclosed prominently
  as the benchmark's main validity limitation.
- **Judging**: criterion-level binary verdicts with a required verbatim
  evidence quote per met criterion; anchors auto-checked deterministically
  where possible and judge-checked otherwise; primary judge cross-family
  (OpenAI grades Anthropic + 3 OR models; Anthropic grades OpenAI + the
  other 3; Marigold graded by both, averaged - its base is OpenAI so
  Anthropic is its cross-family judge of record). 10% dual-judged audit
  slice -> agreement stats; ~30-response gold set with known intended
  scores -> judge meta-evaluation before any campaign scoring.
- **Metrics**: normalized rubric score (partial credit), pass rate
  (>=70%), hazard notice-rate vs act-rate (the gap, scored separately),
  false-alarm rate on clean variants, repeat flip rate on a 20-instance
  x3 subset, hidden-vs-sealed gap.
- **Budget**: OpenRouter hard cap $100 for candidate runs (6 frontier
  models), enforced by a dollar-metering guard using OpenRouter's actual
  per-call cost field; generation + judging on the sponsor's OpenAI and
  Anthropic keys. Every call remains in the append-only usage ledger.
- **What v1 keeps doing**: the 104-instance deterministic core runs
  unchanged as Track V; 2.0 results report both tracks side by side.

## 5. Sources

- LifeSciBench preprint (OpenAI, June 2026) - analysis/papers/lifescibench.pdf
- HealthBench paper (OpenAI, 2025) - analysis/papers/healthbench.pdf
- GeneBench-Pro announcement (OpenAI, June 30 2026) - openai.com/index/introducing-genebench-pro
- LABBench2 (Laurent et al., 2026), LAB-Bench (2024) - cited in LifeSciBench related work
- Judge-bias literature: "Play Favorites: Measuring Self-Bias in
  LLM-as-a-Judge" (2025); "Quantifying and Mitigating Self-Preference Bias
  of LLM Judges" (2026); "Judging the Judges: Bias Mitigation Strategies in
  LLM-as-a-Judge Pipelines" (2026); rubric-generation meta-evaluations
  (2026). arXiv links in the research log.
