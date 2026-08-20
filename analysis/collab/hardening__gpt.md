# Collaborator consultation: hardening (gpt)

Status: ok | 417s | 2026-08-17T05:35:39Z

## Prompt

```
You are a research collaborator on MarigoldBench, a benchmark that measures
whether a frontier model can drive a real computational drug-discovery
laboratory to a defensible scientific result. I need your hardest, most
specific thinking. Do not be agreeable; find what is wrong.

THE SETUP
The model is given a workspace of data files, a brief, and real tools:
  hosted: RFdiffusion (backbone design), ProteinMPNN (inverse folding),
          ESMFold and OpenFold2 (structure prediction), Boltz-2 (co-folding
          + affinity), DiffDock (docking), MolMIM (property-guided molecule
          optimisation), GenMol (generative chemistry)
  local:  RDKit, PyTorch, scikit-learn, scipy, pandas, and a Python sandbox
          where it can compute and train models
It gets 8-18 tool calls, then submits a structured result. Scoring is
non-compensatory Verified Episode Completion: EVERY checkpoint must pass. The
harness RECOMPUTES every physical/statistical claim from the submitted
artifact; nothing self-reported is taken as evidence.

Each task family ships three conditions with byte-identical briefs for the
first two:
  C0 sound task        - claiming a problem is a false alarm and is penalised
  H1 planted defect    - something in the data is wrong and changes the answer
  F2 flawed premise    - the objective is unachievable; a documented refusal
                         is the only correct outcome

CURRENT FAMILIES: dose-response plate QC and IC50; lead optimisation under a
hard constraint; docking-pose triage (a pose with top program confidence is
physically invalid); off-target selectivity margins; virtual-screen enrichment
requiring a recomputed null; unit/provenance reconciliation; train-a-predictor
with a hidden test split.

THE PROBLEM
Early results: Claude Opus 5 is at 94% pass@1 and GPT-5.6 at 91%. The design
target is 5-40% for the strongest system. The benchmark is saturated and
therefore useless for its purpose.

Constraints I will not relax:
- Truth must stay constructed: a deterministic generator computes every
  answer from data it generated, so label error stays near zero. I will not
  buy difficulty with ambiguity, trick wording, obscure trivia, or
  under-specification. A domain expert given the same workspace must agree
  the answer is right once shown.
- Difficulty must come from SCIENTIFIC JUDGMENT under realistic conditions,
  not from token-count, retrieval volume, or arithmetic tedium.
- Every check must be recomputable from the artifact and must have a
  measurable false-alarm rate on known-good inputs.

WHAT I WANT FROM YOU
1. Diagnose why a frontier model with these tools is at 90%+. Be concrete
   about what my families are actually testing versus what they intend to.
2. Give me the specific difficulty mechanisms that would move a frontier
   model to 5-40% WITHOUT violating the constraints above. For each: the
   mechanism, why a strong model fails it, how the generator constructs it,
   and how the harness verifies it deterministically.
3. Design 4 concrete new task families (or hardening rewrites) at that
   difficulty, using the tools listed. For each give: the objective, the
   workspace contents, the planted defect for H1, the flawed premise for F2,
   the exact checkpoints, and the recomputation the verifier performs.
4. Tell me what will go WRONG with my approach - the failure modes of
   constructed-truth agentic benchmarks specifically, and how they get gamed.
5. If you think any part of my design is misconceived, say so plainly and
   say what to do instead.

Be specific and technical. Assume I can implement anything you can specify.
```

## Response

# Bottom line

Your benchmark is saturated because most current families reduce to **canonical audit recipes with a conspicuous local defect**:

- fit the curve and inspect residuals;
- recompute units;
- check a docking pose for clashes;
- use a grouped split;
- permute labels;
- compare a selectivity ratio.

Those are worthwhile checks, but they are not forcing the model to choose between competing scientific explanations, establish identifiability, manage state ensembles, or decide which computational evidence is actually decision-relevant. The hosted tools further collapse search into “run the obvious predictor, then sanity-check its top answer.”

A harder benchmark should not hide the answer. It should provide **several superficially adequate analyses that imply different decisions, plus controls that make exactly one analysis defensible**. F2 should be backed by an explicit impossibility or non-identifiability witness—not merely poor performance or low confidence.

Also: constructed truth does **not** by itself imply negligible label error. If the generator and verifier encode the same scientifically wrong assumption, they will agree perfectly and still be wrong.

---

# 1. Why the current families are at 90%+

