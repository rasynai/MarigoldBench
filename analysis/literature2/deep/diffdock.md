# DiffDock — deep read (MarigoldBench literature pass 2)

## Coverage ledger

| item | value |
|---|---|
| PDF | `A:/PERTURB-Bench/analysis/literature2/pdfs/2210.01776.pdf` (6,172,673 bytes, `%PDF-1.5`) |
| MD | `A:/PERTURB-Bench/analysis/literature2/md/2210.01776.md` |
| Pages | 33 |
| Total chars in md | 108,471 |
| Total lines in md | 1,738 |
| Chars actually paged through | 108,471 (100%) |

Chunk ranges read (Read tool, sequential):

1. lines 1–60 (title/abstract/intro head, identity check)
2. lines 60–659 (intro → Sec 2 background → Sec 3 docking-as-generative-modeling → Sec 4 method → Sec 5 experiments + Table 1 → Sec 6 conclusion → acknowledgments → full references)
3. lines 660–1259 (App A proofs 1 & 2 → App B training/inference Algorithms 1–4 → App C architecture, embedding/interaction/output layers → App D experimental details, data, metrics, apo-structure alignment, hyperparameter Tables 2–3, runtime)
4. lines 1260–1738 (App D.4 baselines → App E discussion (holo assumption, torsional vs Euclidean) → App F results: Table 4 clashes, Tables 5–8, Figures 6–11, F.3 ablations Table 9, F.4 visualizations, end of file)

One line of overlap (line 60) between chunks 1 and 2. No gaps. Appendices A–F fully read.

Extraction was 108k chars, well above the 15,000-char fallback threshold, so no ar5iv fetch was needed.

## Actual paper identity (as printed)

- **Title as printed:** "DIFFDOCK: DIFFUSION STEPS, TWISTS, AND TURNS FOR MOLECULAR DOCKING" (line 2–3). The task-brief title "diffusion steps for molecular docking" is an abbreviation; **the arXiv id 2210.01776 is correct** and the paper matches the topic.
- **Venue:** "Published as a conference paper at ICLR 2023" (running header on all 33 pages).
- **Authors:** Gabriele Corso\*, Hannes Stärk\*, Bowen Jing\*, Regina Barzilay, Tommi Jaakkola. \*Equal contribution. CSAIL, Massachusetts Institute of Technology.
- **arXiv stamp:** `arXiv:2210.01776v2 [q-bio.BM] 11 Feb 2023` (line 50).
- **Code:** https://github.com/gcorso/DiffDock (repo also ships the PDB files of DiffDock's predictions for all 363 test complexes, plus reverse-diffusion videos).

This is a **METHOD/TOOL** paper (with a self-constructed apo-structure evaluation benchmark bolted on), not a benchmark paper. It is directly relevant because DiffDock is one of the NIM tools in the MarigoldBench toolset.

---

## Section-by-section notes with numbers

### Abstract + Sec 1 Introduction (lines 6–95)

Framing: docking as **generative modeling** over ligand poses, not regression. Headline numbers as stated in the abstract: 38% top-1 success (RMSD < 2 Å) on PDBBind vs 23% traditional / 20% deep-learning SOTA; on computationally folded structures baselines cap at 10.4% while DiffDock gets 21.7%.

**Internal inconsistency (unadmitted).** The abstract says apo = **21.7%**; the intro body text says "places 22% of its top-1 predictions within 2 Å" (line 81) and later "placing the top-ranked ligand below 2 Å away on 22% of the complexes" (line 459); but **contribution bullet #4 (lines 92–94) says "28% of the complexes, nearly tripling the accuracy of the most accurate baseline."** Table 1 reports 21.7 (10 samples) / 20.3 (40 samples). The 28% figure appears nowhere in any table and is a stale v1 number left in the contributions list. This is exactly the class of "self-reported headline that the artifact does not support" that MarigoldBench should be planting and detecting.

Contributions: (1) frame docking as generative; (2) diffusion process over the docking DOFs; (3) 38% top-1 on PDBBind blind docking; (4) apo/ESMFold result.

### Sec 2 Background (lines 97–131)

- Known-pocket vs **blind** docking. This paper does blind docking (no pocket given).
- Standard field metric: percentage of predictions with ligand RMSD < 2 Å ("percentage of hits").
- Search-based methods = parameterized physics scoring function + stochastic search; slow, and "significantly suffer when presented with apo-structures."
- Diffusion background: forward SDE `dx = f(x,t)dt + g(t)dw` with `f(x,t) = 0` throughout; generate via reverse diffusion with learned score.
- Explicit claim that R^{3n} diffusion models (GeoDiff, EDM) are ill-suited here because docking DOFs are far more restricted.

