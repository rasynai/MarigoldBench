# The logistics moat: what it costs to replicate CRUCIBLE, and why "use theirs" beats "build our own"

Date: 2026-08-16. Status: working document for the flagship strategy team.
Evidence: this repository (code, usage ledger, build logs, corrections) and the
primary sources archived in `analysis/literature/` and `analysis/papers/`
(23 benchmarks + methodology papers, read in full). Model prices: Anthropic list
($5/M input, $25/M output for claude-opus-5). Where a number is an estimate, the
assumption is stated inline.

---

## 1. The itemized bill of replication

What a lab must build, end to end, to stand up a constructed-truth chain
benchmark equivalent to CRUCIBLE-CHAIN. Every line is grounded in an artifact in
this repo. Volume for context: ~13,700 lines of Python (pipeline + tests,
`crucible/`, `tests/`), ~34,000 lines of design/governance/release markdown,
74 test functions, 9 published corrections.

| # | Component | What it actually involves | Evidence in repo |
|---|---|---|---|
| 1 | **Generator authoring contract** | A 16-hard-rule authoring spec (trap separation ≥3×tol, decoy plausibility ratio [0.1,10], byte-identical C0/H1 prompts, no meta-vocabulary, computed-never-hardcoded keys, H1-must-change-the-answer, no %-formatting, no asserts, 150–250-line budget...) plus a 345-line hand-written exemplar generator that the authoring model must match. Half the rules exist because a template died without them — the contract annotates "this is the single most common reason templates are rejected" per rule. | `crucible/chain/author.py` (AUTHOR_TEMPLATE), `crucible/chain/exemplar.py` |
| 2 | **Structural gates (machine)** | Per-stage checks: correct/decoy typing, tolerance, alias disjointness in the scorer's normal form; `leak_scan` (~12 renderings of every stage answer grepped against everything candidate-visible); `giveaway_scan` (option menus, method-recipe sentences, decoy-warning phrases); META_WORDS list with documented false-positive history (banning "trap"/"hazard" as bare words rejected valid mass-spec and survival-analysis tasks). | `crucible/chain/spec.py` (321 lines), `tests/test_giveaway_gate.py` |
| 3 | **Validity gates (behavioral)** | Determinism (re-run byte-identical), reference answer must score VCC=1, weak answer must score 0 *and* trip ≥1 decoy (proves the trap is reachable, not declared), C0/H1 prompt byte-equality, C0-vs-H1 key must differ, seed variation, B0 guessability probe. Runs in a `python -I` stdlib sandbox. | `crucible/chain/validate.py`, `crucible/chain/sandbox2.py` |
| 4 | **Adversarial (hostile) review** | Cross-family reviewer recomputes the chain and answers 7 questions (key correctness, alternative valid analyses, shortcuts, trap quality, leakage/symmetry, ambiguity, ≥20 expert-minutes difficulty). Rejection feedback loops back into re-authoring, 3 attempts per slot. | `crucible/chain/author.py` (REVIEW_TEMPLATE), `crucible/chain/build.py` |
| 5 | **Judge meta-evaluation gate** | Judge qualification on construction-sound labels (weak answer is silent by construction → false-notice rate gate ≤0.25; stripped answer contains nothing to notice → ≤0.15), campaign blocked until a judge passes; a registered amendment when the original recall bar turned out to rest on a false assumption about reference answers. | `crucible/chain/meta_eval.py`, `analysis/preregistrations/campaign-3.0.0.md` Amendment 1 |
| 6 | **Campaign infrastructure** | Sharded restartable workers per system, repeats for pass^3, right-censoring rules, deterministic instance subsampling fixed before any run, usage ledger, spend guards (OpenRouter hard cap; 402-billing voiding rules), baseline-ladder integrity gates (B1/B8/B9 must read 0/1/0 or the headline is withheld), scorecard with Wilson CIs + cluster bootstrap over templates + hidden-vs-sealed memorization probe. Windows restart-proofing via scheduled tasks. | `crucible/chain/campaign.py`, `crucible/release_campaign.py`, `crucible/stats.py`, `runs/usage.jsonl` (2,311 records), `runs/launch_*.py` |
| 7 | **Truth boundary & release engineering** | Agent-visible bundle packaging with truth-leak scans by path, content hash, and canary marker; hash-chained append-only audit log; sealed split never published; sha256 release manifests; benchmark card with funding/entanglement disclosure. | `crucible/packaging.py`, `crucible/audit.py`, `crucible/leakgate.py`, `crucible/release_build.py`, `release/1.0.0/` |
| 8 | **Corrections governance** | Numbered, published corrections with content-blind voiding rules, retained voided outcomes for auditability, reduced denominators instead of silent exclusions, rescoring machinery. Nine to date (CORR-001..009). | `runs/corrections/`, `crucible/rescore.py`, `release/1.0.0/corrections*.md` |
| 9 | **Evidence base** | 23 benchmarks/methodology papers read in full; every design decision traces to a measured result (e.g. criterion-level judging −31.5% self-preference; reference-guided grading 70%→15% error; markdown bias +0.76). This is what tells you *which* gates to build before you pay to discover them. | `analysis/literature/README.md`, `analysis/literature/md/`, `analysis/crucible3_design.md` |

