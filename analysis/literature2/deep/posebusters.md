# PoseBusters — deep read

## 1. Coverage ledger

| Item | Value |
|---|---|
| PDF | `A:/PERTURB-Bench/analysis/literature2/pdfs/2308.05777.pdf` (14,680,023 bytes, `%PDF-1.5`) |
| Pages | 36 |
| Extracted md | `A:/PERTURB-Bench/analysis/literature2/md/2308.05777.md` |
| Chars extracted (pypdf) | 91,163 |
| File size on disk | 93,488 bytes (1,795 lines, CRLF) |
| Lines | 1,795 |

Chunk ranges read with the Read tool (sequential, no gaps):

| # | Range | Content |
|---|---|---|
| 1 | lines 1–600 | Abstract, §1 Introduction, §2 Methods (Tables 1–4), §3.1 Astex results, Figs 1–3 |
| 2 | lines 601–1200 | §3.2 Benchmark-set results, Fig 4, §3.3 energy minimisation, Figs 5–6, §4 Discussion, data availability, 45 refs, SI TOC, §S1 docking protocols, §S2 search spaces, §S3 Table S1 procurement, §S4/S5 data sets |
| 3 | lines 1201–1795 | Rest of §S5 PDB/CCD listings, §S6 EM example, §S7 cofactor analysis, §S8 all waterfall plots + per-test distributions (Figs S6–S20), §S9 Uni-Mol binding-site sweep (Figs S21–S22), SI references |

**Coverage: 1,795/1,795 lines = 100%. 91,163 chars paged through.** Extraction exceeded the 15,000-char floor, so no ar5iv fallback was needed. Note: the PDF is a figure-heavy RSC-template preprint; numeric values in Figures 1, 4, 5, S4, S6, S7, S21, S22 extract as bare bar labels in reading order, so I reconstructed them by cross-checking against the waterfall integer counts in §S8 (e.g. DiffDock 38/308 = 12%) and the prose. Where the reconstruction is ambiguous I say so below.

## 2. Actual paper identity (as printed)

- **Title (page 1, verbatim):** "PoseBusters: AI-based docking methods fail to generate physically valid poses or generalise to novel sequences"
  - Note: the task brief's title ("AI docking methods fail to generate physically valid poses") is the shorter published *Chemical Science* title; the arXiv v3 title on disk is the longer one above. Same paper, correct arXiv id.
- **Authors:** Martin Buttenschoen, Garrett M. Morris, Charlotte M. Deane (corresponding: deane@stats.ox.ac.uk)
- **Affiliation:** Department of Statistics, 24–29 St Giles', Oxford OX1 3LB, United Kingdom
- **Version read:** `arXiv:2308.05777v3 [q-bio.QM] 28 Nov 2023`. Journal template placeholder still present ("Journal Name [year] [vol.] 1–10"); published as *Chem. Sci.* 2024, 15, 3130–3139.
- **Artifacts:** pip package + BSD-3-Clause source at `github.com/maabuu/posebusters`; data and per-pose tabulated results at `https://zenodo.org/records/8278563`.
- **Type:** hybrid. It is (a) a **validation tool** (PoseBusters, 19 RDKit checks) and (b) a **benchmark set** (PoseBusters Benchmark, 308 complexes) and (c) a **comparative evaluation** of 7 docking methods. I cover it under both the METHOD/TOOL and BENCHMARK headings.

## 3. Section-by-section notes with numbers

### §1 Introduction
Core claim: DL docking methods report state-of-the-art RMSD but produce physically implausible structures; RMSD alone is insufficient. "The five DL-based docking methods we test in this paper all claim better performance than standard docking methods but these claims rest entirely on RMSD. None of these methods test their outputs for physical plausibility." Framing borrowed from PDB ligand structure validation (Shao et al. 2022) and from de-novo generation validity suites (Brown et al., GuacaMol).

### §2.1 Docking methods (Table 1, Table 3)
Seven methods. DL: DeepDock (Dec 2021, pocket), DiffDock (Feb 2023, blind), EquiBind (Feb 2022, blind), TankBind (Oct 2022, blind), Uni-Mol (Feb 2023, pocket). Classical: AutoDock Vina 1.2.3, CCDC Gold (CSD Python API 3.0.14).

