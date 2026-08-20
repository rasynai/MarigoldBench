# Deep read: tdc-scaffold — Therapeutics Data Commons / scaffold-split evaluation pitfalls

## 0. Identity correction (IMPORTANT)

The arXiv id supplied in the task, **2306.09169, is the wrong paper**. Downloaded, extracted
(15 pages, 41,999 chars) and read page 1: it is

> "Opportunities for Large Language Models and Discourse in Engineering Design"
> Jan Göpfert, Jann M. Weinand, Patrick Kuckertz, Detlef Stolten
> (Forschungszentrum Jülich / RWTH Aachen), arXiv:2306.09169v1 [cs.CL], 15 Jun 2023

This is a position paper about LLMs in the product-development process. It has nothing to do
with TDC, scaffold splits, or molecular property prediction. I discarded it after the identity
check (read lines 1–80 only) and searched for the correct topic match.

Two papers cover the assigned topic. I read **both in full** because neither alone covers both
halves of the assigned title ("Therapeutics Data Commons" AND "scaffold split evaluation
pitfalls"):

- **PRIMARY (P1)** — matches both halves: TDC ADMET endpoints + scaffold-split critique.
- **COMPANION (P2)** — the canonical "scaffold splits are not hard enough" result; no TDC,
  but it is the paper P1's whole literature stands on and it supplies the model-selection
  inversion evidence.

---

## 1. Coverage ledger

| File | Lines | Chars | Chunks read (Read tool, offset–limit) | Coverage |
|---|---|---|---|---|
| `A:/PERTURB-Bench/analysis/literature2/md/2607.10729.md` (P1) | 712 | 47,992 | 1–240, 240–479, 480–712 | 712/712 lines = 100% |
| `A:/PERTURB-Bench/analysis/literature2/md/2406.00873.md` (P2) | 564 | 44,157 | 1–290, 290–565 | 564/564 lines = 100% |
| `A:/PERTURB-Bench/analysis/literature2/md/2306.09169.md` (WRONG paper, discarded) | ~1,050 | 41,999 | 1–80 only (identity check) | discarded |

- **Total chars in the two on-topic md files: 92,149.**
- **Chars actually paged through: 92,149** (both files read end to end, including references,
  methods, proposition, and data-availability sections). Plus ~4,600 chars of the discarded
  wrong paper for the identity check, not counted.
- Extraction succeeded on both (>15,000 chars each), so no ar5iv HTML fallback was needed.
- PDFs on disk: `A:/PERTURB-Bench/analysis/literature2/pdfs/2607.10729.pdf` (596,867 bytes),
  `.../2406.00873.pdf` (1,005,184 bytes), `.../2306.09169.pdf` (353,778 bytes, wrong paper).
  All three verified `%PDF` magic and >80 KB.

---

## 2. Actual paper identity (as printed)

**P1.** "Beyond Scaffold Splits: Structural-Frontier Evaluation Reveals Hidden Failures in
ADMET Models." Jiacheng Zheng*(1), Chang Guo(2), Zixuan Wang(3), Xinyu Liu(4), Hao Chen(1).
(1) Marine College, Shandong University, Weihai; (2) Dept. of Mathematics, UCL; (3) School of
Life Science and Technology, Harbin Institute of Technology; (4) Univ. of International
Business and Economics, Beijing. Corresponding: karcenzheng@gmail.com.
`arXiv:2607.10729v3 [cs.LG] 7 Aug 2026`. 15 pages. Keywords: ADMET; Cheminformatics; QSAR;
Machine Learning; Applicability Domain. No external funding; no conflict of interest. Data:
TDC assets from Harvard Dataverse DOI 10.7910/DVN/21LKWG version 105.0 (CC0 1.0) + CMNPD
(CC BY-NC-SA 4.0). Journal-style formatting (numbered-bracket Wiley-ish reference style),
appears to be a chemistry-journal submission; venue not printed.

**P2.** "Scaffold Splits Overestimate Virtual Screening Performance." Qianrong Guo(a), Saiveth
Hernandez-Hernandez(b), Pedro J. Ballester(a*). (a) Dept. of Bioengineering, Imperial College
London; (b) Centre de Recherche en Cancérologie de Marseille. Corresponding:
p.ballester@imperial.ac.uk. `arXiv:2406.00873`. 14 pages, LNCS/Springer conference layout
(running heads "Q. Guo et al."). Funding: CONAHCYT (S.H-H.), Wolfson Foundation + Royal
Society Wolfson Fellowship (P.J.B.). Code:
`https://github.com/ScaffoldSplitsOverestimateVS`.

---

## 3. Section-by-section notes with numbers

### 3.1 P1 — Abstract / Introduction (lines 11–62)

Core claim: "a scaffold label captures only one notion of chemical novelty." They introduce a
**label-free structural-frontier split** that reserves the sparsest and most physicochemically
remote scaffold groups, and benchmark it on **six public TDC ADMET tasks** against a **ratio-
and group-matched scaffold control**.

Headline numbers:
- Frontier inflates primary error by **taskwise median 87.0%**, **skew-sensitive mean 130.3%**
  (descriptive 95% task/seed stability interval 52.1–246.0%, 30 task–seed effects).
- Gap survives a message-passing GNN and **on average exceeds published Lo-Hi and DataSAIL
  splits**.
- BBB produces a **genuine score-ranking inversion**, not a prevalence artifact.
- A count-adjusted multi-view tail-risk penalty (MV-FREX) and three fixed DRO objectives
  **do not reliably close the gap**.

Scale of the study: **468 fully recorded primary runs**, five paired seeds, plus a **46-run
message-passing graph-network control**. 468/468 completed; 5,616 metric records; 120 split
manifests; **zero failed runs discarded**.

Provenance argument (lines 41–48): CMNPD's six ADMET fields are **BIOVIA Pipeline Pilot 18.1
predictions, not experiments**. Treating them as ground truth "would turn evaluation into
distillation of a legacy teacher" and would make a concept-drift claim **unidentifiable**: if
the observed target is Ỹ = h(X), a change in P(X) or in the marginal P(Ỹ) does not establish a
change in the conditional mechanism. Hence the paper reserves the word **accuracy** for the
measured TDC endpoints and uses **teacher agreement** for CMNPD.

### 3.2 P1 — Related work (lines 63–105)

- Scaffold split (Bemis–Murcko, 1996) is "a useful leakage control, not a complete deployment
  model."
- Prior hard splits: SIMPD (simulated medicinal-chemistry series progression without
  timestamps), Lo-Hi (low-similarity tests), Real-World MOOD (distance-to-training vs
  performance/calibration), DataSAIL (leakage-aware partitions).
- Applicability-domain lineage: descriptor-space AD definitions and their cutoffs **need not
  agree**. Molecular UQ benchmarks find **no estimator uniformly reliable across tasks**.
- Conformal prediction gives finite-sample marginal coverage **under exchangeability**, which
  "does not automatically survive the deliberately shifted frontier, and we do not claim it
  here."

### 3.3 P1 — Table 1: primary performance (lines 82–91)

Mean ± SD over five seeds.

| Task | Metric | Scaffold 80/10/10 | Matched scaffold (70/10/20) | Frontier ERM | Frontier MV-FREX |
|---|---|---|---|---|---|
| BBB | AUROC↑ | 0.885±0.019 | 0.879±0.020 | **0.409±0.005** | 0.409±0.004 |
| HIA | AUROC↑ | 0.692±0.169 | 0.717±0.161 | 0.538±0.015 | 0.535±0.024 |
| CYP2D6 | AUPRC↑ | 0.581±0.027 | 0.569±0.017 | 0.383±0.005 | 0.383±0.005 |
| DILI | AUROC↑ | 0.747±0.046 | 0.811±0.025 | 0.584±0.029 | 0.589±0.033 |
| PPBR | MAE↓ | 10.457±1.349 | 11.234±0.653 | 17.897±0.104 | 17.869±0.100 |
| Solubility | MAE↓ | 1.364±0.028 | 1.373±0.040 | 1.915±0.022 | 1.917±0.015 |

Per-task frontier/matched error ratios (Fig. 1a): BBB **5.0×**, HIA 2.1×, CYP2D6 1.4×, DILI
2.2×, PPBR 1.6×, Solubility 1.4×.

Note the conventional 80/10/10 and matched 70/10/20 scaffold columns are nearly identical —
the ratio change is **not** the driver. That is the control that makes the frontier claim
attributable to *where* molecules are held out, not *how many*.

### 3.4 P1 — Result 0.1: endpoint-wide gap (lines 107–122)

- Taskwise median relative error inflation **87.0%**; mean **130.3%** (interval 52.1–246.0%).
- Leave-one-endpoint-out: removing BBB drops mean to **75.9%**, median to **59.7%**; removing
  any other endpoint leaves mean between **131.8% and 148.4%**. They therefore designate the
  median and BBB-excluded mean as primary and the six-endpoint mean as an upper, skew-sensitive
  figure.
- Chance-adjusting CYP2D6 AUPRC reduces its inflation from **43.5% → 31.3%**; equally weighted
  mean remains **128.2%** (48.7–244.7%). CYP2D6 AUROC error rises **42.6%**. Three-seed linear
  control shows mean **112.4%** gap (36.7–229.1%).
- **Label shift induced by a label-free split** (seed 0, train → frontier test positive
  prevalence): BBB 86.0% → 48.1%; HIA 97.0% → 52.6%; CYP2D6 20.9% → 13.0%; DILI 53.0% → 40.7%.
  Reported as "a consequence of structural selection, not as evidence of conditional or causal
  concept drift."

### 3.5 P1 — Result 0.2: the BBB inversion is real (lines 168–182)

This is the methodologically sharpest part of the paper and the single most transferable idea
for a verification harness.

- BBB frontier AUROC **0.409±0.005** over five seeds sharing an **identical 389-molecule test
  set (187 positive, 202 negative)**; compound-and-seed bootstrap interval **0.352–0.467**, in
  which **only 0.155% of resamples reach chance**.
- Rebuttal of the obvious confound: "AUROC is a rank statistic and is invariant to class
  prevalence, so this sub-chance value is a genuine *ranking inversion*." Exact
  class-prevalence reweighting leaves standardized AUROC **unchanged at 0.409** while
  prevalence-sensitive metrics move as expected.
- Mechanism identified as **support-confounded association**: true BBB label correlates
  **negatively** with the frontier score (Spearman **−0.455**) while the model's prediction
  correlates **positively** (Spearman **+0.369**). Mean prediction rises **0.71 → 0.91** as the
  positive fraction falls **0.65 → 0.14**.
- Decomposition: within-novelty-stratum AUROC **0.563** (above chance), cross-stratum AUROC
  **0.384** (inverted) → pooled **0.409**. A textbook Simpson-style stratified decomposition.
- Early stopping ruled out: **frontier validation AUROC is 0.805**.

### 3.6 P1 — Result 0.3: capacity control (lines 221–239, Table 2)

Message-passing GNN, **304,260 parameters**, four binary tasks, same splits/seeds.

| Task | Metric | Matched scaffold | Frontier ERM | Frontier MV-FREX |
|---|---|---|---|---|
| BBB | AUROC↑ | 0.888±0.034 | 0.659±0.093 | 0.680±0.052 |
| HIA | AUROC↑ | 0.683±0.028 | 0.527±0.028 | 0.527±0.028 |
| CYP2D6 | AUPRC↑ | 0.632±0.011 | 0.461±0.029 | 0.456±0.031 |
| DILI† | AUROC↑ | 0.765 | 0.733 | 0.704 |

† single completed seed, descriptive only — explicitly flagged.

- Mean normalized error inflation **82.8%** (interval 21.8–187.2%; four tasks, 15 paired
  effects). Every task still degrades. "A low-capacity head is therefore not the source of the
  effect."
- **BBB no longer inverts** (0.409 → 0.659±0.093): the sub-chance ranking was specific to the
  weakest model. This is an honest self-limitation of their own headline.
- MV-FREX under the stronger encoder: **−1.9%** (interval −8.0 to +3.9%) — the penalty null is
  "reproduced across two model families rather than asserted for one."

### 3.7 P1 — Result 0.4: frontier vs published hard splits (lines 240–314, Table 3)

Same harmonized molecule sets, official implementations, identical matched scaffold control.

| Task | Metric | Matched scaffold | Frontier | Lo-Hi | DataSAIL |
|---|---|---|---|---|---|
| BBB | AUROC↑ | 0.879 | **0.409** | 0.695 | 0.618 |
| HIA | AUROC↑ | 0.717 | 0.538 | 0.691 | **0.412** |
| CYP2D6 | AUPRC↑ | 0.569 | 0.383 | **0.262** | — |
| DILI | AUROC↑ | 0.811 | 0.584 | 0.760 | 0.682 |
| PPBR | MAE↓ | 11.234 | 17.897 | — | 10.385 |
| Solubility | MAE↓ | 1.373 | 1.915 | 1.537 | — |
| **Mean error inflation vs matched** | | — | **118.9%** | **54.1%** | **96.0%** |
| **Median error inflation vs matched** | | — | **61.4%** | **26.5%** | **87.9%** |

- Realized ratios: DataSAIL ≈ 70/10/20 (test fraction 0.19); Lo-Hi ≈ 75/10/14 (it discards
  near-neighbour molecules, so the test block shrinks).
- **Lo-Hi's mixed-integer program was infeasible for PPBR at any feasible fraction.** DataSAIL
  did not solve two tasks within budget. Both are recorded as `n/a` rather than silently
  dropped.
- Restricting the frontier to the same task subsets preserves the ordering: **157.6%** on
  DataSAIL's four, **130.8%** on Lo-Hi's five. This is the right way to handle a ragged
  coverage matrix.
- **Splits are not interchangeable**: DataSAIL makes HIA harder (0.412 vs 0.538) yet PPBR
  *easier* than the matched control (**−7.6%**); Lo-Hi makes CYP2D6 harder (**+71%** vs
  **+43%**). "No single split is uniformly hardest."

### 3.8 P1 — Result 0.5: robust objectives fail (lines 292–321, Table 4)

| Method | Error reduction (%) | 95% CI (%) | Win / tie / loss |
|---|---|---|---|
| V-REx-style | −0.001 | [−0.049, 0.061] | 12 / 5 / 13 |
| Smooth worst-group | 0.012 | [−0.060, 0.089] | 16 / 1 / 13 |
| Sample-tail CVaR-style | −0.342 | [−1.214, 0.215] | 17 / 0 / 13 |
| MV-FREX | 0.160 | [−0.429, 0.844] | 16 / 0 / 14 |

**Every interval contains zero.** MV-FREX worst-view-bin reduction 1.30% (−0.89 to 4.89%).
The paper states plainly: "These controls do not support the motivating hypothesis... **they do
not establish equivalence.**" That is a correctly stated null.

### 3.9 P1 — Result 0.6: novelty is representation-dependent (lines 322–326)

- Pairwise Spearman between frontier-test novelty scores across views ranges **−0.093 to
  0.837**, mean **0.321**.
- ECFP–physicochemical correlation averages **0.198**.
- Frontier score's strongest correlation with any single descriptor is only **0.31–0.55**.
- Conclusion drawn is deliberately narrow: supports multi-view *evaluation*, **not** the
  stronger claim that optimizing worst source-view risk controls unseen chemistry.

Inter-view correlation matrix (Fig. 1c): ECFP–MACCS 0.22, ECFP–atom-pair 0.51,
ECFP–physchem 0.20, MACCS–atom-pair 0.26, MACCS–physchem 0.24, atom-pair–physchem 0.49.

### 3.10 P1 — CMNPD teacher-agreement audit (lines 327–401)

- All **31,561** CMNPD SMILES parse. Six ADMET fields are Pipeline Pilot predictions.
- Mappings explicitly approximate: BBB/HIA teachers use level thresholds; CYP field is a legacy
  binary model trained separately from TDC inhibition labels; PPBR is a binary teacher compared
  with a thresholded regression predictor; hepatotoxicity ≠ curated human DILI.
- CMNPD median physicochemical novelty coordinates **2.73–5.63**; **80.3%** of CMNPD exceeds
  the maximum PPBR training coordinate in that view. Fraction beyond max training novelty by
  view (Fig. 4c): ECFP and MACCS are **0% for every task**, atom-pair 0–18%, physchem 0–80%.
  I.e., **the same molecules are in-domain under one fingerprint and far out-of-domain under
  another.**
- **Coverage collapse**: usable BBB teacher fraction falls from **97.4% in Q1 to 0.73% in Q5**.
- BBB teacher-agreement AUROC falls 0.592 (0.577–0.607) → **0.332 (0.156–0.528)**, but the
  latter uses only **46 compounds (10 pos, 36 neg)** and is flagged descriptive under coverage
  collapse. This is exactly the right disclosure.
- Solubility teacher MAE 1.160 → **5.434** full range; **1.160 → 3.349** on the |ỹ|≤10 subset
  retaining 93.1% of Q5; Spearman **0.609 → −0.012**.
- CYP2D6 is a **counterexample** — agreement *improves* with novelty. Reported anyway.
- "Neither direction identifies biological accuracy."

### 3.11 P1 — Computational Methods (lines 485–619)

**Split construction.** Connectivity-equivalent structures harmonized before splitting; binary
replicates use majority vote with **exact ties removed**; regression replicates use the median.
Conventional reference: stereochemistry-free Murcko groups at 80/10/10, retaining the literal
empty scaffold as one disclosed acyclic group. Central comparison: identical grouping units,
70/10/20; RDKit descriptors robustly scaled; **only the heterogeneous empty-scaffold group is
partitioned into deterministic descriptor-space cells of at most 50 molecules**.

Frontier score for scaffold *s* with median descriptor vector c_s, distance r_s from the median
scaffold, and mean distance d_s to the ten nearest scaffold centres:

> q_s = ½·rank01(r_s) + ½·rank01(d_s)   (Eq. 1)

Highest-scoring groups supply ~20% test, next 10% validation, remaining 70% train. "**Labels
are not read by either procedure.**"

**Views / environments.** All predictors receive the same 1,024-bit radius-2 Morgan
fingerprint. Views V = {ECFP, MACCS, atom pair, physchem} define risk environments *only*.
Fingerprints reduced to ≤32 training-fitted singular-vector components. Novelty coordinate
(Eq. 3) = ½·rscale(‖ψ_v(x) − m_v‖₂) + ½·rscale(d_{v,5}(x)), with medians and MADs **fitted on
training molecules** and thresholds **frozen** for held-out molecules. Training quartiles →
4 ordered bins → G = 16 view–bin groups.

Crucially, they **disclose their own confound**: "The frontier allocation score q_s (Eq. 1) and
the physicochemical view z_physchem are built from the same RDKit descriptor family, so this
environment is partly aligned with the axis that constructs the split."

**Objective.** Binary: cross-entropy. Regression: standardized targets, Huber loss. Only the
robust term is clipped (ℓ̄ = min{ℓ,5}/5 ∈ [0,1]); empirical risk unclipped. Count-adjusted
group quantity (Eq. 4) adds √(log(2G/δ)/(2N_{v,b})) with δ = 0.05. k = ⌈0.4×4⌉. Final objective
(Eq. 5): J = mean loss + 0.5·T̃ + 0.2·S̃. Finite maxima via temperature-0.1 log-sum-exp.
Self-flagged: "Because minibatch means are combined with full training counts, Eq. 4 is a
regularizer, **not an unbiased full-sample objective or post-selection confidence
certificate**."

**Proposition 1** (coverage for a declared mixture family): under a fixed predictor, fixed view
maps and bin thresholds chosen independently of an i.i.d. evaluation sample, distinct ordered
bin centres, and every declared view–bin group represented, with probability ≥ 1−δ, R_{Q0} ≤
T_E for every target Q0 = Σ_b q_b P_{v,b} with q_b ≥ 0, Σq_b = 1, q_b ≤ 1/k; and for the
declared extension family, R_Q ≤ T_E + ρ(S_E + η). The authors then **immediately delimit it**:
the condition excludes within-bin covariate or label-mechanism change, membership in the
extension family is **assumed rather than inferred**, "the proposition therefore does not
certify the training objective or unrestricted molecular OOD," and the realized simultaneous
Hoeffding correction (**0.035–0.202 across groups**) shows the bound is "**non-vacuous but
loose**." It "makes no empirical claim about the frontier gap or about MV-FREX, both of which
are settled by the runs below."

**Datasets (TDC).** BBB permeability **1,941** molecules; intestinal absorption (HIA) **577**;
CYP2D6 inhibition **12,888**; human plasma protein binding **1,578** (percentage points);
aqueous solubility **9,690** (log10 mol L⁻¹); DILI **475**. Classification: AUROC, except
imbalanced CYP2D6 → AUPRC primary. Regression: MAE. Secondary: AUPRC, balanced accuracy, MCC,
Brier, ECE; RMSE, Spearman, R².

**Model.** 64-unit ReLU MLP, dropout 0.1, AdamW lr 0.002, weight decay 1e−4, batch ≤1,024,
gradient clip 5, ≤30 epochs, validation patience 6. "These are fixed implementations, **not a
hyperparameter search or canonical reproduction of every published algorithm**."

**Statistics and integrity.** Error e = 1−m (classification), e = m (regression); matched split
effect = (e_frontier − e_scaffold)/e_scaffold. Descriptive hierarchical bootstrap resamples six
tasks then paired task–seed effects, 10,000 replicates; it "measures task/algorithmic-seed
stability, **not laboratory or held-out-scaffold sampling uncertainty**." Every run stores
configuration, checkpoint, history and predictions. **468/468 primary runs completed; 5,616
metric records; 120 split manifests; 46/46 graph-network runs completed; zero failed runs
discarded.** "All preprocessing, novelty coordinates, thresholds and early stopping use no test
labels. **Unit tests assert split non-overlap and objective differentiability.**"

**LLM disclosure** (lines 639–642): "Language-model assistance was used for code debug and
prose editing under human-author responsibility. No language model is part of the scientific
method, predictor, data generation or statistical analysis; all citations, quantitative claims
and figures were independently verified against primary sources and recorded outputs."

### 3.12 P2 — Scaffold Splits Overestimate Virtual Screening Performance

**The mechanism, stated plainly (§3.1, lines 266–279).** "What has not been noted yet is that
scaffolds are often similar and can be almost identical." Of the 48,416 molecules tested on the
IGROV1 cell line, the two most frequent Bemis–Murcko scaffolds are **benzene and pyridine** —
nearly identical structures. A scaffold split can legally put all benzene-containing molecules
in test and all pyridine-containing molecules in train while satisfying the "no shared
scaffold" constraint exactly. The constraint is satisfied; the leakage is not prevented.

**Data.** NCI-60 (Oct 2020 release), 60 cell lines across nine tumour types, **33,118 unique
molecules**, **1,764,938 GI50 determinations** (88.8% completeness), each dataset ~30,000–50,000
molecules. Target: pGI50.

**Splits.** Seven groups per method so cluster counts match. Scaffold split: 33,118 molecules
evenly into seven groups, ~**4,731** per group. UMAP split: seven UMAP clusters from a prior
optimal-clustering study; the **4,396-molecule** cluster chosen as test to match scaffold test
size. Butina split constructed analogously. Seven-fold CV × 5 seeds × 60 datasets = **2,100
evaluations per algorithm per split**.

**Models.** Linear Regression; Random Forest (scikit-learn defaults, n_estimators 100); GEM
(GeoGNN pre-trained on 20M ZINC15 molecules, fine-tuned 20 epochs, batch 32, dropout 0.1, lr
0.001). Features: 256-bit Morgan radius-2 + 7 RDKit physicochemical descriptors (263 total) for
LR/RF; molecular graphs for GEM.

**Metrics.** Dual regression–classification with activity cutoff **pGI50 > 6 (GI50 = 1 µM)**.
Primary = **hit rate** = TP/(TP+FP). Secondary = MCC. They argue explicitly that ROC AUC — the
MoleculeNet primary — "is a suboptimal metric for VS, as it does not focus on the
early-recognition performance."

**The model-selection inversion (§3.2–3.4, lines 292–361).** This is the payload.
- Under scaffold split on IGROV1: GEM has the **best MCC and ROC AUC** but the **lowest hit
  rate**; RF would be selected. GEM's scaffold-split ROC AUC on IGROV1 is **0.628**, versus its
  MoleculeNet scaffold-split scores of **0.806 (HIV), 0.856 (BACE), 0.724 (BBBP)** — i.e., the
  MoleculeNet benchmarks are far easier than a realistic one.
- Under UMAP split: LR and RF hit rate collapses from **~80% to 0%**; GEM is the only model with
  a non-zero hit rate (**11.9%**).
- Across all 60 datasets: with scaffold split (and with Butina split) RF has the higher median
  hit rate → you would pick RF. With UMAP split, **GEM strongly outperforms RF** in median hit
  rate and median MCC. "**Note that both splits, scaffold and Butina, mislead model
  selection.**"
- Butina is "substantially easier" than UMAP, consistent with its lower clustering quality.
- Under UMAP, RF is "indistinguishable from LR, with both median performances being at a random
  level."
- Statistical backing: differences "highly significant... with strong effect size differences
  too," p-value legend down to p ≤ 1e−4, each boxplot = 5 × 7 × 60 = 2,100 evaluations.

**Discussion (lines 376–431).** "The most ambitious objective of VS is not merely to identify
active molecules with unseen scaffolds, but to discover those with **dissimilar** scaffolds."
Generalization to other tasks: "As scaffold-split data introduces strong training-test
similarities **regardless of the label to predict**, we also expect this split to overestimate
model performance in molecular property prediction problems other than VS." Scale argument:
make-on-demand libraries can exceed **10²⁰** molecules, and "over **97%** of the Bemis–Murcko
scaffolds in make-on-demand libraries were already unavailable from in-stock libraries four
years ago." Closing: "it is urgent to stop the misleading practice of using the scaffold split
to evaluate molecular property prediction models."

---

## 4. Classification: these are METHOD/EVALUATION-PROTOCOL papers, not agent benchmarks

Neither is an agentic benchmark. Both are **evaluation-protocol critiques** with an
accompanying splitter. Filling the METHOD/TOOL template:

### What it does
- **P1 structural-frontier split**: a deterministic, label-free allocation of *existing*
  Bemis–Murcko scaffold groups to train/val/test by a sparsity-and-remoteness score q_s
  (Eq. 1), holding split ratio and grouping units fixed against a matched scaffold control.
- **P2 UMAP-cluster split**: cluster molecules in UMAP-reduced Morgan-fingerprint space, hold
  out whole clusters.
- Both are **drop-in replacements for a line of splitting code** — cheap to run, and that is
  precisely why their neglect is inexcusable.

### Measured effect size / "failure rate" they induce
- P1: median **+87.0%** primary error, mean **+130.3%**, vs an otherwise identical scaffold
  control. Survives capacity increase (**+82.8%** under a 304K-param GNN). Exceeds DataSAIL
  (**96.0%**) and Lo-Hi (**54.1%**).
- P2: hit rate **~80% → 0%** for LR/RF; GEM **11.9%**. Model *ranking* flips.

### Known failure modes
- Scaffold split fails because near-identical scaffolds (benzene/pyridine) legally straddle the
  boundary (P2 §3.1).
- Butina clustering split is "substantially easier" than UMAP and **also misleads model
  selection** (P2 §3.4) — so "not-random" is not the same as "hard."
- Lo-Hi's MIP is **infeasible for PPBR** and returns a **smaller realized test fraction (0.14
  vs 0.20)**, which confounds difficulty with test size unless you match (P1 §0.4).