### The part that does not show up in a file listing: burned iterations

The pipeline's real cost is not the code — it is the discovery loops, each of
which consumed a build round or a full campaign:

- **The saturation event.** Campaign 3.0.0 measured **94–100% for frontier
  models against a single-digit design target**. Cause: the work orders handed
  over the method as an ordered checklist and printed the allowed categorical
  answers, so every judgment call was multiple choice. The numeric-only
  `leak_scan` missed it entirely. Cost: one full campaign burned + population
  regeneration. The fix is ~340 lines (giveaway gates + 10 tests) that a
  replicator does not know they need until they too burn a campaign.
  (`crucible/chain/spec.py` comments, `tests/test_giveaway_gate.py` docstring.)
- **The judge gate that blocked its own campaign.** Both judges failed the
  preregistered 0.85 recall bar (0.775 / 0.700); scoring stayed blocked while
  the cause was investigated; the bar itself was wrong (terse references resolve
  forks without narrating them) and was re-registered on labels sound by
  construction. Published notice-act gaps are now stated as conservative lower
  bounds. (`campaign-3.0.0.md` Amendment 1.)
- **Five build rounds** to get 8 surviving templates
  (`runs/chain_build*.log`), including one round where 28 of 30 slots crashed
  on a single generator-contract bug.
- **Nine corrections**, including CORR-004 (deterministic graders rejected
  scientifically correct answers over phrasing → verifier v1.0.3 + full
  re-verification), CORR-006 (one instruction change moved the native product
  13/28 → 24/28 with the mechanism isolated — false alarms on clean data
  8/10 → 1/10), CORR-007 (336 runs written against an exhausted credit line,
  all voided content-blind), CORR-008 (spend guard summed a field that was
  never recorded).

Each of these is a failure mode a replicator rediscovers at full price. The
gates are cheap to copy; knowing the gate has to exist is what was paid for.

---

## 2. What it actually cost us (documented)

**API spend to date, entire program (v1.0 + chain track + all experts, judges,
reviews, red teams):**

| Line | Amount | Basis |
|---|---|---|
| Anthropic (claude-opus-5): 584 calls, 3.02M in / 10.31M out | **$273** | `runs/usage.jsonl` × list price $5/$25 per MTok |
| OpenRouter (6 candidate systems) | **$300.50** | documented in CORR-007 (credits API: 300.50 used of 300.00 granted) |
| OpenAI (gpt-5.6-sol): 466 calls, 1.78M in / 2.60M out | ~$30–90 | tokens documented; price assumed in the frontier band |
| NVIDIA NIM (3 systems) | $0 | free-tier keys (CORR-009) |
| **Total** | **≈ $600–700** | |

