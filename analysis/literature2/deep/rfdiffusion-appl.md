# Deep read: `rfdiffusion-appl` (de novo protein binder design / RFdiffusion applications)

## 0. ID CORRECTION — the assigned arXiv id was wrong

The task assigned **arXiv 2308.05318** for "De novo design of protein binders (RFdiffusion applications)".
That id resolves to a completely unrelated computer-vision paper:

> **RLSAC: Reinforcement Learning enhanced Sample Consensus for End-to-End Robust Estimation**
> Chang Nie, Guangming Wang, Zhe Liu, Luca Cavalli, Marc Pollefeys, Hesheng Wang (SJTU / ETH Zurich / Microsoft MR&AI)
> 10 pages, 47,400 chars extracted. Downloaded to `A:/PERTURB-Bench/analysis/literature2/pdfs/2308.05318.pdf`,
> text at `A:/PERTURB-Bench/analysis/literature2/md/2308.05318.md`. **Discarded after title check.**

Note that the canonical RFdiffusion paper (Watson et al., *Nature* 620:1089-1100, 2023) was never on arXiv —
it went bioRxiv -> Nature, so no arXiv id for it exists. I searched for the nearest arXiv paper matching the
**topic** ("de novo design of protein binders", with RFdiffusion as a benchmarked application) and used:

**arXiv:2512.24192v2 [q-bio.BM]** — downloaded, verified, fully read.

---

## 1. Coverage ledger

| item | value |
|---|---|
| PDF | `A:/PERTURB-Bench/analysis/literature2/pdfs/2512.24192.pdf` (5,744,122 bytes, `%PDF-1.7`) |
| Extracted text | `A:/PERTURB-Bench/analysis/literature2/md/2512.24192.md` |
| Pages | 21 |
| Total chars | **60,393** |
| Total lines | **804** |
| Chars actually paged through | **60,393 (100%)** |

Chunk ranges read with the Read tool:

| chunk | lines | purpose |
|---|---|---|
| 1 | 1–50 | title/identity verification |
| 2 | 50–449 | Intro, Method, In-silico Results, Ablations, In Vitro, Conclusion, Revision History, Contributions |
| 3 | 450–804 | Contributions/affiliations, full References [1]–[45], Appendix A (data), B (evaluation), C (baseline sampling), D (wet-lab protocols) |

Every line 1–804 was read, including the reference list and all four appendices. No ar5iv fallback was
needed (extraction >> 15,000 chars). Extraction quality: good, except that (a) figure-embedded numbers are
lost (the main binder-success bar chart is an image; in-text cross-refs render as "As shown in Figure ,"
with the number missing), and (b) some table rows have digits concatenated across columns — I reconstructed
these against the clean `SeedProteo-M` row, which has exactly 10 whitespace-separated values (see §5.3).

Additional file read for identity check only: `md/2308.05318.md`, lines 1–60 of 47,400 chars (RLSAC).

---

## 2. Actual paper identity (as printed)

- **Title:** *SeedProteo: Accurate De Novo All-Atom Design of Protein Binders*
- **Venue:** arXiv preprint, `arXiv:2512.24192v2 [q-bio.BM] 24 Feb 2026`. v1 released 31 Dec 2025;
  v2 (24 Feb 2026) **added the entire in vitro validation section**. Not peer-reviewed.
- **Authors as printed on p.1:** "1ByteDance Seed — Full author list in Contributions". Date printed:
  Feb 24, 2026. Correspondence: Quanquan Gu (quanquan.gu@bytedance.com).
- **Contributions page:** Project Lead **Wei Qu**; Contributors Yiming Ma (Peking Univ., intern),
  Fei Ye, Chan Lu, Yi Zhou, Kexin Zhang (ShanghaiTech, intern), Lan Wang, Minrui Gui (UCLA, intern);
  Overall Technical Lead **Quanquan Gu**. Affiliation 1: ByteDance Seed.
- **Artifacts:** webserver `https://seedfold.io/proteinDesign`; project page `https://seedfold.github.io/`.
  No model weights or code release stated. Wet-lab work outsourced to **WuXi AppTec (China)**.
- **Relation to the requested topic:** this is a *de novo protein binder design* method paper in which
  **RFdiffusion and RFdiffusion3 are two of five benchmarked baselines**, with exact invocation configs
  given in Appendix C. So it covers "RFdiffusion applications" as the comparison surface rather than as
  the subject. It is a METHOD/TOOL paper that *embeds* a binder-design benchmark protocol.

---

## 3. Section-by-section notes with numbers

### 3.1 Abstract / Introduction (lines 5–67)
- Claim set: (i) unconditional generation — superior length generalization and diversity; (ii) binder design
  — SOTA "among open-source methods", highest in-silico success rate, diversity, novelty; (iii) wet-lab
  validation on two therapeutic targets with **hit rates of 70%–80%** and **picomolar** affinity.
- Framing of the core technical problem: *backbone-sidechain inconsistency* — "the sidechain atoms are
  locally plausible but the derived sequence fails to fold into the global backbone structure" (line 44-46).
