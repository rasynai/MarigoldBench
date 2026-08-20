# Distribution and integration strategy — CRUCIBLE-CHAIN

Workstream doc, flagship track. Written 2026-08-16. Evidence: 21 primary web
sources (fetched today, quoted inline) + this repo. Every claim is grounded;
URLs at the bottom. Companion context: `analysis/crucible3_design.md` §7
(tiered release), `release/1.0.0/benchmark_card.md` (current splits/scale).

The question: what stack gets CRUCIBLE-CHAIN from a private 460-item program
to the industry's flagship open-ended science benchmark — harness
integrations, HuggingFace presence, leaderboard, and a sealed-split
evaluation service where we run their model.

---

## Part 1 — Findings

### F1. The four named integration targets have four different doors, and two are effectively closed

**lm-evaluation-harness (EleutherAI).** Open PR-based contribution. Hard
requirements from `docs/new_task_guide.md`: dataset **must** be on the
HuggingFace hub; tasks are YAML configs; primary output types are generative
and multiple-choice single calls; the submission checklist requires
"verification that tasks are existing benchmarks with literature references."
The guide has **no support for LLM-judge scoring or multi-turn agentic
tasks**. Adoption is real — the README states it is "the backend for Hugging
Face's popular Open LLM Leaderboard" and used internally by "NVIDIA, Cohere,
BigScience, BigCode, Nous Research, and Mosaic ML" — but the format fits only
our deterministic anchor-track subset (single-call, machine-scorable), not
CHAIN's 5–8-stage judged chains with non-compensatory gating.

**Inspect AI / inspect_evals (UK AISI).** The framework fits CHAIN natively:
multi-turn agents, "custom and MCP tools," model-graded scorers, sandboxing
in "Docker, Kubernetes, Modal, Proxmox, Vagrant." The registry (171 evals,
129 external; built by UK AISI, Arcadia Impact, Vector Institute) already
hosts our nearest neighbors: GAIA, GPQA, LAB-Bench, SciCode, ChemBench,
SWE-bench. But the contributing page says: **"We no longer accept code
submissions for new eval implementations"** — new evals go through a template
+ register process, and eligibility wants "well-established in the research
community — ideally with usage or citations," non-saturated tasks, "agentic
or task-based over simple Q&A," reference frontier results, and credible
sources ("individual-designed evaluations face lower priority"). Translation:
**an Inspect-native implementation can and should ship from our own repo
immediately; registry entry comes after the paper and first external
citations.**

**HELM (Stanford CRFM).** Accepts scenario PRs when the benchmark "is a
commonly-used or notable benchmark (e.g. it has a published paper). It uses
publicly available datasets. It fills a gap in coverage." Scenario types are
classic NLP (MCQA, short/open QA, summarization, classification); the
scenario docs mention nothing about multi-turn, model-graded, or agentic
runs, and leaderboard inclusion is not promised by a merged scenario. Low
priority; anchor track only; after the paper.

**OpenAI.** `openai/simple-evals` is closed: "We will not be actively
maintaining this repository … In particular, **we're not accepting new
evals**," with updates ceased as of July 2025. There is no submission door
into OpenAI's internal stack. The observed path is partnership: ARC Prize
tests OpenAI models on its semi-private set under "zero data retention
agreements with all model providers we test," and OpenAI reports third-party
benchmarks it can run itself or that creators run for it. **You do not get
into a lab's stack; you become a benchmark the lab either self-runs from your
public harness or lets you run under agreement.**

**Anthropic.** The only lab with an explicit, funded intake: the third-party
evaluations initiative solicits evals and lists the criteria. The list reads
like CRUCIBLE's design doc: "sufficiently difficult," "not in the training
data," efficient/scalable, format diversity beyond multiple choice, expert
baselines, and — decisive for us — "strong documentation following standards
like **Inspect** or METR." Two gaps to close before applying: volume ("1,000
or 10,000 tasks … preferable to those with 100" — we are at 104 going on
~460; the generator makes 1,000+ a seeds decision, not an authoring project)
and the human-expert-baseline expectation (we have a baseline ladder and an
honest disclosure instead — say so plainly).

