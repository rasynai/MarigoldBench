# Pre-mortem: the seven ways the flagship bid dies

Status: working document, 2026-08-16. Scope: CRUCIBLE-CHAIN's bid to become the
flagship open-ended science benchmark. Method: every claim below is grounded in
either (a) files in this repository (paths cited inline) or (b) a named external
source (local full texts under `analysis/literature/`, plus eight primary web
sources listed at the end). Probabilities are stated as P(the mode materially
threatens the flagship bid within 24 months) and are judgment calls from the
cited reference classes, not measurements.

## Scoreboard

| # | Failure mode | P (24mo) | Speed of death | Current defense | Verdict |
|---|---|---|---|---|---|
| FM-6 | Maintainer abandonment / infrastructure loss | **50-70%** | silent, by default | weakest | the most likely *actual* death, and the cheapest to fix |
| FM-2 | Contamination scandal | 25-35% | instant, hard to recover | strong design, **unprovable custody** | one hostile blog post from being unanswerable |
| FM-7 | Distrust of a solo-authored, model-graded benchmark | 40-50% | blocks adoption rather than kills | strong disclosure, zero independence | disclosure is necessary but not sufficient |
| FM-1 | Saturation within months | ~60% absent a treadmill | slow, survivable if planned for | strongest (one near-miss already caught) | needs tripwires + a version treadmill, not more gates |
| FM-4 | Competitor with better marketing | 50-60% | slow irrelevance | **nonexistent** (charter forbids marketing) | the pilot charter now contradicts the flagship goal |
| FM-5 | Gaming / overfitting the public split | 25-30% (successful, undetected) | reputational, detectable | strong | needs monitoring + seed rotation, both cheap |
| FM-3 | Judge-bias exposé | 15-25% | embarrassing, recoverable | strongest in the field | real residual is *author*-family bias, which is unmeasured |

---

## FM-1. Saturation within months

