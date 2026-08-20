# Agentic-science literature synthesis (20 papers, full-text, audit-verified)

Corpus: 20 papers on agentic evaluation, science agents, and the structural
biology / cheminformatics methods MarigoldBench hands the model as tools. Every
paper was downloaded to `analysis/literature2/pdfs/`, converted, read end to
end by a dedicated agent, and independently audited for coverage. Deep reports
in `analysis/literature2/deep/`. This is the second corpus; the first
(19 papers on benchmark construction and statistics) is synthesised in
`analysis/literature/deep/SYNTHESIS.md`.

Two frontier collaborators then reviewed the design directly (GPT-5.6 Sol at
high reasoning, Gemini 3.1 Pro), archived verbatim in `analysis/collab/`.

---

## 1. The single most useful number in the corpus

**DiffDock: 38% top-1 success at RMSD < 2 Å — but 12% when physical validity
is also required, and 0.92% on targets far from its training distribution.**
(diffdock, posebusters)

That is the whole design thesis in one measurement. Conjunction is the
difficulty engine: TankBind falls 59% → 5.9% and Uni-Mol 22% → 2.0% purely by
AND-ing a validity suite onto the headline metric. A benchmark that scores the
metric everyone reports is easy; one that requires the metric AND the physics
lands in the single digits without any artificial difficulty.

## 2. What the agentic-eval field has measured about agents

| Finding | Source | Consequence adopted |
|---|---|---|
| Failure is dominated by scaffolding artifacts, not science: Invalid Format 53% (DB), Invalid Action 64% (HH), Task-Limit-Exceeded 82% (LTP) | agentbench | Log a finish taxonomy beside the score; identical parser leniency across families; quarantine harness errors (we already scored 22 of our own as model failures once) |
| >90% of task-limit failures repeat a near-identical action within the last 10 rounds | agentbench | Loop detection as its own failure class, not silent budget exhaustion |
| Retries manufacture score: 0% → >15% at 1,000 retries → >30% at 10^6 | agents-cost | pass^k headline; pass@k reported, never headlined; cost recorded per episode |
| pass^8 < 25% where pass^1 ≈ 61% | tau-bench | Reliability, not single-shot, is the honest number |
| Best model 12% vs human 72% on real computer tasks | osworld | A wide human-agent gap is normal and is not evidence of a broken benchmark |
| Bio-agent benchmark: best ~21% open-answer; multiple-choice with voting is *no better* than open | bixbench | Open-ended answering is the harder and more honest format — do not retreat to menus |
| Chemistry agents: 37.5% average, 100% on old datasets and **0% post-cutoff** | chemistry-agents | Contamination is the dominant confound in this exact domain; fresh minting is mandatory |
| 69% API mortality within a year | toolllm | Tool availability decays; pin and record endpoint versions, cache and replay |
| Dollar rankings are perishable (prices moved ~80% since release) | hal | Report cost per episode, not a cost ranking |

## 3. What the method papers say about verifying science

- **PoseBusters**: a gating check must publish its own false-alarm rate on
  known-good inputs (2/85 Astex, 2/308 benchmark). Ours is measured: 0% on
  known-good molecules. Without that number, a model's false alarm is
  indistinguishable from the instrument's.
- **PLINDER / TDC / molecular-ml-pitfalls**: time-splits are insufficient;
  47/81 Astex complexes and 67/81 Astex proteins exceed 95% identity to
  training corpora. Leakage inflation of 30–50% is documented. Scaffold or
  identity-stratified splitting is the judgment call, and a hidden test split
  re-run by the harness is the only trustworthy verification.
- **docking-power**: scoring functions correlate weakly with truth; a docking
  score is not an affinity. Never let a tool's own confidence be the answer.
- **RFdiffusion applications**: real binder campaigns report success rates of
  a few percent per design, with experimental filtering. A benchmark that
  expects a first-shot design to succeed is not modelling the science.
- **ai-scientist / coscientist / chemcrow**: autonomous science agents fail
  not by crashing but by producing *successful tool calls whose science is
  wrong* — a units slip, an unvalidated assumption, a plausible number. That
  is precisely the failure class our H1 condition must plant.

