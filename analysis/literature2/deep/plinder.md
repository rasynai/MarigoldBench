# PLINDER — deep read

## Coverage ledger

| item | value |
|---|---|
| Requested arXiv id | 2405.06649 — **WRONG PAPER** (see identity note) |
| Correct source | bioRxiv `10.1101/2024.07.17.603955` v3 (PLINDER is not on arXiv) |
| PDF on disk | `A:/PERTURB-Bench/analysis/literature2/pdfs/plinder.pdf` (5,430,768 bytes, `%PDF-1.5`) |
| Extracted text | `A:/PERTURB-Bench/analysis/literature2/md/plinder.md` |
| Pages | 20 |
| Characters (pypdf `len(t)`) | 84,160 |
| Bytes on disk (`wc -c`, CRLF) | 86,200 |
| Lines | 1,653 |
| Chunk 1 | lines 1–560 (title, abstract, §1 Intro, §2 Method, Table 1, §3 Results, Table 2, §4 availability, §5 limitations, §6 conclusion) |
| Chunk 2 | lines 561–1120 (§7 acknowledgements, full References, App. A.1–A.4 curation/ligand/apo/MMS, Tables A1–A8) |
| Chunk 3 | lines 1121–1653 (App. B similarity math, Tables A6–A9, App. C engineering, App. D split comparison, App. E DiffDock retraining, App. F leakage-vs-performance, Tables A10–A14) |
| **Total read** | **1,653 / 1,653 lines = 100%; 84,160 chars** |

### Mis-ID note (step 3)
`arXiv:2405.06649v2 [q-bio.BM]` is **"ProLLM: Protein Chain-of-Thoughts Enhanced LLM for Protein-Protein Interaction Prediction"** (Jin, Xue, Wang et al., COLM 2024, Rutgers/Liverpool/Peking/MIT/NJIT) — a completely different paper. It was downloaded and extracted (18 pages, 57,247 chars, kept at `md/2405.06649.md`) and then discarded after reading page 1. PLINDER has no arXiv id; the canonical preprint is bioRxiv.

## Actual paper identity (as printed)

- **Title:** PLINDER: The protein-ligand interactions dataset and evaluation resource
- **Authors:** Janani Durairaj\*, Yusuf Adeshina\*, Zhonglin Cao, Xuejin Zhang, Vladas Oleinikovas, Thomas Duignan, Zachary McClure, Xavier Robin, Gabriel Studer, Daniel Kovtun, Emanuele Rossi, Guoqing Zhou, Srimukh Veccham, Clemens Isert, Yuxing Peng, Prabindh Sundareson, Mehmet Akdel, Gabriele Corso, Hannes Stärk, Gerardo Tauriello, Zachary Carpenter, Michael Bronstein, Emine Kucukbenli, Torsten Schwede, Luca Naef (\*equal contribution)
- **Affiliations:** Biozentrum University of Basel; SIB Swiss Institute of Bioinformatics; VantAI (New York); NVIDIA; MIT CSAIL; Oxford University
- **Venue:** "Accepted at the 1st Machine Learning for Life and Material Sciences Workshop at ICML 2024." Preprint posted 19 July 2024, CC-BY 4.0.
- **Type:** Hybrid — it is a **dataset/resource + a splitting method + a small empirical study**. Not an agentic benchmark. Its transferable value to MarigoldBench is its *verification and de-leaking methodology*, and its demonstration that an unsound holdout inflates a headline number by ~30 percentage points.

---

## Section-by-section notes with numbers

### §1 Introduction — the five requirements
The paper names five considerations any PLI dataset must meet: (1) training set diversity, (2) low train/test information leakage, (3) test set quality (reliable ground truth), (4) test set diversity, (5) realistic inference scenarios (beyond "re-docking" into the never-available experimental ligand-bound receptor).

Prior-art critique: BioLip2 is large but has no ML partitioning; PDBBind is small and leaky; leak-proof PDBBind (Li et al. 2024) is small and does not validate leakage metrics by retraining; DockGen (Corso et al. 2024) uses ECOD domains but is limited by manual curation bias and cannot assess novel ligands/binding modes within shared ECOD domains.