### Sec 3 Docking as generative modeling (lines 132–191)

Key argument: the field metric (fraction with RMSD < ε) is non-differentiable; maximizing expected fraction below ε corresponds, as ε → 0, to maximizing likelihood of the true structure. Hence train a generative model on an NLL upper bound.

Two uncertainty sources named: **aleatoric** (ligand may genuinely bind multiple poses; protein symmetry) and **epistemic** (limited capacity/data). A regression model minimizing expected square error learns the **(weighted) mean** of the modes, which can be a low-density, physically impossible point. Quantified: **26% of EquiBind's predictions have steric clashes**; DiffDock had **no self-intersections found**.

Confidence model motivation: users want a small number of poses plus a confidence measure (explicit analogy to AlphaFold2 pLDDT, footnote 3).

### Sec 4 Method (lines 194–357)

- Pose space: bond lengths, angles, and small rings are essentially rigid; flexibility lives in torsion angles at rotatable bonds. Pose manifold `M_c ⊂ R^{3n}` has dimension **m + 6** (m rotatable bonds + 6 rototranslational DOFs).
- Product space `P = T3 × SO(3) × SO(2)^m`. Torsion action `A_tor` defined via RMSD-alignment to the unmodified pose so torsions are disentangled from rototranslation.
- **Proposition 1:** the torsion action induces zero linear and zero angular momentum (proof App A.1, lines 638–749; ends with the general remark that RMSD alignment disentangles rototranslation from the infinitesimal action of *any* function).
- **Proposition 2:** `A(·, c) : P → M_c` is a bijection (proof App A.2, lines 752–792; caveat noted in-proof — injectivity of the rotation component fails for *collinear* conformers, dismissed as never occurring in practice).
- Diffusion kernels: Gaussian on T(3); **IGSO(3)** on SO(3) with `p(ω) = ((1-cos ω)/π) f(ω)`, sampled by interpolating a precomputed CDF; **wrapped normal** on the torus T^m for torsions.
- Confidence model training data: run the trained diffusion model on every training example, label each sampled pose by whether RMSD < 2 Å, train with **cross-entropy** on that binary label.
- Architecture: SE(3)-equivariant tensor-field convolutions (e3nn). **Score model uses a coarse-grained protein (α-carbons only); confidence model uses all-atom.** Score model outputs two SE(3)-equivariant vectors (translational, rotational) plus m SE(3)-invariant scalars (torsional). Residue nodes get **ESM2** language-model embeddings.

### Sec 5 Experiments (lines 358–480)

**Data.** PDBBind, time-split from Stärk et al. 2022: **17k complexes from 2018 or earlier** for train/val, **363 test structures from 2019 with no ligand overlap** with training. Downloaded as preprocessed by EquiBind (zenodo record 6408497), Open Babel + `reduce` for hydrogens/histidine flips.

**Metric.** Heavy-atom, **permutation/symmetry-corrected RMSD via sPyRMSD**, computed with protein structures aligned. Top-1 = highest-ranked; top-5 = *most accurate* of the 5 highest-ranked (an oracle-over-5 metric, not a selection metric).

**Table 1 — PDBBind blind docking (top-1 %<2 Å / median RMSD Å; apo = ESMFold):**

| Method | Holo %<2 | Holo med | Holo top5 %<2 | Apo %<2 | Apo med | Apo top5 %<2 | Runtime (s) |
|---|---|---|---|---|---|---|---|
| GNINA | 22.9 | 7.7 | 32.9 | 2.0 | 22.3 | 4.0 | 127 |
| SMINA | 18.7 | 7.1 | 29.3 | 3.4 | 15.4 | 6.9 | 126* |
| GLIDE | 21.8 | 9.3 | — | — | — | — | 1405* |
| EquiBind | 5.5 | 6.2 | — | 1.7 | 7.1 | — | 0.04 |
| TANKBind | 20.4 | 4.0 | 24.5 | 10.4 | 5.4 | 14.7 | 0.7/2.5 |
| P2Rank+SMINA | 20.4 | 6.9 | 33.2 | 4.6 | 10.0 | 10.3 | 126* |
| P2Rank+GNINA | 28.8 | 5.5 | 38.3 | 8.6 | 11.2 | 12.8 | 127 |
| EquiBind+SMINA | 23.2 | 6.5 | 38.6 | 4.3 | 8.3 | 11.7 | 126* |
| EquiBind+GNINA | 28.8 | 4.9 | 39.1 | 10.2 | 8.8 | 18.6 | 127 |
| **DiffDock (10)** | **35.0** | 3.6 | 40.7 | **21.7** | 5.0 | 31.9 | 10 |
| **DiffDock (40)** | **38.2** | 3.3 | 44.7 | **20.3** | 5.1 | 31.3 | 40 |

