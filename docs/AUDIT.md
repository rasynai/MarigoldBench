# MarigoldBench — pre-release audit

Every number in this benchmark was recomputed from the recorded episodes by
code written for this audit, not by the code that produced the scorecard. The
audit scripts are `runs/_audit3.py`, `runs/_audit4.py`, `runs/_audit5.py` and
`runs/_reverify_chunk.py`; the integrity and statistics passes are reproduced
below in full, findings included. Four defects were found in our own claims and
are fixed in this release; they are listed first, because an audit that leads
with its clean results is an advertisement.

## 1. Defects found in our own claims

**D1 — the benchmark card claimed six integrity gates; four are enforced.**
The card listed "Naive-path" and "B0 prior-only" in a table headed *"a family
cannot be scored until all pass"*. In fact `runs/gate_families.py`, which
produces the allow-list the campaign reads, enforces B8 reference, B1
degenerate, C0/H1 byte-identical briefs, and answer entropy. Only 3 of 30
families ship a machine-runnable `naive_submission`, and the prior-only figure
(0.00 VEC, 0.09 stage accuracy) was measured on the earlier CRUCIBLE-CHAIN
family set and never re-measured on these 30. The card now separates what a
mechanism enforces from what a person checked once.

**D2 — the intraclass correlation was reported as ~0.26; it is 0.40 here.**
Measured on this campaign's hidden split across all seven systems: ICC = 0.404
over 210 (system × family) groups averaging 19.3 episodes, giving a design
effect of 8.4. A naive Wilson interval on these data is **2.9× too narrow**,
not the ~1.6× that 0.26 would imply. Every published interval is already the
family-clustered one, so no headline changes — but the ≥100-family bar in
GOAL.md is *more* binding than we said, not less.

**D3 — the discriminating band is selected on the same episodes it scores.**
A family joins the band when no system exceeds 80% on it, and the band's
scores are then reported from those same episodes. Split-half test: choosing
the band on a random half and scoring the held-out half moves a system's band
score by between −9.3 and +10.8 points (Grok, the system most often at the
80% ceiling, is the one flattered in-sample). The band remains the right lens
for reading which families carry signal; it is not a clean out-of-sample
estimate, and at 30 families the selection noise is comparable to the gaps
between systems.

**D4 — reasoning effort is not set identically across systems.** `claude` and
`gpt` run with `effort="high"`; `gemini`, `grok`, `deepseek`, `kimi` and `glm`
run with no effort parameter, i.e. each provider's default. The agent loop,
tools, briefs, budgets and verifiers are identical, but this one knob is not,
and it plausibly favours the two systems that have it set. Worth stating that
Grok still finished first *without* it. Not corrected by re-running, because
that would cost roughly what the original campaign cost; recorded as a known
confound instead.

## 2. Data integrity — 4,935 recorded episodes

| Check | Result |
|---|---|
| Duplicate `(system, run_id)` | none |
| Episodes outside the system's plan | 99, all from the two retired families (`lead-opt`, `pose-triage`); excluded from every score, retained on disk for audit |
| Records missing a required field | none |
| Zero-cost or zero-output-token episodes | 0 and 0 — the CORR-008 signature is absent |
| `vec` disagreeing with its own checkpoints | 0 |
| Mislabelled splits | 0 |
| Censored (infrastructure-failed) episodes | 0 across all seven systems |
| Per-family coverage within a system | exactly even (27 hidden episodes per family on the full plan, 9 on the reduced one) |

## 3. Are the scores reproducible?

320 episodes were sampled at random and **re-scored from scratch**: the episode
was rebuilt from its (family, seed, condition), and the recorded submission was
passed to today's verifier.

**279 agreed, 0 disagreed.** The remaining 41 were lost to the host fault of
CORR-011 (two chunk processes died, one `TypeError` inside
`ensemble-disagreement`), not to any disagreement. There is no verifier drift
and no nondeterminism in scoring.

## 4. Can the tasks be solved without doing the work?

- **No answer appears in any brief.** Across 4 readable seeds × 30 families × 3
  conditions (360 instances), no scored value of the reference submission
  occurs verbatim in the text the model reads. Values do appear in the shipped
  CSVs, which is the point — the model must compute over them.
- **The H1 defect always changes the answer.** For all 30 families × 6 seeds
  (180 pairs), the C0 and H1 reference submissions differ on at least one
  scored field. An earlier version of this check compared only numeric fields
  and appeared to flag seven families; comparing every scored field clears all
  of them.
- **No system passes F2 by refusing everything.** F2 is below C0 for every
  system (e.g. Grok 62.6% F2 vs 68.5% C0; GLM 36.7% vs 41.1%), which is the
  signature the three-condition design exists to produce.

## 5. Contamination

Sealed seeds were fixed before the campaign under a salted commitment
(`crucible/commitment.py`). Comparing sealed with hidden performance, where
contamination would show up as hidden being *better*:

| System | hidden | sealed | gap |
|---|---|---|---|
| claude | 57.9% | 57.2% | +0.7 |
| gpt | 58.3% | 58.3% | −0.1 |
| grok | 63.2% | 65.0% | −1.8 |
| gemini | 48.9% | 54.4% | −5.6 |

No system does better on the split it could have seen. The three reduced-plan
systems have no sealed episodes and therefore no contamination reading.

Publishing this benchmark ends the sealed split's forward value: the generators
are deterministic, so anyone who has the code can produce the sealed episodes
and their answers. The commitment file still does its job retrospectively — it
proves these results were not tuned after seeing that split — but a future
release needs newly minted seeds, not these.

## 6. Are the results bound by capability or by the harness?

- **Stop reasons:** 94–100% of episodes end in a submission. No episode in any
  system exhausted `max_turns`.
- **Tool budget:** median tool calls per episode are 6 (claude, gpt), 8 (grok),
  9–13 (the rest) against per-episode budgets up to 40. Nothing is
  budget-starved.
- **No dominant failure checkpoint.** The largest single (family, checkpoint)
  share of all failures is 5.9% (`assay-mechanism/mechanism`), and every one of
  the top eight is failed by 6 or 7 of the 7 systems — the pattern of a hard
  task, not of a broken verifier. A checkpoint failed by one system alone is
  the tripwire that has caught three of our own key errors (`CORRECTIONS.md`).

## 7. Secrets and release hygiene

- `crucible/leakgate.py`: 1,501 git-tracked files, **CLEAN**.
- All 43 commits in the repository's history scanned for Anthropic, OpenAI,
  OpenRouter, xAI, NVIDIA, Hugging Face and Google service-account key
  patterns: **none found**. `.secrets/` has never been tracked.
- Excluded from the public release: the 49 literature PDFs (copyright — our
  own synthesis notes are included), the 394 MB of episode workspaces
  (regenerable from the seeds), and the 66 MB tool-output cache (regenerable
  with a free NVIDIA NIM key).

## 8. What this instrument can and cannot support

It can separate the top group (Grok, GPT, Claude) from the bottom two (GLM,
Kimi) — those intervals do not overlap. It **cannot** rank within the top
group: the family-clustered intervals overlap heavily, which is what an ICC of
0.40 over 30 families buys you. Any statement of the form "model A beats model
B by 5 points on MarigoldBench" is unsupported by this release, including the
ones that would flatter it.
