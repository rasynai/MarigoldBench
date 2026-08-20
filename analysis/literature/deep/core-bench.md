# Deep read: CORE-Bench (arXiv 2409.11363v2)

**Full title:** CORE-Bench: Fostering the Credibility of Published Research Through a Computational Reproducibility Agent Benchmark
**Authors:** Zachary S. Siegel, Sayash Kapoor, Nitya Nadgir, Benedikt Stroebl, Arvind Narayanan (Princeton University)
**Version read:** arXiv:2409.11363v2 [cs.CL], stamped 22 Jun 2026; body dated September 17, 2024. Code: https://github.com/siegelz/core-bench

## Coverage ledger

- Source file: `A:/PERTURB-Bench/analysis/literature/md/2409.11363.md` (extracted from `A:/PERTURB-Bench/analysis/literature/pdfs/2409.11363.pdf`, 30 pages, 2,885,202-byte PDF)
- Total size: **106,621 bytes** (`wc -c`), 103,994 characters as counted by python `len()` on the extracted string, **1,337 lines** (`wc -l`)
- Chunks read with the Read tool, sequential and complete:
  - Chunk 1: lines 1–700 (title through references up to Stockemer et al.)
  - Chunk 2: lines 701–1337 (remaining references, Appendices A–E, to end of file)
- Union of chunks: lines 1–1337 = entire file. Nothing skipped; all appendices, tables, listings, prompts, and trajectory transcripts read.

## Section-by-section notes

### Abstract
Introduces CORE-Bench: 270 tasks from 90 scientific papers across computer science, social science, and medicine; three difficulty levels; language-only and vision-language tasks. Evaluation system runs tasks in parallel, "saving days of evaluation time for each run." Two baseline agents: general-purpose AutoGPT and task-specific CORE-Agent, each with GPT-4o and GPT-4o-mini. Best agent: 21% on the hardest level. Framing: reproducing existing work is a necessary step toward agents that conduct novel research and could "verify and improve the performance of other research agents."

### 1 Introduction
- Opens with Buckheit & Donoho (1995) quote: an article is "merely advertising of the scholarship."
- Table 1 surveys computational reproducibility failures *despite available reproduction materials* across 15+ fields, 19 studies. Notable rows (studies reviewed / studies with comp. rep. errors): Finance, Pérignon et al. 2024: 1008/484; Multiple, Trisovic et al. 2022: 2000/1480; NLP, Belz et al. 2021: 549/472; ML, Raff 2019: 255/82; Computer Systems, Collberg & Proebsting 2016: 601/311; Economics, McCullough et al. 2006: 150/135; Economics, Gertler et al. 2018: 203/128; Medicine, Naudet et al. 2018: 17/3; Psychology, Hardwicke et al. 2021: 25/16; Geosciences, Konkol et al. 2019: 41/39.
- Authors' own analysis of the 2022 ML Reproducibility Challenge: only 18 of 28 papers with code and data were completely reproducible; in 6/28 cases participants failed even after conversing with original authors.
- Context: LLMs solve most of HumanEval but real-world coding is hard; on SWE-bench LMs alone <5%, agents >30%. AI-Scientist-style claims (Lu et al. 2024) motivate the question: "Can AI agents automate computational reproducibility of published scientific research?"
- Contribution 1: CORE-Bench — 270 tasks, 90 papers, Python or R, curated from CodeOcean; three difficulty levels defined by information provided; "one of the first to include tasks in R"; periodic updates from public repositories "could mitigate concerns about contamination and saturation."
- Contribution 2: baseline results (AutoGPT, CORE-Agent) plus an evaluation harness on isolated VMs; reduces evaluation from over 20 days sequential to "mere hours" (~2 hours) on hundreds of parallel VMs.

### 2 CORE-Bench: Evaluating agents on computational reproducibility
Positions against related benchmarks (ML experiments: Huang et al. 2023; research programming: Tian et al. SciCode; scientific discovery: DiscoveryBench; citation: CiteME; real-world programming: PyBench). Claim: research reproduction "hasn't yet received attention."