### F2. The proven distribution pattern for held-out benchmarks is exactly our split design — plus two mechanics we lack

Every credible held-out benchmark converges on the same shape:

- **GAIA**: dev sets "fully public," test sets keep "private answers and
  metadata"; the HF dataset is gated ("agree to share your contact
  information," "do not reshare … in a crawlable format"); the leaderboard
  scores submissions server-side against withheld answers.
- **LAB-Bench** (FutureHouse; closest domain neighbor): "approximately 80% of
  the full dataset" public, "a 20% private test subset to monitor for
  training contamination," CC-BY-SA-4.0, and a canary string that "is a
  superset of the BIG-bench canary string."
- **HLE** (CAIS/Scale): 2,500 public questions on HF "while maintaining a
  private test set of held out questions to assess model overfitting," plus a
  bug-bounty that removed compromised questions, plus "HLE-Rolling" for
  continuous refresh.
- **ARC Prize**: public / semi-private / private tiers; frontier APIs tested
  on semi-private under zero-data-retention agreements with a "$10,000 USD
  per run" cap; they "monitor for overfitting by tracking the performance gap
  between Public and Semi-Private tasks over time" and release fresh sets
  annually when the gap narrows.
- **LiveBench**: contamination handled by cadence — "releasing new questions
  monthly," newest questions withheld from HF for a delay window, and "each
  question has verifiable, objective ground-truth answers … without the use
  of an LLM judge."

Our repo already implements the split topology (16 dev public / 66 hidden /
22 sealed git-ignored per `release/1.0.0/benchmark_card.md`; tiered-release
plan in `analysis/crucible3_design.md` §7) and the hidden-vs-sealed delta is
ARC's gap-monitoring, preregistered. Two mechanics are missing:

1. **Our canary is not industry-format.** `crucible/paths.py` defines
   `TRUTH_MARKER = "<the truth marker string>"` — a plain string
   on truth-zone files only. BIG-bench's README: canary strings exist "to
   prevent benchmark tasks from leaking into web-scraped training data," and
   LAB-Bench extends the same GUID so one grep catches both. We need a GUID
   canary that is a superset of the BIG-bench canary **on every distributed
   task file** (not just truth files), because the thing we most need to keep
   out of training corpora is the hidden-split task cards themselves.
2. **No gated distribution channel.** Tasks live in this repo only. The
   gating + no-crawlable-reshare terms of GAIA are the standard, and HF is
   where every neighbor (GAIA, LAB-Bench, HLE, LiveBench, ARC results) puts
   its public face.

Our structural advantage over all five: **their refresh is authorship-bound;
ours is a seed.** LiveBench pays monthly authoring cost; ARC ships annual
sets; HLE runs a bug bounty. Our deterministic generators regenerate a sealed
split per campaign at near-zero marginal cost with near-zero label error.
That is the flagship claim distribution should be built around.

### F3. "We run their model" is now a normal, named industry tier — with three working models to copy

- **Creator-run under agreement (ARC model).** ARC Prize runs OpenAI/Google
  models on semi-private tasks via their APIs, protected by "zero data
  retention agreements," cost-capped per run, results published to HF. They
  candidly state semi-private sets face "the possibility of limited leakage
  over time" — which our per-campaign sealed regeneration answers better
  than their annual refresh.
- **Independent runner (Epoch / Artificial Analysis / SEAL model).** Epoch's
  hub is explicitly three-tier: "Epoch AI–run" (FrontierMath, SWE-bench
  Verified), "benchmark creator–run" (ARC-AGI, OSWorld), "model
  developer–run" (MMLU, LiveBench). Artificial Analysis runs its Intelligence
  Index evals itself with "internal copies of all evaluation datasets" — and,
  the key precedent, integrates third-party scoring authority: for CritPt it
  uses **"the official CritPt grading server."** A grading server is exactly
  our shape: predictions in, verdicts out, truth never leaves the building.
- **Artifact-verified self-run (SWE-bench model).** Teams run the public
  harness themselves and PR their results with `all_preds`, per-instance
  `trajs/` ("generated during inference, not retrospectively"), and
  evaluation logs; the verified checkmark means "we will run your model on a
  random subset … and verify the results." Cheap to operate, credible enough
  for model cards.