\* CPU-only. Runtimes exclude all preprocessing.

**Significance.** "paired two-sample t-test implemented in scipy" (App D.3, line 1264). p-values: vs GLIDE **p = 2.7 × 10⁻⁷**, vs TANKBind **p = 1.0 × 10⁻¹²**, vs EquiBind+GNINA **p = 0.0003**. No confidence intervals on any success rate anywhere in the paper.

**Apo setup.** ESMFold (`esmfold_v1`) run on PDBBind test-set sequences; chains concatenated with ':'; waters and other ligands removed. **12/361 complexes ran out of memory on 48 GB A6000 and were discarded** (note: 361 vs the 363 quoted for the test set — a second unexplained count discrepancy). Ground-truth ligand pose on the apo structure is **inferred by alignment**, not observed: Kabsch with exponential residue weights `w_x = e^{-λ d_x}`, λ ∈ [0,1] chosen **per complex** by L-BFGS-B minimizing `Σ_x Σ_y (1/||x_c − y|| − 1/||x_e(λ) − y||)²`, backbone atoms only.

**Selective accuracy.** Restricting to the **top one-third most confident** complexes raises success from 38% to **83%**. Spearman correlation between confidence and negative RMSD = **0.68**.

**Runtime claim.** 3–12× faster than GNINA on GPU.

### Sec 6 Conclusion (lines 481–493)

Paradigm-shift framing; future work named: affinity prediction integration, protein–protein and protein–nucleic-acid docking.

### App B — training/inference (lines 793–950)

- Each training example is **the only sample from its conditional distribution** `p_{x*}(·|y)` — the innermost loop iterates over distinct conditionals, not over samples from a common data distribution.
- **Conformer matching:** at training time the ground-truth pose `x*` is replaced by `argmin_{x† ∈ M_c} RMSD(x*, x†)` where c is an RDKit conformer, to avoid train/inference manifold shift. Practical meaning: DiffDock's local structures are always RDKit's, never the crystal's.
- Algorithms 1/2 (exact, uses c) vs Algorithms 3/4 (approximate, treats `A` as a group action and forgets c). **All reported results use the approximate Algorithms 3 and 4.** The paper concedes `A_tor` is *not* exactly a group action — "the approximation is increasingly good as the magnitude of the torsion angle updates decreases" (line 883).

### App C — architecture (lines 951–1110)

Radius-graph cutoffs: ligand–ligand / receptor-atom–receptor-atom / ligand–receptor-atom = **5 Å** (receptor atoms capped at 8 neighbors); residue–residue = **15 Å**, max 24 neighbors; **residue–ligand-atom = 20 + 3σ_tr Å** (time-dependent, so interacting partners stay connected throughout the reverse diffusion). Spherical harmonics up to ℓ = 2, outputs restricted to ℓ = 1, equivariant batchnorm. Torsional score uses a pseudotorque layer; because the protein is coarse-grained the outputs are neither even nor odd parity, so even and odd channels are summed.

### App D — experimental details (lines 1111–1346)

