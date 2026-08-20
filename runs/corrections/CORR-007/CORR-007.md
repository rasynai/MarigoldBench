# CORR-007 - six systems unevaluated in campaign 3.0.0: OpenRouter credit exhausted

Date: 2026-08-16 (UTC). Scope: campaign release-3.0.0 (CRUCIBLE-CHAIN).

## What happened

The chain campaign launched nine systems. The OpenRouter account had been
exhausted before the campaign began (credits API: 300.50 used of 300.00
granted), so all six OpenRouter-hosted systems returned HTTP 402 on every
call and produced no scientific output at all:

| System | Runs attempted | Runs that reached the model |
|---|---|---|
| gemini-3.7-flash | 56 | 0 |
| grok-4.6 | 56 | 0 |
| deepseek-v4-pro | 56 | 0 |
| qwen3.8-max | 56 | 0 |
| kimi-k3 | 56 | 0 |
| glm-5.2 | 56 | 0 |

336 outcome files were written and have all been voided to
`runs/corrections/CORR-007/outcomes/`. The decision rule is the same
content-blind one used in CORR-003: an outcome whose only integrity problem is
a provider billing refusal is not evidence about the system, because the
system never received the work order. No other outcome was touched, and no
outcome-dependent selection is possible, since every voided run failed
identically before any task content was processed.

## Consequence for the scorecard

Campaign 3.0.0 evaluates **two** systems (claude-opus-5 and gpt-5.6-sol) on
the chain track, not nine. The six OpenRouter systems are reported as
**not evaluated**, not as scoring zero. Any table that lists them must show
"not evaluated - CORR-007" rather than a number or a blank, because a blank
invites the reader to infer failure.

This does not affect campaign 1.0.0, where all nine systems were evaluated on
the deterministic anchor track and the two affected systems there were handled
under CORR-003 with reduced denominators.

## Resolution

Blocked on the sponsor topping up OpenRouter credits. When credits exist, the
campaign is restartable with no rework: workers skip any run that already has
an outcome file, so relaunching evaluates exactly the six missing systems.
The voided files are retained rather than deleted so the gap is auditable.

## Prevention

`crucible/llm.py` already enforces a spend ceiling
(`CRUCIBLE_OR_BUDGET_USD`, default USD 100) computed from the per-call cost
OpenRouter reports. That guard protects against overspending; it cannot detect
a balance of zero before the first call. The campaign launcher should query
the credits endpoint and refuse to start OpenRouter workers on a zero balance,
which would have turned 336 wasted runs into one clear message.