- **Table 2 (capsule selection criteria):** ten criteria with rationales — publicly accessible paper; from CS/medical/social science (assess distribution shift); Python or R; contains a README ("Improves construct validity"); runs under 45 minutes on CodeOcean hardware; "Requires a relatively simple Bash command to reproduce"; results adequately labeled with figure/table/file names; results have low variance ("verifiable and reproducible by a human"); capsule under 10 GB; results reproduce locally. Authors compare this filtering to SWE-bench Verified (Chowdhury et al. 2024). Explicit admission: "Not all papers in the real world meet these criteria; however the criteria improve task clarity and therefore ensure a high accuracy on the benchmark is attainable given the current state of agent development."
- Figure 3: funnel from 5,090 CodeOcean capsules → 90 selected.

#### 2.1 Benchmark Construction
- Design principle: "we want the tasks in the benchmark to be realistically difficult, but we need the construction of the benchmark itself to be much easier than solving the benchmark." Verifying one wild paper can take hours, so ~100 diverse papers would be impractical; hence CodeOcean capsules, "known to be reproducible with little effort" (Clyburne-Sherin et al. 2019).
- 90 papers, split 45 train / 45 test. Task questions written manually per paper about outputs of a successful reproduction (e.g., test accuracy, an axis label). Some tasks have one question, others multiple (1–8 per capsule; 181 questions total).
- Guess-proofing: each task has at least one question that cannot be solved by guessing (open-ended numerical answer), and a task is correct only if ALL task questions are answered correctly.
- Only reproducible papers included, by design: the benchmark measures reproducing the *code's* results, not verifying the *paper's* claims.
- **Table 3 (ladder of difficulty):** 270 tasks and 181 task questions; same questions at all levels, differing only in information given. Easy: complete code output from a successful run provided (pure information extraction). Medium: Dockerfile plus README instructions (run Docker command, then extract). Hard: README only — install all libraries/dependencies, determine and run the correct command, then extract.
- **Figure 4:** task execution pipeline and evaluation criteria. Each capsule manually reproduced **three times**; an agent solves a task iff its reported results for all questions "fall within a 95% prediction interval for every task question of the results from the three manual runs (although only 17 / 181 task questions have stochastic answers)." Prediction intervals cited to Spence & Stanley (2016).

#### 2.2 Why use CORE-Bench?
- Skills: instruction understanding, debugging, retrieval, result interpretation; both text and image outputs. Vision questions extract from figures/plots/PDF tables (example: "From the Indoor Air Quality - Kitchen - Autumn plot, report the correlation between hum and gas"); text questions from terminal output, PDF text, HTML/markdown/latex tables.
- Construct validity argument (Biderman et al. 2024; Raji et al. 2021; Kapoor & Narayanan 2023): tasks correspond closely to real researcher work, unlike toy coding benchmarks.
- "First step towards research agents": reproducing existing work is necessary and more attainable than novel research.

