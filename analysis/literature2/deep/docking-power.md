# Deep read: docking-power

## 0. Identity correction (IMPORTANT)

The assigned arXiv id **2402.05980 is WRONG**. That id resolves to:

> "Do Large Code Models Understand Programming Concepts? Counterfactual Analysis for Code Predicates"
> Ashish Hooda, Mihai Christodorescu, Miltiadis Allamanis, Aaron Wilson, Kassem Fawaz, Somesh Jha
> UW-Madison / Google Research / Google DeepMind. ICML 2024, PMLR 235.

That is a code-LLM interpretability paper, unrelated to docking. Downloaded and title-checked
(`A:/PERTURB-Bench/analysis/literature2/pdfs/2402.05980.pdf`, 11 pages, 51,563 chars, extracted to
`A:/PERTURB-Bench/analysis/literature2/md/2402.05980.md`) then discarded.

No arXiv paper exists with the literal title "Evaluation of docking scoring power and its limits"
(verified against the arXiv API with `ti:"scoring power"`, `all:"docking scoring power and its limits"`,
`abs:"scoring power" AND cat:q-bio.BM`, and the arxiv.org/search HTML interface — zero exact hits).
I therefore substituted the closest **topic** match: a large-scale critical evaluation of docking
scoring/rescoring methods and their limits.

## Actual paper identity (as printed on page 1)

- **Title:** "Benchmarking Single-Pose Docking, Consensus Rescoring, and Supervised ML on the
  LIT-PCBA Library: A Critical Evaluation of DiffDock, AutoDock-GPU, GNINA, and DiffDock-NMDN"
- **arXiv id:** 2605.01681v2
- **Authors as printed:** Youssef Abo-Dahab¹, Xiaoiang Xiang^{1,2}, Joanne Chun^{1,2}, Liang Zhao^{1,2}
  (the "Xiaoiang" spelling is as printed — likely a typo for Xiaojiang)
- **Affiliations:** ¹ Dept. of Bioengineering and Therapeutic Sciences, Schools of Pharmacy and
  Medicine, UCSF; ² UCSF–Stanford Center of Excellence in Regulatory Science and Innovation (CERSI)
- **Venue:** arXiv preprint (structured-abstract / journal-submission format: Background / Objective /
  Methods / Results / Conclusion, with Declarations, Competing interests, Funding, Authors'
  contributions sections). Not stated as accepted anywhere.
- **Provenance disclosed in Acknowledgements:** "conducted as part of a capstone project for Master of
  Science degree in Artificial Intelligence and Computational Drug Discovery and Development (AICD3)
  at the University of California, San Francisco." Funded by internal Zhao Lab funds.
- **Recency marker:** cites Isomorphic Labs IsoDDE (Zenodo, 2026 Feb 10) and says "As of early 2026".

## Coverage ledger

| Item | Value |
| --- | --- |
| PDF | `A:/PERTURB-Bench/analysis/literature2/pdfs/2605.01681.pdf` (1,075,790 bytes, `%PDF-1.5`) |
| MD | `A:/PERTURB-Bench/analysis/literature2/md/2605.01681.md` |
| Pages | 27 |
| Extracted text chars (pypdf) | 62,637 |
| File chars on disk (`wc -c`, CRLF) | 64,877 |
| Lines (`wc -l`) | 883 |
| Chunk 1 | lines 1–300 (Read, limit 300) |
| Chunk 2 | lines 300–599 (Read, offset 300, limit 300) |
| Chunk 3 | lines 599–883 (Read, offset 599, limit 285) |
| **Coverage** | **883 / 883 lines = 100%; 64,877 / 64,877 chars = 100%** |

Also paged: lines 1–60 of the wrong paper `2402.05980.md` (~2,700 chars) for the title check.

Every section was read including Abstract, Introduction, metric definitions (EF/BEDROC/ROC-AUC),
Methodology, Results (Tables 2–5), Case study OPRK1, Discussion, "The Limitations of Docking in Drug
Discovery", "Limitations of Our Study", Conclusions, Declarations, and all 21 references.

---

## Section-by-section notes with numbers

### Abstract (lines 11–47)
- Dataset: LIT-PCBA, 15 targets, **578,295 ligand–target pairs** = **10,008 actives + 568,287 inactives**.
- Pipelines: AutoDock-GPU (10 independent runs per ligand, keep best-affinity pose) vs DiffDock
  (20 poses sampled, keep highest-confidence pose). Both rescored with GNINA (CNNaffinity) and NMDN
  (predicted pKd). Deliberately **single-pose** for both pathways so the comparison is matched.
- Headline: AutoDock-GNINA median EF1% = **2.14**, precision **1.85%**, recall **2.02%**, balanced
  accuracy **50.5%**. DiffDock-GNINA median EF1% = **0.84**. Baselines: AutoDock **1.10**, DiffDock **1.17**.