**Per-component API cost (from the ledger's purpose field):**

- Generator authoring: 242 calls, 1.83M in / 7.48M out → **≈ $28 of API per
  surviving template** (author + hostile review, failures amortized in), at
  8 survivors.
- Hostile review: 107 calls, 1.31M in / 0.79M out.
- 1.0 campaign (828 preregistered runs, 9 systems): 1,372 calls,
  2.4M in / 16.7M out.
- Chain campaign runs: ~10.8k output tokens per run (observed, claude-opus-5)
  → the preregistered ~217 runs/system cost **on the order of $70–100 per
  system per campaign** at Opus prices; a full 9-system, ~5,900-call campaign
  at 300–400 instances lands **≈ $1.5–2k** even if every system priced like
  Opus.

**Wall clock:** the working tree spans ~66 hours (Aug 14 evening → Aug 16
afternoon) of continuous frontier-agent-assisted work — *with* a finished v1.0
implementation guide, the 23-paper literature review, and an operator who had
already internalized the failure modes. That is the floor, not the estimate for
a cold start.

**Yield (measured, not aspirational):** design doc says a third to a half of
authored templates survive; the logged batches show **5 built / 23 failed** in
the main round (~18–23%), and the most recent 6-slot batch under the
post-saturation gates went **0 for 30 author rounds** (17 machine-gate
failures, 13 hostile-review rejections). The dominant rejection is the reviewer
refusing to certify key correctness — the bar the whole design rests on and the
one we deliberately do not lower (`crucible3_design.md` §6b).

**Cold-start replication estimate for a competent lab team** (agent-assisted,
no access to our failure ledger): 6–10 calendar weeks and 200–500 skilled
person-hours — design/evidence pass (1–2 wks), pipeline (1–2 wks), then the
irreducible discovery loops (each saturation/gate/judge/grader incident costs a
build or campaign cycle; we logged eight such cycles) — plus $2–10k API at
300–400-instance scale. At $150–250/h loaded cost: **$30–90k of labor + API +
one to two quarters of calendar**, before anyone outside the lab trusts a
number it prints. The expertise profile is the binding constraint: the same
small team needs multi-domain bench science (12 science areas × 5 workflows in
the plan), psychometrics (unbiased pass^k estimators, cluster bootstrap over
templates, Wilson-not-Wald at floor rates, hazard analysis with right-censoring,
Brier/Murphy decomposition — all implemented in `crucible/stats.py` and
`chain/score.py`), eval security (leak/giveaway/shortcut/injection attacks),
and preregistration discipline (the willingness to block your own campaign when
your judge fails its gate).

---

## 3. The counterfactual: 500 static Q&A items

The apparently-cheap alternative, priced with the field's own published payment
schedules (archived locally):

**Direct cost.** GPQA's schedule per accepted question: $10 writer base +
up to $115 writer bonuses ($20 × 2 expert validators correct, $15 × 3
non-experts wrong, $30 both-experts bonus) + validator payments (experts
$10 base + bonuses; non-experts $10 + $30-correct each) — realized **~$95/hour
average, $150/hour max**, across 61 contractors (arXiv 2311.12022, archived).
Per fully-validated hard item: **≈ $150–300 in incentives alone**. Humanity's
Last Exam needed a **$500,000 prize pool** ($5,000 × top 50, $500 × next 500)
to net ~2,500–3,000 accepted questions from ~70k submissions — up to ~$200 per
final item in prize money before any organizer time (arXiv 2501.14249,
archived). HealthBench took **262 physicians across 26 specialties, 11 months**
(archived paper). So: **500 expert-validated static items ≈ $75k–150k plus
months of expert recruitment.** Comparable to replicating our entire pipeline —
for a strictly weaker instrument.

**What that money buys, per the field's own audits (all archived in
`analysis/literature/`):**

| Failure | Published magnitude |
|---|---|
| Wrong answer keys at the frontier tail | HLE bio/chem: **29 ± 3.7%** contradicted by literature (FutureHouse); HLE's own re-audit: 15.4% expert disagreement. GPQA Diamond: **~8%** invalid (Epoch). FrontierMath: ~7–10% error; v2 later corrected **42%** of problems. SWE-bench: **68.3%** of samples filtered in the Verified re-curation; fixing it moved GPT-4o 16% → 33.2% |
| Shortcut exploitability | CORE-Bench: **20 of 45** hard tasks answerable without the analysis, found only after saturation. Berkeley RDI: **100%** on Terminal-Bench / SWE-bench Verified / Pro without solving a single task; BenchJack: 219 flaws across 10 benchmarks |
| Single-use on release | MLE-bench: private labels recomputable from public data for **74/75** competitions even after patching. A static set leaks into training data once and is spent |
| No reliability, no controls | pass@1 point estimates; no clean-control/false-alarm symmetry, no per-stage diagnostics, no refusal-correct condition; Wei et al.: of 115 human baselines, median n=8, 1.74% ran a power analysis |