### 3 Baseline agents and evaluation setup
- **AutoGPT** (Significant Gravitas 2024): largely unmodified; added a `query_vision_language_model` tool (image+query → OpenAI API response) since VLM querying is not CORE-Bench-specific; they plan to upstream it.
- **CORE-Agent**: AutoGPT variant customized per difficulty level. Primary change: programmatic check that `report.json` is submitted with correct keys. Plus per-level prompt hints (Table 4) addressing failure modes observed on the *training set*. "These adaptations required only a few days of work."
- **Table 4 (modifications):** All levels: report.json check. Easy: use pdftotext/pdftoppm; check full results directory for images before VLM queries; prioritize 'output'/'manuscript' files; convert HTML to PDF/PNG; print directory tree and analyze five most relevant files. Medium: + use absolute paths instead of env vars in execute_shell. Hard: + determine and install dependencies before running code (AutoGPT's error: "Greedily installing dependencies in response to code failures, without a plan").
- **Models:** GPT-4o-2024-05-13 and GPT-4o-mini-2024-07-18 (AutoGPT devs recommend GPT-4 family). $4 API cost cap per task; Figure 7 shows this did not majorly impact accuracy.
- **Metrics:** task accuracy = proportion of tasks with ALL questions answered correctly; plus average API cost.
- **Harness:** each task in an isolated VM (cites Inspect/AISI 2024 and METR Vivaria); Manager machine creates a Worker VM per (agent, task) pair, uploads capsule+agent, runs in parallel, downloads results, deletes VM, evaluates locally. 270 tasks, 181 questions, 2-hour per-task limit: sequential would exceed 20 days; harness "took a little over two hours." Prevents agents from tampering with benchmark evaluations.

### 4 Results
- **Table 5 (test set, pass@1; CORE-Agent averaged over 3 runs, AutoGPT run once due to cost):**
  - CORE-Agent + GPT-4o: Easy 60.00%, Medium 57.78%, Hard 21.48%
  - CORE-Agent + GPT-4o-mini: 44.44% / 32.59% / 16.30%
  - AutoGPT + GPT-4o: 35.56% / 37.78% / 6.67%
  - AutoGPT + GPT-4o-mini: 8.89% / 2.22% / 2.22%
- Test split reported throughout since train was used for agent development (train results in Fig A1).
- **4.1** Accuracy ordered Easy > Medium > Hard as designed (e.g., mini: 44.44/32.59/16.30).
- **4.2** Task-specific modifications help, especially weaker models: GPT-4o Easy 35.6% → 60.60% (note: text says 60.60% here vs 60.00% in Table 5); GPT-4o-mini Easy 8.9% → 44.44%. Hypothesis: stronger future models will need fewer task-specific modifications.
- **4.3** Stronger models win despite lower token budget: GPT-4o-mini per-token cost <5% of GPT-4o, agents 3–5x cheaper, but GPT-4o still outperforms. Cost-limit ablation (train set, Hard): raising cap $4→$10 left mini unchanged; GPT-4o rose modestly 26%→31%. Mini outperformed GPT-4o below ~$2.50 cost limits. Success is cheap: average cost of successful tasks $0.54 vs $2.59 for failed tasks (CORE-Agent, GPT-4o); failures tend to hit the cap while stuck.
- **4.4** Written questions easier than vision: CORE-Agent+GPT-4o on Easy test: 59.26% vision vs 87.88% written; mini: 37.78% vision vs 81.81% written. Vision failures: finding the relevant figure among many outputs, then analyzing it.
- **4.5** Python much easier than R (Figure 8; error bars = one standard deviation over three trials). R outputs often full PDF manuscripts; R dependency installation slower. CS tasks disproportionately Python, which may explain CS being most reproducible.
- **4.6** Qualitative failures: Easy — wrong-file/wrong-figure retrieval when output spans multiple files; Medium — AutoGPT ignoring the Docker instruction and manually reproducing (competing instructions), which CORE-Agent's task prompts fixed; Hard — dependency-resolution loops until the cost cap ("getting stuck attempting to install the same library multiple times").
- **4.7** Safety: an agent tried to create a CodeOcean account to look up the capsule; blocked only because CodeOcean requires JavaScript. Release harness now restricts access to the CodeOcean.com domain. Call for guardrails (cites He et al. 2024): "there are no existing safeguards preventing simple agent errors such as creating thousands of accounts on a website."

### 5 Conclusion
Automating reproducibility is hard but task-specific modifications already help (consistent with SWE-agent findings, Yang et al. 2024). Best baseline: 21% test accuracy on Hard — "vast room for improvement." Goal: reduce human labor in reproducibility assessment.

### Acknowledgments
Veniamin Veselovsky for discussions; compute from Princeton CSML and OpenAI researcher access program.

### References
~60 entries. Notable anchors: SWE-bench (Jimenez et al.), SWE-bench Verified (Chowdhury et al.), AutoGPT, AI Scientist (Lu et al.), AI Agents That Matter (Kapoor et al. 2024 — same group; source of cost-controlled evaluation and retry arguments), tau-bench (Yao et al. — source of pass^k), Spence & Stanley (prediction intervals), Inspect (AISI), Vivaria (METR), plus the 19 reproducibility-failure studies in Table 1.

### Appendix A: Benchmark Details
- **A.1 Original CodeOcean dataset:** webscraper downloaded metadata for all 5,090 capsules; environment files manually exported from CodeOcean's web interface; then filtered by the ten Table 2 criteria.
- **A.2 Examples of selection criteria:** Listing 1: capsule 5507257's run file, a single `python -u multiclass_state_analysis_testing.py "$@"` command (satisfies criterion six, simple Bash command). Listings 2–3: capsule 826891 rejected for high variance — spike probability 0.42303016781806946 on first manual run vs 0.7832228541374207 on second.
- **A.3 Task question construction:** authors examined each capsule's results folder after a successful CodeOcean run, chose outputs (model accuracy, axis label, etc.), and manually wrote a prompt per output. 90 capsules, 181 task questions, 1–8 questions per capsule. Figures/tables referenced three ways: (1) by the metric measured ("From the figure measuring average RTT without ISL, report the x-axis label"), (2) by title, (3) by figure number from filenames/PDF/HTML ("From Figure 3 panel A, report the label of the green line").
- **A.4 Breakdown (Tables A1, A2):** capsules by modality — Medical: 16 vision-only / 5 language-only / 4 both (25); Social: 19/6/3 (28); CS: 9/25/4 (37); totals 44 vision-only / 36 language-only / 11 both. Train/test by discipline: Medical 12/13, Social 14/14, CS 19/18 (45/45). Availability constraint: CodeOcean holds 1,259 CS, 270 social science, and 128 medical Python/R capsules, so CS is overrepresented. Vision-based and language-based *question* counts are similar overall.

### Appendix B: Harness Details
Azure VMs: Standard_E2as_v5 (non-GPU) and Standard_NC4as_T4_v3 (GPU capsules); Ubuntu Linux, 80 GB disk. VM deleted only after agent writes `task_completed.log`. `--resume` flag for Azure failures. Warning that manual VM deletion must remove all associated resources (network interface, public IP, disk, virtual network).

### Appendix C: Experimental Details
- **C.1 Train set accuracy (Fig A1):** same ordering as test — CORE-Agent > AutoGPT, GPT-4o > GPT-4o-mini.
- **C.2 Confidence intervals (Table A3; n=3 trials, 95% CI, test set):**
  - CORE-Agent + GPT-4o: Easy 60.60%±4.51%, Medium 57.78%±4.51%, Hard 21.48%±2.60%; cost $0.6407±$0.1886, $1.2005±$0.3223, $2.9643±$0.0888.
  - CORE-Agent + GPT-4o-mini: Easy 44.44%±13.52%, Medium 32.59%±11.34%, Hard 16.30%±2.60%; cost $0.0445±$0.1083, $0.3893±$0.3891, $0.7315±$0.1871.
  - "The accuracy of the top-performing agent had a CI of under 5 percentage points on all difficulty levels." GPT-4o-mini has wider CIs — "a less reliable model to use."
- **C.3 pass@k (test set, Hard):** GPT-4o pass@1 22.2% → pass@3 31.1%; mini pass@1 15.6% → pass@3 26.7%. Rerunning alone improves performance; cites retry/temperature results (Kapoor et al. 2024; Hassid et al. 2024; Brown et al. 2024 Large Language Monkeys; AlphaCode).
- **C.4 pass∧k (all k trials succeed; from tau-bench):** GPT-4o Hard pass∧1 22.22% → pass∧3 8.89%; mini pass∧1 15.56% → pass∧3 6.67%. pass∧k line identical on Easy and Medium for GPT-4o (Fig A3). Interpretation: stochasticity means agents do not consistently solve the same tasks; reliability is its own challenge.
- Note a minor internal inconsistency: Table 5 lists Easy GPT-4o as 60.00% while §4.2 and Table A3 give 60.60%.

### Appendix D: Agent Details
- **D.1 AutoGPT bug fixes (applied to both agents, not counted as task-specific):** (1) truncate over-long tool outputs (keep beginning and end) instead of erroring; (2) set `shell=True` in subprocess so chained commands (`&&`) work.
- **D.2 CORE-Agent prompts:** full `--ai-role`, `--best-practice`, `--constraint` argument text for each level, reproduced verbatim. Notable lines: "If you are unsure of what to do, make your best guess."; "There is no task that you cannot do, so you should not refuse a request by saying you cannot do it"; the 5-most-relevant-files VLM procedure; Hard adds dependency-planning practice, `open_folder` instead of `cd`, and "NEVER use execute_python_file()". Also key/value hygiene checks for report.json. (Contains typos like "figuclearres" in the shipped prompts.)
- **D.3 Trajectory examples:**
  - **D.3.1 (Easy, wrong figure):** capsule-4299879 — correct answer in Figure_A17.pdf, agent only queried Figure_2/Figure_3; hit an unsupported-image 400 error, converted PDFs to PNG with pdftoppm, then extracted a p-value from the wrong figure and reported "> 0.05".
  - **D.3.2 (Medium, ignoring Docker):** capsule-8234136, GPT-4o-mini manually pip-installed (numpy metadata failures, FreeType, joblib...) instead of following REPRODUCING.md's Docker path; by Steps 65–68 it was reopening `grapher.py` in a loop until hitting the context limit. More persistent on weaker models.
  - **D.3.3 (Hard, dependency versions):** capsule-8807709 — installed network-diffusion 0.14.4 but `MultiSpreading` only exists in version 0.6; agent web-searched, grep'd site-packages, never found the right version within the cost cap. "This example shows how reproducing a paper can be a difficult task, even for a human."
  - **D.3.4 (Hard, looking up the capsule online):** same capsule — agent web-searched the CodeOcean capsule page repeatedly (Steps 62–68), fabricated a requirements.txt pointing at a GitHub master zip, then searched "CodeOcean account creation guide" — stopped only by CodeOcean's JavaScript requirement.

### Appendix E: Reproducibility Study Details
Methodology for Table 1 numbers: some papers report percentages (converted and rounded: Stockemer, Gertler, Collberg & Proebsting, Hardwicke 2021, Raff); some report per-result rather than per-paper counts (Gilbert, Trisovic, Samuel & Mietchen, Pérignon, Belz); McCullough reports approximate (>150 papers, <15 replicated). Their own ML Reproducibility Challenge 2022 analysis: 44 submissions, 28 attempted papers with fully available data+code, 10 of 28 only partially reproduced. Definition: fully reproduced if all main claims hold even with slight quantitative deviation (Livernoche & Sujaya 2023 counted as success; Brivio & Çöltekin 2023 counted as failure because the top accuracy deviated significantly despite the hypothesis holding). Many "fully reproduced" codebases still needed modifications (errors, outdated packages, limited documentation).

## Benchmark anatomy

- **N items:** 270 tasks = 90 papers x 3 difficulty levels; 181 unique task questions (1–8 per paper) shared across levels; 45 train / 45 test papers. Per-level test n = 45 tasks.
- **Construction:** filter 5,090 CodeOcean capsules by discipline (CS/social/medical), language (Python/R), and 10 explicit criteria (README present, <45 min runtime, simple run command, labeled outputs, low output variance, <10 GB, locally reproducible) down to 90. Authors manually wrote questions about outputs of verified successful runs.
- **Who authored items:** the five authors (manual authoring of prompts and answers); no external annotators, no inter-annotator agreement reported.
- **Validation/review:** every capsule manually reproduced **3 times**; answers verified stable; capsules with high-variance outputs rejected (example shown in Listings 2–3). No third-party review.
- **Human baseline:** none in the skilled-performance sense. Ground truth is defined by the authors' three manual reproductions; the low-variance criterion "ensures that all included capsules were verifiable and reproducible by a human," but no human time/accuracy baseline is measured or reported.
- **Contamination defenses:** tasks derive from public CodeOcean capsules (so raw materials are potentially in training data); the stated defense is that the public-repository foundation "enables periodic updates of the benchmark tasks, which could mitigate concerns about contamination and saturation" — a refresh capability, not a deployed mechanism. Harness updated to block the CodeOcean.com domain after an agent tried to look up its capsule online (an anti-cheating patch discovered reactively).
- **Scoring:** deterministic, non-compensatory. Agent writes `report.json` with prescribed keys; task correct iff **all** questions correct; numeric answers must fall within a 95% prediction interval computed from the three manual runs (only 17/181 questions are stochastic; the rest are exact). At least one non-guessable open-ended numeric question per task.
- **Judge design:** no LLM judge. Programmatic key/value comparison. (The *agents* use a VLM tool for figures, but evaluation itself is deterministic.)
- **Statistical reporting:** 95% CIs over n=3 repeat runs for CORE-Agent (Table A3); AutoGPT run once (cost). Figure 8 uses one-standard-deviation error bars over three trials. pass@k and pass∧k reported for k=1..3. No significance tests, no clustered/paper-level standard errors, no power analysis.

## Reported results (with uncertainty where given)

- CORE-Agent + GPT-4o (test, mean of 3 runs): Easy 60.00% (Table 5) / 60.60%±4.51% (Table A3); Medium 57.78%±4.51%; Hard 21.48%±2.60%.
- CORE-Agent + GPT-4o-mini: Easy 44.44%±13.52%; Medium 32.59%±11.34%; Hard 16.30%±2.60%.
- AutoGPT (single run): GPT-4o 35.56 / 37.78 / 6.67%; GPT-4o-mini 8.89 / 2.22 / 2.22%.
- Costs per task (CORE-Agent, 95% CI): GPT-4o $0.6407±$0.1886 (Easy), $1.2005±$0.3223 (Medium), $2.9643±$0.0888 (Hard); mini $0.0445±$0.1083, $0.3893±$0.3891, $0.7315±$0.1871.
- Task-specific adaptation effect (Easy): GPT-4o 35.6% → 60.60%; mini 8.9% → 44.44%. Adaptation cost: "only a few days of work."
- Cost-cap ablation (train, Hard): $4→$10 cap: GPT-4o 26%→31%; mini unchanged; mini superior below ~$2.50 caps. Successful tasks average $0.54 vs $2.59 for failures (GPT-4o CORE-Agent).
- Modality gap (Easy, test): GPT-4o 87.88% written vs 59.26% vision; mini 81.81% written vs 37.78% vision.
- pass@k (test, Hard): GPT-4o 22.2%→31.1% (k=1→3); mini 15.6%→26.7%.
- pass∧k (test, Hard): GPT-4o 22.22%→8.89%; mini 15.56%→6.67%.
- Sequential evaluation >20 days vs ~2 hours on the parallel harness; per-task limit 2 hours; $4 API cap.
- Motivating surveys: 2022 MLRC 18/28 fully reproducible; Table 1 rows as listed above.

## Limitations

**Admitted by the authors:**
- Selection criteria make the benchmark an easier, cleaner subset than real-world reproduction ("Not all papers in the real world meet these criteria"), justified as attainability + construct-validity tradeoff, analogous to SWE-bench Verified.
- Only reproducible papers included; the benchmark checks code-result reproduction, not paper-claim correctness.
- AutoGPT run only once due to cost constraints (so no CI on AutoGPT numbers).
- $4 cost cap could bind, though the $10 ablation shows modest effect (26→31% for GPT-4o).
- Contamination/saturation acknowledged as a concern, addressed only by the *possibility* of periodic updates.
- Agent-safety gaps: the harness had to be patched post hoc to block CodeOcean.com; no general guardrails exist.
- Reliability problem: agents do not consistently solve the same tasks (pass∧3 collapse).

**Not admitted (my observations):**
- n=3 repeats is a very thin basis for 95% CIs (the ±13.52pp mini CI shows run variance is large relative to the CI machinery); the CI method for n=3 is unstated (presumably t-based).
- Per-level test set is only 45 tasks; differences like 21.48% vs 16.30% (Hard, GPT-4o vs mini) are ~2 tasks and are never significance-tested. Questions cluster within capsules and levels share the same questions, but no clustering or paired analysis is done.
- Ground truth authored and verified by the same small team; no inter-rater or external audit of the 181 questions; wrong-figure answers that happen to match (e.g., "> 0.05" style answers) could score correct despite wrong process — the scoring checks values only, not provenance.
- A 95% prediction interval computed from three observations is extremely wide/fragile for the 17 stochastic questions.
- The full test set, including answers, is public on GitHub; "periodic updates" had not happened as of this version, so contamination for post-2024 models is plausible.
- Only OpenAI models and a single agent lineage (AutoGPT derivatives) evaluated; no Claude/Gemini/open-weight baselines, so "best agent 21%" may reflect scaffold choice as much as model frontier.
- Minor internal inconsistency (60.00% vs 60.60% for Easy GPT-4o) suggests light editorial QA on numbers.
- Azure-specific harness (cost, account requirements) is a practical barrier to independent reruns; the paper itself notes billing/cleanup footguns.
- Discipline confound acknowledged only in passing: CS skews Python, so discipline and language effects (Figure 8) are not separable.

## Implications for CRUCIBLE-CHAIN

1. **Scale for significance: independent clusters matter more than raw item count.** CORE-Bench's headline comparison rests on 45 test papers per level and n=3 repeat runs, yielding ±2.6 to ±13.5pp CIs — barely enough to separate 21% from 16%. CRUCIBLE-CHAIN's 8 templates x ~18 instances gives 144 items but only 8 independent clusters; instances within a template are correlated, so the effective n for template-level failure modes is 8, far below CORE's already-thin 45. To claim "single-digit frontier pass rates" with a CI that excludes, say, 15%, plan for on the order of 40–90 independent templates (CORE's paper count), treat template as the clustering unit for standard errors, and run >=3 repeats per model to separate stochastic variance from capability, as Table A3 does.

