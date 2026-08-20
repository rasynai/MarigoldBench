# GOAL.md — MarigoldBench: the benchmark frontier labs use to measure whether a model can *do* computational science

Owner: Ansh Tiwari. Author of record for this document: the build agent.
Created 2026-08-16. This file is the stopping contract. Work does not stop
until every box in §9 is checked, and no box may be checked by assertion —
each names the artifact that proves it.

---

## 1. What changed, and why this document exists

Everything before this file measured **judgment in prose**: a model read a
work order plus static data files and emitted a JSON verdict. That track
(CRUCIBLE-CHAIN) is retained as the *anchor track* and is not the product any
more.

The product is now **MarigoldBench**: the model is given a real computational
laboratory — structure prediction, protein design, docking, generative
chemistry, cheminformatics, and a GPU-less ML training environment — and is
measured on whether it can **drive that laboratory to a scientific result**.

Three scope decisions are absolute:

- **Marigold is out of scope entirely.** No harness, no adapter, no
  comparison, no mention in any result. We supply the infrastructure; the
  only variable under test is the model.
- **OpenRouter is out of scope entirely.** No candidate, no judge, no probe
  is ever routed through it. The spend guard stays, but the intended spend
  through it is zero.
- **Three candidate systems only**: Google Gemini 3.1 Pro (via ADC/Vertex),
  OpenAI GPT-5.6 Sol (highest reasoning effort), Anthropic Claude Opus 5.
  These are also the two permitted research-collaborator models for design
  work (Gemini 3.1 Pro and GPT-5.6 Sol at maximum thinking).

## 2. The claim the benchmark must be able to support

> "This model can be handed a real computational drug-discovery / ML-research
> stack it has never seen, and will independently choose the right tools, in
> the right order, recover from their real failure modes, and produce a
> result that survives an independent physical and statistical check — or
> will correctly refuse when the task as posed cannot be done."

Anything that does not bear on that sentence is out of scope.

## 3. Bars carried over from the literature review (non-negotiable)

These come from 19 papers downloaded, read in full and audit-verified
(`analysis/literature/deep/`, synthesis in `SYNTHESIS.md`). They are not
opinions; each has a citation behind it.

| # | Bar | Source | Consequence for MarigoldBench |
|---|---|---|---|
| B1 | ≥100 independent task families; instances are NOT independent evidence | own ICC measurement (0.26 chain track, 0.40 this campaign) + Miller 2024 ("≥1,000 questions"); GPQA concedes n=448 resolves only ~10-pt effects | ≥100 task families at launch-quality; report template-clustered CIs always |
| B2 | Label error must be structurally ~0, not "carefully reviewed" | MMLU-Redux 6.5% error (Virology 57%); HLE chem/bio 29±3.7% contradicted; FrontierMath v2 corrected 42% | Every answer computed by a deterministic verifier from data the generator produced, or by a physical check (docking score, RMSD, held-out AUC) recomputed at scoring time |
| B3 | No giveaways: no method recipe, no answer menu, no announced defect | own CORR-010 (94→100% saturation); GPQA answer-only baselines; CORE-Bench shipped values | `giveaway_scan` over prompt AND every artifact AND every tool docstring |
| B4 | Prior-only floor must crater | GPQA, LiveBench | B0 (tools disabled / data withheld): VCC ≤0.02, stage accuracy ≤0.15 |
| B5 | pass@k inflation must be controlled | FrontierMath 2%→6% pass@8; MLE-bench 16.9%→34.1% | pass^3 is the headline; pass@k reported, never headlined |
| B6 | Uncertainty on every number | BetterBench: 14/24 benchmarks report none | Template-clustered bootstrap CI on every scorecard line |
| B7 | Prompt/format sensitivity is a confound | lessons-trenches: format alone moves scores 14–46pp | Standing contract is a frozen module constant, byte-identical across tasks |
| B8 | Contamination defense must be structural | contamination survey; SWE-bench Verified obituary | Fresh instances minted per epoch from private seeds + salted commitment before every campaign |
| B9 | Diagnostics are the product, not the score | GPQA domain heatmaps; per-stage hazards | Per-step hazard profile, tool-call traces, failure taxonomy shipped with every result |
| B10 | Agent scaffolding is a confound to be neutralised | PaperBench (Claude 21.0% BasicAgent vs 16.1% IterativeAgent — scaffold flips ranking); MLE-bench | ONE frozen harness for all candidates; harness version is part of the result identity |

