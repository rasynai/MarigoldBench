# Positioning and naming — CRUCIBLE-CHAIN

Date: 2026-08-16. Workstream: flagship positioning. Status: working document —
every claim below is grounded in a repo file or a source fetched today; nothing
is aspirational. Companion evidence: `analysis/crucible3_design.md`,
`analysis/literature/README.md`, `docs/LIMITATIONS.md`.

---

## 1. The claim we uniquely own

**Canonical phrase:** *process-verified scientific judgment under attractive
error.*

Prefer **"attractive error"** over "adversarial data". It is more accurate (the
data is not attacking; every stage offers a *plausible wrong path*, and a third
of instances are clean controls where the right answer is "nothing is wrong"),
it is already the repo's own language (`README.md` line 1), and no other
benchmark uses the term — it is claimable vocabulary the way "Google-proof" was
for GPQA.

**Canonical sentence** (use verbatim everywhere):

> CRUCIBLE-CHAIN measures whether an AI system can carry a realistic scientific
> analysis through 5–8 chained judgment calls, each with a plausible wrong
> path, scored per stage against generated ground truth that cannot be
> mislabeled — with zero credit for a chain broken anywhere, penalties for
> inventing problems on clean data, and a reliability headline (pass^3) that
> retrying cannot inflate.

### Why nobody else can say it (each differentiator vs. the incumbent that lacks it)

| Against | What they measure | What they cannot claim | Evidence |
|---|---|---|---|
| **GPQA** | Graduate-level knowledge recall, MCQ, "Google-proof" | Not process: one answer, no path, no controls. ~8% of Diamond estimated invalid; top models at 87% — effectively saturated | GPQA abstract (`analysis/literature/md/2311.12022.md`); Epoch AI GPQA Diamond page (fetched 2026-08-16: Grok 4 87%, expert baseline 69.7%) |
| **HLE** | Breadth: "final closed-ended academic benchmark", 2,500 exam questions | Difficulty was *selected by model failure*, which enriched wrong keys: FutureHouse found **29 ± 3.7%** of bio/chem answers contradicted by literature. Calibration RMS >70% across models — but still recall, not judgment | `analysis/literature/md/2501.14249.md`; futurehouse.org HLE audit (fetched: 29%±3.7%, HLE-Gold subset released); lastexam.ai (fetched: top score Gemini 3 Pro 38.3%) |
| **Agent benchmarks** (SWE-bench, CORE-Bench, RE-Bench, GAIA class) | Task completion in execution environments | Verifiability collapsed under audit: Berkeley team hit ~100% on six of them *without solving a task*; CORE-Bench shipped answers in artifacts (20/45); SWE-bench Verified retired 68.3% of items | `analysis/literature/README.md` §4 (BenchJack, Berkeley RDI audits) |
| **LifeSciBench** | Open-ended science with expert rubrics (750 tasks, best model 36.1% pass) | Rubric truth is opinion, single-shot, fully public on release, no false-alarm control | `analysis/crucible2_gap_analysis.md` §2; PDF archived `analysis/papers/lifescibench.pdf` |
| **GeneBench-Pro** (closest relative) | Synthetic known-causality bio problems, 28.7% best | *Named* the noticing-to-acting gap, then admitted its binary grading "discards stage-level diagnostic information". No per-stage instrument, no clean-control symmetry, 10/129 items released | `analysis/crucible2_gap_analysis.md` §2; design doc §2 |
| **HealthBench** | Physician-rubric conversations; the judge-validation gold standard | Rubrics are human judgment, not computable truth; medicine, not lab science | `analysis/papers/healthbench.pdf` |

The unique conjunction — no incumbent has more than two of these five:

1. **Constructed truth** (deterministic generator; key error structurally ~0 vs
   published 8% / 29% / 42%-corrected elsewhere) — `docs/LIMITATIONS.md` §0.
2. **Path scoring** (per-stage hazard profile h_k, trap rate, notice–act gap) —
   `analysis/preregistrations/campaign-3.0.0.md`.
3. **Symmetric error design** (C0 clean with false-alarm penalty, H1 planted
   defect, F2 flawed premise where refusal is correct; C0/H1 prompts
   byte-identical by machine check).