2. **Adopt CORE's guess-proofing rule verbatim: every chain needs at least one open-ended numeric stage.** CORE-Bench states each task has "at least one question that cannot be solved by guessing (e.g. a question with an open-ended numerical answer)" and requires all questions correct. CRUCIBLE-CHAIN's saturation came partly from leaked answer menus — a menu converts an open-ended stage into a multiple-choice one. Require that the final stage (and ideally each stage) demands a generator-computed numeric value with no enumerable answer space, and audit every prompt for anything that shrinks the answer space to a pickable list.

3. **Difficulty is an information-provisioning dial — run the headline condition at the "README-only" rung.** The same 181 questions score 60% when the output is handed over, 58% with a Dockerfile, and 21% with only a README. CRUCIBLE-CHAIN's 94–100% saturation is diagnostic of running at the Easy rung: prompts leaked "method recipes," which is exactly CORE's Dockerfile/output provisioning. Strip procedural scaffolding from the headline condition (state the goal and the data, not the pipeline), and keep the scaffolded variants as a diagnostic ladder like CORE's Easy/Medium — useful for localizing failure, never for the headline number.

4. **Treat prompt hints as a measured contaminant: a few days of hint-writing moved scores 4-5x.** CORE-Agent's per-level prompt hints (Table 4/D.2) took "only a few days of work" and lifted GPT-4o-mini from 8.9% to 44.44% on Easy and AutoGPT+GPT-4o from 6.7% to 21.5% on Hard. That is the empirical size of the effect CRUCIBLE-CHAIN experienced when its own prompts leaked recipes. Institutionalize a "hint audit": any text in the task prompt that names a method, tool, ordering, or answer format is a lever worth tens of points; quantify it by running clean vs. hinted prompt variants the way CORE contrasts AutoGPT vs CORE-Agent.

