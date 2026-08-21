---
license: apache-2.0
pretty_name: MarigoldBench
language:
  - en
tags:
  - agents
  - benchmark
  - drug-discovery
  - computational-biology
  - scientific-reasoning
  - tool-use
  - evaluation
task_categories:
  - other
size_categories:
  - 1K<n<10K
configs:
  - config_name: episodes
    data_files: episodes/*/*.json
---

# MarigoldBench

**A model is given a working computational drug-discovery laboratory and
measured on whether it drives that lab to a defensible result.**

Structure prediction, protein design, docking, generative chemistry, RDKit and
a Python sandbox. Eleven tools, a step budget, a brief, and a deterministic
verifier that **recomputes every physical and statistical claim from the
submitted artefact**. Nothing the model says about its own work is taken as
evidence.

Seven frontier systems, 4,923 recorded episodes, every transcript published.

## Headline result

VEC (Verified Episode Completion) on the hidden split. Non-compensatory: every
checkpoint of an episode must pass, or the episode scores zero.

| System | n | VEC pass@1 | family-clustered 95% CI | pass^3 | cost |
|---|---|---|---|---|---|

| gpt-5.6-sol | 810 | 58.3% | [46.2, 70.1] | 49.6% | $113 |
| claude-opus-5 | 810 | 57.9% | [45.2, 70.1] | 45.9% | $1,171 |
| deepseek-v4-pro | 270 | 51.1% | [40.0, 61.5] | – | $15 |
| gemini-3.1-pro-preview | 810 | 48.9% | [39.1, 58.5] | 32.6% | $240 |
| glm-4.7 | 270 | 31.9% | [23.0, 40.7] | – | $10 |
| kimi-k2-thinking | 270 | 29.6% | [20.0, 40.0] | – | $19 |

![Verified Episode Completion, seven systems](figures/fig01_headline.png)

On the 15 **discriminating** families — those where no system exceeds 80% —
every system falls between 15.6% and 38.5%.

**Corrected on 2026-08-20.** Reading the transcripts found three defects in
this benchmark, not in the models: an unisolated tool sandbox (CORR-014), a
checkpoint that scored a ruled-out explanation as a claim (CORR-015), and a
submit handler that dropped 73 of one model's answers and none of another's
(CORR-016). Everything is re-scored, 12 contaminated episodes are voided, and
Claude moved from 57.9 to 61.0 percent, which changes the order of second and
third place. `docs/AUDIT.md` §9 has the detail.

**Read the intervals, not the ranking.** Episodes inside a family share a
generator; the measured intraclass correlation is 0.40, giving a design effect
of 8.4, so a naive binomial interval on these data is **2.9× too narrow**. This
release can separate the top group from the bottom two. It **cannot** rank
Grok, GPT and Claude against each other, and we do not claim it can.

## Figures

Drawn from `runs/_figdata.json`, recomputed from the episode records, so no
figure can show a number the data does not. Regenerate with
`python harness/_figures_house.py`.

**Refusal calibration.** Half of these tasks are sound and the model must not
raise a false alarm; the other half cannot be answered and it has to say so and
show why. A model that refused everything would score higher on the
unanswerable ones. None of the seven does.

![Refusal calibration](figures/fig02_refusal.png)

**Defect detection.** A real flaw that changes the answer, in a task worded
identically to its clean version, so the prompt gives nothing away.

![Defect detection](figures/fig03_defect.png)

**Accuracy by difficulty.** The 30 task types split into a hard half, where
nobody clears 80 percent, and an easier half that any single overall score
averages in.

![Accuracy by difficulty](figures/fig04_hard.png)

**Reliability.** Every task ran three times; pass^3 counts only the ones right
on all three. The three reduced-plan systems ran one attempt and are absent
rather than shown as zero.

![Reliability](figures/fig05_reliability.png)

**Accuracy vs cost.** Real API spend divided by how often the model was right,
so failing cheaply does not read as cheap.

![Accuracy against cost](figures/fig06_cost_accuracy.png)

**Hardest task types.** What the single best model of the seven managed on each
of the 15 hard ones.

![Hardest task types](figures/fig07_hardest.png)

## Why this benchmark is built the way it is

**The answer key cannot be wrong.** Deterministic generators fabricate the
data and therefore know every answer. At single-digit-to-middling pass rates,
label error is the binding constraint on every other benchmark in the field —
published estimates run from ~8% invalid to ~29% wrong — and here it is
structurally near zero.

**Three conditions per family, and two of them are byte-identical.**

- **C0 — sound.** The reported concern is a false alarm. Raising one is scored
  as a failure.
- **H1 — planted defect.** A real defect that *changes the answer*. Verified
  for all 30 families × 6 seeds: the C0 and H1 reference answers differ on at
  least one scored field.
- **F2 — flawed premise.** The question cannot be answered as asked. A
  documented refusal with an **explicit impossibility witness** is the only
  correct outcome; silence scores zero.

C0 and H1 briefs are byte-identical per seed, so the condition cannot be read
off the prompt. No system passes F2 by refusing everything — F2 is below C0 for
all seven.

**Anti-saturation is enforced, not hoped for.** An earlier version of this
benchmark saturated at 94–100% because briefs printed method recipes and answer
menus. That failure is published in full ([CORR-010](corrections/CORR-010.md)),
and the giveaway classes it identified are now rejected mechanically. No scored
value appears verbatim in any brief.

## What is in this repository

| Path | Contents |
|---|---|
| `episodes/<system>/` | 4,758 scored episode records — brief, full tool-call transcript, submission, per-checkpoint verdict, token usage, cost |
| `episodes_retired/` | 165 records from two families retired before this release; kept for audit, **excluded from every score** |
| `episodes_voided/` | 236 records voided under [CORR-012](corrections/CORR-012.md), so a correction can be checked rather than believed |
| `crucible/lab/fam/` | The 30 family generators and verifiers — the answer keys themselves |
| `crucible/lab/` | The frozen agent loop, the 11-tool belt, the campaign runner, the scorer |
| `harness/` | The gate that decides which families may be scored, the launcher, the stop-condition checker, the audit scripts |
| `docs/AUDIT.md` | Pre-release audit, **including four defects found in our own claims** |
| `CORRECTIONS.md` | Every material error in construction, scoring or conduct, newest first |
| `results/scorecard.md` | The full scorecard: by condition, by family, by difficulty tier |

## Read the audit first

[`docs/AUDIT.md`](docs/AUDIT.md) recomputes every published number with code
written for the audit rather than the code that produced it, and it leads with
what it found wrong with us:

- the benchmark card advertised six integrity gates; four are mechanically
  enforced;
- the intraclass correlation was quoted as 0.26 and is 0.40 here;
- the discriminating band is selected on the same episodes it scores
  (split-half optimism −9.3 to +10.8 points);
- reasoning effort is set to `high` for Claude and GPT and left at each
  provider's default for the other five — one knob that is not frozen, and it
  favours the two that have it. Grok still finished first without it.

Verified clean: 279 of 279 re-scored episodes reproduce their recorded verdict;
no duplicates, no zero-cost records, no episode whose verdict disagrees with
its own checkpoints, no censored episodes; no sealed-vs-hidden contamination
signal.

## Known limitations

Read [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) in full. The ones that would
change how you use these numbers:

1. **Scale.** 30 families, against the ≥100 our own literature review argues
   for. This is stated as unmet, not quietly dropped.
2. **The authors evaluate their own benchmark.** There is no human baseline.
3. **Three systems ran a reduced plan.** DeepSeek, Kimi and GLM ran 270 hidden
   episodes rather than 990, because $100 was the entire gateway budget for the
   three of them. Comparable pass@1; no pass^3, no contamination reading.
4. **The evaluation host randomly faults.** Segfaults and corrupted live
   objects in allocation-heavy CPython, reproducible with 25 lines of
   dependency-free Python ([CORR-011](corrections/CORR-011.md)). Recorded
   outcomes are unaffected — a dead process writes no file — but replicate on
   hardware that passes a memory test.
5. **Publishing this ends the sealed split's forward value.** The generators
   are deterministic, so anyone with this repository can produce the sealed
   episodes and their answers. The commitment file in `results/` still proves
   retrospectively that these results were not tuned after seeing that split. A
   future release needs new seeds.

## Reproducing

```bash
pip install -e .                  # Python >= 3.11
python harness/gate_families.py   # must print 30/30 before anything is scored
python -m crucible.lab.scorecard  # rebuild results/scorecard.md from episodes/
```

Running new episodes needs provider credentials and a free NVIDIA NIM key for
the structural-biology tools. `docs/REPLICATION.md` has the versions. The
393 MB of episode workspaces and the 66 MB tool-output cache are not shipped:
both regenerate from the seeds.

## Security note

The tool sandbox in this release runs model-authored code with an allow-listed
environment. It did not always: models that printed `os.environ` read the
harness's provider keys, which went into 26 transcripts and back to four
providers as context. Found by this audit one command before publication, fixed,
tested, and written up in [CORR-013](corrections/CORR-013.md). If you build an
agent harness, pass `env=` to your sandbox.

## Citation

```bibtex
@misc{marigoldbench-2026,
  title  = {MarigoldBench: verified episode completion for agentic
            computational drug discovery},
  year   = {2026},
  note   = {30 task families, 3 conditions, 7 frontier systems,
            4{,}935 published episodes},
  url    = {https://huggingface.co/datasets/rasynai/MarigoldBench}
}
```

Licensed Apache-2.0. The literature PDFs used in the design review are not
redistributed; the synthesis notes in `analysis/` are ours.