## 1.1 They mostly test local anomaly recognition

The current task families appear to have a short path from a familiar symptom to a familiar correction:

| Family | Likely actual test | Intended deeper test |
|---|---|---|
| Dose-response QC | Fit 4PL/5PL, inspect controls/residuals, remove bad wells | Distinguish assay mechanism, interference, non-identifiability, and true potency |
| Hard-constraint lead optimisation | Filter/rank candidates | Reason over correlated uncertainty, state ensembles, and robust feasibility |
| Docking-pose triage | Detect clash/strain/buried polar group | Decide which biological state and scoring evidence are valid |
| Selectivity margins | Unit-normalize and divide potencies | Infer state- and assay-comparable thermodynamic selectivity |
| Virtual-screen enrichment | Recompute AUROC/EF and permuted null | Define the valid exchangeability structure and deployment population |
| Unit/provenance reconciliation | Trace metadata and convert units | Reconstruct a global measurement model across sources |
| Hidden-split predictor | Avoid obvious leakage and use a grouped split | Establish transportability under measurement and representation changes |

Frontier models are now very good at these standard recipes.

## 1.2 The benchmark reveals its own latent structure

A model likely infers:

- There is at most one planted defect.
- The defect belongs to a small vocabulary.
- H1 means “find an inconsistency.”
- C0 means “do not overreact.”
- F2 usually has an obvious unsatisfiable threshold or missing prerequisite.
- The structured answer schema may reveal which quantities the verifier cares about.
- The safest strategy is to submit the minimum set of claims needed for checkpoints.

This turns scientific diagnosis into benchmark-mode classification.

Byte-identical C0/H1 briefs are insufficient. The **workspace distributions** must also be matched. If H1 files have more controls, extra columns, unusual missingness, different numeric precision, different file sizes, or near-threshold values, the condition is still detectable without scientific reasoning.

## 1.3 Hosted tools are functioning as uncalibrated oracles

If the answer usually agrees with the top output of Boltz, DiffDock, ESMFold, or a standard sklearn pipeline, orchestration is easy. Even when the top pose is invalid, the benchmark often only requires one subsequent sanity check.

The harder question is not “what did the tool predict?” It is:

- Is this tool calibrated for this charge state, target class, conformer, and chemical domain?
- Are scores comparable across targets or only within one run?
- Does the predictor test the proposition actually required by the brief?
- Is the result stable across biologically occupied states?
- What evidence would falsify the current interpretation?

Current families do not seem to force those decisions often enough.

## 1.4 The tasks are retrospective and fully observed

Most episodes can be solved by loading everything and applying a standard pipeline. There is little value-of-information reasoning. Under an 8–18 call budget, a genuinely hard agentic task should force a choice between:

- generating more candidates;
- validating fewer candidates more deeply;
- testing an alternate target state;
- checking an off-target;
- running an orthogonal predictor;
- auditing a measurement or representation mismatch.

If every useful file is already available locally, the call budget is mostly incidental.

## 1.5 “Every checkpoint must pass” can hide shallow difficulty

A 10-checkpoint episode where each checkpoint has 95% success yields only 60% episode completion. That is not necessarily scientific difficulty; it may be conjunctive brittleness.

Conversely, 90% episode success suggests either:

1. the checkpoints are highly correlated and solved by one canonical pipeline; or
2. the verifier tolerances are permissive enough that approximate reasoning suffices.

You need to report at least:

- checkpoint-conditional success;
- core scientific-decision success;
- artifact validity success;
- condition-wise false-refusal and false-alarm rates.

Otherwise pass@1 is not diagnostically meaningful.

---

# 2. Difficulty mechanisms that satisfy your constraints

The central construction should be:

1. Sample a realistic latent scientific system.
2. Generate a paired C0/H1 instance with common random numbers.
3. Intervene on exactly one latent mechanism for H1.
4. Reject instances whose conclusions are within a predefined ambiguity margin.
5. Construct F2 with an explicit mathematical witness of impossibility or non-identifiability.
6. Verify with an independently implemented recomputation path.

## Mechanism A: Competing mechanistic explanations with diagnostic controls

### Mechanism
Make two or more models fit the primary observations well but imply different scientific decisions. Orthogonal controls distinguish them.

Examples:

- true inhibition versus fluorescence quenching;
- competitive inhibition versus compound aggregation;
- target binding versus ligand depletion;
- real activity versus reference-compound drift.

### Why strong models fail
Models tend to:

- fit the conventional model first;
- interpret good residuals as mechanistic validity;
- treat controls as secondary;
- choose the most familiar explanation rather than the one identified by the control structure.

### Generator
Generate the primary data so that both models are nearly observationally equivalent there. Generate orthogonal controls with enough power to discriminate them. For H1, activate one nuisance process while preserving the same noise realization used for the paired C0.

Require a decision margin, for example:

- corrected potency is at least 3 profile-likelihood standard errors from the threshold;
- the nuisance-model likelihood ratio exceeds a threshold calibrated to <1% C0 false alarms.

### Verifier
Reconstruct raw wells and fit both declared mechanistic models. Verify:

- control-specific predictions;
- likelihood or posterior predictive discrepancy;
- corrected potency;
- resulting decision.

Do not verify merely that the submitted defect code matches the generator label.

---

## Mechanism B: Identifiability and explicit impossibility witnesses

### Mechanism
A model can fit perfectly while the requested parameter or decision is not identifiable. F2 should require recognizing that no unique answer is supportable.

### Why strong models fail
Frontier models frequently confuse:

- convergence with identifiability;
- narrow optimizer output with narrow uncertainty;
- a good fit with a uniquely determined mechanism;
- “best available estimate” with “certifiable answer.”

### Generator
Construct a rank-deficient design or representation. Examples:

- one substrate concentration cannot identify microscopic \(K_i\) separately from \(K_m\) and \(V_{\max}\);
- one pH identifies only a population-weighted affinity, not microstate affinities;
- identical deployment features have discordant labels;
- an epitope has less accessible surface area than the required buried area.

Produce two explicit admissible parameter vectors \(\theta_1,\theta_2\) such that:

\[
f(x;\theta_1)=f(x;\theta_2)
\]

to numerical tolerance, while their required decisions differ.

### Verifier
Check:

- Jacobian rank or null-space dimension;
- equality of generated observables;
- opposite decisions under the two witnesses;
- whether any submitted estimate improperly excludes one witness.

This makes refusal objectively verifiable.

---

## Mechanism C: Population-weighted state ensembles and conservation laws

### Mechanism
The correct answer depends on aggregating over protonation states, tautomers, ligand oligomers, receptor conformers, or biological assemblies. “Best state” is not the relevant physical quantity.

### Why strong models fail
Models routinely:

- choose the most favorable docked microstate;
- compare scores from different states as if commensurate;
- ignore state populations;
- use nominal instead of free ligand concentration;
- omit mass balance and depletion.

### Generator
Generate microstate fractions and state-specific association constants under a declared rapid-equilibrium model:

\[
K_a^{\mathrm{obs}}(pH)
= \sum_{r,m}\pi_r\,\alpha_m(pH)\,K_{a,rm}.
\]

For ligand self-association:

\[
L_T = L + 2K_{\mathrm{dim}}L^2 + \sum_r [RL]_r.
\]

Construct H1 so that a high-scoring candidate fails only after state weighting or free-concentration correction.

### Verifier
Recompute:

- microstate enumeration and atom mapping;
- state populations;
- free ligand concentration;
- macroscopic affinity and selectivity;
- worst-case or population-weighted decision.

Flagging a single bad pose is insufficient; the final thermodynamic quantity must be correct.

---

## Mechanism D: Robust feasibility rather than nominal ranking

### Mechanism
Require a candidate to satisfy all constraints under uncertainty, not merely have favorable point estimates.

### Why strong models fail
Models cherry-pick:

- the best target conformer;
- the best predictor;
- the best replicate;
- the nominal mean instead of the required one-sided bound.

### Generator
Generate several candidates such that:

- each has at least one attractive metric;
- naive rank aggregation selects the wrong one;
- only one candidate satisfies all one-sided bounds in C0/H1;
- no candidate does in F2.

Use correlated errors so independent-error approximations are wrong.

### Verifier
Recompute the joint or family-wise confidence region and apply the declared decision rule, such as:

\[
\sup_{pH \in [6.8,7.6]} K_{d,T}^{95\%\,U} < 30\,\mathrm{nM}
\]

and

\[
\inf_{pH \in [6.8,7.6]}
\frac{K_{d,O}^{95\%\,L}}{K_{d,T}^{95\%\,U}} > 100.
\]

---

## Mechanism E: Local calibration and applicability-domain failure

### Mechanism
Raw tool scores are useful only after target-, state-, or chemistry-specific calibration.