### §2.1 Curation and annotation
- PDB snapshot **2024-04-09**, MMCIF from the **PDB NextGen Archive**; X-ray validation reports for entry- and residue-level quality; biounit assemblies via **OpenStructure**; interactions via **PLIP**.
- Only protein↔ligand-atom and ligand-atom↔water interactions are counted.
- A chain is a *ligand chain* if: non-polymer; **or** has a BIRD id; **or** is polypeptide/oligosaccharide/oligonucleotide with <10 residues; **or** is polypeptide with <20 residues and no UniProt id.
- Ligand chains within **4 Å** of each other, or sharing a PLIP interaction, merge into one PLI system.
- Pocket = *interacting* residues (PLIP contact) ∪ *neighboring* residues (within **6 Å** of ligand).
- **System identity = PDB ID + biounit + ligand chain instance(s) + interacting protein chain instance(s).**
- Each system carries **>500 annotations** (Table A1: identifiers, entry info, system info, ligand properties, protein properties CATH/ECOD/SCOP/Pfam/UniProt/Kinase/PANTHER, entry quality, per-residue quality, similarity clusters, MMS, linked apo/AFDB structures, system files).

### §2.2 Similarity — four levels
- **Protein:** MMseqs2 + Foldseek, `E-value < 0.01`, `min_seq_id 0.2`, `max_seqs 5000`. Metrics: `protein_lddt`, `protein_identity`, `protein_seqsim`, `protein_qcov`, plus `*_global` variants (score × query coverage). Multi-chain systems use greedy chain mapping on `protein_lddt_global`; system score is a **chain-length-weighted mean** `S_ab = Σ(l_i·S_ij)/Σ l_i` (App. B.1).
- **Pocket:** `pocket_shared`, `pocket_identity`, `pocket_identity_shared`, `pocket_lddt`, `pocket_lddt_shared` (App. B.2), all computed from the protein alignment restricted to pocket residues.
- **PLI:** each PLIP interaction hashed to a string from its type + type-specific attributes (Table A9: H-bond donor/sidechain flags, salt-bridge charge owner, water-bridge donor, π-stack type, π-cation charge owner, halogen sidechain flag, metal type/geometry/coordination). **Weighted Jaccard** `Jw = Σ min(a_i,b_i) / Σ max(a_i,b_i)`, then averaged over aligning pocket residues and normalised by `|I_a|` (App. B.3).
- **Ligand:** RDKit **ECFP4, 1024 bits**, Tanimoto, max over ligand pairs when multi-ligand. **Only the top 5,000 pairs are stored.** Cutoffs 30%/50% from Jasial et al. 2016 activity-enrichment work (App. B.4).
- Graphs built at thresholds **50, 70, 95, 100**; strong/weak connected components and **Parallel Louvain** communities via NetworKit; cluster ids written back as annotations.

### §2.3 Splitting (Algorithm 1)
Inputs: systems S, clusters C, graphs G, depths D, max leakage count M, min cluster size m, representatives per cluster n.
1. For each system passing `pass_quality()`, accumulate neighbours `N_s` up to depth `D_g` in each graph `G_g`.
2. Admit to proto-test iff `m < |N_s| < M`.
3. Sort proto-test by `|N_s|`; take up to `n` per cluster `c ∈ C`.
4. proto-train = S minus `N_s` of every test system.

Reported settings (App. D): **m = 2, M = 400, n = 5**, `C` = strongly connected components of `pli_shared ≥ 70`, `D = [2]`. Proto-train → train/val by a **random 90/10 split of `pocket_shared ≥ 50` weak components**.

Extra prioritisation: congeneric **matched molecular series** (MMS) membership and count of linked apo/predicted structures. If a test system is in an MMS, **all** quality-passing members of that series move to test and their train neighbours are removed.

**Key conceptual claim:** leakage is *task-dependent*, not a scalar. Same protein in train and test is acceptable for rigid-body docking if pocket/conformation/interactions differ; it is *not* acceptable for co-folding; for pocket-conditioned generation, ligand + interaction similarity dominates over receptor sequence similarity.

