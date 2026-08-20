# Deep read: ai-scientist-chemcrow

## 0. ID CORRECTION (important)

The assigned arXiv id **2402.04247 was WRONG**. That id resolves to:

> "Risks of AI Scientists: Prioritizing Safeguarding Over Autonomy" — Xiangru Tang, Qiao Jin, Kunlun Zhu,
> Tongxin Yuan, Yichi Zhang, Wangchunshu Zhou, Meng Qu, Yilun Zhao, Jian Tang, Zhuosheng Zhang,
> Arman Cohan, Dov Greenbaum, Zhiyong Lu, Mark Gerstein (Yale / NLM-NIH / Mila / SJTU / OPPO / Reichman).
> arXiv:2402.04247v5 [cs.CY] 21 Jul 2025. 26 pages, 68,995 chars extracted.
> (Kept on disk at `A:/PERTURB-Bench/analysis/literature2/pdfs/2402.04247.pdf` and
> `.../md/2402.04247.md` — it is a *perspective* on AI-scientist safety, not ChemCrow. It cites ChemCrow as ref [2].)

The ChemCrow paper matching the assigned TOPIC is **arXiv:2304.05376**, which I downloaded and read instead.

## 1. Coverage ledger

| item | value |
|---|---|
| PDF | `A:/PERTURB-Bench/analysis/literature2/pdfs/2304.05376.pdf` (16,226,282 bytes, `%PDF-1.5`, 38 pages) |
| MD | `A:/PERTURB-Bench/analysis/literature2/md/2304.05376.md` |
| Total chars in md | **88,344** |
| Total lines | **1,249** |
| Chunk 1 | lines 1–40 (2,993 chars) — title block, abstract, intro start |
| Chunk 2 | lines 40–639 (48,767 chars) — intro, all Results, Risk Mitigation, Conclusion, all Methods incl. 18 tool descriptions, refs [1]–[38] |
| Chunk 3 | lines 640–1249 (36,688 chars) — refs [38]–[108], Appendix A (experimental procedures), B (human evaluation), C (GPT-4 vs ChemCrow synthesis), D (safety workflow), E (reproducibility), F (limitations), G (14 tasks) |
| **Chars paged through** | **88,344 / 88,344 = 100%** (104 chars of deliberate overlap at line 40) |
| Extraction health | > 15,000 chars, no ar5iv fallback needed. Caveat: Appendix G's 14 task prompts + all numeric evaluation scores live **inside raster figures** (Figs. 4, 9–22) and are therefore NOT in the extracted text. Only figure captions extracted. Figure 8 (reproducibility) *did* extract as letter-spaced text and is legible. |

## 2. Actual paper identity (as printed)

- **Title:** "Augmenting large language models with chemistry tools"
- **Authors:** Andres M. Bran¹², Sam Cox³ (∗equal), Oliver Schilter²⁴, Carlo Baldassari⁴, Andrew D. White³, Philippe Schwaller¹²
- **Affiliations:** ¹ Laboratory of Artificial Chemical Intelligence (LIAC), ISIC, EPFL; ² NCCR Catalysis, EPFL; ³ Dept. of Chemical Engineering, University of Rochester; ⁴ Accelerated Discovery, IBM Research – Europe
- **Venue as printed:** "Preprint. Under review." — arXiv:2304.05376v5 [physics.chem-ph], 2 Oct 2023. (Later published in *Nature Machine Intelligence*, but the on-disk artifact says preprint.)
- **Code:** `github.com/ur-whitelab/chemcrow-public` (open release = **12 of the 18 tools**); runs at `github.com/ur-whitelab/chemcrow-runs`.

**Classification: METHOD/TOOL paper with a small hand-built evaluation suite attached.** It is not a benchmark paper — but its evaluation section is the single most useful part for MarigoldBench because it is a documented failure of LLM-as-judge on an agentic scientific task.

## 3. Section-by-section notes with numbers

