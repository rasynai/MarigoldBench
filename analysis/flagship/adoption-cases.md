# Benchmark Adoption Case Studies: How Evals Become Model-Card Standard

**Workstream:** Flagship strategy for CRUCIBLE-CHAIN.
**Question:** What causally determines whether a benchmark ends up in every provider's launch table — and what kills it?
**Method:** Web research on primary sources (papers, maker sites, provider launch posts, audits, press). 20+ sources fetched 2026-08-16; URLs inline.
**Status:** Working document. Recommendations at the end are ranked and sized for a small team.

---

## 0. The adoption scoreboard

| Benchmark | Maker | Released | Adoption event | Status in provider cards (mid-2026) |
|---|---|---|---|---|
| MMLU | Hendrycks et al. (academic) | Sep 2020 | GPT-3/PaLM/GPT-4 era reporting | Dead as headline; survives as variants (MMMLU, MMLU-Pro) |
| GPQA | Rein et al., NYU (academic) | Nov 2023 | Claude 3 launch, Mar 2024 | Standard (Diamond subset), now saturating at 87–89% |
| SWE-bench | Jimenez/Yang et al., Princeton (academic) | Oct 2023 | OpenAI co-builds "Verified", Aug 2024 | The coding standard, universal |
| HLE | CAIS + Scale AI | Jan 2025 | Gemini 2.5 / Deep Research / Grok 4, H1 2025 | Standard "frontier knowledge" slot despite label-quality audit findings |
| FrontierMath | Epoch AI (OpenAI-funded) | Nov 2024 | o3 announcement, Dec 2024 | Partial adoption only; COI scandal capped it |
| ARC-AGI | Chollet → ARC Prize Foundation (nonprofit) | 2019 / relaunch 2024 | o3 co-announcement, Dec 2024 | Trophy benchmark: cited when a lab wins, not a standing panel item |
| tau-bench | Sierra (vendor) | Jun 2024 | Claude 3.7 Sonnet launch, Feb 2025 | Agentic-slot standard at Anthropic; revised to tau2 (Jun 2025) |

The single clearest pattern: **the adoption event is never the paper — it is the first frontier-lab flagship launch that reports the number.** Everything the maker controls (difficulty, harness, governance, timing) either raises or lowers the probability of that event.

---

## 1. Case studies

### 1.1 MMLU — ubiquity through ease, death through label error