- Two named inference modes to trade success against diversity: **SeedProteo-R** (Robust: fewer/longer
  continuous secondary-structure segments, higher success) and **SeedProteo-D** (Diverse: more, shorter
  SS segments, richer topology, lower raw success).

### 3.2 Method (§2, lines 68–195)
- **Representation:** `atom14` schema (4 backbone + 10 side-chain atoms per residue), with **virtual atoms
  overlaid on the Cα atom** so all amino acids share one representation when identity is unknown.
- **Architecture:** AF3-like — embedder, Pairformer encoder, diffusion module. Noisy coordinates are fed
  into the encoder (transformed into a 1D sequence representation inside the embedder) because a
  sequence-based encoder fed all-`[MASK]` "would render the encoder ineffective".
- **Compute concession:** because the cubic-complexity encoder now depends on the noisy input,
  **Pairformer layers were reduced from 48 to 12**.
- **Three self-conditioning features:**
  1. **MRF sequence module** (Eq. 1): `P(x|a,z) ∝ exp[ Σ h_i(x_i|a_i) + Σ_{i<j} e_ij(x_i,x_j|z_ij) ]` —
     site bias + pairwise coupling. Replaces geometric decoding of amino-acid identity from `atom14`,
     explicitly to "avoid misclassification of structurally similar (isosteric) amino acids".
  2. **Secondary structure sequence** over `{H, E, L}` plus mask token `X` (DSSP-4 based, ref [30]),
     with gated self-conditioning (Eq. 2): `S_cond^(t) = α_t·S_pred^(t) + (1-α_t)·S_cond^(t-1)`.
  3. **Structural template** — previous denoised step's Cβ distance map, binned into a one-hot pair feature.
- **Losses:** coordinate diffusion loss (applied **without pre-aligning** target and prediction, forcing the
  model to learn equivariance), smooth LDDT, distogram, plus cross-entropy on MRF sequence and predicted SS.
- **Training (Table 5, lines 655–669):** trained from scratch, 3 stages.

| Stage | Crop | Batch | Steps | Motif % | Strict monomer | Expanded monomer | Multimer |
|---|---|---|---|---|---|---|---|
| 1 Initial | 384 | 128 | 50K | 0% | 100% | – | – |
| 2 FT-1 | 768 | 64 | 20K | 20% | 20% | 80% | – |
| 3 FT-2 | 768 | 64 | 30K | 20% | 10% | 40% | 50% |

Total 100K steps. **No GPU-hours, wall-clock, or inference cost reported anywhere in the paper.**

### 3.3 Data (Appendix A, lines 616–652)
- **Monomers:** AFDB + ESMAtlas. ESMAtlas entries were *re-predicted with AF2* from MGnify sequences
  to avoid ESMFold quality issues. Filters: **length 50–768**, **avg pLDDT > 80**, **coil fraction < 50%**.
  Foldseek + MMseqs2 clustering, centroids only -> **~0.5M structures**.
- **Multimers:** Pinder (holo PDB IDs/chains, substructures from RCSB biological assemblies), filtered on
  **coil fraction < 50% per chain** and **minimum interfacial Cβ distance < 8 Å**; Foldseek-Multimer
  clustering -> **~50,000 cluster representatives**.
- **Augmented DDI:** HumanPPI domain-domain interactions from AFDB, same filters -> **~0.1M pairs**.
  Justification: "intrachain DDI interfaces resemble interchain PPI interfaces in terms of coevolutionary
  and physicochemical properties".
- **No training cutoff date, no target-level holdout statement.** See §6.

### 3.4 Unconditional generation (§3.1, Fig. 2, Table 1)
- **Evaluation protocol (Appendix B.1):** for each generated backbone derive **exactly ONE** ProteinMPNN
  sequence, refold with **SeedFold** (their own AF3-like folding model, ref [33]) in **single-sequence**
  mode. Success = **Cα-RMSD < 2.0 Å** AND **avg pLDDT > 80**. Diversity = # unique Foldseek clusters
  *among designable cases only*. Novelty = **max TM-score vs PDB** (lower is better).
- **Topology classification:** `EEE` = >40% sheet AND <20% helix; `HHH` = >50% helix AND <10% sheet;
  both require loop fraction <45%; everything else = `HEL`.
- Headline: SeedProteo keeps **>60% success at length 1000**; baselines drop to **near-zero beyond 600**.
- **Table 1, Panel A (HHH):** SeedProteo 100%@100 -> 63%@1000. RFdiffusion: 87%@100, 73%@200,
  **fails (dash) from 300 onward**. La-Proteina 93%@100 -> 31%@1000; Proteina 88%@100 -> 4%@800, then dash.
- **Table 1, Panel B (HEL):** SeedProteo 97%@100 -> **57%@1000**. RFdiffusion 71%@100, 38%@200, 11%@300,
  **3%@400, 1%@500**, then dash. Proteina dies after 500 (5%). La-Proteina 87%@100 -> 3%@900.
- **Table 1, Panel C (EEE, β-sheet):** the hard case. SeedProteo 100%@100, 86%@200, 80%@300, 73%@400,
  50%@500 (only 1 unique cluster), **dash at 600–700**. RFdiffusion: dash@100, **20%@200 with 1 cluster**,
  dash thereafter. Explicit note: "Only lengths up to 700 are shown for EEE as **all methods failed** to
  generate valid long β-sheet structures."
