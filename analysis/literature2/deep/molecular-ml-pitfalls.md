# Deep read: molecular-ml-pitfalls

## 0. Identity correction (IMPORTANT)

The assigned arXiv id **2202.05146 is NOT the requested paper**. Page 1 of that PDF reads:

> "EQUI BIND: Geometric Deep Learning for Drug Binding Structure Prediction — Hannes Stärk*, Octavian-Eugen Ganea*, Lagnajit Pattanaik, Regina Barzilay, Tommi Jaakkola (MIT). Proceedings of the 39th ICML, PMLR 162, 2022."

That is EquiBind (blind docking), not a pitfalls paper. It was downloaded and extracted for verification only
(`A:/PERTURB-Bench/analysis/literature2/pdfs/2202.05146.pdf`, 19 pages, 67,048 chars →
`A:/PERTURB-Bench/analysis/literature2/md/2202.05146.md`), then set aside.

A paper with the exact title *"Pitfalls in machine learning for molecular property prediction"* **does not exist on
arXiv.** I verified this against the arXiv API with the following queries, all of which returned either nothing or
unrelated hits:

- `ti:"pitfalls" AND ti:"molecular"` → 3 hits, none on property prediction (charge transfer, MD hybrid schemes, coarse-grained MLPs)
- `ti:"Pitfalls in machine learning"` → 3 hits, all generic ML
- `ti:"pitfall" AND cat:physics.chem-ph` → 6 hits, closest is reaction prediction
- `abs:"molecular property prediction" AND ti:"pitfalls"` → 0 hits
- `ti:"pitfalls"` sorted by date, 60 most recent → no molecular property prediction paper
- Two WebSearch passes on the exact quoted title → no matching paper

**Substitute selected (topic match):** arXiv **2604.16586**, the only arXiv paper that carries *molecular property
prediction* in the title AND devotes dedicated sections (6.1, 6.2, 6.3, 8.2) to the pitfalls in question — data
curation defects, split-induced leakage, metric inflation, single-seed reporting, and absent statistical inference.
Runner-up candidates considered and rejected on topic drift: 2406.00873 (*Scaffold Splits Overestimate Virtual
Screening Performance*, too narrow, and is in fact ref 49/50 **inside** the chosen paper), 2312.09004 (reaction
prediction), 2606.19624 (MS/MS molecule discovery).

## 1. Coverage ledger

| Item | Value |
|---|---|
| PDF | `A:/PERTURB-Bench/analysis/literature2/pdfs/2604.16586.pdf` (1,322,345 bytes, `%PDF-1.7`) |
| MD | `A:/PERTURB-Bench/analysis/literature2/md/2604.16586.md` |
| Pages | 32 |
| Total chars | 138,016 |
| Total lines | 1,642 |
| Chars read | 138,016 (100%) |

Chunk ranges read with the Read tool, sequential, no gaps:

| # | Lines | Content |
|---|---|---|
| pre | 1–80 (of the wrong 2202.05146 md) | title verification, rejected |
| 1 | 1–560 | title/authors/abstract, §1 Intro, Table 1 (eras), §2 Preliminaries, §2.2 paradigms, §2.3 splits, §2.4 UQ, §3 pipeline + Fig. 2 taxonomy, Table 2 decision matrix, §4.1 1D, §4.2 2D, §4.3 3D |
| 2 | 561–1120 | §4.3 cont., §4.4 images/descriptors, §4.5 multimodal, §5.1–5.4 architectures, §6.1 datasets + MoleculeNet critique, §6.2 splits, §6.3 protocol selection, Table 3 datasets, §6.4 comparative analysis, Tables 4 & 5, §7 applications, §8.1–8.4 challenges, §9 conclusion, refs [1]–[14] |
| 3 | 1121–1642 | refs [15]–[152], Appendix A (losses), Appendix B (E(3) symmetry), Appendix C + Table 6 (hyperparameters) |

## 2. Actual paper identity (as printed)

- **Title:** "A Systematic Survey and Benchmark of Deep Learning for Molecular Property Prediction in the Foundation Model Era"
- **arXiv:** 2604.16586v1 [cs.LG], 17 Apr 2026
- **Venue (from arXiv comment):** "32 pages. It is just accepted by Journal of Chemical Theory and Computation 2026"
- **Authors:** Zongru Li¹†, Xingsheng Chen¹†, Honggang Wen¹, Regina Qianru Zhang²⁷*, Ming Li³, Xiaojin Zhang⁴, Hongzhi Yin⁵, Qiang Yang⁶, Kwok-Yan Lam²*, Pietro Lio⁷*, Siu-Ming Yiu¹* († equal contribution, * corresponding)
- **Affiliations:** ¹Univ. of Hong Kong; ²Nanyang Technological Univ.; ³Zhejiang Normal Univ.; ⁴HKUST; ⁵Univ. of Queensland; ⁶Hong Kong PolyU; ⁷Univ. of Cambridge
- **Repo:** github.com/Zongru-Li/Survey-and-Benchmarks-of-DL-for-Molecular-Property-Prediction-in-the-Foundation-Model-Era
- **Type:** hybrid — survey of >100 architectures + a small original benchmark (Table 5)

