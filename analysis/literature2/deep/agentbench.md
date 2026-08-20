# Deep read: AgentBench (arXiv 2308.03688)

## Coverage ledger

- PDF: `A:/PERTURB-Bench/analysis/literature2/pdfs/2308.03688.pdf` — 23,017,024 bytes, header `%PDF-1.7`, 58 pages.
- Extracted text: `A:/PERTURB-Bench/analysis/literature2/md/2308.03688.md` — **176,121 chars, 3,127 lines**.
- Chunks read with the Read tool (sequential, complete, no gaps):
  - lines 1–60 (title page verification)
  - lines 61–700
  - lines 701–1320
  - lines 1321–1940
  - lines 1941–2560
  - lines 2561–3127 (EOF)
- **chars_read = 176,121 (100% of file)**, including all appendices A–J (framework/max-flow, OS, DB, KG, DCG, LTP, HH, WS, WB dataset details + full prompt dumps + validity analysis + failure case transcripts).
- Extraction was clean (>15k chars), so no ar5iv fallback was needed. Table cells are run together in the text layer (e.g. the Table 3 rows), so numbers below were parsed carefully from the concatenated strings.

## Actual paper identity (as printed)

- Header on every page: **"Published as a conference paper at ICLR 2024"**.
- Title: **AGENTBENCH: EVALUATING LLMS AS AGENTS** — matches the requested paper.
- Authors: Xiao Liu¹\*, Hao Yu¹\*†, Hanchen Zhang¹\*, Yifan Xu¹, Xuanyu Lei¹, Hanyu Lai¹, Yu Gu²†, Hangliang Ding¹, Kaiwen Men¹, Kejuan Yang¹, Shudan Zhang¹, Xiang Deng², Aohan Zeng¹, Zhengxiao Du¹, Chenhui Zhang¹, Sheng Shen³, Tianjun Zhang³, Yu Su², Huan Sun², Minlie Huang¹, Yuxiao Dong¹‡, Jie Tang¹‡ — ¹Tsinghua University, ²The Ohio State University, ³UC Berkeley.
- arXiv stamp in the margin: `arXiv:2308.03688v3 [cs.AI] 4 Oct 2025` (v3 revision; it adds `claude-3 (opus)` and `glm-4`, which are marked with `*` as "evaluated after task weights are computed").
- Code/data: https://github.com/THUDM/AgentBench

## Section-by-section notes with numbers

### Abstract / Fig. 1 (overall picture)
8 environments, 29 LLMs (API-based + OSS ≤70B). Overall AgentBench score (OA, weighted): gpt-4 **4.01**, claude-3 (opus) 3.11, glm-4 2.89, claude-2 2.49, claude v1.3 2.44, gpt-3.5-turbo 2.32, text-davinci-003 1.71, claude-instant 1.60, chat-bison-001 1.39, text-davinci-002 1.25, codellama-34b 0.96, vicuna-13b 0.93, llama-2-70b 0.78 … oasst-12b 0.03. **Average API-based = 2.32, average OSS = 0.51** (4.5x gap). Headline diagnosis: "poor long-term reasoning, decision-making, and instruction following abilities are the main obstacles."

### §2 LLM-as-Agent definition and finish reasons
Formalized as a POMDP (S, A, T, R, U, O). Deliberately uses **plain CoT only** — no self-consistency, no reflection, no tree search: "Without multiple trials, repeated generations, or complicated strategies, CoT is the easiest, cheapest, and most common way for people to deploy LLM agents."

Five finish reasons, which is the paper's most transferable contribution: **Completed**, **Context Limit Exceeded (CLE)**, **Invalid Format (IF)**, **Invalid Action (IA)**, **Task Limit Exceeded (TLE)**. IF/IA ⇒ instruction-following failure; TLE ⇒ weak multi-turn ability.

