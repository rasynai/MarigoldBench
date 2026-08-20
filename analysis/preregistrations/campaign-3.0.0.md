# CRUCIBLE-CHAIN campaign preregistration - 3.0.0

Registered 2026-08-16, before any candidate call against the chain population
(no `runs/release-3.0.0/` outcome file existed at registration). Design basis:
`analysis/crucible3_design.md`; evidence basis: `analysis/literature/README.md`.

## Population

30 model-authored, cross-family-reviewed chain templates across 12 science
areas and 5 workflows. Per template: 4 seeds x 3 conditions = 12 instances,
targeting ~360 chain instances. Conditions: C0 clean control (no defect
exists; asserting one is penalised), H1 planted consequential defect, F2
flawed premise (the requested quantity is not determinable). C0 and H1 prompts
are byte-identical by machine check.

Splits: seed 11 development (truth published), seeds 12-13 hidden test (tasks
public, truth withheld), seed 14 sealed (never published). Cluster unit for all
intervals is the TEMPLATE, because instances within a template share a
generator and are not independent.

## Evaluated subset (fixed before any run)

Running every instance at 3 repeats across 9 systems is ~5,900 calls and does
not fit the sponsor's budget. Repeats are NOT cut, because pass^3 is the one
headline retrying cannot inflate. Instead a deterministic subsample of
instances is evaluated at full repeats:

- 2 hidden instances per template x 3 repeats, plus 1 sealed instance x 1 run
  = 7 runs per template per system (~217 runs per system at 31 templates).
- Which 2 hidden instances is decided by sorted position and a condition
  rotation (H1/F2/C0 cycling by template index), so coverage stays balanced
  across conditions and selection cannot depend on any outcome.
- Every system is evaluated on exactly the same instances.

## Systems

Nine: claude-opus-5 and gpt-5.6-sol (first-party), six OpenRouter flagships
(gemini-3.7-flash, grok-4.6, deepseek-v4-pro, qwen3.8-max, kimi-k3, glm-5.2),
and Marigold as a native product. Harness class is reported with every score:
H0 single-turn no tools for API models, H4 opaque product for Marigold. Cross-
class comparison is descriptive only and never a causal claim about models.

## Primary outcome

**VCC (Verified Chain Completion)**: a run scores 1 only if every stage value
is within its preregistered tolerance AND the decision token is correct. Fully
deterministic; no judge can alter it.

Reported as a monotone ladder, always together, because each alone misleads:

    pass^3  <=  pass@1  <=  pass@3

- **pass^3** (headline): all three independent runs complete the chain, using
  the unbiased estimator E[C(c,k)/C(n,k)]. This is the reliability number and
  is what a retry-until-pass strategy cannot inflate.
- **pass@1**: attempt-level VCC rate, and the calibration guard rail - pass^3
  collapses to a hard zero once pass@1 falls below roughly 8%, and a zero
  there means the benchmark is out of calibration, not that the system scored
  nothing.
- **pass@3**: the retry ceiling, unbiased estimator 1 - C(n-c,k)/C(n,k).

Intervals: cluster bootstrap over TEMPLATES for rates across the population;
Wilson score intervals for individual proportions. The Wald interval is never
used - at these rates it yields zero-width and negative-lower-bound intervals.

## Secondary outcomes (all preregistered, none exploratory)

**Per-stage hazard profile** h_k = P(fail at stage k | reached stage k) with
its survival curve and unnormalized expected depth E[D] = sum_k S_k. This
replaces normalized chain depth (D/K), which is NOT a comparable quantity:
at constant per-stage competence it falls monotonically with chain length
(0.855 at K=2 versus 0.090 at K=100) and moves about +2.7% if a stage is
merely split into two equally hard sub-stages. Our chains vary K from 5 to 8,
so that confound would have been live. D/K is retained only as a
single-instance diagnostic and is never averaged across tasks.

Also: trap rate (stage value matches the decoy within tolerance); notice-act
gap (judge-confirmed naming of the fork minus deterministic correctness on
that stage, H1+F2 only); false-alarm rate on C0; premise-pushback rate on F2;
flip rate across repeats; Brier score with its Murphy decomposition, RMS
calibration error (which equals the square root of the reliability term) and
mean overconfidence; reasoning-quality score from the cross-family rubric
judge (advisory, cannot alter VCC); cost in USD per reliably completed chain.