4. **Reliability as headline** (pass^3 ≤ pass@1 ≤ pass@3 ladder; flips across
   repeats; Wilson/cluster-bootstrap intervals).
5. **Accountable judging** (judges gated by gold-set meta-evaluation, advisory
   only, can never alter the deterministic primary metric; published finding
   that notice rates are conservative lower bounds —
   `runs/release-3.0.0/judge_meta_eval.json`).

### The saturation bug is a positioning asset, not an embarrassment

On 2026-08-16 the chain pilot returned **claude-opus-5 53/56 (94.6%) and
gpt-5.6-sol 56/56 (100%)** (`runs/release-3.0.0/systems/*/outcomes/`). Root
cause found the same day: work orders dictated the method as an ordered recipe,
printed the allowed answer tokens (turning categorical judgments into multiple
choice), and warned candidates away from the trap ("a good r-squared does not
by itself…") — visible verbatim in
`tasks_chain/OEC-ACHEM-TRBL-002/instances/C0-s11/prompt.md`. The numeric
`leak_scan` never fired because the giveaways were categorical. Fix: three
machine gates (`giveaway_scan` in `crucible/chain/spec.py:170-239` — option
menu, recipe-verb density, decoy hints) now reject such templates at build time.

Every incumbent found the equivalent bug *after outsiders did*: CORE-Bench's
shortcuts surfaced post-saturation, HLE's wrong keys via FutureHouse, SWE-bench
via OpenAI's re-curation. We found ours in-house, pre-launch, and published the
gate. **Tell this story loudly** — "the benchmark that red-teams itself before
you can" is the trust claim that makes "process-verified" credible, and it is
consistent with an already-exercised corrections log (CORR-001…CORR-009,
`runs/corrections/`, `release/1.0.0/corrections.md`).

### Claim discipline (what the positioning must never say)

From `docs/LIMITATIONS.md` and the prereg prohibited-claims list: no
human-level/expert claim (no human baseline exists or is planned; scores are
bracketed by the B0–B9 ladder), no discovery claim, no contamination-proof
claim, no causal product-vs-model comparison. Tasks are model-authored and
model-reviewed; artifacts are simulated instruments; single-turn, text-only.
Any pitch that omits these gets corrected by the first hostile reader — build
them into the pitch instead (see §2).

---

## 2. One-sentence pitch per audience

**Lab eval lead** (buys instruments, hates noise):
> "CRUCIBLE-CHAIN shows you *where* your model breaks inside a multi-stage
> analysis — per-stage hazard curves, seduction by plausible-wrong paths,
> false alarms on clean data, and whether it acts on problems it names — on
> generated tasks whose answer key is provably correct and whose headline,
> pass^3, your retry loop cannot inflate."

Supporting beats when they push back: label-error arms race (their pain:
re-auditing GPQA/HLE items), preregistered campaigns with published
corrections, denominators on every rate, cost-per-reliable-completion
(`$/VCC`) reported.

**Researcher citing benchmarks** (needs a defensible sentence in a paper):
> "CRUCIBLE-CHAIN is the first open science benchmark that verifies the
> analysis path rather than the final answer — deterministic per-stage truth
> (key error structurally near zero, versus ~8–29% published for
> expert-written keys), symmetric false-alarm controls, and a measured
> notice–act gap — the stage-level instrument GeneBench-Pro called for but did
> not build."

Supporting beats: cluster-on-template CIs (honest power accounting: templates,
not instances, are the unit of signal — design doc §6b), reported-not-gated
judge recall with the lower-bound argument, everything preregistered before
any candidate call.

**Journalist** (needs a story a reader can retell):
> "AI models now ace tests of what they *know* — this benchmark tests what
> they *do* when the data quietly misleads them, and it can prove the moment
> each model takes the bait, because the test's authors generated the data and
> know exactly where the trap is."

Mandatory rider for press materials (one sentence, non-negotiable): scores
are on simulated lab work, no human comparison is made, and the full
corrections log is public.

---

## 3. Naming: honest analysis

Three names currently refer to one thing — README h1 says **CRUCIBLE**, the
design doc says working title **CRUCIBLE-CHAIN**, the repo directory is
**PERTURB-Bench**, and the Python package is `crucible`. That inconsistency is
the biggest memorability bug, bigger than any individual name's flaws.

### Collision sweep (all fetched 2026-08-16)

**"Crucible" alone — crowded, do not use bare in public:**
- **Dreadnode "Crucible"** — AI red-teaming challenge platform (AIRTBench,
  arXiv 2506.14682); crucible.dreadnode.io now redirects into
  app.dreadnode.io. *Same broad space (AI evaluation/security).*
- **"Crucible" (NeurIPS 2025, Tsinghua)** — arXiv 2510.18491, LLM-agent
  framework for evaluating control algorithms. *Citation collision inside the
  evaluation literature.*
- **GaloisInc/crucible** (775★) symbolic-execution library; **CrucibleC2**
  (1,023★) offensive-security framework; **chaseai-yt/crucible** (1,181★)
  Claude Code skill; Oxide storage service. GitHub total: **1,982 repos**.
- A 2026 RAG system named Crucible (arXiv 2601.13222/13227); 8 small
  HuggingFace datasets; **Atlassian Crucible** code-review product
  (discontinued May 2025, support to May 2028 — 15 years of SEO residue).
- Culture owns the word: Arthur Miller's play dominates search, then the
  Snooker Crucible, Destiny's PvP mode, the USMC final test (that last
  connotation — culminating trial — is actually the right one).