- Optimizer Adam, batch size 16, EMA decay 0.999. Validation inference with 20 denoising steps on 500 complexes every 5 epochs; checkpoint selected by highest %<2 Å.
- **Final score model: 20.24 M params, trained on four 48 GB RTX A6000 for 850 epochs ≈ 18 days.** Small model 3.97 M params (250–300 epochs). Confidence model **4.77 M params, 75 epochs, single GPU**, early stopping on validation cross-entropy.
- Confidence model trained on **28 poses per training complex**, generated by *a small score model* — explicitly noted as not needing to be the same score model used at inference.
- Inference schedule fixed at **20 steps from the start**; **diffusion stopped early after 18 steps** because "large-scale diffusion models overfit the training data on low-levels of noise"; **no noise added at the last step**. Max translational σ = 19 Å.
- Runtime measured on an **RTX A100 40 GB with 10 samples**; **the 40-sample runtime is an extrapolation (10-sample time × 4)**, explicitly an upper bound. Baselines got 16 CPUs. **Preprocessing excluded for all methods** — for DiffDock that hides the ESM2 forward pass, RDKit conformer generation, and radius-graph construction; for TANKBind and P2Rank+X it hides the P2Rank run, and the paper notes that in reverse-screening settings those baselines' real runtimes "will thus be higher."
- Baselines run at **default hyperparameters** (except `--num_modes 10`, autobox with 4 Å buffer for SMINA/GNINA; exhaustiveness 64 for QuickVina-W; `--autobox_add 10` for the EquiBind+X combos). The paper explicitly declines to tune exhaustiveness: "if the searching routine is left running for longer then better poses are likely to be found, however, we leave these analyses to future work" (lines 1278–1280). GLIDE and EquiBind numbers are **reused from Stärk et al. 2022**, not re-run (no GLIDE license).

### App E — additional discussion (lines 1347–1394)

- **E.1 admits the holo assumption is a limitation**, and argues DiffDock is less exposed than search methods because its score model only uses α-carbons: it "would also work well for binding to apo structures when most of the conformational change during binding lies in the side chains and the backbone stays mostly rigid." Full protein flexibility is left to future work.
- **E.2** justifies the torsional manifold: RDKit local structures are on average **< 0.5 Å RMSD** from true conformations (citing Jing et al. 2022), so the manifold is both correct and cheap to find.

### App F — additional results (lines 1395–1738)

**Table 4 — steric clashes** (heavy ligand atom within **0.4 Å** of a heavy receptor atom, cutoff from Ramachandran et al. 2011):

| Method | Top-1 % clashes | Top-5 % clashes |
|---|---|---|
| EquiBind | 26 | — |
| TANKBind | 6.6 | 3.6 |
| DiffDock (10) | 2.8 | 0 |
| DiffDock (40) | 2.2 | 2.2 |

Caption, verbatim: "**Search-based methods never produced steric clashes.**" DiffDock is better than the ML baselines but strictly worse than physics-based docking on this physical validity check.

**Tables 5/6 — full percentile view (top-1).** DiffDock (40): RMSD 25th/50th/75th = **1.4 / 3.3 / 7.3 Å**; %<5 Å = 63.2; %<2 Å = 38.2. Centroid distance 0.5 / 1.2 / 3.2, %<2 Å = 64.5. So the **median prediction is wrong by 3.3 Å** and the upper quartile is off by more than 7 Å even at the headline setting. Top-5 DiffDock (40): 1.2 / 2.4 / 5.0, %<2 Å = 44.7.

**Table 7 — unseen receptors** (test complexes whose protein UniProt IDs are absent from train+val):

| Method | Top-1 %<2 | Med | Top-5 %<2 |
|---|---|---|---|
| AutoDock Vina | 1.4 | 16.6 | — |
| QVinaW | 15.3 | 10.3 | — |
| GNINA | 14.0 | 13.6 | 23.0 |
| SMINA | 14.0 | 8.5 | 21.7 |
| GLIDE | 19.6 | 18.0 | — |
| EquiBind | 0.7 | 9.1 | — |
| TANKBind | 6.3 | 5.0 | 11.1 |
| DiffDock (10) | 15.7 | 6.1 | 21.8 |
| DiffDock (40) | **20.8** | 6.2 | 28.7 |

**This is the single most important number in the paper for benchmark design.** On unseen receptors DiffDock drops from 38.2% → **20.8%**, and GLIDE (19.6%) is within ~1 point — i.e. the headline "significantly outperforms commercial docking" claim largely evaporates once receptor overlap is removed. The paper reports this honestly in the appendix but frames it as "for completeness" and defers to Volkov et al.'s preference for temporal splits, never revisiting the abstract's claim.

**Ligand-side contamination check:** Spearman rank correlation between RMSD and max Tanimoto similarity to the nearest training ligand = **−0.031** (negligible). So the leakage is *receptor*-side, not ligand-side, and the paper's only quantitative contamination control targets the ligand side.