- **Origin:** Hendrycks, Burns, et al., Sep 2020; 57 tasks of exam-style multiple choice. GPT-3 scored ~44% ("almost 20 points above chance") at launch and top models were far from "expert-level accuracy" (https://arxiv.org/abs/2009.03300).
- **Why it won:** trivially runnable (multiple choice, no harness), broad "knowledge" narrative, and it launched exactly when scaling-era labs needed one number to show progress. It became the default headline in essentially every 2021–2024 model card, including Claude 3's launch table (https://www.anthropic.com/news/claude-3-family).
- **Why it died:** saturation (>88% by 2024) plus measured label error. MMLU-Redux re-annotated 5,700 questions and estimated **6.49% of questions contain errors, with 57% of the Virology subset erroneous**, producing "significant discrepancies with the model performance metrics that were originally reported" (https://arxiv.org/abs/2406.04127).
- **Maintenance:** none by the original owner. The community shipped the fixes (MMLU-Redux, MMLU-Pro) and providers quietly swapped to variants (Claude 4 reports MMMLU, not MMLU — https://www.anthropic.com/news/claude-4).
- **Lesson:** ease-of-running buys ubiquity; unmaintained label error forfeits the franchise to successors you don't control.

### 1.2 GPQA — small, clean, expert-validated; owned the "graduate-level" slot

- **Origin:** Rein et al. (NYU, Bowman's group), Nov 2023. Only **448 questions**, written and validated by paid PhD domain experts; skilled non-expert validators with **30+ minutes of unrestricted web access got 34%**, experts 65% (74% discounting clear mistakes), GPT-4 39% (https://arxiv.org/abs/2311.12022). Framed for scalable-oversight research, i.e. "Google-proof" — which is exactly the property providers needed for contamination-resistant claims.
- **Adoption event:** Anthropic put GPQA in the Claude 3 launch table (Mar 4, 2024) as "graduate level expert reasoning" (https://www.anthropic.com/news/claude-3-family). After that, GPQA Diamond (the 198-question high-agreement subset) became a fixture in OpenAI, Google, xAI, Meta and DeepSeek tables.
- **Quality tiering mattered:** providers adopted the **Diamond** subset — the maker pre-built a maximum-label-confidence tier, so the card-ready number was the clean one.
- **Current state:** saturating. Epoch's independent run has Grok 4 at **87% (±2%)** vs OpenAI-recruited PhD experts at 69.7%; GPT-5 Pro reported 89.4% with tools (https://epoch.ai/benchmarks/gpqa-diamond, https://www.vellum.ai/blog/gpt-5-benchmarks). Models now exceed the human-expert ceiling, and the slot is passing to HLE.
- **Lesson:** 448 clean, expensive, expert-validated items beat thousands of scraped ones. A small benchmark is adoptable if the label story is airtight and it names a capability tier ("graduate-level") that providers want to claim. Also: publish your own "Diamond" — don't let providers choose their subset.

### 1.3 SWE-bench — the provider co-maintenance playbook (the strongest case)

- **Origin:** Princeton academics, Oct 2023; 2,294 real GitHub issue/PR pairs; **Claude 2 resolved 1.96%** at launch (https://arxiv.org/abs/2310.06770). ICLR 2024 Oral.
- **Timing:** landed at the exact start of the coding-agent wave — huge headroom, real-work realism, and a metric ("% resolved") an exec can read.
- **The adoption event was a provider fixing the benchmark's labels:** OpenAI's Preparedness team funded the move to a **fully containerized Docker harness (Jun 2024)** and then co-built **SWE-bench Verified (Aug 2024)** — a 500-problem subset "that real software engineers have confirmed are solvable," screened by professional annotators because the original set contained underspecified issues and unfair tests (https://raw.githubusercontent.com/SWE-bench/SWE-bench/main/README.md, https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified). The provider-blessed subset instantly became *the* variant: Claude 3.7 (63.7%), Claude 4 (72.5–72.7%, 79.4–80.2% high-compute), Gemini 2.5 Pro (63.8%), GPT-5 (74.9%) all report Verified (https://www.anthropic.com/news/claude-3-7-sonnet, https://www.anthropic.com/news/claude-4, https://blog.google/technology/google-deepmind/gemini-model-thinking-updates-march-2025/, https://www.vellum.ai/blog/gpt-5-benchmarks).
- **Maintenance:** continuous and visible — Lite/Verified/Multimodal/Multilingual variants, sb-cli cloud evaluation, SWE-smith training-data toolkit, active academic maintainers (Jimenez, Yang), MIT license, public leaderboard (https://www.swebench.com/).
- **Lesson (the big one):** the fastest route to "standard" is to get a frontier lab to *invest* in your benchmark, not merely run it. Labs need trustworthy evals for internal go/no-go (OpenAI did this under its Preparedness Framework); if your label quality, harness, and license make co-investment easy, the lab's fix becomes your endorsement. Every lab then adopts the co-built variant because a competitor's name is on the QA.

### 1.4 HLE — narrative + distribution beat label quality (so far)

- **Origin:** CAIS + Scale AI, Jan 2025. 2,500 questions, ~1,000 expert contributors from 500+ institutions, explicitly positioned as "the final closed-ended academic benchmark of its kind" for the post-MMLU/GPQA saturation era; private held-out set maintained (https://arxiv.org/abs/2501.14249).
- **Sourcing was a paid tournament:** >$500K in bounties ($5,000/question for top 50, $500 for next 500) pulled **70,000 submissions → 13,000 expert-reviewed → ~3,000 released**; frontier models scored **<10%** at launch (https://scale.com/blog/humanitys-last-exam-results).
- **Adoption:** near-instant. Google headlined 18.8% for Gemini 2.5 Pro (Mar 2025); xAI made HLE the Grok 4 flagship number (50.7% for Grok 4 Heavy with tools, Jul 2025); OpenAI reported ~42% with tools at GPT-5 launch; the lastexam.ai leaderboard now runs Gemini 3 Pro 38.3% / GPT-5 25.3% / Grok 4 24.5% no-tools (https://blog.google/technology/google-deepmind/gemini-model-thinking-updates-march-2025/, https://x.ai/news/grok-4, https://www.vellum.ai/blog/gpt-5-benchmarks, https://lastexam.ai/). Published in Nature, Jan 2026.
- **The crack:** FutureHouse audited text-only chemistry/biology items with a literature-search agent plus independent expert raters and estimated **~29% (±3.7%) of answers directly conflict with peer-reviewed literature**, blaming the adversarial sourcing incentive ("questions frontier models can't answer" selects for confusing items) and 5-minute reviewer budgets (https://www.futurehouse.org/research-announcements/hle-exam).
- **Lesson:** owning the *successor narrative slot* at the exact moment the incumbents (MMLU, GPQA) saturate is worth more, short-term, than perfect labels — HLE was adopted in weeks. But incentivized crowdsourcing bakes in a label-error time bomb; HLE's ~29%-in-audited-slice is the standing vulnerability a constructed-truth benchmark can attack.

### 1.5 FrontierMath — quality capped by governance failure

- **Origin:** Epoch AI, Nov 2024. Original, unpublished research-grade problems, hours-to-days of mathematician effort each, automated verification, **<2% solve rate at launch** (https://arxiv.org/abs/2411.04872).
- **Adoption moment:** OpenAI's o3 announcement claimed ~25% (Dec 20, 2024) — huge visibility.
- **The scandal:** it then emerged that **OpenAI had funded the benchmark, owned the problems and solutions, and had access to all but a 50-problem holdout** — undisclosed to contributors and the public until the o3 launch window. Contributing mathematicians said they might not have participated had they known; Epoch co-founder Tamay Besiroglu: "We made a mistake." Safeguards were a *verbal* no-training agreement, and Epoch could not independently verify o3's number at the time (https://techcrunch.com/2025/01/19/ai-benchmarking-organization-criticized-for-waiting-to-disclose-funding-from-openai/, https://epoch.ai/blog/openai-and-frontiermath).
- **Aftermath:** Epoch published commitments (contributor disclosure, proactive sponsorship disclosure) and now runs FrontierMath tiers itself on all frontier models via its Benchmarking Hub (https://epoch.ai/benchmarks). But FrontierMath never became a cross-provider card staple — rival labs won't headline a benchmark a competitor funded and can access.
- **Lesson:** funder conflict-of-interest is the one mistake that *permanently* caps adoption at one provider. Disclosure timing matters as much as the arrangement itself; "verbal agreement" is not a governance answer. Conversely: Epoch running everyone's models itself is what salvaged the asset.

### 1.6 ARC-AGI — prizes and a livestream moment; verification as a service; trophy-not-panel

- **Origin:** Chollet's 2019 "On the Measure of Intelligence"; five years of relative obscurity while LLMs scored ~0 (https://arcprize.org/arc-agi).
- **What changed:** a **$1M+ prize (ARC Prize 2024, Kaggle)** run by a dedicated nonprofit (ARC Prize Foundation), a public-train/semi-private/private split structure, and then the **o3 co-announcement (Dec 20, 2024)**: ARC Prize itself ran o3 on the 100-task semi-private set, in collaboration with OpenAI, reporting **75.7% high-efficiency (~$26/task) and 87.5% at 172× compute (~$4,560/task)** and simultaneously announcing ARC-AGI-2 would knock o3 back under 30% (https://arcprize.org/blog/oai-o3-pub-breakthrough).
- **Adoption shape:** providers cite ARC-AGI **when they win** — OpenAI (o3), xAI (Grok 4: ARC-AGI-2 15.9%, "nearly double" Claude Opus) (https://x.ai/news/grok-4). It is not a standing row in every card; it is a trophy with a referee. The Foundation's role as *independent verifier of frontier claims* (labs come to them pre-launch) is the durable asset, institutionalized through versioning (ARC-AGI-1/2/3) and annual competitions.
- **Lesson:** (a) a prize + nonprofit + semi-private set converts a benchmark into a verification *service* labs must come to; (b) co-announcing a lab's breakthrough — being part of their launch news — is the fame event; (c) trophy benchmarks get cherry-picked; standing-panel benchmarks get reported win or lose. Decide which you are building; the panel needs every-model comparability, the trophy needs a referee.

### 1.7 tau-bench — a vendor benchmark that filled an empty slot early

- **Origin:** Sierra researchers (Yao, Shinn, Razavi, Narasimhan), Jun 2024. Agent + simulated-user + policy-compliance tasks (retail/airline), and — the differentiator — the **pass^k reliability metric**; GPT-4o at launch: <50% pass^1, <25% pass^8 on retail (https://arxiv.org/abs/2406.12045).
- **Adoption:** it was effectively the only credible tool-use-with-user benchmark when the agent narrative arrived. Anthropic made "state-of-the-art on TAU-bench" a Claude 3.7 Sonnet launch claim (Feb 2025) and kept it in the Claude 4 table (May 2025) (https://www.anthropic.com/news/claude-3-7-sonnet, https://www.anthropic.com/news/claude-4). Trivially runnable: pip-installable, LLM-simulated user, no human in the loop.
- **Maintenance:** the maker shipped **tau2-bench (Jun 2025)** — telecom dual-control domain, a *compositional task generator* for verifiable tasks, and a tightened user simulator — explicitly fixing reliability/verifiability weaknesses of v1 (https://arxiv.org/abs/2506.07982).
- **Lesson:** vendor provenance is not fatal (Sierra sells agents; labs still cite it) *if* the benchmark fills an empty capability slot first and is effortless to run. Notably, tau2's fix — programmatic task generation for verifiability — is convergent evolution toward CRUCIBLE's constructed-truth design. Also: a novel metric (pass^k) can itself be the adoption hook; Anthropic adopted the metric's framing, and CRUCIBLE's pass^3 speaks the same language.

---

## 2. Causal factors, ranked by evidence strength

**F1. A frontier-lab flagship launch is the adoption event.** GPQA→Claude 3; SWE-bench→OpenAI Verified; FrontierMath/ARC-AGI→o3 day; HLE→Gemini 2.5/Grok 4; tau-bench→Claude 3.7. Once one lab reports a number, competitors must answer it in their next card. Papers, stars, and leaderboards are inputs; the launch-table row is the output.

**F2. Launch headroom in the "visible progress" band.** Every winner launched with frontier scores roughly 2–40% (Claude 2 at 1.96% SWE-bench; GPT-4 at 39% GPQA; <10% HLE; <2% FrontierMath). Low enough for years of runway, high enough (or with a lab partner poised to break it, as o3 did for ARC/FrontierMath) that progress is demonstrable. Saturation is the standard slot-vacating event (MMLU → GPQA → HLE). CRUCIBLE's just-fixed 94–100% leak would have been terminal; post-fix scores define the entire pitch.

**F3. Label quality is the moat and the kill criterion — and it is now *audited by third parties*.** MMLU: 6.49% error → replaced. SWE-bench: unfair tests → OpenAI had to build Verified before trusting it. HLE: ~29% suspect in the audited slice → standing vulnerability. GPQA: expert-validation protocol + Diamond tier → longest clean run per item. The market has learned to audit (MMLU-Redux, FutureHouse, BetterBench's finding that "most benchmarks do not report statistical significance... nor allow results to be easily replicated" — https://arxiv.org/abs/2411.12990). Constructed truth with near-zero label error is precisely the property every incumbent lacks.

**F4. Effortless provider-side execution.** MMLU's ubiquity was ease. SWE-bench adoption accelerated only after the Docker harness (Jun 2024). tau-bench was pip-and-go. FrontierMath/HLE require the maker (or Epoch) to run private sets — workable only because of F6. If a lab's eval team can't run your dev split in an afternoon for pocket change, you will not be in their pre-launch sweep.

**F5. Neutral governance; disclosed money.** FrontierMath is the controlled experiment: identical quality, adoption capped by undisclosed funder access. ARC's nonprofit foundation and academic provenance (Princeton, NYU) carried trust. Post-2025, contributor/funding disclosure is table stakes (Epoch's own reform commitments).

**F6. A contamination story with a self-serve path.** Winners pair a public dev/train set with a sealed eval: GPQA "Google-proof" construction; HLE private held-out set; ARC semi-private run by the Foundation; FrontierMath unpublished problems; SWE-bench's weakness here (public GitHub data) is why Live/fresh-issue variants exist. The maker running sealed evals for labs (ARC model) doubles as the endorsement channel.

**F7. Owner-driven versioning keeps the franchise.** SWE-bench Lite/Verified/Multimodal/Multilingual; ARC-AGI-1→2→3 with the successor announced *the same day* o3 broke v1; tau→tau2; HLE holds a private set and publishes in Nature. MMLU, unmaintained, lost its name to other people's variants. Version before you saturate, and pre-announce the refresh.

**F8. One legible headline metric; reliability metrics differentiate.** "% resolved", "accuracy", "pass^k". tau-bench proved a reliability metric can be the hook. Non-compensatory scoring is fine — but it must compress to a single card-ready number (CRUCIBLE: pass^3 chain-resolved %).

**F9. Independent third-party runners multiply trust.** Epoch's Benchmarking Hub independently re-runs GPQA Diamond, SWE-bench Verified, FrontierMath, etc., with CIs (https://epoch.ai/benchmarks). Getting into the aggregator/verifier layer means your numbers appear in comparisons a lab doesn't control — pressure to report it themselves.

**F10. Paid crowdsourcing scales volume, not truth.** HLE's $500K bounty bought 70,000 candidate questions and a ~29%-suspect audited slice. GPQA's smaller paid-expert-plus-validators pipeline bought a defensible ceiling. Generators beat both on marginal cost *and* error rate — that is CRUCIBLE's structural advantage; say it with data.

**What a provider's eval team actually needs (distilled checklist):** runnable in-house in <1 day at <$100 (dev split) · sealed split they can't have but can *commission* quickly pre-launch · one headline number + CIs · no funder COI · known label-error rate with a corrections process · a capability-narrative slot their comms team wants to claim · stable versioning so numbers survive a card's lifetime.

---

## 3. Recommendations for CRUCIBLE-CHAIN (ranked)

**R1. Engineer the launch number before anything else.** Re-run the frontier campaign post-saturation-fix at the 300–400-instance scale; the pitch requires headline pass^3 in roughly the 5–45% band with clean separation between models and a hazard profile showing *where* chains break. If a model family scores ~0, add a partial-credit *diagnostic* view (never the headline) so progress is visible. This number is the product; nothing below works without it. *Effort: 1–2 weeks (campaign infra exists in `runs/` + prereg flow).*

**R2. Publish the label-error comparison table — CRUCIBLE's core positioning.** One page: MMLU 6.49% measured error (MMLU-Redux), HLE ~29% suspect in audited chem/bio slice (FutureHouse), SWE-bench pre-Verified unfair-test rate (OpenAI had to rebuild it), GPQA expert ceiling 69.7% — vs. CRUCIBLE constructed truth (deterministic generators, near-zero label error) + the existing 9-entry corrections log (`release/1.0.0/corrections.md`) as proof you audit yourselves. Frame: "the first frontier benchmark where the answer key is computed, not crowdsourced." *Effort: 2–3 days.*

**R3. Ship the self-serve harness with a generate-your-own dev split.** `pip install crucible-chain` + Docker + one command; public dev split regenerated per-user from the generators (contamination-proof by construction — a structural edge no incumbent has), sealed + hidden splits held back (`tasks_chain_sealed/` already exists). Target: an eval team runs the dev split in <2h for <$50. Without this you are FrontierMath (maker-run only); with it you are MMLU-easy and GPQA-clean simultaneously. *Effort: 2–4 weeks.*

**R4. Get one frontier lab to run the sealed split pre-launch — the SWE-bench/ARC play.** Offer eval/preparedness teams (Anthropic, OpenAI, GDM eval leads) free sealed-split runs with 48h turnaround, CIs, and hazard profiles, timed to their launch cycles; invite co-development of a "Verified"-style tier so their name is on the QA. One launch-table row triggers the F1 cascade. This is the highest-leverage, least-controllable item — start outreach the week R1's number exists. *Effort: ongoing outreach; weeks–months to land.*

**R5. Publish the COI/funding policy before any lab money appears.** Written policy in `governance/`: no funder access to sealed splits, no exclusive access, all sponsorships disclosed at benchmark-card level, contributor-facing disclosure. Cite the FrontierMath failure explicitly — it converts a boring policy doc into a differentiator. *Effort: 1–2 days.*

**R6. Pre-announce the versioning cadence.** Benchmark card commits to: v1.x sealed split frozen for card citability; v2 regeneration on a dated schedule (or automatically on measured saturation >70%); deprecation policy for old splits. ARC announced v2 the day v1 broke — CRUCIBLE's generators make this cheap and credible; say so publicly. *Effort: 1–2 days (doc), generators already exist.*

**R7. Get into the independent-runner layer.** Pitch Epoch's Benchmarking Hub (and HELM/Vals-type runners) to run CRUCIBLE-CHAIN sealed evals; self-assess against BetterBench's 46 criteria and publish the scorecard (prereg + corrections log + Wilson CIs already clear the "statistical rigor" bar most benchmarks fail). *Effort: ~1 week including materials.*

**R8. Public leaderboard with CIs and pass^3 as the only headline.** One number per model (pass^3 chain-resolved, Wilson CI); C0/H1/F2 asymmetry and per-stage hazards as expandable diagnostics, never competing headlines. Accept third-party submissions with a verification path (maker re-runs on hidden split — the ARC referee role). *Effort: 1–2 weeks.*

**R9. Name the capability slot and claim it in every artifact.** GPQA owned "graduate-level reasoning," SWE-bench "real software issues," HLE "frontier of human knowledge." CRUCIBLE's empty slot: **"chained scientific judgment under deception" / open-ended lab reasoning where wrong-but-plausible paths are scored**. HLE's audit problems make "the trustworthy successor for open-ended science" available now; move before someone else takes it. *Effort: naming/positioning pass over README, benchmark card, site — days.*

**R10. Manufacture the moment, don't wait for it.** Options in leverage order: (a) co-announce a frontier model's CRUCIBLE result with the lab (o3/ARC pattern); (b) a modest prize for first model/system to pass^3 ≥ 50% on sealed (ARC pattern, scaled to budget); (c) NeurIPS/ICML datasets-track paper + workshop challenge for academic legitimacy (GPQA/SWE-bench pattern). Do (c) regardless; chase (a) via R4. *Effort: (c) ~2–3 weeks writing; (a),(b) opportunistic.*

**Anti-patterns to hard-avoid (each killed or capped a case above):** selling a funder access to sealed data (FrontierMath) · launching with a leaked/saturated split (just dodged) · crowdsourced answer keys (HLE) · maker-only evaluation with no self-serve path (FrontierMath) · letting outsiders own your quality tier or successor (MMLU) · publishing a headline metric that changes between versions (breaks card citability).

---

## Sources

GPQA https://arxiv.org/abs/2311.12022 · SWE-bench https://arxiv.org/abs/2310.06770 · SWE-bench repo/Verified/Docker https://raw.githubusercontent.com/SWE-bench/SWE-bench/main/README.md · Verified dataset card https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified · Leaderboard https://www.swebench.com/ · MMLU https://arxiv.org/abs/2009.03300 · MMLU-Redux https://arxiv.org/abs/2406.04127 · HLE paper https://arxiv.org/abs/2501.14249 · HLE site/leaderboard https://lastexam.ai/ · Scale HLE post https://scale.com/blog/humanitys-last-exam-results · FutureHouse HLE audit https://www.futurehouse.org/research-announcements/hle-exam · FrontierMath https://arxiv.org/abs/2411.04872 · Epoch on OpenAI relationship https://epoch.ai/blog/openai-and-frontiermath · TechCrunch COI coverage https://techcrunch.com/2025/01/19/ai-benchmarking-organization-criticized-for-waiting-to-disclose-funding-from-openai/ · Epoch Benchmarking Hub https://epoch.ai/benchmarks · Epoch GPQA Diamond https://epoch.ai/benchmarks/gpqa-diamond · ARC-AGI overview https://arcprize.org/arc-agi · ARC o3 results https://arcprize.org/blog/oai-o3-pub-breakthrough · tau-bench https://arxiv.org/abs/2406.12045 · tau2-bench https://arxiv.org/abs/2506.07982 · Claude 3 https://www.anthropic.com/news/claude-3-family · Claude 3.7 https://www.anthropic.com/news/claude-3-7-sonnet · Claude 4 https://www.anthropic.com/news/claude-4 · Gemini 2.5 https://blog.google/technology/google-deepmind/gemini-model-thinking-updates-march-2025/ · Grok 4 https://x.ai/news/grok-4 · GPT-5 scores https://www.vellum.ai/blog/gpt-5-benchmarks · BetterBench https://arxiv.org/abs/2411.12990