- DataSAIL leaves PPBR **easier** than the matched control (−7.6%) — a "hard split" can be
  *easier* on some endpoints.
- A label-free split still **induces label shift** (BBB 86.0% → 48.1% positive). If you don't
  check, you'll mistake shift for drift.
- Robust-training objectives (V-REx, worst-group, CVaR, MV-FREX) **all have CIs containing
  zero**. "An environment penalty protects the environments it can see, not unseen chemistry."
- Conformal prediction's marginal coverage assumes exchangeability, which the frontier
  **deliberately breaks**.

### What a naive user gets wrong
1. Believing "I used a scaffold split, so my number is a generalization estimate." It is not —
   P2 shows the constraint is satisfiable with near-duplicates across the boundary.
2. Comparing a hard split against an **unmatched** scaffold baseline, so the "difficulty" is
   partly a test-size or grouping-granularity artifact. P1's whole design is the fix.
3. Reporting a skewed mean over few endpoints. P1's mean is 130.3% but **one endpoint (BBB)
   drags it**; median is 87.0%, BBB-excluded mean is 75.9%.
4. Reading a sub-chance AUROC as "class imbalance." AUROC is prevalence-invariant; sub-chance
   means the ordering is inverted.
5. Optimizing ROC AUC when the deployment decision is a top-k selection — P2 shows the
   AUC-best model (GEM) is the hit-rate-worst model under scaffold split.