### Abstract / Intro (lines 11–101)
- **18 expert-designed tools** integrated; LLM = **GPT-4, temperature 0.1** (Methods 5.1), scaffolded with **LangChain** (5.2) in the **ReAct** Thought / Action / Action Input / Observation loop (also cites MRKL).
- Motivating failure: GPT-4 and GPT-3.5 "cannot consistently and accurately multiply 12345*98765 or convert IUPAC names into the corresponding molecular graph."
- Physical outputs claimed: autonomous synthesis of **1 insect repellent (DEET) + 3 thiourea organocatalysts** (Schreiner's, Ricci's, Takemoto's), plus **1 novel chromophore** discovered via human-AI collaboration.
- **14 use cases** in Appendix G.
- Contemporaneous work called out: Boiko et al. (Coscientist) — "Their focus is specifically on cloud labs, while ours investigates an extensive range of tasks and tools."

### 2.1 Autonomous chemical synthesis (lines 103–122)
- Tool chain actually used: LitSearch/WebSearch → Name2SMILES → ReactionPlanner → ReactionExecute, on IBM **RoboRXN**.
- **Key operational finding:** predicted procedures "are not always directly executable on the RoboRXN platform; typical problems include *'not enough solvent'* or *'invalid purify action'*." ChemCrow "autonomously query[s] the synthesis validation data from the platform and iteratively adapt[s] the synthesis procedure (such as increasing solvent quantity) until the synthesis procedure is fully valid" — this is the **ActionCleaner** loop inside ReactionExecute.
- All 4 syntheses "yielded the anticipated compounds successfully" — verified by HPLC/MS (Appendix A gives m/z: DEET calc 192, found 192.14; Schreiner 501 → 501.02; Takemoto 413 → 413.14; Ricci 421 → 421.08).

### 2.2 Human-AI collaboration / chromophore (lines 123–190)
- Task: clean chromophore data → filter to acetonitrile solvent → Morgan fingerprints → train/test split → **Random Forest** → predict on selection pool → pick molecule nearest **369 nm** target → 2-step synthetic plan.
- Model self-reported **RMSE = 37 nm**.
- Proposed molecule: (E)-3-methyl-4-(2-(3'-(methylsulfonamido)-[1,1'-biphenyl]-4-yl)vinyl)benzoate.
- **Measured absorption max = 336 nm** vs 369 nm target → **33 nm error, i.e. ~0.9× the model's own stated RMSE**. Paper calls this "approximately the desired property." Synthesis conditions in Appendix A.3 (SPhosPd G2 Suzuki, then Pd(OAc)₂/Et₃N Heck; confirmed by MS(ESI) + ¹H/¹³C NMR).
- **This is the single cleanest example in the literature of an agentic result that is "successful" only because the acceptance criterion was never pre-registered.** 336 vs 369 nm would fail any pre-declared tolerance tighter than ±35 nm.

### 2.3 Evaluation across use cases (lines 192–269)
- Comparators: **ChemCrow vs bare GPT-4 prompted to "assume the role of an expert chemist."**
- Two graders:
  - **EvaluatorGPT** — GPT-4 instructed as "a teacher assessing their students," grading only "whether the task is addressed or not, and whether the overall thought process is correct," plus strengths/weaknesses/feedback.
  - **4 expert chemists** (Appendix B) scoring 3 dimensions: (1) chemical correctness, (2) quality of reasoning, (3) degree of task completion.
- Tasks grouped into 3 families of increasing difficulty: **organic synthesis / molecular design / chemical logic & knowledge**; within family, sorted by synthetic accessibility.
- Error bars in Fig. 4c are **95% CIs**. (Actual point values are figure-only; not in extractable text.)
- **Headline result:** humans prefer ChemCrow on all three metrics; **EvaluatorGPT concludes GPT-4 is on average the better model.** GPT-4 wins only on easy, memorized targets (DEET, paracetamol, aspirin) "based almost purely on memorization of training data."
- Verbatim: "when it lacks the required understanding to answer a prompt, it also lacks information to evaluate the prompt completions and thus fails to provide a trustworthy assessment, **rendering it unusable for the benchmarking of LLM capabilities whenever factuality plays key roles in evaluation.**"
- Expert-observation panel (Fig. 4 side text) — GPT-4: "Major hallucination (molecules, reactions, procedures)", "Hard to interpret (need for expert modifications)", "No access to up-to-date information"; ChemCrow: "Chemically accurate solutions", "Modular and extensible", but "**Occasional flawed conclusions**" and "**Limited by tools' quality**."

