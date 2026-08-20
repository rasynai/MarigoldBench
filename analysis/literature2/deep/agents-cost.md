# Deep read: "AI Agents That Matter" (arXiv 2407.01502) — slug `agents-cost`

## Coverage ledger

| Item | Value |
|---|---|
| PDF | `A:/PERTURB-Bench/analysis/literature2/pdfs/2407.01502.pdf` (1,235,369 bytes, `%PDF-1.5`) |
| Extracted text | `A:/PERTURB-Bench/analysis/literature2/md/2407.01502.md` |
| Pages | 33 |
| Total chars | 115,853 |
| Total lines | 1,438 |
| Chars read | 115,853 (100%) |
| Chunk ranges read (Read tool) | L1–60; L60–659; L660–1259; L1260–1438 |
| Notes | No ar5iv fallback needed (extraction >> 15,000 chars). Whole body + all appendices (A–I) + checklist read. Table A4 (17-benchmark survey) and Table A6/A7 (reproducibility) extract as dense run-together text but are legible. |

## Actual paper identity (as printed on page 1)

- **Title:** AI Agents That Matter
- **Authors:** Sayash Kapoor\*, Benedikt Stroebl\*, Zachary S. Siegel, Nitya Nadgir, Arvind Narayanan (\*equal contribution)
- **Affiliation:** Princeton University
- **Date / venue:** July 2, 2024; arXiv:2407.01502v1 [cs.LG], 1 Jul 2024. Formatted with a NeurIPS-style checklist (Appendix, "Checklist"), not a printed venue. Contact: {sayashk,stroebl}@princeton.edu.
- **Title matches the assigned title.** This is a position + empirical-reproduction paper about agent *evaluation methodology*, not a benchmark release and not a tool.

## Section-by-section notes with numbers

### 1. Introduction (L24–66)
Five contributions: (1) evaluations must be cost-controlled; (2) joint accuracy/cost optimization is a new design axis; (3) model-developer vs downstream-developer evaluation needs differ; (4) agent benchmarks enable shortcuts (holdout taxonomy); (5) evaluations lack standardization/reproducibility. Framing: "agents can cost much more than a single model call. For example, the authors of SWE-Agent capped each run of the agent at $4 USD, which translates to hundreds of thousands of language model tokens."

### 1.1 What is an agent (L67–86)
Refuses a new definition; identifies three clusters that make a system more *agentic*: (a) environment/goal complexity (multi-task, multi-stakeholder, long horizon, unexpected changes; pursuing goals without being told how); (b) UI/supervision (natural-language instruction, autonomy, less user supervision); (c) system design (tool use, planning/reflection/subgoal decomposition, LLM-driven dynamic control flow). MarigoldBench sits high on all three clusters.

### 2. Evaluations must be cost-controlled (L87–167)
- Repeated sampling raises accuracy without bound when the environment supplies a cheap correctness signal. AlphaCode: ~0% zero-shot → >15% with 1,000 retries → >30% with 1,000,000 retries (top-10 measure).
- Three agents re-evaluated from the HumanEval PapersWithCode leaderboard with public code: LDB, LATS, Reflexion. AgentCoder excluded (no code link as of late April 2024).
- Four new baselines: zero-shot GPT-3.5/GPT-4; **Retry** (temp 0, up to 5 attempts, gated on the *example* tests in the problem); **Warming** (same, temperature ramped 0 → 0.3 → 0.5); **Escalation** (Llama-3-8B → GPT-3.5 → Llama-3-70B → GPT-4 on test failure).
- Uses the LDB-modified HumanEval so all 164 tasks have example tests (original has them for only 161/164).
- Each agent run **5 times**; Pareto frontier constrained convex (mixtures of two agents are achievable, so zero-shot GPT-4 is *not* on the frontier).
- Headline results (Table A1, April 2024 models; mean, [min–max]): Warming (GPT-4) **93.2% / $2.45**; LDB (GPT-4) 93.3% / $6.36; LDB (Reflexion, GPT-4) 92.9% / $7.26; Retry (GPT-4) 92.0% / $2.51; LDB (GPT-4, GPT-3.5) 91.0% / $2.19; GPT-4 zero-shot 89.6% / $1.93; Reflexion (GPT-4) 87.8% / $3.90; **LATS (GPT-4) 88.0% / $134.50**; Escalation **85.0% / $0.27**; GPT-3.5 zero-shot 73.9% / $0.05.
- Interpretation: no significant accuracy gap between Warming and the best agent architecture; costs differ by ~2 orders of magnitude at substantially similar accuracy; LATS costs >50× Warming; Escalation beats LDB (GPT-3.5) on accuracy at <half the cost. "Lack of evidence that System 2 approaches are responsible for performance gains."
- Prices used: GPT-3.5 $0.5/$1.5 per 1M in/out; GPT-4-turbo $10/$30 per 1M (April 2024). Models: `gpt-3.5-turbo-0125`, `gpt-4-turbo-2024-04-09`.
- Robustness check with June 2023 models (Table A2) reproduces the pattern: Warming (GPT-4) 90.6% / $3.88 vs LATS (GPT-4) 83.5% / **$360.02**. One LATS (GPT-3.5) task (HumanEval/83) was killed after 5 hours and scored incorrect; some tasks took >2 hours.
- 95% CIs computed with Student's t over the 5 runs (Fig. A1, A5).