## 3. Section-by-section notes with numbers

### §1 Introduction + Table 1 — four eras
Four "methodological revolutions", explicitly cumulative not replacement-based:
- **Quantum Era (1950–2000):** wavefunction methods, chemical accuracy **~0.1 kcal/mol**, no training data, steep scaling.
- **Descriptor ML (2000–2015):** ECFP-style fingerprints, **~1.5 kcal/mol**, inference **~ms/mol**, low data needs, poor extrapolation to new chemotypes.
- **Geometric DL (2015–2020):** 3D GNNs / SE(3)-equivariance, linear scaling, high data+memory cost.
- **Foundation Models (2020–present):** multimodal pretraining, sub-linear scaling, few-shot transfer.

Review covers **>100 deep architectures**. Three meta-trends claimed: geometric GNNs win on quantum properties;
transformers win on binding affinity and sequence-to-structure; hybrid/quantum-informed designs win on crystalline
and metal–organic systems.

### §2.2 Learning paradigms
Scale marker: **MolE pretrained on M ≈ 842 million molecules** (self-supervised + multi-task).
Practical selection rule stated: supervised suffices when labels exceed **several thousand per task** and domains
overlap; SSL pretraining gives largest gains when downstream labels are **below a few hundred**.

### §2.3 Data splitting methods (the taxonomy that matters for verification)
Six named regimes, increasing stringency:
1. **Random split** (typically 80/20).
2. **Stratified random** — preserves target distribution.
3. **Scaffold split** — Bemis–Murcko decomposition; all molecules sharing a scaffold go exclusively to train or test.
4. **Butina clustering** — Morgan/ECFP + Tanimoto threshold; cluster centers = molecules with most neighbors within threshold; whole clusters kept together.
5. **UMAP-based clustering** (Guo et al.) — Morgan fingerprints → 2D UMAP → agglomerative clustering into k groups, each assigned wholly to train or test.
6. **Time/temporal split** — chronological by assay date; e.g. train Jan–Sep, test Oct–Dec.