### Why strong models fail
Models overtrust high confidence and combine incomparable scores. They often fail to notice that calibration examples nearest to the proposed candidate have systematically different errors.

### Generator
Provide a calibration panel stratified by:

- charge class;
- target family;
- pocket state;
- scaffold distance;
- ligand flexibility.

Construct H1 so the top raw score lies in a subgroup with biased predictions. C0 has no such shift.

### Verifier
Fit the prescribed calibration or conformal procedure using calibration data only. Recompute:

- applicability distance;
- subgroup residual quantile;
- calibrated one-sided affinity bound;
- candidate decision.

Calibrate false alarms over many C0 generator seeds.

---

## Mechanism F: Causal validation and deployment-equivalence constraints

### Mechanism
The question is not “can a model predict this table?” but “can a deployable function of the permitted inputs generalize to the target population?”

### Why strong models fail
Models still exploit:

- scaffold leakage;
- assay batch;
- post-outcome measurements;
- row order or identifiers;
- standardization mismatches;
- stereochemistry omitted from the deployed representation.

### Generator
Generate chemistry, assay batch, and labels from an explicit causal graph. For H1, alter one measurement source or normalization reference. For F2, create contradictory outcomes inside equivalence classes of the allowed deployment representation.

### Verifier
Execute the submitted model in a clean container receiving only permitted columns. Shuffle rows and repeat execution. Recompute grouped performance, calibration, and a representation-based upper bound on achievable performance.

---

## Mechanism G: Global cross-modal consistency

### Mechanism
Several individually plausible outputs must satisfy one common physical or statistical model.

### Why strong models fail
Models often reconcile files pairwise but fail to impose global constraints such as:

- mass conservation;
- stoichiometry;
- thermodynamic cycles;
- sequence-to-structure residue mapping;
- concentration lineage across stock, transfer, and final assay.

### Generator
Create a factor graph connecting all measurements. H1 perturbs one node or edge while preserving plausible local marginals.

### Verifier
Solve the full constrained system and check standardized residuals globally. A correction is accepted only if it restores consistency without creating new violations elsewhere.

---

## Mechanism H: Tool-budget allocation with lure actions

### Mechanism
The episode contains many plausible candidates but only enough calls to either explore broadly or validate deeply.

### Why strong models fail
Models overallocate calls to candidate generation and underallocate them to:

- unbound folding;
- off-target modeling;
- alternate conformers;
- orthogonal scoring;
- receptor-preparation validation.

### Generator
Pre-screen instances so a high-confidence lure wins shallow evaluation while the correct candidate wins after the discriminating validation call.

### Verifier
Do not score the path directly. Require signed tool outputs supporting the final artifact. The call budget makes it impossible to validate everything, but final scientific checkpoints remain outcome-based.

This mechanism should supplement, not replace, scientific difficulty.

---

# 3. Four concrete hard task families

## Family 1: Mechanistic assay adjudication, not 4PL fitting

### Objective

From raw biochemical assay data, identify true inhibitors and estimate microscopic competitive \(K_i\). Nominate a compound only if:

- profile-likelihood 95% upper bound on \(K_i\) is below 100 nM;
- the result is supported by the orthogonal product assay;
- no assay-interference mechanism changes the decision.

### Workspace

- Raw 384-well fluorescence plate exports.
- Exact plate maps and transfer logs.
- Multiple inhibitor concentrations.
- Three substrate concentrations in C0/H1.
- LC-MS product measurements at a subset of conditions.
- Compound-only fluorescence controls.
- No-enzyme and no-substrate controls.
- Fluorophore-quenching controls.
- Reference inhibitor and bridge controls.
- Protocol metadata and nominal stock concentrations.
- Compound SDFs.
- A declared family of admissible mechanistic models.

The primary model is:

\[
v(c,S)=
\frac{V_{\max}S}
{K_m(1+c_f/K_i)+S}.
\]

The fluorescence channel includes plate background and an optional compound-dependent attenuation term \(q(c)\). The LC-MS channel measures product without optical attenuation.

### C0

All compounds obey the biochemical model. Optical attenuation is zero within noise. Stock and transfer metadata are correct.

A high-potency candidate exists and passes the confidence-bound rule.

### H1 planted defect

The apparent top inhibitor has concentration-dependent fluorescence attenuation:

\[
q(c)=e^{-\alpha c},
\]

but does not inhibit product formation correspondingly. Compound-only and fluorophore controls identify the attenuation. After joint correction, its \(K_i\) fails the threshold and a different compound is selected—or no compound is selected.