### 3. Joint cost/accuracy optimization (L168–244, Appendix B)
- DSPy + Optuna multi-objective search over (a) per-module temperature ∈ {0.0,0.2,0.4,0.6}, (b) number of few-shot examples (max 8), (c) which examples, (d) whether to include formatting instructions. 16 Optuna trials; 16 candidate programs for DSPy random search.
- HotPotQA multi-hop QA (simplified Baleen), ColBERTv2 over a 2017 Wikipedia dump; 2 hops, top-2 passages. **Metric = whether all ground-truth documents were retrieved** (a recomputed, artifact-level check, not answer self-report).
- 100 training samples (50 bootstrap / 50 validation), 200 evaluation samples, fixed seed, 5 runs.
- Results (Table A3): GPT-3.5 joint optimization 0.509 acc / $0.174 variable vs DSPy few-shot 0.47 / $0.384 and random search 0.495 / $0.376 → **53% lower variable cost**. Llama-3-70B joint 0.601 / $0.374 vs few-shot 0.622 / $0.661 → **41% lower**. Fixed (optimization) costs: $2.71 (GPT-3.5 joint), $3.84 (Llama joint), $4.82 (Llama random search), $0.028–0.029 (few-shot).
- Fixed vs variable crossover: joint optimization becomes cheaper in total after **~1,350 tasks** (precisely 1,332 for Llama-3-70B, 1,275 for GPT-3.5; Fig. A6).

### 4. Model vs downstream evaluation (L245–314, Appendix D)
- Model evaluation = scientific question; controlling compute/parameters is right, dollar costs break comparability over time. Downstream evaluation = procurement question; **dollar cost is the construct of interest**.
- Proxies mislead: Mixtral 8x22B marketing used *active parameters*; as of June 2024 Mixtral 8x7B cost twice as much as Llama 2 13B on Anyscale while looking equal on the active-parameter axis.
- Prescription: downstream evaluations must report **input/output token counts alongside dollar costs** so costs can be recomputed at current prices; they prototype an interactive web app for this.
- NovelQA case study: novels 50k–1M+ words, 5–100 questions each, 88 novels, ~2,300 questions, submission via CodaBench. Because NovelQA asks all questions about a novel in one prompt, it makes RAG look bad. Their measurement (Table A5): RAG **67.89% at $52.80** vs long-context **67.81% at $99.80**; realistic per-question usage gives a **cost ratio ≈ 21.86×** in RAG's favor, but the NovelQA protocol shows only ~2× — "a tenfold overestimate" of RAG's cost. NovelQA paper reported 71% for GPT-4; the gap is attributed to stochasticity; run **only once** due to cost. Sequential querying of long-context would cost ~$2,590.