- Consensus: median EF1% ≈ **1.8** in both pathways; Global Consensus **1.9** — improves robustness but
  never beats the best single scorer.
- OPRK1: AutoDock-GNINA EF1% = **12.5** where every DiffDock variant = **0**.
- Throughput: AutoDock **4–8×** cheaper than DiffDock.
- Supervised ML re-ranker: best EF1% = **4.49** (+110% over 2.14), balanced accuracy 50.5% → **55.4%**.
- Conclusion sentence (lines 44–45): prefer "a rigorously tested docking technique, whose limitations
  are well understood" over "an unpredictable novel method that may yield inconsistent results."

### Introduction (lines 48–87)
- Motivating critique of DUD / MUV / DUD-E: **analog bias** (actives more similar to each other than to
  decoys) and **decoy artifacts** (models separate on simple physicochemical properties, not binding).
  These "produce artificially inflated performance metrics."
- LIT-PCBA is built from **149 dose–response PubChem bioassays** with experimentally confirmed
  actives and inactives, chosen to mimic a real screening deck with "very low hit rates."
- Two stated questions: (1) do SOTA ML docking/scoring beat classical physics-based docking on an
  unbiased experimental benchmark; (2) does rank-based consensus beat the best individual method.

### Metric definitions (lines 88–100, 300–350)
- EF_X% = observed enrichment / expected random enrichment. Worked example (Figure 1): library 5%
  actives, top-1% has 10% actives → EF1% = 2.
- ROC-AUC: 0.5 = random. BEDROC(α=20) heavily rewards actives in the top 1%; normalized RIE, range
  0 (random) to 1 (perfect). Explicit acknowledgement that EF is "sensitive to the size of the
  evaluated fraction (x%)", which is why BEDROC and AUC are added.
- Success criterion used throughout: a target "succeeds" if EF1% > 1 (i.e., better than random).

### Tool background (lines 101–175)
- AutoDock-GPU: Lamarckian GA; speedups ~**30–350×** (Solis–Wets) and **2–80×** (ADADELTA) per
  Santos-Martins 2021. Proxy prior: AutoDock Vina on LIT-PCBA median EF1% **1.3**, median AUROC **0.61**.
- DiffDock: diffusion over the non-Euclidean pose manifold (translation/rotation/torsion), blind
  docking; reported **38% top-1 success (RMSD < 2 Å)** on PDBBind vs ~23% traditional and ~20%
  regression DL.
- **Critical caveat carried forward (lines 127–134):** Jain, Cleves & Walters (arXiv:2412.02889) found
  many PDBBind test cases had near-identical training near-neighbours; on truly novel complexes
  DiffDock success rates "dropped by ~40 percentage points," implying partial memorization.
- GNINA: Vina scoring augmented with 3D CNN over voxelized complex. Sunseri & Koes 2021: beats Vina on
  **89 of 117** DUD-E+LIT-PCBA targets; LIT-PCBA median EF1% **1.88–2.58** vs Vina **0.90**;
  median ROC-AUC **0.61–0.62**.
- DiffDock-NMDN (Xia et al. 2025): NMDN learns the probability density of protein-residue–ligand-atom
  distances, emitting a pKd-like score. Xia reported **average EF1% = 4.96** on LIT-PCBA — but with
  many poses sampled and NMDN selecting the best. **This paper deliberately deviates**: single pose
  only, so the comparison is matched across pathways (lines 161–166).
- Table 1 (lines 167–175): AutoDock and DiffDock do both pose generation and scoring; GNINA and NMDN
  are rescoring-only.

### Methodology (lines 176–299)
- **Downsampling disclosure (lines 195–199):** for 7 targets (KAT2A, IDH1, GBA, FEN1, ADRB2, VDR, PKM2)
  the inactive set was downsampled to **5%** of full size, all actives kept. Full library would have
  required docking ~2.5M inactives, "infeasible within our computational budget."
- Target sizes: TP53 smallest at 4,245 molecules; OPRK1 largest at 197,274.
- Sign conventions made explicit: AutoDock lower energy = better; DiffDock/GNINA/NMDN higher = better.
  All converted to ranks (1 = best) before combining.
- Consensus schemes: unweighted rank averaging; "Calibrated Consensus" (CC) with GNINA and NMDN at 2×
  weight vs base docking at 1×. Worked example (line 234–235): ranks GNINA 15, baseline 76, NMDN 939 →
  uncalibrated mean 343.3, calibrated (W_GNINA = 2) 261.25.
