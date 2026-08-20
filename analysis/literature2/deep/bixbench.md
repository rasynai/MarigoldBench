# BixBench — deep read

## Coverage ledger

| item | value |
|---|---|
| Requested arXiv id | 2505.08341 — **WRONG PAPER** (see identity below) |
| Correct arXiv id | 2503.00096 (v3, 8 Oct 2025, q-bio.QM) |
| PDF | `A:/PERTURB-Bench/analysis/literature2/pdfs/2503.00096.pdf` (3,266,197 bytes, `%PDF-1.7`) |
| Extracted md | `A:/PERTURB-Bench/analysis/literature2/md/bixbench.md` |
| Pages | 16 |
| Total chars (pypdf) | 52,392 |
| Total lines | 1,014 |
| Chars read | 52,392 (100%) |

Chunk ranges read with Read tool:
- lines 1–340 (title, abstract, intro, contributions, related work, methods: recruitment / capsule creation / task generation, start of agent infra)
- lines 341–680 (tools, evaluation protocol, model selection, results, discussion, future work, references A–I)
- lines 681–1015 (references J–Z, Appendix A: Figures 6–8, full agent initialisation prompt across 3 pages)

No gaps. Extraction exceeded the 15,000-char floor so no ar5iv fallback was needed.

### Mis-ID note (important)
The supplied id 2505.08341 resolves to a **different paper**: "Benchmarking AI scientists for omics data–driven biological discovery" (BAISBench) by Erpai Luo, Jinmeng Jia, Yifan Xiong, Xiangyu Li, Xiaobo Guo, Baoqi Yu, Minsheng Hao, Lei Wei, Xuegong Zhang (Tsinghua). That PDF was downloaded and extracted (13 pp, 58,952 chars, saved at `.../md/2505.08341.md`) and page 1 was read to confirm the mismatch, then discarded. BAISBench is a plausible sibling read for MarigoldBench (193 MCQs from 41 single-cell studies, 15 expert-labeled datasets, six graduate bioinformaticians as human baseline) but it is not BixBench. Correct id located via WebSearch and re-downloaded.

## Actual paper identity (as printed)

**Title:** BixBench: a Comprehensive Benchmark for LLM-based Agents in Computational Biology
**Authors:** Ludovico Mitchener\*, Jon M Laurent\*, Alex Andonian\*, Benjamin Tenmann, Siddharth Narayanan, Geemi P Wellawatte, Andrew White, Lorenzo Sani, Samuel G Rodriques (\* equal contribution)
**Affiliations:** 1 = FutureHouse, San Francisco, USA; 2 = ScienceMachine, London, UK
**Correspondence:** sam@futurehouse.org, lorenzo@sciencemachine.ai
**Venue:** No venue printed. Formatted in the ICML style with "Copyright 2025 by the author(s)." — i.e. an ICML-format preprint, arXiv:2503.00096v3 [q-bio.QM] 8 Oct 2025.
**Artifacts:** dataset at huggingface.co/datasets/futurehouse/BixBench; harness at github.com/Future-House/BixBench.

Version drift worth recording: the v1 press coverage describes "53 real-world scenarios with 296 open-answer questions"; the v3 text I read says **61 capsules / 205 questions**, and the abstract hedges to "over 60" and "over 200". The headline number moved between versions.

## Section-by-section notes with numbers

### Abstract / §1 Introduction
- Framing: benchmarks are evolving "from pure recall and rote knowledge tasks, towards more practical work." Bioinformatics is picked because it is "a microcosm of the scientific process" that is "disconnect[ed] from the physical laboratory" — i.e. deliberately chosen because no wet-lab step is needed.
- Headline result: **~21% accuracy at best** in open-answer; MCQ with majority voting is **no better than random guessing**.
- Intro promises "extensive validation of our experimental setup, investigating potential data leakage, hyperparameter optimization, and frontier model choice." **This promise is not kept** — the string "leakage" occurs exactly once in the entire document (line 117, the promise itself). There is no leakage section, no hyperparameter sweep table, and no model-choice ablation beyond two models. Verified by grep over the full text.

### §1.1 Contributions
1. 61 analytical scenarios + 205 open-answer questions.
2. Assessment framework "including key metrics and calibrations."
3. Open-source agent framework for Python, R and bash in a Jupyter notebook.