### 5. Agent benchmarks allow shortcuts (L315–430)
- Overfitting is worse than LLM contamination because "knowledge of test samples can be directly programmed into the agent." Benchmarks are small (a few hundred samples); "a lookup table can achieve 100% accuracy on many agent benchmarks."
- Four generality levels and the matching holdout (Table 1): distribution-specific → in-distribution samples (**1/1** adequate); task-specific → out-of-distribution samples (**3/6**); domain-general → held-out *tasks* (**1/8**); fully general → held-out *domains* (**0/2**).
- 17-benchmark survey (Table A4): **7/17 have no holdout and no stated plan**; of the 10 with holdouts only **5** are at the appropriate generality level. A holdout counts as "appropriate" if it exists *or* the designers state intent to build one — a generous criterion.
- Responsibility is assigned to *benchmark* developers: "designing benchmarks that don't allow shortcuts is much easier than checking every single agent to see if it takes shortcuts."
- Alternative when holdouts are impractical: sim2real transfer testing (e.g., WebShop agents tested on amazon.com).
- **WebArena case study (5.1):** 812 tasks, clones of 6 sites (GitLab, Reddit, Wikipedia, OpenStreetMaps, e-commerce, CMS) plus calculator and scratchpad. Top agent STeP: **35.8%**, >2× the paper's best baseline and >10 points above the next agent. STeP achieves this by hardcoding policies — e.g., the profile-navigation policy is literally "look at the current base URL and add a suffix '/user/user_name'". Brittle under drift; failure probability compounds because an agent may invoke dozens of policies per task. WebArena models no drift and has no held-out task set; with unseen websites, "the accuracy [of] agents like STeP would be drastically lower."
- **Human-in-the-loop (5.2):** current evals sit at two extremes (pure QA chatbots vs fully unsupervised agents). Shi et al.: simple human feedback took GPT-4 from **0% to over 86%** on olympiad programming. So no-human evaluation *underestimates* usefulness, while missing holdouts *overestimate* capability.

### 6. Standardization / reproducibility (L459–535, Appendix E)
Five root causes, all assigned to benchmark developers:
1. Evaluation scripts assume an agent design; developers reimplement them → incomparable results.
2. Repurposing LLM benchmarks for agents injects inconsistency: HumanEval lacks example tests for 3/164 tasks and embeds tests in docstrings rather than machine-readable form. Reflexion and LATS *deleted* those tasks; LDB *added* tests. Yet all appear on one PapersWithCode leaderboard.
3. Cost makes CIs infeasible: SWE-bench has 2,000+ tasks at a $4/task cap → **>$8,000 per single evaluation run**; hence no error bars. "Many reported accuracy scores were above the maximum of five runs that we performed."
4. Environment interaction causes subtle errors: WebArena's Reddit clone rate-limits posting, so **task order matters** — the independence assumption fails. Affected 2/129 Reddit tasks for the WebArena baseline and **30/129 for STeP**.
5. Bugs: "both LATS and STeP marked some incorrectly completed tasks as correct." LATS dropped 1 task, STeP dropped 8.
Reported vs reproduced (Table A7, 5 runs, all 164 tasks): LATS (GPT-4) 94.4 → **88.0**; LATS (GPT-3.5) 83.8 → 80.4; LDB (Reflexion, GPT-3.5) 95.1 → 88.9; Reflexion (GPT-4) 91.0 → 87.8; LDB (GPT-3.5) 82.9 → 80.2; LDB (GPT-4, GPT-3.5) 89.6 → 91.0; **GPT-4 baseline reported as 75.0 → reproduced 89.6** (baseline underreported by ~15 points). LATS scored generated code against only a *subset* of the hidden test cases, worth **~3 percentage points** of inflation. LDB claimed GPT-3.5 Reflexion generations but the artifacts they used were GPT-4-generated. WebArena's Reddit autologin had an unimplemented TODO causing **silent failures**. Listing 2 shows a STeP log where the agent correctly stops because of the rate limit and the harness still records `"reward": 1.0, "success": 1.0`.

### Appendices
- A: implementation details for every baseline and agent (LDB max 10 iterations temp 0; LATS 8 iterations, expansion 3, temp 0.8 gen / 0.2 reflection, 6 internal tests GPT-3.5 / 4 GPT-4 — a difference *not in the paper*, learned by emailing the authors; Reflexion 2 iterations, expansion 3, temp 0). Pareto frontier definition + colab implementation.
- B: HotPotQA implementation, Optuna setup, fixed/variable crossover.
- C: the 17-benchmark survey rationale (sourced from AgentBench, AgentBoard, OpenDevin, ICLR 2024 LLM-agents workshop).
- D: NovelQA RAG setup (`text-embedding-3-large`, 10 chunks × 1000 chars), prompt in Listing 1, cost table A5.
- E: per-agent reproduction issues (Tables A6/A7).
- F: no GPUs; all API endpoints (OpenAI, Azure OpenAI, Together.ai).
- G: limitations. H: societal impact — cost measurement helps safety evaluation by pricing dangerous capabilities. I: reproducibility statement (MIT-licensed repo `github.com/benediktstroebl/agent-evals`, web app, colab).

## Classification: this is a METHODOLOGY / CRITIQUE paper (with reproduction experiments)