Search spaces (Table 3): Gold = 25 Å-radius sphere on crystal-ligand centroid; Vina = 25 Å cube on crystal-ligand centroid; DeepDock = surface mesh nodes within 10 Å of any crystal ligand atom; Uni-Mol = residues within 8 Å of any crystal ligand heavy atom; DiffDock = whole protein; EquiBind = chains within 10 Å of crystal ligand; TankBind = P2Rank-predicted pockets. **Every non-blind search space is defined using the crystal ligand** — the answer's location is partially given away, uniformly, to make blind and pocket methods comparable.

Training sets (Table 2): all five DL methods trained on PDBbind General Set subsets — DeepDock 16,367 complexes (2019 GS minus CASF-2016), DiffDock/EquiBind 17,347 (2020 GS, pre-2019, ligand-disjoint from test), TankBind 18,755, Uni-Mol 18,404 (MMseqs2 <40% identity + fingerprint <80% vs CASF-2016). Models used as released, no retuning.

### §2.2 The PoseBusters test suite (Table 4) — 19 checks in 3 groups
Inputs: SDF of docked ligand(s), SDF of true ligand(s), PDB of protein + cofactors. All loaded into RDKit **with sanitisation off** (so the sanitisation check itself is meaningful). Poses passing all checks are **"PB-valid"**.

**A. Chemical validity/consistency (6):** file loads; RDKit sanitisation; molecular formula preserved; bonds preserved; tetrahedral chirality preserved; double-bond stereochemistry preserved. Comparison is via *standard InChI* after stripping isotopes and neutralising charges (layers `/`, `/c`, `/h`, `/q`, `/p`, `/t`, `/b`), because the stereo layer depends on H/charge/proton layers, which "can unexpectedly change during docking even though most docking software considers the charge distribution and protonation state of a ligand as fixed". Primary-ketimine double-bond stereo is normalised away (ambiguous H position).

**B. Intramolecular validity (6):** bond lengths within 0.75× lower / 1.25× upper Distance-Geometry bounds (25% tolerance); bond angles same 25%; aromatic 5-/6-rings planar within 0.25 Å of best-fit plane; aliphatic C=C plus four neighbours planar within 0.25 Å; internal steric clash — non-bonded pair distance above 0.8× (Table 4) / 0.7× (§2.2.2 text and Fig S11) of DG lower bound; **energy ratio ≤ 100**, where ratio = UFF energy of the docked conformer / mean UFF energy of 50 ETKDGv3 conformers relaxed with UFF for ≤200 iterations.

**C. Intermolecular validity (6+):** min protein–ligand heavy-atom distance > 0.75 × sum vdW radii; same for organic cofactors; for inorganic cofactors 0.75 × sum of *covalent* radii; volume overlap with protein < 7.5% of ligand vdW volume (radii scaled 0.8) via RDKit `ShapeTverskyIndex`; same for organic cofactors (0.8) and inorganic cofactors (scaling 0.5).

**Threshold calibration is empirical and explicitly ground-truth-anchored:** thresholds were chosen so that essentially all *crystal* ligands pass. 25% bond tolerance — "all but one of the crystal ligands in the Astex Diverse set and all of those in the PoseBusters Benchmark set pass at this threshold". 0.25 Å planarity — "admits all Astex Diverse and PoseBusters Benchmark set crystal structures by a wide margin". Energy ratio: Wills et al. used 7 (95% of PDBbind crystal ligands pass); the authors deliberately loosened to 100, "where only one structure each from the Astex Diverse and PoseBusters Benchmark set is rejected". Volume-overlap threshold exists because real crystals clash: "Verdonk et al. found that 81 out of 305 selected high-quality protein-ligand complexes from the PDB contain steric clashes."

**Measured false-alarm rate on ground truth (Figs S6a, S7a):** crystal structures themselves — Astex 85 → 83 PB-valid (2 fail: 1 internal steric clash, 1 energy-too-high) = **2.4% false-fail**; Benchmark 308 → 306 PB-valid (2 fail min protein–ligand distance) = **0.65% false-fail**.

### §2.3–2.5 Metrics and post-processing
RMSD: minimum heavy-atom **symmetry-aware** RMSD via RDKit `GetBestRMS` to the nearest crystallographic copy of the ligand. Coverage = fraction under 2 Å ("This value is arbitrary but commonly-used"). Sequence identity: Smith–Waterman in Biopython, BLOSUM62, gap open −11, extend −1, unknown residues counted as mismatches, normalised by query length. Energy minimisation: AMBER ff14SB + OpenFF Sage in OpenMM, PDBfixer-prepared protein with **all protein atoms fixed**, ligand-only relaxation to 0.01 kJ mol⁻¹ convergence.