6. Treating a database's computed columns (CMNPD's Pipeline Pilot ADMET fields) as experimental
   ground truth, which silently converts evaluation into teacher distillation.
7. Assuming one fingerprint defines novelty. Inter-view Spearman averages **0.321**; ECFP says
   0% of CMNPD is beyond training range while physchem says up to 80%.

### Inputs / outputs
- Inputs: SMILES + a measured endpoint; RDKit descriptors; a grouping unit (Murcko scaffold,
  with an explicit rule for the empty/acyclic scaffold); a split ratio; seeds.
- Outputs: split manifests, per-run predictions, checkpoints, metric records. P1 emits **120
  split manifests** and **5,616 metric records** for 468 runs — the artifact set is the
  deliverable, not the headline number.

---

## 5. Limitations

### Admitted (P1, "Limitations," lines 457–466 — five stated boundaries)
1. The frontier is "a controlled descriptor-space stress test, **not a timestamped prospective
   campaign**, and its outer tail shifts label prevalence."
2. The descriptive bootstrap "resamples only **six endpoint units** and captures algorithmic
   stability rather than laboratory sampling error," so the six-endpoint mean must always be
   read beside median and leave-one-out range.
3. The capacity control spans only four binary tasks and only the ERM/MV-FREX contrast — it
   does not rank regression endpoints, large pretrained encoders, or the other three penalties.