### §2 Related work
- Positions against SWE-Bench, BigCodeBench, HumanEval, ML-Bench, MLE-Bench, MLAgentBench, SUPER, DA-Code, DSBench, RE-Bench, BLADE, ChemBench, LAB-Bench, BioLP-Bench, BioLLMBench, CORE-Bench, BioCoder, ScienceAgentBench, DiscoveryBench.
- Two named weaknesses of prior art that BixBench claims to fix: RE-Bench "rel[ies] on a simple reward function such as training loss," and BLADE is "artificially constrained to producing specific artifacts and making specific statistical choices."
- Design thesis: "In science, most analytical tasks are ambiguous, open-ended, and do not benefit from having a clear optimization metric to verify performance."

### §3.1 Benchmark creation
- **Analysts:** recruited via professional networks, cold-emailing bioinformatics paper authors, and affiliated institutions. "exclusively of PhD holders or candidates in bioinformatics and related fields."
- **Capsule = 3 primary parts:** (1) hypothesis/research question, (2) input data, (3) analysis code. Plus captured `result` (few sentences) and `answer` (true/false: was the hypothesis supported), plus metadata.
- Analysts either recapitulated published analyses or produced de novo trajectories from their own data. Code captured in Jupyter via Google Colab; a custom UI let analysts start a capsule, get a template notebook, and upload data. Publicly-fetched data (e.g. `wget`) was re-retrieved separately for persistence.
- Peer review by other experts before merge → **61 approved capsules**.
- **Task generation (3 stages):**
  1. Claude 3.5 Sonnet (20241022) drafts MCQs from a modified notebook + hypothesis + result. **Two rounds of four questions = 8 MCQ drafts per capsule.**
  2. Human expert review with full edit access; Approve/Reject with or without editing; reviewers could re-review earlier items to catch their own review errors; given the original capsule, notebook and data.
  3. LLM duplicate filtering, run **in triplicate**, ~**95% concordance** across the three responses, duplicates manually verified, loop repeated until no flags.
- Final: **205 questions / 61 capsules, 1 to 7 questions per capsule, mean 3.8.**
- Note the funnel: 61 × 8 = 488 drafts → 205 survivors, so roughly **58% of LLM-drafted questions were dropped** by expert review + dedup.

### Table 1 (comparison table)
| Benchmark | Time (h) | Tasks | Eval | Multi-lang | Science | Avg lines |
|---|---|---|---|---|---|---|
| DA-Code | 0.1 | 500 | Verifier | Y | N | 85 |
| DSBench | 17 | 540 | Verifier | N | N | 75 |
| MLE Bench | 2.5 | 75 | Reward | N | N | – |
| RE-Bench | 8 | 7 | Reward | Y | N | 650 |
| BLADE | 1.5 | 188 | MCQ | N | Y | 75 |
| ScienceAgentBench | 2.5 | 102 | Verifier | N | Y | 58 |
| **BixBench** | **4.2** | **205** | **Open-ended** | **Y** | **Y** | **106** |

BixBench is the only row with "Open-ended" eval. 4.2 h is the human reference time per capsule; 106 is average lines of code in the reference notebook.

### §3.2 Evaluation
- **Environment:** agent gets an *empty* Jupyter notebook + input data files + the questions. Pre-built Docker image `BixBench-env:v1.0` with extensive Python/R/bash bioinformatics packages, "so evaluation remains focused on problem-solving capabilities rather than on software installation or dependency resolution." Agents must still identify and load the right packages.
- **Scaffold:** Aviary (Narayanan et al. 2024), SimpleAgent prompting. **Exactly three tools:**
  - `edit cell` — select, modify and execute a notebook cell
  - `list workdir` — recursive workspace inspection
  - `submit answer` — finalize and end the episode