- Score filters: NMDN cutoffs {900, −800, −4000}; GNINA CNNaffinity cutoffs {0.6, 0.1, 0.0}.
  **"We explored with hundreds of combinations, and we found that these cutoffs are more consistent
  than others."** (line 240–241) — i.e., cutoffs were selected by looking at outcomes on the same data.
  - CC-Medium: NMDN ≥ −800, CNNScore ≥ 0.1, calibrated.
  - UC-Strong: NMDN ≥ 900, CNNScore ≥ 0.6, uncalibrated.
  - CC-Weak: NMDN ≥ −4000, CNNScore ≥ 0.0, calibrated.
  - Global Consensus: CC-Medium settings applied across both pathways, chosen "because they produced
    the best results in both pathways."
- ML re-ranker: 17 primary features expanded to **42 derived features** (logs, squares, interaction
  terms, cross-method mean/SD), RobustScaler. **Split is 75/25 within each target** (~417k train /
  ~139k validation), explicitly "split the data by target to avoid any leakage of ligand-specific
  patterns" but the text then says "each target's data was internally split" — i.e., **the same targets
  appear in train and test**; this is a random within-target split, not a held-out-target split.
- Architectures: WNN 512-256-128-1 with batch norm and adaptive dropout 0.3→0.21→0.15; Deep MLP
  256-128-64-1, dropout 0.3→0.2→0.1. Adam lr 1e-3, weight decay 1e-5, batch = N/4, max 30 epochs,
  **early stopping on validation EF1%** (i.e., the reported metric is also the model-selection metric).
- Trees: XGBoost best (200 est., depth 6, lr 0.05) EF1% 3.80; LightGBM LambdaMART mode; Random Forest
  (100 trees, depth 8) EF1% 4.10.

### Results — Tables 2 and 3 (lines 351–434)
Median across 15 targets (Table 2), selected rows:

| Pathway | Scorer | Med EF1% | Med EF10% | Med ROC-AUC | Med BEDROC(20) | Actives remaining | Successes /15 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AutoDock | AutoDock | 1.1 | 0.77 | 0.4568 | 0.06 | – | 5 |
| AutoDock | NMDN | 0.37 | 1.2 | 0.571 | 0.066 | – | 4 |
| AutoDock | GNINA | **2.14** | 1.63 | **0.62** | **0.12** | – | 8 |
| AutoDock | CC-Medium | 1.84 | 1.53 | – | 0.0723 | 83.3% | 9 |
| AutoDock | UC-Strong | 0 | 0 | – | 0 | 0 | 6 |
| AutoDock | CC-Weak | 1.62 | 1.53 | – | 0.0887 | 100% | 9 |
| DiffDock | DiffDock | 1.17 | 0.83 | 0.53 | 0.0762 | – | 5 |
| DiffDock | NMDN | 0.673 | 1.13 | 0.5744 | 0.0642 | – | 6 |
| DiffDock | GNINA | 0.84 | 1.31 | 0.5535 | 0.0666 | – | 4 |
| DiffDock | CC-Medium | 1.8 | 1.54 | – | 0.0683 | 82% | 8 |
| DiffDock | UC-Strong | 0 | 0 | – | 0 | 0 | 5 |
| DiffDock | CC-Weak | 1.8 | 1.47 | – | 0.0891 | 100% | 9 |
| GLOBAL | CC-Medium | 1.9 | 1.58 | – | 0.0634 | 69% | 8 |

Note the baseline AutoDock median ROC-AUC is **0.4568 — worse than random**.

Averages (Table 3) diverge sharply: AutoDock-GNINA average EF1% **4.07** vs median 2.14; UC-Strong
average EF1% **2.87** (AutoDock) / **3.3** (DiffDock) despite **median 0** and ~**4%** actives retained.
The paper itself flags this (lines 431–434): the average "is sensitive to outliers and can reveal
exceptionally high performance on a subset of targets." This is a textbook mean-vs-median trap: a
method that throws away 96% of actives looks good on the mean.

### Per-method narrative (lines 435–474)
- Baseline DiffDock: EF1% = 0 on **ADRB2, IDH1, OPRK1, PPARG**; median 1.17; BEDROC 0.076; success
  rate stated as "33% only" — **inconsistent with Table 2, which lists 5/15 = 33%** for DiffDock but
  the same 33% is also claimed for AutoDock with 5 successes. (Both are 5/15; 5/15 = 33%. Consistent.)
- Baseline AutoDock: EF1% = 0 on **ESR1_ago, FEN1, IDH1, OPRK1, VDR**; median 1.1; BEDROC 0.06.
  IDH1 and OPRK1 fail under both engines. "the only target was that both algorithms succeeded at was GBA."
