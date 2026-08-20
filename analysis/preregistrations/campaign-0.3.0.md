# CRUCIBLE campaign preregistration - 0.3.0 (Marigold + frontier models)

- Campaign ID: release-0.3.0
- Registered: 2026-08-15, before any campaign model call (enforced by the
  restartable-stage design; no stage file existed at registration).
- Sponsor: Ansh Tiwari. Directive: "benchmark marigold and all the frontier
  models" on the user's two servers plus OpenRouter.

## Systems (frozen)

| System | Harness | Access |
|---|---|---|
| marigold | NATIVE PRODUCT: its own 48-tool agent spec, model routing (base gpt-5.6-sol), tier policy, condenser, critic, on the user's GPU server (129.213.93.18, core :8012) | conversation API, mode N1 autonomous, NeverConfirm, 25-min budget/task |
| google/gemini-3.7-flash | matched two-call reference agent (draft + one verification-gated repair) | OpenRouter |
| x-ai/grok-4.6 | same | OpenRouter |
| deepseek/deepseek-v4-pro | same | OpenRouter |
| qwen/qwen3.8-max | same | OpenRouter |
| moonshotai/kimi-k3 | same | OpenRouter |
| z-ai/glm-5.2 | same | OpenRouter |

Reference rows from campaign 0.2.0 (same tasks, same reference agent):
claude-opus-5 and gpt-5.6-sol.

## Primary claim (permitted)

Per-system reliable-completion counts on the five frozen task instances (the
0.2.0 set, unchanged), with denominators. Marigold is a product row: its
result must never be read as a model-vs-model causal comparison against the
reference-agent rows (guide 23.17), and reference-agent rows must not be read
as each lab's best product.

## Prohibited interpretations

All prohibitions from campaign 0.2.0, plus: no "Marigold beats/loses to model
X" claims (different harness, tools, compute); no lab-level generalization
from one flagship model; no cross-campaign trend claims.

## Secondary outcomes

Track D forecasts and Track E proposal ladders for every new system (simulator,
one call each); judge verdicts (anthropic judge, advisory); failure notes.

## Analysis

Counts with denominators; failures classified (gate leaf vs integrity vs
product-produced-no-submission). No exclusions after outcomes are seen; a
model API that errors after retries is recorded as a failed run, not dropped.

## Stop rules

Sponsor stop; truth-boundary violation aborts; a Marigold task is bounded at
25 minutes wall-clock and then interrupted and scored on what it exported.