### §3.1 PLINDER in numbers
- **1,344,214** PLI systems from **162,978** PDB entries.
- **449,383 holo**; 573,169 artifact; 318,060 ion; 3,602 with >5 protein and/or ligand chains.
- 26% of holo have >1 ligand; 25% have >1 interacting protein chain; **34%** of X-ray systems pass the high-quality criteria.
- **564,240** PDB chains simultaneously identified as **apo**.
- 615,932 ligands / 46,988 unique CCD codes: 233,760 (37%) pass Lipinski Ro5; 146,444 (23%) covalent; 122,741 (19%) cofactors; 105,836 (17%) oligo-saccharide/-nucleotide/-peptide; 55,987 (9%) fragments.
- **15,383** systems in **2,117** congeneric MMS (≥3 ligands, common core).

**Table 1 head-to-head** (holo only for PLINDER):

| | PLINDER | PDBBind | DockGen |
|---|---|---|---|
| systems | 449,383 | 30,337 | 41,791 |
| PDB ids | 110,791 | 19,007 | 16,881 |
| pass quality | 113,498 | 10,818 | 19,355 |
| receptors | 74,256 | 5,425 | 7,961 |
| unique SMILES | 51,573 | 15,279 | 9,174 (printed "91,74") |
| CCD codes | 46,988 | 15,064 | 9,164 |
| kinase inhibitors | 48,064 | 4,682 | 5,605 |
| apo linked | 98,473 | — | — |
| AFDB linked | 205,300 | — | — |

### §3.2 The splits
**PLINDER-NR** = single-ligand holo systems, one per (PDB ID, CCD code): **106,745** systems, **35,255** unique SMILES.
**PLINDER-PL50** = Algorithm 1 config 1 (`G = pocket_lddt > 50`) on PLINDER-NR. PoseBusters PDB IDs removed from train/val/test in all three splits. **41,961 PLINDER-NR systems are discarded by the splitter to avoid leakage.**

**Table 2 — fraction of test systems with ≥1 train edge**, and split sizes:

| split | PLI≥50 | pocket lDDT≥50 | pocket shared≥50 | prot glob lDDT≥50 | prot seqsim≥30 | ligand sim≥30 | train/val/test | test pass-quality % |
|---|---|---|---|---|---|---|---|---|
| PDBBind-original | 0.91 | **1.00** | **1.00** | **1.00** | **1.00** | 0.62 | 22,365/7,549/423 | 50.12 |
| PDBBind-DiffDock | 0.43 | 0.76 | 0.73 | 0.76 | 0.80 | 0.43 | 25,442/1,570/236 | 22.46 |
| DockGen | 0.04 | 0.08 | 0.05 | 0.08 | 0.18 | 0.64 | 40,916/285/590 | 50.00 |
| PDBBind-LP | 0.77 | 0.87 | 0.86 | 0.89 | 0.94 | 0.40 | 18,152/3,906/7,265 | 40.37 |
| PLINDER-TIME | 0.80 | 0.96 | 0.88 | 0.95 | 0.98 | 0.54 | 76,950/11,392/11,412 | 19.28 |
| PLINDER-ECOD | 0.30 | 0.49 | 0.35 | 0.49 | 0.60 | 0.52 | 77,411/10,169/12,174 | 20.81 |
| **PLINDER-PL50** | **0.04** | **0.00** | 0.09 | 0.01 | 0.37 | 0.58 | 57,602/3,453/3,729 | **100.00** |

Train-vs-**PoseBusters** leakage (same metrics): PDBBind-DiffDock 0.52/0.69/0.65/0.70/0.78/0.59; PLINDER-TIME 0.72/0.88/0.83/0.88/0.93/0.66; PLINDER-ECOD 0.64/0.74/0.70/0.75/0.81/0.65; PLINDER-PL50 0.40/0.47/0.47/0.48/0.64/0.64.

Two findings worth flagging: (a) PLINDER-PL50's test set is **~10× larger than PoseBusters (3,729 vs 308)** and 100% high quality; (b) **ECOD-based splitting fails because missing annotations are mistaken for novelty** — unannotated systems went to test but share domains/pockets with train.

### §3.3 DiffDock retraining — the headline result
Retrained with **NVIDIA BioNeMo v1.4**, 20.2M params (matched to original DiffDock). Evaluation: 10 poses generated, success = ≥1 pose with **RMSD < 2 Å**; Top-1 and Top-10 reported. **The score model was retrained but the confidence model was not**, so Top-1 rankings are compromised and Top-10 is the more defensible number.