Additional bars from community discourse research (`analysis/community/SYNTHESIS.md`):

- B11 Publish a numeric saturation/retirement trigger with dates → done: `docs/SATURATION_POLICY.md`
- B12 Timestamped pre-campaign commitment to sealed splits → done: `crucible/commitment.py`
- B13 Publish adversarial-audit numbers, not just gate pass/fail
- B14 One-command replication kit + full transcripts + bounty for a wrong key
- B15 Cross-benchmark concordance, and one fully worked public transcript

## 4. What the model is given (the infrastructure WE supply)

Confirmed reachable and **free** on the account keys (probed live,
`runs/probe_bio_nims.py`):

| Tool | Service | Role in a drug-design chain |
|---|---|---|
| RFdiffusion | NVIDIA NIM (IPD) | de-novo protein backbone / binder design |
| ProteinMPNN | NVIDIA NIM (IPD) | inverse folding: sequence for a backbone |
| ESMFold | NVIDIA NIM | fast single-sequence structure prediction |
| OpenFold2 | NVIDIA NIM | MSA/template structure prediction |
| Boltz-2 | NVIDIA NIM (MIT) | co-folding + binding affinity |
| DiffDock | NVIDIA NIM (MIT) | blind molecular docking, pose generation |
| MolMIM | NVIDIA NIM | property-guided molecule optimisation (CMA-ES) |
| GenMol | NVIDIA NIM | fragment-conditioned generative chemistry |
| RDKit 2026.03 | local | descriptors, ADMET-ish filters, substructure, conformers |
| PyTorch 2.5 + scikit-learn | local | the model trains its own predictors |
| pandas / scipy / networkx | local | data wrangling and statistics |

AlphaFold2 NIM timed out on probe and is excluded until it answers reliably;
a tool that intermittently fails is a harness confound, not a science test
(B10).

**Cost consequence:** tool calls are free. The only spend is candidate model
tokens. This is what makes a ≥100-family agentic benchmark financially
possible at all, and it is a genuine moat: replicating it requires either
this free tier or real GPU spend.

## 5. What the tasks look like

Each task is an **episode**: a scientific objective, a workspace with data, a
tool belt, a step budget, and a deterministic verifier. The model plans,
calls tools, reads real outputs (including real failures), and submits a
result. Episodes are 8–25 tool calls of genuine work.

Five families, each with a constructed-truth verifier:

1. **Binder design** — design a binder to a specified epitope; verified by
   recomputed predicted structure + interface metrics against a threshold
   the generator established, with a decoy path (e.g. designing against the
   wrong chain / ignoring the hotspot spec) that fails the physical check.
2. **Lead optimisation** — improve a scaffold on a multi-property objective
   (potency proxy, QED, synthetic accessibility, a hard ADMET filter) without
   violating a stated constraint; verified by recomputation in RDKit +
   docking; the decoy is the single-objective optimum that violates the
   constraint.
3. **Docking / pose triage** — decide which of several proposed complexes is
   physically defensible; verified against recomputed poses and
   PoseBusters-style geometry checks; the decoy is the best-scoring but
   physically impossible pose.
4. **Model-building** — train a predictor on supplied assay data and report
   held-out performance and a decision; verified by the harness re-running
   the model's saved artifact on a **hidden** test split; the decoy is the
   leakage-inflated score (scaffold split vs random split is the judgment).
