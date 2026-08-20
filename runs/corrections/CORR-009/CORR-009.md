# CORR-009 - campaign 3.0.0 lineup restricted to frontier systems

Date: 2026-08-16 (UTC). Scope: campaign release-3.0.0 (CRUCIBLE-CHAIN).

## Decision

The evaluated lineup is restricted to frontier-class systems. `google/gemma-4-31b-it`
is removed, and the three other reachable-but-not-frontier NVIDIA NIM models
(`meta/llama-3.1-70b-instruct`, `nvidia/llama-3.3-nemotron-super-49b-v1`,
`nvidia/llama-3.3-nemotron-super-49b-v1.5`) are not added.

Final lineup (5 systems):

| System | Provider |
|---|---|
| claude-opus-5 | Anthropic (first-party) |
| gpt-5.6-sol | OpenAI (first-party) |
| nvidia/nemotron-3-ultra-550b-a55b | NVIDIA NIM |
| nvidia/nemotron-3-super-120b-a12b | NVIDIA NIM |
| deepseek-ai/deepseek-v4-flash-0731 | NVIDIA NIM |

## Why this is a design decision, not a result-dependent one

CRUCIBLE-CHAIN is non-compensatory: a run scores only if every stage of a 5-8
stage chain and the final decision are correct. Difficulty compounds as p^K.
A system that fails an early stage for reasons of raw capability - it cannot
hold the artifacts in working memory, or cannot carry an intermediate number
through four steps - produces a floor score that is uninformative about
scientific judgment, which is the construct the benchmark claims to measure.
The hazard profile for such a system is a spike at h_1 and nothing after it,
which is not a measurement of anything the benchmark is for.

The exclusion rule is stated in capability terms fixed before scoring and does
not reference any outcome:

> A system is evaluated on the chain track if it is the current flagship of a
> distinct training lineage and is reachable by the account. Prior-generation
> and mid-tier variants of an included lineage are excluded.

**Timing.** 13 Gemma-4 outcome files existed when this decision was taken.
They were not read, scored, or aggregated before the decision; the trigger was
the sponsor's instruction to benchmark frontier systems only, not any Gemma
result. Nonetheless, because outcomes existed, this is recorded as a
correction rather than as a silent config edit. The files are retained at
`runs/excluded-nonfrontier/` so the exclusion is auditable, and they are
outside the directory the scorecard loads.

## The right home for weak models

Excluding weak models from the frontier scorecard does not make them
uninteresting. The informative experiment is the harness-uplift one: run a
weak model *inside* Marigold and ask whether scaffolding moves it toward
frontier accuracy. That is a within-system contrast where the weak model is
the control and its floor score is the point, not a confound. CORR-006 already
established the effect exists at the anchor-track level (Marigold 13/28 ->
24/28 under identical grading, driven by false alarms falling 8/10 -> 1/10).
It is tracked as future work, not as part of the 3.0.0 scorecard.

## Provider access, for the record

Five distinct NVIDIA NIM API keys were recovered from disk and probed with
live completions (`runs/probe_nim_keys.py`). All five resolve to the same
entitlement: 102 models listed, 6 large models actually reachable. Frontier
models absent from every key include `moonshotai/kimi-k2.6`,
`openai/gpt-oss-120b`, `mistralai/mistral-large-2-instruct`,
`meta/llama-3.3-70b-instruct` and `nvidia/llama-3.1-nemotron-ultra-253b-v1`
(HTTP 404 "not found for account"). No additional lineage is obtainable on
this account, so the NIM contribution is capped at three systems regardless of
which key is used. Combined with CORR-007 (OpenRouter credit exhausted), the
3.0.0 chain track evaluates five systems, not the nine originally planned.

## Related

- CORR-006 - Marigold false-alarm mechanism and the v2/v3 harness fixes
- CORR-007 - six OpenRouter systems unevaluated, credit exhausted
- CORR-008 - spend guard summed a `cost_usd` field that was never recorded