- **Every code modification triggers a full rerun of the notebook**, so the agent sees tables, plots and tracebacks. This is a strong statefulness choice: no stale-kernel divergence between what the agent believes and what the notebook actually computes.
- **Open-answer scoring:** `submit_answer` ends the trajectory; a **judge LLM (Claude 3.5 Sonnet)** compares the agent's answer to a ground-truth solution; **binary 1/0**. Each capsule run **5× in parallel**.
- **MCQ scoring:** post-hoc. A *second* LLM receives the complete analysis notebook + the question now with options + the agent's open answer, and picks an option. An **"Insufficient information" refusal option** is provided in the with-refusal condition. **Majority voting over the 5 runs.**
- **Model selection:** GPT-4o and Claude 3.5 Sonnet only. Explicit reason for excluding reasoning models: "reasoning models such as o1 and DeepSeek R1 struggled to perform such tasks due to the long contexts and the structured outputs required for agentic tool use." (This dates the paper hard.)

### §4 Results
- 61 capsules × 5 replicates = **305 trajectories per (model × modality) cell**; 2 models × 2 modalities (images / no images) → **1,220 total trajectories**.
- **Open-answer: Claude 3.5 Sonnet 21%, GPT-4o 15%.**
- **Recall baseline** (questions asked with no notebook and no context at all) is drawn as a solid gray line in Fig. 4. Critically: "Performance does not surpass a baseline assessed as performance on the questions given to the model without access to any analysis notebook" (Fig. 4 caption). **The agents with a full lab do not beat a model answering from memory alone.**
- **MCQ with refusal:** both models "very close to random" — the refusal option is heavily used.
- **MCQ without refusal:** higher and above random, which the authors attribute to recall: "we speculate is due in large part to the model relying on answering via recall rather than the information contained in the analysis."
- **Majority voting:** "we don't see any significant deviation as vote counts accumulate in either refusal or no-refusal regimes." Inference-time scaling via 5-way voting buys essentially nothing.
- **Vision/plot ablation:** motivated by an observation that "models seemed to do a poor job of interpreting plots in the notebooks generated both by humans and the agents themselves." Prompting the agent *not* to generate images produced "no significant effect on actual benchmark results."
- Precision is defined for the MCQ case (correct / answered, excluding refusals) but no numeric precision value appears in the extracted text — it lives only in Figure 4/5.

### §5 Discussion / Future work
- Admits three gaps: field coverage ("many important workflows, pipelines, statistical approaches, data types... are missing"); **no human baseline** ("we anticipate that additional human experts would perform significantly higher... and thus did not prioritize gathering this data"); reasoning models untested.
- Notes reasoning models "hold promise for future work due to their ability to improve performance from binary reward signals, like the capsules we introduce here."

### Appendix A
- Fig. 6: worked example of a capsule (notebook + data + hypothesis/result/answer metadata + generated-then-reviewed questions).
- Fig. 7: per-capsule accuracy across replicates. Fig. 8: per-question accuracy across replicates. Both are distributional views only — no numbers in text.
- **Full agent init prompt across 3 pages (lines 877–1014).** Notable contents:
  - Sample questions are concrete and numeric: "What percentage of genes differentially expressed in strain 97 are also differentially expressed in strain 99?", "How many genes have a dispersion value below 1e-05 after DEseq analysis?"
  - Heavy scaffolded chain-of-thought with `<analysis_planning>` blocks at 5 stages: list directory → load data + descriptive stats → develop analysis plan → execute → conclude/submit.
  - Prompt explicitly asks the agent to "List potential statistical assumptions for your chosen methods and how you'll test them" and "Identify potential confounding factors."
  - Numeric answer convention: "If the question asks for a number, be precise to 2 decimal places."
  - "AVOID USING PLOTS. USE TABLES AND PRINT OUTPUTS INSTEAD AS MUCH AS POSSIBLE." (the no-image ablation condition, baked into the shipped prompt).
  - `%load_ext rpy2.ipython` pre-loaded in cell 1 so `%%R` and `%%bash` cells work.
  - Output contract: `submit_answer({"q1": ..., "q2": ...})` JSON dict, must be called to end the episode.

## Benchmark profile (this is a benchmark)