- DiffDock-NMDN: median 0.67, worse than both DiffDock (1.17) and DiffDock-GNINA (0.84) **on identical
  poses**. Improved only 3 targets (IDH1 0→2.64, ESR1_ant 1.10→2.20, ALDH1 1.17→1.41), worsened 5,
  neutral on 7; EF1% < 1 on 8 targets.
- AutoDock-NMDN: median **0.37**, the worst single scorer. Improved only FEN1 (0→1.63) and MAPK1
  (0.65→1.30); declined on 7. Conclusion: "the same protocol produces different results depending on
  the pose" — NMDN was tuned for DiffDock poses and does not transfer.
- AutoDock-GNINA: improved 8 targets, big gains ESR1_ago 0→7.78, IDH1 0→5.14, OPRK1 0→12.50; declined
  on only KAT2A (1.55→0.52) and MTORC1 (1.03→0), both with compensatory EF10%/BEDROC gains.

### Consensus results and Table 4 (lines 486–542)
Per-target EF1% head-to-head (AutoDock-GNINA vs three CC-Medium variants). Successes >1: AutoDock-GNINA
**10/15 (66%)**, AutoDock CC-Medium **11/15 (73%)**, DiffDock CC-Medium **11/15 (73%)**, Global CC-Medium
**9/15 (60%)**. Times best method: 6 / 3 / 5 / 4. Notable per-target reversals: MTORC1 AutoDock-GNINA
**0** vs AutoDock CC-Medium **8.33**; PPARG DiffDock CC-Medium and Global both **12.5** vs AutoDock-GNINA
3.73; IDH1 AutoDock-GNINA **5.1** vs all consensus **0**; OPRK1 AutoDock-GNINA **12.5** vs Global **0**.
- UC-Strong trade-off spelled out: PPARG EF1% ≈ **20.8** outlier inflates the average to ≈3.3 while
  median is 0 and actives retained ≈0 — "high volatility and limited reliability for prospective
  campaigns."
- Prescription: AutoDock-GNINA as primary scorer; UC-Strong only for ultra-large libraries or
  well-characterized targets; CC-Medium as balanced fallback.

### Case study OPRK1 (lines 543–578)
The most instructive passage for verification design. All DiffDock-pathway methods gave EF1% = 0.
The authors **visually inspected the docked poses against the co-crystallized reference ligand** and
confirmed the ligands sat correctly in the expected pocket — so the failure was **not** a pose-placement
failure. Yet the **21 actives among 197,274 inactives** ranked near the bottom. GNINA lifted them to
EF10% = 0.95 which, translated into practical terms, means "needing to screen ~20,000 molecules (top 10%)
to retrieve just two actives in a 200,000-compound library, rendering this approach impractical" —
i.e., **worse than random screening**. AutoDock-GNINA on the same target (24 actives, 269,734 inactives)
reached EF1% = 12.5.

**Key lesson: a geometrically correct pose can still produce a ranking that is worse than random.
Pose validity and ranking utility are orthogonal checks.**

### ML re-ranking (lines 579–604, Table 5)
| Rank | Model | EF1% | Δ vs baseline |
| --- | --- | --- | --- |
| 1 | Wide NN (512-256-128-1) | 4.49 | +109.8% |
| 2 | Random Forest | 4.10 | +91.6% |
| 3 | XGBoost v2 | 3.796 | +77.4% |
| 4 | LightGBM Classification | 3.735 | +74.6% |
| 5 | LambdaMART | 3.279 | +53.2% |
| 6 | Deep NN (256-128-64-1) | 1.792 | **−16.3%** |
| 7 | AutoDock-GNINA (baseline) | 2.140 | Ref. |

Note the narrower Deep MLP is **worse than the classical baseline**, so the "ML wins" claim is
architecture-dependent, not a general property. Also note the internal inconsistency: line 593 says
WNN EF1% = 4.49 (+109.8%); the caption at line 600–601 says "WNN achieved EF1% = 4.40 (+105.7%)".
The Discussion (line 635) additionally states AutoDock-GNINA "achieved the highest median EF1% (2.03)"
where every table says **2.14**. These three numbers contradict each other in the same paper.