At single-digit frontier pass rates — where a flagship benchmark must operate —
an 8–29% key error rate is not a blemish; it is the signal. That is the
structural argument (`analysis/literature/README.md` §1), and it is why the
static alternative cannot be fixed by spending more on it.

### The economic asymmetry in one table

| | Static Q&A (500 items) | Constructed-truth chains (CRUCIBLE) |
|---|---|---|
| Fixed cost | Low (recruiting + rubric) | High (pipeline + gates + burned iterations) |
| Marginal instance | **$150–300, every time** (expert-hours) | **≈ $0** (a new seed; deterministic re-render, no model calls — `build.py`) |
| Marginal *template* | n/a | ≈ $28 API + review debugging at measured yield |
| Label error | 8–29% at the frontier tail | Structurally ≈ 0 (generator computes the key from data it generated); audited, not asserted |
| After contamination | Item is spent | Regenerate with fresh sealed seeds (`chain/rematerialize.py`); hidden-vs-sealed gap is monitored per system |
| Diagnostic yield | Right/wrong per item | Per-stage hazard, trap rate, notice–act gap, false-alarm rate on byte-identical clean controls, calibration |
| Gaming surface | Demonstrated 100%-without-solving exploits | Leak/giveaway gates at build time, B0/B1/B9 integrity gates at scoring time, judges can never touch the primary metric |

High fixed cost + near-zero marginal cost + regenerability is a classic
platform moat. Static item-writing is linear cost forever, with depreciation.

---

## 4. "Use theirs" vs "build our own", from a lab's chair

For a lab that wants this measurement (multi-stage scientific judgment under
attractive error, with reliability and false-alarm symmetry):

| Option | Cash | Calendar | Residual risk |
|---|---|---|---|
| **Run CRUCIBLE** (hidden + sealed splits, preregistered protocol) | ~$100–300 of inference per system per campaign; $0 authoring | Days | Inherits our disclosed limits (model-authored/reviewed, no human baseline) — all stated in the card |
| **Build equivalent in-house** | $30–90k labor + $2–10k API (est. §2) | 1–2 quarters | Rediscovers the failure ledger at full price; then owns a benchmark it grades its own models on — the "developers grade their own homework" problem the field already calls out (Lessons from the Trenches, archived); zero external trust at launch, no corrections history |
| **Write 500 static items** | $75k–150k expert incentives | Months (recruiting) | 8–29% key error at the tail, single-use, no path/reliability/control measurement at any price |

The cash ratio of adopt-vs-build is **roughly 100–300× per lab**, but the cash
is the smallest term. The two things a lab cannot buy at any speed are (a) the
failure ledger already encoded in our gates, and (b) the trust artifact — a
public preregistration trail, a corrections log that demonstrably voided our
own results (CORR-007 voided 336 runs; the judge gate blocked our own
campaign), and a sealed split that no fork of the public repo can reproduce.
Third-party legitimacy is precisely the thing an in-house benchmark lacks by
construction.

**Where the moat is honestly thin — name it before a competitor does:**

1. *The code is not the moat.* ~14k lines were assembled in days with frontier
   agents. Anyone with the same agents can copy the artifact. The moat is the
   gate list, the review bar, the sealed material, and the operating history.
2. *Single operator, single point of failure.* Much of the failure knowledge
   lives in code comments and one person's head. It is simultaneously the moat
   and the fragility (see recommendation 2).
3. *Templates, not instances, are the unit of statistical power* — 8 chain
   templates today. Instance count (144 → 300–400) buys contamination
   resistance, not power. The credible attack on us is "n=8 clusters"; the
   answer is the template expansion at the unlowered review bar, and honest
   cluster-level CIs meanwhile (`crucible3_design.md` §6b).
4. *LLM-verified truth.* Constructed truth means the *key* can't be mistyped,
   but a generator can still encode a wrong scientific model; the hostile
   review is model-based. Disclosed, and partially mitigated by determinism +
   dual-family review — but a human-expert audit of a template sample is the
   cheapest large credibility purchase available (recommendation 5).