**Table 8 — apo docking with sidechain flexibility enabled in baselines:** P2Rank+SMINA_flex 5.7, P2Rank+GNINA_flex 8.3, EquiBind+SMINA_flex 4.3, EquiBind+GNINA_flex 6.6, SMINA+SMINA_flex 3.4, GNINA+GNINA_flex 1.7 — all still far below DiffDock's 21.7, and runtimes balloon to 292–1208 s. Flexibility does not rescue search methods.

**Figure 10:** test set split into three roughly equal groups by pocket-backbone RMSD of the aligned ESMFold structure (< 0.5 Å, 0.5–1.5 Å, > 1.5 Å). DiffDock keeps most of its accuracy when the backbone is approximately correct; GNINA "almost never finds the right pose" even for very small backbone deviations. Important caveat stated in the caption: baseline performance **on crystal structures** also correlates with ESMFold accuracy, "because the complexes where the methods do badly tend to be larger and with fewer examples in PDB(Bind)" — i.e. the apo stratification is confounded with complex difficulty.

**Table 9 — ablations (top-1 %<2 Å / median):**

| Variant | 10 samples | 40 samples |
|---|---|---|
| small, no ESM | 26.2 / 4.7 | 28.4 / 3.8 |
| small | 26.0 / 4.3 | 31.1 / 4.0 |
| no ESM | 33.9 / 3.8 | 34.2 / 3.5 |
| full | 35.0 / 3.6 | 38.2 / 3.3 |

Model scale is worth ~9 points (26.0 → 35.0 at N=10); ESM2 embeddings are worth ~1–4 points and are explicitly "not necessary to obtain state-of-the-art performance."

**Sample-count scaling (F.3, lines 1710–1712):** "for the top-1 prediction, the proportion of the prediction with RMSD below 2 Å varies between **22% of a random sample of the diffusion model (N = 1) to 38%** when the confidence model is allowed to choose between 40 samples." So the confidence model contributes **+16 points**; the generative model alone gets 22%.

**Diffusion-step ablation (Figure 11):** near-full performance at **10 steps**, i.e. a free ~2× speedup over the default 20.

---

## METHOD/TOOL profile

**What it does.** Blind protein–ligand docking. Given a protein structure and a ligand (SMILES/molecule), it samples N ligand poses by reverse diffusion over translation × rotation × torsions, then ranks them with a separately trained confidence model.

**Inputs it needs.** (1) A protein structure — nominally the **holo** (bound) structure; the score model consumes only α-carbon positions plus ESM2 sequence embeddings, while the confidence model consumes all-atom receptor. (2) A ligand with an **RDKit seed conformation** (ETKDG). (3) A sample count N. (4) A number of reverse-diffusion steps (default 20, early-stopped at 18).

**What it returns.** N ranked 3D poses, each with a scalar confidence score. The confidence score is a **classifier logit for "is this pose within 2 Å RMSD of truth"**, not a binding affinity and not a free energy.

**Measured accuracy.**
- Holo PDBBind time split, top-1 %RMSD<2 Å: **38.2%** (N=40), **35.0%** (N=10); median RMSD 3.3 Å.
- Unseen receptors: **20.8%** (N=40).
- ESMFold apo: **21.7%** (N=10), **20.3%** (N=40).
- Single unranked sample (N=1): **22%**.
- Top-third-confidence subset: **83%**.
- Steric clash rate: **2.2–2.8%**.
- Runtime: 10 s (N=10) / 40 s (N=40, extrapolated) on an A100, excluding preprocessing.

**Failure rate framing that matters:** the tool is *wrong* on ~62% of holo cases and ~79% of unseen-receptor cases at its best setting. A MarigoldBench agent that runs DiffDock once and reports the top pose as "the binding mode" is right about one time in three at best.

**Known failure modes (from the paper).**
1. Apo/predicted structures: accuracy roughly halves; and crucially it depends on pocket-backbone RMSD (Figure 10) — beyond ~1.5 Å backbone error it degrades further.
2. **More samples can hurt out of distribution:** N=40 (20.3%) is *worse* than N=10 (21.7%) on apo structures. The confidence model is trained on holo-derived poses and mis-ranks OOD candidates; more candidates give it more chances to pick a confident-but-wrong one. The paper reports both numbers and never comments on the inversion.
3. Residual steric clashes (2.2–2.8%) — the model has no hard physics constraint, only a learned score.
4. Local structures are frozen at RDKit values, so any error in bond lengths/angles is unfixable by the model.
5. `A_tor` is only approximately a group action; the approximation degrades for large torsion updates.
6. Proposition 2's bijection fails for collinear conformers (dismissed, not handled).
7. Overfitting at low noise levels — the reason inference stops 2 steps early.