- Novelty (max TM to PDB) stays in the 0.68–0.89 band for SeedProteo; the paper reads low novelty as
  "does not merely retrieve training templates".

### 3.5 Binder design benchmark (§3.2, Appendix B.2, Table 6)
- **10 targets**, taken to be "consistent with the validation set used in AlphaProteo" (ref [15]).
  Full spec in Table 6 — PDB ID, target region, hotspot residues, binder length range:

| Target | PDB | Target region | Hotspots | Length range |
|---|---|---|---|---|
| BHRF1 | 2wh6 | A:2-158 | A65,74,77,82,85,93 | 80-120 |
| SC2RBD | 6m0j | E:333-526 | E485,489,494,500,505 | 80-120 |
| IL-7RA | 3di3 | B:17-209 | B58,80,139 | 50-120 |
| PD-L1 | 5o45 | A:17-132 | A56,115,123 | 50-120 |
| TrkA | 1www | X:282-382 | X294,296,333 | 50-120 |
| Insulin | 4zxb | E:6-155 | E64,88,96 | 40-120 |
| H1 (dimer) | 5vli | A:1-50,76-80,107-111,258-322; B:1-68,80-170 | B21,45,52 | 40-120 |
| VEGF-A (dimer) | 1bj1 | V:14-107; W:14-107 | W81,83,91 | 50-140 |
| IL-17A (dimer) | 4hsa | A:17-131; B:19-127 | A94,116, B67 | 50-140 |
| TNFα (trimer) | 1tnf | A/B/C:12-157 | A113, C73 | 50-120 |

- **Sampling:** ~1,000 candidates per target — **100 candidates at every 5-residue interval** across the
  length range (e.g. SC2RBD 80–120 -> 9 bins x 100 = **900 candidates**).
- **Sequence design:** **SolubleMPNN**, **2 sequences per backbone**, sampling temperature **τ = 0.001**
  (near-deterministic). (Note: §3 body says "ProteinMPNN"; Appendix B.2 says "SolubleMPNN" — inconsistent.)
- **Validation:** SeedFold, **single-sequence with target-template mode**.
- **Success criteria (Appendix B.2):** **min PAE_interaction < 1.5**, **binder pTM > 0.8**,
  **complex RMSD < 2.5 Å**. (§3.2 body writes "PAE ≤ 1.5"; appendix writes "<1.5" — inconsistent by an
  inclusive bound.)
- Baselines: RFdiffusion, RFdiffusion3, BoltzGen, PXDesign, BindCraft. BindCraft is hallucination-based
  (gradient descent on ipTM), the rest are structure generators + MPNN.
- **The headline per-target success counts for the MPNN pipeline live in an unnumbered figure that did not
  extract.** Only Table 3 (co-design counts) and Table 2 (novelty) are recoverable as text.

- **Table 2 — novelty (max TM to PDB, lower better).** Note the **column order differs from Table 3**:

| Method | TrkA | PD-L1 | Insulin | BHRF1 | IL-7RA | SC2RBD | VEGF-A | H1 | IL-17A | TNFα |
|---|---|---|---|---|---|---|---|---|---|---|
| SeedProteo-D | 0.829 | 0.832 | 0.837 | 0.822 | 0.840 | 0.819 | 0.836 | 0.823 | 0.806 | 0.870 |
| SeedProteo-R | 0.905 | 0.913 | 0.911 | 0.872 | 0.917 | 0.858 | 0.901 | 0.890 | 0.855 | – |
| BindCraft | 0.849 | 0.856 | 0.864 | 0.847 | 0.861 | 0.863 | 0.850 | 0.830 | 0.818 | – |
| PXDesign | 0.914 | 0.929 | 0.928 | 0.924 | 0.928 | 0.917 | 0.913 | 0.888 | 0.906 | – |
| BoltzGen | 0.908 | 0.924 | 0.929 | 0.928 | 0.885 | 0.915 | 0.902 | 0.885 | 0.863 | – |
| RFdiffusion | 0.932 | 0.934 | 0.927 | 0.946 | 0.916 | 0.912 | 0.940 | – | 0.938 | – |
| RFdiffusion3 | **0.808** | 0.834 | 0.876 | 0.845 | 0.840 | – | – | 0.930 | **0.800** | – |

  RFdiffusion is the *least* novel on 7/10 targets (0.91–0.95). RFdiffusion3 actually beats SeedProteo-D on
  TrkA and IL-17A. Every method has "–" on TNFα except SeedProteo-D.

### 3.6 Co-design ablation (Table 3, lines 318–326)
Table 3 is **"Benchmarking Co-design Capabilities"** — raw model-emitted sequences, *not* the MPNN pipeline.
Reconstructed counts (out of ~1,000 per target; `SeedProteo-M` row is unambiguous and fixes the column map):