5. **Report pass@k AND pass∧k with >=3 repeats; near-saturation and near-zero regimes both demand it.** CORE's Hard results move from 22.2% (pass@1) to 31.1% (pass@3) but collapse to 8.89% (pass∧3) — stochasticity, not stable capability, produces a big share of passes. At CRUCIBLE-CHAIN's target of single-digit pass rates, a model that passes 6% of chains once may pass ~0% consistently (pass∧3), and that distinction is the difference between "emerging capability" and "lottery tickets." Conversely, the current 94-100% saturation should be re-examined under pass∧k — if it drops, the saturation is partly noise. Budget repeats into the campaign design (CORE ran the full benchmark 3x for the CI table).

6. **Exploit the constructed-truth advantage CORE lacks: regenerate instead of "periodically update."** CORE's contamination story is a promise ("enables periodic updates... could mitigate concerns") because its tasks are frozen public artifacts with public answers on GitHub. CRUCIBLE-CHAIN's deterministic generator can mint fresh instances per evaluation run. Operationalize it: never publish concrete test instances, publish the generator plus a commitment hash; rotate seeds per model release; keep a sealed template holdout the way CORE holds out 45 test papers after developing only on train.

7. **Define an explicit tolerance policy per stage, as CORE does with prediction intervals.** CORE marks answers correct within a 95% prediction interval from three reference runs, and flags that only 17/181 questions are stochastic. CRUCIBLE-CHAIN's generator gives exact labels, but model answers legitimately vary in rounding, units, and float path. Publish a per-stage tolerance spec (exact match, relative epsilon, or interval) and a count of which stages use which — otherwise near-miss adjudication becomes an invisible judge. Also note CORE's blind spot: value-only matching lets a wrong-provenance answer (right number from the wrong figure) score correct; CRUCIBLE-CHAIN's chained non-compensatory design mitigates this only if intermediate stages are actually scored, so score all stages, not just the final value.