- **Task count:** 61 capsules, 205 open-answer questions, mean 3.8 q/capsule (range 1–7).
- **Construction:** expert-authored real analyses (PhD bioinformaticians, contracted), peer-reviewed; questions LLM-drafted (8/capsule) then expert-reviewed/edited then LLM-deduped in triplicate; ~58% draft attrition.
- **Verification method:** **LLM-judge against a free-text ground-truth answer, binary.** There is *no* recomputation of the agent's numbers, no unit test, no programmatic verifier, no re-execution of the submitted notebook against an oracle. This is the single biggest methodological difference from what MarigoldBench is planning.
- **Scoring:** accuracy = fraction correct over all questions × all 5 replicates. MCQ variant adds majority voting and a precision metric excluding refusals.
- **Agent scaffolding:** Aviary SimpleAgent, 3 tools (`edit cell`, `list workdir`, `submit answer`), Docker `BixBench-env:v1.0`, full notebook rerun on every edit.
- **Reported scores:** open-answer Claude 3.5 Sonnet **21%**, GPT-4o **15%**; MCQ w/ refusal ≈ random; MCQ w/o refusal above random but below/near the no-notebook recall baseline. 5 replicates per capsule, 1,220 trajectories total.
- **Uncertainty:** **no error bars, no confidence intervals, no significance tests reported in the text.** Words like "significant" are used informally ("no significant deviation", "no significant effect") without a test statistic or p-value. Figs. 7/8 show per-capsule and per-question spread but no CI is stated. There is no clustering of uncertainty by capsule despite questions being nested within capsules (1–7 per capsule) — a textbook source of underestimated variance.
- **Contamination handling:** the *design intent* is stated — "The questions contained in BixBench are intended by design not to be answerable by model recall" — and a **recall baseline is measured** (questions with no notebook/context). That baseline is the paper's real contamination control, and it is damning: agent performance does not exceed it. But the promised data-leakage investigation never appears in the paper body.
- **Cost per run:** **not reported anywhere.** No token counts, no dollar figures, no wall-clock per trajectory for the agent (only the 4.2 h human reference in Table 1). For 1,220 long-context notebook trajectories this is a substantial omission.

## Limitations admitted vs unadmitted

**Admitted:** incomplete coverage of bioinformatics workflows/data types; no human baseline (explicitly deprioritized); reasoning models untested and known to fail the scaffold; models are poor at reading plots.

**Unadmitted (my read):**
1. **The promised leakage/hyperparameter/model-choice validation is absent from the body.** The intro advertises it; grep finds "leakage" once, in that advertisement.
2. **No uncertainty quantification at all**, despite a nested question-in-capsule structure that guarantees correlated errors. "Marginally above random" is asserted, never tested.
3. **The judge is the same model family as one of the tested models** (Claude 3.5 Sonnet judges Claude 3.5 Sonnet), with no judge-agreement study against human graders and no judge-swap ablation. Binary LLM-judge scoring of free text is the entire measurement instrument and it is uncalibrated.
4. **The MCQ regime is not an agentic evaluation.** A second LLM reads the notebook and picks an option — so the MCQ number measures a reader model's ability to extract an answer from a transcript, conflated with the agent's ability to produce a correct analysis.
5. **The ground truth is one expert's trajectory.** Capsules were reviewed, but for open-ended analysis there are usually several defensible analytical routes; a correct answer reached by a different valid method can be judged wrong, and no inter-analyst agreement on the answers is reported.
6. **Refusal is scored as failure, not as a possible correct action.** The paper reads refusal as models "opt[ing] out" and frames the no-refusal uplift as recall contamination — but it never asks whether some questions are genuinely unanswerable from the provided data, in which case refusal would be the right answer. No unanswerable-by-construction control items exist.
7. **An unresolved citation placeholder — `(xxcite lab-benc, figqa)` — survived into arXiv v3**, seven months after v1. Minor, but a copy-editing signal.
8. **No per-capsule difficulty stratification or saturation analysis**, so it is unknown whether the 21% is spread across capsules or concentrated in a few easy ones (Fig. 7 would show this but no numbers are given).

## Implications for MarigoldBench

1. **Do not adopt the LLM-judge-vs-reference-answer design; BixBench is the cautionary case for it.** BixBench's entire instrument is "Claude 3.5 Sonnet compares the agent's free text to a ground-truth string, binary 1/0" — and the paper cannot then distinguish a wrong analysis from a right analysis phrased oddly, or a right answer reached by recall from one reached by work. MarigoldBench's recompute-the-check design directly fixes this. Make the contrast explicit in the paper: our harness re-runs the physical/statistical check on the submitted artifact (PDB file, SDF, model checkpoint, dataframe) rather than reading a sentence about it. The corollary is a hard requirement: **every task family must emit a machine-parseable artifact, not a natural-language claim.** Enforce this in the task schema — a task without a recomputable artifact is not admissible.