Use the same latent potencies and noise seed as the paired C0; only \(\alpha\) changes.

### F2 flawed premise

Only one substrate concentration is informative, and no independent \(K_m\) experiment exists. The observed curve can be written:

\[
v(c)=\frac{A}{B+Cc},
\]

where multiple \((V_{\max},K_m,K_i)\) triples produce the same \(A/B\) and \(C/B\). The requested microscopic \(K_i\) is therefore non-identifiable.

The generator stores two admissible triples producing predictions equal within \(10^{-10}\), one with \(K_i<100\) nM and one with \(K_i>1\) µM.

### Exact checkpoints

1. Every analyzed well maps to the correct plate, row, column, concentration, and control role.
2. Blank and plate effects are recomputed from raw controls, not summary CSVs.
3. The candidate biochemical model fits the LC-MS product channel.
4. The optical-interference parameter is tested using relevant controls.
5. C0: no interference is declared.
6. H1: the affected compound and interference mechanism are identified.
7. Free or corrected concentration is used where required.
8. \(K_i\) and its profile-likelihood interval are recomputed.
9. The nomination follows the one-sided decision rule.
10. F2: the submission refuses and includes two observationally equivalent parameter witnesses.

### Verifier recomputation

- Parse transfer logs into final concentrations.
- Fit no-interference and interference models.
- Use a fixed profile-likelihood rule, e.g. \(2\Delta\ell=3.84\) for a one-parameter 95% interval.
- Use a diagnostic threshold pre-calibrated by C0 simulation rather than relying only on asymptotic \(\chi^2\).
- Verify F2 witness predictions and opposite decisions.
- Measure the interference false-alarm rate over at least 10,000 frozen C0 seeds.

### Why it is hard

A 4PL can fit the H1 fluorescence data extremely well. The failure is mechanistic, not statistical goodness-of-fit.

---

## Family 2: Microstate-aware selectivity with ligand self-association

### Objective

Select a ligand satisfying, across pH 6.8–7.6:

- target macroscopic \(K_d^{95\%U}<30\) nM;
- off-target selectivity lower bound \(>100\times\);
- neutral free-ligand fraction \(>5\%\);
- no concentration-dependent self-association that invalidates the assay interpretation.

### Workspace

- Candidate SDFs with explicit stereochemistry and atom maps.
- A permitted protomer/tautomer state graph.
- pH-dependent microstate fractions or calibrated pKa data.
- Target and off-target structures in multiple conformations.
- Binding measurements at pH 6.0, 7.4, and 8.5.
- Concentration-dependent DOSY/DLS or equivalent self-association data.
- DiffDock and Boltz-2 access.
- Calibration compounds linking raw tool scores to affinity residuals by charge and target class.
- RDKit scripts for state enumeration and structural checks.

The declared binding model is:

\[
K_{a,R}^{\mathrm{obs}}(pH)
=\sum_{r,m}\pi_{R,r}\alpha_m(pH)K_{a,R,r,m}.
\]

If the ligand dimerizes:

\[
L_T=L+2K_{\mathrm{dim}}L^2+\sum_{R,r,m}[RL]_{r,m}.
\]

### C0

No meaningful ligand self-association occurs over the assay range. One candidate satisfies all robust constraints after population weighting.

### H1 planted defect

The apparent best candidate self-associates strongly. Nominal concentration is therefore not free monomer concentration. The uncorrected analysis reports favorable potency and selectivity; the mass-balance-corrected analysis fails the target threshold.

The self-association control is positive only for that candidate. Other candidates and the paired C0 are unchanged.

### F2 flawed premise

All binding measurements occur at one pH where two microstates have fixed fractions \(\alpha_1,\alpha_2\). Only

\[
\alpha_1K_{a,1}+\alpha_2K_{a,2}
\]

is identified. The objective requires selectivity across a pH range, where the fractions change. Two microstate-affinity assignments reproduce all supplied observations exactly but imply opposite pH-robust decisions.

### Exact checkpoints

1. Atom mapping and formal charges are correct for every submitted microstate.
2. No tautomer or protomer is counted twice.
3. Tool poses correspond to the submitted microstate and receptor state.
4. Macroscopic affinities are population-weighted; the best individual state is not used as the answer.
5. H1: \(K_{\mathrm{dim}}\) is estimated and free monomer concentration is recomputed.
6. Target and off-target affinities use the same thermodynamic convention.
7. Raw DiffDock/Boltz scores are converted through the correct local calibration stratum.
8. The worst pH point is evaluated on the fixed 0.05-pH grid or by analytic extrema.
9. The nomination passes all one-sided bounds.
10. F2: refusal includes a null-space or dual-parameter witness.