### §3 The eight environments
Three groundings:
- **Code**: Operating System (new; real Ubuntu Docker + bash), Database (new; real MySQL over a forwarded port), Knowledge Graph (Freebase via Virtuoso, 45M entities / 3B facts, wrapped in 7 query tools).
- **Game**: Digital Card Game (Aquawar, from THUAC 2021), Lateral Thinking Puzzles (new, LLM-hosted riddle game), House-Holding (ALFWorld).
- **Web**: WebShop, Mind2Web.
Five of eight environments are created for the first time in this paper.

### §4.1 Evaluation setup (Table 2)
| Env | Avg rounds | Metric | #Dev (samples/rounds) | #Test (samples/rounds) | Weight⁻¹ |
|---|---|---|---|---|---|
| OS | 8 | SR | 26 / 240 | 144 / 1200 | 10.8 |
| DB | 5 | SR | 60 / 300 | 300 / 1500 | 13.0 |
| KG | 15 | F1 | 20 / 300 | 150 / 2250 | 13.9 |
| DCG | 30 | Reward | 12 / 360 | 20 / 600 | 12.0 |
| LTP | 25 | Game Progress | 20 / 500 | 50 / 1250 | 3.5 |
| HH | 35 | SR | 20 / 700 | 50 / 1750 | 13.0 |
| WS | 5 | Reward | 80 / 400 | 200 / 1000 | 30.7 |
| WB | 10 | Step SR | 31 / 400 | 100 / 1000 | 11.6 |

Dev = 269 samples, Test = **1,014 samples**; ≈3k and ≈11k inference calls respectively — "approximately the identical amounts of calls for inference as MMLU requires." Deterministic decoding: **temperature = 0** everywhere. Context management: a hard budget of **3500 tokens** of history using a crude tokenizer proxy (a word of length n = ⌈n/6⌉ tokens, non-blank char = 1 token); the middle of the trajectory is dropped and `"[NOTICE] 2r messages are omitted."` is appended to the system turn.

**Scoring normalization:** each task's average score across all models is resized to 1, then averaged across tasks; the reciprocal of the average score becomes a **fixed published weight** for future runs. Rationale: naive averaging is dominated by the easy high-scoring task (WebShop, whose weight⁻¹ is 30.7, i.e. ~9x the LTP 3.5). No confidence intervals, no seeds, no repeats are reported anywhere.

**Toolkit:** decoupled Server/Client — Agent servers over HTTP, Task servers = controller + isolated Docker workers, Evaluation client schedules agent×task pairs with a **max-flow (Edmonds–Karp, O(|V||E|²))** allocation over a bipartite graph, plus resumable evaluation.

### §4.2 Main results (Table 3, test split)
gpt-4 leads on 6/8: OS 42.4, DB 32.0, KG 58.8, DCG 74.5, LTP 16.6, HH **78.0**, WS 61.1, WB 29.0.
claude-3 opus: OA 3.11 (OS 22.9, DB **51.7** — best DB, KG 34.6, DCG 44.5, LTP 14.3, HH 70.0, WS 27.9, WB 26.0).
glm-4: OA 2.89 (KG 46.3, WS 61.6). gpt-3.5-turbo: OA 2.32 (OS 32.6, HH only 16.0, WS **64.1** — best WS).
Best OSS ≤70B is codellama-34b at OA 0.96 (WS 52.1, KG 23.5, OS only 2.8). Several OSS models score 0.0 on entire environments. llama-2-70b (0.78) ≈ llama-2-13b (0.77) — the authors re-ran and attribute this to under-training relative to Chinchilla scaling and to weak instruction alignment.
Even for Mind2Web, task-level success is "single-digit," so they report **Step Success Rate** instead of task success.

### §4.3 / Appendix J — failure anatomy (this is the most useful part for us)
Table 4, portion of outcomes averaged over all models (%):