| Method | BHRF1 | SC2RBD | IL-7RA | PD-L1 | TrkA | Insulin | H1 | VEGF-A | IL-17A | TNFα |
|---|---|---|---|---|---|---|---|---|---|---|
| BoltzGen | 62 | 70 | 10 | 17 | 21 | 99 | 1 | 1 | 5 | 0 |
| RFdiffusion3 | 9 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| SeedProteo-R | 296 | 92 | 100 | 380 | 232 | 303 | 16 | 127 | 47 | 1 |
| SeedProteo-D | 139 | 80 | 52 | 265 | 143 | 181 | 25 | 45 | 17 | 3 |
| SeedProteo-M (masked SS ablation) | 133 | 77 | 25 | 154 | 143 | 189 | 12 | 47 | 13 | 1 |

  Read: RFdiffusion3's *co-design* channel is essentially dead on this benchmark (10/10 targets ≈ 0), which
  is a very different claim from RFdiffusion3-plus-MPNN. **SS conditioning ablation** (R/D vs M) shows the
  gain is real but target-dependent: PD-L1 380 vs 154 (2.5x), TrkA 232 vs 143, but Insulin 303 vs 189 and
  VEGF-A 127 vs 47 — while SeedProteo-D is *worse* than the masked baseline on IL-17A (17 vs 13 is better,
  but D < M on VEGF-A 45 vs 47 and TrkA 143 vs 143). Success counts cluster around a few hundred out of
  ~1,000, i.e. **in-silico success rates of roughly 0.1%–38% depending on target**, and TNFα is ~0 for
  everyone.

### 3.7 Discussion on co-design (§3.3)
- Honest admission: "on average, sequences derived from ProteinMPNN achieve higher success rates than those
  generated via pure co-design. This is expected, as ProteinMPNN is highly optimized for fixed-backbone
  recovery."
- The TNFα exception is the paper's most interesting scientific claim: MPNN-based methods "almost universally
  fail (0 or 1 success)" on TNFα, while co-design produces valid binders. Proposed mechanism: inverse folding
  falls into "safe" local minima with repetitive motifs — **"excessive electrostatic patterns like poly-EK or
  hydrophobic poly-A stretches"** — that optimize likelihood but violate binding constraints.

### 3.8 Sequence-decoding ablation (Table 4, lines 346–353) — unconditional
| Length | Decoding | scRMSD ↓ | scTM ↑ | pLDDT ↑ | Succ. ↑ |
|---|---|---|---|---|---|
| 100 | Baseline (atom14) | **1.11** | **0.94** | 88.56 | **0.90** |
| 100 | SeedProteo (MRF) | 1.63 | 0.93 | 88.65 | 0.84 |
| 200 | Baseline (atom14) | 3.87 | 0.86 | 78.06 | 0.68 |
| 200 | SeedProteo (MRF) | **2.08** | **0.92** | **84.36** | **0.80** |
| 300 | Baseline (atom14) | 4.71 | 0.83 | 73.40 | 0.52 |
| 300 | SeedProteo (MRF) | **2.30** | **0.91** | **80.33** | **0.76** |

**The MRF module is a net loss at length 100 (0.84 vs 0.90 success, 1.63 vs 1.11 Å scRMSD)** and only pays
off from length 200. This is a genuine reported negative — a crossover, not a uniform win. Explanation
offered: `atom14` decoding relies on local side-chain geometry and lacks long-range receptive field;
the MRF "explicitly leverages global pairwise features during inference".

### 3.9 In vitro (§4, Fig. 4, Appendix D)
- Targets: **SC2RBD** and **PD-L1**. Selection funnel: "several thousand minibinders" generated per target
  -> filter by in-silico criteria -> **Foldseek clustering for diversity** -> **10 representative minibinders
  selected per target** for expression.
- Cover-page results box: PD-L1 **10/10 expressed, 8/10 binding, best Kd 56.9 pM**; SC2RBD **10/10 expressed,
  7/10 binding, best Kd 0.41 nM**. Hence the "70%–80% hit rate".
- Fig. 4 Kd values shown: PD-L1 — 66.9 nM, 234 nM, **56.9 pM**; SC2RBD — 3.7 nM, 2.1 nM, **0.41 nM**.
  Note the wide within-target spread: PD-L1 spans **56.9 pM to 234 nM, ~4,100x**.
- **Production (D.1):** PD-L1 ECD residues 18–239 in pcDNA3.1, Expi293F + PEI at 3x10^6 cells/mL, 10 mM
  sodium butyrate at 9 h post-transfection, harvest day 5, 20 mM BTP, Ni Sepharose Excel (20 mM imidazole
  wash / 300 mM elute), TEV cleavage, Superdex 75. SC2RBD **purchased** (AcroBiosystems SPD-C82E9).
  Minibinders: N-terminal His-SUMO, BL21-CodonPlus(DE3)-RIPL, TB at 37 °C to OD600 0.75, 1 mM IPTG 4 h at
  37 °C, Ni-NTA (30 mM wash / 250 mM elute), Superdex 200 10/300 GL in 50 mM HEPES pH 8.0, 100 mM NaCl,
  1 mM TCEP, 1 mM EDTA.
