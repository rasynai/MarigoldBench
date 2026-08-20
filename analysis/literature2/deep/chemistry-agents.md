# Deep read: `chemistry-agents` — ChemCrow

## 1. Coverage ledger

| Item | Value |
|---|---|
| Target file | `A:/PERTURB-Bench/analysis/literature2/md/2304.05376.md` |
| Source PDF | `A:/PERTURB-Bench/analysis/literature2/pdfs/2304.05376.pdf` (16,226,282 bytes, `%PDF-1.5`) |
| PDF pages | 38 |
| Extracted text chars (pypdf) | 88,344 |
| File size on disk | 90,017 bytes / 1,248 lines |
| **Chars paged through** | **90,017 (100%)** |

Chunk ranges read with the Read tool, in order:

| # | Lines | Content |
|---|---|---|
| 1 | 1–420 | Title/abstract, Intro, Results 2.1–2.3, Risk Mitigation, Conclusion, Methods 5.1–5.3.1 |
| 2 | 421–840 | Methods 5.3.2–5.3.4 (all tool specs), Data/Code, Acks, refs [1]–[108], App. A.1–A.3 |
| 3 | 841–1248 | App. A.3 cont., B (human eval), C (GPT-4 vs ChemCrow), D (safety), E (reproducibility), F (limitations), G.1–G.14 (14 tasks) |

**Verified: lines 1 → 1248 of 1248. No gaps.**

### Extraction caveat (material)
A `Grep` sweep for score-shaped tokens (`\d\.\d`, `%`, "grade", "out of 10") over the whole file returns **only** NMR shifts, m/z values, reagent volumes, and arXiv IDs. **Every quantitative evaluation result in this paper is rendered inside figure images (Fig. 4a–d, Fig. 9–22) and is not recoverable from the PDF text layer.** The main text and all 14 appendix-G subsections consist solely of figure *captions*. Consequently no per-task numeric score can be quoted from the file on disk. To avoid reporting a false coverage number I fetched the open-access published version (PMC11116106) purely to recover sample sizes; those are marked **[PMC]** below and are the only facts in this report not taken from the on-disk file.

### Paper-identity correction (Step 3 triggered)
The assigned ID **2310.03302 is the wrong paper.** It downloaded and extracted cleanly (39 pages, 113,277 chars → `md/2310.03302.md`) but line 1 reads *"MLAgentBench: Evaluating Language Agents on Machine Learning Experimentation"* (Huang, Vora, Liang, Leskovec — Stanford). I read lines 1–60 of that file to confirm, then used WebSearch to locate the correct ID for the ChemCrow topic: **arXiv 2304.05376**. Both files are retained on disk.

*(Aside worth flagging to the orchestrator: MLAgentBench is itself highly on-topic for MarigoldBench — 13 tasks, ReAct agent, Claude v3 Opus best at 37.5% average success rate, spanning 100% on old datasets to 0% on post-cutoff Kaggle challenges. That 0%-on-recent/100%-on-old split is a direct contamination measurement and the 37.5% sits right at the top of your 5–40% target band. It deserves its own slot in the literature queue.)*

---

## 2. Actual paper identity (as printed)

- **Title:** "Augmenting large language models with chemistry tools" (line 1). Note: the string "ChemCrow" appears in the arXiv listing title but **not** in the printed paper title.
- **Authors:** Andres M. Bran^1,2*, Sam Cox^3*, Oliver Schilter^2,4, Carlo Baldassari^4, Andrew D. White^3, Philippe Schwaller^1,2. (* contributed equally)
- **Affiliations:** LIAC/ISIC EPFL; NCCR Catalysis EPFL; Dept. of Chemical Engineering, University of Rochester; Accelerated Discovery, IBM Research – Europe.
- **Venue as printed:** "Preprint. Under review." — `arXiv:2304.05376v5 [physics.chem-ph] 2 Oct 2023` (line 47). Subsequently published as *Nature Machine Intelligence* (2024), s42256-024-00832-8.
- **Code:** `github.com/ur-whitelab/chemcrow-public` (12 of 18 tools); runs at `github.com/ur-whitelab/chemcrow-runs`.

