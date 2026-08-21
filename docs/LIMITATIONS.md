# MarigoldBench — limitations

Written to be quotable against us. Anything a hostile reviewer would raise
should already be here; if it is not, that is a defect in this document.

## 1. Limitations the design cannot fix

**No human baseline, and none is planned.** Every score must be read against
the baseline ladder (reference / degenerate / naive-path / prior-only), never
against a claim about what a scientist would do. We do not know the human
number. Benchmarks that do have one paid for it: one comparable effort ran
~$95/hr expert time and still reached only ~74% answer objectivity.

**The authors evaluate their own benchmark.** No independent party has run it,
audited the keys, or attempted to break it. The mitigations are structural
(published corrections, cryptographic pre-commitment to sealed splits, full
transcripts) but none of them substitutes for external replication.

**Solo authorship.** Task families were authored and reviewed inside one
pipeline. Cross-family adversarial review is automated, not independent.

**Predictive validity is unestablished.** We can show a model fails to notice
that a docking pose is physically impossible. We cannot show that this
predicts anything about its usefulness in a real programme. No correlation
with downstream outcomes has been measured.

## 2. Limitations of the current release

**Scale is below the bar we set ourselves.** The literature (and our own
measured intraclass correlation, now 0.40 on this campaign's hidden split, up
from the 0.26 measured on the earlier chain track) implies ≥100 independent
families
before between-model claims are safe. We are at 30 gate-clean families with
more in authoring. Until that number is reached, family-clustered intervals
are wide — deliberately reported as such — and close rankings should not be
believed. The naive Wilson interval is printed beside the clustered one only
to show how much narrower a dishonest analysis would look.

**Some families are too easy and are not headline evidence.** Several families
run at >90% for frontier systems. They are retained as a low-difficulty anchor
band, because a benchmark with no easy items cannot distinguish "hard" from
"broken", but they inflate the aggregate. Read the per-family table, not the
aggregate.

**Gemini is 3.1 Pro *preview*.** A preview model may change under the same
name. The endpoint and date are recorded with the run; the result is not
guaranteed reproducible against a later revision of that name.

**Two retired families are excluded from every column.** `lead-opt` and
`pose-triage` predate the hardening gates and survive on disk from pilot runs.
Two systems have them and a third does not, so scoring them would compare
systems on different family sets; the scorecard reads only the gated
allow-list.

**The gateway tier is measured on a reduced plan.** Grok 4.6, DeepSeek V4 Pro
and Kimi K2 Thinking are evaluated on the hidden-test seeds at one attempt per
instance (270 episodes each) rather than the full 990. That is the split the
headline is computed on, so pass@1 stays comparable, but two things cannot be
read for them: pass^3, which needs three attempts per instance, and the
contamination check, which needs the sealed seeds. The reason is budget - the
sponsor's OpenRouter allowance is $100 total for all of them together - and it
is a coverage limitation, not a modelling choice.

**Grok is measured through OpenRouter, not xAI.** The key we were given is
rejected by api.x.ai, so the provider in the record is a gateway. A gateway can
route to a different serving configuration than the first-party API; the
result is a measurement of Grok 4.6 as served by that route.

**One provider's tools underpin every hosted call.** The structural-biology
tools are all on one free tier. If that tier changes, the benchmark's cost
model and possibly its results change. Tool outputs are cached, so past runs
remain reproducible, but new instances are exposed.

**AlphaFold2 is excluded** because it timed out on probe. A tool that fails
intermittently is a harness confound rather than a science test, but excluding
it narrows the tool belt.

**The evaluation host randomly faults.** Allocation-heavy CPython processes on
this machine segfault at a rate that drifts between roughly 5% and 90% over
hours, and occasionally corrupt a live object instead of dying (a `zip` where a
dict belongs). It is not our code: a 25-line pure-Python reproducer with no
repository code in it triggers it, on two different interpreters, with no
native library loaded. Recorded outcomes are unaffected, because a dead process
writes no file and a corrupted one raises and is quarantined rather than
scored. What cannot be excluded is a corruption inside a verifier that fails to
raise and returns a wrong verdict that looks ordinary. We have no evidence of
that, and it is the largest unquantified threat to label accuracy in this
release. Replicate on hardware that passes a memory test. See CORR-011.

**The tool sandbox was not isolated during the recorded campaign.** Model
authored code ran with the harness's environment, network and filesystem, and
371 of 4,935 episodes used it: 111 hit an external service, 42 used one of our
provider keys, and one read the grader source for its own task. Twelve
answer-capable episodes are voided and the rest are tagged in the published data
so anyone can exclude them. The sandbox is closed now, and
`tests/test_sandbox_containment.py` keeps it closed, but the numbers in this
release were collected before that. See CORR-014.

**Two task types were scored wrongly for every system until 2026-08-20.** Both
read model prose by substring and treated a ruled-out explanation as a claim, so
`assay-mechanism` failed 51 of 53 sound-condition episodes while the answers were
correct. Everything is re-scored under one shared, tested matcher, and each
record keeps its previous verdict, but any figure quoted from this benchmark
before that date is wrong for those two families. See CORR-015.

**Claude's numbers were depressed by our own parser.** 73 of its episodes
recorded a submission and stored nothing, against zero for GPT, because it put
its result object in the wrong argument and we read only one. 50 recovered, 27
verdicts changed. A harness that parses one model more strictly than another is
not a frozen loop, and we did not notice for a whole campaign. See CORR-016.

## 3. Threats to validity we actively monitor

**Wrong keys.** The dominant risk in constructed-truth benchmarks: a generator
and a verifier that share one wrong scientific assumption agree perfectly and
are both wrong. Three of our own wrong keys have already been found and fixed
by the rule that two frontier families converging on a non-key answer triggers
a key audit. There are probably more. Every check that can be recomputed from
the observable is, rather than re-deriving the generator's own parameter.

**Verifiers that punish good answers.** Found and fixed twice: a check that
required naming exactly one criterion failed a correct answer for also
mentioning the constraint it satisfied, and a text matcher read "quenching,
*not* inhibition" as claiming inhibition. Both were caught by auditing
implausible score gaps between frontier systems rather than by belief.

**Scaffolding confounds.** One frozen agent loop, no retries, no planning
scaffold, no tool-choice hints. If the harness ever helps, the number stops
being about the model.

**Saturation.** Preregistered numeric triggers with deadlines in
`docs/SATURATION_POLICY.md`. The precedent for enforcing them is our own
CORR-010: an earlier track measured 94-100%, the headline was withheld, and
the numbers were published only inside a correction.

**Contamination.** Structural rather than honour-system: fresh instances per
epoch from private seeds, salted commitment published before scoring, sealed
split never published in any form. The hidden-vs-sealed gap is reported as the
contamination signal.

## 4. What would change our minds

- An external party reproducing the development split and disagreeing with a
  key. We would publish the disagreement and the fix.
- A family where two frontier systems converge on the same non-key answer:
  that is evidence about our key, not their capability, until proven otherwise.
- A demonstration that episode success correlates with nothing downstream,
  which would undercut the whole construct.
