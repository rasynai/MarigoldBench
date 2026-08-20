# Limitations and claim boundaries

This file is load-bearing. Every report in this repository points here, and no
result may be quoted without these boundaries attached.

## 0. CRUCIBLE-CHAIN (3.0) - what a score does and does not mean

The chain track reports how often a system completes an ordered chain of
scientific judgment calls in which every stage offers a plausible wrong path.
Six boundaries apply to every number it produces.

**No human baseline exists, and none is planned.** A defensible expert
baseline costs roughly USD 100k-350k and 500-2,500 expert-hours at published
rates. We have not spent it. Scores are therefore bracketed by an automated
ladder - a naive all-decoy path as the floor, the generator's own reference
answer as the ceiling - which bounds the SCALE but says nothing about where a
qualified human would sit on it. **No human-level, expert-level or superhuman
claim of any kind is supported.** The distance between our reference answer
and what a domain expert would produce is unmeasured.

**The tasks are model-authored and model-reviewed.** A frontier model writes
each generator; a model from the other family reviews it adversarially. That
is a real quality gate - it rejects templates - but it is not peer review, and
"reviewed" here means "another model approved it".

**The truth is constructed, which is a genuine strength and a real limit.**
Because a deterministic generator computes every answer from data it generated
itself, our answer-key error rate is structurally near zero - the constraint
that dominates benchmarks whose keys are human-written (published estimates:
~29% wrong in one frontier benchmark's chemistry subset, ~8% invalid in
another, 42% of a third's problems corrected in one revision). The cost is
realism: these are simulated instruments and records, not laboratory output.

**Single-turn, text-only.** No tool use, no execution environment, no images
or binary instrument formats, no multi-turn clarification. Results are
task-level capability under these constraints, not an estimate of what an
agentic system would achieve with tools.

**Archetypes are not independent domains.** Templates share generator authors
and design conventions, so the cluster unit for every interval is the
template, and even that understates dependence across templates written by the
same model family.

**The judges share model families with the candidates.** Judge output is
advisory and cannot alter the primary metric, which is fully deterministic -
but the reasoning-quality score inherits that conflict and is labelled
advisory wherever it appears.

**What may be said:** "system X reliably completed N% of these generated
multi-stage analyses under this protocol." **What may not:** any claim about
real discovery, real laboratories, human comparison, contamination resistance,
or that a native product and an API model differ causally.

## 1. Models stand in for every human role

By sponsor decision (governance/program_charter.md), all roles the CRUCIBLE
guide assigns to humans — interview participants, independent analysts,
adversarial reviewers, judges, scientists in the uplift study — are played by
LLMs: OpenAI `gpt-5.6-sol` and Anthropic `claude-opus-5`. Consequences:

- **The evaluated systems and the expert panels are the same two model
  families.** Cross-family judging and deterministic primary scoring mitigate
  but do not remove this conflict.
- Phase 0 "interviews" are role-played, so the task-population weights are
  provisional policy inputs, **not** evidence about real scientific work.
- Track F measures an effect on **simulated personas**, never on scientists.
- "Expert acceptance" everywhere means "model-panel acceptance".

Replacing these panels with humans is the single highest-value upgrade path.

## 2. Simulator, not laboratory

Tracks D and E run against a hidden synthetic response surface
(`crucible/simlab.py`). Results are **simulator-based experimental design and
forecasting** — the guide's own claim boundary for the SIMULATOR source class.
No real chemical outcome was measured anywhere in this repository.

## 3. Scale

Pilot campaigns (0.2.0, 0.3.0): five instances, ranking hypotheses only.
Ship 1.0: 30 generated templates / 10 synthetic archetypes / 104 instances,
9 systems, 828 preregistered runs with repeats. This supports cluster-aware
reliable-completion estimates **for this task generator and this protocol**;
archetypes share one generator author, so the 10 "clusters" are not
independent scientific domains.

## 4. Contamination status

Holdout levels populated: B0-B2 plus B7-analog archetypes (STDADD, MELT held
out of development). The sealed split (tasks_sealed/, git-ignored, excluded
from the release build) probes repo-level exposure only: every instance
shares the generator author and one machine. **No contamination-proof or
contamination-resistant generalization claim is permitted.** The exposure
ledger (registry/exposure_ledger.json) records this per instance.

## 4b. Shared-infrastructure hazards (observed, now guarded)

Two incidents during 1.0 established that the harness must defend against its
own environment: a co-tenant workload saturated the Marigold GPU server and
voided a batch (CORR-002; load-guard added, product re-hosted on a second
server from the same lockfile), and OpenRouter credit exhaustion voided 26
tail runs (CORR-003; finalize now refuses to publish over 402 rows). Marigold
1.0 results were produced on an aarch64 host - same product source, config,
and API-side model routing as the original x86 host.

## 4c. Deterministic-grader brittleness (observed, corrected, residual)

CORR-004: the pattern-based graders initially rejected semantically correct
answers over phrasing (negated prose, synonym vocabulary, numeric-evidence
descriptions, and MELT's confirmed/not-confirmed framing). Verifier v1.0.3
makes the machine-readable decision token authoritative, broadens hazard
vocabulary, and accepts instance-specific numeric evidence of the planted
defect; every stored submission was rescored identically (22 flips, all
false->true, 7 of 9 systems affected). Residual: keyword matching can still
miss exotic phrasings, and accepted-conclusion sets do not cover every
defensible answer (observed once: recalculate-with-corrected-parameter);
such answers rely on the escalation path rather than silent credit. Scores
should be read with this one-sided residual risk in mind.

## 5. Infrastructure shortcuts

- Re-execution runs model-written Python locally with a timeout and isolated
  temp dir, but no container/VM sandbox and no network egress proxy.
- The agent has no tool loop; it works in at most two model calls (draft +
  one verification-gated repair), so results measure that specific harness.
- Judges see truncated file contents (8k chars/file).

## 6. What the numbers may be called

Permitted: "reliable-completion rate of this reference agent on these
instances under this protocol", "simulated-persona uplift estimate",
"simulator discovery ladder", "verification-gate effect in this agent,
native-cost".

Prohibited: "discovers", "safe", "validated co-scientist", "generalizes",
"human-level", any claim about real scientists or laboratories, and any use
of these scores in marketing.
