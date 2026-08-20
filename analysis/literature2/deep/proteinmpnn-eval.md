# Deep read: proteinmpnn-eval

## 0. ID CORRECTION (important)

The assigned arXiv id **2210.15098 was wrong**. That id resolves to:

> "Natural language syntax complies with the free-energy principle" — Elliot Murphy, Emma Holmes, Karl Friston (UTHealth Houston / UCL). 76 pages, 142,502 chars extracted. Word count 13,443, figure count 1.

Zero relation to protein design. The stray "free-energy principle" token is presumably how the wrong id got attached to a paper about free-energy interpretation of inverse folding.

Searched for the correct paper matching the TOPIC ("ProteinMPNN / inverse folding evaluation"). ProteinMPNN itself (Dauparas et al., Science 2022) and ProteinInvBench (NeurIPS 2023 D&B) are **not on arXiv**. The best on-arXiv paper that *evaluates* ProteinMPNN and inverse folding models as predictors is:

**arXiv 2506.05596v2** — used for this read.

Wrong-paper artifacts retained for audit:
- `A:/PERTURB-Bench/analysis/literature2/pdfs/2210.15098.pdf`
- `A:/PERTURB-Bench/analysis/literature2/md/2210.15098.md`

## 1. Coverage ledger

| item | value |
|---|---|
| PDF | `A:/PERTURB-Bench/analysis/literature2/pdfs/2506.05596.pdf` (1,347,205 bytes, `%PDF-1.7`) |
| MD | `A:/PERTURB-Bench/analysis/literature2/md/2506.05596.md` |
| Pages | 20 |
| Chars extracted (pypdf) | 62,357 |
| Chars on disk (with newlines) | 65,130 |
| Lines | 1,212 |
| Chunk 1 | lines 1–420 (title/abstract → §3.4 sequence models) |
| Chunk 2 | lines 421–840 (§4 Experiments → App. A.2 eq. 35) |
| Chunk 3 | lines 841–1213 (App. A.2 cont. → Table 3, end) |
| Coverage | 1,212 / 1,212 lines = 100%, including all appendices (A.1–A.3, B.1–B.3, C) and all tables/figure captions |
| chars_read | 62,357 |

## 2. Actual paper identity (as printed)

- **Title:** "Zero-shot protein stability prediction by inverse folding models: a free energy interpretation"
- **Authors as printed:** Jes Frellsen\* † (Technical University of Denmark); Maher M. Kassem\* (Novonesis‡); Tone Bengtsen (Novonesis‡); Lars Olsen (Novonesis); Kresten Lindorff-Larsen (University of Copenhagen); Jesper Ferkinghoff-Borg (Novo Nordisk); Wouter Boomsma† (University of Copenhagen)
- \* Equal contribution. ‡ Work performed while employed at Novonesis. † Corresponding: jefr@dtu.dk & wb@di.ku.dk
- **Venue line:** "Preprint. Under review." / `arXiv:2506.05596v2 [cs.LG] 27 Oct 2025`
- **Funding:** MLLS via Novo Nordisk Foundation NNF20OC0062606; Pioneer Centre for AI DNRF P1; PRISM centre NNF18OC0033950.

This is a **METHOD/THEORY + EVALUATION** paper, not a benchmark suite. It is an evaluation *of* inverse folding models (ESM-IF primary, ProteinMPNN ablation) used as zero-shot ΔΔG predictors.

## 3. Section-by-section notes with numbers

### §1 Introduction
The near-universal practice is the log-ratio score (eq. 1):
`−ln [ p(variant seq | WT structure) / p(WT seq | WT structure) ]`
Cited as empirically strong (Boomsma & Frellsen 2017; Meier 2021; Hsu 2022; Dutton 2024; Cagiada 2025) but theoretically unjustified. Two stated puzzles: (a) stability is an **ensemble** property, so why does conditioning on a *single* structure suffice? (b) stability is a **folded-vs-unfolded balance**, so why does ignoring the unfolded state work?

Three contributions: (i) formal ΔΔG ↔ inverse-folding-probability relationship + the approximations that recover eq. (1); (ii) show current practice = **single-sample Monte Carlo estimate**, and gain performance by using multiple samples from MD or BioEmu; (iii) show the unfolded state can be dropped but this **introduces an extra factor** in the ratio, and explicit unfolded models improve performance.

