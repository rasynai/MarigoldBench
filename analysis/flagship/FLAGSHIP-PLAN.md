# FLAGSHIP-PLAN — CRUCIBLE-CHAIN: the unified plan to become the flagship open-ended science benchmark

Date: 2026-08-16. Status: adopted plan. Synthesizes the ten workstream reports in
`analysis/flagship/` (adoption-cases, moat-economics, distribution,
contamination-protocol, stats-standard, governance, positioning, launch-artifacts,
provider-incentives, failure-modes). Where workstreams conflicted, Section 2 records
the ruling and the reasoning; nothing below is an average of two positions.

Public name, used everywhere from this document forward: **CRUCIBLE-CHAIN**
(never bare "Crucible"; the deterministic 1.0 line is "the anchor track";
PERTURB-Bench is retired as a public name).

---

## 1. The thesis

Providers will adopt CRUCIBLE-CHAIN because it is the only instrument that can back
the science claims they are already making. Every lab's "PhD-level science" story
currently rests on saturating MCQ recall benchmarks whose answer keys carry 8–29%
published error (GPQA ~8% invalid and now scored above its own 69.7% expert ceiling;
HLE 29 ± 3.7% of its audited chem/bio slice contradicted by literature; FrontierMath
v2 corrected 42% of problems; SWE-bench rebuilt by OpenAI after filtering 68.3%),
and when those give out, labs fall back to unrepeatable evidence — anecdote papers,
bespoke expert panels, wet-lab one-offs. The capability slot they need —
**chained scientific judgment under attractive error**: 5–8 linked judgment calls,
each with a plausible wrong path, scored per stage with clean-control false-alarm
symmetry and a pass^3 reliability headline retrying cannot inflate — has no
incumbent. CRUCIBLE-CHAIN fills it with an economic asymmetry no static benchmark
can match: deterministic generators compute every answer from data they generated,
so key error is structurally ~0 (audited, not asserted), a marginal instance costs
~$0 against $150–300 per expert-validated static item, and a contaminated or burned
split regenerates from fresh seeds for CPU cost — contamination becomes a
bookkeeping event and refresh a seed, not a permanent authorship tax. For a lab,
using it costs ~$100–300 of inference and days of calendar; replicating it costs an
estimated $30–90k of labor plus one to two quarters, and the two assets money cannot
buy at any speed: the paid-for failure ledger encoded in our gates (a burned
94–100% saturation campaign caught in-house pre-launch, a judge gate that blocked
our own scoring, nine published corrections and a tenth being written), and the
trust artifact that ledger produces — the benchmark that audits itself before
outsiders can. Adoption is then won the way every flagship won it — one
frontier-lab launch-table row forces every competitor to answer the number — and
the pitch that earns the row is a post-fix headline in the 5–45% visible-progress
band, per-stage hazard diagnostics valuable to a lab's eval team even at VCC = 3%,
and governance (no funder access to sealed splits ever, cryptographic commitments,
published COI policy) that clears the bar FrontierMath set by failing it.

---

## 2. Conflict rulings

Explicit decisions where workstreams disagreed. Each names the sides and the ruling.

**C1. Launch scale: ~30–40 templates now vs the ≥120-template statistical standard.**
stats-standard proves 8 templates supports no public claim and sets ≥120T×3 (or
200T×2; floor 100T) as the requirement for 5–8 pp paired resolution; moat-economics
measured template yield at 18–23% (and 0/30 in the first post-saturation-gate batch)
and budgets 30–40 templates as the realistic next wave; positioning gates the word
"flagship" on ≥30 templates. **Ruling: phase it, do not average it.** The launch
campaign runs at ≥30 templates × ~7 evaluated instances (~217+ runs/system, the
prereg-3.0.0 shape) and prints its honest Holm-corrected MDE (~10–13 pp): frontier
tiers separate, adjacent pairs publish as ties, and the scorecard says so verbatim.
The ≥100-template floor (target 120T×3 or 200T×2) is adopted as a **hard requirement
for steady state, dated within two quarters of launch**. We do not delay launch to
2027 waiting for 120 templates (the slot vacates on HLE-saturation timing, not
ours), and we do not lower the review bar to buy yield (moat red line). Template
count is printed beside instance count in every artifact.