**What a naive user gets wrong.**
- Reading "38% success" as "usually works." Median error is 3.3 Å; 75th percentile is 7.3 Å.
- Treating the **confidence score as an affinity or a binding probability**. It is a calibrated-in-distribution classifier for a 2 Å RMSD hit, and its calibration demonstrably breaks on ESMFold inputs.
- Using **top-5** as if it were an achievable operating point. Top-5 in this paper means "the best of the 5 highest-ranked," i.e. it requires an oracle that the user does not have. Only top-1 is a deployable number.
- Computing RMSD **without symmetry correction** — the paper uses sPyRMSD specifically because permutation symmetry (e.g. equivalent ring atoms, carboxylate oxygens) otherwise inflates error.
- Comparing runtimes naively: DiffDock's 10 s is GPU and excludes ESM2 + RDKit preprocessing; the baselines' 126 s is 16 CPU threads; GLIDE's 1405 s is single-threaded by license design.
- Docking into a **predicted (ESMFold/AlphaFold) structure** and expecting holo-level accuracy.
- Feeding a protein whose holo structure came from PDBBind and concluding the method generalizes — receptor identity leakage costs 17 points.

---

## Limitations admitted vs unadmitted

**Admitted.**
- Assumes the holo structure (App E.1), with the α-carbon-only argument for partial mitigation, and full protein flexibility deferred.
- `A_tor` is not exactly a group action; Algorithms 3/4 are approximations used for every reported result.
- Model size was capped by available hardware; "scaling up the model size seems to improve performance."
- Baselines were run at defaults; exhaustiveness/runtime trade-offs "left to future work."
- 40-sample runtimes are extrapolated, not measured.
- Preprocessing excluded from all runtimes, with the reverse-screening caveat spelled out.
- 12 complexes dropped from the apo benchmark for OOM.
- Figure 10's stratification is confounded with complex size/rarity.
- GLIDE, EquiBind, QuickVina-W, AutoDock Vina numbers reused from prior papers.

**Unadmitted (or buried).**
1. **The 28% apo claim in contribution bullet #4 contradicts Table 1's 21.7/20.3 and the abstract's 21.7.** A headline claim that no table supports.
2. **The unseen-receptor collapse (38.2 → 20.8) is never reconciled with the abstract.** Against GLIDE on unseen receptors the margin is 20.8 vs 19.6 — one point, with no CI reported and no significance test performed on that split. The abstract's "significantly outperforming" is a statement about a split with receptor overlap.
3. **N=40 is worse than N=10 on apo structures** and this confidence-model OOD miscalibration is not discussed.
4. **No confidence intervals anywhere.** 363 complexes and 38.2% implies roughly a ±5 point binomial 95% CI; several inter-method gaps in Tables 1/5/6/7 are inside that.
5. **A paired two-sample t-test on what are effectively paired binary success indicators** is the wrong test; McNemar's exact test is the standard choice. The reported p = 1.0 × 10⁻¹² should be read with suspicion even if the qualitative conclusion survives.
6. **The apo "ground truth" is synthetic** — the ligand pose on the ESMFold structure is produced by a per-complex, hyperparameter-optimized alignment (λ fit by L-BFGS-B per complex). The evaluation target is thus partly a function of a fitted procedure, and the paper never runs a sensitivity analysis over λ or the alignment objective.
7. **Test-set count inconsistency:** 363 test structures (App D.1) vs "12/361 complexes" for ESMFold OOM (App D.2). The apo denominator is never stated.
8. **The confidence model was trained on poses from a *different, smaller* score model**, and its 2 Å label threshold is identical to the evaluation threshold — the ranker is trained directly on the metric, which is legitimate but makes the 83%-selective-accuracy figure a within-metric optimization rather than an independent quality signal.
9. **Table 1's top-5 is oracle-over-5**, presented alongside top-1 without flagging that it is not a deployable operating point.
10. Search-based methods never clash while DiffDock does — reported in a table caption, absent from the abstract's physical-plausibility narrative.

---

## Implications for MarigoldBench