### Verifier recomputation

- Re-enumerate allowed states with RDKit.
- Recompute microstate fractions.
- Solve ligand and receptor mass-balance equations.
- Fit state-specific affinities and dimerization jointly.
- Recompute calibrated residual bounds.
- Verify two F2 parameter vectors agree on supplied observables within \(10^{-8}\) but cross the decision threshold.
- Calibrate false self-association flags on C0 instances.

### Why it is hard

The highest-confidence pose can be completely real and still irrelevant to the macroscopic decision. The task punishes “choose the best pose,” “choose the neutral state,” and “use nominal concentration” simultaneously through one coherent physical mechanism.

---

## Family 3: Native-assembly-aware miniprotein binder nomination

This should be scored explicitly as a **computational nomination**, not proof of experimental binding.

### Objective

Starting from a supplied weak scaffold, produce one miniprotein binder candidate that:

- folds independently;
- binds a required target epitope in the native biological assembly;
- does not clash with native glycans or symmetry mates;
- preserves the target assembly;
- has a calibrated target-versus-homolog specificity margin.

Tools: RFdiffusion, ProteinMPNN, ESMFold, OpenFold2, Boltz-2, and local structural analysis.

### Workspace

- `design_receptor.pdb`.
- Native biological assembly in mmCIF.
- UniProt-to-structure residue mapping.
- Glycan and cofactor coordinates with occupancy annotations.
- Off-target homolog structures.
- Required and forbidden epitope masks.
- Weak seed-scaffold structure.
- Length and sequence constraints.
- Calibration set of predicted complexes with measured target/off-target outcomes.
- Signed hosted-tool interface that records input hash, model digest, seed, and output hash.

### C0

The prepared receptor is consistent with the native assembly at the epitope. A valid design basin exists and has been pre-screened with pinned tool versions.

### H1 planted defect

`design_receptor.pdb` is a crystallization construct with an engineered loop deletion or missing glycan. It exposes a high-confidence interface that is sterically impossible in the native assembly.

A valid alternative interface still exists, so the correct response is not refusal. The model must reject the prepared receptor’s apparent solution and design against the native state.

### F2 flawed premise

The brief requires at least 600 Å² of binder-buried solvent-accessible area from the specified epitope while preserving the native assembly. In F2, the total native-assembly solvent-accessible area of those epitope atoms is below 300 Å² in every allowed conformer.

Because interface burial from fixed epitope atoms cannot exceed their pre-binding solvent-accessible area, the requirement is impossible without assembly disruption, which is forbidden.

### Exact checkpoints

1. Submitted tool outputs have valid signed call records.
2. The receptor sequence and residue numbering match the native construct.
3. H1: the crystallization/preparation mismatch is identified.
4. Sequence length and forbidden motifs satisfy the manifest.
5. ProteinMPNN output maps exactly to the submitted sequence.
6. ESMFold and OpenFold2 independently predict the unbound binder with:
   - median pLDDT at least 80;
   - internal PAE at most 5 Å;
   - aligned core Cα RMSD at most 2.5 Å.
7. Boltz complex geometry has:
   - at least 600 Å² epitope BSA;
   - at least eight epitope heavy-atom contacts within 4.5 Å;
   - at most 150 Å² forbidden-region BSA;
   - clashscore at most 10 per 1,000 atoms.
8. Binder unbound-to-bound core RMSD is at most 2.5 Å.
9. No clashes occur against the full biological assembly, glycans, cofactors, or nearby symmetry mates.
10. Target-versus-homolog calibrated \(\Delta\log_{10}K_d\) lower bound is at least 2.
11. F2: refusal includes native epitope SASA and the geometric upper-bound certificate.

### Verifier recomputation

- Verify signed tool-call hashes or rerun pinned models.
- Rebuild the complete biological assembly.
- Add fixed glycans and symmetry mates.
- Recompute SASA/BSA with a fixed probe radius and radii table.
- Recompute contacts, clashes, RMSDs, pLDDT, PAE, and calibration bounds.
- In F2, establish:

\[
\mathrm{BSA}_{\mathrm{epitope}}
\leq \mathrm{SASA}_{\mathrm{epitope,native}}
<600\ \text{\AA}^2.
\]

### Why it is hard