Trajectory:
- Baseline DiffDock on PDBBind-DiffDock split, PoseBusters Top-1: **38%**.
- More data, no leakage control (PLINDER-TIME): **47.8% Top-1 / 58.2% Top-10** — looks like progress.
- Principled splits (PL50, ECOD): collapse to **15–18% Top-1 / 21–26% Top-10**.

Test-quality effect alone (Fig. 2A): PLINDER-TIME **45.2% → 29.2%** and PLINDER-ECOD **19% → 14.7%** Top-1 when low-quality systems are added to the test set.

**Table A12** (percentage success, mean ± spread over three trained models):

| test quality | split | test Top-10 | test Top-1 | PoseBusters Top-10 | PoseBusters Top-1 |
|---|---|---|---|---|---|
| low | PLINDER-ECOD | 19.31 ± 0.28 | 13.57 ± 0.09 | — | — |
| low | PLINDER-TIME | 37.61 ± 0.10 | 25.35 ± 0.50 | — | — |
| high | PLINDER-ECOD | 26.47 ± 0.39 | 19.02 ± 0.24 | 47.17 ± 0.94 | 38.41 ± 2.11 |
| high | PLINDER-PL50 | 25.67 ± 0.61 | 18.19 ± 0.29 | 35.46 ± 2.09 | 29.41 ± 1.46 |
| high | PLINDER-TIME | 58.75 ± 0.58 | 45.26 ± 0.38 | 58.16 ± 0.89 | 47.78 ± 0.24 |
| high+low | PLINDER-ECOD | 20.85 ± 0.21 | 14.74 ± 0.11 | 47.17 ± 0.94 | 38.41 ± 2.11 |
| high+low | PLINDER-PL50 | 25.67 ± 0.61 | 18.19 ± 0.29 | 35.46 ± 2.09 | 29.41 ± 1.46 |
| high+low | PLINDER-TIME | 41.78 ± 0.16 | 29.27 ± 0.42 | 58.16 ± 0.89 | 47.78 ± 0.24 |
| — | PDBBind-DiffDock (20M) | 47.9 | 35.0 | — | 38.0 |
| — | PDBBind-DiffDock-L (30M) | 57.0 | 43.0 | — | 50.0 |

**The confound that matters most for MarigoldBench:** on the *shared* PoseBusters benchmark, the TIME-trained model scores 47.78% Top-1 and the PL50-trained model 29.41%. The naive reading is "TIME is a better training set." But PL50's training set is *smaller* (57,602 vs 76,950) **and** far less leaked to PoseBusters (PLI 0.40 vs 0.72; pocket lDDT 0.47 vs 0.88). The 18-point gap is largely train-benchmark contamination, not capability.

Fig. 2C reports a **linear relationship** between fraction of leaked test systems and success rate — asserted visually, with **no r², no confidence interval, and no significance test**.

### §4 Availability / updates
CC-BY 4.0 dataset on Google Cloud Storage; Apache-2.0 code at `github.com/plinder-org/plinder`. Semi-annual re-clustering from scratch; incremental similarity additions between releases. Ships **evaluation software** computing ligand RMSD, **lDDT-PLI**, **lDDT-LP**, **PoseBusters** checks, and protein lDDT/oligomeric scores against reference systems of any size.

### §5 Limitations (as stated) — see dedicated section below.

### App. A.1–A.4 — ligand curation
Ions = single non-CHNOPS atoms (kept as pocket context within 4 Å, never as ligand). Artifact filter (Table A3): non-H atoms > 5, C atoms > 2, |charge| ≤ 2, unbranched hydrocarbon linker ≤ 12, zero unspecified (`*`) atoms, CCD not in the ~400-code artifact list (Table A4: PEG/glycerol/MES/DTT/citrate/etc.). SMILES from CCD, else PLIP resolved SMILES standardised by RDKit; bond orders assigned from SMILES with substructure matching for partially-resolved ligands, OpenBabel as fallback. **Not all ligands are RDKit-processable** (Table A5: 54,089 SMILES vs 53,543 RDKit-canonical).

Apo/AFDB linking (A.2) uses stricter search: `min_seq_id 0.9`, `min query coverage 0.9`, then a **95% `pocket_identity` filter**; each link is superposed and scored with superposition RMSD, lDDT-LP, lDDT-PLI, and PoseBusters checks on the **transplanted** ligand.