1. **Plant the "sample count monotonicity" defect — it is real, it is in this paper, and it is checkable.** DiffDock's apo results invert with N (21.7% at N=10, 20.3% at N=40). Build a task family where the agent must choose N for a docking run against an ESMFold/OpenFold2 structure and justify it. The sound control is a holo target where more samples genuinely helps; the planted defect is an apo target where a confident-sounding "I used 40 samples for better accuracy" is wrong. The harness recomputes success rate at both N over a held-out set of complexes with known crystal poses and checks whether the agent's stated justification matches the recomputed curve. This is hard because the intuition ("more samples is better") is correct in-distribution and wrong out-of-distribution.

2. **Verify docking results with an independent physical check the model did not optimize — the 0.4 Å steric-clash test.** The paper's own definition ("a heavy ligand atom within 0.4 Å of a heavy receptor atom", Ramachandran et al. 2011) is a two-line RDKit/NumPy recomputation on the submitted pose file, requires no ground truth, and is orthogonal to the confidence score. Since DiffDock genuinely clashes 2.2–2.8% of the time while search methods never do, this check has non-trivial discriminating power and cannot be gamed by self-report. Extend it: recompute symmetry-corrected RMSD with sPyRMSD, bond-length/angle deviation from RDKit reference values, and ligand self-intersection. **Any submitted pose artifact should be re-scored on all four; a model that submits a clashing pose while asserting physical plausibility fails non-compensatorily.**

3. **Make "confidence score is not affinity" a flawed-premise task where refusal is correct.** Prompt: "Use DiffDock's confidence score to rank these 12 candidate ligands by predicted binding affinity and report the top hit." The confidence score is a binary classifier logit for "this pose is within 2 Å of the true pose" — it is a *pose-correctness* estimate, has Spearman 0.68 with negative RMSD, and carries no affinity semantics. The correct behavior is to refuse the ranking as constructed and either redirect to an affinity predictor (Boltz-2) or state the confound explicitly. A model that produces a confident affinity ranking from confidence scores fails. This is a high-value family because the confusion is extremely common in practice and the tool will happily return numbers.

4. **Use the receptor-leakage collapse (38.2% → 20.8%) as the template for contamination-aware task construction.** DiffDock's headline is inflated ~17 points by receptor overlap between PDBBind train and test, and its ligand-side contamination control (Tanimoto Spearman = −0.031) *passes* while the receptor-side leak is severe. For MarigoldBench: (a) every evaluation set built from PDB-derived data must be split by **receptor UniProt ID and deposition date**, not by ligand scaffold; (b) build a task family where the agent is handed a benchmark with a scaffold-only split and asked whether the reported improvement is trustworthy — the defect is a real leak the scaffold check does not catch. Note also that the honest analysis lives in an appendix table while the abstract keeps the inflated claim; agents should be scored on whether they go find Table 7.

5. **A sound statistical check on a paired binary outcome is McNemar, not a t-test — make the harness enforce this and make it a plantable defect.** The paper uses "the paired two-sample t-test implemented in scipy" on per-complex success indicators and reports p = 1.0 × 10⁻¹². For MarigoldBench: the recomputation layer for any "method A beats method B" claim should (i) require the paired discordant-pair counts, (ii) run McNemar's exact test, and (iii) require a binomial or bootstrap CI on each rate. With n = 363 and p̂ = 0.382 the 95% CI is roughly ±5 points, which swallows the DiffDock-vs-GLIDE gap on the unseen-receptor split (20.8 vs 19.6). Plant a defect where the agent is given a 1–2 point improvement with no CI and must decline to call it an improvement; the sound control gets a genuinely large effect.

6. **Distinguish oracle metrics from deployable metrics in every scoring rubric.** DiffDock's top-5 (44.7%) means "best of the 5 highest ranked" — it presupposes an oracle. An agent that reports top-5 as achievable performance, or that selects a pose post hoc using the crystal structure it was given for evaluation, must be caught. The harness should recompute the metric under a strict top-1 selection rule and separately detect whether the ground-truth file was read before pose selection (tool-call-order audit). **This is a general MarigoldBench principle: the verifier must check not just the artifact but the causal order of tool calls that produced it.**

7. **Build multi-tool chain tasks whose difficulty comes from error propagation, and verify at the joint, not the links.** ESMFold → DiffDock is exactly the chain in this paper, with a measured accuracy cliff tied to pocket-backbone RMSD (Figure 10: three strata at < 0.5 Å, 0.5–1.5 Å, > 1.5 Å). A genuinely hard 8–25-call episode: fold a sequence with ESMFold/OpenFold2, dock with DiffDock, and report a defensible confidence in the resulting pose. The recomputed check is whether the agent measured its own pocket-backbone quality and conditioned its claim on it. Most models will chain the tools successfully and then over-claim, because each individual tool call "succeeded." **Tool-use difficulty lives in the joints, not the tools.**