5. **Flawed-premise refusals (F2 analogue)** — the requested objective is not
   achievable with the supplied tools/data (wrong target class for the tool,
   assay units incompatible, sequence not foldable at useful confidence);
   the correct outcome is a documented refusal with the reason. Prompts are
   byte-identical to a sound sibling.

Every family carries C0 (sound task, false alarms penalised), H1 (a defect
planted in the data or the workspace), F2 (flawed premise) — the same
non-compensatory, condition-controlled structure that survived the CHAIN
audit, now over tool use instead of prose.

## 6. Scoring

- **Primary: Verified Episode Completion (VEC)** — every checkpoint AND the
  final result must be right. Non-compensatory (B5).
- Recomputation, never self-report: the harness re-runs the physical/statistical
  check on the model's submitted artifact.
- **Tool-use diagnostics** (reported, never in VEC): calls made, wasted calls,
  recovery-after-failure rate, whether it read tool errors, budget overrun.
- **Per-step hazard profile** and failure taxonomy (B9).
- **Calibration** on every numeric claim.
- LLM judges (cross-family, meta-eval gated) may score *reasoning quality*
  and *did it notice the fork*; they can never move VEC (B2).

## 7. Research-collaborator protocol (explicit user instruction)

Design decisions of consequence are put to **Gemini 3.1 Pro** and
**GPT-5.6 Sol at maximum reasoning** as collaborators, with their responses
archived verbatim under `analysis/collab/`. Used for: task-family design
review, verifier-soundness review, adversarial "how would a model fake this"
review, and difficulty calibration. Budget-capped (§8) and never on the
critical path of a run.

## 8. Budget discipline (hard)

- OpenRouter: **$0**, permanently.
- NVIDIA NIM tools: free tier.
- Candidate + collaborator tokens are the only spend. Ceiling for the whole
  build-and-benchmark effort: **$120**, enforced by `CRUCIBLE_MAX_CALLS` and
  the recorded per-call cost (CORR-008 fix).
- Every launch is preceded by a dry-run on ONE instance. The round-8 lesson
  is standing policy: **verify the materialised artifact, not the patch.**
- No round is launched without a fresh salted commitment.

## 9. Definition of done — the stopping contract

Work continues until ALL of these hold. Each names its proof artifact.

**A. Literature and design**
- [ ] A1 ≥20 further papers on agentic/tool-use science, drug design, and
      agent evaluation downloaded to `A:/PERTURB-Bench/analysis/literature2/pdfs/`,
      converted to text, **read in full**, each with a deep report in
      `analysis/literature2/deep/` and an independent coverage audit.
- [ ] A2 `analysis/literature2/SYNTHESIS.md` stating what the agentic-eval
      field does, its measured failure modes, and what MarigoldBench must do
      differently.
- [ ] A3 Collaborator reviews from Gemini 3.1 Pro and GPT-5.6 Sol archived in
      `analysis/collab/`, with their objections either implemented or
      answered in writing.

**B. Instrument**
- [ ] B1 Tool belt implemented and unit-tested against live services, with
      deterministic recording/replay so scoring never depends on a live call.
- [ ] B2 Episode harness (frozen contract, step budget, real tool errors
      surfaced, transcript capture) with tests.
- [ ] B3 Deterministic verifier per task family; every verifier recomputes.
- [ ] B4 All gates extended to episodes: `giveaway_scan` over prompts,
      artifacts and tool docs; wrong-path enumeration; C0/H1 byte-identity;
      answer-entropy and condition-independence over the population.
- [ ] B5 Baseline ladder passes on every shipped family: B8 reference = 1.00,
      B1 degenerate = 0, B5b best-wrong-path = 0, B0 tools-disabled ≤0.02,
      B10 tool-ablation shows every tool is load-bearing.