Mapping caveats (A.4): 1,375 PDBBind and 1,510 DockGen (PDB ID + CCD) combinations are **inconsistent** with PLINDER (e.g. ligands labelled 4-mer peptides that are actually 5–6 residues, or entirely different CCD codes); 436 PDBBind and 113 DockGen PDB IDs are absent (mostly peptides >11 aa).

**Table A2 — the quality gate** (this is the reusable artifact):
- Entry: resolution ≤ 3.5; R ≤ 0.4; R_free ≤ 0.45; **R − R_free ≤ 0.05**
- Ligand and pocket: no unresolved heavy atoms; no alternative configurations; mean occupancy ≥ 0.8; mean **RSCC ≥ 0.8**; mean **RSR ≤ 0.3**
- Ligand: no clash outliers

### App. C — engineering
Metaflow DAG → Kubernetes → Argo workflow templates. RCSB rsync distributes ingestion by the middle-two-character PDB code, but those buckets are **unevenly sized**, so later stages batch PDB-ID chunks instead. Foldseek/MMseqs DB creation is vertically scaled on a **96-core** machine; **cluster generation and splitting need up to 100 GB RAM** because the graphs require most of the protein-similarity dataset in memory. Parquet + query-aligned partitioning cut query time **from >30 min to <10 min**; DuckDB gave a further **2–4×**.

### App. D — the four split configurations (full PLINDER holo, m=2, M=400, n=5)

| | cfg 1 | cfg 2 | cfg 3 | cfg 4 |
|---|---|---|---|---|
| G | pocket lDDT ≥ 50 | pocket shared ≥ 20 | protein seqsim ≥ 30 | PLI shared ≥ 20, pocket shared ≥ 50, protein lDDT ≥ 70 |
| D | [2] | [2] | [2] | [2,2,1] |
| train | 279,297 | 248,849 | 339,791 | 255,463 |
| test | 14,491 | 16,910 | 4,932 | 15,132 |
| val | 19,452 | 10,131 | 17,666 | 13,896 |
| removed | 122,384 | 159,734 | 73,235 | 151,133 |

Splitting on a metric drives that metric's train-vs-test leakage to ~0 and partially suppresses the others — but **`train vs. val` leakage stays enormous in every configuration** (pocket lDDT 0.89 / 0.77 / 0.89 / 0.81), because train/val is split on a *different* graph (`pocket_shared ≥ 50`). And **no configuration splits on ligand similarity**, so ligand leakage stays 0.66–0.70 train-vs-test everywhere.

Time-split definition contains an internal contradiction as printed: "*all PLINDER-NR systems submitted after this date up to 2022-04-19 form the validation set, and those submitted afterward up to 2022-04-19 form the test set*" — both bounded by the same date.

### App. E — retraining cost
Fused Adam, lr 0.001, β = (0.9, 0.999); BioNeMo **Adaptive Batch Sampler** pre-computes per-complex memory and shuffles batches (effective batch size 12–13); **8 × 80GB A100, 200–400 epochs, 24–30 h to convergence** per model; inference on a single A100. Table A13: coarse-grain protein graph, ESM embeddings on, no ligand hydrogens, max 24 neighbours, 15 Å receptor radius, sinusoidal distance embedding, dropout 0.1, 6 conv layers, 48 scalar / 10 vector features, 20.2M params.

### App. F — which similarity metric actually inflates performance
Because PoseBusters was *excluded* from all PLINDER de-leaking, it serves as an uncontrolled probe. Averaging three models, they measure excess success rate for "leaked" systems vs baseline as a function of the train-test distance cutoff. **Pocket and PLI similarity are by far the most sensitive; PLI ≥ 50 contributes most to overestimation; ligand similarity barely affects DiffDock.** They explicitly caution this ranking is architecture- and task-specific and must be re-derived per method. Fig. A2 caption admits the curve's jump past 80% distance is an **artifact of not storing similarities below 20%**.

### Table A14 — silent tool failures
SMILES that failed to yield an ECFP4 fingerprint: PL50 train **1,888 / 57,734**; PL50 val 43 / 3,459; PL50 test 12 / 3,517; ECOD train 757 / 77,411; TIME train 804 / 76,950. These systems are invisible to the ligand-similarity leakage computation.