It is not a benchmark release and not a tool. What it *does* provide:

**What it does.** Establishes four evaluation requirements: (i) report cost jointly with accuracy on a Pareto plot; (ii) separate model evaluation from downstream evaluation and use dollars (plus token counts) for the latter; (iii) match holdout type to the intended generality level; (iv) standardize scripts, run multiple seeds, and report error bars.

**Measured accuracy / failure rate of the *evaluation practices* it audits.**
- 4 of 7 reproduced HumanEval numbers were *lower* than reported; 1 baseline was underreported by 14.6 points.
- 2 of 5 audited agent/benchmark implementations marked failed tasks as successful.
- 7/17 surveyed benchmarks have no holdout; 12/17 lack an adequate one.
- One environment-side bug (rate limiting) corrupted 30/129 tasks in a leaderboard-topping submission.

**Known failure modes it names.** Retry-until-pass inflation; hardcoded task-specific policies; leaderboard mixing of differently-modified benchmark variants; task-order dependence via stateful environments; partial test-case grading; silent environment failures scored as success; single-run point estimates; cost proxies substituting for dollars.

**What a naive user gets wrong.** Believing "System 2" scaffolding (reflection/debugging/tree search) is what produces the gain, when temperature-ramped retry matches it at 1/50 the cost; reading a leaderboard as a downstream procurement signal; assuming benchmark tasks are independent; trusting a harness's own success flag.

**Inputs needed / what it returns.** For a defensible agent evaluation: ≥5 runs per configuration, per-run token counts (in/out) and dollar cost, an unmodified task list with documented exclusions, an evaluation script owned by the benchmark, a holdout at the declared generality level, and Student-t CIs. It returns a Pareto frontier (convex hull) over (cost, accuracy) rather than a single leaderboard rank.

**Cost per run (as measured here).** HumanEval 164 tasks: $0.05 (GPT-3.5 zero-shot) to $360 (LATS GPT-4, June-2023 models). HotPotQA variable cost per 100 inferences: $0.071–$0.661; fixed optimization cost $0.03–$4.82. NovelQA single pass: $52.80 (RAG) / $99.80 (long context). SWE-bench full run at SWE-Agent's cap: >$8,000.

## Limitations admitted

- Cost models and prices change; mitigated by publishing a recalculation web app (Appendix G).
- Not exhaustive over task environments or agent variants (G).
- Other cost types — environmental impact, annotation labor, maintenance — are not analyzed (G).
- NovelQA evaluated only once, no error bars, due to cost (Checklist 3c, Appendix D).
- Error bars on HotPotQA capture in-sample test variance only, not variability from optimization/resampling (Fig. A5 caption).
- They guessed at each surveyed benchmark's intended generality level (Table A4 caption).
- HumanEval System-2 conclusion may not transfer to harder tasks like SWE-bench (Section 2.3).

## Limitations *not* admitted

- n = 5 runs on 164 tasks is thin; several of their CIs overlap heavily, so "no significant difference between Warming and the best agent" is a failure to reject, not equivalence. No power analysis, no clustering of tasks, no correction for the many pairwise comparisons implicit in a Pareto plot.
- HumanEval is nearly saturated (86–93%), and the whole cost-vs-accuracy argument is derived from a saturated benchmark where retries have low marginal value; the *ordering* of scaffolds could differ where headroom is large.
- Their own Retry/Warming/Escalation baselines gate on the benchmark's example tests — itself a benchmark-supplied shortcut signal that would be unavailable in most real deployments. They critique shortcut-taking while their winning baseline is powered by a shortcut.
- Dollar cost is a moving, provider-specific quantity; the Pareto frontier they publish is not stable, and they do not quantify how much of the frontier reorders under plausible price moves.
- The convex-hull Pareto assumes agent mixtures are deployable, which is rarely true operationally.
- No treatment of *wall-clock / capacity* cost for non-API tools (GPU-hours for a docking or folding tool), which is the dominant cost in a scientific-tool setting.
- No discussion of how to score *refusal* or partial credit; success is binary throughout.

## Implications for MarigoldBench