4. The external comparison "inherits each splitter's native behaviour," including Lo-Hi's
   smaller realized test fraction and PPBR infeasibility.
5. CMNPD fields are computational, mappings approximate, coverage collapses at the frontier —
   "that analysis cannot speak to biological accuracy."

Additional admissions scattered in-text: physchem view is partly aligned with the split axis;
Eq. 4 is a regularizer not a certificate; Proposition 1's bound is "non-vacuous but loose"
(0.035–0.202); DILI graph-network row is one seed; the penalty nulls "do not establish
equivalence."

### Unadmitted / weakly admitted
- **P1**: the entire study is one MLP architecture plus one GNN. There is no comparison against
  a strong tabular baseline (gradient boosting on descriptors), which is the actual
  state-of-the-art on most TDC ADMET leaderboards — so "the gap survives higher capacity" is
  demonstrated over a narrow model family.
- **P1**: five seeds vary split tie-breaking, init, dropout and batch order **jointly**, so
  variance components are not separable; the reported SDs conflate them.
- **P1**: the frontier is defined by a score built from the same RDKit descriptor family used
  for one of the four evaluation views; it is acknowledged but not quantified as a bound on the
  effect.
- **P1**: TDC dataset sizes are small (DILI = 475, HIA = 577). A 20% frontier test set of DILI
  is ~95 molecules; the AUROC SDs (±0.029) look implausibly tight for that n, and the bootstrap
  is explicitly *not* a sampling-error estimate.