| | OS | DB | KG | DCG | LTP | HH | WS | WB |
|---|---|---|---|---|---|---|---|---|
| Completed | 75.0 | 37.9 | 30.1 | 51.2 | 14.0 | 13.1 | 54.9 | 56.6 |
| CLE | 0.1 | 0.7 | 2.0 | 0.0 | 3.5 | 0.7 | 0.0 | 0.0 |
| Invalid Format | 0.0 | **53.3** | 0.0 | 38.5 | 0.0 | 0.0 | 17.2 | 0.0 |
| Invalid Action | 0.9 | 0.0 | 0.0 | 10.2 | 0.0 | **64.1** | 0.0 | 8.4 |
| TLE | 23.9 | 8.0 | **67.9** | 0.0 | **82.5** | 22.1 | 27.8 | 35.0 |

Table 6 by model class: Commercial API models — Completed 61.5%, CLE 3.0%, IF 6.0%, IA 4.6%, TLE 24.9%. OSS models — Completed 39.1%, CLE 0.0%, IF 10.4%, IA 13.6%, TLE 36.9%.

- **J.2.1** Even gpt-4 sometimes drops the required `Action: Operation` wrapper in DB and emits a tutorial-style explanation with a bare SQL block instead — an *alignment-induced* format failure, not a capability failure.
- **J.2.3** Completed trajectories: rounds median **6.0**, mean **7.95**, IQR 4.0–9.0; tokens median **1850**, mean **2220.1**, IQR 761–2709; "the vast majority of tasks are completed within 3000 tokens."
- **J.2.4** TLE trajectories average **25.5 rounds** and are dominated by *repetition*: >90% of TLE trajectories contain two responses within the last 10 rounds with Rouge-L ≥ 0.8. They deliberately look at the last-n rounds rather than the last two because models cycle through multi-state loops (enter room → open drawer → close drawer → leave room).
- **J.2.2** Side-by-side transcripts: gpt-4 does a clean DFS over an abstract plan tree (Find → Clean → Put) with correct backtracking and one moment of genuine self-reflection (realizing the soapbar was on the countertop all along); gpt-3.5-turbo decomposes the task correctly and then enters an infinite open/close-cabinet-1 loop, apologizing each cycle.
- **J.2.5** Code tuning is a double-edged sword: codellama > llama2 on WebShop (procedural, template-following; completion 50.3% vs 36.5%) but codellama < llama2 on Digital Card Game (strategy, no template).
- **J.2.6** Self-correction from *environment error text* is the discriminator on DB: claude-2 reads the MySQL 1064 syntax error twice and works out that both the column name and the table name need backticks.

### Per-environment construction and verification (Appendices B–I)

**OS (App. B).** Each sample = instruction + Docker image + optional init script + optional start script + **checking pipeline** + optional example (reference) script. Two task types: QA (must `commit` an answer) and **Operation** (no answer needed; the checker inspects system state). The checking pipeline is a chain of scripts f₁…f_n where f_k receives the model answer o₀ and all earlier outputs o₁…o_{k−1}; **correct iff every script exits with code 0**. Provenance: ~half human-authored from 6,000 Stack Overflow bash/shell questions sorted by score, curated by 8 programming-major annotators, **~2 hours of annotation per problem**, then cross-verified; the other half generated by gpt-4 and filtered by unit tests (init script must exit 0; the example solution must pass the checker). Final: **144 samples**. Round limit 8. 1-shot CoT prompt.

**DB (App. C).** Built from WikiSQL, WikiTableQuestions, SQA, HybridQA, FeTaQA; gpt-3.5-turbo used to synthesize 10 new rows per table, 5 new SQL queries, 5 INSERT and 5 UPDATE statements, plus paraphrases — explicitly "to further enrich (**and avoid leakage from**) the dataset." 300 final entries in three categories (select / insert / update). Verification: SELECT compares text answers order-insensitively with exact match (numeric equivalence allowed: 5, "5.0", '+5'); **INSERT/UPDATE compare the hash of the post-operation table against the hash of the table after the gold SQL**. Score = macro average over the three categories. App. C.4 is an **augmentation-bias audit**: they re-annotated a batch with Claude-2 and checked that the score *pattern* holds (gpt-4 weak on UPDATE, strong on INSERT; gpt-4 0.27 INSERT / 0.66 UPDATE new vs 0.32/0.32 original; gpt-3.5-turbo 0.19/0.92 new vs 0.23/0.66 original).