HAL (Princeton) validates the third-party agent-leaderboard concept
("standardized, cost-aware, and third-party," hosting GAIA, ScienceAgentBench,
CORE-Bench…) but "we have paused updating HAL leaderboard with new models" —
so it is a partner to court, not infrastructure to rely on.

Repo readiness: campaigns already are "we run their model" — 8 API models
through a matched two-call reference agent, 828 preregistered runs
(`release/1.0.0/benchmark_card.md`), with a multi-provider client that
reaches every vendor "over the same OpenAI-compatible wire"
(`crucible/llm.py`: openrouter/nvidia/gemini/vertex). The missing pieces are
an intake process, ZDR agreement template, and a public results contract —
not the runner.

### F4. Leaderboard hosting is a solved problem at two tiers

HF's official leaderboard docs describe the standard four-piece template
(frontend Space + gated `requests` dataset + `results` dataset + optional
backend Space), spanning "fully automated … to fully manual (every new
evaluation is run with human control)," with indexing via the Leaderboard
Finder. GAIA demonstrates the pattern we need — Space scores submissions
against server-held answers. Custom domains (swebench.com, tbench.ai,
arcprize.org, livebench.ai) are the maturity step, typically added once
traffic and identity justify it; Terminal-Bench shipped its harness and
browser first and left leaderboard submissions "coming soon" without hurting
adoption. Start on HF (distribution + gating + finder for free), move the
canonical view to a domain at the paper.

### F5. What actually earns lab model-card and index placement

- Labs self-run benchmarks that are **one-command runnable against an API
  key** (tau-bench, SWE-bench Verified pattern; Epoch's "model developer–run"
  category exists because labs do this), or they accept creator-run numbers
  under agreement (ARC).
- Aggregators pick components that are independently runnable, non-saturated,
  and cover a distinct capability. AA's Intelligence Index (9 evals, 4
  categories) has **no constructed-truth open-ended science-reliability
  component** — nearest are CritPt, SciCode, HLE. AA also flags HLE's
  adversarial-curation bias and anonymizes submissions for grading — they
  care about exactly the validity properties (judge gating, curation bias,
  CIs: "95% confidence interval … less than ±1%") that our meta-evaluated
  judges, Wilson CIs, and preregistration already document.
- Inspect eligibility (F1) and Anthropic's criteria (F1) both price in
  **citations and non-saturation**. The saturation bug we just fixed
  (prompts leaked method recipes + answer menus; frontier models at 94–100%)
  would have disqualified us on the one property everyone checks first.
  Post-fix hidden-split results are the evidence to lead with.

### F6. Repo gaps that block distribution today (all cheap to fix)

- **No LICENSE, no CITATION.cff** anywhere at root; `pyproject.toml` has no
  license field and still says `version = "0.1.0"` against a shipped 1.0.0
  release. Neighbors license tasks CC-BY(-SA) (LAB-Bench: CC-BY-SA-4.0) and
  code Apache-2.0/MIT.
- **Canary format** (F2). One constant in `crucible/paths.py` plus a
  regeneration pass; `scan_for_truth` in `crucible/packaging.py` already
  enforces by content, so the plumbing survives the change.
- **No outsider run path.** `crucible/packaging.py::build_agent_bundle`
  produces agent-visible bundles and the truth boundary is enforced, but
  there is no `pip install crucible-bench && crucible eval --model X`
  equivalent for someone who isn't us; campaign code is bespoke
  (`crucible/release_campaign.py`, `crucible/frontier_campaign.py`).
- **Naming.** Working dir PERTURB-Bench, package `crucible-bench`, benchmark
  CRUCIBLE-CHAIN. Pick the public name once, check PyPI/HF-org availability
  before the paper cites it.
- **No paper.** `analysis/literature/` reads 23 external papers; nothing
  citable of our own. Every registry door (inspect_evals, HELM, lm-eval
  checklist "existing benchmarks with literature references") keys on this.

---

## Part 2 — The recommended stack

One sentence: **be Inspect-native at the harness layer, GAIA-shaped at the
data layer, ARC-shaped at the sealed layer, and CritPt-shaped at the scoring
layer — and keep scoring authority centralized because non-compensatory,
judge-gated scoring is not credibly reproducible by outsiders.**