## 4. What the two collaborators told us, and where they agree

Both were asked to attack the design after our families saturated at 91–94%.

**They converge on the same diagnosis.** GPT-5.6: the families are "canonical
audit recipes with a conspicuous local defect". Gemini 3.1: "you have confused
using a complex tool with solving a complex scientific problem… it is acting
as a JSON parser, not a scientist."

Shared prescription — stop hiding an answer; ship **several superficially
adequate analyses that imply different decisions**, plus controls that make
exactly one defensible:

1. **Competing mechanistic explanations.** True inhibition vs fluorescence
   quenching; binding vs aggregation; activity vs reference drift. The primary
   observable fits both; an orthogonal control discriminates.
   *Implemented*: the `assay-mechanism` family.
2. **Explicit impossibility witnesses for F2.** Not "the data are poor" but a
   provable non-identifiability: two admissible parameter vectors θ1, θ2 with
   f(x;θ1) = f(x;θ2) and different required decisions.
   *Implemented*: Cheng-Prusoff (Ki, Km) pairs reproducing one IC50.
3. **Coupled constraints / adversarial landscapes** (Gemini): selectivity
   against a 95%-identical paralog, where optimising affinity destroys
   selectivity. Verified by re-running the co-folding tool against both.
4. **Spurious correlation that inverts on holdout** (Gemini): a descriptor
   correlates with potency in training and anti-correlates in test, so a
   high cross-validated R² is a trap.
5. **Leaky abstractions** (Gemini): tautomer/protonation/stereochemistry that
   default RDKit calls silently destroy.

**Two warnings we had not internalised.**

- GPT-5.6: *"constructed truth does not by itself imply negligible label
  error. If the generator and verifier encode the same scientifically wrong
  assumption, they will agree perfectly and still be wrong."* Adopted: the
  verifier re-derives from the observable where it can, not from the parameter
  that produced it, and any stage where two frontier families converge on a
  non-key answer triggers a key audit before publication. That rule has
  already caught three of our own wrong keys.
- GPT-5.6: byte-identical briefs are **not sufficient**. If H1 workspaces
  differ in file size, column count, missingness or numeric precision, the
  condition is readable without science. Adopted: control files are present in
  every condition with identical shape; only values differ.

**Where they disagree with our current design, and what we are changing.**

Gemini's structural objection is the sharpest thing either of them said:

> "You are operating under a severe structural handicap: 8–18 tool calls… If a
> task can be solved in 8–18 steps, the solution path must be a straight line.
> Frontier models have memorized every straight line."

This is right, and it is not fixable by making the straight line trickier.
Adopted changes:
- Raise the per-episode budget substantially (30–60 calls) for the hard
  families, so a task can require *iterative traversal* — propose, measure,
  discover the proposal fails a coupled constraint, revise.
- Add value-of-information structure: not every useful fact is in the
  workspace. The model must choose which measurement to spend a call on.
- Keep the cheap families as a low-difficulty anchor band, but stop treating
  their pass rate as the headline.

## 5. Scale, restated for this track

The first corpus set the bar (≥100 independent families; Miller's ≥1,000
questions; family-clustered intervals mandatory). Nothing here softens it, and
`agents-cost` adds that agentic benchmarks must report cost alongside score or
the comparison is meaningless. Current state: 14 gate-clean families, 462
episodes per system, family-clustered bootstrap intervals on every headline —
and the clustered interval is roughly three times the naive Wilson width,
which is exactly the discrepancy Miller measured and the reason the naive one
is printed only to show the size of the lie.

## 6. Standing conclusions

1. Score the conjunction, never the headline metric.
2. Never let a tool's own confidence be the answer.
3. Re-run the model's artifact on a hidden split; trust nothing self-reported.
4. Publish every check's false-alarm rate on known-good inputs.
5. Mint fresh instances per campaign — chemistry agents score 100% pre-cutoff
   and 0% post-cutoff, so contamination is the dominant confound here.
6. A large human-agent gap is the expected state of a real benchmark, not a
   bug to be tuned away.