2. **Ship the no-tools recall baseline as a first-class, gating condition for all 100+ families.** BixBench's most valuable single number is the gray line in Fig. 4: agents with a full analysis environment did not beat a model answering the same questions with **no notebook and no context at all**. That baseline is what turns "21%" from a capability claim into an indictment. For MarigoldBench, run each task family through a *tools-disabled* arm where the model must answer from priors alone. Any family where tools-disabled ≥ tools-enabled minus its CI is measuring memorized literature, not lab-driving, and should be cut or redesigned. This is cheap (one short completion per family) and it is the strongest contamination control in the paper.

3. **Our three-condition design already solves BixBench's biggest scoring bug — say so, and exploit it.** BixBench found that removing the refusal option *raised* scores and read that as recall contamination; with the refusal option, models sat at random. They had no way to tell a correct abstention from a cop-out because **no item was unanswerable by construction**. MarigoldBench's flawed-premise condition is exactly the missing control. Two design consequences: (a) keep the flawed-premise share high enough to be non-guessable — if it is a known 1-in-3, a model can farm it, so vary the per-family mix and do not publish the ratio per family; (b) score sound-control false alarms and flawed-premise misses on the *same* scale so that a refuse-everything policy and an accept-everything policy both score near zero. Non-compensatory VEC gives this for free; make sure the harness actually reports the confusion matrix, not just the pass rate.

4. **Make hardness come from multi-step state and heterogeneous inputs, not from obscure trivia.** BixBench's hardness levers are worth copying verbatim: heterogeneous file formats and directory structures (csv, rds, nested dirs) requiring real workspace navigation; ~106 lines of reference code; 4.2 h of expert time; and *a full rerun of the notebook on every edit* so that the agent cannot accumulate a false belief about kernel state. That last one maps cleanly onto our 8–25 tool-call episodes: **make the lab stateful and re-validated between calls** (e.g. re-read the structure file from disk before each downstream step) so an agent that corrupts an intermediate — a mis-chained PDB out of RFdiffusion, a ligand that failed sanitization before DiffDock — is confronted with the failure rather than allowed to narrate past it. Hardness should come from the artifact having to survive the whole pipeline, not from the question being esoteric.

5. **Plant the failure modes BixBench observed empirically, not invented ones.** The paper hands us a validated defect list: (i) *plot-blind reasoning* — models "do a poor job of interpreting plots... generated both by humans and the agents themselves," so plant defects that are only visible in a figure (a bimodal pIC50 distribution, a docking pose clashing with the backbone, a loss curve that diverged after epoch 30) and check whether the model looks; (ii) *skipping assumption checks* — BixBench's own prompt has to beg the agent to "List potential statistical assumptions... and how you'll test them," which implies they don't, so plant violated-assumption defects (non-normal residuals under a t-test, unequal variance, a Pearson r on a monotone-but-nonlinear relation); (iii) *unhandled data-quality issues* — the prompt also has to beg for "missing data or unexpected formats"; plant NaNs, duplicated ligand IDs, a mislabeled chain, a train/test leak in the scikit-learn split. Each of these is a defect a competent human catches and a current agent demonstrably does not.

6. **A sound check is one that is (a) recomputed from the artifact, (b) invariant to the route taken, and (c) has a known false-positive rate on the sound control.** BixBench fails (a) and (b): its ground truth is one expert's trajectory, so a defensible alternative analysis can score 0. For MarigoldBench, define each check as a *property of the artifact*, not a match to a reference run — e.g. "ESMFold pLDDT of the submitted sequence ≥ X and RMSD to the target scaffold ≤ Y", "the submitted binding-affinity delta survives the harness's own re-run of the Boltz-2 call within tolerance Z", "the reported AUC recomputed on the held-out split by the harness is within 0.02 of the claim." Then **calibrate every check by running it against the sound control**: if a check fires on clean inputs more than a few percent of the time it is measuring noise, and the family should be re-tuned before it counts toward the 100. Publish that per-family false-positive rate — it is the number BixBench never reports and the reason its "significant" claims are untestable.