### 3. Risk mitigation (lines 270–324) + Appendix D
- Hard-coded safety guidelines run **every time the agent receives a prompt** (Fig. 7): controlled-chemical check is **automatically invoked whenever a synthesis method or execution is requested**; if hit, **execution stops**.
- Task 11 (similar molecule to nitroglycerin) is the refusal case: "Upon finding molecule is explosive, execution stops with warning. **For this example, no scores are provided, as execution stops.**" → they had no scoring rubric for correct refusal.
- Other risks named: insufficient chemistry knowledge → flawed decisions; IP/patent infringement.

### 5.3 The 18 tools (lines 376–527) — inputs/outputs
- **General (4):** WebSearch (SerpAPI, first Google page); LitSearch (paper-qa + OpenAI embeddings + FAISS, top-k passage summaries); Python REPL (LangChain; "performing numerical computations to training AI models and performing data analysis"); Human (agent-initiated question to user; also used as a permission gate before launching robot runs).
- **Molecule (8):** Name2SMILES (chem-space → PubChem → OPSIN fallback chain); SMILES2Price (molbloom/ZINC20 purchasability → chem-space cheapest price); Name2CAS (PubChem); Similarity (Tanimoto on **ECFP2**); ModifyMol (SynSpace, **50 robust medchem reactions**, retro via PostEra Manifold or reversed rules, building blocks from Purchasable Mcule); PatentCheck (molbloom bloom filter, no web request); FuncGroups (named SMARTS patterns); SMILES2Weight (RDKit exact MW).
- **Safety (3):** ControlledChemicalCheck (CAS vs OPCW Schedules 1–3 + Australia Group list); ExplosiveCheck (PubChem GHS "Explosive" flag); SafetySummary (PubChem + LLM interface over 4 axes: operational safety, GHS, environmental risk, societal impact — "**Whenever no information is available, the LLM is permitted to fill in the gaps while explicitly stating so.**").
- **Reaction (4):** NameRXN (proprietary NextMove, Carey–Laffan–Thomson–Williams hierarchy code + name); ReactionPredict (RXN4Chemistry / Molecular Transformer, reactants → product); ReactionPlanner (RXN4Chemistry multi-step search + action prediction → machine-readable actions, then an **added LLM step converting actions to natural language**); ReactionExecute (plan → robot action sequence → LLM error/warning-repair loop → asks user permission → returns success on **launch**, not on completion).
- Note the boundary: ReactionExecute "returns a success message upon successful **launching** the action sequence" — success ≠ product.

### Appendix B — Human evaluation protocol (lines 867–918)
- 4 expert chemists; a prepared evaluation sheet; every molecule/reaction mentioned in text was **rendered to a structure depiction via OPSIN** so graders judged graphs, not prose.
- "Preparing this sheet proved a challenge, as some responses from GPT-4 required significant human interpretation." Common issue: "inconsistencies between the given IUPAC name of a substance and the verbal description of the transformations leading to it. **Multiple possible conclusions could typically be reached in some cases.**"
- **Two explicit debiasing steps:** (1) randomized presentation order of the two models per task; (2) **style masking** — an extra summarization layer stripped ChemCrow's characteristic ReAct formatting so graders could not identify the system by format.

### Appendix C — Case study (lines 920–1049)
- Takemoto's organocatalyst. GPT-4 proposes a long protect/deprotect route with "inaccurate IUPAC names, non parsable", "incorrect route, not leading to product", "unnecessary protection", "potential loss of chirality in precursor." ChemCrow proposes the correct **single-step** thiourea formation from the isothiocyanate + chiral diamine, with solvent/temperature/time.
- **EvaluatorGPT still scores GPT-4 higher**, praising that it "addresses stereochemistry and protecting group strategies. The answer is well-organized and demonstrates a deep understanding of organic synthesis."

