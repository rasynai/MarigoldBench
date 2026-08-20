# CRUCIBLE 1.0 - benchmark card

## What this benchmark measures

Whether a scientific AI agent, given a realistic analytical-chemistry or
ops work order, produces a RELIABLE completion: a defensible number with
working reproduction, a grounded report, correct hazard behavior (flag real
planted problems, invent none on clean tasks), and a correct
report/don't-report decision - scored by a deterministic, non-compensatory
gate. It also probes run-to-run stability, repo-exposure effects
(hidden vs sealed), and (diagnostically) whether completion skill tracks
simulator forecasting/discovery skill.

## Population

30 templates from 10 synthetic archetypes (UV-Vis, qNMR, titration,
kinetics, mass balance, stoichiometry, standard additions, melting point,
log audit, LC internal standard), 3 conditions each (clean / planted hazard
/ underidentified), 104 instances: 16 development (public), 66 hidden test,
22 sealed (git-ignored, excluded from the release package). Two archetypes
(STDADD, MELT) were held out of development entirely (B7 analog). Truth is
computed, machine-verifiable, and never distributed (canary-marked).

## Who was evaluated (campaign release-1.0.0, 2026-08-16)

8 API models in a matched two-call reference agent, plus the Marigold
native product (own 48-tool harness; reported separately, never as a causal
model comparison). 828 preregistered runs; 797 scored after content-blind
corrections (CORR-002/003).

## Headline numbers (hidden set, first run; denominators always attached)

gemini-3.7-flash 63/66; qwen3.8-max 60/63; claude-opus-5 62/66;
gpt-5.6-sol 62/66; deepseek-v4-pro 58/66; grok-4.6 51/66; glm-5.2 50/66;
kimi-k3 49/66; marigold 10/20. Full table with per-condition splits,
cluster bootstrap intervals, sealed rates, and flip rates:
runs/release-1.0.0/scorecard.md.

## What the numbers may be called

"Reliable-completion rate of this agent/product on this generated task
population under this protocol." Nothing else. Prohibited: "discovers",
"safe", "validated co-scientist", "generalizes", "human-level",
"contamination-proof", marketing use.

## Known weaknesses of this benchmark (read before citing)

1. One generator author; 10 archetypes are not independent scientific
   domains. Sealed controls repo exposure only.
2. Model experts play every human role; the simulator is not a laboratory.
3. Criterion validity is an honest null at n=9 systems (completion does not
   demonstrably track forecasting/discovery skill here).
4. The reference agent is a two-call harness; results measure model+harness.
5. Three corrections were needed for infrastructure failures during the
   campaign; all decision rules were content-blind and are published.

Corrections: CORR-001/002/003. Limitations: docs/LIMITATIONS.md.
Preregistration: analysis/preregistrations/campaign-1.0.0.md.
Build manifest with sha256 hashes: release/1.0.0/build_manifest.json.