- **P2**: uses **scikit-learn defaults** for RF and 20 epochs of GEM fine-tuning with default
  hyperparameters, justified as "to ensure that the model could be easily compared." Under a
  distribution shift, default hyperparameters are not a neutral choice — the hit-rate collapse
  to 0% could partly be a threshold/calibration artifact of an unturned regressor near the
  pGI50 = 6 cutoff. Not discussed.
- **P2**: hit rate at a fixed cutoff with no top-k or enrichment-factor curve; a hit rate of
  exactly 0% means the model predicted *no* positives, which is a calibration statement as much
  as a ranking one. Not disentangled.
- **P2**: UMAP is stochastic and hyperparameter-sensitive; the paper inherits a clustering from
  a prior study and does not test sensitivity to UMAP settings.
- **P2**: the claim "UMAP split simulates better this real-world situation" is asserted from
  clustering quality, not validated against any prospective outcome.

---

## 6. Implications for MarigoldBench

**(1) The single best planted-defect family in all of cheminformatics is "constraint satisfied,
leakage not prevented."** Give the model a dataset and a `scaffold_split()` that is *correctly
implemented* — no shared Bemis–Murcko scaffold between train and test, verifiable by assertion
— and a headline AUROC of 0.88. The defect is that benzene-scaffold molecules are in test while
pyridine-scaffold near-duplicates are in train (P2 §3.1). A model that runs
`assert set(train_scaffolds) & set(test_scaffolds) == set()` and reports "split is clean" fails.
The harness recomputes the **max nearest-neighbour Tanimoto from each test molecule to the
training set** and fails the episode if the median exceeds a threshold. This is a defect that
passes the obvious check and fails the right one — exactly the asymmetry a non-compensatory
score needs. Concretely: a TDC endpoint where >75% of test molecules have a training neighbour
at Tanimoto > 0.4 despite a valid scaffold split.

