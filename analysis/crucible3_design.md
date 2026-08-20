# CRUCIBLE 3.0 — design specification

**Working title:** CRUCIBLE-CHAIN — *verified multi-stage scientific inference under
attractive error*.

Date: 2026-08-16. Status: design frozen for implementation. Evidence base:
`analysis/literature/` (23 benchmarks + judge-methodology papers read in full).

---

## 1. The one-sentence claim we want the benchmark to license

> "System X completes N% of realistic multi-stage scientific analyses in which
> every stage offers a plausible wrong path, and its stated confidence tracks
> its actual correctness."

Nothing weaker (knowledge recall, single-answer accuracy, style-graded prose)
and nothing stronger (real discovery, wet-lab impact).

## 2. What the field already does, and the hole we fill

| Benchmark | Open-ended? | Verifiable truth? | Multi-stage traps? | Reliability? | False-alarm control? | Judge validated? |
|---|---|---|---|---|---|---|
| GPQA / HLE | no (MCQ/short) | yes (key) | no | no | no | n/a |
| LifeSciBench | **yes** | partial (expert rubric) | implicit | no | no | spot-check |
| GeneBench-Pro | partial (JSON fields) | **yes (simulated)** | **yes (forks)** | 10 attempts | no | n/a (deterministic) |
| HealthBench | **yes** | no (physician rubric) | no | worst-at-k | negative criteria | **yes (F1 vs MDs)** |
| PaperBench | **yes** | partial | no | no | no | **yes (JudgeEval)** |
| BixBench / DiscoveryBench | yes | partial | no | no | no | **no** |
| RE-Bench | yes | yes (objective metric) | no | best-of-k | no | n/a |
| **CRUCIBLE-CHAIN** | **yes** | **yes (generated)** | **yes, scored per fork** | **pass^k + flips** | **yes, symmetric clean controls** | **yes, gold-set F1 + dual-judge κ** |

The hole: **nobody scores the *path*, only the destination.** GeneBench-Pro
named the decisive failure mode — the *noticing-to-acting gap* — and then
admitted its own binary grading "discards stage-level diagnostic information"
(their stated future work). We build exactly that instrument, in the open, with
false-alarm controls and reliability that no science benchmark currently has.

## 3. Hardness mechanism (why frontier scores will be single-digit)

Hardness is **constructed, not selected**. We never filter tasks by "models got
it wrong" — Humanity's Last Exam did that without verification and ~29% of its
bio/chem answers turned out wrong, because adversarial filtering enriches for
bad answer keys. Instead:

1. **Ordered inferential chains.** Each instance is K = 5–8 sequential stages.
   Stage k's correct input is stage k−1's correct output. No compensation:
   the headline metric requires *all* stages.
2. **An attractive wrong path at every fork.** Each stage ships a *decoy* — the
   value a competent-but-hasty analyst produces (uncorrected drift, unweighted
   regression, unstratified estimate, substituting LOD/2 for censored values).
   The decoy is the *default* answer; the correct value requires noticing a
   condition in the artifacts.
3. **Programmatic trap separation (ablation guarantee).** The generator must
   emit, per stage, `correct`, `decoy`, `tol`, and the build gate enforces
   `|decoy − correct| ≥ 3·tol`. This is GeneBench-Pro's ablation validation made
   mechanical: a plausible-but-wrong analysis provably fails by a clear margin,
   so "close enough" never scores.
4. **Compounding.** With per-stage correctness p, chain completion ≈ p^K.
   Even a strong p = 0.75 over K = 7 yields ≈ 13%; p = 0.65 yields ≈ 5%.
   Single-digit headline numbers fall out of the structure, not of trickery.
5. **Three conditions per instance, symmetric wording.**
   `C0` clean (no defect; inventing one is penalized),
   `H1` planted defect (must be noticed *and* acted on),
   `F2` flawed premise (the request itself is unsatisfiable/misspecified;
   complying is the failure). C0 and H1 prompts are byte-identical.
6. **No shortcut to the answer.** Truth files never ship to the candidate; the
   final numeric answer is not derivable from any single artifact field; the
   generator is required to make the endpoint depend on ≥2 stages.

## 4. Scoring system (deliberately not "percent of a rubric")

Per run, the candidate returns prose **plus** a final JSON block with one field
per stage, a decision token, and a **confidence in [0,1] per stage**.

**Primary metric — VCC (Verified Chain Completion).**
`VCC = 1` iff every stage value is within tolerance of `correct` *and* the
decision token matches. Reported as a rate with cluster-bootstrap CIs
(cluster = template, because instances within a template are correlated).

**Secondary metrics.**