Runs terminated for reasons unrelated to competence (API error after retries,
context exhaustion) are right-censored in the hazard analysis: they leave the
risk set without counting as a stage failure. They remain failures for VCC.

## Baseline ladder (published beside every headline number)

B0 prior-only (prompt shown, artifacts withheld) - the contamination and
guessability floor; B1 degenerate submissions (empty, refusal, constant) -
must score 0 or the grader is broken; B5 the all-decoy naive path - the
normalised zero; B8 the generator's reference answer - must score ~1.0 or the
grader is broken; B9 adversarial submissions (judge injection, fabricated
evidence quotes, shotgun answers) - must score at floor. B1, B8 and B9 are
integrity gates, not scores: if any fails, the headline is withheld.

## Rules

- No exclusions after outcomes are seen. API failures after retries and
  unparseable submissions are failures, not missing data.
- Judge verdicts are advisory for the reasoning score only and can never
  change VCC, which is fully deterministic.
- The judge must pass its gold-set meta-evaluation BEFORE any campaign
  scoring. See the amendment below for the qualifying criteria actually used
  and why they changed.

## AMENDMENT 1 - judge criteria, registered before any candidate ran

The first meta-evaluation (6 instances, both judges) returned:

| judge | notice recall on reference | false-notice rate on weak | notice on stripped answer |
|---|---|---|---|
| anthropic | 0.775 | 0.025 | 0.000 |
| openai | 0.700 | 0.025 | 0.000 |

Both failed the preregistered recall bar of 0.85, so scoring was blocked and
the cause was investigated rather than the bar lowered to fit.

**Finding.** The recall bar rested on an assumption that turned out to be
false: that a reference answer necessarily *describes* every fork it
navigates. It does not. Model-authored reference answers are terse (roughly
1,000-2,000 characters for a 6-8 stage chain) and frequently compute the
correct value at a fork without narrating the judgment behind it. Every
reference does *mention* each fork's vocabulary, but the judge is instructed -
correctly - not to credit a passing mention as noticing. The judge was right;
the gold label was wrong. A quote-verification artefact was ruled out
separately (all judge quotes survived substring verification on inspection).

**Amended criteria.** The gate now qualifies a judge on the properties whose
labels ARE sound by construction, and treats recall as a measured
characteristic rather than a pass/fail bar:

1. false-notice rate on the weak answer <= 0.25 (the weak answer takes the
   default path silently, so absence of notice is true by construction) -
   both judges achieve 0.025;
2. notice on a stripped answer, with all fork discussion removed, <= 0.15 -
   both judges achieve 0.000;
3. recall on reference answers is REPORTED, not gated.

**Consequence for the headline, stated up front.** Because the judge
under-detects noticing (recall 0.70-0.78 against an imperfect label) while
almost never over-detecting it, every notice rate this benchmark publishes is
a **conservative lower bound**, and the notice-act gap is therefore also a
lower bound: the true gap between seeing a problem and acting on it is at
least as large as reported, never smaller. That direction is the safe one for
the claim being made, and it is stated wherever the gap appears.

**Construction fix for future templates (not applied retroactively).** The
author contract will require reference answers to explain each fork, not only
resolve it, which is what the hand-authored exemplar does. Templates already
built are not regenerated, because changing them after seeing judge results
would be exactly the outcome-dependent editing this protocol forbids.
- Cost guards: CRUCIBLE_MAX_CALLS ledger cap; OpenRouter spend hard-capped at
  USD 100 by CRUCIBLE_OR_BUDGET_USD, metered from per-call cost.
- Every template must pass the machine validity gates and a hostile
  cross-family review before entering the population; failures are logged in
  `runs/chain_build_log/` including rejected attempts.

## Prohibited claims

No human-level, expert-level or superhuman claim of any kind - there is no
human baseline and none is planned. No contamination-proof claim. No causal
comparison between the native product and API models. No claim that a high
score indicates real scientific discovery capability. Scores are interpretable
only against the baseline ladder and only for this task generator, this
harness class and this protocol.

## Stop rules

Sponsor stop; any truth-boundary violation (leak gate non-clean) aborts the
release; cost guard breach aborts the campaign; judge meta-evaluation failure
blocks scoring until the judge protocol is repaired and re-registered.