**(2) Verify by recomputing the counterfactual split, not by re-reading the model's number.**
P1's central design is the *matched control*: same ratio (70/10/20), same grouping units, only
the allocation rule changes, so "the excess error it exposes is attributable to **where**
molecules are held out, not to how many." Port this directly into VEC. When a model submits
"my model achieves AUROC X under a hard split," the harness re-runs the submitted checkpoint
against a harness-generated frontier/UMAP split of the same ratio and same grouping units and
checks that the model's claimed degradation is within tolerance of the recomputed one. The
model never gets to choose the comparison baseline. Any task where the agent chooses its own
control is unverifiable.

**(3) Sub-chance-with-a-mechanism is the gold standard for a sound statistical check, and it
is a template for planted defects.** P1's BBB result is verified four independent ways before
being believed: (a) five seeds share an *identical* 389-molecule test set; (b) a
compound-and-seed bootstrap gives 0.352–0.467 with only **0.155%** of resamples reaching
chance; (c) AUROC is argued to be prevalence-invariant and then **exact prevalence reweighting
is run anyway**, leaving 0.409 unchanged; (d) the mechanism is localized by stratified
decomposition — within-stratum 0.563, cross-stratum 0.384. Build MarigoldBench checks this way:
a claim is verified only when the harness has (i) a fixed-artifact replicate, (ii) a resampling
interval, (iii) an explicit confound ruled out by direct recomputation rather than argument,
and (iv) a decomposition that localizes the effect. Plant defects that pass (i) and (ii) but
fail (iii) — e.g. a "signal" that vanishes under prevalence standardization. This is the
Simpson's-paradox trap: a model that reports the pooled statistic without stratifying is
correct-looking and wrong.