1. **Make cost a first-class, reported axis, and cap it per episode.** MarigoldBench's tools (RFdiffusion, OpenFold2, Boltz-2, DiffDock) have real GPU/NIM cost, so the AlphaCode pathology is live: a model can brute-force ESMFold/Boltz-2 calls until a pLDDT or ipTM threshold is crossed. Publish per-episode dollar cost *and* per-tool call counts and token counts alongside VEC, and score on a convex (cost, VEC) Pareto frontier — not VEC alone. The 8–25 tool-call window is the right instrument; enforce it as a hard budget and report the cost distribution, because "accuracy alone cannot identify progress." Concretely: log `{tool, n_calls, gpu_seconds, input_tokens, output_tokens, usd}` per episode so any future reader can recompute cost at then-current prices, as the paper prescribes for downstream evaluation.

2. **Include the retry/warming/escalation baselines as first-class competitors, not afterthoughts.** Before claiming a frontier model or a scaffold "drives the lab," show that a dumb loop — resample the design, refold, keep the best score — does not match it inside the same budget. On HumanEval the dumb loop matched every published scaffold. In MarigoldBench the analogue is: sample N ProteinMPNN sequences, ESMFold all of them, submit argmax. If that hits the same VEC, the task is measuring sampling budget, not scientific competence. Design task families where the *checkable* quantity the model can locally optimize is deliberately *not* the quantity the harness recomputes (see #4).

3. **The recompute check must close the loop the agent cannot see.** The paper's cleanest positive example is HotPotQA scored by "whether all of the specified documents were retrieved" — an artifact-level recomputation. Its worst example is STeP's log recording `"success": 1.0` on a task the environment made impossible. For MarigoldBench: never accept a self-reported metric; re-derive it from the submitted artifact (re-run ESMFold on the *submitted* sequence, recompute RMSD/pLDDT/ipTM from the *submitted* PDB, recompute the QSAR AUC from the *submitted* split and model, re-run the docking pose scoring from the *submitted* ligand). Also verify artifact *provenance*: hash the artifact against the tool-call transcript so a hand-written PDB or a copied literature value cannot pass.

4. **A tool-use task is genuinely hard when the locally checkable signal and the true criterion diverge.** Every failure in this paper comes from a cheap proxy standing in for the real thing (example tests vs hidden tests, active parameters vs dollars, one-shot batched QA vs sequential queries). Build that gap in deliberately: the model can see pLDDT but is scored on a held-out Boltz-2 co-folding confidence; it can see training-set R² but is scored on a scaffold-split test set the harness holds; it can see DiffDock's confidence but is scored on pose plausibility recomputed with a different scorer plus a steric-clash check. This is the mechanism that puts the strongest frontier model in the 5–40% band without making tasks arbitrarily long.

5. **Plant exactly the defects this paper found in the wild — they are empirically real, not hypothetical.** Priority planted-defect list: (a) *partial-test grading* → a benchmark/eval script that scores only a subset of the held-out ligands or residues, inflating by ~3 points (LATS); (b) *silent environment failure* → a NIM endpoint that returns a default/empty result with HTTP 200 (WebArena autologin TODO), and check whether the model notices the artifact is degenerate; (c) *rate-limit / order dependence* → a tool that throttles after k calls and returns a stale cached result, testing whether the model detects that its "improvement" is an artifact of call order; (d) *silent model swap* → the config claims one checkpoint but the artifact came from another (LDB's GPT-3.5-vs-GPT-4 mixup); (e) *dropped samples* → an input file quietly missing N compounds/chains so the reported denominator is wrong (STeP's 8, LATS's 1, Reflexion's 3); (f) *leakage* → train/test split that shares scaffolds or homologous sequences.

6. **The flawed-premise condition maps directly onto their "shortcut" critique — refusal is the correct handling of a task whose measurement is invalid.** Their STeP log is the canonical case: the environment made the objective impossible, the agent correctly reasoned so, and the *harness* was wrong to score it 1.0. Mirror this: flawed-premise tasks should include ones where the requested check cannot be computed from the supplied data (a binding-affinity claim on a structure with no ligand pocket resolved; a statistical claim with n too small; a docking task against an apo structure with the relevant loop missing). Score "flags the premise and declines to submit a number" as the correct outcome, and score confident submission as a false alarm.

7. **Fix the holdout level to the generality you claim, and keep part of it secret.** MarigoldBench is domain-general (any task in computational drug discovery/ML), which by their Table 1 requires **held-out task families**, not held-out instances — the level at which only **1/8** surveyed benchmarks succeeded. With ≥100 task families, hold out entire families (and ideally entire tools/modalities) from any public release, and keep them unpublished to block both contamination and scaffold overfitting. Their point that a lookup table can max out a few-hundred-item agent benchmark applies directly: 100 families × 3 conditions is ~300 items, squarely in the memorizable regime.

8. **Budget for repeated runs and report clustered CIs — and expect published numbers to be optimistic.** They found reported scores above the max of 5 runs, and cost was the reason nobody ran more than once. Since MarigoldBench targets template-clustered CIs, pre-compute the per-episode dollar/GPU cost and size the campaign so ≥5 seeds per (model × task × condition) is affordable; if that is infeasible for the expensive folding tasks, stratify — many seeds on cheap families, fewer on expensive ones — and say so explicitly rather than quietly reporting single-run point estimates. Their Student-t-over-5-runs convention is a usable floor; template clustering is strictly better and should be stated as such.

9. **Own the evaluation script; do not let a model's scaffold do any part of the grading.** Root causes 1, 2 and 5 all trace to agent developers re-implementing evaluation. MarigoldBench should ship a frozen, versioned harness that ingests only the artifact + transcript, runs in its own container with pinned tool versions and pinned RDKit/PyTorch, and refuses any submission whose artifact does not parse. Publish the exact task list with a documented, machine-readable exclusion log so no future comparison is contaminated by silently different subsets.

10. **Add a stateful-environment audit before launching the campaign.** WebArena's rate limit broke task independence and corrupted 30/129 tasks for the leaderboard leader. NVIDIA NIM endpoints have quotas, cold starts, and version drift; GPU memory pressure across concurrent episodes is another shared-state channel. Run the same task family in shuffled orders and in isolation, and confirm VEC is invariant; log endpoint version/model hash per call so a mid-campaign upstream model update is detectable rather than silently reinterpreted as a capability change.

11. **Consider reporting a human-in-the-loop variant for at least a subset of families.** Shi et al.'s 0% → 86% jump under simple feedback is the paper's evidence that fully autonomous scoring understates real usefulness. A "one clarifying hint after the first failed check" condition would give MarigoldBench a second, more deployment-relevant number and would help distinguish "cannot do the science" from "made one recoverable slip in a 25-call chain."

## Verbatim quotes

1. Section 2.3 (summary paragraph): "To summarize this section, useful agent evaluations must control for cost — even if we ultimately don't care about cost and only about identifying innovative agent designs. Accuracy alone cannot identify progress because it can be improved by scientifically meaningless methods such as retrying."

2. Section 5 (Agent benchmarks allow shortcuts): "This is a much more serious problem than LLM training data contamination, as knowledge of test samples can be directly programmed into the agent as opposed to merely being exposed to them during training. In principle, a lookup table can achieve 100% accuracy on many agent benchmarks."

3. Section 5.1 (Case study of the STeP agent on WebArena): "It turns out that STeP hardcodes policies to solve the specific tasks included in WebArena. For example, several WebArena Reddit tasks involve navigating to a user's profile. The STeP policy for this task is to look at the current base URL and add a suffix '/user/user_name'."

4. Section 6, root cause 3: "The high cost makes it infeasible to run evaluations multiple times, and perhaps as a result, agent evaluations are rarely accompanied by error bars. This makes it hard to understand the variance of reported results. We found that many reported accuracy scores were above the maximum of five runs that we performed in our reproduction attempts, and the reported baselines were in some cases lower than the minimum of five runs we performed."

5. Section 6, root cause 5: "Perhaps due to the issues above, we encountered several bugs with agent developers' implementation of their agents and their evaluations. For example, both LATS [65] and STeP [47] marked some incorrectly completed tasks as correct."

6. Appendix E.1 (LATS): "In addition, their agent was evaluated on only a subset of the test cases provided in the HumanEval benchmark. This exaggerated their accuracy numbers, since the code for a particular HumanEval problem might be incorrect, but if it passes only a portion of the test cases for that problem, it could still be marked as correct. In our analysis, this was responsible for a 3% difference in accuracy (mean across five runs)."

7. Listing 2 caption (Appendix E): "Given the observation from the web environment, the agent correctly concludes that it's currently not possible to make a posting given the rate limit imposed on the user. Despite the environment imposing this limit, the task is still evaluated as successfully solved. This is an example of incorrectly evaluated agents leading to inflated results."

8. Section 5 (responsibility): "Benchmark developers must do their best to ensure that shortcuts are impossible. We view this as the responsibility of benchmark developers rather than agent developers, because designing benchmarks that don't allow shortcuts is much easier than checking every single agent to see if it takes shortcuts."