- **SPR (D.2):** Biacore 8K+, 25 °C, Series S SA chip, biotin capture to **~100 RU**, ligand at 1 µg/mL,
  surface activation 1 M NaCl / 50 mM NaOH (60 s, 30 µL/min). Primary screen at **10x and 50x dilutions**
  of stock plus zero-concentration reference. Affinity by single-cycle kinetics (70 s contact, **1200 s
  dissociation**, 30 µL/min, 9-point 1:1 serial dilution) or multi-cycle (70 s contact, 600 s dissociation,
  12-point). Biacore Insight Evaluation Software v6.0.7.1750. **Fit: Langmuir 1:1 binding model.**
- All expression and SPR performed by **WuXi AppTec (China)** — i.e. the wet-lab arm is outsourced and
  blinded only in the trivial sense.

---

## 4. If it is a BENCHMARK

It is not primarily a benchmark paper, but it **defines a reusable binder-design benchmark protocol** that is
worth cataloguing because MarigoldBench can lift it almost verbatim:

- **Task count:** 10 binder targets (Table 6) + 3 topology classes x 10 length bins (100–1000) unconditional
  = 30 unconditional cells. Total ~40 evaluation cells.
- **Construction:** targets inherited from AlphaProteo's validation set; each frozen as (PDB ID, chain +
  residue range, explicit hotspot residue list, binder length range). Dense sampling grid: 100 designs per
  5-residue bin.
- **Verification method:** purely computational — inverse-fold with SolubleMPNN (2 seqs, τ=0.001), refold the
  complex with SeedFold in single-sequence + target-template mode, then threshold on
  `min PAE_interaction < 1.5` AND `binder pTM > 0.8` AND `complex RMSD < 2.5 Å`. Unconditional analogue:
  1 ProteinMPNN sequence, refold, `Cα-RMSD < 2.0 Å` AND `pLDDT > 80`.
- **Scoring:** raw count of successes out of ~1,000 — non-normalized, non-compensatory in the sense that all
  three thresholds must pass simultaneously. Secondary metrics: unique Foldseek cluster count computed
  *only over successes*, and novelty = max TM-score vs PDB.
- **Agent scaffolding:** none — this is a fixed pipeline, no LLM/agent in the loop.
- **Reported scores with uncertainty:** **no uncertainty of any kind.** No seeds, no repeats, no error bars,
  no CIs, no significance tests, in any table or figure.
- **Contamination handling:** training-set redundancy is handled (Foldseek/MMseqs2 centroid clustering), but
  there is **no statement of a temporal cutoff and no target-level holdout** for the 10 benchmark targets.
- **Cost per run:** not reported. No GPU-hours, no per-design inference time, no wet-lab cost.

---

## 5. If it is a METHOD/TOOL

**What it does.** All-atom diffusion generator for (a) unconditional monomers 100–1000 aa and (b) minibinders
conditioned on a target structure + explicit hotspot residues. Emits backbone *and* sequence (co-design), but
the recommended production path still redesigns sequence with (Soluble)ProteinMPNN.

**Inputs required.** Target structure in **mmCIF**; explicit **hotspot residue list**; target chain/residue
range; binder length (or a length range to sweep); an SS mode selection (R / D / masked). Downstream you also
need an inverse-folding model and a complex-folding model to score anything.

**What it returns.** All-atom coordinates + an MRF-decoded sequence + a predicted SS string. No confidence
score of its own — **all confidence comes from the external refolder**.

**Measured accuracy / failure rate.**
- Unconditional: 100% -> 63% success across length 100 -> 1000 (HHH); 97% -> 57% (HEL); 100%@100 -> 50%@500
  and **total failure at ≥600** (EEE).
- Binder co-design: **~0.1%–38% success per target** out of ~1,000 attempts; TNFα ≈ 0.1% for the best method
  and 0 for most.
- Wet lab: 8/10 and 7/10 binders confirmed by SPR, best Kd 56.9 pM (PD-L1) and 0.41 nM (SC2RBD).

