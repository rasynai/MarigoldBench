# CRUCIBLE frontier scorecard - campaign release-0.3.0

Native product row (marigold) and API-model rows are NOT causally
comparable (guide 23.17): marigold runs its own 48-tool agentic
harness on the user's GPU server; API models run the matched two-call
reference agent. All caveats in docs/LIMITATIONS.md apply; judge
verdicts are advisory (anthropic judge, 91% gold-set accuracy).

## Reliable completion by system (5 task instances)

| System | Harness | Overall | Track A (2) | Track C (2) | Track H (1) | Judge PASS |
|---|---|---|---|---|---|---|
| deepseek/deepseek-v4-pro | reference agent | 2/5 | 1/2 | 1/2 | 0/1 | 4/5 |
| google/gemini-3.7-flash | reference agent | 5/5 | 2/2 | 2/2 | 1/1 | 5/5 |
| marigold | native product | 0/5 | 0/2 | 0/2 | 0/1 | 5/5 |
| moonshotai/kimi-k3 | reference agent | 3/5 | 0/2 | 2/2 | 1/1 | 4/5 |
| qwen/qwen3.8-max | reference agent | 5/5 | 2/2 | 2/2 | 1/1 | 5/5 |
| x-ai/grok-4.6 | reference agent | 2/5 | 0/2 | 2/2 | 0/1 | 5/5 |
| z-ai/glm-5.2 | reference agent | 2/5 | 0/2 | 2/2 | 0/1 | 4/5 |

Campaign 0.2.0 reference (same tasks, same reference agent, post-CORR-001):
claude-opus-5 5/5, gpt-5.6-sol 4/5 - see runs/release-0.2.0/scorecard.md.

## Per-system failure notes
- deepseek/deepseek-v4-pro / N0-s103: ['reproducibility.clean_rerun']
- deepseek/deepseek-v4-pro / N2-s104: ['decision.reportability']
- deepseek/deepseek-v4-pro / S1-s201: ['grounding.report_artifact_consistency']
- marigold / N0-s101: ['hazards.no_false_alarm']
- marigold / N1-s102: ['reproducibility.clean_rerun']
- marigold / N0-s103: ['hazards.no_false_alarm', 'reproducibility.clean_rerun']
- marigold / N2-s104: ['decision.reportability']
- marigold / S1-s201: ['grounding.report_artifact_consistency']
- moonshotai/kimi-k3 / N0-s101: ['agent produced no parseable submission after retries']
- moonshotai/kimi-k3 / N0-s103: ['hazards.no_false_alarm']
- x-ai/grok-4.6 / N0-s101: ["claims.json: claims/1: Additional properties are not allowed ('qualifications' was unexpected)"]
- x-ai/grok-4.6 / N0-s103: ['hazards.no_false_alarm']
- x-ai/grok-4.6 / S1-s201: ['grounding.report_artifact_consistency']
- z-ai/glm-5.2 / N0-s101: ['hazards.no_false_alarm']
- z-ai/glm-5.2 / N0-s103: ['hazards.no_false_alarm']
- z-ai/glm-5.2 / S1-s201: ['grounding.report_artifact_consistency']

## Track D - simulator forecasting (Brier, lower is better)
- openrouter/deepseek/deepseek-v4-pro: 0.065
- openrouter/z-ai/glm-5.2: 0.098
- openrouter/moonshotai/kimi-k3: 0.104
- openrouter/x-ai/grok-4.6: 0.105
- openrouter/google/gemini-3.7-flash: 0.152
- base_rate_baseline: 0.161
- marigold: 0.165
- openrouter/qwen/qwen3.8-max: 0.170
- nearest_disclosed_heuristic: 0.180

## Track E - simulator discovery ladder
- openrouter/google/gemini-3.7-flash: generated 8, eligible 8, tested 8, primary+ 0, confirmed+ 0; Brier 0.151
- openrouter/x-ai/grok-4.6: generated 8, eligible 8, tested 8, primary+ 0, confirmed+ 0; Brier 0.046
- openrouter/deepseek/deepseek-v4-pro: generated 8, eligible 8, tested 8, primary+ 0, confirmed+ 0; Brier 0.125
- openrouter/qwen/qwen3.8-max: generated 8, eligible 8, tested 8, primary+ 0, confirmed+ 0; Brier 0.015
- openrouter/moonshotai/kimi-k3: generated 8, eligible 8, tested 8, primary+ 0, confirmed+ 0; Brier 0.098
- openrouter/z-ai/glm-5.2: generated 8, eligible 8, tested 8, primary+ 0, confirmed+ 0; Brier 0.069
- marigold: generated 8, eligible 8, tested 8, primary+ 0, confirmed+ 0; Brier 0.090
- baseline_random: generated 8, eligible 8, tested 8, primary+ 0, confirmed+ 0; Brier 0.022
- baseline_grid: generated 6, eligible 6, tested 6, primary+ 0, confirmed+ 0; Brier 0.022

## Cost accounting (local ledger; marigold's own spend is on its server)
- gpt-5.6-sol: 192 calls, 275,643 in / 539,107 out tokens
- claude-opus-5: 204 calls, 660,327 in / 2,241,622 out tokens
- z-ai/glm-5.2: 196 calls, 289,366 in / 3,112,082 out tokens
- google/gemini-3.7-flash: 165 calls, 237,988 in / 829,817 out tokens
- x-ai/grok-4.6: 165 calls, 315,474 in / 1,692,200 out tokens
- deepseek/deepseek-v4-pro: 136 calls, 173,980 in / 1,674,968 out tokens
- qwen/qwen3.8-max: 98 calls, 113,716 in / 1,517,285 out tokens
- moonshotai/kimi-k3: 82 calls, 124,077 in / 1,321,284 out tokens