**(4) Plant "hard split that is actually easier," and score refusal to over-claim.** DataSAIL
leaves PPBR **−7.6%** easier than the matched scaffold control, and Butina "also misleads model
selection." Construct a flawed-premise condition: "We switched to DataSAIL for a harder
evaluation — confirm the model degrades." On the planted endpoint it does not degrade. The
correct behaviour is to report the negative and refuse the premise, not to hunt for a metric
that shows degradation. Similarly, Lo-Hi's MIP is **infeasible for PPBR at any feasible
fraction** — plant an infeasible-solver task and score whether the agent reports `n/a` honestly
versus silently loosening the constraint until something returns. Silent constraint relaxation
is the highest-value agentic failure mode to catch, because it is invisible in the final
artifact unless the harness logs the solver's realized parameters. Require the agent to emit a
**split manifest** (P1 emits 120) and recompute the realized test fraction from it: Lo-Hi's
0.14 vs the requested 0.20 is machine-checkable.

**(5) Make "which metric" a first-class scored decision, because it flips the answer.** P2 is a
clean model-selection inversion: GEM wins on ROC AUC and MCC, loses on hit rate under the
scaffold split, then wins on everything under UMAP. Task family: give the agent three trained
models and a stated deployment objective ("we will synthesize the top 200 compounds"), and
score whether it selects on an early-recognition metric (hit rate / EF / BEDROC) rather than
ROC AUC. The sound-control version has the AUC-best model also be the hit-rate-best model, and
a false alarm ("your metric is wrong") is penalized. This is a genuinely hard tool-use task
because both metrics are computable in one RDKit/sklearn call — the difficulty is entirely in
knowing which recomputation is the decision-relevant one, which is exactly the skill
MarigoldBench claims to measure.

**(6) Plant predicted-labels-as-ground-truth, and make the identifiability argument the
scored artifact.** P1: CMNPD's six ADMET fields are BIOVIA Pipeline Pilot outputs; treating
them as truth "would turn evaluation into distillation of a legacy teacher," and a drift claim
becomes **unidentifiable** — if Ỹ = h(X), a change in P(X) or P(Ỹ) does not establish a change
in the conditional mechanism. Build a task where the agent is handed a database whose label
column is computational (this is trivially realistic: ADMET-AI, ADMETlab, Pipeline Pilot, and
most public "annotated" natural-product sets). The verified completion is that the agent
detects the provenance from the metadata, refuses the accuracy claim, and reports **agreement**
instead. Bonus check: the agent should notice **coverage collapse** — the usable teacher
fraction falling 97.4% → 0.73% across novelty quintiles — which makes the far-quintile
statistic (46 compounds, 10 positive) uninterpretable. A model that reports AUROC 0.332 on 46
compounds without flagging n is failing.

**(7) Score negative results as first-class outcomes, with correctly stated nulls.** All four
of P1's robust objectives have CIs containing zero, and the paper writes: "These controls do
not support the motivating hypothesis... **they do not establish equivalence.**" Many
MarigoldBench episodes should have no effect to find. The sound control is "run the four
objectives and report honestly"; the failure is fabricating a win from 16/14 wins/losses, and
the *subtle* failure is over-claiming equivalence from a null. Score the wording of the
conclusion, not just the number. This directly serves the 5–40% target band: frontier models
are strongly biased toward reporting a positive finding, and a benchmark where ~30% of episodes
have no effect will separate models sharply.

**(8) Force multi-view / multi-representation robustness checks and penalize single-view
conclusions.** Inter-view novelty Spearman averages **0.321** (ECFP–physchem **0.198**), and
under ECFP **0%** of CMNPD is beyond max training novelty while under physchem up to **80%**
is. A single fingerprint family "can hide a failure that another exposes." Task: "is this
compound set in-domain for the model?" — verifiable answer is representation-dependent, so the
scored artifact must be a per-view table plus an explicit statement that the views disagree. A
confident single-number applicability-domain answer is a scored failure even when it is the
same number the harness computes under that view.