### Classical accuracy metrics (lines 605–629)
The single most transferable passage on deceptive metrics. Treating top-1% as "predicted active":
- AutoDock-GNINA: median **accuracy 98.1%** ("misleading because of the overwhelming dominance of
  inactives"), **precision 1.85%**, **recall 2.02%**, **F1 1.9%**, **balanced accuracy 50.53%**.
- WNN at optimal threshold 0.1: accuracy 93.9%, precision **8.2%**, recall **15.0%**, F1 **10.6%**,
  balanced accuracy **55.4%**, **MCC 0.081**.

An MCC of 0.081 is the honest number: the best model in the paper is very nearly worthless in absolute
terms, even though it is +110% relative to the classical baseline.

### Discussion (lines 630–759)
- Cost: AutoDock ≈ **2 ligands/second on an RTX 3090**; DiffDock ≈ **1–2 seconds per ligand on an A100**
  (which is itself ≥2× an RTX 3090) → **4–8× more compute for inferior precision**.
- FEN1 failure: AutoDock-GNINA EF1% and EF10% both < 1 with ROC-AUC **0.509** (near-random). Consistent
  with Zhang et al. 2023 (Glide SP EF1% = 0 on FEN1). But Xia et al. got FEN1 enrichment with
  DiffDock-NMDN poses (AD4 1.08, Vina 2.17, Vinardo 1.90, NMDN 2.44, pKd+NMDN 3.79), and this paper's
  AutoDock-NMDN got 1.63 vs GNINA's 0.27 on FEN1 — target-specific scorer supremacy with no predictor.
- **Pose-quality mechanism, molecule 17434066** (SMILES `CCOc1cc(\C=C\2/N=C(SCC=C)SC2=O)cc(c1OC(=O)C)[N+](=O)[O-]`):
  the AutoDock pose received NMDN pKd-score **46.62 → rank 7**; the DiffDock pose of the *same molecule*
  received **3.19 → rank 7,039 of 18,135**. "pose quality is a primary determinant of machine-learning
  rescoring outcomes." Scoring 20–40 poses would mitigate this at **~20–40× compute**.
- Consensus literature: MILCDock (MLP over 52 features from 5 docking tools) average EF1% **4.37**;
  criticized for training on benchmark data → overfits benchmark chemical space. DockM8 (multiple
  engines, **16 scoring functions, 10 consensus strategies**) reached median EF1% **7.83**, AUROC
  **0.623**, beating 18 protocols — but required exploring **~6.2 × 10⁵ workflow combinations** and
  presupposes known actives.
- Forward-looking caution about IsoDDE (Isomorphic Labs, 2026): "Historically, many newly introduced
  AI-based docking and scoring tools have reported strong performance on curated benchmarks but failed
  to reproduce those gains in more realistic screening environments."

### "The Limitations of Docking in Drug Discovery" (lines 723–759)
Four numbered structural limits plus a fifth:
1. Benchmark-to-reality gap: CASF-strong methods contract on LIT-PCBA; best scorer here is EF1% 2.14,
   ROC-AUC ≈0.6, precision 1.85%, balanced accuracy 50.5%.
2. Target dependence: consensus had EF1% < 1 on **4/15** targets, AutoDock-GNINA on **5/15** —
   "even worse than randomly screening."
3. Pose-selection ambiguity: highest-confidence (DiffDock) vs best-affinity (AutoDock) vs most-common
   pose vs closest-to-true — unresolved, and each choice "adds to the complexity of docking, and the
   uncertainty of any approach."
4. Consensus and ML help but do not solve: CC-Medium buys one extra target (11 vs 10) at a complexity
   cost "it may not be justifiable"; ML risks overfitting and limited generalization to novel targets.
5. Deeper structural doubt: Abo-Dahab et al. 2026 showed pharmacology knowledge graphs predict
   drug–protein interactions from network topology alone, with explicit chemical structure features
   "not only redundant but often detrimental."

### Limitations of Our Study (lines 760–783) — admitted
1. Single-pose design underestimates ceiling for diffusion/search methods that benefit from ensembles.
2. 5% inactive subsampling on several targets "can shift EF statistics and tail behavior, particularly
   for EF1% where a few actives dominate variance"; medians/averages are "conservative approximations."
3. Consensus cutoffs and weights fixed across targets, not per-target optimal.
4. Single-dataset generalization caveat; different families/libraries/prep protocols could change even
   the relative ranking of methods.

### Conclusions (lines 784–791)
"Docking-based virtual screening provides useful enrichment but limited absolute predictive power on
realistic datasets such as LIT-PCBA... effective workflows should only use methods that can be
validated against that specific target or closely related systems."

---

## Classification: this is a BENCHMARK/EVALUATION study (not a new method)

- **What it evaluates:** 2 pose generators × 3-ish scorers × 3 consensus filters × 6 ML re-rankers on
  15 targets = 13 ranking pipelines in Tables 2–3 plus 6 ML models in Table 5.
- **Construction:** LIT-PCBA (149 PubChem dose–response bioassays), experimentally confirmed
  actives/inactives, no synthetic decoys. 578,295 pairs actually docked after 5% inactive subsampling
  on 7 of 15 targets.
- **Verification method:** purely retrospective label-based ranking metrics — EF1%, EF10%, ROC-AUC,
  BEDROC(α=20), plus precision/recall/F1/balanced accuracy/MCC at a top-1% cut. Plus one qualitative
  structural check (visual pose inspection vs co-crystal ligand) used to *rule out* a pose failure.
- **Scoring:** median across 15 targets as the primary summary, with averages reported alongside and
  explicitly flagged as outlier-sensitive; "success" = EF1% > 1.
- **Agent scaffolding:** none. This is a scripted pipeline, no LLM agent involved.
- **Uncertainty reporting:** **none.** No confidence intervals, no bootstrap, no standard errors, no
  seeds, no repeat runs. Medians and means over 15 targets with no dispersion statistic at all. Given
  OPRK1 has 21–24 actives and EF1% at n=21 has enormous variance, this is the paper's largest
  unadmitted weakness.
- **Contamination handling:** partially addressed by *choice of dataset* (LIT-PCBA over DUD-E) and by
  citing the DiffDock near-neighbour memorization critique. But the paper's own ML re-ranker is trained
  and tested on the **same 15 targets** with a within-target 75/25 split, and it cites (ref 6)
  "Data leakage and redundancy in the LIT-PCBA benchmark" (arXiv:2507.21404) without applying any of it
  to its own splits. GNINA and NMDN were both trained on data overlapping PDBBind/CrossDocked lineage;
  no train/test overlap audit is performed for the rescorers.
- **Cost per run:** AutoDock ≈2 ligands/s on RTX 3090; DiffDock ≈1–2 s/ligand on A100; overall DiffDock
  4–8× more expensive. Full un-subsampled library would have been ~2.5M inactives, declared infeasible.
  Multi-pose ensembling estimated at 20–40× current cost.

---

## Limitations admitted vs unadmitted

**Admitted:** single-pose ceiling; 5% inactive subsampling; fixed global consensus parameters;
single-dataset generalization; ML overfitting risk; EF's fraction-sensitivity.

**Unadmitted (my read):**
1. **No uncertainty quantification anywhere.** 15 targets, no CI, no bootstrap, no repeated seeds.
   AutoDock is stochastic (10 LGA runs); DiffDock is a stochastic sampler (20 poses). Run-to-run
   variance is never measured, so "2.14 vs 1.80" is not shown to be a real difference.
2. **Filter cutoffs selected on the evaluation data.** "We explored with hundreds of combinations, and
   we found that these cutoffs are more consistent than others" (line 240) plus Global Consensus using
   "these settings because they produced the best results in both pathways" (line 264) = selection on
   the test set. The consensus numbers are optimistically biased by an undisclosed amount.
3. **ML early stopping on validation EF1%, then EF1% reported as the result** (line 291–292). The
   headline 4.49 is a selected-maximum, not a held-out estimate.
4. **Within-target train/test split** presented as leakage-safe. It prevents nothing about target
   identity; the honest experiment (leave-one-target-out) is never run, yet the paper generalizes to
   "supervised ML models can significantly boost docking enrichment."
5. **Numerical inconsistencies:** 4.49 vs 4.40 for the same WNN; 2.14 vs 2.03 for AutoDock-GNINA;
   Table 3 mislabels "AutoDock / AutoDock-NMDN" where Table 2 says "AutoDock / DiffDock-NMDN".
   OPRK1 is described as 21 actives/197,274 inactives in the DiffDock case study but 24 actives/269,734
   inactives in the AutoDock paragraph — the same target with two different library sizes, unexplained
   (likely a subsampling artifact, never stated).
6. **Median-of-15 masks the discreteness of EF1%.** With 21 actives and a 1% cut of ~2,000 compounds,
   EF1% moves in coarse quanta; "EF1% = 0" and "EF1% = 12.5" can be a one- or two-molecule difference.
7. **DiffDock is used out of its design regime.** Blind docking over the whole surface is compared
   against pocket-constrained AutoDock; the paper never states whether DiffDock got the same box/pocket
   prior, so part of the DiffDock deficit may be a harness-fairness artifact rather than model quality.
8. **Data availability is "upon reasonable request"** — the generated docking results, rescoring
   outputs, and ML features are not released, so none of this is independently recomputable.

---

## Implications for MarigoldBench

1. **A tool-use task is genuinely hard when the tool succeeds and the science still fails.** The OPRK1
   case is the template: DiffDock returned poses that a visual check confirmed were correctly seated in
   the pocket, and the resulting ranking was still worse than random (21 actives buried at the bottom of
   197,274). Build task families where every tool call returns HTTP 200 and a physically valid artifact,
   yet the scientific conclusion the model is asked to reach is unsupported. Models that equate "the
   tool ran" with "the result is real" fail; models that run the downstream enrichment check pass.
   Concretely: give the model DiffDock + a labelled actives/inactives set and ask "does this pipeline
   enrich?", where the ground truth is EF1% ≈ 0.

2. **Verify by recomputing a rank-based enrichment metric from the submitted artifact, never from the
   model's number.** The harness should demand the full submitted ranking (ligand id → score, all N
   rows), then recompute EF1%, BEDROC(α=20) and ROC-AUC itself against a held-back label vector the
   model never sees. This is exactly the paper's own verification and it is cheap, deterministic, and
   impossible to fake by self-report. Reject submissions whose row count, id set, or score-direction
   convention doesn't match the input manifest — the paper had to explicitly handle "lower AutoDock
   energy = better rank, higher GNINA = better rank" (line 215–218), and a sign flip is a silent,
   plausible, fully-recomputable defect.