**"CRUCIBLE-CHAIN" — claimable today:** GitHub search for
crucible-chain / cruciblechain: **0 repositories**; no arXiv match. Costs to
carry: five syllables; people will shorten it to "Crucible" in speech (styling
rule below mitigates in print, nothing mitigates speech); "-chain" echoes
blockchain (chainbench = a blockchain load-testing tool, chainstacklabs, 51★).
The suffix is load-bearing though — chained non-compensatory stages *are* the
mechanism — so the echo is a cost worth paying.

**"PERTURB-Bench" — retire as a public name.** Direct collision:
**PerturBench** (Altos Labs, arXiv 2408.10609, 2024;
github.com/altoslabs/perturbench) is an established, *currently active* ML
benchmark for cellular perturbation prediction — PRiMeFlow (arXiv 2604.13986,
2026) was "extensively benchmarked inside PerturBench" this year. It sits in
the adjacent field (ML for biology), so citation confusion is guaranteed and
would look like name-squatting. The name is also wrong on the merits: a third
of our instances are *clean controls*; the design's point is symmetric error,
not perturbation.

### Decision recommendation

**Keep CRUCIBLE-CHAIN as the sole public benchmark name.** Rationale: the
compound is collision-free today; the provenance trail that carries the trust
story (three campaign preregistrations, corrections CORR-001…009, release
records 0.2.0→1.0.0) is already written under CRUCIBLE; a fresh coinage
forfeits that continuity and needs identical collision diligence anyway.
Styling rules that make it work:

1. Public materials always write **CRUCIBLE-CHAIN** (caps, hyphen), never bare
   "Crucible". First mention expands the mechanism: "CRUCIBLE-CHAIN, a
   chained-judgment benchmark…".
2. The deterministic 1.0 track is "the anchor track", not a second brand.
3. Repo/org slug becomes `crucible-chain` (verified free); the directory name
   PERTURB-Bench disappears from anything public. `crucible` stays as the
   internal module name only.
4. FAQ line pre-drafted: no affiliation with PerturBench (Altos Labs),
   Dreadnode's Crucible platform, or Galois's crucible.

Runner-up considered and rejected: fresh distinctive coinage (maximum
searchability, zero baggage) — rejected because the release history *is* the
differentiator and renaming orphans it mid-scale-up; revisit only if a trademark
search (not yet done — see actions) surfaces a blocking mark.

---

## 4. Ranked recommendations

1. **Freeze the name and unify it everywhere** — public name CRUCIBLE-CHAIN
   per styling rules above; rename repo slug to `crucible-chain`; register the
   GitHub org name and HF namespace now while free; sweep README/benchmark
   card/scorecards for bare "Crucible" and "PERTURB-Bench". *(0.5 day; do
   before any external link circulates.)*