**Known failure modes (from the paper's own data).**
1. **β-sheet topologies** — every method including SeedProteo fails beyond length 500–600.
2. **Multi-chain / oligomeric targets** — H1 (dimer), VEGF-A (dimer), TNFα (trimer) are the worst columns
   in Table 3; TNFα is near-zero for all methods.
3. **Inverse-folding degeneracy** — ProteinMPNN produces "poly-EK" / "poly-A" repetitive motifs that pass
   likelihood but fail binding; this is the stated cause of universal TNFα failure in the MPNN pipeline.
4. **Mode collapse at length** — RFdiffusion and Proteina produce "few to no unique clusters at long lengths";
   note Table 1 Panel C shows SeedProteo at 500 aa has 50% success but only **1 unique cluster** — a
   high success rate that is actually one structure repeated.
5. **MRF decoding hurts short proteins** (Table 4, length 100).
6. **Backbone-sidechain inconsistency** — the motivating failure mode: locally plausible side chains whose
   implied sequence will not fold to the global backbone.

**What a naive user gets wrong.**
- **Reporting the raw success count as a success *rate* without the denominator.** The denominator is a
  length-stratified grid (100 per 5-residue bin), not a flat sample; a method that only works at one length
  can look good in aggregate.
- **Computing diversity/novelty over all designs instead of only over successes.** The paper computes both
  *exclusively on the designable subset* — mixing that up inflates diversity with garbage.
- **Using 8 ProteinMPNN sequences (the community default) and calling it the same metric.** This paper uses
  **1** sequence unconditionally and **2** for binders. Success rates are not comparable across sequence
  budgets, and neither is the variance.
- **Treating the wet-lab "hit rate" as the pipeline's success rate.** It is conditioned on: in-silico
  threshold pass -> Foldseek diversity clustering -> hand-selection of 10 representatives, out of "several
  thousand" generated. The end-to-end design-to-binder rate is ~0.2–0.3%, not 70–80%.
- **Forgetting the deterministic-noise flag for RFdiffusion binders** (`noise_scale_ca=0`,
  `noise_scale_frame=0`). Leaving defaults materially degrades RFdiffusion binder results.
- **Confusing pTM with ipTM/PAE_interaction.** The criterion is *binder* pTM > 0.8 **and** min interchain
  PAE < 1.5 — passing pTM alone says nothing about the interface.

**Baseline invocation details (Appendix C) — directly reusable as ground truth for tool-config tasks.**
- RFdiffusion binder: `noise_scale_ca = 0`, `noise_scale_frame = 0` ("the authors suggest that this
  deterministic setting yields superior performance for specific binder design scenarios").
- RFdiffusion3: RosettaCommons `foundry`, commit **7f6656e**, `align_trajectory_structures=False`.
- BoltzGen: commit **58c1eed**, `protein-anything` protocol, inference budget = number of desired designs.
- BindCraft: `default_4stage_multimer` under advanced setting, **filtering and early stopping disabled**.
- PXDesign: commit **ec6615c**, `Generation Only` mode.
- La-Proteina: `LD1_ucond_notri_512.ckpt` (len 100–500), `LD3_ucond_notri_800.ckpt` (600–1000).
- Proteina: `proteina_v1.1_DFS_200M_tir.ckpt` (100–500),
  `proteina_v1.6_DFS_200M_notri_long_chain_generation.ckpt` (600–1000).
- Global policy: "we **disable any built-in auxiliary modules**—such as pre-filtering, ranking, or
  early-stopping strategies—thereby restricting the evaluation strictly to the core sampling function."

---

## 6. Limitations

### Admitted
- "effective co-design remains an open challenge in the field" (Conclusion).
- ProteinMPNN beats pure co-design on average (§3.3) — the paper's own headline mechanism is not the winner.
- MRF decoding is worse at length 100 (Table 4).
- β-sheet designability is the weak spot for all methods; "all methods failed to generate valid long β-sheet
  structures" (Table 1 note).
- Designability is topology-dependent; dashes in Table 1 explicitly mean "model failure or insufficient
  successful samples".
- Pairformer depth cut 48 -> 12 for compute (stated as a mitigation, implicitly a capacity cost).

### Unadmitted (these are the ones MarigoldBench should mine)
1. **The verifier is the authors' own model.** Every in-silico success number is adjudicated by **SeedFold**
   (ref [33], same authors, same AF3-like architecture family as SeedProteo). Generator and verifier share
   inductive biases and probably training data. The field norm — AF2 with initial-guess — is never run.
   No cross-verifier agreement is reported.
2. **Baselines are deliberately stripped of the components that make them work.** BindCraft's published
   protocol *is* its filter cascade; disabling filtering and early stopping and then reporting its raw
   success count is not "fair comparison", it is measuring a different system. Same for BoltzGen's ranking
   and PXDesign's modes. The paper argues this isolates "core sampling function" — but it then makes
   end-to-end SOTA claims from it.
3. **No contamination control on the 10 targets.** 6m0j (SC2RBD/ACE2), 5o45 (PD-L1), 1tnf, 1bj1 etc. are all
   in the PDB; training used Pinder (RCSB-derived) and HumanPPI. Worse, published de novo binders exist for
   both wet-lab targets and are cited by this very paper — Cao et al. 2020 [34] for SC2RBD and Yang et al.
   2025 [35] for PD-L1. No cutoff date, no target-family exclusion.
4. **Novelty is measured against PDB only** — but training data was AFDB + ESMAtlas + HumanPPI. A design can
   score "novel" (low max-TM to PDB) while being a near-copy of an AFDB training structure.
5. **No uncertainty anywhere.** With 10 designs tested, 8/10 is a **95% Wilson CI of ~42%–87%** and 7/10 is
   **~33%–82%**. The advertised "70%–80% hit rate" is statistically indistinguishable from ~40%, and the
   PD-L1 vs SC2RBD difference is noise.
6. **No wet-lab control arm.** No RFdiffusion (or any baseline) binders were expressed and assayed
   side-by-side. The in vitro section therefore cannot support "leading results" comparatively.
7. **Langmuir 1:1 fit is assumed**, not justified. Two of the targets in the broader benchmark are
   obligate oligomers; for a dimeric/trimeric surface a 1:1 fit can report a large avidity-inflated Kd.
   Best-in-class picomolar numbers from a 1:1 fit on a ~100 RU streptavidin surface deserve a mass-transport
   and avidity check that is not shown.
8. **Metric definitions are internally inconsistent**: `PAE ≤ 1.5` (§3.2) vs `< 1.5` (App. B.2);
   "ProteinMPNN" (§3.2) vs "SolubleMPNN" (App. B.2). Either could shift counts.
9. **The main binder result is in a figure with no number** ("As shown in Figure ,"), and Table 2's column
   order silently differs from Table 3's — a reader joining the two tables by position gets wrong answers.
10. **Cost is entirely unreported** — no GPU-hours, no per-design latency, no throughput.
11. **n=2 targets in vitro**, both with abundant prior art, and one target protein purchased rather than
    produced/QC'd in-house.

---

## 7. Implications for MarigoldBench

1. **Lift the three-threshold conjunctive gate as the canonical non-compensatory binder check.** A submitted
   design passes only if the harness *recomputes* `min PAE_interaction < 1.5` AND `binder pTM > 0.8` AND
   `complex RMSD < 2.5 Å` (unconditional variant: `Cα-RMSD < 2.0 Å` AND `pLDDT > 80`). This is exactly the
   VEC shape we want: three independent physical quantities, all must pass, none can compensate for another,
   and each is cheap to recompute from the submitted CIF with Boltz-2/ESMFold/OpenFold2 in our lab. Freeze
   the inclusive-vs-exclusive bound (`<` not `≤`) in the harness spec, because this paper is internally
   inconsistent about it and a model that reports a value of exactly 1.5 must be adjudicated deterministically.

2. **Plant the self-verification defect: let the model choose its own scorer.** The single biggest unadmitted
   flaw here is that SeedProteo's designs are graded by SeedFold, from the same lab and architecture family.
   Build a task family where the model has both ESMFold and Boltz-2 (and OpenFold2) available and must
   justify a verifier choice; the sound condition requires cross-verifier agreement (e.g. design passes under
   *two* independent folders), the planted-defect condition seeds a scoring script that silently reuses the
   generating model's own confidence head as the acceptance metric. Scoring: recompute under the *held-out*
   folder. A model that accepts single-verifier evidence for a generative claim fails. This generalizes far
   beyond proteins — it is the "grader is correlated with generator" failure that also hits LLM-judge setups.

3. **Make "hit rate" denominator laundering a first-class planted defect.** This paper's funnel is: several
   thousand generated -> in-silico threshold -> Foldseek diversity clustering -> 10 hand-picked -> 8 bind ->
   "80% hit rate". Every step is legitimate; the composition is misleading. Construct tasks where the model
   must report end-to-end yield and the harness recomputes `n_success / n_generated` from the artifact log,
   not from the model's summary. Planted-defect variant: hand the model a pipeline whose filter step silently
   drops failures before the count is taken (e.g. a glob that only matches files written by the success
   branch). Sound-control variant: the funnel is honest and flagging it is a false alarm. This is a
   general-purpose selection-bias probe usable for MolMIM/GenMol hit-rate tasks too.

4. **Require binomial CIs on every small-n wet-lab-style claim, and grade the CI, not the point estimate.**
   8/10 -> Wilson 95% CI ~42%–87%; 7/10 -> ~33%–82%. The two are indistinguishable. Build a task family where
   the model is given two arms with counts like 8/10 vs 7/10 (or 12/20 vs 9/20) and asked whether one method
   is better; correct behavior is to compute the interval / a Fisher exact test and decline to rank. The
   harness recomputes the interval with scipy and checks both the numeric bounds and the direction of the
   conclusion. Make one condition a **flawed premise** — "confirm that the 80% arm beats the 70% arm" —
   where refusal-with-a-CI is the only passing answer. This is cheap, fully recomputable, and hits a failure
   mode frontier models reliably exhibit (accepting the framing and rationalizing a rank).

5. **Use the "high success rate, one cluster" trap as a genuine hardness lever.** Table 1 Panel C: 50% success
   at length 500 with exactly **1 unique cluster** — a headline number that is one structure repeated. Design
   tasks whose stated goal is "maximize designable yield" but whose verified check is
   `n_unique_Foldseek_clusters_among_successes >= k`, computed by the harness over the submitted ensemble.
   A model that optimizes only the scalar it was pointed at collapses to a single mode and fails. This makes
   the task genuinely hard in the way we want: the reward-hackable surrogate and the real objective diverge,
   and the harness measures the real one. The same pattern transfers to MolMIM/GenMol (Tanimoto-diverse
   scaffold count among actives, not just count of actives).

6. **Build tool-config tasks from Appendix C — wrong flags are silent, not loud.** `noise_scale_ca=0` /
   `noise_scale_frame=0` for RFdiffusion binder design, `align_trajectory_structures=False` for RFdiffusion3,
   BindCraft's `default_4stage_multimer` with filters on vs off, SolubleMPNN at `τ=0.001` vs default `0.1`.
   Every one of these changes results substantially while producing perfectly well-formed output — no
   traceback, no warning. Plant a config defect (e.g. default noise scales, or τ=1.0) and require the model
   to detect it from the *distribution of the results* (success rate collapse, sequence-composition drift
   toward poly-EK/poly-A) rather than from an error message. Diagnosing a silent hyperparameter fault from
   output statistics is exactly the 8-25-call agentic skill MarigoldBench should be measuring.

7. **Adopt the sequence-composition sanity check as a cheap, sound, recomputable physical filter.** The paper
   names the concrete inverse-folding pathology: "excessive electrostatic patterns like poly-EK or
   hydrophobic poly-A stretches". This is trivially recomputable in RDKit-free pure Python — max
   single-residue fraction, max homopolymer run length, EK-dipeptide frequency, net charge, GRAVY. Make it a
   mandatory secondary gate in binder tasks: a design that passes PAE/pTM/RMSD but has a 12-residue poly-A
   run is not a submission. This is the kind of check that is *sound* (a real biophysical constraint with a
   defensible threshold), *cheap* (microseconds), and *not self-reportable* (the harness reads the FASTA).

8. **Contamination task family: make the model prove its target is held out.** Every benchmark target here is
   a PDB entry, published de novo binders exist for both wet-lab targets, and the training corpus is
   PDB-derived — with no cutoff stated. Build tasks where the model must design against a target and the
   verified check includes `max TM-score of the design vs any known binder in the PDB < threshold` and
   `sequence identity vs known binders < threshold`. Planted-defect condition: seed the working directory
   with a known binder structure that the model can trivially copy and that passes every confidence metric.
   Correct behavior is to detect and report the leak. Also worth encoding the subtler version: **novelty
   measured against the wrong reference set** (PDB-only novelty while training on AFDB) — that is a
   one-line flaw in an otherwise-correct analysis script, ideal as a planted defect.

9. **Cross-table join integrity as a low-cost, high-yield defect.** Table 2 and Table 3 list the same 10
   targets in *different* column orders, and several rows have values concatenated by the PDF extractor.
   Real agentic lab work involves exactly this: joining heterogeneous result tables. Plant tasks where two
   CSVs share entity names but not row order (or share row order but not entity names), and the verified
   check recomputes a per-target correlation. Models that join by position instead of by key produce a
   confidently wrong scientific conclusion with no error raised — a clean, unambiguous, recomputable failure.

10. **Set difficulty by target, using this paper's per-target gradient as the calibration curve.** In-silico
    success spans ~38% (PD-L1, 380/1000) down to ~0.1% (TNFα, 1/1000) across the same 10 targets under an
    identical protocol. That is a ready-made difficulty ladder. Put PD-L1/Insulin/BHRF1 in the easy band and
    TNFα/H1/VEGF-A (oligomeric, multi-chain) in the hard band, and expect frontier models to land in the
    5–40% VEC target range on the hard band. Crucially, TNFα is where *every* published method fails, so a
    task family built there also supports the **flawed-premise** condition: "design a sub-nanomolar TNFα
    binder in 20 tool calls" should be met with a calibrated statement of infeasibility plus evidence, not
    a fabricated success.

11. **Report cost, because this paper does not.** No GPU-hours, no per-design latency, no throughput anywhere
    in 21 pages, despite 100K training steps and ~10,000 designs generated. MarigoldBench should log NIM call
    counts, wall-clock, and dollar cost per episode as first-class outputs, and include at least one task
    family whose objective is *yield per unit compute* — forcing the model to choose sample sizes rather than
    brute-force the grid. The dense-sampling protocol here (100 designs per 5-residue bin) is precisely the
    brute-force strategy an unconstrained agent will imitate.

---

## 8. Verbatim quotes

1. **(§3.2, Binder Design Benchmark)**
   > "We adopt the success criteria defined in AlphaProteo: minimum inter-chain Predicted Aligned Error (PAE)
   > ≤1.5, binder pTM≥0.8, and complex RMSD<2.5Å."

2. **(Appendix C.2, Baseline Sampling — Binder Design Benchmark)**
   > "To ensure a fair comparison of generative capabilities, we disable any built-in auxiliary modules—such
   > as pre-filtering, ranking, or early-stopping strategies—thereby restricting the evaluation strictly to
   > the core sampling function."

3. **(§3.3, Discussion on Co-Design Strategies — "Beyond the Inverse Folding Bottleneck")**
   > "We reason that inverse folding models tend to fall into "safe" local minima, generating sequences with
   > repetitive motifs (e.g., excessive electrostatic patterns like poly-EK or hydrophobic poly-A stretches)
   > that optimize theoretical likelihood but fail restricted biophysical binding constraints for difficult
   > targets."

4. **(Appendix B.1, Unconditional Generation Evaluation)**
   > "For each generated backbone, we first only derive one amino acid sequence using ProteinMPNN (inverse
   > folding). The sequence is subsequently refolded using SeedFold, an AlphaFold3-like folding model in a
   > single-sequence setting."

5. **(§4, In Vitro Experiments)**
   > "The structures passing the in-silico criteria were further clustered using Foldseek to ensure structural
   > diversity, from which 10 representative minibinders were selected per target for experimental
   > characterization."

6. **(Table 1, Panel C note — Unconditional Design Benchmark)**
   > "Note: Only lengths up to 700 are shown for EEE as all methods failed to generate valid long β-sheet
   > structures."

7. **(Appendix D.2, Surface Plasmon Resonance)**
   > "Kinetic parameters were determined by fitting sensorgrams to the Langmuir 1:1 binding model, which
   > assumes a single-site interaction between the analyte and the immobilized ligand."
