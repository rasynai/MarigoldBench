# Deep read: PaperBench (arXiv 2504.01848v3, OpenAI, 7 Apr 2025)

"PaperBench: Evaluating AI's Ability to Replicate AI Research" — Starace, Jaffe, Sherburn, Aung, Chan, Maksin, Dias, Mays, Kinsella, Thompson, Heidecke, Glaese, Patwardhan (OpenAI).

## Coverage ledger

- Source PDF: A:/PERTURB-Bench/analysis/literature/pdfs/2504.01848.pdf (1,703,363 bytes, 30 pages, `%PDF-1.5`).
- Extracted text: A:/PERTURB-Bench/analysis/literature/md/2504.01848.md
- Total size: **105,707 bytes** (`wc -c`), **1,872 lines** (`wc -l`; the final line, a page number "30", has no trailing newline, so 1,873 display lines).
- Extraction reported by pypdf: 30 pages, 103,223 chars (byte count differs due to CRLF newline translation on write).
- Chunks read with the Read tool, sequentially, no gaps:
  - Chunk 1: lines 1–1200 (title through Appendix C Table 7 first half)
  - Chunk 2: lines 1201–1873 = EOF (Table 7 remainder, Appendices D–I, all prompt figures, task instructions)
- Every line of the file was paged through, including all appendices, all nine per-paper results tables, and all prompt-text figures.

## Section-by-section notes

### Abstract (lines 5–32)
20 ICML 2024 Spotlight and Oral papers must be replicated from scratch: understand contributions, develop a codebase, execute experiments. 8,316 individually gradable tasks via hierarchical rubrics co-developed with each paper's author(s). LLM judge with its own auxiliary benchmark (JudgeEval). Best tested agent: Claude 3.5 Sonnet (New) with open-source scaffolding, 21.0% average Replication Score. Top ML PhDs attempted a subset; "models do not yet outperform the human baseline." Code open-sourced.

### 1. Introduction (lines 33–131)
Motivation is safety-forward: PaperBench measures model autonomy for OpenAI's Preparedness Framework, Anthropic's RSP "autonomous capabilities," and Google DeepMind's Frontier Safety Framework. Each replication task "takes human experts several days of work at a minimum." 20 papers span 12 ICML topics. Rubrics decompose replication hierarchically; grading a single attempt manually can take "tens of hours." Best judge: o3-mini-high + custom scaffolding, F1 0.83 on JudgeEval. Headline numbers: Claude 3.5 Sonnet (New) 21.0%; human ML PhDs best-of-3 41.4% after 48 hours on a 3-paper subset vs 26.6% for o1 on the same subset; o1 scores 43.4% on the lighter PaperBench Code-Dev variant. Four listed contributions: PaperBench, PaperBench Code-Dev, JudgeEval, frontier-model evaluations.

### 2. PaperBench (lines 132–159): Task
Candidate receives the paper + an addendum of author clarifications; must output a repo with `reproduce.sh` at root that reproduces the paper's empirical results. The rubric is hidden from the candidate "to prevent overfitting to the evaluation criteria." Using or viewing the authors' original codebases is disallowed (measures from-scratch ability, contrast with CORE-Bench).

### 2.2 Reproduction (lines 201–226)
Submission is copied to a fresh VM (Ubuntu 24.04, A10 GPU); `reproduce.sh` is executed from a clean start, producing `reproduce.log` and output files ("executed submission"). This separates real reproduction from results hard-coded at task time. Footnote 1: runtime capped at 12h, "sufficient for all scripts to complete"; agent-produced reproduce.sh scripts executed for an **average of 5.5 minutes** — a striking tell about how little agents actually ran.

### 2.3 Grading (lines 218–245)
Rubric = tree; each leaf is a single pass/fail criterion; every node manually weighted relative to siblings. Judge grades leaves binary 0/1; parent score = weighted average of children; root score = Replication Score. Main metric = average Replication Score across papers.