**KG (App. D).** From GrailQA, ComplexWebQuestions, GraphQuestions over Freebase in Virtuoso. Filtered to questions needing **≥5 tool invocations**; 1,663 questions collected, **first 500 used**. Seven tools: `get_relations`, `get_neighbors`, `intersection`, `get_attributes`, `argmax`, `argmin`, `count`, with explicit typed preconditions ("get_neighbors() can only be used after get_relations()"). Topic entities are given so entity linking is not part of the task. Max 15 actions. Metrics: **F1** (primary), Exact Match on the *answer set* (not the logical form), and **Executability** (1.0 if the action sequence yields any answer set at all, else 0). Zero-shot fails completely, so a full teaching example is included.

**DCG (App. E).** Aquawar, 4 fish per side from a 10-fish pool, 400 HP / 200 ATK each, hidden identities with an assertion mechanism. Two stages (without/with assertions), scores averaged. The agent gets **5 chances to produce a legally formatted action**; then it is deemed defeated. Reward = 0.7 × win-rate + 0.3 × damage-rate. Two scripted baselines (random; greedy AOE/one-hit-kill heuristic). App. E.4 defines a principled difficulty knob: single-fish combat power = HP·ATK, team power = (mean HP)·(sum ATK), and **difficulty ρ(H|F) = Power(H)/Power(F)**, with ρ = 1 as parity.

**LTP (App. F).** New environment. An LLM (gpt-3.5-turbo) hosts a lateral-thinking riddle and answers only Yes/No/Irrelevant; 4 difficulty levels; max 25 rounds. Ground truth is broken into **key points** ("answer_keys") summarized by gpt-3.5-turbo; the main metric **Game Progress** = fraction of key points reached. The pipeline converts each Yes-answered question into a declarative sentence (No-answered → negated declarative), merges the reasoning into one sentence, then asks a judge model whether the merged sentence contains all information in the key point; matched key points are deleted to prevent double counting. Secondary metrics: Single Game Accuracy, Round Efficiency, Query Relevance. **They validated the auto-judge against humans and found it biased-lenient**: "automatic evaluation sometimes more tolerate for the agent, which make SGA and QR seem better than human evaluation, especially on open-sourced models" — but GP and RE match human evaluation.

**HH (App. G).** ALFWorld, **134 solvable problems** from the *eval out-of-distribution* split, six categories (pick and place, pick clean then place, pick heat then place, pick cool then place, look at obj, pick two obj). 1-shot per category using ReAct's prompts. Two soft-landing hacks: invalid-format outputs are snapped to the **highest-BLEU valid action**, and **three consecutive identical outputs = failure by repetition** (a time-saving early stop).

**WS (App. H).** WebShop; ~1M scraped Amazon products, 12,087 human instructions; **first 500** used as the test set. Reward = (|U_att ∩ Y_att| + |U_opt ∩ Y_opt| + 1[y_price ≤ u_price]) / (|U_att| + |U_opt| + 1) × r_type, with r_type ∈ {0, 0.1, 0.5, 1} keyed to a text match on the product title. This is a **partial-credit, compensatory** metric — note that WebShop is exactly the environment whose scores had to be down-weighted 9x relative to LTP.