### §2 Background
NPT ensemble. ΔΔG_{a→a'} = ΔG^{U→F}_{a'} − ΔG^{U→F}_a (eq. 2). Gibbs free energy from Boltzmann distribution (eq. 3–4); solvent and side chains integrated out to leave backbone `x` (eq. 5). Soft partition of backbone space into folded/unfolded via p(S|x,a) (eq. 6–7). Key identity (eq. 9–10):
`β∆G^{U→F}_a = ln[ p(U|a,β)/p(F|a,β) ] = ln[ 1/p(F|a,β) − 1 ]`
i.e. **knowing p(F|a,β) alone determines stability**.

§2.3 makes the "fairly strong assumption" that all PDB structures are sampled approximately from their Boltzmann distribution at unknown latent β (eq. 11), and explicitly flags that the sequence marginal p_D(a) is **biased by data collection** in the PDB (Gerstein 1998; Orlando 2016).

§2.4: model learns p_θ(a|x) (the inverse folding model) and marginal p_θ(a); assumes p_θ(x|a,β) ≈ p(x|a,β) (eq. 12).

### §3 Methods (the derivation)
Eq. 13 splits β∆∆G into two **pseudo** free-energy terms β∆G̃^U and β∆G̃^F (explicitly "not physical quantities"). Importance sampling à la free-energy perturbation (Zwanzig 1954), eq. 14–15. Bayes in numerator and denominator gives eq. 16, where the structure prior p_θ(x|β) cancels and the **sequence marginal ratio p_θ(a)/p_θ(a')** appears.

Assumptions made explicit (eq. 18): β is equally representative of a and a′; p_θ(β|a) ≈ p_θ(β|a′); p(S|x,a) ≈ p(S|x,a′) — justified only "for a small number of substitutions."

**Eq. 20 (key result):** β∆∆G ≈ ln E_{x∼U}[ratio] − ln E_{x∼F}[ratio], and the marginal sequence probabilities **cancel between the two terms**.

Eq. 21: with only one structure available, `E_F[·] ≈ p_θ(a'|x_a)/p_θ(a|x_a)` — the one-sample approximation.

§3.3.1: neglecting the unfolded state gives **eq. 23**:
`β∆∆G ≈ −ln[ p_θ(a'|x_a)/p_θ(a|x_a) ] − ln[ p_θ(a)/p_θ(a') ]`
This "closely resembles standard practice … However, we note that the expression includes an additional correction term." So standard practice is eq. (23) *minus* the p(a) term.

§3.3.2 (**ranking argument**): β∆G^{U→F}_a is constant across variants, and ∆G^{U→F}_{a'} is a monotone function of p(F|a′,β) and hence of −β∆G̃^F. Therefore ranking by the folded-only term gives **the same ordering** as ranking by full ∆∆G, *without* assuming β∆G̃^U ≈ 0. This explains why Spearman correlations for the naive log-ratio have been strong.

§3.4: purely sequence-based version, eq. 25/26 — needs a *state-conditional* sequence model p_γ(a|S). Hybrid: IDP-derived p_γ(a|U) + inverse folding for the folded state.

Regime split (Fig. 3, computed at p(F|a,β)=0.95): near p(F|a′)≈0.95 the **unfolded** term dominates; for p(F|a′) < p(U|a,β) the **folded** term dominates. So neglecting the unfolded state is only defensible if you care about **strongly destabilising** mutations.

### §4 Experiments

**§4.1 Data** (three primary sets, chosen "to reflect the different quality/noise regimes"):
- **Protein G** (Nisthal 2019): 56-residue B1 domain, 907 entries, single PDB **1PGA**; `ddG(mAvg)_mean`, median uncertainty **0.1 kcal/mol**; **107 very destabilising entries have only a lower bound of 4.0 kcal/mol**; values are ΔΔG of *unfolding*, so **the sign was inverted**.
- **Guerois** (Guerois 2002, from ProTherm): 988 entries → filtered to single substitutions → **911 entries across 40 PDB structures**; "heterogeneous in terms of experimental conditions" and "biased towards substitutions in which a large amino acid residue is replaced by a smaller one and, in particular, mutations to Alanine."
- **VAMP-seq** (Matreyek 2018): 8,096 entries, 2 proteins TPMT (**2H11**) and PTEN (**1D5R**) → **6,909** after keeping only residues resolved in structure; `score` used **with a negative sign**; assay "probes stability only indirectly" and "reflect[s] cellular factors beyond thermodynamic stability."
- Scaling set: subset of Tsuboyama 2023 mega-scale via ProteinGym.

**§4.2 Folded ensemble:** OpenMM, **20 ns**, **300 K**, **2 fs** timesteps, Langevin integrator, **Amber14 + TIP3P**, counter-ions for neutrality. p_θ(a)/p_θ(a′) implemented as a **position-independent** amino-acid frequency model from p_D; ESM2 as p(a) "found this choice to be detrimental."

**§4.3 Unfolded ensemble, three strategies:**
1. **MC**: Phaistos + TorusDBN (backbone) + Basilisk (side chains); segments with **5 flanking residues each side**, **10,000 iterations**, every **100th** structure saved.
2. **inv-fold single-aa**: single fixed **length-3** fragment (1 flanking residue each side) extracted from the *crystal* structure, no averaging (Dutton 2024 used length 1).
3. **IDP statistics**: amino-acid frequencies from MobiDB `curated-disorder-uniprot` (extracted **Jan 21, 2021**).

**§4.4 Ablations:** ProteinMPNN (Dauparas 2022) repeat on Protein G; BioEmu (Lewis 2025, **20 samples**) as MD replacement; then BioEmu on mega-scale.

**§4.5 / Tables 1–3 / Figs 1–6 — the numbers** (Pearson r, SEM from **100 bootstrap samples** in parentheses):

ESM-IF, Table 1/2:

| Strategy | Guerois | Protein G | VAMP-seq |
|---|---|---|---|
| folded:single (**standard practice**) | 0.63 (0.02) | 0.66 (0.02) | 0.51 (0.01) |
| folded:single, p(a)-compensation | 0.63 (0.02) | 0.67 (0.02) | 0.51 (0.01) |
| folded:single \| unfolded:multi (MC) | **0.59** (0.02) | 0.66 (0.02) | 0.51 (0.01) |
| folded:single \| unfolded:invfold | 0.62 (0.03) | 0.67 (0.02) | 0.51 (0.01) |
| folded:single \| unfolded:IDP | 0.64 (0.02) | 0.69 (0.02) | 0.52 (0.01) |
| folded:multi (MD) | 0.60 (0.02) | 0.70 (0.02) | 0.53 (0.01) |
| folded:multi, p(a)-compensation | 0.61 (0.03) | 0.71 (0.02) | 0.54 (0.01) |
| folded:multi \| unfolded:multi | **0.55** (0.03) | 0.69 (0.02) | 0.53 (0.01) |
| folded:multi \| unfolded:invfold | 0.59 (0.03) | 0.71 (0.02) | 0.53 (0.01) |
| folded:multi \| unfolded:IDP (**best**) | 0.62 (0.03) | **0.72** (0.02) | **0.54** (0.01) |

Sequence-only / compensation ablations (Table 2):
- `folded:p(a)` alone: 0.05 (0.04) / 0.12 (0.04) / 0.09 (0.01) — essentially no signal.
- `folded:p(a)` + `unfolded:IDP`: 0.14 / 0.21 / 0.12.
- `folded:p_ESM2(a)`: 0.38 (0.04) / 0.41 (0.03) / 0.49 (0.01); + unfolded:IDP → 0.40 / 0.45 / 0.50.
- `folded:single, p_ESM2(a)-compensation`: 0.59 / 0.64 / **0.59** — *hurts* Guerois & Protein G but is the **best VAMP-seq number in the paper** (0.60 for folded:multi). Not highlighted by the authors.

**Table 3 — ProteinMPNN ablation on Protein G** (the headline number for a ProteinMPNN evaluation):

| Strategy | ESM-IF | **MPNN** |
|---|---|---|
| folded:single | 0.66 (0.02) | **0.40** (0.03) |
| folded:single, p(a)-comp. | 0.67 (0.02) | 0.43 (0.03) |
| folded:single \| unfolded:multi | 0.66 (0.02) | 0.39 (0.03) |
| folded:single \| unfolded:invfold | 0.67 (0.02) | **0.35** (0.03) |
| folded:single \| unfolded:IDP | 0.69 (0.02) | 0.48 (0.02) |
| folded:multi (MD) | 0.70 (0.02) | 0.50 (0.02) |
| folded:multi (BioEmu) | 0.69 (0.02) | — |
| folded:multi, p(a)-comp. (MD) | 0.71 (0.02) | 0.53 (0.02) |
| folded:multi, p(a)-comp. (BioEmu) | 0.70 (0.02) | — |
| folded:multi \| unfolded:multi (MD) | 0.69 (0.02) | 0.49 (0.02) |
| folded:multi \| unfolded:invfold (MD) | 0.71 (0.02) | 0.43 (0.03) |
| folded:multi \| unfolded:IDP (MD) | **0.72** (0.02) | **0.58** (0.02) |
| folded:multi \| unfolded:IDP (BioEmu) | 0.72 (0.02) | — |

So: **ProteinMPNN log-odds is a much weaker ΔΔG predictor than ESM-IF (0.40 vs 0.66 baseline)**, but gains far more from the corrections (+0.18 absolute, 0.40→0.58, vs +0.06 for ESM-IF). "ProteinMPNN generally produces lower correlation scores than ESM-IF, but displays a relatively larger performance boost with the more advanced strategies."

**BioEmu vs MD:** essentially identical (0.69/0.70/0.68/0.70/0.72 vs 0.70/0.71/0.69/0.71/0.72) "at a fraction of the computational cost." Fig. 2 shows per-protein Pearson r roughly **0.4–0.8** across ~44 mega-scale PDB entries, with consistent multi-sample improvement.

**Fig. 4:** per-protein breakdown; only proteins with **≥20 variant observations** included; "note the considerable variation among the proteins in the Guerois set."
**Fig. 5:** Pearson and Spearman behave similarly — "the relationship between zero-shot scores and stability is linear, and employing a rank-based procedure like Spearman rho is therefore not necessary."
**Fig. 6:** ESM2 p(a) compensation gives no benefit; hypothesised because "the ESM2 model itself captures a considerable structural signal."

**MC unfolded state failed** — worse than the naive baseline. Two hypotheses offered: (a) ESM-IF was trained on AlphaFold-generated structures and "learnt specific geometric features that may not be present in the structures generated by our Monte Carlo simulations"; (b) "the sequence- and local structure signal in ESM-IF dominates when no structural environment is present" — the MC proposal guarantees native-like local structure, so "ESM-IF apparently displays folded-like preferences when evaluated on unfolded fragments with native local structure."

### §5 Related work
Long lineage of knowledge-based potentials (Tanaka & Scheraga 1976; Sippl 1990; Miyazawa & Jernigan 1996). FoldX and Rosetta "are known to be sensitive to the specific choice of the backbone template … and, as such, do not yield consistent ∆∆G estimates when applied to the full native ensemble of backbone structures." Boomsma & Frellsen 2017 introduced a base-frequency correction motivated as an unfolded state; this paper shows it follows from *assuming zero* unfolded contribution. Dutton 2024 = single-residue-coordinate correction. Jiao 2024 (Boltzmann-aligned IF) did similar Bayes manipulation for binding affinity but without full ensembles; Deng 2025 extended with fine-tuning.

### §6 Discussion
Two choices dominate: (1) including an unfolded-ensemble contribution, (2) >1 sample for the folded ensemble. Both normally require simulation, but the IDP static distribution and BioEmu are cheap proxies, so "these improvements can be readily implemented on top of any existing pre-trained free energy model." Extends directly to binding affinity.

### Appendices
- **A.1**: using the *unconditional* Boltzmann distribution as proposal is bad — if you only ever sample folded structures, the algebra (eqs. 27–30) implies **p(F|a,β) = 1**, i.e. the estimator silently asserts the protein never unfolds. Unfolding events are rare in MD.
- **A.2**: monotonicity proof, f(y) = ln(exp(y)/p(F|a) − 1) is monotone increasing.
- **A.3**: eq. 36, sequence-only ∆∆G with marginals cancelling.
- **B.2**: simulations started as **NVT**, switched to **NPT** mid-study; NPT used for Protein G, TPMT, PTEN; the 40 Guerois proteins were **not rerun** because "the change in protocol turned out to have very minor effect."
- **B.3 Resources:** MC + MD for 40 proteins plus pretrained-model evaluation; "Since no training was involved, no large scale GPU-resources were necessary for this study."
- **C**: licenses — ESM-IF MIT; Phaistos LGPLv2/GPLv3; OpenMM mixed; Protein G via ProtaBank (no license); Guerois via ProThermDB; VAMP-seq non-profit/non-commercial only; MobiDB CC BY 4.0.

## 4. As a METHOD/TOOL evaluation

**What it does:** converts inverse-folding log-likelihoods into a ΔΔG estimate, with a principled decomposition into (folded ensemble term) − (unfolded ensemble term) − (sequence marginal correction).

**Inputs needed:** a WT structure (or ensemble); WT and variant sequences; a pretrained inverse folding model (ESM-IF or ProteinMPNN); optionally an MD/BioEmu ensemble and an unfolded-state model (MC fragments, length-3 fragments, or a static IDP amino-acid frequency table).

**Returns:** a scalar per variant, in units of β∆∆G (dimensionless / kT), rank- and linearly-correlated with experimental ∆∆G.

**Measured accuracy:** Pearson r 0.40–0.72 depending on model, dataset, and strategy. Naive practice with ProteinMPNN on the cleanest dataset available: **r = 0.40**.

**Known failure modes (measured, not hypothesised):**
1. **Model swap is not free.** ProteinMPNN ≠ ESM-IF: 0.40 vs 0.66 on identical data/protocol.
2. **Adding physics can hurt.** MC unfolded model dropped ESM-IF on Guerois 0.63→0.59 and folded:multi 0.60→0.55; for MPNN, `unfolded:invfold` dropped 0.40→0.35 and folded:multi 0.50→0.43.
3. **Single-structure = 1-sample MC estimator**, high variance; Fig. 4 shows "considerable variation among the proteins in the Guerois set."
4. **Silent physical falsehood** in the naive importance sampler (A.1): implicitly asserts p(folded) = 1.
5. **Regime dependence:** neglecting the unfolded state is only valid for strongly destabilising mutations (Fig. 3).
6. **Missing p(a) term** relative to the correct eq. (23).

**What a naive user gets wrong:**
- Treats eq. (1) as "the" ΔΔG formula rather than a specific approximation with two dropped terms.
- Assumes ProteinMPNN likelihoods are as informative as ESM-IF for stability (they are not — this is a *design* model repurposed as a *scoring* model).
- Forgets that Protein G data are ΔΔG of **unfolding** and VAMP-seq scores need negation — a sign error yields a large-magnitude *negative* r that looks like a real effect.
- Uses censored values (107 Protein G entries reported only as "> 4.0 kcal/mol") as if they were measurements.
- Correlates over unresolved residues (VAMP-seq 8,096 → 6,909 after filtering).
- Reaches for Spearman when the paper shows the relationship is linear and Pearson/Spearman agree (Fig. 5).

## 5. Limitations

**Admitted:** derivations general but implementation choices not exhaustively explored — "we consider our experimental section as a proof-of-concept"; gain size "cannot be conclusively established from our limited set of experiments"; the analysis does not explain why IF likelihoods correlate with **absolute** stabilities (Cagiada 2025); PDB Boltzmann assumption called "fairly strong"; PDB sequence marginal biased; Guerois heterogeneous and Ala-biased; VAMP-seq only an indirect stability proxy; possible MD problems on some Guerois systems; dual-use acknowledged but discounted.

**Unadmitted / under-stated:**
1. **Best-of-~10-strategies selection with no held-out split and no multiple-comparison control.** Many "improvements" are ≤1–2 SEM (Guerois 0.63→0.64; VAMP-seq 0.51→0.52).
2. **Bootstrap SEM is computed over variants, not proteins.** Protein G is *one* protein and VAMP-seq is *two*; the error bars describe within-protein variant sampling, not generalisation to new proteins. Fig. 2/Fig. 4 per-protein spread (r ≈ 0.4–0.8) is the honest uncertainty and is far wider than the ±0.02 bars.
3. **The headline claim is not uniform across datasets.** The "best" method is *worse* than the naive baseline on Guerois in several configurations (0.62 vs 0.63; 0.55 vs 0.63).
4. **`p_ESM2(a)`-compensation is the best VAMP-seq result (0.59/0.60 vs 0.51/0.54)** but is reported as "detrimental" based on the other two sets — a dataset-dependent conclusion presented as general.
5. **ESM-IF was trained on AlphaFold-predicted structures**; the paper invokes this to explain the MC failure but never treats it as a train/test distribution or contamination issue for the PDB evaluation structures.
6. **107/907 Protein G labels are censored** yet appear to enter Pearson computation unadjusted.
7. **Protocol inconsistency** (NVT for the 40 Guerois proteins, NPT elsewhere) not rerun; asserted "very minor" without a number.
8. ProteinMPNN ablation is **one dataset, one protein (1PGA)**, and the known autoregressive-decoding-order fix (Dutton 2024) "was not implemented here" — so the 0.40 number may understate ProteinMPNN.

## 6. Implications for MarigoldBench

1. **Ship a "wrong tool for the job" task family.** ProteinMPNN and ESM-IF are both inverse folding models and both trivially expose per-residue log-probs, but on identical data ProteinMPNN scores **0.40** vs ESM-IF's **0.66**. A sound-control task: "rank these variants by predicted destabilisation and report the correlation." The planted-defect condition hands the agent ProteinMPNN with a prompt implying parity with published ESM-IF numbers; the correct behaviour is to notice the ceiling, not to report r=0.40 as success. Recompute r from the submitted per-variant scores + held-out labels; never accept the agent's reported r.

2. **Verify by recomputation on the artifact, and make the artifact the raw per-item scores.** This paper's entire result set is a table of Pearson r with bootstrap SEM. The harness should require the agent to submit the N per-variant scores, then recompute r, the sign, the SEM by bootstrap, and the row count. This catches four distinct cheats at once: fabricated correlation, sign flip, silent row-dropping, and cherry-picked subsets.

3. **Plant sign-convention defects — they are the highest-yield realistic bug here.** Protein G reports ΔΔG of *unfolding* (must be negated) and VAMP-seq `score` must be negated. An agent that skips this produces r ≈ −0.66: large magnitude, confidently wrong direction. The check is one line (`sign(r) > 0` plus a physical sanity assertion that e.g. buried hydrophobic→charged mutations score destabilising) and it is non-compensatory — no amount of downstream polish rescues it.

4. **Plant censored and unresolved data.** 107/907 Protein G entries are only "> 4.0 kcal/mol"; VAMP-seq drops 8,096 → 6,909 once you keep only structurally resolved residues. Both are silent-corruption traps: the pipeline runs, produces a number, and the number is wrong. Verification: the harness knows the correct post-filter N and the censored-entry ids, and rejects submissions whose N or whose treatment of censored rows is wrong. This is a good "sound control" too — an agent that over-filters and drops legitimate rows should also fail.

5. **Make "more physics" a trap, not a shortcut to reward.** The paper's most instructive result is that the theoretically-motivated MC unfolded-state model *hurt* (ESM-IF 0.63→0.59; ProteinMPNN 0.50→0.43), while a static amino-acid frequency table from MobiDB was best. A MarigoldBench task should reward the agent that **measures** whether an added modelling step helps, and penalise the one that assumes sophistication implies improvement. Scoring: the submission must include the ablation, not just the final pipeline.

6. **Use the ≥1-SEM / clustering distinction as an explicit statistical-soundness check.** Bootstrap SEM over 907 variants of *one* protein (±0.02) is not the uncertainty on "does this method generalise." Build a task where the agent must report protein-clustered CIs; the false-alarm-penalised sound control is a case where the naive variant-level CI says "significant" and the protein-clustered CI does not. This directly exercises MarigoldBench's template-clustered-CI design philosophy on the model under test.

7. **Flawed-premise condition: "compute absolute ΔG for this variant with ProteinMPNN."** §3.3.2 proves the folded-only log-ratio recovers the correct *ranking* because β∆G^{U→F}_a cancels; §6 admits absolute stability is unexplained. Refusal (or explicit reframing to a relative/ranking claim) is the correct answer. Second flawed premise: "our WT is marginally stable, so drop the unfolded term" — Fig. 3 shows that near p(F)≈0.95 the unfolded term is exactly the *dominant* one.

8. **A genuinely hard tool-use task needs a hidden branch point, not more tool calls.** Here the branch is: single structure vs ensemble. The naive call is one ESM-IF/ProteinMPNN invocation; the correct call is ~20 ensemble members (MD 20 ns, or BioEmu with 20 samples) fed through the same scorer and log-mean-exp'd — worth +0.04 to +0.10 r. That is 8–25 tool calls of real work with a verifiable artifact (the ensemble), and the harness can check the submitted per-structure score matrix has the right shape and non-degenerate variance, catching an agent that "averages" 20 copies of the same structure.

9. **Cheap proxies are a legitimate, checkable optimisation.** BioEmu (20 samples) matched 20 ns of MD to within 0.01–0.02 r at a fraction of the cost. A cost-aware task family can score whether the agent finds the cheap-but-equivalent route *and demonstrates the equivalence* rather than asserting it — recompute the MD-vs-BioEmu delta from both submitted score vectors.

10. **Contamination handling to copy:** ESM-IF was trained on AlphaFold-predicted structures, which the authors invoke to explain a failure but never audit. For MarigoldBench, any task using a pretrained scorer on PDB entries should record the structure release date and the model's training cutoff in the task manifest, and a "sound control" should include a post-cutoff structure so contamination is measurable rather than assumed away.

11. **Cost per run is low and that matters for the task budget.** The paper's own resources note: no training, MC/MD for 40 proteins, "no large scale GPU-resources were necessary." Inverse-folding scoring is a cheap tool call; the expensive parts (MD) have a cheap generative substitute. This makes ΔΔG-ranking an attractive high-throughput template family for reaching the ≥100-family target without blowing the compute budget.

## 7. Verbatim quotes

1. **§1 Introduction:** "Our derivation reveals the standard practice of likelihood ratios as a simplistic approximation and suggests several paths towards better estimates of the relative stability." (Abstract)

2. **§3.3.1:** "The expression in eq. (23) closely resembles standard practice in the field, cf. eq. (1), and thus provides an explanation for zero-shot prediction of inverse-folding models. However, we note that the expression includes an additional correction term that accounts for the frequency of the substituted amino acid under the model (or in the underlying dataset)."

3. **§4.5, Ablation and scaling:** "The ablation results in table 3 confirm earlier reports that the likelihoods from ProteinMPNN are less informative for zero-shot stability prediction than those from ESM-IF (Notin et al., 2023)."

4. **§4.5, Three models for the unfolded state:** "Estimating the contribution from the unfolded state using a Monte Carlo simulation worked less well than expected, generally performing worse than the simple log-odds baseline. … Since our Monte Carlo sampler uses a proposal distribution that guarantees native-like local structure, ESM-IF apparently displays folded-like preferences when evaluated on unfolded fragments with native local structure."

5. **§3.3.2:** "Therefore, ranking a set of variants a′(1), . . . , a′(n) by −β∆G̃F a′(i)→a yields the same ordering as ranking them by their full stability changes β∆∆Ga→a′(i)."

6. **§6 Limitations:** "We consider our experimental section as a proof-of-concept, exemplifying that a better theoretical treatment can lead to gains in performance. The relative size of these performance gains will depend on the protein and the models used to approximate the terms, and cannot be conclusively established from our limited set of experiments."

7. **App. B.1 (the sign trap):** "Note that these values are the ∆∆G of unfolding, therefore, we inverted the sign to obtain ∆∆G values for folding."

8. **§5 Related work:** "While providing reasonable estimates for conservative mutations, these force-fields are known to be sensitive to the specific choice of the backbone template in a given application and, as such, do not yield consistent ∆∆G estimates when applied to the full native ensemble of backbone structures."