### 2.4 Requirement Types (lines 246–309)
Three leaf types: (1) **Result Match** — did the executed submission replicate a specific result (judge sees reproduce.sh, reproduce.log, repro outputs, docs; NOT source code); (2) **Execution** — did some execution result occur when running reproduce.sh (sees source + reproduce files, not outputs); (3) **Code Development** — does source appear to correctly implement a requirement (sees source, docs, reproduce.sh only). Partial-credit rationale is explicit: Execution and Code Dev nodes exist "thus ensuring that agent performance on PaperBench improves incrementally." Missing reproduce.sh ⇒ 0 on all Execution and Result Match nodes. Table 1 maps file visibility per type.

### 2.5 Rules (lines 310–342)
Internet allowed except per-paper blacklists (authors' repo + online replications). No compute/runtime restrictions (report setups). Developers should supply API keys (e.g., HuggingFace). A simple post-hoc monitor greps logs for blacklisted URLs, escalating to manual review: **10 cases of blacklisted-resource use across all 646 runs**, disqualified by setting score to 0.

### 2.6 PaperBench Code-Dev (lines 343–363)
Lightweight variant: grade only Code Development nodes, skip the reproduction step; no GPU needed; grading cost drops ~85% ($66 → ~$10/paper with o3-mini judge). Performance is only "weakly correlated" with full PaperBench: footnote 5 gives Pearson r = 0.48 for o1, with PB = 0.45·PBCD + 0.05.

### 3. Dataset (lines 364–415, Table 2)
20 papers, all ICML 2024 Spotlight/Oral, curated per Appendix B; 2 NeurIPS 2024 Workshop papers released as a dev set; a held-out set is kept internal. Table 2 lists each paper with topic and rubric node counts, ranging 94 (stochastic-interpolants) to 2,551 (pinn).

### 3.1 Rubrics (lines 416–452)
Rubric construction was "the most time-intensive aspect" — multiple weeks per paper: reading, drafting, review, iteration, author sign-off. Decomposition continues until an expert human could verify a leaf in <15 minutes. 8,316 leaf nodes across 20 papers. Weights encode importance, "not necessarily the node's implementation difficulty."

### 3.2 Dealing with Underspecification (lines 455–461)
Per-paper addendum with author clarifications, including scope exclusions; where needed a judge-only addendum with reference info for grading. (Candidate-visible vs judge-only information is deliberately separated.)

### 4. LLM Judge / 4.1 SimpleJudge (lines 462–510)
Manual grading takes tens of hours/paper, so automation is necessary. SimpleJudge grades each leaf independently: prompt = paper markdown + full rubric JSON + leaf requirement + submission; codebase filtered by having the judge rank files, top 10 in context. Backend o3-mini-2025-01-31 (reasoning high): ~$66/submission (o1 pricing basis, 2025/03/21); ~50M input + 2M output tokens per paper; Code-Dev ~$10. Table 3 (JudgeEval, macro-averaged): Random 0.48 acc / F1 0.49; GPT-4o-mini F1 0.59 ($8); GPT-4o 0.73 ($120); o1-mini 0.78 ($72); o1 0.84 ($830); o3-mini 0.83 ($66).

### 4.2 JudgeEval (lines 511–531)
Aux benchmark: partial replications of 4 PaperBench papers + 1 dev-set paper, built from scratch or by modifying author codebases (footnote 8: author codebases are "often incomplete or contain bugs" and lack reproduce.sh, so they wouldn't score perfectly). Human experts manually graded each attempt's leaves = gold labels; judges evaluated as binary classifiers. o3-mini chosen as most cost-effective (F1 0.83 at $66).

### 5. Experiments / 5.1 Environment (lines 532–559)
Agents run in Ubuntu 24.04 Docker with one A10 GPU; workdir has paper PDF+MD, addendum, instructions; internet on; HuggingFace + OpenAI API keys with $1000 loaded. BasicAgent = Inspect AI basic-agent ReAct scaffold + nanoeval orchestration; tools: bash, python, browser, paginated file reader.

### 5.2 Main Experiment (lines 560–626, Tables 4–6)
GPT-4o, o1, o3-mini, DeepSeek-R1, Claude 3.5 Sonnet (New), Gemini 2.0 Flash; 20 papers × 3 runs; 12h limit. (Claude 3.7 Sonnet skipped — Anthropic API rate limits.) BasicAgent Replication Scores (±1 SEM): o3-mini-high 2.6±0.2; Gemini 2.0 Flash 3.2±0.2; GPT-4o 4.1±0.1; DeepSeek-R1 6.0±0.3; o1-high 13.2±0.3; Claude 3.5 Sonnet 21.0±0.8. Failure modes from log inspection: all models except Claude 3.5 Sonnet frequently finished early (claiming completion or unsolvable problems); all failed to strategize under the time budget; o3-mini struggled with tools. Interpretation: models can write multi-step plans but "fail to actually take series of actions that execute that plan." Authors frame results as an initial baseline, not an upper limit.

### 5.3 IterativeAgent (lines 627–666, Table 5)
Variant that removes the submit/end-task tool and prompts stepwise work. o3-mini 8.5±0.8 (up from 2.6); o1 24.4±0.7 (up from 13.2); Claude 3.5 Sonnet 16.1±0.1 (DOWN from 21.0) — "highlighting models' sensitivities to prompting"; the tuning is "differentially suited for OpenAI o-series models." o1 with 36h limit: 26.0±0.3.

### 5.4 Human Baseline (lines 667–725, Figure 3)
8 participants, current/completed ML PhDs (Berkeley, Cambridge, CMU, Columbia, Cornell, Purdue, TU Wien, UMass Amherst), hired via CV screen + ML/git technical test. 4-paper subset, 3 independent attempts/paper, best@3 = "expert" score. Similar conditions to agents (single A10; footnote 19: four attempts got an A100 for availability, deemed insignificant since reproduction still on A10; AI assistants like ChatGPT/Copilot allowed; blacklists still apply). Part-time over a 4-week window; graded after week 1, only best performer extended. Tracked hours via timesheet (unattended experiment time counts). o1 IterativeAgent extended to 36h, snapshots graded at 1/3/6/12/36h. Result: o1 beats humans in the first hours but "plateaus after the first hour"; humans overtake after 24 hours (consistent with RE-Bench/Wijk et al. 2024). The test-time-model-adaptation human attempt stopped at 24h, hence the "3-paper subset" (humans best@3 41.4% at 48h vs o1 26.6%). Model error bars = SEM over 3 repeats.

### 6. Related Work (lines 726–766)
CORE-Bench (reproduce given repo — PaperBench is from scratch); MLE-bench/MLAgentBench/DSBench (Kaggle-style, "dated and relatively simple"); RE-Bench (7 tasks with scoring functions; PaperBench = broader, longer horizon, no viable scoring functions); ideation work (Si et al.); toy-discovery environments (DiscoveryWorld, ScienceWorld). Judge lineage: MT-Bench, MLLM-as-a-Judge, GPTScore, Agent-as-a-Judge; "We benchmark the judging capability of models on significantly harder tasks than what has been used before."

### 7. Limitations (lines 767–823)
(1) **Dataset size**: only 20 papers, but each rubric has hundreds of nodes ⇒ thousands of requirements. (2) **Contamination**: authors' codebases exist online for almost all papers; pretrained models "may have internalized solutions"; recency protects current models but not future ones. (3) **Challenging dataset creation**: several full expert-days per rubric; "We found it to be challenging to train others to create rubrics at our desired quality level"; suggests model-assisted rubric generation. (4) **LLM judge**: not as accurate as an expert human; non-deterministic; adversarial submissions un-stress-tested. (5) **Cost**: ~$400/paper for an o1 IterativeAgent 12h rollout ⇒ $8,000/eval run for 20 papers + $66/paper grading; PBCD ≈ $4,000 + $10/paper; pruned-rubric judging (Appendix H) shows a 10x grading-cost reduction.

### 8. Conclusion + Impact Statement (lines 824–882)
Restates 21.0% best score; agents "far from competently performing the full range of tasks." Impact statement: replication ability indicates autonomy/ML expertise; risk that self-improving R&D outpaces oversight; open-sourcing supports measurement of autonomous R&D capabilities.

### Acknowledgements + References (lines 883–1093)
Names the 22 paper authors who validated rubrics and the 8 human-baseline participants; standard references (all 20 dataset papers cited).

### Appendix A. Future Directions (lines 1096–1136)
Rubrics convert complex, unstructured, non-programmatically-gradable outputs into simpler well-specified checks; author collaboration resolves underspecification ("there exist many different realizations of our paper rubrics which are no less valid"). A.1: child-node order encodes dependencies, but the rubric doesn't specify which prerequisites matter; dependency graphs proposed. Automated rubric creation: frontier models are "excellent partners for understanding and summarizing papers" but "struggle to create reliable rubrics from start to end, even with significant prompt engineering." A.2: better judges ⇒ coarser decomposition suffices; a specification-vs-delegation trade-off. A.3: cannot rule out rubric loopholes; agents may sandbag (van der Weij) or specification-game (DeepMind, Pan et al.); stress-testing left to future work.

### Appendix B. Paper Selection (lines 1137–1167)
Systematic filtering of ICML 2024 Spotlight/Orals, initial filtering implemented with gpt-4o-2024-08-06 prompts: commercial/geographic filter (≥75% authors with constraint-affiliations excluded); empirical-content filter (no position/pure-theory/framework papers); hardware filter (no multi-node distributed training); model-dependency filter (no closed-source pretrained model dependencies); data filter (no human data collection/annotation); reproducibility filter (enough detail to replicate from the paper); framework filter; accessible-dependencies filter. Then random selection + manual read; contacted 42 authors to secure 20 collaborations.

### Appendix C. Rubric and Addendum Creation (lines 1168–1206, Table 7)
Two research engineers draft; several internal review rounds; original author verifies under a formal agreement, multiple feedback rounds; clarifications folded into addendum. "On average, the creation of a rubric and its addendum takes many tens of hours of labor." Table 7 per-paper node counts (total / leaves / CodeDev / Execution / ResultMatch), e.g. pinn 2551/1963/126/1815/22; lbcs 1471/916/485/410/21; what-will-my-model-forget 1146/921/872/28/21; bam 1021/789/255/518/16; smallest stochastic-interpolants 94/69/58/7/4. Result Match leaves are rare (4–71 per paper).

### Appendix D. SimpleJudge Implementation (lines 1178–1223)
Prompt includes paper markdown, addendums, preceding criteria (siblings + direct ancestors), leaf requirement, relevant files. File selection: whitelist source/docs/config (blacklist venv etc.); if the filtered submission fits in (n_ctx − 10,000) tokens, concatenate everything; else the judge ranks files and adds in descending relevance to the limit. For Result Match: whitelist plaintext tabular files (CSV/JSON/JSONL/HTML) modified after reproduce.sh start. gpt-4o-2024-08-06 parses the judge output into {score 0/1, explanation, valid_score flag}.

### Appendix E. Monitor (lines 1224–1228)
Plain text search over logs for blacklisted terms; hits logged with surrounding context for human review.

### Appendix F. Agent Implementation (lines 1232–1270 + Figures 10–14)
API-retry time not counted toward limits. BasicAgent mods vs Inspect basic agent: submit reframed as "end task"; context-length management drops old non-instruction messages; paginated file reader. Preliminary failure modes: describing plans instead of acting; o1 attempting one-shot finishes; not reading the full paper; ending early. IterativeAgent: per-query "take the next step" instruction; submit tool removed; separate system prompt + continue message. Task instructions (Figures 13–14): replicate core contributions with prioritization; partial credit weighted by importance; "reasonable margin of error" on metrics; appendix-only experiments out of scope; submission = git repo ≤1GB at /home/submission with reproduce.sh; graded after `git clean -fd`; fresh Ubuntu 24.04 container, max runtime 7 days (instructions) with A10; README required; agents told rubric.json "may or may not" be provided; API keys for OpenAI/Anthropic/Gemini/OpenRouter in agent.env; "you must use all the time available."

### Appendix G. More on JudgeEval (lines 1271–1316, Figure 5, Table 8)
F1-vs-cost plot; human judge cost estimated at 12h × $100/hr = $1,200/paper ("hundreds of dollars more costly than the most expensive model"); o3-mini ≈ o1 performance at one-tenth cost. Table 8 stratified F1: o3-mini overall 0.83 = CodeDev 0.72 / Execution 0.82 / ResultMatch 0.94; o1 0.84 = 0.74/0.84/0.88; random ≈ 0.45–0.49. "Models struggle most on Code Development nodes and perform best on Result Match nodes"; 0.72 deemed "acceptable for tracking signal."

### Appendix H. Pruned Rubric Grading (lines 1317–1334, Figure 6)
Collapse subtrees past a depth into single leaves graded with a float 0–1. On JudgeEval's rice/0 submission: depth 1 ⇒ 0.93±0.04; depth 2 ⇒ 0.48±0.01; depth 3 ⇒ 0.30±0.01; depth 4 ⇒ 0.27±0.00; no pruning (depth 100) ⇒ 0.25±0.00, vs human gold. Depth-3 pruning cuts grading cost 10× with slight degradation — but shallow pruning wildly inflates scores (0.93 vs 0.25), and they note "cases of unsatisfactory performance." Error bars = SEM over 3 repeats.

### Appendix I. Full Results (lines 1335–1583, Tables 9–18)
Per-paper, per-run scores for every model. "For most agents, we see high variance in results on the same paper"; they recommend several seeds. Table 9 stratified by requirement type (SEM across 3 seeds, except o1-IterativeAgent and Gemini across 2): CodeDev vs Execution vs ResultsAnalysis — Claude 3.5 Sonnet Basic 35.4±0.8 / 1.8±0.7 / 0.7±0.3; o1 Iterative 43.3±1.1 / 4.5±1.5 / 0.0±0.0; o1 36h 42.4±1.0 / 7.4±1.1 / 1.4±0.1; humans best@3 (3-paper) 72.4 / 20.4 / 8.9. Result-Match scores are ~0 for every model. Per-paper spreads are huge (e.g., o1 Basic sample-specific-masks runs: 0.448/0.229/0.098; o3-mini Iterative sequential-neural-score-estimation: 0.680/0.542/0.144). Asterisks mark disqualified runs set to 0; one Gemini run lost to infrastructure failure.

### Figures 7–14 (lines 1586–1872)
Full verbatim prompts: judge file-ranking prompt; two-part judge prompt (with color-coded variants per node type and for Code-Dev; forced 3-part "Expectations / Reality / Score" output; "Be strict and thorough… but do not check for things that are outside of your scope"; missing artifacts are failures); BasicAgent and IterativeAgent system prompts; IterativeAgent continue message; two-part task instructions with a toy "count the r's in strawberry" grading example.

## Benchmark anatomy

- **N items**: 20 papers (units of evaluation), decomposed into **8,316 gradable leaf nodes** (94–2,551 total nodes per paper; leaves 69–1,963). Three leaf types: Code Development (majority), Execution, Result Match (rare: 4–71/paper). Plus 2 dev papers (NeurIPS 2024 workshops) and an internal held-out set.
- **Construction**: ICML 2024 Spotlight/Oral pool → 8 automated filters (run by GPT-4o with prompts) → random selection + manual read → author outreach (42 contacted, 20 secured).
- **Item authorship**: rubrics drafted by two OpenAI research engineers, iterated through internal review, then validated and signed off by an original author of each paper under formal agreement; author clarifications become the addendum. Multiple weeks / "many tens of hours" per rubric.
- **Validation/review**: internal review rounds + author sign-off; leaf granularity standard = expert-verifiable in <15 minutes; no inter-rater reliability numbers reported for rubric quality or for the human gold-label grading.
- **Human baseline**: 8 ML PhDs, screened (CV + ML/git test), 4 papers × 3 independent attempts, best@3, part-time over 4 weeks, timesheets, snapshot grading; best@3 = 41.4% at 48h on the 3-paper subset (one paper's attempts stopped at 24h and was excluded).
- **Contamination defenses**: paper recency (post-cutoff-ish, ICML 2024); per-paper blacklists of author repos/replications; post-hoc log monitor (text search) + manual review, 10/646 runs disqualified; rubric hidden from candidates; reproduction on a fresh VM to defeat hard-coded results. Admitted residual risk: pretraining internalization of online author codebases.
- **Scoring**: leaf-level binary judgments → weight-averaged up the tree → Replication Score per paper → mean across papers. Partial credit is a design goal (incremental progress). Non-compensatory only at the leaf level, fully compensatory above it.
- **Judge design**: SimpleJudge (o3-mini-high) grades each leaf independently with paper+addendum+ancestor context and relevance-ranked files (top-10 fallback); per-node file-visibility rules by leaf type; response parsed by GPT-4o. Judge validated on JudgeEval (5 papers' graded submissions; human expert gold labels): F1 0.83 overall; 0.72/0.82/0.94 by CodeDev/Execution/ResultMatch; cost $66/paper (~50M in / 2M out tokens). Human judging estimated 12h/$1,200 per paper.
- **Statistical reporting**: ±1 SEM over 3 seeds (2 seeds for two configs) on aggregate scores; per-paper means with SEM over 3 runs; **no confidence intervals, no clustering by paper, no hypothesis tests, no judge-uncertainty propagation, no inter-human agreement**. Explicit warning of high per-paper variance and advice to run several seeds.

## Reported results

- BasicAgent (mean Replication Score ±1 SEM, 3 seeds, 20 papers): o3-mini-high 2.6±0.2; Gemini 2.0 Flash 3.2±0.2 (2 seeds for stratified table); GPT-4o 4.1±0.1; DeepSeek-R1 6.0±0.3; o1-high 13.2±0.3; **Claude 3.5 Sonnet (New) 21.0±0.8** (headline best).
- IterativeAgent: o3-mini 8.5±0.8; Claude 3.5 Sonnet 16.1±0.1 (regression vs BasicAgent); o1 24.4±0.7; o1 at 36h: 26.0±0.3.
- PaperBench Code-Dev: o1 43.4±0.8.
- Human vs model (3-paper subset): humans best@3 41.4% at 48h; o1 26.6%. o1 beats humans before ~24h, then plateaus (plateau begins after hour 1).
- Stratified (Table 9): CodeDev ≫ Execution ≫ ResultMatch for all models; best model ResultMatch ≤1.4%; human best@3 72.4/20.4/8.9.
- JudgeEval: o3-mini F1 0.83 ($66/paper); o1 0.84 ($830); GPT-4o 0.73 ($120); GPT-4o-mini 0.59 ($8); o1-mini 0.78 ($72); random ≈0.49. Stratified o3-mini: 0.72/0.82/0.94.
- Pruned grading (one submission): depth-1 0.93±0.04 vs unpruned 0.25±0.00 (gold ≈ human); depth-3 0.30±0.01 at 10× cheaper.
- Ops numbers: 646 total runs; 10 disqualifications; reproduce.sh average execution 5.5 minutes (12h cap); rollout cost ≈$400/paper (o1, 12h), $8,000/full run; grading $66/paper ($10 Code-Dev); PB↔PBCD correlation r=0.48 (o1), PB = 0.45·PBCD + 0.05.

## Limitations

### Admitted by the authors (Section 7, Appendix A)
1. Only 20 papers (defended by the 8,316-node count).
2. Contamination risk from authors' public codebases for future (post-training-cutoff) models.
3. Rubric creation is extremely labor-intensive (several expert-days each) and hard to delegate; scaling the dataset is bottlenecked.
4. LLM judge is below expert-human accuracy and non-deterministic; adversarial/gaming submissions not stress-tested; rubric loopholes can't be ruled out.
5. Cost ($8k/run + grading).
6. Prompt/scaffold sensitivity (Claude ranking flips between agents); results are baselines, not upper limits.
7. Code-Dev variant only weakly correlates with the full benchmark (r=0.48).

### Observed, not (fully) admitted
1. **No inter-rater reliability anywhere**: JudgeEval gold labels come from human grading with no reported second grader or agreement statistic; rubric-quality checks are process-based (author sign-off), not measured.
2. **Judge error is not propagated**: with leaf F1 0.83 (and 0.72 on the dominant CodeDev type), a 21.0% vs 13.2% model gap is reported without any analysis of how judge false positives/negatives bias or widen aggregate scores. Given most leaves are CodeDev and models' scores are mostly CodeDev credit, the headline metric leans on the judge's weakest category.
3. **SEM over 3 seeds is the only uncertainty**; paper-to-paper variance (the dominant component, visible in Tables 10–18) is never separated from seed variance; no clustered or bootstrap CIs; model comparisons (e.g., R1 6.0 vs GPT-4o 4.1) are made without tests.
4. **Human-vs-model comparison is asymmetric**: humans get best@3 at 48h; o1 gets (apparently) mean over 3 repeats at 36h; humans worked part-time over weeks with AI assistants allowed and four attempts on A100s. "Models do not yet outperform the human baseline" rests on a 3-paper, 8-person, asymmetric protocol.
5. **Partial credit inflates apparent capability**: 21.0% headline is nearly all code-written credit; true end-to-end replication (Result Match) is ~0–1.4% for every model — arguably the honest "replication" number, mentioned only in Appendix I.
6. **Monitor is weak**: text search over logs catches only literal blacklisted URLs; memorized (pretrained) solutions or paraphrased pulls are invisible; disqualification is binary score-zeroing.
7. **The 12h reproduce cap + 5.5-minute average script runtime** means the reproduction phase barely exercises submissions; many papers need days of compute, so Result Match may be unreachable within the environment budget, conflating agent failure with environment constraint (instructions even promise a 7-day runtime that experiments don't use).
8. **Selection filters bias the dataset** toward single-GPU, open-model, no-human-data papers — the "state-of-the-art AI research" claim covers only the replicable-on-one-A10 slice of it.
9. Judge context management (top-10 file ranking, n_ctx−10k truncation) is unvalidated as a source of grading error for large submissions.

## Implications for CRUCIBLE-CHAIN

1. **Hide the grading spec from the candidate; keep a judge-only addendum.** PaperBench's core anti-overfitting move is that "the candidate is not shown the rubric during its attempt" while a separate judge-only addendum carries grading reference info (Sections 2.1, 3.2). CRUCIBLE-CHAIN's saturation came precisely from prompts leaking method recipes and answer menus — restructure every template so the candidate-visible prompt contains only the scenario and data, and move stage criteria, expected-form hints, and any enumerable answer space into a grader-only artifact. Then add a release gate that greps candidate-visible text for recipe/menu tokens, the way PaperBench's monitor greps logs for blacklist hits.

2. **Template count is your real n; PaperBench's own defense ("20 papers but 8,316 nodes") doesn't transfer.** PaperBench smooths variance by averaging hundreds of weighted leaves per paper; CRUCIBLE-CHAIN's non-compensatory all-stages-right scoring makes each instance a single Bernoulli outcome, and instances within one template are correlated (same recipe, same trap structure). With 8 templates, cluster-robust n is 8 — far below what any significance claim needs. Concretely: to show "frontier model at ≤10% vs 30%" with a two-proportion test at alpha=0.05, power 0.8, you need ~60+ independent items per condition; to make claims robust to template effects, target **25–40 independent templates × 6–10 instances × ≥3 repeats per model** (PaperBench's Appendix I explicitly recommends multiple seeds after observing per-paper run variance like 0.448/0.229/0.098), and report SEM/CIs clustered at template level — which PaperBench never does and visibly should have.

3. **Keep the headline non-compensatory, but log stage-level diagnostics for free.** PaperBench deliberately added Execution/CodeDev partial credit so scores "improve incrementally" — the direct cause of a 21% headline that masks ~0% true end-to-end replication (Table 9). CRUCIBLE-CHAIN's all-stages metric is the right refusal of that trap; keep it, but emit the per-stage pass ledger (your generator already knows each stage's truth) as a secondary stratified table, exactly like Table 9, so you can (a) locate where chains break, (b) verify each stage's attractive-wrong-path actually attracts, and (c) show incremental progress to sponsors without inflating the pass rate.

4. **Build a JudgeEval-equivalent before trusting any LLM grading — and hand-check the deterministic grader too.** PaperBench's o3-mini judge hits only F1 0.83 overall and 0.72 on code-correctness judgments, validated against human gold labels on 5 papers' submissions. Any CRUCIBLE-CHAIN stage graded by an LLM (e.g., "did the model justify refusal for the flawed-premise condition correctly?") needs a gold-labeled transcript set with reported agreement, re-run on every judge-model change; and even the deterministic string/value matcher deserves an audited sample, since parsing model outputs into stage answers is itself a judging step. Report judge agreement alongside headline scores — CRUCIBLE-CHAIN's near-zero label error is a genuine edge over PaperBench only if the answer-extraction layer is verified.

5. **Adopt the dev/held-out split as a saturation canary.** PaperBench ships 2 dev papers and keeps an internal held-out set. CRUCIBLE-CHAIN should freeze a private set of templates (including novel trap structures, not just new instances of public templates) never included in released prompts; a public-vs-held-out score gap directly measures recipe leakage/overfitting — the exact failure that caused the 94–100% saturation. New public releases graduate from the held-out pool.

6. **Measure scaffold/prompt sensitivity before claiming "single-digit frontier pass rates."** PaperBench's ranking inverted across two scaffolds (Claude 21.0→16.1, o1 13.2→24.4; "highlighting models' sensitivities to prompting"), and IterativeAgent's forced-full-time design shows harness choices can double scores. Run each model under ≥2 prompt framings (e.g., with/without explicit stage decomposition) and report the max, so a single-digit claim can't be dismissed as a harness artifact; conversely, if a framing change lifts a model from 5% to 40%, the templates are leaking structure again.

7. **A solvability baseline is mandatory for a benchmark targeting single-digit model scores.** PaperBench's expensive 8-PhD baseline exists to prove tasks are humanly tractable and to anchor "models don't outperform humans yet" — but its asymmetries (best@3 vs mean, 48h vs 36h) blunt the claim. For CRUCIBLE-CHAIN: have blinded expert humans (or the authors under leakage-free conditions) attempt a sample of instances per condition; report human and model scores under identical k-attempt statistics (both mean@k and best@k). Also copy the operational hygiene: timesheets/snapshots (for time-scaling curves), disqualification marks in results tables, and infrastructure-failure disclosure — cheap credibility for the next campaign report.

8. **Exploit the cost asymmetry.** PaperBench pays $8,000/run plus $66/paper judging and had to invent Code-Dev and pruned-rubric variants (10× cheaper, but depth-1 pruning inflated a 0.25 score to 0.93 — coarse holistic judging fails). CRUCIBLE-CHAIN's deterministic scoring costs ~nothing, so the budget frontier is entirely rollouts: spend it on more templates and ≥3 repeats per cell (model × condition × instance) rather than on grading; and never replace stage-wise deterministic checks with a single holistic LLM judgment, which Appendix H shows is exactly where scores decouple from truth.

## Verbatim quotes

1. "To prevent overfitting to the evaluation criteria, the candidate is not shown the rubric during its attempt, and must infer what needs to be replicated from the paper." — Section 2.1 Task (de-hyphenated across the PDF line break "dur-/ing")
2. "We find 10 cases of using blacklisted resources across all 646 runs we conducted for our results, and disqualify these submissions by setting their score to 0." — Section 2.5 Rules
3. "We find performance on PaperBench Code-Dev to be weakly correlated with performance on the full PaperBench eval." — Section 2.6 (footnote 5: "o1 performance correlates with a Pearson r value of 0.48, with PB = 0.45PBCD + 0.05.")
4. "Our best LLM-based judge, which uses o3-mini-high with custom scaffolding, achieves an F1 score of 0.83 on the auxiliary evaluation, suggesting that this judge is a reasonable stand-in for a human judge." — Abstract/Section 1
5. "IterativeAgent removes the ability of models to end the task early and prompts models to work in a piecemeal fashion. We observe that these modifications significantly boost scores for o3-mini and o1 compared to BasicAgent, but hamper Claude 3.5 Sonnet, highlighting models' sensitivities to prompting." — Table 5 caption, Section 5.3
6. "All agents failed to strategize about how best to replicate the paper given the limited time available to them." — Section 5.2
7. "This trend of agents initially outperforming humans but falling behind at longer time horizons is consistent with previous results Wijk et al. (2024)." — Section 5.4
8. "Since each rubric is composed of hundreds of nodes, PaperBench evaluates agents on thousands of different individual requirements." — Section 7, Dataset Size
9. "PaperBench rubrics have been carefully designed to avoid false negatives and false positives, but given the large number of nodes and the complexity of paper replication, we cannot yet rule out loopholes in our evaluation." — Appendix A.3
10. "However, we found frontier models struggle to create reliable rubrics from start to end, even with significant prompt engineering." — Appendix A.1
11. "Notably, for most agents, we see high variance in results on the same paper. Due to the high variance, we recommend others to use several seeds when evaluating PaperBench to get an accurate measure of agent performance." — Appendix I
