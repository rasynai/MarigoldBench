# CRUCIBLE 1.0 scorecard - campaign release-1.0.0

Population: 30 generated templates / 10 archetypes; hidden (66) and
sealed (22) instances; conditions: clean (N0), planted hazard (N1),
underidentified (N2). All caveats in docs/LIMITATIONS.md apply;
archetype is the top cluster unit for every interval below.

## Hidden-set reliable completion (first run per instance)

| System | Harness | Hidden overall | N0 clean | N1 hazard | N2 underid. | Sealed | Repeat flip rate |
|---|---|---|---|---|---|---|---|
| anthropic | reference agent | 62/66 | 19/22 | 21/22 | 22/22 | 20/22 | 0/6 |
| marigold | native product | 18/20 | 6/6 | 7/8 | 5/6 | 6/8 | 0/0 |
| openai | reference agent | 63/66 | 21/22 | 21/22 | 21/22 | 20/22 | 1/6 |
| openrouter/deepseek/deepseek-v4-pro | reference agent | 59/66 | 20/22 | 19/22 | 20/22 | 19/22 | 0/6 |
| openrouter/google/gemini-3.7-flash | reference agent | 63/66 | 22/22 | 19/22 | 22/22 | 18/22 | 0/6 |
| openrouter/moonshotai/kimi-k3 | reference agent | 53/66 | 16/22 | 18/22 | 19/22 | 7/10 | 3/6 |
| openrouter/qwen/qwen3.8-max | reference agent | 60/63 | 17/19 | 21/22 | 22/22 | 10/11 | 0/6 |
| openrouter/x-ai/grok-4.6 | reference agent | 52/66 | 20/22 | 15/22 | 17/22 | 15/22 | 2/6 |
| openrouter/z-ai/glm-5.2 | reference agent | 52/66 | 14/22 | 19/22 | 19/22 | 16/22 | 5/6 |

## Cluster-aware intervals (hidden first-run, archetype clusters)
- anthropic: 62/66 (94%; 95% Wilson CI 85%-98%); archetype-cluster bootstrap CI [0.8666666666666667, 1.0] (10 clusters)
- marigold: 18/20 (90%; 95% Wilson CI 70%-97%); archetype-cluster bootstrap CI [0.7916666666666666, 1.0] (10 clusters)
- openai: 63/66 (95%; 95% Wilson CI 87%-98%); archetype-cluster bootstrap CI [0.9047619047619048, 1.0] (10 clusters)
- openrouter/deepseek/deepseek-v4-pro: 59/66 (89%; 95% Wilson CI 80%-95%); archetype-cluster bootstrap CI [0.8133333333333334, 0.9565217391304348] (10 clusters)
- openrouter/google/gemini-3.7-flash: 63/66 (95%; 95% Wilson CI 87%-98%); archetype-cluster bootstrap CI [0.8888888888888888, 1.0] (10 clusters)
- openrouter/moonshotai/kimi-k3: 53/66 (80%; 95% Wilson CI 69%-88%); archetype-cluster bootstrap CI [0.6825396825396826, 0.9027777777777778] (10 clusters)
- openrouter/qwen/qwen3.8-max: 60/63 (95%; 95% Wilson CI 87%-98%); archetype-cluster bootstrap CI [0.8983050847457628, 0.9871794871794872] (10 clusters)
- openrouter/x-ai/grok-4.6: 52/66 (79%; 95% Wilson CI 67%-87%); archetype-cluster bootstrap CI [0.6363636363636364, 0.9365079365079365] (10 clusters)
- openrouter/z-ai/glm-5.2: 52/66 (79%; 95% Wilson CI 67%-87%); archetype-cluster bootstrap CI [0.6666666666666666, 0.8933333333333333] (10 clusters)

## Hidden vs sealed gap (memorization probe)
- anthropic: hidden 62/66 vs sealed 20/22 (gap +3%)
- marigold: hidden 18/20 vs sealed 6/8 (gap +15%)
- openai: hidden 63/66 vs sealed 20/22 (gap +5%)
- openrouter/deepseek/deepseek-v4-pro: hidden 59/66 vs sealed 19/22 (gap +3%)
- openrouter/google/gemini-3.7-flash: hidden 63/66 vs sealed 18/22 (gap +14%)
- openrouter/moonshotai/kimi-k3: hidden 53/66 vs sealed 7/10 (gap +10%)
- openrouter/qwen/qwen3.8-max: hidden 60/63 vs sealed 10/11 (gap +4%)
- openrouter/x-ai/grok-4.6: hidden 52/66 vs sealed 15/22 (gap +11%)
- openrouter/z-ai/glm-5.2: hidden 52/66 vs sealed 16/22 (gap +6%)

## Judge agreement sample (advisory, cross-family)
- anthropic: 5/6 agree (judge: openai)
- marigold: 4/6 agree (judge: anthropic)
- openai: 6/6 agree (judge: anthropic)
- openrouter/deepseek/deepseek-v4-pro: 6/6 agree (judge: anthropic)
- openrouter/google/gemini-3.7-flash: 6/6 agree (judge: anthropic)
- openrouter/moonshotai/kimi-k3: 4/6 agree (judge: anthropic)
- openrouter/qwen/qwen3.8-max: 6/6 agree (judge: anthropic)
- openrouter/x-ai/grok-4.6: 5/6 agree (judge: anthropic)
- openrouter/z-ai/glm-5.2: 5/6 agree (judge: anthropic)

## Cost accounting
- gpt-5.6-sol: 230 calls, 498,543 in / 891,344 out tokens
- claude-opus-5: 332 calls, 1,238,005 in / 3,835,694 out tokens
- z-ai/glm-5.2: 241 calls, 365,409 in / 3,821,463 out tokens
- google/gemini-3.7-flash: 165 calls, 237,988 in / 829,817 out tokens
- x-ai/grok-4.6: 217 calls, 419,793 in / 2,316,293 out tokens
- deepseek/deepseek-v4-pro: 195 calls, 248,985 in / 2,394,334 out tokens
- qwen/qwen3.8-max: 168 calls, 204,783 in / 3,026,954 out tokens
- moonshotai/kimi-k3: 165 calls, 270,903 in / 2,535,588 out tokens
## Corrections applied to this campaign

Read the Marigold row with CORR-006 attached: it is a *native product* row and
its prompt was iterated during the campaign, so it is not comparable to the
API-model rows either causally or temporally.

- **CORR-002**: the original Marigold batch was voided when an unrelated
  co-tenant workload saturated the GPU host and every run died at
  conversation-create. Re-hosted on a second server from the same lockfile and
  re-run; a load guard now refuses to start under contention.
- **CORR-003**: 26 OpenRouter runs voided for billing exhaustion (HTTP 402) and
  DROPPED with reduced denominators (kimi sealed n=10, qwen sealed n=11, qwen
  hidden n=63); 5 Marigold runs voided as harness-terminated and re-run. Both
  decision rules are content-blind.
- **CORR-004**: the deterministic graders were rejecting scientifically correct
  answers over phrasing. Verifier v1.0.3 makes the machine-readable decision
  token authoritative, broadens hazard vocabulary, and accepts instance-specific
  numeric evidence. All 792 stored submissions were rescored identically: 22
  outcomes flipped, every one of them false->true, across 7 of 9 systems.
- **CORR-006**: the Marigold row reflects prompt v3. Under identical grading the
  three versions score 13/28, 25/28 and 24/28; v1 differs from v2/v3 with
  disjoint intervals, driven by clean-data false alarms falling from 8/10 to
  1/10. v2 and v3 are indistinguishable at this sample size.

Full records: runs/corrections/.