### §2.6 / §S3 Data sets
Astex Diverse: 81 complexes / **85 ligand cases** (2007, hand-picked). PoseBusters Benchmark: **308 unique PDB entries, 308 unique ligands (CCD IDs)**, released 1 Jan 2021 – 30 May 2023, so disjoint from PDBbind 2020 GS.

Table S1 procurement funnel — 22 filter steps, 10,537 entries / 6,635 ligands → 308/308:
MW 100–900 Da → 6,424 ligands; ≥3 heavy atoms → 6,374; elements limited to H,C,O,N,P,S,F,Cl → 6,271; not covalently bound to protein → 7,247/4,891; no unknown atoms → 7,218/4,881; **X-ray resolution ≤ 2 Å → 4,686**; **ligand real-space R-factor ≤ 0.2 → 3,800**; **ligand RSCC ≥ 0.95 → 1,849** (largest single cut); ligand model completeness 100% → 1,820; ETKDGv3 start conformer generatable → 1,733; RDKit loads + sanitises → 1,706/994; no stereochemical errors in PDB ligand report → unchanged; **no atomic clashes in PDB ligand report → 1,256/844**; single conformation selected; intermolecular distance to protein ≥ 0.2 Å → 1,237; to other organics ≥ 0.2 Å; to metal ions ≥ 0.2 Å → 1,232; PDB blocklist (bad conformations 7X48/7UYC, polymer-forming ligands 7WJD/7DB4, racemic CCD mismatches 6ZYU/7W2W, unsupported elements Te/Yb 7ZSQ/8AVA) → 1,227; CCD blocklist (I8P, 5A3, U71, UEV — too symmetric, RMSD mapping blowup) → 1,223; random selection for unique ligands → 809/823; unique PDB entries → 809; **Diamond sequence clustering (0% identity cutoff, 100% coverage) → 428**; **remove ligands within 5.0 Å of any protein symmetry mate → 308**.

Leakage quantification for the *old* benchmark: "47 of the 81 complexes in the Astex Diverse set are in the PDBbind 2020 General Set and 67 out of the 81 of the Astex Diverse set proteins have more than 95% sequence identity with proteins found in PDBbind 2020 General Set." Vina is also implicated: its scoring-function regression was fit on an earlier PDBbind that already contained most of Astex.

### §3.1 Astex Diverse results (n = 85)

| Method | RMSD ≤ 2 Å | RMSD ≤ 2 Å **and** PB-valid | Δ (points lost) |
|---|---|---|---|
| Gold | 67% | 64% | −3 |
| Vina | 58% | 56% | −2 |
| DeepDock | 35% | 11% | −24 |
| Uni-Mol | 45% | 12% | −33 |
| DiffDock | 72% | 47% | −25 |
| EquiBind | 7.1% | 1.2% | −5.9 |
| TankBind | 59% | 5.9% | −53 |

DiffDock is the RMSD winner (72% > Gold 67%); after PB-validity the ranking flips to Gold 64% > Vina 56% > DiffDock 47%. TankBind loses 90% of its apparent wins. Waterfall (Fig 2, TankBind/Astex): 85 → 50 within 2 Å → −17 tetrahedral chirality → −2 double-bond stereo → −3 internal clash → −3 energy → −20 protein–ligand distance → **5 PB-valid (5.9%)**.

Per-method dominant failure modes (Figs 2, S6): TankBind "habitually overlooks stereochemistry" (17/50 chirality) and clashes with protein (20); Uni-Mol "very often fails to predict valid bond lengths" (Astex: −7 chirality, −15 bond lengths, −2 angles, −4 energy → 10 PB-valid); EquiBind "tends to produce protein-ligand clashes" (Astex: 6 within 2 Å, −5 protein clash → 1); DeepDock: −7 chirality, −5 internal clash, −2 rings, −6 energy → 9; DiffDock: −1 energy, **−19 protein–ligand clash**, −1 organic cofactor → 40 of 61; Vina −1 energy → 48/49; Gold −3 protein clash → 54/57.

Fig 3 gallery of failures, all with RMSD near or under 2 Å: DiffDock 7QPP/VDX stereo flip at 1.9 Å; Uni-Mol 1OPK/P16 long bonds at 1.5 Å; Uni-Mol 1UML/FR4 extreme angles at 1.4 Å; DeepDock 1N2V/BDI internal clash at 1.6 Å; TankBind 1TOW/CRZ non-flat aromatic at 2.2 Å; TankBind 1U4D/DBQ non-flat double bond at 1.7 Å; **Vina 7LOU/IFM energy ratio too high at 1.9 Å**; DiffDock 7L7C/XQ1 protein clash at 1.6 Å.