3. **Plant the mean-vs-median trap as a defect condition.** UC-Strong has average EF1% 2.87–3.3 (better
   than most methods) while its median EF1% is 0 and it retains ~4% of actives. A model that reports the
   mean and declares victory has produced a defensible-looking, wrong answer. The harness recomputes
   both the mean and the median plus the actives-retained fraction and fails any submission that
   recommends a filter retaining <50% of actives. This generalizes: **aggregate-statistic choice is a
   plantable defect that is invisible to self-report and trivial to recompute.**

4. **Plant the accuracy-on-imbalanced-data trap; require balanced accuracy or MCC in the check.**
   AutoDock-GNINA is 98.1% accurate and has precision 1.85%, recall 2.02%, MCC-equivalent near zero.
   A sound physical/statistical check on any classification-flavoured episode must (a) be
   prevalence-invariant (balanced accuracy, MCC, BEDROC, EF — not raw accuracy), and (b) be compared
   against an explicit random baseline computed on the *same* label vector. Make "the model reports raw
   accuracy on a 1.7%-positive set" an automatic fail in the sound-control condition too, so it costs
   something to reach for the flattering metric even when nothing is planted.

5. **Threshold/hyperparameter selection on the evaluation set is the most realistic planted defect for
   an agentic lab.** This paper chose its consensus cutoffs by scanning "hundreds of combinations" for
   the best result and early-stopped its NN on the very EF1% it reports. An 8-25 call episode is exactly
   long enough for a model to do this: sweep MolMIM/DiffDock/scoring thresholds, pick the best, report
   it as the result. Verification: the harness logs every scoring call the model makes against the
   labelled split, and if the submitted configuration was chosen after >1 evaluation on that split, the
   harness re-evaluates it on a truly untouched holdout and scores *that* number. The pass condition is
   that the model either reserved a holdout itself or explicitly reported the selected-max as biased.

