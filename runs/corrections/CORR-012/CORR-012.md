# CORR-012 - Grok moved off the gateway at the sponsor's instruction

**Date:** 2026-08-18
**Scope:** campaign lab-1.0.0, system `grok-or` (236 episodes, $31.51).
**Status:** closed, with a second failure recorded below.

## What happened

The xAI key supplied for this run was rejected by `api.x.ai` with `"Incorrect
API key provided"` on every endpoint and both header styles. Reading that as a
dead key, Grok 4.6 was started through OpenRouter instead, and 16 episodes were
collected. The sponsor then corrected the diagnosis: the key is an xAI
**management** key, not an inference key, and instructed that Grok must not run
through OpenRouter at all.

Both halves of that were right. `GET /auth/management-keys/validation` on
`management-api.x.ai` validates the key and returns its team; an inference key
was then minted with `POST /auth/teams/{teamId}/api-keys` and granted
`api-key:endpoint:*` and `api-key:model:*` - a new key has no access to
anything until its ACLs are set, which is why the first minted key still could
not call a model. The key sees twelve models; `grok-4.6` is the newest.

## The stop that did not stop

The first attempt to end the gateway run failed silently and was reported as
successful. The stop was issued as an inline PowerShell one-liner from a
`python -c` string, and the shell quoting turned `$_.TaskName` into
`\$_.TaskName`, so every `schtasks /End` ran against a task name with a leading
backslash and matched nothing. `2>&1 | Out-Null` swallowed the errors, and the
script printed its own success message regardless of what schtasks returned.

The three workers therefore kept running for about four hours and collected
220 further episodes at a cost of **$30.21** - money spent through OpenRouter
on a route the sponsor had just forbidden, and spent outside the $95 ceiling,
which at the time only summed the three systems still in the registry.

Three changes follow:

1. The stop now runs from a **script file**, enumerates the registered tasks,
   issues `/End` and `/Delete` per task, and **prints each return code and the
   list of tasks still present afterwards**. A stop that cannot be verified is
   not a stop.
2. `openrouter_spend` now counts **voided** episodes as well as scored ones, by
   reading `runs/corrections/` for any system in
   `VOIDED_OPENROUTER_SYSTEMS`. Voiding an episode does not refund it.
3. No campaign control command may report success on output it did not check.

## Decision

All 236 `grok-or` episodes are **voided content-blind** and moved to this
directory. The reason is the provider route, which is fixed before any episode
runs and is independent of every outcome: no selection on results occurred, and
the voided set is retained here in full for audit. `grok-or` is removed from
the system registry rather than left as a dormant option, so no shard can
resume it.

Grok is now evaluated on the direct xAI route, on the **full** 990-episode plan
rather than the reduced one, because it no longer competes for the OpenRouter
allowance. That makes it comparable to Claude, GPT and Gemini on pass^3 and on
the sealed seeds, which the three gateway-hosted systems cannot be.

## Effect on published numbers

None on the models' scores: `grok-or` appeared in one intermediate scorecard
build during the four hours it was running and in no published artefact, and
the Grok column of record is the direct xAI run.

The effect on the budget is real and is not written off: $31.51 of the
sponsor's $100 OpenRouter allowance went on episodes that will never be
scored, and the ceiling now carries it, leaving $19.67 of the $95 working
limit rather than the $51 a naive read of the scored files would suggest.