### §3.2 PoseBusters Benchmark results (n = 308)

| Method | RMSD ≤ 2 Å | RMSD ≤ 2 Å **and** PB-valid | PB-valid count (Fig S7) |
|---|---|---|---|
| Gold | 58% | 55% | 167/308 |
| Vina | 60% | 58% | 178/308 |
| DeepDock | 20% | 5.2% | 16/308 |
| Uni-Mol | 22% | 2.0% | 6/308 |
| DiffDock | 38% | 12% | 38/308 |
| EquiBind | 2.0% | ~0% | **0/308** |
| TankBind | 16% | 3.3% | 10/308 |

Every method drops vs Astex; the DL drop is catastrophic (DiffDock 47% → 12%). DiffDock's Benchmark waterfall: 308 → 1 unloadable → 190 over 2 Å → 117 → −1 stereo, −3 internal clash, −2 energy, **−72 protein–ligand clash**, −1 volume overlap w/ organic cofactor → 38.

**Sequence-identity stratification (Fig 4)** vs max identity to PDBbind 2020 GS, bins [0,30%], (30%,95%], (95%,100%]:
- RMSD ≤ 2 Å: Gold 53/64/60, Vina 56/57/65 (flat); DeepDock 13/21/25, Uni-Mol 21/21/23, DiffDock **15/45/54**, EquiBind 0.0/1.3/4.1, TankBind 1.8/13/30 (steeply increasing with similarity).
- RMSD ≤ 2 Å **and** PB-valid, low-identity bin: Gold 49%, Vina 54%, DeepDock 1.8%, Uni-Mol 0.0%, **DiffDock 0.92%**, EquiBind/TankBind ≈0. Prose: "across all of the DL-based docking methods almost no physically valid poses were generated within the 2 Å threshold."
- Methodological verdict: time-split alone is not enough — "we argue that this is insufficient for testing generalisation to novel targets and the sequence identity between the proteins in the training and test must be reported on."

**Cofactor stratification (Fig S4, §S7).** ~45–46% of Benchmark complexes have a cofactor within 4.0 Å of the ligand (main text says "About 45%", Fig S5 caption says 46%). No-cofactor vs has-cofactor, RMSD ≤ 2 Å: Gold 58/59, Vina 55/65, DeepDock 20/19, Uni-Mol 26/18, DiffDock 46/29, EquiBind 2.5/1.4, TankBind 20/12. Classical methods get *better* with cofactors present; DL methods get worse (DiffDock PB-valid 17% → 7.5%).

### §3.3 Post-docking energy minimisation (Fig 5, Benchmark n = 308)

| Method | RMSD≤2Å raw | RMSD≤2Å +EM | PB-valid raw | PB-valid +EM |
|---|---|---|---|---|
| Gold | 58% | 56% | 55% | **49%** |
| Vina | 60% | 56% | 58% | **49%** |
| DeepDock | 20% | 21% | 5.2% | 14% |
| Uni-Mol | 22% | 29% | 2.0% | 18% |
| DiffDock | 38% | 40% | 12% | **35%** |
| EquiBind | 2.0% | 5.4% | ~0% | 4.7% |
| TankBind | 16% | 22% | 3.3% | 13% |

EM roughly triples DL PB-validity but **degrades both classical methods** (Gold 55→49, Vina 58→49). Fig S3 shows a Vina pose that was PB-valid at 1.9 Å and was "destroyed" into 2.2 Å by minimisation. Fig 6 shows a Uni-Mol pose repaired from 2.0 Å to 1.1 Å (rings flattened, over-long bond shortened). Even after EM, DiffDock 35% < Gold/Vina 49%. Conclusion: "at least some key aspects of chemistry and physics encoded in force fields are missing from deep learning models."

### §S9 Binding-site sensitivity (Figs S21–S22) — the most under-reported result
Uni-Mol's headline number is dominated by an evaluation knob. With its *preferred* tight 6 Å pocket, Uni-Mol reaches ~68% RMSD ≤ 2 Å on the Benchmark set — vs **22%** at the 8 Å pocket used in Figure 1 — "Under the tight pocket definition Uni-Mol performs better than any of the blind docking methods." Gold is comparatively flat across 6/8/10 Å/25 Å-centroid definitions. With 6 Å pocket + EM, Uni-Mol PB-validity rises "to about the same level as DiffDock (35%)". A ~3× swing in the headline metric from a pocket-radius choice.