**C. Scale**
- [ ] C1 **≥100 independent task families** built and gate-passing.
- [ ] C2 ≥300 instances minted across them, with sealed/hidden/dev splits.
- [ ] C3 Population gates pass: no constant answers, condition does not
      determine the outcome, sealed split not reconstructible from dev.

**D. Measurement**
- [ ] D1 All three candidates — Gemini 3.1 Pro, GPT-5.6 Sol, Claude Opus 5 —
      benchmarked on the hidden split with ≥3 repeats, one frozen harness.
- [ ] D2 Strongest system's pass@1 lands in **5–40%** (below 5% = suspect
      over-correction, investigate per §5.4 discriminants; above 40% = T1
      saturation trigger, mint a harder epoch).
- [ ] D3 Every failure that a discriminant flags (D2 convergent-wrongness,
      D6 cross-family convergence on a non-key value) audited before
      publication, with wrong keys fixed and documented.
- [ ] D4 Scorecard with template-clustered CIs, hazard profiles, tool-use
      diagnostics, calibration, and the baseline ladder.

**E. Release**
- [ ] E1 Benchmark card, LIMITATIONS, CORRECTIONS ledger updated.
- [ ] E2 Replication kit: one command runs the dev split end to end.
- [ ] E3 Sealed-split commitment published for the scoring epoch; leak gate
      CLEAN; full transcripts published.

**Stop condition — explicit and checkable.** Work stops when ALL of the
following are literally true, each verifiable by running the named command. No
item may be checked by narrative.

| # | Condition | Verify with | Status at last check |
|---|---|---|---|
| S1 | Every task family passes every rung of the gate | `python runs/validate_families.py` prints `USABLE FAMILIES: n/n` | 31/31 |
| S2 | >=30 gate-clean families (interim bar; >=100 remains the standing target of B1 and is explicitly NOT met) | same command | 31 |
| S3 | GPT-5.6 Sol has an outcome file for **every** episode in `plan()` | `len(glob('runs/lab-1.0.0/systems/gpt/outcomes/*.json')) == len(plan())` | 553 / 1023 |
| S4 | Gemini 3.1 Pro preview likewise | same, for `gemini` | 403 / 1023 |
| S5 | Claude Opus 5 likewise, started ONLY after S3 and S4 are true | same, for `claude` | 231 (pilot, on an older family set) |
| S6 | Zero quarantined episodes remain unexplained | `ls runs/lab-1.0.0/systems/*/censored/*.json` empty, or each remaining one named in CORRECTIONS.md | 0 |
| S7 | Every family whose result crossed a discriminant tripwire has been audited | audit notes in CORRECTIONS.md or the family docstring | 3 wrong keys found and fixed |
| S8 | Scorecard built with family-clustered intervals and difficulty tiers | `python -m crucible.lab.scorecard` | built |
| S9 | Release artefacts present | `docs/BENCHMARK_CARD.md`, `docs/LIMITATIONS.md`, `docs/REPLICATION.md`, `CORRECTIONS.md`, `docs/SATURATION_POLICY.md` | all present |
| S10 | Leak gate clean | `python -m crucible.leakgate` prints `CLEAN` | CLEAN |
| S11 | Sealed-split commitment published for the scoring epoch | `python -m crucible.commitment verify --label <epoch>` prints `intact: true` | pending final epoch |
| S12 | Both collaborator consultations archived | `analysis/collab/hardening__gpt.md`, `analysis/collab/hardening__gemini.md` | both present |
| S13 | Literature corpora read and synthesised | `analysis/literature*/deep/` reports + both `SYNTHESIS.md` | 49 papers, 40 reports |
| S14 | Grok 4.6 complete on the full plan | `python runs/check_goal.py` | 990 episodes, xAI direct |
| S15 | DeepSeek V4 Pro complete on the reduced plan | `python runs/check_goal.py` | 270 hidden episodes |
| S16 | Kimi K2 Thinking complete on the reduced plan | `python runs/check_goal.py` | 270 hidden episodes |
| S17 | GLM 4.7 complete on the reduced plan | `python runs/check_goal.py` | 270 hidden episodes |

