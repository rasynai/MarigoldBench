# CORR-013 - the sandbox handed models the machine's API keys

**Date:** 2026-08-19
**Scope:** `run_python` tool sandbox; 26 episode records across four systems.
**Status:** contained in code and data; **key rotation is required and is the
account owner's action.**
**Severity:** highest in this project's history. This is a credential
compromise, not a scoring bug.

## What happened

The `run_python` tool executes model-authored code in the episode workspace. It
called `subprocess.run` without an `env=` argument, so the child inherited the
harness's entire environment - including `ANTHROPIC_API_KEY`,
`OPENAI_API_KEY`, `OPENROUTER_API_KEY` and `NVIDIA_API_KEY`, which
`crucible.llm.load_keys` puts there at start-up.

Models explore their sandbox. Several of them ran the obvious thing:

    import os; print(dict(os.environ))
    print(sorted(os.environ))            # then printed the interesting values

The tool returns stdout to the model, and the harness appends that tool result
to the conversation. So each leaked key was (a) written to the episode record on
disk and (b) sent back to the serving provider as context on the next turn.

Found by the pre-release audit, scanning the staged Hugging Face folder for
credential shapes - roughly one step before the keys would have been published
to the internet.

## Blast radius

26 records contained at least one live key:

| System that received the dump | records | provider that saw it |
|---|---|---|
| gemini | 11 | Google (Vertex AI) |
| gpt | 8 | OpenAI |
| claude | 3 | Anthropic |
| deepseek | 1 | OpenRouter -> DeepSeek |
| (voided grok-or records) | 2 | OpenRouter -> xAI |

Credentials present: **Anthropic** (25 records), **NVIDIA** (25), **OpenAI**
(22), and **OpenRouter** in truncated form. Each dump contained *all* the keys,
not just the key of the provider being called - so, for example, Google and
DeepSeek both received the Anthropic and OpenAI keys.

The xAI inference key and the Hugging Face token were created after these
episodes ran and never entered that environment. Google credentials are
Application Default Credentials in a file, not an environment variable, and did
not appear in any dump.

**These four keys must be treated as compromised and rotated:** Anthropic,
OpenAI, OpenRouter, NVIDIA.

## Why the existing gate missed it

`crucible/leakgate.py` scanned **git-tracked** files. `runs/` is gitignored,
because it holds hundreds of megabytes of episode output. The tree we were
about to publish was therefore the one tree the gate never looked at. "Not
committed" is not "not distributed".

## Fixes

1. **The sandbox gets a minimal environment.** `crucible/lab/tools.py` now
   builds it from an allow-list (`PATH`, `TEMP`, locale, processor count) and
   additionally refuses any variable whose name contains `KEY`, `TOKEN`,
   `SECRET`, `PASSWORD`, `CREDENTIAL`, `AUTH`, `COOKIE`, `SESSION` or
   `PRIVATE` - allow-list plus deny-check, so a future edit that widens the
   allow-list still cannot pass a credential. numpy, pandas, scipy,
   scikit-learn, rdkit, networkx and torch all still import.
2. **The leak gate scans distributed data**, not just tracked files, for eight
   credential shapes.
3. **Tests that fail if either mechanism regresses**
   (`tests/test_credential_containment.py`): a canary key in the environment
   must not appear in sandbox stdout, every claimed pattern must be caught by
   the scanner, and clean text must not trip it.
4. **The 26 records are redacted in place.** Each key is replaced with
   `[REDACTED-<PROVIDER>-KEY-CORR-013]`, 74 values in total. Only characters
   inside transcript text changed: verdicts, checkpoints, tool-call counts,
   token usage and costs are byte-identical, all 4,935 records still parse, and
   the re-verification in `docs/AUDIT.md` §3 was re-run after the redaction.

## What this does not affect

No score, verdict or published statistic. The dumps happened inside episodes
whose grading depends on the submitted artefact, and reading the environment
neither helps nor hinders that. Two of the 26 records belong to the already
voided `grok-or` set.

## Honest note on how close this came

The audit that found it was requested as a publication step, not as security
review. If the release had been assembled and pushed without it - one command
earlier - four live keys would have gone public. The gate that was supposed to
prevent exactly this was pointed at the wrong tree for the whole project.