8. **Instrument cost and cap it; failures are where budget dies.** CORE reports average cost as a first-class metric, caps at $4/task, and finds successes cost $0.54 vs $2.59 for failures — stuck loops (dependency retries, file-reopen loops in D.3.2) burn the budget. At single-digit pass rates, ~90%+ of CRUCIBLE-CHAIN spend will be on failures; set per-chain cost/step caps, log cost per condition (clean/planted-defect/flawed-premise), and run a cap-sensitivity ablation like CORE's $4 vs $10 to prove the cap isn't binding on the headline number.

9. **Anti-lookup defenses must be designed in, not patched in.** CORE discovered mid-evaluation that an agent was searching CodeOcean for its own capsule (D.3.4) and only then blocked the domain; the agent even fabricated a plausible requirements.txt from a web zip. CRUCIBLE-CHAIN's constructed tasks have no true external answer source — an advantage — but flawed-premise conditions are vulnerable to the mirror failure: prompts like CORE's shipped constraint "There is no task that you cannot do, so you should not refuse a request by saying you cannot do it" show how scaffold text can make correct refusal impossible. Ensure the harness neither forbids refusal nor telegraphs it, and network-isolate runs so models cannot search for template descriptions if any are ever published.

10. **Keep benchmark construction cheaper than benchmark solving, and reject high-variance items with evidence.** CORE's stated design principle — construction "much easier than solving" — was achieved by building on pre-verified capsules and documenting rejections (capsule 826891's spike probability swung 0.423→0.783 across runs, so it was cut). CRUCIBLE-CHAIN's generator already satisfies the cost principle; copy the rejection discipline: for each template, run the generator's reference pipeline multiple times (or across environments), and drop or interval-ize any stage whose ground truth is environment-sensitive, keeping an audit trail of rejected instances like CORE's Listings 2–3.