6. **Give the flawed-premise condition a "pose is valid, therefore the affinity ranking is valid"
   framing — refusal/correction is the right answer.** Molecule 17434066 got NMDN pKd 46.62 (rank 7)
   from an AutoDock pose and 3.19 (rank 7,039/18,135) from a DiffDock pose — same molecule, same scorer.
   A task that says "we validated the poses with PoseBusters, so rescore them and report the affinity
   ranking as reliable" contains a false premise: rescorers are pose-provenance-dependent and a
   scorer tuned on one generator's poses (NMDN on DiffDock poses → median EF1% 0.37 on AutoDock poses)
   silently degrades. Correct behaviour is to flag the provenance mismatch, not to comply.

7. **Cross-tool transfer failure is a cheap, high-yield defect family.** NMDN was developed for DiffDock
   poses and collapses to median EF1% 0.37 on AutoDock poses; GNINA is 2.14 on AutoDock poses and 0.84
   on DiffDock poses — a 2.5× swing from pose provenance alone. In MarigoldBench, wire episodes that
   chain Boltz-2 / DiffDock / MolMIM outputs into a scorer trained on a different generator's
   distribution. The check is a paired comparison on identical ligands across both provenances; the
   model must detect that the score distribution shifted, not just report the numbers.

8. **Force an explicit random/negative-control arm in every episode and recompute it.** The paper's most
   valuable finding is comparative: "worse than random screening" appears repeatedly, and 4–5 of 15
   targets fall below EF1% = 1 for even the best method. Any MarigoldBench task whose success criterion
   is "the model found signal" must have the harness compute the shuffled-label / random-ranking null on
   the same data and require the submitted result to clear it by a stated margin. Without this, the
   sound-control condition cannot distinguish a real result from a lucky one, and false alarms cannot be
   penalized fairly.

9. **Budget realism: make cost part of the score.** AutoDock at ~2 ligands/s beat DiffDock at ~1–2 s/ligand
   on both accuracy and 4–8× on cost, and multi-pose ensembling would cost 20–40×. Episodes capped at
   8–25 tool calls should include tasks where the correct answer is the cheaper tool, and where a model
   that burns its call budget on the fashionable diffusion model runs out before it can verify anything.
   This makes tool *selection* — not just tool *operation* — a scored dimension.

