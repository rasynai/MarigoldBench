# Provider incentives — why the six frontier labs would run and cite CRUCIBLE-CHAIN

Flagship workstream. Date: 2026-08-16. Status: working document, execute top-down.
Method: 15 primary web sources opened (lab launch pages, leaderboards, audits, controversy records) + repo evidence (paths cited inline). Every claim is grounded; source list at the end.

---

## TL;DR

1. Every lab's science story is currently carried by **saturating MCQ benchmarks with 8-29% label error** (GPQA, HLE) plus **anecdote papers** where benchmarks give out. "PhD-level" is a marketing claim resting on answer-key recall.
2. Labs demonstrably **do** report hard, low-score benchmarks — HLE launched single-digit, xAI headlined ARC-AGI-2 at 15.9%, Anthropic cites BixBench — **when everyone is low, trajectory is visible, and there is a "first-to-X" race**. They avoid or game benchmarks when the asymmetry is against them (Llama 4/LMArena, Grok consensus@64).
3. CRUCIBLE-CHAIN's differentiator is not "harder"; it is **process-verified with a near-zero-error answer key** ("the answer key cannot be wrong") plus diagnostics no one else has: per-stage hazard, notice-act gap, false-alarm rate on byte-identical clean controls, premise pushback, calibration. Those are valuable to a lab's eval team **even at VCC = 3%**.
4. The realistic adoption path is **two customers inside each lab**: eval/post-training teams first (METR-style private preview, diagnostics-first, no fee), comms teams second (once scores climb into the teens and a race exists).
5. Current blocker: the 3.0 chain scorecard is **empty** (post-saturation-fix rerun pending, 2 first-party systems only, OpenRouter credit exhausted). Nothing in this document matters until a populated multi-lab scorecard exists at the 300-400-instance scale.

---

## 1. What the six labs cite for science claims today (evidence)

| Lab | Science evals actually cited | The marketing claim | Where the real science story lives |
|---|---|---|---|
| **OpenAI** | GPQA, AIME, FrontierMath (funded/owns it), HLE (GPT-5: 25.3% on lastexam.ai) | Altman: GPT-5 has "PhD-level" abilities; "significant step along the path to AGI" [W-GPT5] | *Early science acceleration experiments with GPT-5* (arXiv 2025-11-20, Bubeck et al., incl. CPO Kevin Weil): **case studies** in math/physics/bio, explicitly noting where the model failed and humans intervened [W-SCIACC] |
| **Google** | HLE 37.5%, GPQA Diamond 91.9%, ARC-AGI-2 45.1% (Deep Think + code exec) | Verbatim: "It demonstrates **PhD-level reasoning** with top scores on Humanity's Last Exam (37.5%...) and GPQA Diamond (91.9%)" [W-GEM3] | AI co-scientist (2025-02-19): validated by **bespoke 7-expert panel + wet-lab experiments** (AML repurposing, organoids, AMR); GPQA only secondary [W-COSCI] |
| **Anthropic** | GPQA Diamond (Opus 4: 76.9%); Opus 4.5 leads with SWE-bench, GPQA/HLE/ARC relegated to a table | Opus 4 "excels in research, writing, and scientific discovery" [W-CL4] | **Claude for Life Sciences** (2025-10-20) cites *third-party niche science evals*: Protocol QA 0.83 vs human 0.79, BixBench improvement — proof Anthropic reaches for small process benchmarks when selling science [W-CLS]; AI for Science credits program (2025-05-05) [W-AFS] |
| **xAI** | HLE — "first to score 50.7%" (Grok 4 Heavy); ARC-AGI-2 15.9% "SOTA for closed models"; GPQA | Grok 3 marketing: "GPQA for **PhD-level science problems**" [W-GROKW] | "First-to-X%" races on prestige benchmarks; no science-process evidence [W-GROK4] |
| **Meta** | Little science-eval citation; LMArena Elo was the Llama 4 headline | — | The LMArena gaming episode (below) *is* the story; science ambitions unevidenced by evals |
| **DeepSeek** | GPQA Diamond, AIME, math/code suites; R1 published in **Nature** 645:633-638 | "superior performance on **verifiable tasks** such as mathematics, coding competitions, and STEM fields" [W-R1] | Verifiable-rewards training thesis — deterministic checkable tasks are their native language |