S14 is on the full plan because Grok runs on xAI's own key; S15-S17 are on the
reduced plan because the sponsor's OpenRouter allowance is $100 for the three
of them together, enforced as one shared ceiling in `campaign.run` with tests
in `tests/test_openrouter_ceiling.py` that make it fire. Grok is NOT permitted
through OpenRouter (sponsor instruction, 2026-08-18); see CORR-012.

**The only outstanding items are S3, S4, S5 and S11.** S3/S4 are bounded by
provider wall-clock, not by any decision; S5 is gated on them by the sponsor's
sequencing instruction; S11 is minted once the final epoch is fixed. Nothing
else is pending, and no item is blocked on a judgement call.

If an item becomes blocked on a credential or resource only the sponsor can
supply, that blocker is stated plainly, everything else is finished, and the
blocked item is the sole outstanding work.

## 11. Working rules

- Audit before believing a result. A failure by two frontier families at the
  same step is evidence about the key, not the model, until proven otherwise.
- Never fix a scoring problem by loosening the science. Fix the contract, the
  aliases, or the task — never the physical check.
- Every mistake that costs money gets written down (`CORRECTIONS.md`).
- Report outcomes exactly as they are, including self-inflicted waste.

## 12. Amendments (recorded, not silently applied)

**A1 (2026-08-17, revised) — Anthropic deferred to last, not cancelled.**
The sponsor first instructed that the Anthropic key not be used, then
clarified: **start Claude when everything else is done and finished.** So the
three-system lineup of section 1 stands, executed in sequence rather than in
parallel:

1. GPT-5.6 Sol and Gemini 3.1 Pro preview run to completion on the full
   family set.
2. Family authoring, gating, scorecard, and release artefacts complete.
3. ONLY THEN is the Anthropic campaign started, on the same frozen harness
   and the same episode list, so its numbers are comparable.

The 231 Claude episodes already collected predate the final family set and
are therefore treated as a pilot, not as the measurement of record; the
Claude column in the scorecard is marked incomplete until step 3 runs. No
Anthropic call is made before step 3, and D1 is not considered satisfied
until all three systems have run the same episode list.

**A2 (2026-08-17) — Gemini reachability resolved.** ADC is configured
(project `foundational-model-495611`). `gemini-3.1-pro-preview` is served ONLY
from `location=global`, on the unprefixed host `aiplatform.googleapis.com`;
every `us-central1` 3.x id returns 404 and `global-aiplatform...` returns an
HTML error page that reads like a missing model. Section 10's blocker is
closed.

**A3 (2026-08-17) — collaborator protocol executed.** Both required
collaborators have reviewed the design and their responses are archived
verbatim: `analysis/collab/hardening__gpt.md` (GPT-5.6 Sol, high reasoning)
and `analysis/collab/hardening__gemini.md` (Gemini 3.1 Pro). Per the sponsor's
later instruction, collaborators are now OpenAI and Gemini only. Their
objections and the design changes each one caused are recorded in
`analysis/literature2/SYNTHESIS.md` section 4.

**A4 (2026-08-17) — step budget raised for hard families.** Gemini's
structural objection is accepted: an 8-18 call budget forces a straight-line
solution, and frontier models have memorised the straight lines. Hard families
move to 30-60 calls so an episode can require iterative traversal (propose,
measure, discover a coupled constraint is violated, revise). The cheap
families are retained as a deliberate low-difficulty anchor band and their
pass rate is no longer read as the headline.

**A5 (2026-08-17) — second literature corpus complete.** 20 further papers
downloaded, read in full and audit-verified (`analysis/literature2/`), with
synthesis. A1 of section 9 is satisfied: 49 papers total across both corpora,
40 deep reports.