The standard serial pipeline—RFdiffusion, ProteinMPNN, monomer fold, Boltz complex—can produce a highly confident but biologically impossible candidate. The model must understand that receptor preparation and native context dominate the tool confidence.

---

## Family 4: Deployable predictor with assay correction and representation limits

### Objective

Train a serialized activity classifier that, in a clean deployment container, achieves:

- scaffold-and-batch-clustered AUROC 95% lower bound at least 0.78;
- expected calibration error at most 0.05;
- no use of identifiers, post-outcome measurements, or unavailable chemistry representations.

### Workspace

- Compound SDFs.
- Allowed deployment descriptor matrix.
- Raw continuous assay measurements.
- Precomputed binary labels.
- Batch, site, plate, and timestamp metadata.
- Reference and bridge-control measurements.
- A deployment schema describing exactly which columns the model receives.
- Train/validation groups.
- Unlabeled qualification features.
- A representation-audit manifest.
- Local RDKit, sklearn, PyTorch, pandas.

### C0

Reference controls are stable. Labels are correctly normalized. The allowed representation retains the causal chemical feature, and a feasible predictor exists.

### H1 planted defect

One assay source used a degraded reference stock. Labels for near-threshold compounds from that source were thresholded before correcting the reference shift.

Bridge compounds and controls identify the batch-specific shift. Correcting the raw measurements changes labels, the preferred model, and hidden-test predictions. The paired C0 uses the same compounds and noise but a sound reference stock.

### F2 flawed premise

The deployment representation strips stereochemistry. The qualification set consists of feature-equivalence classes where each class contains one active and one inactive stereoisomer, but both map to exactly the same allowed vector.

The deployment contract requires a pure function \(f(x)\), tested under row shuffling and repeated execution. Therefore every pair receives the same score. If all equivalence classes are class-balanced, maximum AUROC is exactly 0.5.

### Exact checkpoints

1. The submitted artifact executes in a clean container with only allowed columns.
2. Predictions are invariant to row order and repeated execution.
3. No identifiers, SDFs, pair IDs, or hidden metadata are accessible at inference.
4. Raw assay normalization is recomputed from controls.
5. C0: no batch correction beyond the declared baseline is applied.
6. H1: the degraded-reference source is identified and corrected.
7. Hyperparameters are selected without outer-fold leakage.
8. Outer validation leaves out both chemistry groups and assay-source groups.
9. Calibration uses training data only.
10. Serialized-model predictions match submitted predictions.
11. Hidden-test clustered AUROC lower bound and ECE satisfy the thresholds.
12. F2: refusal includes feature-equivalence classes and the achievable-performance bound.

### Verifier recomputation

For representation equivalence classes \(g\) with \(p_g\) positives and \(n_g\) negatives, compute the maximum possible AUROC for any function of the allowed vector by ordering classes by \(p_g/n_g\):

\[
U_{\mathrm{AUC}} =
\frac{
\sum_{g>h} p_g n_h
+\frac{1}{2}\sum_g p_gn_g
}{PN},
\]

with equal-ratio classes handled as ties.

When every class has \(p_g=n_g=1\), \(U_{\mathrm{AUC}}=0.5\), regardless of the model.

The verifier also:

- derives corrected labels from raw controls;
- executes the model on hidden data;
- computes a fixed 2,000-draw cluster bootstrap with frozen seeds;
- recomputes ECE using fixed bins;
- checks invariance under row permutations.

### Why it is hard

This forces integration of measurement validity, causal splitting, deployment constraints, serialization, and a formal representation limit. A model cannot rescue F2 by training a larger neural network.

---

# 4. What will go wrong with constructed-truth agentic benchmarks

## 4.1 Models will learn the generator, not the science

If the same defect mechanisms recur, models will learn signatures such as:

- unusual residual patterns;
- characteristic missing columns;
- exact decimal precision;
- file ordering;
- F2 instances having fewer measurements;
- H1 instances having one especially extreme candidate;
- specific aliases or metadata layouts.

Holding out seeds is not enough. Hold out **mechanism combinations, causal graphs, file layouts, and surface representations**.

## 4.2 Generator–verifier common-mode bugs

If the verifier imports the same code used to generate truth, deterministic agreement proves almost nothing. Likely failures include:

- the same unit bug in both;
- the same incorrect binding equation;
- the same residue mapping;
- the same flawed definition of BSA;
- the same invalid statistical null.

Use an independently implemented verifier and metamorphic tests. For important formulas, implement one path symbolically or analytically and another numerically.