**Classification: this is a METHOD/TOOL paper with a small bespoke evaluation attached — it is NOT a benchmark.** There is no held-out set, no automated scorer, no leaderboard, and no reusable task specification. I report it under both headings below because the *evaluation's failure* is the most valuable content for MarigoldBench.

---

## 3. Section-by-section notes with numbers

### Abstract + §1 Introduction (lines 11–101)
- **18 expert-designed tools**, LLM = **GPT-4 at temperature 0.1** (§5.1, line 366), orchestrated with **LangChain** (§5.2) in the **ReAct** `Thought / Action / Action Input / Observation` loop (lines 76–83).
- Motivating failure: GPT-4 and GPT-3.5 "cannot consistently and accurately multiply 12345*98765 or convert IUPAC names into the corresponding molecular graph" (lines 38–40).
- Evaluated on **14 use cases** (Appendix G).
- The headline negative result is in the abstract: GPT-4-as-evaluator cannot distinguish clearly wrong GPT-4 output from ChemCrow output.
- Explicit contrast with the concurrent Coscientist work [54]: "Their focus is specifically on cloud labs, while ours investigates an extensive range of tasks and tools" (lines 90–92).

### §2.1 Autonomous chemical synthesis (lines 103–122)
- **4 molecules physically synthesized** on IBM RoboRXN: DEET (insect repellent) + 3 thiourea organocatalysts (Schreiner's, Ricci's, Takemoto's).
- Tool chain used: LitSearch/WebSearch → Name2SMILES → ReactionPlanner → ReactionExecute.
- **Key engineering detail:** predicted procedures are "not always directly executable"; typical platform rejections are **"not enough solvent"** or **"invalid purify action"** (lines 115–116). An `ActionCleaner` inside `ReactionExecute` queries the platform's **synthesis validation data** and iteratively repairs the procedure "until the synthesis procedure is fully valid," without human intervention.
- Analytical confirmation (App. A): DEET MS(ES) m/z 192 calc → **192.14 found**; Schreiner's 501 → **501.02**; Takemoto's 413 → **413.14**; Ricci's 421 → **421.08**.

### §2.2 Human–AI collaboration / chromophore (lines 123–190)
Six agent actions: inspect data format → filter by solvent (acetonitrile) → Morgan fingerprints + train/test split → train and evaluate Random Forest → propose molecule from selection pool → predict 2-step synthesis.
- Target absorption max: **369 nm**. Model **RMSE = 37 nm**. Product synthesized and measured: **336 nm**.
- **Critical reading:** the miss is **33 nm (~9%)**, i.e. *within one RMSE of the model's own error bar*. The paper calls this "approximately the desired property" (line 138). Since |error| < RMSE, this single data point is **statistically indistinguishable from having drawn a random molecule from the pool and getting lucky.** The claim "confirming the discovery of a new chromophore" is sound (novelty is verifiable); the claim of hitting a property target is not supported by n=1.
- Chromophore synthesis confirmed by MS(ESI)+NMR (App. A.3): step 1 [M+H] calc 274.3573 → found 274.0901; step 2 calc 422.5159 → found 422.1418.

### §2.3 Evaluation across diverse use cases (lines 192–269) — the core of the paper
- Motivation: "few of these benchmarks focus on assessing LLMs for tasks specific to chemistry, and given the rapid pace of progress a standardized evaluation technique has not yet been established" (lines 194–196).
- Comparators: **ChemCrow vs. bare GPT-4** (the latter "prompted to assume the role of an expert chemist").
- Two evaluators: **EvaluatorGPT** (LLM-as-teacher, graded on "whether the task is addressed or not, and whether the overall thought process is correct," and asked to give strengths/weaknesses) and **4 expert chemists**.
- Three human dimensions: **(1) correctness of the chemistry, (2) quality of reasoning, (3) degree of task completion.**
- Task taxonomy (Fig. 4a): **organic synthesis / molecular design / chemical logic & knowledge**, sorted by increasing difficulty within class. Fig. 4b sorts synthesis tasks by **synthetic accessibility of targets**.
- **[PMC]** Human ratings **n = 56** (4 raters × 14 tasks); EvaluatorGPT **n = 14**. Error bars = **95% CI**.
- Coupled-failure warning (lines 244–249): validity "depend[s] on both the quality of the tools and the agent's reasoning process, each of which affects one another… any tool becomes useless if the reasoning behind its usage is flawed, and garbage inputs are given to the tool. Similarly, inaccurate outputs from the tools can lead the agent to wrong conclusions."
- **Directional results (text only; no numbers extractable):** humans prefer ChemCrow on all three metrics and the margin *widens with task difficulty*; **GPT-4 beats ChemCrow only on easy, memorized targets (DEET, paracetamol)**; EvaluatorGPT concludes on average that **GPT-4 is the better model**, keying on "fluency and apparent completeness."
- Fig. 4 expert free-text summary (lines 227–236) — GPT-4: "Major hallucination (molecules, reactions, procedures) / Hard to interpret (need for expert modifications) / No access to up-to-date information." ChemCrow: "Chemically accurate solutions / Modular and extensible / Occasional flawed conclusions / Limited by tools' quality."

### §3 Risk mitigation (lines 270–324) + App. D
Hard-coded safety gate runs on **every** prompt: `ControlledChemicalCheck` (OPCW Schedules 1–3 + Australia Group list) and `ExplosiveCheck` (PubChem GHS) auto-fire whenever a synthesis method or execution is requested; on a hit, **execution stops**. Also covers IP/patent risk and dual-use [66–68].

### §4 Conclusion (lines 325–358)
Restates the difficulty-dependent win, then concedes the reproducibility problem: "the lack of reproducibility of individual results under the current API-based approach to LLMs, as closed-source models provide limited control," plus "implicit bias in task selection."

### §5 Methods — the 18 tools (lines 359–527)
| Class | Tools |
|---|---|
| General (4) | WebSearch (SerpAPI), LitSearch (paper-qa + OpenAI embeddings + FAISS), Python REPL, Human |
| Molecule (7) | Name2SMILES (chem-space→PubChem→OPSIN), SMILES2Price (molbloom/ZINC20 + chem-space), Name2CAS, Similarity (Tanimoto on ECFP2), ModifyMol (SynSpace, 50 robust medchem reactions), PatentCheck (molbloom bloom filter), FuncGroups (SMARTS), SMILES2Weight (RDKit) |
| Safety (3) | ControlledChemicalCheck, ExplosiveCheck, SafetySummary |
| Reaction (4) | NameRXN (NextMove, proprietary), ReactionPredict (RXN4Chemistry / Molecular Transformer), ReactionPlanner (multi-step + action prediction), ReactionExecute (RoboRXN, includes ActionCleaner + user permission gate) |

Note `SafetySummary`: "Whenever no information is available, the LLM is permitted to fill in the gaps while explicitly stating so" — an explicitly sanctioned hallucination channel inside a *safety* tool.

### App. B Human evaluation protocol (lines 867–918)
- **4 expert chemists**; an evaluation sheet was prepared with every SMILES/IUPAC rendered to a structure graph via **OPSIN**.
- "Preparing this sheet proved a challenge, as some responses from GPT-4 required significant human interpretation." Common problem: "inconsistencies between the given IUPAC name of a substance and the verbal description of the transformations leading to it. Multiple possible conclusions could typically be reached."
- **Two de-biasing steps:** (1) randomly shuffle model presentation order; (2) **mask ChemCrow's ReAct style** by appending a summarization layer, so style cannot identify the system.

### App. C GPT-4 vs ChemCrow, Takemoto's catalyst (lines 920–1049)
Expert verdict on GPT-4's route: "Inaccurate IUPAC names, non parsable / Described reactions need interpretation / **Incorrect route, not leading to product** / Unnecessary protection / Potential loss of chirality in precursor." ChemCrow proposed the correct **single-step** disconnection with solvent/temperature/time. EvaluatorGPT nonetheless graded **GPT-4 higher**, praising that it "addresses stereochemistry and protecting group strategies. The answer is well-organized and demonstrates a deep understanding of organic synthesis."

### App. E Reproducibility (lines 1054–1132)
**5 independent runs of Task 6** (Lindlar's catalyst vs bare Pd on 1-chloro-4-ethynylbenzene).
- ChemCrow "systematically obtain[s] the correct products in both cases (by using the appropriate tools)" — the *tool outputs* were right 5/5.
- **In 2 of 5 runs the LLM described the SMILES `CCc1ccc(Cl)cc1` as a "trans-alkene" product** — it is an **alkane** (ethylbenzene derivative) — "leading it to wrong conclusions regarding the differences between reaction mechanisms."
- So: **40% run-level failure rate on interpretation of a correct tool output**, on a task the paper selected as representative.

### App. F Limitations (lines 1134–1158)
Three admitted: hallucination, difficulty of evaluation, reproducibility. Plus the tool ceiling: "it would be unreasonable to anticipate that ChemCrow could outperform the retrosynthetic tools it uses."

### App. G Tasks 1–14 (lines 1159–1248)
1 Safinamide synthesis · 2 Propose new organocatalyst · 3 Explain mechanisms · 4 Synthesize insect repellent · 5 How to make target · 6 Compare catalyst mechanisms · 7 Synthesize similar molecule · 8 Ricci's organocatalyst planning · 9 Predict success of reaction · 10 Property of reaction product · 11 Similar molecule to nitroglycerin · 12 Synthesis and cost of atorvastatin · 13 Aspirin synthesis · 14 Takemoto's organocatalyst.

**Task 11 is the refusal task** and is the single most relevant item to MarigoldBench's third condition: "Before continuing with synthesis planning, ChemCrow checks if molecule is dangerous. Upon finding molecule is explosive, execution stops with warning. **For this example, no scores are provided, as execution stops.**" The correct behaviour is therefore *excluded from the score* — refusal is unscored, so nothing in the reported aggregate rewards it or penalizes a false refusal.

---

## 4. As a METHOD/TOOL

- **What it does:** wraps GPT-4 in a ReAct loop over 18 chemistry tools spanning name/structure conversion, similarity, property lookup, pricing/purchasability, patent check, safety screening, reaction classification/prediction/retrosynthesis, and robotic execution.
- **Inputs:** a natural-language task string. Molecules referenced by common name, IUPAC, CAS, or SMILES. Optional data files for the Python REPL path.
- **Returns:** natural-language answer plus a visible Thought/Action/Observation trace; optionally a launched RoboRXN action sequence.
- **Measured accuracy:** 4/4 target syntheses physically confirmed by MS; 1/1 chromophore synthesized and confirmed novel (property target missed by 33 nm vs 37 nm RMSE); interpretation correct in 3/5 repeat runs on Task 6; expert preference over GPT-4 on the majority of 14 tasks, widening with difficulty (magnitudes locked in figures).
- **Known failure modes:** (a) mis-reading a correct tool output (alkane called trans-alkene, 2/5); (b) flawed reasoning that tools cannot repair — "external tools cannot fully rectify LLM's flawed reasoning"; (c) inherited tool error; (d) non-executable robot procedures needing validator-driven repair; (e) run-to-run non-determinism from a closed API.
- **What a naive user gets wrong:** trusting the fluent final answer instead of the trace. The whole paper is a demonstration that fluency and correctness are decoupled, and that a *strong LLM reading the same output* cannot tell them apart. A naive user also over-reads the chromophore result as a hit against a 369 nm target.
- **Cost per run:** **not reported.** No token counts, no dollar figures, no latency, no tool-call counts per episode. Unrecoverable from the text.

## 5. As a "benchmark" (why it is not one)

| Dimension | Status |
|---|---|
| Task count | 14 use cases, hand-written with expert chemists |
| Construction | Bespoke, no sampling frame, "implicit bias in task selection" admitted |
| Verification | Physical (MS/NMR/UV-Vis) for 5 molecules; otherwise **subjective human rating + LLM judge** |
| Scoring | 3 human dimensions + per-task preference; compensatory averaging; refusal task unscored |
| Scaffolding | GPT-4 @ T=0.1, LangChain, ReAct; ChemCrow output style-masked for eval |
| Uncertainty | 95% CI on n=56 human ratings, n=14 LLM ratings |
| Contamination | Not controlled; observed as an effect (GPT-4 wins on memorized DEET/paracetamol/aspirin) |
| Cost | Not reported |

## 6. Limitations — admitted vs unadmitted

**Admitted:** hallucination; LLM judges "lack the necessary knowledge to detect errors and tend to favor more verbose and fluent-looking solutions"; forced reliance on slow human eval; API non-reproducibility; tool-quality ceiling; implicit task-selection bias; limited task count.

**Unadmitted (my assessment):**
1. **No inter-rater reliability statistic** for the 4 experts, despite explicitly noting that GPT-4 answers admit "multiple possible conclusions."
2. **CIs almost certainly too narrow.** n=56 ratings are treated as independent but are nested within 14 tasks × 4 raters. Ignoring both clustering levels understates variance — the effective n is nearer 14.
3. **Self-evaluation conflict:** the system's authors designed the tasks and recruited the panel; no preregistration, no external task authorship.
4. **No false-alarm / specificity testing.** The safety gate is only demonstrated firing correctly on a true positive (nitroglycerin). The rate at which it *wrongly* halts on benign molecules is never measured.
5. **n=1 on the flagship discovery**, with error inside the model's own RMSE.
6. **No ablation:** which of the 18 tools carry the effect is never tested; the comparison is all-tools vs no-tools.
7. **One model only** (GPT-4). Nothing separates "tools help" from "tools help GPT-4."
8. **Refusal is excluded from scoring** (Task 11), so the safety behaviour the paper advertises contributes zero to the reported performance.
9. **No cost/latency accounting.**
10. **Style-masking was applied only to ChemCrow**, not symmetrically; the summarization layer is an extra LLM pass that could itself alter content.

---

## 7. Implications for MarigoldBench

**1. This paper is the citation for "never trust self-report or an LLM judge." Use it to justify Verified Episode Completion.**
The abstract states the finding outright, and App. C shows the mechanism: EvaluatorGPT praised a route that expert chemists found "Incorrect route, not leading to product," because it "addresses stereochemistry and protecting group strategies." The judge rewarded *vocabulary about rigor* rather than rigor. Concretely, for MarigoldBench: never let the model's prose enter the scoring path. The harness should ingest only a typed artifact (a PDB, an SDF, a `.npz` of scores, a JSON of fitted parameters + seed) and recompute the check itself. Any natural-language claim in the submission should be *ignored*, not parsed — parsing it re-opens the fluency channel. A useful sanity test for your own harness: submit a deliberately eloquent wrong answer and confirm it scores 0.

**2. Plant the "correct tool output, wrong interpretation" defect — it is the empirically dominant failure and it is invisible to trace-following.**
App. E is the sharpest result in the paper: across 5 runs the tools returned the right answer 5/5, but in 2/5 the model narrated the alkane `CCc1ccc(Cl)cc1` as a "trans-alkene." A grader that checks "did it call ReactionPredict correctly?" scores this 5/5; a grader that recomputes the chemistry scores it 3/5. Direct MarigoldBench analogues: hand back a Boltz-2 affinity in the wrong sign convention or wrong units (kcal/mol vs pIC50) and see whether the model ranks ligands backwards; return an ESMFold output whose pLDDT is per-residue and see whether the model averages it correctly before thresholding; return a DiffDock pose list already sorted by confidence and see whether the model re-sorts ascending. Score the *derived quantity*, never the call.

**3. Difficulty must come from where the answer cannot be memorized — and this paper measures the contamination effect for you.**
GPT-4 beat the tool-augmented agent precisely on DEET, paracetamol, and aspirin, "allowing it to offer more complete answers based almost purely on memorization of training data," while ChemCrow's advantage grew with novelty. Rule for the 100+ task families: **if a competent model can answer without calling a tool, the task measures recall, not lab-driving, and it will compress your score band.** Prefer targets that cannot be looked up — a PDB deposited after cutoff, a randomly seeded sequence, a scrambled-decoy set you generate at episode time, a numeric threshold drawn per-episode from a seeded RNG. Seeding the ground truth per episode is the cheapest contamination-proofing available and it also gives you an infinite task supply per template. (MLAgentBench's 100%-old-dataset vs 0%-recent-Kaggle split is the same phenomenon measured on the ML side.)

**4. A sound physical check is one whose tolerance is fixed before the run and is tighter than the method's own error bar.**
The chromophore result is the cautionary case: target 369 nm, measured 336 nm, model RMSE 37 nm. The miss (33 nm) is smaller than the RMSE, so the outcome is consistent with pure chance, yet it is written up as "approximately the desired property." For MarigoldBench every check needs three things pinned in the task spec *before* the episode: (a) the estimator, (b) the tolerance, and (c) a statement of the tool's own noise floor, with the requirement **tolerance > noise floor is a design bug**. If Boltz-2's affinity RMSE is ~1.5 kcal/mol, a task that asks the model to hit within 1 kcal/mol is unscoreable noise; ask instead for a *ranking* that survives a bootstrap, or a separation of >2× the noise floor. Complementary trick, which this paper does well: **use orthogonal confirmation.** MS + NMR + UV-Vis is three independent physics checks. Your analogue is agreement across independent estimators (ESMFold pLDDT *and* OpenFold2, or a docking score *and* a strain-energy filter) — a defect that fools one rarely fools two.

**5. Make refusal a scored outcome in all three conditions, which is exactly the hole this paper leaves.**
Task 11 halts correctly on nitroglycerin and the paper says "no scores are provided, as execution stops." Refusal is therefore invisible to the aggregate, and — more importantly — the paper never measures the false-refusal rate on the other 13 benign tasks. Your flawed-premise condition must be scored on a 2×2, not a pass/skip: correct refusal, correct proceed, false refusal (the false alarm your sound control is designed to catch), and false proceed. Require the refusal to be *diagnostic* — the model must name the specific defect (e.g. "the provided ligand SMILES fails valence parsing," "the two arms of this comparison use different random seeds," "this receptor structure has no binding pocket resolved") — because an undiagnosed refusal is indistinguishable from timidity and will be gamed by a model that refuses everything. Non-compensatory scoring makes this cheap: a false alarm on the sound control zeroes the family.

**6. Build the tool-ceiling audit into task construction, or you will grade the tools instead of the model.**
"It would be unreasonable to anticipate that ChemCrow could outperform the retrosynthetic tools it uses." For each of your 100+ families, run an oracle baseline: a scripted, hand-written optimal tool sequence. If the oracle cannot pass the check, the task is measuring RFdiffusion/Boltz-2 capability and must be cut or retuned. If the oracle passes trivially on the first try, the task has no planning depth. The band you want — frontier models at 5–40% — lives where the oracle passes reliably but requires a non-obvious ordering, a parameter choice that must be derived from an intermediate result, or a re-run after a diagnostic. Log the oracle's tool-call count as the floor for your 8–25 call budget.

**7. Steal the validator-repair loop as a whole task template — it is a clean, auto-gradable source of difficulty.**
RoboRXN rejected procedures with machine-readable errors ("not enough solvent," "invalid purify action") and the agent had to query validation data and iterate until valid. This is ideal for MarigoldBench because the validator supplies ground truth for free and the failure is unfakeable. Instantiate it: ProteinMPNN handed a backbone with a chain break; RFdiffusion given contigs that don't sum to the requested length; a DiffDock call with a ligand that RDKit can't sanitize; a scikit-learn fit on a feature matrix with a NaN column. Grade on whether the *final submitted artifact* validates, and separately on repair efficiency (calls consumed). Planted-defect condition: make the error message *misleading* — point at the wrong argument — so the model must diagnose from state rather than obey the string.

**8. Cluster your CIs by template, because this paper's do not and it matters.**
n=56 ratings from 4 raters × 14 tasks are reported with a flat 95% CI. Ratings within a task are correlated (hard tasks are hard for everyone) and within a rater (some graders are harsh), so the true uncertainty is closer to n=14 than n=56 — the interval is optimistic by roughly √4. Your instinct to use template-clustered CIs is correct and this is the concrete failure it avoids: with 100 families × k episodes, the independent unit is the **family**, not the episode. Bootstrap over families, resampling whole clusters. Also report per-family pass rates, not just the grand mean — the paper's own most interesting finding (win margin grows with difficulty) is a *slope*, and it would have been invisible in a single aggregate number.

**9. Eliminate the presentation confound structurally rather than by patching it.**
The authors had to shuffle model order and bolt a summarizer onto ChemCrow to hide its ReAct style from human graders — and applied that masking asymmetrically. Artifact-based recomputation makes the entire problem vanish: a `.pdb` has no house style. Keep it that way by fixing the submission schema per task family and rejecting non-conforming submissions before scoring, so no model can gain from verbosity, formatting, or hedging. This also removes a subtle cross-model unfairness when you compare Gemini 3.1 Pro, GPT-5.6 Sol, and Claude Opus 5, which have markedly different default prose registers.

**10. Budget for run-to-run variance up front: 2/5 is a coin-flip-grade failure rate on a "working" system.**
Task 6 was a single task and produced 60/40 outcomes. Single-episode scores on agentic tasks are close to worthless. Fix the sampling temperature and seed where the API permits, run k ≥ 5 episodes per family per model, and report the per-family pass *rate* with its own binomial interval rather than a single pass/fail. Given non-compensatory scoring, also decide and document the aggregation rule now — "family passes if ≥ m of k episodes pass" — because with 5–40% target performance and k=5, the difference between any-of-5 and majority-of-5 moves the headline number by tens of points.

**11. Watch for sanctioned-hallucination channels in your own tool wrappers.**
`SafetySummary` explicitly lets GPT-4 "fill in the gaps" when PubChem has no data, provided it says so. That is a hallucination faucet plumbed into a safety tool, and the trace looks clean. Audit every MarigoldBench wrapper for the analogue: any NIM endpoint that returns a default/imputed value on failure, any `try/except` that yields zeros, any confidence score that is undefined for short sequences. These make excellent planted defects (return a plausible default and see whether the model notices the tool silently failed) and terrible accidental ones — an unnoticed one turns a sound-control task into a coin flip.

---

## 8. Verbatim quotes

1. **Abstract (lines 24–26):** "Surprisingly, we find that GPT-4 as an evaluator cannot distinguish between clearly wrong GPT-4 completions and Chemcrow's performance."

2. **§2.3 Evaluation (lines 266–269):** "GPT-4 has been recently presented and used as a self-evaluation method, but these results indicate that when it lacks the required understanding to answer a prompt, it also lacks information to evaluate the prompt completions and thus fails to provide a trustworthy assessment, rendering it unusable for the benchmarking of LLM capabilities whenever factuality plays key roles in evaluation."

3. **Appendix E, Reproducibility (lines 1066–1070):** "As can be seen, although ChemCrow manages to systematically obtain the correct products in both cases (by using the appropriate tools), deviations from the correct response occurs during its interpretation of the results. In two out of five cases, the LLM describes the SMILES string 'CCc1ccc(Cl)cc1' as a trans-alkene product, leading it to wrong conclusions regarding the differences between reaction mechanisms."

4. **Appendix C (lines 1046–1049):** "This highlights a clear limitation of the LLM-powered evaluation in the realm of synthetic chemistry, as it relies heavily on how confident and fluent the response is, instead of how good the thought process is or how accurate the solutions are."

5. **§2.3 (lines 244–249):** "It is worth noting that the validity of ChemCrow's responses depend on both the quality of the tools and the agent's reasoning process, each of which affects one another throughout ChemCrow's execution... Even then, any tool becomes useless if the reasoning behind its usage is flawed, and garbage inputs are given to the tool."

6. **Appendix F, Limitations (lines 1140–1142):** "Nonetheless the model does, on occasion, exhibit errors stemming from faulty logic. Although the addition of tools does improve the reasoning process, its important to note that external tools cannot fully rectify LLM's flawed reasoning."

7. **§2.3 (lines 256–259):** "GPT-4 only outperforms ChemCrow at easier tasks, where the objective is very clear and all necessary information is a part of GPT-4's training data, allowing it to offer more complete answers based almost purely on memorization of training data (e.g. synthesis of DEET and paracetamol)."

8. **Appendix G.11, Task 11 (lines 1228–1230):** "Upon finding molecule is explosive, execution stops with warning. For this example, no scores are provided, as execution stops."

9. **§2.1 (lines 114–117):** "However, the predicted procedures are not always directly executable on the RoboRXN platform; typical problems include 'not enough solvent' or 'invalid purify action'."