**(9) Adopt P1's run-integrity accounting as the harness's own artifact spec.** "468 of 468
primary runs completed, producing 5,616 metric records and 120 split manifests... **zero failed
runs were discarded**," plus "unit tests assert split non-overlap and objective
differentiability," plus "all preprocessing, novelty coordinates, thresholds and early stopping
use no test labels." Every MarigoldBench episode should require a machine-readable run ledger
with attempted-vs-completed counts, and the harness should fail any submission where
attempted ≠ completed + explicitly-reported-failures. Silent dropping of failed runs is the
most common and most invisible form of agentic self-report inflation, and it is cheaply
detectable from a ledger. Also require an explicit test-label-touch audit: any preprocessing
statistic (scaler medians, MAD, bin thresholds, early-stopping criterion) fitted on anything but
train is an automatic fail — P1 fits medians and MADs on training molecules and **freezes
thresholds** for held-out data.

**(10) Report skew-robust summaries and leverage diagnostics, and plant a leverage trap.**
P1's mean is 130.3% but BBB alone drags it; median 87.0%, BBB-excluded mean 75.9%, every other
leave-one-out between 131.8% and 148.4%. Design a task family whose aggregate is dominated by
one unit and score whether the agent runs leave-one-out and reports median beside mean. Because
MarigoldBench itself aggregates over ~100 task families with template-clustered CIs, this is
also a directive for the benchmark's own reporting: publish the median family effect, the
leave-one-family-out range, and be explicit (as P1 is) that a bootstrap over task units measures
**task/seed stability, not sampling error over the universe of possible tasks**. Do not let the
benchmark commit the error it is testing for.

**(11) Small-n honesty as a scored behaviour.** DILI has 475 molecules total; a 20% frontier
test set is ~95, and P1's graph-network DILI row is a **single seed** and is explicitly labelled
descriptive. Plant tasks where the requested analysis is underpowered and the correct answer is
"this endpoint cannot support the claim at this n." The harness can recompute the achievable
CI width exactly, so this is a fully verifiable refusal task — and refusal tasks that are
*arithmetically* checkable are the most defensible members of the flawed-premise condition.

**(12) Cost note.** Both studies are cheap: P1's 468 runs are a 64-unit MLP plus a 304K-param
GNN over datasets of 475–12,888 molecules; P2's 2,100 models per algorithm are LR/RF on 263
features plus a fine-tuned GEM. Everything here is reproducible with local RDKit + scikit-learn
+ PyTorch inside an 8–25 tool-call budget — no NIM calls required. Split-and-evaluation task
families are therefore the **cheapest high-difficulty families** available to MarigoldBench, and
should be over-represented relative to structure-prediction families that burn wall-clock on
ESMFold/Boltz-2. Neither paper reports monetary cost or runtime, so budget from first
principles.

---

## 7. Verbatim quotes

1. **(P2, Abstract)** "However, here we show that the scaffold split also overestimates VS
   performance. The reason is that molecules with different chemical scaffolds are often
   similar, which hence introduces unrealistically high similarities between training molecules
   and test molecules following a scaffold split."

2. **(P2, §3.1 "Limitations of scaffold split to generate realistic VS benchmarks")** "The
   scaffold split ensures that the test set only contains molecules with unseen scaffolds. That
   is, there are no training molecules with any of the scaffolds in the test molecules. What has
   not been noted yet is that scaffolds are often similar and can be almost identical. Take, for
   instance, the 48,416 molecules tested on the IGROV1 cell line by the NCI-60. The two most
   frequent scaffolds in these molecules are benzene and pyridine (Fig. 1A), which are almost
   identical."

3. **(P2, §3.4 "These results are robust across the 60 datasets")** "Note that both splits,
   scaffold and Butina, mislead model selection. The results with either of these splits would
   have led to the incorrect conclusion that RF was the optimal model based on the hit rate
   performance. However, UMAP split results show that the GEM model is a more suitable choice."

4. **(P1, §0.2 "The BBB effect is a ranking inversion, not a prevalence artifact")** "AUROC is a
   rank statistic and is invariant to class prevalence, so this sub-chance value is a genuine
   *ranking inversion*: the model orders frontier molecules opposite to their labels, and the
   prevalence shift above cannot arithmetically produce it. Exact class-prevalence reweighting
   confirms this: the standardized AUROC is unchanged at 0.409, while the prevalence-sensitive
   metrics move as expected."

5. **(P1, Discussion, "Why the tested robust objectives do not help")** "an environment penalty
   protects the environments it can see, not unseen chemistry. The practical reading is that
   robustness at the frontier is a data-support problem before it is an objective-design
   problem."

6. **(P1, Discussion, "Placing the structural frontier among existing OOD splits")** "because it
   reuses the matched split's ratio and acyclic group units, the excess error it exposes is
   attributable to *where* molecules are held out, not to how many."

7. **(P1, Introduction / "Measured versus predicted labels")** "Treating these fields as
   biological ground truth would turn evaluation into distillation of a legacy teacher. It would
   also make a claim of concept drift unidentifiable: if the observed target is Ỹ = h(X), a
   change in P(X) or in the marginal P(Ỹ) does not establish a change in the conditional
   mechanism."

8. **(P1, Computational Methods, "Statistics and integrity")** "In total, 468 of 468 primary
   runs completed, producing 5,616 metric records and 120 split manifests, and all 46
   graph-network control runs completed as well; zero failed runs were discarded. All
   preprocessing, novelty coordinates, thresholds and early stopping use no test labels. Unit
   tests assert split non-overlap and objective differentiability."

9. **(P1, Conclusion)** "scaffold generalization is not sufficient evidence of frontier
   robustness, and predicted database annotations are not substitutes for experimental
   validation."

10. **(P2, Discussion and Conclusion)** "As scaffold-split data introduces strong training-test
    similarities regardless of the label to predict, we also expect this split to overestimate
    model performance in molecular property prediction problems other than VS. ... With fast
    growing chemical diversity, it is urgent to stop the misleading practice of using the
    scaffold split to evaluate molecular property prediction models."
