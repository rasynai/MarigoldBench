# CRUCIBLE ship 1.0 - sponsor signoff

Date: 2026-08-16. Campaign: release-1.0.0 (preregistered in
analysis/preregistrations/campaign-1.0.0.md before any run).

## What was run

- Population: 30 generated templates / 10 synthetic archetypes / 104
  instances (16 development, 66 hidden, 22 sealed in git-ignored
  tasks_sealed/). Conditions per template: N0 clean, N1 planted hazard,
  N2 underidentified. Card text is byte-identical across conditions
  (regression-tested) so no wording leaks the condition.
- Systems: 8 API reference agents (claude-opus-5, gpt-5.6-sol, and 6
  OpenRouter flagships) at 100 planned runs each (hidden + sealed + 3x
  repeats on 6 instances); Marigold native product on a seeded 28-run
  subset. 828 planned runs; 797 scored after corrections (below).
- Scoring: deterministic non-compensatory reliable-completion gate;
  cross-family judge sample advisory only.

## Headline results (runs/release-1.0.0/scorecard.md)

- Hidden-set reliable completion: gemini-3.7-flash 63/66 (95%),
  qwen3.8-max 60/63 (95%), claude-opus-5 62/66 (94%), gpt-5.6-sol 62/66
  (94%), deepseek-v4-pro 58/66 (88%), grok-4.6 51/66 (77%), glm-5.2 50/66
  (76%), kimi-k3 49/66 (74%). Marigold (native product, not causally
  comparable): 10/20 (50%).
- Condition profile: N2 underidentified tasks are nearly solved by the top
  tier (abstaining is easy when signalled); N1 hazard detection and N0
  clean-task false alarms separate systems. glm/kimi lose most of their
  deficit on clean-task false alarms - inventing problems, not missing them.
- Hidden vs sealed: gaps of +3% to +14% across API systems (n=22 sealed;
  kimi n=10, qwen n=11 after CORR-003). No large repo-exposure signal;
  marigold +12% on n=8 is uninformative at this size.
- Repeat stability: 12 flips across 54 repeated (system, instance) pairs;
  glm-5.2 flipped 5/6 - its rate estimates carry real run-to-run noise.
- Judge agreement (advisory): 47/54 overall; disagreements concentrate in
  weaker systems' submissions.
- Criterion validity (release/1.0.0/criterion_validity.json): Spearman of
  hidden RCR vs Track D Brier = +0.25 (expected negative), vs discovery
  hits = +0.08. At n=9 this is an honest null: task completion does NOT
  demonstrably track simulator forecasting/discovery skill. Reported as a
  limitation, not buried.

## Corrections

- CORR-001 (0.2.0): verifier pointer-syntax fix, rescored, 2 cells flipped.
- CORR-002: marigold batch voided for host saturation by a co-tenant
  workload; product re-hosted from the same lockfile and re-run; load guard
  added to the adapter.
- CORR-003: 26 OpenRouter runs voided for billing exhaustion (402) and
  dropped with reduced denominators (content-blind; a preregistration
  deviation weakening kimi/qwen sealed cells to n=10/11); 5 marigold runs
  voided as harness-terminated and re-run. 402 guard added to finalize.

## Claim boundaries

Everything in docs/LIMITATIONS.md applies: model panels are not humans, the
task generator has one author (archetype clusters are not independent
domains), the simulator is not a laboratory, sealed means repo-level
exposure control only, and no discovery/safety/human-uplift claim about the
real world is supported. Release package: release/1.0.0/ with sha256
manifest and truth-marker leak scan (clean).

Signed: automated release manager on behalf of sponsor Ansh Tiwari.