| Layer | Choice | Copied from |
|---|---|---|
| Harness | Inspect AI task package in our repo (`inspect eval crucible_chain`), registry entry post-citations | inspect_evals eligibility; Anthropic "standards like Inspect" |
| Data | Gated HF dataset: dev split with truth; hidden split task-cards only, truth withheld; GUID canary superset of BIG-bench on every file | GAIA gating; LAB-Bench 80/20 + canary |
| Leaderboard | HF Space scoring hidden-split submissions against server-held truth; custom domain at paper time | GAIA leaderboard; HF demo-leaderboard template |
| Self-serve tier | Public-harness self-run + artifact PR (predictions, per-stage trajectories, logs) + spot re-verification badge | SWE-bench experiments repo |
| Sealed tier | Creator-run campaigns under ZDR agreements, cost-capped, pass^3 + Wilson CIs + hazard profile report; sealed split regenerated per campaign from fresh seeds | ARC Prize policy; our generator advantage |
| Scoring authority | Grading server (predictions in, verdict + hazard profile out; truth never leaves) offered to aggregators | CritPt grading server used by Artificial Analysis |
| Lab channel | Anthropic third-party-evals application; ARC-style ZDR partnership offers to other labs; labs self-run via Inspect package | Anthropic initiative; ARC ZDR precedent |
| Aggregators | Epoch hub as "creator-run" first; AA Intelligence Index pitch (uncovered category + grading-server integration); HAL when unpaused | Epoch three-tier hub; AA methodology |
| Legacy presence | Anchor-track subset as lm-eval YAML task + HELM scenario, post-paper | lm-eval new-task guide; HELM criteria |

What we deliberately do **not** do: publish truth to HF in any form
(`scan_for_truth`/`leakgate` stay load-bearing); chase fully-automated
open-submission evaluation of arbitrary checkpoints (Open LLM Leaderboard
model) — our judged, gated scoring can't be farmed out without losing the
validity story that differentiates us; wait for inspect_evals/HELM
acceptance before shipping our own Inspect package.

---

## Part 3 — Ranked recommendations

**R1. Ship an Inspect-native `crucible_chain` package from our own repo.**
Port the reference agent to an Inspect solver and the non-compensatory gate +
meta-eval-gated judge to Inspect scorers; `inspect eval` one-liner against
any provider. This is simultaneously: the format AISI runs pre-deployment,
the documentation standard Anthropic names, the lab self-run path (F5), and
the future inspect_evals registry artifact. Effort: 1–2 weeks (the two-call
agent and deterministic verifier port cleanly; judge gating is the work).
Blocker for: R5, R7.