2. **Paste the canonical claim sentence and the §1 comparison table into
   README top and `benchmark_card`** with the four label-error citations
   (FutureHouse 29%, Epoch ~8%, FrontierMath 42% corrected, CORE-Bench 20/45).
   The table already exists in `analysis/crucible3_design.md` §2 — this is
   assembly, not writing. *(0.5 day.)*
3. **Publish the saturation post-mortem as a 1-2 page methods note** ("We
   saturated our own benchmark in a day; here is the gate that makes it
   structural"): the 53/56 and 56/56 numbers, the three giveaway classes with
   the before/after prompt excerpt, and `giveaway_scan` as released code. This
   converts the week's worst bug into the launch trust asset and is the
   concrete proof behind "process-verified". *(1–2 days; ship with the
   300–400-item release, reference from the benchmark card.)*
4. **Create `PITCH.md`** with the three audience sentences plus the mandatory
   caveat block (from LIMITATIONS §0) so every future abstract, README intro,
   tweet and email reuses identical language — positioning drift is how
   prohibited claims leak out. *(0.5 day.)*
5. **Gate any "flagship" language on scale and coverage**: today the chain
   track is 8 templates / 96 instances with only two frontier systems scored
   pre-fix (CORR-007 killed six via OpenRouter credit; CORR-009 fixed lineup
   at five). The flagship claim needs the 30-template population, ≥6 evaluated
   frontier systems, and a *post-fix* non-saturated campaign. Until then the
   honest register is "new benchmark, unusually strict validity program".
   *(Blocking condition, not a task.)*
6. **Pre-launch collision re-sweep + registrations**: re-run the GitHub/arXiv/
   HF sweep on final styling, a basic USPTO/EUIPO word-mark search on
   "CRUCIBLE-CHAIN", and claim a domain (e.g. cruciblechain.org or a
   crucible-chain.github.io landing page). *(Hours, plus registrar cost.)*
7. **Prepare the pass^3-reads-as-zero explainer** for the scorecard: pass^3
   collapses to hard zero below pass@1 ≈ 8% (prereg), which journalists will
   misread as "benchmark broken". The ladder framing (pass^3 ≤ pass@1 ≤
   pass@3, always printed together) must appear in every public table.
   *(Hours; template text exists in `runs/release-3.0.0/scorecard.md`.)*

---

## Sources

Repo evidence: `README.md`; `analysis/crucible3_design.md`;
`analysis/literature/README.md` (23 papers read in full, per-claim numbers);
`analysis/crucible2_gap_analysis.md`; `docs/LIMITATIONS.md`;
`analysis/preregistrations/campaign-3.0.0.md`;
`release/1.0.0/benchmark_card-1.0.0.md`; `runs/corrections/CORR-007/`,
`CORR-009/`; `crucible/chain/spec.py` (leak_scan, giveaway_scan);
`runs/release-3.0.0/` (outcomes, baselines, judge_meta_eval);
`tasks_chain/OEC-ACHEM-TRBL-002/instances/C0-s11/prompt.md` (pre-fix giveaway
exemplar); archived full texts `analysis/literature/md/2311.12022.md` (GPQA),
`2501.14249.md` (HLE), `analysis/papers/lifescibench.pdf`, `healthbench.pdf`.

Fetched 2026-08-16: GitHub search API ("crucible" 1,982 repos; "crucible-chain"
0; "chainbench" 10) · arXiv API ("crucible" papers incl. 2510.18491;
"perturbench" → 2408.10609, 2604.13986) · arxiv.org/abs/2510.18491 (NeurIPS
2025 Crucible) · atlassian.com/software/crucible (discontinued) ·
crucible.dreadnode.io → app.dreadnode.io redirect · epoch.ai/benchmarks/
gpqa-diamond (Grok 4 87%) · lastexam.ai (positioning + Gemini 3 Pro 38.3%) ·
futurehouse.org HLE audit (29 ± 3.7%) · huggingface.co API (8 "crucible"
datasets) · en.wikipedia.org Crucible disambiguation.