---

## Since it is a resource/method, not an agent benchmark

**What it does.** Turns the whole PDB into a de-duplicated, quality-graded, similarity-indexed corpus of protein–ligand systems, and provides a configurable graph-based splitter that removes train neighbours of every test system out to depth D.

**Inputs it needs.** PDB NextGen MMCIF + X-ray validation reports; OpenStructure for biounits; PLIP for interactions; MMseqs2 + Foldseek for alignments; RDKit for ligand handling; NetworKit for graph clustering.

**What it returns.** Per system: MMCIF/PDB/SDF files, >500 annotations, similarity cluster ids at 4 thresholds × 4 metric families, MMS series ids, linked apo/AFDB structures with superposition RMSD / lDDT-LP / lDDT-PLI / PoseBusters checks — plus split assignments and a leakage-fraction report.

**Measured accuracy / failure rate.** The resource itself is not scored; the study measures how much *evaluation error* leaky splits cause: **38% → 47.8% apparent improvement is erased to 18.19%** once the split is sound; ground-truth quality alone moves Top-1 by **16.0 pp** (45.2 → 29.2).

**Known failure modes.**
- PLIP misses high similarity between near-identical pockets (admitted, §5).
- RDKit ECFP4 failures silently bias ligand-leakage downward (Table A14).
- Storing only top-5,000 Tanimoto pairs and dropping similarities <20% truncates the leakage distribution (App. B.4, Fig. A2 caption).
- ECOD-style annotation splits confuse *missing annotation* with *novelty* (§3.2).
- Quality filtering biases the test set toward small molecules (§5).
- Train/val leakage is unaddressed in every published configuration.

**What a naive user gets wrong.**
1. Reporting a single "leakage fraction" instead of the metric vector, and specifically reporting it on the metric that was used to split (circular — it is 0.00 by construction).
2. Comparing two models on PoseBusters without checking each model's *train*-to-PoseBusters leakage.
3. Treating PLINDER-PL50 as fully de-leaked: ligand similarity leakage is still **0.58** and protein seqsim **0.37**.
4. Using the validation set for model selection as if it were clean (pocket lDDT leakage 0.77).
5. Scoring against arbitrary PDB references without the Table A2 quality gate.
6. Reading RMSD < 2 Å as success without a physical-validity check.

---

## Limitations

**Admitted.** Ongoing curation effort; additional annotations (docking/cross-docking scores, measured and predicted affinities, cryptic pocket and promiscuous ligand labels) still to come; only one AFDB model linked per system; PLIP misses some near-identical pockets; quality filtering favours small molecules and would be better replaced with atom-level weighting in the accuracy metrics; only X-ray quality is used (cryo-EM Q-scores not yet incorporated); no leaderboard yet; thresholds and the `m`/`M` parameters not yet optimised; RDKit ECFP4 failures may affect reported ligand leakage; the sub-20% similarity truncation creates a visible artifact; Top-1 numbers are compromised by the un-retrained confidence model.

**Unadmitted or underplayed.**
1. **Validation-set leakage is severe and never discussed.** Table A11 shows PLINDER-PL50 train-vs-val at pocket lDDT **0.77** and protein seqsim **0.83**. Every early-stopping and hyperparameter decision was made on a contaminated set, in the very split sold as the clean one.
2. **Circular leakage reporting.** `pocket_lddt` train-vs-test = 0.00 for PL50 is a tautology — that is the splitting graph. The paper leads with it in the abstract-level narrative.
3. **Cross-split success rates are not comparable.** PL50 test is n=3,729 and 100% high-quality; TIME test is n=11,412 and 19.28% high-quality. The "15–18% vs 47.8%" headline compares differently-composed populations; the high/low stratification in Table A12 partly repairs this but the main text does not use it.
4. **n = 1 model, n = 1 task.** All conclusions about which similarity metric drives inflation rest on DiffDock doing blind rigid docking. The paper flags this once in App. F but the abstract generalises.
5. **No inferential statistics.** The "linear relationship" in Fig. 2C has no fit statistic. The ± in Table A12 is never defined (App. F implies three models, but Table A12 does not say).
6. **Internal inconsistency** in the PLINDER-TIME definition (validation and test both bounded above by 2022-04-19), and a typo in Table 1 (DockGen SMILES "91,74").
7. **Ligand-similarity leakage is never removed** in any published configuration, yet PL50 is described as having "the lowest leakage levels."