10. **Require dispersion, not point estimates, and make the absence of it a failure.** This paper reports
    zero confidence intervals across 15 targets with stochastic samplers, and its per-target n is as low
    as 21 actives. For MarigoldBench's template-clustered CIs to mean anything, the *tasks themselves*
    should demand the model report uncertainty on its own result (bootstrap over targets/ligands, or
    repeated seeds), and the harness should recompute the bootstrap from the submitted per-item scores
    and check the model's stated interval against it. A model that submits "EF1% = 4.49" with no
    interval when n=21 has not produced a scientific result.

11. **Plant internal-inconsistency defects and check artifact self-consistency mechanically.** This paper
    contains 4.49 vs 4.40 for the same model, 2.14 vs 2.03 for the same method, and OPRK1 at both
    197,274 and 269,734 inactives. Cheap, fully automatic verification: cross-check every number the
    model states in prose against the artifact it submitted, and check conservation properties
    (row counts, actives counts, library sizes) across all stages of the pipeline. A model that reports
    a summary inconsistent with its own submitted table fails without any domain reasoning needed.

12. **Contamination handling should be an in-task obligation.** DiffDock's 38% PDBBind top-1 drops ~40
    percentage points on complexes with no training near-neighbours. Give the model targets/ligands whose
    contamination status differs, and score whether it checks for training-set near-neighbours before
    quoting a published benchmark number as its expected performance. This is a tool-use task
    (similarity search over a reference set) with a recomputable answer, and it directly tests the
    behaviour that separates a scientist from a benchmark-quoter.

---

## Verbatim quotes

1. **(Abstract / Conclusion, lines 41–45)**
   > "Overall, no single docking technique works on all targets. Therefore , we believe that employing a
   > rigorously tested docking technique, whose limitations are well understood, is preferable to relying
   > on an unpredictable novel method that may yield inconsistent results."

2. **(Results, Case study: OPRK1, lines 554–559)**
   > "Despite correct docking poses, visualization of active compound rankings revealed that the 21
   > actives (out of 197,274 inactives) were concentrated near the bottom of the ranked lists for
   > DiffDock scoring methods. GNINA marginally improved rankings, achieving an EF10% of 0.95, but this
   > translates to needing to screen ~20,000 molecules (top 10%) to retrieve just two actives in a
   > 200,000-compound library, rendering this approach impractical. This case highlights that, for
   > OPRK1, docking performance with the DiffDock pathway was worse than random screening"

3. **(Results, Classical Accuracy Metrics, lines 612–622)**
   > "If we assumed the top 1% of the ranked molecules are actives, and all the rest are not,
   > AutoDock -GNINA rescoring will achieve a median accuracy of 98.1%, which at first glance appears
   > strong. However, this figure is misleading because of the overwhelming dominance of inactives in the
   > dataset. Precision, on the other hand was only 1.85%, meaning that fewer than 2 of every 100
   > compounds predicted as actives were truly active. Recall was 2.02%, showing that only about 2 in
   > every 100 true actives were successfully identified. ... The result is 50.53%, which is slightly
   > better than random guessing."

4. **(Discussion, pose-quality mechanism, lines 662–667)**
   > "On the right is the pose that was generated by AutoDock and NMDN gave it a pKd-Score 46.62 so it
   > ranked number 7 in the list . On left, is the same molecule pose that was generated by DiffDock it
   > was given a pKd-Score of just 3.19. So it ranked 7039 out 18135. This illustrates that pose quality
   > is a primary determinant of machine-learning rescoring outcomes."

5. **(Discussion, The Limitations of Docking in Drug Discovery, lines 724–727)**
   > "Even the best-performing components in our benchmark expose inherent limits of docking for
   > prospective hit finding. First, there is a persistent gap between benchmark gains and real -world
   > efficacy. Methods that look strong on decoy-based suites (e.g., CASF ) can contract sharply on
   > experimentally curated sets like LIT-PCBA."

6. **(Methodology, the test-set-selection admission, lines 239–241)**
   > "Specifically, we applied several cutoff values for both NMDN_Score (900, -800, and -4000) and GNINA
   > CNNaffinity (0.6, 0.1, and 0.0). We explored with hundreds of combinations, and we found that these
   > cutoffs are more consistent than others."

7. **(Discussion, on new AI systems, lines 718–722)**
   > "Historically, many newly introduced AI-based docking and scoring tools have reported strong
   > performance on curated benchmarks but failed to reproduce those gains in more realistic screening
   > environments. Rigorous independent evaluation on experimentally derived datasets such as LIT-PCBA
   > and in prospective drug discovery campaigns will therefore be essential before the reliability and
   > generalizability of these new systems can be established."