**WB (App. I).** Mind2Web **Cross-Domain** split: 912 tasks over 73 websites (they run 100). Raw HTML is unusable, so a fine-tuned DeBERTa ranker selects top-k candidate elements and the LLM answers a **5-way multiple-choice question** per step (with "A. None of the above" as an explicit option), plus the argument for Type/Select. Metrics: Element Accuracy, Action F1, Step SR (primary), Task SR (all steps correct — "even the best LLMs now can only achieve single-digit task success percentages"). They note results diverge from the original paper because they use top-k = 10 with CoT few-shot instead of top-k = 50.

## Benchmark card

- **Task count:** 1,014 test instances (269 dev) across 8 environments: OS 144, DB 300, KG 150, DCG 20, LTP 50, HH 50, WS 200, WB 100. Only 8 "families," so the per-family sample counts are wildly unequal.
- **Construction:** 5/8 environments new; heavy reuse of existing datasets with re-formulation into interactive form; human annotation (8 annotators, ~2 h/problem for OS) plus LLM-generated + unit-test-filtered items (OS QA half, DB inserts/updates).
- **Verification:** environment-side and program-side, not judge-side, in 6/8 environments — shell exit codes (OS), post-state table hashes (DB), executed KG queries with F1 against gold answer sets, simulator success flags (HH), reward function over annotated product attributes (WS), string/element match against annotated traces (WB). Two environments use an **LLM as the environment/judge**: LTP (gpt-3.5-turbo hosts and scores key points) and, partly, DCG's format policing.
- **Scoring:** per-environment metric (SR / F1 / reward / progress / step-SR), then a variance-flattening weighted average with published fixed weights. **Non-compensatory only within an episode** (OS is binary correct/wrong; HH is binary success); *compensatory across environments and inside WS/WB/LTP/DCG*.
- **Agent scaffolding:** plain ReAct-style Thought+Action in a single turn, 1-shot or 3-shot demo, temperature 0, 3500-token sliding history with middle-omission, chat/completion adapters, no retries, no reflection, no ensembling. Explicitly a floor, not a ceiling.
- **Reported uncertainty:** **none.** No CIs, no error bars, no multiple seeds, no repeat runs; deterministic decoding is the substitute. DCG uses fixed battle presets "for fair evaluation."
- **Contamination handling:** partial and informal — DB augmentation is described as being "to further enrich (and avoid leakage from) the dataset"; OS QA items are gpt-4-generated rather than lifted verbatim; the Mind2Web Cross-Domain split targets generalization to unseen websites. There is no held-out/private split, no canary, no timestamp analysis, and the released datasets are public.
- **Cost per run:** not reported in dollars. Reported proxies: ~11k inference calls for the test split (~3k for dev), completed trajectories mean 7.95 rounds / 2220 tokens, TLE trajectories mean 25.5 rounds. Acknowledgement states Zhipu AI covered all GPU and API cost. The max-flow scheduler exists precisely because wall-clock is the binding constraint.

## Limitations admitted

- Only CoT; better strategies (self-consistency, Reflexion, ToT) are known to exist and are not evaluated.
- OSS models capped at ≤70B because of compute.
- The LTP auto-host is more lenient than human judges on SGA and QR; they plan to train a dedicated host model.
- Mind2Web numbers are not comparable to the original paper (top-k 10 vs 50, different prompting).
- Task Success Rate on web browsing is uselessly low, so a step-level proxy is substituted.
- Naive score averaging is unfair across environments (motivating the weighting).
- Even gpt-4 "is not qualified as a practically usable agent."

## Limitations not admitted