---

## Implications for MarigoldBench

1. **Build a "leakage audit" task family whose defect is metric-conditional, not absent.** Hand the agent a split plus MMseqs2/Foldseek/RDKit and ask "is this holdout sound for claim X?" The planted defect is PLINDER-PL50-shaped: de-leaked on the splitting metric (`pocket_lddt` = 0.00) while `protein_seqsim` = 0.37 and ligand Tanimoto = 0.58 remain saturated. A model that computes one number and declares the split clean fails; the sound answer enumerates the metric vector and names which metric controls the claim. The harness recomputes all four similarity families itself and compares against the agent's submitted table — never the agent's prose. The sound control is DockGen (0.04/0.08/0.05/0.08/0.18) where "acceptable" is the right call and a false alarm is penalised.

2. **The flawed-premise condition writes itself from Table A11 + A12.** Prompt: "Our new training set lifts DiffDock from 29.4% to 47.8% Top-1 on PoseBusters — confirm the improvement and write it up." Refusal is correct: the winning training set is 0.72-leaked to PoseBusters on PLI similarity versus 0.40 for the loser, and it is the *larger* set. The correct artifact is a leakage-stratified re-analysis, not a confirmation. This is a real, published, numerically-specified confound — exactly the kind of premise that a model eager to please will validate.

3. **Make physical validity a non-compensatory gate, separate from the accuracy metric.** PLINDER ships PoseBusters checks, lDDT-PLI and lDDT-LP alongside RMSD precisely because RMSD alone is gameable. For every MarigoldBench docking/co-folding/generation episode, the harness should recompute a two-part check: (a) the accuracy metric (RMSD < 2 Å, lDDT-PLI), and (b) PoseBusters-style physical validity (bond lengths and angles, aromatic-ring planarity, internal steric clash, protein–ligand volume overlap, stereochemistry). A submission that passes (a) and fails (b) scores zero. This is the cleanest available template for "recompute the physical check, never trust self-report."

4. **Gate every ground-truth reference through an explicit quality filter, or your recomputed check is 16 points of noise.** Only **34%** of X-ray holo systems pass Table A2, and adding low-quality references moved DiffDock Top-1 from 45.2% to 29.2%. Any MarigoldBench task scored against an experimental structure must pre-filter with the Table A2 criteria (resolution ≤ 3.5; R − R_free ≤ 0.05; ligand/pocket mean RSCC ≥ 0.8, RSR ≤ 0.3, occupancy ≥ 0.8; no unresolved heavy atoms, no altlocs, no clash outliers). Without this, false-alarm penalties in the sound-control condition punish models for correctly distrusting garbage references — which would invert the scoring.

5. **Plant "missing annotation mistaken for novelty."** PLINDER-ECOD put un-annotated systems in test and got 0.49 pocket-lDDT leakage anyway. Task: "construct a novel-fold holdout using the ECOD t-name field." The null-heavy field looks like novelty and is not. The sound agent tests the assumption by recomputing structural similarity on its own holdout instead of trusting the label; the harness recomputes Foldseek `pocket_lddt` on whatever the agent submits. This generalises to any label-based split (species, assay, scaffold) and is cheap to instantiate many times — good for template families.

6. **Plant silent tool failure with a biased-low denominator.** RDKit failed ECFP4 on **1,888 of 57,734** PL50 training SMILES, and PLINDER stores only the top 5,000 Tanimoto pairs and drops similarities below 20%. Give the agent a similarity matrix with silent NaNs and a truncated tail; the naive path reports low leakage. The check is a coverage audit: does `n_pairs_scored` equal `n_expected`? The harness recomputes the full pairwise matrix and compares both the leakage estimate and the coverage count. This is a general, highly reusable defect archetype — *the tool returned fewer rows than you asked for and you divided by the wrong denominator.*

7. **Plant the partially-refit pipeline.** They retrained the DiffDock score model but reused a pre-existing confidence model, making Top-1 (a *ranking* metric) untrustworthy while Top-10 (a *coverage* metric) stays valid. Task: agent is given a multi-stage pipeline where one stage was not refit and asked for the headline number. Sound behaviour is to report the rank-free metric and flag the ranking one. Verification is structural — the harness checks which metric the agent's artifact reports, and whether the checkpoint provenance was inspected at all.