**Reading:** the citation pattern is uniform — each lab leads with the benchmark it wins (Anthropic → SWE-bench; xAI → HLE; Google → HLE/GPQA/ARC; DeepSeek → verifiable math). Nobody has a science-*process* number, so science claims escalate to anecdote (OpenAI), wet-lab one-offs (Google), or testimonials (Anthropic's pharma logos).

## 2. The gap between "PhD-level" marketing and what the benchmarks demonstrate

**2a. The benchmarks under the claim are answer-key recall, and the keys are bad.** (Numbers assembled in `release/1.0.0/literature-review.md`, cross-checked against primary sources.)

- **HLE**: FutureHouse audited 321 text-only chem/bio items → **29 ± 3.7% contradicted by peer-reviewed literature**; HLE's own re-audit: 15.4% expert disagreement. Cause: adversarial filtering *kept questions because models failed them*, enriching for wrong keys ("gotcha" items like the oganesson question) [W-FH-HLE].
- **GPQA**: Epoch estimates ~8% of Diamond invalid; authors' own objectivity estimate 73.6-76.4%; experts only reached 65→81% accuracy. Gemini 3 now scores **91.9% — above the expert-agreement ceiling**. GPQA is finished as a differentiator; the "PhD-level" line survives on a saturated instrument.
- **FrontierMath**: ~7-10% posterior error on double review; **v2 corrected 42% of problems**; and OpenAI *funded it, owns the problems, and had solution access* — Epoch's own admission: "should have been more systematic and transparent" [W-EPOCH].
- **CORE-Bench**: post-saturation audit found 15/45 hard tasks erroneous, 20/45 shortcut-exploitable — errors found only *after* the leaderboard maxed out.
- **SWE-bench**: OpenAI's re-curation filtered **68.3%** of items; fixing labels moved GPT-4o 16%→33.2%.

**The one-line consequence (this is the pitch sentence):** *at single-digit pass rates, the benchmark's own error rate is the binding constraint — and CRUCIBLE's constructed truth makes it structurally ~zero* (generator computes every stage answer from data it generated; `README.md`, `analysis/crucible3_design.md` §3).

**2b. Nothing scores the process.** HLE's own creators say it tests "structured academic problems rather than open-ended research" [W-HLE]. GeneBench-Pro named the decisive failure mode — models **notice** QC flags then fail to **act** on them — and conceded its binary grading "collapses useful stage-level diagnostic evidence" (`release/1.0.0/literature-review.md` §2). No lab can currently answer: *where in a multi-step analysis does my model break, and does it invent problems on clean data?* CORR-006 shows why that matters: one instruction change moved the native product 13/28→24/28 purely by cutting false alarms 8/10→1/10 — "a benchmark without clean controls would have scored the original over-flagging as diligence" (`README.md`).

**2c. Calibration is claimed nowhere and failed everywhere.** lastexam.ai reports ~89% calibration error for GPT-4o-class models [W-HLE]. CRUCIBLE scores per-stage confidence (Brier/ECE) natively (`analysis/crucible3_design.md` §4).

**2d. When benchmarks give out, labs pay for wet labs and case studies.** Google bought a 7-expert panel plus three wet-lab validations to support co-scientist claims; OpenAI published a 14-author anecdote paper. Both are unrepeatable and expensive. A process-verified benchmark is the **standardized instrument both already tried to improvise**.

## 3. The differentiation story, per lab

The generic story: *"System X completes N% of realistic multi-stage scientific analyses in which every stage offers a plausible wrong path, and its stated confidence tracks its correctness"* (`analysis/crucible3_design.md` §1) — the first science number that survives due diligence on label error, contamination, and judge bias (headline VCC never touches an LLM judge; judges are advisory-only with gold-set F1 gates).

| Lab | Why they'd run it | The line they'd cite |
|---|---|---|
| **Anthropic** | Life-sci GTM already cites Protocol QA/BixBench; recall-heavy HLE undersells them (Claude 4.5 Sonnet 13.7%, bottom of frontier table) — a judgment/honesty benchmark reshuffles the deck; FA + pushback + calibration metrics map directly onto the "doesn't invent findings" brand | "Lowest false-alarm rate on byte-identical clean controls; highest flawed-premise pushback" |
| **OpenAI** | "PhD-level" is publicly mocked (MIT Tech Review: "far short of the transformative AI future") [W-GPT5]; the for-science program needs a repeatable metric instead of anecdotes; GPQA is saturated by a rival | "Completes N% of verified multi-stage analyses with calibrated confidence — the benchmark whose answer key cannot be wrong" |
| **Google** | Tops HLE/GPQA — needs the *next* unsaturated frontier number (they showcased ARC-AGI-2 45.1% for exactly this); co-scientist claims need a standardized process instrument instead of bespoke panels | "First to double-digit reliable chain completion (pass^3)" |
| **xAI** | Marketing pattern is "first to X" on prestige-hard benchmarks (first to 50% HLE); an unsaturated benchmark is fresh first-to real estate | "First to X% VCC" (require harness disclosure — see R-gaming) |
| **DeepSeek** | Verifiable-rewards thesis (Nature framing); a deterministic generator is an RLVR-compatible environment; $/VCC flatters efficient models | "Best $/completed-chain at frontier accuracy" — and license the **dev-split generator** as training environment while sealed splits stay eval-only |
| **Meta** | Post-LMArena credibility rebuild; running a preregistered, refresh-proof third-party eval is a cheap integrity signal for the superintelligence-lab reset | "Evaluated under preregistration, all runs published" |

## 4. Will labs report a benchmark they score 4% on? The precedent cuts both ways

**Evidence they will:**
- HLE launched with *every* frontier model in single digits and every lab reported it anyway; it became the flagship number of 2025-26 (now: Gemini 3 Pro 38.3%, GPT-5 25.3%, Grok 4 24.5%, Claude 4.5 Sonnet 13.7%) [W-HLE].
- xAI headlined **15.9%** on ARC-AGI-2 as "SOTA for closed models" [W-GROK4]; Google headlined 45.1% with tools [W-GEM3].
- OpenAI headlined FrontierMath at ~25% for o3; Anthropic cites BixBench, where launch scores were **17% open-answer (Claude 3.5 Sonnet) and 9% (GPT-4o), below random on MCQ with an opt-out** [W-BIX], [W-CLS].
- Conditions that made low scores reportable: (a) everyone is low, (b) an upward trajectory is visible, (c) the benchmark has prestige/credibility, (d) "first-to-X" framing is available.

**Evidence they won't (avoidance and gaming are real):**
- Labs cite selectively: Opus 4.5's announcement leads SWE-bench and buries GPQA/HLE/ARC in a table [W-OP45]; each lab's launch page is a highlight reel of wins (§1).
- Meta submitted an unreleased "experimental chat version... optimized for conversationality" to LMArena; LMArena: "Meta's interpretation of our policy did not match what we expect from model providers" [W-LLAMA].
- xAI published Grok 3 charts using consensus@64 for itself vs single-shot for o3-mini-high [W-GROKW].
- OpenAI bought FrontierMath (funding, ownership, solution access) rather than risk an eval it didn't control [W-EPOCH].

**Synthesis:** the danger case is *asymmetric* low scores — one lab at 20%, rivals at 3% → one citation, five silences. The design answer is (i) private-first diagnostics so the eval team gets value without a public number, (ii) multiple winnable axes so more than one lab has a citable first, (iii) a declared lineup policy that makes refusal visible. METR proves the private-first model works: OpenAI, Anthropic, Google DeepMind and Meta already grant a nonprofit **pre-deployment, non-public model access, uncompensated**, for evaluations they may look bad on [W-METR].

## 5. Risks and mitigations (ranked by likelihood × damage)

| # | Risk | Evidence | Mitigation (mechanism already in repo where noted) |
|---|---|---|---|
| R1 | **Avoidance/selective citation** — labs ignore a benchmark they lose | §4; every launch page cites only wins | Private preview on METR terms (NDA sealed-split run, full diagnostic report, no fee, lab may withhold its v1 number); publish the declared frontier-flagship-per-lineage rule (CORR-009 wording, fixed in capability terms, content-blind — `runs/corrections/CORR-009/`) so the public table prints "declined", never a blank; "not evaluated ≠ zero" norm already established (CORR-007) |
| R2 | **Low score = "noise", dismissed as unusable** | pass^3 → hard zero once pass@1 < ~8% (`runs/release-3.0.0/scorecard.md`) | Report the ladder pass^3 ≤ pass@1 ≤ pass@3 with the 8% guard rail; chain-depth survival curves + per-stage hazard give graded signal at VCC≈0; B0/B1 baselines prove the floor is measured, not noise; **the diagnostic report (hazard spike location, notice-act gap, FA rate, calibration quadrant) is the product for eval teams even when VCC is unquotable** |
| R3 | **Owner credibility / conflict once labs engage** | Epoch's FrontierMath transparency apology [W-EPOCH] | Publish an independence charter *before* first lab contact: no per-task lab funding, all funding disclosed, sealed split hash-committed in prereg (sha256 manifests + hash-chained audit log exist — `crucible/audit.py`, `crucible/release_build.py`), corrections log continues (9 published: CORR-001..009) |
| R4 | **Gaming and contamination after publication** | CORE-Bench exploits found post-saturation; our own campaign-3.0.0 saturation: "frontier models scored 94-100% because the work order handed over the method as an ordered checklist and the answer schema printed the allowed values" (`crucible/chain/spec.py` ~L170) | Constructed truth = unlimited fresh sealed instances per campaign; hidden-vs-sealed gap probe published every campaign (already in `release/1.0.0/scorecard-1.0.0.md`); build gates now enforce no answer menus, method-verb recipe limits, alias disjointness, rendered-value leak scan (`crucible/chain/spec.py`, `score.py`); require harness disclosure via system cards (schema exists) — the consensus@64 lesson |
| R5 | **Solo-project trust deficit** | Today's chain evidence: 2 first-party systems, `summary.json` = `{}`, empty scorecard table (CORR-007 billing exhaustion; rerun pending post-fix) | Populated ≥6-lineage campaign at 300-400 instances is the entry ticket; then third-party replication from raw transcripts; then peer review (HLE and DeepSeek-R1 both ran through **Nature** — review is now part of benchmark prestige) |
| R6 | **Due-diligence findings weaponized** — LLM stand-ins for human roles, single-turn scope | `docs/LIMITATIONS.md`, `docs/NOT_DONE.md` | Pre-empt in all outreach: claims bounded exactly per design §1 ("nothing stronger: no discovery, no wet-lab impact"); the limitations doc is itself a credibility asset — lead with it |

## 6. Recommendations (ranked; S < 1 day, M = days, L = weeks)

1. **(L, blocker) Populate the scorecard before any outreach.** Re-run campaign 3.0 post-saturation-fix at the expanded 300-400-instance scale across ≥6 lineages (needs the OpenRouter top-up per CORR-007; lineup rule per CORR-009). An empty systems table is unanswerable in any lab conversation.
2. **(S) Publish the saturation post-mortem as the flagship credibility artifact.** "Frontier models hit 94-100%; root cause: prompts leaked method recipes and answer menus; gates now make it structurally impossible; found pre-release in days" vs CORE-Bench's 15/45 errors found only after saturation. This converts the near-miss into the strongest validity credential the project owns. Source: `crucible/chain/spec.py`, `score.py` docstrings.
3. **(S) Write the "label-error budget" one-pager.** The table from §2a (HLE 29±3.7%/15.4%, GPQA ~8%, FrontierMath 42% corrected, CORE-Bench 15/45, SWE-bench 68.3% filtered) against constructed truth + a published audited-error estimate. This is the quotable model-card sentence: *"the benchmark whose answer key cannot be wrong."*
4. **(M) Stand up a private-preview lane on METR terms.** NDA'd sealed-split run, full per-stage diagnostic report returned, no fee, lab may hold its v1 number out of the public table; subsequent campaigns are publish-by-default with "declined" printed. Target: eval and post-training leads (the METR/AISI consumers), not comms. METR proves all six labs already accept this shape [W-METR].
5. **(M) Contract the low-score-proof report format.** Every scorecard leads with the ladder + survival curve + hazard profile + FA/pushback/calibration quadrant. Define 3-4 *winnable secondary axes* (lowest false-alarm on clean controls; best premise pushback; best calibration; deepest median chain) so multiple labs own a citable first — while VCC stays the only headline. Guard against medal inflation: secondary axes are named in prereg, never invented post hoc.
6. **(S) Write the six per-lab pitch briefs** from §3, one page each, with the named program hook (Claude for Life Sciences; OpenAI for Science / science-acceleration paper; co-scientist; R1 verifiable-rewards; Grok first-to-X; Meta integrity rebuild) and the specific citable line each lab gets.
7. **(S) Publish the independence charter now, before any lab money or access exists.** Funding disclosure rules, no per-task lab funding, hash-committed sealed splits, harness-disclosure requirement, standing corrections policy. Epoch had to apologize for learning this in the wrong order [W-EPOCH].
8. **(M) Make contamination-resistance a marketed cadence, not a property.** Regenerate the sealed split every campaign from the generator; publish the hidden-vs-sealed gap probe each time (1.0 precedent: gaps +3% to +15%, `release/1.0.0/scorecard-1.0.0.md`); commit instance hashes in the preregistration.
9. **(M) Offer DeepSeek-style labs the dev-split generator as an RLVR training environment** (license or collaboration), keeping sealed/hidden splits eval-only. This creates a *usage* incentive orthogonal to leaderboard vanity — but firewall it: any lab that trains on generator output gets flagged on the scorecard, and the sealed refresh cadence (rec 8) is the enforcement mechanism.
10. **(L) External anchoring.** Methods paper (NeurIPS D&B or Nature-track — HLE and R1 set the precedent that benchmark prestige now runs through peer review) + one respected third party replicating scoring from raw transcripts. Do this after rec 1; a paper on an empty scorecard is premature.

---

## Source list

Web (opened this session):
- [W-GEM3] https://blog.google/products/gemini/gemini-3/ — "PhD-level reasoning", HLE 37.5%, GPQA 91.9%, ARC-AGI-2 45.1%
- [W-GPT5] https://en.wikipedia.org/wiki/GPT-5 — Altman "PhD-level" claims; MIT Tech Review critique
- [W-GROK4] https://x.ai/news/grok-4 — "first to score 50.7% on Humanity's Last Exam"; ARC-AGI-2 15.9%
- [W-GROKW] https://en.wikipedia.org/wiki/Grok_(chatbot) — "GPQA for PhD-level science problems"; consensus@64 chart criticism
- [W-CL4] https://www.anthropic.com/news/claude-4 — GPQA Diamond 76.9% (Opus 4)
- [W-OP45] https://www.anthropic.com/news/claude-opus-4-5 — SWE-bench-led launch, science benchmarks in table only
- [W-CLS] https://www.anthropic.com/news/claude-for-life-sciences — Protocol QA 0.83 vs human 0.79; BixBench
- [W-AFS] https://www.anthropic.com/news/ai-for-science-program — credits program, capability claims
- [W-HLE] https://lastexam.ai/ — leaderboard (Gemini 3 Pro 38.3% ... Claude 4.5 Sonnet 13.7%); Nature Jan 2026; calibration error; "structured academic problems rather than open-ended research"
- [W-FH-HLE] https://www.futurehouse.org/research-announcements/hle-exam — 29 ± 3.7% of 321 chem/bio items contradicted
- [W-BIX] https://www.futurehouse.org/research-announcements/bixbench — 17%/9% open-answer; below random MCQ
- [W-EPOCH] https://epoch.ai/blog/openai-and-frontiermath — funding, ownership, solution access, holdout, transparency apology
- [W-LLAMA] https://en.wikipedia.org/wiki/Llama_(language_model) — Llama 4 Maverick LMArena episode
- [W-METR] https://metr.org/ — pre-deployment evals with OpenAI/Anthropic/GDM/Meta; uncompensated non-public access; time-horizon metric
- [W-COSCI] https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/ — bespoke expert + wet-lab validation
- [W-SCIACC] *Early science acceleration experiments with GPT-5*, arXiv 2025-11-20 (Bubeck, ..., Weil) — located via export.arxiv.org API
- [W-R1] https://arxiv.org/abs/2501.12948 — DeepSeek-R1, Nature 645:633-638; "verifiable tasks" framing

Repo:
- `README.md` — program claims, CORR-006 false-alarm result
- `analysis/crucible3_design.md` — claim boundary, comparison table, p^K hardness math, metric suite, judge mitigations
- `release/1.0.0/literature-review.md` — label-error evidence base; GeneBench-Pro 28.7% + notice-act gap
- `crucible/chain/spec.py` (~L143-179), `crucible/chain/score.py` (~L58-75) — saturation bug (94-100%), leak scan, menu removal, method-verb gates
- `runs/corrections/CORR-007/CORR-007.md`, `runs/corrections/CORR-009/CORR-009.md` — not-evaluated norm; declared lineup rule
- `runs/release-3.0.0/scorecard.md`, `summary.json` — ladder framing; current empty state
- `release/1.0.0/scorecard-1.0.0.md` — 828-run campaign, 9 systems, hidden-vs-sealed probe, near-ceiling anchor scores (79-95%)
- `docs/LIMITATIONS.md`, `docs/NOT_DONE.md` — LLM stand-ins, scope bounds