| Metric | Definition | What it isolates |
|---|---|---|
| Chain depth `D` | index of first failed stage / K, mean over runs | partial progress (survival curve reportable) |
| Trap rate `T` | P(any stage value within tol of its decoy) | *seduction* by the plausible path vs. random error |
| Notice–Act gap `G` | P(judge finds the fork named in prose) − P(stage acted correctly) | the GeneBench-Pro failure mode, measured |
| False-alarm `FA` | on C0 only: P(asserts a defect that does not exist) | the symmetric error; keeps "flag everything" from scoring |
| Premise pushback `PB` | on F2 only: P(refuses/redesigns instead of complying) | over-compliance |
| Reliability `pass^k` | P(all k independent runs complete the chain) | run-to-run stability (HealthBench worst-at-k logic, stricter) |
| Calibration `Brier`, `ECE` | over per-stage (confidence, correctness) pairs | knowing what it doesn't know |
| RQS | LLM-rubric score 0–100 on method/uncertainty/communication | open-ended quality that determinism can't see |
| `$/VCC` | campaign cost ÷ completed chains | practical utility |

**Baseline ladder (no humans — disclosed, and bracketed instead).**
`B0` prompt-only, artifacts withheld (guessability floor — DiscoveryBench's
NoDataGuess control); `B1` all-decoy path (what the naive analysis scores by
construction); `B2` single-fork-corrected; `B3` generator reference solution
(ceiling = 1.0 by construction). Any system scoring near B1 is doing the naive
analysis; near B0 means the artifacts are not being used at all.

## 5. Judging (the part v1 got wrong)

Deterministic anchors do the stage checking. LLM judges score only what
determinism cannot see (method soundness, uncertainty handling, communication,
and whether a fork was *named*). Every mitigation below is adopted because a
2025–26 paper measured it working:

- **criterion-level binary verdicts**, never a holistic score (−31.5% self-preference bias);
- **≤8 criteria per judge call** (batching many criteria over long outputs costs up to −35 pts accuracy);
- **verbatim evidence quote required and substring-verified** against the answer (blocks hallucinated credit);
- **style normalization before judging** (markdown bias up to +0.76 vs position bias ≤0.04);
- **reference-guided**: judge sees the truth block and reference answer (error 70% → 15%);
- **cross-family judge of record**, self-family never grades itself;
- **gold-set meta-evaluation before any campaign scoring** (macro-F1 vs known-intent labels, HealthBench's protocol) + **dual-judged audit slice with κ**;
- judges are *advisory for RQS only* — they can never change VCC.

## 6. Validity gates a template must pass before it enters the benchmark

1. structural: K∈[5,8]; every stage has correct/decoy/tol; `|decoy−correct| ≥ 3·tol`; endpoint depends on ≥2 stages;
2. symmetry: C0 and H1 prompts byte-identical; no meta-vocabulary anywhere agent-visible;
3. determinism: generator re-run 3× byte-identical; stdlib only; sandboxed;
4. solvability: reference answer scores VCC=1; weak answer scores VCC=0 and trips ≥1 decoy;
5. non-guessability: B0 (prompt-only) run scores below chance-equivalent threshold;
6. cross-family hostile review approves (question–rubric consistency, ambition, factual soundness, leakage, answerability);
7. shortcut red-team: an adversarial agent given the artifacts must not reach the endpoint without doing the analysis (CORE-Bench's exploits were found only *after* saturation — we look first).

## 6b. Yield, and why we did not raise it

Roughly a third to a half of authored templates survive. The dominant rejection
is the reviewer refusing to certify key correctness - it independently
recomputes the chain and rejects when its arithmetic disagrees or when the
stated method does not determine the answer uniquely.

That bar is deliberately not relaxed, for the reason the whole design rests on:
at single-digit pass rates the benchmark's own error rate is the binding
constraint, and every published attempt to buy scale by loosening verification
has paid for it (one frontier benchmark shipped ~29% wrong answers in its
chemistry subset precisely because reviewers were told not to spend more than
five minutes checking). A smaller suite of verified chains is worth more than a
larger one of unverified ones.

The honest consequence for reporting: **templates, not instances, are the unit
of independent signal.** Instances within a template share a generator and are
strongly correlated, so every interval clusters on the template and the
template count is reported next to the instance count everywhere. Raising
instances-per-seed is cheap and improves contamination resistance, but it does
NOT buy statistical power, and this document does not pretend otherwise.

## 7. Scale and release

~30 chain templates × 3 conditions × ~4 seeds ≈ 360 open-ended chain instances,
plus the 104 v1 deterministic instances retained as the anchor track ≈ 460 items.
Tiered release (FrontierMath/GeneBench-Pro lesson): public development split
with full truth; hidden test split (tasks public, truth withheld); sealed split
never published, used to detect leakage; generator code published *after* the
first campaign with fresh seeds reserved. Funding, authorship, and the fact
that the same model families author, judge, and are evaluated are disclosed in
the benchmark card — the entanglement the FrontierMath episode punished.

## 8. Known validity limits (stated up front, not in an appendix)

Model-authored tasks reviewed by models, not humans; simulated artifacts, not
instruments; text-only (no images/binary formats); one generator author per
template so archetypes are correlated; no measured human baseline (bracketed by
the ladder instead); judges share families with candidates.