### §S1 Protocols (reproducibility detail)
All methods that need a starting conformer got the **identical** ETKDGv3+UFF conformer. All receptors prepared **without waters** ("as none of the DL-based methods supports docking with waters"). 40 poses generated per case for Vina (exhaustiveness 32) and Gold (PLP rescore, autoscale 100%, early termination off), **top-ranked pose only** evaluated. DiffDock: 40 poses, 20 inference steps, no noise on final step, top-ranked. Exact commit hashes pinned for all five DL methods (DeepDock 54a2a64, DiffDock fff8f0b, EquiBind 41bd00f, TankBind 804e9fc, Uni-Mol b962451) plus versions for Vina 1.2.3/Meeko 0.4.0/Reduce/ADFRsuite/RDKit 2022.09.1/MSMS 2.6.1/p2rank 2.3.

## 4. As a BENCHMARK

- **Task count:** 308 re-docking cases (PoseBusters Benchmark) + 85 (Astex Diverse). One task = re-dock a cognate ligand into its own crystal receptor. 7 methods × 393 cases ≈ 2,751 predictions, plus an EM arm on the 308 and a 4-point pocket sweep for Uni-Mol/Gold.
- **Construction:** 22-step deterministic filter over the PDB with hard experimental-quality gates (resolution ≤2 Å, RSR ≤0.2, RSCC ≥0.95, 100% completeness, PDB-report clash-free and stereo-error-free), chemical scope gates (100–900 Da, 8 element types, non-covalent), de-duplication (unique ligand, unique entry, Diamond sequence clustering at 0% identity/100% coverage), and two hand-curated blocklists. Final symmetry-mate filter (5.0 Å) removed 120 of 428 remaining cases.
- **Verification method:** the *scoring is recomputation*, not self-report. Every claim is re-derived from the submitted SDF/PDB geometry with RDKit — DG bounds, best-fit planes, UFF energies, vdW distance ratios, Tversky volume overlap, symmetry-aware RMSD. No model output is trusted; nothing is graded by an LLM or by the method's own confidence score.
- **Scoring:** non-compensatory conjunction. A prediction counts only if RMSD ≤ 2 Å **AND** all 19 checks pass. A single failed check zeroes the case (see TankBind: 59% → 5.9%). This is exactly the MarigoldBench VEC shape.
- **Agent scaffolding:** none — this is a static method comparison, not an agentic benchmark. Each method run under its authors' documented protocol with pinned commits.
- **Reported scores with uncertainty:** **no confidence intervals, no error bars, no significance tests anywhere.** Point estimates only, quoted to 2–3 significant figures (e.g. "0.92%" from n=109-ish). At n = 308, a binomial 95% CI at p ≈ 0.55 is roughly ±5.6 points, so Gold 55% vs Vina 58% is not distinguishable; at n = 85 the CI is ~±10 points. Sub-bin claims (three sequence bins over 308 cases) are on n ≈ 70–130 with CIs of ±9–12 points.
- **Contamination handling:** the central design feature. Time cutoff (post-2021 release) is used to guarantee disjointness from PDBbind 2020 GS, but the paper's own result is that **time cutoff is insufficient** — it adds sequence-identity stratification against the training corpus as the real contamination probe, and quantifies contamination in the legacy benchmark (47/81 Astex complexes in PDBbind; 67/81 proteins >95% identity).
- **Cost per run:** not reported. No wall-clock, GPU-hours, or licence costs, despite speed being the stated motivation for DL docking. Unadmitted gap.

## 5. As a METHOD/TOOL