**Kill mechanism.** Frontier capability rises until the headline is 90%+, the
benchmark stops discriminating, and attention moves on. The field's velocity:
Humanity's Last Exam went from <10% at launch (Jan 2025, [HLE paper, local:
`analysis/literature/md/2501.14249.md`]) to 38.3% (Gemini 3 Pro) on the public
leaderboard by Aug 2026 ([lastexam.ai](https://lastexam.ai)) — roughly 4x in 18
months. ARC-AGI-1's private-set SOTA moved 33% → 55.5% in calendar 2024 alone
([ARC Prize 2024 technical report](https://arxiv.org/abs/2412.04604)), then o3
effectively ended it. MMLU sits above 90% and motivated HLE's existence.

**This already happened to us once.** Campaign 3.0.0's first build measured
**94-100% for frontier models against a single-digit design target** — not
because the science was easy, but because the work order handed over the method
as an ordered checklist and the answer schema printed the allowed values,
turning every categorical judgment into multiple choice
(`tests/test_giveaway_gate.py:1-12`, `crucible/chain/spec.py:170-175`).
`leak_scan` missed it because it only inspects numeric stages. The fix is now a
build gate: `giveaway_scan` rejects option menus (correct+decoy both printed),
method recipes (≥3 decision verbs in one sentence), and decoy hints
(`crucible/chain/spec.py:202-239`), and categorical stages are scored
menu-free via generator-authored aliases (`crucible/chain/score.py:59-67`).
The gate is tested in both directions — an over-broad gate that banned
"trap"/"hazard" rejected valid tasks and was itself fixed
(`tests/test_giveaway_gate.py:9-11`).

**What the design already does.**
- Hardness is constructed, not selected: p^K compounding over K=5-8 stages with
  enforced decoy separation `|decoy−correct| ≥ 3·tol`
  (`analysis/crucible3_design.md` §3) — so difficulty does not depend on
  models being bad, and adversarial filtering's key-error trap (HLE imported a
  ~29% error rate that way) is avoided.
- Non-guessability gate: B0 prompt-only run must score below threshold before a
  template enters the population (`analysis/crucible3_design.md` §6.5).
- Tiered release holds back headroom: hidden seeds 12-13, sealed seed never
  published, fresh seeds reserved for post-publication regeneration
  (`analysis/preregistrations/campaign-3.0.0.md`, `crucible/chain/rematerialize.py`).

**Gaps.**
1. The arithmetic that protects us also bounds us: at per-stage p = 0.93 —
   plausible for 2027 frontier models on 5-8 text-only single-turn stages —
   0.93^7 ≈ 60%. K is capped at 8 and the track is single-turn text-only
   (`docs/LIMITATIONS.md` §0), so capability growth eats the headroom and
   there is no harder tier to promote candidates into.
2. Eight templates (`tasks_chain/`: 8 dirs, 12 instances each + 8 sealed
   counterparts) is a small surface; the preregistered expansion to ~30
   templates/~360 instances buys contamination resistance but **not**
   statistical power — templates are the unit of signal
   (`analysis/crucible3_design.md` §6b) — and not difficulty.
3. No saturation response protocol exists: no tripwire thresholds, no
   pre-committed action when they fire.

**Early-warning tripwires (propose preregistering these).**
- Any system's hidden-split pass@1 > 30% → begin next-version authoring.
- pass@1 > 60% or trap rate < 10% for two systems → the version is declared
  legacy at the next campaign, with a published saturation postmortem.
- Per-stage hazard profile flattening toward uniform (traps no longer doing
  the work) → audit the newest templates with `giveaway_scan` retrospectively.
- B0 (prior-only) creeping up across campaigns → prompts are leaking method
  or the archetype's conventions have been learned; rotate seeds.

**Actions.** (1) Preregister the tripwires above in the next campaign prereg
(half a day). (2) Commit to a version treadmill now: CHAIN-v2 authoring starts
when the first tripwire fires, with escalation levers already designed —
K→10-12, multi-defect H1×2 instances, subtler decoy separation at the 3·tol
floor, cross-artifact forks (2-3 weeks per version). (3) Publish the 94-100%
near-miss as a methods note — it is the single best proof the team measures its
own validity (see FM-4).

---

## FM-2. Contamination scandal

**Kill mechanism.** Someone demonstrates the hidden/sealed truth was learnable
— training-set ingestion of the public split, sealed-split leakage, or
generator conventions that make new instances predictable — and every
published number becomes suspect at once. Case histories: GSM1k measured up to
8% accuracy drops vs GSM8k with overfit gap correlated to memorization
likelihood (Spearman r² = 0.36) ([GSM1k](https://arxiv.org/abs/2405.00332));
SWE-Bench Illusion showed models name the buggy file path from the issue text
alone at 76% on SWE-bench vs 53% off-benchmark, and 35% vs 18% verbatim 5-gram
reproduction ([SWE-Bench Illusion](https://arxiv.org/abs/2506.12286));
MLE-bench's private labels were recomputable from public Kaggle data for 74/75
competitions even after patching (`analysis/literature/README.md` §4).

**What the design already does.** This is where constructed truth pays twice:
- Three-tier split with a sealed tier that is never published, used as a
  leakage probe (hidden-vs-sealed delta: `crucible/release_campaign.py:1-8`,
  `crucible/chain/campaign.py:104-126`).
- B0 prior-only floor printed beside every headline — the frontier's real
  credit is (score − B0) (`analysis/preregistrations/campaign-3.0.0.md`).
- Exposure ledger per instance (`registry/exposure_ledger.json`,
  `docs/LIMITATIONS.md` §4) and an explicit prohibition on contamination-proof
  claims — the scandal-proof posture is already in writing.
- Instances regenerate from seeds (`crucible/chain/rematerialize.py`), so a
  contaminated cohort can be *replaced*, not just retracted — an option
  benchmarks with human-written keys do not have.

**Gaps — and one of them is disqualifying at flagship scale.**
1. **Chain of custody is unprovable.** The entire benchmark, sealed split
   included, lives on one Windows machine, on the same disk as `.secrets/`,
   with **no version control at all** — `Test-Path A:\PERTURB-Bench\.git` →
   False. `docs/LIMITATIONS.md` §4 says the sealed split is "git-ignored";
   there is no git. If accused, we cannot prove the sealed split predates a
   model, wasn't edited after results, or never left the machine. FrontierMath
   survived its custody crisis only because Epoch could construct a genuinely
   unseen 50-problem holdout after the fact
   ([Epoch statement](https://epoch.ai/blog/openai-and-frontiermath)).
2. No cryptographic commitment: nothing timestamps the sealed truth.
3. No canaries in the public split to detect training ingestion.
4. The hidden-vs-sealed probe runs when a campaign runs; it is not a standing
   tripwire with a preregistered threshold.

**Early-warning tripwires.**
- Hidden-vs-sealed pass@1 delta > a preregistered margin (e.g. 10 points with
  non-overlapping template-clustered CIs) for any system → freeze headline,
  rotate seeds, publish the probe result either way.
- Public-split scores rising across model generations faster than sealed →
  same response.
- Canary string reproduced by any model → public split declared contaminated,
  regenerated from fresh seeds.

**Actions.** (1) `git init` + private remote today (FM-6 shares this). (2)
Hash-commitment scheme, one day's work: at every release, publish SHA-256 of
each sealed instance's truth bundle and of the generator+seed manifest; reveal
on rotation. Third-party timestamp (OpenTimestamps or a signed tag on a public
remote) makes custody provable. (3) Embed per-instance canary GUIDs in public
artifacts (packaging already scans canaries for the truth boundary —
`crucible/packaging.py` per `README.md`; extend to detection-in-the-wild). (4)
Preregister the hidden-vs-sealed tripwire and its response in the next prereg.

---

## FM-3. Judge-bias exposé

**Kill mechanism.** A third party shows the LLM judge systematically favors a
family or style and the press headline is "AI benchmark graded by the AIs it
grades." The reference exposé is The Leaderboard Illusion — Meta tested 27
private Llama-4 variants pre-release; Google and OpenAI got ~19.2% and ~20.4%
of all Arena data vs ~29.7% for 83 open-weight models combined; arena-data
access yields up to 112% relative gains
([Leaderboard Illusion](https://arxiv.org/abs/2504.20879)). The judge
literature says the risk is real: 17/20 models show significant
self-preference, only 3/20 qualify as objective judges
(`analysis/literature/README.md` §3).

**What the design already does — the strongest section of the whole program.**
- The primary metric is deterministic; **no judge can alter VCC**
  (`analysis/preregistrations/campaign-3.0.0.md` Rules). Judges touch only the
  advisory RQS and the notice half of the notice-act gap.
- Cross-family judge of record; criterion-level binary verdicts (−31.5%
  self-preference); ≤8 criteria per call; substring-verified evidence quotes;
  style normalization before judging (markdown bias +0.76 vs position ≤0.04)
  (`analysis/crucible3_design.md` §5, grounded per-mitigation in
  `analysis/literature/README.md` §3).
- The gold-set gate has demonstrably fired: both judges failed the
  preregistered 0.85 recall bar (0.775/0.700), scoring was **blocked**, the
  cause investigated, and the amendment registered before any candidate ran —
  with the direction-of-error argument (published notice rates are
  conservative lower bounds) stated where the number appears
  (`analysis/preregistrations/campaign-3.0.0.md` Amendment 1). That paper
  trail is exactly what survives an exposé.

**Gaps.**
1. **The real exposure is authorship, not judging.** Templates are authored by
   the same two families being evaluated (`docs/LIMITATIONS.md` §0). Whether
   claude-opus-5 scores better on claude-authored templates than on
   gpt-authored ones is measurable from campaign artifacts and has never been
   computed or reported. If a hostile party computes it first and finds an
   effect, the story writes itself.
2. The judge meta-eval's gold labels are themselves model-constructed
   (Amendment 1 found one wrong-label case already); no human has audited a
   single judge verdict.
3. Two families do all authoring, judging, and evaluating; a third family
   exists in the lineup (NVIDIA NIM systems, `runs/corrections/CORR-009`) but
   not in the authoring/judging rotation.

**Early-warning tripwires.** Author-family × candidate-family VCC interaction
significant at template-clustered CIs; RQS-vs-VCC rank divergence for any one
family; any judge meta-eval metric drifting across campaigns.

**Actions.** (1) Compute and publish the authorship cross-table (author family
× candidate family × VCC and RQS) in every scorecard from 3.0.0 onward — one
day, data already exists. Preempting this is far cheaper than rebutting it.
(2) Add a third-family template author for the expansion wave and report the
three-way cross. (3) Commission a human audit of ~50 judge notice-verdicts
(~$1-2k at the rates in `docs/LIMITATIONS.md` §0) and publish agreement.

---

## FM-4. A competitor benchmark with better marketing

**Kill mechanism.** Not refutation — irrelevance. A lab-backed benchmark with
a press cycle becomes the default citation in model cards, and flagship status
is decided by adoption, not validity. Case histories: HLE launched with a
Scale AI/CAIS press machine and became the default "hardest exam" citation
despite a 29 ± 3.7% error rate in its bio/chem subset later documented by
FutureHouse ([FutureHouse audit](https://www.futurehouse.org/research-announcements/hle-exam))
— marketing beat validity. ARC Prize turned a 2019 dataset into the o3 launch
stage with prize money and a technical report
([ARC Prize 2024](https://arxiv.org/abs/2412.04604)). Chatbot Arena remains
dominant through a documented validity crisis
([Leaderboard Illusion](https://arxiv.org/abs/2504.20879)).

**What the design already does: nothing — by charter.** The pilot charter
states "no public leaderboard, no capability marketing"
(`governance/program_charter.md`), and the prohibited-claims list
(`analysis/preregistrations/campaign-3.0.0.md`) bars the vocabulary competitors
lead with. Honest, and correct for a pilot — but the flagship bid inverts the
goal and the charter has not been updated. There is no paper, no website, no
DOI, no public repo, no harness integration (HAL / Epoch hub /
lm-eval-harness), and the 3.0.0 scorecard's systems table is currently empty
(`runs/release-3.0.0/scorecard.md`).

**The asset nobody else has.** The differentiators are already built and are
exactly what the field's post-2025 critique demands: near-zero key error by
construction vs 29%/~8%/42% published error rates elsewhere
(`analysis/literature/README.md` §1); C0/H1 byte-identical prompts and
false-alarm controls no competitor scores; pass^3 reliability; preregistration
with registered amendments; and a public corrections log (CORR-001..CORR-009,
`runs/corrections/`, `release/1.0.0/corrections.md`) including embarrassing
ones. "The benchmark that audits itself" is a marketing position with no
incumbent — BetterBench found 17/24 benchmarks ship no replication script and
only 3/24 have CI (`analysis/literature/README.md` §7).

**Early-warning signals.** A lab announces a science-judgment benchmark with
per-stage scoring; model cards cite a competitor for "scientific reasoning";
CRUCIBLE mentioned in a survey without a score attached.

**Actions.** (1) Amend the charter: flagship goals replace pilot non-goals;
keep the prohibited-claims list (it is the brand). (2) Ship the public package
in one release: arXiv paper, public repo with hashes, leaderboard page with
the baseline ladder printed beside every score, corrections page front and
center (2-4 weeks). (3) Publish the saturation near-miss postmortem as the
launch essay — counterintuitive, and the strongest credibility signal
available. (4) Integrate with one third-party harness (HAL or Epoch hub) so
scores are reproducible by outsiders (1 week). (5) Name the thing once:
CRUCIBLE-CHAIN, one line — "every stage has an attractive wrong answer."

---

## FM-5. Gaming / overfitting to the public split

**Kill mechanism.** Once a leaderboard exists, someone optimizes against the
artifact instead of the construct: fine-tuning on the public split, learning
generator conventions ("house style": decision vocabulary, unit conventions,
fork archetypes), or exploiting the grader. The 2026 audits found a team
scoring ~100% on Terminal-Bench, SWE-bench Verified and WebArena without
solving a single task, and BenchJack found 219 flaws across 10 benchmarks
(`analysis/literature/README.md` §4); a do-nothing agent passed 38% of
τ-bench airline tasks; visible scorers produced 43x more reward hacking on
RE-Bench (ibid.).

**What the design already does.**
- Grading is a pure function of the submission string; nothing the candidate
  writes is executed; truth never ships
  (`analysis/literature/README.md` §4 defense column; `crucible/packaging.py`
  truth-boundary scans per `README.md`).
- Integrity gates that withhold the headline: B1 degenerate and B9 adversarial
  submissions (judge injection, fabricated quotes, shotgun answers) must score
  0 (`analysis/preregistrations/campaign-3.0.0.md`); a standing shortcut
  attacker suite exists (`crucible/shortcuts.py`: metadata-only,
  card-language, artifact-spoof, naive-replay).
- Decoy separation ≥ 3·tol means "close enough" never scores; menu-free alias
  matching prevents token-list shotgunning within a stage answer
  (`crucible/chain/score.py:59-67`).
- The sealed split doubles as the overfit detector (FM-2 machinery).

**Gaps.** (1) Generator conventions are learnable from the public split, and
nothing measures how much: a B-rung that fine-tunes or few-shots on the public
split and runs on hidden would quantify the "house style" bonus. (2) No
per-template anomaly monitoring — one template at 100% while the population is
single-digit is a leak signature (CORE-Bench's exploits were found only after
saturation; our design says "we look first", `analysis/crucible3_design.md`
§6.7 — make that standing, not one-time). (3) No published evaluation policy:
nothing stops repeated hidden-split queries by one org walking toward the
answers. (4) Seed rotation per campaign is cheap
(`crucible/chain/rematerialize.py`) but not scheduled.

**Early-warning tripwires.** Per-template pass anomaly (any template's pass@1
> 3x the population mean with clustered CIs); public-vs-hidden gap widening
generation over generation; submission prose matching generator vocabulary
verbatim (canary-adjacent phrasing).

**Actions.** (1) Add the "trained-on-public-split" rung to the baseline ladder
in the 300-400 expansion campaign (2-3 days; it converts the gaming question
into a published number). (2) Preregister per-template anomaly tripwires
(hours). (3) Rotate hidden seeds every campaign; publish old seeds on
rotation (policy, one paragraph). (4) Publish an evaluation-access policy
before any external submissions are accepted.

---

## FM-6. Maintainer abandonment — the one that kills by default

**Kill mechanism.** Every other failure mode requires the world to notice the
benchmark; this one only requires a hard-drive failure or a lost month. The
field's base rate is brutal: BIG-bench — Google-backed, 5,893 commits, 204
authors — was archived read-only on 2026-04-17
([github.com/google/BIG-bench](https://github.com/google/BIG-bench)).
BetterBench found maintenance is the field's weakest practice: 17/24
benchmarks ship no replication script, 14/24 report no uncertainty, 3/24 have
CI (`analysis/literature/README.md` §7; full text
`analysis/literature/md/2411.12990.md`). Survivors (lm-eval-harness,
`analysis/literature/deep/lessons-trenches.md`) survive institutionally, not
personally.

**Current exposure — worse than any external threat.**
- One human holds every role that matters: sponsor, release board, and
  operator (`governance/program_charter.md`,
  `governance/decision_rights_and_boards.md`). Bus factor: 1.
- **No version control**: the repo is not a git repository (verified:
  `Test-Path A:\PERTURB-Bench\.git` → False), despite a `.gitignore` and
  docs that say "git-ignored". No remote, no backup discipline visible, one
  physical Windows machine (long jobs already require battery-safe Task
  Scheduler workarounds — user memory note), `.secrets/` on the same disk.
- If this machine dies tonight: the sealed split, the exposure ledger, the
  hash-chained audit log, and all 828+ run artifacts are gone
  simultaneously. The audit chain (`crucible/audit.py`) detects tampering; it
  does not survive disk loss.
- No LICENSE file anywhere → nobody else can legally adopt, fork, or rescue
  the work even if they wanted to.
- Corrections are split across `release/1.0.0/corrections.md` (CORR-001) and
  `runs/corrections/` (002-009, with 005 absent and 008 existing only as a
  reference in CORR-009) — no single canonical index for a successor to find.

**Early-warning signals.** Corrections stop appearing; a campaign's scorecard
stays empty >30 days (release-3.0.0's systems table is empty now — currently
legitimate, but it is what abandonment would look like); no release in 6
months; single-maintainer commit gap > 8 weeks.

**Actions (this is the highest-leverage list in the document).**
1. Today, ~2 hours: `git init`, commit, private remote (GitHub/GitLab), plus
   an encrypted off-machine copy of `tasks_chain_sealed/`, `tasks_sealed/`,
   and `registry/` — with `.secrets/` excluded from the repo and rotated out
   of the tree.
2. This week: LICENSE (code Apache-2.0 / data CC-BY-SA or similar), and a
   canonical `CORRECTIONS.md` index linking all nine records.
3. This month: CI running the 12 test files on every push;
   `governance/SUCCESSION.md` naming a steward and a dead-man's-switch policy
   — "if no maintainer activity for 6 months, the sealed-split hashes,
   generators, and seeds are released publicly" — which converts abandonment
   from silent death into a survivable open-sourcing event.
4. This quarter: recruit 1-2 co-maintainers with commit and release rights
   (also the single best FM-7 mitigation).

---

## FM-7. Community distrust of a solo-authored, model-graded benchmark

**Kill mechanism.** The first response to the flagship bid is "one person, no
institution, models writing tasks and models grading them" — and adoption
stalls regardless of technical merit. The community's sensitivity is
calibrated by the FrontierMath episode: OpenAI commissioned the benchmark,
held problems and solutions for ~250/300 items under a verbal agreement,
contributors weren't told, and disclosure landed the day o3 was announced;
Epoch's retrofit — a 50-problem sponsor-blind holdout plus a standing
disclosure policy — is now the community's expected baseline
([Epoch statement](https://epoch.ai/blog/openai-and-frontiermath);
`analysis/literature/README.md` §7). Benchmarks buy trust with named external
humans: HealthBench with 262 physicians, GPQA with 61 contracted experts
(local full texts).

**What the design already does — disclosure is genuinely best-in-class.**
- The conflict is named in writing, structurally, wherever results appear:
  same two families author, judge, and are evaluated; one human sponsor; every
  board is the sponsor plus model panels
  (`governance/decision_rights_and_boards.md`, `docs/LIMITATIONS.md` §1).
- Negative-result commitment is honored in practice, not just stated: CORR-007
  reports six systems unevaluated over a billing failure and voids 336 runs
  rather than hiding them; CORR-009 records a lineup change as a correction
  specifically because 13 outcome files existed, and retains the excluded
  outcomes (`runs/corrections/CORR-007/`, `runs/corrections/CORR-009/`).
- Preregistration with amendments registered before candidate runs
  (`analysis/preregistrations/campaign-3.0.0.md` Amendment 1); prohibited
  claims enumerated; limitations file is load-bearing ("no result may be
  quoted without these boundaries", `docs/LIMITATIONS.md`).

**Gaps — disclosure is not independence.**
1. No human being other than the author has verified a single template's
   science. "Cross-family hostile review" means "another model approved it"
   (`docs/LIMITATIONS.md` §0).
2. Nothing is externally verifiable: no public repo, no timestamps (see FM-6),
   so even the excellent preregistration discipline is only self-attested.
3. All sign-offs are the sponsor signing their own work
   (`release/1.0.0/signoff-1.0.0.md` pattern; release board = sponsor).

**Early-warning signals.** First external coverage leads with "solo" or
"AI-graded"; a lab declines to be evaluated citing governance; reviewers ask
for the human-verification rate and the answer is zero.

**Actions.** (1) Paid spot-audit: 2-3 domain scientists independently verify a
random sample of ~5 templates (chain arithmetic, method correctness, decoy
plausibility) and publish their report verbatim — at the expert rates already
cited in `docs/LIMITATIONS.md` §0 this is ~$2-5k, the cheapest trust available
per dollar. (2) Make the repo public with signed, timestamped history (FM-6
work makes prereg timestamps provable). (3) Standing advisory reviewers (2-3
named external people) with a documented veto on releases — Epoch-pattern
governance before anyone demands it. (4) Publish the sponsorship/funding
policy now, while the answer is "self-funded, no lab money" — it is worth more
stated before the first lab check arrives than after.

---

## Ranked recommendations

Ordered by (risk retired × cheapness). Effort in parentheses.

1. **Version control + off-machine encrypted backup + LICENSE** (hours-days).
   Retires the default-death scenario of FM-6, creates the provable custody
   FM-2 needs, and makes FM-7's verifiability possible. Nothing else on this
   list matters if the disk dies first. Do before the 300-400 expansion.
2. **Cryptographic commitments + canaries** (1-2 days). Publish SHA-256 of
   sealed truth bundles and generator+seed manifests at each release with a
   third-party timestamp; embed canary GUIDs in public artifacts. Converts any
   contamination accusation from unanswerable to checkable (FM-2, FM-5).
3. **Preregister the tripwire table** (half a day). Saturation thresholds
   (pass@1 > 30%/60%, trap rate < 10%), hidden-vs-sealed delta margin,
   per-template anomaly bound — each with its pre-committed response, in the
   expansion campaign's prereg (FM-1, FM-2, FM-5).
4. **Authorship-bias cross-table in every scorecard** (1 day; data exists).
   Author family × candidate family × VCC/RQS. Preempts the most likely
   exposé angle (FM-3, FM-7).
5. **Human spot-audit of ~5 templates + ~50 judge verdicts** (~$3-7k, 2
   weeks calendar). The only mitigation that touches "no human has ever
   checked this" (FM-7, FM-3).
6. **Charter amendment + public release package** (2-4 weeks): paper, public
   repo, leaderboard with the baseline ladder beside every score, canonical
   corrections index, saturation-near-miss postmortem as the launch essay,
   one third-party harness integration (FM-4, FM-7).
7. **Version treadmill commitment** (design now, execute on tripwire):
   CHAIN-v2 escalation levers — K→10-12, multi-defect instances, subtler
   decoys, cross-artifact forks; third-family template author in the
   expansion wave (FM-1, FM-3).
8. **SUCCESSION.md + dead-man's-switch policy + 1-2 co-maintainers + CI**
   (1 day writing; recruiting ongoing). Converts abandonment into an
   open-sourcing event instead of a silent death (FM-6, FM-7).
9. **Gaming policy + trained-on-public-split baseline rung + scheduled seed
   rotation** (2-3 days) (FM-5, FM-2).

## Sources

Repository evidence: paths cited inline throughout; key artifacts —
`tests/test_giveaway_gate.py`, `crucible/chain/spec.py`,
`crucible/chain/score.py`, `analysis/crucible3_design.md`,
`analysis/preregistrations/campaign-3.0.0.md`, `docs/LIMITATIONS.md`,
`governance/program_charter.md`, `governance/decision_rights_and_boards.md`,
`runs/corrections/CORR-002..009`, `release/1.0.0/corrections.md`,
`runs/release-3.0.0/scorecard.md`, `registry/exposure_ledger.json`,
`crucible/shortcuts.py`, `crucible/chain/rematerialize.py`.

Local full-text library (23 papers read in full during design;
`analysis/literature/README.md` records the numbers used above): HLE
(2501.14249), GPQA (2311.12022), SWE-bench (2310.06770), CORE-Bench
(2409.11363 + `deep/core-bench.md`), FrontierMath (2411.04872), RE-Bench
(2411.15114), BetterBench (2411.12990), LiveBench (2406.19314), LAB-Bench
(2407.10362), lm-eval-harness lessons (`deep/lessons-trenches.md`), Adding
Error Bars to Evals (`deep/error-bars.md`), HealthBench and LifeSciBench
(`analysis/papers/`).

Web sources opened for this document:
[FutureHouse HLE bio/chem audit](https://www.futurehouse.org/research-announcements/hle-exam) ·
[The Leaderboard Illusion](https://arxiv.org/abs/2504.20879) ·
[GSM1k](https://arxiv.org/abs/2405.00332) ·
[Epoch AI, "OpenAI and FrontierMath"](https://epoch.ai/blog/openai-and-frontiermath) ·
[ARC Prize 2024 Technical Report](https://arxiv.org/abs/2412.04604) ·
[SWE-Bench Illusion](https://arxiv.org/abs/2506.12286) ·
[BIG-bench repository (archived 2026-04-17)](https://github.com/google/BIG-bench) ·
[Humanity's Last Exam leaderboard](https://lastexam.ai).
