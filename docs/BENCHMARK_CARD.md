# MarigoldBench — benchmark card

**What it measures.** Whether a model can be handed a real computational
drug-discovery / ML laboratory it has never seen, choose the right tools in the
right order, recover from their genuine failure modes, and produce a result
that survives an independent physical and statistical check — or correctly
refuse when the task as posed cannot be done.

**What it does not measure.** Knowledge recall, literature familiarity, or
wet-lab judgment. No human baseline exists and none is planned; read every
score against the baseline ladder, never against a claim about people.

## Design in one page

| Property | Choice | Why |
|---|---|---|
| Unit of evaluation | **Episode**: brief + workspace + tool belt + step budget | The model plans and acts; a single-turn answer cannot test tool use |
| Primary metric | **Verified Episode Completion (VEC)** — every checkpoint AND the final result correct | Non-compensatory; partial credit hides which judgment failed |
| Headline statistic | **pass^3** (all three independent runs succeed) | Retrying cannot inflate it. Agent benchmarks measure 0%→30% purely from retries |
| Verification | The harness **recomputes** every physical/statistical claim from the submitted artifact | A tool's own confidence is not truth; self-report is never evidence |
| Truth source | Deterministic generators fabricate the data and therefore know every answer | Keeps label error structurally near zero. The most-cited MCQ benchmark has ~6.5% wrong answers; an audited chem/bio slice of another has ~29% |
| Conditions | **C0** sound (false alarms penalised) · **H1** planted defect that changes the answer · **F2** flawed premise where documented refusal is the only correct outcome | Separates capability from caution. A system that answers everything and one that refuses everything can share a VEC |
| Condition symmetry | C0 and H1 briefs byte-identical; workspace *shape* matched (same filenames, columns, rows, precision) | If the condition is readable from the files, no science is required to detect it |
| Uncertainty | Family-clustered bootstrap interval on every headline | Episodes within a family share a generator and are not independent evidence. Clustered intervals here run ~3x the naive width |
| Harness | ONE frozen loop for every candidate; contract text is a module constant | A scaffold change has been measured flipping the ranking of two models |
| Contamination | Fresh instances minted per epoch from private seeds; salted pre-campaign commitment published | Chemistry agents score ~100% pre-cutoff and ~0% post-cutoff — contamination is the dominant confound in this domain |

## The laboratory the model is given

Hosted (free tier, probed live before inclusion): **RFdiffusion** (backbone
design), **ProteinMPNN** (inverse folding), **ESMFold** and **OpenFold2**
(structure prediction), **Boltz-2** (co-folding + affinity), **DiffDock**
(docking), **MolMIM** (property-guided optimisation), **GenMol** (generative
chemistry). Local: **RDKit**, **PyTorch**, **scikit-learn**, **scipy**,
**pandas**, and a sandboxed Python environment where the model computes and
trains its own models.

Tools fail for real, and their errors are returned verbatim: recovering from a
genuine service failure is part of the science being measured.

## Integrity gates

Mechanically enforced on every family before it may be scored, by
`runs/gate_families.py`, which produces the allow-list the campaign reads.
A family that fails any of these is absent from the scorecard:

| Rung | Requirement |
|---|---|
| B8 reference | The family's own reference submission completes it, on all 18 instances |
| B1 degenerate | An empty submission fails every instance — **silence is never a refusal** |
| Condition symmetry | C0 and H1 briefs byte-identical per seed |
| Answer entropy | No scored field constant across the population, judged across all six seeds |

Checked, but NOT enforced by that gate — stated separately because an
integrity claim should say which mechanism backs it:

| Check | Status |
|---|---|
| H1 changes the answer | Verified for all 30 families × 6 seeds: the C0 and H1 reference submissions differ on at least one scored field in every case (`docs/AUDIT.md` §4) |
| No giveaway in the brief | Verified: no scored value appears verbatim in any brief (`docs/AUDIT.md` §4). The authoring-time scanner in `runs/validate_families.py` also checks for method verbs and decoy hints, but it is not the gate of record |
| Naive-path fails on H1 | Enforced at authoring time and re-checked per family by hand; only 3 of 30 families ship a machine-runnable `naive_submission`, so this is NOT a mechanical gate for the other 27 |
| B0 prior-only craters | Measured once (0.00 VEC, 0.09 stage accuracy) on the earlier CRUCIBLE-CHAIN family set, NOT re-measured on these 30 families |

Infrastructure failures are quarantined, never scored. A harness crash is not
a measurement of a model — we learned that by briefly recording 22 of our own.

## The systems evaluated

Two tiers, and the difference between them is coverage, not method: every
system meets the same briefs, the same tool belt, the same step budget and the
same verifiers, inside one frozen agent loop.

| System | Model | Route | Episodes | Carries pass^3 |
|---|---|---|---|---|
| claude | claude-opus-5 | Anthropic direct | 990 | yes |
| gpt | gpt-5.6-sol | OpenAI Responses API | 990 | yes |
| gemini | gemini-3.1-pro-preview | Vertex AI (`location=global`) | 990 | yes |
| grok | grok-4.6 | xAI direct | 990 | yes |
| deepseek | deepseek-v4-pro | OpenRouter | 270 | no |
| kimi | kimi-k2-thinking | OpenRouter | 270 | no |
| glm | glm-4.7 | OpenRouter | 270 | no |

The three gateway-hosted systems run the hidden-test seeds at one attempt each
instead of three, because the whole OpenRouter allowance for them together is
$100. That is the split the headline is computed on, so pass@1 is comparable;
pass^3 and the sealed-seed contamination reading simply do not exist for them,
and are printed as `-` rather than as a number.

## Known limitations

See `docs/LIMITATIONS.md`. The short list: no human baseline; the authors
evaluate their own benchmark; scale is below the ≥100-family bar the
literature sets and is being raised; some families are deliberately easy and
act as a low-difficulty anchor band rather than headline evidence.

## Corrections

Every material error in construction, scoring or conduct is published in
`CORRECTIONS.md`, including the ones that cost money and the one where a
verifier penalised a correct answer for being thorough. An instrument that
claims near-zero label error has to audit itself in public.

## Reproducing

`docs/REPLICATION.md`. The development split runs end to end from one command.
Tool calls are cached and replayed, so scoring never depends on a live
service and two systems making the same call see identical bytes.