- **What it does:** `posebusters` (pip, BSD-3) runs 19 deterministic RDKit checks in three tiers (chemical consistency, intramolecular geometry/energy, intermolecular clash) and emits a per-check pass/fail table plus the aggregate `PB-valid` boolean. Also computes symmetry-aware RMSD to the reference ligand.
- **Inputs:** predicted ligand SDF, true ligand SDF, protein+cofactor PDB. Modes exist for redock (all three), dock (no true ligand), and molecule-only (intramolecular checks only). Every threshold is user-configurable.
- **Returns:** boolean per check per pose; `PB-valid` = AND of all; plus the underlying continuous quantities (ratios to DG bounds, Å from best-fit plane, energy ratio, distance/sum-vdW ratio, % volume overlap).
- **Measured accuracy / false-alarm rate:** on experimental crystal structures — 83/85 Astex (2.4% false-fail) and 306/308 Benchmark (0.65% false-fail) pass. Thresholds were tuned to produce exactly this. The false-*negative* rate (implausible poses that pass) is never measured.
- **Known failure modes / what a naive user gets wrong:**
  1. Treating PB-valid as a *correctness* claim. It is a necessary condition, not sufficient — a pose 30 Å from the site can be PB-valid. Gold's 55% on the Benchmark is `RMSD ≤ 2 Å AND PB-valid`; PB-valid alone is much higher.
  2. Treating PB-invalid as fatal. 2 of 85 crystal structures fail. Any pipeline that hard-rejects PB-invalid poses discards real physics ~1–2% of the time.
  3. Not realising the tool is threshold-parameterised and that defaults are *permissive*. Energy ratio 100 vs Wills et al.'s 7 is a >10× loosening; tighten it and DL numbers collapse further.
  4. Feeding a sanitised RDKit mol. The tool deliberately loads with sanitisation **off** so the sanitisation check has signal; pre-sanitising destroys the check.
  5. Ignoring protonation/charge normalisation. Stereo layers depend on `/h`, `/q`, `/p`, so an unnormalised InChI comparison produces spurious stereo failures.
  6. Highly symmetric ligands (I8P, 5A3, U71, UEV) blow up symmetry-aware RMSD mapping time — the authors blocklisted them rather than fix it.
  7. No-cofactor / no-water receptors: the intermolecular checks only see what is in the PDB you hand them. Strip cofactors and clashes with them become invisible.
  8. Naively applying force-field EM as a repair step: it lifts DL methods (DiffDock 12→35%) but *costs* classical methods 6–9 points and can push a good pose across the 2 Å line (Fig S3: 1.9 Å → 2.2 Å).

## 6. Limitations

**Admitted:**
- The 2 Å RMSD threshold is "arbitrary but commonly-used and recommended for regular-size ligands".
- Volume-overlap thresholds are necessary because real crystals already clash (81/305 in Verdonk et al.).
- Waters removed from all receptors because DL methods can't use them.
- DL models used as released, without retuning — performance could differ with tuning.
- Uni-Mol's result depends on pocket definition; a whole SI section is devoted to it, and the main-text choice (8 Å) is defended as "more comparable with the blind docking methods".
- Time-based splits are insufficient for generalisation testing (their own methodological recommendation).
- Post-hoc corrections were needed after community feedback: the symmetry-mate/crystal-contact filter came from Andrew Henry, and Eric Alcaide flagged an error in the preprint's Uni-Mol pre-processing description.

**Unadmitted / under-stated:**
1. **No uncertainty quantification of any kind.** Rankings between adjacent methods (Gold 55 vs Vina 58; DiffDock 47 vs Vina 56 on Astex) are asserted from point estimates on n = 85/308.
2. **Redocking only, cognate holo receptor.** No cross-docking, no apo, no predicted (AF2) structures. This is the easiest possible setting and inflates every method; the real virtual-screening task is harder.
3. **Search spaces are defined from the crystal ligand** for 4 of 7 methods, i.e. partial answer leakage that varies systematically by method class.
4. **Top-1 only.** 40 poses generated, one scored. Top-5 / oracle numbers would change the story materially, especially for diffusion samplers.
5. **Internal numeric inconsistencies.** Internal-clash threshold is 0.8× in Table 4 but 30% / 0.7× in §2.2.2 and Fig S11. Volume-overlap threshold is 7.5% in Table 4 but "cutoff of 5%" in Figs S18/S19 and "cutoff of 20%" in Fig S20. Cofactor prevalence is "about 45%" in the main text and 46% in the Fig S5 caption. Both waterfall captions (S6, S7) mis-state their own reading examples (S6: "37 are not within 2 Å ... 47 ligands ... pass" vs the plotted 36/48; S7: "200 are not within 2 Å ... leaving 224" vs the plotted 124/178).
6. **Checks are calibrated on the same 393 crystal structures used as the benchmark's ground truth** — the tolerance selection and the evaluation share data.
7. **No false-negative characterisation.** No adversarial/perturbed poses were constructed to measure what fraction of deliberately broken structures slip through.
8. **No runtime or cost accounting**, despite speed being the entire premise of DL docking.
9. Only 8 element types and non-covalent ligands: metalloenzyme covalent binders, boron/halogen-rich chemotypes, and macrocycles are largely out of scope.

## 7. Implications for MarigoldBench