### §2.4 Uncertainty quantification
Four families after Hirschfeld et al.: **ensemble-based** (init diversity, bootstrap, snapshot, MC dropout; cost scales
linearly with ensemble size), **mean-variance estimation** (single forward pass, variance often miscalibrated),
**distance-based** (Tanimoto or latent Euclidean; "quantify distributional shift rather than prediction error
directly"), **union-based** (NN embedding → GP or RF; **MPNN+RF performed best overall** in Hirschfeld's benchmark).
Plus evidential regression (Normal-Inverse-Gamma), conformal prediction (finite-sample coverage under
exchangeability), Bayesian NNs, GPs (cubic scaling).
Aleatoric vs epistemic split made explicit; aleatoric named as irreducible even with infinite data, with the two
concrete examples being **heterogeneous assay conditions for binding affinity** and **approximate exchange-correlation
functionals in DFT-derived labels**.

### §3.3 Operational decision framework (Table 2)
| Constraint | Recommended | Trade-off |
|---|---|---|
| Low compute / low data | Descriptor ML (RF/XGBoost + ECFP, N-Gram) | ~ms/mol, interpretable, poor extrapolation |
| 3D-sensitive (quantum, docking) | Geometric GNNs (DimeNet++, SphereNet, EGNN) | needs conformer generation |
| Scarce labels / high OOD risk | Foundation models (MolE, Uni-Mol, ChemBERTa, GEM) | pretraining cost, low interpretability |
| First-principles rigor (~0.1 kcal/mol) | Quantum / quantum hybrid (DFT, neural wavefunctions, PennyLane) | steep scaling |

Distance-only models (SchNet) suffice for radially dominated properties; **directional models (DimeNet, SphereNet)
required for torsion-sensitive tasks**. Rankings declared unstable across protocols.

### §4 Representations
- **SMILES:** not canonical by default (same molecule → many strings depending on traversal order); arbitrary strings need not be valid molecules. Mitigations: canonical SMILES, randomized-SMILES augmentation.
- **SELFIES:** every string is a valid molecule by construction (context-free grammar enforcing valency); longer strings; SELFormer reported comparable/superior to ChemBERTa on ESOL and SIDER.
- **2D graphs:** message passing eq. (1); ignore conformational variability and long-range spatial effects.
- **3D:** grid (voxel, memory-heavy, sparse) vs coordinate-based; **E(3) invariance is the stated physical requirement** for scalar properties.
- **Multimodal:** "requires all modalities to be available at inference"; "careful regularization and interpretability analyses are needed to ensure that improvements stem from complementary information rather than redundancy."

### §5 Architectures — headline numbers
- **DimeNet** outperforms previous GNNs on average by **76% on MD17** and **31% on QM9**.
- **Graphormer**: **>10 percentage-point** reduction in relative error vs most mainstream GNN variants on OGB-LSC.
- **GPS++**: competitive single-model accuracy on PCQM4Mv2 with substantially fewer parameters; ensemble took **1st place in OGB-LSC 2022**.
- Quantum-hybrid (Fourier neural operators, orbital networks): **<0.1 kcal/mol** but need specialized optimization to keep self-consistent convergence.
- SE(3)-equivariant nets **computationally prohibitive beyond ~100 atoms** (§8.1).

### §6.1 Benchmark datasets and the MoleculeNet indictment (core pitfalls content)
MoleculeNet = **16 datasets, 4 categories**. Four documented defects (attributed to Walters, ref 129):
1. **Curation defects:** invalid SMILES, inconsistent standardization, pervasive undefined stereochemistry. **71% of molecules in BACE contain at least one undefined stereocenter** — "making it unclear what chemical entity is actually being modeled."
2. **Heterogeneous assay aggregation:** BACE compiled from **55 separate papers**; combining IC50 values across protocols "introduces substantial noise that may exceed the signal one hopes to model."
3. **Endpoint unsuitability / dynamic-range inflation:** ESOL spans **>13 log units** vs the **2–3 log** range in pharmaceutical practice, inflating apparent performance; BBBP and clinical toxicity are multifactorial and reduced to binary labels from heterogeneous sources.
4. **Assay artifacts:** in HIV, **70% of confirmed actives trigger structural alerts**.

Table 3 sizes (compounds / tasks / recommended split / metric): QM7 7,165; QM7b 7,211 (14 tasks); QM8 21,786 (12);
QM9 133,885 (12); ESOL 1,128; FreeSolv 643; Lipophilicity 4,200; BBBP 2,053 (scaffold, ROC-AUC); Tox21 8,014 (12);
ToxCast 8,615 (**617 tasks**); ClinTox 1,491 (2); SIDER 1,427 (27); BACE 1,522 (scaffold); HIV 41,913 (scaffold);
PCBA 439,863 (128, PRC-AUC); MUV 93,127 (17, PRC-AUC); PDBbind 11,908 (time, RMSE).
ADME (Fang et al. 130), all time-split, all Pearson R: HLM 3,087; RLM 3,054; MDR1-MDCK ER 2,642; Solubility (pH 6.8)
2,173; hPPB 1,808; rPPB 885.

### §6.2 Splitting strategies — the leakage argument and its counter-argument
- Random splitting → "highly similar molecules appearing in both training and test sets, leading to overly optimistic performance estimates."
- Scaffold splitting mitigates only partly: **"structurally similar molecules may possess distinct scaffolds, allowing near-trivial predictions to leak into the test set."**
- **Guo et al. evidence:** systematic study across **60 NCI-60 cancer cell line datasets** (each ~30,000–50,000 molecules); scaffold splits significantly overestimate VS performance vs UMAP splits; model selection on scaffold-split results can produce suboptimal prospective outcomes.
- **Counter-pressure (Sheridan, ref 51):** splits yielding greater train–test dissimilarity produce **overly pessimistic** estimates; **time-split CV produces the most realistic estimate of prospective prediction**.
- **Counter-pressure (Walters, ref 52) against UMAP splits:** (a) the projection captures only a portion of the structural similarity present; (b) agglomerative clustering "often produces highly imbalanced cluster sizes, which may artificially increase the variability of the evaluation metrics."
- Net position: **time-based splits are the gold standard, but most public benchmarks lack the necessary timestamps.**

### §6.3 Protocol selection (the statistics recipe — most directly reusable for MarigoldBench)
Following Ash et al. (2025, JCIM 65(18):9398–9411):
- Diagnosis: a **"replicability gap"** — single mean score, no hypothesis testing, on datasets that are small (**≤10⁴**), imbalanced and noisy.
- **5×5 repeated cross-validation** as the default for datasets of **500–100,000 molecules**, producing **25 per-fold samples**.
- Rejected alternatives: vanilla 10-fold CV, repeated random sampling, and bootstrapping — all "exhibit elevated false positive rates or strong inter-sample dependence in simulation."
- **The same splits must be applied to all methods**, enabling paired testing.
- Group-structured splits via GroupKFold, "provided groups are non-overlapping and roughly balanced."
- **Temporal splits require chronology-preserving protocols**; discretizing time into arbitrary groups destroys the prospective realism.
- Hyperparameter tuning: split each outer-training fold into train/val, avoiding full nested CV.
- Testing: **repeated-measures ANOVA + Tukey's HSD** (reduces to paired t-test for two methods); **Bonferroni at the ANOVA stage** when multiple metrics are assessed.
- **Statistical significance ≠ practical utility.** Concrete number: on ESOL, **R² drops from 0.68 to 0.33 over a realistic 3-log subrange.**
- Decision-aligned metrics: **recall@precision, TNR@recall**.
- Bound the result: **lower bound from null models, upper bound from experimental variability.**
- Report **simultaneous confidence interval plots or MCSim plots**, not single-value leaderboards.

### §6.4 Comparative analysis — the paper's own empirical result
Table 4 (MoleculeNet, scaffold split, ROC-AUC, **taken from Li et al. ref 134, not run by the authors**):
KA-GCN and KA-GAT claim top position on **6 of 7** datasets. Selected values —
KA-GCN: BBBP 0.787±0.014, Tox21 0.799±0.005, ClinTox 0.992±0.005, SIDER 0.842±0.001, BACE 0.890±0.014, HIV
0.821±0.005, MUV 0.834±0.009. KA-GAT: Tox21 0.800±0.006, SIDER 0.847±0.002, HIV 0.823±0.002.
Baselines: D-MPNN BBBP 0.710±0.003; AttentiveFP BBBP 0.663±0.018, Tox21 0.781±0.005; Uni-Mol BBBP 0.729±0.006.
"Performance differences across methods are often modest, with many approaches clustering within a few percentage
points of ROC-AUC."

Table 5 (ADME, **time split**, Pearson R, **the authors' own experiments**, 11 models × 6 endpoints):
| Model | HLM | RLM | ER | Solubility | hPPB | rPPB |
|---|---|---|---|---|---|---|
| AttentiveFP | 0.4377 | **0.4694** | 0.3783 | 0.3917 | 0.5843 | 0.4222 |
| N-GramRF | 0.3080 | 0.1429 | 0.3069 | 0.3739 | 0.3621 | 0.2404 |
| N-GramXGB | 0.2194 | 0.1839 | 0.3487 | 0.3448 | 0.3244 | 0.1651 |
| PretrainGNN | 0.3357 | 0.2222 | 0.6413 | 0.5498 | 0.7269 | 0.4867 |
| GraphMVP | 0.3201 | 0.1116 | 0.6107 | 0.4901 | 0.7450 | 0.5180 |
| MolCLR-GCN | 0.1658 | 0.1543 | 0.6227 | 0.3757 | **0.9264** | **0.7714** |
| MolCLR-GIN | 0.1452 | 0.0938 | 0.6192 | 0.3556 | 0.7726 | 0.4187 |
| Mol-GDL | 0.3101 | 0.3065 | 0.6719 | 0.4099 | 0.6771 | 0.6049 |
| GraphKAN | 0.1014 | 0.1220 | 0.6262 | 0.3009 | 0.8794 | 0.3369 |
| KA-GCN | **0.4596** | 0.2324 | 0.6204 | **0.5549** | 0.6458 | 0.6019 |
| KA-GAT | 0.2595 | 0.2775 | **0.7149** | 0.4744 | 0.6760 | 0.6523 |

Two shifts reported: (1) **absolute performance collapses — Pearson R rarely exceeds 0.7**; (2) **rankings invert** —
AttentiveFP, near the bottom on most MoleculeNet tasks, leads RLM and is second on HLM; **four different models claim
the best score across the six endpoints**. Explicit attribution: "The compressed, relatively stable rankings observed
on MoleculeNet under scaffold splitting may partly reflect the data leakage and metric inflation discussed in Sections
6.1 and 6.2."

The rank inversion is even sharper than the paper states: MolCLR-GCN is **worst-but-one on HLM (0.1658)** and **best on
hPPB (0.9264)** — a within-benchmark swing from bottom to top depending only on which endpoint is scored.

### §7 Applications — numbers worth reusing
- **GNoME:** GNN + DFT active learning loop enumerated **2.2 million candidate crystal structures**, identified **~380,000 likely stable**; **hundreds experimentally confirmed**.
- **PFAS transfer + multitask:** average **AUC 0.886** across five hepatic toxicity targets (incl. PPARα, PPARγ).
- **TamGen:** GPT-like model for TB ClpP protease → **seven experimentally validated compounds**.
- **T-ALPHA:** SOTA using **predicted rather than crystal structures** (e.g., AlphaFold), expanding utility where co-crystals are absent.
- "Multitask GNNs leverage shared substructural features, [but] they often degrade under strict scaffold-split evaluations."
- BAMBOO decomposes electrolyte potential energy into semi-local, electrostatic, and dispersion contributions.

### §8 Challenges
**8.1 Architectural:** GNNs struggle with long-range quantum effects, "as reflected in their limited performance on
binding affinity benchmarks such as PDBbind compared to **well-calibrated physics-based scoring functions**";
transformers quadratic; SE(3) nets prohibitive **>100 atoms**; models "still learning approximate mappings rather than
encoding exact quantum mechanical relationships." A **"transparency crisis"** — MolBERT-class models are black boxes,
blocking regulatory adoption. Multimodal fusion "yet to demonstrate consistent improvements."

**8.2 Evaluation and benchmarking shortcomings — four named failure modes:**
1. **Single-split, single-seed reporting** — small differences treated as definitive; rankings unstable due to data scarcity, label noise, class imbalance and training stochasticity.
2. **Split-induced leakage and overly optimistic generalization** — "conclusions must still be scoped to the evaluated split regime."
3. **Insufficient statistical inference** — tests omitted, or tests applied that "ignore correlation across folds/repeats and multiple-comparison issues."
4. **Metric mismatch with decision-making** — ROC-AUC may not reflect early enrichment or low-FPR precision; "regression gains should be interpreted relative to experimental noise"; report **practical** significance/effect sizes.

Plus **unimodality**: benchmarks predict from structure alone. Two counter-intuitive multimodal results cited —
**USNCO-V (Cui et al.): for some weaker models, removing image inputs slightly improved accuracy**; **MaCBench
(Alampara et al.): models did better on the text version of information than the visual version**, with performance
"degrading sharply as the reasoning chain length increases" on isomers and crystal space groups.

Five-point prescription: (i) specify split protocol **and all randomness sources**, (ii) report uncertainty over
repeated evaluations, (iii) statistically sound comparisons, (iv) effect sizes and decision-aligned metrics,
(v) modality-aware evaluation.

**8.3 Practical adoption barriers:** "**Few models undergo rigorous wet-lab validation, and those that do often show
significantly degraded performance in real-world settings.**" Key mechanism for MarigoldBench: **"when the underlying
model cannot represent the relevant physics, uncertainty scores may inherit the same systematic blind spots"** — i.e.
the error bar is correlated with the error, so self-reported confidence is not an independent check. Also: "Strong
average transfer performance does not guarantee that a specific molecule falls within the model's effective
applicability domain." No universally superior UQ method across datasets.

**8.4 Pathways:** physics-aware learning; uncertainty-calibrated foundation models; realistic multimodal benchmark
ecosystems.

### Appendices
- **A:** loss definitions (MSE eq. 3, CE eq. 4, SSL eq. 5, fine-tuning eq. 6, semi-supervised eq. 7).
- **B:** geometric formalism — RBF expansion eq. 8, bond angle eq. 9, dihedral eq. 10, spherical basis eq. 11, **E(3) invariance eq. 12** `f({Qrᵢ+t}) = f({rᵢ}) ∀Q∈O(3), t∈R³`, **E(3) equivariance eq. 13** with Wigner-D matrices, equivariant coordinate update eq. 14 with scalars βᵢⱼ depending only on rotationally invariant inputs.
- **C / Table 6:** unified encoding = **CGCNN atom encoder + 14-dimensional bond encoder for all models**; 2–5 layers; LR **1e-4 to 1e-3**; **batch 128**; **501 epochs**; dropout 0.1–0.5; MEAN/AVG pooling throughout; KA-GAT grid=3, heads=2; GraphKAN grid=5, order=3, hidden 256; MolCLR-GCN hidden 256, MolCLR-GIN hidden 512, both dropout 0.3, LR 5e-4.

## 4. Benchmark facts (it is a survey + a small benchmark)

- **Task count:** Table 4 = 7 MoleculeNet classification tasks (not run by the authors); Table 5 = **6 ADME regression endpoints × 11 models = 66 model-endpoint results**, run by the authors. Table 3 catalogues 17 MoleculeNet-family + 6 ADME datasets.
- **Construction:** MoleculeNet numbers **copied from Li et al. (ref 134)**; ADME data from Fang et al. (ref 130), "consistently measured data on commercially available drug-like compounds across six *in vitro* ADME endpoints."
- **Verification method:** none independent. Table 5 is a single time-split evaluation per endpoint. There is no recomputation of the Table 4 numbers.
- **Scoring:** ROC-AUC (Table 4), Pearson R (Table 5). Compensatory best-per-column bolding; no aggregate.
- **Agent scaffolding:** **none** — this is not an agentic benchmark; models are trained predictors.
- **Uncertainty:** Table 4 carries ±std "computed across multiple independent training runs" (inherited from the source paper). **Table 5 carries no error bars, no seeds, no repeats, and no statistical test.**
- **Contamination handling:** discussed only as *train/test chemical similarity leakage* (§6.2), not as pretraining-corpus contamination. Notably, several Table 4 entries are **pretrained** models (PretrainGNN, GraphMVP, MolCLR, GEM, Uni-Mol, MolE) whose pretraining corpora plausibly overlap the MoleculeNet test molecules; the paper never raises this.
- **Cost per run:** not reported. Only Table 6 hyperparameters (501 epochs, batch 128) and qualitative claims (~ms/mol descriptor inference; ensembles scale linearly).

## 5. Limitations admitted vs unadmitted

**Admitted:**
- MoleculeNet is defective (stereochemistry, assay heterogeneity, dynamic range, assay artifacts).
- Random and scaffold splits leak; UMAP splits have their own projection and cluster-balance problems; time splits are gold standard but timestamps are usually missing.
- Single-split/single-seed reporting and missing statistical tests inflate perceived progress.
- ROC-AUC may not be decision-relevant; regression gains must be read against experimental noise.
- No universally superior UQ method; UQ inherits the base model's physics blind spots.
- Benchmarks are structure-only/unimodal.
- Few models get wet-lab validation and those that do degrade.

**Unadmitted (my read):**
1. **The paper commits the exact pitfall it names.** §8.2 bullet 1 condemns "single-split, single-seed reporting," yet **Table 5 — the authors' own contribution — reports one number per cell with no std, no repeats, no ANOVA, no Tukey HSD**, despite §6.3 prescribing 5×5 repeated CV and paired testing for datasets of exactly this size (885–3,087 molecules, squarely inside the 500–100,000 recommended band). They also acknowledge "Without the rigorous statistical testing advocated by Ash et al., it remains unclear whether many observed pairwise differences reflect genuine methodological improvements" — while presenting bolded winners anyway.
2. **Table 4 is a self-reported leaderboard imported wholesale.** All numbers come from ref 134 (Li et al.), the paper that introduces KA-GCN/KA-GAT — and KA-GCN/KA-GAT win 6 of 7 columns. Reusing an authoring team's own comparison table is precisely the provenance failure the survey warns about, and it is never flagged.
3. **Anomalous Table 4 values go unexamined.** SIDER jumps from 0.57–0.676 for eleven methods to 0.831/0.837/0.842/0.847 for Mol-GDL/GraphKAN/KA-GCN/KA-GAT; ClinTox reaches 0.992±0.005. A 17-point discontinuity on one dataset across a method family is a protocol-difference signature, not an architecture win, and the paper does not interrogate it.
4. **Table 5's hPPB/rPPB column is not sanity-checked.** MolCLR-GCN scores 0.9264 on hPPB while scoring 0.1658 on HLM. A Pearson R of 0.93 under a temporal OOD split, in a table whose own thesis is "PearsonR values rarely exceed 0.7," deserved a leakage check that was not performed.
5. **No null-model floor or experimental-noise ceiling is computed** for Table 5, even though §6.3 recommends exactly that.
6. **Effect sizes and confidence intervals are recommended but never produced** (no MCSim plot, no simultaneous CI plot anywhere in the paper).
7. **Search/inclusion methodology for the ">100 architectures" is never stated** — no databases queried, no date cutoff, no inclusion criteria, no PRISMA-style flow.

## 6. Implications for MarigoldBench

1. **Plant the split-leakage defect as a first-class task family, and verify by recomputing train/test chemical similarity — never by reading the model's claimed split name.** The paper gives the exact ladder to exploit: random → scaffold → Butina → UMAP → temporal. A sound harness check is: take the model's submitted train/test index files, compute the max Tanimoto similarity of each test molecule to the training set on Morgan/ECFP, and gate on the distribution (e.g., reject if the median nearest-neighbor Tanimoto exceeds the threshold implied by the requested split regime). This is cheap, deterministic, and catches a model that says "I used a scaffold split" while the scaffolds are near-duplicates — the documented case where "structurally similar molecules may possess distinct scaffolds, allowing near-trivial predictions to leak into the test set." For the **flawed-premise** condition, ask for a temporal split on a MoleculeNet dataset that has no timestamps: correct behavior is refusal, since "most public benchmarks lack the necessary timestamps."

2. **Make single-seed reporting an automatic failure, and make the recomputed check the 25-sample distribution, not the mean.** Adopt Ash et al.'s 5×5 repeated CV verbatim for any task with 500–100,000 molecules: the harness re-runs the model's submitted pipeline over the harness's own 25 fixed fold assignments and compares distributions, not point estimates. The paper explicitly rejects 10-fold CV, repeated random sampling, and bootstrapping as having "elevated false positive rates or strong inter-sample dependence." Score the model on whether it reported mean±CI and ran a **repeated-measures ANOVA + Tukey HSD** (paired t-test for two methods, Bonferroni at the ANOVA stage across metrics) — this is a machine-checkable artifact requirement, not a judgment call.

3. **Use dynamic-range manipulation as a planted defect with an exact, recomputable ground truth.** The ESOL number is a gift: **R² = 0.68 on the full >13-log range collapses to 0.33 on a realistic 3-log subrange.** Build a task where the model must report solubility model quality; the sound control uses the pharma-realistic 2–3 log window, the planted defect silently hands back the 13-log dataset. The harness recomputes R² on both windows from the submitted predictions and flags any submission whose headline number is only defensible on the inflated range. Same construction works for any endpoint where restricting to the decision-relevant range is the honest move.

4. **Plant chemistry-level data defects that make the artifact meaningless regardless of the statistics — and require the model to detect them before modeling.** Concrete, verifiable seeds from this paper: **71% undefined stereocenters** (recompute with RDKit `FindMolChiralCenters(includeUnassigned=True)` and gate on the fraction), **assay heterogeneity from 55 source papers** (inject a provenance column and check whether the model conditioned on or pooled across it), **70% of actives triggering structural alerts** (recompute PAINS/structural-alert hits with RDKit's filter catalog). A model that trains a beautiful, well-cross-validated model on a dataset where the chemical entity is undefined has failed the episode. These checks are pure RDKit, run in seconds, and are impossible to satisfy by self-report.

5. **Never accept a model's uncertainty estimate as the verification signal — the paper states the exact mechanism by which it is not independent.** "When the underlying model cannot represent the relevant physics, uncertainty scores may inherit the same systematic blind spots." So the harness must recompute calibration externally: hold out a coverage set, check empirical coverage of the model's claimed 90% interval, and require conformal prediction (finite-sample coverage under exchangeability) rather than a bare softmax or MVE variance, which the paper notes "may be miscalibrated without additional post-hoc adjustment." A good task family: model must deliver calibrated intervals on an OOD chemotype; harness recomputes coverage and interval width; passing requires **both** coverage ≥ nominal **and** width below a trivial-baseline width, so the degenerate "make intervals infinitely wide" strategy is non-compensatorily rejected.

6. **Rank instability across evaluation protocols is the single best generator of genuinely hard tool-use tasks.** The paper's own result: under MoleculeNet scaffold splits, rankings compress and KA-GCN/KA-GAT sweep 6/7; under ADME temporal splits, **four different models win six endpoints**, Pearson R "rarely exceeds 0.7," and AttentiveFP goes from near-bottom to first. Build tasks where the model must select a method for a stated deployment context and the only way to be right is to run the deployment-realistic evaluation itself. The **false-alarm-penalized sound control** is the case where the leaderboard-favorite genuinely is best; the **planted defect** is the case where the leaderboard-favorite loses under the temporal split. A model that pattern-matches "use the SOTA from the benchmark table" fails the defect condition; a model that reflexively distrusts every leaderboard fails the control. That asymmetry is exactly what a non-compensatory scorer needs, and it is very hard to fake in 8–25 tool calls.

7. **Bound every submitted score between a recomputed null floor and an experimental-noise ceiling, and reject anything outside.** §6.3 prescribes "a lower bound from null models and an upper bound estimated from experimental variability." Operationally: the harness independently fits a label-shuffled / majority-class / mean-predictor baseline on the same folds, and computes the assay's replicate noise ceiling. Any submitted metric below the null is a broken pipeline; any metric **above** the noise ceiling is proof of leakage. This two-sided sanity gate catches the anomalies this very paper failed to catch (MolCLR-GCN's 0.9264 hPPB Pearson R under a supposedly OOD temporal split), and it requires zero trust in the model's narrative.

8. **Prefer decision-relevant metrics over ROC-AUC in the scoring contract, and state the metric in the task, not in the model's discretion.** The paper: default metrics "may not reflect operational goals (e.g., early enrichment, low-FPR precision)." Specify **recall@precision** or **TNR@recall** in the task statement and have the harness recompute it from the submitted per-compound scores. This closes the common agentic dodge of reporting whichever metric happens to look best, and it makes the check a pure function of the artifact.

9. **Encode physical invariance as a recomputable check for any 3D/structure task in the lab (RFdiffusion, ESMFold, OpenFold2, Boltz-2, DiffDock).** Appendix B eq. 12 is a directly executable test: apply a random `Q ∈ O(3)` and translation `t` to the input coordinates, re-run the tool, and require the scalar prediction to be invariant to numerical tolerance (and vector outputs to transform by `ρ(Q)`). This is a **sound physical check** in exactly the sense MarigoldBench needs — cheap, tool-agnostic, model-blind, and impossible to satisfy by assertion. Corollary planted defect: a pipeline that silently canonicalizes or re-aligns coordinates, hiding a genuine equivariance violation.

10. **Two flawed-premise refusal tasks fall straight out of the paper.** (a) Ask for a torsion-sensitive property (e.g., a conformer-dependent energy) using a **distance-only** model like SchNet — §3.3 says distance-only "suffices for radially dominated properties" while directional models "are preferred for torsion-sensitive tasks," so the correct response is to refuse the specified architecture and justify. (b) Ask for an SE(3)-equivariant treatment of a system well beyond **~100 atoms**, which §8.1 calls "computationally prohibitive" — correct behavior is to refuse or propose a bounded alternative, not to burn the episode budget. Both are verifiable from the submitted plan without running anything.

11. **Do not assume richer inputs make tasks harder or better — measure it.** USNCO-V found that **removing image inputs slightly improved accuracy for some weaker models**, and MaCBench found models **do better on text than on the visually equivalent presentation**. For MarigoldBench this is a design warning: adding structural images or plots to a task may inject noise rather than difficulty. Run an ablation per template (with/without the extra modality) before locking it in, and treat any template where the extra modality *helps by being ignorable* as broken.

12. **Template-cluster the CIs by defect mechanism, not by biological domain.** The paper's evidence that rankings are unstable across protocols but compressed within one protocol implies that tasks sharing a split regime or a metric are strongly correlated, regardless of whether they concern toxicity, solubility, or affinity. Cluster on {split regime × metric × defect type}, otherwise the 100-family CI will be badly anti-conservative.

## 7. Verbatim quotes

1. §6.1, on data curation: *"First, many constituent datasets suffer from data curation issues, including invalid SMILES representations, inconsistent chemical standardization, and pervasive undefined stereochemistry. For example, 71% of molecules in the BACE dataset contain at least one undefined stereocenter, making it unclear what chemical entity is actually being modeled."*

2. §6.2, on leakage through scaffolds: *"Scaffold splitting mitigates this to some extent, but has a well-documented limitation: structurally similar molecules may possess distinct scaffolds, allowing near-trivial predictions to leak into the test set. The systematic evaluation by Guo et al. across 60 NCI-60 cancer cell line datasets demonstrated that scaffold splits significantly overestimate virtual screening performance compared to UMAP-based splits, and that model selection based on scaffold-split results can lead to suboptimal prospective outcomes."*

3. §6.3, on statistical vs practical significance: *"Statistical significance, however, does not ensure practical utility. As discussed in Section 6.1, the ESOL dataset's 13-log dynamic range inflates apparent performance (R2 drops from 0.68 to 0.33 over a realistic 3-log subrange). Decisional impact metrics such as recall@precision or TNR@recall better reflect compound prioritization decisions."*

4. §6.4, on rank instability under a realistic split: *"Under time-based splitting on the ADME benchmark (Table 5), however, two notable shifts emerge. First, absolute performance drops substantially, with PearsonR values rarely exceeding 0.7, reflecting the genuine difficulty of temporally out-of-distribution prediction. Second, relative rankings change markedly: AttentiveFP, which ranks near the bottom on most MoleculeNet tasks, leads on RLM and ranks second on HLM. No single method dominates overall. Four different models claim the best score across the six ADME endpoints."*

5. §8.2, on single-seed reporting: *"Single-split, single-seed reporting. Many studies report a single score (often from one split and one seed) and treat small differences as definitive. In practice, rankings can be unstable due to data scarcity, label noise, class imbalance, and training stochasticity. Robust comparisons should quantify variability via repeated evaluation and report distributions (e.g., mean±std or confidence intervals)."*

6. §8.3, on why self-reported uncertainty is not an independent check: *"These limitations also affect uncertainty estimation: when the underlying model cannot represent the relevant physics, uncertainty scores may inherit the same systematic blind spots. In addition, benchmark studies show that UQ methods perform inconsistently across datasets, with no universally superior approach."*

7. §8.3, on the wet-lab gap: *"Few models undergo rigorous wet-lab validation, and those that do often show significantly degraded performance in real-world settings."*