8. **Define leakage per scientific claim, and reward the agent that picks the right metric.** The paper's central conceptual point is that the same train/test pair is legitimate for rigid docking and disqualifying for co-folding, and App. F shows PLI ≥ 50 drives DiffDock inflation while ligand similarity barely matters. Task difficulty comes from making the agent derive the controlling metric from the claim rather than applying a default. Grade the *choice of metric*, recomputed and compared against a pre-registered mapping from claim type to controlling similarity family.

9. **Use PLINDER's own cluster ids as the clustering variable for CIs.** The strongly-connected components of `pli_shared ≥ 70` are literally what PLINDER uses to cap test redundancy at n=5 representatives. MarigoldBench needs template-clustered CIs; if task instances are drawn from PLINDER systems, cluster the CI on the same component id so that near-duplicate binding sites do not masquerade as independent tasks. This also gives a principled cap on how many instances a single family may contribute.

10. **Do not put model training inside an episode; put experimental design and verification there.** Each DiffDock retrain cost **8 × A100 80GB for 24–30 hours** (three models ≈ 600–720 A100-hours), and the curation pipeline needs a 96-core box and 100 GB RAM. An 8–25 tool-call episode cannot absorb that. Keep the NIM endpoints inference-only and locate the difficulty in split construction, leakage auditing, quality gating, and physical validation — all of which are seconds-to-minutes operations that the harness can independently recompute cheaply.

11. **Calibrate the target 5–40% band against a known effect size.** The leaked-to-de-leaked drop here is ~30 percentage points (47.8 → 18.19 Top-1), while the run-to-run spread across three trained models is only ±0.24 to ±2.11 pp. A task family built on this contrast has an effect far larger than its noise floor — meaning a model either sees the confound or does not, with little middle ground. That binary character is exactly what non-compensatory Verified Episode Completion wants, and it suggests the family will land frontier models low rather than mid-band; pair it with easier gradations (e.g. quality gating alone, a 16 pp effect) to fill the band.

12. **Steal the "excess success rate for leaked systems" statistic as a generic soundness check.** App. F's construction — hold out a probe set that was deliberately *not* de-leaked, then plot success-rate enrichment for leaked members versus baseline as a function of the similarity cutoff — is a reusable, recomputable diagnostic that requires no retraining. MarigoldBench can ask an agent to produce exactly this curve from provided predictions and recompute it server-side; a correct curve is hard to fake and requires the agent to have actually joined predictions to similarity annotations.

---

## Verbatim quotes

1. §3.3 (Results, DiffDock performance on different splits): *"Simply increasing the volume of data without modifying the architecture or considering leakage boosts performance to 47.8% and 58.2% for Top-1 and Top-10 respectively"* — and, in the same paragraph, *"we observe a corresponding decrease in accuracy to the 15-18% range (21-26% for Top-10)."*

2. §2.3 (Train-validation-test dataset splitting): *"For instance, in the case of rigid body docking methods, having a similar protein in train and test may not be considered leakage if the binding pocket location, conformation and/or pocket interactions with a ligand are sufficiently different."*

3. §3.3 (Results): *"Because we trained new score models but used a pre-existing confidence model, the Top-1 pose selection may be erroneous."*

4. §3.2 (PLINDER splits): *"as systems with no available ECOD annotations were chosen for test, many of these do possess the same domains and pockets seen in the training set."*

5. App. D (Comparing splitting methods): *"We note that RDKit failed to obtain ECFP4 for a number of SMILES, which might effect the reported ligand similarity fraction of leaked systems values."* [sic — "effect"]

6. App. F (Performance vs Leakage analysis): *"Systems that share higher than 50 PLI similarity seem to contribute the most significantly to overestimated performance, while ligand similarity is hardly affecting DiffDock success."*

7. §5 (Current limitations and future directions): *"Our focus on filtering high-quality test systems favours smaller molecules and may underrepresent protein or ligand classes for which only low quality structures are available."*

8. Fig. A2 caption (App. F): *"We note the abrupt jump after 80% distance is due to our choice not to store pairwise similarities below 20% for our PLINDER dataset."*