1. **Adopt PB-validity literally as a recomputed verifier for any pose-producing task.** DiffDock is already in the MarigoldBench tool set. A task like "dock ligand X into receptor Y and submit the best pose" must be graded by the harness running `posebusters` on the submitted SDF+PDB, not by the model's reported confidence or its RMSD claim. The paper gives the exact expected difficulty: DiffDock on unseen targets is 38% at RMSD ≤ 2 Å but **12% at RMSD ≤ 2 Å AND PB-valid**, and **0.92% on targets with <30% sequence identity to PDBbind**. A DiffDock-based family scored non-compensatively will land squarely in the target 5–40% band without any artificial difficulty inflation.

2. **This is a working template for a sound physical check: deterministic, recomputable from the artifact alone, threshold-calibrated against ground truth with a measured false-alarm rate.** Every MarigoldBench check should be able to state its own false-fail rate on known-good inputs the way PoseBusters does (2/85 Astex, 2/308 Benchmark). Bake this into the check-authoring standard: before a check ships, run it on N real experimental artifacts and record the false-alarm rate; if it exceeds a few percent, the threshold is wrong. A check with an unmeasured false-alarm rate cannot support a **sound-control** condition, because you cannot distinguish a model's false alarm from the check's.

3. **Non-compensatory conjunction is the difficulty engine — and the paper quantifies the gap it opens.** TankBind goes 59% → 5.9% and Uni-Mol 22% → 2.0% purely from ANDing a validity suite onto a headline metric. Design MarigoldBench tasks so the primary metric the model will naturally optimise (RMSD, pLDDT, ipTM, docking score, R²) is *insufficient*, and the recomputed conjunction includes 3–6 orthogonal physical/statistical gates. Report the per-gate waterfall the way Fig 2 does — that tells you *which* gate is doing the discriminating and stops one accidentally-trivial gate from carrying the score.

4. **Plant "physically invalid but metrically excellent" defects — the single most transferable failure mode here.** Fig 3 is a catalogue of ready-made plants, each with a real PDB exemplar: flipped double-bond stereochemistry at 1.9 Å RMSD (7QPP/VDX), bonds 25%+ too long at 1.5 Å (1OPK/P16), non-planar aromatic ring at 2.2 Å (1TOW/CRZ), internal steric clash at 1.6 Å (1N2V/BDI), ligand interpenetrating protein at 1.6 Å (7L7C/XQ1), UFF energy ratio >100 at 1.9 Å (7LOU/IFM). In the **planted-defect** condition, hand the model a pose/structure that scores beautifully on the obvious metric and is physically impossible; correct behaviour is to detect and report it. In the **sound-control** condition, hand it a real crystal pose — and note that ~2% of real crystal poses genuinely fail a PB check, so the control must use a verified-passing structure or the false-alarm penalty is unfair.

5. **Build a leakage/generalisation task family straight from §3.2's finding that time-splits are insufficient.** Give the model a model + a test set and ask it to establish whether reported performance generalises. The correct action is to stratify by sequence identity against the training corpus (Smith–Waterman or MMseqs2), not merely to check release dates. The harness verifies by recomputing the identity bins and checking the model's submitted stratified numbers. The **flawed-premise** variant is powerful here: "this method achieves 72% on Astex Diverse, characterise its generalisation" — where the honest answer is that 47/81 Astex complexes and 67/81 Astex proteins (>95% identity) are in the training corpus, so the premise that Astex measures generalisation is false and refusal/reframing is correct.

6. **Plant the "helpful post-processing that silently hurts" defect.** Force-field EM raises DiffDock from 12% → 35% PB-valid but drops Gold 55% → 49% and Vina 58% → 49%, and Fig S3 shows a good pose pushed from 1.9 Å to 2.2 Å. A task where the model is told "apply energy minimisation to improve your results" tests whether it *measures* the effect on its own pipeline rather than assuming a repair step is monotonically good. The harness recomputes both pre- and post-EM PB-validity and RMSD; a model that applies EM without an A/B check fails even when its final number happens to improve.

7. **Plant the protocol-knob defect using the Uni-Mol pocket sweep.** Uni-Mol goes from 22% to ~68% RMSD ≤ 2 Å purely by tightening the pocket definition from 8 Å to 6 Å around the *crystal ligand* — i.e. by leaking more of the answer into the input. This is a perfect planted defect for an evaluation-design task family: give the model a comparison protocol with an asymmetric, answer-leaking search-space definition and see whether it notices that the benchmark, not the method, is producing the result. Verification: the harness re-runs the comparison at matched search-space definitions and checks whether the model's conclusion survives.