- **No uncertainty quantification at all.** DCG n=20 and HH/LTP n=50; a claude-3 vs glm-4 OA gap of 0.22 is reported to 2 decimals with no interval. Ranking claims are not defensible at these n.
- **The weights are computed from the very model pool being scored**, and two models (claude-3, glm-4) were added *after* weights were fixed — the normalization is retro-fit, and each new frontier model is scored on a scale defined by 2023-era models.
- **The primary weight is dominated by a leaky construct**: WebShop's weight⁻¹ of 30.7 means WS scores are shrunk ~9x relative to LTP, but the choice of "average model score" as the difficulty proxy conflates *hard* with *unaligned-so-fails-formatting*.
- **Invalid Format is scored as task failure but is partly a harness artifact.** DB's 53.3% IF rate is mostly a strict regex on a markdown wrapper; HH silently rescues invalid outputs with BLEU snapping while DB does not. The scaffolding leniency is not held constant across environments, so cross-environment comparisons mix capability with parser strictness.
- **LLM-in-the-loop dataset construction is only lightly audited.** The DB bias check compares two models on a re-annotated "small batch" and calls the pattern stable; LTP's key points are themselves gpt-3.5-turbo summaries, so the ground truth for the primary LTP metric is model-generated.
- **No false-alarm / abstention condition anywhere.** Every task is solvable; no task rewards refusal, none plants an unsatisfiable premise, and no environment penalizes a confidently wrong committed answer differently from a timeout. gpt-4's "ACTION: Task failed. No soapbar found in the room." — a *correct-looking* give-up that was actually wrong — is presented as an anecdote, not as a scored behavior.
- **The 3500-token middle-omission is a confound.** Long-horizon environments (HH 35 rounds, DCG 30, LTP 25) systematically lose their own middle history, so "long-term reasoning failure" is partly harness-induced amnesia.
- **Repetition detection uses Rouge-L on surface text**, which will miss semantically identical loops phrased differently and over-flag legitimate repeated probing.

## Implications for MarigoldBench