### Appendix E — Reproducibility (lines 1054–1132)
- **n = 5** independent runs of Task 6 (Lindlar's catalyst vs bare Pd on 1-chloro-4-ethynylbenzene).
- Tool-level results were **5/5 correct** (the right product SMILES came back every time).
- **Interpretation was 3/5 correct: in 2 of 5 runs the agent read the SMILES `CCc1ccc(Cl)cc1` (an alkane) as a "trans-alkene"** and then produced a wrong mechanistic comparison ("Difference: Stereochemistry of the double bond" instead of partial vs full hydrogenation).
- Diagnosis: "the issue is in molecular structure interpretation" — a *representation-reading* failure downstream of a correct tool call. Suggested fix: multimodal molecular captioning models.

### Appendix F — Limitations, as admitted (lines 1134–1158)
1. Hallucination persists: "**external tools cannot fully rectify LLM's flawed reasoning.**"
2. Evaluation: LLM judges "lack the necessary knowledge to detect errors and tend to favor more verbose and fluent-looking solutions"; forced reliance on human experts "restrict[s] the pace and scale at which performance can be measured."
3. Ceiling from tools: "it would be unreasonable to anticipate that ChemCrow could outperform the retrosynthetic tools it uses."
4. Reproducibility under closed-source APIs (Appendix E).
5. "**implicit bias in task selection**" (Conclusion, line 354).

## 4. What a naive user gets wrong (tool-paper checklist)

- Believing "success" from the agent means the physical result was achieved. ReactionExecute returns success on **launch**; the chromophore was "successful" at 336 nm against a 369 nm ask.
- Trusting a self-reported RMSE (37 nm) as if it were a validated generalization bound; there is no held-out check that the reported RMSE was computed on the split the agent claims.
- Assuming a correct tool call implies a correct conclusion — 2/5 runs read a correct SMILES wrongly.
- Assuming SafetySummary is grounded: it is explicitly allowed to fabricate when PubChem is empty, as long as it says so.
- Assuming the open-source repo reproduces the paper: it ships **12 of 18** tools (NameRXN and the RXN4Chemistry/RoboRXN path are proprietary/gated).
- Assuming LLM grading is a cheap stand-in for expert grading. It inverts the ranking here.

## 5. Limitations NOT admitted

- **n is tiny and unstated as a statistic.** 14 tasks, 4 graders, 1 reproducibility task × 5 runs. No per-task variance, no inter-rater agreement (κ) reported, no task-family clustering of the 95% CIs even though tasks are explicitly grouped into 3 families.
- **No sound-control condition.** Every task has something to find. There is no task where the correct answer is "the premise is wrong" or "no valid route exists," so false-alarm/over-claiming rate is unmeasured.
- **The one refusal case (Task 11) is unscored** — the safety stop is asserted as correct behavior but never enters any aggregate, so refusal precision/recall are both unknown, as is the false-refusal rate on benign molecules.
- **Contamination is acknowledged only rhetorically.** They note GPT-4 wins on memorized targets (DEET, paracetamol, aspirin) but never remove them, never date-partition, and never test on post-cutoff molecules. The chromophore is the only genuinely novel target.
- **The chromophore result has no control arm** — no random-baseline or literature-baseline molecule was synthesized, so 336 vs 369 nm cannot be shown to beat picking a plausible molecule by hand.
- **No cost, latency, or tool-call-count reporting anywhere.** Not one number for tokens, dollars, or steps per episode.
- **Verification of the physical results is by MS only** for the four robot syntheses (m/z match) — no yield, no purity, no chiral analysis for the stereodefined Takemoto/Ricci catalysts, despite chirality being the exact axis on which GPT-4's route was faulted.
- **The human graders are not independent of the authors** (a "panel of four expert chemists," unspecified provenance) and the same style-masking layer that hides ReAct format is itself an extra GPT-4 call that could repair content.

## 6. Implications for MarigoldBench

1. **Never let an LLM judge be in the scoring path — this paper is the citation for why.** ChemCrow's headline negative result is that GPT-4-as-evaluator ranked a route that "does not lead to the product" above a correct one-step route, because the wrong answer was fluent and mentioned protecting groups. MarigoldBench's recompute-the-check design is exactly the mitigation; cite Appendix C as prior evidence and add a *deliberate* fluency-decoy condition: a planted-defect variant whose submitted artifact is accompanied by an unusually polished, jargon-dense rationale. If VEC is doing its job, decoy polish should have zero effect on score; measure that as a harness self-test.

2. **Score the artifact, not the tool trace — but also require the tool trace, because "correct tool call → wrong conclusion" is the dominant real failure.** ChemCrow's own reproducibility study is 5/5 correct at the tool layer and 3/5 correct at the interpretation layer. Concretely for MarigoldBench: for a Boltz-2 or DiffDock episode, log both (a) the raw tool return and (b) the model's natural-language claim about it, and add a *transcription check* to VEC — recompute the scalar the model asserted (affinity, pLDDT, RMSD, Tanimoto) directly from the artifact and fail the episode on any mismatch beyond float tolerance. This catches the exact `CCc1ccc(Cl)cc1`-read-as-trans-alkene class of failure, which self-report can never surface because the model is not lying, it is misreading.

3. **Pre-register the acceptance tolerance in the task spec, or you get 336-nm-counts-as-369-nm.** ChemCrow's flagship discovery missed its own target by 33 nm against a self-reported 37 nm RMSE and was written up as success. Every MarigoldBench task family should carry a machine-readable `success_criterion` (target value, tolerance, and the estimator used) fixed *before* the episode runs, and VEC should compare the recomputed value to that literal. A useful hard variant: give the model a target and let it *propose* the tolerance, then score it on whether its proposed tolerance is honest — i.e. whether the recomputed error actually falls inside the interval it claimed, with over-wide intervals penalized as a non-answer.

4. **Plant the four failure modes this paper demonstrates, because they are documented as real rather than hypothetical.** (a) *Representation misread*: hand the model a correct-but-adversarial artifact (a SMILES/PDB whose obvious visual reading differs from its true content — an alkane that looks alkene-y in prose, a PDB with the ligand in a symmetry mate) and see whether it recomputes with RDKit or eyeballs it. (b) *Environment-invalid plan*: mirror the RoboRXN "not enough solvent / invalid purify action" pattern — a MolMIM/GenMol request with a parameter outside the NIM's accepted range, or a ProteinMPNN call on a backbone with chain breaks — and score whether the model reads the validation error and repairs versus retries blindly or reports success. (c) *Silent gap-filling*: ChemCrow's SafetySummary is permitted to invent when PubChem is empty; plant a tool that returns an empty/`null` field and check whether the model propagates a fabricated number into its artifact. (d) *Tool-ceiling attribution*: give a task whose correct answer is "the underlying predictor cannot resolve this" (e.g. an ESMFold call on an IDR, or Boltz-2 on a target outside its applicability domain) and score whether the model says so instead of reporting the low-confidence number as a result.

5. **Build an explicit refusal/false-alarm rubric — ChemCrow shows what happens without one.** Their Task 11 stops on an explosive and is simply excluded ("no scores are provided, as execution stops"), so their safety mechanism has an unmeasured false-refusal rate. MarigoldBench's flawed-premise condition must be scored on a two-sided rubric: refusal is only credited if the model *names the specific defect* (recomputable: does the stated defect match the planted one?), and the sound-control condition must contain near-miss lookalikes of each planted defect so that a model refusing on pattern-match alone gets penalized. Report refusal precision and recall separately, never a merged accuracy.

6. **A tool-use task is genuinely hard when the tools are individually correct and the difficulty lives in composition, unit/representation handoffs, and knowing when to stop.** ChemCrow's easy tasks (DEET, paracetamol, aspirin) were won by *bare GPT-4 with no tools at all* through memorization — those tasks measure nothing. Difficulty in the ChemCrow data came from (i) chaining ≥4 heterogeneous tools where one's output format is another's input, (ii) targets outside the memorization set, and (iii) tasks requiring interpretation of a tool return rather than its verbatim relay. Design MarigoldBench families around handoff friction: RFdiffusion → ProteinMPNN → ESMFold → recomputed self-consistency RMSD is exactly this shape, and the check (scRMSD < 2 Å, computed by the harness from the deposited backbone + sequence + refolded structure) is sound because it is a physical quantity the model cannot assert into existence.

7. **A physical/statistical check is "sound" for VEC only if it is (a) recomputable from the deposited artifact alone, (b) monotone in the thing you actually care about, and (c) not gameable by the generator that produced the artifact.** ChemCrow's four robot syntheses were verified by m/z match alone — an identity check that is recomputable and hard to fake, which is why those results survive; the chromophore's RMSE was self-reported, which is why it does not. Apply the same triage: prefer checks like mass/formula match, scRMSD, held-out-split AUC recomputed by the harness on a split the harness chose, PoseBusters-style geometry validity, and Boltz-2 rescoring of a *shuffled-decoy* control. Distrust any metric the model both computes and reports.

8. **Design against contamination the way ChemCrow failed to.** They kept aspirin/paracetamol/DEET in the suite and then had to explain away GPT-4 winning them. For MarigoldBench, each family needs a parameterized instance generator (random target, random split seed, random decoy set) so that no episode's answer is a lookup, and at least one instance per family should be built from post-training-cutoff data (recent PDB depositions, recent ChEMBL activity). Add a memorization probe as a null task: ask for the answer with the tools disabled; any family where a tool-less model scores non-trivially is contaminated and should be cut.

9. **Report cost and step count — ChemCrow reports neither, and that omission is why nobody can compare against it.** MarigoldBench is already committed to 8–25 tool calls per episode; log and publish tokens, wall-clock, NIM calls, and dollars per episode per model, and report VEC alongside a cost-normalized variant. Also fix the scaffold explicitly (ChemCrow's is ReAct/LangChain over GPT-4 at temperature 0.1) and treat scaffold as a declared experimental condition, since the paper shows the same base model swings from worst to best depending on tool access.

10. **Use template-clustered CIs and run ≥5 seeds per cell, because the within-task variance is the finding.** ChemCrow's own n=5 rerun showed a 40% interpretation-failure rate on a task they otherwise present as solved; a single-run benchmark would have scored that task 1.0. With 100+ families and a 5–40% target band, single-shot scoring will misestimate badly. Report per-family pass rate over seeds, cluster CIs at the template level (ChemCrow's Fig. 4c uses 95% CIs but pools across obviously non-independent task families), and publish the seed-level pass/fail matrix.

## 7. Verbatim quotes

1. (§2.3 Evaluation, lines 266–269) — "GPT-4 has been recently presented and used as a self-evaluation method, but these results indicate that when it lacks the required understanding to answer a prompt, it also lacks information to evaluate the prompt completions and thus fails to provide a trustworthy assessment, rendering it unusable for the benchmarking of LLM capabilities whenever factuality plays key roles in evaluation."

2. (Appendix C, lines 1043–1049) — "Regardless of this, EvaluatorGPT gives a higher grade to GPT-4, argumenting that the model 'addresses stereochemistry and protecting group strategies. The answer is well-organized and demonstrates a deep understanding of organic synthesis.' This highlights a clear limitation of the LLM-powered evaluation in the realm of synthetic chemistry, as it relies heavily on how confident and fluent the response is, instead of how good the thought process is or how accurate the solutions are."

3. (Appendix E Reproducibility, lines 1066–1071) — "As can be seen, although ChemCrow manages to systematically obtain the correct products in both cases (by using the appropriate tools), deviations from the correct response occurs during its interpretation of the results. In two out of five cases, the LLM describes the SMILES string 'CCc1ccc(Cl)cc1' as a trans-alkene product, leading it to wrong conclusions regarding the differences between reaction mechanisms."

4. (Appendix F Limitations, lines 1139–1142) — "In this study, we've demonstrated how chemical tools significantly enhance both the factual correctness and decision-making abilities of LLMs. Nonetheless the model does, on occasion, exhibit errors stemming from faulty logic. Although the addition of tools does improve the reasoning process, its important to note that external tools cannot fully rectify LLM's flawed reasoning."

5. (§2.1, lines 114–119) — "Standardized synthesis procedures are key for successful execution. However, the predicted procedures are not always directly executable on the RoboRXN platform; typical problems include 'not enough solvent' or 'invalid purify action'. Addressing these issues requires human interaction to fix the invalid actions before attempting to execute the synthesis."

6. (§2.2 / Fig. 3, lines 131–138) — "The proposed molecule (see Figure 3) was subsequently synthesized and analyzed, confirming the discovery of a new chromophore with approximately the desired property (measured absorption maximum wavelength of 336nm)." [target was 369 nm; model's self-reported RF RMSE was 37 nm]

7. (§5.3.3 SafetySummary, lines 494–496) — "Whenever no information is available, the LLM is permitted to fill in the gaps while explicitly stating so. In that case, GPT-4 is permitted to fill in the gaps, but must explicitly state so."

8. (Appendix G.11 / Fig. 19 caption, lines 1228–1230) — "Upon finding molecule is explosive, execution stops with warning. For this example, no scores are provided, as execution stops."