8. **Require CIs and template clustering because this paper shows what their absence costs.** PoseBusters ranks Gold above/below Vina and slices 308 cases into three bins with no error bars; at those n the top two methods are statistically tied and several sub-bin claims are noise-dominated. MarigoldBench's template-clustered CIs are the right correction, and a genuinely hard task family is "here are two methods and 308 paired evaluations, is the difference real?" — graded by recomputing a paired test (McNemar on the paired binary outcomes, since the same complexes are scored by both methods) and checking that the model used a *paired* test and reported an interval, not a bare point difference.

9. **Reuse the 22-step Table S1 funnel as the gold standard for a dataset-construction task family.** Ask the model to build a contamination-free, quality-controlled evaluation set from the PDB. The harness recomputes the funnel and checks the submitted set for the specific traps the authors themselves hit or nearly hit: crystal symmetry mates within 5.0 Å (this filter removed 120 of 428 — a 28% cut the authors only added after external feedback), covalently bound ligands, duplicate ligands/entries, ligands with RSCC < 0.95, and unclustered near-duplicate sequences. Each of these is an independently checkable, non-negotiable gate, and the symmetry-mate one is exactly the kind of expert-only trap that separates a competent agent from a plausible-sounding one.

10. **Make "which check failed" part of the submitted artifact, and grade it.** The waterfall structure means a model can be asked not just to produce a valid pose but to *diagnose* an invalid one. The harness knows the ground-truth failing check (e.g. "tetrahedral chirality changed"), so it can verify the model's diagnosis exactly, with no self-report trust and no LLM judging. Diagnosis tasks are cheap to verify and hard to guess — 19 checks, and the per-method distributions in Figs S8–S20 show the failures are method-characteristic, not random.

11. **Copy the pinned-artifact discipline into the harness.** §S1 pins commit hashes and versions for all seven methods (DiffDock fff8f0b, Uni-Mol b962451, RDKit 2022.09.1, p2rank 2.3, …) and gives every method the *identical* ETKDGv3+UFF starting conformer. MarigoldBench episodes hitting NVIDIA NIM endpoints face silently-updating remote models; log the endpoint version with every episode, and give every condition of a task family byte-identical inputs, or the sound-control / planted-defect / flawed-premise arms are not comparable.

12. **Note the honest disclosure precedent for the paper's own errors.** The acknowledgements credit two external readers for finding a data-set defect and a protocol mis-description. Expect MarigoldBench checks to have bugs; ship the per-episode recomputed check outputs (as PoseBusters ships per-pose tables on Zenodo) so third parties can find them.

## 8. Verbatim quotes

1. **Abstract:** "However, despite claims of state-of-the-art performance in terms of crystallographic root-mean-square deviation (RMSD), upon closer inspection, it has become apparent that they often produce physically implausible molecular structures. It is therefore not sufficient to evaluate these methods solely by RMSD to a native binding mode."

2. **§1 Introduction:** "The five DL-based docking methods we test in this paper all claim better performance than standard docking methods but these claims rest entirely on RMSD. None of these methods test their outputs for physical plausibility."

3. **§2.2.2 Intramolecular validity (threshold calibration against ground truth):** "The tolerance used throughout this manuscript is 25 % for bond lengths and bond angles and 30 % for non-covalently bound pairs of atoms e.g.: if a bond is less than 75 % of the Distance Geometry bond length lower bound, it is treated as anomalous. This was selected as all but one of the crystal ligands in the Astex Diverse set and all of those in the PoseBusters Benchmark set pass at this threshold."

4. **§3.1 Results on the Astex Diverse set (contamination in the legacy benchmark):** "47 of the 81 complexes in the Astex Diverse set are in the PDBbind 2020 General Set and 67 out of the 81 of the Astex Diverse set proteins have more than 95 % sequence identity with proteins found in PDBbind 2020 General Set."

5. **§4 Discussion (time-splits are insufficient):** "The most commonly-used train-test approach for building DL-based docking models is time-based, e.g., complexes released before a certain date are used for training and complexes released later for testing. Based on our results, we argue that this is insufficient for testing generalisation to novel targets and the sequence identity between the proteins in the training and test must be reported on."

6. **§4 Discussion (the low-identity collapse):** "Our analysis of the targets with sequence identity lower than 30 % to any member of PDBbind General Set v2020 revealed that across all of the DL-based docking methods almost no physically valid poses were generated within the 2 Å threshold."

7. **§2.2 (definition of the pass criterion):** "Molecule poses which pass all tests in PoseBusters are 'PB-valid'."

8. **§S9 (protocol knob dominates the headline):** "Under the tight pocket definition Uni-Mol performs better than any of the blind docking methods (SI Figure S21)."