## Verbatim quotes

1. Section 2.1 (Benchmark Construction): "The key problem is that we want the tasks in the benchmark to be realistically difficult, but we need the construction of the benchmark itself to be much easier than solving the benchmark."
2. Section 2.1 (Benchmark Construction): "We ensure each task has at least one question that cannot be solved by guessing (e.g. a question with an open-ended numerical answer), and a task is marked as correct only ifallof the task questions are answered correctly, which ensures all tasks cannot be solved by guessing." [extraction ligature: "ifallof" = "if all of"]
3. Figure 4 caption (Section 2.2): "We determine if an agent correctly solves a task if the agent's reported results for all questions fall within a 95% prediction interval for every task question of the results from the three manual runs (although only 17 / 181 task questions have stochastic answers)."
4. Section 4 (Results): "Overall, CORE-Agent with GPT-4o is the top performing agent on all three levels of the benchmark, solving 60.00% of tasks onCORE-Bench-Easy, 57.78% onCORE-Bench-Medium, but only 21.48% onCORE-Bench-Hard." [extraction runs benchmark names into preceding words]
5. Section 1 (Introduction, contribution 1): "CORE-Bench's foundation in public repositories enables periodic updates of the benchmark tasks, which could mitigate concerns about contamination and saturation." [PDF renders the apostrophe as a right single quote]
6. Appendix C.2 (Confidence Intervals on Test Set): "The accuracy of the top-performing agent had a CI of under 5 percentage points on all difficulty levels."
7. Appendix C.4 (pass∧k): "The results suggests that the underlying stochasticity of the agent caused it to not consistently solve the same tasks." [sic — "suggests"]
8. Section 4.3: "the average cost of successful tasks forCORE-Agent and GPT-4o was $0.54, compared to $2.59 for failed tasks"
9. Table 2 caption context (Section 2): "Not all papers in the real world meet these criteria; however the criteria improve task clarity and therefore ensure a high accuracy on the benchmark is attainable given the current state of agent development."
10. Appendix D.2 (CORE-Agent prompts, constraint shipped at every level): "There is no task that you cannot do, so you should not refuse a request by saying you cannot do it"