---

## 5. Recommendations (ranked)

1. **Publish the moat itself: a "cost to replicate" page + the saturation
   post-mortem.** Turn §1–§3 of this document into a public artifact: the
   itemized bill, the measured yield (5/28, then 0/30 under tightened gates),
   the 94–100% saturation story and the gate that closed it, the corrections
   log. This converts our most embarrassing week into the strongest possible
   evidence that the gates are real, and it reframes every "we could build
   that" conversation into "here is the bill and the ways you will burn
   campaigns." Material already exists in-repo. **Effort: 1–2 days. Do first.**
2. **Write the failure-mode runbook (bus-factor fix).** Extract every encoded
   lesson — the 16 author rules' annotations, META_WORDS false-positive
   history, the greedy-fence parsing bug, thinking-budget truncation, the
   %-formatting rejection class, credit-preflight (CORR-007/008) — into
   `docs/RUNBOOK.md` with pointers to the incident that motivated each. The
   moat currently lives partly in one operator's head; that is the single
   biggest fragility of the flagship plan. **Effort: 2–3 days.**
3. **Productize "use theirs": publish per-system campaign pricing and a
   sealed-split evaluation service.** We already compute $/VCC and per-system
   cost in the scorecard; publish "evaluate your model: ~$X inference + $0
   authoring, preregistered protocol, hidden + sealed splits, results in
   days" as a standing offer. The sealed split (48 sealed instances today;
   seeds 14/16 never published) is the structural lock — a repo fork cannot
   reproduce it. Add the CORR-007 lesson as product hygiene: preflight credit
   checks before any campaign. **Effort: ~1 week including the service
   wrapper.**
4. **Preregister a seed-rotation policy: contamination resistance as a
   subscription.** Quarterly fresh sealed seeds via `rematerialize.py` at ≈ $0
   marginal cost, with the hidden-vs-sealed gap published per system each
   rotation. No static benchmark can match this economically — $150–300 per
   replacement item forever vs. our free seeds. This is the sharpest
   fixed-vs-marginal argument in public form. **Effort: policy doc + one
   scheduled job; days.**
5. **Buy the one credibility asset money can still buy: a human expert audit
   of a template sample.** Commission 2–3 domain scientists to independently
   recompute ~10 templates end to end (the review protocol in `author.py` is
   already the audit script; GPQA's realized ~$95/h is the price anchor —
   roughly $5–10k). Publishing an audited key-error estimate converts
   "structurally near-zero" from a claim into a measurement, and directly
   neutralizes the "LLM-reviewed truth" objection before a critic raises it.
   **Effort: ~2 weeks calendar, mostly waiting; highest credibility per
   dollar after #1.**
6. **Expand templates at the unlowered bar, and budget for the measured
   yield.** 30–40 surviving templates means ~130–200 authored attempts at
   observed yield: ≈ $1–2k of authoring API and review-debugging time — the
   cheapest part of the whole program. Never buy yield by loosening the
   reviewer (the design doc's own red line; HLE's ≤5-minute reviews are the
   cautionary case). Track power honestly: report template count next to
   instance count everywhere. **Effort: continuous; API ≈ $1–2k.**
7. **Open-core the gates, keep the trust layer.** Release the gate suite
   (spec/validate/giveaway tests + author/review contracts) under a permissive
   license so the field standardizes on our validity vocabulary — while sealed
   seeds, judge gold sets, and campaign history remain the service. Adoption
   of the open layer makes the closed layer more valuable, and a BetterBench-
   style compliance table (field baseline: 17/24 benchmarks ship no
   replication script, 3/24 report CIs — we ship both) makes the contrast
   legible. **Effort: ~1 week; do after #1 and #3 so the narrative lands.**
8. **Recruit 2–3 external labs for co-signed sealed campaigns.** Flagship
   status is conferred, not claimed: external groups run the preregistered
   protocol on the sealed split, co-sign the scorecard, and appear in the
   corrections governance. This is the cheapest path from "our benchmark" to
   "the benchmark," and it directly answers the same-family
   author/judge/candidate entanglement we disclose. **Effort: outreach-bound;
   start now, lands in months.**