**C2. Self-serve harness vs maintainer-run-only scoring.** adoption-cases demands a
<2h/<$50 self-serve path ("without it you are FrontierMath"); launch-artifacts says
maintainer-run scoring is the only honest policy and deliberately skips a self-serve
hidden-split harness; distribution proposes a two-tier service. **Ruling: split the
question by split; scoring authority is never distributed.**
- DEV split: fully self-serve — Inspect-native package, one command, truth included,
  per-user regenerable. This satisfies the <2h/<$50 eval-team test.
- OPEN/hidden split: self-run **inference** is welcome; **scoring is centralized**
  (submissions scored server-side against withheld truth, CritPt/GAIA model), with a
  SWE-bench-style verified badge from maintainer spot re-runs. Self-*reported*
  scores never appear anywhere.
- LIVE/sealed split: maintainer-run only, under ZDR agreements, freshly minted per
  campaign. This is the endorsement channel, not a product compromise.

**C3. "Engineer the launch number" vs the negative-result commitment.**
adoption-cases R1 says the headline must land ~5–45% with separation; governance and
the charter forbid tuning results. **Ruling: difficulty is engineered ex ante and
preregistered — K mix (5–8), decoy floor at 3·tol, giveaway gates — never selected
post hoc on model failure (that is exactly HLE's key-error trap). The campaign
publishes whatever it measures.** If all systems land <5% pass^3, the ladder,
survival curves, and hazard diagnostics carry the launch and the version-treadmill
review runs in the other direction; if any system lands >30%, the saturation
tripwire (Section 6) fires. The band is a design target, not a reporting filter.

**C4. Generator publication and RLVR licensing.** The old design (§7: "generator
code published after the first campaign with fresh seeds reserved") is void —
contamination-protocol showed seeds are enumerable once generators are public.
moat-economics wants the gate suite open-cored; provider-incentives wants the
dev-split generator offered as an RLVR training environment. **Ruling: adopt keyed
minting (HMAC epoch key), publish generator source only per retired template;
open-core the gate suite and authoring/review contracts (spec/validate/giveaway
tests) which contain no instance-generating code; RLVR licensing is offered only
for retired template families, never live ones, with trained-on-generator labs
flagged on the scorecard and the epoch refresh cadence as the enforcement
mechanism.**

**C5. Version identity.** governance flags the 0.2→0.3→1.0→3.0 line as a public
contradiction; contamination-protocol specifies the two-axis scheme; positioning
freezes the name. **Ruling: the public chain line resets to CRUCIBLE-CHAIN v1.0
under the two-axis scheme (`v<MAJOR>.<MINOR> @ e<YYYY.MM>`); internal campaign
label 3.0.0 maps to "CHAIN v1.0 @ e2026.09" with one lineage paragraph in the
benchmark card. No public 3.0 without a 2.x.**

**C6. Epoch cadence: quarterly subscription vs per-campaign.** moat-economics
proposed preregistered quarterly seed rotation; contamination-protocol specifies
one epoch per campaign, minimum one per 6 months, plus out-of-cycle triggers.
**Ruling: contamination-protocol's spec supersedes — epochs are campaign-bound
(min 6-month cadence, liberal out-of-cycle triggers at ~$0 marginal cost). A
calendar promise we might not campaign against is theater; a trigger table is not.**

**C7. Capability-slot vocabulary.** adoption-cases proposed "chained scientific
judgment under deception"; positioning owns "attractive error" and shows
"deception" is wrong for the third of instances that are clean controls.
**Ruling: the slot is "chained scientific judgment under attractive error";
the canonical sentence in positioning §1 is pasted verbatim in every artifact.
"Deception"/"adversarial data" do not appear in our materials.**

**C8. Human baseline vs human audit.** Anthropic's intake expects human-expert
baselines; launch-artifacts deliberately skips a human-performance study.
**Ruling: no human performance baseline — the B0–B9 baseline-ladder stance is
principled and the paper owns it rather than apologizes. Human money buys
correctness instead: a paid expert audit of ~10 templates + ~50 judge verdicts
($5–10k), converting "near-zero key error" from construction argument to
measurement. The Anthropic application states this position plainly.**

**C9. Charter vs leaderboard/marketing.** The pilot charter forbids a public
leaderboard and capability marketing; four workstreams need both. **Ruling: amend
the charter through its own governance process (minuted, before launch work):
flagship goals replace pilot non-goals; "maintainer-run verified leaderboard, no
self-reported scores" replaces "no leaderboard"; the prohibited-claims list is
retained unchanged — it is the brand, not a casualty.**

**C10. Outreach timing.** moat says recruit external labs "now"; provider-incentives
says nothing works until a populated scorecard exists. **Ruling: prepare now,
engage on the number.** Policies, ZDR template, pitch briefs, and the private-preview
lane are built during Phases 1–2; no lab conversation is initiated until the Phase 2
scorecard is populated. The one exception: quiet pre-launch preview offers to eval
teams (results private, METR terms) may go out as soon as the campaign
infrastructure has scored its first post-fix systems, because that lane produces no
public number.

**C11. Lineup size.** CORR-009 fixed the campaign lineup at 5 frontier systems;
positioning gates "flagship" language on ≥6 evaluated frontier systems.
**Ruling: the campaign hard minimum is the CORR-009 five-lineage rule; the target
is 6–8 lineages (fund the OpenRouter top-up per CORR-007 with preflight credit
checks; add third-family/NIM lineages where frontier-credible). The word
"flagship" is not used publicly until ≥6 lineages are evaluated post-fix. Until
then the register is "new benchmark, unusually strict validity program".**

---

## 3. The ordered execution plan

Budget envelope to launch: ≈$10–20k total (campaign inference ~$1.5–2k, authoring
~$1–2k, human audit $5–10k, bounty prizes $1–3k, infra/registrations <$500).
Solo-operator plan; Phase 5 explicitly ends the solo condition.

### Phase 0 — Existential fixes (days; target 2026-08-18; nothing else matters first)

Artifacts:
1. `git init`; first commit = current state; private remote; dry-run `git add -An`
   audit of the CORR-005 truth boundary before anything is staged; encrypted
   off-machine backup of `tasks_chain_sealed/`, `tasks_sealed/`, `registry/`,
   `.secrets/` rotated out of the tree.
2. LICENSE (Apache-2.0 code / CC-BY-SA-4.0 tasks), CITATION.cff, CONTRIBUTING.md,
   `pyproject.toml` version + license alignment.
3. Name freeze: CRUCIBLE-CHAIN everywhere; repo slug `crucible-chain`; GitHub org +
   HF namespace + domain registered; collision re-sweep + basic word-mark check;
   no-affiliation FAQ line (PerturBench / Dreadnode / Galois).
4. Charter amendment per C9, minuted.
5. External anchoring: OpenTimestamps `.ots` proofs on build manifests, all
   preregistrations, and the audit-chain head; Zenodo DOI for the 1.0.0 release
   package; salted Merkle-root commitments to both sealed directories published in
   the manifest.

Acceptance: repo under version control with off-machine backup and public,
third-party-timestamped commitments; license/citation present; one public name;
amended charter recorded. Every later credibility claim now reduces to something
checkable instead of "trust the author's filesystem".

### Phase 1 — Protocol lock-in (~1 week; hard gate: nothing is minted before this lands)

Artifacts:
1. **Contamination/versioning protocol adopted in code and card** (full spec in
   Section 5): two-axis versioning, DEV/OPEN/LIVE/VAULT split taxonomy as
   constants in `chain/build.py`, keyed minting via HMAC epoch key, per-provider
   burn ledger (candidate and judge calls), GUID canary (BIG-bench superset) on
   every distributed file, leakgate extended to forbid quoting unretired
   LIVE/OPEN text.
2. **Statistical standard implemented** (full requirements in Section 4):
   `crucible/chain/paired.py` (paired clustered SE, t_{T−1} CI, exact McNemar,
   sign-flip permutation), interval fixes (n_eff = N/DEFF everywhere, wild cluster
   bootstrap for legacy T<30), pass^3 cluster-bootstrap CI, the ten-line scorecard
   block, judge kappa + PPI machinery, post-campaign re-estimation loop.
3. **Governance consolidation**: root `CORRECTIONS.md` index with the A/B/C/D class
   taxonomy; missing records written (CORR-005, CORR-008) and **CORR-010 for the
   chain-track saturation event**; the 1.0.0 card/signoff divergence fixed under
   the new rule "a correction regenerates every document displaying the number";
   one-page versioning policy; standing COI policy naming all four conflicts
   (judge families, builder-runs-everything, vendor API exposure, sponsor product)
   with the judge-swap sensitivity row added to scorecards; provider access +
   independence charter (no funder access to sealed splits, no per-task lab
   funding, full disclosure, sealed-holdout-from-everyone, named intake channel) —
   published while the answer is still "self-funded, no lab money".
4. **Expansion preregistration registered externally** (OSF + OTS-stamped, pinned
   to a tagged commit): design (C1 shape), multiplicity families, MDE table,
   lineup rule (C11), named secondary axes (lowest false-alarm, best premise
   pushback, best calibration, deepest median chain — fixed now, never post hoc),
   the full tripwire table (Section 6), keyed-mint commitments, and the analysis
   code hash.

Acceptance: prereg is live on infrastructure we cannot edit, referencing every
protocol above; CI runs the test suite including giveaway gates on every push;
zero epoch-e1 instances exist yet.

### Phase 2 — Population expansion and the launch campaign (~weeks 2–6)

Artifacts:
1. **Template expansion at the unlowered bar**: ≥30–40 surviving templates
   (~130–200 authored attempts at measured yield, ~$1–2k API); third-family
   template author added to the rotation; ≥2 template families held out of all
   public splits; authoring-contract iteration against the new gates with an
   explicit checkpoint — if yield stays <10% after two contract revisions, audit
   the gates for false positives (META_WORDS precedent) rather than lowering the
   review bar.
2. **Epoch e2026.09 mint** under keyed scheme: 300–400+ evaluated instances across
   conditions, byte-identical C0/H1 maintained, commitments published per prereg.
3. **The campaign**: credits funded with preflight checks (CORR-007 lesson); 5–8
   frontier lineages (C11) + full baseline ladder (B0/B1/B9 integrity gates) +
   pinned open-weight anchors; 3 repeats on hidden instances for pass^3; judges
   pass the meta-eval gate before scoring; burn ledger records every provider
   exposure.
4. **Scorecard under the new standard**: ten-line block, pairwise WIN/TIE/LOSS
   matrix, MDE sentence verbatim, BH-corrected hazard grids, contamination
   telemetry columns, hidden-vs-sealed (OPEN-vs-LIVE) gap, **author-family ×
   candidate-family cross-table** (pre-empting the most likely exposé).
5. **Human expert audit** commissioned in parallel: 2–3 domain scientists recompute
   ~10 random templates + ~50 judge notice-verdicts (~$5–10k at the GPQA ~$95/h
   anchor); report published verbatim → the audited key-error estimate.

Acceptance: populated scorecard with ≥5 (target ≥6) lineages, integrity gates
green; headline band check per C3 with the pre-committed contingency; audited
error estimate published; author-family cross-table published (clean, or published
with mitigation). This phase is the gate for everything downstream — an empty
systems table is unanswerable in any lab conversation.

### Phase 3 — Launch package (overlapping, ~weeks 4–8; ships as one bundle)

Artifacts (each cross-references the others — shipping a subset reads as a research
artifact, not a flagship):
1. **arXiv paper** (the long pole — skeleton starts in Phase 1 from
   `crucible3_design.md` + `literature/README.md`; results slot in from Phase 2).
   Thesis: constructed truth makes single-digit pass rates meaningful because key
   error is structurally ~0 while every rival's key error exceeds its signal.
   Owns the no-human-baseline stance (C8). Target: arXiv in launch week;
   NeurIPS/ICML datasets track submission.
2. **Public repo** under `crucible-chain` via the `release_build.py` export
   pipeline with leakgate as blocking CI; open-cored gate suite + contracts (C4).
3. **Inspect-native `crucible_chain` package**: `inspect eval` one-liner against
   any provider on the DEV split; simultaneously the AISI format, the
   documentation standard Anthropic names, and the lab self-run path.
4. **Gated HF dataset** (DEV with truth; OPEN prompts only), GAIA-style terms +
   canary; **leaderboard** (HF Space scoring submissions server-side, custom
   domain at paper time): pass^3 sole headline with the ladder
   pass^3 ≤ pass@1 ≤ pass@3, Wilson/clustered CIs, rank tie-groups, the
   pass^3-reads-as-zero explainer, C0/H1/F2 and hazards as diagnostics.
5. **Transcript gallery**: 6–10 annotated C0/H1 matched pairs (byte-identical
   prompt, one pass one fail, per-stage hazard annotated), dev-split only,
   leakgate-verified — the thesis demonstrated in one screen.
6. **Narrative artifacts**: the saturation post-mortem methods note ("we saturated
   our own benchmark in a day; here is the gate that makes it structural" — 53/56,
   56/56, before/after prompt excerpt, giveaway_scan as released code); the
   label-error comparison one-pager ("the answer key is computed, not
   crowdsourced"); the cost-to-replicate page; launch blog built on the CORR-006
   false-alarm story + the saturation catch; `PITCH.md` with the three audience
   sentences + mandatory limitations block.
7. **External adversarial pass**: two-week scoring-exploit bounty on the truth
   boundary and graders (dev split scope; confirmed breaks become credited CORRs);
   2–3 named external reviewers with verbatim published notes including dissent;
   one external reproduction of one scorecard row.

Acceptance: every artifact live and interlinked; leakgate green on all public
surfaces; bounty results in the corrections log; positioning gates (C11) met
before the word "flagship" appears.

### Phase 4 — Adoption engine (weeks 6–16, then ongoing)

Artifacts:
1. **Private-preview lane on METR terms**: NDA sealed-split run on a freshly
   minted LIVE block, ZDR agreement template, cost cap, 48h turnaround timed to
   lab launch cycles, full per-stage diagnostic report (hazard spike location,
   notice–act gap, false-alarm rate, calibration quadrant — the product for eval
   teams even when VCC is unquotable); lab may withhold its v1 number; subsequent
   campaigns are publish-by-default with "declined" printed under the declared
   lineup rule.
2. **Two-tier evaluation service** (C2): self-run verified tier (predictions +
   per-stage trajectories + logs PR'd, centrally scored, spot re-run badge) and
   creator-run sealed tier (per-customer regenerated split — the differentiator
   no static benchmark can match), each with published pricing (~$100–300
   inference, $0 authoring).
3. **Outreach sequence** (order fixed): Anthropic third-party-evals application
   (Inspect package + criteria mapping + seeds-backed plan to 1,000+ instances);
   Epoch Benchmarking Hub as "benchmark creator-run"; Artificial Analysis pitch
   (uncovered index category + CritPt-style grading-server integration);
   ARC-style ZDR sealed-campaign offers to OpenAI/GDM eval teams (partnership
   sale — no submission door exists); HAL when unpaused. Six per-lab pitch briefs
   with named program hooks; invitation to co-develop a "Verified"-style tier so
   a lab's name is on the QA (the SWE-bench play); chase one co-announced result
   (the o3/ARC pattern).
4. **Registry entries post-paper**: inspect_evals registration; anchor-track
   subset as lm-eval YAML task + HELM scenario, explicitly labeled anchor-only.
5. Optional manufactured moment: workshop challenge; modest prize for first
   pass^3 ≥ 50% on sealed.

Acceptance: ≥1 frontier lab has run the sealed split (privately or publicly)
within one quarter of launch; listed by ≥1 independent runner; ≥2 external
co-signed campaigns within two quarters — the conversion of "our benchmark" into
"the benchmark".

### Phase 5 — Steady state and franchise keeping (quarterly)

Artifacts:
1. Epoch per campaign (min 6-month cadence): mint → gate → commit → campaign →
   publish → retire, with the full telemetry table (Section 5) each time;
   anchor equating across epochs.
2. **Template growth to the statistical standard** (C1): ≥100 templates hard
   floor, target 120T×3 or 200T×2, within two quarters of launch; ρ, ρ_d, q,
   DEFF, MDE re-estimated every campaign and fed to the next prereg.
3. Version treadmill executed on tripwire (Section 6): CHAIN-v2 levers designed
   now — K→10–12, multi-defect H1, subtler decoys at the 3·tol floor,
   cross-artifact forks.
4. **Bus-factor retirement**: `docs/RUNBOOK.md` (every encoded failure-mode
   lesson with incident pointers), `governance/SUCCESSION.md` + dead-man's switch
   ("if unmaintained 6 months, sealed hashes/generators/seeds auto-publish" —
   abandonment becomes an open-sourcing event, not a silent death), 1–2
   co-maintainers with release rights, CI on every push.
5. BetterBench-style self-assessment scorecard published; corrections cadence
   continues; versioning/deprecation policy honored (v1.x frozen for card
   citability; regeneration at measured saturation).

---

## 4. Statistical scale requirements (adopted as hard requirements)

From stats-standard, binding on every campaign and public number:

1. **Cluster unit is the template, preregistered.** Every published interval is
   template-clustered: primary intervals use clustered SE with t_{T−1} once
   T ≥ 30; Wilson intervals run on n_eff = N/DEFF with DEFF = 1+(m̄−1)ρ; any
   legacy T < 30 table uses the wild cluster bootstrap; percentile bootstrap is
   demoted to sensitivity. The cluster count is printed inside every interval
   line ("95% CI x–y, T clusters").
2. **Every model-vs-model claim is a paired, clustered, multiplicity-corrected
   difference or it is a tie.** Paired clustered SE (Miller Eq. 8), exact McNemar
   on discordant runs, template sign-flip permutation as primary p when T < 30;
   the scorecard prints a WIN/TIE/LOSS matrix with Δ, SE, CI, correlation, and
   Holm-adjusted verdicts. "A outperforms B" is used only for Holm-significant
   pairs. No rank column without this matrix.
3. **Multiplicity families preregistered per campaign**: Family 1 primary
   pairwise claims under Holm–Bonferroni; Family 2 diagnostic grids
   (conditions, per-stage hazards, calibration) under Benjamini–Hochberg
   q* = 0.05; Family 3 simultaneous display CIs with Bonferroni-widened z.
4. **pass^3 carries a CI** (cluster bootstrap over templates of per-instance
   unbiased estimates) and is always printed inside the ladder
   pass^3 ≤ pass@1 ≤ pass@3 with the reads-as-zero explainer (hard zero below
   pass@1 ≈ 8%). Unbiased combinatorial estimators only; plug-in forms banned.
5. **MDE is stated before any run and printed after**: every prereg contains the
   MDE table for its design; every scorecard prints the verbatim sentence "This
   campaign separates systems differing by ≥X pp (paired, template-clustered,
   Holm-corrected across m primary comparisons, power .80). Smaller gaps are
   reported as ties."
6. **Scale floors** (C1): launch campaign ≥30 templates × ~7 evaluated instances
   (~217+ runs/system), honest MDE ~10–13 pp printed; steady state ≥100 templates
   hard floor, target 120T×3 or 200T×2 within two quarters; no campaign below
   100 templates may claim adjacent-pair separations under 10 pp; 2–3 pp gaps
   are published as ties by design (they require ~1,600+ paired runs; pooled
   fresh-template campaigns may eventually resolve them).
7. **Repeats buy reliability, not precision**: 3 repeats on hidden instances for
   pass^3 (real signal for mid-tier systems, flip rates 0.20–0.67); repeats are
   never counted toward separation power; only new templates buy effective n.
8. **Judge-derived metrics** (advisory only, never touching VCC): gold-set
   agreement and kappa with bootstrap CIs; PPI-rectified means against the 40–60
   item gold set; the sentence "judge verdicts cannot alter VCC" in every
   scorecard.
9. **Self-calibration loop**: ρ, ρ_d, q, DEFF, and achieved MDE re-estimated
   automatically after every campaign and fed into the next preregistration.
10. **The ten-line scorecard block** (denominators, ladder, condition panel,
    pairwise matrix, MDE, multiplicity note, calibration, hazards, judge block,
    provenance) is the mandatory format; a line that cannot be printed states why.

---

## 5. The contamination and versioning protocol (adopted)

The contamination-protocol workstream's scheme is adopted wholesale, with C4/C6
rulings applied. Flagship claim language: **"contamination-resistant by refresh,
contamination-measured by design" — never "contamination-proof"** (prohibited).

1. **Two-axis identity**: `CRUCIBLE-CHAIN v<MAJOR>.<MINOR> @ e<YYYY.MM>`.
   MAJOR = construct/scoring change (bridge study required across it); MINOR =
   population change within construct; epoch = a mint event under one epoch key.
   A score without an epoch label is invalid for the leaderboard. Public reset
   per C5: the expansion campaign is CHAIN v1.0 @ e2026.09.
2. **Split taxonomy per epoch per template**: DEV (1 seed; prompts+truth public;
   known-burned bait and twin-probe base) / OPEN (2; prompts public, truth at
   retirement; self-serve inference, central scoring) / LIVE (2; unpublished
   leaderboard split, maintainer-run only) / VAULT (1; never leaves local
   infrastructure, never any third-party API, judge calls included). The split
   formerly called "sealed" that transited OpenRouter is LIVE by definition;
   VAULT is the never-API set used for audits, post-leak forensics, and
   written-agreement private evals; any use burns and rotates the touched
   instances.
3. **Keyed minting and commitments**: per-instance RNG =
   HMAC-SHA256(epoch_key, template_id || split || index); the prereg publishes
   the key commitment plus a sha256/Merkle manifest over every minted file
   including truth; retirement reveals key + truth so anyone regenerates
   byte-for-byte; generator source publishes only per retired template.
4. **Evaluation is exposure — account for it**: per-provider burn ledger with one
   event per (instance, provider, channel, timestamp) for candidate and judge
   calls; a LIVE instance evaluated via provider P is burned-for-P; P's next
   model generation is scored on a virgin block (free via rematerialize).
5. **Behavioral telemetry, published every campaign beside the headline**:
   B0 prior-only floor; Δ_contam (stale retired-OPEN vs fresh LIVE, paired per
   template, cluster CI); twin-probe hit rate (DEV twins perturbed >3·tol) and
   C0/H1 answer-consistency; canary-emission probe; corpus/mirror scan summary
   (exact-search canary + internal rare-string fingerprints; labeled
   verbatim-only assurance); anchor drift vs previous epoch (2 pinned
   open-weight anchors, local inference; API anchors forbidden); the burn table;
   Min-K% advisory rows for open-weight candidates. Detectors are published,
   never trusted: no scan ever "clears" the benchmark.
6. **Cadence and lifecycle**: mint → gate (full validity suite incl. leak/giveaway
   scans, hostile review, B0 probe) → commit → campaign → publish → retire.
   One epoch per campaign, minimum one per 6 months. Out-of-cycle triggers (any
   one suffices): leakgate violation; canary/fingerprint hit; Δ_contam CI
   excluding 0 for ≥2 systems; burned-for-P block facing P's new model; a
   correction changing instance content. Marginal trigger cost is CPU + a prereg
   addendum — use it liberally.
7. **Canary + terms**: `crucible:<split>:<epoch>:<GUID>` (BIG-bench superset) on
   every published file; gated HF distribution with no-train/no-crawlable-reshare
   click-through; plain GitHub carries DEV only.
8. **Standing policies**: ≥2 template families held out per MAJOR; retire a
   template when its per-stage hazards collapse while B0 stays flat (idiom
   learned); nothing quoting unretired LIVE/OPEN text is ever published
   (leakgate-enforced); comparability across epochs verified by anchors, across
   MAJOR only via bridge study.

---

## 6. Top 5 risks, each with tripwires and pre-committed responses

Ranked by expected damage (probability × severity, from the pre-mortem). The full
tripwire table is preregistered in the Phase 1 prereg — firing a tripwire triggers
the written response, not a meeting.

**R1. Maintainer abandonment / infrastructure loss (P 50–70%; the default death).**
One operator, until Phase 0 one machine, bus factor 1; BIG-bench died archived with
Google behind it. Tripwires: no release in 6 months; a campaign scorecard empty
>30 days; maintainer commit gap >8 weeks; corrections stop appearing. Response:
Phase 0 backups make death non-silent; SUCCESSION.md dead-man's switch
auto-publishes sealed hashes, generators, and seeds — abandonment becomes an
open-sourcing event; co-maintainer recruitment is a Phase 5 acceptance criterion,
not an aspiration.

**R2. Contamination scandal / unprovable custody (P 25–35%; instant damage).**
Strong design, but until Phase 0/1 no cryptographic custody, and "sealed" was
semi-private in ARC terms. Tripwires: OPEN-vs-LIVE (hidden-vs-sealed) pass@1 delta
beyond the preregistered margin (10 pp with non-overlapping clustered CIs) for any
system; Δ_contam CI excluding 0 for ≥2 systems; any canary emission by a model;
any corpus/mirror fingerprint hit. Response: freeze the headline, out-of-cycle
epoch (fresh mint, ~$0), publish the probe result either way, per-provider burn
accounting names who saw what — the accusation becomes checkable arithmetic, and
regeneration (not retraction) is the recovery no static benchmark has.

**R3. Solo-author / model-graded distrust (P 40–50%; blocks adoption rather than
kills).** No human has verified a template; the same two model families author,
judge, and are evaluated. Tripwires: first external coverage leads with
"solo"/"AI-graded"; a lab declines evaluation citing governance; the
author-family × candidate-family cross-table shows a significant interaction;
reviewers ask for the human-verification rate while it is zero. Response: the
Phase 2 paid expert audit (published verbatim) retires "zero humans checked this";
the cross-table is computed and published by us before a hostile party computes
it; third-family authoring; external reviewers with published dissent; co-signed
external campaigns convert disclosure into independence.

**R4. Saturation (P ~60% absent a treadmill; survivable if planned).** It already
happened once (94–100% via leaked recipes/answer menus) and was caught in-house;
the residual bound is arithmetic: at per-stage p = 0.93 and K ≤ 8, chains pass
~60%. Tripwires (preregistered): any system's hidden pass@1 >30% → CHAIN-v2
authoring starts; pass@1 >60% or trap rate <10% for two systems → version declared
legacy at the next campaign with a published post-mortem; per-stage hazard profile
flattening toward uniform → retrospective giveaway audit of newest templates;
B0 creeping up across campaigns → seed rotation. Response: the version treadmill
(K→10–12, multi-defect H1, subtler decoys, cross-artifact forks) with the
successor pre-announced ARC-style — versioning before saturation keeps the
franchise; unmaintained saturation forfeits the name to other people's variants.

**R5. Avoidance, asymmetric scores, and better-marketed competitors (P 50–60%;
slow irrelevance).** Labs cite only wins; the danger case is one lab at 20% and
five silences; HLE beat better instruments with a press machine. Tripwires: a
lab-backed science-process benchmark announces with per-stage scoring; model
cards cite a competitor for "scientific reasoning"; only one lab ever cites us;
CRUCIBLE-CHAIN appears in surveys without a score. Response: the private-preview
lane gives eval teams value with no public number (METR proves all six labs accept
this shape); the declared lineup rule prints "declined" so silence is visible;
four preregistered winnable secondary axes give multiple labs a citable first
while pass^3 stays the sole headline; the launch bundle (paper + post-mortem +
label-error table + leaderboard) is our press machine, and the co-announce chase
(R4/Phase 4) is the fame event we actively engineer rather than await.

---

## 7. What we explicitly will NOT do

Money and governance:
- Never grant any funder or evaluated party access to sealed/LIVE/VAULT splits;
  no per-task lab funding; no exclusivity; all funding and data-access agreements
  disclosed before results ship (the FrontierMath lesson, applied on day one).
- No verbal agreements; ZDR and data-access terms are written or the run does not
  happen.

Population and truth:
- Never buy template yield by loosening the hostile-review bar, and never select
  or retain items because models fail them (adversarial filtering imports key
  error — HLE's trap).
- No crowdsourced or static item authoring; no paid question tournaments.
- Never publish truth for unretired instances anywhere, in any format; never
  publish live generator source (retired templates only); never publish anything
  quoting unretired LIVE/OPEN text.
- No human-performance baseline study; the B0–B9 ladder stance is owned publicly
  (human money buys correctness audits instead).

Scoring and claims:
- No self-reported scores on the leaderboard, ever; no fully-automated
  open-submission scoring of arbitrary checkpoints; scoring authority stays
  centralized (grading-server model).
- No headline other than pass^3 with its ladder; no partial credit in the
  headline (diagnostic views only); no post-hoc secondary axes or medals.
- No separation claims below the printed MDE (ties by design); no comparisons
  across harness classes, tracks, or MAJOR versions without a bridge study;
  no unclustered intervals.
- Prohibited claim vocabulary stands permanently: no "contamination-proof",
  "human-level", "PhD-level", "expert-level", or discovery claims; no causal
  product-vs-model comparisons; every public number travels with the
  limitations block.

Naming and packaging:
- Never bare "Crucible" in public; PERTURB-Bench never appears publicly again;
  no "flagship" language before the C11 gates are met.
- Do not wait for inspect_evals/HELM/lm-eval acceptance to ship our own Inspect
  package; do not build on HAL or any paused third-party infrastructure as a
  dependency; the anchor-track registry entries are labeled anchor-only so they
  are never mistaken for CHAIN.
- No encrypted-channel theater or security claims beyond the two-secret surface
  (epoch key, fingerprint index) under existing `.secrets/` discipline; no
  API-model anchors for cross-epoch equating.
- Numbers change only via a correction record, and a correction regenerates every
  document that displays the number — no silent edits, no deletions, voided
  artifacts are quarantined and kept.

---

## Provenance

Source reports (all read in full for this synthesis): `adoption-cases.md`,
`moat-economics.md`, `distribution.md`, `contamination-protocol.md`,
`stats-standard.md`, `governance.md`, `positioning.md`, `launch-artifacts.md`,
`provider-incentives.md`, `failure-modes.md` (this directory). Key repo evidence
inherited from them: `crucible/chain/spec.py` (giveaway gates),
`crucible/chain/rematerialize.py`, `crucible/leakgate.py`,
`analysis/preregistrations/campaign-3.0.0.md`, `runs/corrections/CORR-001..009`,
`release/1.0.0/`, `analysis/statistical_power.md`, `docs/LIMITATIONS.md`,
`governance/program_charter.md`.