1. **Adopt the five-way finish taxonomy and report it next to VEC, but split "invalid" from "wrong."** AgentBench's Table 4 shows the failure mode is environment-specific and enormous: DB 53.3% Invalid Format, HH 64.1% Invalid Action, LTP 82.5% TLE. If MarigoldBench reports only a single VEC number, a 30% score could be 30% real science or 70% JSON-schema noise on the NIM tool calls. Log `completed / malformed-call / invalid-tool-args / budget-exceeded / abstained / verified-correct / verified-wrong` per episode, and publish the matrix. Critically, keep parser leniency **identical across all task families** — AgentBench silently BLEU-snaps invalid actions in House-Holding but hard-fails them in DB, which corrupts its cross-environment comparison.
2. **Verify by recomputing post-state, not by parsing the answer — AgentBench's DB hash check is the pattern to copy and generalize.** For INSERT/UPDATE they hash the whole table after the agent's operation and compare against the hash of the table after the gold SQL; for OS they run a *chained* checker f_k(o₀…o_{k−1}) and require every stage to exit 0. Translate directly: for a design episode, don't read the model's claimed pLDDT — re-run ESMFold/Boltz-2 on the submitted FASTA yourself and recompute; for a docking claim, re-run the scoring function on the submitted pose file; for an ML claim, re-fit on the frozen split and recompute the metric. Make each check a **chain of independent stages that must all pass** (file parses → chemistry valid → physical quantity in range → statistic beats the null), which is exactly the non-compensatory VEC property AgentBench only achieves in its binary-SR environments.
3. **Plant defects that mimic the two failure modes AgentBench proves are real and cheap to detect: silent state-loop repetition and un-read error text.** >90% of TLE trajectories repeat a response with Rouge-L ≥ 0.8 within the last 10 rounds, and the paper's DB case study shows the discriminating skill is reading a MySQL 1064 error and inferring "backtick the identifiers." Plant defects that surface *only in a tool's stderr/warning field* — a ProteinMPNN run that silently drops a chain, a DiffDock call whose receptor has missing residues, an RDKit sanitization warning, a scikit-learn convergence warning — and score whether the model reads and acts on the message rather than retrying identically. Also instrument every episode with a repetition detector (semantic, not Rouge-L: embed the tool-call payloads and flag near-duplicate consecutive calls) and treat a detected loop as its own failure class, since AgentBench shows it is the single largest cause of non-completion.
4. **Difficulty must be an explicit, tunable, physically-grounded ratio, not an emergent property of the prompt.** Appendix E.4 is the best idea in the paper: they define combat power = HP·ATK and difficulty ρ = Power(hostile)/Power(friendly), so a task's difficulty is a dial with ρ=1 meaning parity. MarigoldBench should define an analogous per-family difficulty scalar from the physics — e.g. the effect size the model must resolve divided by the tool's own noise floor (Δbinding-affinity / Boltz-2 run-to-run σ; planted-signal AUC / bootstrap σ; RMSD margin / DiffDock pose variance). That gives a principled way to *tune* the frontier model into the 5–40% band per family instead of discovering the band post hoc, and it makes "this task is hard" auditable rather than asserted.
5. **A check is only sound if the null is computed in the same harness the agent used.** AgentBench's soundest checks (exit code, table hash, F1 against a gold entity set) share one property: the reference is *executed*, not stored as a number. Every MarigoldBench statistical check should ship with a recomputed null — permutation/scramble baseline for any claimed enrichment, a decoy-ligand control for any docking claim, a shuffled-label refit for any ML claim, and a same-seed rerun to bound tool nondeterminism. State the acceptance threshold as *effect must exceed the recomputed null by k σ*, so the check cannot be passed by a lucky seed. And record the tool version + seed in the artifact, because AgentBench's DCG had to freeze battle presets "for fair evaluation" precisely to keep stochastic environments comparable.
6. **The flawed-premise condition is the gap AgentBench leaves wide open — and its own transcript shows why it matters.** gpt-4 emits "ACTION: Task failed. No soapbar found in the room" when the soapbar was on the countertop: a plausible, well-reasoned, *wrong* refusal that AgentBench neither rewards nor punishes as a category. MarigoldBench's three-condition design must therefore score refusal against *both* directions: on the flawed-premise arm, correct refusal must require the model to **name the specific defect and cite the tool output that reveals it**, not just decline; on the sound-control arm, a refusal or a hedged non-submission must cost the same as a wrong answer. Otherwise the dominant strategy under a non-compensatory scorer becomes strategic abstention.
7. **Budget the episode from measured completion distributions and treat context truncation as a scored variable, not a hidden default.** AgentBench's completed trajectories run 6 rounds median / 7.95 mean with IQR 4–9, while TLE trajectories average 25.5 rounds — i.e. beyond ~2.5x the median, extra rounds buy essentially nothing. MarigoldBench's 8–25 call range straddles exactly that boundary, so per-family call budgets should be set at roughly 2x the human-expert reference trajectory and reported per family. Do **not** silently drop the middle of history the way AgentBench does at 3500 tokens; with 8–25 real tool calls returning PDB files and dataframes, either give the model an explicit externalized scratchpad/artifact store or count truncation events as an experimental condition, because otherwise "long-horizon failure" will be unfalsifiably confounded with harness amnesia.
8. **Never let a model be both the ground truth and the grader for a headline metric — and if you must, publish the human-agreement audit.** LTP's primary metric (Game Progress) is scored against key points *generated by gpt-3.5-turbo* and adjudicated by gpt-3.5-turbo, and the authors' own validation found the auto-judge "sometimes more tolerate for the agent," inflating scores especially for weak models. For MarigoldBench this means: LLM-written task *prompts* are fine, but the acceptance predicate must be executable code over the artifact. Where any judgment call is unavoidable (e.g. "is this rationale scientifically coherent"), report agreement with expert labels on a held-out sample and keep it out of the headline VEC.
9. **Report clustered CIs and refuse to rank on n=20 — AgentBench's own numbers show why.** It reports OA to two decimals (claude-3 3.11 vs glm-4 2.89) off environments with n=20 (DCG) and n=50 (HH, LTP) and zero repeats. With target n per family, MarigoldBench's template-clustered CIs are the right call; go further and pre-register the minimum detectable difference per family, and prefer many small families (100+) over few large ones — 8 environments with unequal n is exactly the structure that makes a weighted overall score fragile.
10. **Fix scoring weights and the score scale *before* running any model, and keep a private split.** AgentBench derives its per-task weights from the average score of the model pool being evaluated, then bolts on claude-3 and glm-4 "after task weights are computed" — so the yardstick is defined by the models it measures, and it drifts as frontier models improve. MarigoldBench should publish a fixed, physics-motivated weighting (or, better, weight all families equally and let non-compensatory VEC do the work), and hold back a private task set: AgentBench has no canary, no timestamped split, and fully public data, and its only contamination defense is gpt-3.5-turbo paraphrasing — insufficient for a benchmark meant to survive several model generations.
11. **Steal the operational architecture: containerized tool workers, HTTP-decoupled agent, resumable runs, and a scheduler.** The Server/Client split with per-task Docker isolation, max-flow scheduling of agent×task pairs, and resumable evaluation is what made 29 models × 8 environments tractable. For MarigoldBench, where a single episode may call RFdiffusion + OpenFold2 + Boltz-2 over NIM with rate limits and multi-minute latencies, resumability and a scheduler are not optional; also cache and content-hash every tool response so that verification reruns are free and episodes are exactly replayable.
12. **Track cost and report it.** AgentBench never states a dollar figure and only implies scale (~11k calls; sponsor covered API/GPU). A benchmark whose per-episode cost is unknown cannot be adopted. Publish median GPU-seconds and NIM calls per episode per family, plus the verification overhead (recomputation is a second, often more expensive, pass) — this also lets you justify per-family n against a fixed budget.

