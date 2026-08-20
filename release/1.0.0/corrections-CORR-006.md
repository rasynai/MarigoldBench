# CORR-006 - Marigold prompt iteration v1 -> v2 -> v3, and what it shows

Date: 2026-08-16. Scope: the Marigold native-product row of campaign
release-1.0.0. This is a correction record because the published scorecard row
changed; it is also the most useful result the 1.0 campaign produced.

## What happened

The 1.0 scorecard originally reported Marigold at 10/20 hidden instances. Two
separate things were wrong with that number, and they pulled in opposite
directions:

1. **The grader was rejecting correct science** (CORR-004). Marigold phrases
   answers in natural prose, so it was penalised more than any other system by
   pattern-matching graders. Fixing the graders and rescoring every stored
   submission from every system moved 22 outcomes, 11 of them Marigold's.
2. **The product really was over-flagging.** Once graded fairly, the dominant
   failure was unambiguous: on clean data with no defect present, Marigold
   asserted a fabricated problem in 8 of 10 cases.

## The three versions, scored identically

All three runs use the same 28 instances, the same verifier (v1.0.3), and the
same host. Only the product's system prompt differs. Runs that died on
infrastructure (host contention, SSH termination, billing) are excluded under
CORR-002/003 and re-run, not scored.

| Version | Overall | 95% CI | N0 clean | N1 defect | N2 underid. | False alarms | Missed defects |
|---|---|---|---|---|---|---|---|
| v1 original | 13/28 (46%) | [30%, 64%] | 2/10 | 5/12 | 6/6 | **8/10** | 3/12 |
| v2 "don't invent problems" | 25/28 (89%) | [73%, 96%] | 9/10 | 10/12 | 6/6 | 1/10 | 1/12 |
| v3 balanced procedure | 24/28 (86%) | [69%, 94%] | 8/10 | 11/12 | 5/6 | 1/10 | **0/12** |

## What this licenses, and what it does not

**Supported.** v1 differs from both v2 and v3: the intervals are disjoint, and
the mechanism is identified rather than inferred - the gain comes almost
entirely from the false-alarm rate falling from 8/10 to 1/10 on clean data.
The instruction change that produced it was a single rule: report a problem
only when you can name the record and the rule it violates; routine
incompleteness is a limitation, not a defect.

**Not supported.** v2 and v3 are indistinguishable at this sample size (24 vs
25 of 28 is one task, and the intervals overlap almost entirely). We do NOT
claim v3 is better overall. What v3 does show is the cleanest error profile of
the three - zero missed defects while holding false alarms at the floor -
which is the behaviour a laboratory would want, but at n=12 hazard instances
that is a direction, not a finding.

## Why it matters beyond this product

The v1 -> v2 step is a worked example of the failure this benchmark exists to
measure. A system that flags everything looks careful and scores terribly; a
system that flags nothing looks calm and is dangerous. Only an evaluation with
symmetric controls - planted defects AND clean data where the correct answer is
"nothing is wrong" - can tell the two apart. A benchmark without clean controls
would have rewarded v1's over-flagging as diligence, and a benchmark without
planted defects would have rewarded an over-corrected v2 as calm competence.

It is also a caution about our own instrument: the same iteration that
improved the product by 40 points was initially invisible, because the grader
was mismeasuring the product's phrasing. The grader was fixed first, and only
then was the product change measurable.