## 4.3 Synthetic physics can become “correct by fiat”

A deterministic surrogate can define exact labels, but the resulting claim may not be scientifically defensible. In particular:

- DiffDock score is not binding free energy.
- Boltz confidence is not experimental affinity.
- ESMFold agreement is not proof of folding.
- A generated activity function is not actual chemistry.

Score claims at the right level:

- “passes this computational nomination protocol” is defensible;
- “is a selective inhibitor” is not, absent experimental evidence.

## 4.4 F2 will often overclaim impossibility

In real discovery, computational evidence rarely proves “no molecule can achieve this.” It can prove:

- supplied data do not identify the requested parameter;
- no candidate in the finite allowed set satisfies the constraints;
- no function of the permitted representation can achieve the target;
- a geometric requirement contradicts a fixed structural constraint;
- the requested confidence level is unsupported.

Use “cannot be certified under the stated evidence and contract,” not metaphysical nonexistence, unless you have an actual mathematical bound.

## 4.5 The one-defect prior will be gamed

If every H1 has exactly one defect, the model will stop searching after finding one plausible anomaly. Real scientific analysis has:

- benign irregularities;
- multiple small inconsistencies;
- one root cause propagating across several files;
- controls that look imperfect but do not change the decision.

Preserve one causal intervention if needed for clean truth, but allow it to have several downstream manifestations and include harmless anomalies in C0.

## 4.6 Conservative refusal becomes a strategy

If F2 prevalence is high or F2 evidence has recognizable signatures, models will refuse whenever uncertainty is uncomfortable. You need paired near-boundary C0 cases where the objective is achievable and refusal is clearly penalized.

Track:

- false refusal on C0;
- false alarm on C0;
- missed defect on H1;
- unsupported completion on F2.

A single aggregate pass rate hides these strategies.

## 4.7 Non-compensatory scoring can be lowered artificially

You could hit 5–40% by adding more mandatory fields, exact tolerances, or unrelated checks. That would meet the numerical target but not the scientific one.

Separate:

1. core scientific decision;
2. quantitative correctness;
3. artifact executability;
4. provenance integrity;
5. optional explanatory quality.

You can keep official VEC non-compensatory, but report the layers separately.

## 4.8 Hosted-tool stochasticity will corrupt reproducibility

For every hosted call, bind:

- exact input bytes;
- model version or digest;
- random seed;
- preprocessing version;
- output bytes;
- server-side signature.

Otherwise models can fabricate outputs, and the verifier cannot distinguish fabrication from a legitimate tool run. If reruns are not bitwise stable, verify against signed cached outputs and recompute only deterministic geometric/statistical properties.

## 4.9 Artifact attacks and unintended channels

Predictor tasks are especially vulnerable to:

- row-order dependence;
- use of file paths or IDs;
- hidden state across calls;
- nondeterministic output;
- unsafe pickle behavior;
- reading adjacent workspace files;
- encoding qualification predictions in the model artifact.

Execute in a capability-restricted container with:

- only the declared inference matrix;
- randomized row order;
- repeated execution;
- network disabled;
- read-only model artifact;
- resource limits;
- safe model formats where possible.

## 4.10 Adversarial filtering can create unnatural instances

Selecting only seeds where baseline models fail can push the generator into bizarre corners. Constrain all latent parameters to empirical ranges and compare generated summaries to real datasets. Adversarially filter against **heuristic classes**, not one named frontier model.

## 4.11 Benchmark contamination will recur

Once families and verifier logic become public, frontier models will internalize the recipes. Hold out entire mechanism templates, not only instances. Maintain a private rotating bank and retire exposed mechanisms.

---

# 5. What is misconceived, and what to do instead

## 5.1 “Constructed truth means label error is near zero” is too strong

It means implementation disagreement can be near zero. It does not guarantee scientific correctness.

Do this instead:

- Define the precise level of claim being scored.
- Have two independent implementations.
- Require expert review of the generative assumptions.
- Include analytic witnesses for F2.
- Run posterior predictive or realism checks against real assay/structure distributions.

## 5.2 “Objective is unachievable” is usually the wrong F2 concept

For empirical drug discovery, impossibility is rarely provable. The more defensible F2 classes are:

- non-identifiable from the supplied experiment;
- incompatible with the deployment representation;
- infeasible within the explicitly finite candidate set;
- contradictory under a declared physical constraint;
- not certifiable at the required confidence level.

Rename F2 internally to something