7. **Cluster CIs by task family, and report them — BixBench reports none and it undermines every claim.** BixBench nests 1–7 questions inside each of 61 capsules and then reports a bare accuracy with no error bars, no significance test, and no accounting for within-capsule correlation, while making comparative claims ("marginally above random", "no significant deviation"). Our template-clustered CI plan is the fix; the lesson is to be disciplined about *which* unit is independent. Two episodes from the same task family with different random seeds are **not** independent samples. Budget the campaign so each family has enough independent instantiations to support the cluster, and pre-register the target band (5–40%) with the CI width needed to distinguish Gemini 3.1 Pro / GPT-5.6 Sol / Claude Opus 5 — otherwise we will land three models inside one interval and be unable to rank them.

8. **Report cost per episode from day one.** BixBench ran 1,220 long-context notebook trajectories and reports zero tokens and zero dollars — so nobody can reproduce it on a budget or compare compute-matched. With 100+ families × 3 conditions × replicates, our campaign is larger. Log tokens, wall-clock, tool-call count, and NIM API spend per episode, and publish median and p95 per family. It also gives us a second axis: an agent that reaches the same VEC in 9 tool calls instead of 24 is meaningfully better, and cost data is what makes 8–25 calls an interesting range rather than an arbitrary cap.

9. **Budget for scaffold-induced floor effects and validate the harness on the strongest models before the campaign.** BixBench excluded o1 and DeepSeek R1 because they "struggled... due to the long contexts and the structured outputs required for agentic tool use" — i.e. the scaffold, not the models, set the ceiling, and the paper's headline number was obsolete within months. Before spending the campaign, smoke-test the MarigoldBench harness against all three candidate models specifically for tool-call schema compliance, long-context truncation, and NIM timeout/retry behaviour, and log harness-attributable failures separately from scientific failures. A VEC of 0 because the model emitted malformed JSON to DiffDock is not evidence about drug discovery, and if we cannot separate the two our 5–40% band is uninterpretable.

10. **Steal the question-construction funnel, but invert who checks whom.** BixBench's pipeline (LLM drafts 8 candidates per capsule → expert edits/approves → LLM dedups in triplicate at ~95% concordance → 205 of ~488 survive) is a reasonable, cheap way to reach 100+ families and worth reusing for generating *task variants* within a family. But note the direction: they used an LLM to write the questions and humans to check. Because our scoring is recomputation-based, we can invert it — **let the harness check the task**. Auto-generate candidate defects, then require that the planted defect actually flips the recomputed check (and that the sound control passes it) before the family is admitted. A defect that does not move the verifier is not a defect, and this is a filter BixBench structurally could not build.

## Verbatim quotes

1. (§1 Introduction / abstract) — "We find that even the latest frontier models achieve only 21% accuracy in the open-answer regime, and marginally better than random in a multiple-choice setting."

2. (§4.1 Results, Figure 4 caption) — "Performance does not surpass a baseline assessed as performance on the questions given to the model without access to any analysis notebook to base answers in (i.e. pure model recall.)"

3. (§3.2.4 Evaluation, Open-answer) — "The final submitted answer is then automatically evaluated by a judge LLM (Claude 3.5 Sonnet) by comparing the agent-generated response against a ground-truth solution, with correctness assigned as a binary score (1 if correct, 0 otherwise)."

4. (§5 Discussion) — "Of note, when removing the option to abstain from answering the performance again increases, which we speculate is due in large part to the model relying on answering via recall rather than the information contained in the analysis."

5. (§2.2 Related Work) — "In science, most analytical tasks are ambiguous, open-ended, and do not benefit from having a clear optimization metric to verify performance."

6. (§4.1 Results, vision ablation) — "we noted during question generation and other testing that the models seemed to do a poor job of interpreting plots in the notebooks generated both by humans and the agents themselves, something previously observed in a benchmark of model performance on understanding scientific figures (xxcite lab-benc, figqa)." — note the unresolved citation placeholder, present in arXiv v3.

7. (§3.2.5 Model Selection) — "During our preliminary tests we found that reasoning models such as o1 and DeepSeek R1 struggled to perform such tasks due to the long contexts and the structured outputs required for agentic tool use."

8. (§5.1.2 Future Work) — "we anticipate that additional human experts would perform significantly higher than the agent performance reported here, and thus did not prioritize gathering this data."