## Verbatim quotes

1. §2, "Chain-of-Thought (CoT) and Other Reasoning Strategies": *"Despite many improved strategies proposed later, such as introducing ensemble (Wang et al., 2023c), reflection (Shinn et al., 2023), and search (Yao et al., 2023a), we evaluate LLMs with the most primitive CoT in AGENTBENCH. Without multiple trials, repeated generations, or complicated strategies, CoT is the easiest, cheapest, and most common way for people to deploy LLM agents."*

2. Appendix B.1, OS "Evaluation Setup — Checking": *"For each problem, there is a checking pipeline containing a list of scripts f1, f2, · · · , fn, where fk denotes the k-th script piece in the pipeline. For fk, the answer of the model, o0, and the output of ft(t < k), ot, will be fed as input arguments into fk, i.e., ok = fk(o0, o1, · · · , ok−1). The result is correct if and only if all the scripts exit with code 0."*

3. Appendix C.1, DB "Evaluation Setup — Checking": *"For insertion or updating types of problems, we calculate and compare the hash of the table after the agent's operation with the hash of the table after the correct SQL operation."*

4. Appendix J.2.4: *"As illustrated in Figure 9, more than 90% of the trajectories experiencing Task Limit Exceeded (TLE) demonstrate a significant level of repetition. This is evidenced by at least two responses within the last 10 rounds sharing a Rouge-L score of 0.8 or higher, indicating a notable degree of redundancy."*

5. Appendix F.2, LTP system validation: *"We compare the Single Game Accuracy and Query Relevance between automatic evaluation and human evaluation, and found that automatic evaluation sometimes more tolerate for the agent, which make SGA and QR seem better than human evaluation, especially on open-sourced models."*

6. §4.1, "Overall Score Calculation": *"We have observed that the score distribution for each task varies significantly as tasks differ in difficulty levels. As a consequence, a naively averaged score is heavily impacted by tasks that generally yield higher scores (e.g., Web Shopping in our observation), overshadowing those with lower scores and being unsuitable for AGENTBENCH's purpose."*

7. Appendix I.1, Web Browsing metrics: *"for the Task Success Rate, a task is considered successful only if all the steps have been successful, making it a rigorous measure. Unfortunately, even the best LLMs now can only achieve single-digit task success percentages."*