**R2. Fix the distribution blockers in the repo.** GUID canary
(BIG-bench-superset, on every distributed file) + regeneration pass; LICENSE
(Apache-2.0 code, CC-BY-SA-4.0 tasks); CITATION.cff; version alignment;
final public name + PyPI/HF-org check. Effort: 1–2 days. Blocker for: R3
(can't gate-distribute unlicensed, uncanaried tasks).

**R3. Stand up the HF presence: gated dataset + leaderboard Space.** Dev
split with full truth; hidden split task-cards only; GAIA-style gate terms
(contact info, no crawlable reshare). Space from the demo-leaderboard
template, scoring submissions server-side against withheld truth; register
with Leaderboard Finder. Effort: about 1 week including submission-format
docs. Depends on: R2.

**R4. Launch the two-tier evaluation service.**
(a) *Self-serve verified*: SWE-bench-mechanics — run our harness yourself on
the hidden split, PR predictions + per-stage trajectories + logs; we
spot-re-run for the verified badge. Effort: process doc + template repo,
2–3 days on top of R1/R3.
(b) *Sealed, creator-run*: intake form; ZDR agreement template (ARC
precedent); cost cap per run; we run their model through the existing
multi-provider wire on a **freshly regenerated sealed split**; deliverable is
the scorecard (pass^3, pass@1/3, Wilson CIs, per-stage hazard, notice-act
gap) plus the public-vs-sealed gap published as contamination telemetry.
Effort: 2–4 weeks, mostly legal template + intake + report automation; the
runner exists. This tier is the flagship differentiator — nobody else can
regenerate their held-out set per customer.

**R5. Write the paper and preregister the 300–400-instance campaign as its
evidence.** Include: constructed-truth mechanism and near-zero label error;
the saturation bug as a validation story (found via hidden-split telemetry,
fixed, scores restratified); corrections log (9 published); judge
meta-evaluation. Every remaining door (inspect_evals "usage or citations,"
HELM "has a published paper," lm-eval "literature references," Epoch/AA
credibility) keys on this artifact. Effort: 3–4 weeks alongside the
expansion campaign. Depends on: R1 (report Inspect-runnable), R2.

**R6. Run the lab and aggregator outreach sequence.** Order: (1) Anthropic
third-party evals initiative — apply with the Inspect package, the 10-criteria
mapping, and a seeds-backed plan to 1,000+ instances; (2) Epoch hub as
"benchmark creator–run" results; (3) Artificial Analysis — pitch the
uncovered index category plus CritPt-style grading-server integration; (4)
ARC-style ZDR sealed-campaign offers to OpenAI/GDM eval teams (there is no
submission door; this is a partnership sale); (5) HAL when it unpauses.
Effort: ongoing from paper week; each engagement is a meeting + a runnable
artifact we already have from R1–R4.

**R7. Add the anchor-track subset to lm-evaluation-harness and HELM.**
Single-call-scorable instances as a YAML task on a HF dataset + a HELM
scenario PR. Value is discoverability and the "hundreds of papers" citation
channel, not fidelity — label it explicitly as the anchor subset so nobody
mistakes it for CHAIN. Effort: 2–3 days each. Depends on: R3, R5.

Sequence at a glance: R2 → R1 + R3 (parallel) → R4 → R5 → R6 → R7.
R1–R4 are ~4–6 team-weeks and complete the stack; R5 unlocks every
institutional door; R6 is where flagship status is actually won.

---

## Sources

Harnesses and registries: [lm-eval new task guide](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/new_task_guide.md); [lm-eval README (adoption)](https://github.com/EleutherAI/lm-evaluation-harness); [inspect_evals contributing](https://ukgovernmentbeis.github.io/inspect_evals/contributing/); [inspect_evals registry](https://ukgovernmentbeis.github.io/inspect_evals/); [Inspect AI docs](https://inspect.aisi.org.uk/); [HELM adding scenarios](https://crfm-helm.readthedocs.io/en/latest/adding_new_scenarios/); [openai/simple-evals](https://github.com/openai/simple-evals); [METR Task Standard](https://github.com/METR/task-standard).

Held-out distribution models: [GAIA dataset card](https://huggingface.co/datasets/gaia-benchmark/GAIA); [LAB-Bench dataset card](https://huggingface.co/datasets/futurehouse/lab-bench); [Humanity's Last Exam](https://lastexam.ai/); [ARC Prize testing policy](https://arcprize.org/policy); [LiveBench](https://github.com/LiveBench/LiveBench); [BIG-bench canary](https://github.com/google/BIG-bench).

Runners, leaderboards, aggregators: [Epoch AI Benchmarking Hub](https://epoch.ai/benchmarks); [Artificial Analysis methodology](https://artificialanalysis.ai/methodology/intelligence-benchmarking); [HAL](https://hal.cs.princeton.edu/); [SWE-bench submission](https://github.com/SWE-bench/experiments); [HF leaderboard docs](https://huggingface.co/docs/leaderboards/en/leaderboards/building_page); [Terminal-Bench docs](https://www.tbench.ai/docs); [Anthropic third-party evals initiative](https://www.anthropic.com/news/a-new-initiative-for-developing-third-party-model-evaluations).

Repo evidence: `crucible/paths.py` (TRUTH_MARKER), `crucible/packaging.py`
(truth boundary), `crucible/llm.py` (multi-provider wire),
`release/1.0.0/benchmark_card.md` (splits, campaign),
`analysis/crucible3_design.md` §7 (tiered release), `pyproject.toml`
(version/license gaps), repo root (no LICENSE/CITATION.cff).