8. **The synthetic-ground-truth pattern is a first-class flawed-premise family.** The apo ligand pose here is not measured — it is produced by a per-complex alignment with a fitted λ. A task that hands the agent an evaluation set whose "ground truth" was itself generated by a fitted procedure, and asks for a headline accuracy number, should be scored on whether the agent identifies that the target depends on a free parameter and asks for/performs a sensitivity analysis. The sound control uses real crystal poses.

9. **Cost and reproducibility envelope for calibrating episode budgets.** DiffDock's *training* cost was 4 × 48 GB A6000 × 18 days (850 epochs) for a 20.24 M-parameter score model plus a 4.77 M confidence model. *Inference* is 10 s for 10 samples on an A100 excluding preprocessing (ESM2 forward pass + RDKit conformer + graph build). At the NIM endpoint, budget an episode using 8–25 docking calls at roughly this scale; the ablation that 10 diffusion steps nearly matches 20 (Figure 11) means a ~2× compute lever exists that a well-informed agent could exploit and a naive one will not — usable as an efficiency sub-score. Also note ESM2 embeddings are worth only ~1–4 points (Table 9), so "the pipeline needs the language model" is a plantable false premise.

10. **Force agents to report the full RMSD distribution, not the threshold hit rate.** DiffDock's own numbers make the case: 38.2% below 2 Å but median 3.3 Å and 75th percentile 7.3 Å. A scoring rule that accepts "38% success" as the answer rewards exactly the summarization that hides the failure mass. The harness should recompute 25th/50th/75th percentiles and %<5 Å from the submitted pose set and penalize a submission that reports only the threshold rate — non-compensatorily, since a single headline number is the canonical way an agent launders a mediocre result.

---

## Verbatim quotes

1. **Sec 3, "Problem with regression-based methods" (lines 185–188):** "This behavior, illustrated in Figure 2, causes the regression-based models to produce signiﬁcantly more physically implausible poses than our method. In particular, we observe frequent steric clashes (e.g., 26% of EquiBind's predictions) and self-intersections in EquiBind's and TANKBind's predictions (Figures 4 and 12). We found no intersections in DIFFDOCK's predictions."

2. **App F.1, Table 4 caption (lines 1397–1398):** "Steric clashes. Percentage of test complexes for which the predictions of the different methods exhibit steric clashes. Search-based methods never produced steric clashes."

3. **App F.3, "Diffusion samples" (lines 1709–1712):** "For example, for the top-1 prediction, the proportion of the prediction with RMSD below 2 Å varies between 22% of a random sample of the diffusion model (N = 1) to 38% when the conﬁdence model is allowed to choose between 40 samples."

4. **App D.3, "Statistical signiﬁcance" (lines 1263–1264):** "To determine the statistical signiﬁcance of the superior performance of our method we used the paired two-sample t-test implemented in scipy [Virtanen et al., 2020a]."

5. **App E.1, "Access to bound protein structure" (lines 1349–1354):** "One limitation of DIFFDOCK is that it assumes access to the bound structure of the protein known as holo-structure. Although most of the literature in molecular docking makes this assumption, in practice, one often only has access to the unbound apo protein structure or the holo structure of the protein bound to a different ligand."

6. **Sec 5, "Selective accuracy of conﬁdence score" (lines 476–478):** "When only making predictions for the top one-third of complexes in terms of model conﬁdence, the success rate improves from 38% to 83%. Additionally, there is a Spearman correlation of 0.68 between DIFFDOCK's conﬁdence and the negative RMSD."

7. **App D.4, baselines (lines 1276–1280):** "We note that for all these baselines we have used the default hyperparameters unless speciﬁed differently below. Modifying some of these hyperparameters (for example the scoring method's exhaustiveness) will change the runtime and performance tradeoffs (e.g., if the searching routine is left running for longer then better poses are likely to be found), however, we leave these analyses to future work."

8. **App B (lines 905–908):** "We ﬁnd that the approximation of A as a group action works quite well in practice and use Algorithms 3 and 4 for all training and experiments discussed in the paper. Of course, disentangling the torsion updates from rotations in a way that makes Ator exactly a group action would justify the procedure further, and we regard this as a possible direction for future work."
