# CRUCIBLE campaign release-0.3.0 - sponsor signoff

Date: 2026-08-16. Scope: 6 OpenRouter frontier flagships (reference agent) +
Marigold (native product) on the 5-instance pilot task set; Tracks D and E on
the simulator. Preregistration: analysis/preregistrations/campaign-0.3.0.md.

## Headline results (runs/release-0.3.0/scorecard.md)

- Reference agent, 5 tasks: gemini-3.7-flash 5/5 and qwen3.8-max 5/5 match
  claude-opus-5 (0.2.0); kimi-k3 3/5; deepseek-v4-pro, grok-4.6, glm-5.2 2/5.
  Dominant failure: false alarms on clean tasks (hazards.no_false_alarm) -
  weaker models invent problems rather than miss them.
- Marigold (native product; NOT causally comparable to API rows): 0/5 on the
  non-compensatory gate - clean-task false alarms, missing/failed
  reproduction scripts, one wrong reportability call, one grounding failure -
  while the advisory judge passed 5/5 of its submissions. The gate-vs-judge
  gap is the finding: the product writes convincing reports that do not
  withstand mechanical verification.
- Track D forecasting: deepseek best (Brier 0.065); marigold (0.165) and
  qwen (0.170) worse than the base-rate baseline (0.161).
- Track E discovery: no arm achieved a confirmed positive (ladder is honest:
  the simulator's hidden effects were not found by any system); calibration
  Brier best for qwen 0.015; baselines 0.022.

## Corrections applied

- CORR-002 (runs/corrections/CORR-002/CORR-002.md): every original Marigold
  run failed at conversation-create because an unrelated co-tenant workload
  saturated the GPU server (load >445, MCP tool-listing timeout). Those runs
  were voided as evaluation-infrastructure failures - the product never
  received a work order - and re-run on the sponsor's second server
  (same source, same lockfile, same pinned agent config; smoke-verified).
  Prevention: the adapter now refuses to start runs when host load > 24.
  No other rows were touched; the decision rule is content-blind (create-time
  MCP timeout = void) so no outcome-dependent selection was possible.

## Claim boundaries (unchanged)

Pilot scale (5 instances) supports ranking hypotheses only, not capability
claims; archetype coverage is 3 templates. The 1.0 campaign (104 instances,
30 templates, 10 archetypes, hidden + sealed splits) is the load-bearing
evaluation. No contamination-proof claim; no human-scientist claim.

Signed: automated release manager on behalf of sponsor Ansh Tiwari.
